from __future__ import annotations

import gzip
import math
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

from models import (
    SUPPORTED_FORMATS,
    ActivitySample,
    DeviceRecord,
    LapRecord,
    NormalizedActivity,
    RecordingEvent,
)

try:
    import fitdecode
except ImportError:  # pragma: no cover - CLI reports the missing dependency
    fitdecode = None


def detect_recording_format(path: str | Path) -> str:
    name = Path(path).name.lower()
    for suffix in SUPPORTED_FORMATS:
        if name.endswith(suffix):
            return suffix
    suffixes = Path(name).suffixes
    if suffixes and suffixes[-1] == ".gz" and len(suffixes) > 1:
        return "".join(suffixes[-2:])
    return Path(name).suffix.lower() or "<none>"


def recording_key(path: str | Path) -> str:
    name = Path(path).name
    detected = detect_recording_format(name)
    return name[: -len(detected)] if detected in SUPPORTED_FORMATS else Path(name).stem


def _open_binary(path: Path) -> BinaryIO:
    return gzip.open(path, "rb") if path.name.lower().endswith(".gz") else path.open("rb")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def parse_timestamp(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc).astimezone(timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _first_descendant_text(element: ET.Element, names: set[str]) -> str | None:
    for child in element.iter():
        if _local_name(child.tag) in names and child.text and child.text.strip():
            return child.text.strip()
    return None


def _extension_values(element: ET.Element) -> dict[str, float]:
    aliases = {
        "hr": "heart_rate_bpm",
        "heartratebpm": "heart_rate_bpm",
        "cad": "cadence_rpm",
        "cadence": "cadence_rpm",
        "atemp": "temperature_c",
        "temp": "temperature_c",
        "temperature": "temperature_c",
        "power": "power_w",
        "watts": "power_w",
        "speed": "device_speed_mps",
        "distance": "device_distance_m",
        "hdop": "gps_accuracy_m",
    }
    result: dict[str, float] = {}
    for child in element.iter():
        destination = aliases.get(_local_name(child.tag))
        value = number(child.text)
        if destination and value is not None:
            result.setdefault(destination, value)
    return result


def _sample_from_xml_point(
    point: ET.Element,
    index: int,
    latitude: float | None,
    longitude: float | None,
) -> ActivitySample:
    values = _extension_values(point)
    recorded_altitude = number(_first_descendant_text(point, {"ele", "altitudemeters"}))
    timestamp = parse_timestamp(_first_descendant_text(point, {"time"}))
    direct = {
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "recorded_altitude_m": recorded_altitude,
        **values,
    }
    return ActivitySample(
        index=index,
        timestamp=timestamp,
        latitude=latitude,
        longitude=longitude,
        recorded_altitude_m=recorded_altitude,
        direct_fields=tuple(sorted(name for name, value in direct.items() if value is not None)),
        **values,
    )


def parse_gpx(path: Path) -> NormalizedActivity:
    with _open_binary(path) as stream:
        root = ET.parse(stream).getroot()
    activity = NormalizedActivity(
        source_path=path,
        source_format=detect_recording_format(path),
        source_metadata={"creator": root.attrib.get("creator")},
    )
    for segment in (element for element in root.iter() if _local_name(element.tag) == "trkseg"):
        first_timestamp: datetime | None = None
        for point in (child for child in segment if _local_name(child.tag) == "trkpt"):
            sample = _sample_from_xml_point(
                point,
                len(activity.samples),
                number(point.attrib.get("lat")),
                number(point.attrib.get("lon")),
            )
            first_timestamp = first_timestamp or sample.timestamp
            activity.samples.append(sample)
        activity.events.append(
            RecordingEvent(first_timestamp, "track_segment_start", source="parser_normalized")
        )
    if not activity.samples:
        for point in (element for element in root.iter() if _local_name(element.tag) == "rtept"):
            activity.samples.append(
                _sample_from_xml_point(
                    point,
                    len(activity.samples),
                    number(point.attrib.get("lat")),
                    number(point.attrib.get("lon")),
                )
            )
    creator = root.attrib.get("creator")
    if creator:
        activity.devices.append(DeviceRecord(None, None, creator))
    return activity


def parse_tcx(path: Path) -> NormalizedActivity:
    with _open_binary(path) as stream:
        root = ET.parse(stream).getroot()
    activity = NormalizedActivity(path, detect_recording_format(path))
    creator = next(
        (element for element in root.iter() if _local_name(element.tag) == "creator"),
        None,
    )
    if creator is not None:
        activity.devices.append(
            DeviceRecord(
                None,
                _first_descendant_text(creator, {"productid"}),
                _first_descendant_text(creator, {"name"}),
            )
        )
    for point in (element for element in root.iter() if _local_name(element.tag) == "trackpoint"):
        sample = _sample_from_xml_point(
            point,
            len(activity.samples),
            number(_first_descendant_text(point, {"latitudedegrees"})),
            number(_first_descendant_text(point, {"longitudedegrees"})),
        )
        sample.device_distance_m = number(_first_descendant_text(point, {"distancemeters"}))
        sample.heart_rate_bpm = number(_first_descendant_text(point, {"value"}))
        sample.cadence_rpm = sample.cadence_rpm or number(
            _first_descendant_text(point, {"cadence"})
        )
        activity.samples.append(sample)
    for lap in (element for element in root.iter() if _local_name(element.tag) == "lap"):
        start = parse_timestamp(lap.attrib.get("StartTime"))
        elapsed = number(_first_descendant_text(lap, {"totaltimeseconds"}))
        activity.laps.append(
            LapRecord(
                start_time=start,
                end_time=(
                    None
                    if start is None or elapsed is None
                    else datetime.fromtimestamp(start.timestamp() + elapsed, timezone.utc)
                ),
                elapsed_seconds=elapsed,
                timer_seconds=elapsed,
                distance_m=number(_first_descendant_text(lap, {"distancemeters"})),
            )
        )
    return activity


def _fit_fields(frame: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in frame.fields:
        if item.value is not None:
            values[item.name] = item.value
    return values


def _fit_position(value: Any) -> float | None:
    numeric = number(value)
    if numeric is None:
        return None
    return numeric * 180.0 / (2**31) if abs(numeric) > 180 else numeric


def _text(value: Any) -> str | None:
    return None if value is None else str(value)


SAMPLE_VALUE_FIELDS = (
    "latitude",
    "longitude",
    "recorded_altitude_m",
    "device_distance_m",
    "device_speed_mps",
    "heart_rate_bpm",
    "cadence_rpm",
    "power_w",
    "temperature_c",
    "gps_accuracy_m",
)


def merge_same_timestamp_samples(
    samples: list[ActivitySample],
) -> tuple[list[ActivitySample], int, int]:
    """Merge complementary FIT record messages while retaining conflict evidence."""
    merged: list[ActivitySample] = []
    by_timestamp: dict[datetime, ActivitySample] = {}
    merge_count = 0
    conflict_count = 0
    for sample in samples:
        if sample.timestamp is None or sample.timestamp not in by_timestamp:
            merged.append(sample)
            if sample.timestamp is not None:
                by_timestamp[sample.timestamp] = sample
            continue
        target = by_timestamp[sample.timestamp]
        merge_count += 1
        for field_name in SAMPLE_VALUE_FIELDS:
            current = getattr(target, field_name)
            incoming = getattr(sample, field_name)
            if current is None and incoming is not None:
                setattr(target, field_name, incoming)
            elif current is not None and incoming is not None and not math.isclose(
                current, incoming, rel_tol=1e-9, abs_tol=1e-9
            ):
                conflict_count += 1
        target.direct_fields = tuple(
            sorted(set(target.direct_fields) | set(sample.direct_fields))
        )
    for index, sample in enumerate(merged):
        sample.index = index
    return merged, merge_count, conflict_count


def parse_fit(path: Path) -> NormalizedActivity:
    if fitdecode is None:
        raise RuntimeError(
            "FIT support requires fitdecode; install scripts/activity_research/requirements.txt"
        )
    activity = NormalizedActivity(path, detect_recording_format(path))
    file_devices: set[DeviceRecord] = set()
    creator_devices: set[DeviceRecord] = set()
    auxiliary_device_records = 0
    with _open_binary(path) as stream:
        with fitdecode.FitReader(stream) as reader:
            for frame in reader:
                if frame.frame_type != fitdecode.FIT_FRAME_DATA:
                    continue
                values = _fit_fields(frame)
                if frame.name == "record":
                    selected = {
                        "timestamp": parse_timestamp(values.get("timestamp")),
                        "latitude": _fit_position(values.get("position_lat")),
                        "longitude": _fit_position(values.get("position_long")),
                        "recorded_altitude_m": number(
                            values.get("enhanced_altitude", values.get("altitude"))
                        ),
                        "device_distance_m": number(values.get("distance")),
                        "device_speed_mps": number(
                            values.get("enhanced_speed", values.get("speed"))
                        ),
                        "heart_rate_bpm": number(values.get("heart_rate")),
                        "cadence_rpm": number(values.get("cadence")),
                        "power_w": number(values.get("power")),
                        "temperature_c": number(values.get("temperature")),
                        "gps_accuracy_m": number(values.get("gps_accuracy")),
                    }
                    activity.samples.append(
                        ActivitySample(
                            index=len(activity.samples),
                            direct_fields=tuple(
                                sorted(name for name, value in selected.items() if value is not None)
                            ),
                            **selected,
                        )
                    )
                elif frame.name == "event":
                    activity.events.append(
                        RecordingEvent(
                            parse_timestamp(values.get("timestamp")),
                            _text(values.get("event")) or "unknown",
                            _text(values.get("event_type")),
                        )
                    )
                elif frame.name == "lap":
                    activity.laps.append(
                        LapRecord(
                            parse_timestamp(values.get("start_time")),
                            parse_timestamp(values.get("timestamp")),
                            number(values.get("total_elapsed_time")),
                            number(values.get("total_timer_time")),
                            number(values.get("total_distance")),
                        )
                    )
                elif frame.name == "session":
                    for key in (
                        "sport",
                        "sub_sport",
                        "start_time",
                        "timestamp",
                        "total_elapsed_time",
                        "total_timer_time",
                        "total_distance",
                        "total_ascent",
                        "total_descent",
                    ):
                        if key in values:
                            value = values[key]
                            activity.session_metadata[key] = (
                                value.isoformat() if isinstance(value, datetime) else value
                            )
                elif frame.name in {"file_id", "device_info"}:
                    device = DeviceRecord(
                        _text(values.get("manufacturer")),
                        _text(values.get("garmin_product", values.get("product"))),
                        _text(values.get("product_name")),
                    )
                    if device.label != "Unknown" and frame.name == "file_id":
                        file_devices.add(device)
                    elif (
                        device.label != "Unknown"
                        and values.get("device_index") == "creator"
                    ):
                        creator_devices.add(device)
                    elif device.label != "Unknown":
                        auxiliary_device_records += 1
    activity.samples, merge_count, conflict_count = merge_same_timestamp_samples(
        activity.samples
    )
    activity.devices = sorted(file_devices or creator_devices, key=lambda item: item.label)
    activity.source_metadata["merged_same_timestamp_record_count"] = merge_count
    activity.source_metadata["same_timestamp_field_conflict_count"] = conflict_count
    activity.source_metadata["auxiliary_device_record_count"] = (
        auxiliary_device_records
    )
    return activity


def parse_recording(path: Path) -> NormalizedActivity:
    detected = detect_recording_format(path)
    if detected in {".fit", ".fit.gz"}:
        return parse_fit(path)
    if detected in {".gpx", ".gpx.gz"}:
        return parse_gpx(path)
    if detected in {".tcx", ".tcx.gz"}:
        return parse_tcx(path)
    raise ValueError(f"Unsupported recording format: {detected}")
