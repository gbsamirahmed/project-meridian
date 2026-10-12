"""Synthetic mathematical and rejection controls; no genuine-data claims."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

spec = importlib.util.spec_from_file_location("pilot", Path(__file__).with_name("pilot.py"))
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class Controls(unittest.TestCase):
    def test_affine_edge_height(self):
        x = y = np.arange(6, dtype=float)
        z = y[:, None]*2+x[None, :]*3
        for coords in pilot.generator(x, y, z).lines(7):
            self.assertLess(pilot.edge_residual(coords, x, y, z, 7), .001)

    def test_constant_and_level_tie(self):
        x = y = np.arange(4, dtype=float)
        self.assertEqual(pilot.generator(x, y, np.ones((4, 4))).lines(1), [])
        coords = pilot.generator(x, y, np.tile(x, (4, 1))).lines(1)
        self.assertEqual(len(coords), 1)
        np.testing.assert_array_equal(coords[0][:, 0], 1.)

    def test_saddle_pinned(self):
        x = y = np.arange(2, dtype=float)
        z = np.array([[0., 2.], [2., 0.]])
        lines = pilot.generator(x, y, z).lines(1)
        self.assertEqual([line.tolist() for line in lines],
                         [[[0., .5], [.5, 1.]], [[1., .5], [.5, 0.]]])

    def test_nodata_excludes_whole_quad(self):
        x = y = np.arange(2, dtype=float)
        z = np.array([[0., 2.], [np.nan, 2.]])
        self.assertEqual(pilot.generator(x, y, z).lines(1), [])
        z[1, 0] = np.inf
        self.assertEqual(pilot.generator(x, y, z).lines(1), [])

    def test_monotonic_grid_rejection(self):
        with self.assertRaisesRegex(ValueError, "Non-monotonic"):
            pilot.generator(np.array([1., 0.]), np.arange(2.), np.ones((2, 2)))

    def test_strict_aggregation_and_smoothing(self):
        z = np.arange(64., dtype=float).reshape(8, 8)
        self.assertEqual(pilot.block_mean(z)[0, 0], z[:4, :4].mean())
        z[0, 0] = np.nan
        self.assertTrue(np.isnan(pilot.block_mean(z)[0, 0]))
        field = pilot.smooth(np.ones((10, 10)))
        self.assertTrue(np.isnan(field[:3]).all())
        np.testing.assert_allclose(field[3:-3, 3:-3], 1.)

    def test_semantic_identity_units_and_fusion(self):
        meta = {key: "declared" for key in ("id", "source", "revision", "surface",
            "verticalReference", "units", "horizontalReference", "processing", "rights", "limitations")}
        meta.update(units="m", verticalReference="LN02", horizontalReference="EPSG:2056")
        pilot.require_product(meta)
        for key, value in (("id", ""), ("units", "feet"), ("verticalReference", "unknown"),
                           ("horizontalReference", "unknown")):
            with self.assertRaises(ValueError):
                pilot.require_product(dict(meta, **{key: value}))
        with self.assertRaisesRegex(ValueError, "fusion"):
            pilot.require_merge(meta, dict(meta, verticalReference="EGM2008"))

    def test_missing_and_changed_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pins = {"inputs": [{"id": "synthetic", "path": "input", "bytes": 3, "sha256": "wrong"}]}
            with self.assertRaises(ValueError):
                pilot.verify_inputs(root, pins)
            (root/"input").write_bytes(b"abc")
            with self.assertRaises(ValueError):
                pilot.verify_inputs(root, pins)

    def test_native_allocation_gate(self):
        self.assertFalse(pilot.allocation_allowed(16_000_000, 60*1024**2))
        self.assertTrue(pilot.allocation_allowed(1_000_000, 60*1024**2))

    def test_duplicate_input_identity(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            pilot.verify_inputs(Path("unused"), {"inputs": [{"id": "same"}, {"id": "same"}]})

    def test_partition_completeness(self):
        from shapely.geometry import LineString, box
        from shapely.ops import unary_union
        master = LineString([(0, .1), (2, 1.7)])
        parts = [master.intersection(box(a, b, a+1, b+1)) for a in (0, 1) for b in (0, 1)]
        self.assertLess(master.hausdorff_distance(unary_union(parts)), 1e-6)
        self.assertGreater(master.hausdorff_distance(unary_union(parts[:2])), 1e-6)


if __name__ == "__main__":
    unittest.main()
