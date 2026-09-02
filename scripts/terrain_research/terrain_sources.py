from __future__ import annotations

import hashlib
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import OrderedDict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.io import MemoryFile
from rasterio.windows import Window

from route_geometry import RouteGeometry


WELSH_DTM_URL = (
    "https://dmwproductionblob.blob.core.windows.net/cogs/lidar/"
    "wales_dtm_32bit_cog.tif"
)
WELSH_DTM_CRS = "EPSG:27700"
WGS84_CRS = "EPSG:4326"
EA_DTM_WCS_URL = (
    "https://environment.data.gov.uk/spatialdata/"
    "lidar-composite-digital-terrain-model-dtm-1m/wcs"
)
EA_DTM_COVERAGE_ID = (
    "13787b9a-26a4-4775-8523-806d13af58fc__"
    "Lidar_Composite_Elevation_DTM_1m"
)
EA_DTM_NODATA = -3.4028234663852886e38
EA_DTM_BLOCK_SIZE = 1024


@dataclass(slots=True, frozen=True)
class RasterMetadata:
    url: str
    driver: str
    width: int
    height: int
    crs: str
    transform: tuple[float, ...]
    bounds: tuple[float, float, float, float]
    pixel_size_m: float
    dtype: str
    nodata: float | None
    block_shape: tuple[int, int]
    overviews: tuple[int, ...]
    compression: str | None
    layout: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _gdal_environment() -> dict[str, str]:
    return {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
        "GDAL_HTTP_MULTIRANGE": "YES",
        "CPL_VSIL_CURL_USE_HEAD": "YES",
        "CPL_VSIL_CURL_CACHE_SIZE": str(32 * 1024 * 1024),
    }


def inspect_cog(url: str = WELSH_DTM_URL) -> RasterMetadata:
    with rasterio.Env(**_gdal_environment()):
        with rasterio.open(url) as source:
            if source.count != 1:
                raise ValueError("Expected a single-band terrain raster")
            image_structure = source.tags(ns="IMAGE_STRUCTURE")
            transform = tuple(float(value) for value in source.transform)
            return RasterMetadata(
                url=url,
                driver=source.driver,
                width=source.width,
                height=source.height,
                crs=str(source.crs),
                transform=transform,
                bounds=tuple(float(value) for value in source.bounds),
                pixel_size_m=abs(float(source.transform.a)),
                dtype=source.dtypes[0],
                nodata=None if source.nodata is None else float(source.nodata),
                block_shape=tuple(int(value) for value in source.block_shapes[0]),
                overviews=tuple(int(value) for value in source.overviews(1)),
                compression=image_structure.get("COMPRESSION"),
                layout=image_structure.get("LAYOUT"),
            )


class WelshCogBlockCache:
    def __init__(
        self,
        cache_root: Path,
        url: str = WELSH_DTM_URL,
        max_cache_bytes: int = 1_000_000_000,
        max_blocks: int = 5_000,
        memory_blocks: int = 64,
    ) -> None:
        self.url = url
        self.metadata = inspect_cog(url)
        if self.metadata.crs != WELSH_DTM_CRS:
            raise ValueError(f"Unexpected Welsh DTM CRS: {self.metadata.crs}")
        if self.metadata.pixel_size_m != 1.0:
            raise ValueError(
                f"Unexpected Welsh DTM pixel size: {self.metadata.pixel_size_m} m"
            )
        self.cache_root = cache_root / hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        self.max_cache_bytes = max_cache_bytes
        self.max_blocks = max_blocks
        self.memory_blocks = memory_blocks
        self.memory: OrderedDict[tuple[int, int], np.ndarray] = OrderedDict()
        self.disk_cache_hits = 0
        self.downloaded_blocks = 0
        self.remote_uncompressed_bytes = 0
        self.transformer = Transformer.from_crs(
            WGS84_CRS, WELSH_DTM_CRS, always_xy=True
        )

    @property
    def block_height(self) -> int:
        return self.metadata.block_shape[0]

    @property
    def block_width(self) -> int:
        return self.metadata.block_shape[1]

    def project_route(self, route: RouteGeometry) -> tuple[np.ndarray, np.ndarray]:
        longitudes = [coordinate.longitude for coordinate in route.coordinates]
        latitudes = [coordinate.latitude for coordinate in route.coordinates]
        x, y = self.transformer.transform(longitudes, latitudes)
        return np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)

    def coverage_fraction(self, route: RouteGeometry) -> float:
        x, y = self.project_route(route)
        left, bottom, right, top = self.metadata.bounds
        covered = (x >= left) & (x < right) & (y >= bottom) & (y < top)
        return float(np.mean(covered)) if len(covered) else 0.0

    def _fractional_pixel(self, x: float, y: float) -> tuple[float, float]:
        transform = self.metadata.transform
        col = (x - transform[2]) / transform[0] - 0.5
        row = (y - transform[5]) / transform[4] - 0.5
        return row, col

    def _block_key_for_pixel(self, row: int, col: int) -> tuple[int, int]:
        return row // self.block_height, col // self.block_width

    def _block_path(self, key: tuple[int, int]) -> Path:
        return self.cache_root / f"r{key[0]:04d}" / f"c{key[1]:04d}.npz"

    def _valid_block(self, key: tuple[int, int]) -> bool:
        rows = math.ceil(self.metadata.height / self.block_height)
        columns = math.ceil(self.metadata.width / self.block_width)
        return 0 <= key[0] < rows and 0 <= key[1] < columns

    def required_blocks(
        self, projected_points: Iterable[tuple[float, float]], radius_m: float = 0.0
    ) -> set[tuple[int, int]]:
        radius_pixels = math.ceil(radius_m / self.metadata.pixel_size_m) + 1
        result: set[tuple[int, int]] = set()
        for x, y in projected_points:
            row_float, col_float = self._fractional_pixel(float(x), float(y))
            row = round(row_float)
            col = round(col_float)
            for edge_row in (row - radius_pixels, row + radius_pixels):
                for edge_col in (col - radius_pixels, col + radius_pixels):
                    key = self._block_key_for_pixel(edge_row, edge_col)
                    if self._valid_block(key):
                        result.add(key)
            row_start = (row - radius_pixels) // self.block_height
            row_end = (row + radius_pixels) // self.block_height
            col_start = (col - radius_pixels) // self.block_width
            col_end = (col + radius_pixels) // self.block_width
            for block_row in range(row_start, row_end + 1):
                for block_col in range(col_start, col_end + 1):
                    key = (block_row, block_col)
                    if self._valid_block(key):
                        result.add(key)
        return result

    def cache_size_bytes(self) -> int:
        if not self.cache_root.exists():
            return 0
        return sum(path.stat().st_size for path in self.cache_root.rglob("*.npz"))

    def prepare_blocks(self, keys: Iterable[tuple[int, int]]) -> None:
        ordered = sorted(set(keys))
        if len(ordered) > self.max_blocks:
            raise RuntimeError(
                f"Terrain request needs {len(ordered)} blocks, above the {self.max_blocks} limit"
            )
        missing = [key for key in ordered if not self._block_path(key).is_file()]
        self.disk_cache_hits += len(ordered) - len(missing)
        projected_max = self.cache_size_bytes() + (
            len(missing) * self.block_height * self.block_width * 4
        )
        if projected_max > self.max_cache_bytes:
            raise RuntimeError("Bounded Welsh terrain cache limit would be exceeded")
        if not missing:
            return
        with rasterio.Env(**_gdal_environment()):
            with rasterio.open(self.url) as source:
                for index, key in enumerate(missing, start=1):
                    row_offset = key[0] * self.block_height
                    col_offset = key[1] * self.block_width
                    height = min(self.block_height, self.metadata.height - row_offset)
                    width = min(self.block_width, self.metadata.width - col_offset)
                    values = source.read(
                        1,
                        window=Window(col_offset, row_offset, width, height),
                        masked=True,
                    ).filled(np.nan).astype(np.float32, copy=False)
                    path = self._block_path(key)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    temporary = path.with_suffix(".npz.tmp")
                    with temporary.open("wb") as handle:
                        np.savez_compressed(handle, elevation=values)
                    if self.cache_size_bytes() + temporary.stat().st_size > self.max_cache_bytes:
                        temporary.unlink(missing_ok=True)
                        raise RuntimeError("Bounded Welsh terrain cache limit was reached")
                    temporary.replace(path)
                    self.downloaded_blocks += 1
                    self.remote_uncompressed_bytes += values.nbytes
                    if index % 25 == 0 or index == len(missing):
                        print(f"Cached Welsh DTM block {index}/{len(missing)}")

    def _load_block(self, key: tuple[int, int]) -> np.ndarray:
        cached = self.memory.get(key)
        if cached is not None:
            self.memory.move_to_end(key)
            return cached
        path = self._block_path(key)
        if not path.is_file():
            raise FileNotFoundError(f"Welsh terrain block is not prepared: {key}")
        with np.load(path) as archive:
            values = archive["elevation"].astype(np.float64)
        self.memory[key] = values
        while len(self.memory) > self.memory_blocks:
            self.memory.popitem(last=False)
        return values

    def _pixel(self, row: int, col: int) -> float | None:
        if not (0 <= row < self.metadata.height and 0 <= col < self.metadata.width):
            return None
        key = self._block_key_for_pixel(row, col)
        values = self._load_block(key)
        value = values[row - key[0] * self.block_height, col - key[1] * self.block_width]
        return None if not np.isfinite(value) else float(value)

    def sample_projected(
        self, projected_points: Iterable[tuple[float, float]]
    ) -> list[float | None]:
        result: list[float | None] = []
        for x, y in projected_points:
            row_float, col_float = self._fractional_pixel(float(x), float(y))
            row_0 = math.floor(row_float)
            col_0 = math.floor(col_float)
            fraction_row = row_float - row_0
            fraction_col = col_float - col_0
            corners = (
                self._pixel(row_0, col_0),
                self._pixel(row_0, col_0 + 1),
                self._pixel(row_0 + 1, col_0),
                self._pixel(row_0 + 1, col_0 + 1),
            )
            if any(value is None for value in corners):
                result.append(None)
                continue
            top = corners[0] * (1.0 - fraction_col) + corners[1] * fraction_col
            bottom = corners[2] * (1.0 - fraction_col) + corners[3] * fraction_col
            result.append(top * (1.0 - fraction_row) + bottom * fraction_row)
        return result

    def read_neighbourhood(
        self, x: float, y: float, radius_m: float
    ) -> np.ndarray:
        row_float, col_float = self._fractional_pixel(x, y)
        centre_row = round(row_float)
        centre_col = round(col_float)
        radius = math.ceil(radius_m / self.metadata.pixel_size_m)
        row_start = centre_row - radius
        row_end = centre_row + radius
        col_start = centre_col - radius
        col_end = centre_col + radius
        grid = np.full((radius * 2 + 1, radius * 2 + 1), np.nan, dtype=np.float64)
        for block_row in range(row_start // self.block_height, row_end // self.block_height + 1):
            for block_col in range(col_start // self.block_width, col_end // self.block_width + 1):
                key = (block_row, block_col)
                if not self._valid_block(key):
                    continue
                values = self._load_block(key)
                source_row_0 = max(0, row_start - block_row * self.block_height)
                source_col_0 = max(0, col_start - block_col * self.block_width)
                source_row_1 = min(values.shape[0], row_end - block_row * self.block_height + 1)
                source_col_1 = min(values.shape[1], col_end - block_col * self.block_width + 1)
                if source_row_1 <= source_row_0 or source_col_1 <= source_col_0:
                    continue
                destination_row = block_row * self.block_height + source_row_0 - row_start
                destination_col = block_col * self.block_width + source_col_0 - col_start
                grid[
                    destination_row : destination_row + source_row_1 - source_row_0,
                    destination_col : destination_col + source_col_1 - source_col_0,
                ] = values[source_row_0:source_row_1, source_col_0:source_col_1]
        return grid


class EAWcsBlockCache(WelshCogBlockCache):
    """Bounded route-local cache for the official EA 1 m DTM WCS."""

    def __init__(
        self,
        cache_root: Path,
        url: str = EA_DTM_WCS_URL,
        coverage_id: str = EA_DTM_COVERAGE_ID,
        max_cache_bytes: int = 750_000_000,
        max_blocks: int = 320,
        memory_blocks: int = 12,
        minimum_request_interval_s: float = 0.4,
    ) -> None:
        self.url = url
        self.coverage_id = coverage_id
        self.metadata = RasterMetadata(
            url=url,
            driver="WCS 2.0.1 / GeoTIFF",
            width=576_000,
            height=661_000,
            crs=WELSH_DTM_CRS,
            transform=(1.0, 0.0, 80_000.0, 0.0, -1.0, 665_000.0, 0.0, 0.0, 1.0),
            bounds=(80_000.0, 4_000.0, 656_000.0, 665_000.0),
            pixel_size_m=1.0,
            dtype="float32",
            nodata=EA_DTM_NODATA,
            block_shape=(EA_DTM_BLOCK_SIZE, EA_DTM_BLOCK_SIZE),
            overviews=(),
            compression="server GeoTIFF; private NPZ block cache",
            layout="route-local WCS subsets",
        )
        identity = f"{url}|{coverage_id}|{EA_DTM_BLOCK_SIZE}"
        self.cache_root = cache_root / hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        self.max_cache_bytes = max_cache_bytes
        self.max_blocks = max_blocks
        self.memory_blocks = memory_blocks
        self.memory = OrderedDict()
        self.disk_cache_hits = 0
        self.downloaded_blocks = 0
        self.remote_uncompressed_bytes = 0
        self.downloaded_bytes = 0
        self.request_count = 0
        self.failed_requests = 0
        self.minimum_request_interval_s = minimum_request_interval_s
        self._last_request_started = 0.0
        self.transformer = Transformer.from_crs(
            WGS84_CRS, WELSH_DTM_CRS, always_xy=True
        )

    def _coverage_url(
        self, west: float, south: float, east: float, north: float
    ) -> str:
        parameters = [
            ("service", "WCS"),
            ("version", "2.0.1"),
            ("request", "GetCoverage"),
            ("coverageId", self.coverage_id),
            ("format", "image/tiff"),
            ("subset", f"E({west:.0f},{east:.0f})"),
            ("subset", f"N({south:.0f},{north:.0f})"),
        ]
        return self.url + "?" + urllib.parse.urlencode(parameters)

    def _request_geotiff(
        self, west: float, south: float, east: float, north: float
    ) -> bytes:
        last_error: Exception | None = None
        for attempt in range(3):
            wait = self.minimum_request_interval_s - (
                time.monotonic() - self._last_request_started
            )
            if wait > 0:
                time.sleep(wait)
            self._last_request_started = time.monotonic()
            request = urllib.request.Request(
                self._coverage_url(west, south, east, north),
                headers={"User-Agent": "Meridian terrain research/2"},
            )
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    payload = response.read(12 * 1024 * 1024)
                    if response.read(1):
                        raise RuntimeError("EA WCS response exceeded the 12 MiB block limit")
                    if response.status != 200 or response.headers.get_content_type() != "image/tiff":
                        raise RuntimeError(
                            f"Unexpected EA WCS response: HTTP {response.status} "
                            f"{response.headers.get_content_type()}"
                        )
                self.request_count += 1
                self.downloaded_bytes += len(payload)
                return payload
            except (OSError, RuntimeError, urllib.error.URLError) as error:
                last_error = error
                self.failed_requests += 1
                if attempt < 2:
                    time.sleep(1.0 * (attempt + 1))
        raise RuntimeError("EA WCS block request failed after bounded retries") from last_error

    def _decode_subset(
        self,
        payload: bytes,
        expected_transform: tuple[float, float, float, float, float, float],
        expected_shape: tuple[int, int],
    ) -> np.ndarray:
        with MemoryFile(payload) as memory:
            with memory.open() as source:
                if str(source.crs) != WELSH_DTM_CRS or source.dtypes[0] != "float32":
                    raise ValueError("Unexpected EA WCS raster CRS or data type")
                if (source.height, source.width) != expected_shape:
                    raise ValueError(
                        f"Unexpected EA WCS raster shape {(source.height, source.width)}"
                    )
                actual = tuple(float(value) for value in source.transform)[:6]
                if not np.allclose(actual, expected_transform, atol=1e-6):
                    raise ValueError("EA WCS subset transform does not match its request")
                values = source.read(1).astype(np.float32, copy=False)
                nodata = source.nodata
        invalid = ~np.isfinite(values)
        if nodata is not None:
            invalid |= np.isclose(values, float(nodata), rtol=0.0, atol=1e30)
        values[invalid] = np.nan
        return values

    def probe_projected(self, x: float, y: float, size_m: int = 10) -> dict[str, object]:
        half = size_m // 2
        west = math.floor(x) - half
        south = math.floor(y) - half
        east = west + size_m
        north = south + size_m
        payload = self._request_geotiff(west, south, east, north)
        values = self._decode_subset(
            payload,
            (1.0, 0.0, float(west), 0.0, -1.0, float(north)),
            (size_m, size_m),
        )
        finite = values[np.isfinite(values)]
        return {
            "bytes": len(payload),
            "valid_fraction": float(len(finite) / values.size),
            "nonzero_fraction": float(np.count_nonzero(np.abs(finite) > 1e-6) / values.size),
            "minimum_m": None if not len(finite) else float(np.min(finite)),
            "maximum_m": None if not len(finite) else float(np.max(finite)),
        }

    def prepare_blocks(self, keys: Iterable[tuple[int, int]]) -> None:
        ordered = sorted(set(keys))
        if len(ordered) > self.max_blocks:
            raise RuntimeError(
                f"Terrain request needs {len(ordered)} EA blocks, above the "
                f"{self.max_blocks}-block safety limit"
            )
        missing = [key for key in ordered if not self._block_path(key).is_file()]
        self.disk_cache_hits += len(ordered) - len(missing)
        projected_uncompressed = (
            len(missing) * self.block_height * self.block_width * 4
        )
        if projected_uncompressed > self.max_cache_bytes:
            raise RuntimeError("Bounded EA terrain request exceeds the byte safety limit")
        for index, key in enumerate(missing, start=1):
            row_offset = key[0] * self.block_height
            col_offset = key[1] * self.block_width
            height = min(self.block_height, self.metadata.height - row_offset)
            width = min(self.block_width, self.metadata.width - col_offset)
            west = self.metadata.transform[2] + col_offset
            north = self.metadata.transform[5] - row_offset
            east = west + width
            south = north - height
            payload = self._request_geotiff(west, south, east, north)
            values = self._decode_subset(
                payload,
                (1.0, 0.0, float(west), 0.0, -1.0, float(north)),
                (height, width),
            )
            path = self._block_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".npz.tmp")
            with temporary.open("wb") as handle:
                np.savez_compressed(handle, elevation=values)
            if self.cache_size_bytes() + temporary.stat().st_size > self.max_cache_bytes:
                temporary.unlink(missing_ok=True)
                raise RuntimeError("Bounded EA terrain cache limit was reached")
            temporary.replace(path)
            self.downloaded_blocks += 1
            self.remote_uncompressed_bytes += values.nbytes
            if index % 10 == 0 or index == len(missing):
                print(f"Cached EA DTM block {index}/{len(missing)}")

    def stats(self) -> dict[str, int]:
        return {
            "required_limit": self.max_blocks,
            "downloaded_blocks": self.downloaded_blocks,
            "disk_cache_hits": self.disk_cache_hits,
            "request_count": self.request_count,
            "failed_requests": self.failed_requests,
            "downloaded_bytes": self.downloaded_bytes,
            "cache_bytes": self.cache_size_bytes(),
            "uncompressed_block_bytes": self.remote_uncompressed_bytes,
        }


def _activity_research_imports() -> tuple[type, type]:
    activity_root = Path(__file__).resolve().parents[1] / "activity_research"
    if str(activity_root) not in sys.path:
        sys.path.insert(0, str(activity_root))
    from terrain_experiment import MovementPoint, TerrariumTileCache

    return MovementPoint, TerrariumTileCache


class TerrariumRouteSource:
    def __init__(self, cache_root: Path) -> None:
        movement_point, tile_cache = _activity_research_imports()
        self._movement_point = movement_point
        self.cache = tile_cache(cache_root)

    def _points(self, route: RouteGeometry) -> list[object]:
        return [
            self._movement_point(
                0,
                coordinate.latitude,
                coordinate.longitude,
                0.0,
                0.0,
                route.cumulative_distances_m[index],
                route.cumulative_distances_m[index],
            )
            for index, coordinate in enumerate(route.coordinates)
        ]

    def prepare(self, routes: Sequence[RouteGeometry]) -> int:
        points = [point for route in routes for point in self._points(route)]
        return self.cache.prepare(points)

    def sample(self, route: RouteGeometry) -> list[float]:
        return self.cache.sample(self._points(route))

    def stats(self) -> dict[str, int]:
        return {
            "downloaded_tiles": self.cache.downloaded_tiles,
            "downloaded_bytes": self.cache.downloaded_bytes,
            "cache_hits": self.cache.cache_hits,
            "failed_tiles": len(self.cache.failed_tiles),
        }


def configure_gdal_environment() -> None:
    for key, value in _gdal_environment().items():
        os.environ.setdefault(key, value)
