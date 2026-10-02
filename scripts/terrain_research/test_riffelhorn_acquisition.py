"""Synthetic-file checks; never require Swiss payloads or network access."""
import copy
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np
import rasterio
from rasterio.transform import from_origin

import riffelhorn_acquisition as acquisition


class AcquisitionTests(unittest.TestCase):
    def las_fixture(self, path):
        header = bytearray(227)
        header[:4] = b'LASF'
        header[24:26] = bytes([1, 2])
        struct.pack_into('<H', header, 6, 1)
        struct.pack_into('<HII', header, 94, 227, 227, 0)
        struct.pack_into('<BHI', header, 104, 1, 28, 2)
        struct.pack_into('<3d', header, 131, .01, .01, .01)
        struct.pack_into('<3d', header, 155, 2624000, 1091000, 0)
        points = bytearray(56)
        for i, (x, y, z, return_bits, class_bits, gps) in enumerate([
            (100, 200, 230000, 9, 34, 313821569.99),
            (20000, 30000, 231000, 18, 3, 345287981.97),
        ]):
            struct.pack_into('<iii', points, i * 28, x, y, z)
            points[i * 28 + 14] = return_bits
            points[i * 28 + 15] = class_bits
            struct.pack_into('<d', points, i * 28 + 20, gps)
        path.write_bytes(header + points)

    def test_las_coordinates_flags_returns_and_mixed_acquisition(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'vendor-name.las'
            self.las_fixture(path)
            result = acquisition.las_metadata(path, '2624-1091')
        self.assertEqual(result['xyz_min'], [2624001, 1091002, 2300])
        self.assertEqual(result['xyz_max'], [2624200, 1091300, 2310])
        self.assertEqual(result['classification_counts'], {'2': 1, '3': 1})
        self.assertEqual(result['return_number_counts'], {'1': 1, '2': 1})
        self.assertEqual(result['acquisition_gps_date_counts'], {'2021-08-24': 1, '2022-08-23': 1})
        self.assertEqual(result['first_return_density_per_m2'], 1e-6)
        self.assertAlmostEqual(sum(map(sum, result['density_100m_cells_all_returns'])), .0002)

    def test_truncated_las_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.las'
            self.las_fixture(path)
            path.write_bytes(path.read_bytes()[:-28])
            with self.assertRaisesRegex(ValueError, 'Truncated'):
                acquisition.las_metadata(path, '2624-1091')

    def test_wrong_tile_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.las'
            self.las_fixture(path)
            with self.assertRaisesRegex(ValueError, 'out-of-tile'):
                acquisition.las_metadata(path, '2625-1091')

    def test_retained_original_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'original.tif'
            path.write_bytes(b'unchanged vendor payload')
            with self.assertRaisesRegex(ValueError, 'hash changed'):
                acquisition.download(root, {'path': path.name, 'expected_sha256': '0' * 64})
            self.assertEqual(path.read_bytes(), b'unchanged vendor payload')

    def inventory_fixture(self):
        records = []
        for product in acquisition.PRODUCTS:
            for tile in acquisition.TILES:
                e, n = [int(v) * 1000 for v in tile.split('-')]
                spacing = .1 if product == 'swissimage-dop10' else .5
                records.append({'product': product, 'tile': tile, 'actual_file': {
                    'point_count': 1, 'epsg': 2056, 'bounds': [e, n, e+1000, n+1000],
                    'transform': [spacing, 0, e, 0, -spacing, n+1000],
                    'dimensions': [int(1000/spacing)] * 2, 'missing_cells_band1': 0}})
        return records

    def test_coverage_requires_exact_complete_inventory(self):
        records = self.inventory_fixture()
        self.assertEqual(acquisition.validate_inventory(records)['raster_coverage_percent'], 100)
        with self.assertRaises(ValueError):
            acquisition.validate_inventory(records[:-1])
        changed = copy.deepcopy(records)
        changed[0]['actual_file']['transform'][4] = .1
        with self.assertRaisesRegex(ValueError, 'orientation'):
            acquisition.validate_inventory(changed)
        changed = copy.deepcopy(records)
        changed[4]['actual_file']['missing_cells_band1'] = 1
        with self.assertRaisesRegex(ValueError, 'missing coverage'):
            acquisition.validate_inventory(changed)

    def test_black_rgb_distinguished_from_validity_mask(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rgb.tif'
            data = np.full((3, 2, 2), 10, dtype=np.uint8)
            data[:, 0, 0] = 0
            with rasterio.open(path, 'w', driver='GTiff', width=2, height=2, count=3,
                               dtype='uint8', crs='EPSG:2056', transform=from_origin(2624000, 1091001, .5, .5)) as dst:
                dst.write(data)
            result = acquisition.raster_metadata(path)
        self.assertEqual(result['all_zero_rgb_cells'], 1)
        self.assertEqual(result['missing_cells_band1'], 0)


if __name__ == '__main__':
    unittest.main()
