"""Bounded Swiss native-source acquisition/inspection; no terrain reconstruction."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import urllib.parse
import urllib.request
import zipfile

import numpy as np
from pyproj import Transformer
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from meridian_paths import resolve_storage_roots

BASE = 'https://data.geo.admin.ch/api/stac/v0.9'
API = 'https://api3.geo.admin.ch/rest/services/api'
BOUNDS = (2624000, 1091000, 2626000, 1093000)
TILES = ('2624-1091', '2624-1092', '2625-1091', '2625-1092')
PRODUCTS = {
    'swissimage-dop10': ('2023', '_0.1_2056.tif'),
    'swisssurface3d-raster': ('2021', '_0.5_2056_5728.tif'),
    'swissalti3d': ('2024', '_0.5_2056_5728.tif'),
    'swisssurface3d': ('2021', '_2056_5728.las.zip'),
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def get_json(url, path):
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    with urllib.request.urlopen(url, timeout=60) as r:
        data = json.load(r)
    write_json(path, data)
    return data


def identify(layer, geometry, envelope=False):
    return API + '/MapServer/identify?' + urllib.parse.urlencode({
        'geometry': geometry, 'geometryType': 'esriGeometryEnvelope' if envelope else 'esriGeometryPoint',
        'sr': 2056, 'layers': 'all:' + layer, 'tolerance': 0,
        'mapExtent': ','.join(map(str, BOUNDS)), 'imageDisplay': '1000,1000,96',
        'returnGeometry': 'true', 'lang': 'en', 'limit': 100,
    })


def discovery(root):
    metadata = root / 'metadata'
    transform = Transformer.from_crs(2056, 4326, always_xy=True)
    bbox = transform.transform_bounds(*BOUNDS, densify_pts=21)
    places = {}
    for name in ('Riffelhorn', 'Riffelsee'):
        url = API + '/SearchServer?' + urllib.parse.urlencode({'searchText': name, 'type': 'locations', 'origins': 'gazetteer', 'sr': 2056})
        places[name] = {'url': url, 'response': get_json(url, metadata / (name + '.json'))}
    evidence = {}
    for layer in ('images-swissimage-dop10.metadata', 'swisssurface3d.metadata', 'swisssurface3d-raster.metadata', 'lubis-bildstreifen'):
        url = identify('ch.swisstopo.' + layer, ','.join(map(str, BOUNDS)), True)
        evidence[layer] = {'url': url, 'response': get_json(url, metadata / (layer + '.json'))}
    assets = []
    for product, (year, suffix) in PRODUCTS.items():
        collection = 'ch.swisstopo.' + product
        get_json(BASE + '/collections/' + collection, metadata / (collection + '.json'))
        query = BASE + '/collections/' + collection + '/items?' + urllib.parse.urlencode({'bbox': ','.join(map(str, bbox)), 'limit': 100})
        response = get_json(query, metadata / (collection + '-aoi.json'))
        if any(link['rel'] == 'next' for link in response.get('links', [])):
            raise ValueError('Bounded query unexpectedly paginated; inspect before acquiring')
        for tile in TILES:
            item_id = f'{product}_{year}_{tile}'
            if not any(f['id'] == item_id for f in response['features']):
                raise ValueError('Selected item absent from bounded query: ' + item_id)
            item_url = BASE + '/collections/' + collection + '/items/' + item_id
            item = get_json(item_url, metadata / (item_id + '.json'))
            key = item_id + suffix
            asset = item['assets'][key]
            multihash = asset['checksum:multihash'].lower()
            if not multihash.startswith('1220') or len(multihash) != 68:
                raise ValueError('Expected authoritative SHA256 multihash')
            assets.append({'product': product, 'tile': tile, 'item_id': item_id,
                           'item_url': item_url, 'item_properties': item['properties'],
                           'asset': asset, 'path': 'originals/' + product + '/' + key,
                           'expected_sha256': multihash[4:]})
    plan = {'aoi': {'crs': 'EPSG:2056', 'bounds': BOUNDS, 'width_m': 2000, 'height_m': 2000,
                    'wgs84_bounds': bbox, 'centre_wgs84': transform.transform(2625000, 1092000)},
            'place_evidence': places, 'map_metadata': evidence, 'assets': assets}
    write_json(metadata / 'acquisition-plan.json', plan)
    return plan


def download(root, record):
    path = root / record['path']
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if sha(path) != record['expected_sha256']:
            raise ValueError('Retained original hash changed: ' + path.name)
        return
    temp = path.with_suffix(path.suffix + '.partial')
    with urllib.request.urlopen(record['asset']['href'], timeout=120) as r, temp.open('wb') as f:
        shutil.copyfileobj(r, f, length=1024 * 1024)
        expected_length = r.headers.get('Content-Length')
    if expected_length and temp.stat().st_size != int(expected_length):
        raise ValueError('Download length mismatch')
    if sha(temp) != record['expected_sha256']:
        raise ValueError('Authoritative checksum mismatch: ' + path.name)
    temp.rename(path)
    write_json(root / 'metadata' / (path.name + '.receipt.json'), {
        'download_utc': datetime.now(timezone.utc).isoformat(), 'url': record['asset']['href'],
        'bytes': path.stat().st_size, 'sha256': record['expected_sha256']})


def raster_metadata(path):
    with rasterio.open(path) as src:
        missing = 0
        black_rgb = 0
        minimum, maximum = float('inf'), float('-inf')
        for _, window in src.block_windows(1):
            mask = src.read_masks(1, window=window)
            missing += int(np.count_nonzero(mask == 0))
            if src.count == 3:
                black_rgb += int(np.count_nonzero(np.all(src.read(window=window) == 0, axis=0)))
            if src.count == 1:
                data = src.read(1, window=window, masked=True)
                if data.count():
                    minimum = min(minimum, float(data.min()))
                    maximum = max(maximum, float(data.max()))
        return {'dimensions': [src.width, src.height], 'bands': src.count,
                'dtype': src.dtypes, 'crs_wkt': src.crs.to_wkt(), 'epsg': src.crs.to_epsg(),
                'bounds': list(src.bounds), 'transform': list(src.transform)[:6],
                'pixel_size_m': list(src.res), 'nodata': src.nodata, 'missing_cells_band1': missing,
                'all_zero_rgb_cells': black_rgb if src.count == 3 else None,
                'compression': str(src.compression), 'is_tiled': src.is_tiled,
                'block_shapes': src.block_shapes, 'overviews': src.overviews(1),
                'image_structure': src.tags(ns='IMAGE_STRUCTURE'), 'tags': src.tags(),
                'units': src.units, 'colour_interpretation': [str(c) for c in src.colorinterp],
                'elevation_range_m': [minimum, maximum] if src.count == 1 else None}


def las_metadata(path, tile):
    """Read uncompressed LAS 1.2 formats 0-3 in chunks; preserve vendor originals."""
    with path.open('rb') as f:
        header = f.read(227)
        if header[:4] != b'LASF' or tuple(header[24:26]) != (1, 2):
            raise ValueError('Inspection supports LAS 1.2 only; inspect new format explicitly')
        header_size, offset, vlr_count = struct.unpack_from('<HII', header, 94)
        fmt, length, count = struct.unpack_from('<BHI', header, 104)
        if fmt not in (0, 1, 2, 3) or length < (20, 28, 26, 34)[fmt]:
            raise ValueError('Unexpected LAS point layout')
        scales = np.array(struct.unpack_from('<3d', header, 131))
        offsets = np.array(struct.unpack_from('<3d', header, 155))
        vlrs = []
        f.seek(header_size)
        for _ in range(vlr_count):
            record = f.read(54)
            _, user, rid, size, description = struct.unpack('<H16sHH32s', record)
            payload = f.read(size)
            item = {'user': user.rstrip(b'\0').decode(errors='replace'), 'record_id': rid,
                    'description': description.rstrip(b'\0').decode(errors='replace'), 'bytes': size}
            if rid == 34735:
                values = struct.unpack('<' + 'H' * (size // 2), payload)
                item['geokeys_raw'] = list(values)
            elif rid == 34737:
                item['geoascii'] = payload.decode(errors='replace')
            vlrs.append(item)
        fields = ['x', 'y', 'z', 'return_bits', 'class_bits']
        formats = ['<i4', '<i4', '<i4', 'u1', 'u1']
        positions = [0, 4, 8, 14, 15]
        if fmt in (1, 3):
            fields.append('gps'); formats.append('<f8'); positions.append(20)
        dtype = np.dtype({'names': fields, 'formats': formats, 'offsets': positions, 'itemsize': length})
        classes = np.zeros(32, dtype=np.int64)
        returns = np.zeros(8, dtype=np.int64)
        total_returns = np.zeros(8, dtype=np.int64)
        bins = np.zeros((10, 10), dtype=np.int64)
        first_bins = np.zeros_like(bins)
        minima, maxima = np.full(3, np.inf), np.full(3, -np.inf)
        gps_min, gps_max = np.inf, -np.inf
        gps_days = {}
        f.seek(offset)
        seen = 0
        tile_e, tile_n = [int(x) * 1000 for x in tile.split('-')]
        while seen < count:
            points = np.fromfile(f, dtype=dtype, count=min(250000, count - seen))
            if not len(points):
                raise ValueError('Truncated LAS points')
            xyz = np.column_stack([points[c] for c in ('x', 'y', 'z')]) * scales + offsets
            if not np.isfinite(xyz).all() or np.any(xyz[:, :2] < [tile_e, tile_n]) or np.any(xyz[:, :2] > [tile_e + 1000, tile_n + 1000]):
                raise ValueError('Invalid/out-of-tile point coordinates')
            minima = np.minimum(minima, xyz.min(0)); maxima = np.maximum(maxima, xyz.max(0))
            classes += np.bincount(points['class_bits'] & 31, minlength=32)
            returns += np.bincount(points['return_bits'] & 7, minlength=8)
            total_returns += np.bincount((points['return_bits'] >> 3) & 7, minlength=8)
            col = np.clip(((xyz[:, 0] - tile_e) / 100).astype(int), 0, 9)
            row = np.clip(((xyz[:, 1] - tile_n) / 100).astype(int), 0, 9)
            np.add.at(bins, (row, col), 1)
            first = (points['return_bits'] & 7) == 1
            np.add.at(first_bins, (row[first], col[first]), 1)
            if 'gps' in fields:
                gps_min = min(gps_min, float(points['gps'].min())); gps_max = max(gps_max, float(points['gps'].max()))
                if struct.unpack_from('<H', header, 6)[0] & 1:
                    days, numbers = np.unique(np.floor((points['gps'] + 1e9) / 86400).astype(np.int64), return_counts=True)
                    for day, number in zip(days, numbers):
                        date = (datetime(1980, 1, 6) + timedelta(days=int(day))).date().isoformat()
                        gps_days[date] = gps_days.get(date, 0) + int(number)
            seen += len(points)
        if path.stat().st_size < offset + count * length:
            raise ValueError('LAS declared record count exceeds file length')
    return {'version': '1.2', 'point_format': fmt, 'point_record_bytes': length,
            'point_count': count, 'xyz_min': minima.tolist(), 'xyz_max': maxima.tolist(),
            'scales': scales.tolist(), 'offsets': offsets.tolist(), 'vlrs': vlrs,
            'global_encoding': struct.unpack_from('<H', header, 6)[0],
            'system_identifier': header[26:58].rstrip(b'\0').decode(errors='replace'),
            'generating_software': header[58:90].rstrip(b'\0').decode(errors='replace'),
            'creation_day_year': list(struct.unpack_from('<HH', header, 90)),
            'classification_counts': {str(i): int(n) for i, n in enumerate(classes) if n},
            'return_number_counts': {str(i): int(n) for i, n in enumerate(returns) if n},
            'number_of_returns_counts': {str(i): int(n) for i, n in enumerate(total_returns) if n},
            'gps_time_range_raw': [gps_min, gps_max] if fmt in (1, 3) else None,
            'acquisition_gps_date_counts': dict(sorted(gps_days.items())),
            'gps_date_note': 'Adjusted standard GPS time + 1e9 seconds since 1980-01-06. GPS timescale, not UTC; no leap-second conversion. Creation year/day is file generation, not acquisition.',
            'all_return_density_per_m2': count / 1e6,
            'first_return_density_per_m2': int(returns[1]) / 1e6,
            'density_100m_cells_all_returns': (bins / 10000).tolist(),
            'density_100m_cells_first_returns': (first_bins / 10000).tolist(),
            'density_note': 'Plan-area counts; repeated returns/flight overlaps do not equal independent surface samples. Row 0 south, column 0 west. No terrain raster is generated.'}


def inspect(root, plan):
    records = []
    for record in plan['assets']:
        path = root / record['path']
        if sha(path) != record['expected_sha256']:
            raise ValueError('Original does not match authoritative checksum')
        result = dict(record)
        result.update(bytes=path.stat().st_size, sha256=sha(path))
        result['receipt'] = json.loads((root / 'metadata' / (path.name + '.receipt.json')).read_text())
        if path.suffix == '.tif':
            result['actual_file'] = raster_metadata(path)
        else:
            extracted = root / 'extracted' / path.stem
            extracted.mkdir(parents=True, exist_ok=True)
            members = []
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if Path(info.filename).name != info.filename:
                        raise ValueError('Unexpected nested archive layout')
                    target = extracted / info.filename
                    with archive.open(info) as src:
                        h = hashlib.sha256()
                        if target.exists():
                            for block in iter(lambda: src.read(1024 * 1024), b''):
                                h.update(block)
                            if sha(target) != h.hexdigest():
                                raise ValueError('Retained extraction changed')
                        else:
                            with target.open('wb') as dst:
                                for block in iter(lambda: src.read(1024 * 1024), b''):
                                    dst.write(block); h.update(block)
                    members.append({'path': target.relative_to(root).as_posix(), 'bytes': info.file_size, 'sha256': h.hexdigest()})
                    if target.suffix.lower() == '.las':
                        result['actual_file'] = las_metadata(target, record['tile'])
            result['extracted_members'] = members
        records.append(result)
        print('INSPECTED', path.name, flush=True)
        write_json(root / 'metadata' / 'file-inventory.json', records)
    return records


def validate_inventory(records):
    """Prove exact AOI coverage and native-file grid compatibility, without resampling."""
    if len(records) != 16 or len({(r['product'], r['tile']) for r in records}) != 16:
        raise ValueError('Expected exactly four tiles in each of four products')
    for product in PRODUCTS:
        selected = [r for r in records if r['product'] == product]
        if {r['tile'] for r in selected} != set(TILES):
            raise ValueError('Missing or unexpected tile')
        for record in selected:
            e, n = [int(v) * 1000 for v in record['tile'].split('-')]
            actual = record['actual_file']
            if product == 'swisssurface3d':
                if actual['point_count'] <= 0:
                    raise ValueError('Empty point cloud')
                continue
            spacing = 0.1 if product == 'swissimage-dop10' else 0.5
            if actual['epsg'] != 2056 or actual['bounds'] != [e, n, e + 1000, n + 1000]:
                raise ValueError('Unexpected CRS or tile bounds')
            if not np.allclose(actual['transform'], [spacing, 0, e, 0, -spacing, n + 1000], rtol=0, atol=1e-9):
                raise ValueError('Unexpected pixel-edge affine or orientation')
            if actual['dimensions'] != [int(1000 / spacing)] * 2 or actual['missing_cells_band1']:
                raise ValueError('Unexpected raster dimensions or missing coverage')
    return {'raster_coverage_percent': 100, 'bounds': list(BOUNDS),
            'height_grids_identical': True, 'horizontal_reprojection_required': False,
            'north_up': True, 'rotation_or_mirroring': False,
            'imagery_to_height_cell_ratio_per_axis': 5,
            'pixel_centres_note': 'Grids share edges; imagery centres are 0.05 m from tile edge, height centres 0.25 m. Not identical centres.',
            'point_cloud_note': 'Four complete tile footprints; populated 100 m bins do not establish gap-free 1 m sampling.',
            'vertical_note': 'LN02 (EPSG:5728), metres, established by official product metadata; not encoded in these TIFF horizontal CRS tags or LAS VLRs.'}


def previews(root, records):
    """Offline 2-D inspection only. Native originals remain untouched."""
    from PIL import Image, ImageDraw
    selected = [r for r in records if r['product'] == 'swissimage-dop10']
    canvas = Image.new('RGB', (2000, 2040))
    for r in selected:
        e, n = [int(v) * 1000 for v in r['tile'].split('-')]
        with rasterio.open(root / r['path']) as src:
            data = src.read(out_shape=(3, 1000, 1000), resampling=rasterio.enums.Resampling.nearest)
        canvas.paste(Image.fromarray(data.transpose(1, 2, 0)), (e - BOUNDS[0], BOUNDS[3] - n - 1000))
    draw = ImageDraw.Draw(canvas)
    for label, e, n in [('Riffelhorn', 2624809.668, 1092252.405), ('Riffelsee', 2625061, 1092475)]:
        x, y = e - BOUNDS[0], BOUNDS[3] - n
        draw.ellipse((x-5, y-5, x+5, y+5), fill='red')
        draw.text((x+8, y), label, fill='red')
    draw.text((10, 2010), 'North up; 1 m inspection preview; native observation 25 cm; ©swisstopo', fill='white')
    target = root / 'diagnostics'
    target.mkdir(exist_ok=True)
    canvas.save(target / 'aoi-orthophoto-overview.png')
    for label, e, n in [('riffelhorn', 2624809.668, 1092252.405), ('riffelsee', 2625061, 1092475), ('southern-landforms', 2625000, 1091500)]:
        # Snap the 150 m inspection window to distributed pixel edges, not new observations.
        west, south = np.floor((e - 75) * 10) / 10, np.floor((n - 75) * 10) / 10
        crop = Image.new('RGB', (1500, 1530))
        for r in selected:
            with rasterio.open(root / r['path']) as src:
                b = src.bounds
                left, bottom, right, top = max(west, b.left), max(south, b.bottom), min(west+150, b.right), min(south+150, b.top)
                if left >= right or bottom >= top:
                    continue
                window = rasterio.windows.from_bounds(left, bottom, right, top, src.transform).round_offsets().round_lengths()
                data = src.read(window=window)
            crop.paste(Image.fromarray(data.transpose(1, 2, 0)), (round((left-west)*10), round((south+150-top)*10)))
        ImageDraw.Draw(crop).text((10, 1505), '150 m square; distributed 10 cm grid, native 25 cm observation; ©swisstopo', fill='white')
        crop.save(target / (label + '-distributed-10cm-crop.png'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('discover', 'download', 'inspect', 'verify', 'preview'))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    data = resolve_storage_roots(repository_root=repo, require_data=True).data
    root = data / 'sources/atlas/riffelhorn/swisstopo-2021-2024'
    if args.mode == 'discover':
        plan = discovery(root)
        print('Selected', len(plan['assets']), 'assets; no source downloads')
    else:
        plan = json.loads((root / 'metadata/acquisition-plan.json').read_text(encoding='utf-8'))
        if args.mode == 'download':
            for record in plan['assets']:
                download(root, record)
                print('VERIFIED DOWNLOAD', record['path'], flush=True)
        elif args.mode == 'inspect':
            inspect(root, plan)
        else:
            records = json.loads((root / 'metadata/file-inventory.json').read_text())
            validation = validate_inventory(records)
            write_json(root / 'metadata/spatial-validation.json', validation)
            if args.mode == 'preview':
                previews(root, records)
                print('External 2-D inspection previews written; no terrain product generated')
                sys.exit(0)
            for record in records:
                if sha(root / record['path']) != record['sha256']:
                    raise ValueError('Original changed')
                for member in record.get('extracted_members', []):
                    if sha(root / member['path']) != member['sha256']:
                        raise ValueError('Extraction changed')
            print('All', len(records), 'originals and retained extraction hashes PASS')
