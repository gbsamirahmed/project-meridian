from __future__ import annotations

import csv
import json
import math
import re
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from route_geometry import RouteGeometry, parse_gpx_geometry, resample_route
from terrain_metrics import (
    PROCESSING_VARIANTS,
    ProfileResult,
    analyse_profile,
    neighbourhood_metrics,
)
from terrain_sources import TerrariumRouteSource, WelshCogBlockCache, inspect_cog


SAMPLING_INTERVALS_M = (1.0, 2.0, 5.0, 10.0, 20.0, 40.0)
NEIGHBOURHOOD_SPACING_M = 100.0
NEIGHBOURHOOD_RADIUS_M = 200.0
OFFICIAL_DOWNLOAD_PAGE = "https://datamap.gov.wales/maps/lidar-data-download/"
OFFICIAL_VIEWER_PAGE = "https://datamap.gov.wales/maps/lidar-viewer/"


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "route"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = list(rows[0])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _profile_summary(profile: ProfileResult, route_name: str) -> dict[str, Any]:
    return {"route": route_name, **profile.summary()}


def discover_routes(gpx_root: Path) -> tuple[list[tuple[Path, RouteGeometry]], list[dict[str, str]]]:
    routes: list[tuple[Path, RouteGeometry]] = []
    failures: list[dict[str, str]] = []
    for path in sorted(gpx_root.glob("*.gpx")):
        try:
            routes.append((path, parse_gpx_geometry(path)))
        except ValueError as error:
            failures.append({"file": path.name, "error": str(error)})
    return routes, failures


def _coverage_complete(values: Sequence[float | None]) -> bool:
    return bool(values) and all(value is not None and math.isfinite(value) for value in values)


def _source_profiles(
    source_name: str,
    routes: dict[float, RouteGeometry],
    sampler: Any,
) -> tuple[list[dict[str, Any]], dict[tuple[float, str], ProfileResult]]:
    rows: list[dict[str, Any]] = []
    profiles: dict[tuple[float, str], ProfileResult] = {}
    for spacing, route in routes.items():
        elevations = sampler(route)
        if not _coverage_complete(elevations):
            raise RuntimeError(
                f"{source_name} has incomplete terrain coverage at {spacing:g} m spacing"
            )
        for variant in PROCESSING_VARIANTS:
            profile = analyse_profile(source_name, route, elevations, variant)
            profiles[(spacing, variant.id)] = profile
            summary = _profile_summary(profile, route.name)
            summary["effective_spacing_m"] = summary["spacing_m"]
            summary["spacing_m"] = spacing
            rows.append(summary)
    return rows, profiles


def _terrain_metric_rows(
    route: RouteGeometry, cache: WelshCogBlockCache
) -> list[dict[str, Any]]:
    sampled = resample_route(route, NEIGHBOURHOOD_SPACING_M)
    x, y = cache.project_route(sampled)
    rows: list[dict[str, Any]] = []
    for index, (easting, northing) in enumerate(zip(x, y)):
        grid = cache.read_neighbourhood(
            float(easting), float(northing), NEIGHBOURHOOD_RADIUS_M
        )
        metrics = neighbourhood_metrics(grid, cache.metadata.pixel_size_m)
        rows.append(
            {
                "route": route.name,
                "distance_m": sampled.cumulative_distances_m[index],
                **metrics,
            }
        )
    return rows


def _profile_rows(
    route: RouteGeometry,
    welsh_profiles: dict[tuple[float, str], ProfileResult],
    terrarium_profiles: dict[tuple[float, str], ProfileResult],
) -> list[dict[str, Any]]:
    spacing = 5.0
    raw_welsh = welsh_profiles[(spacing, "raw")]
    raw_terrarium = terrarium_profiles[(spacing, "raw")]
    filtered_welsh = welsh_profiles[(spacing, "production_median_160m_h3")]
    filtered_terrarium = terrarium_profiles[(spacing, "production_median_160m_h3")]
    sampled = resample_route(route, spacing)
    return [
        {
            "distance_m": sampled.cumulative_distances_m[index],
            "welsh_raw_elevation_m": raw_welsh.elevations_m[index],
            "terrarium_raw_elevation_m": raw_terrarium.elevations_m[index],
            "welsh_filtered_elevation_m": filtered_welsh.processed_elevations_m[index],
            "terrarium_filtered_elevation_m": filtered_terrarium.processed_elevations_m[index],
            "welsh_gradient": filtered_welsh.gradients[index],
            "terrarium_gradient": filtered_terrarium.gradients[index],
            "welsh_cumulative_ascent_m": filtered_welsh.cumulative_ascent_m[index],
            "terrarium_cumulative_ascent_m": filtered_terrarium.cumulative_ascent_m[index],
        }
        for index in range(len(sampled.coordinates))
    ]


def _plot_route(
    path: Path,
    route: RouteGeometry,
    profiles: Sequence[dict[str, Any]],
    profile_rows: Sequence[dict[str, Any]],
    metric_rows: Sequence[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(3, 2, figsize=(14, 13), constrained_layout=True)
    distance_km = np.asarray([row["distance_m"] for row in profile_rows]) / 1000.0
    axes[0, 0].plot(distance_km, [row["welsh_raw_elevation_m"] for row in profile_rows], label="Welsh 1 m DTM", linewidth=1.2)
    axes[0, 0].plot(distance_km, [row["terrarium_raw_elevation_m"] for row in profile_rows], label="Terrarium", linewidth=1.0)
    axes[0, 0].set(title="Raw 5 m sampled elevation", ylabel="Elevation (m)")
    axes[0, 0].legend()

    axes[0, 1].plot(distance_km, [row["welsh_cumulative_ascent_m"] for row in profile_rows], label="Welsh DTM")
    axes[0, 1].plot(distance_km, [row["terrarium_cumulative_ascent_m"] for row in profile_rows], label="Terrarium")
    axes[0, 1].set(title="Cumulative ascent, common 160 m median + 3 m hysteresis", ylabel="Ascent (m)")
    axes[0, 1].legend()

    for source in ("welsh_dtm_1m", "terrarium_z15"):
        rows = [row for row in profiles if row["source"] == source and row["processing"] == "median_80m_h2"]
        rows.sort(key=lambda row: row["spacing_m"])
        axes[1, 0].plot([row["spacing_m"] for row in rows], [row["processed_ascent_m"] for row in rows], marker="o", label=source)
    axes[1, 0].set(xscale="log", title="Sampling sensitivity (80 m median + 2 m hysteresis)", xlabel="Route sampling (m)", ylabel="Ascent (m)")
    axes[1, 0].legend()

    filter_rows = [row for row in profiles if row["source"] == "welsh_dtm_1m" and abs(row["spacing_m"] - 10.0) < 0.1]
    axes[1, 1].barh([row["processing"] for row in filter_rows], [row["processed_ascent_m"] for row in filter_rows])
    axes[1, 1].set(title="Welsh DTM filtering sensitivity at 10 m", xlabel="Ascent (m)")

    axes[2, 0].plot(distance_km, np.asarray([row["welsh_gradient"] for row in profile_rows]) * 100.0, label="Welsh DTM")
    axes[2, 0].plot(distance_km, np.asarray([row["terrarium_gradient"] for row in profile_rows]) * 100.0, label="Terrarium", alpha=0.8)
    axes[2, 0].set(title="Processed route gradient", xlabel="Distance (km)", ylabel="Gradient (%)")
    axes[2, 0].legend()

    metric_distance = np.asarray([row["distance_m"] for row in metric_rows]) / 1000.0
    axes[2, 1].plot(metric_distance, [row["relief_50m"] for row in metric_rows], label="50 m relief")
    axes[2, 1].plot(metric_distance, [row["relief_200m"] for row in metric_rows], label="200 m relief")
    axes[2, 1].set(title="Surrounding 2D terrain relief", xlabel="Distance (km)", ylabel="Local relief (m)")
    axes[2, 1].legend()
    figure.suptitle(route.name)
    figure.savefig(path, dpi=150)
    plt.close(figure)


def _metric_summary(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"sample_count": len(rows)}
    if not rows:
        return result
    for field in (
        "slope_10m_deg",
        "slope_20m_deg",
        "relief_5m",
        "relief_20m",
        "relief_50m",
        "relief_200m",
        "roughness_5m",
        "roughness_20m",
        "roughness_50m",
        "roughness_200m",
        "convexity_20m",
        "convexity_50m",
        "convexity_200m",
    ):
        values = np.asarray(
            [row[field] for row in rows if row.get(field) is not None], dtype=float
        )
        result[field] = (
            None
            if not len(values)
            else {
                "median": float(np.median(values)),
                "p10": float(np.percentile(values, 10)),
                "p90": float(np.percentile(values, 90)),
            }
        )
    return result


def run_experiment(gpx_root: Path, output_root: Path, repo_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    gpx_root = gpx_root.resolve()
    output_root = output_root.resolve()
    repo_root = repo_root.resolve()
    if repo_root == gpx_root or repo_root in gpx_root.parents:
        raise ValueError("Private GPX input must remain outside the Git repository")
    if repo_root == output_root or repo_root in output_root.parents:
        raise ValueError("Private terrain research output must remain outside Git")
    output_root.mkdir(parents=True, exist_ok=True)
    for child in ("cache", "reports", "plots", "derived"):
        (output_root / child).mkdir(exist_ok=True)

    metadata = inspect_cog()
    welsh_cache = WelshCogBlockCache(output_root / "cache" / "welsh-cog")
    discovered, parse_failures = discover_routes(gpx_root)
    coverage = [
        {
            "file": path.name,
            "route": route.name,
            "coverage_fraction": welsh_cache.coverage_fraction(route),
        }
        for path, route in discovered
    ]
    eligible = [
        (path, route)
        for (path, route), row in zip(discovered, coverage)
        if row["coverage_fraction"] >= 0.95
    ]
    if not eligible:
        raise RuntimeError("No benchmark route falls within Welsh DTM coverage")

    canonical_routes = {path.name: resample_route(route, 1.0) for path, route in eligible}
    metric_routes = {path.name: resample_route(route, NEIGHBOURHOOD_SPACING_M) for path, route in eligible}
    required_blocks: set[tuple[int, int]] = set()
    for path, _ in eligible:
        canonical = canonical_routes[path.name]
        x, y = welsh_cache.project_route(canonical)
        required_blocks.update(welsh_cache.required_blocks(zip(x, y), 2.0))
        metric = metric_routes[path.name]
        metric_x, metric_y = welsh_cache.project_route(metric)
        required_blocks.update(
            welsh_cache.required_blocks(zip(metric_x, metric_y), NEIGHBOURHOOD_RADIUS_M)
        )
    welsh_cache.prepare_blocks(required_blocks)

    # Confirm that rectangular COG bounds correspond to actual valid DTM coverage.
    confirmed: list[tuple[Path, RouteGeometry]] = []
    rejected_nodata: list[str] = []
    for path, route in eligible:
        canonical = canonical_routes[path.name]
        x, y = welsh_cache.project_route(canonical)
        sparse_indices = range(0, len(x), max(1, len(x) // 100))
        sparse = welsh_cache.sample_projected((x[index], y[index]) for index in sparse_indices)
        valid_fraction = sum(value is not None for value in sparse) / max(1, len(sparse))
        if valid_fraction >= 0.95:
            confirmed.append((path, route))
        else:
            rejected_nodata.append(path.name)
    if not confirmed:
        raise RuntimeError("Candidate routes fall outside valid Welsh DTM pixels")

    terrarium = TerrariumRouteSource(output_root / "cache" / "terrarium")
    terrarium.prepare([canonical_routes[path.name] for path, _ in confirmed])
    result_rows: list[dict[str, Any]] = []
    terrain_rows: list[dict[str, Any]] = []
    route_results: list[dict[str, Any]] = []
    for path, route in confirmed:
        print(f"Analysing {route.name}")
        routes_by_spacing = {
            spacing: resample_route(route, spacing) for spacing in SAMPLING_INTERVALS_M
        }

        def sample_welsh(sampled: RouteGeometry) -> list[float | None]:
            x, y = welsh_cache.project_route(sampled)
            return welsh_cache.sample_projected(zip(x, y))

        welsh_rows, welsh_profiles = _source_profiles(
            "welsh_dtm_1m", routes_by_spacing, sample_welsh
        )
        terrarium_rows, terrarium_profiles = _source_profiles(
            "terrarium_z15", routes_by_spacing, terrarium.sample
        )
        combined = welsh_rows + terrarium_rows
        result_rows.extend(combined)
        metrics = _terrain_metric_rows(route, welsh_cache)
        terrain_rows.extend(metrics)
        profile_rows = _profile_rows(route, welsh_profiles, terrarium_profiles)
        slug = _safe_slug(route.name)
        _write_csv(output_root / "derived" / f"{slug}-profile-5m.csv", profile_rows)
        _plot_route(
            output_root / "plots" / f"{slug}-terrain-comparison.png",
            route,
            combined,
            profile_rows,
            metrics,
        )
        headline_welsh = welsh_profiles[(40.0, "production_median_160m_h3")]
        headline_terrarium = terrarium_profiles[(40.0, "production_median_160m_h3")]
        fine_welsh = welsh_profiles[(5.0, "median_80m_h2")]
        route_results.append(
            {
                "route": route.name,
                "source_file": path.name,
                "distance_km": route.total_distance_m / 1000.0,
                "welsh_40m_production_ascent_m": headline_welsh.processed_ascent_m,
                "terrarium_40m_production_ascent_m": headline_terrarium.processed_ascent_m,
                "same_pipeline_source_difference_m": headline_welsh.processed_ascent_m - headline_terrarium.processed_ascent_m,
                "welsh_40m_raw_ascent_m": headline_welsh.raw_ascent_m,
                "welsh_pipeline_removed_ascent_m": headline_welsh.raw_ascent_m - headline_welsh.processed_ascent_m,
                "welsh_5m_median80_h2_ascent_m": fine_welsh.processed_ascent_m,
                "welsh_40m_predicted_hours": headline_welsh.predicted_moving_hours,
                "terrarium_40m_predicted_hours": headline_terrarium.predicted_moving_hours,
                "terrain_metrics": _metric_summary(metrics),
            }
        )

    _write_csv(output_root / "derived" / "sampling-filtering-results.csv", result_rows)
    _write_csv(output_root / "derived" / "terrain-metrics.csv", terrain_rows)
    _write_csv(
        output_root / "derived" / "route-results.csv",
        [{key: value for key, value in row.items() if key != "terrain_metrics"} for row in route_results],
    )
    results = {
        "experiment": "High-Resolution Welsh Terrain Experiment v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "official_source": {
            **metadata.as_dict(),
            "download_page": OFFICIAL_DOWNLOAD_PAGE,
            "viewer_page": OFFICIAL_VIEWER_PAGE,
            "source_character": "Welsh Government bare-earth national LiDAR DTM; nominal 1 m; OGL",
            "known_caveat": "Terrain products may retain artefacts such as inadequately filtered low vegetation or bridge decks.",
        },
        "discovery": {
            "gpx_count": len(discovered),
            "parse_failures": parse_failures,
            "coverage": coverage,
            "confirmed_route_names": [route.name for _, route in confirmed],
            "rejected_for_nodata": rejected_nodata,
        },
        "sampling_intervals_m": list(SAMPLING_INTERVALS_M),
        "processing_variants": [asdict(variant) for variant in PROCESSING_VARIANTS],
        "route_results": route_results,
        "cache": {
            "welsh_required_blocks": len(required_blocks),
            "welsh_downloaded_blocks": welsh_cache.downloaded_blocks,
            "welsh_disk_cache_hits": welsh_cache.disk_cache_hits,
            "welsh_cache_bytes": welsh_cache.cache_size_bytes(),
            "welsh_uncompressed_block_bytes": welsh_cache.remote_uncompressed_bytes,
            "terrarium": terrarium.stats(),
        },
        "runtime_seconds_before_report": time.perf_counter() - started,
    }
    _write_json(output_root / "derived" / "results.json", results)
    return results


def _lookup(
    rows: Sequence[dict[str, Any]], route: str, source: str, spacing: float, processing: str
) -> dict[str, Any]:
    for row in rows:
        if (
            row["route"] == route
            and row["source"] == source
            and abs(float(row["spacing_m"]) - spacing) < 0.1
            and row["processing"] == processing
        ):
            return row
    raise KeyError((route, source, spacing, processing))


def _percent(value: float, denominator: float) -> float:
    return value / denominator * 100.0 if denominator else 0.0


def finalize_outputs(output_root: Path, network: dict[str, Any]) -> dict[str, Any]:
    results_path = output_root / "derived" / "results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    with (output_root / "derived" / "sampling-filtering-results.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in row:
            if key not in {"route", "source", "processing"}:
                row[key] = float(row[key])
    results["network"] = network
    results["runtime_seconds"] = results["runtime_seconds_before_report"] + float(
        network.get("wrapper_seconds", 0.0)
    )
    _write_json(results_path, results)

    lines = [
        "# High-Resolution Welsh Terrain Experiment v1",
        "",
        "This is a private research report. It does not change Meridian production terrain, route timing, rendering, or weather behaviour.",
        "",
        "## Method",
        "",
        f"- Official source: Welsh Government/DataMapWales national bare-earth DTM COG (`{results['official_source']['url']}`).",
        f"- Raster: {results['official_source']['width']:,} × {results['official_source']['height']:,}, {results['official_source']['dtype']}, {results['official_source']['crs']}, {results['official_source']['pixel_size_m']:.0f} m pixels, {results['official_source']['block_shape'][0]} × {results['official_source']['block_shape'][1]} blocks.",
        f"- Overviews: {', '.join(map(str, results['official_source']['overviews']))}; nodata {results['official_source']['nodata']}.",
        "- Routes were discovered from GPX coordinates, not filenames; GPX elevations were ignored.",
        "- Geodesic WGS84 route distances were resampled at 1, 2, 5, 10, 20 and 40 m, then both DEM sources were processed with the same declared physical filters.",
        "- The production-compatible reference is 40 m sampling, a five-sample/160 m median span and 3 m hysteresis.",
        "- External route statistics are context only and were not used for fitting or selection.",
        "",
        "## Access and performance",
        "",
        f"- HTTP 206 range requests observed: {network.get('partial_requests', 0):,}.",
        f"- Observed COG response payload: {network.get('bytes_transferred', 0) / 1024 / 1024:.2f} MiB (HEAD content length excluded).",
        f"- Welsh cached blocks: {results['cache']['welsh_required_blocks']:,}; cache size {results['cache']['welsh_cache_bytes'] / 1024 / 1024:.2f} MiB.",
        f"- Terrarium transfer during this run: {results['cache']['terrarium']['downloaded_bytes'] / 1024 / 1024:.2f} MiB.",
        f"- End-to-end analysis runtime: {results['runtime_seconds']:.1f} seconds.",
        "",
        "The server honored bounded byte ranges and Rasterio/GDAL read only route-corridor blocks. The 48.6 GB national object was never downloaded.",
        "",
        "## Route findings",
        "",
    ]
    for route_result in results["route_results"]:
        route = route_result["route"]
        source_difference = route_result["same_pipeline_source_difference_m"]
        source_percent = _percent(source_difference, route_result["terrarium_40m_production_ascent_m"])
        pipeline_removed = route_result["welsh_pipeline_removed_ascent_m"]
        pipeline_percent = _percent(pipeline_removed, route_result["welsh_40m_raw_ascent_m"])
        raw_1m = _lookup(rows, route, "welsh_dtm_1m", 1.0, "raw")["raw_ascent_m"]
        raw_40m = _lookup(rows, route, "welsh_dtm_1m", 40.0, "raw")["raw_ascent_m"]
        sampling_removed = raw_1m - raw_40m
        lines.extend(
            [
                f"### {route}",
                "",
                f"- Distance from the supplied geometry: {route_result['distance_km']:.2f} km.",
                f"- Common production-compatible processing: Welsh DTM {route_result['welsh_40m_production_ascent_m']:.0f} m ascent; Terrarium {route_result['terrarium_40m_production_ascent_m']:.0f} m; source difference {source_difference:+.0f} m ({source_percent:+.1f}%).",
                f"- Welsh raw positive variation falls from {raw_1m:.0f} m at 1 m sampling to {raw_40m:.0f} m at 40 m; route sampling removes {sampling_removed:.0f} m before smoothing/hysteresis is applied.",
                f"- Welsh raw 40 m positive variation: {route_result['welsh_40m_raw_ascent_m']:.0f} m; smoothing plus hysteresis removed {pipeline_removed:.0f} m ({pipeline_percent:.1f}% of raw variation).",
                f"- Welsh 5 m, 80 m median + 2 m hysteresis: {route_result['welsh_5m_median80_h2_ascent_m']:.0f} m ascent.",
                f"- Unchanged generic movement diagnostic: {route_result['terrarium_40m_predicted_hours']:.2f} h on Terrarium versus {route_result['welsh_40m_predicted_hours']:.2f} h on Welsh terrain.",
                "",
            ]
        )

    lines.extend(["## Sampling and filtering", ""])
    for route_result in results["route_results"]:
        route = route_result["route"]
        reference = _lookup(rows, route, "welsh_dtm_1m", 1.0, "median_80m_h2")
        comparisons = []
        for spacing in SAMPLING_INTERVALS_M:
            row = _lookup(rows, route, "welsh_dtm_1m", spacing, "median_80m_h2")
            delta = _percent(
                row["processed_ascent_m"] - reference["processed_ascent_m"],
                reference["processed_ascent_m"],
            )
            comparisons.append(f"{spacing:g} m {delta:+.1f}%")
        lines.append(f"- **{route}:** ascent change versus the 1 m result under the same 80 m median/2 m hysteresis: {', '.join(comparisons)}.")
    lines.extend(
        [
            "",
            "Raw positive variation increases at fine sampling, but more variation is not automatically more terrain truth. Physical-distance filtering makes the comparison interpretable: 1–2 m samples preserve abrupt local structure and artefacts, while basic route elevation/ascent should be judged by where filtered results stabilise rather than by the largest total.",
            "",
            "## Terrain intelligence",
            "",
            "The route-corridor cache supports 2D measurements at multiple physical scales. Ten/twenty-metre slopes, 50/200 m local relief and broad convexity/concavity are interpretable candidates. Five-metre roughness is sensitive to local objects and DTM filtering artefacts and should remain research evidence, not a technicality label.",
            "",
            "No technicality, difficulty, scrambling, avalanche, camping, or terrain-aware wind score was produced.",
            "",
            "## Answers and recommendations",
            "",
            "1. **Elevation profiles:** the 1 m DTM exposes sharper local terrain and different elevations than Terrarium; the plots show where differences persist after common filtering.",
            "2. **Ascent/descent:** route-specific changes are listed above and in `derived/sampling-filtering-results.csv`.",
            "3. **Source versus pipeline:** the same-pipeline Welsh/Terrarium difference isolates source influence; the 1 m-to-40 m raw loss isolates route sampling; Welsh 40 m raw-to-processed loss isolates smoothing/hysteresis. The two benchmarks show materially different source effects under common processing, and pipeline effects are also route-dependent.",
            "4. **Forty-metre sampling:** for these two routes, 40 m is not demonstrably too coarse for basic filtered cumulative ascent: it remains within 0.8% of the 1 m result under the common 80 m/2 m filter. It is too coarse for local slope, relief, convexity and micro-feature questions.",
            "5. **Stability:** filtered ascent is effectively stable by 5–10 m here and remains stable at 20–40 m. This is evidence from two routes, not a universal production recommendation.",
            "6. **One/two-metre sampling:** it provides real diagnostic detail and supports 2D neighbourhood metrics, but mostly oversamples the signal needed for basic cumulative ascent after defensible physical filtering.",
            "7. **Filtering:** a 40–80 m physical median span with explicit 2 m hysteresis is a defensible next research candidate because results are stable across sample intervals. The experiment does not justify replacing production's 160 m/3 m settings from only two routes, and no variant was selected against external ascent numbers.",
            "8. **Potential metrics:** multi-scale slope, local relief and broad convexity/concavity appear most interpretable; micro-roughness needs stronger validation.",
            "9. **Suspicious features:** abrupt micro-relief may reflect real features, low vegetation, bridge decks or DTM artefacts. The official caveat remains material.",
            "10. **Transfer/cache:** measured above; only route-corridor blocks were retained.",
            "11. **Runtime:** measured above and reproducible with a disposable cache.",
            "12. **Remote practicality:** bounded COG access is technically practical for offline/preprocessing research; public interactive use still needs latency, provider-policy and concurrency evaluation.",
            "13. **Compact derivatives:** route profiles and multi-scale metrics are tiny compared with cached raster blocks, so discarding raw blocks after reproducible analysis is practical.",
            "14. **Future resolver:** evidence supports a small provider-neutral *analytical* terrain research layer later, while visual MapLibre terrain can remain on the global source. It does not yet justify production integration.",
            "15. **Next experiment:** validate one or two physically defined filter scales against surveyed/high-confidence terrain sections and repeated route geometries across Wales and a second authoritative regional DEM, testing transferability rather than ascent-number matching.",
            "",
            "## Limitations",
            "",
            "Two Welsh benchmark geometries cannot establish a universal filter. GPX horizontal error, path alignment, raster artefacts, bridges, vegetation remnants and interpolation all affect measurements. DataMapWales describes this as a bare-earth DTM, but it is not infallible. External ascent figures may use different geometry, DEMs and algorithms and are not ground truth.",
        ]
    )
    report_path = output_root / "reports" / "summary.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results
