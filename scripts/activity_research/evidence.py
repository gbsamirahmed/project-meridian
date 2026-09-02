from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Sequence

from models import (
    LONG_STATIONARY_SECONDS,
    ActivitySample,
    EvidenceThresholds,
    NormalizedActivity,
    RecordingState,
    SegmentEvidence,
    TerrainRequest,
)


EARTH_RADIUS_METRES = 6_371_008.8


def geodesic_distance_m(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    latitude_1 = math.radians(first_latitude)
    latitude_2 = math.radians(second_latitude)
    latitude_delta = latitude_2 - latitude_1
    longitude_delta = math.radians(
        ((second_longitude - first_longitude + 540) % 360) - 180
    )
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(longitude_delta / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METRES * math.asin(min(1.0, math.sqrt(haversine)))


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def explicit_pause_intervals(activity: NormalizedActivity) -> list[tuple[datetime, datetime]]:
    timer_events = sorted(
        (
            event
            for event in activity.events
            if event.timestamp is not None and event.kind.lower() == "timer"
        ),
        key=lambda event: event.timestamp or datetime.min.replace(tzinfo=timezone.utc),
    )
    intervals: list[tuple[datetime, datetime]] = []
    paused_at: datetime | None = None
    for event in timer_events:
        event_type = (event.event_type or "").lower()
        if event_type.startswith("stop"):
            paused_at = event.timestamp
        elif event_type in {"start", "resume"} and paused_at is not None:
            if event.timestamp and event.timestamp > paused_at:
                intervals.append((paused_at, event.timestamp))
            paused_at = None
    return intervals


def _overlaps_pause(
    start: datetime,
    end: datetime,
    intervals: Sequence[tuple[datetime, datetime]],
) -> bool:
    return any(start < pause_end and end > pause_start for pause_start, pause_end in intervals)


def interpret_recording_states(
    activity: NormalizedActivity,
    thresholds: EvidenceThresholds | None = None,
) -> list[SegmentEvidence]:
    limits = thresholds or EvidenceThresholds()
    pauses = explicit_pause_intervals(activity)
    result: list[SegmentEvidence] = []
    for first, second in zip(activity.samples, activity.samples[1:]):
        if first.timestamp is None or second.timestamp is None:
            result.append(
                SegmentEvidence(
                    first.index,
                    second.index,
                    RecordingState.UNCERTAIN,
                    None,
                    None,
                    None,
                    "missing timestamp",
                )
            )
            continue
        duration = (second.timestamp - first.timestamp).total_seconds()
        if duration <= 0:
            result.append(
                SegmentEvidence(
                    first.index,
                    second.index,
                    RecordingState.ANOMALOUS,
                    duration,
                    None,
                    None,
                    "non-increasing timestamp",
                )
            )
            continue
        if _overlaps_pause(first.timestamp, second.timestamp, pauses):
            result.append(
                SegmentEvidence(
                    first.index,
                    second.index,
                    RecordingState.EXPLICIT_PAUSE,
                    duration,
                    None,
                    None,
                    "overlaps recorded timer stop/start interval",
                )
            )
            continue
        if duration > limits.timestamp_gap_seconds:
            result.append(
                SegmentEvidence(
                    first.index,
                    second.index,
                    RecordingState.RECORDING_GAP,
                    duration,
                    None,
                    None,
                    f"timestamp gap exceeds {limits.timestamp_gap_seconds:g} s",
                )
            )
            continue
        if None in (first.latitude, first.longitude, second.latitude, second.longitude):
            result.append(
                SegmentEvidence(
                    first.index,
                    second.index,
                    RecordingState.UNCERTAIN,
                    duration,
                    None,
                    None,
                    "missing GPS coordinate",
                )
            )
            continue
        distance = geodesic_distance_m(
            first.latitude,
            first.longitude,
            second.latitude,
            second.longitude,
        )
        speed = distance / duration
        if speed > limits.max_plausible_speed_mps:
            state = RecordingState.ANOMALOUS
            reason = f"GPS-derived speed exceeds {limits.max_plausible_speed_mps:g} m/s"
        elif (
            distance <= limits.stationary_distance_metres
            and speed <= limits.stationary_speed_mps
        ):
            state = RecordingState.STATIONARY
            reason = (
                f"GPS displacement is at most {limits.stationary_distance_metres:g} m "
                f"and speed is at most {limits.stationary_speed_mps:g} m/s"
            )
        else:
            state = RecordingState.MOVEMENT
            reason = "continuous plausible GPS progression"
        result.append(
            SegmentEvidence(
                first.index,
                second.index,
                state,
                duration,
                distance,
                speed,
                reason,
            )
        )
    return result


def terrain_requests(activity: NormalizedActivity) -> list[TerrainRequest]:
    return [
        TerrainRequest(sample.index, sample.timestamp, sample.latitude, sample.longitude)
        for sample in activity.samples
        if sample.latitude is not None and sample.longitude is not None
    ]


def _descriptive_speed_signature(speeds: Sequence[float], movement_seconds: float) -> str:
    if len(speeds) < 100 or movement_seconds < 600:
        return "insufficient"
    low = percentile(speeds, 0.25)
    middle = percentile(speeds, 0.5)
    high = percentile(speeds, 0.75)
    if middle is not None and low is not None and middle >= 2.4 and low >= 1.7:
        return "predominantly_fast_progression"
    if low is not None and high is not None and low < 1.3 and high >= 2.7:
        return "mixed_speed_progression"
    if middle is not None and middle < 1.0:
        return "predominantly_slow_progression"
    if middle is not None and middle < 2.4:
        return "predominantly_moderate_progression"
    return "ambiguous"


def summarize_activity(activity: NormalizedActivity) -> dict[str, object]:
    evidence = interpret_recording_states(activity)
    pause_intervals = explicit_pause_intervals(activity)
    gps_samples = [
        sample
        for sample in activity.samples
        if sample.timestamp is not None
        and sample.latitude is not None
        and sample.longitude is not None
    ]
    timestamps = [sample.timestamp for sample in activity.samples if sample.timestamp]
    sample_intervals = [
        (second.timestamp - first.timestamp).total_seconds()
        for first, second in zip(gps_samples, gps_samples[1:])
        if first.timestamp and second.timestamp and second.timestamp > first.timestamp
    ]
    movement = [
        segment
        for segment in evidence
        if segment.state == RecordingState.MOVEMENT
        and segment.duration_seconds is not None
        and segment.distance_m is not None
        and segment.speed_mps is not None
    ]
    speeds = [segment.speed_mps for segment in movement if segment.speed_mps is not None]
    movement_seconds = sum(segment.duration_seconds or 0 for segment in movement)
    state_seconds: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    for segment in evidence:
        state_counts[segment.state.value] += 1
        if segment.duration_seconds and segment.duration_seconds > 0:
            state_seconds[segment.state.value] += segment.duration_seconds
    long_stationary = 0
    stationary_run = 0.0
    for segment in evidence:
        if segment.state == RecordingState.STATIONARY:
            stationary_run += segment.duration_seconds or 0
        else:
            if stationary_run >= LONG_STATIONARY_SECONDS:
                long_stationary += 1
            stationary_run = 0
    if stationary_run >= LONG_STATIONARY_SECONDS:
        long_stationary += 1
    sensor_fields = {
        "recorded_altitude": "recorded_altitude_m",
        "device_distance": "device_distance_m",
        "device_speed": "device_speed_mps",
        "heart_rate": "heart_rate_bpm",
        "cadence": "cadence_rpm",
        "power": "power_w",
        "temperature": "temperature_c",
        "gps_accuracy": "gps_accuracy_m",
    }
    sensor_counts = {
        label: sum(getattr(sample, attribute) is not None for sample in activity.samples)
        for label, attribute in sensor_fields.items()
    }
    return {
        "source_file": activity.source_path.name,
        "source_format": activity.source_format,
        "merged_same_timestamp_record_count": activity.source_metadata.get(
            "merged_same_timestamp_record_count", 0
        ),
        "same_timestamp_field_conflict_count": activity.source_metadata.get(
            "same_timestamp_field_conflict_count", 0
        ),
        "sample_count": len(activity.samples),
        "timestamped_gps_count": len(gps_samples),
        "usable_timestamped_gps": len(gps_samples) >= 2,
        "first_timestamp": min(timestamps).isoformat() if timestamps else None,
        "last_timestamp": max(timestamps).isoformat() if timestamps else None,
        "devices": sorted({device.label for device in activity.devices}),
        "lap_count": len(activity.laps),
        "event_count": len(activity.events),
        "timer_event_type_counts": dict(
            Counter(
                event.event_type or "unknown"
                for event in activity.events
                if event.kind.lower() == "timer"
            )
        ),
        "explicit_pause_interval_count": len(pause_intervals),
        "explicit_pause_seconds": sum(
            (end - start).total_seconds() for start, end in pause_intervals
        ),
        "sample_interval_median_s": percentile(sample_intervals, 0.5),
        "sample_interval_p90_s": percentile(sample_intervals, 0.9),
        "sensor_counts": sensor_counts,
        "state_counts": dict(state_counts),
        "state_seconds": dict(state_seconds),
        "long_stationary_episode_count": long_stationary,
        "movement_distance_m": sum(segment.distance_m or 0 for segment in movement),
        "movement_duration_s": movement_seconds,
        "movement_speed_p10_mps": percentile(speeds, 0.1),
        "movement_speed_median_mps": percentile(speeds, 0.5),
        "movement_speed_p90_mps": percentile(speeds, 0.9),
        "descriptive_speed_signature": _descriptive_speed_signature(
            speeds, movement_seconds
        ),
    }


def make_sample(
    index: int,
    timestamp: datetime | None,
    latitude: float | None,
    longitude: float | None,
) -> ActivitySample:
    """Concise constructor used by deterministic evidence tests."""
    return ActivitySample(index, timestamp, latitude, longitude)
