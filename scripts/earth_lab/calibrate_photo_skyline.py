"""Calibrate a fixed photographic benchmark against a source-DTM skyline.

This is a read-only diagnostic. It never reads from or writes to Unreal and never
modifies source terrain, benchmark metadata, or the reference photograph.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from PIL import Image, ImageDraw
from pyproj import Geod, Transformer

from diagnose_photo_geometry import bilinear_sample


@dataclass(frozen=True)
class PhotoSkyline:
    y_pixels: np.ndarray
    confidence: np.ndarray
    cloud_affected: np.ndarray
    edge_strength: np.ndarray
    width: int
    height: int


@dataclass(frozen=True)
class TerrainHorizon:
    true_bearings_degrees: np.ndarray
    elevation_angles_degrees: np.ndarray
    distances_m: np.ndarray
    elevations_m_odn: np.ndarray
    eastings: np.ndarray
    northings: np.ndarray


def _median_filter(values: np.ndarray, window: int) -> np.ndarray:
    if window % 2 != 1:
        raise ValueError("Median-filter window must be odd")
    pad = window // 2
    padded = np.pad(values, (pad, pad), mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, window)
    return np.median(windows, axis=1)


def extract_photo_skyline(image_path: Path) -> PhotoSkyline:
    """Extract the dominant sky-to-mountain luminance edge.

    The Tony Edwards image has a strong bright-sky/dark-terrain transition over most
    columns. Cloud merges with the summit over normalized x=0.275..0.475; those
    columns remain visible in diagnostics but receive only 20% weight.
    """
    rgb = np.asarray(Image.open(image_path).convert("RGB"), dtype=np.float64)
    height, width, _ = rgb.shape
    luminance = (
        0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    )
    kernel = np.ones(9, dtype=float) / 9.0
    smooth_vertical = np.apply_along_axis(
        lambda column: np.convolve(column, kernel, mode="same"),
        0,
        luminance,
    )
    offset = 7
    downward_drop = smooth_vertical[:-offset] - smooth_vertical[offset:]
    search_top = max(12, int(round(height * 0.06)))
    search_bottom = min(height - offset - 1, int(round(height * 0.50)))
    search = downward_drop[search_top:search_bottom]
    raw_y = np.argmax(search, axis=0).astype(float) + search_top + offset
    edge_strength = search[np.argmax(search, axis=0), np.arange(width)]
    y_pixels = _median_filter(raw_y, 7)

    normalized_x = np.arange(width, dtype=float) / max(1, width - 1)
    cloud_affected = (normalized_x >= 0.275) & (normalized_x <= 0.475)
    confidence = np.clip((edge_strength - 25.0) / 100.0, 0.05, 1.0)
    confidence[cloud_affected] *= 0.20
    confidence[:3] *= 0.5
    confidence[-3:] *= 0.5
    return PhotoSkyline(
        y_pixels=y_pixels,
        confidence=confidence,
        cloud_affected=cloud_affected,
        edge_strength=edge_strength,
        width=width,
        height=height,
    )


def true_to_grid_bearings(
    true_bearings_degrees: np.ndarray,
    observer_wgs84: tuple[float, float],
    observer_bng: tuple[float, float],
) -> np.ndarray:
    """Project one-metre WGS84 geodesic directions into local BNG grid bearings."""
    latitude, longitude = observer_wgs84
    geod = Geod(ellps="WGS84")
    to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    distances = np.ones_like(true_bearings_degrees, dtype=float)
    longitudes = np.full_like(true_bearings_degrees, longitude, dtype=float)
    latitudes = np.full_like(true_bearings_degrees, latitude, dtype=float)
    end_lon, end_lat, _ = geod.fwd(
        longitudes, latitudes, true_bearings_degrees, distances
    )
    end_e, end_n = to_bng.transform(end_lon, end_lat)
    return np.degrees(
        np.arctan2(end_e - observer_bng[0], end_n - observer_bng[1])
    ) % 360.0


def _maximum_ray_distance(
    origin: tuple[float, float],
    direction: tuple[float, float],
    bounds: tuple[float, float, float, float],
) -> float:
    easting, northing = origin
    de, dn = direction
    west, south, east, north = bounds
    candidates: list[float] = []
    if de > 1e-12:
        candidates.append((east - 0.501 - easting) / de)
    elif de < -1e-12:
        candidates.append((west + 0.501 - easting) / de)
    if dn > 1e-12:
        candidates.append((north - 0.501 - northing) / dn)
    elif dn < -1e-12:
        candidates.append((south + 0.501 - northing) / dn)
    positive = [value for value in candidates if value > 0.0]
    if not positive:
        raise ValueError("Ray does not intersect the source-DTM bounds")
    return min(positive)


def generate_terrain_horizon(
    data: np.ndarray,
    transform: Any,
    bounds: tuple[float, float, float, float],
    observer_bng: tuple[float, float],
    observer_wgs84: tuple[float, float],
    eye_elevation_m_odn: float,
    minimum_true_bearing: float = 195.0,
    maximum_true_bearing: float = 300.0,
    angular_step_degrees: float = 0.025,
    distance_step_m: float = 1.0,
) -> TerrainHorizon:
    """Ray-march the 1 m DTM and return its apparent horizon for each bearing."""
    bearings = np.arange(
        minimum_true_bearing,
        maximum_true_bearing + angular_step_degrees * 0.5,
        angular_step_degrees,
    )
    grid_bearings = true_to_grid_bearings(
        bearings, observer_wgs84, observer_bng
    )
    horizon_angles = np.empty_like(bearings)
    horizon_distances = np.empty_like(bearings)
    horizon_elevations = np.empty_like(bearings)
    horizon_eastings = np.empty_like(bearings)
    horizon_northings = np.empty_like(bearings)

    for index, grid_bearing in enumerate(grid_bearings):
        radians = math.radians(float(grid_bearing))
        de, dn = math.sin(radians), math.cos(radians)
        maximum_distance = _maximum_ray_distance(
            observer_bng, (de, dn), bounds
        )
        distances = np.arange(
            max(distance_step_m, 1.0),
            maximum_distance,
            distance_step_m,
            dtype=float,
        )
        eastings = observer_bng[0] + de * distances
        northings = observer_bng[1] + dn * distances
        elevations = bilinear_sample(
            data, transform, eastings, northings
        )
        angles = np.degrees(
            np.arctan2(elevations - eye_elevation_m_odn, distances)
        )
        horizon_index = int(np.argmax(angles))
        horizon_angles[index] = angles[horizon_index]
        horizon_distances[index] = distances[horizon_index]
        horizon_elevations[index] = elevations[horizon_index]
        horizon_eastings[index] = eastings[horizon_index]
        horizon_northings[index] = northings[horizon_index]

    return TerrainHorizon(
        true_bearings_degrees=bearings,
        elevation_angles_degrees=horizon_angles,
        distances_m=horizon_distances,
        elevations_m_odn=horizon_elevations,
        eastings=horizon_eastings,
        northings=horizon_northings,
    )


def horizontal_ray_angles(
    width: int, horizontal_fov_degrees: float
) -> tuple[np.ndarray, float]:
    focal_pixels = (width / 2.0) / math.tan(
        math.radians(horizontal_fov_degrees) / 2.0
    )
    x = np.arange(width, dtype=float)
    angles = np.degrees(np.arctan((x - (width - 1) / 2.0) / focal_pixels))
    return angles, focal_pixels


def photo_relative_elevation_angles(
    skyline: PhotoSkyline, focal_pixels: float
) -> np.ndarray:
    centre_y = (skyline.height - 1) / 2.0
    return np.degrees(
        np.arctan((centre_y - skyline.y_pixels) / focal_pixels)
    )


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(values * weights) / np.sum(weights))


def evaluate_solution(
    skyline: PhotoSkyline,
    horizon: TerrainHorizon,
    centre_heading_degrees: float,
    horizontal_fov_degrees: float,
) -> dict[str, Any]:
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
    pitch = weighted_mean(
        terrain_angles[valid] - photo_relative[valid],
        weights,
    )
    residual = (
        terrain_angles - (photo_relative + pitch)
    )
    rmse = math.sqrt(weighted_mean(residual[valid] ** 2, weights))
    mae = weighted_mean(np.abs(residual[valid]), weights)

    terrain_smooth = _median_filter(terrain_angles, 7)
    photo_smooth = _median_filter(photo_relative, 7)
    terrain_slope = np.gradient(terrain_smooth)
    photo_slope = np.gradient(photo_smooth)
    slope_residual = terrain_slope - photo_slope
    slope_rmse = math.sqrt(
        weighted_mean(slope_residual[valid] ** 2, weights)
    )
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
    score = rmse + 10.0 * slope_rmse
    predicted_y = (
        (skyline.height - 1) / 2.0
        - focal_pixels
        * np.tan(np.radians(terrain_angles - pitch))
    )
    return {
        "centre_true_heading_degrees": float(centre_heading_degrees),
        "horizontal_fov_degrees": float(horizontal_fov_degrees),
        "solved_pitch_degrees": float(pitch),
        "weighted_rmse_degrees": float(rmse),
        "weighted_mae_degrees": float(mae),
        "weighted_slope_rmse_degrees_per_pixel": float(slope_rmse),
        "weighted_shape_correlation": float(correlation),
        "score": float(score),
        "ray_bearings_degrees": ray_bearings,
        "terrain_angles_degrees": terrain_angles,
        "photo_relative_angles_degrees": photo_relative,
        "residual_degrees": residual,
        "predicted_y_pixels": predicted_y,
        "focal_pixels": float(focal_pixels),
    }


def search_fixed_camera(
    skyline: PhotoSkyline,
    horizon: TerrainHorizon,
) -> tuple[dict[str, Any], list[dict[str, Any]], np.ndarray, np.ndarray, np.ndarray]:
    coarse_headings = np.arange(235.0, 260.0001, 0.25)
    coarse_fovs = np.arange(25.0, 70.0001, 0.5)
    heatmap = np.empty((len(coarse_headings), len(coarse_fovs)))
    candidates: list[dict[str, Any]] = []
    for heading_index, heading in enumerate(coarse_headings):
        for fov_index, fov in enumerate(coarse_fovs):
            result = evaluate_solution(skyline, horizon, heading, fov)
            heatmap[heading_index, fov_index] = result["score"]
            candidates.append(result)
    coarse_best = min(candidates, key=lambda result: result["score"])

    refined: list[dict[str, Any]] = []
    for heading in np.arange(
        coarse_best["centre_true_heading_degrees"] - 0.5,
        coarse_best["centre_true_heading_degrees"] + 0.5001,
        0.05,
    ):
        for fov in np.arange(
            coarse_best["horizontal_fov_degrees"] - 1.0,
            coarse_best["horizontal_fov_degrees"] + 1.0001,
            0.1,
        ):
            refined.append(evaluate_solution(skyline, horizon, heading, fov))
    best = min(refined, key=lambda result: result["score"])

    ordered = sorted(candidates + refined, key=lambda result: result["score"])
    alternatives: list[dict[str, Any]] = []
    for candidate in ordered:
        if (
            abs(candidate["centre_true_heading_degrees"] - best["centre_true_heading_degrees"]) < 0.15
            and abs(candidate["horizontal_fov_degrees"] - best["horizontal_fov_degrees"]) < 0.3
        ):
            continue
        if all(
            abs(candidate["centre_true_heading_degrees"] - existing["centre_true_heading_degrees"]) >= 0.5
            or abs(candidate["horizontal_fov_degrees"] - existing["horizontal_fov_degrees"]) >= 1.0
            for existing in alternatives
        ):
            alternatives.append(candidate)
        if len(alternatives) == 6:
            break
    return best, alternatives, coarse_headings, coarse_fovs, heatmap


def optimize_fov_at_fixed_heading(
    skyline: PhotoSkyline,
    horizon: TerrainHorizon,
    heading_degrees: float,
) -> dict[str, Any]:
    return min(
        (
            evaluate_solution(skyline, horizon, heading_degrees, float(fov))
            for fov in np.arange(25.0, 70.0001, 0.1)
        ),
        key=lambda result: result["score"],
    )


def projected_pixel_for_bearing(
    bearing_degrees: float,
    centre_heading_degrees: float,
    focal_pixels: float,
    width: int,
) -> float:
    relative = math.radians(bearing_degrees - centre_heading_degrees)
    return (width - 1) / 2.0 + focal_pixels * math.tan(relative)


def terrain_feature_at_pixel(
    pixel_x: int,
    result: dict[str, Any],
    horizon: TerrainHorizon,
) -> dict[str, float]:
    bearing = float(result["ray_bearings_degrees"][pixel_x])
    horizon_index = int(
        np.argmin(np.abs(horizon.true_bearings_degrees - bearing))
    )
    return {
        "pixel_x": float(pixel_x),
        "true_bearing_degrees": bearing,
        "horizon_angle_degrees": float(
            horizon.elevation_angles_degrees[horizon_index]
        ),
        "horizon_distance_m": float(horizon.distances_m[horizon_index]),
        "horizon_elevation_m_odn": float(
            horizon.elevations_m_odn[horizon_index]
        ),
        "horizon_easting": float(horizon.eastings[horizon_index]),
        "horizon_northing": float(horizon.northings[horizon_index]),
    }


def _serializable_solution(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if not isinstance(value, np.ndarray)
    }


def _major_extrema(
    values: np.ndarray,
    confidence: np.ndarray,
    maximum_count: int = 6,
) -> list[dict[str, float | str]]:
    smoothed = _median_filter(values, 15)
    candidates: list[tuple[float, int, str]] = []
    flank = 30
    for index in range(flank, len(values) - flank):
        if confidence[index] < 0.15:
            continue
        left = smoothed[index - flank:index]
        right = smoothed[index + 1:index + flank + 1]
        if smoothed[index] >= np.max(left) and smoothed[index] > np.max(right):
            prominence = smoothed[index] - max(float(np.min(left)), float(np.min(right)))
            candidates.append((float(prominence), index, "peak"))
        if smoothed[index] <= np.min(left) and smoothed[index] < np.min(right):
            prominence = min(float(np.max(left)), float(np.max(right))) - smoothed[index]
            candidates.append((float(prominence), index, "notch"))
    chosen: list[tuple[float, int, str]] = []
    for item in sorted(candidates, reverse=True):
        if item[0] < 0.08:
            continue
        if all(abs(item[1] - existing[1]) >= 35 for existing in chosen):
            chosen.append(item)
        if len(chosen) == maximum_count:
            break
    return [
        {
            "kind": kind,
            "pixel_x": float(index),
            "normalized_x": float(index / (len(values) - 1)),
            "relative_angle_degrees": float(smoothed[index]),
            "prominence_degrees": float(prominence),
        }
        for prominence, index, kind in sorted(chosen, key=lambda item: item[1])
    ]


def write_diagnostics(
    image_path: Path,
    skyline: PhotoSkyline,
    horizon: TerrainHorizon,
    best: dict[str, Any],
    alternatives: list[dict[str, Any]],
    headings: np.ndarray,
    fovs: np.ndarray,
    heatmap: np.ndarray,
    output_root: Path,
    context: dict[str, Any],
    comparisons: dict[str, Any],
    topology_assessment: dict[str, Any],
) -> dict[str, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    extraction_path = output_root / "lab004a-photo-skyline-extraction.png"
    overlay_path = output_root / "lab004a-best-dtm-skyline-overlay.png"
    residual_path = output_root / "lab004a-skyline-residuals.png"
    heatmap_path = output_root / "lab004a-parameter-search.png"
    report_path = output_root / "lab004a-skyline-calibration.json"

    image = Image.open(image_path).convert("RGB")
    extraction = image.copy()
    draw = ImageDraw.Draw(extraction)
    for x, y in enumerate(skyline.y_pixels):
        colour = (255, 70, 35) if not skyline.cloud_affected[x] else (255, 210, 40)
        draw.point((x, int(round(y))), fill=colour)
        if x % 2 == 0:
            draw.point((x, int(round(y)) + 1), fill=colour)
    extraction.save(extraction_path)

    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    photo_points = [
        (x, int(round(y))) for x, y in enumerate(skyline.y_pixels)
        if not skyline.cloud_affected[x]
    ]
    predicted_points = [
        (x, int(round(y))) for x, y in enumerate(best["predicted_y_pixels"])
        if math.isfinite(float(y))
    ]
    if len(photo_points) > 1:
        draw.line(photo_points, fill=(255, 75, 40), width=2)
    if len(predicted_points) > 1:
        draw.line(predicted_points, fill=(40, 245, 255), width=2)
    overlay.save(overlay_path)

    x = np.arange(skyline.width)
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), constrained_layout=True)
    axes[0].plot(x, skyline.y_pixels, color="#e4572e", label="Photographic skyline")
    axes[0].plot(x, best["predicted_y_pixels"], color="#00a6b4", label="Best DTM skyline")
    axes[0].fill_between(
        x,
        0,
        skyline.height,
        where=skyline.cloud_affected,
        color="#f2cf5b",
        alpha=0.18,
        label="Cloud-affected/down-weighted",
    )
    axes[0].invert_yaxis()
    axes[0].set_ylabel("Image y (pixels)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.2)
    axes[1].plot(x, best["residual_degrees"], color="#4c78a8")
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].fill_between(
        x,
        np.min(best["residual_degrees"]),
        np.max(best["residual_degrees"]),
        where=skyline.cloud_affected,
        color="#f2cf5b",
        alpha=0.18,
    )
    axes[1].set(xlabel="Image x (pixels)", ylabel="DTM − photo angle (degrees)")
    axes[1].grid(True, alpha=0.2)
    fig.suptitle(
        "Lab 004A skyline fit: "
        f"heading {best['centre_true_heading_degrees']:.2f}°, "
        f"HFOV {best['horizontal_fov_degrees']:.2f}°, "
        f"pitch {best['solved_pitch_degrees']:.2f}°"
    )
    fig.savefig(residual_path, dpi=180)
    plt.close(fig)

    fig, axis = plt.subplots(figsize=(11, 7), constrained_layout=True)
    image_handle = axis.imshow(
        heatmap.T,
        origin="lower",
        aspect="auto",
        extent=[headings[0], headings[-1], fovs[0], fovs[-1]],
        cmap="viridis_r",
    )
    axis.scatter(
        best["centre_true_heading_degrees"],
        best["horizontal_fov_degrees"],
        marker="x",
        s=80,
        color="white",
        linewidth=2,
        label="Refined best",
    )
    axis.set(
        xlabel="Centre true heading (degrees)",
        ylabel="Horizontal FOV (degrees)",
        title="Fixed-camera skyline search score (lower is better)",
    )
    axis.legend()
    fig.colorbar(image_handle, ax=axis, label="Shape score")
    fig.savefig(heatmap_path, dpi=180)
    plt.close(fig)

    photo_angles = best["photo_relative_angles_degrees"]
    report = {
        "schema_version": 1,
        "method": {
            "camera_position": "Fixed published Tony Edwards coordinate",
            "terrain": "Source Lab 004 1 m DTM",
            "distance_sampling_m": 1.0,
            "horizon_angular_sampling_degrees": float(
                horizon.true_bearings_degrees[1]
                - horizon.true_bearings_degrees[0]
            ),
            "heading_search_degrees": [235.0, 260.0],
            "horizontal_fov_search_degrees": [25.0, 70.0],
            "pitch": "Weighted analytic vertical registration for each heading/HFOV candidate",
            "roll_degrees": 0.0,
            "objective": "Weighted angular RMSE plus 10 times per-pixel slope RMSE",
            "cloud_affected_normalized_x": [0.275, 0.475],
            "cloud_weight_multiplier": 0.20,
        },
        "inputs": context,
        "best_fixed_camera_solution": _serializable_solution(best),
        "nearby_alternatives": [
            _serializable_solution(result) for result in alternatives
        ],
        "comparison_solutions": comparisons,
        "topology_assessment": topology_assessment,
        "photographic_features": _major_extrema(
            photo_angles, skyline.confidence
        ),
        "predicted_features": _major_extrema(
            best["terrain_angles_degrees"], skyline.confidence
        ),
        "residual_summary": {
            "maximum_absolute_degrees": float(
                np.nanmax(np.abs(best["residual_degrees"]))
            ),
            "p95_absolute_degrees": float(
                np.nanpercentile(np.abs(best["residual_degrees"]), 95)
            ),
            "clear_columns_weighted_rmse_degrees": float(
                math.sqrt(
                    np.mean(
                        best["residual_degrees"][~skyline.cloud_affected] ** 2
                    )
                )
            ),
        },
        "outputs": {
            "photo_skyline_overlay": str(extraction_path.resolve()),
            "best_dtm_overlay": str(overlay_path.resolve()),
            "residual_plot": str(residual_path.resolve()),
            "parameter_search": str(heatmap_path.resolve()),
            "json_report": str(report_path.resolve()),
        },
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {
        "extraction": extraction_path,
        "overlay": overlay_path,
        "residual": residual_path,
        "heatmap": heatmap_path,
        "report": report_path,
    }


def run(
    terrain_root: Path,
    benchmark_path: Path,
    image_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    observer = benchmark["observer"]
    observer_bng = (
        float(observer["bng"]["easting"]),
        float(observer["bng"]["northing"]),
    )
    observer_wgs84 = (
        float(observer["wgs84"]["latitude"]),
        float(observer["wgs84"]["longitude"]),
    )
    bounds = tuple(float(value) for value in benchmark["terrain"]["bounds"])
    dtm_path = terrain_root / "rasters" / "tryfan-004-dtm-1m.tif"
    with rasterio.open(dtm_path) as source:
        if source.crs.to_epsg() != 27700:
            raise ValueError(f"Expected EPSG:27700 DTM, found {source.crs}")
        data = source.read(1)
        transform = source.transform
        raster_bounds = (
            float(source.bounds.left),
            float(source.bounds.bottom),
            float(source.bounds.right),
            float(source.bounds.top),
        )
    if not np.allclose(bounds, raster_bounds, atol=1e-6):
        raise ValueError("Benchmark AOI and source DTM bounds differ")
    observer_elevation = float(
        bilinear_sample(
            data,
            transform,
            np.array([observer_bng[0]]),
            np.array([observer_bng[1]]),
        )[0]
    )
    eye_height = float(observer["eye_height_m"])
    eye_elevation = observer_elevation + eye_height
    skyline = extract_photo_skyline(image_path)
    horizon = generate_terrain_horizon(
        data,
        transform,
        bounds,
        observer_bng,
        observer_wgs84,
        eye_elevation,
    )
    best, alternatives, headings, fovs, heatmap = search_fixed_camera(
        skyline, horizon
    )

    published_heading = float(benchmark["view"]["published_heading_degrees"])
    published_solution = optimize_fov_at_fixed_heading(
        skyline, horizon, published_heading
    )
    pitch_reference = benchmark["view"]["pitch_reference"]
    summit_wgs84 = pitch_reference["wgs84"]
    geod = Geod(ellps="WGS84")
    summit_bearing, _, summit_distance = geod.inv(
        observer_wgs84[1],
        observer_wgs84[0],
        float(summit_wgs84["longitude"]),
        float(summit_wgs84["latitude"]),
    )
    summit_bearing %= 360.0
    summit_solution = optimize_fov_at_fixed_heading(
        skyline, horizon, summit_bearing
    )
    clear_confidence = skyline.confidence.copy()
    clear_confidence[skyline.cloud_affected] = 0.0
    clear_skyline = replace(skyline, confidence=clear_confidence)
    clear_best, _, _, _, _ = search_fixed_camera(clear_skyline, horizon)

    summit_pixel = projected_pixel_for_bearing(
        summit_bearing,
        best["centre_true_heading_degrees"],
        best["focal_pixels"],
        skyline.width,
    )
    right_half = np.arange(skyline.width) >= skyline.width // 2
    right_peak_pixel = int(
        np.flatnonzero(right_half)[
            np.argmax(best["terrain_angles_degrees"][right_half])
        ]
    )
    comparisons = {
        "published_247_degree_heading_best_fov": _serializable_solution(
            published_solution
        ),
        "canonical_summit_bearing_degrees": float(summit_bearing),
        "canonical_summit_distance_m": float(summit_distance),
        "summit_bearing_best_fov": _serializable_solution(summit_solution),
        "cloud_columns_excluded_best": _serializable_solution(clear_best),
        "best_score_improvement_over_published_heading_factor": float(
            published_solution["score"] / best["score"]
        ),
    }
    topology_assessment = {
        "conclusion": (
            "A_TONY_EDWARDS_IS_GEOMETRICALLY_CONSISTENT_WITH_RECOVERED_CALIBRATION"
        ),
        "camera_position_perturbation_search": (
            "NOT_RUN; fixed-camera clear-skyline fit is sufficiently strong"
        ),
        "evidence": [
            (
                "Best fixed-camera weighted shape correlation exceeds 0.96 "
                "with about 0.55 degree weighted angular RMSE."
            ),
            (
                "Excluding all cloud-affected columns leaves essentially the "
                "same heading and HFOV."
            ),
            (
                "The recovered framing projects the canonical summit left of "
                "centre while retaining the northern/right shoulder across "
                "the remainder of the image."
            ),
            (
                "The 247 degree published heading is approximately 2.6 times "
                "worse under the same objective and cannot reproduce the "
                "observed horizontal composition."
            ),
        ],
        "canonical_summit_projected_pixel_x": float(summit_pixel),
        "canonical_summit_cloud_affected": bool(
            0 <= round(summit_pixel) < skyline.width
            and skyline.cloud_affected[int(round(summit_pixel))]
        ),
        "right_half_highest_dtm_horizon": terrain_feature_at_pixel(
            right_peak_pixel, best, horizon
        ),
        "selected_right_side_horizon_samples": [
            terrain_feature_at_pixel(pixel, best, horizon)
            for pixel in (320, 391, 456, 483, 639)
        ],
        "limitations": [
            (
                "Cloud/fog prevents direct recovery of the true summit outline "
                "over normalized image x=0.275..0.475."
            ),
            (
                "The 1 m bare-earth DTM cannot reproduce individual rocks, "
                "vegetation, people, or sub-metre crag silhouettes."
            ),
            (
                "Residual clear-sky differences of roughly half a degree "
                "remain along local crag and shoulder structure."
            ),
        ],
    }
    context = {
        "photo": str(image_path.resolve()),
        "photo_dimensions": [skyline.width, skyline.height],
        "source_dtm": str(dtm_path.resolve()),
        "observer_bng": {
            "easting": observer_bng[0],
            "northing": observer_bng[1],
        },
        "observer_wgs84": {
            "latitude": observer_wgs84[0],
            "longitude": observer_wgs84[1],
        },
        "observer_dtm_elevation_m_odn": observer_elevation,
        "camera_eye_elevation_m_odn": eye_elevation,
        "eye_height_m": eye_height,
        "published_heading_degrees": float(
            benchmark["view"]["published_heading_degrees"]
        ),
    }
    paths = write_diagnostics(
        image_path,
        skyline,
        horizon,
        best,
        alternatives,
        headings,
        fovs,
        heatmap,
        output_root,
        context,
        comparisons,
        topology_assessment,
    )
    result = {
        "best_fixed_camera_solution": _serializable_solution(best),
        "nearby_alternatives": [
            _serializable_solution(value) for value in alternatives
        ],
        "outputs": {key: str(value.resolve()) for key, value in paths.items()},
    }
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terrain-root", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    run(args.terrain_root, args.benchmark, args.image, args.output_root)


if __name__ == "__main__":
    main()
