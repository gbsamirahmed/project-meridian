"""Run Meridian Earth Lab 009 and write external reconstruction products."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject

from experiment_paths import resolve_repository_value
from surface_reconstruction import (
    LAB007_CLASSES,
    READINESS_NAMES,
    VISUAL_CLASSES,
    coarse_boundary_jump,
    neighbor_correlation,
    reconstruct_controls,
    sha256_file,
    stable_json_hash,
    verify_sha256,
)


COLORS = np.asarray(
    [
        [0.23, 0.24, 0.23],
        [0.36, 0.33, 0.29],
        [0.22, 0.30, 0.14],
        [0.34, 0.42, 0.18],
        [0.10, 0.16, 0.11],
    ],
    dtype=np.float32,
)


def _repo_root(config_path: Path) -> Path:
    return config_path.resolve().parents[2]


def _resolve(root: Path, value: str) -> Path:
    return resolve_repository_value(root, value)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_raster(path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    with rasterio.open(path) as source:
        data = source.read(1).copy()
        nodata = source.nodata
        result = data.astype(np.float32)
        if nodata is not None:
            result[data == nodata] = np.nan
        metadata = {
            "crs": str(source.crs),
            "transform": source.transform,
            "width": source.width,
            "height": source.height,
            "nodata": nodata,
        }
    return result, metadata


def _target_transform(config: dict[str, Any]) -> Affine:
    west, _, _, north = config["aoi"]["bounds"]
    spacing = float(config["aoi"]["vertex_spacing_m"])
    return Affine(spacing, 0.0, west - spacing / 2.0, 0.0, -spacing, north + spacing / 2.0)


def _reproject_field(
    path: Path,
    shape: tuple[int, int],
    transform: Affine,
    *,
    resampling: Resampling,
) -> np.ndarray:
    destination = np.full(shape, np.nan, dtype=np.float32)
    with rasterio.open(path) as source:
        source_values = source.read(1).copy()
        source_transform = source.transform
        source_nodata = source.nodata
        if source_nodata is not None and np.any(source_values == source_nodata):
            raise RuntimeError(f"Frozen source contains unexpected nodata: {path}")
        # The 3025 renderer samples include AOI boundary vertices, whereas the
        # 300-cell evidence grid stores cell centres. Edge padding provides the
        # documented nearest-cell support outside those outer centres without
        # inventing a new evidence value.
        source_values = np.pad(source_values, 1, mode="edge")
        source_transform = source_transform * Affine.translation(-1, -1)
        reproject(
            source=source_values,
            destination=destination,
            src_transform=source_transform,
            src_crs=source.crs,
            src_nodata=None,
            dst_transform=transform,
            dst_crs=source.crs,
            dst_nodata=np.nan,
            resampling=resampling,
        )
    return destination


def _fill_nearest(values: np.ndarray) -> tuple[np.ndarray, float]:
    data = np.asarray(values, dtype=np.float32)
    missing = ~np.isfinite(data)
    fraction = float(np.mean(missing))
    if not np.any(missing):
        return data, fraction
    if np.all(missing):
        raise RuntimeError("A required terrain metric is entirely undefined")
    filled = data.copy()
    filled[missing] = float(np.nanmedian(data))
    return filled, fraction


def _write_tiff(path: Path, values: np.ndarray, transform: Affine) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=values.shape[1],
        height=values.shape[0],
        count=1,
        dtype="float32",
        crs="EPSG:27700",
        transform=transform,
        nodata=-9999.0,
        tiled=True,
        blockxsize=256,
        blockysize=256,
        compress="deflate",
        predictor=3,
    ) as target:
        target.write(np.where(np.isfinite(values), values, -9999.0).astype(np.float32), 1)


def _write_rgba(path: Path, channels: list[np.ndarray]) -> None:
    encoded = np.stack(
        [np.rint(np.clip(channel, 0.0, 1.0) * 255.0).astype(np.uint8) for channel in channels],
        axis=-1,
    )
    Image.fromarray(encoded, mode="RGBA").save(path, optimize=True)


def _field_summary(values: np.ndarray) -> dict[str, Any]:
    valid = np.asarray(values, dtype=np.float64)
    valid = valid[np.isfinite(valid)]
    return {
        "minimum": float(np.min(valid)),
        "maximum": float(np.max(valid)),
        "mean": float(np.mean(valid)),
        "standard_deviation": float(np.std(valid)),
        "percentiles": {
            str(percentile): float(value)
            for percentile, value in zip((1, 5, 25, 50, 75, 95, 99), np.percentile(valid, (1, 5, 25, 50, 75, 95, 99)))
        },
    }


def _save_figure(path: Path, figure: plt.Figure) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150, bbox_inches="tight", metadata={"Software": "Meridian Earth Lab 009"})
    plt.close(figure)


def _plot_diagnostics(
    output: Path,
    probabilities_10m: np.ndarray,
    readiness_10m: np.ndarray,
    controls: np.ndarray,
    freedom: np.ndarray,
    slope: np.ndarray,
    terrain_influence: np.ndarray,
) -> list[Path]:
    images = output / "images"
    paths: list[Path] = []

    figure, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    for index, (axis, name) in enumerate(zip(axes.flat, LAB007_CLASSES)):
        item = axis.imshow(probabilities_10m[..., index], vmin=0, vmax=0.5, cmap="viridis")
        axis.set_title(f"Lab 007 {name}")
        axis.set_axis_off()
        figure.colorbar(item, ax=axis, shrink=0.7)
    path = images / "lab007-probability-reference.png"
    _save_figure(path, figure); paths.append(path)

    figure, axis = plt.subplots(figsize=(7, 6), constrained_layout=True)
    item = axis.imshow(readiness_10m, vmin=1, vmax=3, cmap="viridis")
    axis.set_title("Frozen Lab 008 reconstruction readiness")
    axis.set_axis_off(); figure.colorbar(item, ax=axis, ticks=(1, 2, 3))
    path = images / "lab008-reconstruction-readiness.png"
    _save_figure(path, figure); paths.append(path)

    step = 4
    figure, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    for index, (axis, name) in enumerate(zip(axes.flat[:5], VISUAL_CLASSES)):
        item = axis.imshow(controls[::step, ::step, index], vmin=0, vmax=0.6, cmap="magma")
        axis.set_title(f"Reconstructed {name}")
        axis.set_axis_off(); figure.colorbar(item, ax=axis, shrink=0.7)
    item = axes.flat[5].imshow(freedom[::step, ::step], vmin=0, vmax=1, cmap="cividis")
    axes.flat[5].set_title("Reconstruction freedom")
    axes.flat[5].set_axis_off(); figure.colorbar(item, ax=axes.flat[5], shrink=0.7)
    path = images / "reconstructed-continuous-controls.png"
    _save_figure(path, figure); paths.append(path)

    colour = np.tensordot(controls[::step, ::step], COLORS, axes=([-1], [0]))
    shade = 0.72 + 0.28 * (1.0 - np.clip(slope[::step, ::step] / 65.0, 0.0, 1.0))
    colour = np.clip(colour * shade[..., None], 0.0, 1.0)
    figure, axis = plt.subplots(figsize=(8, 8), constrained_layout=True)
    axis.imshow(colour); axis.set_title("Lab 009 top-down material-control preview (not a photograph)")
    axis.set_axis_off()
    path = images / "reconstruction-material-preview.png"
    _save_figure(path, figure); paths.append(path)

    figure, axes = plt.subplots(1, 3, figsize=(14, 5), constrained_layout=True)
    items = (
        (slope[::step, ::step], "Measured slope (degrees)", "terrain", 0, 70),
        (terrain_influence[::step, ::step], "Bounded terrain influence", "magma", 0, 0.45),
        (freedom[::step, ::step], "Reconstruction freedom", "cividis", 0, 1),
    )
    for axis, (values, title, cmap, lower, upper) in zip(axes, items):
        item = axis.imshow(values, cmap=cmap, vmin=lower, vmax=upper)
        axis.set_title(title); axis.set_axis_off(); figure.colorbar(item, ax=axis, shrink=0.7)
    path = images / "terrain-conditioning-and-freedom.png"
    _save_figure(path, figure); paths.append(path)

    known = probabilities_10m[..., :5]
    known /= np.maximum(np.sum(known, axis=-1, keepdims=True), 1e-8)
    figure, axis = plt.subplots(figsize=(9, 5), constrained_layout=True)
    x = np.arange(5)
    axis.bar(x - 0.18, np.mean(known, axis=(0, 1)), 0.36, label="Lab 007 known-class conditional")
    axis.bar(x + 0.18, np.mean(controls, axis=(0, 1)), 0.36, label="Lab 009 reconstruction")
    axis.set_xticks(x, VISUAL_CLASSES, rotation=20); axis.set_ylabel("AOI mean weight")
    axis.set_title("Aggregate evidence versus reconstruction"); axis.legend()
    path = images / "aggregate-evidence-versus-reconstruction.png"
    _save_figure(path, figure); paths.append(path)
    return paths


def run(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _read_json(config_path)
    repo = _repo_root(config_path)
    frozen = config["frozen_inputs"]
    lab007_root = _resolve(repo, frozen["lab007_root"])
    lab008_root = _resolve(repo, frozen["lab008_root"])
    output = _resolve(repo, config["output_root"])
    output.mkdir(parents=True, exist_ok=True)

    lab007_report_path = lab007_root / "lab007-report.json"
    lab008_report_path = lab008_root / "lab008-report.json"
    verify_sha256(lab007_report_path, frozen["lab007_report_sha256"])
    verify_sha256(lab007_root / "lab007-surface-model-package.json", frozen["lab007_package_sha256"])
    verify_sha256(lab008_report_path, frozen["lab008_report_sha256"])
    lab007_report = _read_json(lab007_report_path)
    lab008_report = _read_json(lab008_report_path)
    if lab007_report["deterministic_result_sha256"] != frozen["lab007_result_sha256"]:
        raise RuntimeError("Frozen Lab 007 deterministic identity does not match")
    if lab008_report["deterministic_result_sha256"] != frozen["lab008_result_sha256"]:
        raise RuntimeError("Frozen Lab 008 deterministic identity does not match")

    protected_paths: list[Path] = [lab007_report_path, lab008_report_path]
    r16 = _resolve(repo, frozen["canonical_r16"]["path"])
    verify_sha256(r16, frozen["canonical_r16"]["sha256"]); protected_paths.append(r16)
    terrain_paths: dict[str, Path] = {}
    for name, item in frozen["terrain_metrics"].items():
        terrain_paths[name] = _resolve(repo, item["path"])
        verify_sha256(terrain_paths[name], item["sha256"]); protected_paths.append(terrain_paths[name])
    readiness_path = lab008_root / "rasters" / "reconstruction-readiness-10m.tif"
    verify_sha256(readiness_path, frozen["readiness_raster_sha256"]); protected_paths.append(readiness_path)
    output_hash_lookup = {item["path"].replace("\\", "/"): item["sha256"] for item in lab007_report["outputs"]}
    source_probability_paths: list[Path] = []
    probability_10m = []
    for name in LAB007_CLASSES:
        path = lab007_root / "rasters" / f"probability-{name}-10m.tif"
        verify_sha256(path, output_hash_lookup[f"rasters/probability-{name}-10m.tif"])
        protected_paths.append(path); source_probability_paths.append(path)
        values, _ = _read_raster(path); probability_10m.append(values)
    probabilities_10m = np.stack(probability_10m, axis=-1)
    uncertainty_path = lab007_root / "rasters" / "uncertainty-normalized-entropy-10m.tif"
    verify_sha256(uncertainty_path, output_hash_lookup["rasters/uncertainty-normalized-entropy-10m.tif"])
    protected_paths.append(uncertainty_path)
    protected_before = {str(path): sha256_file(path) for path in protected_paths}
    readiness_10m, _ = _read_raster(readiness_path)

    height, width = [int(value) for value in config["aoi"]["output_vertices"]]
    shape = (height, width)
    transform = _target_transform(config)
    probabilities = np.stack(
        [_reproject_field(path, shape, transform, resampling=Resampling.bilinear) for path in source_probability_paths],
        axis=-1,
    )
    probabilities = np.clip(probabilities, 0.0, 1.0)
    probabilities /= np.sum(probabilities, axis=-1, keepdims=True)
    readiness = np.rint(_reproject_field(readiness_path, shape, transform, resampling=Resampling.nearest)).astype(np.uint8)
    slope, _ = _read_raster(terrain_paths["slope"])
    roughness, _ = _read_raster(terrain_paths["roughness_15m"])
    curvature, _ = _read_raster(terrain_paths["laplacian_curvature"])
    slope, slope_missing = _fill_nearest(slope)
    roughness, roughness_missing = _fill_nearest(roughness)
    curvature, curvature_missing = _fill_nearest(curvature)

    settings = config["reconstruction"]
    reconstructed = reconstruct_controls(
        probabilities,
        readiness,
        slope,
        roughness,
        curvature,
        seed=int(settings["seed"]),
        vertex_spacing_m=float(config["aoi"]["vertex_spacing_m"]),
        scales_m=settings["procedural_scales_m"],
        scale_weights=settings["procedural_scale_weights"],
        regime_amplitudes=settings["regime_logit_amplitudes"],
        terrain_settings=settings["terrain_conditioning"],
    )
    controls = reconstructed["controls"]
    if not np.all(np.isfinite(controls)) or not np.allclose(np.sum(controls, axis=-1), 1.0, atol=2e-6):
        raise RuntimeError("Reconstruction controls are not finite normalized mixtures")

    raster_paths: list[Path] = []
    for index, name in enumerate(VISUAL_CLASSES):
        path = output / "rasters" / f"reconstruction-{name}-1m.tif"
        _write_tiff(path, controls[..., index], transform); raster_paths.append(path)
    for name in ("freedom", "lab007_uncertainty", "terrain_influence"):
        path = output / "rasters" / f"reconstruction-{name.replace('_', '-')}-1m.tif"
        _write_tiff(path, reconstructed[name], transform); raster_paths.append(path)

    texture_dir = output / "unreal"
    texture_dir.mkdir(parents=True, exist_ok=True)
    surface_texture = texture_dir / "lab009-surface-controls-rgba.png"
    context_texture = texture_dir / "lab009-context-controls-rgba.png"
    _write_rgba(surface_texture, [controls[..., index] for index in range(4)])
    _write_rgba(
        context_texture,
        [controls[..., 4], reconstructed["freedom"], reconstructed["lab007_uncertainty"], np.ones(shape, dtype=np.float32)],
    )

    diagnostic_paths = _plot_diagnostics(
        output,
        probabilities_10m.copy(),
        readiness_10m,
        controls,
        reconstructed["freedom"],
        slope,
        reconstructed["terrain_influence"],
    )

    known_10m = probabilities_10m[..., :5]
    known_10m /= np.maximum(np.sum(known_10m, axis=-1, keepdims=True), 1e-8)
    mean_lab007 = np.mean(known_10m, axis=(0, 1), dtype=np.float64)
    mean_lab009 = np.mean(controls, axis=(0, 1), dtype=np.float64)
    summaries = {name: _field_summary(controls[..., index]) for index, name in enumerate(VISUAL_CLASSES)}
    summaries["reconstruction_freedom"] = _field_summary(reconstructed["freedom"])
    validations = {
        "coverage_fraction": float(np.mean(np.all(np.isfinite(controls), axis=-1))),
        "probability_sum_maximum_absolute_error": float(np.max(np.abs(np.sum(controls, axis=-1) - 1.0))),
        "aggregate_lab007_known_conditional_means": dict(zip(VISUAL_CLASSES, map(float, mean_lab007))),
        "aggregate_lab009_control_means": dict(zip(VISUAL_CLASSES, map(float, mean_lab009))),
        "aggregate_maximum_absolute_delta": float(np.max(np.abs(mean_lab009 - mean_lab007))),
        "neighbor_correlation": {name: neighbor_correlation(controls[..., index]) for index, name in enumerate(VISUAL_CLASSES)},
        "coarse_grid_boundary_diagnostics": {
            name: coarse_boundary_jump(controls[..., index], 10.0 / float(config["aoi"]["vertex_spacing_m"]))
            for index, name in enumerate(VISUAL_CLASSES)
        },
        "metric_undefined_fractions_filled_only_for_edge_conditioning": {
            "slope": slope_missing,
            "roughness_15m": roughness_missing,
            "laplacian_curvature": curvature_missing,
        },
        "unknown_not_assigned_to_material": True,
        "unknown_freedom_correlation": float(np.corrcoef(probabilities[..., 5].ravel(), reconstructed["freedom"].ravel())[0, 1]),
    }

    product_paths = raster_paths + [surface_texture, context_texture]
    product_inventory = [
        {"path": str(path.relative_to(output)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(product_paths)
    ]
    package = {
        "schema_version": 1,
        "experiment": "Meridian Earth Laboratory 009",
        "algorithm_version": config["algorithm_version"],
        "grid": {"crs": "EPSG:27700", "shape": list(shape), "transform": list(transform)[:6], "vertex_spacing_m": config["aoi"]["vertex_spacing_m"]},
        "channels": {
            "scientific_inference": {"source": "frozen Lab 007", "classes": list(LAB007_CLASSES), "native_alignment_m": 10},
            "audited_freedom": {"source": "frozen Lab 008", "classes": READINESS_NAMES, "native_alignment_m": 10},
            "reconstructed_visual_controls": {"classes": list(VISUAL_CLASSES), "sum_to_one": True, "information_resolution_warning": "3025x3025 renderer grid does not make categorical evidence metre-scale observation"},
            "other_unknown": {"use": "reconstruction freedom only", "material_assignment": False},
        },
        "packed_textures": {
            "surface": {"path": str(surface_texture.relative_to(output)).replace("\\", "/"), "rgba": settings["packed_textures"]["surface_rgba"]},
            "context": {"path": str(context_texture.relative_to(output)).replace("\\", "/"), "rgba": settings["packed_textures"]["context_rgba"]},
        },
        "products": product_inventory,
    }
    package_path = output / "lab009-reconstruction-package.json"
    package_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result_identity = {
        "algorithm_version": config["algorithm_version"],
        "configuration_sha256": sha256_file(config_path),
        "frozen_lab007_result": frozen["lab007_result_sha256"],
        "frozen_lab008_result": frozen["lab008_result_sha256"],
        "canonical_r16_sha256": frozen["canonical_r16"]["sha256"],
        "products": product_inventory,
        "validations": validations,
    }
    deterministic_hash = stable_json_hash(result_identity)
    protected_after = {str(path): sha256_file(path) for path in protected_paths}
    if protected_after != protected_before:
        raise RuntimeError("A frozen upstream input changed while Lab 009 was running")

    all_outputs = product_paths + diagnostic_paths + [package_path]
    report = {
        "schema_version": 1,
        "experiment": "Meridian Earth Laboratory 009",
        "algorithm_version": config["algorithm_version"],
        "deterministic_result_sha256": deterministic_hash,
        "configuration_sha256": sha256_file(config_path),
        "frozen_inputs_verified": {
            "lab007_result_sha256": frozen["lab007_result_sha256"],
            "lab008_result_sha256": frozen["lab008_result_sha256"],
            "canonical_r16_sha256": frozen["canonical_r16"]["sha256"],
            "protected_hashes_unchanged": True,
        },
        "provenance_categories": config["provenance_categories"],
        "method": {
            "description": "Bilinearly interpolated Lab 007 inference is transformed into continuous known-class mixtures with bounded measured-terrain conditioning and deterministic correlated multiscale variation. Lab 008 readiness controls procedural amplitude. Unknown remains a freedom field, not a material.",
            "reconstruction_regimes": READINESS_NAMES,
            "procedural_scales_m": settings["procedural_scales_m"],
            "procedural_seed": settings["seed"],
            "terrain_conditioning": settings["terrain_conditioning"],
        },
        "output_grid": package["grid"],
        "statistics": summaries,
        "validation": validations,
        "unreal": {
            "material_asset": config["unreal"]["material_asset"],
            "surface_texture_asset": config["unreal"]["surface_texture_asset"],
            "context_texture_asset": config["unreal"]["context_texture_asset"],
            "setup_status": "PENDING_UNREAL_SETUP",
            "benchmark_status": "PENDING_FIXED_CAMERA_CAPTURE",
        },
        "outputs": [
            {"path": str(path.relative_to(output)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in sorted(all_outputs)
        ],
        "storage_bytes": int(sum(path.stat().st_size for path in all_outputs)),
        "limitations": [
            "Renderer texels are not metre-scale categorical observations.",
            "Procedural placement is reconstructed and does not locate measured rocks, scree fragments, vegetation objects, wet patches, or fractures.",
            "Simple v0.1 colours and roughness are a restrained visual vocabulary, not final materials or current seasonal state.",
            "Other/unknown controls reconstruction freedom and is never converted directly into a surface family.",
        ],
        "research_judgement": {"status": "PENDING_UNREAL_VISUAL_ACCEPTANCE"},
    }
    report_path = output / "lab009-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "deterministic_result_sha256": deterministic_hash, "storage_bytes": report["storage_bytes"]}, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.config)


if __name__ == "__main__":
    main()
