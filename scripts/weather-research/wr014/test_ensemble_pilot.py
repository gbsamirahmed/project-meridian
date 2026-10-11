"""Synthetic invariants are separate from optional genuine three-member replay."""
import copy
import json
import math
import os
from pathlib import Path
import tempfile
import unittest

import ensemble_pilot as p

HERE = Path(__file__).resolve().parent


def synthetic():
    """Invented metadata; never evidence for another historical member."""
    pin = p.checked_pin()
    m = copy.deepcopy(pin['expected'])
    m.update(tablesVersion=2, localTablesVersion=1, centre=7, subCentre=2, generatingProcessIdentifier=107, typeOfGeneratingProcess=4, productDefinitionTemplateNumber=1,
             typeOfEnsembleForecast=1, perturbationNumber=0, numberOfForecastsInEnsemble=30,
             dataRepresentationTemplateNumber=3, binaryScaleFactor=0, decimalScaleFactor=2,
             numberOfMissing=0, numberOfValues=259920, numberOfPoints=259920)
    return pin, m


def cohort():
    pin, m = synthetic()
    result = []
    for name, fp in pin['members'].items():
        n = copy.deepcopy(m)
        n.update(perturbationNumber=fp['member_number'], typeOfEnsembleForecast=fp['member_type_code'])
        result.append(p.interpret(n, fp, pin, 'synthetic-grid-seal'))
    return result


class SyntheticRejections(unittest.TestCase):
    def changed(self, key, value):
        c = cohort()
        c[1][key] = value
        with self.assertRaises(p.Error): p.comparable(c)

    def test_duplicate_identity(self):
        c = cohort(); c[1]['member'] = copy.deepcopy(c[0]['member'])
        with self.assertRaises(p.Error): p.comparable(c)

    def test_missing_identity(self):
        c = cohort(); c[1].pop('member')
        with self.assertRaises(p.Error): p.comparable(c)

    def test_missing_member_number(self):
        c = cohort(); c[1]['member'].pop('number')
        with self.assertRaises(p.Error): p.comparable(c)

    def test_filename_only_identity(self):
        c = cohort(); c[1]['member']['authority'] = 'filename only'
        with self.assertRaises(p.Error): p.comparable(c)

    def test_ambiguous_control(self):
        c = cohort(); c[1]['member']['role'] = 'control'
        with self.assertRaises(p.Error): p.comparable(c)

    def test_false_control_role(self):
        c = cohort(); c[1]['member']['role'] = c[0]['member']['role']
        with self.assertRaises(p.Error): p.comparable(c)

    def test_inconsistent_total(self):
        c = cohort(); c[1]['member']['encoded_number_of_forecasts'] = 31
        with self.assertRaises(p.Error): p.comparable(c)

    def test_smaller_than_selected_count(self):
        c = cohort()
        for x in c: x['member']['encoded_number_of_forecasts'] = 2
        with self.assertRaises(p.Error): p.comparable(c)

    def test_encoded_count_is_not_population(self):
        out = p.comparable(cohort())
        self.assertEqual(out['encoded_count_agreement'], 30)
        self.assertEqual(out['selection_size'], 3)
        self.assertEqual(out['encoded_to_full_population_mapping'], 'Unresolved')
        self.assertEqual(out['full_distribution_and_operational_weights'], 'Not tested')

    def test_system(self): self.changed('system', 'other ensemble')
    def test_product(self): self.changed('product', 'other delivery')
    def test_parameter(self): self.changed('parameter', {'codes': [0, 0, 6]})
    def test_parameter_authority(self):
        c = cohort(); v = copy.deepcopy(c[1]['parameter']); v['centre'] = 98
        self.changed('parameter', v)
    def test_units(self): self.changed('native_unit', 'Celsius')
    def test_level(self): self.changed('vertical', {'height_m': 10})
    def test_vertical_reference(self):
        v = copy.deepcopy(cohort()[1]['vertical']); v['reference'] = 'mean sea level'
        self.changed('vertical', v)
    def test_initialisation(self):
        t = copy.deepcopy(cohort()[1]['temporal']); t['reference_time'] = '2025-01-15T06:00:00Z'
        self.changed('temporal', t)
    def test_lead(self):
        t = copy.deepcopy(cohort()[1]['temporal']); t['lead_seconds'] = 43200
        self.changed('temporal', t)
    def test_validity(self):
        t = copy.deepcopy(cohort()[1]['temporal']); t['valid_time'] = '2025-01-16T06:00:00Z'
        self.changed('temporal', t)
    def test_temporal_support(self):
        t = copy.deepcopy(cohort()[1]['temporal']); t['kind'] = 'accumulation'
        self.changed('temporal', t)
    def test_grid(self): self.changed('grid', {'rows': 721})
    def test_grid_scanning(self):
        g = copy.deepcopy(cohort()[1]['grid']); g['scan'] = 64
        self.changed('grid', g)
    def test_missingness(self): self.changed('missingness', {'bitmap': True, 'missing_cells': 1})
    def test_deterministic_as_member(self):
        _, m = synthetic(); m['productDefinitionTemplateNumber'] = 0
        with self.assertRaises(p.Error): p.member_identity(m, {'member_number':0,'member_type_code':1})
    def test_unknown_member_type(self):
        _, m = synthetic(); m['typeOfEnsembleForecast'] = 255
        with self.assertRaises(p.Error): p.member_identity(m, {'member_number':0,'member_type_code':255})
    def test_unknown_member_number(self):
        _, m = synthetic(); m['perturbationNumber'] = None
        with self.assertRaises(p.Error): p.member_identity(m, {'member_number':0,'member_type_code':1})
    def test_boolean_identity(self):
        _, m = synthetic(); m['perturbationNumber'] = False
        with self.assertRaises(p.Error): p.member_identity(m, {'member_number':0,'member_type_code':1})
    def test_invalid_control_number(self):
        _, m = synthetic(); m['perturbationNumber'] = 7
        with self.assertRaises(p.Error): p.member_identity(m, {'member_number':7,'member_type_code':1})
    def test_nonfinite_statistics(self):
        for v in (math.nan, math.inf, -math.inf, None):
            with self.assertRaises(p.Error): p.subset_statistics([270, v, 280])
    def test_subset_population_std(self):
        out = p.subset_statistics([1, 2, 3])
        self.assertEqual(out['arithmetic_selected_subset_mean_K'], 2)
        self.assertAlmostEqual(out['population_standard_deviation_selected_subset_K'], math.sqrt(2/3))
        self.assertEqual(out['population'], 'SELECTED SUBSET ONLY')
    def test_full_probability_rejected(self):
        with self.assertRaises(p.Error): p.subset_statistics([270,280,290], 'event_probability')
    def test_full_ensemble_mean_rejected(self):
        with self.assertRaises(p.Error): p.subset_statistics([270,280,290], 'ensemble_mean')
    def test_confidence_interval_rejected(self):
        with self.assertRaises(p.Error): p.subset_statistics([270,280,290], 'confidence_interval')
    def test_unbounded_cohort(self):
        with self.assertRaises(p.Error): p.comparable(cohort()+cohort())
    def test_receipt_serialisation(self):
        c = cohort(); self.assertEqual(p.field.canonical(p.comparable(c)), p.field.canonical(p.comparable(c)))
    def test_wrong_pinned_raw(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'synthetic.grib2'; f.write_bytes(b'not a scientific field')
            with self.assertRaises(p.Error): p.field.pinned_input(f, p.checked_pin()['members']['control'])


@unittest.skipUnless(os.environ.get('MERIDIAN_WR014_INPUTS') and os.environ.get('MERIDIAN_WR007_GDAL_PYTHON'),
                     'genuine replay requires pinned local inputs and independent GDAL')
class GenuineReplay(unittest.TestCase):
    def test_full_three_member_independent_deterministic_replay(self):
        with tempfile.TemporaryDirectory(prefix='wr014-genuine-') as d:
            a,b=Path(d)/'a.json',Path(d)/'b.json'
            args=(Path(os.environ['MERIDIAN_WR014_INPUTS']),Path(os.environ['MERIDIAN_WR007_GDAL_PYTHON']))
            first=p.run(*args,a); second=p.run(*args,b)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(first,second)
            self.assertEqual(first['outcome'],'A')
            self.assertEqual(first,json.loads((HERE/'integrity-receipt.json').read_text(encoding='utf-8')))
            for x in first['members'].values():
                self.assertEqual(x['independent_comparison']['compared_cells'],259920)
                self.assertEqual(x['independent_comparison']['g2clib_rounding_profile_exact_cells'],259920)
                self.assertTrue(x['independent_comparison']['mask_agreement'])
                self.assertTrue(x['raw_input_unchanged'])


if __name__=='__main__': unittest.main()
