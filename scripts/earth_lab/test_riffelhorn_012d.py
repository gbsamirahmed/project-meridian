"""Independent synthetic checks for the held-out heightfield experiment."""
import unittest
import numpy as np
from riffelhorn_012d import (ORIGIN, spatial_split, unique_heights, Interpolant,
                            Surface, regular_xy, grid_faces, refinement_cells,
                            adaptive_xy, section_lines)


class AdaptiveHeightfieldTests(unittest.TestCase):
    def test_spatial_partition_groups_flights_and_buffers_edges(self):
        xy = np.array([[.5, .5], [2.01, .5], [2.3, .5], [2.3, .5], [4.5, .5]])
        labels = spatial_split(xy, origin=np.zeros(2))
        np.testing.assert_array_equal(labels, [1, 2, 0, 0, 0])
        np.testing.assert_array_equal(labels, spatial_split(xy, origin=np.zeros(2)))
        # A diagonal buffer is Euclidean rather than an expanded square.
        self.assertEqual(spatial_split(np.array([[2.15, 2.15]]), np.zeros(2))[0], 0)

    def test_conflicting_coincident_heights_are_not_stacked_or_averaged(self):
        p = np.array([[0, 0, 1], [0, 0, 1.1], [1, 0, 0], [1, 0, 2], [0, 1, 1.]])
        unique, conflicts = unique_heights(p)
        self.assertEqual(conflicts, 1)
        self.assertEqual(len(unique), 2)
        self.assertAlmostEqual(unique[0, 2], 1.05)

    def test_linear_interpolant_preserves_tilt_and_exposes_extrapolation(self):
        xy = ORIGIN+np.array([[0., 0], [1, 0], [0, 1], [1, 1]])
        p = np.column_stack([xy, 2800+2*(xy[:, 0]-ORIGIN[0])])
        interp = Interpolant(p)
        z, support, _ = interp.sample(ORIGIN+np.array([[.2, .3], [1.2, .3]]))
        self.assertAlmostEqual(z[0], 2800.4)
        self.assertTrue(support[0]); self.assertFalse(support[1]); self.assertTrue(np.isnan(z[1]))

    def test_long_unsupported_bridge_is_masked(self):
        xy = ORIGIN+np.array([[0., 0], [.2, 0], [0, .2], [5, 0], [5, .2]])
        p = np.column_stack([xy, np.zeros(len(xy))])
        interp = Interpolant(p)
        z, support, _ = interp.sample(ORIGIN+np.array([[.05, .05], [2, .05]]))
        self.assertTrue(np.isfinite(z[0])); self.assertEqual(support[1], 0)

    def test_steep_plane_span_requires_orientation_support_not_arbitrary_length(self):
        xy = ORIGIN+np.array([[0., 0], [2.5, 0], [0, 2.5], [2.5, 2.5]])
        p = np.column_stack([xy, 2800+10*(xy[:, 0]-ORIGIN[0])])
        n = np.tile(np.array([-10., 0, 1])/np.sqrt(101), (4, 1))
        unsupported = Interpolant(p)
        supported = Interpolant(p, normals=n)
        query = ORIGIN+np.array([[1.25, 1.25]])
        self.assertFalse(unsupported.sample(query)[1][0])
        z, code, _ = supported.sample(query)
        self.assertAlmostEqual(z[0], 2812.5)
        self.assertEqual(code[0], 3)
        # Inconsistent surrounding planes must not legitimize a steep bridge.
        n[:] = [0, 0, 1]
        self.assertFalse(Interpolant(p, normals=n).sample(query)[1][0])

    def test_indexed_distance_equals_independent_bruteforce_and_signed_plane(self):
        xy = ORIGIN+np.array([[0., 0], [2, 0], [0, 2], [2, 2]])
        p = np.column_stack([xy, 2800+2*(xy[:, 0]-ORIGIN[0])])
        surface = Surface(p, np.array([[0, 1, 2], [1, 3, 2]]))
        q = np.array([[*ORIGIN+[1, 1], 2804.], [*ORIGIN+[-1, -1], 2800.]])
        result = surface.distances(q)
        self.assertAlmostEqual(result[0, 0], 2/np.sqrt(5))
        self.assertAlmostEqual(result[1, 0], np.sqrt(2))
        np.testing.assert_array_equal(surface.support(q[:, :2]), [True, False])

    def test_refinement_requires_multiple_points_and_xy_subcells(self):
        p = np.column_stack([ORIGIN+np.array([[.1, .1], [.12, .1], [.14, .1], [2.1, 2.1], [2.4, 2.1], [2.7, 2.1]]), np.zeros(6)])
        cells, buffered = refinement_cells(p, np.ones(6))
        self.assertEqual(cells, {(2, 2)})
        self.assertEqual(len(buffered), 9)
        xy = adaptive_xy(buffered)
        self.assertEqual(len(xy), len(np.unique(xy, axis=0)))
        self.assertGreater(len(xy), 14400)

    def test_regular_nodes_share_provider_cell_centres_and_triangle_diagonal(self):
        coarse, shape = regular_xy(.5); fine, fine_shape = regular_xy(.25)
        self.assertEqual(shape, (120, 120)); self.assertEqual(fine_shape, (239, 239))
        np.testing.assert_array_equal(coarse, fine.reshape(*fine_shape, 2)[::2, ::2].reshape(-1, 2))
        faces = grid_faces((2, 2))
        np.testing.assert_array_equal(faces, [[0, 2, 1], [1, 2, 3]])

    def test_exact_section_plane_has_true_metre_units(self):
        t = np.array([[[0., 0, 1], [1, 0, 3], [0, 1, 1]]])
        lines = section_lines(t, 0, .25)
        self.assertEqual(lines.shape, (1, 2, 3))
        np.testing.assert_allclose(lines[:, :, 0], .25)
        np.testing.assert_allclose(lines[:, :, 2], 1.5)


if __name__ == '__main__':
    unittest.main()
