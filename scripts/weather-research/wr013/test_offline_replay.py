"""Synthetic rejection/invariant tests, separately labelled genuine package replay."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

import offline_reader as r

HERE = Path(__file__).resolve().parent


def synthetic():
    """Invented affine values and evidence; not a historical observation/forecast."""
    m = json.loads((HERE.parent/'wr007/input-pins.json').read_text(encoding='utf-8'))['expected']
    m['indicatorOfUnitOfTimeRange'] = 1
    f = {'field_id': 'synthetic', 'native_unit': 'K', 'encoded_metadata': m,
         'source_grid': {'grid_type': 'regular_ll', 'template': 0, 'scanning_mode': 0, 'earth_shape': 6,
             'radius_m': 6371229, 'rows': 721, 'columns': 1440, 'north': 90, 'longitude_origin': 0,
             'dx': .25, 'dy': .25, 'section3_sha256': '1'*64},
         'subset': {'row_start': 124, 'column_start': 1408, 'rows': 21, 'columns': 25,
                    'north': 59, 'south': 54, 'west_0_360': 352, 'east_unwrapped': 358, 'periodic': False},
         'temporal': {'kind': 'instant', 'reference_time': '2025-01-15T00:00:00Z', 'valid_time': '2025-01-16T00:00:00Z'},
         'vertical': {'first_surface_code': 103, 'reference': 'model ground', 'height_m': 2},
         'parameter': {'codes': [0, 0, 0], 'centre': 7, 'master_table': 2, 'local_table': 1},
         'provenance': {'raw_input': {'sha256': '2'*64}, 'evidence': 'SYNTHETIC; not raw scientific input'},
         'missingness': {'profile': 'all finite; no bitmap or sentinel', 'missing_cells': 0},
         'ensemble': {'kind': 'deterministic', 'member': None}}
    values = [300 + y*.25 + x*.125 for y in range(21) for x in range(25)]
    body = struct.pack('<525d', *values)
    f['payload'] = {'filename': 'synthetic.f64', 'encoding': 'IEEE754-binary64-little-endian-row-major',
                    'bytes': len(body), 'sha256': r.digest(body)}
    return {'version': r.VERSION, 'fields': [f]}, body


class SyntheticRejections(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wr013-synthetic-')
        self.root = Path(self.temp.name)
        self.m, self.body = synthetic()
        self.write()

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        body = r.canonical(self.m)
        self.identity = r.digest(body)
        (self.root/'manifest.json').write_bytes(body)
        (self.root/'synthetic.f64').write_bytes(self.body)

    def package(self):
        return r.Package(self.root, self.identity)

    def query(self, **changes):
        q = {'field_id': 'synthetic', 'latitude': 56.5, 'longitude': -5, 'method': 'BILINEAR'}
        q.update(changes)
        return self.package().query(q)

    def reject_change(self, callback):
        callback(self.m['fields'][0])
        self.write()
        with self.assertRaises(r.PackageError): self.package()

    def test_modified_payload(self):
        (self.root/'synthetic.f64').write_bytes(bytes([self.body[0]^1])+self.body[1:])
        with self.assertRaises(r.PackageError): self.package()

    def test_missing_metadata(self):
        (self.root/'manifest.json').unlink()
        with self.assertRaises(r.PackageError): self.package()

    def test_missing_payload(self):
        (self.root/'synthetic.f64').unlink()
        with self.assertRaises(r.PackageError): self.package()

    def test_modified_manifest(self):
        (self.root/'manifest.json').write_bytes((self.root/'manifest.json').read_bytes()+b' ')
        with self.assertRaises(r.PackageError): self.package()

    def test_wrong_trusted_identity(self):
        with self.assertRaises(r.PackageError): r.Package(self.root, '0'*64)

    def test_incompatible_version(self):
        self.m['version'] = 'v2'; self.write()
        with self.assertRaises(r.PackageError): self.package()

    def test_ambiguous_field(self):
        self.m['fields'].append(copy.deepcopy(self.m['fields'][0])); self.write()
        with self.assertRaises(r.PackageError): self.package()

    def test_missing_temporal_metadata(self):
        self.reject_change(lambda f: f.pop('temporal'))

    def test_unknown_temporal_structure(self):
        self.reject_change(lambda f: f['temporal'].update(kind='average'))

    def test_instant_interval_contradiction(self):
        self.reject_change(lambda f: f['temporal'].update(duration_seconds=86400))

    def test_negative_duration(self):
        t={'kind':'accumulation','reference_time':'2025-01-15T00:00:00Z','valid_time':'2025-01-16T00:00:00Z',
           'interval_start':'2025-01-15T00:00:00Z','interval_end':'2025-01-16T00:00:00Z',
           'duration_seconds':-1,'statistical_process_code':1}
        with self.assertRaises(r.PackageError): r.temporal(t)

    def test_wrong_interval_end(self):
        t={'kind':'accumulation','reference_time':'2025-01-15T00:00:00Z','valid_time':'2025-01-16T00:00:00Z',
           'interval_start':'2025-01-15T00:00:00Z','interval_end':'2025-01-15T23:00:00Z',
           'duration_seconds':86400,'statistical_process_code':1}
        with self.assertRaises(r.PackageError): r.temporal(t)

    def test_encoded_timestamp_mismatch(self):
        self.reject_change(lambda f: f['temporal'].update(valid_time='2025-01-17T00:00:00Z'))

    def test_encoded_step_mismatch(self):
        self.reject_change(lambda f: f['encoded_metadata'].update(forecastTime=12))

    def test_unit_metadata_mismatch(self):
        self.reject_change(lambda f: f.update(native_unit='degC'))

    def test_vertical_reference_mismatch(self):
        self.reject_change(lambda f: f['vertical'].update(reference='mean sea level'))

    def test_vertical_height_mismatch(self):
        self.reject_change(lambda f: f['vertical'].update(height_m=1.5))

    def test_parameter_authority_mismatch(self):
        self.reject_change(lambda f: f['parameter'].update(centre=98))

    def test_grid_scanning_mismatch(self):
        self.reject_change(lambda f: f['source_grid'].update(scanning_mode=64))

    def test_grid_longitude_origin_mismatch(self):
        self.reject_change(lambda f: f['source_grid'].update(longitude_origin=180))

    def test_unsupported_subset_longitude_wrap(self):
        self.reject_change(lambda f: f['subset'].update(periodic=True))

    def test_unsupported_ensemble(self):
        self.reject_change(lambda f: f['ensemble'].update(kind='member', member=0))

    def test_missing_provenance(self):
        self.reject_change(lambda f: f['provenance']['raw_input'].update(sha256=''))

    def test_nonfinite_payload_even_if_resealed(self):
        self.body=struct.pack('<d', math.nan)+self.body[8:]
        self.m['fields'][0]['payload']['sha256']=r.digest(self.body);self.write()
        with self.assertRaises(r.PackageError): self.package()

    def test_unsupported_missing_mask(self):
        self.reject_change(lambda f: f['missingness'].update(missing_cells=1))

    def test_truncated_payload(self):
        (self.root/'synthetic.f64').write_bytes(self.body[:-1])
        with self.assertRaises(r.PackageError): self.package()

    def test_component_traversal(self):
        self.reject_change(lambda f: f['payload'].update(filename='../synthetic.f64'))

    def test_duplicate_json_keys(self):
        with self.assertRaises(r.PackageError): r.parse(b'{"version":1,"version":2}')

    def test_nonfinite_json_constant(self):
        with self.assertRaises(r.PackageError): r.parse(b'{"latitude":NaN}')

    def test_unknown_field(self):
        self.assertEqual(self.query(field_id='wrong')['status'],'UNKNOWN_FIELD')

    def test_invalid_coordinates(self):
        for q in [{'latitude':91},{'latitude':math.nan},{'longitude':math.inf},{'latitude':True},
                  {'latitude':'56'},{'longitude':10**400}]:
            with self.subTest(q=q): self.assertEqual(self.query(**q)['status'],'INVALID_QUERY')

    def test_outside_nearest_rejected(self):
        self.assertEqual(self.query(latitude=59.001,method='NEAREST')['status'],'OUTSIDE_EXTENT')

    def test_unsupported_method(self):
        self.assertEqual(self.query(method='CUBIC')['status'],'UNSUPPORTED_METHOD')

    def test_bad_query_structure(self):
        for q in [None,[],{}, {'field_id':'synthetic','latitude':56.5,'longitude':-5,'method':'NEAREST','extra':True}]:
            self.assertEqual(self.package().query(q)['status'],'INVALID_QUERY')

    def test_explicit_assumption_mismatches(self):
        for expect in [{'native_unit':'m'},{'temporal_kind':'accumulation'},{'vertical':{'height_m':1.5}},
                       {'longitude_convention':'clamp'}, {'temporal':{'valid_time':'2025-01-17T00:00:00Z'}}]:
            self.assertEqual(self.query(expect=expect)['status'],'ASSUMPTION_MISMATCH')

    def test_longitude_equivalence(self):
        self.assertEqual(self.query(longitude=-5),self.query(longitude=355))
        self.assertEqual(self.query(longitude=-5),self.query(longitude=715))

    def test_affine_and_weights(self):
        result=self.query(latitude=56.375,longitude=-4.875)
        self.assertEqual([n['weight'] for n in result['nodes']],[.25]*4)
        self.assertEqual(result['native_value'],300+10.5*.25+12.5*.125)

    def test_halfway_nearest_east_south(self):
        node=self.query(latitude=56.375,longitude=-4.875,method='NEAREST')['nodes'][0]
        self.assertEqual((node['source_row'],node['source_column']),(135,1421))

    def test_closed_corner(self):
        for method in ['NEAREST','BILINEAR']:
            self.assertEqual(self.query(latitude=54,longitude=-2,method=method)['native_value'],300+20*.25+24*.125)

    def test_constant_field(self):
        self.body=struct.pack('<525d',*([7.25]*525))
        self.m['fields'][0]['payload']['sha256']=r.digest(self.body);self.write()
        self.assertEqual(self.query(latitude=56.37,longitude=-4.88)['native_value'],7.25)

    def test_immutability_and_deterministic_serialisation(self):
        package=self.package();before=package.values['synthetic']
        a=package.query({'field_id':'synthetic','latitude':56.5,'longitude':-5,'method':'NEAREST'})
        self.assertIs(before,package.values['synthetic'])
        self.assertEqual(r.canonical(a),r.canonical(package.query({'field_id':'synthetic','latitude':56.5,'longitude':-5,'method':'NEAREST'})))

    def test_guard_rejects_external_reads_network_imports_and_writes(self):
        shutil.copyfile(HERE/'offline_reader.py',self.root/'offline_reader.py')
        (self.root/'requests.json').write_bytes(b'[]')
        probe = """
import sys
sys.path.insert(0,'.')
from pathlib import Path
import offline_reader as r
r.stamp('2025-01-15T00:00:00Z');r.memory()
r.guard(Path('.'),Path('requests.json'))
def rejected(action):
    try: action()
    except r.PackageError: return
    raise AssertionError('Guard did not reject')
rejected(lambda: Path('../outside.grib2').read_bytes())
rejected(lambda: Path('requests.json').write_bytes(b'changed'))
rejected(lambda: sys.audit('socket.connect',None,None))
rejected(lambda: __import__('eccodes'))
print('four cooperative guard probes rejected')
"""
        out=subprocess.check_output([sys.executable,'-I','-S','-B','-c',probe],cwd=self.root)
        self.assertIn(b'four cooperative guard probes rejected',out)


class GenuineReplay(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MERIDIAN_WR013_PACKAGE'), 'Pinned genuine WR013 package not supplied; not a pass')
    def test_all_cells_and_isolated_query_replay(self):
        root=Path(os.environ['MERIDIAN_WR013_PACKAGE'])
        integrity=json.loads((root.parent/'package-integrity-receipt.json').read_text(encoding='utf-8'))
        previous=json.loads((root.parent/'offline-query-replay-receipt.json').read_text(encoding='utf-8'))
        pins=json.loads((HERE/'input-pins.json').read_text(encoding='utf-8'))
        package=r.Package(root,integrity['package_identity'])
        self.assertEqual(set(package.fields),set(pins['fields']))
        for fid, f in package.fields.items():
            self.assertEqual(len(package.values[fid]),525)
            self.assertEqual(f['provenance']['raw_input'],pins['fields'][fid]['input'])
            self.assertEqual(r.digest((root/f['payload']['filename']).read_bytes()),integrity['fields'][fid]['payload_sha256'])
            self.assertEqual(integrity['fields'][fid]['exact_equal_cells'],525)
        requests=[{k:v for k,v in q.items() if k not in ('label','expected_status')} for q in pins['queries']]
        with tempfile.TemporaryDirectory(prefix='wr013-real-isolated-') as name:
            isolated=Path(name)
            shutil.copytree(root,isolated/'package')
            shutil.copyfile(HERE/'offline_reader.py',isolated/'offline_reader.py')
            (isolated/'requests.json').write_bytes(r.canonical(requests))
            command=[sys.executable,'-I','-S','-B','offline_reader.py','--package','package','--identity',integrity['package_identity'],'--requests','requests.json','--isolate']
            a=r.parse(subprocess.check_output(command,cwd=isolated))
            b=r.parse(subprocess.check_output(command,cwd=isolated))
        a.pop('resources');b.pop('resources')
        self.assertEqual(a,b)
        self.assertTrue(a['isolation']['python_no_site'])
        self.assertTrue(a['isolation']['python_isolated'])
        self.assertEqual(a['isolation']['scientific_modules_loaded'],[])
        self.assertEqual(a['isolation'],previous['isolation'])
        for q,result in zip(pins['queries'],a['results']):
            self.assertEqual(result['status'],q['expected_status'])
            self.assertEqual(result,package.query({k:v for k,v in q.items() if k not in ('label','expected_status')}))


if __name__ == '__main__':
    unittest.main()
