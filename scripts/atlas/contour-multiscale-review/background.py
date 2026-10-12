"""Small native-grid visual hillshade, independent of contour derivation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['PROJ_NETWORK'] = 'OFF'
os.environ['GDAL_PAM_ENABLED'] = 'NO'

BOUNDS = (2624000, 1091000, 2626000, 1093000)
SIZE = 4000
CELL = 0.5
STRIP = 256


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for body in iter(lambda: stream.read(1048576), b''):
            value.update(body)
    return value.hexdigest()


def shade(window, cell=CELL):
    """Horn gradients: columns east, rows south; grid azimuth 315°, altitude 45°."""
    import numpy as np
    a, b, c = window[:-2, :-2], window[:-2, 1:-1], window[:-2, 2:]
    d, e, f = window[1:-1, :-2], window[1:-1, 1:-1], window[1:-1, 2:]
    g, h, i = window[2:, :-2], window[2:, 1:-1], window[2:, 2:]
    valid = np.isfinite(a) & np.isfinite(b) & np.isfinite(c) & np.isfinite(d)
    valid &= np.isfinite(e) & np.isfinite(f) & np.isfinite(g) & np.isfinite(h) & np.isfinite(i)
    east = ((c + 2*f + i) - (a + 2*d + g)) / (8*cell)
    north = ((a + 2*b + c) - (g + 2*h + i)) / (8*cell)
    azimuth, altitude = np.deg2rad(315), np.deg2rad(45)
    light_east = np.cos(altitude)*np.sin(azimuth)
    light_north = np.cos(altitude)*np.cos(azimuth)
    intensity = np.maximum(0, (-east*light_east - north*light_north + np.sin(altitude))
                           / np.sqrt(1 + east*east + north*north))
    pixels = np.empty((*e.shape, 2), dtype=np.uint8)
    pixels[:, :, 0] = np.rint(96 + 159*np.nan_to_num(intensity)).astype(np.uint8)
    pixels[:, :, 1] = valid.astype(np.uint8)*255
    return pixels


def mosaic_window(datasets, first_row, last_row):
    """Read a strip with true neighbours across tile joins; outside support is invalid."""
    import numpy as np
    from rasterio.windows import Window
    result = np.full((last_row-first_row, SIZE+2), np.nan, dtype=np.float32)
    for dataset in datasets:
        transform = dataset.transform
        row = round((BOUNDS[3]-transform.f)/CELL)
        col = round((transform.c-BOUNDS[0])/CELL)
        start, end = max(first_row, row), min(last_row, row+dataset.height)
        if end <= start:
            continue
        values = dataset.read(1, window=Window(0, start-row, dataset.width, end-start),
                              masked=True, out_dtype='float32').filled(np.nan)
        result[start-first_row:end-first_row, col+1:col+1+dataset.width] = values
    return result


def render(data_root, output):
    started = time.monotonic()
    if output.exists():
        raise ValueError('Fresh background directory required')
    pilot = Path(__file__).resolve().parent.parent/'contour-pilot'
    sys.path.insert(0, str(pilot))
    from resource_guard import confine_process
    guard = confine_process()
    from worker_supervision import api
    kernel, memory = api()
    import rasterio
    from PIL import Image
    pins = json.loads((pilot/'input-pins.json').read_text())
    # The pin catalogue is a list under inputs, not a new source selection.
    entries = pins['inputs']
    if isinstance(entries, dict):
        entries = list(entries.values())
    sources = [entry for entry in entries if 'swissalti3d' in entry['path']]
    if len(sources) != 4:
        raise ValueError('Exactly four pinned Swiss source tiles required')
    paths = [data_root/entry['path'] for entry in sources]
    for path, entry in zip(paths, sources):
        if digest(path) != entry['sha256']:
            raise ValueError('Source pin mismatch: '+path.name)
    output.mkdir(parents=True)
    image = Image.new('LA', (SIZE, SIZE), (244, 0))
    valid_pixels = 0
    with rasterio.Env(GDAL_CACHEMAX=32*1024**2, GDAL_NUM_THREADS='1'):
        datasets = [rasterio.open(path) for path in paths]
        try:
            for dataset in datasets:
                if (dataset.crs.to_epsg() != 2056 or dataset.shape != (2000, 2000)
                        or dataset.transform.a != CELL or dataset.transform.e != -CELL
                        or dataset.transform.b != 0 or dataset.transform.d != 0):
                    raise ValueError('Pinned raster grid incompatible with native display')
            for start in range(0, SIZE, STRIP):
                if time.monotonic()-started > 60:
                    raise RuntimeError('Visual background 60-second deadline reached')
                end = min(SIZE, start+STRIP)
                pixels = shade(mosaic_window(datasets, start-1, end+1))
                valid_pixels += int((pixels[:, :, 1] != 0).sum())
                image.paste(Image.fromarray(pixels), (0, start))
                if memory(kernel.GetCurrentProcess()).peak > 512*1024**2:
                    raise RuntimeError('Visual background working-set ceiling reached')
        finally:
            for dataset in datasets:
                dataset.close()
    partial = output/'hillshade.partial'
    image.save(partial, format='PNG')
    if partial.stat().st_size > 64_000_000 or time.monotonic()-started > 60:
        raise RuntimeError('Visual background output/time allowance reached')
    target = output/'hillshade.png'
    partial.rename(target)
    for path, entry in zip(paths, sources):
        if digest(path) != entry['sha256']:
            raise ValueError('Source changed during rendering')
    counters = memory(kernel.GetCurrentProcess())
    receipt = {
        'purpose': 'visual background only; no contour extraction or analytical elevation product',
        'source': 'swissALTI3D 2024/2 DTM, ©swisstopo / Swiss OGD',
        'inputs': sources, 'horizontalReference': 'EPSG:2056', 'verticalReference': 'LN02 / EPSG:5728',
        'bounds': BOUNDS, 'pixelSizeMetres': CELL, 'shape': [SIZE, SIZE],
        'pixelCentre': 'E=2624000+(column+0.5)*0.5; N=1093000-(row+0.5)*0.5',
        'method': 'native 3×3 Horn slope normal; grid-north azimuth 315°, altitude 45°, z factor 1',
        'greyMapping': '96+159*max(0, normal dot light); viewer opacity 0.5',
        'nodata': 'transparent if any of nine samples invalid, including outer one-pixel rim',
        'validPixels': valid_pixels, 'requests': 0, 'newContours': 0, 'processingThreads': 1,
        'stripRows': STRIP, 'gdalCacheBytes': 32*1024**2,
        'peakWorkingSetBytes': counters.peak, 'elapsedSeconds': time.monotonic()-started,
        'outputBytes': target.stat().st_size, 'outputSha256': digest(target),
        'implementationSha256': digest(__file__),
        'limits': {'workingSetBytes': guard['workingSetMaximum'],
                   'privateCommitBytes': guard['privateCommitMaximum'],
                   'seconds': 60, 'outputBytes': 64_000_000},
        'limitations': 'No vertical transformation, source-epoch/accuracy qualification unchanged; grid north is not true north.'}
    (output/'background-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.data_root, args.output), indent=2))
