from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from evidence import percentile, summarize_activity
from models import RecordingState, SUPPORTED_FORMATS
from parsers import detect_recording_format, parse_recording, recording_key


def load_catalogue(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_catalogue_date(value: str) -> datetime | None:
    for pattern in (
        "%b %d, %Y, %I:%M:%S %p",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            return datetime.strptime(value.strip(), pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _normalise_reference(value: str) -> str:
    return value.strip().replace("\\", "/").lstrip("./")


def inventory_export(export_root: Path) -> dict[str, Any]:
    rows = load_catalogue(export_root / "activities.csv")
    files = sorted(path for path in (export_root / "activities").rglob("*") if path.is_file())
    relative_files = {path.relative_to(export_root).as_posix(): path for path in files}
    references = [_normalise_reference(row.get("Filename", "")) for row in rows]
    referenced = {reference for reference in references if reference}
    by_key: dict[str, list[str]] = defaultdict(list)
    for relative, path in relative_files.items():
        by_key[recording_key(path)].append(relative)
    zero_byte: list[str] = []
    unreadable: list[str] = []
    for relative, path in relative_files.items():
        if path.stat().st_size == 0:
            zero_byte.append(relative)
            continue
        try:
            with path.open("rb") as stream:
                stream.read(1)
        except OSError:
            unreadable.append(relative)
    exact_duplicates: list[list[str]] = []
    size_groups: dict[int, list[Path]] = defaultdict(list)
    for path in files:
        size_groups[path.stat().st_size].append(path)
    for same_size in size_groups.values():
        if len(same_size) < 2 or same_size[0].stat().st_size == 0:
            continue
        hashes: dict[str, list[str]] = defaultdict(list)
        for path in same_size:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hashes[digest].append(path.relative_to(export_root).as_posix())
        exact_duplicates.extend(
            sorted(group) for group in hashes.values() if len(group) > 1
        )
    dates = [
        parsed
        for row in rows
        if (parsed := parse_catalogue_date(row.get("Activity Date", ""))) is not None
    ]
    sizes = [path.stat().st_size for path in files]
    format_counts = Counter(detect_recording_format(path) for path in files)
    return {
        "catalogue_rows": len(rows),
        "catalogue_filename_count": sum(bool(reference) for reference in references),
        "unique_catalogue_filenames": len(referenced),
        "recording_file_count": len(files),
        "format_counts": dict(sorted(format_counts.items())),
        "compressed_count": sum(
            detect_recording_format(path).endswith(".gz") for path in files
        ),
        "uncompressed_count": sum(
            not detect_recording_format(path).endswith(".gz") for path in files
        ),
        "unknown_format_files": sorted(
            relative
            for relative, path in relative_files.items()
            if detect_recording_format(path) not in SUPPORTED_FORMATS
        ),
        "zero_byte_files": zero_byte,
        "unreadable_files": unreadable,
        "file_size_bytes": {
            "minimum": min(sizes) if sizes else None,
            "median": percentile(sizes, 0.5),
            "p90": percentile(sizes, 0.9),
            "maximum": max(sizes) if sizes else None,
            "total": sum(sizes),
        },
        "catalogue_date_range": {
            "first": min(dates).isoformat() if dates else None,
            "last": max(dates).isoformat() if dates else None,
        },
        "missing_referenced_files": sorted(
            reference for reference in referenced if reference not in relative_files
        ),
        "unassociated_recording_files": sorted(
            relative for relative in relative_files if relative not in referenced
        ),
        "multiple_recordings_by_key": {
            key: sorted(paths) for key, paths in by_key.items() if len(paths) > 1
        },
        "exact_duplicate_file_groups": exact_duplicates,
        "activity_label_counts": dict(
            Counter((row.get("Activity Type") or "<missing>").strip() for row in rows)
        ),
        "files": [str(path) for path in files],
    }


def select_representative_files(paths: Sequence[Path], sample_size: int) -> list[Path]:
    by_format: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        by_format[detect_recording_format(path)].append(path)
    selected: list[Path] = []
    for group in by_format.values():
        ordered = sorted(group, key=lambda path: path.stat().st_size)
        for index in {0, len(ordered) // 2, len(ordered) - 1}:
            candidate = ordered[index]
            if candidate not in selected:
                selected.append(candidate)
    remaining = sorted(
        (path for path in paths if path not in selected),
        key=lambda path: (path.stat().st_size, path.name),
    )
    while len(selected) < min(sample_size, len(paths)) and remaining:
        fraction = len(selected) / max(1, sample_size - 1)
        position = min(round((len(remaining) - 1) * fraction), len(remaining) - 1)
        selected.append(remaining.pop(position))
    return selected[:sample_size]


def _distribution(values: Sequence[float]) -> dict[str, float | None]:
    return {
        "p10": percentile(values, 0.1),
        "median": percentile(values, 0.5),
        "p90": percentile(values, 0.9),
    }


def aggregate_diagnostics(
    inventory: dict[str, Any],
    summaries: Sequence[dict[str, Any]],
    parse_errors: Sequence[dict[str, str]],
    mode: str,
) -> dict[str, Any]:
    usable = [summary for summary in summaries if summary["usable_timestamped_gps"]]
    sensor_names = (
        "recorded_altitude",
        "device_distance",
        "device_speed",
        "heart_rate",
        "cadence",
        "power",
        "temperature",
        "gps_accuracy",
    )
    devices = Counter(
        device
        for summary in summaries
        for device in summary.get("devices", [])
        if device and device != "Unknown"
    )
    timestamps = [
        datetime.fromisoformat(value)
        for summary in summaries
        for value in (summary.get("first_timestamp"), summary.get("last_timestamp"))
        if value
    ]
    interval_medians = [
        summary["sample_interval_median_s"]
        for summary in usable
        if summary["sample_interval_median_s"] is not None
    ]
    movement_distances = [summary["movement_distance_m"] for summary in usable]
    movement_durations = [summary["movement_duration_s"] for summary in usable]
    format_summaries: dict[str, dict[str, int]] = {}
    for format_name in sorted({summary["source_format"] for summary in summaries}):
        matching = [
            summary for summary in summaries if summary["source_format"] == format_name
        ]
        format_summaries[format_name] = {
            "parsed": len(matching),
            "usable_timestamped_gps": sum(
                bool(summary["usable_timestamped_gps"]) for summary in matching
            ),
            "explicit_pause": sum(
                summary["explicit_pause_interval_count"] > 0 for summary in matching
            ),
        }
    state_counts: Counter[str] = Counter()
    state_seconds: Counter[str] = Counter()
    timer_event_types: Counter[str] = Counter()
    for summary in summaries:
        state_counts.update(summary["state_counts"])
        state_seconds.update(summary["state_seconds"])
        timer_event_types.update(summary["timer_event_type_counts"])
    label_signatures: dict[str, Counter[str]] = defaultdict(Counter)
    for summary in summaries:
        label_signatures[summary.get("catalogue_label") or "<missing>"][
            summary["descriptive_speed_signature"]
        ] += 1
    return {
        "mode": mode,
        "parsed_recording_count": len(summaries),
        "parse_error_count": len(parse_errors),
        "parse_errors": list(parse_errors),
        "usable_timestamped_gps_count": len(usable),
        "recording_date_range": {
            "first": min(timestamps).isoformat() if timestamps else None,
            "last": max(timestamps).isoformat() if timestamps else None,
        },
        "devices": dict(devices.most_common()),
        "format_summaries": format_summaries,
        "total_sample_count": sum(summary["sample_count"] for summary in summaries),
        "total_timestamped_gps_count": sum(
            summary["timestamped_gps_count"] for summary in summaries
        ),
        "merged_same_timestamp_record_count": sum(
            summary["merged_same_timestamp_record_count"] for summary in summaries
        ),
        "same_timestamp_field_conflict_count": sum(
            summary["same_timestamp_field_conflict_count"] for summary in summaries
        ),
        "sensor_activity_counts": {
            name: sum(summary["sensor_counts"].get(name, 0) > 0 for summary in summaries)
            for name in sensor_names
        },
        "sensor_sample_counts": {
            name: sum(summary["sensor_counts"].get(name, 0) for summary in summaries)
            for name in sensor_names
        },
        "timer_event_type_counts": dict(timer_event_types),
        "total_state_counts": dict(state_counts),
        "total_state_seconds": dict(state_seconds),
        "explicit_pause_interval_count": sum(
            summary["explicit_pause_interval_count"] for summary in summaries
        ),
        "explicit_pause_seconds": sum(
            summary["explicit_pause_seconds"] for summary in summaries
        ),
        "explicit_pause_activity_count": sum(
            summary["explicit_pause_interval_count"] > 0 for summary in summaries
        ),
        "recording_gap_activity_count": sum(
            summary["state_counts"].get(RecordingState.RECORDING_GAP.value, 0) > 0
            for summary in summaries
        ),
        "stationary_activity_count": sum(
            summary["state_counts"].get(RecordingState.STATIONARY.value, 0) > 0
            for summary in summaries
        ),
        "long_stationary_activity_count": sum(
            summary["long_stationary_episode_count"] > 0 for summary in summaries
        ),
        "suspicious_gps_activity_count": sum(
            summary["state_counts"].get(RecordingState.ANOMALOUS.value, 0) > 0
            for summary in summaries
        ),
        "sample_interval_median_distribution_s": _distribution(interval_medians),
        "movement_distance_distribution_m": _distribution(movement_distances),
        "movement_duration_distribution_s": _distribution(movement_durations),
        "total_interpreted_movement_distance_m": sum(movement_distances),
        "total_interpreted_movement_duration_s": sum(movement_durations),
        "speed_signature_counts": dict(
            Counter(summary["descriptive_speed_signature"] for summary in summaries)
        ),
        "catalogue_label_speed_signatures": {
            label: dict(counts) for label, counts in label_signatures.items()
        },
        "inventory": inventory,
    }


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def run_analysis(
    export_root: Path,
    output_root: Path,
    mode: str = "full",
    sample_size: int = 18,
) -> dict[str, Any]:
    inventory = inventory_export(export_root)
    catalogue_labels = {
        Path(_normalise_reference(row.get("Filename", ""))).name:
            (row.get("Activity Type") or "<missing>").strip()
        for row in load_catalogue(export_root / "activities.csv")
        if row.get("Filename")
    }
    all_files = [
        Path(path)
        for path in inventory["files"]
        if detect_recording_format(path) in SUPPORTED_FORMATS
    ]
    selected = (
        select_representative_files(all_files, sample_size) if mode == "sample" else all_files
    )
    summaries: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    for index, path in enumerate(selected, start=1):
        try:
            summary = summarize_activity(parse_recording(path))
            summary["catalogue_label"] = catalogue_labels.get(path.name)
            summaries.append(summary)
        except Exception as error:  # one malformed activity must not hide the archive inventory
            parse_errors.append(
                {
                    "source_file": path.name,
                    "source_format": detect_recording_format(path),
                    "error_type": type(error).__name__,
                    "message": str(error),
                }
            )
        if index % 25 == 0 or index == len(selected):
            print(f"Parsed {index}/{len(selected)} recordings")
    aggregate = aggregate_diagnostics(inventory, summaries, parse_errors, mode)
    output_root.mkdir(parents=True, exist_ok=True)
    write_json_atomic(output_root / "inventory.json", inventory)
    write_json_atomic(output_root / "activity-summaries.json", summaries)
    write_json_atomic(output_root / "aggregate.json", aggregate)
    from report import build_private_report

    report_path = output_root / "research-report.md"
    report_path.write_text(build_private_report(aggregate), encoding="utf-8")
    return {"inventory": inventory, "aggregate": aggregate, "report_path": str(report_path)}
