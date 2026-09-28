"""Provider-neutral numeric helpers for Meridian surface evidence."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject


@dataclass(frozen=True)
class AnalysisGrid:
    crs: str
    west: float
    south: float
    east: float
    north: float
    resolution_m: float

    @property
    def width(self) -> int:
        return int(round((self.east - self.west) / self.resolution_m))

    @property
    def height(self) -> int:
        return int(round((self.north - self.south) / self.resolution_m))

    @property
    def transform(self):
        return from_origin(self.west, self.north, self.resolution_m, self.resolution_m)

    def as_dict(self) -> dict[str, Any]:
        return {
            "crs": self.crs,
            "bounds": [self.west, self.south, self.east, self.north],
            "resolution_m": self.resolution_m,
            "width": self.width,
            "height": self.height,
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def surface_reflectance(
    digital_number: np.ndarray,
    *,
    scale: float,
    offset: float,
    nodata: int | float | None,
) -> np.ndarray:
    raw = np.asarray(digital_number)
    result = raw.astype(np.float32) * float(scale) + float(offset)
    if nodata is not None:
        result[raw == nodata] = np.nan
    return result


def normalized_difference(
    a: np.ndarray,
    b: np.ndarray,
    *,
    minimum_sum: float = 1e-8,
    require_nonnegative: bool = False,
) -> np.ndarray:
    """Return (a-b)/(a+b), preserving missing and zero-denominator cells."""
    left = np.asarray(a, dtype=np.float32)
    right = np.asarray(b, dtype=np.float32)
    denominator = left + right
    valid = np.isfinite(left) & np.isfinite(right) & (denominator > float(minimum_sum))
    if require_nonnegative:
        valid &= (left >= 0.0) & (right >= 0.0)
    result = np.full(left.shape, np.nan, dtype=np.float32)
    np.divide(left - right, denominator, out=result, where=valid)
    return result


SCL_LABELS = {
    0: "no_data",
    1: "saturated_or_defective",
    2: "topographic_cast_shadow",
    3: "cloud_shadow",
    4: "vegetation",
    5: "not_vegetated",
    6: "water",
    7: "unclassified",
    8: "cloud_medium_probability",
    9: "cloud_high_probability",
    10: "thin_cirrus",
    11: "snow_or_ice",
}
INVALID_SCL_CLASSES = frozenset((0, 1, 3, 8, 9, 10, 11))


def scl_valid_mask(scl: np.ndarray) -> np.ndarray:
    values = np.asarray(scl)
    return ~np.isin(values, tuple(INVALID_SCL_CLASSES))


def scl_summary(scl: np.ndarray) -> dict[str, Any]:
    values = np.asarray(scl)
    total = int(values.size)
    counts = {int(value): int(count) for value, count in zip(*np.unique(values, return_counts=True))}
    valid = scl_valid_mask(values)
    return {
        "total_cells": total,
        "valid_cells": int(np.count_nonzero(valid)),
        "usable_fraction": float(np.mean(valid)),
        "class_counts": {
            SCL_LABELS.get(code, f"unknown_{code}"): count
            for code, count in sorted(counts.items())
        },
        "cloud_fraction": float(np.mean(np.isin(values, (8, 9, 10)))),
        "cloud_shadow_fraction": float(np.mean(values == 3)),
        "snow_or_ice_fraction": float(np.mean(values == 11)),
        "nodata_fraction": float(np.mean(values == 0)),
    }


def apply_valid_mask(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=np.float32).copy()
    result[~np.asarray(valid, dtype=bool)] = np.nan
    return result


def reproject_numeric(
    source: np.ndarray,
    source_transform: Any,
    source_crs: Any,
    destination_grid: AnalysisGrid,
    *,
    resampling: Resampling,
    source_nodata: float | int | None = None,
    destination_nodata: float = np.nan,
) -> np.ndarray:
    destination = np.full(
        (destination_grid.height, destination_grid.width),
        destination_nodata,
        dtype=np.float32,
    )
    reproject(
        source=np.asarray(source),
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        src_nodata=source_nodata,
        dst_transform=destination_grid.transform,
        dst_crs=destination_grid.crs,
        dst_nodata=destination_nodata,
        resampling=resampling,
        num_threads=2,
    )
    return destination


def numeric_summary(values: np.ndarray, units: str) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    valid = array[np.isfinite(array)]
    if not valid.size:
        return {
            "units": units,
            "valid_count": 0,
            "undefined_fraction": 1.0,
        }
    percentiles = (1, 5, 25, 50, 75, 95, 99)
    return {
        "units": units,
        "valid_count": int(valid.size),
        "undefined_fraction": float(1.0 - valid.size / array.size),
        "minimum": float(np.min(valid)),
        "maximum": float(np.max(valid)),
        "mean": float(np.mean(valid)),
        "median": float(np.median(valid)),
        "standard_deviation": float(np.std(valid)),
        "percentiles": {
            str(percentile): float(value)
            for percentile, value in zip(percentiles, np.percentile(valid, percentiles))
        },
    }


def pearson_pair(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    left = np.asarray(a, dtype=np.float64).ravel()
    right = np.asarray(b, dtype=np.float64).ravel()
    valid = np.isfinite(left) & np.isfinite(right)
    if np.count_nonzero(valid) < 3:
        return {"count": int(np.count_nonzero(valid)), "pearson_r": None}
    return {
        "count": int(np.count_nonzero(valid)),
        "pearson_r": float(np.corrcoef(left[valid], right[valid])[0, 1]),
    }


def assert_grid(grid: AnalysisGrid) -> None:
    if grid.width <= 0 or grid.height <= 0:
        raise ValueError("Analysis grid has non-positive dimensions")
    if not math.isclose(
        grid.width * grid.resolution_m, grid.east - grid.west, abs_tol=1e-6
    ) or not math.isclose(
        grid.height * grid.resolution_m, grid.north - grid.south, abs_tol=1e-6
    ):
        raise ValueError("Bounds must be exactly divisible by the analysis resolution")
