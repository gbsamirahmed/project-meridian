from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
from rasterio.transform import from_origin

from calibrate_photo_skyline import (
    PhotoSkyline,
    TerrainHorizon,
    evaluate_solution,
    extract_photo_skyline,
    horizontal_ray_angles,
)

from diagnose_photo_geometry import (
    Profile,
    bilinear_sample,
    bng_bearing_distance,
    line_of_sight,
)


class PhotoGeometryDiagnosticTests(unittest.TestCase):
    def test_bng_bearing_uses_clockwise_from_grid_north(self) -> None:
        bearing, distance = bng_bearing_distance(0.0, 0.0, -3.0, -4.0)
        self.assertAlmostEqual(bearing, 216.86989764584402)
        self.assertAlmostEqual(distance, 5.0)

    def test_bilinear_sample_uses_pixel_centres(self) -> None:
        data = np.array([[10.0, 20.0], [30.0, 40.0]])
        transform = from_origin(100.0, 202.0, 1.0, 1.0)
        sample = bilinear_sample(
            data,
            transform,
            np.array([101.0]),
            np.array([201.0]),
        )
        self.assertAlmostEqual(float(sample[0]), 25.0)

    def test_line_of_sight_reports_intervening_ridge(self) -> None:
        profile = Profile(
            "blocked",
            np.array([0.0, 50.0, 100.0]),
            np.array([0.0, 50.0, 100.0]),
            np.array([0.0, 0.0, 0.0]),
            np.array([100.0, 170.0, 200.0]),
            100.0,
        )
        result = line_of_sight(profile, 1.7)
        self.assertFalse(result["line_of_sight_clear"])
        self.assertGreater(
            result["maximum_intervening_clearance_above_sightline_m"], 18.0
        )

    def test_line_of_sight_accepts_clear_profile(self) -> None:
        profile = Profile(
            "clear",
            np.array([0.0, 50.0, 100.0]),
            np.array([0.0, 50.0, 100.0]),
            np.array([0.0, 0.0, 0.0]),
            np.array([100.0, 140.0, 200.0]),
            100.0,
        )
        result = line_of_sight(profile, 1.7)
        self.assertTrue(result["line_of_sight_clear"])

    def test_photo_skyline_extractor_follows_strong_synthetic_boundary(self) -> None:
        width, height = 120, 90
        boundary = 52.0 - 0.18 * np.arange(width)
        image = np.full((height, width, 3), 245, dtype=np.uint8)
        for x, y in enumerate(boundary):
            image[int(round(y)) :, x, :] = 55
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.png"
            Image.fromarray(image).save(path)
            result = extract_photo_skyline(path)
        reliable = ~result.cloud_affected
        self.assertLess(
            float(np.max(np.abs(result.y_pixels[reliable] - boundary[reliable]))),
            3.0,
        )
        self.assertLess(
            float(np.mean(result.confidence[result.cloud_affected])),
            float(np.mean(result.confidence[reliable])),
        )

    def test_horizontal_projection_uses_pinhole_field_of_view(self) -> None:
        angles, focal = horizontal_ray_angles(640, 40.0)
        self.assertGreater(focal, 0.0)
        self.assertAlmostEqual(float(angles[0]), -20.0, delta=0.1)
        self.assertAlmostEqual(float(angles[-1]), 20.0, delta=0.1)

    def test_solution_recovers_pitch_from_shape_without_vertical_offset_bias(self) -> None:
        width, height = 160, 120
        heading, fov, pitch = 247.0, 42.0, 18.5
        ray_angles, focal = horizontal_ray_angles(width, fov)
        bearings = np.linspace(210.0, 285.0, 3001)
        terrain_angles = (
            28.0
            + 5.0 * np.exp(-((bearings - 243.0) / 4.5) ** 2)
            - 2.5 * np.exp(-((bearings - 252.0) / 2.0) ** 2)
            + 3.0 * np.exp(-((bearings - 260.0) / 5.0) ** 2)
        )
        sampled = np.interp(heading + ray_angles, bearings, terrain_angles)
        y = (height - 1) / 2.0 - focal * np.tan(np.radians(sampled - pitch))
        skyline = PhotoSkyline(
            y_pixels=y,
            confidence=np.ones(width),
            cloud_affected=np.zeros(width, dtype=bool),
            edge_strength=np.full(width, 100.0),
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
        result = evaluate_solution(skyline, horizon, heading, fov)
        self.assertAlmostEqual(result["solved_pitch_degrees"], pitch, places=10)
        self.assertLess(result["weighted_rmse_degrees"], 1e-10)
        wrong = evaluate_solution(skyline, horizon, heading + 5.0, fov)
        self.assertGreater(
            wrong["weighted_rmse_degrees"],
            result["weighted_rmse_degrees"] + 0.5,
        )


if __name__ == "__main__":
    unittest.main()
