"""Deterministic diagnostics for Earth Lab 008's frozen Lab 007 audit."""
from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from underlying_surface_model import CLASSES, normalized_entropy

MEANINGFUL_CLASSES = CLASSES[:-1]
UNKNOWN_INDEX = len(CLASSES) - 1


def meaningful_ranking(probabilities: np.ndarray) -> dict[str, np.ndarray]:
    values = np.asarray(probabilities, dtype=np.float64)
    meaningful = values[..., :UNKNOWN_INDEX]
    order = np.argsort(meaningful, axis=-1)[..., ::-1]
    first = np.take_along_axis(meaningful, order[..., :1], axis=-1)[..., 0]
    second = np.take_along_axis(meaningful, order[..., 1:2], axis=-1)[..., 0]
    return {
        "first_index": order[..., 0],
        "second_index": order[..., 1],
        "first_probability": first,
        "second_probability": second,
        "margin": first - second,
        "meaningful_mass": np.sum(meaningful, axis=-1),
        "unknown_dominant": values[..., UNKNOWN_INDEX] > first,
    }


def conditional_meaningful_entropy(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float64)[..., :UNKNOWN_INDEX]
    totals = np.sum(values, axis=-1, keepdims=True)
    normalized = np.divide(values, totals, out=np.full_like(values, 1 / UNKNOWN_INDEX), where=totals > 0)
    safe = np.where(normalized > 0, normalized, 1.0)
    entropy = -np.sum(np.where(normalized > 0, normalized * np.log(safe), 0.0), axis=-1) / np.log(UNKNOWN_INDEX)
    return np.clip(entropy, 0.0, 1.0)


def pair_codes(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    low = np.minimum(first, second)
    high = np.maximum(first, second)
    return (low * len(MEANINGFUL_CLASSES) + high + 1).astype(np.uint8)


def pair_name(code: int) -> str:
    value = int(code) - 1
    low, high = divmod(value, len(MEANINGFUL_CLASSES))
    return f"{MEANINGFUL_CLASSES[low]}__{MEANINGFUL_CLASSES[high]}"


def top_pair_summary(first: np.ndarray, second: np.ndarray, valid: np.ndarray) -> list[dict[str, Any]]:
    codes = pair_codes(first, second)
    counts = Counter(int(value) for value in codes[np.asarray(valid, dtype=bool)])
    total = max(int(np.count_nonzero(valid)), 1)
    return [
        {"pair": pair_name(code), "cells": count, "fraction": count / total}
        for code, count in counts.most_common()
    ]


def ablation_metrics(baseline: np.ndarray, ablated: np.ndarray, valid: np.ndarray, threshold: float) -> dict[str, Any]:
    baseline = np.asarray(baseline, dtype=np.float64)
    ablated = np.asarray(ablated, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool)
    delta = ablated - baseline
    tvd = 0.5 * np.sum(np.abs(delta), axis=-1)
    baseline_rank = meaningful_ranking(baseline)
    ablated_rank = meaningful_ranking(ablated)
    return {
        "mean_total_variation_distance": float(np.nanmean(tvd[valid])),
        "p95_total_variation_distance": float(np.nanpercentile(tvd[valid], 95)),
        "materially_affected_fraction": float(np.mean(tvd[valid] >= threshold)),
        "meaningful_dominant_changed_fraction": float(np.mean(
            baseline_rank["first_index"][valid] != ablated_rank["first_index"][valid]
        )),
        "unknown_dominance_changed_fraction": float(np.mean(
            baseline_rank["unknown_dominant"][valid] != ablated_rank["unknown_dominant"][valid]
        )),
        "mean_probability_delta": {
            name: float(np.nanmean(delta[..., index][valid]))
            for index, name in enumerate(CLASSES)
        },
        "mean_entropy_delta": float(np.nanmean(
            normalized_entropy(ablated)[valid] - normalized_entropy(baseline)[valid]
        )),
        "mean_other_unknown_delta": float(np.nanmean(delta[..., UNKNOWN_INDEX][valid])),
    }


def gap_flags(
    probabilities: np.ndarray,
    conflict: np.ndarray,
    family_count: np.ndarray,
    temporal_variability: np.ndarray,
    source_preferences: dict[str, np.ndarray],
    thresholds: dict[str, float],
    overlapping_pairs: set[frozenset[str]],
    flag_values: dict[str, int],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    ranking = meaningful_ranking(probabilities)
    valid = np.all(np.isfinite(probabilities), axis=-1)
    conflict_cut = float(np.nanpercentile(conflict[valid], thresholds["source_conflict_percentile"]))
    temporal_cut = float(np.nanpercentile(temporal_variability[valid], thresholds["temporal_variability_percentile"]))
    first_names = np.asarray(MEANINGFUL_CLASSES, dtype=object)[ranking["first_index"]]
    second_names = np.asarray(MEANINGFUL_CLASSES, dtype=object)[ranking["second_index"]]
    overlap = np.zeros(valid.shape, dtype=bool)
    for left, right in overlapping_pairs:
        overlap |= ((first_names == left) & (second_names == right)) | ((first_names == right) & (second_names == left))

    source_specificity = {
        source: 1.0 - normalized_entropy(values)
        for source, values in source_preferences.items()
    }
    contextual_dependence = (
        (source_specificity["habitat"] + source_specificity["geology"])
        > (source_specificity["terrain"] + source_specificity["sentinel"])
    )
    weak = ranking["margin"] <= thresholds["meaningful_margin_weak"]
    flags = {
        "source_conflict": valid & (conflict >= conflict_cut),
        "weak_discrimination": valid & weak,
        "coarse_evidence": valid & weak & contextual_dependence,
        "temporal_ambiguity": valid & (temporal_variability >= temporal_cut) & weak,
        "ontology_ambiguity": valid & overlap & (ranking["margin"] <= thresholds["meaningful_margin_strong"]),
        "missing_evidence": valid & (family_count < 4),
    }
    count = sum(mask.astype(np.uint8) for mask in flags.values())
    flags["mixed_unresolved"] = valid & (count >= 2)
    bitmask = np.zeros(valid.shape, dtype=np.uint8)
    for name, mask in flags.items():
        bitmask[mask] |= np.uint8(flag_values[name])
    return bitmask, flags


def reconstruction_readiness(probabilities: np.ndarray, thresholds: dict[str, float]) -> np.ndarray:
    ranking = meaningful_ranking(probabilities)
    valid = np.all(np.isfinite(probabilities), axis=-1)
    result = np.zeros(valid.shape, dtype=np.uint8)
    constrained = (
        (ranking["margin"] >= thresholds["meaningful_margin_strong"])
        & (ranking["first_probability"] >= thresholds["meaningful_top_minimum"])
        & (probabilities[..., UNKNOWN_INDEX] < thresholds["unknown_high"])
    )
    high_freedom = (
        (probabilities[..., UNKNOWN_INDEX] >= thresholds["unknown_high"])
        | (ranking["margin"] <= thresholds["meaningful_margin_weak"] / 2)
    )
    result[valid] = 2
    result[valid & constrained] = 1
    result[valid & high_freedom] = 3
    return result
