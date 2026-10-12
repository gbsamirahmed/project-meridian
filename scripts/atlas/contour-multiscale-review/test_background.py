"""Synthetic visual-gradient and affine-registration checks, no genuine DEM reads."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import rasterio
from rasterio.transform import from_origin
from background import shade, mosaic_window


class BackgroundTests(unittest.TestCase):
    def test_flat_light(self):
        result = shade(np.full((5, 5), 2500, dtype=np.float32))
        self.assertTrue(np.all(result[:, :, 0] == round(96+159/np.sqrt(2))))
        self.assertTrue(np.all(result[:, :, 1] == 255))

    def test_light_direction_and_height_offset(self):
        row, col = np.mgrid[:7, :7]
        east = col.astype(np.float32)*0.5
        west = -east
        north = -row.astype(np.float32)*0.5
        south = -north
        self.assertGreater(shade(east)[0, 0, 0], shade(west)[0, 0, 0])
        self.assertGreater(shade(south)[0, 0, 0], shade(north)[0, 0, 0])
        np.testing.assert_array_equal(shade(east), shade(east+2500))

    def test_nodata_requires_all_neighbours(self):
        field = np.ones((7, 7), dtype=np.float32)
        field[3, 3] = np.nan
        alpha = shade(field)[:, :, 1]
        self.assertEqual(int((alpha == 0).sum()), 9)
        self.assertEqual(int((alpha == 255).sum()), 16)

    def test_strip_and_tile_joins_match_monolithic_synthetic(self):
        row, col = np.mgrid[:8, :8]
        field = (2500 + 0.7*col - 1.3*row).astype(np.float32)
        field[2, 5] = np.nan
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for y in (0, 4):
                for x in (0, 4):
                    path = Path(directory)/f'{x}-{y}.tif'
                    with rasterio.open(path, 'w', driver='GTiff', width=4, height=4,
                                       count=1, dtype='float32', crs='EPSG:2056', nodata=-9999,
                                       transform=from_origin(x*0.5, 4-y*0.5, 0.5, 0.5)) as dataset:
                        dataset.write(np.nan_to_num(field[y:y+4, x:x+4], nan=-9999), 1)
                    paths.append(path)
            datasets = [rasterio.open(path) for path in paths]
            try:
                with patch('background.SIZE', 8), patch('background.BOUNDS', (0, 0, 4, 4)):
                    whole = mosaic_window(datasets, -1, 9)
                    np.testing.assert_array_equal(whole, np.pad(field, 1, constant_values=np.nan))
                    strips = np.concatenate([shade(mosaic_window(datasets, start-1, min(8, start+3)+1))
                                             for start in range(0, 8, 3)])
                    np.testing.assert_array_equal(strips, shade(whole))
                    self.assertTrue(np.all(strips[0, :, 1] == 0))
            finally:
                for dataset in datasets:
                    dataset.close()

    def test_pixel_centre_registration(self):
        transform = from_origin(2624000, 1093000, 0.5, 0.5)
        self.assertEqual(transform*(0.5, 0.5), (2624000.25, 1092999.75))
        self.assertEqual(transform*(4000, 4000), (2626000, 1091000))


if __name__ == '__main__':
    unittest.main()
