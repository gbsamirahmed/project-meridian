from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np

from temporal_evidence import (
    cloud_clear_mask,
    cosine_illumination,
    snow_mask,
    temporal_correlation,
    temporal_scl_summary,
    temporal_statistics,
)


class TemporalEvidenceTests(unittest.TestCase):
    def test_cloud_and_snow_are_distinct(self) -> None:
        scl = np.array([[0, 3, 8, 9, 10, 11, 4]], dtype=np.uint8)
        self.assertEqual(cloud_clear_mask(scl).tolist(), [[False, False, False, False, False, True, True]])
        self.assertEqual(snow_mask(scl).tolist(), [[False, False, False, False, False, True, False]])
        summary = temporal_scl_summary(scl)
        self.assertEqual(summary["cloud_clear_cells_including_snow"], 2)
        self.assertEqual(summary["surface_clear_cells_excluding_snow"], 1)

    def test_flat_surface_illumination_is_sine_of_sun_elevation(self) -> None:
        result = cosine_illumination(np.zeros((1, 1)), np.full((1, 1), np.nan), 30.0, 180.0)
        self.assertAlmostEqual(float(result[0, 0]), 0.5, places=6)

    def test_sun_facing_slope_is_brighter_than_opposing_slope(self) -> None:
        slope = np.array([[60.0, 60.0]])
        aspect = np.array([[180.0, 0.0]])
        result = cosine_illumination(slope, aspect, 30.0, 180.0)
        self.assertGreater(float(result[0, 0]), float(result[0, 1]))
        self.assertAlmostEqual(float(result[0, 0]), 1.0, places=6)

    def test_temporal_statistics_preserve_missing_counts(self) -> None:
        values = np.array([[[1.0, 10.0]], [[3.0, np.nan]], [[5.0, 30.0]]], dtype=np.float32)
        statistics = temporal_statistics(values, coefficient_of_variation=True)
        self.assertEqual(statistics["count"].tolist(), [[3, 2]])
        self.assertAlmostEqual(float(statistics["median"][0, 0]), 3.0)
        self.assertAlmostEqual(float(statistics["range"][0, 1]), 20.0)
        self.assertTrue(np.isfinite(statistics["coefficient_of_variation"][0, 0]))

    def test_explicit_validity_excludes_an_observation(self) -> None:
        values = np.array([[[1.0]], [[100.0]], [[3.0]]], dtype=np.float32)
        valid = np.array([[[True]], [[False]], [[True]]])
        statistics = temporal_statistics(values, valid)
        self.assertEqual(int(statistics["count"][0, 0]), 2)
        self.assertAlmostEqual(float(statistics["mean"][0, 0]), 2.0)

    def test_temporal_correlation(self) -> None:
        observations = np.array([[[1.0]], [[2.0]], [[3.0]], [[4.0]]])
        driver = np.array([[[2.0]], [[4.0]], [[6.0]], [[8.0]]])
        result = temporal_correlation(observations, driver)
        self.assertAlmostEqual(float(result[0, 0]), 1.0, places=6)
        driver[2, 0, 0] = np.nan
        result = temporal_correlation(observations, driver)
        self.assertAlmostEqual(float(result[0, 0]), 1.0, places=6)

    def test_grid_mismatch_fails(self) -> None:
        with self.assertRaises(ValueError):
            temporal_statistics(np.ones((4, 2, 2)), np.ones((4, 3, 2), dtype=bool))
        with self.assertRaises(ValueError):
            temporal_correlation(np.ones((4, 2, 2)), np.ones((4, 3, 2)))


    def test_lab005c_config_preserves_seasons_resolutions_and_frozen_inputs(self) -> None:
        root = Path(__file__).resolve().parents[2]
        config = json.loads((root / "docs/earth-lab/tryfan-005c-temporal-evidence.json").read_text(encoding="utf-8"))
        observations = config["observations"]
        self.assertEqual([item["season"] for item in observations], ["winter", "spring", "summer", "autumn"])
        summer = next(item for item in observations if item["season"] == "summer")
        self.assertEqual(
            summer["official_product_id"],
            "S2A_MSIL2A_20260712T113331_N0512_R080_T30UVD_20260712T174812",
        )
        self.assertTrue(summer["reuse_lab005b_native"])
        self.assertNotIn(11, config["processing"]["cloud_invalid_scl_classes"])
        self.assertEqual(config["processing"]["snow_scl_class"], 11)
        self.assertEqual(
            {band["native_resolution_m"] for band in config["bands"].values() if band["code"] != "SCL"},
            {10, 20},
        )
        self.assertEqual(config["aoi"]["analysis_grids_m"], [10.0, 20.0])
        self.assertEqual(
            config["frozen_inputs"]["canonical_r16_sha256"],
            "31cbe763dac4072772ac9bcb4a3217b78eba0c10265e576ede708154288f6bf6",
        )
        self.assertEqual(
            config["frozen_inputs"]["lab005b_expected_deterministic_result_sha256"],
            "53d1dcf31d559f6f7ab6dcfe4ebf902b822e4ee7ebdaf2ae593b092c6344f0ab",
        )


if __name__ == "__main__":
    unittest.main()
