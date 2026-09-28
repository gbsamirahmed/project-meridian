"""Deterministic, interpretable evidence fusion for Earth Lab 007."""
from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np

CLASSES = ("rock", "scree_talus", "heath", "grass", "wet_ground", "other_unknown")
UNKNOWN_INDEX = 5


def smoothstep(values: np.ndarray, lower: float, upper: float) -> np.ndarray:
    if upper <= lower:
        raise ValueError("upper must be greater than lower")
    scaled = np.clip((np.asarray(values, dtype=np.float64) - lower) / (upper - lower), 0.0, 1.0)
    return scaled * scaled * (3.0 - 2.0 * scaled)


def normalized_entropy(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float64)
    safe = np.where(values > 0, values, 1.0)
    return -np.sum(np.where(values > 0, values * np.log(safe), 0.0), axis=-1) / np.log(values.shape[-1])


def normalize_preferences(raw: np.ndarray) -> np.ndarray:
    values = np.maximum(np.asarray(raw, dtype=np.float64), 0.0)
    totals = np.sum(values, axis=-1, keepdims=True)
    fallback = np.zeros_like(values)
    fallback[..., UNKNOWN_INDEX] = 1.0
    return np.divide(values, totals, out=fallback, where=totals > 0)


def jensen_shannon(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    a = normalize_preferences(left)
    b = normalize_preferences(right)
    middle = 0.5 * (a + b)
    def divergence(values):
        ratio = np.divide(values, middle, out=np.ones_like(values), where=(values > 0) & (middle > 0))
        return np.sum(np.where(values > 0, values * np.log2(ratio), 0.0), axis=-1)
    return 0.5 * (divergence(a) + divergence(b))


def terrain_preferences(slope: np.ndarray, roughness: np.ndarray, rules: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    slope = np.asarray(slope, dtype=np.float64)
    roughness = np.asarray(roughness, dtype=np.float64)
    available = np.isfinite(slope) & np.isfinite(roughness)
    steep = smoothstep(slope, *rules["steep_ramp_degrees"])
    gentle = 1.0 - smoothstep(slope, *rules["gentle_ramp_degrees"])
    rough = smoothstep(roughness, *rules["rough_ramp_m_rms"])
    smooth = 1.0 - smoothstep(roughness, *rules["smooth_ramp_m_rms"])
    middle = np.clip(1.0 - np.abs(slope - 24.0) / 24.0, 0.0, 1.0)
    raw = np.stack((
        0.12 + 0.55 * steep + 0.45 * rough + 0.35 * steep * rough,
        0.10 + 0.45 * steep + 0.35 * rough,
        0.25 + 0.35 * middle,
        0.25 + 0.60 * gentle,
        0.10 + 0.65 * gentle * smooth,
        np.full(slope.shape, 0.25),
    ), axis=-1)
    return normalize_preferences(raw), available


def sentinel_preferences(ndvi: np.ndarray, ndvi_stddev: np.ndarray, ndmi: np.ndarray, persistent_low_ndvi: np.ndarray, rules: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    ndvi = np.asarray(ndvi, dtype=np.float64)
    deviation = np.asarray(ndvi_stddev, dtype=np.float64)
    ndmi = np.asarray(ndmi, dtype=np.float64)
    persistent = np.asarray(persistent_low_ndvi, dtype=bool)
    available = np.isfinite(ndvi) & np.isfinite(deviation)
    vegetation = smoothstep(ndvi, *rules["vegetation_ndvi_ramp"])
    stable = 1.0 - smoothstep(deviation, *rules["stable_ndvi_stddev_ramp"])
    moisture = np.where(np.isfinite(ndmi), smoothstep(ndmi, *rules["moisture_ndmi_ramp"]), 0.0)
    low_stable = (1.0 - vegetation) * stable
    small = float(rules["persistent_low_ndvi_maximum_rock_increment"])
    raw = np.stack((
        0.08 + 0.08 * low_stable + small * persistent,
        0.07 + 0.06 * low_stable + small * persistent,
        0.20 + 0.42 * vegetation,
        0.20 + 0.42 * vegetation,
        0.12 + 0.18 * vegetation + 0.20 * moisture,
        0.35 + 0.65 * (1.0 - stable) + 0.12 * persistent,
    ), axis=-1)
    return normalize_preferences(raw), available


def categorical_preferences(values: np.ndarray, lookup: dict[int, str], preference_map: dict[str, list[float]]) -> tuple[np.ndarray, np.ndarray]:
    identifiers = np.asarray(values)
    result = np.zeros(identifiers.shape + (len(CLASSES),), dtype=np.float64)
    available = identifiers != 0
    for identifier in np.unique(identifiers):
        if int(identifier) == 0:
            continue
        name = lookup.get(int(identifier), "other_or_unknown")
        preference = preference_map.get(name, preference_map.get("other_or_unknown", [0, 0, 0, 0, 0, 1]))
        result[identifiers == identifier] = preference
    result[~available, UNKNOWN_INDEX] = 1.0
    return normalize_preferences(result), available


def geology_preferences(superficial_groups: np.ndarray, superficial_lookup: dict[int, str], bedrock_groups: np.ndarray, superficial_map: dict[str, list[float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    superficial = np.asarray(superficial_groups)
    bedrock = np.asarray(bedrock_groups)
    available = bedrock != 0
    mapped_superficial = superficial != 0
    result = np.zeros(superficial.shape + (len(CLASSES),), dtype=np.float64)
    result[...] = superficial_map["none_mapped"]
    for identifier in np.unique(superficial):
        if int(identifier) == 0:
            continue
        name = superficial_lookup.get(int(identifier), "other_superficial_deposit")
        result[superficial == identifier] = superficial_map.get(name, superficial_map["other_superficial_deposit"])
    # Bedrock is contextual only: it adds a tiny generic exposure plausibility and
    # mostly uncertainty. It cannot determine exposure or a surface class.
    result[..., 0] += np.where(available, 0.025, 0.0)
    result[..., 1] += np.where(available, 0.015, 0.0)
    result[..., UNKNOWN_INDEX] += np.where(available, 0.10, 0.0)
    result[~available] = np.array([0, 0, 0, 0, 0, 1], dtype=np.float64)
    return normalize_preferences(result), available, mapped_superficial


def fuse_sources(preferences: dict[str, np.ndarray], availability: dict[str, np.ndarray], budgets: dict[str, float], baseline: list[float] | np.ndarray, missing_unknown_support: float, conflict_unknown_support: float, valid_model: np.ndarray) -> dict[str, Any]:
    shape = np.asarray(valid_model).shape
    scores = np.broadcast_to(np.asarray(baseline, dtype=np.float64), shape + (len(CLASSES),)).copy()
    contributions: dict[str, np.ndarray] = {}
    for source, preference in preferences.items():
        available = np.asarray(availability[source], dtype=bool)
        contribution = np.asarray(preference, dtype=np.float64) * float(budgets[source]) * available[..., None]
        contributions[source] = contribution
        scores += contribution
        scores[..., UNKNOWN_INDEX] += (~available) * float(missing_unknown_support)

    conflict_sum = np.zeros(shape, dtype=np.float64)
    conflict_weight = np.zeros(shape, dtype=np.float64)
    for left, right in combinations(preferences, 2):
        both = np.asarray(availability[left], dtype=bool) & np.asarray(availability[right], dtype=bool)
        left_specificity = 1.0 - normalized_entropy(preferences[left])
        right_specificity = 1.0 - normalized_entropy(preferences[right])
        weight = np.sqrt(np.maximum(left_specificity, 0) * np.maximum(right_specificity, 0)) * both
        conflict_sum += jensen_shannon(preferences[left], preferences[right]) * weight
        conflict_weight += weight
    conflict = np.divide(conflict_sum, conflict_weight, out=np.zeros(shape), where=conflict_weight > 0)
    scores[..., UNKNOWN_INDEX] += conflict * float(conflict_unknown_support)
    probabilities = normalize_preferences(scores)
    probabilities[~valid_model] = np.nan
    uncertainty = normalized_entropy(np.where(np.isfinite(probabilities), probabilities, 1 / len(CLASSES)))
    uncertainty[~valid_model] = np.nan
    dominant = np.zeros(shape, dtype=np.uint8)
    dominant[valid_model] = np.argmax(probabilities[valid_model], axis=-1).astype(np.uint8) + 1
    return {"scores": scores, "probabilities": probabilities, "uncertainty": uncertainty, "dominant": dominant, "conflict": conflict, "contributions": contributions}
