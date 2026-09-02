from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
from pyproj import Transformer
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from route_geometry import (
    RouteCoordinate,
    RouteGeometry,
    geodesic_distance_m,
    resample_route,
)
from terrain_metrics import (
    ProcessingVariant,
    analyse_profile,
    median_smooth_physical,
    neighbourhood_metrics,
)
from terrain_sources import EAWcsBlockCache, RasterMetadata, WelshCogBlockCache


def synthetic_route(length_m: float = 100.0) -> RouteGeometry:
    start = RouteCoordinate(52.0, -3.0)
    end = RouteCoordinate(52.0 + length_m / 111_200.0, -3.0)
    return RouteGeometry("synthetic", (start, end), (0.0, length_m), length_m)


def fake_cache(root: Path, nodata: bool = False) -> WelshCogBlockCache:
    cache = WelshCogBlockCache.__new__(WelshCogBlockCache)
    cache.url = "https://example.invalid/dtm.tif"
    cache.metadata = RasterMetadata(
        cache.url,
        "GTiff",
        8,
        8,
        "EPSG:27700",
        (1.0, 0.0, 0.0, 0.0, -1.0, 8.0, 0.0, 0.0, 1.0),
        (0.0, 0.0, 8.0, 8.0),
        1.0,
        "float32",
        -9999.0,
        (4, 4),
        (),
        "DEFLATE",
        "COG",
    )
    cache.cache_root = root / "stable-cache"
    cache.max_cache_bytes = 1_000_000
    cache.max_blocks = 16
    cache.memory_blocks = 4
    cache.memory = __import__("collections").OrderedDict()
    cache.disk_cache_hits = 0
    cache.downloaded_blocks = 0
    cache.remote_uncompressed_bytes = 0
    cache.transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    for block_row in range(2):
        for block_col in range(2):
            rows, cols = np.indices((4, 4))
            values = (
                (block_row * 4 + rows) * 10.0 + block_col * 4 + cols
            ).astype(np.float32)
            if nodata and block_row == 0 and block_col == 0:
                values[1, 1] = np.nan
            path = cache._block_path((block_row, block_col))
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as handle:
                np.savez_compressed(handle, elevation=values)
    return cache


class GeometryTests(unittest.TestCase):
    def test_wgs84_to_british_national_grid(self) -> None:
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
        easting, northing = transformer.transform(-3.1791, 51.4816)
        self.assertAlmostEqual(easting, 318_000, delta=2_000)
        self.assertAlmostEqual(northing, 176_000, delta=2_000)

    def test_geodesic_resampling_uses_physical_spacing(self) -> None:
        route = synthetic_route(105.0)
        sampled = resample_route(route, 20.0)
        self.assertEqual(len(sampled.coordinates), 7)
        self.assertAlmostEqual(sampled.cumulative_distances_m[-1], 105.0)
        self.assertAlmostEqual(
            geodesic_distance_m(sampled.coordinates[0], sampled.coordinates[1]),
            20.0,
            delta=0.1,
        )


class RasterTests(unittest.TestCase):
    def test_cache_key_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = fake_cache(Path(temporary))
            second = fake_cache(Path(temporary))
            self.assertEqual(first._block_path((1, 2)), second._block_path((1, 2)))

    def test_bilinear_sampling_and_nodata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cache = fake_cache(Path(temporary))
            self.assertAlmostEqual(cache.sample_projected([(2.0, 6.0)])[0], 16.5)
            nodata = fake_cache(Path(temporary) / "nodata", nodata=True)
            self.assertIsNone(nodata.sample_projected([(1.5, 6.5)])[0])

    def test_outside_and_partial_coverage_remain_nodata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cache = fake_cache(Path(temporary))
            values = cache.sample_projected([(-1.0, 4.0), (4.0, 4.0)])
            self.assertIsNone(values[0])
            self.assertIsNotNone(values[1])

    def test_ea_wcs_request_is_bounded_and_numeric(self) -> None:
        cache = EAWcsBlockCache.__new__(EAWcsBlockCache)
        cache.url = "https://example.invalid/wcs"
        cache.coverage_id = "synthetic-dtm"
        url = cache._coverage_url(100.0, 200.0, 110.0, 210.0)
        self.assertIn("request=GetCoverage", url)
        self.assertIn("coverageId=synthetic-dtm", url)
        self.assertIn("subset=E%28100%2C110%29", url)
        self.assertIn("subset=N%28200%2C210%29", url)

        values = np.arange(100, dtype=np.float32).reshape(10, 10)
        with MemoryFile() as memory:
            with memory.open(
                driver="GTiff",
                width=10,
                height=10,
                count=1,
                dtype="float32",
                crs="EPSG:27700",
                transform=from_origin(100.0, 210.0, 1.0, 1.0),
                nodata=-3.4028234663852886e38,
            ) as destination:
                destination.write(values, 1)
            payload = memory.read()
        decoded = cache._decode_subset(
            payload,
            (1.0, 0.0, 100.0, 0.0, -1.0, 210.0),
            (10, 10),
        )
        np.testing.assert_array_equal(decoded, values)

    def test_ea_wcs_block_limit_prevents_unbounded_access(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cache = EAWcsBlockCache.__new__(EAWcsBlockCache)
            cache.cache_root = Path(temporary)
            cache.max_blocks = 1
            cache.max_cache_bytes = 10_000_000
            cache.metadata = RasterMetadata(
                "https://example.invalid/wcs",
                "WCS",
                2048,
                2048,
                "EPSG:27700",
                (1.0, 0.0, 0.0, 0.0, -1.0, 2048.0, 0.0, 0.0, 1.0),
                (0.0, 0.0, 2048.0, 2048.0),
                1.0,
                "float32",
                -3.4028234663852886e38,
                (1024, 1024),
                (),
                None,
                None,
            )
            cache.disk_cache_hits = 0
            with self.assertRaisesRegex(RuntimeError, "safety limit"):
                cache.prepare_blocks({(0, 0), (0, 1)})


class TerrainMetricTests(unittest.TestCase):
    def test_physical_filter_footprint_changes_with_spacing(self) -> None:
        dense = np.array([0.0, 0.0, 10.0, 0.0, 0.0])
        self.assertEqual(median_smooth_physical(dense, 10.0, 40.0)[2], 0.0)
        self.assertEqual(median_smooth_physical(dense, 40.0, 40.0)[2], 10.0)

    def test_ascent_and_hysteresis_are_reported_separately(self) -> None:
        route = resample_route(synthetic_route(100.0), 20.0)
        elevations = [0.0, 2.0, 4.0, 3.0, 5.0, 5.0]
        result = analyse_profile(
            "synthetic",
            route,
            elevations,
            ProcessingVariant("h3", 0.0, 3.0, 20.0),
        )
        self.assertAlmostEqual(result.raw_ascent_m, 6.0)
        self.assertAlmostEqual(result.processed_ascent_m, 4.0)
        self.assertAlmostEqual(result.hysteresis_removed_ascent_m, 2.0)

    def test_neighbourhood_metrics_recover_planar_slope(self) -> None:
        y, x = np.indices((41, 41))
        plane = x.astype(float) * 0.1
        metrics = neighbourhood_metrics(plane, 1.0, (5.0, 20.0))
        self.assertAlmostEqual(metrics["slope_10m_deg"], 5.7106, places=2)
        self.assertLess(metrics["roughness_20m"], 1e-9)
        self.assertAlmostEqual(metrics["convexity_20m"], 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
