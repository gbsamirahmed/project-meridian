"""Bounded lighting comparison; reads frozen terrain, never reconstructs it."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time
import numpy as np
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo
import riffelhorn_012b as mountain
import riffelhorn_012e as previous
from meridian_paths import resolve_storage_roots

VIEWS = ('overview', 'riffelhorn_oblique', 'alpine_path')
DIRECTIONS = {'northeast': [.4, -.3, .8660254], 'southwest': [-.4, .3, .8660254]}
CONDITIONS = ['baseline', 'directional_northeast', 'shadow_northeast',
              'directional_southwest', 'shadow_southwest']
# Image-space windows fixed from the historical neutral/RGB captures before fitting.
REGIONS = {
    'overview': {'mountain_relief': [650, 230, 1000, 630], 'alpine_channels': [1000, 150, 1300, 470]},
    'riffelhorn_oblique': {'ridge_face': [450, 340, 1000, 530],
                         'foreground_shoulder': [930, 550, 1250, 760],
                         'photographed_dark_face': [1150, 800, 1500, 1020]},
    'alpine_path': {'ground_undulation': [400, 350, 1000, 670],
                    'convex_protrusion': [1250, 220, 1570, 480]},
}


def paths(repo, data):
    old = data/'experiments/earth-lab/riffelhorn-012b/observed-mountain-v1'
    out = data/'experiments/earth-lab/riffelhorn-012f/terrain-lighting-v1'
    return old, out


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def preserve(repo, data):
    parents, _ = previous.preserve(repo, data)
    for lab, folder in [('riffelhorn-012e', 'robust-plane-heightfield-v1'),
                        ('bluesky-012a', 'native-surface-v1')]:
        m = json.loads((repo/f'docs/earth-lab/{lab}-metadata.json').read_text(encoding='utf-8'))
        root = data/f'experiments/earth-lab/{lab}/{folder}'
        for p in m['products']:
            if previous.digest(root/p['path']) != p['sha256']: raise ValueError('Frozen product changed: '+p['path'])
        parents[lab] = {'identity': m['identity'], 'unchanged_products': len(m['products'])}
    old, _ = paths(repo, data)
    validation = json.loads((repo/'docs/earth-lab/riffelhorn-012b-validation.json').read_text(encoding='utf-8'))
    inventory = json.loads((old/'unreal-assets.json').read_text(encoding='utf-8'))
    for p in validation['capture_hashes']+inventory['files']:
        if previous.digest(old/p['path']) != p['sha256']: raise ValueError('Historical capture/asset changed: '+p['path'])
    parents['historical_raw_frames'] = len(validation['capture_hashes'])
    parents['historical_unreal_assets'] = len(inventory['files'])
    return parents


def illumination(normals, direction, ambient=.35, visibility=1.):
    """Analytical reference for the shader, with unchanged imported normals."""
    return ambient+(1-ambient)*np.maximum(np.asarray(normals)@direction, 0)*visibility


def light_uv(points, origin, right, up, forward, width):
    relative = np.asarray(points)-origin
    return np.column_stack((.5+relative@right/width, .5-relative@up/width, relative@forward))


def linear_luminance(rgb):
    v = np.asarray(rgb, dtype=np.float64)/255
    v = np.where(v <= .04045, v/12.92, ((v+.055)/1.055)**2.4)
    return v@np.array([.2126, .7152, .0722])


def region_statistics(rgb):
    y = linear_luminance(rgb)
    encoded = np.asarray(rgb)@np.array([.2126, .7152, .0722])
    return {'pixels': int(y.size), 'linear_mean': float(y.mean()),
            'linear_p05_p50_p95': np.percentile(y, [5, 50, 95]).tolist(),
            'linear_p95_minus_p05': float(np.percentile(y, 95)-np.percentile(y, 5)),
            'mean_absolute_horizontal_gradient': float(np.abs(np.diff(y, axis=1)).mean()),
            'mean_absolute_vertical_gradient': float(np.abs(np.diff(y, axis=0)).mean()),
            'display_luma_at_most_5_fraction': float((encoded <= 5).mean()),
            'any_channel_at_least_250_fraction': float((np.asarray(rgb).max(2) >= 250).mean())}


def baseline_equivalence(image, historical):
    """Audit unchanged rendering despite UE's display-quantisation dither phase.

    No filtering is applied to the published frames. Eight-pixel block means are
    used only to distinguish zero-mean dither from a changed lighting transfer.
    """
    difference = image.astype(float)-historical.astype(float)
    block = difference.reshape(135, 8, 240, 8, 3).mean((1, 3))
    record = {'pixel_identical': bool(np.array_equal(image, historical)),
              'maximum_encoded_difference': float(np.abs(difference).max()),
              'signed_encoded_mean_difference': float(difference.mean()),
              'block8_mean_absolute_difference': float(np.abs(block).mean()),
              'block8_maximum_absolute_difference': float(np.abs(block).max())}
    if (record['maximum_encoded_difference'] > 24 or
        abs(record['signed_encoded_mean_difference']) > .01 or
        record['block8_mean_absolute_difference'] > .4 or
        record['block8_maximum_absolute_difference'] > 3):
        raise ValueError('Historical baseline changed beyond display dither')
    return record


def geometric_forms(repo, data):
    """Read-only native-grid profiles confirming form independent of RGB.

    These are controls, not a new reconstruction or terrain derivative suite.
    Heights remain LN02 metres and are sampled at original cell centres.
    """
    catalog = json.loads((repo/'docs/atlas/riffelhorn-data-catalog.json').read_text(encoding='utf-8'))
    grid = mountain.height_grid(catalog, data/catalog['external_root_relative'], 'swisssurface3d-raster')
    profiles = {
        'summit_ridge_breaks': ([2624780.25, 1092252.25], [2624839.75, 1092252.25]),
        'alpine_ground_and_shoulder': ([2625210.25, 1092530.25], [2625269.75, 1092530.25]),
        'northern_channel_context': ([2625100.25, 1092600.25], [2625100.25, 1092799.75]),
    }
    answer = {'crs': 'EPSG:2056', 'vertical_reference': 'LN02 metres',
              'sampling_m': .5, 'source': 'unchanged 012B swissSURFACE3D grid', 'profiles': {}}
    for name, (start, end) in profiles.items():
        count = round(np.linalg.norm(np.subtract(end, start))/.5)+1
        xy = np.linspace(start, end, count)
        z = mountain.sample_grid(grid, xy[:, 0], xy[:, 1])
        answer['profiles'][name] = {'start_xy': start, 'end_xy': end, 'samples': count,
            'heights_ln02_m': z.tolist(), 'range_m': float(np.ptp(z)),
            'maximum_adjacent_height_change_m': float(np.abs(np.diff(z)).max())}
    return answer


def prepare(repo, data):
    start = time.monotonic(); parents = preserve(repo, data); old, out = paths(repo, data)
    out.mkdir(parents=True, exist_ok=True)
    project = out/'unreal'; project.mkdir(exist_ok=True)
    # Physical copies: never hard-link writable Unreal packages to historical assets.
    inventory = json.loads((old/'unreal-assets.json').read_text(encoding='utf-8'))
    copied = []
    for p in inventory['files']:
        relative = Path(p['path']).relative_to('unreal')
        # No DTM mesh or material is needed for a frozen DSM lighting experiment.
        if '/dtm/' in relative.as_posix() or relative.as_posix().endswith('/dtm.umap'): continue
        target = project/relative; target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists(): shutil.copy2(old/p['path'], target)
        if previous.digest(target) != p['sha256']: raise ValueError('Copied historical asset differs: '+p['path'])
        copied.append({'path': relative.as_posix(), 'sha256': p['sha256'], 'bytes': p['bytes']})
    (project/'Config').mkdir(exist_ok=True)
    shutil.copy2(old/'unreal/Config/DefaultEngine.ini', project/'Config/DefaultEngine.ini')
    doc = json.loads((old/'unreal/RiffelhornLab012B.uproject').read_text(encoding='utf-8'))
    doc['Description'] = 'Frozen Riffelhorn terrain lighting experiment; \u00a9 swisstopo'
    write(project/'RiffelhornLab012F.uproject', doc)
    folder = project/'Content/Python'; folder.mkdir(exist_ok=True)
    shutil.copy2(repo/'scripts/earth_lab/unreal_riffelhorn_012f.py', folder/'lab012f.py')
    shutil.copy2(repo/'scripts/earth_lab/unreal_bluesky_012a.py', folder/'lab012a_common.py')
    prefix = "import sys,unreal\nsys.path.insert(0,unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()+'Python'))\nimport lab012f\n"
    for run in ('first', 'repeat'):
        (folder/f'capture_{run}.py').write_text(prefix+f"lab012f.run('{run}')\n", encoding='utf-8')
    b = json.loads((repo/'docs/earth-lab/riffelhorn-012b-metadata.json').read_text(encoding='utf-8'))
    write(project/'lab012f-source.json', {'output_root': str(out)})
    manifest = {'experiment': 'Lab 012F — terrain lighting and readability', 'parents': parents,
                'geometry': b['geometry']['dsm'], 'coordinate_frame': b['coordinate_frame'],
                'textures': b['textures'], 'views': {v: b['views'][v] for v in VIEWS},
                'render_settings': b['render_settings'], 'directions_unreal_east_south_up': DIRECTIONS,
                'lighting': {'baseline': {'ambient': .65, 'directional': .35},
                             'directional': {'ambient': .35, 'directional': .65},
                             'shadow': {'ambient': .35, 'directional': .65, 'depth_pixels': 4096,
                                        'pcf': '3x3 uniform', 'bias_cm': '15 + 0.5*shadow_texel_cm*(1-max(n·l,0))'}},
                'regions': REGIONS, 'copied_assets': copied,
                'processing_sha256': previous.digest(Path(__file__)),
                'adapter_sha256': previous.digest(repo/'scripts/earth_lab/unreal_riffelhorn_012f.py'),
                'attribution': '\u00a9 swisstopo'}
    manifest['identity'] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    write(out/'lab012f-inputs.json', manifest)
    write(out/'preparation-performance.json', {'seconds': time.monotonic()-start,
                                              'copied_asset_bytes': sum(p['bytes'] for p in copied)})
    return manifest


def analyse(repo, data):
    old, out = paths(repo, data); m = json.loads((out/'lab012f-inputs.json').read_text(encoding='utf-8'))
    reports = [json.loads((out/f'capture-{run}.json').read_text(encoding='utf-8')) for run in ('first', 'repeat')]
    assert len(reports[0]['frames']) == 30 and len(reports[1]['frames']) == 30
    assert reports[0]['invariance'] == reports[1]['invariance']
    assert reports[0]['shadows'] == reports[1]['shadows']
    assert all(r['adapter_sha256'] == m['adapter_sha256'] for r in reports)
    historical = json.loads((old/'captures-dsm-neutral.json').read_text(encoding='utf-8'))
    assert [s[:11] for s in reports[0]['invariance']['signature']] == historical['geometry_signature']
    old_poses = {p['view']: p['camera_pose_cm_degrees'] for p in historical['captures']}
    metrics, products, baselines = {}, [], []
    for a, b in zip(reports[0]['frames'], reports[1]['frames']):
        assert {k: v for k, v in a.items() if k != 'run'} == {k: v for k, v in b.items() if k != 'run'}
        name = a['name']; p = out/'captures/first'/f'{name}.png'; q = out/'captures/repeat'/f'{name}.png'
        # SceneCapture LDR alpha is unused and not stable in this UE version.
        # Compare decoded RGB first, then encode those exact pixels canonically.
        image = np.array(Image.open(p).convert('RGB'))
        repeat = np.array(Image.open(q).convert('RGB'))
        assert np.array_equal(image, repeat), 'Repeat RGB mismatch: '+name
        for target, pixels in ((p, image), (q, repeat)):
            attribution = PngInfo(); attribution.add_text('Attribution', '\u00a9 swisstopo')
            Image.fromarray(pixels).save(target, pnginfo=attribution)
        assert previous.digest(p) == previous.digest(q), name
        assert image.shape == (1080, 1920, 3)
        view, state, condition = a['view'], a['state'], a['condition']
        np.testing.assert_allclose(a['pose'], old_poses[view], rtol=0, atol=1e-6)
        baseline = np.array(Image.open(old/'captures/raw'/f'{view}-dsm-{state}.png').convert('RGB'))
        if condition == 'baseline':
            baselines.append({'name': name, **baseline_equivalence(image, baseline)})
        if condition.startswith('shadow_'):
            direct = np.array(Image.open(out/'captures/first'/f'{view}-{state}-directional_{condition[7:]}.png').convert('RGB'))
            assert (image.astype(int)-direct.astype(int)).max() <= 1, 'Shadow made directional light brighter'
        if state == 'neutral':
            # Quantisation adds up to 12 encoded levels to the black background.
            assert np.array_equal(image.max(2) > 32, baseline.max(2) > 32), 'Lighting altered silhouette/coverage'
        entry = {}
        for region, (x0, y0, x1, y1) in REGIONS[view].items():
            entry[region] = region_statistics(image[y0:y1, x0:x1])
        metrics[name] = entry
        products.append({'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': previous.digest(p)})
    contacts = out/'comparisons'; contacts.mkdir(exist_ok=True)
    for view in VIEWS:
        for state in ('neutral', 'rgb'):
            row = Image.new('RGB', (1920, 252), 'white'); draw = ImageDraw.Draw(row)
            for i, condition in enumerate(CONDITIONS):
                with Image.open(out/'captures/first'/f'{view}-{state}-{condition}.png') as im:
                    row.paste(im.convert('RGB').resize((384, 216), Image.Resampling.LANCZOS), (i*384, 20))
                draw.text((i*384+3, 4), condition, fill='black')
            draw.text((5, 237), f'{view} / {state} | 5x reduced preview; originals 1920x1080 | \u00a9 swisstopo', fill='black')
            p = contacts/f'{view}-{state}.png'; row.save(p)
            products.append({'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': previous.digest(p)})
    validation = {'result': 'PASS', 'canonical_frames': 30, 'byte_identical_repeat_frames': 30,
                  'historical_baseline_equivalence': baselines,
                  'canonical_rgb_export': 'exact decoded RGB; unused nondeterministic alpha omitted',
                  'preservation': preserve(repo, data),
                  'copied_assets_unchanged': len(m['copied_assets']),
                  'geometry_camera_invariance': reports[0]['invariance'], 'shadow_views': reports[0]['shadows']}
    for p in m['copied_assets']:
        assert previous.digest(out/'unreal'/p['path']) == p['sha256'], p['path']
    write(out/'measurements.json', metrics); write(out/'validation.json', validation)
    write(out/'geometric-form-controls.json', geometric_forms(repo, data))
    for p in (out/'measurements.json', out/'validation.json', out/'geometric-form-controls.json'):
        products.append({'path': p.relative_to(out).as_posix(), 'bytes': p.stat().st_size, 'sha256': previous.digest(p)})
    result = {'input_identity': m['identity'], 'products': products, 'attribution': '\u00a9 swisstopo'}
    result['identity'] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    write(out/'lab012f-products.json', result)
    return validation


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--analyse', action='store_true')
    args = parser.parse_args(); repo = Path(__file__).resolve().parents[2]
    data = resolve_storage_roots(repository_root=repo, require_data=True).data
    if args.analyse:
        result = analyse(repo, data)
        print(json.dumps({k: result[k] for k in ('result', 'canonical_frames', 'byte_identical_repeat_frames')}))
    else:
        print(prepare(repo, data)['identity'])
