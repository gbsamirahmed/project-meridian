"""One-patch, held-out single-valued heightfield experiment; no production terrain."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.tri as mtri
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from PIL import Image, ImageDraw
import riffelhorn_012c as retention
from riffelhorn_012b import source_catalog, height_grid
from meridian_paths import resolve_storage_roots
from bluesky_012a import digest

BOUNDS = np.array(retention.PATCHES['summit_cliff'], dtype=float)
ORIGIN = BOUNDS[:2]
PARAMETERS = {
    'split_block_m': 2., 'split_modulus': 4, 'guard_m': .2,
    'construction_class': 2, 'support_radius_3d_m': 1., 'minimum_neighbours': 6,
    'minimum_planarity': .05, 'maximum_plane_rms_m': .25,
    'maximum_point_plane_offset_m': .3, 'duplicate_xy_maximum_z_span_m': .2,
    'maximum_interpolation_xy_span_m': 4., 'long_interpolation_3d_span_m': 4.,
    'long_span_normal_radius_m': 2., 'long_span_minimum_neighbours': 10,
    'long_span_maximum_plane_rms_m': .2, 'long_span_minimum_planarity': .1,
    'long_span_maximum_normal_angle_degrees': 20.,
    'regular_spacings_m': [.5, .25, .125],
    'refinement_construction_distance_m': .5, 'refinement_bin_m': 1.,
    'refinement_minimum_returns': 3, 'refinement_minimum_subcells': 2,
    'refinement_subcell_m': .25, 'refinement_buffer_m': 1.,
    'evaluation_edge_margin_m': 2., 'attribution': '\u00a9 swisstopo',
}


def spatial_split(xy, origin=ORIGIN, block=2., guard=.2):
    """All flights in held-out (bx+2*by)%4==0 blocks; Euclidean buffer."""
    local = np.asarray(xy)-origin
    cell = np.floor(local/block).astype(int)
    held = (cell[:, 0]+2*cell[:, 1]) % 4 == 0
    near = np.zeros(len(cell), dtype=bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            other = cell+[dx, dy]
            is_held = (other[:, 0]+2*other[:, 1]) % 4 == 0
            lo = other*block
            delta = np.maximum(np.maximum(lo-local, local-(lo+block)), 0)
            near |= is_held & (np.linalg.norm(delta, axis=1) < guard)
    result = np.zeros(len(cell), dtype=np.uint8)
    result[near] = 2
    result[held] = 1
    return result


class Bins:
    """Small deterministic spatial index; no new scientific dependency."""
    def __init__(self, points, cell=1.):
        self.points = np.asarray(points)
        self.cell = cell
        self.bins = {}
        for i, key in enumerate(np.floor(self.points/cell).astype(int)):
            self.bins.setdefault(tuple(key), []).append(i)

    def neighbours(self, query, radius):
        lo = np.floor((query-radius)/self.cell).astype(int)
        hi = np.floor((query+radius)/self.cell).astype(int)
        import itertools
        ids = [i for k in itertools.product(*[range(a, b+1) for a, b in zip(lo, hi)])
               for i in self.bins.get(k, ())]
        ids = np.asarray(ids, dtype=int)
        if not len(ids):
            return ids
        return ids[np.linalg.norm(self.points[ids]-query, axis=1) <= radius]


def unique_heights(points, maximum_span=.2):
    """Median coincident observations only when Z agrees; conflicting XY excluded."""
    xy, inverse = np.unique(points[:, :2], axis=0, return_inverse=True)
    order = np.argsort(inverse, kind='stable')
    offsets = np.r_[0, np.cumsum(np.bincount(inverse))]
    result = []
    conflicting = 0
    for i in range(len(xy)):
        z = points[order[offsets[i]:offsets[i+1]], 2]
        if np.ptp(z) > maximum_span:
            conflicting += 1
        else:
            result.append([*xy[i], np.median(z)])
    return np.asarray(result), conflicting


def construction_support(points):
    index = Bins(points, 1.)
    quality = np.full((len(points), 4), np.nan)
    keep = np.zeros(len(points), bool)
    for i, q in enumerate(points):
        ids = index.neighbours(q, PARAMETERS['support_radius_3d_m'])
        quality[i, 0] = len(ids)
        if len(ids) < PARAMETERS['minimum_neighbours']:
            continue
        p = points[ids]
        normal, rms, planarity = retention.fit_plane(p)
        offset = abs((q-p.mean(0)) @ normal)
        quality[i, 1:] = [rms, planarity, offset]
        keep[i] = (rms <= PARAMETERS['maximum_plane_rms_m']
                   and planarity >= PARAMETERS['minimum_planarity']
                   and offset <= PARAMETERS['maximum_point_plane_offset_m'])
    return keep, quality


def support_normals(points):
    """Construction-only 2m spherical planes for long-span orientation screening."""
    index = Bins(points, 2.)
    normals = np.full((len(points), 3), np.nan)
    for i, q in enumerate(points):
        ids = index.neighbours(q, PARAMETERS['long_span_normal_radius_m'])
        if len(ids) < PARAMETERS['long_span_minimum_neighbours']:
            continue
        normal, rms, planarity = retention.fit_plane(points[ids])
        if rms <= PARAMETERS['long_span_maximum_plane_rms_m'] and planarity >= PARAMETERS['long_span_minimum_planarity']:
            normals[i] = normal
    return normals


class Interpolant:
    """Supported piecewise-linear XY Delaunay; no extrapolation or gap completion."""
    def __init__(self, points, xy_span=4., space_span=4., normals=None):
        self.points = np.asarray(points)
        local = self.points[:, :2]-ORIGIN
        self.tri = mtri.Triangulation(local[:, 0], local[:, 1])
        triangles = self.points[self.tri.triangles]
        spans = np.stack([np.linalg.norm(triangles[:, a]-triangles[:, b], axis=1)
                          for a, b in ((0, 1), (1, 2), (2, 0))], axis=1)
        xy_spans = np.stack([np.linalg.norm(triangles[:, a, :2]-triangles[:, b, :2], axis=1)
                             for a, b in ((0, 1), (1, 2), (2, 0))], axis=1)
        self.xy_span = xy_spans.max(1)
        self.space_span = spans.max(1)
        long = self.space_span > space_span
        if normals is None:
            self.long_supported = np.zeros(len(triangles), bool)
        else:
            facet = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
            facet /= np.linalg.norm(facet, axis=1)[:, None]
            alignment = np.abs(np.sum(normals[self.tri.triangles]*facet[:, None, :], axis=2))
            self.long_supported = (alignment >= np.cos(np.radians(PARAMETERS['long_span_maximum_normal_angle_degrees']))).sum(1) >= 2
        self.mask = (self.xy_span > xy_span) | (long & ~self.long_supported)
        self.tri.set_mask(self.mask)
        self.finder = self.tri.get_trifinder()
        self.linear = mtri.LinearTriInterpolator(self.tri, self.points[:, 2])

    def sample(self, xy):
        local = np.asarray(xy)-ORIGIN
        face = self.finder(local[:, 0], local[:, 1])
        z = np.asarray(self.linear(local[:, 0], local[:, 1]).filled(np.nan))
        # 0 unsupported, 1 nearby, 2 longer XY, 3 long 3D plane-supported interpolation.
        support = np.zeros(len(xy), dtype=np.uint8)
        valid = face >= 0
        support[valid] = np.where(self.xy_span[face[valid]] <= .75, 1, 2)
        support[valid & (self.space_span[np.maximum(face, 0)] > 4)] = 3
        span = np.full(len(xy), np.nan)
        span[valid] = self.xy_span[face[valid]]
        return z, support, span


def regular_xy(spacing):
    # Exact 012B cell centres, including both boundary centres at every spacing.
    x = np.arange(BOUNDS[0]+.25, BOUNDS[2]-.25+spacing/2, spacing)
    y = np.arange(BOUNDS[3]-.25, BOUNDS[1]+.25-spacing/2, -spacing)
    xx, yy = np.meshgrid(x, y)
    return np.column_stack([xx.ravel(), yy.ravel()]), (len(y), len(x))


def grid_faces(shape):
    r, c = np.mgrid[:shape[0]-1, :shape[1]-1]
    a = (r*shape[1]+c).ravel()
    b, d, e = a+shape[1], a+1, a+shape[1]+1
    return np.concatenate([np.column_stack([a, b, d]), np.column_stack([d, b, e])])


def refinement_cells(points, distances):
    """Coherent construction-only provider disagreement, 1m buffer; fixed rule."""
    p = points[distances > PARAMETERS['refinement_construction_distance_m']]
    bins = np.floor(p[:, :2]-ORIGIN).astype(int)
    selected = set()
    for key in sorted(set(map(tuple, bins))):
        rows = np.all(bins == key, axis=1)
        sub = np.floor((p[rows, :2]-ORIGIN)/.25).astype(int)
        if rows.sum() >= 3 and len(np.unique(sub, axis=0)) >= 2:
            selected.add(tuple(int(v) for v in key))
    buffered = {(x+dx, y+dy) for x, y in selected
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                if 0 <= x+dx < 60 and 0 <= y+dy < 60}
    return selected, buffered


def adaptive_xy(cells):
    coarse, _ = regular_xy(.5)
    fine, _ = regular_xy(.25)
    ids = np.floor(fine-ORIGIN).astype(int)
    select = np.array([tuple(k) in cells for k in ids])
    return np.unique(np.concatenate([coarse, fine[select]]), axis=0)


class Surface:
    """Finite single-valued triangle surface with exact XY-indexed distance search."""
    def __init__(self, vertices, faces):
        self.vertices = vertices
        self.faces = faces[np.isfinite(vertices[faces, 2]).all(1)]
        self.triangles = vertices[self.faces]
        local = vertices[:, :2]-ORIGIN
        # TriFinder uses all vertices; explicit face list has no overlapping XY faces.
        self.tri = mtri.Triangulation(local[:, 0], local[:, 1], self.faces)
        self.finder = self.tri.get_trifinder()
        self.index = {}
        lo = np.floor(self.triangles[:, :, :2].min(1)-ORIGIN).astype(int)
        hi = np.floor(self.triangles[:, :, :2].max(1)-ORIGIN).astype(int)
        for i, (a, b) in enumerate(zip(lo, hi)):
            for x in range(a[0], b[0]+1):
                for y in range(a[1], b[1]+1):
                    self.index.setdefault((x, y), []).append(i)

    def support(self, xy):
        p = xy-ORIGIN
        return self.finder(p[:, 0], p[:, 1]) >= 0

    def distances(self, points):
        result = np.empty((len(points), 8))
        for i, q in enumerate(points):
            radius = .5
            while True:
                lo = np.floor(q[:2]-ORIGIN-radius).astype(int)
                hi = np.floor(q[:2]-ORIGIN+radius).astype(int)
                ids = sorted({v for x in range(lo[0], hi[0]+1) for y in range(lo[1], hi[1]+1)
                              for v in self.index.get((x, y), ())})
                if ids:
                    d, closest, normal = retention.triangle_closest(q[None, :], self.triangles[ids])
                    if d[0] < radius:
                        result[i] = [d[0], *closest[0], *normal[0], radius]
                        break
                radius *= 2
                if radius > 128:
                    raise ValueError('No finite supported surface within diagnostic search')
        return result


def statistics(a):
    result = retention.stats(a)
    if result['count']:
        result['p75'] = float(np.percentile(a[np.isfinite(a)], 75))
    return result


def report_errors(points, result, support, strata):
    signed = np.sum((points-result[:, 1:4])*result[:, 4:7], axis=1)
    report = {'all_distances_m': statistics(result[:, 0]),
              'signed_nearest_facet_m': statistics(signed),
              'represented_at_query_xy_percent': float(support.mean()*100),
              'represented_distances_m': statistics(result[support, 0]),
              'unrepresented_nearest_edge_distances_m': statistics(result[~support, 0]),
              'by_region': {k: {'distance_m': statistics(result[v, 0]),
                               'xy_coverage_percent': float(support[v].mean()*100) if v.any() else None}
                            for k, v in strata.items()}}
    return report


def source_preservation(repo, data):
    source_catalog(repo, data)
    parents = {}
    for lab, folder in (('012b', 'observed-mountain-v1'), ('012c', 'raw-retention-v1')):
        m = json.loads((repo/f'docs/earth-lab/riffelhorn-{lab}-metadata.json').read_text(encoding='utf-8'))
        root = data/f'experiments/earth-lab/riffelhorn-{lab}/{folder}'
        for p in m['products']:
            if digest(root/p['path']) != p['sha256']:
                raise ValueError(f'Frozen {lab} product differs: '+p['path'])
        parents[lab] = {'identity': m['identity'], 'unchanged_products': len(m['products'])}
    return parents


def coherent_queries(previous, xyz):
    ids = np.load(previous/'summit_cliff-queries.npy')
    q = xyz[ids]
    a = np.load(previous/'summit_cliff-normals-2.npy')
    d = np.load(previous/'summit_cliff-closest.npy')[:, 0]
    reliable = (a[:, 5] >= 10) & (a[:, 4] >= .3) & (a[:, 3] <= .1) & (a[:, 6] <= 10)
    candidate = reliable & (d > .5)
    distance = np.linalg.norm(q[:, None]-q[None, :], axis=2)
    similar = np.abs(a[:, :3] @ a[:, :3].T) > np.cos(np.radians(15))
    neighbours = (distance > 0) & (distance <= 4) & similar
    coherent = candidate & ((neighbours & candidate[None, :]).sum(1) >= 2)
    selected = ids[coherent]
    if len(selected) != 19:
        raise ValueError('012C supported geometry candidate identity differs')
    return selected


def section_lines(triangles, axis, position):
    """Identical exact zero-width plane intersections as 012C, vectorised."""
    segments = []
    edges = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        a, b = triangles[:, i], triangles[:, j]
        hit = ((a[:, axis] <= position) & (position < b[:, axis])) | ((b[:, axis] <= position) & (position < a[:, axis]))
        t = np.full(len(a), np.nan)
        t[hit] = (position-a[hit, axis])/(b[hit, axis]-a[hit, axis])
        edges.append(a+(b-a)*t[:, None])
    e = np.stack(edges, axis=1)
    valid = np.isfinite(e[:, :, 0])
    for face in np.flatnonzero(valid.sum(1) == 2):
        segments.append(e[face, valid[face]])
    return np.asarray(segments)


def diagnostics(out, xyz, split, surfaces, results, evaluation, views, sections):
    colours = {'provider': '#888888', 'regular_0.5': '#b29c00', 'regular_0.25': '#d35020',
               'regular_0.125': '#b700b7', 'adaptive': '#1268ad'}
    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    for ax, spec in zip(axes.ravel(), sections):
        axis = {'northing': 1, 'easting': 0, 'height_ln02_m': 2}[spec['constant_axis']]
        pos = spec['coordinate']
        mask = np.abs(xyz[:, axis]-pos) <= spec['full_thickness_m']/2
        dims = [0, 1] if axis == 2 else [1-axis, 2]
        offset = np.array([ORIGIN[d] if d < 2 else 0 for d in dims])
        for code, label, colour in ((0, 'construction', '#444444'), (1, 'held out', '#10a95c')):
            p = xyz[mask & (split == code)][:, dims]-offset
            ax.scatter(p[:, 0], p[:, 1], s=4, c=colour, label=label)
        for name, surface in surfaces.items():
            lines = section_lines(surface.triangles, axis, pos)
            if len(lines):
                ax.add_collection(LineCollection(lines[:, :, dims]-offset, colors=colours[name], linewidths=.8, label=name))
        ax.autoscale(); ax.set_aspect('equal', adjustable='box')
        ax.set(title=f'{spec["constant_axis"]}={pos:.3f}; raw full thickness 0.2 m',
               xlabel='east offset (m)' if dims[0] == 0 else 'north offset (m)',
               ylabel='LN02 (m)' if dims[1] == 2 else 'north offset (m)')
    axes[0, 0].legend(fontsize=7)
    fig.suptitle('012D | unchanged 012C sections; unsupported gaps remain gaps | © swisstopo')
    fig.tight_layout(); fig.savefig(out/'sections.png', dpi=150); plt.close(fig)
    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    q = xyz[evaluation]
    for ax, (name, surface) in zip(axes.ravel(), surfaces.items()):
        im = ax.scatter(q[:, 0]-ORIGIN[0], q[:, 1]-ORIGIN[1], c=np.minimum(results[name][:, 0], 2),
                        cmap='viridis', vmin=0, vmax=2, s=3)
        ax.set(title=name+' held-out distance (m; colour capped at 2)', aspect='equal', xlabel='east (m)', ylabel='north (m)')
        fig.colorbar(im, ax=ax)
    axes.ravel()[-1].axis('off'); fig.suptitle('All held-out queries; no outlier deletion | © swisstopo')
    fig.tight_layout(); fig.savefig(out/'held-out-maps.png', dpi=130); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 8))
    for code, label, colour in ((0, 'construction', '#555555'), (1, 'held out', '#119955'), (2, '0.2 m guard', '#bb5555')):
        p = xyz[split == code]
        ax.scatter(p[:, 0]-ORIGIN[0], p[:, 1]-ORIGIN[1], s=.3, c=colour, label=label)
    ax.set(aspect='equal', xlabel='east offset (m)', ylabel='north offset (m)', title='Frozen spatial split, all flights together | © swisstopo')
    ax.legend(); fig.tight_layout(); fig.savefig(out/'split.png', dpi=130); plt.close(fig)
    for view in views:
        contact = Image.new('RGB', (1280, 4*754), 'white'); draw = ImageDraw.Draw(contact)
        for row, name in enumerate(('provider', 'regular_0.25', 'regular_0.125', 'adaptive')):
            print('render', view['name'], name, flush=True)
            im = retention.render(surfaces[name].triangles, np.empty((0, 3)),
                                  np.array(view['camera_lv95_ln02_m']), np.array(view['target_lv95_ln02_m']), 'mesh')
            im.save(out/(view['name']+'-'+name+'.png'))
            contact.paste(im, (0, row*754))
            draw.text((8, row*754+725), f'{name} | {view["distance_m"]:g} m | identical camera, flat neutral shade | gaps explicit | © swisstopo', fill='black')
        contact.save(out/(view['name']+'-comparison.png'))


def build(repo, data, out):
    start = time.monotonic()
    parents = source_preservation(repo, data)
    catalog, source = source_catalog(repo, data)
    grid = height_grid(catalog, source, 'swisssurface3d-raster')
    previous = data/'experiments/earth-lab/riffelhorn-012c/raw-retention-v1'
    old = json.loads((previous/'measurements.json').read_text(encoding='utf-8'))
    xyz = np.load(previous/'summit_cliff-xyz.npy')
    records = np.load(previous/'summit_cliff-records.npy')
    out.mkdir(parents=True, exist_ok=True)
    split = spatial_split(xyz[:, :2])
    np.save(out/'split.npy', split)
    train = np.flatnonzero((split == 0) & ((records['class_flags'] & 31) == 2))
    keep, quality = construction_support(xyz[train])
    np.save(out/'construction-support.npy', quality)
    supported = train[keep]
    np.save(out/'construction-used-indices.npy', supported)
    points, conflicts = unique_heights(xyz[supported])
    np.save(out/'interpolation-points.npy', points)
    print('split', retention.counts(split), 'supported', len(points), 'conflicts', conflicts, flush=True)
    normal = support_normals(points)
    np.save(out/'interpolation-support-normals.npy', normal)
    interpolant = Interpolant(points, normals=normal)
    # Adaptive selection never sees held-out points: only supported construction returns.
    construct_baseline = retention.mesh_distances(grid, xyz[supported])
    selected, buffered = refinement_cells(xyz[supported], construct_baseline[0])
    retention.write_json(out/'refinement-cells.json', {'selected': sorted(selected), 'buffered': sorted(buffered)})
    surfaces = {}
    timings = {}
    provider_tri = retention.patch_triangles(grid, BOUNDS)
    xy, shape = regular_xy(.5)
    # Keep native NW/SW/NE diagonal and float32 elevations bit-for-bit.
    r0 = int((1093000-BOUNDS[3])/.5); c0 = int((BOUNDS[0]-2624000)/.5)
    z = grid[r0:r0+shape[0], c0:c0+shape[1]].ravel()
    vertices = np.column_stack([xy, z])
    surfaces['provider'] = Surface(vertices, grid_faces(shape))
    np.testing.assert_array_equal(surfaces['provider'].triangles, provider_tri)
    np.save(out/'provider-vertices.npy', vertices)
    np.save(out/'provider-faces.npy', surfaces['provider'].faces)
    cost = {}
    for name, spacing in [('regular_'+str(s), s) for s in PARAMETERS['regular_spacings_m']] + [('adaptive', None)]:
        candidate_start = time.monotonic()
        xy, shape = regular_xy(spacing) if spacing else (adaptive_xy(buffered), None)
        z, support, span = interpolant.sample(xy)
        vertices = np.column_stack([xy, z])
        if shape:
            faces = grid_faces(shape)
        else:
            p = xy-ORIGIN
            faces = mtri.Triangulation(p[:, 0], p[:, 1]).triangles
        # Do not bridge a masked source gap just because both endpoints are valid.
        face_xy = xy[faces]
        probes = np.concatenate([face_xy.mean(1),
                                 (face_xy[:, 0]+face_xy[:, 1])/2,
                                 (face_xy[:, 1]+face_xy[:, 2])/2,
                                 (face_xy[:, 2]+face_xy[:, 0])/2])
        _, probe_support, _ = interpolant.sample(probes)
        valid_probes = probe_support.reshape(4, len(faces)).all(0)
        faces = faces[valid_probes]
        surface = Surface(vertices, faces)
        surfaces[name] = surface
        np.save(out/(name+'-vertices.npy'), vertices)
        np.save(out/(name+'-faces.npy'), surface.faces)
        np.save(out/(name+'-support.npy'), np.column_stack([support, span]))
        t = surface.triangles
        u, v = t[:, 1, :2]-t[:, 0, :2], t[:, 2, :2]-t[:, 0, :2]
        xy_area = abs(u[:, 0]*v[:, 1]-u[:, 1]*v[:, 0]).sum()/2
        edges = np.concatenate([t[:, a]-t[:, b] for a, b in ((0, 1), (1, 2), (2, 0))])
        normal = np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0])
        inclination = np.degrees(np.arccos(np.clip(abs(normal[:, 2])/np.linalg.norm(normal, axis=1), 0, 1)))
        cost[name] = {'height_samples': len(vertices), 'finite_samples': int(np.isfinite(z).sum()),
                      'triangles': len(t), 'array_bytes': vertices.nbytes+surface.faces.nbytes,
                      'horizontal_represented_area_m2': float(xy_area),
                      'common_cell_centre_footprint_area_m2': 59.5**2,
                      'support_codes': retention.counts(support), 'interpolation_span_m': statistics(span),
                      'edge_3d_length_m': statistics(np.linalg.norm(edges, axis=1)),
                      'edge_occurrences_longer_than_4m': int((np.linalg.norm(edges, axis=1) > 4).sum()),
                      'facet_inclination_degrees': statistics(inclination),
                      'facet_occurrences_steeper_than_89_degrees': int((inclination > 89).sum()),
                      'single_valued': bool(len(np.unique(xy, axis=0)) == len(xy)),
                      'unsupported_faces_removed': int((~valid_probes).sum())+len(faces)-len(t)}
        timings[name+'_generation_seconds'] = time.monotonic()-candidate_start
    interior = (xyz[:, 0] > BOUNDS[0]+2) & (xyz[:, 0] < BOUNDS[2]-2) & (xyz[:, 1] > BOUNDS[1]+2) & (xyz[:, 1] < BOUNDS[3]-2)
    evaluation = np.flatnonzero((split == 1) & interior)
    # Fixed lexicographic construction sample for overfit audit, not population estimate.
    construction = np.flatnonzero((split == 0) & interior)
    order = construction[np.lexsort((xyz[construction, 2], xyz[construction, 1], xyz[construction, 0]))]
    construction = order[np.linspace(0, len(order)-1, min(2048, len(order)), dtype=int)]
    ids19 = coherent_queries(previous, xyz)
    reports = {}; results = {}; revisit = []
    np.save(out/'evaluation-indices.npy', evaluation)
    np.save(out/'construction-audit-indices.npy', construction)
    for name, surface in surfaces.items():
        print('evaluate', name, len(evaluation), flush=True)
        queries = xyz[evaluation]
        result = np.column_stack(retention.mesh_distances(grid, queries)) if name == 'provider' else surface.distances(queries)
        results[name] = result
        np.save(out/(name+'-held-out.npy'), result)
        baseline_strong = results['provider'][:, 0] > .5
        strata = {'lower_height_below_2890': queries[:, 2] < 2890,
                  'upper_height_at_least_2890': queries[:, 2] >= 2890,
                  'provider_distance_over_0.5m': baseline_strong,
                  'provider_distance_at_most_0.1m': results['provider'][:, 0] <= .1,
                  'class_2': (records['class_flags'][evaluation] & 31) == 2,
                  'class_1': (records['class_flags'][evaluation] & 31) == 1}
        closest_provider = results['provider'][:, 1:3]
        strata['provider_nearest_xy_inside_patch'] = ((closest_provider >= BOUNDS[:2]+.25) & (closest_provider <= BOUNDS[2:]-.25)).all(1)
        report = report_errors(queries, result, surface.support(queries[:, :2]), strata)
        report['provider_on_same_represented_query_cohort_m'] = statistics(results['provider'][surface.support(queries[:, :2]), 0])
        cresult = np.column_stack(retention.mesh_distances(grid, xyz[construction])) if name == 'provider' else surface.distances(xyz[construction])
        np.save(out/(name+'-construction-audit.npy'), cresult)
        report['construction_lexicographic_audit'] = report_errors(xyz[construction], cresult, surface.support(xyz[construction, :2]), {})
        actually_used = np.isin(construction, supported)
        report['construction_used_in_fit_distance_m'] = statistics(cresult[actually_used, 0])
        reports[name] = report
        v = np.column_stack(retention.mesh_distances(grid, xyz[ids19])) if name == 'provider' else surface.distances(xyz[ids19])
        revisit.append(v[:, 0])
    candidates19 = []
    for k, i in enumerate(ids19):
        distances = {name: float(revisit[j][k]) for j, name in enumerate(surfaces)}
        represented = {name: bool(s.support(xyz[i:i+1, :2])[0]) for name, s in surfaces.items()}
        status = {}
        for name in list(surfaces)[1:]:
            gain = distances['provider']-distances[name]
            status[name] = ('remains ambiguous: no represented height at query XY' if not represented[name]
                            else 'substantially improved' if gain >= .25 and distances[name] <= distances['provider']*.75
                            else 'partially improved' if gain > .05 else 'not improved')
        candidates19.append({'source_index_012c': int(i), 'xyz_lv95_ln02': xyz[i].tolist(), 'partition': int(split[i]),
                             'distance_m': distances, 'represented_at_xy': represented, 'recovery_status': status})
    ambiguous = []
    for candidate in retention.overlap_candidates(xyz):
        ids = np.asarray(candidate['indices'])
        xy = xyz[ids, :2].mean(0)[None, :]
        # Single-value predictions cannot establish whether two coherent sheets exist.
        values = {}
        for name, surface in surfaces.items():
            f = surface.finder(*(xy-ORIGIN).T)[0]
            if f < 0:
                values[name] = None
            else:
                triangle = surface.triangles[f]
                a = np.column_stack([triangle[:, :2]-ORIGIN, np.ones(3)])
                coef = np.linalg.solve(a, triangle[:, 2])
                values[name] = float(np.r_[xy[0]-ORIGIN, 1] @ coef)
        ambiguous.append({'indices_012c': ids.tolist(), 'xy_lv95': xy[0].tolist(), 'z_min_max_ln02': [float(xyz[ids, 2].min()), float(xyz[ids, 2].max())],
                          'partition_counts': retention.counts(split[ids]), 'predicted_single_height_ln02': values,
                          'conclusion': 'Ambiguity persists: a chosen single-valued interpolation is not independent evidence of topology.'})
    if len(ambiguous) != 9:
        raise ValueError('012C ambiguous group identity changed')
    measurements = {'bounds_lv95': BOUNDS.tolist(), 'height_reference': 'LN02 metres, unchanged',
                    'baseline_native_triangle_array_sha256': hashlib.sha256(provider_tri.tobytes()).hexdigest(),
                    'split': {'counts': retention.counts(split), 'classes_by_partition': {str(k): retention.counts(records['class_flags'][split == k] & 31) for k in (0, 1, 2)},
                              'flights_by_partition': {str(k): retention.counts(records['point_source_id'][split == k]) for k in (0, 1, 2)},
                              'evaluation_count': len(evaluation), 'construction_audit_count': len(construction)},
                    'interpolation': {'eligible_class_2_construction': len(train), 'quality_supported_returns': len(supported), 'unique_xy_support_points': len(points),
                                      'conflicting_duplicate_xy_excluded': conflicts, 'raw_triangles': len(interpolant.mask), 'raw_triangles_masked': int(interpolant.mask.sum())},
                    'refinement': {'unbuffered_area_m2': len(selected), 'buffered_area_m2': len(buffered), 'buffered_patch_area_percent': len(buffered)/36},
                    'cost': cost, 'held_out': reports, 'supported_012c_geometry_candidates': candidates19,
                    'ambiguous_012c_multiple_height_candidates': ambiguous,
                    'views': old['views'], 'sections': old['patches']['summit_cliff']['sections'],
                    'evaluation_note': 'All held-out interior returns including unclassified; provider uses all original observations implicitly. Distances to finite candidates include hole edges; XY coverage reported separately. Construction audit is deterministic 2048-query sample, not matched population.'}
    retention.write_json(out/'measurements.json', measurements)
    diagnostics(out, xyz, split, surfaces, results, evaluation, old['views'], measurements['sections'])
    files = sorted([*out.glob('*.npy'), *out.glob('*.png'), out/'measurements.json', out/'refinement-cells.json'])
    manifest = {'experiment': 'Lab 012D adaptive cliff heightfield', 'parents': parents,
                'processing_script_sha256': digest(Path(__file__)), 'parameters': PARAMETERS,
                'bounds_lv95': BOUNDS.tolist(), 'crs': 'EPSG:2056 LV95, LN02 metres; no transformation, no exaggeration',
                'sources': {'012c_xyz_sha256': digest(previous/'summit_cliff-xyz.npy'), '012c_records_sha256': digest(previous/'summit_cliff-records.npy')},
                'toolchain': {'python': sys.version.split()[0], **{k: importlib.metadata.version(k) for k in ('numpy', 'rasterio', 'matplotlib', 'Pillow')}},
                'products': [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files]}
    manifest['identity'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    retention.write_json(out/'manifest.json', manifest)
    timings['total_seconds'] = time.monotonic()-start
    retention.write_json(out/'performance.json', timings)  # intentionally noncanonical wall-clock evidence
    print('IDENTITY', manifest['identity'], 'seconds', time.monotonic()-start, flush=True)
    return manifest


def verify(repo, data, out):
    parents = source_preservation(repo, data)
    m = json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    identity = m.pop('identity')
    if hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest() != identity:
        raise ValueError('Manifest identity changed')
    if m['parents'] != parents or m['processing_script_sha256'] != digest(Path(__file__)):
        raise ValueError('Derivation identity changed')
    for p in m['products']:
        if digest(out/p['path']) != p['sha256']:
            raise ValueError('Changed derived product '+p['path'])
    previous = data/'experiments/earth-lab/riffelhorn-012c/raw-retention-v1'
    xyz = np.load(previous/'summit_cliff-xyz.npy')
    split = np.load(out/'split.npy')
    np.testing.assert_array_equal(spatial_split(xyz[:, :2]), split)
    used = np.load(out/'construction-used-indices.npy')
    if not (split[used] == 0).all():
        raise ValueError('Held-out or buffer point used in construction')
    held_index = Bins(xyz[split == 1, :2], 2.)
    if any(len(held_index.neighbours(q, .2-1e-7)) for q in xyz[split == 0, :2]):
        raise ValueError('Spatial guard violated')
    catalog, source = source_catalog(repo, data)
    grid = height_grid(catalog, source, 'swisssurface3d-raster')
    ids = np.load(out/'evaluation-indices.npy')
    sampled = np.linspace(0, len(ids)-1, 16, dtype=int)
    for name in ('provider', 'regular_0.5', 'regular_0.25', 'regular_0.125', 'adaptive'):
        if name == 'provider':
            result = np.column_stack(retention.mesh_distances(grid, xyz[ids[sampled]]))
        else:
            vertices = np.load(out/(name+'-vertices.npy'))
            surface = Surface(vertices, np.load(out/(name+'-faces.npy')))
            if len(np.unique(vertices[:, :2], axis=0)) != len(vertices):
                raise ValueError('Multiple heights at same XY')
            result = surface.distances(xyz[ids[sampled]])
            # Independent full-face search validates the spatial-index stopping bound.
            for j in (0, len(sampled)-1):
                best = np.inf
                for offset in range(0, len(surface.triangles), 4096):
                    d, _, _ = retention.triangle_closest(xyz[ids[sampled[j]]][None, :], surface.triangles[offset:offset+4096])
                    best = min(best, d[0])
                np.testing.assert_allclose(result[j, 0], best, atol=1e-8, rtol=0)
        np.testing.assert_allclose(result, np.load(out/(name+'-held-out.npy'))[sampled], atol=1e-8, rtol=0)
    old = json.loads((previous/'measurements.json').read_text(encoding='utf-8'))
    measurements = json.loads((out/'measurements.json').read_text(encoding='utf-8'))
    if old['views'] != measurements['views'] or old['patches']['summit_cliff']['sections'] != measurements['sections']:
        raise ValueError('Camera or sections differ')
    baseline = Surface(np.load(out/'provider-vertices.npy'), np.load(out/'provider-faces.npy'))
    np.testing.assert_array_equal(baseline.triangles, retention.patch_triangles(grid, BOUNDS))
    frames = 0
    for view in measurements['views']:
        screen, _ = retention.project(np.array(view['target_lv95_ln02_m'])[None, :],
                                      np.array(view['camera_lv95_ln02_m']), np.array(view['target_lv95_ln02_m']))
        np.testing.assert_allclose(screen, [[640, 360]], atol=1e-8)
        for name in ('provider', 'regular_0.25', 'regular_0.125', 'adaptive'):
            with Image.open(out/(view['name']+'-'+name+'.png')) as frame:
                if frame.size != (1280, 720) or np.asarray(frame).std() < 1:
                    raise ValueError('Frame dimensions/content changed')
            frames += 1
    return {'result': 'PASS', 'identity': identity, 'source_originals': 16, 'source_las': 4,
            'frozen_012b_products': 209, 'frozen_012c_products': 46, 'products': len(m['products']),
            'repeated_split_points': len(xyz), 'repeated_distance_queries': 80,
            'global_bruteforce_candidate_queries': 8, 'guard_m': .2,
            'exact_baseline_triangles': len(baseline.triangles), 'diagnostic_frames': frames,
            'unchanged_cameras': 3, 'unchanged_sections': 6}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    data = resolve_storage_roots(repository_root=repo, require_data=True).data
    out = data/'experiments/earth-lab/riffelhorn-012d/adaptive-heightfield-v1'
    result = verify(repo, data, out) if args.verify else build(repo, data, out)
    print(json.dumps(result if args.verify else {'identity': result['identity']}, indent=2), flush=True)
