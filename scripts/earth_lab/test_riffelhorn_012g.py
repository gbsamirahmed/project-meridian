"""Geometric source tracing and conservative radiometric controls."""
import unittest
import numpy as np
from riffelhorn_012g import decode, encode, normalise, blur, interpolate, density_from_gradients, rays, raycast


class ProjectionTests(unittest.TestCase):
    def test_density_tracks_surface_area_not_distributed_grid_claim(self):
        c, native, distributed, tangent = density_from_gradients(np.array([0, np.sqrt(3), np.sqrt(99)]), 0)
        np.testing.assert_allclose(c, [1, .5, .1]); np.testing.assert_allclose(native, [16, 8, 1.6])
        np.testing.assert_allclose(distributed/native, 6.25); np.testing.assert_allclose(tangent, [.25, .5, 2.5])

    def test_rgb_roundtrip_gain_black_hue_and_no_clipping(self):
        rgb = np.array([[[0, 0, 0], [50, 80, 100], [240, 120, 60]]], np.uint8)
        np.testing.assert_array_equal(encode(decode(rgb)), rgb)
        changed, actual = normalise(rgb, np.full((1, 3), 4.))
        np.testing.assert_array_equal(changed[0, 0], [0, 0, 0])
        self.assertLess(actual[0, 2], 4)
        np.testing.assert_allclose(decode(changed[0, 1])/decode(rgb[0, 1]), 4, atol=.06)

    def test_constant_low_frequency_and_pixel_centre_sampling(self):
        field = np.full((12, 12), .2)
        np.testing.assert_allclose(blur(field, 2), field)
        field = np.arange(16).reshape(4, 4)
        np.testing.assert_allclose(interpolate(field, [1, 3, 2, -1], [1, 3, 2, -1]), [0, 5, 2.5, 0])

    def test_ray_uses_diagonal_triangle_not_bilinear_height(self):
        grid = np.array([[0., 0.], [0., 1.]])
        # x+y<1 triangle is flat; bilinear would incorrectly report .0625.
        hit, grad = raycast(grid, np.array([.5, .5, 2]), np.array([[0., 0., -1.]]), spacing=1, centre=.25, vertical_origin=0)
        np.testing.assert_allclose(hit, [[.5, .5, 0]])
        np.testing.assert_allclose(grad, [[0, 0]])
        hit, grad = raycast(grid, np.array([1., 1., 2]), np.array([[0., 0., -1.]]), spacing=1, centre=.25, vertical_origin=0)
        np.testing.assert_allclose(hit, [[1, 1, .5]]); np.testing.assert_allclose(grad, [[1, 1]])

    def test_ray_oblique_first_hit_orientation_and_camera(self):
        grid = np.array([[0., 1., 2.], [0., 1., 2.], [0., 1., 2.]])
        direction = np.array([[1., 0., -1.]])/np.sqrt(2)
        hit, grad = raycast(grid, np.array([-.75, .5, 2.]), direction, spacing=1, centre=.25, vertical_origin=0)
        np.testing.assert_allclose(hit, [[.75, .5, .5]]); np.testing.assert_allclose(grad, [[1, 0]])
        v = {'position_m': [1, 1, 10], 'target_m': [1, 1, 0]}
        _, d = rays(v, [[959.5, 539.5], [0, 539.5]])
        np.testing.assert_allclose(d[0], [0, 0, -1]); self.assertLess(d[1, 1], 0)


if __name__ == '__main__': unittest.main()
