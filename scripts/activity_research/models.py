from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, Sequence


SUPPORTED_FORMATS = (".fit", ".fit.gz", ".gpx", ".gpx.gz", ".tcx", ".tcx.gz")
TIMESTAMP_GAP_SECONDS = 60.0
STATIONARY_DISTANCE_METRES = 3.0
STATIONARY_SPEED_MPS = 0.35
MAX_PLAUSIBLE_GPS_SPEED_MPS = 25.0
LONG_STATIONARY_SECONDS = 120.0


class RecordingState(StrEnum):
    MOVEMENT = "continuous_movement"
    STATIONARY = "continuous_stationary"
    EXPLICIT_PAUSE = "explicit_pause"
    RECORDING_GAP = "recording_gap"
    ANOMALOUS = "gps_anomaly"
    UNCERTAIN = "uncertain"


@dataclass(slots=True)
class ActivitySample:
    index: int
    timestamp: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    recorded_altitude_m: float | None = None
    device_distance_m: float | None = None
    device_speed_mps: float | None = None
    heart_rate_bpm: float | None = None
    cadence_rpm: float | None = None
    power_w: float | None = None
    temperature_c: float | None = None
    gps_accuracy_m: float | None = None
    direct_fields: tuple[str, ...] = ()


@dataclass(slots=True)
class RecordingEvent:
    timestamp: datetime | None
    kind: str
    event_type: str | None = None
    source: str = "recorded"


@dataclass(slots=True)
class LapRecord:
    start_time: datetime | None
    end_time: datetime | None
    elapsed_seconds: float | None
    timer_seconds: float | None
    distance_m: float | None


@dataclass(slots=True, frozen=True)
class DeviceRecord:
    manufacturer: str | None
    product: str | None
    product_name: str | None = None

    @property
    def label(self) -> str:
        parts = [
            part
            for part in (self.manufacturer, self.product_name or self.product)
            if part
        ]
        return " / ".join(parts) if parts else "Unknown"


@dataclass(slots=True)
class NormalizedActivity:
    source_path: Path
    source_format: str
    samples: list[ActivitySample] = field(default_factory=list)
    events: list[RecordingEvent] = field(default_factory=list)
    laps: list[LapRecord] = field(default_factory=list)
    devices: list[DeviceRecord] = field(default_factory=list)
    session_metadata: dict[str, Any] = field(default_factory=dict)
    source_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SegmentEvidence:
    start_index: int
    end_index: int
    state: RecordingState
    duration_seconds: float | None
    distance_m: float | None
    speed_mps: float | None
    reason: str


@dataclass(slots=True)
class EvidenceThresholds:
    timestamp_gap_seconds: float = TIMESTAMP_GAP_SECONDS
    stationary_distance_metres: float = STATIONARY_DISTANCE_METRES
    stationary_speed_mps: float = STATIONARY_SPEED_MPS
    max_plausible_speed_mps: float = MAX_PLAUSIBLE_GPS_SPEED_MPS
    long_stationary_seconds: float = LONG_STATIONARY_SECONDS


@dataclass(slots=True, frozen=True)
class TerrainRequest:
    sample_index: int
    timestamp: datetime | None
    latitude: float
    longitude: float


class TerrainEnricher(Protocol):
    def enrich(self, requests: Sequence[TerrainRequest]) -> Sequence[float | None]:
        """Return DEM elevations aligned with requests without mutating source data."""
