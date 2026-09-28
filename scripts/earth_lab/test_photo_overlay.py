from __future__ import annotations

import unittest
from pathlib import Path

from photo_overlay import (
    aspect_ratio,
    camera_mismatches,
    signed_angle_delta_degrees,
    validate_opacity,
)


class PhotoOverlayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.expected = {
            "location_cm": {
                "x": 52549.121742951684,
                "y": -29494.947166356724,
                "z": -16443.74237411574,
            },
            "rotation_degrees": {
                "pitch": 30.3418,
                "yaw": 165.1419994775921,
                "roll": 0.0,
            },
            "horizontal_fov_degrees": 35.2,
            "aspect_ratio": 4.0 / 3.0,
        }
        self.observed = {
            **self.expected,
            "location_cm": dict(self.expected["location_cm"]),
            "rotation_degrees": dict(self.expected["rotation_degrees"]),
            "constrain_aspect_ratio": True,
        }

    def test_reference_aspect_is_native_four_by_three(self) -> None:
        self.assertEqual(aspect_ratio(640, 480), 4.0 / 3.0)

    def test_default_camera_matches_fixed_calibration(self) -> None:
        self.assertEqual(camera_mismatches(self.observed, self.expected), [])

    def test_overlay_refuses_camera_orientation_drift(self) -> None:
        self.observed["rotation_degrees"]["yaw"] = 158.591999
        mismatches = camera_mismatches(self.observed, self.expected)
        self.assertTrue(any("yaw" in item for item in mismatches))

    def test_overlay_refuses_position_fov_and_aspect_drift(self) -> None:
        self.observed["location_cm"]["x"] += 1.0
        self.observed["horizontal_fov_degrees"] = 40.0
        self.observed["constrain_aspect_ratio"] = False
        mismatches = camera_mismatches(self.observed, self.expected)
        self.assertTrue(any("camera X" in item for item in mismatches))
        self.assertTrue(any("HFOV" in item for item in mismatches))
        self.assertTrue(any("constrain" in item for item in mismatches))

    def test_opacity_is_bounded(self) -> None:
        self.assertEqual(validate_opacity(0.5), 0.5)
        for invalid in (-0.01, 1.01, float("nan")):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_opacity(invalid)

    def test_wrapped_angle_delta(self) -> None:
        self.assertAlmostEqual(signed_angle_delta_degrees(-179.0, 179.0), 2.0)

    def test_unreal_overlay_source_preserves_camera_and_exposes_controls(self) -> None:
        source = (
            Path(__file__).with_name("unreal_photo_overlay.py").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("MERIDIAN_REFERENCE_OVERLAY_ENABLED", source)
        self.assertIn("MERIDIAN_REFERENCE_OVERLAY_OPACITY", source)
        self.assertIn("verified_against_fixed_lab004a_calibration", source)
        self.assertIn('"modified_by_overlay": False', source)
        self.assertNotIn("set_field_of_view", source)
        self.assertNotIn("set_aspect_ratio", source)
        self.assertNotIn("set_constraint_aspect_ratio", source)


    def test_restore_script_saves_only_after_strict_camera_and_landscape_checks(self) -> None:
        source = Path(__file__).with_name("unreal_restore_camera.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("camera_mismatches(after, expected)", source)
        self.assertIn("landscape_after != landscape_before", source)
        self.assertIn("camera.modify()", source)
        self.assertIn("camera.camera_component.modify()", source)
        self.assertIn(
            'save_map(world, "/Game/Tryfan_Lab004")',
            source,
        )
        self.assertIn("set_actor_location_and_rotation", source)
        self.assertIn("set_field_of_view", source)
        self.assertNotIn("Landscape.import", source)
        self.assertNotIn("set_actor_scale3d", source)

    def test_saved_map_validator_uses_same_strict_comparison(self) -> None:
        source = Path(__file__).with_name("unreal_validate_camera.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("load_map(MAP_ASSET)", source)
        self.assertIn("camera_mismatches(observed, expected)", source)
        self.assertIn('"result": "PASS" if not mismatches else "FAIL"', source)


if __name__ == "__main__":
    unittest.main()
