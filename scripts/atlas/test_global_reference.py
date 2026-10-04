"""Synthetic checks only: no external terrain, network or geoid grids."""
import unittest
import numpy as np
from rasterio import Affine
from assess_global_reference import sample_posts, buffer_mask, stable_mask, fit_translation, conservative_cover


class ReferenceTests(unittest.TestCase):
    def test_point_registration_and_joined_source_boundary(self):
        # First centre at (7, 47), not the transform's outer half-pixel corner.
        transform = Affine(.01, 0, 6.995, 0, -.01, 47.005)
        values = np.arange(36, dtype=float).reshape(6, 6)
        np.testing.assert_allclose(sample_posts(values, transform, np.array([7, 7.025]), np.array([47, 46.975])), [0, 17.5], atol=1e-10)
        with self.assertRaises(ValueError):
            sample_posts(values, transform, np.array([8]), np.array([47]))

    def test_buffer_uses_metres_and_diagonal_distance(self):
        a = np.zeros((9, 9), bool); a[4, 4] = True
        result = buffer_mask(a, 50, step=25)
        self.assertTrue(result[4, 6]); self.assertTrue(result[5, 5])
        self.assertFalse(result[6, 6]); self.assertFalse(result[4, 7])

    def test_mask_rejects_each_independent_invalid_support_class(self):
        valid = np.ones(8, bool); valid[0] = False
        bare = np.ones(8, bool); bare[1] = False
        ice = np.zeros(8, bool); ice[2] = True
        edge = np.full(8, 500); edge[3] = 199
        slope = np.array([20, 20, 20, 20, 4, 41, 5, 40])
        np.testing.assert_array_equal(stable_mask(valid, bare, ice, edge, slope), [False]*6 + [True]*2)

    def test_cover_exclusions_are_not_mistaken_for_nodata_or_lost(self):
        classes = np.full((4, 4), 60, dtype='uint8')
        classes[0, 0] = 80
        transform = Affine(10, 0, 2620000, 0, -10, 1097000)
        coarse = transform*Affine.scale(2)
        np.testing.assert_array_equal(conservative_cover(classes, transform, 2056, coarse, (2, 2)), [[False, True], [True, True]])
        # Extending the diagnostic target beyond the source must not add bare land.
        extended = conservative_cover(classes, transform, 2056, coarse, (3, 3))
        self.assertFalse(extended[2].any()); self.assertFalse(extended[:, 2].any())

    def test_translation_signature_recovers_known_components_with_outliers(self):
        x, y = np.meshgrid(np.linspace(-1, 1, 70), np.linspace(-1, 1, 70))
        east = np.sin(x*3)*.4; north = np.cos(y*4)*.3
        difference = 4*east - 7*north + 2
        difference[::17, ::13] += 100
        fitted = fit_translation(difference, east, north, np.ones_like(x, bool))
        np.testing.assert_allclose(fitted['coefficients'], [4, -7, 2], atol=.02)
        self.assertGreater(fitted['downweightedFraction'], 0)

    def test_flat_terrain_cannot_establish_translation(self):
        a = np.ones((30, 30))
        self.assertEqual(fit_translation(a, np.zeros_like(a), np.zeros_like(a), a.astype(bool))['status'], 'insufficient support')


if __name__ == '__main__':
    unittest.main()
