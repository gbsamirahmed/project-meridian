from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import median
from typing import Callable, Iterable, Sequence

from evidence import percentile
from terrain_experiment import TerrainProfile


SLOPE_BIN_EDGES = (-0.5, -0.3, -0.2, -0.12, -0.08, -0.04, 0.0, 0.04, 0.08, 0.12, 0.2, 0.3, 0.5)
SLOPE_BIN_CENTRES = tuple(
    (left + right) / 2 for left, right in zip(SLOPE_BIN_EDGES, SLOPE_BIN_EDGES[1:])
)
SHRINKAGE_DISTANCE_M = 4000.0
VALIDATION_SEED = 20260902


@dataclass(slots=True, frozen=True)
class MovementObservation:
    activity_key: str
    gradient: float
    distance_m: float
    duration_s: float
    observed_speed_mps: float
    generic_speed_mps: float
    progress: float
    cumulative_distance_m: float
    cumulative_ascent_m: float


@dataclass(slots=True)
class ActivityObservations:
    key: str
    behaviour_signature: str
    observations: list[MovementObservation]
    observed_movement_s: float
    distance_m: float
    ascent_m: float
    interruption_diagnostic: bool


@dataclass(slots=True, frozen=True)
class SlopeBinEstimate:
    centre: float
    distance_m: float
    raw_ratio: float
    shrunk_ratio: float
    observation_count: int


@dataclass(slots=True)
class PersonalSlopeModel:
    bins: list[SlopeBinEstimate]

    def speed_mps(self, gradient: float) -> float:
        generic = generic_tobler_speed_mps(gradient)
        populated = [item for item in self.bins if item.distance_m > 0]
        if not populated:
            return generic
        if gradient <= populated[0].centre:
            ratio = populated[0].shrunk_ratio
        elif gradient >= populated[-1].centre:
            ratio = populated[-1].shrunk_ratio
        else:
            ratio = populated[-1].shrunk_ratio
            for first, second in zip(populated, populated[1:]):
                if first.centre <= gradient <= second.centre:
                    fraction = (gradient - first.centre) / (second.centre - first.centre)
                    ratio = first.shrunk_ratio * (1 - fraction) + second.shrunk_ratio * fraction
                    break
        return max(0.15, min(3.5, generic * ratio))


def generic_tobler_speed_mps(gradient: float) -> float:
    slope = max(-0.5, min(0.5, gradient))
    speed_kmh = 6 * math.exp(-3.5 * abs(slope + 0.05))
    return max(0.8, min(7.0, speed_kmh)) / 3.6


def observations_from_profile(
    activity_key: str,
    behaviour_signature: str,
    profile: TerrainProfile,
    interruption_diagnostic: bool,
) -> ActivityObservations:
    observations: list[MovementObservation] = []
    total_distance = profile.points[-1].activity_distance_m if profile.points else 0.0
    cumulative_ascent = 0.0
    previous_elevation: float | None = None
    previous_chain: int | None = None
    for index in range(1, len(profile.points)):
        previous = profile.points[index - 1]
        current = profile.points[index]
        if current.chain_id != previous.chain_id:
            previous_elevation = profile.processed_elevations_m[index]
            previous_chain = current.chain_id
            continue
        distance = current.chain_distance_m - previous.chain_distance_m
        duration = current.timestamp_s - previous.timestamp_s
        first_gradient = profile.gradients[index - 1]
        second_gradient = profile.gradients[index]
        if distance < 1 or duration <= 0 or first_gradient is None or second_gradient is None:
            continue
        elevation = profile.processed_elevations_m[index]
        if previous_elevation is not None and previous_chain == current.chain_id:
            cumulative_ascent += max(0.0, elevation - previous_elevation)
        previous_elevation = elevation
        previous_chain = current.chain_id
        gradient = (first_gradient + second_gradient) / 2
        observed_speed = distance / duration
        if not math.isfinite(observed_speed) or observed_speed <= 0:
            continue
        observations.append(
            MovementObservation(
                activity_key,
                gradient,
                distance,
                duration,
                observed_speed,
                generic_tobler_speed_mps(gradient),
                min(1.0, current.activity_distance_m / max(total_distance, 1)),
                current.activity_distance_m,
                cumulative_ascent,
            )
        )
    return ActivityObservations(
        activity_key,
        behaviour_signature,
        observations,
        sum(item.duration_s for item in observations),
        sum(item.distance_m for item in observations),
        profile.ascent_after_hysteresis_m,
        interruption_diagnostic,
    )


def _weighted_median(values: Sequence[tuple[float, float]]) -> float:
    ordered = sorted(values)
    threshold = sum(weight for _, weight in ordered) / 2
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


def _bin_index(gradient: float) -> int:
    for index, upper in enumerate(SLOPE_BIN_EDGES[1:]):
        if gradient < upper:
            return index
    return len(SLOPE_BIN_CENTRES) - 1


def fit_personal_slope_model(
    activities: Sequence[ActivityObservations],
) -> PersonalSlopeModel:
    values: list[list[tuple[float, float]]] = [[] for _ in SLOPE_BIN_CENTRES]
    counts = [0] * len(SLOPE_BIN_CENTRES)
    for activity in activities:
        for observation in activity.observations:
            index = _bin_index(observation.gradient)
            ratio = observation.observed_speed_mps / observation.generic_speed_mps
            if math.isfinite(ratio) and ratio > 0:
                values[index].append((math.log(ratio), observation.distance_m))
                counts[index] += 1
    bins: list[SlopeBinEstimate] = []
    for centre, entries, count in zip(SLOPE_BIN_CENTRES, values, counts):
        distance = sum(weight for _, weight in entries)
        raw_ratio = math.exp(_weighted_median(entries)) if entries else 1.0
        shrinkage = distance / (distance + SHRINKAGE_DISTANCE_M)
        shrunk_ratio = math.exp(math.log(raw_ratio) * shrinkage)
        bins.append(
            SlopeBinEstimate(
                centre,
                distance,
                max(0.5, min(1.8, raw_ratio)),
                max(0.5, min(1.8, shrunk_ratio)),
                count,
            )
        )
    return PersonalSlopeModel(bins)


def predict_activity_seconds(
    activity: ActivityObservations,
    speed: Callable[[float], float],
) -> float:
    return sum(item.distance_m / speed(item.gradient) for item in activity.observations)


def activity_folds(
    activities: Sequence[ActivityObservations],
    fold_count: int = 5,
    seed: int = 20260902,
) -> list[list[str]]:
    folds: list[list[str]] = [[] for _ in range(min(fold_count, len(activities)))]
    grouped: dict[str, list[ActivityObservations]] = {}
    for activity in activities:
        grouped.setdefault(activity.behaviour_signature, []).append(activity)
    randomizer = random.Random(seed)
    for group in grouped.values():
        ordered = sorted(group, key=lambda item: item.observed_movement_s)
        chunks = [ordered[index : index + 2] for index in range(0, len(ordered), 2)]
        randomizer.shuffle(chunks)
        flattened = [item for chunk in chunks for item in chunk]
        for index, activity in enumerate(flattened):
            folds[index % len(folds)].append(activity.key)
    return folds


def _metric_summary(rows: Sequence[dict[str, float]]) -> dict[str, float | int | None]:
    absolute_minutes = [abs(row["error_s"]) / 60 for row in rows]
    percentages = [abs(row["error_s"]) / row["observed_s"] * 100 for row in rows]
    signed_minutes = [row["error_s"] / 60 for row in rows]
    return {
        "activity_count": len(rows),
        "median_absolute_error_minutes": percentile(absolute_minutes, 0.5),
        "median_absolute_percentage_error": percentile(percentages, 0.5),
        "signed_bias_minutes": sum(signed_minutes) / len(signed_minutes) if rows else None,
        "median_signed_percentage_bias": percentile(
            [row["error_s"] / row["observed_s"] * 100 for row in rows], 0.5
        ),
        "p90_absolute_percentage_error": percentile(percentages, 0.9),
    }


def cross_validate(
    activities: Sequence[ActivityObservations],
    fold_count: int = 5,
    repeat_count: int = 5,
) -> dict[str, object]:
    by_key = {activity.key: activity for activity in activities}
    personal_predictions: dict[str, list[float]] = {key: [] for key in by_key}
    assignments: list[list[list[str]]] = []
    for repeat in range(repeat_count):
        folds = activity_folds(activities, fold_count, VALIDATION_SEED + repeat)
        assignments.append(folds)
        for test_keys in folds:
            test_set = set(test_keys)
            training = [activity for activity in activities if activity.key not in test_set]
            model = fit_personal_slope_model(training)
            for key in test_keys:
                personal_predictions[key].append(
                    predict_activity_seconds(by_key[key], model.speed_mps)
                )
    rows: list[dict[str, float | str | int]] = []
    for key, activity in by_key.items():
        rows.append(
            {
                "activity_key": key,
                "observed_s": activity.observed_movement_s,
                "generic_s": predict_activity_seconds(activity, generic_tobler_speed_mps),
                "personal_s": median(personal_predictions[key]),
                "behaviour_signature": activity.behaviour_signature,
                "duration_hours": activity.observed_movement_s / 3600,
                "ascent_per_km": activity.ascent_m / max(activity.distance_m / 1000, 0.001),
            }
        )
    generic_rows = [
        {"observed_s": float(row["observed_s"]), "error_s": float(row["generic_s"]) - float(row["observed_s"])}
        for row in rows
    ]
    personal_rows = [
        {"observed_s": float(row["observed_s"]), "error_s": float(row["personal_s"]) - float(row["observed_s"])}
        for row in rows
    ]
    duration_groups: dict[str, dict[str, object]] = {}
    for label, predicate in (
        ("under_2h", lambda value: value < 2),
        ("2_to_5h", lambda value: 2 <= value < 5),
        ("5h_plus", lambda value: value >= 5),
    ):
        selected = [row for row in rows if predicate(float(row["duration_hours"]))]
        duration_groups[label] = {
            "generic": _metric_summary([
                {"observed_s": float(row["observed_s"]), "error_s": float(row["generic_s"]) - float(row["observed_s"])}
                for row in selected
            ]),
            "personal": _metric_summary([
                {"observed_s": float(row["observed_s"]), "error_s": float(row["personal_s"]) - float(row["observed_s"])}
                for row in selected
            ]),
        }
    ascent_values = sorted(float(row["ascent_per_km"]) for row in rows)
    lower_ascent = percentile(ascent_values, 1 / 3) or 0.0
    upper_ascent = percentile(ascent_values, 2 / 3) or 0.0
    terrain_groups: dict[str, dict[str, object]] = {}
    for label, predicate in (
        ("lower_ascent_density", lambda value: value < lower_ascent),
        ("middle_ascent_density", lambda value: lower_ascent <= value < upper_ascent),
        ("higher_ascent_density", lambda value: value >= upper_ascent),
    ):
        selected = [row for row in rows if predicate(float(row["ascent_per_km"]))]
        terrain_groups[label] = {
            "generic": _metric_summary([
                {"observed_s": float(row["observed_s"]), "error_s": float(row["generic_s"]) - float(row["observed_s"])}
                for row in selected
            ]),
            "personal": _metric_summary([
                {"observed_s": float(row["observed_s"]), "error_s": float(row["personal_s"]) - float(row["observed_s"])}
                for row in selected
            ]),
        }
    behaviour_groups: dict[str, dict[str, object]] = {}
    for signature in sorted({activity.behaviour_signature for activity in activities}):
        selected = [row for row in rows if row["behaviour_signature"] == signature]
        behaviour_groups[signature] = {
            "generic": _metric_summary([
                {"observed_s": float(row["observed_s"]), "error_s": float(row["generic_s"]) - float(row["observed_s"])}
                for row in selected
            ]),
            "personal": _metric_summary([
                {"observed_s": float(row["observed_s"]), "error_s": float(row["personal_s"]) - float(row["observed_s"])}
                for row in selected
            ]),
        }
    return {
        "fold_assignments": assignments,
        "repeat_count": repeat_count,
        "rows": rows,
        "generic": _metric_summary(generic_rows),
        "personal": _metric_summary(personal_rows),
        "by_duration": duration_groups,
        "by_terrain_character": terrain_groups,
        "by_behaviour_signature": behaviour_groups,
        "terrain_group_thresholds_ascent_per_km": [lower_ascent, upper_ascent],
    }


def progression_validation(
    activities: Sequence[ActivityObservations],
    fold_count: int = 5,
    repeat_count: int = 5,
) -> dict[str, object]:
    by_key = {activity.key: activity for activity in activities}
    predictions: dict[tuple[str, float], list[float]] = {}
    observed_values: dict[tuple[str, float], tuple[float, float]] = {}
    for repeat in range(repeat_count):
        folds = activity_folds(activities, fold_count, VALIDATION_SEED + repeat)
        for test_keys in folds:
            test_set = set(test_keys)
            model = fit_personal_slope_model(
                [activity for activity in activities if activity.key not in test_set]
            )
            for key in test_keys:
                activity = by_key[key]
                for target in (0.25, 0.5, 0.75):
                    observed = generic = personal = 0.0
                    for item in activity.observations:
                        if item.progress > target:
                            break
                        observed += item.duration_s
                        generic += item.distance_m / generic_tobler_speed_mps(item.gradient)
                        personal += item.distance_m / model.speed_mps(item.gradient)
                    if observed > 0:
                        predictions.setdefault((key, target), []).append(personal)
                        observed_values[(key, target)] = (observed, generic)
    rows: list[dict[str, float]] = []
    for key_target, personal_predictions in predictions.items():
        observed, generic = observed_values[key_target]
        rows.append(
            {
                "progress": key_target[1],
                "generic_absolute_percentage_error": abs(generic - observed) / observed * 100,
                "personal_absolute_percentage_error": abs(median(personal_predictions) - observed) / observed * 100,
            }
        )
    return {
        "sample_count": len(rows),
        "generic_median_absolute_percentage_error": percentile(
            [row["generic_absolute_percentage_error"] for row in rows], 0.5
        ),
        "personal_median_absolute_percentage_error": percentile(
            [row["personal_absolute_percentage_error"] for row in rows], 0.5
        ),
        "by_progress": {
            str(target): {
                "generic_median_absolute_percentage_error": percentile(
                    [row["generic_absolute_percentage_error"] for row in rows if row["progress"] == target], 0.5
                ),
                "personal_median_absolute_percentage_error": percentile(
                    [row["personal_absolute_percentage_error"] for row in rows if row["progress"] == target], 0.5
                ),
            }
            for target in (0.25, 0.5, 0.75)
        },
    }


def fatigue_diagnostics(
    activities: Sequence[ActivityObservations], model: PersonalSlopeModel
) -> dict[str, object]:
    activity_quartile_ratios: list[list[float]] = [[] for _ in range(4)]
    for activity in activities:
        quartiles: list[list[float]] = [[] for _ in range(4)]
        for observation in activity.observations:
            index = min(3, int(observation.progress * 4))
            expected = model.speed_mps(observation.gradient)
            quartiles[index].append(math.log(observation.observed_speed_mps / expected))
        for index, values in enumerate(quartiles):
            if values:
                activity_quartile_ratios[index].append(median(values))
    ratios = [
        math.exp(median(values)) if values else None
        for values in activity_quartile_ratios
    ]
    change = None
    if ratios[0] is not None and ratios[-1] is not None:
        change = (ratios[-1] / ratios[0] - 1) * 100
    return {
        "median_speed_ratio_by_distance_quartile": ratios,
        "final_vs_initial_percentage": change,
        "activity_counts": [len(values) for values in activity_quartile_ratios],
        "aggregation": "equal_weight_per_activity_after_within_activity_median",
    }


def behavioural_mode_diagnostic(
    activities: Sequence[ActivityObservations], model: PersonalSlopeModel
) -> dict[str, object]:
    values: list[float] = []
    for activity in activities:
        ratios = [
            math.log(item.observed_speed_mps / model.speed_mps(item.gradient))
            for item in activity.observations
        ]
        if ratios:
            values.append(median(ratios))
    if len(values) < 10:
        return {"supported": False, "reason": "too_few_complete_activities"}
    centres = [percentile(values, 0.25) or 0.0, percentile(values, 0.75) or 0.0]
    groups: list[list[float]] = [[], []]
    for _ in range(30):
        groups = [[], []]
        for value in values:
            index = 0 if abs(value - centres[0]) <= abs(value - centres[1]) else 1
            groups[index].append(value)
        updated = [sum(group) / len(group) if group else centres[index] for index, group in enumerate(groups)]
        if max(abs(updated[index] - centres[index]) for index in range(2)) < 1e-6:
            break
        centres = updated
    single_mad = median(abs(value - median(values)) for value in values)
    grouped_mad = sum(
        sum(abs(value - median(group)) for value in group) for group in groups if group
    ) / len(values)
    separation = abs(centres[1] - centres[0])
    reduction = 0.0 if single_mad == 0 else 1 - grouped_mad / single_mad
    supported = min(len(group) for group in groups) >= 5 and separation >= math.log(1.25) and reduction >= 0.35
    return {
        "supported": supported,
        "activity_count": len(values),
        "group_sizes": [len(group) for group in groups],
        "relative_speed_centres": [math.exp(value) for value in sorted(centres)],
        "log_separation": separation,
        "absolute_deviation_reduction": reduction,
        "interpretation": (
            "distinct_pace_regimes_need_contextual_validation"
            if supported
            else "one_curve_variability_does_not_justify_profiles"
        ),
    }


def slope_model_rows(model: PersonalSlopeModel) -> list[dict[str, float | int]]:
    return [
        {
            "gradient": item.centre,
            "generic_speed_kmh": generic_tobler_speed_mps(item.centre) * 3.6,
            "personal_speed_kmh": model.speed_mps(item.centre) * 3.6,
            "raw_ratio": item.raw_ratio,
            "shrunk_ratio": item.shrunk_ratio,
            "evidence_distance_km": item.distance_m / 1000,
            "observation_count": item.observation_count,
        }
        for item in model.bins
    ]
