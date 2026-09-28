"""Deterministic terrain derivatives for Meridian Earth Lab 005A."""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def _as_surface(elevation: np.ndarray) -> np.ndarray:
    result = np.asarray(elevation, dtype=np.float64)
    if result.ndim != 2 or min(result.shape) < 3:
        raise ValueError("Elevation must be a two-dimensional array at least 3x3")
    return result


def horn_gradients(
    elevation_m: np.ndarray, spacing_m: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return dz/deast and dz/dsouth using Horn's weighted 3x3 derivative."""
    z = _as_surface(elevation_m)
    spacing = float(spacing_m)
    if not math.isfinite(spacing) or spacing <= 0.0:
        raise ValueError("spacing_m must be positive and finite")
    p = np.full(z.shape, np.nan, dtype=np.float64)
    q = np.full(z.shape, np.nan, dtype=np.float64)
    nw, n, ne = z[:-2, :-2], z[:-2, 1:-1], z[:-2, 2:]
    w, c, e = z[1:-1, :-2], z[1:-1, 1:-1], z[1:-1, 2:]
    sw, s, se = z[2:, :-2], z[2:, 1:-1], z[2:, 2:]
    valid = np.isfinite(nw) & np.isfinite(n) & np.isfinite(ne)
    valid &= np.isfinite(w) & np.isfinite(c) & np.isfinite(e)
    valid &= np.isfinite(sw) & np.isfinite(s) & np.isfinite(se)
    p_inner = ((ne + 2.0 * e + se) - (nw + 2.0 * w + sw)) / (8.0 * spacing)
    q_inner = ((sw + 2.0 * s + se) - (nw + 2.0 * n + ne)) / (8.0 * spacing)
    p[1:-1, 1:-1] = np.where(valid, p_inner, np.nan)
    q[1:-1, 1:-1] = np.where(valid, q_inner, np.nan)
    return p, q


def slope_aspect(
    elevation_m: np.ndarray,
    spacing_m: float,
    *,
    flat_threshold_degrees: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Return slope degrees and downhill aspect clockwise from grid north."""
    p_east, q_south = horn_gradients(elevation_m, spacing_m)
    slope = np.degrees(np.arctan(np.hypot(p_east, q_south)))
    aspect = np.degrees(np.arctan2(-p_east, q_south)) % 360.0
    aspect[~np.isfinite(slope) | (slope < float(flat_threshold_degrees))] = np.nan
    return slope, aspect


def binomial_smooth(elevation_m: np.ndarray) -> np.ndarray:
    """Apply a normalized separable [1,4,6,4,1]/16 filter with NaN support."""
    z = _as_surface(elevation_m)
    weights = np.array([1.0, 4.0, 6.0, 4.0, 1.0], dtype=np.float64)

    def axis_filter(values: np.ndarray, axis: int) -> np.ndarray:
        pad = [(0, 0), (0, 0)]
        pad[axis] = (2, 2)
        valid = np.isfinite(values)
        numer = np.pad(np.where(valid, values, 0.0), pad, mode="reflect")
        denom = np.pad(valid.astype(np.float64), pad, mode="reflect")
        output_n = np.zeros_like(values, dtype=np.float64)
        output_d = np.zeros_like(values, dtype=np.float64)
        for offset, weight in enumerate(weights):
            slices = [slice(None), slice(None)]
            slices[axis] = slice(offset, offset + values.shape[axis])
            output_n += weight * numer[tuple(slices)]
            output_d += weight * denom[tuple(slices)]
        return np.divide(
            output_n,
            output_d,
            out=np.full_like(output_n, np.nan),
            where=output_d > 0.0,
        )

    return axis_filter(axis_filter(z, 1), 0)


def terrain_curvatures(
    elevation_m: np.ndarray,
    spacing_m: float,
    *,
    minimum_slope_degrees: float = 1.0,
) -> dict[str, np.ndarray]:
    """Return Laplacian, downslope profile, and horizontal plan curvature.

    Positive values are concave/hollow and negative values convex/ridge under
    the documented local graph-surface convention.
    """
    z = binomial_smooth(elevation_m)
    spacing = float(spacing_m)
    q_south, p_east = np.gradient(z, spacing, spacing, edge_order=2)
    d2_south = np.gradient(q_south, spacing, axis=0, edge_order=2)
    d2_east = np.gradient(p_east, spacing, axis=1, edge_order=2)
    mixed_a = np.gradient(p_east, spacing, axis=0, edge_order=2)
    mixed_b = np.gradient(q_south, spacing, axis=1, edge_order=2)
    mixed = 0.5 * (mixed_a + mixed_b)
    gradient_squared = p_east * p_east + q_south * q_south
    gradient = np.sqrt(gradient_squared)
    valid_direction = gradient >= math.tan(math.radians(minimum_slope_degrees))

    laplacian = d2_east + d2_south
    profile_num = (
        d2_east * p_east * p_east
        + 2.0 * mixed * p_east * q_south
        + d2_south * q_south * q_south
    )
    profile_den = gradient_squared * np.power(1.0 + gradient_squared, 1.5)
    profile = np.divide(
        profile_num,
        profile_den,
        out=np.full_like(z, np.nan),
        where=valid_direction & (profile_den > 0.0),
    )

    plan_num = (
        d2_east * q_south * q_south
        - 2.0 * mixed * p_east * q_south
        + d2_south * p_east * p_east
    )
    plan_den = np.power(gradient_squared, 1.5)
    plan = np.divide(
        plan_num,
        plan_den,
        out=np.full_like(z, np.nan),
        where=valid_direction & (plan_den > 0.0),
    )

    source_valid = np.isfinite(_as_surface(elevation_m))
    for output in (laplacian, profile, plan):
        output[~source_valid] = np.nan
        output[:3, :] = np.nan
        output[-3:, :] = np.nan
        output[:, :3] = np.nan
        output[:, -3:] = np.nan
    return {
        "laplacian_per_m": laplacian,
        "profile_per_m": profile,
        "plan_per_m": plan,
        "smoothed_elevation_m": z,
    }


def _box_sum(values: np.ndarray, window: int) -> np.ndarray:
    integral = np.pad(values, ((1, 0), (1, 0)), mode="constant")
    integral = np.cumsum(np.cumsum(integral, axis=0), axis=1)
    return (
        integral[window:, window:]
        - integral[:-window, window:]
        - integral[window:, :-window]
        + integral[:-window, :-window]
    )


def detrended_rms_roughness(elevation_m: np.ndarray, window_samples: int) -> np.ndarray:
    """RMS vertical residual after fitting a plane in each complete square window."""
    z = _as_surface(elevation_m)
    window = int(window_samples)
    if window < 3 or window % 2 != 1:
        raise ValueError("window_samples must be an odd integer of at least 3")
    if window > min(z.shape):
        raise ValueError("window_samples exceeds the surface dimensions")
    radius = window // 2
    valid = np.isfinite(z)
    reference_elevation = float(np.nanmean(z))
    filled = np.where(valid, z - reference_elevation, 0.0)
    count = _box_sum(valid.astype(np.float64), window)
    sum_z = _box_sum(filled, window)
    sum_z2 = _box_sum(filled * filled, window)
    columns = np.arange(z.shape[1], dtype=np.float64)[None, :]
    rows = np.arange(z.shape[0], dtype=np.float64)[:, None]
    sum_xz = _box_sum(filled * columns, window)
    sum_yz = _box_sum(filled * rows, window)
    centre_columns = np.arange(radius, z.shape[1] - radius, dtype=np.float64)[None, :]
    centre_rows = np.arange(radius, z.shape[0] - radius, dtype=np.float64)[:, None]
    local_xz = sum_xz - centre_columns * sum_z
    local_yz = sum_yz - centre_rows * sum_z
    n = float(window * window)
    sum_offsets_squared = float(window * np.sum(np.arange(-radius, radius + 1) ** 2))
    sse = (
        sum_z2
        - sum_z * sum_z / n
        - local_xz * local_xz / sum_offsets_squared
        - local_yz * local_yz / sum_offsets_squared
    )
    sse = np.maximum(sse, 0.0)
    inner = np.where(count == n, np.sqrt(sse / n), np.nan)
    output = np.full(z.shape, np.nan, dtype=np.float64)
    output[radius:-radius, radius:-radius] = inner
    return output


def numeric_summary(values: np.ndarray, units: str) -> dict[str, Any]:
    data = np.asarray(values, dtype=np.float64)
    valid = data[np.isfinite(data)]
    if valid.size == 0:
        raise ValueError("Cannot summarize an entirely undefined field")
    percentiles = (0, 1, 5, 25, 50, 75, 95, 99, 100)
    return {
        "units": units,
        "valid_count": int(valid.size),
        "undefined_count": int(data.size - valid.size),
        "undefined_fraction": float(1.0 - valid.size / data.size),
        "mean": float(np.mean(valid)),
        "median": float(np.median(valid)),
        "standard_deviation": float(np.std(valid)),
        "percentiles": {
            str(value): float(result)
            for value, result in zip(percentiles, np.percentile(valid, percentiles))
        },
    }


def aspect_summary(aspect_degrees: np.ndarray) -> dict[str, Any]:
    data = np.asarray(aspect_degrees, dtype=np.float64)
    valid = data[np.isfinite(data)]
    if valid.size == 0:
        raise ValueError("Cannot summarize an entirely undefined aspect field")
    radians = np.radians(valid)
    mean_sin = float(np.mean(np.sin(radians)))
    mean_cos = float(np.mean(np.cos(radians)))
    mean_direction = math.degrees(math.atan2(mean_sin, mean_cos)) % 360.0
    edges = np.arange(0.0, 361.0, 45.0)
    shifted = (valid + 22.5) % 360.0
    counts, _ = np.histogram(shifted, bins=edges)
    labels = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    return {
        "units": "degrees_clockwise_from_grid_north",
        "valid_count": int(valid.size),
        "undefined_count": int(data.size - valid.size),
        "undefined_fraction": float(1.0 - valid.size / data.size),
        "circular_mean_degrees": float(mean_direction),
        "mean_resultant_length": float(math.hypot(mean_sin, mean_cos)),
        "direction_fractions": {
            label: float(count / valid.size) for label, count in zip(labels, counts)
        },
    }