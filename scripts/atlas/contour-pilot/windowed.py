"""Serial source-specific contours with disjoint quad ownership and shared samples."""
from dataclasses import dataclass
from contextlib import nullcontext
import gc
import json
from pathlib import Path
import time

import contourpy
import numpy as np
import shapely
from shapely.geometry import LineString

from pilot import canonical, digest, memory
from accounting import GeometryAccount, AccountingLimit

WINDOW_QUADS = 256
MAX_LEVEL_VERTICES = 100_000


@dataclass
class Grid:
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    row: int
    col: int

    def xy(self):
        if self.x.ndim == 1:
            return np.meshgrid(self.x, self.y)
        return self.x, self.y


class LimitsReached(RuntimeError):
    pass


class Ledger:
    """One ledger for all products/runs, including staging and final geometry."""
    def __init__(self, root, *, bytes_limit=150_000_000, vertices_limit=2_000_000,
                 memory_limit=512*1024**2, seconds_limit=1200):
        self.root = Path(root)
        self.bytes_limit, self.vertices_limit = bytes_limit, vertices_limit
        self.memory_limit, self.seconds_limit = memory_limit, seconds_limit
        self.start = time.monotonic()
        self.bytes = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        self.vertices = 0
        self.geometry = GeometryAccount(vertices_limit)
        self.preflight_rejected_vertices = 0
        self.peak = 0
        self.max_window_samples = 0

    def check(self, *, add_bytes=0, add_vertices=0, reserve_bytes=0):
        try:
            self.geometry.check()
        except AccountingLimit as error:
            raise LimitsReached(str(error)) from error
        current, peak = memory()
        self.peak = max(self.peak, peak)
        if peak > self.memory_limit or current+reserve_bytes > self.memory_limit:
            raise LimitsReached('Working-set limit/preflight')
        if time.monotonic()-self.start > self.seconds_limit:
            raise LimitsReached('Elapsed-time limit')
        if self.bytes+add_bytes > self.bytes_limit or self.vertices+add_vertices > self.vertices_limit:
            raise LimitsReached('Scratch-byte/stored-vertex limit')

    def append(self, stream, record, vertices=0):
        if vertices < 0 or not isinstance(vertices,int):raise ValueError('Invalid vertex count')
        try:
            self.check(reserve_bytes=vertices*256+8192)
            body = canonical(record)+b'\n'
            self.check(add_bytes=len(body))
        except LimitsReached:
            self.preflight_rejected_vertices += vertices
            raise
        # Keep the old cumulative-write gate. Role counters do not refund it.
        self.geometry.written = self.vertices
        name = Path(stream.name)
        role = 'intermediate' if name.parent.name.endswith('-fragments') else (
            'final' if 'twentyMetreSubset' in record else 'control')
        try:
            self.geometry.append(stream, body, vertices, role)
        except AccountingLimit as error:
            raise LimitsReached(str(error)) from error
        self.bytes += len(body)
        self.vertices += vertices

    def resource_counters(self):
        self.geometry.written = self.vertices
        result = self.geometry.snapshot()
        result['writerPreflightRejectedVertices'] = self.preflight_rejected_vertices
        return result

    def json(self, path, value):
        with Path(path).open('xb') as stream:
            self.append(stream, value)


def make_generator(grid):
    if contourpy.__version__ != '1.4.0':
        raise ValueError('Unapproved algorithm version')
    z = np.asarray(grid.z, dtype=np.float64)
    if z.shape[0] < 2 or z.shape[1] < 2 or max(z.shape) > WINDOW_QUADS+1:
        raise ValueError('Contour window exceeds declared sample bound')
    x, y = grid.x, grid.y
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Invalid coordinates')
    if x.ndim == 1:
        if not (np.diff(x)>0).all() or not (np.diff(y)>0).all():
            raise ValueError('Non-monotonic grid')
    else:
        if x.shape != z.shape or y.shape != z.shape:
            raise ValueError('Coordinate shape mismatch')
        dx = np.diff(x, axis=1)[:-1]
        dy = np.diff(y, axis=0)[:, :-1]
        cross_x = np.diff(x, axis=0)[:, :-1]
        cross_y = np.diff(y, axis=1)[:-1]
        if not (dx*dy-cross_x*cross_y > 0).all():
            raise ValueError('Folded/reversed curvilinear grid')
    # Invalid masking and float64 conversion occur once, for this bounded window.
    return contourpy.contour_generator(x=x, y=y, z=z, name='serial',
        line_type='Separate', z_interp='Linear', corner_mask=False,
        quad_as_tri=False, thread_count=1)


def crossing_check(points, grid, level):
    """Independent edge projection/interpolation; not interior-segment elevation."""
    x, y = grid.xy()
    z = np.asarray(grid.z, dtype=np.float64)
    starts, ends, za, zb = [], [], [], []
    for a, b in ((np.s_[:, :-1], np.s_[:, 1:]), (np.s_[:-1, :], np.s_[1:, :])):
        good = np.isfinite(z[a]) & np.isfinite(z[b]) & (
            ((z[a] <= level) & (z[b] > level)) | ((z[b] <= level) & (z[a] > level)))
        starts.append(np.column_stack((x[a][good], y[a][good])))
        ends.append(np.column_stack((x[b][good], y[b][good])))
        za.append(z[a][good]); zb.append(z[b][good])
    a, b, va, vb = map(np.concatenate, (starts, ends, za, zb))
    if not len(a):
        raise ValueError('Contour has no qualifying sample-edge crossings')
    fraction = (level-va)/(vb-va)
    expected = a+fraction[:, None]*(b-a)
    tree = shapely.STRtree(shapely.points(expected))
    index = tree.nearest(shapely.points(points))
    distance = np.linalg.norm(points-expected[index], axis=1)
    tolerance = 1e-10 if np.max(np.abs(x)) < 180 else 1e-6
    if distance.max(initial=0)>tolerance:
        raise ValueError('Contour vertex is off a declared crossing')
    edge = b[index]-a[index]
    t = np.sum((points-a[index])*edge, axis=1)/np.sum(edge*edge, axis=1)
    error = np.abs(va[index]+t*(vb[index]-va[index])-level).max(initial=0)
    if error > .001:
        raise ValueError('Edge elevation residual exceeds 0.001 m')
    return float(error)


def seam_endpoint(point, grid, level):
    """Key by native grid edge/node, never by arbitrary proximity between lines."""
    x, y = grid.xy()
    z = np.asarray(grid.z, dtype=np.float64)
    candidates = []
    for axis in ('h', 'v'):
        for side in (0, -1):
            if axis == 'h':
                row = 0 if side == 0 else z.shape[0]-1
                for col in range(z.shape[1]-1):
                    candidates.append((axis, row, col, (row, col), (row, col+1)))
            else:
                col = 0 if side == 0 else z.shape[1]-1
                for row in range(z.shape[0]-1):
                    candidates.append((axis, row, col, (row, col), (row+1, col)))
    tolerance = 1e-10 if np.max(np.abs(x)) < 180 else 1e-6
    for axis, row, col, a, b in candidates:
        va, vb = z[a], z[b]
        if not np.isfinite(va+vb) or va == vb:
            continue
        t = (level-va)/(vb-va)
        if not 0 <= t <= 1:
            continue
        p = np.array([x[a], y[a]])
        q = np.array([x[b], y[b]])
        crossing = p+t*(q-p)
        if np.linalg.norm(point-crossing)>tolerance:
            continue
        if t == 0:
            key = ('n', grid.row+a[0], grid.col+a[1])
        elif t == 1:
            key = ('n', grid.row+b[0], grid.col+b[1])
        else:
            key = (axis, grid.row+row, grid.col+col)
        return list(key), crossing
    return None, point


def extract(reader, levels, folder, ledger):
    """Own each quad once; only its bordering samples are shared with neighbours."""
    folder = Path(folder)
    folder.mkdir()
    streams = {level: (ledger.open_geometry(folder/f'{level}.ndjson','intermediate',True)
        if hasattr(ledger,'open_geometry') else (folder/f'{level}.ndjson').open('xb')) for level in levels}
    result = {'windows': 0, 'fragments': 0, 'vertices': 0, 'maxEdgeResidualMetres': 0.}
    try:
        for row in range(0, reader.shape[0]-1, WINDOW_QUADS):
            for col in range(0, reader.shape[1]-1, WINDOW_QUADS):
                r1 = min(row+WINDOW_QUADS, reader.shape[0]-1)
                c1 = min(col+WINDOW_QUADS, reader.shape[1]-1)
                ledger.check(reserve_bytes=32*1024**2)
                grid = reader.read(row, r1+1, col, c1+1)
                ledger.max_window_samples = max(ledger.max_window_samples, grid.z.size)
                generator = make_generator(grid)
                valid = np.isfinite(grid.z)
                if not valid.any():
                    del generator, grid, valid
                    continue
                low, high = float(np.nanmin(grid.z)), float(np.nanmax(grid.z))
                result['windows'] += 1
                for level in levels:
                    if not low <= level <= high:
                        continue
                    ledger.check(reserve_bytes=16*1024**2)
                    reservation=(ledger.generation_reservation((r1-row)*(c1-col))
                        if hasattr(ledger,'generation_reservation') else nullcontext())
                    with reservation:
                        generated=generator.lines(level)
                        if hasattr(ledger,'observe_generated'):
                            ledger.observe_generated(sum(map(len,generated)))
                        for line in generated:
                            ledger.geometry.processed('extracted',len(line))
                            if len(line) < 2 or not np.isfinite(line).all():
                                raise ValueError('Invalid generated geometry')
                            error = crossing_check(line, grid, level)
                            start, line[0] = seam_endpoint(line[0], grid, level)
                            end, line[-1] = seam_endpoint(line[-1], grid, level)
                            ledger.append(streams[level], {'level': level, 'window': [row, col],
                                'start': start, 'end': end, 'coordinates': line.tolist()}, len(line))
                            result['maxEdgeResidualMetres'] = max(result['maxEdgeResidualMetres'], error)
                            result['fragments'] += 1
                            result['vertices'] += len(line)
                        del generated
                del generator, grid, valid
                gc.collect()
    finally:
        for stream in streams.values():
            stream.close()
    return result


def canonical_line(coords):
    points = [tuple(p) for p in coords]
    if points[0] == points[-1]:
        points = points[:-1]
        least = min(range(len(points)), key=points.__getitem__)
        forward = points[least:]+points[:least]
        reverse = [forward[0]]+list(reversed(forward[1:]))
        chosen = min(forward, reverse)
        return chosen+[chosen[0]]
    return min(points, list(reversed(points)))


def stitch(records, max_vertices=MAX_LEVEL_VERTICES):
    """Join degree-two shared-edge endpoints; reject ambiguous junctions."""
    total = sum(len(record['coordinates']) for record in records)
    if total > max_vertices:
        raise LimitsReached('Per-level geometry bound')
    nodes = {}
    for index, record in enumerate(records):
        for side in ('start', 'end'):
            key = record[side]
            if key is not None:
                nodes.setdefault(tuple(key), []).append((index, side))
    if any(len(incidences)>2 for incidences in nodes.values()):
        raise ValueError('Ambiguous level-tie seam junction; no invented continuation')
    used, output = set(), []
    for index, record in enumerate(records):
        if index in used:
            continue
        coords = list(map(tuple, record['coordinates']))
        used.add(index)
        for front in (False, True):
            key = record['start' if front else 'end']
            while key is not None:
                candidates = [(i, side) for i, side in nodes[tuple(key)] if i not in used]
                if not candidates:
                    break
                i, side = candidates[0]
                next_record = records[i]
                next_coords = list(map(tuple, next_record['coordinates']))
                if (front and side == 'start') or (not front and side == 'end'):
                    next_coords.reverse()
                a, b = (next_coords[-1], coords[0]) if front else (coords[-1], next_coords[0])
                if a != b:
                    raise ValueError('Shared native edge produced unequal seam coordinates')
                coords = next_coords[:-1]+coords if front else coords+next_coords[1:]
                used.add(i)
                key = next_record['end' if side == 'start' else 'start']
        output.append(canonical_line(coords))
    return sorted(output)


def load_level(path, ledger):
    records, count = [], 0
    with Path(path).open('rb') as stream:
        for body in stream:
            ledger.check(reserve_bytes=32*1024**2)
            if len(body)>2_000_000:
                raise LimitsReached('Fragment serialisation bound')
            record = json.loads(body)
            count += len(record['coordinates'])
            ledger.geometry.processed('loaded',len(record['coordinates']))
            if count>MAX_LEVEL_VERTICES:
                raise LimitsReached('Per-level geometry bound')
            records.append(record)
    return records


def finish_product(fragment_folder, levels, target, ledger):
    target = Path(target)
    target.mkdir()
    stats = {'levels': {}, 'lines': 0, 'vertices': 0, 'closedLines': 0}
    for level in levels:
        records = load_level(Path(fragment_folder)/f'{level}.ndjson', ledger)
        lines = stitch(records)
        ledger.geometry.processed('stitched',sum(map(len,lines)))
        with (target/f'{level}.ndjson').open('xb') as stream:
            for index, line in enumerate(lines):
                ledger.append(stream, {'level': level, 'index': level % 100 == 0,
                    'twentyMetreSubset': level % 20 == 0, 'line': index, 'coordinates': line}, len(line))
        stats['levels'][str(level)] = {'lines': len(lines), 'vertices': sum(map(len, lines)),
            'closed': sum(line[0] == line[-1] for line in lines),
            'length': sum(LineString(line).length for line in lines),
            'sha256': digest(target/f'{level}.ndjson')}
        stats['lines'] += len(lines)
        stats['vertices'] += sum(map(len, lines))
        stats['closedLines'] += sum(line[0] == line[-1] for line in lines)
        del records, lines
        gc.collect()
    return stats


def simplification_check(lines, tolerance=2.):
    """Level-sized control, including same-level and cross-level crossings."""
    originals = [LineString(line) for line in lines]
    simplified = [line.simplify(tolerance, preserve_topology=True) for line in originals]
    displacement = max((a.hausdorff_distance(b) for a, b in zip(originals, simplified)), default=0.)
    collapsed = sum(a.is_ring and (not b.is_ring or len(b.coords)<4) for a, b in zip(originals, simplified))
    tree = shapely.STRtree(simplified)
    introduced = 0
    for i, line in enumerate(simplified):
        for j in tree.query(line, predicate='intersects'):
            if j>i and not originals[i].intersects(originals[j]):
                introduced += 1
    return {'maxDisplacement': displacement, 'collapsedRings': collapsed,
            'introducedCrossings': introduced,
            'accepted': displacement<=tolerance and collapsed==0 and introduced==0}
