import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from surface_uncertainty_audit import (
    ablation_metrics, conditional_meaningful_entropy, gap_flags,
    meaningful_ranking, reconstruction_readiness, top_pair_summary,
)
from underlying_surface_model import CLASSES


class SurfaceUncertaintyAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.config = json.loads((self.root / "docs/earth-lab/tryfan-008-uncertainty-audit.json").read_text())
        self.thresholds = self.config["thresholds"]

    def test_frozen_lab007_identity_matches(self):
        lab007 = (self.root / self.config["frozen_lab007"]["root"]).resolve()
        report_path = lab007 / "lab007-report.json"
        before = hashlib.sha256(report_path.read_bytes()).hexdigest()
        report = json.loads(report_path.read_text())
        after = hashlib.sha256(report_path.read_bytes()).hexdigest()
        self.assertEqual(before, self.config["frozen_lab007"]["report_sha256"])
        self.assertEqual(report["deterministic_result_sha256"], self.config["frozen_lab007"]["deterministic_result_sha256"])
        self.assertEqual(before, after)

    def test_output_root_cannot_overwrite_frozen_baseline(self):
        frozen = (self.root / self.config["frozen_lab007"]["root"]).resolve()
        output = (self.root / self.config["output_root"]).resolve()
        self.assertNotEqual(frozen, output)
        self.assertNotIn(frozen, output.parents)

    def test_meaningful_ranking_preserves_information_when_unknown_dominates(self):
        probabilities = np.array([[.18, .08, .25, .10, .08, .31]])
        ranking = meaningful_ranking(probabilities)
        self.assertTrue(ranking["unknown_dominant"][0])
        self.assertAlmostEqual(ranking["meaningful_mass"][0], .69)
        self.assertEqual(ranking["first_index"][0], 2)
        self.assertGreater(ranking["margin"][0], 0)

    def test_uncertainty_metrics_are_bounded_and_finite(self):
        probabilities = np.array([[.18, .08, .25, .10, .08, .31], [.2] * 5 + [0.]])
        entropy = conditional_meaningful_entropy(probabilities)
        self.assertTrue(np.all(np.isfinite(entropy)))
        self.assertTrue(np.all((entropy >= 0) & (entropy <= 1)))

    def test_ablation_metrics_are_deterministic_and_bounded(self):
        baseline = np.array([[.1, .1, .2, .2, .1, .3]])
        ablated = np.array([[.12, .08, .18, .22, .1, .3]])
        first = ablation_metrics(baseline, ablated, np.array([True]), .01)
        second = ablation_metrics(baseline, ablated, np.array([True]), .01)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first["mean_total_variation_distance"], 0)
        self.assertLessEqual(first["mean_total_variation_distance"], 1)

    def test_gap_flags_stay_in_documented_bit_schema(self):
        probabilities = np.array([[[.1, .1, .2, .2, .1, .3], [.2, .1, .1, .1, .1, .4]]])
        conflict = np.array([[.8, .1]])
        family_count = np.array([[4, 3]])
        temporal = np.array([[.4, .1]])
        prefs = {name: np.broadcast_to(np.array([.1, .1, .2, .2, .1, .3]), probabilities.shape) for name in ("terrain", "sentinel", "habitat", "geology")}
        bitmask, flags = gap_flags(
            probabilities, conflict, family_count, temporal, prefs,
            self.thresholds, {frozenset(item) for item in self.config["overlapping_pairs"]},
            self.config["information_gap_flags"],
        )
        allowed = 0
        for value in self.config["information_gap_flags"].values():
            allowed |= value
        self.assertTrue(np.all((bitmask & np.uint8(~allowed & 0xFF)) == 0))
        self.assertTrue(flags["missing_evidence"][0, 1])

    def test_missing_family_is_not_equated_with_none_mapped(self):
        self.assertIn("missing_evidence", self.config["information_gap_flags"])
        lab007_config = json.loads((self.root / self.config["model_config"]).read_text())
        none_mapped = lab007_config["geology_superficial_preferences"]["none_mapped"]
        self.assertGreater(none_mapped[-1], 0)
        self.assertNotEqual(none_mapped, [0, 0, 0, 0, 0, 1])

    def test_temporal_state_remains_explicitly_dated(self):
        lab007 = (self.root / self.config["frozen_lab007"]["root"]).resolve()
        package = json.loads((lab007 / "lab007-surface-model-package.json").read_text())
        sentinel = package["context"]["sentinel"]
        self.assertEqual(sentinel["temporal_class"], "dated_dynamic_observational")
        self.assertEqual(len(sentinel["observations"]), 4)
        self.assertTrue(all(item["acquisition_time_utc"] for item in sentinel["observations"]))

    def test_top_pair_summary_is_reproducible(self):
        first = np.array([0, 2, 2])
        second = np.array([1, 3, 4])
        summary = top_pair_summary(first, second, np.array([True, True, True]))
        self.assertEqual({item["pair"] for item in summary}, {"rock__scree_talus", "heath__grass", "heath__wet_ground"})
        self.assertTrue(all(item["cells"] == 1 for item in summary))

    def test_readiness_schema_is_bounded(self):
        probabilities = np.array([[[.1, .1, .3, .1, .1, .3], [.1, .1, .11, .1, .1, .49]]])
        readiness = reconstruction_readiness(probabilities, self.thresholds)
        self.assertTrue(np.all(np.isin(readiness, [1, 2, 3])))


if __name__ == "__main__":
    unittest.main()
