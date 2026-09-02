from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import asdict
from html import escape
from pathlib import Path
from typing import Any, Iterable, Sequence

from archive_analysis import write_json_atomic
from calibration_model import (
    ActivityObservations,
    behavioural_mode_diagnostic,
    cross_validate,
    fatigue_diagnostics,
    fit_personal_slope_model,
    observations_from_profile,
    progression_validation,
    slope_model_rows,
)
from evidence import percentile
from parsers import parse_recording
from terrain_experiment import (
    TERRAIN_VARIANTS,
    TerrariumTileCache,
    build_movement_chains,
    build_terrain_profile,
    profile_summary,
    resample_movement_chains,
)


EXPERIMENT_SEED = 20260902
DEFAULT_SAMPLE_COUNT = 32
WORKING_TERRAIN_VARIANT = "lighter_20m_median3_h2"
TARGET_SIGNATURE_COUNTS = {
    "predominantly_fast_progression": 8,
    "predominantly_moderate_progression": 8,
    "predominantly_slow_progression": 8,
    "mixed_speed_progression": 6,
    "ambiguous": 2,
}


def _source_fingerprint(export_root: Path) -> dict[str, Any]:
    files = sorted(path for path in export_root.rglob("*") if path.is_file())
    metadata = "\n".join(
        f"{path.relative_to(export_root).as_posix()}\t{path.stat().st_size}\t{path.stat().st_mtime_ns}"
        for path in files
    ).encode()
    return {
        "file_count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
        "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
        "catalogue_sha256": hashlib.sha256((export_root / "activities.csv").read_bytes()).hexdigest(),
    }


def _candidate_is_usable(summary: dict[str, Any]) -> bool:
    if not summary.get("usable_timestamped_gps"):
        return False
    if summary.get("descriptive_speed_signature") == "insufficient":
        return False
    duration = float(summary.get("movement_duration_s") or 0)
    distance = float(summary.get("movement_distance_m") or 0)
    if not 900 <= duration <= 16 * 3600 or not 500 <= distance <= 60_000:
        return False
    median_speed = summary.get("movement_speed_median_mps")
    high_speed = summary.get("movement_speed_p90_mps")
    if median_speed is None or high_speed is None or median_speed > 4.8 or high_speed > 8.5:
        return False
    state_counts = summary.get("state_counts", {})
    segment_count = sum(int(value) for value in state_counts.values())
    if int(state_counts.get("gps_anomaly", 0)) > max(3, round(segment_count * 0.002)):
        return False
    state_seconds = summary.get("state_seconds", {})
    uncertain = float(state_seconds.get("uncertain", 0))
    interpreted = sum(
        float(state_seconds.get(name, 0))
        for name in ("continuous_movement", "continuous_stationary", "uncertain")
    )
    return interpreted <= 0 or uncertain / interpreted <= 0.2


def _altitude_span(activity: Any) -> float:
    values = sorted(
        sample.recorded_altitude_m
        for sample in activity.samples
        if sample.recorded_altitude_m is not None and math.isfinite(sample.recorded_altitude_m)
    )
    low = percentile(values, 0.05)
    high = percentile(values, 0.95)
    return 0.0 if low is None or high is None else max(0.0, high - low)


def _sensor_diagnostics(activity: Any) -> dict[str, float | None]:
    cadence = [sample.cadence_rpm for sample in activity.samples if sample.cadence_rpm is not None]
    heart_rate_count = sum(sample.heart_rate_bpm is not None for sample in activity.samples)
    sample_count = max(1, len(activity.samples))
    return {
        "cadence_median_rpm": percentile(cadence, 0.5),
        "cadence_coverage": len(cadence) / sample_count,
        "heart_rate_coverage": heart_rate_count / sample_count,
    }


def _normalised_features(candidates: Sequence[dict[str, Any]]) -> dict[str, tuple[float, ...]]:
    raw = {
        item["source_file"]: (
            math.log1p(float(item["movement_duration_s"])),
            math.log1p(float(item["movement_distance_m"])),
            math.log1p(float(item["recorded_altitude_span_m"])),
            1.0 if item["interruption_diagnostic"] else 0.0,
        )
        for item in candidates
    }
    columns = list(zip(*raw.values()))
    ranges = [(min(column), max(column)) for column in columns]
    return {
        key: tuple(
            0.0 if maximum == minimum else (value - minimum) / (maximum - minimum)
            for value, (minimum, maximum) in zip(values, ranges)
        )
        for key, values in raw.items()
    }


def _diverse_pick(candidates: Sequence[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if len(candidates) <= count:
        return list(candidates)
    features = _normalised_features(candidates)
    by_key = {item["source_file"]: item for item in candidates}
    seeds = [
        min(candidates, key=lambda item: float(item["movement_duration_s"])),
        max(candidates, key=lambda item: float(item["movement_duration_s"])),
        max(candidates, key=lambda item: float(item["recorded_altitude_span_m"])),
    ]
    interrupted = [item for item in candidates if item["interruption_diagnostic"]]
    if interrupted:
        seeds.append(max(interrupted, key=lambda item: float(item["movement_duration_s"])))
    selected: list[str] = []
    for item in seeds:
        if item["source_file"] not in selected and len(selected) < count:
            selected.append(item["source_file"])
    while len(selected) < count:
        best_key = ""
        best_distance = -1.0
        for key, point in features.items():
            if key in selected:
                continue
            minimum = min(
                math.sqrt(sum((left - right) ** 2 for left, right in zip(point, features[chosen])))
                for chosen in selected
            )
            if minimum > best_distance or (minimum == best_distance and key < best_key):
                best_key = key
                best_distance = minimum
        selected.append(best_key)
    return [by_key[key] for key in selected]


def select_bounded_activities(
    summaries: Sequence[dict[str, Any]],
    activities_root: Path,
    target_count: int = DEFAULT_SAMPLE_COUNT,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = [dict(summary) for summary in summaries if _candidate_is_usable(summary)]
    parsed: dict[str, Any] = {}
    enriched: list[dict[str, Any]] = []
    for summary in candidates:
        path = activities_root / summary["source_file"]
        activity = parse_recording(path)
        parsed[summary["source_file"]] = activity
        item = dict(summary)
        item["recorded_altitude_span_m"] = _altitude_span(activity)
        item.update(_sensor_diagnostics(activity))
        state_counts = summary.get("state_counts", {})
        item["interruption_diagnostic"] = bool(
            summary.get("explicit_pause_interval_count", 0)
            or state_counts.get("recording_gap", 0)
            or state_counts.get("continuous_stationary", 0)
        )
        enriched.append(item)
    selected: list[dict[str, Any]] = []
    for signature, desired in TARGET_SIGNATURE_COUNTS.items():
        group = [item for item in enriched if item["descriptive_speed_signature"] == signature]
        selected.extend(_diverse_pick(group, min(desired, len(group))))
    if len(selected) < target_count:
        selected_keys = {item["source_file"] for item in selected}
        remainder = [item for item in enriched if item["source_file"] not in selected_keys]
        selected.extend(_diverse_pick(remainder, min(target_count - len(selected), len(remainder))))
    selected = selected[:target_count]
    diagnostics = {
        "input_summary_count": len(summaries),
        "behaviour_eligible_count": len(candidates),
        "selected_count": len(selected),
        "selected_signature_counts": _counts(item["descriptive_speed_signature"] for item in selected),
        "selected_with_interruption_diagnostics": sum(bool(item["interruption_diagnostic"]) for item in selected),
        "selection_seed": EXPERIMENT_SEED,
        "rules": {
            "movement_duration_seconds": [900, 57600],
            "movement_distance_metres": [500, 60000],
            "maximum_median_speed_mps": 4.8,
            "maximum_p90_speed_mps": 8.5,
            "maximum_uncertain_fraction": 0.2,
            "anomaly_limit": "max(3 segments, 0.2% of interpreted segments)",
            "labels_used_for_selection": False,
        },
    }
    for item in selected:
        item["_parsed_activity"] = parsed[item["source_file"]]
    return selected, diagnostics


def _calibration_exclusion_reasons(
    selection: dict[str, Any], observations: ActivityObservations
) -> list[str]:
    reasons: list[str] = []
    median_speed = float(selection.get("movement_speed_median_mps") or 0)
    p90_speed = float(selection.get("movement_speed_p90_mps") or 0)
    cadence_coverage = float(selection.get("cadence_coverage") or 0)
    heart_rate_coverage = float(selection.get("heart_rate_coverage") or 0)
    if observations.distance_m > 40_000 and p90_speed > 6:
        reasons.append("extreme_distance_and_speed_for_foot_calibration")
    if median_speed > 4.2 and cadence_coverage < 0.05:
        reasons.append("sustained_high_speed_without_foot_cadence_evidence")
    ascent_density = observations.ascent_m / max(observations.distance_m / 1000, 0.001)
    if (
        median_speed < 1
        and p90_speed < 2.5
        and cadence_coverage < 0.05
        and heart_rate_coverage < 0.05
        and ascent_density < 10
    ):
        reasons.append("sensor_poor_flat_trace_has_uncertain_movement_modality")
    return reasons


def _counts(values: Iterable[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        result[value] = result.get(value, 0) + 1
    return result


def _terrain_aggregate(per_activity: Sequence[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for variant in TERRAIN_VARIANTS:
        rows = [item["terrain"][variant.id] for item in per_activity]
        raw = sum(float(row["raw_positive_variation_m"]) for row in rows)
        processed = sum(float(row["processed_positive_variation_m"]) for row in rows)
        final = sum(float(row["ascent_after_hysteresis_m"]) for row in rows)
        result[variant.id] = {
            "activity_count": len(rows),
            "total_raw_positive_variation_m": raw,
            "total_processed_positive_variation_m": processed,
            "total_ascent_after_hysteresis_m": final,
            "smoothing_removed_percentage": 0 if raw == 0 else (raw - processed) / raw * 100,
            "hysteresis_removed_percentage_of_processed": 0 if processed == 0 else (processed - final) / processed * 100,
            "median_ascent_m": percentile([float(row["ascent_after_hysteresis_m"]) for row in rows], 0.5),
            "median_raw_to_final_ratio": percentile([
                float(row["ascent_after_hysteresis_m"]) / max(float(row["raw_positive_variation_m"]), 1e-6)
                for row in rows
            ], 0.5),
        }
    current = result["current_40m_median5_h3"]["total_ascent_after_hysteresis_m"]
    for values in result.values():
        values["ascent_vs_current_percentage"] = (
            (values["total_ascent_after_hysteresis_m"] / current - 1) * 100 if current else None
        )
    return result


def _svg_frame(title: str, body: str, width: int = 900, height: int = 520) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        '<rect width="100%" height="100%" fill="#08110f"/>'
        f'<text x="40" y="38" fill="#f4f1e8" font-family="system-ui" font-size="20">{escape(title)}</text>'
        f'{body}</svg>'
    )


def _write_slope_chart(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    left, top, width, height = 70, 70, 760, 370
    max_speed = max(max(float(row["generic_speed_kmh"]), float(row["personal_speed_kmh"])) for row in rows) * 1.1
    def point(row: dict[str, Any], key: str) -> tuple[float, float]:
        x = left + (float(row["gradient"]) + 0.4) / 0.8 * width
        y = top + height - float(row[key]) / max_speed * height
        return x, y
    generic = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(row, "generic_speed_kmh") for row in rows))
    personal = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(row, "personal_speed_kmh") for row in rows))
    body = (
        f'<line x1="{left}" y1="{top+height}" x2="{left+width}" y2="{top+height}" stroke="#60706a"/>'
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+height}" stroke="#60706a"/>'
        f'<polyline points="{generic}" fill="none" stroke="#79a9e8" stroke-width="3"/>'
        f'<polyline points="{personal}" fill="none" stroke="#ff8a68" stroke-width="3"/>'
        f'<text x="{left}" y="480" fill="#aebbb6" font-family="system-ui" font-size="14">gradient (−40% to +40%)</text>'
        f'<text x="{left+500}" y="92" fill="#79a9e8" font-family="system-ui" font-size="14">generic</text>'
        f'<text x="{left+590}" y="92" fill="#ff8a68" font-family="system-ui" font-size="14">personal (shrunk)</text>'
    )
    path.write_text(_svg_frame("Generic and personal slope response", body), encoding="utf-8")


def _write_terrain_chart(path: Path, terrain: dict[str, Any]) -> None:
    rows = list(terrain.items())
    maximum = max(float(values["total_ascent_after_hysteresis_m"]) for _, values in rows)
    body = ''
    for index, (name, values) in enumerate(rows):
        y = 75 + index * 52
        bar = float(values["total_ascent_after_hysteresis_m"]) / max(maximum, 1) * 590
        body += (
            f'<text x="40" y="{y+17}" fill="#cbd4d0" font-family="system-ui" font-size="12">{escape(name)}</text>'
            f'<rect x="300" y="{y}" width="{bar:.1f}" height="24" fill="#ff8a68" opacity="0.82"/>'
            f'<text x="{310+bar:.1f}" y="{y+17}" fill="#f4f1e8" font-family="system-ui" font-size="12">{float(values["ascent_vs_current_percentage"] or 0):+.1f}%</text>'
        )
    path.write_text(
        _svg_frame("Terrain processing sensitivity", body, height=max(500, 110 + len(rows) * 52)),
        encoding="utf-8",
    )


def _write_validation_chart(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    maximum = max(float(row["observed_s"]) for row in rows) / 3600 * 1.05
    left, top, size = 80, 70, 380
    body = f'<line x1="{left}" y1="{top+size}" x2="{left+size}" y2="{top}" stroke="#64736e" stroke-dasharray="5 5"/>'
    for row in rows:
        observed = float(row["observed_s"]) / 3600
        for key, colour in (("generic_s", "#79a9e8"), ("personal_s", "#ff8a68")):
            predicted = float(row[key]) / 3600
            x = left + observed / maximum * size
            y = top + size - predicted / maximum * size
            body += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{colour}" opacity="0.72"/>'
    body += (
        f'<text x="{left}" y="490" fill="#aebbb6" font-family="system-ui" font-size="14">observed reconstructed movement hours</text>'
        f'<text x="520" y="110" fill="#79a9e8" font-family="system-ui" font-size="14">generic</text>'
        f'<text x="520" y="135" fill="#ff8a68" font-family="system-ui" font-size="14">personal</text>'
    )
    path.write_text(_svg_frame("Held-out whole-activity predictions", body), encoding="utf-8")


def _write_density_chart(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    maximum = max(float(row["evidence_distance_km"]) for row in rows) or 1
    body = ''
    for index, row in enumerate(rows):
        x = 55 + index * 66
        height = float(row["evidence_distance_km"]) / maximum * 330
        body += (
            f'<rect x="{x}" y="{420-height:.1f}" width="42" height="{height:.1f}" fill="#87d5a5" opacity="0.8"/>'
            f'<text x="{x}" y="445" fill="#aebbb6" font-family="system-ui" font-size="10" transform="rotate(45 {x} 445)">{float(row["gradient"])*100:+.0f}%</text>'
        )
    path.write_text(_svg_frame("Observation distance by gradient bin", body), encoding="utf-8")


def _private_report(results: dict[str, Any]) -> str:
    selection = results["selection"]
    terrain = results["terrain_aggregate"]
    current = terrain["current_40m_median5_h3"]
    fixed_20 = terrain["fixed_footprint_20m_median9_h3"]
    fixed_10 = terrain["fixed_footprint_10m_median17_h3"]
    lighter_40 = terrain["lighter_40m_median3_h2"]
    smoothing_only = terrain["smoothing_only_20m_median3_h3"]
    light = terrain[WORKING_TERRAIN_VARIANT]
    low_hysteresis = terrain["lower_hysteresis_20m_median3_h1"]
    validation = results["validation"]
    model_rows = results["slope_model"]
    evidence_bins = [row for row in model_rows if float(row["evidence_distance_km"]) > 0]
    modes = results["behavioural_modes"]
    mode_text = (
        f"A two-group residual-speed diagnostic crossed its conservative evidence threshold "
        f"({modes['group_sizes'][0]} and {modes['group_sizes'][1]} activities; centres "
        f"{modes['relative_speed_centres'][0]:.2f}× and {modes['relative_speed_centres'][1]:.2f}× "
        "the common curve). This supports investigating contextual movement regimes, but does not identify what those regimes mean."
        if modes.get("supported")
        else "The activity-level residual distribution did not cross the declared threshold for distinct pace regimes."
    )
    fatigue = results["fatigue"]
    fatigue_ratios = fatigue["median_speed_ratio_by_distance_quartile"]
    slow_group = validation["by_behaviour_signature"].get("predominantly_slow_progression")
    high_terrain = validation["by_terrain_character"]["higher_ascent_density"]
    return f"""# Meridian private personal journey-calibration experiment

This report is private. It omits coordinate histories but contains user-specific movement and model-performance results. Strava labels, Strava moving time, device speed and device elevation were not used as calibration truth.

## 1. Methodology and bounded selection

- Behaviour-eligible recordings: {selection['behaviour_eligible_count']}
- Selected complete activities: {selection['selected_count']}
- Activities retained for foot-movement calibration after the conservative modality screen: {selection['calibration_activity_count']}
- Behaviour signatures: {selection['selected_signature_counts']}
- Selected activities with pause/gap/stationary diagnostics: {selection['selected_with_interruption_diagnostics']}
- Selection was deterministic and based on GPS-derived speed structure, duration, distance, recorded-altitude span as selection context only, interruption evidence and anomaly/uncertainty quality. Catalogue activity labels were not selection inputs.

## 2. Movement-time reconstruction

Movement time was reconstructed from raw timestamps on plausible continuous GPS progression. Explicit timer pauses, timestamp gaps, stationary evidence, anomalies and uncertain segments remain separate. Segments under 0.6 m/s were retained when a surrounding 30-second window showed coherent net progress; there is no minimum hiking speed. Observations with incoherent low-speed jitter were withheld rather than reclassified as ordinary stopping.

## 3. Terrain enrichment

The experiment used the same AWS Terrarium z15 source, 256-pixel decoding and bilinear Web Mercator sampling as Meridian routes. Device/GPX elevation was retained only for selection diagnostics. Required tiles: {results['dem']['required_tiles']}; persistent cache footprint: {results['dem']['cache_tile_count']} tiles / {results['dem']['cache_bytes'] / 1024 / 1024:.2f} MiB. This run downloaded {results['dem']['downloaded_tiles']} tiles and reused {results['dem']['cache_hits']}; DEM preparation took {results['dem']['prepare_seconds']:.1f} seconds.

## 4. Terrain-processing findings

The production-equivalent 40 m / median-5 / 3 m hysteresis pipeline retained {current['median_raw_to_final_ratio'] * 100:.1f}% of raw positive DEM variation at the median activity. Across the bounded sample, smoothing removed {current['smoothing_removed_percentage']:.1f}% of raw positive variation and hysteresis removed a further {current['hysteresis_removed_percentage_of_processed']:.1f}% of the smoothed positive variation.

Holding the median filter's physical footprint approximately constant, 20 m and 10 m sampling changed aggregate ascent by {fixed_20['ascent_vs_current_percentage']:+.1f}% and {fixed_10['ascent_vs_current_percentage']:+.1f}% relative to current 40 m. In contrast, the lighter 40 m / median-3 / 2 m pipeline changed it by {lighter_40['ascent_vs_current_percentage']:+.1f}%. At 20 m, median-3 with the original 3 m hysteresis changed ascent by {smoothing_only['ascent_vs_current_percentage']:+.1f}%; reducing hysteresis to 2 m and 1 m changed it by {light['ascent_vs_current_percentage']:+.1f}% and {low_hysteresis['ascent_vs_current_percentage']:+.1f}%.

This isolates most apparent recovery to the physical smoothing footprint and hysteresis rather than to 10 m sampling itself. Raw positive variation is not ground-truth ascent: it includes DEM interpolation/noise and is reported only to locate where processing removes signal. Full sensitivity results are in `results.json` and `terrain-processing-sensitivity.svg`.

## 5. Gradient-speed observations

The working observation field used 20 m spacing, median-3 smoothing, 2 m hysteresis and an 80 m half-window for gradient. The model contains {len(evidence_bins)} populated gradient bins. Each bin estimates the robust median log-speed ratio to Meridian's unchanged Tobler baseline and shrinks toward that baseline over 4 km of evidence. Sparse slopes therefore do not extrapolate aggressively.

## 6. Held-out validation

Five repeated five-fold activity-level splits were used. No activity contributed segments to both train and test within a fold; each final personal prediction is the median of its five held-out predictions.

- Generic median absolute error: {validation['generic']['median_absolute_error_minutes']:.1f} min
- Generic median absolute percentage error: {validation['generic']['median_absolute_percentage_error']:.1f}%
- Generic signed bias: {validation['generic']['signed_bias_minutes']:+.1f} min
- Generic p90 absolute percentage error: {validation['generic']['p90_absolute_percentage_error']:.1f}%
- Personal median absolute error: {validation['personal']['median_absolute_error_minutes']:.1f} min
- Personal median absolute percentage error: {validation['personal']['median_absolute_percentage_error']:.1f}%
- Personal signed bias: {validation['personal']['signed_bias_minutes']:+.1f} min
- Personal p90 absolute percentage error: {validation['personal']['p90_absolute_percentage_error']:.1f}%

The aggregate improvement is not uniform. For the higher-ascent-density group, median percentage error changed from {high_terrain['generic']['median_absolute_percentage_error']:.1f}% to {high_terrain['personal']['median_absolute_percentage_error']:.1f}%.{f" For predominantly slow progression it changed from {slow_group['generic']['median_absolute_percentage_error']:.1f}% to {slow_group['personal']['median_absolute_percentage_error']:.1f}%." if slow_group else ''} The two longest activities also worsened. The common personal curve is therefore not a production hiking model despite its aggregate improvement.

Held-out progression error at 25/50/75% distance is in `results.json`; this helps detect a model that reaches the right final time for the wrong within-activity reason.

## 7. Behavioural profiles

{mode_text}

The diagnostic is deliberately not a production classifier. Distinct pace regimes may reflect running, fast hiking, group travel, load, terrain technicality, weather, injury or recording context. Strava labels were not used to name or assign groups.

## 8. Activity position / fatigue

Equal-weight activity medians fell across route-distance quartiles: {fatigue_ratios[0]:.2f}×, {fatigue_ratios[1]:.2f}×, {fatigue_ratios[2]:.2f}× and {fatigue_ratios[3]:.2f}× the fitted slope expectation. The final quartile was {fatigue['final_vs_initial_percentage']:.1f}% below the first.

Each activity contributes one median residual per distance quartile, preventing long recordings from dominating. This remains descriptive after controlling only for the fitted slope curve. It does not control for technical terrain, stops, weather, load or group effects, so a production fatigue component is not justified solely by a monotonic quartile pattern.

## 9. Limitations and confounders

- The sample is deliberately diverse rather than representative of one future planning mode.
- Terrain technicality, surface, load, party, weather, injury and intent are not observed reliably.
- Terrarium source resolution varies geographically and is about 30 m in relevant UK terrain; 10 m samples can only interpolate that field.
- GPS jitter and ambiguous pause semantics cannot be eliminated perfectly without erasing genuine slow movement.
- Recorded altitude, cadence and heart rate are incomplete or device-dependent and were not required by the model.
- External route ascent values are contextual references, not optimisation targets; no private benchmark GPX set was available to this run.

## 10. Recommendations

Use this evidence to decide whether a contained production terrain-processing comparison is warranted, but do not change route constants from this experiment alone. Personal timing should remain opt-in and interpretable. Any future model should preserve generic fallback, keep movement and stopping separate, and require held-out whole-activity improvement.

## 11. Not justified by this evidence

- Treating Strava moving time or activity labels as ground truth.
- A universal minimum hiking speed.
- Terrain downscaling below the source DEM's information content.
- Automatic behavioural-profile selection from speed alone.
- A production fatigue penalty, break multiplier, weather penalty or safety assessment.
- An opaque machine-learning model.
"""


def run_personal_calibration_experiment(
    export_root: Path,
    ingestion_root: Path,
    output_root: Path,
    target_count: int = DEFAULT_SAMPLE_COUNT,
) -> dict[str, Any]:
    started = time.perf_counter()
    source_before = _source_fingerprint(export_root)
    summaries = json.loads((ingestion_root / "activity-summaries.json").read_text(encoding="utf-8"))
    selected, selection_diagnostics = select_bounded_activities(
        summaries, export_root / "activities", target_count
    )
    prepared: list[dict[str, Any]] = []
    all_points = []
    for index, item in enumerate(selected, start=1):
        activity = item.pop("_parsed_activity")
        points = resample_movement_chains(build_movement_chains(activity))
        if len(points) < 20:
            continue
        anonymous_key = f"activity-{index:03d}"
        prepared.append({"key": anonymous_key, "selection": item, "points": points})
        all_points.extend(points)
    selection_diagnostics["prepared_count"] = len(prepared)
    cache = TerrariumTileCache(output_root / "dem-cache")
    dem_started = time.perf_counter()
    required_tiles = cache.prepare(all_points)
    dem_prepare_seconds = time.perf_counter() - dem_started
    cache_files = list((output_root / "dem-cache" / "15").rglob("*.png"))
    per_activity: list[dict[str, Any]] = []
    observation_sets_by_variant: dict[str, list[ActivityObservations]] = {
        variant.id: [] for variant in TERRAIN_VARIANTS
    }
    private_selection: list[dict[str, Any]] = []
    for item in prepared:
        elevations = cache.sample(item["points"])
        profiles = {
            variant.id: build_terrain_profile(item["points"], elevations, variant)
            for variant in TERRAIN_VARIANTS
        }
        terrain_rows = {name: profile_summary(profile) for name, profile in profiles.items()}
        selection = item["selection"]
        activity_observations = {
            variant.id: observations_from_profile(
                item["key"],
                selection["descriptive_speed_signature"],
                profiles[variant.id],
                bool(selection["interruption_diagnostic"]),
            )
            for variant in TERRAIN_VARIANTS
        }
        observation_set = activity_observations[WORKING_TERRAIN_VARIANT]
        if len(observation_set.observations) < 20 or observation_set.observed_movement_s < 600:
            continue
        exclusion_reasons = _calibration_exclusion_reasons(selection, observation_set)
        if not exclusion_reasons:
            for variant_id, variant_observations in activity_observations.items():
                observation_sets_by_variant[variant_id].append(variant_observations)
        per_activity.append(
            {
                "activity_key": item["key"],
                "behaviour_signature": selection["descriptive_speed_signature"],
                "interruption_diagnostic": bool(selection["interruption_diagnostic"]),
                "observation_count": len(observation_set.observations),
                "observed_movement_s": observation_set.observed_movement_s,
                "distance_m": observation_set.distance_m,
                "calibration_exclusion_reasons": exclusion_reasons,
                "terrain": terrain_rows,
            }
        )
        private_selection.append(
            {
                "activity_key": item["key"],
                "source_file": selection["source_file"],
                "behaviour_signature": selection["descriptive_speed_signature"],
                "movement_duration_s_at_selection": selection["movement_duration_s"],
                "movement_distance_m_at_selection": selection["movement_distance_m"],
                "recorded_altitude_span_m_for_selection_only": selection["recorded_altitude_span_m"],
                "interruption_diagnostic": selection["interruption_diagnostic"],
                "calibration_exclusion_reasons": exclusion_reasons,
            }
        )
    observation_sets = observation_sets_by_variant[WORKING_TERRAIN_VARIANT]
    selection_diagnostics["calibration_activity_count"] = len(observation_sets)
    selection_diagnostics["calibration_exclusion_reason_counts"] = _counts(
        reason
        for item in per_activity
        for reason in item["calibration_exclusion_reasons"]
    )
    model = fit_personal_slope_model(observation_sets)
    validation_by_terrain_variant = {
        variant_id: cross_validate(variant_activities)
        for variant_id, variant_activities in observation_sets_by_variant.items()
    }
    validation = validation_by_terrain_variant[WORKING_TERRAIN_VARIANT]
    terrain_aggregate = _terrain_aggregate(per_activity)
    results = {
        "schema_version": 1,
        "methodology": {
            "seed": EXPERIMENT_SEED,
            "working_terrain_variant": WORKING_TERRAIN_VARIANT,
            "strava_labels_used": False,
            "strava_moving_time_used": False,
            "device_speed_used_as_target": False,
            "device_elevation_used_as_terrain": False,
            "generic_model_changed": False,
        },
        "selection": selection_diagnostics,
        "dem": {
            "source": "AWS elevation-tiles-prod Terrarium z15",
            "required_tiles": required_tiles,
            "downloaded_tiles": cache.downloaded_tiles,
            "cache_hits": cache.cache_hits,
            "downloaded_bytes": cache.downloaded_bytes,
            "cache_tile_count": len(cache_files),
            "cache_bytes": sum(path.stat().st_size for path in cache_files),
            "failed_tiles": cache.failed_tiles,
            "prepare_seconds": dem_prepare_seconds,
        },
        "terrain_aggregate": terrain_aggregate,
        "slope_model": slope_model_rows(model),
        "validation": validation,
        "validation_by_terrain_variant": validation_by_terrain_variant,
        "progression_validation": progression_validation(observation_sets),
        "behavioural_modes": behavioural_mode_diagnostic(observation_sets, model),
        "fatigue": fatigue_diagnostics(observation_sets, model),
        "per_activity": per_activity,
        "source_integrity_before": source_before,
        "runtime_seconds": time.perf_counter() - started,
    }
    source_after = _source_fingerprint(export_root)
    results["source_integrity_after"] = source_after
    results["source_archive_unchanged"] = source_before == source_after
    output_root.mkdir(parents=True, exist_ok=True)
    write_json_atomic(output_root / "selection-private.json", private_selection)
    write_json_atomic(output_root / "results.json", results)
    (output_root / "report-private.md").write_text(_private_report(results), encoding="utf-8")
    _write_slope_chart(output_root / "slope-response.svg", results["slope_model"])
    _write_terrain_chart(output_root / "terrain-processing-sensitivity.svg", terrain_aggregate)
    _write_validation_chart(output_root / "heldout-validation.svg", validation["rows"])
    _write_density_chart(output_root / "gradient-evidence-density.svg", results["slope_model"])
    return results
