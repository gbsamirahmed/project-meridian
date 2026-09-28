from __future__ import annotations

import unittest

import numpy as np

from terrain_metrics import (
    aspect_summary,
    detrended_rms_roughness,
    numeric_summary,
    slope_aspect,
    terrain_curvatures,
)


class TerrainMetricsTests(unittest.TestCase):
    def test_flat_plane_has_zero_slope_undefined_aspect_and_zero_laplacian(self) -> None:
        elevation = np.full((21, 21), 650.0)
        slope, aspect = slope_aspect(elevation, 1.0)
        self.assertTrue(np.allclose(slope[1:-1, 1:-1], 0.0))
        self.assertTrue(np.all(np.isnan(aspect)))
        curvature = terrain_curvatures(elevation, 1.0)
        self.assertTrue(
            np.allclose(curvature["laplacian_per_m"][3:-3, 3:-3], 0.0)
        )
        self.assertTrue(np.all(np.isnan(curvature["profile_per_m"])))
        self.assertTrue(np.all(np.isnan(curvature["plan_per_m"])))

    def test_known_east_rising_plane_faces_west_at_45_degrees(self) -> None:
        columns = np.arange(15, dtype=float)[None, :]
        elevation = np.repeat(columns, 15, axis=0)
        slope, aspect = slope_aspect(elevation, 1.0)
        self.assertTrue(np.allclose(slope[2:-2, 2:-2], 45.0))
        self.assertTrue(np.allclose(aspect[2:-2, 2:-2], 270.0))

    def test_known_south_rising_plane_faces_north(self) -> None:
        rows = np.arange(15, dtype=float)[:, None]
        elevation = np.repeat(rows, 15, axis=1)
        slope, aspect = slope_aspect(elevation, 1.0)
        self.assertTrue(np.allclose(slope[2:-2, 2:-2], 45.0))
        north = np.minimum(aspect[2:-2, 2:-2], 360.0 - aspect[2:-2, 2:-2])
        self.assertTrue(np.allclose(north, 0.0))

    def test_concave_and_convex_paraboloids_have_opposite_curvature(self) -> None:
        coordinates = np.arange(-15.0, 16.0)
        x, y = np.meshgrid(coordinates, coordinates)
        bowl = 0.01 * (x * x + y * y)
        hill = -bowl
        bowl_curvature = terrain_curvatures(bowl, 1.0)
        hill_curvature = terrain_curvatures(hill, 1.0)
        annulus = (x * x + y * y >= 25.0) & (x * x + y * y <= 100.0)
        self.assertGreater(
            float(np.nanmedian(bowl_curvature["laplacian_per_m"][annulus])), 0.0
        )
        self.assertLess(
            float(np.nanmedian(hill_curvature["laplacian_per_m"][annulus])), 0.0
        )
        self.assertGreater(
            float(np.nanmedian(bowl_curvature["profile_per_m"][annulus])), 0.0
        )
        self.assertLess(
            float(np.nanmedian(hill_curvature["profile_per_m"][annulus])), 0.0
        )
        self.assertGreater(
            float(np.nanmedian(bowl_curvature["plan_per_m"][annulus])), 0.0
        )
        self.assertLess(
            float(np.nanmedian(hill_curvature["plan_per_m"][annulus])), 0.0
        )

    def test_plane_detrended_roughness_is_zero_for_any_plane(self) -> None:
        rows, columns = np.indices((31, 31), dtype=float)
        plane = 400.0 + 0.3 * columns - 0.2 * rows
        for window in (5, 15):
            roughness = detrended_rms_roughness(plane, window)
            self.assertLess(float(np.nanmax(roughness)), 1e-5)

    def test_roughness_detects_irregularity_and_changes_with_scale(self) -> None:
        rows, columns = np.indices((51, 51), dtype=float)
        irregular = 500.0 + 0.2 * columns + ((rows + columns) % 2) * 1.5
        local = detrended_rms_roughness(irregular, 5)
        broad = detrended_rms_roughness(irregular, 15)
        self.assertGreater(float(np.nanmedian(local)), 0.5)
        self.assertGreater(float(np.nanmedian(broad)), 0.5)
        self.assertNotEqual(float(np.nanmedian(local)), float(np.nanmedian(broad)))

    def test_nodata_propagates_through_required_neighbourhoods(self) -> None:
        elevation = np.arange(441, dtype=float).reshape(21, 21)
        elevation[10, 10] = np.nan
        slope, aspect = slope_aspect(elevation, 1.0)
        self.assertTrue(np.all(np.isnan(slope[9:12, 9:12])))
        self.assertTrue(np.all(np.isnan(aspect[9:12, 9:12])))
        roughness = detrended_rms_roughness(elevation, 5)
        self.assertTrue(np.all(np.isnan(roughness[8:13, 8:13])))

    def test_summaries_are_deterministic_and_aspect_is_circular(self) -> None:
        values = np.array([[1.0, 2.0], [3.0, np.nan]])
        self.assertEqual(numeric_summary(values, "m"), numeric_summary(values, "m"))
        aspects = np.array([[350.0, 10.0], [np.nan, 0.0]])
        summary = aspect_summary(aspects)
        wrapped = min(
            summary["circular_mean_degrees"],
            360.0 - summary["circular_mean_degrees"],
        )
        self.assertLess(wrapped, 1e-10)
        self.assertGreater(summary["mean_resultant_length"], 0.98)


if __name__ == "__main__":
    unittest.main()