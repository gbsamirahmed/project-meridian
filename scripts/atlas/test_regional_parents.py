"""Synthetic support/aggregation tests; no external estate required."""
import unittest
from unittest.mock import patch
import numpy as np
import regional_parents as p


class ParentTests(unittest.TestCase):
    def test_complete_mean_and_constant(self):
        a = np.arange(16, dtype=float).reshape(4, 4)
        mean, count = p.aggregate(a, np.ones(a.shape, dtype='uint32'))
        np.testing.assert_array_equal(mean, [[2.5, 4.5], [10.5, 12.5]])
        np.testing.assert_array_equal(count, 4)
        again, count = p.aggregate(mean, count)
        self.assertEqual(again.item(), 7.5); self.assertEqual(count.item(), 16)
        mean, count = p.aggregate(np.full((4, 4), 2987.125), np.ones((4, 4), dtype='uint32'))
        np.testing.assert_array_equal(mean, 2987.125)

    def test_partial_is_subset_not_full_cell_or_confidence(self):
        a = np.array([[10., np.nan], [20., np.nan]])
        mean, count = p.aggregate(a, np.array([[1, 0], [1, 0]], dtype='uint32'))
        self.assertEqual(mean.item(), 15); self.assertEqual(count.item(), 2)
        mean, count = p.aggregate(np.full((2, 2), np.nan), np.zeros((2, 2), dtype='uint32'))
        self.assertTrue(np.isnan(mean.item())); self.assertEqual(count.item(), 0)
        with self.assertRaises(ValueError):
            p.aggregate(np.full((2, 2), np.nan), np.ones((2, 2), dtype='uint32'))

    def test_recursive_support_preserves_observed_sum(self):
        a = np.arange(64, dtype=float).reshape(8, 8); c = np.ones((8, 8), dtype='uint32')
        c[:3, :3] = 0; a[c == 0] = np.nan
        expected = np.nanmean(a)
        for _ in range(3):
            a, c = p.aggregate(a, c)
        self.assertEqual(c.item(), 55); self.assertAlmostEqual(a.item(), expected)

    def test_geometry_support_checks_extent_not_just_centres(self):
        class Identity:
            def transform(self, x, y):
                return x, y
        with patch.object(p.sp, 'BOUNDS', (-p.rt.WORLD / 2, 0, 0, p.rt.WORLD / 2)):
            c = p.support_cells(0, 0, 0, np.ones((256, 256)), Identity())
        # Source edge guard excludes first row/col and cells on the half-world boundary.
        self.assertEqual(c[0, 5], 0); self.assertEqual(c[5, 0], 0)
        self.assertEqual(c[5, 5], 1); self.assertEqual(c[200, 200], 0)

    def test_alignment_padding_keeps_missing_support(self):
        def grids(z):
            return (1, 1, 1, 1, (256, 256), None) if z == 14 else (0, 0, 0, 0, (256, 256), None)
        with patch.object(p.sp, 'hierarchy', grids):
            a, c = p.parent_grid(np.full((256, 256), 40.), np.ones((256, 256), dtype='uint32'), 13)
        self.assertTrue(np.all(np.isnan(a[:128]))); self.assertTrue(np.all(c[:128] == 0))
        np.testing.assert_array_equal(a[128:, 128:], 40)
        np.testing.assert_array_equal(c[128:, 128:], 4)


if __name__ == '__main__':
    unittest.main()
