"""Transform retained contour XY and warp an existing shaded PNG; no DEM processing."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import time

for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['PROJ_NETWORK'] = 'OFF'
os.environ['GDAL_PAM_ENABLED'] = 'NO'
SOURCE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('retained', SOURCE.parent/'contour-visual-review/build.py')
retained = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retained)


def prepare(data, output):
    import numpy as np
    import pyproj
    from pyproj.transformer import TransformerGroup
    import rasterio
    from rasterio.transform import from_origin
    from rasterio.warp import reproject, Resampling
    from PIL import Image
    started = time.monotonic()
    if output.exists():
        raise ValueError('Fresh external product directory required')
    history = data/'experiments/atlas/source-aware-contours-v1'
    pilot = SOURCE.parent/'contour-pilot'
    seal = json.loads((pilot/'genuine-rerun-receipt.json').read_text())
    retained.verify_history(history, seal)
    pins = json.loads((pilot/'input-pins.json').read_text())
    for entry in pins['inputs']:
        if retained.digest(data/entry['path']) != entry['sha256']:
            raise ValueError('Original input pin changed')
    group = TransformerGroup(2056, 4326, always_xy=True, allow_ballpark=False)
    mercator = TransformerGroup(2056, 3857, always_xy=True, allow_ballpark=False)
    if not group.best_available or not mercator.best_available:
        raise ValueError('Required offline horizontal operation unavailable')
    xy, projected = group.transformers[0], mercator.transformers[0]
    inverse = pyproj.Transformer.from_pipeline(xy.definition)
    output.mkdir(parents=True)
    (output/'inputs').mkdir()
    products = []
    roundtrip_max = 0
    for name, expected in zip(retained.PRODUCTS, retained.EXPECTED):
        source = history/'execution-3/processing/run-1'/name
        manifest = json.loads((source/'manifest.json').read_text())
        vertices = lines = 0
        target = output/'inputs'/f'{name}.geojson'
        with target.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write('{"type":"FeatureCollection","features":[')
            for level in range(2000, 3201, 10):
                path = source/f'{level}.ndjson'
                if retained.digest(path) != manifest['geometry']['levels'][str(level)]['sha256']:
                    raise ValueError('Retained contour payload changed')
                for raw in path.read_text(encoding='utf-8').splitlines():
                    record = json.loads(raw)
                    vertices += retained.validate_record(record, level)
                    coordinates = np.asarray(record['coordinates'], dtype=np.float64)
                    lon, lat = xy.transform(coordinates[:, 0], coordinates[:, 1], errcheck=True)
                    e, n = inverse.transform(lon, lat, direction='INVERSE', errcheck=True)
                    roundtrip_max = max(roundtrip_max, float(np.hypot(e-coordinates[:, 0], n-coordinates[:, 1]).max()))
                    properties = {'elevation_m': level, 'index100': record['index'],
                                  'source_product': name, 'source_line': f"{level}:{record['line']}",
                                  'vertical_ref': 'LN02', 'units': 'm'}
                    feature = {'type': 'Feature', 'id': lines+1, 'properties': properties,
                               'geometry': {'type': 'LineString', 'coordinates': np.column_stack((lon, lat)).tolist()}}
                    if lines:
                        stream.write(',')
                    json.dump(feature, stream, separators=(',', ':'), allow_nan=False)
                    lines += 1
                    if time.monotonic()-started > 120 or stream.tell() > 64_000_000:
                        raise RuntimeError('Preparation time/file allowance reached')
            stream.write(']}\n')
        if (vertices, lines) != expected[:2] or roundtrip_max > 0.01:
            raise ValueError('Counts or horizontal round-trip validation failed')
        products.append({'id': name, 'sourceManifestSha256': retained.digest(source/'manifest.json'),
                         'sourceManifest': manifest, 'vertices': vertices, 'lines': lines,
                         'geojsonBytes': target.stat().st_size, 'geojsonSha256': retained.digest(target)})
    # Reproject the retained intensity/alpha image only; never read an elevation raster.
    background = data/'experiments/atlas/multiscale-contours-hillshade-v1/background'
    bg = json.loads((background/'background-receipt.json').read_text())
    if retained.digest(background/'hillshade.png') != bg['outputSha256']:
        raise ValueError('Retained shaded background changed')
    edges = []
    for t in np.linspace(0, 1, 101):
        edges.extend([(2624000+2000*t, 1091000), (2624000+2000*t, 1093000),
                      (2624000, 1091000+2000*t), (2626000, 1091000+2000*t)])
    mx, my = projected.transform(*np.asarray(edges).T, errcheck=True)
    left, right, bottom, top = min(mx), max(mx), min(my), max(my)
    cell = 0.75  # projected metres; about 0.52 ground metres at this latitude.
    width, height = int(np.ceil((right-left)/cell)), int(np.ceil((top-bottom)/cell))
    if width*height > 20_000_000:
        raise RuntimeError('Visual image pixel allowance reached')
    transform = from_origin(left, top, cell, cell)
    image = np.asarray(Image.open(background/'hillshade.png'))
    destination = np.zeros((height, width, 2), dtype=np.uint8)
    with rasterio.Env(GDAL_CACHEMAX=32*1024**2, GDAL_NUM_THREADS='1'):
        for band in range(2):
            reproject(image[:, :, band], destination[:, :, band],
                      src_transform=from_origin(2624000, 1093000, 0.5, 0.5), src_crs='EPSG:2056',
                      dst_transform=transform, dst_crs='EPSG:3857', src_nodata=0, dst_nodata=0,
                      resampling=Resampling.bilinear, num_threads=1, warp_mem_limit=32,
                      COORDINATE_OPERATION=projected.definition)
    Image.fromarray(destination).save(output/'hillshade-mercator.png')
    to_lonlat = pyproj.Transformer.from_crs(3857, 4326, always_xy=True)
    corners = [to_lonlat.transform(*point) for point in
               [(left, top), (left+width*cell, top), (left+width*cell, top-height*cell), (left, top-height*cell)]]
    centre = xy.transform(2625000, 1092000)
    lon, lat = xy.transform(*np.asarray(edges).T, errcheck=True)
    receipt = {'id': 'riffelhorn-swiss-contour-mvt-v1', 'sourceBounds': list(retained.BOUNDS),
               'sourceHorizontalReference': 'EPSG:2056', 'deliveryHorizontalReference': 'EPSG:3857 tile grid / WGS84 GeoJSON',
               'verticalReference': 'LN02 / EPSG:5728', 'units': 'm', 'surface': 'DTM',
               'heightTransformation': 'none; elevation attributes copied exactly', 'products': products,
               'operation': {'definition': xy.definition, 'description': xy.description,
                             'reportedAccuracyMetres': xy.accuracy, 'mercatorDefinition': projected.definition,
                             'pyproj': pyproj.__version__, 'proj': pyproj.proj_version_str, 'network': False,
                             'maximumHorizontalRoundtripMetres': roundtrip_max},
               'boundsLonLat': [min(lon), min(lat), max(lon), max(lat)], 'centre': centre,
               'background': {'inputSha256': bg['outputSha256'], 'outputSha256': retained.digest(output/'hillshade-mercator.png'),
                              'operation': 'bilinear horizontal image warp only, 0.75 projected metres/pixel; no slope/elevation derivation',
                              'imageCoordinates': corners, 'shape': [height, width], 'mercatorAffine': list(transform)[:6]},
               'rights': '©swisstopo / Swiss OGD; retain original source notices and qualifications',
               'limitations': ['retained subset only; not global coverage', 'single-run source evidence; genuine repeatability incomplete',
                               'quantisation is visual loss, not a new elevation measurement', 'no DSM/DTM fusion'],
               'elapsedSeconds': time.monotonic()-started, 'requests': 0, 'newContours': 0}
    retained.verify_history(history, seal)
    if sum(path.stat().st_size for path in output.rglob('*') if path.is_file()) > 100_000_000:
        raise RuntimeError('Preparation storage allowance reached')
    (output/'product.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'vertices': sum(p['vertices'] for p in products), 'roundtripMaxMetres': roundtrip_max,
                      'elapsedSeconds': receipt['elapsedSeconds'], 'imageShape': [height, width]}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); prepare(args.data_root, args.output)
