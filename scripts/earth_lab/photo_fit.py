"""Pure helpers for bounded Lab 004B photographic alignment."""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from affine import Affine

from calibrate_photo_skyline import (
    PhotoSkyline,
    TerrainHorizon,
    _median_filter,
    horizontal_ray_angles,
    photo_relative_elevation_angles,
    weighted_mean,
)
from diagnose_photo_geometry import bilinear_sample


@dataclass(frozen=True)
class DecodedLandscape:
    elevations_m_odn: np.ndarray
    transform: Affine
    bounds: tuple[float, float, float, float]
    spacing_m: float
    sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode_landscape_r16(
    path: Path,
    *,
    width: int,
    height: int,
    bounds: tuple[float, float, float, float],
    vertical_origin_m_odn: float,
    z_scale: float,
    expected_sha256: str | None = None,
) -> DecodedLandscape:
    actual_sha256 = sha256_file(path)
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        raise ValueError(
            f"R16 SHA-256 {actual_sha256} does not match {expected_sha256}"
        )
    encoded = np.fromfile(path, dtype="<u2")
    if encoded.size != width * height:
        raise ValueError(
            f"R16 contains {encoded.size} samples; expected {width * height}"
        )
    encoded = encoded.reshape(height, width)
    elevations = (
        vertical_origin_m_odn
        + (encoded.astype(np.float64) - 32768.0) / 128.0 * z_scale / 100.0
    )
    west, south, east, north = bounds
    spacing_x = (east - west) / (width - 1)
    spacing_y = (north - south) / (height - 1)
    if not math.isclose(spacing_x, spacing_y, abs_tol=1e-12):
        raise ValueError("Landscape vertex spacing differs between axes")
    # Pixel centres coincide with Landscape vertices, including the AOI edges.
    transform = (
        Affine.translation(west - spacing_x / 2.0, north + spacing_y / 2.0)
        @ Affine.scale(spacing_x, -spacing_y)
    )
    return DecodedLandscape(
        elevations_m_odn=elevations,
        transform=transform,
        bounds=bounds,
        spacing_m=spacing_x,
        sha256=actual_sha256,
    )


def sample_surface(
    surface: DecodedLandscape, easting: float, northing: float
) -> float:
    return float(
        bilinear_sample(
            surface.elevations_m_odn,
            surface.transform,
            np.array([float(easting)]),
            np.array([float(northing)]),
        )[0]
    )


def evaluate_camera(
    skyline: PhotoSkyline,
    horizon: TerrainHorizon,
    centre_heading_degrees: float,
    horizontal_fov_degrees: float,
    pitch_degrees: float,
) -> dict[str, Any]:
    """Measure an explicit camera without solving away its vertical error."""
    horizontal_angles, focal_pixels = horizontal_ray_angles(
        skyline.width, horizontal_fov_degrees
    )
    ray_bearings = centre_heading_degrees + horizontal_angles
    terrain_angles = np.interp(
        ray_bearings,
        horizon.true_bearings_degrees,
        horizon.elevation_angles_degrees,
        left=np.nan,
        right=np.nan,
    )
    photo_relative = photo_relative_elevation_angles(skyline, focal_pixels)
    valid = np.isfinite(terrain_angles) & (skyline.confidence > 0.0)
    weights = skyline.confidence[valid]
    residual_degrees = terrain_angles - (photo_relative + pitch_degrees)
    rmse = math.sqrt(weighted_mean(residual_degrees[valid] ** 2, weights))
    mae = weighted_mean(np.abs(residual_degrees[valid]), weights)

    terrain_smooth = _median_filter(terrain_angles, 7)
    photo_smooth = _median_filter(photo_relative, 7)
    slope_residual = np.gradient(terrain_smooth) - np.gradient(photo_smooth)
    slope_rmse = math.sqrt(weighted_mean(slope_residual[valid] ** 2, weights))

    terrain_centered = terrain_angles[valid] - weighted_mean(
        terrain_angles[valid], weights
    )
    photo_centered = photo_relative[valid] - weighted_mean(
        photo_relative[valid], weights
    )
    covariance = weighted_mean(terrain_centered * photo_centered, weights)
    variance_product = weighted_mean(
        terrain_centered**2, weights
    ) * weighted_mean(photo_centered**2, weights)
    correlation = (
        covariance / math.sqrt(variance_product)
        if variance_product > 0.0
        else 0.0
    )

    predicted_y = (
        (skyline.height - 1) / 2.0
        - focal_pixels
        * np.tan(np.radians(terrain_angles - pitch_degrees))
    )
    pixel_residual = predicted_y - skyline.y_pixels
    pixel_rmse = math.sqrt(weighted_mean(pixel_residual[valid] ** 2, weights))
    pixel_mae = weighted_mean(np.abs(pixel_residual[valid]), weights)
    clear = valid & ~skyline.cloud_affected
    clear_weights = skyline.confidence[clear]
    clear_rmse_degrees = math.sqrt(
        weighted_mean(residual_degrees[clear] ** 2, clear_weights)
    )
    clear_rmse_pixels = math.sqrt(
        weighted_mean(pixel_residual[clear] ** 2, clear_weights)
    )
    return {
        "centre_true_heading_degrees": float(centre_heading_degrees),
        "horizontal_fov_degrees": float(horizontal_fov_degrees),
        "pitch_degrees": float(pitch_degrees),
        "weighted_rmse_degrees": float(rmse),
        "weighted_mae_degrees": float(mae),
        "weighted_slope_rmse_degrees_per_pixel": float(slope_rmse),
        "weighted_shape_correlation": float(correlation),
        "weighted_rmse_pixels": float(pixel_rmse),
        "weighted_mae_pixels": float(pixel_mae),
        "p95_absolute_pixels": float(
            np.nanpercentile(np.abs(pixel_residual[valid]), 95)
        ),
        "maximum_absolute_pixels": float(np.nanmax(np.abs(pixel_residual[valid]))),
        "clear_sky_weighted_rmse_degrees": float(clear_rmse_degrees),
        "clear_sky_weighted_rmse_pixels": float(clear_rmse_pixels),
        "clear_sky_p95_absolute_pixels": float(
            np.nanpercentile(np.abs(pixel_residual[clear]), 95)
        ),
        "score": float(rmse + 10.0 * slope_rmse),
        "focal_pixels": float(focal_pixels),
        "terrain_angles_degrees": terrain_angles,
        "photo_relative_angles_degrees": photo_relative,
        "residual_degrees": residual_degrees,
        "predicted_y_pixels": predicted_y,
        "pixel_residuals": pixel_residual,
        "ray_bearings_degrees": ray_bearings,
    }


def solve_bounded_pitch(
    skyline: PhotoSkyline,
    horizon: TerrainHorizon,
    centre_heading_degrees: float,
    horizontal_fov_degrees: float,
    pitch_bounds: tuple[float, float],
) -> dict[str, Any]:
    horizontal_angles, focal_pixels = horizontal_ray_angles(
        skyline.width, horizontal_fov_degrees
    )
    terrain_angles = np.interp(
        centre_heading_degrees + horizontal_angles,
        horizon.true_bearings_degrees,
        horizon.elevation_angles_degrees,
        left=np.nan,
        right=np.nan,
    )
    photo_relative = photo_relative_elevation_angles(skyline, focal_pixels)
    valid = np.isfinite(terrain_angles) & (skyline.confidence > 0.0)
    solved = weighted_mean(
        terrain_angles[valid] - photo_relative[valid], skyline.confidence[valid]
    )
    pitch = min(max(solved, pitch_bounds[0]), pitch_bounds[1])
    result = evaluate_camera(
        skyline, horizon, centre_heading_degrees, horizontal_fov_degrees, pitch
    )
    result["unconstrained_solved_pitch_degrees"] = float(solved)
    result["pitch_bound_reached"] = not math.isclose(pitch, solved, abs_tol=1e-12)
    return result


def inclusive_values(minimum: float, maximum: float, step: float) -> np.ndarray:
    if step <= 0.0 or maximum < minimum:
        raise ValueError("Invalid inclusive range")
    count = int(math.floor((maximum - minimum) / step + 1e-9))
    values = minimum + np.arange(count + 1, dtype=float) * step
    if values[-1] < maximum - 1e-9:
        values = np.append(values, maximum)
    return values


def bound_reached(value: float, bounds: tuple[float, float], tolerance: float) -> bool:
    return (
        abs(value - bounds[0]) <= tolerance
        or abs(value - bounds[1]) <= tolerance
    )


def serializable_metrics(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if not isinstance(value, np.ndarray)
    }
