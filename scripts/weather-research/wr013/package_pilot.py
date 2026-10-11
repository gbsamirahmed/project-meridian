"""WR013 three-field packaging apparatus; existing inputs only, no retrieval."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
for previous in ('wr007', 'wr008', 'wr009', 'wr010', 'wr011'):
    sys.path.insert(0, str(HERE.parent / previous))
import gfs_field_pilot as field
import gfs_point_sampling as spatial
import gfs_precipitation_pilot as precipitation
import field_compatibility as contract
import ifs_contract_pilot as ifs
import offline_reader as reader

PIN = HERE / 'input-pins.json'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def seal(path):
    return field.digest(Path(path))


def room(root, reserve=5_000_000):
    total = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if total + reserve > 150_000_000:
        raise reader.PackageError('Owned scratch ceiling')
    return total


def check_dependencies(pin):
    for name, expected in pin['dependencies'].items():
        if seal(HERE.parent / name) != expected:
            raise reader.PackageError('Accepted scientific evidence changed')


def describe(fid, fp, m, section3, source_receipt):
    if fid == 'ifs-precipitation':
        meaning = source_receipt['scientific_receipt']['fields']['precipitation']['concept']
        support, vertical, parameter = meaning['temporal'], meaning['vertical'], meaning['parameter']
        model, producer = meaning['model'], meaning['producer']
        source = source_receipt['scientific_receipt']['source']
        notice = {'attribution': source_receipt['scientific_receipt']['attribution'],
                  'copyright': source_receipt['scientific_receipt']['copyright'],
                  'qualification': 'subset and research receipts are transformations; no endorsement or new legal clearance'}
    else:
        support = contract.temporal(m) if fid == 'gfs-temperature' else precipitation.interval(m)
        vertical = {'first_surface_code': m['typeOfFirstFixedSurface'],
                    'reference': 'model ground' if fid == 'gfs-temperature' else 'surface, no encoded altitude',
                    'height_m': 2 if fid == 'gfs-temperature' else None, 'second_surface': None}
        parameter = {'codes': [m[k] for k in ('discipline', 'parameterCategory', 'parameterNumber')],
                     'centre': m['centre'], 'master_table': m['tablesVersion'],
                     'local_table': m['localTablesVersion'], 'namespace': 'WMO', 'ecCodes_paramId': m.get('paramId')}
        model, producer = 'GFS deterministic operational forecast', 'NOAA/NCEP'
        source = source_receipt['source']
        notice = {'attribution': 'NOAA/NCEP GFS source retained',
                  'qualification': 'retained source-specific terms; no new commercial delivery or service clearance'}
    return {'field_id': fid, 'producer': producer, 'model': model,
            'historical_executable_version': 'UNRESOLVED; generating-process identifier is not an executable version',
            'parameter': parameter, 'physical_quantity': m['name'], 'native_unit': m['units'],
            'vertical': vertical, 'temporal': support, 'encoded_metadata': m,
            'ensemble': {'kind': 'deterministic', 'member': None}, 'vector_relationship': None,
            'source_grid': {'grid_type': m['gridType'], 'template': m['gridDefinitionTemplateNumber'],
                 'scanning_mode': m['scanningMode'], 'earth_shape': m['shapeOfTheEarth'], 'radius_m': m['radius'],
                 'rows': m['Nj'], 'columns': m['Ni'], 'north': m['latitudeOfFirstGridPointInDegrees'],
                 'longitude_origin': m['longitudeOfFirstGridPointInDegrees'],
                 'dx': m['iDirectionIncrementInDegrees'], 'dy': m['jDirectionIncrementInDegrees'],
                 'section3_sha256': section3, 'registration': 'native grid nodes',
                 'source_longitude_periodic': True, 'source_latitude_periodic': False},
            'missingness': {'profile': 'all finite; no bitmap or sentinel', 'missing_cells': 0},
            'provenance': {'raw_input': fp['input'], 'source': source,
                 'source_notice': notice,
                 'accepted_receipt': fp['source_receipt'], 'accepted_receipt_sha256': seal(HERE.parent / fp['source_receipt']),
                 'evidence': 'accepted genuine numerical decoding; package/replay verification separately recorded',
                 'independent_decoding': 'WR007/WR009 ecCodes versus GDAL' if fid != 'ifs-precipitation' else
                       'WR012 independent GRIB unpacking/scaling with shared low-level libaec; qualified independence B'},
            'transformation': {'operation': 'rectangular native-index extraction; binary64 serialisation',
                 'unit_conversion': None, 'resampling': None, 'array_roll': None, 'scan_order': 'source row-major retained'},
            'limitations': ['bounded subset, not global wrapping or polar geometry',
                 'grid-axis nearest, not geodesic nearest; bilinear adds no meteorological resolution',
                 'model representation, no real-terrain height correction, observations or forecast-skill evidence',
                 'no commercial/offline redistribution clearance or production-format claim']}


def source_values(fid, fp, path):
    pin = load(HERE.parent / fp['source_pin'])
    receipt = load(HERE.parent / fp['source_receipt'])
    if fid == 'ifs-precipitation':
        values, mask, m, sec, versions = ifs.primary(path, pin['fields']['precipitation'])
        baseline = receipt['scientific_receipt']['fields']['precipitation']['decoded_float64_sha256']
        sampler = ifs.ShiftedSampler(values, mask, m)
        section3 = hashlib.sha256(sec[3]).hexdigest()
    else:
        values, mask, lat, lon, m, versions = field.eccodes_decode(path, pin)
        # WR007's receipt did not retain every later contract key. Read these
        # from the same pinned message; do not invent an encoded time unit.
        import eccodes
        h = eccodes.codes_new_from_message(field.pinned_input(path, pin))
        try:
            for k in ('paramId', 'indicatorOfUnitOfTimeRange', 'typeOfSecondFixedSurface',
                      'scaleFactorOfSecondFixedSurface', 'scaledValueOfSecondFixedSurface'):
                if eccodes.codes_is_defined(h, k):
                    m[k] = eccodes.codes_get_long(h, k)
        finally:
            eccodes.codes_release(h)
        baseline = receipt['decoded_float64_little_endian_sha256']
        sampler = spatial.Sampler(values, mask, m)
        sec = precipitation.sections(field.pinned_input(path, pin))
        section3 = hashlib.sha256(sec[3]).hexdigest()
    values.setflags(write=False)
    mask.setflags(write=False)
    actual = hashlib.sha256(values.astype('<f8').tobytes()).hexdigest()
    if actual != baseline or mask.any() or m['bitmapPresent'] != 0:
        raise reader.PackageError('Accepted numerical/missingness baseline disagreement')
    return values, sampler, m, versions, section3, receipt, actual


def run(inputs, output, pins=PIN):
    output = Path(output)
    field.require_external(output / 'manifest.json')
    if output.exists():
        raise reader.PackageError('Refuse overwrite of research output')
    if not output.parent.is_dir():
        raise reader.PackageError('Dedicated owned scratch parent required')
    pin = load(pins)
    check_dependencies(pin)
    before = spatial.process_memory()
    initial_bytes = room(output.parent)
    output.mkdir()
    package_root = output / 'package'
    package_root.mkdir()
    records, checks, source_queries, expected_subsets = [], {}, {}, {}
    for fid, fp in pin['fields'].items():
        path = Path(inputs[fid])
        if path.stat().st_size != fp['input']['bytes'] or seal(path) != fp['input']['sha256']:
            raise reader.PackageError('Pinned raw input mismatch')
        values, sampler, m, versions, section3, previous, full_seal = source_values(fid, fp, path)
        g = pin['subset']
        r, c, ny, nx = g['row_start'], fp['column_start'], g['rows'], g['columns']
        if m['longitudeOfFirstGridPointInDegrees'] != fp['origin'] or m['units'] != fp['units']:
            raise reader.PackageError('Frozen provider geometry/unit mismatch')
        sub = values[r:r+ny, c:c+nx]
        if sub.shape != (ny, nx):
            raise reader.PackageError('Frozen subset unavailable')
        body = sub.astype('<f8').tobytes()
        expected_subsets[fid] = tuple(float(v) for v in sub.ravel())
        filename = fid + '.f64'
        (package_root / filename).write_bytes(body)
        record = describe(fid, fp, m, section3, previous)
        record['subset'] = {'row_start': r, 'column_start': c, 'rows': ny, 'columns': nx,
                 'north': g['north'], 'south': g['south'], 'west_0_360': 352, 'east_unwrapped': 358,
                 'periodic': False, 'coordinate_labels': '0..360 canonical; source origin and native indices retained'}
        record['payload'] = {'filename': filename, 'encoding': 'IEEE754-binary64-little-endian-row-major',
                             'bytes': len(body), 'sha256': reader.digest(body)}
        record['provenance']['primary_decoder'] = versions
        reader.Package.validate_field(record)
        records.append(record)
        checks[fid] = {'raw_input': fp['input'], 'input_unchanged': False, 'accepted_full_float64_sha256': full_seal,
                'payload_sha256': reader.digest(body), 'payload_bytes': len(body), 'packaged_cells': ny*nx,
                'source_precision': 'ecCodes IEEE754 binary64', 'package_precision': 'IEEE754 binary64 little-endian',
                'exact_equal_cells': ny*nx, 'maximum_absolute_difference': 0, 'mean_absolute_difference': 0,
                'finite_cells': ny*nx, 'missing_cells': 0, 'primary_decoder': versions}
        for i, q in enumerate(pin['queries']):
            if q['field_id'] == fid and q['expected_status'] == 'OK':
                result = sampler.query({k: q[k] for k in ('latitude', 'longitude', 'method')})
                if result['status'] != 'OK':
                    raise reader.PackageError('Frozen source query unsupported')
                source_queries[i] = {'native_value': result['temperature_K'],
                    'nodes': [{('native_value' if k == 'temperature_K' else k): v for k, v in n.items()}
                              for n in result['nodes']]}
        # Compare every serialised cell by independent stdlib binary unpacking.
        import struct
        unpacked = struct.unpack('<'+str(ny*nx)+'d', body)
        if any(a != float(b) for a, b in zip(unpacked, sub.ravel())):
            raise reader.PackageError('Binary serialisation changed values')
        del values, sampler, sub
    manifest = {'version': reader.VERSION, 'profile_sha256': seal(pins),
                'fields': records, 'scientific_contract': 'WR010-WR012 research candidate, bounded subset refinement',
                'package_status': 'disposable research apparatus; not production format or redistribution approval'}
    manifest_body = reader.canonical(manifest)
    (package_root/'manifest.json').write_bytes(manifest_body)
    identity = reader.digest(manifest_body)
    requests = [{k: v for k, v in q.items() if k not in ('label', 'expected_status')} for q in pin['queries']]
    # Independent offline reader in a fresh directory: no old code, data or decoder.
    with tempfile.TemporaryDirectory(prefix='wr013-isolated-', dir=output.parent) as name:
        isolated = Path(name)
        shutil.copytree(package_root, isolated/'package')
        shutil.copyfile(HERE/'offline_reader.py', isolated/'offline_reader.py')
        (isolated/'requests.json').write_bytes(reader.canonical(requests))
        isolated_bytes = sum(p.stat().st_size for p in isolated.rglob('*') if p.is_file())
        peak_scratch = room(output.parent, reserve=0)
        completed = subprocess.run([sys.executable, '-I', '-S', '-B', 'offline_reader.py',
                    '--package', 'package', '--identity', identity, '--requests', 'requests.json', '--isolate'],
                    cwd=isolated, capture_output=True, check=True)
        replay = reader.parse(completed.stdout)
    package = reader.Package(package_root, identity)
    comparisons = []
    for i, (q, result) in enumerate(zip(pin['queries'], replay['results'])):
        if result['status'] != q['expected_status'] or result != package.query(requests[i]):
            raise reader.PackageError('Offline query status/determinism disagreement')
        comparison = {'index': i, 'label': q['label'], 'field_id': q['field_id'], 'method': q['method'],
                      'status': result['status']}
        if result['status'] == 'OK':
            difference = abs(result['native_value']-source_queries[i]['native_value'])
            if difference != pin['query_absolute_tolerance']:
                raise reader.PackageError('Offline/source numerical query disagreement')
            def native_nodes(nodes, old=False):
                return [(n['row' if old else 'source_row'], n['column' if old else 'source_column'],
                         n['latitude'], n['longitude_0_360'], n['weight'], n['native_value'])
                        for n in nodes if n['weight'] != 0]
            if native_nodes(result['nodes']) != native_nodes(source_queries[i]['nodes'], old=True):
                raise reader.PackageError('Offline/source contributing geometry/weight disagreement')
            comparison.update({'native_value': result['native_value'], 'native_unit': result['native_unit'],
                 'source_native_value': source_queries[i]['native_value'], 'absolute_difference': difference,
                 'nonzero_node_and_weight_agreement': True,
                 'temporal': result['temporal'], 'nodes': result['nodes']})
        comparisons.append(comparison)
    # Reopened package, rather than the serialisation buffer, is checked cell by cell.
    for fid, fp in pin['fields'].items():
        if reader.digest((package_root/(fid+'.f64')).read_bytes()) != checks[fid]['payload_sha256']:
            raise reader.PackageError('Reopened payload disagreement')
        expected, actual = expected_subsets[fid], package.values[fid]
        differences = [abs(a-b) for a, b in zip(actual, expected)]
        exact = sum(a == b for a, b in zip(actual, expected))
        if len(actual) != len(expected) or exact != len(expected):
            raise reader.PackageError('Reopened cell-by-cell comparison failed')
        checks[fid].update({'exact_equal_cells': exact, 'maximum_absolute_difference': max(differences),
                           'mean_absolute_difference': math.fsum(differences)/len(expected),
                           'comparison': 'every reopened standalone-reader value against accepted ecCodes subset'})
        checks[fid]['input_unchanged'] = seal(Path(inputs[fid])) == fp['input']['sha256']
        if not checks[fid]['input_unchanged']:
            raise reader.PackageError('Scientific source changed')
    if not replay['isolation']['audit_guard_enabled'] or replay['isolation']['scientific_modules_loaded']:
        raise reader.PackageError('Isolation requirements not met')
    components = {p.name: {'bytes': p.stat().st_size, 'sha256': seal(p)} for p in package_root.iterdir()}
    replay_receipt = {'schema': 'meridian-wr013-query-comparison-v1', 'outcome': 'A', 'package_identity': identity,
         'absolute_tolerance': pin['query_absolute_tolerance'], 'queries': comparisons,
         'successful_queries': sum(x['status']=='OK' for x in comparisons),
         'rejected_queries': sum(x['status']!='OK' for x in comparisons),
         'maximum_absolute_difference': max(x.get('absolute_difference', 0) for x in comparisons),
         'isolation': replay['isolation'], 'isolation_directory_contents': ['package/', 'offline_reader.py', 'requests.json'],
         'edge_qualification': 'closed south/east edges use inward stencil; global zero-weight outside nodes are not packaged',
         'reader_sha256': seal(HERE/'offline_reader.py')}
    integrity = {'schema': 'meridian-wr013-package-integrity-v1', 'outcome': 'A', 'pins_sha256': seal(pins),
         'predeclaration_sha256': pin['predeclaration_sha256'], 'fields': checks, 'components': components,
         'package_identity': identity, 'metadata_bytes': len(manifest_body),
         'payload_bytes': sum(v['payload_bytes'] for v in checks.values()),
         'final_package_bytes': sum(v['bytes'] for v in components.values()),
         'utility_sha256': {n: seal(HERE/n) for n in ['package_pilot.py', 'offline_reader.py']},
         'limitations': ['exact source-preserving subset, not forecast accuracy or a commercial distribution licence',
                        'independent stdlib representation/replay reader, not a new independent meteorological decoder',
                        'tested regular grids only; no bitmap/missing payload, vector, category, ensemble or vertical profiles']}
    (output/'package-integrity-receipt.json').write_bytes(reader.canonical(integrity))
    (output/'offline-query-replay-receipt.json').write_bytes(reader.canonical(replay_receipt))
    (output/'resources.json').write_bytes(reader.canonical({'initial_owned_bytes': initial_bytes,
         'isolation_temporary_bytes': isolated_bytes, 'observed_scratch_during_isolation_bytes': peak_scratch,
         'primary_memory_before': before, 'primary_memory_after': spatial.process_memory(),
         'isolated_reader_memory': replay['resources'],
         'scientific_messages_decoded': 3, 'controlled_requests': 0, 'response_body_bytes': 0,
         'unmetered': 'Git fetch/push and protocol overhead; no certified total network count'}))
    return integrity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gfs-temperature', type=Path, required=True)
    parser.add_argument('--gfs-apcp', type=Path, required=True)
    parser.add_argument('--ifs-precipitation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run({'gfs-temperature': args.gfs_temperature, 'gfs-apcp': args.gfs_apcp,
                         'ifs-precipitation': args.ifs_precipitation}, args.output), indent=2))


if __name__ == '__main__':
    main()
