from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from calibrate_photo_skyline import PhotoSkyline, TerrainHorizon, horizontal_ray_angles
from photo_fit import (
    bound_reached,
    decode_landscape_r16,
    evaluate_camera,
    sample_surface,
    solve_bounded_pitch,
)


class PhotoFitTests(unittest.TestCase):
    def test_r16_decode_uses_manifest_encoding_and_full_vertex_bounds(self) -> None:
        encoded = np.array(
            [[32768, 32896, 33024], [32640, 32768, 32896], [32512, 32640, 32768]],
            dtype="<u2",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "surface.r16"
            encoded.tofile(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            surface = decode_landscape_r16(
                path,
                width=3,
                height=3,
                bounds=(100.0, 200.0, 102.0, 202.0),
                vertical_origin_m_odn=650.0,
                z_scale=100.0,
                expected_sha256=digest,
            )
        self.assertAlmostEqual(surface.spacing_m, 1.0)
        self.assertAlmostEqual(sample_surface(surface, 100.0, 202.0), 650.0)
        self.assertAlmostEqual(sample_surface(surface, 102.0, 202.0), 652.0)
        self.assertAlmostEqual(sample_surface(surface, 100.0, 200.0), 648.0)
        self.assertAlmostEqual(sample_surface(surface, 101.0, 201.0), 650.0)

    def test_r16_hash_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "surface.r16"
            np.full((2, 2), 32768, dtype="<u2").tofile(path)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                decode_landscape_r16(
                    path,
                    width=2,
                    height=2,
                    bounds=(0.0, 0.0, 1.0, 1.0),
                    vertical_origin_m_odn=650.0,
                    z_scale=150.0,
                    expected_sha256="0" * 64,
                )

    def test_bounded_pitch_cannot_escape_configured_interval(self) -> None:
        width, height = 80, 60
        heading, fov = 250.0, 40.0
        ray_angles, focal = horizontal_ray_angles(width, fov)
        bearings = np.linspace(220.0, 280.0, 1201)
        terrain_angles = 35.0 + 2.0 * np.sin(np.radians((bearings - 250.0) * 8.0))
        sampled = np.interp(heading + ray_angles, bearings, terrain_angles)
        photographic_pitch = 20.0
        y = (height - 1) / 2.0 - focal * np.tan(
            np.radians(sampled - photographic_pitch)
        )
        skyline = PhotoSkyline(
            y_pixels=y,
            confidence=np.ones(width),
            cloud_affected=np.zeros(width, dtype=bool),
            edge_strength=np.ones(width),
            width=width,
            height=height,
        )
        horizon = TerrainHorizon(
            true_bearings_degrees=bearings,
            elevation_angles_degrees=terrain_angles,
            distances_m=np.ones_like(bearings),
            elevations_m_odn=np.ones_like(bearings),
            eastings=np.ones_like(bearings),
            northings=np.ones_like(bearings),
        )
        result = solve_bounded_pitch(skyline, horizon, heading, fov, (25.0, 30.0))
        self.assertEqual(result["pitch_degrees"], 25.0)
        self.assertTrue(result["pitch_bound_reached"])

    def test_metric_is_deterministic_and_preserves_fov(self) -> None:
        width, height = 64, 48
        bearings = np.linspace(230.0, 270.0, 801)
        terrain = 30.0 + np.cos(np.radians((bearings - 250.0) * 12.0))
        angles, focal = horizontal_ray_angles(width, 36.0)
        sampled = np.interp(250.0 + angles, bearings, terrain)
        y = (height - 1) / 2.0 - focal * np.tan(np.radians(sampled - 29.0))
        skyline = PhotoSkyline(
            y, np.ones(width), np.zeros(width, dtype=bool), np.ones(width), width, height
        )
        horizon = TerrainHorizon(
            bearings, terrain, np.ones_like(bearings), np.ones_like(bearings),
            np.ones_like(bearings), np.ones_like(bearings)
        )
        first = evaluate_camera(skyline, horizon, 250.0, 36.0, 29.0)
        second = evaluate_camera(skyline, horizon, 250.0, 36.0, 29.0)
        self.assertEqual(first["horizontal_fov_degrees"], 36.0)
        self.assertAlmostEqual(first["weighted_rmse_pixels"], 0.0, places=10)
        self.assertEqual(first["score"], second["score"])

    def test_lab004b_config_freezes_004a_and_uses_distinct_actor(self) -> None:
        root = Path(__file__).resolve().parents[2]
        fit = json.loads(
            (root / "docs/earth-lab/tryfan-004b-photo-fit.json").read_text(
                encoding="utf-8"
            )
        )
        overlay = json.loads(
            (root / "docs/earth-lab/tryfan-004-photo-overlay.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(fit["lab004a"]["immutable_snapshot"], overlay["camera"])
        self.assertNotEqual(
            fit["output"]["camera_actor_label"], overlay["camera"]["actor_label"]
        )
        self.assertEqual(fit["fit"]["fixed"]["roll_degrees"], 0.0)
        self.assertEqual(fit["fit"]["fixed"]["aspect_ratio"], 4.0 / 3.0)
        self.assertFalse(bound_reached(0.0, (-20.0, 20.0), 0.1))
        self.assertTrue(bound_reached(20.0, (-20.0, 20.0), 0.1))


if __name__ == "__main__":
    unittest.main()