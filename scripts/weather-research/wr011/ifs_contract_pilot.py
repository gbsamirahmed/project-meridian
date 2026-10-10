"""WR011 finite IFS conformance experiment; no acquisition or production API."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = Path(__file__).resolve().parent
for previous in ('wr007', 'wr008', 'wr009', 'wr010'):
    sys.path.insert(0, str(HERE.parent / previous))
import gfs_field_pilot as field
import gfs_point_sampling as spatial
import gfs_precipitation_pilot as precipitation
import field_compatibility as previous_contract

PIN = HERE / 'input-pins.json'
Error = field.IntegrityError


def checked_pin():
    pin = json.loads(PIN.read_text(encoding='utf-8'))
    for name, seal in pin['dependencies'].items():
        if field.digest(HERE.parent / name) != seal:
            raise Error('Retained WR007-WR010 evidence changed')
    return pin


def sections(body):
    """Single-message framing, retaining ECMWF Section2; not a numerical decoder."""
    field.validate_framing(body)
    result = {}; offset = 16; sequence = []
    while offset < len(body)-4:
        length = int.from_bytes(body[offset:offset+4], 'big')
        if length < 5 or offset+length > len(body)-4:
            raise Error('Malformed section extent')
        number = body[offset+4]
        if number in result:
            raise Error('Duplicate section')
        result[number] = body[offset:offset+length]
        sequence.append(number); offset += length
    if sequence != [1, 2, 3, 4, 5, 6, 7] or offset != len(body)-4:
        raise Error('Unsupported finite IFS section structure')
    return result


class ShiftedGrid(spatial.Grid):
    """Finite global regular-grid adapter, preserving the actual longitude origin."""
    def __init__(self, m):
        if (m.get('gridType'), m.get('gridDefinitionTemplateNumber'), m.get('scanningMode'),
            m.get('shapeOfTheEarth')) != ('regular_ll', 0, 0, 6):
            raise Error('Unsupported grid family/scanning/Earth shape')
        self.nx, self.ny = m['Ni'], m['Nj']
        self.dx, self.dy = m['iDirectionIncrementInDegrees'], m['jDirectionIncrementInDegrees']
        self.north, self.south = m['latitudeOfFirstGridPointInDegrees'], m['latitudeOfLastGridPointInDegrees']
        self.west, self.east = m['longitudeOfFirstGridPointInDegrees'], m['longitudeOfLastGridPointInDegrees']
        self.radius = m['radius']
        if (not all(math.isfinite(x) for x in (self.dx, self.dy, self.west, self.east, self.radius))
            or self.nx < 4 or self.ny < 4 or self.dx <= 0 or self.dy <= 0 or self.radius <= 0
            or (self.north, self.south) != (90, -90) or not 0 <= self.west < 360
            or self.nx*self.dx != 360 or self.east != (self.west+(self.nx-1)*self.dx) % 360
            or self.south != self.north-(self.ny-1)*self.dy or m['numberOfPoints'] != self.nx*self.ny):
            raise Error('Unsupported periodic point-grid geometry')

    def position(self, latitude, longitude):
        native = float(longitude) % 360
        if native == 360: native = 0.0
        signed = native-360 if native >= 180 else native
        return (self.north-float(latitude))/self.dy, ((native-self.west) % 360)/self.dx, native, signed

    def coordinates(self, row, col):
        return self.north-self.dy*row, (self.west+self.dx*col) % 360


class ShiftedSampler(spatial.Sampler):
    def __init__(self, values, mask, metadata):
        self.grid = ShiftedGrid(metadata)
        if values.shape != mask.shape or values.shape != (self.grid.ny, self.grid.nx) or mask.dtype != np.bool_:
            raise Error('Array/mask geometry mismatch')
        self.values, self.mask = values, mask


def temporal(m):
    """Preserve the WR010 discriminant; extend only the inspected increment profile."""
    if m.get('productDefinitionTemplateNumber') == 0:
        return previous_contract.temporal(m)
    try:
        if (m['productDefinitionTemplateNumber'], m['stepType'], m['typeOfStatisticalProcessing'],
            m['numberOfTimeRange'], m['numberOfMissingInStatisticalProcess'], m['typeOfTimeIncrement'],
            m['indicatorOfUnitForTimeIncrement'], m['timeIncrement']) != (8, 'accum', 1, 1, 0, 2, 13, 450):
            raise Error('Unsupported interval/statistical increment profile')
        ref = datetime.strptime(f"{m['dataDate']:08d}{m['dataTime']:04d}", '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
        start_seconds = precipitation.seconds(m['forecastTime'], m['indicatorOfUnitOfTimeRange'])
        duration = precipitation.seconds(m['lengthOfTimeRange'], m['indicatorOfUnitForTimeRange'])
        end = datetime(*(m[k] for k in ['yearOfEndOfOverallTimeInterval', 'monthOfEndOfOverallTimeInterval',
                       'dayOfEndOfOverallTimeInterval', 'hourOfEndOfOverallTimeInterval',
                       'minuteOfEndOfOverallTimeInterval', 'secondOfEndOfOverallTimeInterval']), tzinfo=timezone.utc)
        valid = datetime.strptime(f"{m['validityDate']:08d}{m['validityTime']:04d}", '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
        start = ref+timedelta(seconds=start_seconds)
        if (duration <= 0 or start_seconds < 0 or end != start+timedelta(seconds=duration) or valid != end
            or precipitation.seconds(m['startStep'], m['stepUnits']) != start_seconds
            or precipitation.seconds(m['endStep'], m['stepUnits']) != start_seconds+duration):
            raise Error('Contradictory interval bounds')
    except (KeyError, TypeError, ValueError, OverflowError) as e:
        raise Error('Incomplete interval support') from e
    return {'kind': 'accumulation', 'reference_time': precipitation.stamp(ref), 'valid_time': precipitation.stamp(valid),
            'interval_start': precipitation.stamp(start), 'interval_end': precipitation.stamp(end),
            'duration_seconds': duration, 'forecast_lead_to_start_seconds': start_seconds,
            'forecast_lead_to_end_seconds': start_seconds+duration, 'statistical_process_code': 1,
            'increment': {'type_code': 2, 'unit_code': 13, 'value': 450, 'seconds': 450,
                          'qualification': 'encoded increment; no inferred internal sample count or endpoint algorithm'}}


def concept(identity, m, grid_seal, input_seal):
    profiles = {'temperature': ([0, 0, 0], 'K', 103, 2),
                'precipitation': ([0, 1, 193], 'm', 1, 0),
                'wind_u': ([0, 2, 2], 'm s**-1', 103, 10)}
    if identity not in profiles:
        raise Error('Unacquired field family')
    parameter, units, surface, level = profiles[identity]
    if (m.get('centre'), m.get('tablesVersion'), m.get('localTablesVersion'), m.get('typeOfProcessedData'),
        m.get('marsClass'), m.get('marsType'), m.get('marsStream')) != (98, 33, 1, 1, 'od', 'fc', 'oper'):
        raise Error('Unsupported producer/product/ensemble identity')
    if ([m.get(k) for k in ['discipline', 'parameterCategory', 'parameterNumber']], m.get('units'),
        m.get('typeOfFirstFixedSurface'), m.get('level'), m.get('typeOfSecondFixedSurface')) != (parameter, units, surface, level, 255):
        raise Error('Parameter/unit/vertical mismatch')
    for seal in (grid_seal, input_seal):
        if not isinstance(seal, str) or len(seal) != 64 or any(x not in '0123456789abcdef' for x in seal):
            raise Error('Missing scientific provenance')
    grid = ShiftedGrid(m)
    if identity == 'wind_u' and (m.get('uvRelativeToGrid'), m.get('resolutionAndComponentFlags')) != (0, 48):
        raise Error('Unsupported wind component frame')
    return {'producer': 'ECMWF', 'model': 'IFS Open Data deterministic oper fc',
            'historical_executable_version': 'UNKNOWN; process158 is not an executable version',
            'parameter': {'codes': parameter, 'centre': 98, 'master_table': 33, 'local_table': 1,
                          'namespace': 'ECMWF local' if identity == 'precipitation' else 'WMO', 'ecCodes_paramId': m['paramId']},
            'physical_quantity': m['name'], 'native_unit': units, 'temporal': temporal(m),
            'vertical': {'first_surface_code': surface, 'reference': 'model ground' if surface == 103 else 'surface, no encoded altitude',
                         'height_m': level if surface == 103 else None, 'second_surface': None},
            'grid': grid.description(), 'grid_section3_sha256': grid_seal, 'input_sha256': input_seal,
            'vector': {'component': 'eastward U', 'partner': 'NOT ACQUIRED', 'paired_vector': False} if identity == 'wind_u' else None,
            'ensemble': {'kind': 'deterministic', 'member': None, 'ensemble_structures': 'NOT TESTED'},
            'evidence': 'genuine primary numerical decoding; independent numerical verification separately recorded; not forecast skill',
            'query_limitations': ['grid-axis nearest, not geodesic nearest', 'bilinear excludes polar caps',
                                  'no terrain correction, no temporal interpolation or physical accuracy inference']}


def numeric_compare(a, b, mask, other_mask, m):
    if a.shape != b.shape or a.shape != mask.shape or mask.shape != other_mask.shape or not np.array_equal(mask, other_mask):
        raise Error('Grid/missingness disagreement')
    if (mask.dtype != np.bool_ or other_mask.dtype != np.bool_ or not a.size or np.any(mask)
        or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b))):
        raise Error('Unsupported actual missing/nonfinite profile')
    if (m.get('dataRepresentationTemplateNumber'), m.get('decimalScaleFactor')) != (42, 0):
        raise Error('Unsupported predeclared CCSDS scaling')
    scale = 2.0**m['binaryScaleFactor']; ref = m['referenceValue']
    integer = np.rint((a-ref)/scale)
    if (np.any(integer < 0) or np.any(integer >= 2**24) or not np.array_equal(ref+integer*scale, a)
        or float(np.float32(ref)) != ref):
        raise Error('Outside exact binary32 integer/lattice domain')
    predicted32 = np.float32(ref) + integer.astype(np.float32)*np.float32(scale)
    predicted = predicted32.astype(np.float64)
    bound = .5*np.abs(np.spacing(predicted32).astype(np.float64))+8*np.finfo(float).eps*np.abs(a)
    difference = np.abs(a-b)
    if not np.array_equal(predicted, b) or np.any(difference > bound):
        raise Error('Unexplained independent decoder disagreement')
    return {'compared_cells': int(a.size), 'mask_agreement': True, 'maximum_difference_native': float(difference.max()),
            'mean_absolute_difference_native': float(difference.mean()), 'maximum_bound_native': float(bound.max()),
            'exact_predicted_binary32_cells': int(a.size), 'unexplained_disagreements': 0,
            'tolerance': 'exact predeclared g2clib binary32 prediction AND per-cell half-ULP plus float64 guard'}


def query_checks(values, mask, metadata, independent, transform, queries):
    sampler = ShiftedSampler(values, mask, metadata); records = []
    dx, _, corner, _, negdy, northcorner, *_ = transform
    for query in queries:
        raw = sampler.query(query)
        record = {('native_value' if k == 'temperature_K' else k): v for k, v in raw.items() if k != 'nodes'}
        if 'nodes' in raw:
            record['nodes'] = [{('native_value' if k == 'temperature_K' else k): v for k, v in n.items()} for n in raw['nodes']]
        if raw['status'] == 'OK':
            origin = corner+dx/2
            unwrapped = origin+(float(query['longitude'])-origin) % 360
            row = (float(query['latitude'])-northcorner)/negdy-.5; col = (unwrapped-corner)/dx-.5
            if query['method'] == 'NEAREST':
                r, c = math.floor(row+.5), math.floor(col+.5) % values.shape[1]
                if r in (0, values.shape[0]-1): c = 0
                nodes = [(r, c)]; weights = np.array([1.])
            else:
                r, c = math.floor(row), math.floor(col)
                if r == values.shape[0]-2: r -= 1
                nodes = [(r, c), (r, (c+1) % values.shape[1]), (r+1, c), (r+1, (c+1) % values.shape[1])]
                weights = np.outer([1-(row-r), row-r], [1-(col-c), col-c]).ravel()
            if nodes != [(n['row'], n['column']) for n in raw['nodes']]:
                raise Error('Independent affine node disagreement')
            factor = 1+360/dx+180/(-negdy)
            if np.max(np.abs(weights-[n['weight'] for n in raw['nodes']])) > 32*np.finfo(float).eps*factor:
                raise Error('Independent query weight disagreement')
            for (r, c), n in zip(nodes, raw['nodes']):
                if ((corner+(c+.5)*dx) % 360, northcorner+(r+.5)*negdy) != (n['longitude_0_360'], n['latitude']):
                    raise Error('Independent node coordinate disagreement')
            if independent is None:
                record['comparison'] = {'geometry': 'GDAL affine node and weight agreement',
                    'numerical': 'NOT TESTED: independent decoder unavailable',
                    'qualification': 'ecCodes values with reused WR008 arithmetic; not independent numerical query validation'}
                records.append(record); continue
            av = np.array([n['temperature_K'] for n in raw['nodes']]); bv = np.array([independent[r, c] for r, c in nodes])
            numeric_compare(av, bv, np.zeros(av.shape, dtype=bool), np.zeros(av.shape, dtype=bool), metadata)
            other = float(np.dot(weights, bv)); diff = abs(raw['temperature_K']-other)
            bound = float(np.dot(weights, np.abs(av-bv)))+128*np.finfo(float).eps*max(1., float(np.abs(bv).max()))*factor
            if not math.isfinite(other) or diff > bound:
                raise Error('Independent sampled arithmetic disagreement')
            record['comparison'] = {'independent_native_value': other, 'difference_native': diff, 'bound_native': bound,
                                    'mechanism': 'GDAL decoding/affine plus separate NumPy dot; not independent GDAL warp'}
        records.append(record)
    return records


def primary(path, fp):
    import eccodes
    body = field.pinned_input(path, fp); sec = sections(body)
    h = eccodes.codes_new_from_message(body)
    try:
        m = {k: eccodes.codes_get_long(h, k) if k in fp['numeric_keys'] else eccodes.codes_get(h, k) for k in fp['expected']}
        field.validate_metadata(m, fp)
        if any(eccodes.codes_is_defined(h, k) for k in fp['undefined_keys']):
            raise Error('Unexpected metadata structure')
        if m['productDefinitionTemplateNumber'] == 8:
            precipitation.check_section4(sec[4], m)
        grid = ShiftedGrid(m)
        values = eccodes.codes_get_array(h, 'values').reshape(grid.ny, grid.nx)
        lat = eccodes.codes_get_array(h, 'latitudes').reshape(values.shape)
        lon = eccodes.codes_get_array(h, 'longitudes').reshape(values.shape)
        if not np.array_equal(lat, np.broadcast_to((grid.north-np.arange(grid.ny)*grid.dy)[:, None], values.shape)):
            raise Error('Decoded latitude/storage mismatch')
        # ecCodes labels this native column order as -180..179.75; no array rotation.
        if not np.array_equal(lon % 360, np.broadcast_to((grid.west+np.arange(grid.nx)*grid.dx) % 360, values.shape)):
            raise Error('Decoded longitude/storage mismatch')
        m['decoded_longitude_labels'] = {'minimum': float(lon.min()), 'maximum': float(lon.max()),
                                        'comparison_mapping': 'labels modulo360; arrays retain native order'}
        if m['bitmapPresent'] or m['numberOfMissing'] or not np.all(np.isfinite(values)):
            raise Error('Actual finite/no-bitmap profile changed')
        mask = np.zeros(values.shape, dtype=bool); values.setflags(write=False); mask.setflags(write=False)
        return values, mask, m, sec, {'python': sys.version.split()[0], 'numpy': np.__version__,
                                    'ecCodes': eccodes.codes_get_api_version(), 'eccodes_python': eccodes.__version__}
    finally:
        eccodes.codes_release(h)


def secondary(path, output, fp):
    import rasterio
    body = field.pinned_input(path, fp); sec = sections(body); before = spatial.process_memory()
    with rasterio.Env(GRIB_NORMALIZE_UNITS='NO', GRIB_ADJUST_LONGITUDE_RANGE='NO', GDAL_CACHEMAX=16_000_000):
        with rasterio.open(path) as ds:
            expected = fp['gdal_metadata']; tags = ds.tags(1)
            if (ds.count != 1 or tags != expected['tags'] or [ds.height, ds.width] != expected['shape']
                or list(ds.transform) != expected['transform'] or ds.crs.to_wkt() != expected['crs']
                or [int(x) for x in tags['GRIB_PDS_TEMPLATE_NUMBERS'].split()] != list(sec[4][9:])):
                raise Error('Independent GDAL metadata/raw PDT/geometry disagreement')
            meta = {'tags': tags, 'transform': list(ds.transform), 'crs': ds.crs.to_wkt(),
                    'versions': {'python': sys.version.split()[0], 'numpy': np.__version__,
                                 'rasterio': rasterio.__version__, 'GDAL': rasterio.__gdal_version__}}
            output.with_suffix('.json').write_bytes(field.canonical(meta))
            try:
                values, mask = ds.read(1), ds.read_masks(1) == 0
                np.savez(output, values=values, mask=mask)
            finally:
                output.with_name(output.stem+'-resources.json').write_bytes(field.canonical({'before': before, 'after': spatial.process_memory()}))


def run(root, gdal_python, output, allow_unavailable=False):
    field.require_external(output); pin = checked_pin()
    resource_path = output.with_name(output.stem+'-resources.json')
    if output.exists() or resource_path.exists(): raise Error('Refuse output overwrite')
    before = spatial.process_memory(); started = time.perf_counter(); records = {}; child_resources = []; temporary_peak = 0
    for identity in ['temperature', 'precipitation', 'wind_u']:
        fp = pin['fields'][identity]; path = root/fp['input']['filename']
        values, mask, m, sec, decoder = primary(path, fp)
        array_hash = hashlib.sha256(values.tobytes()).hexdigest()
        with tempfile.TemporaryDirectory(dir=output.parent) as temp:
            ref_path = Path(temp)/'reference.npz'
            child = subprocess.run([str(gdal_python), '-B', str(Path(__file__).resolve()), '--secondary', identity,
                            '--inputs', str(root.resolve()), '--output', str(ref_path)], capture_output=True, text=True)
            temporary_peak = max(temporary_peak, sum(p.stat().st_size for p in Path(temp).rglob('*') if p.is_file()))
            other = json.loads(ref_path.with_suffix('.json').read_text(encoding='utf-8'))
            child_resources.append(json.loads(ref_path.with_name('reference-resources.json').read_text()))
            if child.returncode:
                if not allow_unavailable or 'Data Representation Template 5.42 decoding requires building against libaec' not in child.stderr:
                    raise Error('Independent decoder failed: '+child.stderr)
                compared = {'status': 'UNAVAILABLE', 'compared_cells': 0,
                    'failure': 'GDAL3.9.3 g2_unpack7: Data Representation Template5.42 decoding requires building against libaec',
                    'qualification': 'subsequent Out of memory diagnostic is not evidence of exhausted RAM; no independent numerical/mask agreement'}
                queries = query_checks(values, mask, m, None, other['transform'], pin['selection']['queries'])
            else:
                with np.load(ref_path) as z:
                    independent = z['values']; independent_mask = z['mask']
                    compared = numeric_compare(values, independent, mask, independent_mask, m)
                    queries = query_checks(values, mask, m, independent, other['transform'], pin['selection']['queries'])
                del independent, independent_mask
        if hashlib.sha256(values.tobytes()).hexdigest() != array_hash or field.digest(path) != fp['input']['sha256']:
            raise Error('Input/decoded array mutated')
        seals = {str(k): hashlib.sha256(v).hexdigest() for k, v in sec.items() if k in (2, 3, 4, 5, 6)}
        candidate = concept(identity, m, seals['3'], fp['input']['sha256'])
        records[identity] = {'input': fp['input'], 'source_index': fp['source'], 'actual_metadata': m,
            'section_sha256': seals, 'concept': candidate, 'primary_decoder': decoder,
            'independent_decoder': other, 'numerical_comparison': compared,
            'decoded_float64_sha256': array_hash, 'summary': {'cells': int(values.size), 'valid': int(values.size),
                'missing': int(mask.sum()), 'finite': int(np.isfinite(values).sum()), 'minimum_native': float(values.min()),
                'maximum_native': float(values.max()), 'mean_native': float(values.mean()),
                'zero_cells': int(np.count_nonzero(values == 0)), 'negative_cells': int(np.count_nonzero(values < 0))},
            'queries': queries, 'input_and_decoded_array_unchanged': True,
            'physical_unit_confirmation': 'producer definitions; GDAL vocabulary unknown' if identity == 'precipitation' else 'ecCodes and GDAL native unit agreement'}
        del values, mask
    if len({v['section_sha256']['3'] for v in records.values()}) != 1: raise Error('New-field grid mismatch')
    outcome = 'B' if any(v['numerical_comparison'].get('status') == 'UNAVAILABLE' for v in records.values()) else 'A'
    receipt = {'schema': 'meridian-weather-wr011-ifs-conformance-v1', 'outcome': outcome, 'fields': records,
        'source': pin['selection'], 'pins_sha256': field.digest(PIN), 'attribution':
        'This research is based on data and products of the European Centre for Medium-Range Weather Forecasts (ECMWF).',
        'copyright': 'Copyright 2025 ECMWF; CC BY4.0 with source notices; modified derived research receipts, no endorsement',
        'limitations': ['only three deterministic delivered IFS fields; not full internal model grid or all IFS products',
            'no complete vector, ensemble, cloud, reduced/rotated/projected grid or real bitmap evidence',
            'GDAL local precipitation name/unit unavailable; raw PDT metadata checked; independent numerical status recorded per field',
            'no forecast skill, model comparison, terrain accuracy, production API or observation verification']}
    output.write_bytes(field.canonical(receipt))
    resource_path.write_bytes(field.canonical({'primary_before': before, 'primary_after': spatial.process_memory(),
        'secondary_processes': child_resources, 'temporary_peak_bytes': temporary_peak, 'elapsed_seconds': time.perf_counter()-started,
        'network_in_replay': 'no acquisition code executed; external OS/Git traffic not metered'}))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--gdal-python', type=Path); parser.add_argument('--secondary', choices=['temperature', 'precipitation', 'wind_u'])
    parser.add_argument('--allow-unavailable-independent', action='store_true', help='Record known missing libaec as Outcome B, never agreement')
    args = parser.parse_args()
    if args.secondary:
        field.require_external(args.output)
        if any(p.exists() for p in (args.output, args.output.with_suffix('.json'),
                                   args.output.with_name(args.output.stem+'-resources.json'))):
            raise Error('Refuse output overwrite')
        pin = checked_pin(); fp = pin['fields'][args.secondary]
        secondary(args.inputs/fp['input']['filename'], args.output, fp)
    else:
        if not args.gdal_python: parser.error('--gdal-python required')
        receipt = run(args.inputs, args.gdal_python, args.output, args.allow_unavailable_independent)
        print(json.dumps({k: {'summary': v['summary'], 'comparison': v['numerical_comparison']} for k, v in receipt['fields'].items()}, indent=2))


if __name__ == '__main__': main()
