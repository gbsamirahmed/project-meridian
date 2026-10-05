"""Deterministic numerical diagnosis, never a terrain reconciliation."""
import json
from pathlib import Path
import numpy as np
from pyproj import Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import regional_parents as p

rt, sp = p.rt, p.sp


def stats(a):
    a = np.asarray(a); a = a[np.isfinite(a)]
    if not a.size:
        return {'n': 0}
    med = float(np.median(a))
    return {'n': int(a.size), 'mean': float(a.mean()), 'median': med, 'nmad': float(1.4826 * np.median(abs(a - med))),
            'rms': float(np.sqrt(np.mean(a * a))), 'min': float(a.min()), 'max': float(a.max()),
            'p05': float(np.quantile(a, .05)), 'p95': float(np.quantile(a, .95))}


def sample_field(a, z, e, n):
    x0, _, y0, _, _, _ = sp.hierarchy(z)
    x, y = Transformer.from_crs(2056, 3857, always_xy=True).transform(e, n)
    gx = (x + rt.WORLD / 2) / rt.WORLD * 256 * 2 ** z - .5 - x0 * 256
    gy = (rt.WORLD / 2 - y) / rt.WORLD * 256 * 2 ** z - .5 - y0 * 256
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int)
    wx, wy = gx - ix, gy - iy
    return (1 - wy) * ((1 - wx) * a[iy, ix] + wx * a[iy, ix + 1]) + wy * ((1 - wx) * a[iy + 1, ix] + wx * a[iy + 1, ix + 1])


def sample_stream(stream, strategy, z, e, n):
    x, y = Transformer.from_crs(2056, 3857, always_xy=True).transform(e, n)
    gx = (x + rt.WORLD / 2) / rt.WORLD * 256 * 2 ** z - .5
    gy = (rt.WORLD / 2 - y) / rt.WORLD * 256 * 2 ** z - .5
    ix, iy = np.floor(gx).astype(int), np.floor(gy).astype(int); wx, wy = gx - ix, gy - iy
    values = []
    for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        px, py = ix + dx, iy + dy; a = np.empty(px.shape)
        for tx, ty in set(zip((px // 256).ravel(), (py // 256).ravel())):
            m = (px // 256 == tx) & (py // 256 == ty)
            body, _ = p.h.Hierarchy.tile(stream, 'common', z, int(tx), int(ty)) if strategy == 'common' else stream.tile(strategy, z, int(tx), int(ty))
            heights = rt.decode(body); a[m] = heights[py[m] % 256, px[m] % 256]
        values.append(a)
    a, b, c, d = values
    return (1 - wy) * ((1 - wx) * a + wx * b) + wy * ((1 - wx) * c + wx * d)


def run(data):
    m = p.verify(data, parents=True); stream = p.Stream(data)
    out = data / p.EXPERIMENT; out.mkdir(parents=True, exist_ok=True)
    fields = {}; counts = {}
    for z in range(10, 15):
        with np.load(data / p.PRODUCT / f'fields/z{z}.npz') as f:
            fields[z], counts[z] = f['heights'], f['counts']
    y, x = np.mgrid[:400, :400]
    e, n = 2620000 + (x + .5) * 25, 1097000 - (y + .5) * 25
    ev, nv = e[::4, ::4], n[::4, ::4]
    inside = np.hypot(ev - 2625000, nv - 1092000) <= 1500
    ev, nv = ev[inside], nv[inside]
    result = {'baseline': json.loads(p.PLAN.read_text())['baseline'], 'productIdentity': m['identity'],
              'heightPolicy': 'Swiss LN02 minus common EGM2008; no accepted transformation',
              'levels': {}, 'aggregationResiduals': {}, 'protectedSamples': int(len(ev)),
              'LOD': {}, 'servedLOD': {}, 'boundaries': {}, 'originalProductPreserved': True,
              'protectedPointSameLevel': {}}
    inverse = Transformer.from_crs(3857, 2056, always_xy=True)
    all_overlap = np.load(data / 'experiments/atlas/global-reference-assessment-v1/fields-and-mask.npz')
    expected = json.loads((p.REPO / 'docs/atlas/global-reference-measurements.json').read_text())['arrayHashes']
    import hashlib
    for key in all_overlap.files:
        if hashlib.sha256(all_overlap[key].tobytes()).hexdigest() != expected[key]:
            raise ValueError('Retained overlap mask drift')
    fig, axes = plt.subplots(2, 5, figsize=(18, 8))
    previous = None
    for z in range(10, 15):
        a, c = fields[z], counts[z]; full_count = 4 ** (14 - z); full = c == full_count
        x0, x1, y0, y1, shape, extent = sp.hierarchy(z)
        yy, xx = np.mgrid[:shape[0], :shape[1]]
        resolution = rt.WORLD / (256 * 2 ** z)
        mx = -rt.WORLD / 2 + (xx + x0 * 256 + .5) * resolution
        my = rt.WORLD / 2 - (yy + y0 * 256 + .5) * resolution
        ee, nn = inverse.transform(mx, my)
        common = np.empty(a.shape)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                body, _ = p.h.Hierarchy.tile(stream, 'common', z, tx, ty)
                common[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = rt.decode(body)
        diff = a - common
        sectors = {name: stats(diff[full & mask]) for name, mask in [('NW', (ee < 2625000) & (nn >= 1092000)), ('NE', (ee >= 2625000) & (nn >= 1092000)), ('SW', (ee < 2625000) & (nn < 1092000)), ('SE', (ee >= 2625000) & (nn < 1092000))]}
        iy = np.clip(((1097000 - nn) / 25).astype(int), 0, 399)
        ix = np.clip(((ee - 2620000) / 25).astype(int), 0, 399)
        stable = all_overlap['primaryMask'][iy, ix].astype(bool)
        slope = all_overlap['slope'][iy, ix]
        rough = abs(a - (np.roll(a, 1, axis=0) + np.roll(a, -1, axis=0) + np.roll(a, 1, axis=1) + np.roll(a, -1, axis=1)) / 4)
        rough_valid = full & np.roll(full, 1, axis=0) & np.roll(full, -1, axis=0) & np.roll(full, 1, axis=1) & np.roll(full, -1, axis=1)
        # Ground area estimate at cell centres; exact Mercator support counts remain separate.
        ground_pixel_area = resolution ** 2 / np.cosh(my / (rt.WORLD / (2 * np.pi))) ** 2
        lev = next(r for r in m['levels'] if r['zoom'] == z)
        result['levels'][str(z)] = {**lev, 'sameLevelSwissMinusCommon': stats(diff[full]), 'partialSupportedSubsetMinusCommon': stats(diff[(c > 0) & ~full]),
            'protectedArea': stats(diff[full & (np.hypot(ee - 2625000, nn - 1092000) <= 1500)]), 'sectors': sectors,
            'retainedStableCentreDiagnostic': stats(diff[full & stable]),
            'slopeCentreStrata': {f'{lo}-{hi}': stats(diff[full & (slope >= lo) & (slope < hi)]) for lo, hi in [(0, 15), (15, 35), (35, 90)]},
            'roughnessStrata': {f'{lo}-{hi}': stats(diff[rough_valid & (rough >= lo) & (rough < hi)]) for lo, hi in [(0, 1), (1, 5), (5, 10000)]},
            'tileEnvelopeMercatorM2': float(a.size * resolution ** 2), 'completeCellMercatorM2': float(full.sum() * resolution ** 2),
            'partialCellMercatorM2': float(((c > 0) & ~full).sum() * resolution ** 2), 'observedAreaEquivalentMercatorM2': float(c.sum() / full_count * resolution ** 2),
            'observedAreaEquivalentApproxGroundM2': float(np.sum(ground_pixel_area * c / full_count)),
            'unsupportedEnvelopeFraction': float(np.mean(c == 0)), 'supportBoundsLV95': list(sp.BOUNDS),
            'groundPostingAtBenchmarkM': float(resolution * np.cos(np.deg2rad(45.97910794)))}
        if z < 14:
            expected_a, expected_c = p.parent_grid(fields[z + 1], counts[z + 1], z)
            np.testing.assert_array_equal(c, expected_c)
            result['aggregationResiduals'][str(z)] = stats((a - expected_a)[c > 0])
            if result['aggregationResiduals'][str(z)]['max'] != 0:
                raise ValueError('Aggregation drift')
        vals = sample_field(np.where(full, a, np.nan), z, ev, nv)
        if not np.all(np.isfinite(vals)):
            raise ValueError('Protected samples lack complete footprint')
        # Fixed coordinates avoid confusing a changing coarse-cell population with convergence.
        common_point = sample_stream(stream, 'common', z, ev, nv)
        result['protectedPointSameLevel'][str(z)] = stats(vals - common_point)
        if previous is not None:
            result['LOD'][f'{z-1}-{z}'] = stats(vals - previous)
        previous = vals
        view = np.where(full, diff, np.nan)
        ax = axes[0, z - 10]; im = ax.imshow(view, cmap='RdBu_r', vmin=-50, vmax=50); ax.set_title(f'z{z}: Swiss−common (m)'); ax.axis('off')
        axes[1, z - 10].imshow(c / full_count, vmin=0, vmax=1, cmap='viridis'); axes[1, z - 10].set_title('Support fraction, not confidence'); axes[1, z - 10].axis('off')
    fig.colorbar(im, ax=list(axes[0]), shrink=.5); fig.savefig(out / 'coarse-difference-support.png', dpi=130); plt.close(fig)
    for strategy in ['control', 'regional']:
        previous = None; rows = {}
        for z in range(11, 19):
            vals = sample_stream(stream, strategy, z, ev, nv)
            if previous is not None:
                rows[f'{z-1}-{z}'] = stats(vals - previous)
            previous = vals
        result['servedLOD'][strategy] = rows
    result['protectedFineModification'] = {str(z): stats(sample_stream(stream, 'regional', z, ev, nv) - sample_stream(stream, 'control', z, ev, nv)) for z in [14, 15, 16, 17, 18]}
    result['basisEncodingVersusOriginalZ14'] = stats(sample_field(fields[14], 14, ev, nv) - sample_stream(stream, 'regional', 14, ev, nv))
    # Deterministic frontier strips; characterize, never tune the spatial join.
    for z in [12, 13]:
        tiles = {(int(k.split('/')[2]), int(k.split('/')[3].split('.')[0])) for k in stream.parent_files if k.startswith(f'tiles/{z}/')}
        edges = [(x, y, dx, dy) for x, y in tiles for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)] if (x + dx, y + dy) not in tiles]
        rows = []
        for x, y, dx, dy in sorted(edges):
            a = rt.decode(stream.tile('regional', z, x, y)[0]); b = rt.decode(stream.tile('regional', z, x + dx, y + dy)[0])
            ca = rt.decode(p.h.Hierarchy.tile(stream, 'common', z, x, y)[0]); cb = rt.decode(p.h.Hierarchy.tile(stream, 'common', z, x + dx, y + dy)[0])
            def jump(a, b):
                return b[:, 0] - a[:, -1] if dx == 1 else a[:, 0] - b[:, -1] if dx == -1 else b[0, :] - a[-1, :] if dy == 1 else a[0, :] - b[-1, :]
            rows.append({'tile': [z, x, y], 'direction': [dx, dy], 'adjacentCell': stats(jump(a, b)), 'commonAdjacentControl': stats(jump(ca, cb)), 'excessOverCommon': stats(jump(a, b) - jump(ca, cb))})
        result['boundaries'][str(z)] = rows
    # Retain exact sampled profiles as a separate external product, with identical coordinates for all levels.
    es = 2625000 + np.arange(-1400, 1401, 25); ns = np.full(es.shape, 1092000)
    profiles = {str(z): sample_field(fields[z], z, es, ns).tolist() for z in range(10, 15)}
    sp.save(out / 'profiles.json', {'LV95East': es.tolist(), 'LV95North': ns.tolist(), 'SwissLN02': profiles})
    fig, ax = plt.subplots(figsize=(12, 4))
    for z, v in profiles.items():
        ax.plot(es - 2625000, v, label='Swiss z' + z)
    ax.legend(); ax.set_xlabel('LV95 east offset (m)'); ax.set_ylabel('LN02 elevation (m)'); ax.set_title('Protected interior: same-source coarse summaries'); fig.tight_layout(); fig.savefig(out / 'parent-profiles.png', dpi=140); plt.close(fig)
    result['profileSha256'] = rt.digest(out / 'profiles.json')
    sp.save(out / 'measurements.json', result); sp.save(p.REPO / 'docs/atlas/regional-parent-measurements.json', result)
    print(json.dumps({'LOD': result['LOD'], 'servedLOD': result['servedLOD'], 'levelSummary': {z: r['sameLevelSwissMinusCommon'] for z, r in result['levels'].items()}}, indent=2))


if __name__ == '__main__':
    run(rt.resolve_storage_roots(require_data=True).data)
