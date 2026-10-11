"""Synthetic rejection tests and separately opted-in genuine WR015 replay."""
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import support_comparison as pilot


class SyntheticRejections(unittest.TestCase):
    def setUp(self):
        self.pin = pilot.checked_pin()
        self.m = deepcopy(self.pin['expected'])
        self.forecast = deepcopy(self.pin['forecast']['expected'])

    def assert_mismatch(self, key, value):
        self.m[key] = value
        with self.assertRaises(pilot.Error):
            pilot.matched(self.m, self.forecast, 'grid', 'grid')

    def test_mismatched_grid(self):
        with self.assertRaises(pilot.Error):
            pilot.matched(self.m, self.forecast, 'grid', 'another-grid')

    def test_unverified_model_configuration(self): self.assert_mismatch('generatingProcessIdentifier', 107)
    def test_wrong_producer(self): self.assert_mismatch('centre', 98)
    def test_wrong_run(self): self.assert_mismatch('dataDate', 20250116)
    def test_wrong_lead(self): self.assert_mismatch('forecastTime', 48)
    def test_wrong_parameter(self): self.assert_mismatch('parameterNumber', 4)
    def test_wrong_level(self): self.assert_mismatch('typeOfFirstFixedSurface', 103)
    def test_wrong_unit(self): self.assert_mismatch('units', 'K')
    def test_wrong_temporal_support(self): self.assert_mismatch('stepType', 'accum')

    def test_unknown_vertical_reference(self):
        r = pilot.difference(2700, 2600, None, 'LN02', 'same-height-quantity', 'qualified-point-to-point')
        self.assertIsNone(r['signed_difference'])
        self.assertIsNone(r['absolute_difference'])

    def test_incompatible_vertical_reference(self):
        r = pilot.difference(2700, 2600, 'geopotential', 'LN02', 'same-height-quantity', 'qualified-point-to-point')
        self.assertIsNone(r['signed_difference'])

    def test_same_unit_different_quantity(self):
        r = pilot.difference(2700, 2600, 'LN02', 'LN02', 'different-height-quantities', 'qualified-point-to-point')
        self.assertIsNone(r['signed_difference'])

    def test_explicit_signed_convention_synthetic_only(self):
        r = pilot.difference(2500, 2600, 'synthetic-reference', 'synthetic-reference', 'same-height-quantity', 'qualified-point-to-point')
        self.assertEqual((r['signed_difference'], r['absolute_difference']), (-100, 100))

    def test_unsupported_aggregation(self):
        with self.assertRaises(pilot.Error):
            pilot.difference(2500, 2600, 'same', 'same', 'same-height-quantity', 'model-cell-mean')

    def test_no_temperature_correction(self):
        with self.assertRaises(pilot.Error):
            pilot.difference(2500, 2600, 'same', 'same', 'same-height-quantity', 'qualified-point-to-point', 'temperature-correction')

    def test_no_skill_inference(self):
        with self.assertRaises(pilot.Error):
            pilot.difference(2500, 2600, 'same', 'same', 'same-height-quantity', 'qualified-point-to-point', 'forecast-skill')

    def test_invalid_height(self):
        with self.assertRaises(pilot.Error):
            pilot.difference(math.nan, 2600, None, 'LN02', 'different', 'point')

    def test_east_south_tie_and_native_registration(self):
        self.assertEqual(pilot.terrain_cell(2625000, 1092000, [2625000,1091000,2626000,1092000]), (0,0))
        self.assertEqual(pilot.terrain_cell(2625001, 1091999, [2625000,1091000,2626000,1092000]), (2,2))

    def test_no_cross_tile_edge_clipping(self):
        for e, n in [(2626000,1091500), (2625500,1091000), (2624999,1091500), (2625500,1092001)]:
            with self.assertRaises(pilot.Error):
                pilot.terrain_cell(e,n,[2625000,1091000,2626000,1092000])

    def test_unknown_posting(self):
        with self.assertRaises(pilot.Error): pilot.terrain_cell(1,1,[0,0,2,2],1)

    def test_invalid_coordinates(self):
        with self.assertRaises(pilot.Error): pilot.terrain_cell(math.inf,1,[0,0,2,2])

    def test_nodata(self):
        with self.assertRaises(pilot.Error): pilot.valid_terrain(-9999,False)

    def test_masked(self):
        with self.assertRaises(pilot.Error): pilot.valid_terrain(2600,True)

    def test_nonfinite_terrain(self):
        with self.assertRaises(pilot.Error): pilot.valid_terrain(math.nan,False)

    def test_unverified_parent(self):
        record = deepcopy(self.pin['acquisition'][-1]); record['headers']['ETag'] = 'different'
        with self.assertRaises(pilot.Error): pilot.validate_parent(self.pin['source'],record)

    def test_unverified_range(self):
        record = deepcopy(self.pin['acquisition'][-1]); record['status'] = 200
        with self.assertRaises(pilot.Error): pilot.validate_parent(self.pin['source'],record)

    def test_unsupported_packing(self):
        m = deepcopy(self.m); m['binaryScaleFactor'] = 0
        with self.assertRaises(pilot.Error):
            pilot.compare_arrays(np.ones(2),np.ones(2),np.zeros(2,bool),np.zeros(2,bool),m)

    def test_missingness_disagreement(self):
        with self.assertRaises(pilot.Error):
            pilot.compare_arrays(np.ones(2),np.ones(2),np.zeros(2,bool),np.ones(2,bool),self.m)

    def test_numerical_disagreement(self):
        with self.assertRaises(pilot.Error):
            pilot.compare_arrays(np.array([self.m['referenceValue']/100]),np.array([0.]),np.zeros(1,bool),np.zeros(1,bool),self.m)

    def test_truncated_message(self):
        with self.assertRaises(pilot.Error): pilot.field.validate_framing(b'GRIB')

    def test_unsupported_grid_geometry(self):
        m = deepcopy(self.m); m['scanningMode'] = 64
        with self.assertRaises(pilot.Error): pilot.spatial.Grid(m)

    def test_invalid_model_query(self):
        sampler = pilot.spatial.Sampler(np.zeros((721,1440)),np.zeros((721,1440),bool),self.m)
        with self.assertRaises(pilot.Error): pilot.model_query(sampler,91,7,'NEAREST')

    def test_no_interpolation_fallback(self):
        sampler = pilot.spatial.Sampler(np.zeros((721,1440)),np.zeros((721,1440),bool),self.m)
        with self.assertRaises(pilot.Error): pilot.model_query(sampler,90,7,'BILINEAR')

    def test_receipt_determinism_and_explicit_null(self):
        value = pilot.difference(2700,2600,None,'LN02','different','point')
        self.assertEqual(pilot.field.canonical(value),pilot.field.canonical(deepcopy(value)))
        self.assertIn(b'null',pilot.field.canonical(value))


@unittest.skipUnless(all(os.environ.get(n) for n in
    ('MERIDIAN_WR015_INPUT','MERIDIAN_WR007_INPUT','MERIDIAN_WR015_DATA','MERIDIAN_WR007_GDAL_PYTHON')),
    'Explicit genuine local inputs and independent interpreter required; no synthetic fallback')
class GenuineReplay(unittest.TestCase):
    def test_actual_full_grid_and_five_native_cells(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('MERIDIAN_WR015_SCRATCH')) as d:
            first = pilot.run(Path(os.environ['MERIDIAN_WR015_INPUT']),Path(os.environ['MERIDIAN_WR007_INPUT']),
                              Path(os.environ['MERIDIAN_WR015_DATA']),Path(os.environ['MERIDIAN_WR007_GDAL_PYTHON']),Path(d)/'receipt.json')
        accepted = json.loads(pilot.HERE.joinpath('integrity-receipt.json').read_text())
        self.assertEqual(first,accepted)
        self.assertEqual(first['independent_comparison']['compared_cells'],1038240)
        self.assertEqual(len(first['locations']),5)
        self.assertTrue(all(x['comparison']['signed_difference'] is None for x in first['locations']))


if __name__ == '__main__': unittest.main()
