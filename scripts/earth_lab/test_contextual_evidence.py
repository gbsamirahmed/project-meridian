import json
from pathlib import Path
import unittest

import numpy as np

from analyze_contextual_evidence import _fill_opaque_cartography
from contextual_evidence import (
    binary_overlap,
    categorical_summary,
    clip_geometry_to_bounds,
    habitat_group,
    mode_reduce_2x2,
    nearest_palette_indices,
    parse_mosaic_components,
)


class ContextualEvidenceTests(unittest.TestCase):
    def test_mosaic_and_grouping_preserve_source_meaning(self):
        label = "Mosaic of:50% B.1.1,50% E.2.1"
        self.assertEqual(parse_mosaic_components(label), {"B.1.1": 0.5, "E.2.1": 0.5})
        self.assertEqual(habitat_group(None, label, {"B.1.1": "grass", "E.2.1": "wet"}), "mixed_mosaic")

    def test_categorical_summary_keeps_unknown_as_unmapped(self):
        result = categorical_summary(np.array([[0, 1], [1, 2]]), {1: "a", 2: "b"}, 100.0)
        self.assertEqual(result["mapped_cells"], 3)
        self.assertAlmostEqual(result["coverage_fraction"], 0.75)

    def test_mode_reduction_never_interpolates_ids(self):
        source = np.array([[1, 1, 2, 0], [1, 2, 2, 2], [3, 3, 4, 4], [3, 0, 4, 5]], dtype=np.uint8)
        reduced = mode_reduce_2x2(source)
        np.testing.assert_array_equal(reduced, np.array([[1, 2], [3, 4]], dtype=np.uint8))

    def test_palette_matching_respects_transparency_and_tolerance(self):
        rgba = np.array([[[101, 99, 50, 255], [200, 200, 200, 0], [0, 0, 0, 255]]], dtype=np.uint8)
        result = nearest_palette_indices(rgba, [{"id": 7, "rgb": [100, 100, 50]}], 3.0)
        np.testing.assert_array_equal(result, np.array([[7, 0, 0]], dtype=np.uint16))

    def test_overlap_reports_directional_agreement(self):
        result = binary_overlap(np.array([1, 1, 0], dtype=bool), np.array([1, 0, 1], dtype=bool))
        self.assertAlmostEqual(result["jaccard"], 1 / 3)
        self.assertAlmostEqual(result["right_given_left"], 0.5)

    def test_configuration_preserves_provenance_and_frozen_inputs(self):
        root = Path(__file__).resolve().parents[2]
        config = json.loads((root / "docs/earth-lab/tryfan-006-contextual-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(config["aoi"]["bounds"], [264900, 357800, 267900, 360800])
        self.assertEqual(config["habitat"]["licence"], "Open Government Licence 3.0")
        self.assertEqual(config["geology"]["nominal_scale"], "1:50,000")
        self.assertEqual(config["frozen_inputs"]["canonical_r16_sha256"], "31cbe763dac4072772ac9bcb4a3217b78eba0c10265e576ede708154288f6bf6")
        self.assertIn("must not be treated as metre-scale truth", config["habitat"]["effective_scale"])

    def test_vector_clip_keeps_polygon_inside_aoi(self):
        geometry = {"type": "Polygon", "coordinates": [[[-1, -1], [2, -1], [2, 2], [-1, 2], [-1, -1]]]}
        clipped = clip_geometry_to_bounds(geometry, (0, 0, 1, 1))
        self.assertIsNotNone(clipped)
        for x, y in clipped["coordinates"][0]:
            self.assertGreaterEqual(x, 0)
            self.assertLessEqual(x, 1)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(y, 1)

    def test_cartographic_fill_does_not_fill_transparent_absence(self):
        source = np.array([[1, 0, 2], [1, 0, 0]], dtype=np.uint8)
        opaque = np.array([[1, 1, 1], [1, 1, 0]], dtype=bool)
        result, count = _fill_opaque_cartography(source, opaque)
        self.assertEqual(count, 2)
        self.assertNotEqual(result[0, 1], 0)
        self.assertNotEqual(result[1, 1], 0)
        self.assertEqual(result[1, 2], 0)


if __name__ == "__main__":
    unittest.main()
