"""WR014 fixed GEFS cohort experiment; no acquisition or probability engine."""
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
for previous in ('wr007', 'wr008', 'wr009'):
    sys.path.insert(0, str(HERE.parent / previous))
import gfs_field_pilot as field
import gfs_point_sampling as spatial
import gfs_precipitation_pilot as precipitation

PIN = HERE / 'input-pins.json'
Error = field.IntegrityError


def checked_pin():
    pin = json.loads(PIN.read_text(encoding='utf-8'))
    for name, expected in pin['dependencies'].items():
        if field.digest(HERE.parent / name) != expected:
            raise Error('Accepted WR007-WR013 evidence changed')
    return pin


def member_identity(m, expected):
    """A PDT1 member is not a deterministic field with an invented number."""
    if (m.get('productDefinitionTemplateNumber'), m.get('typeOfGeneratingProcess')) != (1, 4):
        raise Error('No supported individual ensemble identity')
    number, kind, total = (m.get(k) for k in
                           ('perturbationNumber', 'typeOfEnsembleForecast', 'numberOfForecastsInEnsemble'))
    if any(type(v) is not int for v in (number, kind, total)) or number < 0 or total < 3:
        raise Error('Missing/unsupported encoded member information')
    if (number, kind) != (expected['member_number'], expected['member_type_code']):
        raise Error('Member identity contradicts frozen profile')
    if kind == 1 and number == 0:
        role = 'unperturbed low-resolution control'
    elif kind == 3 and number > 0:
        role = 'positively perturbed forecast'
    else:
        raise Error('Unsupported or ambiguous member classification')
    return {'number': number, 'type_code': kind, 'role': role,
            'authority': 'encoded PDT4.1 octets35-37; NOAA/WMO code table4.6',
            'encoded_number_of_forecasts': total,
            'documented_GEFS_v12_population': 31,
            'count_mapping': 'UNRESOLVED: raw30 is not silently normalised to documented31 or registry21',
            'full_population_inspected': False, 'operational_weight': 'UNKNOWN'}


def interpret(m, expected, pin, grid_seal):
    field.validate_metadata(m, pin)
    member = member_identity(m, expected)
    if (m.get('centre'), m.get('subCentre'), m.get('generatingProcessIdentifier')) != (7, 2, 107):
        raise Error('Wrong producing system')
    if m.get('dataRepresentationTemplateNumber') != 3 or (m['binaryScaleFactor'], m['decimalScaleFactor']) != (0, 2):
        raise Error('Unsupported prospective packing/rounding profile')
    if m['numberOfMissing'] != 0 or m['numberOfValues'] != m['numberOfPoints']:
        raise Error('Unsupported actual missingness profile')
    return {'system': 'NOAA/NCEP GEFS operational ensemble', 'product': pin['product'],
            'producer': {'centre': 7, 'subcentre': 2, 'generating_process': 107},
            'historical_executable_version': 'UNKNOWN; process107 is not an executable version',
            'member': member,
            'parameter': {'codes': [m[k] for k in ('discipline', 'parameterCategory', 'parameterNumber')],
                          'centre': m['centre'], 'master_table': m['tablesVersion'],
                          'local_table': m['localTablesVersion'], 'authority': 'WMO temperature'},
            'native_unit': m['units'],
            'vertical': {'type_code': m['typeOfFirstFixedSurface'], 'height_m': m['level'],
                         'reference': 'model ground; not actual local terrain'},
            'temporal': {'kind': 'instant', 'reference_time': '2025-01-15T00:00:00Z',
                         'valid_time': '2025-01-16T00:00:00Z', 'lead_seconds': 86400},
            'grid': {'section3_sha256': grid_seal, 'type': m['gridType'], 'rows': m['Nj'], 'columns': m['Ni'],
                     'spacing_degrees': .5, 'north': 90, 'south': -90, 'longitude_origin': 0,
                     'last_longitude': 359.5, 'scan': 0, 'earth_radius_m': 6371229,
                     'registration': 'delivered native grid nodes; not model computational resolution'},
            'missingness': {'bitmap': False, 'missing_cells': 0},
            'evidence': 'genuine encoded member and primary numerical interpretation; independent check separate'}


def comparable(items):
    if not 2 <= len(items) <= 3:
        raise Error('Only bounded selected cohort supported')
    if any(not isinstance(x.get('member'), dict) or
           any(k not in x['member'] for k in ('type_code', 'number', 'authority', 'role', 'encoded_number_of_forecasts'))
           for x in items):
        raise Error('Missing verified member identity')
    identities = [(x['member']['type_code'], x['member']['number']) for x in items]
    if len(set(identities)) != len(items) or len({x['member']['number'] for x in items}) != len(items):
        raise Error('Duplicate selected member identity')
    for item in items:
        if item['member']['authority'] != 'encoded PDT4.1 octets35-37; NOAA/WMO code table4.6':
            raise Error('Member identity not verified')
        member = item['member']
        role = ('unperturbed low-resolution control' if (member['type_code'], member['number']) == (1, 0)
                else 'positively perturbed forecast' if member['type_code'] == 3 and
                type(member['number']) is int and member['number'] > 0 else None)
        if role is None or member['role'] != role:
            raise Error('Ambiguous control/perturbation mapping')
    for key in ('system', 'product', 'producer', 'parameter', 'native_unit', 'vertical', 'temporal', 'grid', 'missingness'):
        if any(x[key] != items[0][key] for x in items[1:]):
            raise Error('Selected-member support mismatch: ' + key)
    totals = {x['member']['encoded_number_of_forecasts'] for x in items}
    if len(totals) != 1 or type(next(iter(totals))) is not int or next(iter(totals)) < len(items):
        raise Error('Inconsistent encoded count; no complete-population inference')
    return {'requirements': {key: 'Verified' for key in
              ['system', 'product', 'reference', 'lead_validity', 'quantity_authority_unit', 'vertical',
               'instantaneous_support', 'identical_encoded_grid', 'coordinate_order', 'no_bitmap_missingness', 'distinct_members']},
            'member_role_mapping': 'Verified through explicit encoded provider/table mapping',
            'encoded_count_agreement': next(iter(totals)),
            'encoded_to_full_population_mapping': 'Unresolved',
            'selection_size': len(items), 'full_distribution_and_operational_weights': 'Not tested'}


def subset_statistics(values, operation='descriptive_subset'):
    if operation != 'descriptive_subset':
        raise Error('Full-ensemble probabilities/means/intervals unsupported from selected subset')
    if not 2 <= len(values) <= 3 or any(type(x) not in (float, int) or not math.isfinite(x) for x in values):
        raise Error('Invalid selected-subset numerical values')
    mean = math.fsum(values) / len(values)
    return {'population': 'SELECTED SUBSET ONLY', 'selected_members': len(values),
            'arithmetic_selected_subset_mean_K': mean, 'minimum_K': min(values), 'maximum_K': max(values),
            'range_K': max(values)-min(values),
            'population_standard_deviation_selected_subset_K': math.sqrt(math.fsum((x-mean)**2 for x in values)/len(values)),
            'weighting': 'equal descriptive weights; not inferred operational member probabilities',
            'prohibited_interpretation': 'not full-ensemble mean, spread distribution, calibrated bounds or skill'}


def primary(path, fp, pin):
    import eccodes as ec
    import numpy as np
    body = field.pinned_input(path, fp)
    sec = precipitation.sections(body)
    h = ec.codes_new_from_message(body)
    try:
        m = {k: ec.codes_get_long(h, k) if k in pin['numeric_keys'] else ec.codes_get(h, k)
             for k in pin['metadata_keys']}
        concept = interpret(m, fp, pin, hashlib.sha256(sec[3]).hexdigest())
        if len(sec[4]) != 37 or tuple(sec[4][34:37]) != (m['typeOfEnsembleForecast'], m['perturbationNumber'], m['numberOfForecastsInEnsemble']):
            raise Error('Actual raw PDT member octets disagree')
        values = np.reshape(ec.codes_get_values(h), (m['Nj'], m['Ni']))
        lat = np.reshape(ec.codes_get_array(h, 'latitudes'), values.shape)
        lon = np.reshape(ec.codes_get_array(h, 'longitudes'), values.shape)
        if not np.array_equal(lat, np.broadcast_to((90-.5*np.arange(361))[:, None], values.shape)):
            raise Error('Latitude alignment mismatch')
        if not np.array_equal(lon, np.broadcast_to((.5*np.arange(720))[None, :], values.shape)):
            raise Error('Longitude alignment mismatch')
        mask = np.zeros(values.shape, dtype=bool)
        if not np.all(np.isfinite(values)):
            raise Error('Unsupported nonfinite numerical cells')
        values.setflags(write=False); mask.setflags(write=False)
        versions = {'ecCodes': ec.codes_get_api_version(), 'eccodes_python': ec.__version__,
                    'numpy': np.__version__, 'python': sys.version.split()[0]}
    finally:
        ec.codes_release(h)
    return values, mask, m, concept, sec, versions


def secondary(path, output, fp, pin):
    import numpy as np
    import rasterio
    field.require_external(output)
    if any(output.with_suffix(suffix).exists() for suffix in ('.npz', '.json', '.resources.json')):
        raise Error('Refuse overwrite of independent output')
    before = spatial.process_memory()
    sec = precipitation.sections(field.pinned_input(path, fp))
    with rasterio.Env(GRIB_NORMALIZE_UNITS='NO', GRIB_ADJUST_LONGITUDE_RANGE='NO'):
        with rasterio.open(path) as d:
            tags = d.tags(1)
            required = {'GRIB_UNIT': '[K]', 'GRIB_ELEMENT': 'TMP', 'GRIB_SHORT_NAME': '2-HTGL',
                        'GRIB_REF_TIME': '1736899200', 'GRIB_VALID_TIME': '1736985600',
                        'GRIB_FORECAST_SECONDS': '86400', 'GRIB_PDS_PDTN': '1'}
            if d.count != 1 or any(tags.get(k) != v for k, v in required.items()):
                raise Error('Independent scientific metadata mismatch')
            if [int(x) for x in tags.get('GRIB_PDS_TEMPLATE_NUMBERS', '').split()] != list(sec[4][9:]):
                raise Error('Independent raw ensemble-template mismatch')
            if (d.height, d.width) != (361, 720) or tuple(d.transform) != (.5, 0, -.25, 0, -.5, 90.25, 0, 0, 1):
                raise Error('Independent native coordinate alignment mismatch')
            if d.crs is None or d.crs.to_dict().get('R') != 6371229:
                raise Error('Independent geographic reference mismatch')
            values, mask = d.read(1), d.read_masks(1) == 0
            result = {'rasterio': rasterio.__version__, 'gdal': rasterio.__gdal_version__,
                      'numpy': np.__version__, 'python': sys.version.split()[0], 'metadata': tags,
                      'transform': list(d.transform), 'native_sample_coordinates': [d.xy(q['row'],q['column']) for q in pin['locations']],
                      'implementation': 'GDAL GRIB driver/degrib/g2clib, separate from ecCodes'}
    np.savez(output.with_suffix('.npz'), values=values, mask=mask)
    output.with_suffix('.json').write_bytes(field.canonical(result))
    output.with_suffix('.resources.json').write_bytes(field.canonical({'before':before,'after':spatial.process_memory()}))


def run(root, gdal_python, output):
    import numpy as np
    output = Path(output); field.require_external(output)
    if output.exists() or output.with_suffix('.resources.json').exists():
        raise Error('Refuse overwrite')
    pin = checked_pin(); precipitation.scratch_room(output.parent)
    before = spatial.process_memory(); members = {}; concepts=[]; point_values={q['label']:[] for q in pin['locations']}
    temporary_peak=0; reference_peaks=[]
    for name, fp in pin['members'].items():
        path = Path(root)/fp['filename']
        values, mask, m, concept, sec, versions = primary(path, fp, pin)
        array_hash = hashlib.sha256(values.astype('<f8').tobytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='wr014-reference-', dir=output.parent) as directory:
            other = Path(directory)/'reference'
            subprocess.run([str(gdal_python), '-B', str(Path(__file__).resolve()), '--secondary',
                            '--inputs', str(root), '--member', name, '--output', str(other)],check=True)
            ref = json.loads(other.with_suffix('.json').read_text(encoding='utf-8'))
            reference_peaks.append(json.loads(other.with_suffix('.resources.json').read_text(encoding='utf-8')))
            temporary_peak=max(temporary_peak,sum(p.stat().st_size for p in Path(directory).iterdir()))
            with np.load(other.with_suffix('.npz'), allow_pickle=False) as other_values:
                agreement = field.compare_arrays(values,other_values['values'],mask,other_values['mask'],m)
        samples=[]
        for i,q in enumerate(pin['locations']):
            r,c=q['row'],q['column']
            if ref['native_sample_coordinates'][i] != [q['longitude_0_360'],q['latitude']]:
                raise Error('Native query geometry disagrees')
            v=float(values[r,c]);samples.append({**q,'native_value_K':v});point_values[q['label']].append(v)
        concepts.append(concept)
        members[name]={'input':fp['input'],'actual_metadata':m,'concept':concept,'raw_member_octets':list(sec[4][34:37]),
            'decoded_float64_sha256':array_hash,'primary_decoder':versions,'independent_decoder':ref,
            'independent_comparison':agreement,'summary_K':{'minimum':float(values.min()),'maximum':float(values.max()),
                'mean':float(values.mean()),'finite_cells':int(values.size),'missing_cells':0,'invalid_cells':0},
            'samples':samples,'raw_input_unchanged':field.digest(path)==fp['input']['sha256']}
        if not members[name]['raw_input_unchanged'] or hashlib.sha256(values.astype('<f8').tobytes()).hexdigest()!=array_hash:
            raise Error('Source/decoded array mutated')
        del values,mask
    conformity = comparable(concepts)
    statistics=[{'location':q,'member_order':list(pin['members']),'member_values_K':point_values[q['label']],
                 **subset_statistics(point_values[q['label']])} for q in pin['locations']]
    receipt={'schema':'meridian-wr014-bounded-ensemble-integrity-v1','outcome':'A',
       'pins_sha256':field.digest(PIN),'original_freeze_sha256':pin['original_freeze_sha256'],
       'comparison_amendment_sha256':pin['comparison_amendment_sha256'],
       'utility_sha256':field.digest(Path(__file__)),'members':members,'conformance':conformity,
       'selected_subset_statistics':statistics,
       'limitations':['three selected members; no full-ensemble weighting, distribution, probability, calibration or skill',
                      'raw encoded30/documented31/outdated registry21 distinguished; complete count mapping unresolved',
                      'one actual delivery grid/run/lead/height/packing/no-bitmap profile; no production/member-universality claim']}
    output.write_bytes(field.canonical(receipt))
    output.with_suffix('.resources.json').write_bytes(field.canonical({'primary_before':before,'primary_after':spatial.process_memory(),
        'independent_processes':reference_peaks,'maximum_sequential_temporary_bytes':temporary_peak,
        'messages_per_run':{'ecCodes':3,'GDAL':3},'requests_during_run':0}))
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--gdal-python',type=Path);parser.add_argument('--secondary',action='store_true');parser.add_argument('--member')
    args=parser.parse_args()
    if args.secondary:
        pin=checked_pin();secondary(args.inputs/pin['members'][args.member]['filename'],args.output,pin['members'][args.member],pin)
    else:
        if args.gdal_python is None:parser.error('--gdal-python is required; no silent independent skip')
        print(json.dumps(run(args.inputs,args.gdal_python,args.output)['conformance'],indent=2))


if __name__=='__main__':main()
