"""Run Meridian Earth Lab 005B Sentinel/terrain evidence analysis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.warp import Resampling

from sentinel2_evidence import extract_native_window
from surface_evidence import (
    AnalysisGrid,
    apply_valid_mask,
    assert_grid,
    normalized_difference,
    numeric_summary,
    pearson_pair,
    reproject_numeric,
    scl_summary,
    scl_valid_mask,
    sha256_file,
    stable_json_sha256,
    surface_reflectance,
)

NODATA = -9999.0

def _tile_size(length: int) -> int:
    return max(16, min(256, (int(length) // 16) * 16))


def _resolve(config_path: Path, convention: str) -> Path:
    path = Path(convention)
    return path.resolve() if path.is_absolute() else (config_path.parents[2] / path).resolve()


def _write_float(path: Path, values: np.ndarray, grid: AnalysisGrid) -> None:
    output = np.where(np.isfinite(values), values, NODATA).astype(np.float32)
    with rasterio.open(
        path, "w", driver="GTiff", width=grid.width, height=grid.height,
        count=1, dtype="float32", crs=grid.crs, transform=grid.transform,
        nodata=NODATA, compress="deflate", predictor=3, tiled=True,
        blockxsize=_tile_size(grid.width), blockysize=_tile_size(grid.height),
    ) as destination:
        destination.write(output, 1)


def _write_byte(path: Path, values: np.ndarray, grid: AnalysisGrid) -> None:
    with rasterio.open(
        path, "w", driver="GTiff", width=grid.width, height=grid.height,
        count=1, dtype="uint8", crs=grid.crs, transform=grid.transform,
        nodata=0, compress="deflate", tiled=True,
        blockxsize=_tile_size(grid.width), blockysize=_tile_size(grid.height),
    ) as destination:
        destination.write(np.asarray(values, dtype=np.uint8), 1)


def _aligned_band(native_path: Path, spec: dict[str, Any], grid: AnalysisGrid) -> np.ndarray:
    with rasterio.open(native_path) as source:
        raw = source.read(1)
        reflectance = surface_reflectance(
            raw, scale=float(spec["scale"]), offset=float(spec["offset"]), nodata=spec.get("nodata")
        )
        return reproject_numeric(
            reflectance, source.transform, source.crs, grid,
            resampling=Resampling.bilinear, source_nodata=np.nan,
        )


def _aligned_scl(native_path: Path, grid: AnalysisGrid) -> np.ndarray:
    with rasterio.open(native_path) as source:
        result = reproject_numeric(
            source.read(1), source.transform, source.crs, grid,
            resampling=Resampling.nearest, source_nodata=None, destination_nodata=0.0,
        )
    return np.rint(result).astype(np.uint8)


def _terrain_to_grid(path: Path, grid: AnalysisGrid, resampling: Resampling) -> np.ndarray:
    with rasterio.open(path) as source:
        return reproject_numeric(
            source.read(1), source.transform, source.crs, grid,
            resampling=resampling, source_nodata=source.nodata,
        )


def _plot_rgb(values: np.ndarray, path: Path, title: str, extent: tuple[float, ...]) -> None:
    rgb = np.moveaxis(values, 0, -1).astype(np.float32)
    valid = np.all(np.isfinite(rgb), axis=2)
    display = np.zeros_like(rgb)
    for channel in range(3):
        sample = rgb[..., channel][valid]
        low, high = np.percentile(sample, (2, 98))
        display[..., channel] = np.clip((rgb[..., channel] - low) / max(high - low, 1e-6), 0, 1)
    display[~valid] = 0
    figure, axis = plt.subplots(figsize=(8, 8), constrained_layout=True)
    axis.imshow(display, extent=extent, origin="upper", interpolation="nearest")
    axis.set(title=title, xlabel="BNG easting (m)", ylabel="BNG northing (m)", aspect="equal")
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_indices(fields: dict[str, np.ndarray], path: Path, extent: tuple[float, ...]) -> None:
    specifications = [
        ("ndvi", "NDVI vegetation evidence", "RdYlGn", -0.2, 0.9),
        ("ndwi", "NDWI open-water/wetness evidence", "BrBG", -0.8, 0.8),
        ("ndmi", "NDMI canopy/surface moisture evidence (20 m)", "BrBG", -0.6, 0.6),
        ("ndre", "NDRE red-edge vegetation evidence (20 m)", "RdYlGn", -0.2, 0.7),
        ("swir_ratio", "(B11-B12)/(B11+B12), 20 m", "PuOr", -0.4, 0.4),
        ("brightness", "Visible/NIR mean reflectance", "gray", 0.0, 0.4),
    ]
    figure, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    for axis, (name, title, cmap, vmin, vmax) in zip(axes.ravel(), specifications):
        image = axis.imshow(fields[name], extent=extent, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
        axis.set(title=title, xlabel="Easting", ylabel="Northing", aspect="equal")
        figure.colorbar(image, ax=axis, shrink=0.75)
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _plot_mask(scl: np.ndarray, path: Path, extent: tuple[float, ...]) -> None:
    figure, axis = plt.subplots(figsize=(8, 8), constrained_layout=True)
    image = axis.imshow(scl, extent=extent, origin="upper", cmap="tab20", vmin=0, vmax=19, interpolation="nearest")
    axis.set(title="Sentinel-2 scene classification (20 m)", xlabel="BNG easting (m)", ylabel="BNG northing (m)", aspect="equal")
    figure.colorbar(image, ax=axis, label="SCL class", shrink=0.8)
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_relationships(ndvi: np.ndarray, ndmi: np.ndarray, terrain10: dict[str, np.ndarray], terrain20: dict[str, np.ndarray], path: Path) -> None:
    pairs = [
        (terrain10["slope_mean"], ndvi, "Mean slope (degrees)", "NDVI"),
        (terrain10["roughness15_mean"], ndvi, "15 m roughness mean (m)", "NDVI"),
        (terrain20["curvature_mean"], ndmi, "Laplacian curvature mean (1/m)", "NDMI"),
        (terrain20["elevation_mean"], ndmi, "Elevation mean (m ODN)", "NDMI"),
    ]
    figure, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
    for axis, (x, y, xlabel, ylabel) in zip(axes.ravel(), pairs):
        valid = np.isfinite(x) & np.isfinite(y)
        axis.hexbin(x[valid], y[valid], gridsize=42, bins="log", mincnt=1, cmap="viridis")
        axis.set(xlabel=xlabel, ylabel=ylabel)
    figure.suptitle("Lab 005B terrain / Sentinel relationships (observational, not material classes)")
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _terrain_aggregates(root: Path, grid: AnalysisGrid) -> dict[str, np.ndarray]:
    raster_root = root / "rasters"
    sources = {
        "elevation": "elevation_m_odn.tif",
        "slope": "slope_degrees.tif",
        "curvature": "curvature_laplacian_per_m.tif",
        "roughness5": "roughness_detrended_rms_5samples_m.tif",
        "roughness15": "roughness_detrended_rms_15samples_m.tif",
        "roughness51": "roughness_detrended_rms_51samples_m.tif",
        "aspect": "aspect_degrees.tif",
    }
    result: dict[str, np.ndarray] = {}
    for name in ("elevation", "slope", "curvature", "roughness5", "roughness15", "roughness51"):
        path = raster_root / sources[name]
        result[f"{name}_mean"] = _terrain_to_grid(path, grid, Resampling.average)
        result[f"{name}_max"] = _terrain_to_grid(path, grid, Resampling.max)
    with rasterio.open(raster_root / sources["aspect"]) as source:
        aspect = source.read(1).astype(np.float32)
        aspect[aspect == source.nodata] = np.nan
        radians = np.radians(aspect)
        sin_mean = reproject_numeric(np.sin(radians), source.transform, source.crs, grid, resampling=Resampling.average, source_nodata=np.nan)
        cos_mean = reproject_numeric(np.cos(radians), source.transform, source.crs, grid, resampling=Resampling.average, source_nodata=np.nan)
        result["aspect_circular_mean"] = np.degrees(np.arctan2(sin_mean, cos_mean)) % 360.0
        result["aspect_concentration"] = np.hypot(sin_mean, cos_mean)
    return result


def _contrast_examples(ndvi: np.ndarray, slope: np.ndarray, roughness: np.ndarray, grid: AnalysisGrid) -> dict[str, Any]:
    valid = np.isfinite(ndvi) & np.isfinite(slope) & np.isfinite(roughness)
    slope_bin = np.floor(slope / 5.0).astype(np.int16)
    rough_quantiles = np.nanquantile(roughness[valid], (0.25, 0.5, 0.75))
    rough_bin = np.digitize(roughness, rough_quantiles)
    best: dict[str, Any] | None = None
    for sb in np.unique(slope_bin[valid]):
        for rb in range(4):
            group = valid & (slope_bin == sb) & (rough_bin == rb)
            if np.count_nonzero(group) < 25:
                continue
            values = ndvi[group]
            spread = float(np.percentile(values, 90) - np.percentile(values, 10))
            if best is None or spread > best["ndvi_p90_minus_p10"]:
                best = {
                    "slope_bin_degrees": [int(sb * 5), int((sb + 1) * 5)],
                    "roughness_quartile": rb + 1,
                    "cell_count": int(values.size),
                    "ndvi_p10": float(np.percentile(values, 10)),
                    "ndvi_p90": float(np.percentile(values, 90)),
                    "ndvi_p90_minus_p10": spread,
                }
    ndvi_bin = np.full(ndvi.shape, -32768, dtype=np.int16)
    ndvi_bin[valid] = np.floor((ndvi[valid] + 1.0) / 0.1).astype(np.int16)
    spectral_best: dict[str, Any] | None = None
    for nb in np.unique(ndvi_bin[valid]):
        group = valid & (ndvi_bin == nb)
        if np.count_nonzero(group) < 25:
            continue
        values = slope[group]
        spread = float(np.percentile(values, 90) - np.percentile(values, 10))
        if spectral_best is None or spread > spectral_best["slope_p90_minus_p10_degrees"]:
            spectral_best = {
                "ndvi_bin": [float(nb * 0.1 - 1.0), float((nb + 1) * 0.1 - 1.0)],
                "cell_count": int(values.size),
                "slope_p10_degrees": float(np.percentile(values, 10)),
                "slope_p90_degrees": float(np.percentile(values, 90)),
                "slope_p90_minus_p10_degrees": spread,
            }
    return {"similar_geometry_different_spectrum": best, "similar_spectrum_different_geometry": spectral_best}


def run(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bounds = tuple(float(value) for value in config["aoi"]["bounds"])
    grid10 = AnalysisGrid(config["aoi"]["crs"], *bounds, 10.0)
    grid20 = AnalysisGrid(config["aoi"]["crs"], *bounds, 20.0)
    assert_grid(grid10); assert_grid(grid20)
    output_root = _resolve(config_path, config["output"]["root_convention"])
    native_root = output_root / "source-native"
    aligned_root = output_root / "aligned-bng"
    image_root = output_root / "images"
    for path in (native_root, aligned_root, image_root): path.mkdir(parents=True, exist_ok=True)

    r16 = _resolve(config_path, config["terrain"]["canonical_r16_convention"])
    r16_hash = sha256_file(r16)
    if r16_hash != config["terrain"]["canonical_r16_sha256"]:
        raise ValueError(f"Canonical R16 integrity failure: {r16_hash}")
    lab005a_root = _resolve(config_path, config["terrain"]["lab005a_root_convention"])
    retrieval_bounds = (
        bounds[0] - config["aoi"]["retrieval_margin_m"], bounds[1] - config["aoi"]["retrieval_margin_m"],
        bounds[2] + config["aoi"]["retrieval_margin_m"], bounds[3] + config["aoi"]["retrieval_margin_m"],
    )
    native: dict[str, dict[str, Any]] = {}
    for name, spec in config["bands"].items():
        path = native_root / f"{spec['code']}_{spec['native_resolution_m']}m-native-window.tif"
        native[name] = extract_native_window(spec["url"], path, retrieval_bounds)
        native[name]["sha256"] = sha256_file(path)
        native[name]["bytes"] = path.stat().st_size

    scl20 = _aligned_scl(Path(native["scl"]["path"]), grid20)
    scl10 = _aligned_scl(Path(native["scl"]["path"]), grid10)
    valid20, valid10 = scl_valid_mask(scl20), scl_valid_mask(scl10)
    _write_byte(aligned_root / "scl_20m.tif", scl20, grid20)
    _write_byte(aligned_root / "valid_mask_20m.tif", valid20.astype(np.uint8), grid20)
    _write_byte(aligned_root / "valid_mask_10m.tif", valid10.astype(np.uint8), grid10)

    reflectance10 = {name: apply_valid_mask(_aligned_band(Path(native[name]["path"]), config["bands"][name], grid10), valid10) for name in ("blue", "green", "red", "nir")}
    reflectance20 = {name: apply_valid_mask(_aligned_band(Path(native[name]["path"]), config["bands"][name], grid20), valid20) for name in ("rededge1", "rededge2", "rededge3", "nir_narrow", "swir16", "swir22")}
    for name, values in {**reflectance10, **reflectance20}.items():
        grid = grid10 if name in reflectance10 else grid20
        _write_float(aligned_root / f"{name}_reflectance_{int(grid.resolution_m)}m.tif", values, grid)

    indices10 = {
        "ndvi": apply_valid_mask(normalized_difference(reflectance10["nir"], reflectance10["red"], minimum_sum=0.02, require_nonnegative=True), valid10),
        "ndwi": apply_valid_mask(normalized_difference(reflectance10["green"], reflectance10["nir"], minimum_sum=0.02, require_nonnegative=True), valid10),
        "brightness": apply_valid_mask(np.nanmean(np.stack(tuple(reflectance10.values())), axis=0), valid10),
    }
    nir20 = apply_valid_mask(_aligned_band(Path(native["nir"]["path"]), config["bands"]["nir"], grid20), valid20)
    indices20 = {
        "ndmi": apply_valid_mask(normalized_difference(nir20, reflectance20["swir16"], minimum_sum=0.02, require_nonnegative=True), valid20),
        "ndre": apply_valid_mask(normalized_difference(reflectance20["nir_narrow"], reflectance20["rededge1"], minimum_sum=0.02, require_nonnegative=True), valid20),
        "swir_ratio": apply_valid_mask(normalized_difference(reflectance20["swir16"], reflectance20["swir22"], minimum_sum=0.02, require_nonnegative=True), valid20),
    }
    for name, values in indices10.items(): _write_float(aligned_root / f"{name}_10m.tif", values, grid10)
    for name, values in indices20.items(): _write_float(aligned_root / f"{name}_20m.tif", values, grid20)

    terrain10 = _terrain_aggregates(lab005a_root, grid10)
    terrain20 = _terrain_aggregates(lab005a_root, grid20)
    for resolution, grid, terrain in ((10, grid10, terrain10), (20, grid20, terrain20)):
        for name, values in terrain.items(): _write_float(aligned_root / f"terrain_{name}_{resolution}m.tif", values, grid)

    extent = (bounds[0], bounds[2], bounds[1], bounds[3])
    _plot_rgb(np.stack((reflectance10["red"], reflectance10["green"], reflectance10["blue"])), image_root / "natural-colour-10m.png", "Sentinel-2 L2A natural colour (10 m)", extent)
    _plot_rgb(np.stack((reflectance10["nir"], reflectance10["red"], reflectance10["green"])), image_root / "false-colour-nir-10m.png", "Sentinel-2 L2A NIR false colour (10 m)", extent)
    display_indices = {**indices10, **indices20}
    _plot_indices(display_indices, image_root / "spectral-indices.png", extent)
    _plot_mask(scl20, image_root / "scene-classification-20m.png", extent)
    _plot_relationships(indices10["ndvi"], indices20["ndmi"], terrain10, terrain20, image_root / "terrain-spectral-relationships.png")

    statistics = {
        name: numeric_summary(values, "dimensionless_reflectance") for name, values in {**reflectance10, **reflectance20}.items()
    }
    statistics.update({name: numeric_summary(values, "dimensionless_index") for name, values in display_indices.items()})
    correlations: dict[str, Any] = {}
    for index_name, index_values, terrain in (("ndvi", indices10["ndvi"], terrain10), ("ndwi", indices10["ndwi"], terrain10), ("ndmi", indices20["ndmi"], terrain20), ("ndre", indices20["ndre"], terrain20), ("swir_ratio", indices20["swir_ratio"], terrain20)):
        for terrain_name in ("elevation_mean", "slope_mean", "slope_max", "curvature_mean", "roughness5_mean", "roughness15_mean", "roughness51_mean", "aspect_circular_mean", "aspect_concentration"):
            correlations[f"{index_name}__{terrain_name}"] = pearson_pair(index_values, terrain[terrain_name])

    output_files = sorted(path for path in output_root.rglob("*") if path.is_file() and path.name != "lab005b-report.json")
    report: dict[str, Any] = {
        "schema_version": 1,
        "experiment": config["experiment"],
        "configuration_sha256": stable_json_sha256(config),
        "observation": config["observation"],
        "licence": config["licence"],
        "aoi": config["aoi"],
        "retrieval_bounds_bng": list(retrieval_bounds),
        "analysis_grids": {"10m": grid10.as_dict(), "20m": grid20.as_dict()},
        "terrain": {**config["terrain"], "observed_r16_sha256": r16_hash},
        "native_windows": native,
        "mask": {"invalid_scl_classes": [0, 1, 3, 8, 9, 10, 11], "aoi_summary": scl_summary(scl20)},
        "indices": {
            "ndvi": {"equation": "(B08-B04)/(B08+B04)", "effective_resolution_m": 10, "validity": "both reflectances nonnegative and sum > 0.02", "interpretation": "green vegetation vigour/fraction evidence; affected by substrate, shadow and canopy structure"},
            "ndwi": {"equation": "(B03-B08)/(B03+B08)", "effective_resolution_m": 10, "validity": "both reflectances nonnegative and sum > 0.02", "interpretation": "open-water/wetness contrast; not a direct soil-moisture measurement"},
            "brightness": {"equation": "mean(B02,B03,B04,B08)", "effective_resolution_m": 10, "interpretation": "broad visible/NIR brightness proxy, not hemispherical albedo"},
            "ndmi": {"equation": "(B08-B11)/(B08+B11)", "effective_resolution_m": 20, "validity": "both reflectances nonnegative and sum > 0.02", "interpretation": "canopy/surface moisture-related evidence with substrate and shadow ambiguity"},
            "ndre": {"equation": "(B8A-B05)/(B8A+B05)", "effective_resolution_m": 20, "validity": "both reflectances nonnegative and sum > 0.02", "interpretation": "red-edge vegetation/chlorophyll-related evidence"},
            "swir_ratio": {"equation": "(B11-B12)/(B11+B12)", "effective_resolution_m": 20, "validity": "both reflectances nonnegative and sum > 0.02", "interpretation": "SWIR spectral-shape evidence sensitive to moisture/mineral/substrate mixtures"},
        },
        "statistics": statistics,
        "terrain_aggregation": {
            "method": "area-weighted average and maximum from frozen 0.992063 m Lab 005A rasters onto exact 10 m and 20 m BNG cells; aspect aggregated through mean sine/cosine",
            "warning": "Sentinel values are never upsampled to the ~1 m terrain grid; each cell remains 10 m or 20 m observational evidence.",
        },
        "correlations": correlations,
        "contrast_examples": _contrast_examples(indices10["ndvi"], terrain10["slope_mean"], terrain10["roughness15_mean"], grid10),
        "output_files": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in output_files],
    }
    report["deterministic_result_sha256"] = stable_json_sha256({key: value for key, value in report.items() if key != "output_files"})
    report_path = output_root / "lab005b-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.config)
    print(json.dumps({"product": report["observation"]["official_product_id"], "usable_fraction": report["mask"]["aoi_summary"]["usable_fraction"], "result_sha256": report["deterministic_result_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
