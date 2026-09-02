from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from route_geometry import RouteGeometry


@dataclass(slots=True, frozen=True)
class ProcessingVariant:
    id: str
    median_span_m: float
    hysteresis_m: float
    gradient_half_window_m: float = 120.0


PROCESSING_VARIANTS = (
    ProcessingVariant("raw", 0.0, 0.0),
    ProcessingVariant("hysteresis_3m_only", 0.0, 3.0),
    ProcessingVariant("median_40m_h2", 40.0, 2.0, 80.0),
    ProcessingVariant("median_80m_h2", 80.0, 2.0, 80.0),
    # At 40 m spacing a radius of two is the production five-sample median.
    ProcessingVariant("production_median_160m_h3", 160.0, 3.0, 120.0),
)


@dataclass(slots=True)
class ProfileResult:
    source: str
    spacing_m: float
    processing: ProcessingVariant
    sample_count: int
    distance_m: float
    min_elevation_m: float
    max_elevation_m: float
    raw_ascent_m: float
    raw_descent_m: float
    smoothed_ascent_m: float
    smoothed_descent_m: float
    processed_ascent_m: float
    processed_descent_m: float
    smoothing_removed_ascent_m: float
    hysteresis_removed_ascent_m: float
    gradient_p10: float
    gradient_median: float
    gradient_p90: float
    predicted_moving_hours: float
    elevations_m: np.ndarray
    processed_elevations_m: np.ndarray
    gradients: np.ndarray
    cumulative_ascent_m: np.ndarray

    def summary(self) -> dict[str, float | int | str]:
        return {
            "source": self.source,
            "spacing_m": self.spacing_m,
            "processing": self.processing.id,
            "sample_count": self.sample_count,
            "distance_m": self.distance_m,
            "min_elevation_m": self.min_elevation_m,
            "max_elevation_m": self.max_elevation_m,
            "raw_ascent_m": self.raw_ascent_m,
            "raw_descent_m": self.raw_descent_m,
            "smoothed_ascent_m": self.smoothed_ascent_m,
            "smoothed_descent_m": self.smoothed_descent_m,
            "processed_ascent_m": self.processed_ascent_m,
            "processed_descent_m": self.processed_descent_m,
            "smoothing_removed_ascent_m": self.smoothing_removed_ascent_m,
            "hysteresis_removed_ascent_m": self.hysteresis_removed_ascent_m,
            "gradient_p10": self.gradient_p10,
            "gradient_median": self.gradient_median,
            "gradient_p90": self.gradient_p90,
            "predicted_moving_hours": self.predicted_moving_hours,
        }


def median_smooth_physical(
    elevations: Sequence[float], spacing_m: float, span_m: float
) -> np.ndarray:
    values = np.asarray(elevations, dtype=np.float64)
    if span_m <= 0:
        return values.copy()
    radius = round(span_m / (2.0 * spacing_m))
    if radius <= 0:
        return values.copy()
    return np.asarray(
        [
            np.median(values[max(0, index - radius) : index + radius + 1])
            for index in range(len(values))
        ],
        dtype=np.float64,
    )


def raw_variation(elevations: Sequence[float]) -> tuple[float, float]:
    differences = np.diff(np.asarray(elevations, dtype=np.float64))
    return (
        float(np.sum(differences[differences > 0.0])),
        float(-np.sum(differences[differences < 0.0])),
    )


def hysteresis_profile(
    elevations: Sequence[float], threshold_m: float
) -> tuple[float, float, np.ndarray]:
    values = np.asarray(elevations, dtype=np.float64)
    if len(values) == 0:
        return 0.0, 0.0, np.asarray([], dtype=np.float64)
    reference = float(values[0])
    ascent = 0.0
    descent = 0.0
    cumulative = [0.0]
    for elevation in values[1:]:
        difference = float(elevation) - reference
        if abs(difference) >= threshold_m:
            if difference > 0:
                ascent += difference
            else:
                descent -= difference
            reference = float(elevation)
        cumulative.append(ascent)
    return ascent, descent, np.asarray(cumulative, dtype=np.float64)


def gradients(
    elevations: Sequence[float], distances_m: Sequence[float], half_window_m: float
) -> np.ndarray:
    values = np.asarray(elevations, dtype=np.float64)
    distances = np.asarray(distances_m, dtype=np.float64)
    result = np.full(len(values), np.nan, dtype=np.float64)
    if len(values) < 2:
        return result
    spacing = max(0.01, float(np.median(np.diff(distances))))
    radius = max(1, round(half_window_m / spacing))
    for index in range(len(values)):
        before = max(0, index - radius)
        after = min(len(values) - 1, index + radius)
        distance = distances[after] - distances[before]
        if distance >= 1.0:
            result[index] = (values[after] - values[before]) / distance
    return result


def tobler_speed_kmh(gradient: float) -> float:
    slope = max(-0.5, min(0.5, gradient))
    baseline = 6.0 * math.exp(-3.5 * abs(slope + 0.05))
    return max(0.8, min(7.0, baseline))


def predicted_moving_hours(route: RouteGeometry, gradient_values: np.ndarray) -> float:
    minutes = 0.0
    for index in range(1, len(route.coordinates)):
        distance_m = route.cumulative_distances_m[index] - route.cumulative_distances_m[index - 1]
        left = gradient_values[index - 1]
        right = gradient_values[index]
        if distance_m <= 0 or not np.isfinite(left) or not np.isfinite(right):
            continue
        speed_kmh = tobler_speed_kmh(float((left + right) / 2.0))
        minutes += (distance_m / 1000.0 / speed_kmh) * 60.0
    return minutes / 60.0


def analyse_profile(
    source: str,
    route: RouteGeometry,
    elevations: Sequence[float | None],
    variant: ProcessingVariant,
) -> ProfileResult:
    if len(elevations) != len(route.coordinates):
        raise ValueError("Elevation samples do not align with route geometry")
    if any(value is None or not math.isfinite(value) for value in elevations):
        raise ValueError("Complete finite terrain coverage is required for profile analysis")
    values = np.asarray(elevations, dtype=np.float64)
    spacing = route.total_distance_m / max(1, len(route.coordinates) - 1)
    processed = median_smooth_physical(values, spacing, variant.median_span_m)
    raw_ascent, raw_descent = raw_variation(values)
    smoothed_ascent, smoothed_descent = raw_variation(processed)
    ascent, descent, cumulative = hysteresis_profile(processed, variant.hysteresis_m)
    gradient_values = gradients(
        processed, route.cumulative_distances_m, variant.gradient_half_window_m
    )
    finite_gradients = gradient_values[np.isfinite(gradient_values)]
    percentiles = np.percentile(finite_gradients, [10, 50, 90])
    return ProfileResult(
        source=source,
        spacing_m=spacing,
        processing=variant,
        sample_count=len(values),
        distance_m=route.total_distance_m,
        min_elevation_m=float(np.min(values)),
        max_elevation_m=float(np.max(values)),
        raw_ascent_m=raw_ascent,
        raw_descent_m=raw_descent,
        smoothed_ascent_m=smoothed_ascent,
        smoothed_descent_m=smoothed_descent,
        processed_ascent_m=ascent,
        processed_descent_m=descent,
        smoothing_removed_ascent_m=raw_ascent - smoothed_ascent,
        hysteresis_removed_ascent_m=smoothed_ascent - ascent,
        gradient_p10=float(percentiles[0]),
        gradient_median=float(percentiles[1]),
        gradient_p90=float(percentiles[2]),
        predicted_moving_hours=predicted_moving_hours(route, gradient_values),
        elevations_m=values,
        processed_elevations_m=processed,
        gradients=gradient_values,
        cumulative_ascent_m=cumulative,
    )


def neighbourhood_metrics(
    elevation_grid: np.ndarray,
    pixel_size_m: float,
    radii_m: Sequence[float] = (5.0, 20.0, 50.0, 200.0),
) -> dict[str, float | None]:
    grid = np.asarray(elevation_grid, dtype=np.float64)
    if grid.ndim != 2 or min(grid.shape) < 3:
        raise ValueError("Terrain neighbourhood must be a two-dimensional grid")
    centre_row = grid.shape[0] // 2
    centre_col = grid.shape[1] // 2
    centre = grid[centre_row, centre_col]
    if not np.isfinite(centre):
        return {"centre_elevation_m": None}
    y, x = np.indices(grid.shape)
    dx = (x - centre_col) * pixel_size_m
    dy = (centre_row - y) * pixel_size_m
    distance = np.hypot(dx, dy)
    result: dict[str, float | None] = {"centre_elevation_m": float(centre)}
    for radius_m in radii_m:
        mask = (distance <= radius_m) & np.isfinite(grid)
        key = str(int(radius_m))
        if np.count_nonzero(mask) < 9:
            result[f"relief_{key}m"] = None
            result[f"roughness_{key}m"] = None
            result[f"convexity_{key}m"] = None
            continue
        stride = max(1, round(radius_m / max(pixel_size_m, 1e-6) / 40.0))
        sampled = mask & ((x % stride) == centre_col % stride) & ((y % stride) == centre_row % stride)
        z = grid[sampled]
        xx = dx[sampled]
        yy = dy[sampled]
        design = np.column_stack((xx, yy, np.ones_like(xx)))
        coefficients, *_ = np.linalg.lstsq(design, z, rcond=None)
        residual = z - design @ coefficients
        annulus = mask & (distance >= radius_m * 0.6)
        result[f"relief_{key}m"] = float(np.max(z) - np.min(z))
        result[f"roughness_{key}m"] = float(np.std(residual))
        result[f"convexity_{key}m"] = (
            float(centre - np.mean(grid[annulus]))
            if np.count_nonzero(annulus) >= 5
            else None
        )
    for baseline_m in (10.0, 20.0):
        offset = max(1, round(baseline_m / pixel_size_m))
        if (
            centre_row - offset < 0
            or centre_row + offset >= grid.shape[0]
            or centre_col - offset < 0
            or centre_col + offset >= grid.shape[1]
        ):
            result[f"slope_{int(baseline_m)}m_deg"] = None
            result[f"aspect_{int(baseline_m)}m_deg"] = None
            continue
        samples = (
            grid[centre_row, centre_col - offset],
            grid[centre_row, centre_col + offset],
            grid[centre_row + offset, centre_col],
            grid[centre_row - offset, centre_col],
        )
        if not all(np.isfinite(value) for value in samples):
            result[f"slope_{int(baseline_m)}m_deg"] = None
            result[f"aspect_{int(baseline_m)}m_deg"] = None
            continue
        denominator = 2.0 * offset * pixel_size_m
        dzdx = (samples[1] - samples[0]) / denominator
        dzdy = (samples[3] - samples[2]) / denominator
        result[f"slope_{int(baseline_m)}m_deg"] = math.degrees(
            math.atan(math.hypot(dzdx, dzdy))
        )
        result[f"aspect_{int(baseline_m)}m_deg"] = (
            math.degrees(math.atan2(-dzdx, -dzdy)) + 360.0
        ) % 360.0
    return result
