"""Derive deterministic Lab 005A surface metrics from the validated Unreal R16."""
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
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap

from photo_fit import decode_landscape_r16, sha256_file
from terrain_metrics import (
    aspect_summary,
    detrended_rms_roughness,
    numeric_summary,
    slope_aspect,
    terrain_curvatures,
)

NODATA = -9999.0


def _resolve_repo_path(config_path: Path, convention: str) -> Path:
    path = Path(convention)
    if path.is_absolute():
        return path.resolve()
    return (config_path.resolve().parents[2] / path).resolve()


def _write_raster(path: Path, values: np.ndarray, transform: Any) -> None:
    output = np.where(np.isfinite(values), values, NODATA).astype(np.float32)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=output.shape[1],
        height=output.shape[0],
        count=1,
        dtype="float32",
        crs="EPSG:27700",
        transform=transform,
        nodata=NODATA,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as destination:
        destination.write(output, 1)


def _plot_field(
    values: np.ndarray,
    path: Path,
    extent: tuple[float, float, float, float],
    *,
    title: str,
    label: str,
    cmap: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 8), constrained_layout=True)
    image = axis.imshow(
        values,
        extent=extent,
        origin="upper",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation="nearest",
    )
    axis.set(
        title=title,
        xlabel="BNG easting (m)",
        ylabel="BNG northing (m)",
        aspect="equal",
    )
    figure.colorbar(image, ax=axis, label=label, shrink=0.82)
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _field_location(
    values: np.ndarray,
    spacing: float,
    bounds: tuple[float, float, float, float],
    mode: str,
) -> dict[str, float]:
    finite = np.where(np.isfinite(values), values, np.nan)
    flat_index = int(np.nanargmax(finite) if mode == "max" else np.nanargmin(finite))
    row, column = np.unravel_index(flat_index, values.shape)
    west, _, _, north = bounds
    return {
        "value": float(values[row, column]),
        "easting": float(west + column * spacing),
        "northing": float(north - row * spacing),
        "row": int(row),
        "column": int(column),
    }


def _mask_summary(
    mask: np.ndarray,
    valid: np.ndarray,
    spacing: float,
    bounds: tuple[float, float, float, float],
) -> dict[str, Any]:
    selected = mask & valid
    count = int(np.count_nonzero(selected))
    result: dict[str, Any] = {
        "count": count,
        "fraction_of_common_valid": float(count / np.count_nonzero(valid)),
        "area_hectares_approx": float(count * spacing * spacing / 10000.0),
    }
    if count:
        rows, columns = np.nonzero(selected)
        result["centroid_bng"] = {
            "easting": float(bounds[0] + np.mean(columns) * spacing),
            "northing": float(bounds[3] - np.mean(rows) * spacing),
        }
    return result


def _roughness_region_summary(
    values: np.ndarray,
    spacing: float,
    bounds: tuple[float, float, float, float],
    centre: tuple[float, float],
    radius_m: float,
) -> dict[str, Any]:
    rows, columns = np.indices(values.shape)
    eastings = bounds[0] + columns * spacing
    northings = bounds[3] - rows * spacing
    region = (eastings - centre[0]) ** 2 + (northings - centre[1]) ** 2 <= radius_m**2
    valid = region & np.isfinite(values)
    selected = values[valid]
    return {
        "centre_bng": {"easting": centre[0], "northing": centre[1]},
        "radius_m": radius_m,
        "valid_count": int(selected.size),
        "median_m": float(np.median(selected)),
        "p75_m": float(np.percentile(selected, 75)),
        "p95_m": float(np.percentile(selected, 95)),
    }


def run(config_path: Path, output_root: Path | None = None) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest_path = _resolve_repo_path(
        config_path, config["input"]["landscape_manifest_path_convention"]
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    surface_manifest = manifest["surfaces"][config["input"]["surface"]]
    surface_output = surface_manifest["output"]
    r16_path = manifest_path.parent / "heightmaps" / surface_output["files"]["r16"]["path"]
    expected_hash = config["input"]["expected_r16_sha256"]
    before_hash = sha256_file(r16_path)
    if before_hash != expected_hash:
        raise ValueError(f"Canonical R16 hash {before_hash} does not match {expected_hash}")
    bounds = tuple(float(value) for value in manifest["source_aoi_bounds"])
    encoding = manifest["height_encoding"]
    surface = decode_landscape_r16(
        r16_path,
        width=int(surface_output["width"]),
        height=int(surface_output["height"]),
        bounds=bounds,
        vertical_origin_m_odn=float(encoding["vertical_origin_m_odn"]),
        z_scale=float(encoding["z_scale"]),
        expected_sha256=expected_hash,
    )
    elevation = surface.elevations_m_odn
    spacing = surface.spacing_m
    derivatives = config["derivatives"]
    slope, aspect = slope_aspect(
        elevation,
        spacing,
        flat_threshold_degrees=float(
            derivatives["aspect"]["flat_slope_threshold_degrees"]
        ),
    )
    finite_slope = slope[np.isfinite(slope)]
    if finite_slope.size == 0 or np.min(finite_slope) < 0.0 or np.max(finite_slope) > 90.0:
        raise ValueError("Slope contains impossible values outside 0..90 degrees")

    curvature = terrain_curvatures(
        elevation,
        spacing,
        minimum_slope_degrees=float(
            derivatives["curvature"]["minimum_slope_for_profile_plan_degrees"]
        ),
    )
    roughness: dict[int, np.ndarray] = {}
    for window in derivatives["roughness"]["window_sizes_samples"]:
        roughness[int(window)] = detrended_rms_roughness(elevation, int(window))

    output_root = (
        output_root.resolve()
        if output_root is not None
        else _resolve_repo_path(config_path, config["output"]["path_convention"])
    )
    raster_root = output_root / "rasters"
    image_root = output_root / "images"
    raster_root.mkdir(parents=True, exist_ok=True)
    image_root.mkdir(parents=True, exist_ok=True)

    fields: dict[str, tuple[np.ndarray, str]] = {
        "elevation_m_odn": (elevation, "metres ODN"),
        "slope_degrees": (slope, "degrees"),
        "aspect_degrees": (aspect, "degrees clockwise from grid north"),
        "curvature_laplacian_per_m": (curvature["laplacian_per_m"], "1/metre"),
        "curvature_profile_per_m": (curvature["profile_per_m"], "1/metre"),
        "curvature_plan_per_m": (curvature["plan_per_m"], "1/metre"),
    }
    for window, values in roughness.items():
        effective = window * spacing
        fields[f"roughness_detrended_rms_{window}samples_m"] = (values, "metres")

    raster_paths: dict[str, str] = {}
    for name, (values, _) in fields.items():
        path = raster_root / f"{name}.tif"
        _write_raster(path, values, surface.transform)
        raster_paths[name] = str(path.resolve())

    extent = (bounds[0], bounds[2], bounds[1], bounds[3])
    image_paths: dict[str, str] = {}
    basic_plots = [
        ("elevation", elevation, "terrain", "Elevation", "metres ODN", None, None),
        ("slope", slope, "magma", "Slope", "degrees", 0.0, float(np.nanpercentile(slope, 99.5))),
        ("aspect", aspect, "twilight", "Downhill aspect", "degrees clockwise from grid north", 0.0, 360.0),
    ]
    for name, values, cmap, title, label, vmin, vmax in basic_plots:
        path = image_root / f"{name}.png"
        _plot_field(values, path, extent, title=title, label=label, cmap=cmap, vmin=vmin, vmax=vmax)
        image_paths[name] = str(path.resolve())

    for curvature_name, title in (
        ("laplacian_per_m", "Laplacian curvature: hollow (+) / ridge (-)"),
        ("profile_per_m", "Profile curvature: concave (+) / convex (-)"),
        ("plan_per_m", "Plan curvature: hollow (+) / ridge (-)"),
    ):
        values = curvature[curvature_name]
        limit = float(np.nanpercentile(np.abs(values), 98.0))
        path = image_root / f"curvature_{curvature_name}.png"
        _plot_field(values, path, extent, title=title, label="1/metre", cmap="RdBu", vmin=-limit, vmax=limit)
        image_paths[f"curvature_{curvature_name}"] = str(path.resolve())

    roughness_statistics: dict[str, Any] = {}
    for window, values in roughness.items():
        effective = window * spacing
        name = f"roughness_{window}samples"
        path = image_root / f"{name}.png"
        _plot_field(
            values,
            path,
            extent,
            title=f"Plane-detrended RMS roughness ({effective:.1f} m window)",
            label="vertical RMS residual (m)",
            cmap="inferno",
            vmin=0.0,
            vmax=float(np.nanpercentile(values, 99.0)),
        )
        image_paths[name] = str(path.resolve())
        roughness_statistics[name] = numeric_summary(values, "metres") | {
            "window_samples": window,
            "window_footprint_m": effective,
            "interior_span_between_outer_sample_centres_m": (window - 1) * spacing,
            "maximum_location": _field_location(values, spacing, bounds, "max"),
            "tryfan_core": _roughness_region_summary(
                values, spacing, bounds, (266405.0, 359387.0), 600.0
            ),
        }

    relation_config = config["relationships"]
    local_roughness = roughness[min(roughness)]
    common_valid = np.isfinite(slope) & np.isfinite(local_roughness) & np.isfinite(curvature["laplacian_per_m"])
    local_valid = local_roughness[common_valid]
    rough_low, rough_high = np.quantile(
        local_valid, relation_config["rough_and_smooth_quantiles"]
    )
    laplacian_valid = curvature["laplacian_per_m"][common_valid]
    curvature_threshold = float(
        np.quantile(
            np.abs(laplacian_valid),
            relation_config["curvature_quantile_of_absolute_laplacian"],
        )
    )
    steep = slope >= float(relation_config["steep_threshold_degrees"])
    gentle = slope <= float(relation_config["gentle_threshold_degrees"])
    rough = local_roughness >= rough_high
    smooth = local_roughness <= rough_low
    concave = curvature["laplacian_per_m"] >= curvature_threshold
    convex = curvature["laplacian_per_m"] <= -curvature_threshold
    relationship_masks = {
        "steep_and_rough": steep & rough,
        "steep_and_relatively_smooth": steep & smooth,
        "concave_and_rough": concave & rough,
        "convex_and_rough": convex & rough,
        "gentle_and_smooth": gentle & smooth,
    }
    relationships = {
        "thresholds": {
            "steep_degrees": relation_config["steep_threshold_degrees"],
            "gentle_degrees": relation_config["gentle_threshold_degrees"],
            "local_roughness_p25_m": float(rough_low),
            "local_roughness_p75_m": float(rough_high),
            "absolute_laplacian_p75_per_m": curvature_threshold,
        },
        "classes": {
            name: _mask_summary(mask, common_valid, spacing, bounds)
            for name, mask in relationship_masks.items()
        },
        "warning": relation_config["interpretation"],
    }
    class_values = np.zeros(elevation.shape, dtype=np.float32)
    for code, name in enumerate(relationship_masks, 1):
        class_values[relationship_masks[name] & common_valid] = code
    class_values[~common_valid] = np.nan
    class_path = image_root / "terrain_relationships.png"
    colours = ["#333333", "#d73027", "#fc8d59", "#4575b4", "#984ea3", "#91cf60"]
    cmap = ListedColormap(colours)
    norm = BoundaryNorm(np.arange(-0.5, 6.5, 1.0), cmap.N)
    figure, axis = plt.subplots(figsize=(9, 8), constrained_layout=True)
    image = axis.imshow(class_values, extent=extent, origin="upper", cmap=cmap, norm=norm, interpolation="nearest")
    axis.set(title="Relative terrain-geometry relationships", xlabel="BNG easting (m)", ylabel="BNG northing (m)", aspect="equal")
    colourbar = figure.colorbar(image, ax=axis, ticks=np.arange(0, 6), shrink=0.82)
    colourbar.ax.set_yticklabels(["other", "steep+rough", "steep+smooth", "concave+rough", "convex+rough", "gentle+smooth"])
    figure.savefig(class_path, dpi=160)
    plt.close(figure)
    image_paths["terrain_relationships"] = str(class_path.resolve())

    curvature_statistics = {
        name: numeric_summary(values, "1/metre")
        for name, values in (
            ("laplacian", curvature["laplacian_per_m"]),
            ("profile", curvature["profile_per_m"]),
            ("plan", curvature["plan_per_m"]),
        )
    }
    field_statistics = {
        "elevation": numeric_summary(elevation, "metres ODN"),
        "slope": numeric_summary(slope, "degrees"),
        "aspect": aspect_summary(aspect),
        "curvature": curvature_statistics,
        "roughness": roughness_statistics,
    }
    after_hash = sha256_file(r16_path)
    if after_hash != before_hash:
        raise RuntimeError("Canonical R16 changed during read-only surface analysis")

    report = {
        "schema_version": 1,
        "experiment": config["experiment"],
        "categories": {
            "input": "MEASURED_GEOMETRY_ENCODED_FOR_VALIDATED_UNREAL_LANDSCAPE",
            "outputs": "DETERMINISTICALLY_DERIVED_FROM_MEASURED_GEOMETRY",
            "observed_surface_information": "NOT_USED",
            "procedural_sub_resolution_reconstruction": "NOT_USED",
        },
        "input": {
            "r16": str(r16_path.resolve()),
            "sha256_before": before_hash,
            "sha256_after": after_hash,
            "manifest": str(manifest_path),
            "surface": config["input"]["surface"],
            "dimensions_vertices": [elevation.shape[1], elevation.shape[0]],
            "crs": manifest["source_crs"],
            "aoi_bounds_bng": bounds,
            "sample_spacing_m": spacing,
            "vertical_quantization_step_m": float(encoding["quantization_step_m"]),
            "complete_coverage": bool(np.all(np.isfinite(elevation))),
        },
        "algorithms": config["derivatives"],
        "statistics": field_statistics,
        "relationships": relationships,
        "diagnostic_locations": {
            "maximum_slope": _field_location(slope, spacing, bounds, "max"),
            "maximum_positive_laplacian": _field_location(curvature["laplacian_per_m"], spacing, bounds, "max"),
            "maximum_negative_laplacian": _field_location(curvature["laplacian_per_m"], spacing, bounds, "min"),
        },
        "outputs": {
            "rasters": raster_paths,
            "images": image_paths,
        },
        "limitations": [
            "The 0.992 m vertex grid cannot resolve sub-metre blocks, cracks or texture.",
            "Slope and especially curvature amplify height quantisation, interpolation and classification noise.",
            "DTM is bare-earth geometry and does not identify rock, grass, scree, paths, vegetation or wetness.",
            "Roughness is scale-dependent geometric evidence, not a material classification.",
            "Square-window roughness is undefined near edges by half the window width.",
        ],
        "deterministic": True,
    }
    report_path = output_root / "lab005a-surface-analysis.json"
    report["outputs"]["report"] = str(report_path.resolve())
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "input": report["input"],
        "statistics": report["statistics"],
        "relationships": report["relationships"],
        "outputs": report["outputs"],
    }, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    arguments = parser.parse_args()
    run(arguments.config, arguments.output_root)


if __name__ == "__main__":
    main()