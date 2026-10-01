from __future__ import annotations

import json
from pathlib import Path
import unittest

import numpy as np
import rasterio
from pyproj import Transformer
from PIL import Image

from observed_natural_colour import BOUNDS, BANDS, build, display_rgb, sha256, world_uv
from meridian_paths import resolve_storage_roots


class ObservedColourTests(unittest.TestCase):
    def test_fixed_display_not_adaptive(self):
        values = np.array([-0.1, 0.02, 0.16, 0.30, 0.6], dtype=np.float32)
        np.testing.assert_array_equal(display_rgb(values), [0, 0, 128, 255, 255])

    def test_nodata_is_not_invented_colour(self):
        with self.assertRaises(ValueError):
            display_rgb(np.array([np.nan]))

    def test_unreal_geographic_orientation(self):
        self.assertEqual(world_uv(264900, 360800), (0, 0))
        self.assertEqual(world_uv(267900, 357800), (1, 1))
        self.assertEqual(world_uv(266400, 359300), (0.5, 0.5))

    def test_real_retained_observation_and_repeatability(self):
        repo = Path(__file__).resolve().parents[2]
        root = resolve_storage_roots(repository_root=repo, require_data=True).data
        out = root / "experiments/earth-lab/tryfan-010/observed-natural-colour-v1"
        first = build(repo)
        first_manifest = sha256(out / "lab010-manifest.json")
        second = build(repo)
        self.assertEqual(first["products"], second["products"])
        self.assertEqual(first_manifest, sha256(out / "lab010-manifest.json"))
        with rasterio.open(out / "lab010-rgb-reflectance-10m.tif") as dst:
            self.assertEqual(dst.crs.to_epsg(), 27700)
            self.assertEqual(tuple(dst.bounds), BOUNDS)
            self.assertEqual((dst.count, dst.height, dst.width), (3, 300, 300))
            self.assertEqual((dst.transform.a, dst.transform.e, dst.transform.b, dst.transform.d), (10, -10, 0, 0))
            rgb = dst.read()
            self.assertTrue(np.isfinite(rgb).all())
            # Independent inverse-coordinate sampling at four corners and the centre
            # detects a flip, mirrored image, swapped bands or rotated registration.
            to_native = Transformer.from_crs(27700, 32630, always_xy=True)
            for band_index, code in enumerate(BANDS):
                path = root / f"experiments/earth-lab/tryfan-005b/sentinel2-surface-evidence/source-native/{code}_10m-native-window.tif"
                with rasterio.open(path) as src:
                    source = src.read(1).astype(np.float64) * 0.0001 - 0.1
                    for row, col in [(5, 5), (5, 295), (295, 5), (295, 295), (150, 150)]:
                        e, n = dst.xy(row, col)
                        x, y = to_native.transform(e, n)
                        px, py = ~src.transform * (x, y)
                        px -= 0.5
                        py -= 0.5
                        ix, iy = int(np.floor(px)), int(np.floor(py))
                        fx, fy = px-ix, py-iy
                        expected = ((1-fx)*(1-fy)*source[iy, ix] + fx*(1-fy)*source[iy, ix+1]
                                    + (1-fx)*fy*source[iy+1, ix] + fx*fy*source[iy+1, ix+1])
                        self.assertAlmostEqual(float(rgb[band_index, row, col]), expected, delta=0.003)
        png = np.array(Image.open(out / "lab010-natural-colour-10m.png"))
        np.testing.assert_array_equal(png, np.moveaxis(display_rgb(rgb), 0, -1))
        for product in second["products"]:
            self.assertEqual(sha256(out / product["path"]), product["sha256"])
        self.assertEqual(second["processing"]["nodata_cells"], 0)
        self.assertEqual(len(second["season_audit"]), 4)


if __name__ == "__main__":
    unittest.main()
