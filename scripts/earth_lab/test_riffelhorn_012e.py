"""Independent checks of plane fitting, constrained continuation and support refusal."""
import unittest
import numpy as np
from riffelhorn_012e import (robust_plane, derive_planes, PlaneEstimator, hull_margin,
                            supported_faces, nearest_distance, mean_plane_normal, previous, ORIGIN)


def plane_sample(gradient=2., height=2850.):
    x, y = np.meshgrid(np.linspace(-.7, .7, 15), np.linspace(-.7, .7, 15))
    xy = ORIGIN + np.column_stack([x.ravel(), y.ravel()])
    points = np.column_stack([xy, height+gradient*x.ravel()])
    records = np.zeros(len(points), dtype=[('point_source_id', 'u2')])
    records['point_source_id'] = np.arange(len(points)) % 2
    return points, records


class RobustHeightfieldTests(unittest.TestCase):
    def test_plane_orientation_and_outlier_trim_preserve_measured_units(self):
        points, _ = plane_sample()
        # PCA conditioning is evaluated on a physical 3-D neighbourhood, not a
        # horizontally square sample that elongates along the tilted plane.
        points = points[np.linalg.norm(points-np.r_[ORIGIN, 2850.], axis=1) <= 1.]
        points = np.vstack([points, points[0]+[0, 0, .7]])
        fit = robust_plane(points, 2.)
        self.assertIsNotNone(fit)
        _, normal, rms, _, count, angle, _ = fit
        np.testing.assert_allclose(normal, np.array([-2., 0, 1])/np.sqrt(5), atol=1e-8)
        self.assertLess(rms, 1e-8); self.assertLess(angle, 1e-5)
        self.assertEqual(count, len(points)-1)

    def test_volumetric_scatter_does_not_become_reliable_surface(self):
        rng = np.random.default_rng(1205)
        self.assertIsNone(robust_plane(rng.uniform(-1, 1, (200, 3)), 2.))

    def test_oriented_scalar_height_is_exact_and_refuses_extrapolation(self):
        points, records = plane_sample()
        planes, _ = derive_planes(points, records, np.arange(len(points)))
        estimator = PlaneEstimator(planes, points, records)
        z, evidence = estimator.sample(ORIGIN+[[.1, .1], [.9, .1]])
        self.assertAlmostEqual(z[0], 2850.2, places=8)
        self.assertIn(evidence[0, 0], [1, 2])
        self.assertTrue(np.isnan(z[1])); self.assertEqual(evidence[1, 1], 7)
        again, repeated = estimator.sample(ORIGIN+[[.1, .1], [.9, .1]])
        np.testing.assert_allclose(again, z, equal_nan=True)
        np.testing.assert_allclose(repeated, evidence, equal_nan=True)

    def test_conflicting_coherent_planes_cannot_be_averaged_into_one_surface(self):
        points, records = plane_sample(gradient=0)
        lower, _ = derive_planes(points, records, np.arange(len(points)))
        upper = lower.copy(); upper[:, 2] += 1.; upper[:, 15] += 1.
        estimator = PlaneEstimator(np.vstack([lower, upper]), np.vstack([points, points+[0, 0, 1]]), np.tile(records, 2))
        z, evidence = estimator.query(ORIGIN+[0., 0])
        self.assertTrue(np.isnan(z)); self.assertEqual(evidence[1], 4)

    def test_vertical_plane_is_conditioning_failure_not_topology_verdict(self):
        points, records = plane_sample()
        planes, _ = derive_planes(points, records, np.arange(len(points)))
        planes[:, 3:6] = [1, 0, 0]
        z, evidence = PlaneEstimator(planes, points, records).query(ORIGIN)
        self.assertTrue(np.isnan(z)); self.assertEqual(evidence[1], 2)

    def test_unsigned_plane_normals_are_aligned_before_averaging(self):
        normal = np.array([1., 0, .01]); normal /= np.linalg.norm(normal)
        result = mean_plane_normal(np.array([normal, -normal]), np.ones(2), normal)
        np.testing.assert_allclose(result, normal, atol=1e-12)

    def test_edge_check_retains_tilt_but_rejects_false_bridge(self):
        vertices = np.array([[0., 0, 0], [.1, 0, .5], [0, .1, 0]])
        faces = np.array([[0, 1, 2]])
        evidence = np.zeros((3, 16)); evidence[:, 13:16] = np.array([-5., 0, 1])/np.sqrt(26)
        accepted, report = supported_faces(vertices, faces, evidence)
        self.assertEqual(len(accepted), 1)
        evidence[:, 13:16] = [0, 0, 1]
        accepted, report = supported_faces(vertices, faces, evidence)
        self.assertEqual(len(accepted), 0); self.assertEqual(report['plane_inconsistent_bridge_faces'], 1)

    def test_xy_bracketing_and_full_survey_distance_are_independent(self):
        xy = np.array([[0., 0], [1, 0], [0, 1]])
        self.assertGreater(hull_margin(xy, np.array([.2, .2])), 0)
        self.assertLess(hull_margin(xy, np.array([.9, .9])), 0)
        q = np.array([[.2, .2, 2.]])
        full = previous.Bins(np.array([[0., 0, 0], [.2, .2, 2.1]]), 1.)
        construction = previous.Bins(np.array([[0., 0, 0]]), 1.)
        self.assertAlmostEqual(nearest_distance(full, q)[0], .1)
        self.assertGreater(nearest_distance(construction, q)[0], 2.)


if __name__ == '__main__':
    unittest.main()
