"""Fit a bounded Lab 004B camera against the canonical Unreal Landscape R16.

Lab 004A is immutable input. Generated diagnostics are written outside Git.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer

from calibrate_photo_skyline import (
    extract_photo_skyline,
    generate_terrain_horizon,
    true_to_grid_bearings,
)
from observer_geometry import (
    bng_to_unreal_xy_cm,
    geographic_heading_to_unreal_yaw_degrees,
)
from photo_fit import (
    bound_reached,
    decode_landscape_r16,
    evaluate_camera,
    inclusive_values,
    sample_surface,
    serializable_metrics,
    solve_bounded_pitch,
)


def _resolve_repo_path(config_path: Path, convention: str) -> Path:
    path = Path(convention)
    if path.is_absolute():
        return path.resolve()
    return (config_path.resolve().parents[2] / path).resolve()


def _absolute_bounds(initial: float, relative: list[float]) -> tuple[float, float]:
    return initial + float(relative[0]), initial + float(relative[1])


def _best_for_horizon(
    skyline: Any,
    horizon: Any,
    headings: np.ndarray,
    fovs: np.ndarray,
    pitch_bounds: tuple[float, float],
) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for heading in headings:
        for fov in fovs:
            result = solve_bounded_pitch(
                skyline, horizon, float(heading), float(fov), pitch_bounds
            )
            if best is None or result["score"] < best["score"]:
                best = result
    if best is None:
        raise RuntimeError("Camera search produced no candidates")
    return best


def _position_grid(
    easting_bounds: tuple[float, float],
    northing_bounds: tuple[float, float],
    step: float,
) -> list[tuple[float, float]]:
    return [
        (float(easting), float(northing))
        for easting in inclusive_values(*easting_bounds, step)
        for northing in inclusive_values(*northing_bounds, step)
    ]


def _clipped_bounds(
    centre: float,
    radius: float,
    absolute: tuple[float, float],
) -> tuple[float, float]:
    return max(absolute[0], centre - radius), min(absolute[1], centre + radius)


def _with_position(
    result: dict[str, Any], easting: float, northing: float, terrain: float
) -> dict[str, Any]:
    result = dict(result)
    result.update(
        camera_bng_easting=float(easting),
        camera_bng_northing=float(northing),
        camera_terrain_elevation_m_odn=float(terrain),
    )
    return result


def _plot_diagnostics(
    image_path: Path,
    skyline: Any,
    initial: dict[str, Any],
    fitted: dict[str, Any],
    output_root: Path,
) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    overlay_path = output_root / "lab004b-before-after-skyline.png"
    residual_path = output_root / "lab004b-before-after-residuals.png"
    image = Image.open(image_path).convert("RGB")
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    draw.line(
        [(x, int(round(y))) for x, y in enumerate(skyline.y_pixels)],
        fill=(255, 90, 35), width=2,
    )
    draw.line(
        [(x, int(round(y))) for x, y in enumerate(initial["predicted_y_pixels"])
         if math.isfinite(float(y))],
        fill=(60, 170, 255), width=2,
    )
    draw.line(
        [(x, int(round(y))) for x, y in enumerate(fitted["predicted_y_pixels"])
         if math.isfinite(float(y))],
        fill=(55, 255, 145), width=2,
    )
    overlay.save(overlay_path)

    x = np.arange(skyline.width)
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), constrained_layout=True)
    axes[0].plot(x, skyline.y_pixels, color="#e4572e", label="Photograph")
    axes[0].plot(x, initial["predicted_y_pixels"], color="#4c78a8", label="004A")
    axes[0].plot(x, fitted["predicted_y_pixels"], color="#2ca25f", label="004B fit")
    axes[0].fill_between(
        x, 0, skyline.height, where=skyline.cloud_affected,
        color="#f2cf5b", alpha=0.15, label="Cloud-affected/down-weighted"
    )
    axes[0].invert_yaxis()
    axes[0].set_ylabel("Image y (pixels)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.2)
    axes[1].plot(x, initial["pixel_residuals"], color="#4c78a8", label="004A")
    axes[1].plot(x, fitted["pixel_residuals"], color="#2ca25f", label="004B")
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].set(xlabel="Image x (pixels)", ylabel="Predicted - photo y (pixels)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.2)
    fig.suptitle("Lab 004B bounded alignment - canonical Unreal R16")
    fig.savefig(residual_path, dpi=180)
    plt.close(fig)
    return {
        "before_after_overlay": str(overlay_path.resolve()),
        "before_after_residuals": str(residual_path.resolve()),
    }


def run(config_path: Path, output_root: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    initial = config["lab004a"]["immutable_snapshot"]
    lab004a_path = config_path.with_name(config["lab004a"]["configuration"])
    lab004a = json.loads(lab004a_path.read_text(encoding="utf-8"))["camera"]
    if initial != lab004a:
        raise ValueError(
            "Lab 004B immutable snapshot differs from canonical Lab 004A configuration"
        )

    image_path = _resolve_repo_path(
        config_path, config["inputs"]["reference_image_path_convention"]
    )
    manifest_path = _resolve_repo_path(
        config_path, config["inputs"]["landscape_manifest_path_convention"]
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bounds = tuple(float(value) for value in manifest["source_aoi_bounds"])
    surface_manifest = manifest["surfaces"][config["inputs"]["surface"]]
    output = surface_manifest["output"]
    r16_path = manifest_path.parent / "heightmaps" / output["files"]["r16"]["path"]
    encoding = manifest["height_encoding"]
    surface = decode_landscape_r16(
        r16_path,
        width=int(output["width"]),
        height=int(output["height"]),
        bounds=bounds,
        vertical_origin_m_odn=float(encoding["vertical_origin_m_odn"]),
        z_scale=float(encoding["z_scale"]),
        expected_sha256=config["inputs"]["expected_r16_sha256"],
    )
    skyline = extract_photo_skyline(image_path)

    fit = config["fit"]
    relative = fit["bounds_relative_to_lab004a"]
    initial_e = float(initial["bng"]["easting"])
    initial_n = float(initial["bng"]["northing"])
    initial_heading = float(initial["applied_true_heading_degrees"])
    initial_pitch = float(initial["rotation_degrees"]["pitch"])
    initial_fov = float(initial["horizontal_fov_degrees"])
    e_bounds = _absolute_bounds(initial_e, relative["easting_m"])
    n_bounds = _absolute_bounds(initial_n, relative["northing_m"])
    heading_bounds = _absolute_bounds(initial_heading, relative["heading_degrees"])
    pitch_bounds = _absolute_bounds(initial_pitch, relative["pitch_degrees"])
    fov_bounds = _absolute_bounds(initial_fov, relative["horizontal_fov_degrees"])
    eye_height = float(fit["fixed"]["eye_height_m"])
    to_wgs84 = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

    horizon_cache: dict[tuple[float, float], tuple[Any, float, tuple[float, float]]] = {}
    minimum_bearing = heading_bounds[0] - fov_bounds[1] / 2.0 - 1.0
    maximum_bearing = heading_bounds[1] + fov_bounds[1] / 2.0 + 1.0

    def horizon_at(easting: float, northing: float) -> tuple[Any, float, tuple[float, float]]:
        key = round(easting, 6), round(northing, 6)
        if key in horizon_cache:
            return horizon_cache[key]
        longitude, latitude = to_wgs84.transform(easting, northing)
        terrain = sample_surface(surface, easting, northing)
        horizon = generate_terrain_horizon(
            surface.elevations_m_odn, surface.transform, bounds,
            (easting, northing), (latitude, longitude), terrain + eye_height,
            minimum_true_bearing=minimum_bearing,
            maximum_true_bearing=maximum_bearing,
            angular_step_degrees=float(fit["horizon_angular_step_degrees"]),
            distance_step_m=float(fit["horizon_distance_step_m"]),
        )
        horizon_cache[key] = horizon, terrain, (latitude, longitude)
        return horizon_cache[key]

    initial_horizon, initial_terrain, _ = horizon_at(initial_e, initial_n)
    initial_metrics = _with_position(
        evaluate_camera(
            skyline, initial_horizon, initial_heading, initial_fov, initial_pitch
        ),
        initial_e, initial_n, initial_terrain,
    )

    coarse_headings = inclusive_values(
        *heading_bounds, float(fit["coarse_heading_step_degrees"])
    )
    coarse_fovs = inclusive_values(*fov_bounds, float(fit["coarse_fov_step_degrees"]))
    fixed_coarse = _best_for_horizon(
        skyline, initial_horizon, coarse_headings, coarse_fovs, pitch_bounds
    )
    fixed_position_best = _with_position(
        _best_for_horizon(
            skyline,
            initial_horizon,
            inclusive_values(
                *_clipped_bounds(
                    fixed_coarse["centre_true_heading_degrees"], 0.3, heading_bounds
                ),
                0.01,
            ),
            inclusive_values(
                *_clipped_bounds(
                    fixed_coarse["horizontal_fov_degrees"], 0.6, fov_bounds
                ),
                0.025,
            ),
            pitch_bounds,
        ),
        initial_e,
        initial_n,
        initial_terrain,
    )
    coarse_best: dict[str, Any] | None = None
    for easting, northing in _position_grid(
        e_bounds, n_bounds, float(fit["coarse_position_step_m"])
    ):
        horizon, terrain, _ = horizon_at(easting, northing)
        result = _with_position(
            _best_for_horizon(
                skyline, horizon, coarse_headings, coarse_fovs, pitch_bounds
            ),
            easting, northing, terrain,
        )
        if coarse_best is None or result["score"] < coarse_best["score"]:
            coarse_best = result
    assert coarse_best is not None

    refined_e_bounds = _clipped_bounds(
        coarse_best["camera_bng_easting"],
        float(fit["coarse_position_step_m"]), e_bounds,
    )
    refined_n_bounds = _clipped_bounds(
        coarse_best["camera_bng_northing"],
        float(fit["coarse_position_step_m"]), n_bounds,
    )
    refined_headings = inclusive_values(
        *_clipped_bounds(coarse_best["centre_true_heading_degrees"], 0.4, heading_bounds),
        float(fit["refined_heading_step_degrees"]),
    )
    refined_fovs = inclusive_values(
        *_clipped_bounds(coarse_best["horizontal_fov_degrees"], 0.8, fov_bounds),
        float(fit["refined_fov_step_degrees"]),
    )
    fitted: dict[str, Any] | None = None
    for easting, northing in _position_grid(
        refined_e_bounds, refined_n_bounds, float(fit["refined_position_step_m"])
    ):
        horizon, terrain, _ = horizon_at(easting, northing)
        result = _with_position(
            _best_for_horizon(
                skyline, horizon, refined_headings, refined_fovs, pitch_bounds
            ),
            easting, northing, terrain,
        )
        if fitted is None or result["score"] < fitted["score"]:
            fitted = result
    assert fitted is not None

    final_headings = inclusive_values(
        *_clipped_bounds(fitted["centre_true_heading_degrees"], 0.08, heading_bounds),
        0.01,
    )
    final_fovs = inclusive_values(
        *_clipped_bounds(fitted["horizontal_fov_degrees"], 0.15, fov_bounds),
        0.025,
    )
    for easting, northing in _position_grid(
        _clipped_bounds(fitted["camera_bng_easting"], 1.0, e_bounds),
        _clipped_bounds(fitted["camera_bng_northing"], 1.0, n_bounds),
        0.5,
    ):
        horizon, terrain, _ = horizon_at(easting, northing)
        result = _with_position(
            _best_for_horizon(
                skyline, horizon, final_headings, final_fovs, pitch_bounds
            ),
            easting, northing, terrain,
        )
        if result["score"] < fitted["score"]:
            fitted = result

    fitted_e = float(fitted["camera_bng_easting"])
    fitted_n = float(fitted["camera_bng_northing"])
    fitted_horizon, fitted_terrain, fitted_wgs84 = horizon_at(fitted_e, fitted_n)
    fitted_heading = float(fitted["centre_true_heading_degrees"])
    fitted_fov = float(fitted["horizontal_fov_degrees"])
    fitted_pitch = float(fitted["pitch_degrees"])
    pitch_solution = solve_bounded_pitch(
        skyline, fitted_horizon, fitted_heading, fitted_fov, pitch_bounds
    )
    fitted = _with_position(
        evaluate_camera(
            skyline, fitted_horizon, fitted_heading, fitted_fov, fitted_pitch
        ) | {
            "unconstrained_solved_pitch_degrees": float(
                pitch_solution["unconstrained_solved_pitch_degrees"]
            ),
            "pitch_bound_reached": bool(pitch_solution["pitch_bound_reached"]),
        },
        fitted_e, fitted_n, fitted_terrain,
    )

    grid_bearing = float(
        true_to_grid_bearings(
            np.array([fitted_heading]), fitted_wgs84, (fitted_e, fitted_n)
        )[0]
    )
    unreal_yaw = geographic_heading_to_unreal_yaw_degrees(grid_bearing)
    origin = manifest["coordinate_frame"]["local_origin_bng"]
    x_cm, y_cm = bng_to_unreal_xy_cm(
        fitted_e, fitted_n, float(origin["easting"]), float(origin["northing"])
    )
    z_cm = (fitted_terrain + eye_height - float(origin["elevation_m_odn"])) * 100.0

    delta_e = fitted_e - initial_e
    delta_n = fitted_n - initial_n
    position_delta = math.hypot(delta_e, delta_n)
    deltas = {
        "easting_m": delta_e,
        "northing_m": delta_n,
        "horizontal_position_m": position_delta,
        "vertical_eye_position_m": fitted_terrain - initial_terrain,
        "true_heading_degrees": fitted_heading - initial_heading,
        "pitch_degrees": fitted_pitch - initial_pitch,
        "horizontal_fov_degrees": fitted_fov - initial_fov,
    }
    bound_flags = {
        "easting": bound_reached(fitted_e, e_bounds, 0.25),
        "northing": bound_reached(fitted_n, n_bounds, 0.25),
        "heading": bound_reached(fitted_heading, heading_bounds, 0.005),
        "pitch": bound_reached(fitted_pitch, pitch_bounds, 0.005),
        "horizontal_fov": bound_reached(fitted_fov, fov_bounds, 0.0125),
    }
    thresholds = fit["classification_thresholds"]
    if any(bound_flags.values()):
        classification = "C_BOUND_LIMITED_REQUIRES_FURTHER_INVESTIGATION"
    elif (
        position_delta <= float(thresholds["A_tiny_position_delta_m"])
        and abs(deltas["true_heading_degrees"])
        <= float(thresholds["A_tiny_heading_delta_degrees"])
        and abs(deltas["pitch_degrees"])
        <= float(thresholds["A_tiny_pitch_delta_degrees"])
        and abs(deltas["horizontal_fov_degrees"])
        <= float(thresholds["A_tiny_hfov_delta_degrees"])
    ):
        classification = "A_TINY_CORRECTION_SUPPORTS_METADATA_CALIBRATION_UNCERTAINTY"
    else:
        classification = "B_MODERATE_PLAUSIBLE_PHOTOGRAPH_METADATA_UNCERTAINTY"

    outputs = _plot_diagnostics(image_path, skyline, initial_metrics, fitted, output_root)
    initial_serial = serializable_metrics(initial_metrics)
    fitted_serial = serializable_metrics(fitted)
    improvement = {
        "score_absolute": initial_metrics["score"] - fitted["score"],
        "score_percent": (initial_metrics["score"] - fitted["score"]) / initial_metrics["score"] * 100.0,
        "angular_rmse_degrees_absolute": initial_metrics["weighted_rmse_degrees"] - fitted["weighted_rmse_degrees"],
        "angular_rmse_percent": (initial_metrics["weighted_rmse_degrees"] - fitted["weighted_rmse_degrees"]) / initial_metrics["weighted_rmse_degrees"] * 100.0,
        "pixel_rmse_absolute": initial_metrics["weighted_rmse_pixels"] - fitted["weighted_rmse_pixels"],
        "pixel_rmse_percent": (initial_metrics["weighted_rmse_pixels"] - fitted["weighted_rmse_pixels"]) / initial_metrics["weighted_rmse_pixels"] * 100.0,
    }
    report = {
        "schema_version": 1,
        "purpose": config["purpose"],
        "inputs": {
            "configuration": str(config_path),
            "lab004a_configuration": str(lab004a_path),
            "reference_image": str(image_path),
            "landscape_manifest": str(manifest_path),
            "canonical_r16": str(r16_path.resolve()),
            "canonical_r16_sha256": surface.sha256,
            "landscape_vertex_spacing_m": surface.spacing_m,
        },
        "provenance_and_uncertainty": {
            "camera_coordinate": "Published Geograph marker transformed WGS84 to BNG; not independently surveyed.",
            "lab004a_heading_pitch_hfov": "Recovered from the source 1 m DTM skyline with camera XY fixed at the published coordinate.",
            "eye_height": "Explicit 1.70 m assumption; no tripod or optical-height metadata.",
            "terrain": "Final decoded 3025-vertex little-endian R16 imported by Unreal, with manifest SHA-256 verification.",
            "photographic_skyline": "Deterministic bright-sky/dark-terrain edge; cloud-affected x=0.275..0.475 down-weighted to 20 percent.",
        },
        "method": {
            "comparison_surface": "Canonical Unreal DTM R16, not the higher-resolution source GeoTIFF",
            "correspondence": "Full weighted skyline plus skyline slope; no hidden editor points or manual feature dragging",
            "bounds": {
                "easting": e_bounds,
                "northing": n_bounds,
                "true_heading": heading_bounds,
                "pitch": pitch_bounds,
                "horizontal_fov": fov_bounds,
            },
            "bounds_relative_to_lab004a": relative,
            "bounds_rationale": fit["bounds_rationale"],
            "roll_degrees": 0.0,
            "eye_height_m": eye_height,
            "aspect_ratio": fit["fixed"]["aspect_ratio"],
            "horizon_angular_step_degrees": fit["horizon_angular_step_degrees"],
            "horizon_distance_step_m": fit["horizon_distance_step_m"],
            "objective": fit["objective"],
            "candidate_position_count": len(horizon_cache),
            "deterministic": True,
        },
        "lab004a": initial_serial,
        "fixed_position_sensitivity": serializable_metrics(fixed_position_best),
        "lab004b": fitted_serial | {
            "camera_wgs84": {"latitude": fitted_wgs84[0], "longitude": fitted_wgs84[1]},
            "camera_eye_elevation_m_odn": fitted_terrain + eye_height,
            "bng_grid_bearing_degrees": grid_bearing,
            "unreal": {
                "actor_label": config["output"]["camera_actor_label"],
                "location_cm": {"x": x_cm, "y": y_cm, "z": z_cm},
                "rotation_degrees": {"pitch": fitted_pitch, "yaw": unreal_yaw, "roll": 0.0},
                "horizontal_fov_degrees": fitted_fov,
                "aspect_ratio": fit["fixed"]["aspect_ratio"],
                "constrain_aspect_ratio": True,
            },
        },
        "deltas_from_lab004a": deltas,
        "improvement": improvement,
        "bounds_reached": bound_flags,
        "classification": classification,
        "interpretation": "The fitted camera is diagnostic only. Lab 004A remains the canonical geospatial reference.",
        "outputs": outputs,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = output_root / "lab004b-photo-fit.json"
    report["outputs"]["json_report"] = str(report_path.resolve())
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": classification,
        "lab004a": initial_serial,
        "fixed_position_sensitivity": serializable_metrics(fixed_position_best),
        "lab004b": report["lab004b"],
        "deltas": deltas,
        "improvement": improvement,
        "bounds_reached": bound_flags,
        "outputs": report["outputs"],
    }, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.config, arguments.output_root)


if __name__ == "__main__":
    main()