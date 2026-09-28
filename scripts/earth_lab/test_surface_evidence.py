from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from rasterio.transform import from_origin
from rasterio.warp import Resampling

from observational_evidence import EvidenceCatalogue, EvidenceQuery, Observation
from sentinel2_evidence import observation_from_items
from surface_evidence import (
    AnalysisGrid,
    apply_valid_mask,
    assert_grid,
    normalized_difference,
    reproject_numeric,
    scl_summary,
    scl_valid_mask,
    sha256_file,
    stable_json_sha256,
    surface_reflectance,
)


class SurfaceEvidenceTests(unittest.TestCase):
    def test_reflectance_scale_offset_and_nodata(self) -> None:
        raw = np.array([[0, 1000, 2500]], dtype=np.uint16)
        result = surface_reflectance(raw, scale=0.0001, offset=-0.1, nodata=0)
        self.assertTrue(np.isnan(result[0, 0]))
        self.assertAlmostEqual(float(result[0, 1]), 0.0, places=7)
        self.assertAlmostEqual(float(result[0, 2]), 0.15, places=7)

    def test_indices_preserve_missing_and_reject_low_signal(self) -> None:
        nir = np.array([[0.5, 0.01, np.nan, 0.2]], dtype=np.float32)
        red = np.array([[0.1, 0.001, 0.1, -0.01]], dtype=np.float32)
        result = normalized_difference(nir, red, minimum_sum=0.02, require_nonnegative=True)
        self.assertAlmostEqual(float(result[0, 0]), 2.0 / 3.0, places=6)
        self.assertTrue(np.isnan(result[0, 1]))
        self.assertTrue(np.isnan(result[0, 2]))
        self.assertTrue(np.isnan(result[0, 3]))

    def test_scl_mask_is_explicit(self) -> None:
        scl = np.array([[0, 2, 3, 4, 8, 9, 10, 11]], dtype=np.uint8)
        self.assertEqual(scl_valid_mask(scl).tolist(), [[False, True, False, True, False, False, False, False]])
        summary = scl_summary(scl)
        self.assertEqual(summary["valid_cells"], 2)
        self.assertAlmostEqual(summary["cloud_fraction"], 3 / 8)
        self.assertAlmostEqual(summary["cloud_shadow_fraction"], 1 / 8)

    def test_analysis_grid_and_alignment(self) -> None:
        grid = AnalysisGrid("EPSG:27700", 0, 0, 20, 20, 10)
        assert_grid(grid)
        source = np.array([[1, 2], [3, 4]], dtype=np.float32)
        aligned = reproject_numeric(source, from_origin(0, 20, 10, 10), "EPSG:27700", grid, resampling=Resampling.nearest)
        np.testing.assert_array_equal(source, aligned)
        with self.assertRaises(ValueError):
            assert_grid(AnalysisGrid("EPSG:27700", 0, 0, 21, 20, 10))

    def test_masking_does_not_turn_missing_into_zero(self) -> None:
        values = np.array([[0.2, 0.8]], dtype=np.float32)
        masked = apply_valid_mask(values, np.array([[True, False]]))
        self.assertEqual(float(masked[0, 0]), float(values[0, 0]))
        self.assertTrue(np.isnan(masked[0, 1]))

    def test_hashes_are_deterministic_and_detect_input_change(self) -> None:
        self.assertEqual(stable_json_sha256({"b": 2, "a": 1}), stable_json_sha256({"a": 1, "b": 2}))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.bin"
            path.write_bytes(b"terrain-a")
            before = sha256_file(path)
            path.write_bytes(b"terrain-b")
            self.assertNotEqual(before, sha256_file(path))

    def test_official_and_access_items_share_product_identity(self) -> None:
        official = {"id": "PRODUCT", "properties": {"datetime": "2026-01-01T00:00:00Z"}}
        cog = {"id": "COG", "properties": {"s2:product_uri": "PRODUCT.SAFE"}, "assets": {}}
        self.assertEqual(observation_from_items(official, cog).product_id, "PRODUCT")
        cog["properties"]["s2:product_uri"] = "OTHER.SAFE"
        with self.assertRaises(ValueError):
            observation_from_items(official, cog)

    def test_provider_registry_supports_location_time_evidence_query(self) -> None:
        class Provider:
            def query(self, request: EvidenceQuery) -> list[Observation]:
                return [Observation("test", "p", request.datetime_range, request.crs)]
        catalogue = EvidenceCatalogue()
        catalogue.register("sentinel2", Provider())
        request = EvidenceQuery((0, 0, 1, 1), "EPSG:4326", "2026-01-01/2026-01-02", ("surface_reflectance",))
        self.assertEqual(catalogue.query("sentinel2", request)[0].product_id, "p")

    def test_configuration_preserves_resolution_and_terrain_identity(self) -> None:
        config_path = Path(__file__).parents[2] / "docs" / "earth-lab" / "tryfan-005b-sentinel2.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(config["aoi"]["analysis_grids_m"], [10.0, 20.0])
        self.assertEqual(config["bands"]["blue"]["native_resolution_m"], 10)
        self.assertEqual(config["bands"]["swir16"]["native_resolution_m"], 20)
        self.assertEqual(config["terrain"]["canonical_r16_sha256"], "31cbe763dac4072772ac9bcb4a3217b78eba0c10265e576ede708154288f6bf6")
        self.assertIn("sentinel-2-c1-l2a", config["bands"]["red"]["url"])


if __name__ == "__main__":
    unittest.main()
