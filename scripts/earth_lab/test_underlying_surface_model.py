import json
from pathlib import Path
import unittest

import numpy as np

from underlying_surface_model import (
    CLASSES, categorical_preferences, fuse_sources, geology_preferences,
    normalized_entropy, sentinel_preferences, terrain_preferences,
)
from analyze_underlying_surface import _coverage


class UnderlyingSurfaceModelTests(unittest.TestCase):
    def setUp(self):
        self.rules = {"steep_ramp_degrees": [20, 50], "gentle_ramp_degrees": [5, 25], "rough_ramp_m_rms": [0.2, 0.9], "smooth_ramp_m_rms": [0.1, 0.5]}
        self.sentinel_rules = {"vegetation_ndvi_ramp": [0.25, 0.65], "stable_ndvi_stddev_ramp": [0.1, 0.3], "moisture_ndmi_ramp": [0.05, 0.3], "persistent_low_ndvi_maximum_rock_increment": 0.03}

    def _fuse(self, prefs, avail):
        budgets = {name: 1.0 for name in prefs}
        return fuse_sources(prefs, avail, budgets, [0.55, .55, .65, .65, .55, 1.1], .3, 1.2, np.array([True]))

    def test_probabilities_are_bounded_normalized_and_deterministic(self):
        preference, available = terrain_preferences(np.array([35.]), np.array([.7]), self.rules)
        first = self._fuse({"terrain": preference}, {"terrain": available})["probabilities"]
        second = self._fuse({"terrain": preference}, {"terrain": available})["probabilities"]
        np.testing.assert_array_equal(first, second)
        self.assertAlmostEqual(float(first.sum()), 1.0)
        self.assertTrue(np.all((first >= 0) & (first <= 1)))

    def test_entropy_clear_less_than_ambiguous(self):
        clear = normalized_entropy(np.array([[1, 0, 0, 0, 0, 0.]]))[0]
        ambiguous = normalized_entropy(np.full((1, 6), 1 / 6))[0]
        self.assertLess(clear, ambiguous)
        self.assertAlmostEqual(ambiguous, 1.0)

    def test_missing_source_increases_other_unknown(self):
        preference, available = terrain_preferences(np.array([20.]), np.array([.2]), self.rules)
        present = self._fuse({"terrain": preference}, {"terrain": available})["probabilities"][0, 5]
        missing = self._fuse({"terrain": preference}, {"terrain": np.array([False])})["probabilities"][0, 5]
        self.assertGreater(missing, present)

    def test_conflict_increases_other_unknown(self):
        heath = np.array([[0, 0, 1, 0, 0, 0.]], dtype=float)
        grass = np.array([[0, 0, 0, 1, 0, 0.]], dtype=float)
        result = self._fuse({"a": heath, "b": grass}, {"a": np.array([True]), "b": np.array([True])})
        self.assertGreater(result["conflict"][0], 0.5)
        self.assertGreater(result["scores"][0, 5], 1.1)

    def test_slope_alone_cannot_force_rock(self):
        preference, available = terrain_preferences(np.array([80.]), np.array([3.]), self.rules)
        result = self._fuse({"terrain": preference}, {"terrain": available})["probabilities"][0]
        self.assertLess(result[0], 0.5)

    def test_low_ndvi_alone_cannot_force_rock_or_become_timeless(self):
        preference, available = sentinel_preferences(np.array([.05]), np.array([.05]), np.array([-.1]), np.array([True]), self.sentinel_rules)
        result = self._fuse({"sentinel": preference}, {"sentinel": available})["probabilities"][0]
        self.assertLess(result[0], 0.3)
        config = json.loads((Path(__file__).resolve().parents[2] / "docs/earth-lab/tryfan-007-underlying-surface.json").read_text())
        self.assertIn("Dated Sentinel state does not become timeless surface identity.", config["semantic_invariants"])

    def test_bedrock_and_no_superficial_deposit_do_not_force_rock(self):
        preference, available, mapped = geology_preferences(np.array([0]), {}, np.array([1]), {"none_mapped": [.04,.04,.06,.06,.04,.76], "other_superficial_deposit": [0,0,0,0,0,1]})
        result = self._fuse({"geology": preference}, {"geology": available})["probabilities"][0]
        self.assertFalse(mapped[0])
        self.assertLess(result[0], 0.25)
        self.assertGreater(result[5], result[0])

    def test_unavailable_geology_differs_from_valid_none_mapped(self):
        preference, available, mapped = geology_preferences(np.array([0]), {}, np.array([0]), {"none_mapped": [.04,.04,.06,.06,.04,.76], "other_superficial_deposit": [0,0,0,0,0,1]})
        self.assertFalse(available[0]); self.assertFalse(mapped[0]); self.assertEqual(preference[0, 5], 1.0)

    def test_evidence_coverage_distinguishes_none_mapped_from_unavailable(self):
        availability = {
            "terrain": np.array([True, True]),
            "sentinel": np.array([True, True]),
            "habitat": np.array([True, False]),
            "geology": np.array([True, False]),
        }
        mapped = np.array([False, False])
        valid = np.array([True, True])
        probabilities = np.full((2, 6), 1 / 6, dtype=float)
        uncertainty = np.ones(2)
        summary, count = _coverage(availability, mapped, valid, probabilities, uncertainty)
        np.testing.assert_array_equal(count, np.array([4, 2]))
        self.assertEqual(summary["bgs_superficial_context"]["valid_none_mapped_cells"], 1)
        self.assertEqual(summary["bgs_superficial_context"]["source_unavailable_cells"], 1)
        self.assertEqual(summary["family_count"]["4"]["cells"], 1)
        self.assertEqual(summary["family_count"]["2"]["cells"], 1)

    def test_source_budget_is_bounded(self):
        preference = np.array([[1,0,0,0,0,0.]], dtype=float)
        result = fuse_sources({"x": preference}, {"x": np.array([True])}, {"x": 1.7}, [.1]*6, .3, 1.2, np.array([True]))
        self.assertAlmostEqual(float(result["contributions"]["x"].sum()), 1.7)

    def test_source_specificity_and_temporal_metadata_are_preserved(self):
        root = Path(__file__).resolve().parents[2]
        config = json.loads((root / "docs/earth-lab/tryfan-007-underlying-surface.json").read_text())
        self.assertEqual(config["frozen_inputs"]["lab006_report"]["deterministic_result_sha256"], "f0b85ebfa28ecf9bad63c7db9a515b15b442fd2cdf5a3c51c71cc0989df51280")
        self.assertIn("habitat_lookup", config["frozen_inputs"])
        self.assertIn("geology_lookup", config["frozen_inputs"])
        self.assertEqual(tuple(config["classes"]), CLASSES)

    def test_categorical_unknown_remains_explicit(self):
        pref, available = categorical_preferences(np.array([0, 1]), {1: "known"}, {"known": [0,0,1,0,0,0], "other_or_unknown": [0,0,0,0,0,1]})
        self.assertFalse(available[0]); self.assertEqual(pref[0, 5], 1.0); self.assertTrue(available[1])


if __name__ == "__main__":
    unittest.main()
