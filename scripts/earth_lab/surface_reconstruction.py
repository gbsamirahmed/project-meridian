"""Deterministic evidence-constrained surface reconstruction for Earth Lab 009.

The scientific Lab 007 probabilities remain immutable.  This module derives a
separate renderer-oriented mixture at the exact Unreal Landscape vertex grid.
Procedural variation is explicitly reconstruction, never observation.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image
VISUAL_CLASSES = ("rock", "scree_talus", "heath", "grass", "wet_ground")
LAB007_CLASSES = VISUAL_CLASSES + ("other_unknown",)
READINESS_NAMES = {
    1: "broad_tendency_constrained",
    2: "guided_mixture_reconstruction",
    3: "high_reconstruction_freedom",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str) -> str:
    observed = sha256_file(path)
    if observed != expected:
        raise RuntimeError(
            f"Frozen input changed: {path} expected {expected}, observed {observed}"
        )
    return observed


def smoothstep(values: np.ndarray, lower: float, upper: float) -> np.ndarray:
    if not math.isfinite(lower) or not math.isfinite(upper) or upper <= lower:
        raise ValueError("smoothstep bounds must be finite and increasing")
    scaled = np.clip((np.asarray(values, dtype=np.float32) - lower) / (upper - lower), 0.0, 1.0)
    return scaled * scaled * (3.0 - 2.0 * scaled)


def normalize_known(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float32)
    if values.shape[-1] != len(VISUAL_CLASSES):
        raise ValueError(f"Expected {len(VISUAL_CLASSES)} visual classes")
    values = np.maximum(values, 0.0)
    totals = np.sum(values, axis=-1, keepdims=True)
    fallback = np.full_like(values, 1.0 / len(VISUAL_CLASSES))
    return np.divide(values, totals, out=fallback, where=totals > 1e-8)


def normalized_entropy(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float64)
    safe = np.where(values > 0.0, values, 1.0)
    return (
        -np.sum(np.where(values > 0.0, values * np.log(safe), 0.0), axis=-1)
        / math.log(values.shape[-1])
    ).astype(np.float32)


def _coarse_noise(
    shape: tuple[int, int],
    spacing_samples: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Return smooth deterministic unit-variance noise without periodic tiling."""
    spacing = max(float(spacing_samples), 2.0)
    coarse_shape = (
        max(4, int(math.ceil(shape[0] / spacing)) + 3),
        max(4, int(math.ceil(shape[1] / spacing)) + 3),
    )
    coarse = rng.standard_normal(coarse_shape, dtype=np.float32)
    field = np.asarray(
        Image.fromarray(coarse, mode="F").resize(
            (shape[1], shape[0]),
            resample=Image.Resampling.BICUBIC,
        ),
        dtype=np.float32,
    ).copy()
    field -= float(np.mean(field))
    deviation = float(np.std(field))
    if deviation <= 1e-8:
        raise RuntimeError("Deterministic spatial field unexpectedly has zero variance")
    return np.clip(field / deviation, -2.75, 2.75).astype(np.float32)


def coherent_field(
    shape: tuple[int, int],
    *,
    seed: int,
    vertex_spacing_m: float,
    scales_m: Iterable[float],
    weights: Iterable[float],
) -> np.ndarray:
    scales = tuple(float(value) for value in scales_m)
    scale_weights = np.asarray(tuple(float(value) for value in weights), dtype=np.float32)
    if len(scales) == 0 or len(scales) != len(scale_weights):
        raise ValueError("Procedural scales and weights must be non-empty and aligned")
    if np.any(scale_weights < 0.0) or float(np.sum(scale_weights)) <= 0.0:
        raise ValueError("Procedural weights must be non-negative with positive sum")
    scale_weights /= np.sum(scale_weights)
    rng = np.random.default_rng(int(seed))
    result = np.zeros(shape, dtype=np.float32)
    for scale_m, weight in zip(scales, scale_weights):
        if scale_m <= 0.0:
            raise ValueError("Procedural scales must be positive")
        result += weight * _coarse_noise(shape, scale_m / vertex_spacing_m, rng)
    result -= float(np.mean(result))
    deviation = float(np.std(result))
    return np.clip(result / max(deviation, 1e-8), -2.75, 2.75).astype(np.float32)


def terrain_logit_adjustments(
    slope_degrees: np.ndarray,
    roughness_m: np.ndarray,
    laplacian_per_m: np.ndarray,
    settings: dict[str, Any],
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Create bounded physical placement preferences, not surface observations."""
    slope = np.nan_to_num(np.asarray(slope_degrees, dtype=np.float32), nan=0.0)
    roughness = np.nan_to_num(np.asarray(roughness_m, dtype=np.float32), nan=0.0)
    curvature = np.nan_to_num(np.asarray(laplacian_per_m, dtype=np.float32), nan=0.0)
    steep = smoothstep(slope, *settings["slope_ramp_degrees"])
    gentle = 1.0 - smoothstep(slope, *settings["gentle_ramp_degrees"])
    rough = smoothstep(roughness, *settings["roughness_ramp_m_rms"])
    curvature_scale = float(settings["curvature_scale_per_m"])
    convex = np.clip(-curvature / curvature_scale, 0.0, 1.0)
    concave = np.clip(curvature / curvature_scale, 0.0, 1.0)
    middle_slope = np.clip(1.0 - np.abs(slope - 24.0) / 24.0, 0.0, 1.0)

    raw = np.stack(
        (
            0.25 * (steep - 0.5) + 0.22 * (rough - 0.5) + 0.08 * convex,
            0.20 * (steep - 0.45) + 0.18 * (rough - 0.45) + 0.10 * concave,
            0.10 * (middle_slope - 0.5) - 0.05 * steep,
            0.14 * (gentle - 0.5) - 0.07 * rough,
            0.22 * (gentle - 0.5) + 0.16 * (concave - 0.25) - 0.08 * rough,
        ),
        axis=-1,
    )
    maximum = float(settings["maximum_logit_adjustment"])
    return np.clip(raw, -maximum, maximum).astype(np.float32), {
        "steep": steep,
        "gentle": gentle,
        "rough": rough,
        "convex": convex,
        "concave": concave,
    }


def reconstruction_freedom(
    other_unknown: np.ndarray,
    uncertainty: np.ndarray,
    readiness: np.ndarray,
) -> np.ndarray:
    other = np.clip(np.asarray(other_unknown, dtype=np.float32), 0.0, 1.0)
    entropy = np.clip(np.asarray(uncertainty, dtype=np.float32), 0.0, 1.0)
    regime = np.asarray(readiness, dtype=np.uint8)
    regime_level = np.choose(np.clip(regime, 1, 3) - 1, [0.15, 0.50, 0.85]).astype(np.float32)
    return np.clip(0.45 * other + 0.30 * entropy + 0.25 * regime_level, 0.0, 1.0)


def reconstruct_controls(
    probabilities: np.ndarray,
    readiness: np.ndarray,
    slope_degrees: np.ndarray,
    roughness_m: np.ndarray,
    laplacian_per_m: np.ndarray,
    *,
    seed: int,
    vertex_spacing_m: float,
    scales_m: Iterable[float],
    scale_weights: Iterable[float],
    regime_amplitudes: dict[str, float],
    terrain_settings: dict[str, Any],
) -> dict[str, np.ndarray]:
    probabilities = np.asarray(probabilities, dtype=np.float32)
    if probabilities.ndim != 3 or probabilities.shape[-1] != len(LAB007_CLASSES):
        raise ValueError("probabilities must have shape (rows, columns, 6)")
    shape = probabilities.shape[:2]
    for name, value in (
        ("readiness", readiness),
        ("slope", slope_degrees),
        ("roughness", roughness_m),
        ("curvature", laplacian_per_m),
    ):
        if np.asarray(value).shape != shape:
            raise ValueError(f"{name} does not match the probability grid")
    if not np.all(np.isfinite(probabilities)):
        raise ValueError("Lab 007 probabilities contain non-finite values")
    if np.any(probabilities < -1e-6) or np.any(probabilities > 1.0 + 1e-6):
        raise ValueError("Lab 007 probabilities are outside [0,1]")

    known = normalize_known(probabilities[..., :5])
    uncertainty = normalized_entropy(probabilities)
    freedom = reconstruction_freedom(probabilities[..., 5], uncertainty, readiness)
    terrain_adjustment, terrain_channels = terrain_logit_adjustments(
        slope_degrees, roughness_m, laplacian_per_m, terrain_settings
    )

    amplitudes = np.zeros(shape, dtype=np.float32)
    for regime in (1, 2, 3):
        amplitudes[np.asarray(readiness) == regime] = float(regime_amplitudes[str(regime)])
    if np.any(amplitudes == 0.0):
        raise ValueError("Readiness contains unsupported or nodata values")

    noise_channels = []
    for class_index in range(len(VISUAL_CLASSES)):
        noise_channels.append(
            coherent_field(
                shape,
                seed=int(seed) + class_index * 7919,
                vertex_spacing_m=vertex_spacing_m,
                scales_m=scales_m,
                weights=scale_weights,
            )
        )
    noise = np.stack(noise_channels, axis=-1)
    logits = np.log(np.maximum(known, 1e-6))
    logits += terrain_adjustment
    logits += amplitudes[..., None] * noise
    logits -= np.max(logits, axis=-1, keepdims=True)
    controls = np.exp(logits).astype(np.float32)
    controls /= np.sum(controls, axis=-1, keepdims=True)

    return {
        "controls": controls,
        "freedom": freedom,
        "lab007_uncertainty": uncertainty,
        "procedural_field": np.mean(noise, axis=-1).astype(np.float32),
        "terrain_influence": np.mean(np.abs(terrain_adjustment), axis=-1).astype(np.float32),
        **terrain_channels,
    }


def neighbor_correlation(values: np.ndarray) -> float:
    field = np.asarray(values, dtype=np.float64)
    pairs = []
    for left, right in ((field[:, :-1], field[:, 1:]), (field[:-1, :], field[1:, :])):
        valid = np.isfinite(left) & np.isfinite(right)
        if np.count_nonzero(valid) > 1:
            pairs.append(float(np.corrcoef(left[valid], right[valid])[0, 1]))
    return float(np.mean(pairs)) if pairs else float("nan")


def coarse_boundary_jump(values: np.ndarray, coarse_factor: float) -> dict[str, float]:
    """Compare changes near original 10 m boundaries with all adjacent changes."""
    field = np.asarray(values, dtype=np.float64)
    dx = np.abs(np.diff(field, axis=1))
    dy = np.abs(np.diff(field, axis=0))
    x_boundaries = np.zeros(dx.shape[1], dtype=bool)
    y_boundaries = np.zeros(dy.shape[0], dtype=bool)
    for boundary in np.arange(1.0, 300.0) * coarse_factor:
        column = int(round(boundary)) - 1
        row = int(round(boundary)) - 1
        if 0 <= column < x_boundaries.size:
            x_boundaries[column] = True
        if 0 <= row < y_boundaries.size:
            y_boundaries[row] = True
    boundary_values = np.concatenate((dx[:, x_boundaries].ravel(), dy[y_boundaries, :].ravel()))
    all_values = np.concatenate((dx.ravel(), dy.ravel()))
    boundary_mean = float(np.mean(boundary_values))
    overall_mean = float(np.mean(all_values))
    return {
        "mean_absolute_jump_at_10m_boundaries": boundary_mean,
        "mean_absolute_jump_all_neighbors": overall_mean,
        "boundary_to_all_ratio": boundary_mean / max(overall_mean, 1e-12),
    }


def stable_json_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
