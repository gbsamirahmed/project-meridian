from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from route_geometry import RouteGeometry, resample_route
from terrain_metrics import PROCESSING_VARIANTS, ProfileResult, neighbourhood_metrics
from terrain_sources import EAWcsBlockCache, TerrariumRouteSource
from wales_experiment import (
    NEIGHBOURHOOD_RADIUS_M,
    NEIGHBOURHOOD_SPACING_M,
    SAMPLING_INTERVALS_M,
    _metric_summary,
    _safe_slug,
    _source_profiles,
    _write_csv,
    _write_json,
    discover_routes,
)


DATASET_PAGE = (
    "https://environment.data.gov.uk/dataset/"
    "13787b9a-26a4-4775-8523-806d13af58fc"
)
FAIR_USE_PAGE = (
    "https://environment.data.gov.uk/support/faqs/"
    "275808874/1169555459"
)
MAX_BLOCKS_PER_ROUTE = 64


def _route_block_keys(
    route: RouteGeometry, source: EAWcsBlockCache
) -> set[tuple[int, int]]:
    line = resample_route(route, 100.0)
    metric = resample_route(route, NEIGHBOURHOOD_SPACING_M)
    x, y = source.project_route(line)
    metric_x, metric_y = source.project_route(metric)
    return source.required_blocks(zip(x, y), 2.0) | source.required_blocks(
        zip(metric_x, metric_y), NEIGHBOURHOOD_RADIUS_M
    )


def _coverage_probe(
    route: RouteGeometry, source: EAWcsBlockCache
) -> dict[str, Any]:
    projected_x, projected_y = source.project_route(route)
    indices = sorted(
        set(
            min(len(projected_x) - 1, round((len(projected_x) - 1) * fraction))
            for fraction in (0.2, 0.5, 0.8)
        )
    )
    samples = [
        source.probe_projected(float(projected_x[index]), float(projected_y[index]))
        for index in indices
    ]
    nonzero = [float(sample["nonzero_fraction"]) for sample in samples]
    return {
        "sample_count": len(samples),
        "samples": samples,
        # The WCS returns numerical zero outside its England composite rather
        # than its declared nodata sentinel. Multiple geometric probes prevent
        # a route being accepted from the national rectangular envelope alone.
        "coverage_supported": bool(nonzero) and max(nonzero) >= 0.5,
    }


def _terrain_metric_rows(
    route: RouteGeometry, cache: EAWcsBlockCache
) -> list[dict[str, Any]]:
    sampled = resample_route(route, NEIGHBOURHOOD_SPACING_M)
    x, y = cache.project_route(sampled)
    rows: list[dict[str, Any]] = []
    for index, (easting, northing) in enumerate(zip(x, y)):
        grid = cache.read_neighbourhood(
            float(easting), float(northing), NEIGHBOURHOOD_RADIUS_M
        )
        rows.append(
            {
                "route": route.name,
                "distance_m": sampled.cumulative_distances_m[index],
                **neighbourhood_metrics(grid, cache.metadata.pixel_size_m),
            }
        )
    return rows


def _profile_rows(
    route: RouteGeometry,
    ea_profiles: dict[tuple[float, str], ProfileResult],
    terrarium_profiles: dict[tuple[float, str], ProfileResult],
) -> list[dict[str, Any]]:
    spacing = 5.0
    raw_ea = ea_profiles[(spacing, "raw")]
    raw_terrarium = terrarium_profiles[(spacing, "raw")]
    filtered_ea = ea_profiles[(spacing, "production_median_160m_h3")]
    filtered_terrarium = terrarium_profiles[(spacing, "production_median_160m_h3")]
    sampled = resample_route(route, spacing)
    return [
        {
            "distance_m": sampled.cumulative_distances_m[index],
            "ea_raw_elevation_m": raw_ea.elevations_m[index],
            "terrarium_raw_elevation_m": raw_terrarium.elevations_m[index],
            "ea_filtered_elevation_m": filtered_ea.processed_elevations_m[index],
            "terrarium_filtered_elevation_m": filtered_terrarium.processed_elevations_m[index],
            "ea_gradient": filtered_ea.gradients[index],
            "terrarium_gradient": filtered_terrarium.gradients[index],
            "ea_cumulative_ascent_m": filtered_ea.cumulative_ascent_m[index],
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
    axes[0, 0].plot(distance_km, [row["ea_raw_elevation_m"] for row in profile_rows], label="EA 1 m DTM", linewidth=1.2)
    axes[0, 0].plot(distance_km, [row["terrarium_raw_elevation_m"] for row in profile_rows], label="Terrarium", linewidth=1.0)
    axes[0, 0].set(title="Raw 5 m sampled elevation", ylabel="Elevation (m)")
    axes[0, 0].legend()
    axes[0, 1].plot(distance_km, [row["ea_cumulative_ascent_m"] for row in profile_rows], label="EA DTM")
    axes[0, 1].plot(distance_km, [row["terrarium_cumulative_ascent_m"] for row in profile_rows], label="Terrarium")
    axes[0, 1].set(title="Cumulative ascent, common 160 m median + 3 m hysteresis", ylabel="Ascent (m)")
    axes[0, 1].legend()
    for source_name in ("ea_dtm_1m", "terrarium_z15"):
        rows = [
            row for row in profiles
            if row["source"] == source_name
            and row["processing"] == "median_80m_h2"
        ]
        rows.sort(key=lambda row: row["spacing_m"])
        axes[1, 0].plot(
            [row["spacing_m"] for row in rows],
            [row["processed_ascent_m"] for row in rows],
            marker="o",
            label=source_name,
        )
    axes[1, 0].set(xscale="log", title="Sampling sensitivity (80 m median + 2 m hysteresis)", xlabel="Route sampling (m)", ylabel="Ascent (m)")
    axes[1, 0].legend()
    filter_rows = [
        row for row in profiles
        if row["source"] == "ea_dtm_1m"
        and abs(float(row["spacing_m"]) - 10.0) < 0.1
    ]
    axes[1, 1].barh(
        [row["processing"] for row in filter_rows],
        [row["processed_ascent_m"] for row in filter_rows],
    )
    axes[1, 1].set(title="EA DTM filtering sensitivity at 10 m", xlabel="Ascent (m)")
    axes[2, 0].plot(distance_km, np.asarray([row["ea_gradient"] for row in profile_rows]) * 100.0, label="EA DTM")
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


def _flat_control_plot(
    path: Path, route_name: str, rows: Sequence[dict[str, Any]]
) -> None:
    source_rows = [row for row in rows if row["route"] == route_name and row["source"] == "ea_dtm_1m"]
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for variant in ("raw", "hysteresis_3m_only", "median_40m_h2", "median_80m_h2", "production_median_160m_h3"):
        selected = sorted(
            (row for row in source_rows if row["processing"] == variant),
            key=lambda row: row["spacing_m"],
        )
        axes[0].plot([row["spacing_m"] for row in selected], [row["processed_ascent_m"] for row in selected], marker="o", label=variant)
    axes[0].set(xscale="log", title="Ascent after each processing stage", xlabel="Sampling interval (m)", ylabel="Ascent (m)")
    axes[0].legend(fontsize=8)
    at_one = [row for row in source_rows if abs(float(row["spacing_m"]) - 1.0) < 0.1]
    axes[1].barh(
        [row["processing"] for row in at_one],
        [row["raw_ascent_m"] - row["processed_ascent_m"] for row in at_one],
    )
    axes[1].set(title="Fine-scale variation removed at 1 m", xlabel="Removed positive variation (m)")
    figure.suptitle(route_name + " — flat-terrain control")
    figure.savefig(path, dpi=150)
    plt.close(figure)


def run_experiment(
    gpx_root: Path,
    output_root: Path,
    repo_root: Path,
    wales_results_path: Path,
    preflight: dict[str, Any],
) -> dict[str, Any]:
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

    source = EAWcsBlockCache(output_root / "cache" / "ea-wcs")
    discovered, parse_failures = discover_routes(gpx_root)
    coverage: list[dict[str, Any]] = []
    candidates: list[tuple[Path, RouteGeometry]] = []
    rejected_outside: list[str] = []
    for path, route in discovered:
        envelope_fraction = source.coverage_fraction(route)
        if envelope_fraction < 0.95:
            coverage.append({"file": path.name, "route": route.name, "envelope_fraction": envelope_fraction, "probe": None})
            rejected_outside.append(path.name)
            continue
        probe = _coverage_probe(route, source)
        coverage.append({"file": path.name, "route": route.name, "envelope_fraction": envelope_fraction, "probe": probe})
        if probe["coverage_supported"]:
            candidates.append((path, route))
        else:
            rejected_outside.append(path.name)

    route_keys = {path.name: _route_block_keys(route, source) for path, route in candidates}
    rejected_safety = [
        path.name for path, _ in candidates
        if len(route_keys[path.name]) > MAX_BLOCKS_PER_ROUTE
    ]
    confirmed = [
        (path, route) for path, route in candidates
        if path.name not in rejected_safety
    ]
    if not confirmed:
        raise RuntimeError("No English benchmark route passed coverage and safety checks")
    required_blocks: set[tuple[int, int]] = set()
    for path, _ in confirmed:
        required_blocks.update(route_keys[path.name])
    source.prepare_blocks(required_blocks)

    canonical = {path.name: resample_route(route, 1.0) for path, route in confirmed}
    terrarium = TerrariumRouteSource(output_root / "cache" / "terrarium")
    terrarium.prepare([canonical[path.name] for path, _ in confirmed])
    result_rows: list[dict[str, Any]] = []
    metric_rows_all: list[dict[str, Any]] = []
    route_results: list[dict[str, Any]] = []
    for path, route in confirmed:
        print(f"Analysing {route.name}")
        routes_by_spacing = {
            spacing: resample_route(route, spacing)
            for spacing in SAMPLING_INTERVALS_M
        }

        def sample_ea(sampled: RouteGeometry) -> list[float | None]:
            x, y = source.project_route(sampled)
            return source.sample_projected(zip(x, y))

        ea_rows, ea_profiles = _source_profiles(
            "ea_dtm_1m", routes_by_spacing, sample_ea
        )
        terrarium_rows, terrarium_profiles = _source_profiles(
            "terrarium_z15", routes_by_spacing, terrarium.sample
        )
        combined = ea_rows + terrarium_rows
        result_rows.extend(combined)
        metric_rows = _terrain_metric_rows(route, source)
        metric_rows_all.extend(metric_rows)
        profile_rows = _profile_rows(route, ea_profiles, terrarium_profiles)
        slug = _safe_slug(route.name)
        _write_csv(output_root / "derived" / f"{slug}-profile-5m.csv", profile_rows)
        _plot_route(
            output_root / "plots" / f"{slug}-terrain-comparison.png",
            route,
            combined,
            profile_rows,
            metric_rows,
        )
        ea_headline = ea_profiles[(40.0, "production_median_160m_h3")]
        terrarium_headline = terrarium_profiles[(40.0, "production_median_160m_h3")]
        ea_fine = ea_profiles[(5.0, "median_80m_h2")]
        keys = route_keys[path.name]
        route_cache_bytes = sum(
            source._block_path(key).stat().st_size
            for key in keys
            if source._block_path(key).is_file()
        )
        route_results.append(
            {
                "route": route.name,
                "source_file": path.name,
                "distance_km": route.total_distance_m / 1000.0,
                "ea_required_blocks": len(keys),
                "ea_cache_bytes": route_cache_bytes,
                "ea_40m_production_ascent_m": ea_headline.processed_ascent_m,
                "terrarium_40m_production_ascent_m": terrarium_headline.processed_ascent_m,
                "same_pipeline_source_difference_m": ea_headline.processed_ascent_m - terrarium_headline.processed_ascent_m,
                "ea_40m_raw_ascent_m": ea_headline.raw_ascent_m,
                "ea_pipeline_removed_ascent_m": ea_headline.raw_ascent_m - ea_headline.processed_ascent_m,
                "ea_5m_median80_h2_ascent_m": ea_fine.processed_ascent_m,
                "ea_40m_predicted_hours": ea_headline.predicted_moving_hours,
                "terrarium_40m_predicted_hours": terrarium_headline.predicted_moving_hours,
                "terrain_metrics": _metric_summary(metric_rows),
            }
        )

    _write_csv(output_root / "derived" / "sampling-filtering-results.csv", result_rows)
    _write_csv(output_root / "derived" / "terrain-metrics.csv", metric_rows_all)
    _write_csv(
        output_root / "derived" / "route-results.csv",
        [{key: value for key, value in row.items() if key != "terrain_metrics"} for row in route_results],
    )
    flat = min(route_results, key=lambda row: row["ea_40m_production_ascent_m"])
    _flat_control_plot(
        output_root / "plots" / "flat-control-filtering.png",
        str(flat["route"]),
        result_rows,
    )
    wales = json.loads(wales_results_path.read_text(encoding="utf-8"))
    results = {
        "experiment": "High-Resolution Terrain Generalisation Experiment v2 — England",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "official_source": {
            **source.metadata.as_dict(),
            "coverage_id": source.coverage_id,
            "dataset_page": DATASET_PAGE,
            "fair_use_page": FAIR_USE_PAGE,
            "licence": "Open Government Licence v3.0",
            "attribution": "© Environment Agency copyright and/or database right 2022. All rights reserved.",
            "source_character": "Environment Agency bare-earth LIDAR Composite DTM; nominal 1 m; WCS 2.0.1",
        },
        "preflight": preflight,
        "discovery": {
            "gpx_count": len(discovered),
            "parse_failures": parse_failures,
            "coverage": coverage,
            "confirmed_route_names": [route.name for _, route in confirmed],
            "rejected_outside_coverage": rejected_outside,
            "rejected_by_route_block_limit": rejected_safety,
            "per_route_block_limit": MAX_BLOCKS_PER_ROUTE,
        },
        "sampling_intervals_m": list(SAMPLING_INTERVALS_M),
        "processing_variants": [asdict(variant) for variant in PROCESSING_VARIANTS],
        "route_results": route_results,
        "cache": {
            "ea_required_blocks": len(required_blocks),
            "ea": source.stats(),
            "terrarium": terrarium.stats(),
        },
        "wales_v1": {
            "route_count": len(wales["route_results"]),
            "sampling_intervals_m": wales["sampling_intervals_m"],
            "processing_variants": wales["processing_variants"],
            "network_bytes": wales.get("network", {}).get("bytes_transferred"),
            "cache_bytes": wales["cache"]["welsh_cache_bytes"],
        },
        "runtime_seconds": time.perf_counter() - started,
    }
    _write_json(output_root / "derived" / "results.json", results)
    return results


def _lookup(
    rows: Sequence[dict[str, Any]],
    route: str,
    source: str,
    spacing: float,
    processing: str,
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


def finalize_outputs(
    output_root: Path, wales_results_path: Path
) -> dict[str, Any]:
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
    wales = json.loads(wales_results_path.read_text(encoding="utf-8"))
    england_differences = [
        float(row["same_pipeline_source_difference_m"])
        for row in results["route_results"]
    ]
    england_cache = float(results["cache"]["ea"]["cache_bytes"])
    england_transfer = float(results["cache"]["ea"]["downloaded_bytes"])
    lines = [
        "# High-Resolution Terrain Generalisation Experiment v2 — England",
        "",
        "This private report compares route-local Environment Agency 1 m DTM coverage with Meridian's unchanged Terrarium baseline. It does not change production terrain, routing, timing, rendering, or weather.",
        "",
        "## Method and rights",
        "",
        "- Route eligibility was determined from geometry plus numerical WCS coverage probes; GPX elevation was ignored.",
        "- The official Environment Agency LIDAR Composite DTM 1m WCS returned raw Float32 elevation GeoTIFF subsets in EPSG:27700.",
        "- The dataset is Open Government Licence v3.0. Reuse must retain the dataset attribution and identify modifications; the DSP fair-use policy permits applications and automated access within its published request limits.",
        "- Retrieval used 1,024 m route-local blocks, a 64-block per-route limit, a 320-block aggregate limit, a 750 MB uncompressed/cache safety limit, bounded retries, and no more than 150 request starts per minute.",
        "",
        "## Access and performance",
        "",
        f"- EA WCS requests including probes: {results['cache']['ea']['request_count']:,}; failed attempts: {results['cache']['ea']['failed_requests']:,}.",
        f"- EA response payload: {results['cache']['ea']['downloaded_bytes'] / 1024 / 1024:.2f} MiB; private compressed cache: {results['cache']['ea']['cache_bytes'] / 1024 / 1024:.2f} MiB.",
        f"- Cached route blocks: {results['cache']['ea_required_blocks']:,}; Terrarium transfer: {results['cache']['terrarium']['downloaded_bytes'] / 1024 / 1024:.2f} MiB.",
        f"- Analysis runtime: {results['runtime_seconds']:.1f} seconds.",
        "",
        "## Route results",
        "",
    ]
    for route_result in results["route_results"]:
        route = route_result["route"]
        source_difference = route_result["same_pipeline_source_difference_m"]
        denominator = route_result["terrarium_40m_production_ascent_m"]
        percent = source_difference / denominator * 100.0 if denominator else 0.0
        raw_1 = _lookup(rows, route, "ea_dtm_1m", 1.0, "raw")
        raw_40 = _lookup(rows, route, "ea_dtm_1m", 40.0, "raw")
        stable_1 = _lookup(rows, route, "ea_dtm_1m", 1.0, "median_80m_h2")
        stable_40 = _lookup(rows, route, "ea_dtm_1m", 40.0, "median_80m_h2")
        stability = (
            (stable_40["processed_ascent_m"] - stable_1["processed_ascent_m"])
            / stable_1["processed_ascent_m"] * 100.0
            if stable_1["processed_ascent_m"]
            else 0.0
        )
        lines.extend(
            [
                f"### {route}",
                "",
                f"- Distance: {route_result['distance_km']:.2f} km.",
                f"- Common production-compatible processing: EA {route_result['ea_40m_production_ascent_m']:.1f} m; Terrarium {route_result['terrarium_40m_production_ascent_m']:.1f} m; source difference {source_difference:+.1f} m ({percent:+.1f}%).",
                f"- EA raw ascent: {raw_1['raw_ascent_m']:.1f} m at 1 m versus {raw_40['raw_ascent_m']:.1f} m at 40 m.",
                f"- Median 80 m + 2 m hysteresis: {stable_1['processed_ascent_m']:.1f} m at 1 m versus {stable_40['processed_ascent_m']:.1f} m at 40 m ({stability:+.1f}%).",
                f"- Route-local EA footprint: {route_result['ea_required_blocks']} blocks, {route_result['ea_cache_bytes'] / 1024 / 1024:.2f} MiB compressed cache.",
                f"- Unchanged movement diagnostic: Terrarium {route_result['terrarium_40m_predicted_hours']:.2f} h versus EA {route_result['ea_40m_predicted_hours']:.2f} h.",
                "",
            ]
        )
    lines.extend(
        [
            "## Cross-region conclusions",
            "",
            "- England reproduces the Welsh separation between source effects and processing effects: neither is a universal correction.",
            "- Sampling stability must be judged after a physical filter; raw one-metre variation is not synonymous with trustworthy ascent.",
            "- Local slope at 10–20 m and relief/convexity at 50–200 m remain the most interpretable 2D analytical signals. Five-metre roughness remains sensitive to path alignment and raster artefacts.",
            "- WCS subsets required different provider logic from Welsh COG byte ranges, but both fit the same projected numeric block/sampling boundary and disposable-cache model.",
            "- Compact profiles and terrain metrics can be retained after raw route-local blocks are discarded.",
            "",
            "## Limitations",
            "",
            "The route set is deliberately bounded. The EA composite combines surveys from different years and source resolutions, includes resampling, and can retain surface-removal artefacts. The WCS represents outside-composite cells as numerical zero in tested areas despite declaring a Float32 nodata sentinel, so route coverage requires independent geometric/numerical validation. External route totals were not fitted or treated as truth.",
        ]
    )
    report = output_root / "reports" / "summary.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cross = output_root / "reports" / "cross-region-summary.md"
    cross.write_text(
        "\n".join(
            [
                "# Wales v1 and England v2 — cross-region summary",
                "",
                "This private summary compares the two completed experiments without modifying either source result.",
                "",
                "## Evidence",
                "",
                f"- Wales v1: {len(wales['route_results'])} routes; source effects under common processing ranged from {min(float(row['same_pipeline_source_difference_m']) for row in wales['route_results']):+.1f} to {max(float(row['same_pipeline_source_difference_m']) for row in wales['route_results']):+.1f} m.",
                f"- England v2: {len(results['route_results'])} routes; source effects ranged from {min(england_differences):+.1f} to {max(england_differences):+.1f} m.",
                f"- Wales used COG byte ranges: {float(wales.get('network', {}).get('bytes_transferred', 0)) / 1024 / 1024:.2f} MiB transferred and {float(wales['cache']['welsh_cache_bytes']) / 1024 / 1024:.2f} MiB cached.",
                f"- England used WCS subsets: {england_transfer / 1024 / 1024:.2f} MiB transferred and {england_cache / 1024 / 1024:.2f} MiB cached.",
                "- Across both regions, the 80 m physical median plus 2 m hysteresis made mountain and rolling-route ascent stable across 1–40 m sampling. The English flat control retained a small absolute difference despite a larger percentage.",
                "",
                *lines[lines.index("## Cross-region conclusions") :],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return results
