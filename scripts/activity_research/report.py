from __future__ import annotations

from typing import Any

from models import (
    LONG_STATIONARY_SECONDS,
    MAX_PLAUSIBLE_GPS_SPEED_MPS,
    TIMESTAMP_GAP_SECONDS,
)


def _format(value: float | int | None, digits: int = 1) -> str:
    return "Unavailable" if value is None else f"{value:,.{digits}f}"


def build_private_report(aggregate: dict[str, Any]) -> str:
    inventory = aggregate["inventory"]
    parsed = aggregate["parsed_recording_count"]
    usable = aggregate["usable_timestamped_gps_count"]
    sensor_lines = "\n".join(
        f"- {name.replace('_', ' ').title()}: {count}/{parsed} parsed recordings"
        for name, count in aggregate["sensor_activity_counts"].items()
    )
    device_lines = "\n".join(
        f"- {device}: {count} recording(s)"
        for device, count in list(aggregate["devices"].items())[:15]
    ) or "- No device metadata was decoded."
    format_lines = "\n".join(
        f"- {format_name}: {count}"
        for format_name, count in inventory["format_counts"].items()
    )
    signature_lines = "\n".join(
        f"- {name.replace('_', ' ')}: {count}"
        for name, count in aggregate["speed_signature_counts"].items()
    )
    format_quality_lines = "\n".join(
        f"- {name}: {values['usable_timestamped_gps']}/{values['parsed']} usable GPS; "
        f"{values['explicit_pause']} with explicit pause intervals"
        for name, values in aggregate["format_summaries"].items()
    )
    run_signatures = aggregate["catalogue_label_speed_signatures"].get("Run", {})
    run_signature_text = ", ".join(
        f"{name.replace('_', ' ')} {count}" for name, count in run_signatures.items()
    ) or "Unavailable"
    files = inventory["file_size_bytes"]
    intervals = aggregate["sample_interval_median_distribution_s"]
    distances = aggregate["movement_distance_distribution_m"]
    durations = aggregate["movement_duration_distribution_s"]
    dates = aggregate["recording_date_range"]
    return f"""# Meridian private Strava archive research report

This report contains aggregate diagnostics only. It deliberately excludes raw coordinates and route histories. Interpretive movement states are evidence labels, not ground-truth activity classifications.

## 1. Archive inventory

- Catalogue rows: {inventory['catalogue_rows']}
- Recording files: {inventory['recording_file_count']}
- Parsed in this run: {parsed} ({aggregate['mode']} mode)
- Compressed/uncompressed: {inventory['compressed_count']} / {inventory['uncompressed_count']}
- Zero-byte files: {len(inventory['zero_byte_files'])}
- Unknown-format files: {len(inventory['unknown_format_files'])}
- File size median/p90/max: {_format(files['median'] / 1024)} / {_format(files['p90'] / 1024)} / {_format(files['maximum'] / 1024)} KiB
- Catalogue date range: {inventory['catalogue_date_range']['first']} to {inventory['catalogue_date_range']['last']}
- Recording timestamp range: {dates['first']} to {dates['last']}
- Decoded samples / timestamped GPS samples: {aggregate['total_sample_count']:,} / {aggregate['total_timestamped_gps_count']:,}
- Complementary same-timestamp FIT records merged / conflicting field values retained as diagnostics: {aggregate['merged_same_timestamp_record_count']:,} / {aggregate['same_timestamp_field_conflict_count']:,}

### Formats

{format_lines}

### Format usability

{format_quality_lines}

## 2. Catalogue/file association

- CSV rows with filenames: {inventory['catalogue_filename_count']}
- Missing referenced recordings: {len(inventory['missing_referenced_files'])}
- Unassociated recording files: {len(inventory['unassociated_recording_files'])}
- Keys with multiple representations: {len(inventory['multiple_recordings_by_key'])}
- Exact duplicate byte groups: {len(inventory['exact_duplicate_file_groups'])}

The CSV is useful catalogue context, but movement evidence comes from decoded recording messages. Activity labels are not used as behavioural truth.

## 3. Usable movement evidence

- Recordings with at least two timestamped GPS points: {usable}/{parsed}
- Interpreted movement history: {_format(aggregate['total_interpreted_movement_distance_m'] / 1000)} km and {_format(aggregate['total_interpreted_movement_duration_s'] / 3600)} hours
- Per-recording median sampling interval p10/median/p90: {_format(intervals['p10'])} / {_format(intervals['median'])} / {_format(intervals['p90'])} seconds
- Movement-distance p10/median/p90: {_format((distances['p10'] or 0) / 1000)} / {_format((distances['median'] or 0) / 1000)} / {_format((distances['p90'] or 0) / 1000)} km
- Movement-duration p10/median/p90: {_format((durations['p10'] or 0) / 3600)} / {_format((durations['median'] or 0) / 3600)} / {_format((durations['p90'] or 0) / 3600)} hours

## 4. Devices

{device_lines}

## 5. Sensor availability

{sensor_lines}

Optional sensor values are preserved only when directly recorded. Device altitude remains diagnostic and is not treated as canonical terrain elevation.

## 6. Recording semantics

- Recordings containing explicit decoded FIT timer pause intervals: {aggregate['explicit_pause_activity_count']}
- Explicit pause intervals / total interval duration: {aggregate['explicit_pause_interval_count']} / {_format(aggregate['explicit_pause_seconds'] / 3600)} hours
- Recordings containing timestamp gaps over {TIMESTAMP_GAP_SECONDS:g} seconds: {aggregate['recording_gap_activity_count']}
- Recordings containing continuous stationary evidence: {aggregate['stationary_activity_count']}
- Recordings containing stationary episodes lasting at least {LONG_STATIONARY_SECONDS:g} seconds: {aggregate['long_stationary_activity_count']}
- Recordings containing at least one implausible GPS segment over {MAX_PLAUSIBLE_GPS_SPEED_MPS:g} m/s or non-increasing timestamp: {aggregate['suspicious_gps_activity_count']}
- Malformed/unreadable supported recordings during parsing: {aggregate['parse_error_count']}

Timer event types decoded: {aggregate['timer_event_type_counts']}

Segment evidence counts: {aggregate['total_state_counts']}

Explicit timer stop/start intervals, stationary recorded time, timestamp gaps, anomalous displacement, and uncertain data are kept separate. Long stationary periods are not assumed to be normal hiking breaks, and very slow but progressive movement is retained.

## 7. Descriptive movement signals

{signature_lines}

The 295 catalogue entries labelled Run alone span: {run_signature_text}. This is direct evidence that the catalogue label cannot select a movement model.

These signatures use only sustained GPS-derived speed distributions and are intentionally descriptive. They do not use Strava labels and are not movement-model classes. Gradient, cadence, DEM elevation and whole-activity context are needed before deciding whether multiple personal profiles are justified.

## 8. Canonical representation

Each recording is normalized into ordered optional samples, recorded events, laps, devices, session metadata and source provenance. Samples can preserve timestamp, GPS, recorded altitude, device distance/speed, heart rate, cadence, power, temperature and GPS accuracy. A separate terrain-request interface exposes timestamped GPS positions for future Meridian DEM enrichment; no DEM values are fabricated or downloaded in this stage.

## 9. Reliability assessment

Strong candidates for later calibration are timestamped GPS progression, movement continuity, recording-event timing, and—after common DEM enrichment—the relationship between gradient and sustained horizontal/vertical movement. Cadence and heart rate may help distinguish regimes only where coverage is sufficient.

Do not directly calibrate from Strava activity labels, total elapsed time, long stops, GPX/device elevation, or isolated instantaneous speed values. Do not interpret overzoomed GPS/DEM precision as terrain-scale truth.

## 10. Next experiment

Enrich a bounded, representative subset with the same Terrarium source and smoothing/gradient conventions used by Route Foundation v1. Derive interpretable movement segments, retain explicit pauses/gaps/stationary/anomalous evidence, fit a small transparent gradient-to-speed relationship on training activities, and evaluate it on held-out complete activities against Meridian's unchanged generic Tobler-style baseline.
"""
