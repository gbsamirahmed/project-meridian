from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from evidence import interpret_recording_states, percentile, summarize_activity
from models import NormalizedActivity, RecordingState
from terrain_experiment import (
    MovementPoint,
    TerrainProfile,
    accepted_movement_segment_indices,
)


INFERENCE_VERSION = "activity-context-v1"
INSERTED_COLUMNS = (
    "codex_mode",
    "human_mode",
    "codex_terrain_profile",
    "human_terrain_profile",
    "codex_terrain_surface",
    "human_terrain_surface",
    "codex_party",
    "human_party",
    "codex_load",
    "human_load",
    "codex_conditions",
    "human_conditions",
    "codex_representative",
    "human_representative",
    "codex_notes",
    "human_notes",
)

ALLOWED_VALUES = {
    "codex_mode": {
        "hike", "walk", "run", "trail_run", "mixed", "ski", "surf",
        "swim", "cycle", "other", "unknown",
    },
    "codex_terrain_profile": {"flat", "rolling", "hilly", "mountainous", "unknown"},
    "codex_terrain_surface": {"easy", "rough", "technical", "unknown"},
    "codex_party": {"solo", "group", "unknown"},
    "codex_load": {"light", "heavy", "unknown"},
    "codex_conditions": {"normal", "difficult", "unknown"},
    "codex_representative": {"yes", "no", "unsure"},
}

RUN_SPEED_MPS = 2.2
WALK_SPEED_MPS = 1.9
MIN_PHASE_SECONDS = 120.0


@dataclass(slots=True, frozen=True)
class RecordingFeatures:
    usable_timestamped_gps: bool
    sample_count: int
    interpreted_segment_count: int
    movement_segment_count: int
    movement_distance_m: float
    movement_duration_s: float
    median_speed_mps: float | None
    p10_speed_mps: float | None
    p90_speed_mps: float | None
    walking_duration_fraction: float
    running_duration_fraction: float
    intermediate_duration_fraction: float
    longest_walking_phase_s: float
    longest_running_phase_s: float
    walking_running_transition_count: int
    stationary_seconds: float
    pause_seconds: float
    gap_seconds: float
    uncertain_seconds: float
    anomalous_segment_fraction: float
    cadence_coverage: float
    median_cadence_rpm: float | None
    explicit_pause_count: int
    long_stationary_episode_count: int

    @property
    def uncertain_fraction(self) -> float:
        denominator = self.movement_duration_s + self.stationary_seconds + self.uncertain_seconds
        return 0.0 if denominator <= 0 else self.uncertain_seconds / denominator

    @property
    def has_material_interruption(self) -> bool:
        return (
            self.pause_seconds > 0
            or self.gap_seconds > 120
            or self.long_stationary_episode_count > 0
        )


@dataclass(slots=True, frozen=True)
class TerrainFeatures:
    available: bool
    distance_m: float
    ascent_m: float
    descent_m: float
    elevation_range_m: float
    ascent_per_km: float
    meaningful_gradient_fraction: float
    steep_gradient_fraction: float
    sustained_climb_m: float
    sustained_descent_m: float
    gradient_p10: float | None
    gradient_median: float | None
    gradient_p90: float | None


@dataclass(slots=True, frozen=True)
class ContextGuess:
    mode: str
    terrain_profile: str
    terrain_surface: str
    party: str
    load: str
    conditions: str
    representative: str
    notes: str
    non_run_type_contributed: bool = False

    def codex_values(self) -> dict[str, str]:
        return {
            "codex_mode": self.mode,
            "codex_terrain_profile": self.terrain_profile,
            "codex_terrain_surface": self.terrain_surface,
            "codex_party": self.party,
            "codex_load": self.load,
            "codex_conditions": self.conditions,
            "codex_representative": self.representative,
            "codex_notes": self.notes,
        }


def _weighted_percentile(
    values: Sequence[tuple[float, float]], quantile: float
) -> float | None:
    usable = sorted((value, weight) for value, weight in values if weight > 0)
    if not usable:
        return None
    threshold = sum(weight for _, weight in usable) * quantile
    cumulative = 0.0
    for value, weight in usable:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return usable[-1][0]


def _phase_statistics(
    segments: Sequence[tuple[int, float, float]],
) -> tuple[float, float, float, float, float, int]:
    totals = {"walk": 0.0, "middle": 0.0, "run": 0.0}
    blocks: list[tuple[str, float]] = []
    previous_index: int | None = None
    for index, duration, speed in segments:
        category = "run" if speed >= RUN_SPEED_MPS else "walk" if speed <= WALK_SPEED_MPS else "middle"
        totals[category] += duration
        if blocks and blocks[-1][0] == category and previous_index is not None and index == previous_index + 1:
            blocks[-1] = (category, blocks[-1][1] + duration)
        else:
            blocks.append((category, duration))
        previous_index = index
    total = sum(totals.values())
    material = [category for category, duration in blocks if duration >= MIN_PHASE_SECONDS and category != "middle"]
    transitions = sum(left != right for left, right in zip(material, material[1:]))
    longest_walk = max((duration for category, duration in blocks if category == "walk"), default=0.0)
    longest_run = max((duration for category, duration in blocks if category == "run"), default=0.0)
    if total <= 0:
        return 0.0, 0.0, 0.0, longest_walk, longest_run, transitions
    return (
        totals["walk"] / total,
        totals["run"] / total,
        totals["middle"] / total,
        longest_walk,
        longest_run,
        transitions,
    )


def recording_features(activity: NormalizedActivity) -> RecordingFeatures:
    summary = summarize_activity(activity)
    evidence = interpret_recording_states(activity)
    accepted = accepted_movement_segment_indices(activity)
    movement: list[tuple[int, float, float, float]] = []
    for segment in evidence:
        if (
            segment.start_index in accepted
            and segment.duration_seconds is not None
            and segment.distance_m is not None
            and segment.speed_mps is not None
            and segment.duration_seconds > 0
        ):
            movement.append(
                (segment.start_index, segment.duration_seconds, segment.distance_m, segment.speed_mps)
            )
    speed_values = [(speed, duration) for _, duration, _, speed in movement]
    phases = _phase_statistics([(index, duration, speed) for index, duration, _, speed in movement])
    cadence = [sample.cadence_rpm for sample in activity.samples if sample.cadence_rpm is not None]
    state_seconds = summary["state_seconds"]
    state_counts = summary["state_counts"]
    interpreted_count = sum(int(value) for value in state_counts.values())
    anomalous_count = int(state_counts.get(RecordingState.ANOMALOUS.value, 0))
    return RecordingFeatures(
        bool(summary["usable_timestamped_gps"]),
        int(summary["sample_count"]),
        interpreted_count,
        len(movement),
        sum(distance for _, _, distance, _ in movement),
        sum(duration for _, duration, _, _ in movement),
        _weighted_percentile(speed_values, 0.5),
        _weighted_percentile(speed_values, 0.1),
        _weighted_percentile(speed_values, 0.9),
        phases[0], phases[1], phases[2], phases[3], phases[4], phases[5],
        float(state_seconds.get(RecordingState.STATIONARY.value, 0)),
        float(summary["explicit_pause_seconds"]),
        float(state_seconds.get(RecordingState.RECORDING_GAP.value, 0)),
        float(state_seconds.get(RecordingState.UNCERTAIN.value, 0)),
        0.0 if interpreted_count == 0 else anomalous_count / interpreted_count,
        len(cadence) / max(1, len(activity.samples)),
        percentile(cadence, 0.5),
        int(summary["explicit_pause_interval_count"]),
        int(summary["long_stationary_episode_count"]),
    )


def _longest_directional_distance(
    profile: TerrainProfile, predicate: Callable[[float], bool]
) -> float:
    longest = 0.0
    current = 0.0
    for index in range(1, len(profile.points)):
        previous = profile.points[index - 1]
        point = profile.points[index]
        if point.chain_id != previous.chain_id:
            current = 0.0
            continue
        distance = point.chain_distance_m - previous.chain_distance_m
        gradients = (profile.gradients[index - 1], profile.gradients[index])
        gradient = None if None in gradients else (gradients[0] + gradients[1]) / 2
        if gradient is not None and predicate(gradient):
            current += max(0.0, distance)
            longest = max(longest, current)
        else:
            current = 0.0
    return longest


def terrain_features(profile: TerrainProfile) -> TerrainFeatures:
    if len(profile.points) < 2 or not profile.processed_elevations_m:
        return unknown_terrain()
    distance = max(point.activity_distance_m for point in profile.points)
    weighted_gradients: list[tuple[float, float]] = []
    for index in range(1, len(profile.points)):
        previous = profile.points[index - 1]
        point = profile.points[index]
        if point.chain_id != previous.chain_id:
            continue
        gradient_values = (profile.gradients[index - 1], profile.gradients[index])
        if None in gradient_values:
            continue
        segment_distance = max(0.0, point.chain_distance_m - previous.chain_distance_m)
        weighted_gradients.append(((gradient_values[0] + gradient_values[1]) / 2, segment_distance))
    weighted_distance = sum(weight for _, weight in weighted_gradients)
    meaningful = sum(weight for value, weight in weighted_gradients if abs(value) >= 0.05)
    steep = sum(weight for value, weight in weighted_gradients if abs(value) >= 0.10)
    gradients = [value for value, _ in weighted_gradients]
    return TerrainFeatures(
        True,
        distance,
        profile.ascent_after_hysteresis_m,
        profile.descent_after_hysteresis_m,
        max(profile.processed_elevations_m) - min(profile.processed_elevations_m),
        profile.ascent_after_hysteresis_m / max(distance / 1000, 0.001),
        0.0 if weighted_distance == 0 else meaningful / weighted_distance,
        0.0 if weighted_distance == 0 else steep / weighted_distance,
        _longest_directional_distance(profile, lambda gradient: gradient >= 0.03),
        _longest_directional_distance(profile, lambda gradient: gradient <= -0.03),
        percentile(gradients, 0.1),
        percentile(gradients, 0.5),
        percentile(gradients, 0.9),
    )


def unknown_terrain() -> TerrainFeatures:
    return TerrainFeatures(False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, None, None)


def classify_terrain_profile(terrain: TerrainFeatures) -> str:
    if not terrain.available or terrain.distance_m < 500:
        return "unknown"
    if (
        terrain.elevation_range_m >= 500
        and (terrain.ascent_per_km >= 35 or terrain.steep_gradient_fraction >= 0.15)
        and max(terrain.sustained_climb_m, terrain.sustained_descent_m) >= 800
    ):
        return "mountainous"
    if (
        (terrain.elevation_range_m >= 180 and terrain.ascent_per_km >= 20)
        or terrain.ascent_per_km >= 35
        or (
            terrain.meaningful_gradient_fraction >= 0.35
            and max(terrain.sustained_climb_m, terrain.sustained_descent_m) >= 300
        )
    ):
        return "hilly"
    if (
        terrain.ascent_per_km >= 8
        or terrain.elevation_range_m >= 60
        or terrain.meaningful_gradient_fraction >= 0.15
    ):
        return "rolling"
    return "flat"


def _mixed_evidence(recording: RecordingFeatures) -> bool:
    return (
        recording.walking_duration_fraction >= 0.20
        and recording.running_duration_fraction >= 0.20
        and recording.longest_walking_phase_s >= MIN_PHASE_SECONDS
        and recording.longest_running_phase_s >= MIN_PHASE_SECONDS
    )


def _running_mode(terrain_profile: str, terrain: TerrainFeatures) -> str:
    terrain_influenced = terrain_profile in {"hilly", "mountainous"} or (
        terrain_profile == "rolling"
        and terrain.meaningful_gradient_fraction >= 0.25
        and terrain.steep_gradient_fraction >= 0.08
    )
    return "trail_run" if terrain_influenced else "run"


def _infer_foot_mode(
    recording: RecordingFeatures,
    terrain: TerrainFeatures,
    terrain_profile: str,
    non_run_type: str | None,
) -> tuple[str, bool]:
    if not recording.usable_timestamped_gps or recording.movement_duration_s < 300:
        if non_run_type == "hike":
            return "hike", True
        if non_run_type == "walk":
            return "walk", True
        return "unknown", False
    if _mixed_evidence(recording):
        return "mixed", False
    strong_running = (
        recording.running_duration_fraction >= 0.60
        and recording.longest_running_phase_s >= 300
    ) or (
        recording.median_speed_mps is not None
        and recording.median_speed_mps >= 2.5
        and recording.running_duration_fraction >= 0.45
    )
    if strong_running:
        return _running_mode(terrain_profile, terrain), False
    strong_walking = (
        recording.walking_duration_fraction >= 0.55
        or (recording.median_speed_mps is not None and recording.median_speed_mps <= 1.8)
    )
    if strong_walking:
        if terrain_profile in {"hilly", "mountainous"} or non_run_type == "hike":
            return "hike", non_run_type == "hike"
        return "walk", non_run_type == "walk"
    if non_run_type == "hike":
        return "hike", True
    if non_run_type == "walk":
        return ("hike" if terrain_profile in {"hilly", "mountainous"} else "walk"), True
    return "unknown", False


def _broad_non_run_mode(activity_type: str) -> str | None:
    normalized = activity_type.strip().casefold().replace("_", " ")
    if normalized == "run":
        return None
    if "ski" in normalized:
        return "ski"
    if normalized in {"ride", "cycle", "cycling", "bike"}:
        return "cycle"
    if "swim" in normalized:
        return "swim"
    if "surf" in normalized:
        return "surf"
    if normalized == "walk":
        return "walk"
    if normalized == "hike":
        return "hike"
    if normalized:
        return "other"
    return None


def _representative(mode: str, recording: RecordingFeatures) -> str:
    if not recording.usable_timestamped_gps or recording.movement_segment_count < 2:
        return "no"
    if mode in {"ski", "surf", "swim", "cycle", "other"}:
        return "no"
    if recording.anomalous_segment_fraction > 0.01 or recording.uncertain_fraction > 0.20:
        return "no"
    if (
        mode == "unknown"
        or recording.movement_duration_s < 600
        or recording.movement_distance_m < 500
        or recording.has_material_interruption
    ):
        return "unsure"
    return "yes"


def _note(
    mode: str,
    terrain_profile: str,
    recording: RecordingFeatures,
    broad_type_used: bool,
) -> str:
    if not recording.usable_timestamped_gps or recording.movement_segment_count < 2:
        return "Insufficient usable timestamped GPS to infer activity context reliably."
    terrain_text = (
        "DEM terrain is unavailable"
        if terrain_profile == "unknown"
        else f"DEM profile is {terrain_profile}"
    )
    if broad_type_used and mode in {"ski", "surf", "swim", "cycle", "other"}:
        return f"Non-Run source type supports {mode}; decoded trajectory was sanity-checked where GPS was available."
    if mode in {"run", "trail_run"}:
        lead = "Sustained running-speed geographic progression dominates"
    elif mode == "mixed":
        lead = "Distinct sustained walking-speed and running-speed phases are present"
    elif mode in {"walk", "hike"}:
        lead = "Walking-speed geographic progression dominates"
    else:
        lead = "Movement evidence is insufficient or conflicting for a confident mode"
    additions = [terrain_text]
    if recording.has_material_interruption:
        additions.append("pauses, gaps or stationary episodes remain separate evidence")
    if terrain_profile in {"hilly", "mountainous"}:
        additions.append("the recording cannot establish surface technicality")
    return lead + "; " + "; ".join(additions) + "."


def infer_context(
    activity_type: str,
    recording: RecordingFeatures,
    terrain: TerrainFeatures,
) -> ContextGuess:
    terrain_profile = classify_terrain_profile(terrain)
    broad = _broad_non_run_mode(activity_type)
    broad_used = False
    if broad in {"walk", "hike"}:
        mode, broad_used = _infer_foot_mode(recording, terrain, terrain_profile, broad)
    elif broad is not None:
        mode = broad
        broad_used = True
    else:
        mode, broad_used = _infer_foot_mode(recording, terrain, terrain_profile, None)
    guess = ContextGuess(
        mode=mode,
        terrain_profile=terrain_profile,
        # GPS plus a roughly 30 m DEM cannot establish underfoot condition.
        terrain_surface="unknown",
        # No available recording signal identifies companions or pack weight.
        party="unknown",
        load="unknown",
        # Absence of evidence is not evidence of normal conditions.
        conditions="unknown",
        representative=_representative(mode, recording),
        notes=_note(mode, terrain_profile, recording, broad_used),
        non_run_type_contributed=broad_used,
    )
    validate_guess(guess)
    return guess


def unavailable_guess(reason: str = "Recording could not be analysed") -> ContextGuess:
    return ContextGuess(
        "unknown", "unknown", "unknown", "unknown", "unknown", "unknown", "no",
        f"{reason}; activity context cannot be inferred reliably.", False,
    )


def validate_guess(guess: ContextGuess) -> None:
    for column, value in guess.codex_values().items():
        if column == "codex_notes":
            if not value.strip():
                raise ValueError("codex_notes must not be blank")
        elif value not in ALLOWED_VALUES[column]:
            raise ValueError(f"Unexpected {column} value: {value}")


def categorical_distribution(guesses: Iterable[ContextGuess]) -> dict[str, dict[str, int]]:
    result = {column: {} for column in ALLOWED_VALUES}
    for guess in guesses:
        for column, value in guess.codex_values().items():
            if column == "codex_notes":
                continue
            counts = result[column]
            counts[value] = counts.get(value, 0) + 1
    return result


def inference_methodology() -> dict[str, object]:
    """Serializable rule record stored beside the frozen private predictions."""
    return {
        "version": INFERENCE_VERSION,
        "prohibited_inputs": [
            "Activity Name",
            "Activity Description",
            "human_* annotations",
            "external place or route lookup",
            "Strava moving time as truth",
        ],
        "movement": {
            "primary_evidence": "raw timestamps plus geographic displacement",
            "running_speed_threshold_mps": RUN_SPEED_MPS,
            "walking_speed_threshold_mps": WALK_SPEED_MPS,
            "minimum_material_phase_seconds": MIN_PHASE_SECONDS,
            "minimum_walking_speed": None,
            "slow_progression_policy": "retain when the existing coherent-progress review accepts it",
        },
        "mode": {
            "run_type_policy": "no behavioural subtype evidence",
            "non_run_type_policy": "broad prior, sanity-checked against recording evidence",
            "mixed_policy": "at least 20% walking-speed and 20% running-speed time with a two-minute phase of each",
            "trail_run_policy": "sustained running plus DEM-supported terrain influence",
        },
        "terrain": {
            "source": "AWS Terrarium z15 with Meridian decoding and bilinear sampling",
            "working_variant": "40 m spacing, median-5 smoothing, 3 m ascent/descent hysteresis, 120 m gradient half-window",
            "profile_inputs": [
                "ascent per kilometre",
                "elevation range",
                "gradient distribution",
                "sustained climb/descent distance",
            ],
            "surface_policy": "unknown because GPS and the DEM do not observe footing or technicality",
        },
        "unobservable_context": {
            "party": "unknown",
            "load": "unknown",
            "conditions": "unknown",
        },
        "representativeness": {
            "no": "unusable/severely anomalous recording or clearly non-foot mode",
            "unsure": "ambiguous/short recording or material pause, gap, or stationary context",
            "yes": "usable foot-travel recording without those recording-quality concerns",
        },
    }
