"""Synthetic rejection/invariant tests; one separately labelled opt-in real replay."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import ifs_contract_pilot as pilot


class Synthetic(unittest.TestCase):
    def setUp(self):
        self.pin = pilot.checked_pin()
        self.m = copy.deepcopy(self.pin['fields']['temperature']['expected'])

    def bad_concept(self, key, value, identity='temperature'):
        m = copy.deepcopy(self.pin['fields'][identity]['expected']); m[key] = value
        with self.assertRaises(pilot.Error): pilot.concept(identity, m, 'a'*64, 'b'*64)

    def test_provider_identity(self): self.bad_concept('centre', 7)
    def test_local_namespace(self): self.bad_concept('localTablesVersion', 0, 'precipitation')
    def test_wrong_parameter(self): self.bad_concept('parameterNumber', 8, 'precipitation')
    def test_wrong_unit(self): self.bad_concept('units', 'kg m**-2', 'precipitation')
    def test_vertical_distinction(self): self.bad_concept('level', 1.5)
    def test_ensemble_rejection(self): self.bad_concept('typeOfProcessedData', 4)
    def test_provenance(self):
        with self.assertRaises(pilot.Error): pilot.concept('temperature', self.m, 'unknown', 'b'*64)
    def test_single_u_not_vector(self):
        c = pilot.concept('wind_u', self.pin['fields']['wind_u']['expected'], 'a'*64, 'b'*64)
        self.assertFalse(c['vector']['paired_vector']); self.assertEqual(c['vector']['partner'], 'NOT ACQUIRED')
    def test_grid_relative_vector_rejection(self): self.bad_concept('uvRelativeToGrid', 1, 'wind_u')
    def test_surface_not_zero_height(self):
        c = pilot.concept('precipitation', self.pin['fields']['precipitation']['expected'], 'a'*64, 'b'*64)
        self.assertIsNone(c['vertical']['height_m'])
    def test_instant_vs_interval(self):
        a = pilot.temporal(self.m); b = pilot.temporal(self.pin['fields']['precipitation']['expected'])
        self.assertEqual(a['kind'], 'instant'); self.assertEqual(b['kind'], 'accumulation')
        self.assertEqual(b['duration_seconds'], 86400); self.assertEqual(b['forecast_lead_to_start_seconds'], 0)
        self.assertEqual(b['increment']['seconds'], 450)
    def test_instant_time_contradiction(self):
        self.m['forecastTime'] = 23
        with self.assertRaises(pilot.Error): pilot.temporal(self.m)
    def interval_bad(self, key, value):
        m = copy.deepcopy(self.pin['fields']['precipitation']['expected']); m[key] = value
        with self.assertRaises(pilot.Error): pilot.temporal(m)
    def test_missing_interval(self):
        m = copy.deepcopy(self.pin['fields']['precipitation']['expected']); del m['lengthOfTimeRange']
        with self.assertRaises(pilot.Error): pilot.temporal(m)
    def test_statistic_rejection(self): self.interval_bad('typeOfStatisticalProcessing', 0)
    def test_interval_zero(self): self.interval_bad('lengthOfTimeRange', 0)
    def test_interval_end_contradiction(self): self.interval_bad('dayOfEndOfOverallTimeInterval', 17)
    def test_unknown_increment(self): self.interval_bad('timeIncrement', 0)
    def test_unknown_time_unit(self): self.interval_bad('indicatorOfUnitForTimeRange', 7)
    def test_unsupported_geometry(self):
        for key, value in [('gridType', 'reduced_gg'), ('scanningMode', 64), ('shapeOfTheEarth', 5),
                           ('longitudeOfLastGridPointInDegrees', 360), ('numberOfPoints', 1)]:
            m = copy.deepcopy(self.m); m[key] = value
            with self.assertRaises(pilot.Error): pilot.ShiftedGrid(m)
    def test_coordinate_labels(self):
        g = pilot.ShiftedGrid(self.m)
        self.assertEqual(g.coordinates(0, 0), (90, 180))
        self.assertEqual(g.coordinates(0, 720), (90, 0))
        self.assertEqual(g.position(-40.1, 179.9), g.position(-40.1, -180.1))
    def sampler(self):
        m = copy.deepcopy(self.m); m.update(Ni=4, Nj=5, numberOfPoints=20,
            iDirectionIncrementInDegrees=90, jDirectionIncrementInDegrees=45,
            longitudeOfLastGridPointInDegrees=90)
        a = np.arange(20, dtype=float).reshape(5, 4)
        return pilot.ShiftedSampler(a, np.zeros(a.shape, dtype=bool), m)
    def test_shifted_index_and_half_tie(self):
        s = self.sampler()
        self.assertEqual(s.query({'latitude': 0, 'longitude': 0, 'method': 'NEAREST'})['nodes'][0]['column'], 2)
        q = s.query({'latitude': 0, 'longitude': 225, 'method': 'NEAREST'})
        self.assertEqual(q['nodes'][0]['column'], 1)
    def test_constant_bilinear_and_wrapping(self):
        s = self.sampler(); s.values[:] = 7
        q = {'latitude': 10, 'longitude': 179.9, 'method': 'BILINEAR'}
        a = s.query(q); q['longitude'] -= 360; b = s.query(q)
        self.assertAlmostEqual(a['temperature_K'], 7, places=13); self.assertEqual(a['nodes'], b['nodes'])
        self.assertAlmostEqual(a['weight_sum'], 1, places=15)
    def test_boundaries_and_invalid(self):
        s = self.sampler()
        for lat, status in [(89, 'UNSUPPORTED_POLAR_CAP_BILINEAR'), (91, 'LATITUDE_OUT_OF_RANGE'),
                            (float('nan'), 'NONFINITE_COORDINATE')]:
            self.assertEqual(s.query({'latitude': lat, 'longitude': 0, 'method': 'BILINEAR'})['status'], status)
    def test_missing_nodes_fail_closed(self):
        s = self.sampler(); s.mask[2, 2] = True
        self.assertEqual(s.query({'latitude': 0, 'longitude': 0, 'method': 'BILINEAR'})['status'], 'MISSING_CONTRIBUTING_NODE')
    def test_nonfinite_node(self):
        s = self.sampler(); s.values[2, 2] = np.inf
        self.assertEqual(s.query({'latitude': 0, 'longitude': 0, 'method': 'NEAREST'})['status'], 'UNINTERPRETABLE_NODE')
    def test_synthetic_binary32_prediction(self):
        a = self.m['referenceValue']+np.arange(4)*2.**self.m['binaryScaleFactor']
        b = a.astype(np.float32).astype(float); z = np.zeros(a.shape, dtype=bool)
        self.assertEqual(pilot.numeric_compare(a, b, z, z, self.m)['compared_cells'], 4)
        b[0] += .1
        with self.assertRaises(pilot.Error): pilot.numeric_compare(a, b, z, z, self.m)
    def test_unsupported_packing(self):
        m = copy.deepcopy(self.m); m['dataRepresentationTemplateNumber'] = 3
        z = np.zeros(1, dtype=bool)
        with self.assertRaises(pilot.Error): pilot.numeric_compare(np.zeros(1), np.zeros(1), z, z, m)
    def test_actual_mask_requires_evidence(self):
        a = np.zeros(1); z = np.ones(1, dtype=bool)
        with self.assertRaises(pilot.Error): pilot.numeric_compare(a, a, z, z, self.m)
    def test_framing_malformed(self):
        for body in [b'', b'GRIB', b'GRIB'+bytes(100)]:
            with self.assertRaises(pilot.Error): pilot.sections(body)
    def test_canonical_determinism(self):
        self.assertEqual(pilot.field.canonical({'a': 1, 'b': 2}), pilot.field.canonical({'b': 2, 'a': 1}))
    def test_original_gfs_profiles_remain_strict(self):
        with self.assertRaises(pilot.Error): pilot.spatial.Grid(self.m)
        with self.assertRaises(pilot.Error): pilot.precipitation.interval(self.pin['fields']['precipitation']['expected'])
    def test_affine_synthetic_no_mutation(self):
        s = self.sampler(); s.values[:] = np.arange(5)[:, None]*3+np.arange(4)[None, :]*2
        before = s.values.copy()
        q = s.query({'latitude': 22.5, 'longitude': 225, 'method': 'BILINEAR'})
        self.assertAlmostEqual(q['temperature_K'], 5.5)
        self.assertTrue(np.array_equal(before, s.values))
    def test_metadata_comparison_does_not_claim_numeric(self):
        s = self.sampler(); m = copy.deepcopy(self.m)
        m.update(Ni=4, Nj=5, numberOfPoints=20, iDirectionIncrementInDegrees=90,
                 jDirectionIncrementInDegrees=45, longitudeOfLastGridPointInDegrees=90)
        q = pilot.query_checks(s.values, s.mask, m, None, [90, 0, 135, 0, -45, 112.5, 0, 0, 1],
                               [{'latitude': 0, 'longitude': 0, 'method': 'NEAREST'}])[0]
        self.assertIn('NOT TESTED', q['comparison']['numerical'])


class GenuineReplay(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('MERIDIAN_WR011_INPUTS') and os.environ.get('MERIDIAN_WR007_GDAL_PYTHON'), 'pinned external inputs/reference runtime not supplied')
    def test_three_real_fields_replay(self):
        root = Path(os.environ['MERIDIAN_WR011_INPUTS']); runtime = Path(os.environ['MERIDIAN_WR007_GDAL_PYTHON'])
        with tempfile.TemporaryDirectory() as temporary:
            a, b = Path(temporary)/'a.json', Path(temporary)/'b.json'
            first = pilot.run(root, runtime, a, allow_unavailable=True)
            second = pilot.run(root, runtime, b, allow_unavailable=True)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(first['outcome'], 'B')
            for identity in first['fields']:
                result = first['fields'][identity]
                self.assertTrue(result['input_and_decoded_array_unchanged'])
                self.assertEqual(result['summary']['cells'], 1038240)
                self.assertEqual(result['numerical_comparison']['compared_cells'], 0)
            accepted = json.loads((pilot.HERE/'integrity-receipt.json').read_text())
            self.assertEqual(accepted['scientific_receipt_sha256'], pilot.field.digest(a))
            self.assertEqual(first, second)


if __name__ == '__main__': unittest.main()
