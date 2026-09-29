"""Run Meridian Earth Lab 005C four-season Sentinel evidence analysis."""
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

from analyze_surface_evidence import (
    _aligned_band,
    _aligned_scl,
    _terrain_aggregates,
    _write_byte,
    _write_float,
)
from experiment_paths import resolve_config_value
from sentinel2_evidence import extract_native_window
from surface_evidence import (
    AnalysisGrid,
    apply_valid_mask,
    normalized_difference,
    numeric_summary,
    pearson_pair,
    sha256_file,
    stable_json_sha256,
)
from temporal_evidence import (
    cloud_clear_mask,
    cosine_illumination,
    snow_mask,
    temporal_correlation,
    temporal_scl_summary,
    temporal_statistics,
)


SEASON_ORDER = ("winter", "spring", "summer", "autumn")
TEN_METRE_BANDS = ("blue", "green", "red", "nir")
TWENTY_METRE_BANDS = ("rededge1", "rededge2", "rededge3", "nir_narrow", "swir16", "swir22")


def _resolve(config_path: Path, convention: str) -> Path:
    return resolve_config_value(config_path, convention)


def _asset_url(config: dict[str, Any], observation: dict[str, Any], band: dict[str, Any]) -> str:
    return (
        f"{config['processing']['cog_base_url']}/{observation['cog_year']}/"
        f"{observation['cog_month']}/{observation['cog_item_id']}/{band['code']}.tif"
    )


def _surface_index(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return normalized_difference(a, b, minimum_sum=0.02, require_nonnegative=True)


def _mean_available(values: tuple[np.ndarray, ...]) -> np.ndarray:
    """Mean finite inputs without warning for cells where every band is invalid."""
    stack = np.stack(values)
    finite = np.isfinite(stack)
    count = np.sum(finite, axis=0)
    total = np.nansum(stack, axis=0)
    result = np.full(total.shape, np.nan, dtype=np.float32)
    np.divide(total, count, out=result, where=count > 0)
    return result


def _common_rgb(red: np.ndarray, green: np.ndarray, blue: np.ndarray, settings: dict[str, float]) -> np.ndarray:
    rgb = np.stack((red, green, blue), axis=-1).astype(np.float32)
    minimum = float(settings["minimum_reflectance"])
    maximum = float(settings["maximum_reflectance"])
    gamma = float(settings["gamma"])
    display = np.clip((rgb - minimum) / (maximum - minimum), 0.0, 1.0)
    if gamma != 1.0:
        display = np.power(display, 1.0 / gamma)
    display[~np.all(np.isfinite(rgb), axis=2)] = 0.0
    return display


def _plot_seasonal_rgb(observations: dict[str, dict[str, Any]], settings: dict[str, float], path: Path, extent: tuple[float, ...]) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 11), constrained_layout=True)
    for axis, season in zip(axes.ravel(), SEASON_ORDER):
        fields = observations[season]["reflectance10"]
        axis.imshow(_common_rgb(fields["red"], fields["green"], fields["blue"], settings), extent=extent, origin="upper", interpolation="nearest")
        metadata = observations[season]["metadata"]
        axis.set(title=f"{season.title()} · {metadata['official_acquisition_time_utc'][:10]} · sun {metadata['sun_elevation_degrees']:.1f}°", xlabel="BNG easting (m)", ylabel="BNG northing (m)", aspect="equal")
    figure.suptitle(f"Sentinel-2 L2A common RGB transform: {settings['minimum_reflectance']:.2f}–{settings['maximum_reflectance']:.2f} reflectance, gamma {settings['gamma']:.1f}")
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_seasonal_field(observations: dict[str, dict[str, Any]], field: str, resolution: int, path: Path, extent: tuple[float, ...], title: str, cmap: str, vmin: float, vmax: float) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 11), constrained_layout=True)
    image = None
    key = "indices10" if resolution == 10 else "indices20"
    for axis, season in zip(axes.ravel(), SEASON_ORDER):
        image = axis.imshow(observations[season][key][field], extent=extent, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
        axis.set(title=season.title(), xlabel="Easting", ylabel="Northing", aspect="equal")
    figure.suptitle(title)
    figure.colorbar(image, ax=axes.ravel().tolist(), shrink=0.78)
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_scl(observations: dict[str, dict[str, Any]], path: Path, extent: tuple[float, ...]) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 11), constrained_layout=True)
    image = None
    for axis, season in zip(axes.ravel(), SEASON_ORDER):
        image = axis.imshow(observations[season]["scl20"], extent=extent, origin="upper", cmap="tab20", vmin=0, vmax=19, interpolation="nearest")
        summary = observations[season]["scl_summary"]
        axis.set(title=f"{season.title()} · snow {summary['snow_or_ice_fraction']*100:.1f}% · cloud {summary['cloud_fraction']*100:.1f}%", xlabel="Easting", ylabel="Northing", aspect="equal")
    figure.suptitle("Scene classification: snow retained as environmental state; cloud masked")
    figure.colorbar(image, ax=axes.ravel().tolist(), shrink=0.78, label="SCL class")
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_temporal(fields: dict[str, np.ndarray], path: Path, extent: tuple[float, ...]) -> None:
    specifications = [
        ("ndvi_median", "Snow-excluded NDVI median", "RdYlGn", -0.1, 0.9),
        ("ndvi_range", "NDVI seasonal range", "magma", 0.0, 0.8),
        ("ndmi_range", "NDMI seasonal range (20 m)", "magma", 0.0, 0.7),
        ("brightness_cv", "Brightness coefficient of variation", "viridis", 0.0, 0.8),
        ("illumination_correlation", "Brightness / cosine-illumination r", "coolwarm", -1.0, 1.0),
        ("snow_count", "Snow-observation count (20 m)", "Blues", 0.0, 4.0),
    ]
    figure, axes = plt.subplots(2, 3, figsize=(16, 10), constrained_layout=True)
    for axis, (name, title, cmap, vmin, vmax) in zip(axes.ravel(), specifications):
        image = axis.imshow(fields[name], extent=extent, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
        axis.set(title=title, xlabel="Easting", ylabel="Northing", aspect="equal")
        figure.colorbar(image, ax=axis, shrink=0.76)
    figure.suptitle("Lab 005C temporal evidence — diagnostics, not material classes")
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_illumination(observations: dict[str, dict[str, Any]], path: Path, extent: tuple[float, ...]) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 11), constrained_layout=True)
    image = None
    for axis, season in zip(axes.ravel(), SEASON_ORDER):
        image = axis.imshow(observations[season]["illumination10"], extent=extent, origin="upper", cmap="cividis", vmin=-0.5, vmax=1.0, interpolation="nearest")
        axis.set(title=f"{season.title()} local cosine incidence", xlabel="Easting", ylabel="Northing", aspect="equal")
    figure.suptitle("Cell-scale expected direct illumination from terrain slope/aspect and solar geometry")
    figure.colorbar(image, ax=axes.ravel().tolist(), shrink=0.78)
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _plot_relationships(temporal: dict[str, np.ndarray], terrain10: dict[str, np.ndarray], path: Path) -> None:
    pairs = [
        (terrain10["elevation_mean"], temporal["ndvi_range"], "Elevation (m ODN)", "NDVI range"),
        (terrain10["slope_mean"], temporal["ndvi_range"], "Mean slope (degrees)", "NDVI range"),
        (terrain10["roughness15_mean"], temporal["ndvi_range"], "15 m roughness mean (m)", "NDVI range"),
        (terrain10["slope_mean"], np.abs(temporal["illumination_correlation"]), "Mean slope (degrees)", "|brightness / illumination r|"),
    ]
    figure, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
    for axis, (x, y, xlabel, ylabel) in zip(axes.ravel(), pairs):
        valid = np.isfinite(x) & np.isfinite(y)
        axis.hexbin(x[valid], y[valid], gridsize=40, bins="log", mincnt=1, cmap="viridis")
        axis.set(xlabel=xlabel, ylabel=ylabel)
    figure.suptitle("Temporal spectral behaviour versus terrain morphology")
    figure.savefig(path, dpi=170)
    plt.close(figure)


def _threshold_mask(values: np.ndarray, quantile: float, high: bool = True) -> tuple[np.ndarray, float]:
    valid = values[np.isfinite(values)]
    threshold = float(np.quantile(valid, quantile))
    return ((values >= threshold) if high else (values <= threshold)) & np.isfinite(values), threshold


def run(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bounds = tuple(float(value) for value in config["aoi"]["bounds"])
    grid10 = AnalysisGrid(config["aoi"]["crs"], *bounds, 10.0)
    grid20 = AnalysisGrid(config["aoi"]["crs"], *bounds, 20.0)
    retrieval_bounds = (bounds[0]-config["aoi"]["retrieval_margin_m"], bounds[1]-config["aoi"]["retrieval_margin_m"], bounds[2]+config["aoi"]["retrieval_margin_m"], bounds[3]+config["aoi"]["retrieval_margin_m"])
    output_root = _resolve(config_path, config["output"]["root_convention"])
    aligned_root = output_root / "aligned-bng"
    temporal_root = output_root / "temporal"
    image_root = output_root / "images"
    for path in (aligned_root, temporal_root, image_root): path.mkdir(parents=True, exist_ok=True)

    frozen = config["frozen_inputs"]
    r16_path = _resolve(config_path, frozen["canonical_r16_convention"])
    if sha256_file(r16_path) != frozen["canonical_r16_sha256"]:
        raise ValueError("Canonical R16 changed")
    lab005b_report_path = _resolve(config_path, frozen["lab005b_report_convention"])
    lab005b_report = json.loads(lab005b_report_path.read_text(encoding="utf-8"))
    if lab005b_report["deterministic_result_sha256"] != frozen["lab005b_expected_deterministic_result_sha256"]:
        raise ValueError("Frozen Lab 005B report identity changed")
    lab005b_native_root = _resolve(config_path, frozen["lab005b_native_root_convention"])
    lab005a_root = _resolve(config_path, frozen["lab005a_root_convention"])
    terrain10 = _terrain_aggregates(lab005a_root, grid10)
    terrain20 = _terrain_aggregates(lab005a_root, grid20)

    observations: dict[str, dict[str, Any]] = {}
    input_files: list[dict[str, Any]] = []
    for metadata in config["observations"]:
        season = metadata["season"]
        observation_root = output_root / "observations" / season
        native_root = observation_root / "source-native"
        season_aligned = aligned_root / season
        native_root.mkdir(parents=True, exist_ok=True)
        season_aligned.mkdir(parents=True, exist_ok=True)
        native_paths: dict[str, Path] = {}
        for name, spec in config["bands"].items():
            filename = f"{spec['code']}_{spec['native_resolution_m']}m-native-window.tif"
            url = _asset_url(config, metadata, spec)
            if metadata.get("reuse_lab005b_native"):
                path = lab005b_native_root / filename
                expected = lab005b_report["native_windows"][name]["sha256"]
                if sha256_file(path) != expected:
                    raise ValueError(f"Frozen Lab 005B native band changed: {name}")
                source_role = "read_only_reuse_from_lab005b"
            else:
                path = native_root / filename
                extract_native_window(url, path, retrieval_bounds)
                source_role = "lab005c_bounded_native_window"
            native_paths[name] = path
            input_files.append({"season": season, "band": name, "path": str(path), "sha256": sha256_file(path), "source_role": source_role, "url": url})

        scl20 = _aligned_scl(native_paths["scl"], grid20)
        scl10 = _aligned_scl(native_paths["scl"], grid10)
        clear20, clear10 = cloud_clear_mask(scl20), cloud_clear_mask(scl10)
        snow20, snow10 = snow_mask(scl20), snow_mask(scl10)
        surface20, surface10 = clear20 & ~snow20, clear10 & ~snow10
        summary = temporal_scl_summary(scl20)
        for key in ("cloud_fraction", "cloud_shadow_fraction", "snow_or_ice_fraction", "topographic_shadow_fraction", "nodata_fraction"):
            if abs(summary[key] - float(metadata["aoi_scl"][key])) > 1.0 / scl20.size + 1e-9:
                raise ValueError(f"{season} SCL provenance mismatch for {key}: {summary[key]} vs {metadata['aoi_scl'][key]}")
        _write_byte(season_aligned / "scl_20m.tif", scl20, grid20)
        _write_byte(season_aligned / "cloud_clear_including_snow_20m.tif", clear20, grid20)
        _write_byte(season_aligned / "snow_20m.tif", snow20, grid20)

        reflectance10 = {name: apply_valid_mask(_aligned_band(native_paths[name], config["bands"][name], grid10), clear10) for name in TEN_METRE_BANDS}
        reflectance20 = {name: apply_valid_mask(_aligned_band(native_paths[name], config["bands"][name], grid20), clear20) for name in TWENTY_METRE_BANDS}
        nir20 = apply_valid_mask(_aligned_band(native_paths["nir"], config["bands"]["nir"], grid20), clear20)
        indices10 = {
            "ndvi": apply_valid_mask(_surface_index(reflectance10["nir"], reflectance10["red"]), clear10),
            "ndwi": apply_valid_mask(_surface_index(reflectance10["green"], reflectance10["nir"]), clear10),
            "brightness": apply_valid_mask(_mean_available(tuple(reflectance10.values())), clear10),
        }
        indices20 = {
            "ndmi": apply_valid_mask(_surface_index(nir20, reflectance20["swir16"]), clear20),
            "ndre": apply_valid_mask(_surface_index(reflectance20["nir_narrow"], reflectance20["rededge1"]), clear20),
            "swir_ratio": apply_valid_mask(_surface_index(reflectance20["swir16"], reflectance20["swir22"]), clear20),
        }
        for name, values in {**reflectance10, **indices10}.items(): _write_float(season_aligned / f"{name}_10m.tif", values, grid10)
        for name, values in {**reflectance20, **indices20}.items(): _write_float(season_aligned / f"{name}_20m.tif", values, grid20)

        illumination10 = cosine_illumination(terrain10["slope_mean"], terrain10["aspect_circular_mean"], metadata["sun_elevation_degrees"], metadata["sun_azimuth_degrees"])
        illumination20 = cosine_illumination(terrain20["slope_mean"], terrain20["aspect_circular_mean"], metadata["sun_elevation_degrees"], metadata["sun_azimuth_degrees"])
        _write_float(season_aligned / "cosine_illumination_10m.tif", illumination10, grid10)
        observations[season] = {
            "metadata": metadata, "native_paths": native_paths, "scl20": scl20,
            "clear10": clear10, "clear20": clear20, "snow10": snow10, "snow20": snow20,
            "surface10": surface10, "surface20": surface20,
            "reflectance10": reflectance10, "reflectance20": reflectance20,
            "indices10": indices10, "indices20": indices20,
            "illumination10": illumination10, "illumination20": illumination20,
            "scl_summary": summary,
        }

    temporal_fields: dict[str, np.ndarray] = {}
    temporal_reports: dict[str, Any] = {}
    for field in ("ndvi", "ndwi", "brightness"):
        stack = np.stack([observations[season]["indices10"][field] for season in SEASON_ORDER])
        surface_valid = np.stack([observations[season]["surface10"] for season in SEASON_ORDER])
        all_clear = np.stack([observations[season]["clear10"] for season in SEASON_ORDER])
        surface_stats = temporal_statistics(stack, surface_valid, coefficient_of_variation=(field == "brightness"))
        environmental_stats = temporal_statistics(stack, all_clear, coefficient_of_variation=(field == "brightness"))
        for statistic, values in surface_stats.items():
            if statistic == "count": _write_byte(temporal_root / f"{field}_surface_{statistic}_10m.tif", values, grid10)
            else: _write_float(temporal_root / f"{field}_surface_{statistic}_10m.tif", values, grid10)
        temporal_fields[f"{field}_median"] = surface_stats["median"]
        temporal_fields[f"{field}_range"] = surface_stats["range"]
        temporal_fields[f"{field}_stddev"] = surface_stats["standard_deviation"]
        temporal_fields[f"{field}_count"] = surface_stats["count"]
        if field == "brightness": temporal_fields["brightness_cv"] = surface_stats["coefficient_of_variation"]
        temporal_reports[field] = {
            "surface_snow_excluded": {name: numeric_summary(values, "count" if name == "count" else "dimensionless") for name, values in surface_stats.items()},
            "environmental_snow_retained": {name: numeric_summary(values, "count" if name == "count" else "dimensionless") for name, values in environmental_stats.items()},
        }
    for field in ("ndmi", "ndre", "swir_ratio"):
        stack = np.stack([observations[season]["indices20"][field] for season in SEASON_ORDER])
        surface_valid = np.stack([observations[season]["surface20"] for season in SEASON_ORDER])
        all_clear = np.stack([observations[season]["clear20"] for season in SEASON_ORDER])
        surface_stats = temporal_statistics(stack, surface_valid)
        environmental_stats = temporal_statistics(stack, all_clear)
        for statistic, values in surface_stats.items():
            if statistic == "count": _write_byte(temporal_root / f"{field}_surface_{statistic}_20m.tif", values, grid20)
            else: _write_float(temporal_root / f"{field}_surface_{statistic}_20m.tif", values, grid20)
        temporal_fields[f"{field}_median"] = surface_stats["median"]
        temporal_fields[f"{field}_range"] = surface_stats["range"]
        temporal_fields[f"{field}_stddev"] = surface_stats["standard_deviation"]
        temporal_fields[f"{field}_count"] = surface_stats["count"]
        temporal_reports[field] = {
            "surface_snow_excluded": {name: numeric_summary(values, "count" if name == "count" else "dimensionless") for name, values in surface_stats.items()},
            "environmental_snow_retained": {name: numeric_summary(values, "count" if name == "count" else "dimensionless") for name, values in environmental_stats.items()},
        }

    brightness_stack = np.stack([observations[season]["indices10"]["brightness"] for season in SEASON_ORDER])
    illumination_stack = np.stack([observations[season]["illumination10"] for season in SEASON_ORDER])
    surface_valid10 = np.stack([observations[season]["surface10"] for season in SEASON_ORDER])
    illumination_correlation = temporal_correlation(brightness_stack, illumination_stack, surface_valid10)
    temporal_fields["illumination_correlation"] = illumination_correlation
    _write_float(temporal_root / "brightness_cosine_illumination_correlation_10m.tif", illumination_correlation, grid10)
    snow_count20 = np.sum(np.stack([observations[season]["snow20"] for season in SEASON_ORDER]), axis=0).astype(np.uint8)
    temporal_fields["snow_count"] = snow_count20
    _write_byte(temporal_root / "snow_observation_count_20m.tif", snow_count20, grid20)

    low_ndvi, low_ndvi_threshold = _threshold_mask(temporal_fields["ndvi_stddev"], 0.25, high=False)
    low_brightness, low_brightness_threshold = _threshold_mask(temporal_fields["brightness_stddev"], 0.25, high=False)
    low_variability = low_ndvi & low_brightness
    low_ndvi_median, low_ndvi_median_threshold = _threshold_mask(temporal_fields["ndvi_median"], 0.25, high=False)
    persistent_low_ndvi = low_ndvi_median & low_ndvi & (temporal_fields["ndvi_count"] >= 3)
    high_phenology, high_phenology_threshold = _threshold_mask(temporal_fields["ndvi_range"], 0.75, high=True)
    high_moisture, high_moisture_threshold = _threshold_mask(temporal_fields["ndmi_range"], 0.75, high=True)
    illumination_range = np.nanmax(illumination_stack, axis=0) - np.nanmin(illumination_stack, axis=0)
    high_illumination_range, illumination_range_threshold = _threshold_mask(illumination_range, 0.75, high=True)
    illumination_sensitive = high_illumination_range & (np.abs(illumination_correlation) >= 0.8)
    for name, values, grid in (
        ("low_temporal_spectral_variability_10m", low_variability, grid10),
        ("persistent_low_ndvi_evidence_10m", persistent_low_ndvi, grid10),
        ("high_ndvi_variability_10m", high_phenology, grid10),
        ("high_ndmi_variability_20m", high_moisture, grid20),
        ("high_illumination_sensitivity_10m", illumination_sensitive, grid10),
    ): _write_byte(temporal_root / f"{name}.tif", values, grid)

    observation_summaries: dict[str, Any] = {}
    illumination_relationships: dict[str, Any] = {}
    for season in SEASON_ORDER:
        item = observations[season]
        all_indices = {**item["indices10"], **item["indices20"]}
        surface_masks = {name: item["surface10"] for name in item["indices10"]}
        surface_masks.update({name: item["surface20"] for name in item["indices20"]})
        observation_summaries[season] = {
            "metadata": item["metadata"],
            "actual_aoi_scl": item["scl_summary"],
            "indices_environmental_snow_retained": {
                name: numeric_summary(values, "dimensionless") for name, values in all_indices.items()
            },
            "indices_surface_snow_excluded": {
                name: numeric_summary(apply_valid_mask(values, surface_masks[name]), "dimensionless")
                for name, values in all_indices.items()
            },
        }
        illumination_relationships[season] = pearson_pair(
            item["indices10"]["brightness"],
            item["illumination10"],
        )

    northness10 = np.cos(np.radians(terrain10["aspect_circular_mean"]))
    eastness10 = np.sin(np.radians(terrain10["aspect_circular_mean"]))
    terrain_relationships: dict[str, Any] = {}
    for field in ("ndvi_median", "ndvi_range", "ndvi_stddev", "brightness_cv", "illumination_correlation"):
        for terrain_name, terrain_values in {
            "elevation_mean": terrain10["elevation_mean"], "slope_mean": terrain10["slope_mean"],
            "curvature_mean": terrain10["curvature_mean"], "roughness5_mean": terrain10["roughness5_mean"],
            "roughness15_mean": terrain10["roughness15_mean"], "roughness51_mean": terrain10["roughness51_mean"],
            "northness": northness10, "eastness": eastness10,
        }.items(): terrain_relationships[f"{field}__{terrain_name}"] = pearson_pair(temporal_fields[field], terrain_values)
    for field in ("ndmi_range", "ndre_range", "swir_ratio_range"):
        for terrain_name in ("elevation_mean", "slope_mean", "curvature_mean", "roughness5_mean", "roughness15_mean", "roughness51_mean"):
            terrain_relationships[f"{field}__{terrain_name}"] = pearson_pair(temporal_fields[field], terrain20[terrain_name])

    extent = (bounds[0], bounds[2], bounds[1], bounds[3])
    _plot_seasonal_rgb(observations, config["processing"]["common_rgb_display"], image_root / "seasonal-natural-colour-common-transform.png", extent)
    _plot_seasonal_field(observations, "ndvi", 10, image_root / "seasonal-ndvi.png", extent, "Seasonal NDVI (10 m, fixed scale)", "RdYlGn", -0.1, 0.9)
    _plot_seasonal_field(observations, "ndmi", 20, image_root / "seasonal-ndmi.png", extent, "Seasonal NDMI (20 m, fixed scale)", "BrBG", -0.4, 0.5)
    _plot_scl(observations, image_root / "seasonal-scene-classification.png", extent)
    _plot_illumination(observations, image_root / "seasonal-cosine-illumination.png", extent)
    _plot_temporal(temporal_fields, image_root / "temporal-evidence-summary.png", extent)
    _plot_relationships(temporal_fields, terrain10, image_root / "temporal-terrain-relationships.png")

    output_files = sorted(path for path in output_root.rglob("*") if path.is_file() and path.name != "lab005c-report.json")
    report: dict[str, Any] = {
        "schema_version": 1,
        "experiment": config["experiment"],
        "configuration_sha256": stable_json_sha256(config),
        "aoi": config["aoi"],
        "seasons": config["seasons"],
        "processing": config["processing"],
        "licence": config["licence"],
        "frozen_inputs": {**frozen, "canonical_r16_observed_sha256": sha256_file(r16_path), "lab005b_report_observed_sha256": sha256_file(lab005b_report_path)},
        "input_files": input_files,
        "observations": observation_summaries,
        "temporal_statistics": temporal_reports,
        "illumination": {
            "formula": "sin(sun_elevation)*cos(slope)+cos(sun_elevation)*sin(slope)*cos(sun_azimuth-aspect)",
            "terrain_scale": "Sentinel-cell aggregate mean slope and circular-mean aspect",
            "no_topographic_correction_applied": True,
            "brightness_relationship_by_observation": illumination_relationships,
            "illumination_range_summary": numeric_summary(illumination_range, "cosine_incidence_range"),
            "brightness_temporal_correlation_summary": numeric_summary(illumination_correlation, "pearson_r"),
        },
        "diagnostic_thresholds": {
            "low_variability": {"ndvi_stddev_p25": low_ndvi_threshold, "brightness_stddev_p25": low_brightness_threshold, "fraction": float(np.mean(low_variability))},
            "persistent_low_ndvi": {"ndvi_median_p25": low_ndvi_median_threshold, "ndvi_stddev_p25": low_ndvi_threshold, "minimum_valid_observations": 3, "fraction": float(np.mean(persistent_low_ndvi))},
            "high_vegetation_related_variability": {"ndvi_range_p75": high_phenology_threshold, "fraction": float(np.mean(high_phenology))},
            "high_moisture_related_variability": {"ndmi_range_p75": high_moisture_threshold, "fraction": float(np.mean(high_moisture))},
            "high_illumination_sensitivity": {"illumination_range_p75": illumination_range_threshold, "minimum_abs_brightness_correlation": 0.8, "fraction": float(np.mean(illumination_sensitive))},
            "interpretation": "Relative diagnostic evidence only; no mask is a rock, grass, scree, substrate or material class."
        },
        "terrain_relationships": terrain_relationships,
        "output_files": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in output_files],
    }
    report["deterministic_result_sha256"] = stable_json_sha256({key: value for key, value in report.items() if key != "output_files"})
    report_path = output_root / "lab005c-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.config)
    print(json.dumps({"observations": list(report["observations"]), "result_sha256": report["deterministic_result_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
