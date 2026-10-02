"""012G: source appearance audit; immutable terrain and imagery remain evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from pathlib import Path
import shutil
import time
import numpy as np
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo
import riffelhorn_012b as mountain
import riffelhorn_012f as lighting
from meridian_paths import resolve_storage_roots

VIEWS = ('overview', 'riffelhorn_oblique', 'alpine_path', 'riffelhorn_structure')
STATES = ('original_unlit', 'original_lit', 'normalised_lit', 'density')
ROOT = 'experiments/earth-lab/riffelhorn-012g/projection-illumination-v1'
LUMA = np.array([.2126, .7152, .0722])


def write(path, value):
    with path.open('w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, indent=2, allow_nan=False)+'\n')


def preserve(repo, data):
    parents = lighting.preserve(repo, data)
    m = json.loads((repo/'docs/earth-lab/riffelhorn-012f-metadata.json').read_text(encoding='utf-8'))
    root = data/'experiments/earth-lab/riffelhorn-012f/terrain-lighting-v1'
    for p in m['products']:
        if mountain.digest(root/p['path']) != p['sha256']: raise ValueError('012F product changed: '+p['path'])
    parents['012f'] = {'identity': m['identity'], 'unchanged_products': len(m['products'])}
    f_inputs = json.loads((root/'lab012f-inputs.json').read_text(encoding='utf-8'))
    for p in f_inputs['copied_assets']:
        if mountain.digest(root/'unreal'/p['path']) != p['sha256']: raise ValueError('012F frozen scene changed')
    existing = data/ROOT/'lab012g-inputs.json'
    if existing.exists():
        for p in json.loads(existing.read_text(encoding='utf-8'))['copied_assets']:
            if '/Lab012F/' in p['path'] and mountain.digest(root/'unreal'/p['path']) != p['sha256']:
                raise ValueError('012F compiled lighting material changed')
    return parents


def decode(rgb):
    x = np.asarray(rgb, dtype=np.float32)/255
    return np.where(x <= .04045, x/12.92, ((x+.055)/1.055)**2.4)


def encode(linear):
    x = np.clip(linear, 0, 1)
    return np.rint(np.where(x <= .0031308, 12.92*x, 1.055*x**(1/2.4)-.055)*255).astype(np.uint8)


def blur(field, sigma):
    """Explicit separable Gaussian, +/-3 sigma, edge replication; no new dependency."""
    radius = int(np.ceil(3*sigma)); x = np.arange(-radius, radius+1)
    kernel = np.exp(-.5*(x/sigma)**2); kernel /= kernel.sum()
    result = np.asarray(field, dtype=np.float64)
    for axis in (0, 1):
        padding = [(0, 0)]*2; padding[axis] = (radius, radius)
        padded = np.pad(result, padding, mode='edge'); result = np.zeros_like(result)
        for i, weight in enumerate(kernel):
            slices = [slice(None), slice(None)]; slices[axis] = slice(i, i+field.shape[axis])
            result += weight*padded[tuple(slices)]
    return result


def interpolate(field, x, y, spacing=2.):
    """Bilinear field sampled at pixel centres; edge clamp is explicit."""
    c = np.clip(np.asarray(x)/spacing-.5, 0, field.shape[1]-1)
    r = np.clip(np.asarray(y)/spacing-.5, 0, field.shape[0]-1)
    ci = np.minimum(np.floor(c).astype(int), field.shape[1]-2)
    ri = np.minimum(np.floor(r).astype(int), field.shape[0]-2)
    fc, fr = c-ci, r-ri
    return ((1-fr)*((1-fc)*field[ri, ci]+fc*field[ri, ci+1])+
            fr*((1-fc)*field[ri+1, ci]+fc*field[ri+1, ci+1]))


def normalise(rgb, gain):
    """Common linear RGB gain, limited to avoid channel clipping; black stays black."""
    linear = decode(rgb)
    actual = np.minimum(gain, 1/np.maximum(linear.max(-1), 1e-12))
    return encode(linear*actual[..., None]), actual


def density_from_gradients(dx, dy):
    cosine = 1/np.sqrt(1+dx*dx+dy*dy)
    return cosine, 16*cosine, 100*cosine, .25/cosine


def rays(view, pixels, dimensions=(1920, 1080)):
    p, t = np.array(view['position_m'], dtype=float), np.array(view['target_m'], dtype=float)
    forward = t-p; forward /= np.linalg.norm(forward)
    right = np.cross([0., 0., 1.], forward)
    if np.linalg.norm(right) < 1e-10: right = np.array([0., 1., 0.])
    else: right /= np.linalg.norm(right)
    up = np.cross(forward, right); w, h = dimensions
    uv = (np.asarray(pixels)+.5)/[w, h]
    direction = forward+2*np.tan(np.radians(25))*((uv[:, 0]-.5)[:, None]*right+
                                                 ((.5-uv[:, 1])*h/w)[:, None]*up)
    return p, direction/np.linalg.norm(direction, axis=1)[:, None]


def raycast(grid, origin, directions, spacing=.5, centre=.25, vertical_origin=2500.):
    """Exact first intersection with the 012B diagonal triangles using XY DDA.

    This is a read-only source-tracing diagnostic, not another rendered terrain.
    Positions are local east/south/up metres. No bilinear-height approximation.
    """
    d = np.asarray(directions, dtype=float); n = len(d)
    inv = np.divide(1., d[:, :2], out=np.full((n, 2), np.inf), where=np.abs(d[:, :2]) > 1e-14)
    far_xy = centre+(np.array(grid.shape[::-1])-1)*spacing
    with np.errstate(invalid='ignore'):
        a = (centre-origin[:2])*inv; b = (far_xy-origin[:2])*inv
    parallel = np.abs(d[:, :2]) <= 1e-14
    inside = (origin[:2] >= centre) & (origin[:2] <= far_xy)
    near = np.where(parallel, np.where(inside, -np.inf, np.inf), np.minimum(a, b))
    far = np.where(parallel, np.where(inside, np.inf, -np.inf), np.maximum(a, b))
    start = np.maximum(near.max(1), 0); end = far.min(1)
    answer = np.full((n, 3), np.nan); gradients = np.full((n, 2), np.nan)
    indices = np.where(start <= end)[0]
    point = origin[:2]+d[indices, :2]*(start[indices, None]+1e-7)
    cells = np.floor((point-centre)/spacing).astype(int)
    cells = np.clip(cells, 0, np.array(grid.shape[::-1])-2)
    now = start[indices]; step = np.sign(d[indices, :2]).astype(int)
    for _ in range(sum(grid.shape)+2):
        if not len(indices): break
        dc = d[indices]; c, r = cells.T; xy = centre+cells*spacing
        edge = xy+np.where(step > 0, spacing, 0)
        nxt = np.where(step != 0, (edge-origin[:2])*inv[indices], np.inf)
        until = np.minimum(nxt.min(1), end[indices])
        h00 = grid[r, c].astype(float)-vertical_origin
        h10 = grid[r, c+1].astype(float)-vertical_origin
        h01 = grid[r+1, c].astype(float)-vertical_origin
        h11 = grid[r+1, c+1].astype(float)-vertical_origin
        best = np.full(len(indices), np.inf); best_gradient = np.zeros((len(indices), 2))
        for triangle in (0, 1):
            gx = ((h10-h00) if triangle == 0 else (h11-h01))/spacing
            gy = ((h01-h00) if triangle == 0 else (h11-h10))/spacing
            intercept = h00 if triangle == 0 else h10+h01-h11
            numerator = intercept+gx*(origin[0]-xy[:, 0])+gy*(origin[1]-xy[:, 1])-origin[2]
            denominator = dc[:, 2]-gx*dc[:, 0]-gy*dc[:, 1]
            distance = np.divide(numerator, denominator, out=np.full_like(numerator, np.inf), where=np.abs(denominator) > 1e-12)
            hitxy = origin[:2]+dc[:, :2]*distance[:, None]; uv = (hitxy-xy)/spacing
            total = uv.sum(1)
            valid = ((distance >= now-1e-7) & (distance <= until+1e-7) &
                     (uv >= -1e-7).all(1) & (uv <= 1+1e-7).all(1) &
                     ((total <= 1+1e-7) if triangle == 0 else (total >= 1-1e-7)) & (distance < best))
            best[valid] = distance[valid]; best_gradient[valid] = np.column_stack((gx, gy))[valid]
        found = np.isfinite(best)
        answer[indices[found]] = origin+d[indices[found]]*best[found, None]
        gradients[indices[found]] = best_gradient[found]
        remain = ~found & (until < end[indices]-1e-7)
        crossed = nxt <= until[:, None]+1e-9
        cells += crossed*step
        remain &= (cells >= 0).all(1) & (cells < np.array(grid.shape[::-1])-1).all(1)
        indices, cells, step, now = indices[remain], cells[remain], step[remain], until[remain]
    else: raise ValueError('Ray traversal did not terminate')
    return answer, gradients


def sample_rgb(old, xy, normalised=None):
    c = np.clip(np.floor(xy[:, 0]/.1).astype(int), 0, 19999)
    r = np.clip(np.floor(xy[:, 1]/.1).astype(int), 0, 19999)
    tr, tc = r//2500, c//2500; result = np.empty((len(xy), 3), np.uint8)
    folder = normalised if normalised is not None else old/'textures'
    for a, b in sorted(set(zip(tr, tc))):
        mask = (tr == a) & (tc == b)
        image = np.asarray(Image.open(folder/f'tile_{a}_{b}.png').convert('RGB'))
        result[mask] = image[r[mask]-a*2500+5, c[mask]-b*2500+5]
    return result


def summary(values):
    values = np.asarray(values)
    return {'min': float(values.min()), 'p05_p50_p95': np.percentile(values, [5, 50, 95]).tolist(), 'max': float(values.max())}


def audit(repo, data, out):
    """Trace fixed pixel windows and physical source controls before correction."""
    old, _ = lighting.paths(repo, data)
    b = json.loads((repo/'docs/earth-lab/riffelhorn-012b-metadata.json').read_text(encoding='utf-8'))
    catalog = json.loads((repo/'docs/atlas/riffelhorn-data-catalog.json').read_text(encoding='utf-8'))
    grid = mountain.height_grid(catalog, data/catalog['external_root_relative'], 'swisssurface3d-raster')
    windows = {v: dict(lighting.REGIONS.get(v, {})) for v in VIEWS}
    windows['riffelhorn_structure'] = {'steep_projection_control': [500, 350, 1450, 1000]}
    answer = {'regions': {}, 'camera_visible_sampling': {}, 'trace_stride_pixels': 8,
              'density_model': 'horizontal area / triangle surface area; not sensor visibility or optical resolution'}
    traces = out/'traces'; traces.mkdir(parents=True, exist_ok=True)
    for view in VIEWS:
        # Entire fixed view at 16-pixel stride for a bounded visibility/footprint audit.
        windows[view]['whole_view'] = [0, 0, 1920, 1080]
        for name, box in windows[view].items():
            stride = 16 if name == 'whole_view' else 8
            xx, yy = np.meshgrid(np.arange(box[0], box[2], stride), np.arange(box[1], box[3], stride))
            pixels = np.column_stack((xx.ravel(), yy.ravel()))
            origin, direction = rays(b['views'][view], pixels)
            hit, grad = raycast(grid, origin, direction); valid = np.isfinite(hit[:, 0])
            hit, grad, pixels = hit[valid], grad[valid], pixels[valid]
            cosine, native, distributed, tangent = density_from_gradients(grad[:, 0], grad[:, 1])
            normal = np.column_stack((-grad[:, 0], -grad[:, 1], np.ones(len(hit))))*cosine[:, None]
            depth = (hit-origin)@((np.asarray(b['views'][view]['target_m'])-origin)/b['views'][view]['distance_to_target_m'])
            # Local perspective area Jacobian, not a uniform target-plane approximation.
            facing = np.abs(np.sum(normal*(origin-hit), axis=1))
            focal = 1920/(2*np.tan(np.radians(25)))
            output_area_per_m2 = focal*focal*facing/np.maximum(depth, 1e-10)**3
            record = {'box': box, 'hit_queries': len(hit), 'sky_or_outside_queries': int(valid.size-valid.sum()),
                'lv95_bounds': [float(hit[:, 0].min()+2624000), float(1093000-hit[:, 1].max()),
                               float(hit[:, 0].max()+2624000), float(1093000-hit[:, 1].min())],
                'slope_degrees': summary(np.degrees(np.arccos(cosine))),
                'native_information_elements_per_surface_m2': summary(native),
                'distributed_samples_per_surface_m2': summary(distributed),
                'native_steepest_tangent_footprint_m': summary(tangent),
                'native_information_elements_per_output_pixel': summary(native/np.maximum(output_area_per_m2, 1e-12)),
                'stretch_over_2_fraction': float((cosine < .5).mean()), 'stretch_over_5_fraction': float((cosine < .2).mean())}
            rgb = sample_rgb(old, hit[:, :2]); y = decode(rgb)@LUMA
            record['source_sample_luminance'] = summary(y)
            record['source_encoded_luma_at_most_5_fraction'] = float((rgb@LUMA <= 5).mean())
            record['source_exact_black_fraction'] = float((rgb.max(1) == 0).mean())
            np.savez(traces/f'{view}-{name}.npz', pixels=pixels, hit=hit, gradients=grad, rgb=rgb)
            target = 'camera_visible_sampling' if name == 'whole_view' else 'regions'
            answer[target][view+'-'+name] = record
            print('traced', view, name, len(hit), flush=True)
    write(out/'source-audit.json', answer)
    return answer


def products(out, paths):
    return [{'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': mountain.digest(p)} for p in sorted(paths)]


def registration_checks(repo, data, out):
    """Independent source-file pixel checks, not only agreement with tiled copies."""
    import rasterio
    from rasterio.windows import Window
    catalog = json.loads((repo/'docs/atlas/riffelhorn-data-catalog.json').read_text(encoding='utf-8'))
    source = data/catalog['external_root_relative']; checks = []
    for path in sorted((out/'traces').glob('*.npz')):
        trace = np.load(path); xy = trace['hit'][:, :2]
        for i in np.linspace(0, len(xy)-1, 3, dtype=int):
            e, n = 2624000+xy[i, 0], 1093000-xy[i, 1]
            for record in catalog['assets']:
                if record['product'] != 'swissimage-dop10': continue
                with rasterio.open(source/record['path']) as src:
                    if src.bounds.left <= e < src.bounds.right and src.bounds.bottom < n <= src.bounds.top:
                        r, c = src.index(e, n)
                        actual = src.read(window=Window(c, r, 1, 1))[:, 0, 0]
                        np.testing.assert_array_equal(actual, trace['rgb'][i])
                        checks.append({'trace': path.stem, 'query_index': int(i), 'asset': record['path'],
                                       'pixel_row_col': [r, c], 'rgb': actual.tolist()})
                        break
            else: raise ValueError('Trace outside source coverage')
    return {'direct_original_cog_checks': checks, 'checked_pixels': len(checks)}


def normalised_textures(old, out):
    """One bounded global low-frequency gain field; no local-content enhancement.

    2 m block means are only an illumination estimator. The output retains all
    native 10 cm samples, with nominal 25 cm information and unchanged UVs.
    """
    coarse = np.empty((1000, 1000), np.float64)
    for r in range(8):
        for c in range(8):
            image = np.asarray(Image.open(old/'textures'/f'tile_{r}_{c}.png').convert('RGB'))
            y = decode(image[5:2505, 5:2505])@LUMA
            coarse[r*125:(r+1)*125, c*125:(c+1)*125] = y.reshape(125, 20, 125, 20).mean((1, 3))
    low = blur(coarse, 15)  # sigma 30 m, +/-90 m support, common across tile seams.
    target = float(np.median(low))
    gain = np.clip(np.sqrt(target/np.maximum(low, 1e-6)), .5, 4)
    np.savez(out/'illumination-field.npz', block_mean=coarse, low_frequency=low, gain=gain)
    folder = out/'textures'; folder.mkdir(exist_ok=True)
    clipped_count = 0; exact_black = 0; total = 0
    for r in range(8):
        for c in range(8):
            image = np.asarray(Image.open(old/'textures'/f'tile_{r}_{c}.png').convert('RGB'))
            x = np.clip((c*2500+np.arange(2510)-5+.5)*.1, .05, 1999.95)
            y = np.clip((r*2500+np.arange(2510)-5+.5)*.1, .05, 1999.95)
            requested = interpolate(gain, x[None, :], y[:, None])
            changed, actual = normalise(image, requested)
            black = image.max(2) == 0
            assert not changed[black].any(), 'Black source anomaly modified'
            core = np.s_[5:2505, 5:2505]
            clipped_count += int((actual[core] < requested[core]-1e-7).sum())
            exact_black += int(black[core].sum()); total += 2500**2
            attribution = PngInfo(); attribution.add_text('Attribution', '\u00a9 swisstopo')
            attribution.add_text('Processing', '012G bounded experimental low-frequency gain; not source albedo')
            Image.fromarray(changed).save(folder/f'tile_{r}_{c}.png', pnginfo=attribution)
        print('normalised texture row', r, flush=True)
    assert exact_black == 267, 'Historical black anomaly count changed'
    # Aprons cover identical source coordinates and must agree after correction.
    for r in range(8):
        for c in range(8):
            a = np.asarray(Image.open(folder/f'tile_{r}_{c}.png'))
            if c < 7:
                b = np.asarray(Image.open(folder/f'tile_{r}_{c+1}.png'))
                np.testing.assert_array_equal(a[:, -10:], b[:, :10])
            if r < 7:
                b = np.asarray(Image.open(folder/f'tile_{r+1}_{c}.png'))
                np.testing.assert_array_equal(a[-10:], b[:10])
    return {'method': 'common linear RGB gain = clip(sqrt(median(L)/max(L,1e-6)),0.5,4)',
        'L': '2 m block-mean linear Rec.709 luminance, separable Gaussian sigma 30 m, +/-90 m support, edge replication',
        'application': 'bilinear field at original 10 cm pixel centres; gain limited to 1/max(linear RGB) to avoid channel clipping; nearest-integer sRGB output',
        'global_target_linear': target, 'gain': summary(gain), 'channel_ceiling_limited_fraction': clipped_count/total,
        'exact_black_pixels_preserved': exact_black, 'interpretation': 'illumination proxy confounded with material colour; not intrinsic albedo or calibrated de-shadowing'}


def source_controls(old, out):
    controls = [('steep_face', (805, 670), 60), ('alpine_path', (1240, 470), 60),
                ('summit_context', (810, 748), 150),
                ('dark_face_context', (740, 682), 150)]  # encloses the exact 012F dark-window traces.
    result = {}
    for name, centre, side in controls:
        coordinates = (np.arange(round(side/.1))+.5)*.1-side/2
        xx, yy = np.meshgrid(centre[0]+coordinates, centre[1]+coordinates)
        xy = np.column_stack((xx.ravel(), yy.ravel()))
        original = sample_rgb(old, xy).reshape(len(coordinates), len(coordinates), 3)
        changed = sample_rgb(old, xy, out/'textures').reshape(original.shape)
        y0, y1 = decode(original)@LUMA, decode(changed)@LUMA
        gradients = [np.concatenate((np.diff(y, axis=0).ravel(), np.diff(y, axis=1).ravel())) for y in (y0, y1)]
        highpass = [y-blur(y, 5) for y in (y0, y1)]  # diagnostic only; no source filtering.
        result[name] = {'centre_lv95': [2624000+centre[0], 1093000-centre[1]], 'side_m': side,
            'original': lighting.region_statistics(original), 'normalised': lighting.region_statistics(changed),
            'linear_gradient_correlation': float(np.corrcoef(*gradients)[0, 1]),
            'gradient_sign_agreement': float((np.sign(gradients[0]) == np.sign(gradients[1])).mean()),
            'half_metre_highpass_correlation': float(np.corrcoef(highpass[0].ravel(), highpass[1].ravel())[0, 1])}
        sheet = Image.new('RGB', (2*len(coordinates), len(coordinates)+24), 'white')
        for i, (state, rgb) in enumerate((('original', original), ('normalised', changed))):
            attribution = PngInfo(); attribution.add_text('Attribution', '\u00a9 swisstopo')
            Image.fromarray(rgb).save(out/f'{name}-{state}-source.png', pnginfo=attribution)
            sheet.paste(Image.fromarray(rgb), (i*len(coordinates), 24))
            ImageDraw.Draw(sheet).text((i*len(coordinates)+5, 5), f'{name} / {state} / native samples / \u00a9 swisstopo', fill='black')
        sheet.save(out/f'{name}-source-comparison.png')
    return result


def prepare_project(repo, data, out):
    old, froot = lighting.paths(repo, data); project = out/'unreal'; project.mkdir(exist_ok=True)
    f = json.loads((froot/'lab012f-inputs.json').read_text(encoding='utf-8'))
    copied = []
    for p in f['copied_assets']:
        target = project/p['path']; target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists(): shutil.copy2(froot/'unreal'/p['path'], target)
        assert mountain.digest(target) == p['sha256'], p['path']
        copied.append(p)
    # Reuse compiled 012F L1 materials, not a subtly changed lighting graph.
    for name in ('M_rgb_directional', 'M_neutral_directional'):
        relative = Path('Content/Lab012F/Materials')/(name+'.uasset')
        target = project/relative; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(froot/'unreal'/relative, target)
        copied.append({'path': relative.as_posix(), 'bytes': target.stat().st_size, 'sha256': mountain.digest(target)})
    (project/'Config').mkdir(exist_ok=True)
    shutil.copy2(froot/'unreal/Config/DefaultEngine.ini', project/'Config/DefaultEngine.ini')
    doc = json.loads((froot/'unreal/RiffelhornLab012F.uproject').read_text(encoding='utf-8'))
    doc['Description'] = '012G orthophoto projection and baked illumination; \u00a9 swisstopo'
    write(project/'RiffelhornLab012G.uproject', doc)
    folder = project/'Content/Python'; folder.mkdir(exist_ok=True)
    for source, destination in [('unreal_riffelhorn_012g.py', 'lab012g.py'), ('unreal_riffelhorn_012f.py', 'lab012f.py'),
                                 ('unreal_bluesky_012a.py', 'lab012a_common.py')]:
        shutil.copy2(repo/'scripts/earth_lab'/source, folder/destination)
    prefix = "import sys,unreal\nsys.path.insert(0,unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()+'Python'))\nimport lab012g\n"
    for run in ('first', 'repeat'):
        (folder/f'capture_{run}.py').write_text(prefix+f"lab012g.run('{run}')\n", encoding='utf-8', newline='\n')
    write(project/'lab012g-source.json', {'output_root': str(out)})
    return copied


def prepare(repo, data, out):
    start = time.monotonic(); parents = preserve(repo, data); old, _ = lighting.paths(repo, data)
    if not (out/'source-audit.json').exists(): audit(repo, data, out)
    method = normalised_textures(old, out)
    controls = source_controls(old, out); write(out/'source-controls.json', controls)
    copied = prepare_project(repo, data, out)
    b = json.loads((repo/'docs/earth-lab/riffelhorn-012b-metadata.json').read_text(encoding='utf-8'))
    manifest = {'experiment': 'Lab 012G — orthophoto projection and baked illumination', 'parents': parents,
        'geometry': b['geometry']['dsm'], 'coordinate_frame': b['coordinate_frame'], 'textures': b['textures'],
        'views': {v: b['views'][v] for v in VIEWS}, 'lighting': {'ambient': .35, 'directional': .65,
        'direction_east_south_up': lighting.DIRECTIONS['northeast'], 'cast_shadows': False},
        'states': STATES, 'normalisation': method, 'copied_assets': copied,
        'processing_sha256': mountain.digest(Path(__file__)),
        'adapter_sha256': mountain.digest(repo/'scripts/earth_lab/unreal_riffelhorn_012g.py'),
        'toolchain': {'python': platform.python_version(), 'numpy': np.__version__,
                      'pillow': Image.__version__, 'unreal': '5.8.2 / D3D11'}, 'attribution': '\u00a9 swisstopo'}
    manifest['identity'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    write(out/'lab012g-inputs.json', manifest)
    write(out/'preparation-performance.json', {'seconds': time.monotonic()-start})
    return manifest


def analyse(repo, data, out):
    m = json.loads((out/'lab012g-inputs.json').read_text(encoding='utf-8'))
    assert m['processing_sha256'] == mountain.digest(Path(__file__)), 'Prepare with this exact processing code first'
    reports = [json.loads((out/f'capture-{run}.json').read_text(encoding='utf-8')) for run in ('first', 'repeat')]
    assert len(reports[0]['frames']) == len(reports[1]['frames']) == 16
    assert reports[0]['frames'] == reports[1]['frames']
    assert reports[0]['invariance'] == reports[1]['invariance']
    assert all(r['adapter_sha256'] == m['adapter_sha256'] for r in reports)
    old, froot = lighting.paths(repo, data)
    b = json.loads((old/'captures-dsm-neutral.json').read_text(encoding='utf-8'))
    assert [s[:11] for s in reports[0]['invariance']['signature']] == b['geometry_signature']
    old_poses = {r['view']: r['camera_pose_cm_degrees'] for r in b['captures']}
    audit_result = json.loads((out/'source-audit.json').read_text(encoding='utf-8'))
    metrics, baseline_checks = {}, []
    for frame in reports[0]['frames']:
        name = frame['name']; a, bpath = [out/f'captures/{run}/{name}.png' for run in ('first', 'repeat')]
        image, repeat = [np.asarray(Image.open(p).convert('RGB')) for p in (a, bpath)]
        assert np.array_equal(image, repeat), 'Non-deterministic RGB: '+name
        assert image.shape == (1080, 1920, 3)
        np.testing.assert_allclose(frame['pose'], old_poses[frame['view']], rtol=0, atol=1e-6)
        for target, rgb in ((a, image), (bpath, repeat)):
            attribution = PngInfo(); attribution.add_text('Attribution', '\u00a9 swisstopo')
            Image.fromarray(rgb).save(target, pnginfo=attribution)
        assert mountain.digest(a) == mountain.digest(bpath)
        if frame['state'] == 'original_lit' and frame['view'] in lighting.VIEWS:
            historical = np.asarray(Image.open(froot/'captures/first'/f"{frame['view']}-rgb-directional_northeast.png").convert('RGB'))
            baseline_checks.append({'view': frame['view'], **lighting.baseline_equivalence(image, historical)})
        metrics[name] = {}
        for key, region in audit_result['regions'].items():
            if not key.startswith(frame['view']+'-'): continue
            x0, y0, x1, y1 = region['box']
            metrics[name][key] = lighting.region_statistics(image[y0:y1, x0:x1])
    # Trace the same source locations in the corrected texture. Do not claim that
    # point sampling is identical to the GPU's trilinear/mip footprint.
    for key, region in audit_result['regions'].items():
        trace = np.load(out/'traces'/f'{key}.npz')
        rgb = sample_rgb(old, trace['hit'][:, :2], out/'textures')
        gain_field = np.load(out/'illumination-field.npz')['gain']
        requested = interpolate(gain_field, trace['hit'][:, 0], trace['hit'][:, 1])
        _, actual = normalise(trace['rgb'], requested)
        region['requested_gain'] = summary(requested)
        region['actual_channel_ceiling_limited_gain'] = summary(actual)
        region['corrected_source_sample_luminance'] = summary(decode(rgb)@LUMA)
        region['corrected_source_encoded_luma_at_most_5_fraction'] = float((rgb@LUMA <= 5).mean())
        view = key.rsplit('-', 1)[0]
        if view in lighting.VIEWS:
            pixels = trace['pixels']; samples = {}
            for direction in ('northeast', 'southwest'):
                image = np.asarray(Image.open(froot/'captures/first'/f'{view}-rgb-directional_{direction}.png').convert('RGB'))
                samples[direction] = image[pixels[:, 1], pixels[:, 0]]
            y0, y1 = [decode(samples[d])@LUMA for d in ('northeast', 'southwest')]
            region['012f_opposed_light_output'] = {'northeast_linear_luminance': summary(y0),
                'southwest_linear_luminance': summary(y1), 'luminance_correlation': float(np.corrcoef(y0, y1)[0, 1])}
        original = np.asarray(Image.open(out/'captures/first'/f'{view}-original_unlit.png').convert('RGB'))
        pixels = trace['pixels']; displayed = decode(original[pixels[:, 1], pixels[:, 0]])@LUMA
        source_y = decode(trace['rgb'])@LUMA
        region['source_to_unlit_output_luminance_correlation'] = float(np.corrcoef(source_y, displayed)[0, 1])
        region['unlit_output_at_source_query_pixels'] = summary(displayed)
    contacts = out/'comparisons'; contacts.mkdir(exist_ok=True)
    for view in VIEWS:
        sheet = Image.new('RGB', (1920, 300), 'white'); draw = ImageDraw.Draw(sheet)
        for i, state in enumerate(STATES):
            with Image.open(out/'captures/first'/f'{view}-{state}.png') as im:
                sheet.paste(im.convert('RGB').resize((480, 270), Image.Resampling.LANCZOS), (i*480, 18))
            draw.text((i*480+5, 3), state, fill='black')
        draw.text((5, 288), f'{view} / 4x reduced preview / full frames 1920x1080 / density: red stretched, green horizontal / \u00a9 swisstopo', fill='black')
        sheet.save(contacts/f'{view}.png')
    validation = {'result': 'PASS', 'canonical_frames': 16, 'byte_identical_repeat_frames': 16,
        '012f_original_lighting_equivalence': baseline_checks, 'geometry_camera_invariance': reports[0]['invariance'],
        'preservation': preserve(repo, data), 'copied_assets_unchanged': len(m['copied_assets']),
        'canonical_rgb_export': 'exact decoded RGB; nondeterministic unused alpha omitted',
        'normalised_texture_seams': '64 tile aprons checked bit-exact during preparation',
        'original_black_anomalies_preserved': 267, 'independent_source_registration': registration_checks(repo, data, out)}
    for p in m['copied_assets']: assert mountain.digest(out/'unreal'/p['path']) == p['sha256'], p['path']
    write(out/'measurements.json', {'render_windows': metrics, 'source_traces': audit_result})
    write(out/'validation.json', validation)
    paths = list((out/'textures').glob('*.png'))+list((out/'traces').glob('*.npz'))
    paths += list((out/'captures/first').glob('*.png'))+list(contacts.glob('*.png'))
    paths += list(out.glob('*-source*.png'))
    paths += [out/p for p in ('illumination-field.npz', 'source-audit.json', 'source-controls.json', 'measurements.json', 'validation.json')]
    result = {'input_identity': m['identity'], 'products': products(out, paths), 'attribution': '\u00a9 swisstopo'}
    result['identity'] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    write(out/'lab012g-products.json', result)
    return validation


def verify(repo, data, out):
    preserve(repo, data)
    m = json.loads((out/'lab012g-products.json').read_text(encoding='utf-8'))
    inputs = json.loads((out/'lab012g-inputs.json').read_text(encoding='utf-8'))
    assert inputs['processing_sha256'] == mountain.digest(Path(__file__))
    assert inputs['adapter_sha256'] == mountain.digest(repo/'scripts/earth_lab/unreal_riffelhorn_012g.py')
    assert inputs['identity'] == m['input_identity']
    for p in inputs['copied_assets']: assert mountain.digest(out/'unreal'/p['path']) == p['sha256'], p['path']
    for p in m['products']:
        if mountain.digest(out/p['path']) != p['sha256']: raise ValueError('012G product changed: '+p['path'])
    return {'result': 'PASS', 'products': len(m['products']), 'identity': m['identity']}


def reproduce(repo, data, out):
    """Repeat the numerical/texture pipeline; independent UE captures are separate."""
    before = json.loads((out/'lab012g-products.json').read_text(encoding='utf-8'))
    audit(repo, data, out); prepare(repo, data, out); analyse(repo, data, out)
    after = json.loads((out/'lab012g-products.json').read_text(encoding='utf-8'))
    assert before == after, 'Canonical identity/output changed during repeat processing'
    return {'result': 'PASS', 'identity': after['identity'], 'unchanged_canonical_products': len(after['products']),
            'freshly_reprocessed_source_diagnostics_textures': 91, 'independent_byte_identical_render_frames': 16}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=('audit', 'prepare', 'analyse', 'verify', 'reproduce'))
    args = parser.parse_args(); repo = Path(__file__).resolve().parents[2]
    data = resolve_storage_roots(repository_root=repo, require_data=True).data; out = data/ROOT
    out.mkdir(parents=True, exist_ok=True)
    if args.action == 'audit':
        preserve(repo, data); print(json.dumps(audit(repo, data, out)['regions'], indent=2))
    elif args.action == 'prepare': print(prepare(repo, data, out)['identity'])
    elif args.action == 'analyse': print(analyse(repo, data, out)['result'])
    elif args.action == 'verify': print(json.dumps(verify(repo, data, out)))
    elif args.action == 'reproduce':
        proof = reproduce(repo, data, out); write(out/'reproduction-proof.json', proof); print(json.dumps(proof))


if __name__ == '__main__': main()
