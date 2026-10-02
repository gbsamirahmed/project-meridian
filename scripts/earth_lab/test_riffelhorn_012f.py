"""Small analytical controls for light axes, transfer and light-space registration."""
import unittest
import numpy as np
from riffelhorn_012f import DIRECTIONS, illumination, light_uv, linear_luminance, region_statistics, baseline_equivalence


class LightingTests(unittest.TestCase):
    def test_baseline_audit_rejects_changed_lighting_not_zero_mean_dither(self):
        old = np.full((1080, 1920, 3), 120, np.uint8)
        new = old.copy(); new[:, ::2] += 1; new[:, 1::2] -= 1
        self.assertEqual(baseline_equivalence(new, old)['signed_encoded_mean_difference'], 0)
        with self.assertRaises(ValueError): baseline_equivalence(old+1, old)

    def test_opposing_azimuths_preserve_elevation_and_source_axes(self):
        a, b = map(np.asarray, DIRECTIONS.values())
        np.testing.assert_allclose(np.linalg.norm(a), 1, atol=1e-8)
        np.testing.assert_array_equal(a[:2], -b[:2])
        self.assertEqual(a[2], b[2])
        self.assertAlmostEqual(np.degrees(np.arcsin(a[2])), 60, places=5)
        # Unreal Y is south: the first vector is north-east illumination.
        self.assertGreater(a[0], 0); self.assertLess(a[1], 0)

    def test_shadow_removes_only_directional_contribution(self):
        normal = np.array([[0, 0, 1], [0, 0, -1], DIRECTIONS['northeast']])
        direct = illumination(normal, DIRECTIONS['northeast'])
        shadow = illumination(normal, DIRECTIONS['northeast'], visibility=0)
        np.testing.assert_allclose(shadow, .35)
        self.assertTrue((shadow <= direct).all())
        self.assertAlmostEqual(direct[2], 1, places=7)
        self.assertAlmostEqual(illumination(normal[1], DIRECTIONS['northeast'], ambient=.65), .65)

    def test_light_space_uv_orientation_depth_and_metres(self):
        origin = np.array([10., 20., 30.])
        p = np.array([origin, origin+[1, 0, 0], origin+[0, 1, 0], origin+[0, 0, 2]])
        actual = light_uv(p, origin, [1, 0, 0], [0, 1, 0], [0, 0, 1], 4)
        np.testing.assert_allclose(actual, [[.5, .5, 0], [.75, .5, 0], [.5, .25, 0], [.5, .5, 2]])

    def test_luminance_is_linear_and_dark_metric_not_global_black_background(self):
        rgb = np.full((4, 4, 3), 128, dtype=np.uint8)
        self.assertAlmostEqual(float(linear_luminance(rgb).mean()), .2158605, places=6)
        stats = region_statistics(rgb)
        self.assertEqual(stats['display_luma_at_most_5_fraction'], 0)
        self.assertEqual(stats['mean_absolute_horizontal_gradient'], 0)
        rgb[0, 0] = 0
        self.assertEqual(region_statistics(rgb)['display_luma_at_most_5_fraction'], 1/16)


if __name__ == '__main__': unittest.main()
