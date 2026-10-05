"""Bounded Swiss parent diagnostic. Never imported by production startup."""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import time
import numpy as np
import rasterio
from pyproj import Transformer
import riffelhorn_support as sp
import riffelhorn_terrain as rt
import copernicus_common as cp
import terrain_hierarchy as h

VERSION = 'riffelhorn-regional-parents-v1'
PRODUCT = 'derived/atlas/riffelhorn/' + VERSION
EXPERIMENT = 'experiments/atlas/' + VERSION
REPO = Path(__file__).resolve().parents[2]
PLAN = REPO / 'docs/atlas/regional-parent-plan.json'


def aggregate(values, counts):
    """Observed-subset mean plus exact support count; not mixed DEM fusion.

    Partial values describe only the supported subset, never the complete cell.
    No finite height is assigned to count zero. Accumulate unencoded float64.
    """
    if values.shape != counts.shape or values.ndim != 2 or any(n % 2 for n in values.shape):
        raise ValueError('Aligned even heights/support arrays required')
    if np.any(counts < 0) or np.any((counts > 0) & ~np.isfinite(values)):
        raise ValueError('Invalid observed support')
    shape = (values.shape[0] // 2, 2, values.shape[1] // 2, 2)
    total = counts.astype('uint32').reshape(shape).sum(axis=(1, 3), dtype='uint32')
    signal = np.where(counts > 0, values, 0).astype('float64') * counts
    sums = signal.reshape(shape).sum(axis=(1, 3))
    mean = np.divide(sums, total, out=np.full(total.shape, np.nan), where=total > 0)
    return mean, total


def support_cells(z, x0, y0, values, inverse):
    """Conservative sampled cell footprint test, not centre-in-coverage."""
    span = rt.WORLD / (256 * 2 ** z)
    xx = -rt.WORLD / 2 + (x0 * 256 + np.arange(values.shape[1])) * span
    yy = rt.WORLD / 2 - (y0 * 256 + np.arange(values.shape[0])) * span
    valid = np.isfinite(values)
    for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1), (.5, 0), (.5, 1), (0, .5), (1, .5)]:
        e, n = inverse.transform(np.broadcast_to(xx + dx * span, values.shape), np.broadcast_to((yy - dy * span)[:, None], values.shape))
        valid &= (e >= sp.BOUNDS[0] + .5) & (e <= sp.BOUNDS[2] - .5) & (n >= sp.BOUNDS[1] + .5) & (n <= sp.BOUNDS[3] - .5)
    return valid.astype('uint32')


def parent_grid(values, counts, z):
    """Pad support with zero, heights with NaN, to globally aligned parent tiles."""
    cx0, _, cy0, _, _, _ = sp.hierarchy(z + 1)
    x0, _, y0, _, shape, _ = sp.hierarchy(z)
    size = (shape[0] * 2, shape[1] * 2)
    v = np.full(size, np.nan); c = np.zeros(size, dtype='uint32')
    row, col = cy0 * 256 - y0 * 512, cx0 * 256 - x0 * 512
    v[row:row + values.shape[0], col:col + values.shape[1]] = values
    c[row:row + counts.shape[0], col:col + counts.shape[1]] = counts
    return aggregate(v, c)


def prepare(data, suffix=''):
    start = time.perf_counter()
    swiss = sp.verify(data); common = cp.verify(data)
    plan = json.loads(PLAN.read_text())
    if plan['products'] != {'swiss': swiss['identity'], 'common': common['identity']}:
        raise ValueError('Frozen inputs differ')
    out = data / (PRODUCT + suffix)
    if (out / 'manifest.json').exists():
        raise ValueError('Immutable build exists; verify or explicit named sibling')
    out.mkdir(parents=True, exist_ok=True)
    sp.build_vrt(data, out, sp.source_record(data))
    forward = Transformer.from_crs(2056, 3857, always_xy=True, allow_ballpark=False)
    forward.transform(*sp.CENTRE)
    inverse = Transformer.from_crs(3857, 2056, always_xy=True, allow_ballpark=False)
    with rasterio.Env(GDAL_CACHEMAX=256 * 1024 * 1024), rasterio.open(out / 'source-mosaic.vrt') as ds:
        warped, (x0, _, y0, _) = sp.warped(ds, 14, forward)
        with warped:
            values = warped.read(1).astype('float64')
    counts = support_cells(14, x0, y0, values, inverse)
    values[counts == 0] = np.nan
    files = []; levels = []; max_quant = 0.; fine_matches = 0
    originals = {f['path']: f for f in swiss['files']}
    for z in range(14, 9, -1):
        if z < 14:
            values, counts = parent_grid(values, counts, z)
        x0, x1, y0, y1, shape, _ = sp.hierarchy(z)
        if tuple(shape) != values.shape:
            raise ValueError('Grid alignment mismatch')
        full = 4 ** (14 - z)
        raster = out / f'fields/z{z}.npz'; raster.parent.mkdir(exist_ok=True)
        np.savez_compressed(raster, heights=values, counts=counts)
        files.append({'path': raster.relative_to(out).as_posix(), 'sha256': rt.digest(raster), 'bytes': raster.stat().st_size})
        delivered = 0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rs = slice((y - y0) * 256, (y - y0 + 1) * 256)
                cs = slice((x - x0) * 256, (x - x0 + 1) * 256)
                a, c = values[rs, cs], counts[rs, cs]
                if not np.all(c == full) or not sp.tile_supported(z, x, y, inverse):
                    continue
                body = rt.encode(a)
                max_quant = max(max_quant, float(np.max(abs(rt.decode(body) - a))))
                key = f'tiles/{z}/{x}/{y}.png'
                p = out / key; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(body)
                files.append({'path': key, 'sha256': rt.digest(p), 'bytes': len(body)})
                delivered += 1
                if z == 14 and key in originals:
                    if rt.digest(p) != originals[key]['sha256']:
                        raise ValueError('Unencoded basis does not reproduce original Swiss z14 bytes')
                    fine_matches += 1
        levels.append({'zoom': z, 'extentTiles': [x0, x1, y0, y1], 'shape': list(shape), 'fullCount': full,
                       'completeCells': int((counts == full).sum()), 'partialCells': int(((counts > 0) & (counts < full)).sum()),
                       'unsupportedCells': int((counts == 0).sum()), 'supportEquivalentCells': float(counts.sum() / full),
                       'completeDeliveryTiles': delivered})
        print('PARENTS', z, levels[-1], flush=True)
    manifest = {'version': VERSION, 'parents': plan['products'], 'sourceIdentity': swiss['sourceIdentity'],
                'planSha256': rt.repository_text_digest(PLAN), 'toolSha256': rt.repository_text_digest(__file__),
                'basis': 'unencoded Swiss z14 GDAL average; same warp as original; no vertical operation',
                'parentRule': 'recursive supported 2x2 sample sum/count; float64; Mercator base-cell area',
                'height': 'LN02 retained; no common contributor', 'levels': levels, 'files': files,
                'basisTilesByteIdentical': fine_matches, 'maxQuantizationM': max_quant,
                'software': {'numpy': np.__version__, 'rasterio': rasterio.__version__, 'gdal': rasterio.__gdal_version__},
                'sourceVrtSha256': rt.repository_text_digest(out / 'source-mosaic.vrt')}
    manifest['identity'] = rt.stable_id(manifest)
    sp.save(out / 'manifest.json', manifest)
    sp.save(data / EXPERIMENT / ('generation' + suffix + '.json'), {'identity': manifest['identity'], 'seconds': time.perf_counter() - start,
        'bytes': sum(f['bytes'] for f in files), 'tileBytes': sum(f['bytes'] for f in files if f['path'].startswith('tiles/'))})
    print('PRODUCT', manifest['identity'], flush=True)


def verify(data, suffix='', parents=True):
    if parents:
        sp.verify(data); cp.verify(data)
    out = data / (PRODUCT + suffix); m = json.loads((out / 'manifest.json').read_text())
    if m['identity'] != rt.stable_id({k: v for k, v in m.items() if k != 'identity'}) or m['planSha256'] != rt.repository_text_digest(PLAN) or m['toolSha256'] != rt.repository_text_digest(__file__):
        raise ValueError('Diagnostic identity drift')
    for f in m['files']:
        if rt.digest(out / f['path']) != f['sha256']:
            raise ValueError('Derived output drift: ' + f['path'])
    for row in m['levels']:
        with np.load(out / f"fields/z{row['zoom']}.npz") as ds:
            a, c = ds['heights'], ds['counts']
            if np.any(c > row['fullCount']) or np.any((c > 0) & ~np.isfinite(a)) or np.any((c == 0) & np.isfinite(a)):
                raise ValueError('Support/value semantics drift')
    return m


class Stream(h.Hierarchy):
    """Isolated stream: original H1 control or supported derived regional parents.

    The inherited common adapter uses a separate evaluation cache, never edits
    either parent product or the previous hierarchy experiment.
    """
    def __init__(self, data):
        self.parents = verify(data, parents=True)
        super().__init__(data, gate=14, suffix='-regional-parent-control', verify=False)
        self.parent_files = {f['path']: f for f in self.parents['files'] if f['path'].startswith('tiles/')}

    def tile(self, strategy, z, x, y):
        if strategy not in ['control', 'regional']:
            raise ValueError('Unknown parent diagnostic strategy')
        key = f'tiles/{z}/{x}/{y}.png'
        if strategy == 'regional' and z in [12, 13] and key in self.parent_files:
            p = self.data / PRODUCT / key
            row = self.parent_files[key]
            if rt.digest(p) != row['sha256']:
                raise ValueError('Derived tile drift')
            return p.read_bytes(), {'contributor': 1, 'heightReference': 'LN02', 'method': 'Swiss-derived recursive parent', 'productIdentity': self.parents['identity']}
        body, row = super().tile('H1', z, x, y)
        return body, {**row, 'productIdentity': self.swiss['identity'] if row['contributor'] else self.common['identity']}


def serve(data, port):
    import re
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    stream = Stream(data)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            match = re.fullmatch(r'/tiles/(control|regional)/(\d+)/(\d+)/(\d+)\.png', self.path)
            try:
                if not match:
                    raise FileNotFoundError('Unsupported route')
                body, row = stream.tile(match[1], *map(int, match.groups()[1:])); status = 200
            except FileNotFoundError:
                body, row, status = b'', {}, 404
            except Exception as e:
                print('ERROR', repr(e), flush=True); body, row, status = b'', {}, 500
            self.send_response(status)
            for key, value in {'Access-Control-Allow-Origin': '*', 'Access-Control-Expose-Headers': 'X-Meridian-Contributor,X-Meridian-Height,X-Meridian-Product', 'Content-Type': 'image/png', 'Content-Length': str(len(body)), 'Cache-Control': 'public,max-age=3600' if status == 200 else 'no-store'}.items():
                self.send_header(key, value)
            if row:
                for key, value in {'X-Meridian-Contributor': row['contributor'], 'X-Meridian-Height': row['heightReference'], 'X-Meridian-Product': row['productIdentity']}.items():
                    self.send_header(key, str(value))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
        def log_message(self, *args):
            pass
    print('SERVING', port, stream.parents['identity'], flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('command', choices=['prepare', 'verify', 'serve']); p.add_argument('--suffix', default=''); p.add_argument('--port', type=int, default=4184)
    args = p.parse_args()
    if args.suffix and not __import__('re').fullmatch('-[a-z0-9-]+', args.suffix):
        raise ValueError('Explicit named sibling required')
    root = rt.resolve_storage_roots(require_data=True).data
    if args.command == 'prepare':
        prepare(root, args.suffix)
    elif args.command == 'verify':
        print('VERIFIED', verify(root, args.suffix)['identity'])
    else:
        serve(root, args.port)
