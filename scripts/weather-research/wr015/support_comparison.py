"""WR015: one qualified support comparison; no forecast correction or acquisition."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for name in ('wr007', 'wr008', 'wr009'):
    sys.path.insert(0, str(HERE.parent / name))
sys.path.insert(0, str(REPO / 'scripts/atlas/portable-spike/geometry-crs'))
import gfs_field_pilot as field
import gfs_point_sampling as spatial
from gfs_precipitation_pilot import sections
from native_proj import NativeProj, PIPELINE

Error = field.IntegrityError
PIN = HERE / 'input-pins.json'


def checked_pin():
    pin = json.loads(PIN.read_text(encoding='utf-8'))
    for name, expected in pin['dependencies'].items():
        if field.digest(REPO / name) != expected:
            raise Error('Accepted evidence dependency changed')
    return pin


def matched(metadata, forecast_metadata, grid_seal, forecast_grid_seal):
    """A shared grid alone cannot establish a producing-product relationship."""
    if grid_seal != forecast_grid_seal:
        raise Error('Forecast/orography encoded grids differ')
    for key in ('centre', 'subCentre', 'generatingProcessIdentifier', 'dataDate', 'dataTime',
                'forecastTime', 'stepUnits', 'validityDate', 'validityTime', 'stepType'):
        if metadata.get(key) != forecast_metadata.get(key):
            raise Error('Forecast configuration/time not matched: ' + key)
    if (metadata.get('discipline'), metadata.get('parameterCategory'), metadata.get('parameterNumber'),
            metadata.get('typeOfFirstFixedSurface')) != (0, 3, 5, 1):
        raise Error('Not surface geopotential height')
    if metadata.get('units') != 'm' or metadata.get('stepType') != 'instant':
        raise Error('Unexpected decoder unit/temporal mapping')
    return {'status': 'VERIFIED SAME DELIVERED PRODUCT', 'grid_section3_sha256': grid_seal,
            'historical_executable_version': 'UNKNOWN; encoded process96 is not a suite version',
            'internal_orography_generation': 'NOT TESTED', 'static_across_runs_or_steps': 'NOT TESTED'}


def validate_parent(source, acquisition):
    if (acquisition.get('status') != 206 or
            acquisition.get('url') != source['object_url'] or
            acquisition.get('requested_range') != [source['range_start'], source['range_end_inclusive']] or
            acquisition.get('headers', {}).get('ETag', '').strip('"') != source['parent_etag'] or
            acquisition.get('headers', {}).get('Content-Range') !=
            f"bytes {source['range_start']}-{source['range_end_inclusive']}/{source['parent_bytes']}"):
        raise Error('Unverified same-object orography/forecast relationship')


def compare_arrays(a, b, mask, other, metadata):
    """Prospective E4/D2 extension of WR007's two-operation binary32 diagnostic."""
    import numpy as np
    if (metadata['binaryScaleFactor'], metadata['decimalScaleFactor'],
            metadata['dataRepresentationTemplateNumber']) != (4, 2, 3):
        raise Error('Unsupported prospective packing profile')
    if a.shape != b.shape or a.shape != mask.shape or b.shape != other.shape or not np.array_equal(mask, other):
        raise Error('Independent array alignment/missingness mismatch')
    a, b = a[~mask], b[~other]
    if not a.size or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise Error('Non-finite independent values')
    ref = metadata['referenceValue']
    q = (a * 100 - ref) / 16
    integers = np.rint(q)
    residual = np.abs(q - integers)
    if np.any(integers < 0) or np.any(integers * 16 >= 2**24) or residual.max() > 64 * np.finfo(float).eps * max(float(np.abs(q).max()), 1):
        raise Error('Unsupported integer lattice/precision')
    scaled = (integers * 16).astype(np.float32)
    summed = scaled + np.float32(ref)
    coefficient = np.float32(.01)
    predicted = (summed * coefficient).astype(float)
    bounds = (np.abs(np.spacing(summed)).astype(float) * .5 * abs(float(coefficient))
              + np.abs(integers * 16 + ref) * abs(float(coefficient) - .01)
              + np.abs(np.spacing(predicted.astype(np.float32))).astype(float) * .5
              + 8 * np.finfo(float).eps * np.abs(a))
    differences = np.abs(a - b)
    if not np.array_equal(predicted, b) or np.any(differences > bounds):
        raise Error('Unexplained independent numerical disagreement')
    return {'status': 'INDEPENDENT AGREEMENT; EXPLAINED BINARY32 ROUNDING',
            'compared_cells': int(a.size), 'mask_agreement': True,
            'exact_equality_cells': int(np.count_nonzero(a == b)),
            'maximum_absolute_difference_native': float(differences.max()),
            'mean_absolute_difference_native': float(differences.mean()),
            'maximum_analytic_bound_native': float(bounds.max()),
            'exact_binary32_profile_cells': int(np.count_nonzero(predicted == b)),
            'maximum_integer_lattice_residual': float(residual.max()),
            'policy': 'prospective per-cell bound and exact g2clib arithmetic profile; no fitted tolerance'}


def terrain_cell(easting, northing, bounds, posting=.5):
    if not all(math.isfinite(x) for x in (easting, northing)) or posting != .5:
        raise Error('Unsupported coordinate/posting')
    left, bottom, right, top = bounds
    if not left <= easting < right or not bottom < northing <= top:
        raise Error('Outside declared half-open terrain support')
    return math.floor((top - northing) / posting), math.floor((easting - left) / posting)


def valid_terrain(value, masked):
    if masked or not math.isfinite(value) or value == -9999:
        raise Error('Missing/invalid native terrain cell')
    return value


def difference(model, terrain, model_reference, terrain_reference, quantity, support, purpose='support'):
    if purpose != 'support':
        raise Error('Temperature correction or forecast-skill inference prohibited')
    if not all(math.isfinite(x) for x in (model, terrain)):
        raise Error('Non-finite height')
    if not model_reference or not terrain_reference or model_reference != terrain_reference or quantity != 'same-height-quantity':
        return {'status': 'UNRESOLVED VERTICAL COMPARABILITY', 'signed_difference': None,
                'absolute_difference': None, 'reason': 'No established quantity/reference equivalence or vertical transformation'}
    if support != 'qualified-point-to-point':
        raise Error('Unsupported grid-cell mean/terrain aggregation assumption')
    signed = model - terrain
    return {'status': 'QUALIFIED SUPPORT DIFFERENCE', 'signed_difference': signed,
            'absolute_difference': abs(signed), 'convention': 'model-ground height minus Atlas terrain height'}


def model_query(sampler, latitude, longitude, method):
    # Only WR008's accepted geometry/arithmetic is reused. Kelvin labels are removed,
    # not numerically converted; the authoritative quantity remains geopotential height.
    result = sampler.query({'latitude': latitude, 'longitude': longitude, 'method': method})
    if result['status'] != 'OK':
        raise Error('Unsupported model-ground query: ' + result['status'])
    result['native_value'] = result.pop('temperature_K')
    for node in result['nodes']:
        node['native_value'] = node.pop('temperature_K')
    result['decoder_unit_label'] = 'm'
    result['physical_quantity'] = 'geopotential height; authoritative table unit gpm'
    return result


def gdal_reference(path, output, pin):
    import numpy as np
    import rasterio
    field.pinned_input(path, pin)
    with rasterio.Env(GRIB_NORMALIZE_UNITS='NO', GRIB_ADJUST_LONGITUDE_RANGE='NO', GDAL_CACHEMAX=16_000_000):
        with rasterio.open(path) as ds:
            tags = ds.tags(1)
            required = {'GRIB_ELEMENT': 'HGT', 'GRIB_UNIT': '[gpm]', 'GRIB_SHORT_NAME': '0-SFC',
                        'GRIB_REF_TIME': '1736899200', 'GRIB_VALID_TIME': '1736985600',
                        'GRIB_FORECAST_SECONDS': '86400', 'GRIB_PDS_PDTN': '0'}
            if ds.count != 1 or any(tags.get(k) != v for k, v in required.items()):
                raise Error('Independent parameter/unit/time mapping not verified')
            if (ds.height, ds.width) != (721, 1440) or tuple(ds.transform) != (.25, 0, -.125, 0, -.25, 90.125, 0, 0, 1):
                raise Error('Independent grid alignment not verified')
            if ds.crs.to_dict().get('R') != 6371229:
                raise Error('Independent model Earth shape mismatch')
            values, mask = ds.read(1), ds.read_masks(1) == 0
            result = {'gdal': rasterio.__gdal_version__, 'rasterio': rasterio.__version__,
                      'numpy': np.__version__, 'python': sys.version.split()[0],
                      'metadata': tags, 'transform': list(ds.transform), 'crs': ds.crs.to_wkt(),
                      'independence': 'GDAL/degrib/g2clib GRIB unpacking, not ecCodes',
                      'resources': spatial.process_memory()}
    np.savez(output.with_suffix('.npz'), values=values, mask=mask)
    output.with_suffix('.json').write_bytes(field.canonical(result))


def run(path, forecast, data_root, gdal_python, output):
    import numpy as np
    import rasterio
    from rasterio.windows import Window
    from pyproj import Transformer
    pin = checked_pin()
    field.require_external(output)
    if output.exists() or output.with_name(output.stem + '-resources.json').exists():
        raise Error('Refuse receipt overwrite')
    validate_parent(pin['source'], pin['acquisition'][-1])
    body = field.pinned_input(path, pin)
    original = field.pinned_input(forecast, pin['forecast'])
    seal = hashlib.sha256(sections(body)[3]).hexdigest()
    forecast_seal = hashlib.sha256(sections(original)[3]).hexdigest()
    values, mask, latitudes, longitudes, metadata, versions = field.eccodes_decode(path, pin)
    relationship = matched(metadata, pin['forecast']['expected'], seal, forecast_seal)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        prefix = Path(temporary) / 'independent'
        subprocess.run([str(gdal_python), '-B', str(Path(__file__).resolve()), '--gdal-only',
                        '--input', str(path), '--output', str(prefix)], check=True)
        reference = json.loads(prefix.with_suffix('.json').read_text())
        with np.load(prefix.with_suffix('.npz'), allow_pickle=False) as second:
            agreement = compare_arrays(values, second['values'], mask, second['mask'], metadata)
        temporary_bytes = sum(p.stat().st_size for p in Path(temporary).iterdir())
    del latitudes, longitudes
    sampler = spatial.Sampler(values, mask, metadata)
    records = []
    with NativeProj() as crs:
        if PIPELINE != pin['horizontal_pipeline']:
            raise Error('Unsupported horizontal transformation')
        xy = crs.xy([p['easting'] for p in pin['locations']], [p['northing'] for p in pin['locations']],
                    'EPSG:2056', 'OGC:CRS84')
        operation = crs.operation('EPSG:2056', 'OGC:CRS84')[1]
        reference_xy = Transformer.from_pipeline(operation).transform(
            [p['easting'] for p in pin['locations']], [p['northing'] for p in pin['locations']])
        if xy != tuple(tuple(x) for x in reference_xy):
            raise Error('Horizontal binding/reference dispatch disagreement')
        coordinate_receipt = {'operation': operation, 'identity': crs.identity,
                              'network_enabled': False, 'height_transformed': False,
                              'interface_agreement': 'exact; shared PROJ kernel, not independent CRS implementation',
                              'reference_labels': 'OGC:CRS84 longitude-first; GFS spherical grid labels; no 3D Earth reconciliation'}
        for i, site in enumerate(pin['locations']):
            asset = site['atlas_asset']
            terrain = Path(data_root) / asset['path']
            field.require_external(terrain)
            if terrain.stat().st_size != asset['bytes'] or field.digest(terrain) != asset['sha256']:
                raise Error('Native Atlas source identity mismatch')
            row, col = terrain_cell(site['easting'], site['northing'], asset['bounds'])
            with rasterio.Env(GDAL_CACHEMAX=16_000_000):
                with rasterio.open(terrain) as ds:
                    left, bottom, right, top = asset['bounds']
                    if (ds.width, ds.height, ds.crs.to_epsg(), ds.dtypes, ds.nodata) != (2000, 2000, 2056, ('float32',), -9999):
                        raise Error('Atlas schema/CRS/nodata mismatch')
                    if tuple(ds.transform) != (.5, 0, left, 0, -.5, top, 0, 0, 1):
                        raise Error('Atlas registration mismatch')
                    window = Window(col, row, 1, 1)
                    value = valid_terrain(float(ds.read(1, window=window)[0, 0]), ds.read_masks(1, window=window)[0, 0] == 0)
                    centre = list(ds.xy(row, col))
            lon, latitude = xy[0][i], xy[1][i]
            queries = {method: model_query(sampler, latitude, lon, method) for method in site['model_sampling']}
            records.append({'location': site['id'], 'original_coordinate': [site['easting'], site['northing']],
                            'horizontal_crs': site['crs'], 'geographic_lon_lat': [lon, latitude],
                            'setting': site['setting'], 'model_queries': queries,
                            'terrain': {'source': asset, 'row': row, 'column': col, 'cell_centre': centre,
                                        'footprint': [left + col*.5, top-(row+1)*.5, left+(col+1)*.5, top-row*.5],
                                        'value_m': value, 'vertical_reference': 'LN02 EPSG:5728',
                                        'sampling': site['atlas_sampling'], 'precision': 'native float32'},
                            'comparison': difference(queries['BILINEAR']['native_value'], value, None,
                                                     'LN02 EPSG:5728', 'geopotential-height-versus-national-height',
                                                     'qualified-point-to-point'),
                            'support_qualification': 'native model nodes/interpolated orography versus 0.5m DTM cell; no cell-mean equivalence'})
            if field.digest(terrain) != asset['sha256']:
                raise Error('Terrain input mutated')
    if field.digest(path) != pin['input']['sha256'] or field.digest(forecast) != pin['forecast']['input']['sha256']:
        raise Error('Weather input mutated')
    scientific = {'schema': 'meridian-wr015-support-v1', 'outcome': 'B — PARTIAL SUPPORT COMPARISON',
                  'pins_sha256': field.digest(PIN), 'utility_sha256': field.digest(Path(__file__)),
                  'input': pin['input'], 'source': pin['source'], 'actual_metadata': metadata,
                  'forecast_relationship': relationship, 'primary_decoder': versions,
                  'independent_decoder': {k: v for k, v in reference.items() if k != 'resources'},
                  'independent_comparison': agreement, 'coordinates': coordinate_receipt,
                  'grid': sampler.grid.description(), 'atlas_source': pin['atlas_source'],
                  'model_height': {'quantity': 'geopotential height WMO0/3/5', 'eccodes_unit_label': 'm',
                                   'NCEP_authoritative_unit': 'gpm', 'native_conversion': 'none',
                                   'vertical_reference': 'UNRESOLVED exact relation to LN02; no vertical transformation'},
                  'numerical_summary_native': {'finite': int(np.isfinite(values).sum()), 'missing': int(mask.sum()),
                                               'minimum': float(values.min()), 'maximum': float(values.max()),
                                               'mean': float(values.mean()), 'dtype': str(values.dtype)},
                  'locations': records, 'signed_difference_convention': pin['signed_difference_convention'],
                  'limitations': ['No datum/height equivalence established; all scientific differences withheld',
                                  'No model-cell terrain mean or internal orography-generation evidence',
                                  'No lapse rate, forecast correction, skill or mountain safety inference',
                                  'One delivered GFS profile only; no IFS/GEFS orography match tested']}
    output.write_bytes(field.canonical(scientific))
    output.with_name(output.stem + '-resources.json').write_bytes(field.canonical({
        'primary': spatial.process_memory(), 'independent': reference['resources'],
        'sequential_temporary_bytes': temporary_bytes, 'terrain_array_cells_read': 5,
        'additional_source_copies': 0}))
    return scientific


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--forecast', type=Path)
    parser.add_argument('--data-root', type=Path)
    parser.add_argument('--gdal-python', type=Path)
    parser.add_argument('--gdal-only', action='store_true')
    args = parser.parse_args()
    if args.gdal_only:
        field.require_external(args.output)
        if args.output.with_suffix('.npz').exists() or args.output.with_suffix('.json').exists():
            parser.error('Refuse reference overwrite')
        gdal_reference(args.input, args.output, checked_pin())
    else:
        if any(v is None for v in (args.forecast, args.data_root, args.gdal_python)):
            parser.error('--forecast, --data-root and --gdal-python are required; no decoder fallback')
        result = run(args.input, args.forecast, args.data_root, args.gdal_python, args.output)
        print(json.dumps(result['independent_comparison'], indent=2))


if __name__ == '__main__':
    main()
