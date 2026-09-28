"""Temporal evidence helpers for Meridian Earth Lab 005C."""
from __future__ import annotations

from typing import Any

import numpy as np

CLOUD_INVALID_SCL_CLASSES = frozenset((0, 1, 3, 8, 9, 10))


def cloud_clear_mask(scl: np.ndarray) -> np.ndarray:
    """Validity for observation: cloud/shadow/invalid masked, snow retained."""
    values = np.asarray(scl)
    return ~np.isin(values, tuple(CLOUD_INVALID_SCL_CLASSES))


def snow_mask(scl: np.ndarray) -> np.ndarray:
    return np.asarray(scl) == 11


def temporal_scl_summary(scl: np.ndarray) -> dict[str, Any]:
    values = np.asarray(scl)
    clear = cloud_clear_mask(values)
    snow = snow_mask(values)
    total = int(values.size)
    unique, counts = np.unique(values, return_counts=True)
    return {
        "total_cells": total,
        "cloud_clear_cells_including_snow": int(np.count_nonzero(clear)),
        "cloud_clear_fraction_including_snow": float(np.mean(clear)),
        "surface_clear_cells_excluding_snow": int(np.count_nonzero(clear & ~snow)),
        "surface_clear_fraction_excluding_snow": float(np.mean(clear & ~snow)),
        "cloud_fraction": float(np.mean(np.isin(values, (8, 9, 10)))),
        "cloud_shadow_fraction": float(np.mean(values == 3)),
        "snow_or_ice_fraction": float(np.mean(snow)),
        "nodata_fraction": float(np.mean(values == 0)),
        "topographic_shadow_fraction": float(np.mean(values == 2)),
        "class_counts": {str(int(code)): int(count) for code, count in zip(unique, counts)},
    }


def cosine_illumination(
    slope_degrees: np.ndarray,
    aspect_degrees: np.ndarray,
    sun_elevation_degrees: float,
    sun_azimuth_degrees: float,
) -> np.ndarray:
    """Cosine of local solar incidence on a grid-north slope/aspect surface.

    Aspect is downhill/facing azimuth clockwise from grid north. Negative values
    mean the direct sun lies below the local terrain plane; no atmospheric or
    cast-shadow correction is applied.
    """
    slope = np.asarray(slope_degrees, dtype=np.float64)
    aspect = np.asarray(aspect_degrees, dtype=np.float64)
    slope_radians = np.radians(slope)
    aspect_radians = np.radians(np.where(np.isfinite(aspect), aspect, 0.0))
    elevation = np.radians(float(sun_elevation_degrees))
    azimuth = np.radians(float(sun_azimuth_degrees))
    result = (
        np.sin(elevation) * np.cos(slope_radians)
        + np.cos(elevation) * np.sin(slope_radians) * np.cos(azimuth - aspect_radians)
    )
    valid = np.isfinite(slope) & (np.isfinite(aspect) | (np.abs(slope) < 0.5))
    return np.where(valid, result, np.nan).astype(np.float32)


def temporal_statistics(
    values: np.ndarray,
    valid: np.ndarray | None = None,
    *,
    coefficient_of_variation: bool = False,
    cv_minimum_abs_mean: float = 0.02,
) -> dict[str, np.ndarray]:
    """Per-cell temporal statistics across an observation-first stack."""
    stack = np.asarray(values, dtype=np.float32)
    if stack.ndim != 3:
        raise ValueError("Temporal values must have shape observations x rows x columns")
    mask = np.isfinite(stack)
    if valid is not None:
        valid_array = np.asarray(valid, dtype=bool)
        if valid_array.shape != stack.shape:
            raise ValueError("Temporal validity mask must match the value stack")
        mask &= valid_array
    working = np.where(mask, stack, np.nan)
    count = np.sum(mask, axis=0).astype(np.uint8)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.nanmean(working, axis=0).astype(np.float32)
        median = np.nanmedian(working, axis=0).astype(np.float32)
        minimum = np.nanmin(working, axis=0).astype(np.float32)
        maximum = np.nanmax(working, axis=0).astype(np.float32)
        standard_deviation = np.nanstd(working, axis=0).astype(np.float32)
    for output in (mean, median, minimum, maximum, standard_deviation):
        output[count == 0] = np.nan
    result = {
        "count": count,
        "mean": mean,
        "median": median,
        "minimum": minimum,
        "maximum": maximum,
        "range": (maximum - minimum).astype(np.float32),
        "standard_deviation": standard_deviation,
    }
    if coefficient_of_variation:
        cv = np.full(mean.shape, np.nan, dtype=np.float32)
        safe = (count > 1) & np.isfinite(mean) & (np.abs(mean) >= cv_minimum_abs_mean)
        np.divide(standard_deviation, np.abs(mean), out=cv, where=safe)
        result["coefficient_of_variation"] = cv
    return result


def temporal_correlation(
    observations: np.ndarray,
    driver: np.ndarray,
    valid: np.ndarray | None = None,
    *,
    minimum_count: int = 3,
) -> np.ndarray:
    """Per-cell Pearson correlation across the observation axis."""
    left = np.asarray(observations, dtype=np.float64)
    right = np.asarray(driver, dtype=np.float64)
    if left.shape != right.shape or left.ndim != 3:
        raise ValueError("Observation and driver stacks must share a 3-D shape")
    mask = np.isfinite(left) & np.isfinite(right)
    if valid is not None:
        mask &= np.asarray(valid, dtype=bool)
    count = np.sum(mask, axis=0)
    left_mean = np.divide(np.sum(np.where(mask, left, 0.0), axis=0), count, out=np.zeros(left.shape[1:]), where=count > 0)
    right_mean = np.divide(np.sum(np.where(mask, right, 0.0), axis=0), count, out=np.zeros(right.shape[1:]), where=count > 0)
    left_delta = np.where(mask, left - left_mean, 0.0)
    right_delta = np.where(mask, right - right_mean, 0.0)
    numerator = np.sum(left_delta * right_delta, axis=0)
    denominator = np.sqrt(np.sum(left_delta**2, axis=0) * np.sum(right_delta**2, axis=0))
    result = np.full(left.shape[1:], np.nan, dtype=np.float32)
    usable = (count >= minimum_count) & (denominator > 1e-12)
    np.divide(numerator, denominator, out=result, where=usable)
    return result
