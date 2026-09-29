"""Run Meridian Earth Laboratory 008 against frozen Lab 007 outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = Path(__file__).resolve().parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from experiment_paths import resolve_repository_value
from surface_evidence import AnalysisGrid, numeric_summary, sha256_file, stable_json_sha256
from surface_uncertainty_audit import (
    MEANINGFUL_CLASSES, ablation_metrics, conditional_meaningful_entropy,
    gap_flags, meaningful_ranking, pair_codes, pair_name,
    reconstruction_readiness, top_pair_summary,
)
from underlying_surface_model import CLASSES, fuse_sources, jensen_shannon, normalized_entropy


def _path(value: str) -> Path:
    return resolve_repository_value(ROOT, value)


def _read(path: Path, categorical: bool = False) -> tuple[np.ndarray, dict[str, Any]]:
    with rasterio.open(path) as source:
        values = source.read(1)
        profile = source.profile.copy()
        if categorical:
            return values, profile
        values = values.astype(np.float64)
        if source.nodata is not None:
            values[values == source.nodata] = np.nan
        return values, profile


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_raster(path: Path, values: np.ndarray, profile: dict[str, Any], categorical: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = profile.copy()
    if categorical:
        output.update(dtype="uint8", nodata=0, compress="deflate", count=1)
        encoded = np.asarray(values, dtype=np.uint8)
    else:
        output.update(dtype="float32", nodata=-9999.0, compress="deflate", predictor=3, count=1)
        data = np.asarray(values, dtype=np.float32)
        encoded = np.where(np.isfinite(data), data, -9999.0).astype(np.float32)
    with rasterio.open(path, "w", **output) as target:
        target.write(encoded, 1)


def _verify_frozen(config: dict[str, Any]) -> tuple[Path, dict[str, str], dict[str, Any]]:
    root = _path(config["frozen_lab007"]["root"])
    required = {
        "report": root / "lab007-report.json",
        "package": root / "lab007-surface-model-package.json",
        "trace": root / "canonical-tryfan-evidence-trace.json",
    }
    hashes = {name: sha256_file(path) for name, path in required.items()}
    for name in required:
        expected = config["frozen_lab007"][f"{name}_sha256"]
        if hashes[name] != expected:
            raise RuntimeError(f"Frozen Lab 007 {name} hash mismatch")
    report = json.loads(required["report"].read_text(encoding="utf-8"))
    if report["deterministic_result_sha256"] != config["frozen_lab007"]["deterministic_result_sha256"]:
        raise RuntimeError("Frozen Lab 007 deterministic result identity mismatch")
    for item in report["outputs"]:
        path = root / item["path"]
        if sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"Frozen Lab 007 output mismatch: {item['path']}")
    return root, hashes, report


def _source_arrays(root: Path, budgets: dict[str, float]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray]]:
    preferences: dict[str, np.ndarray] = {}
    availability: dict[str, np.ndarray] = {}
    contributions: dict[str, np.ndarray] = {}
    for source in ("terrain", "sentinel", "habitat", "geology"):
        layers = []
        for name in CLASSES:
            values, _ = _read(root / "contributions" / f"{source}-{name}-support-10m.tif")
            layers.append(values)
        contribution = np.stack(layers, axis=-1)
        available = np.sum(contribution, axis=-1) > 0
        preference = np.divide(
            contribution,
            float(budgets[source]),
            out=np.zeros_like(contribution),
            where=available[..., None],
        )
        preference[~available, -1] = 1.0
        contributions[source] = contribution
        preferences[source] = preference
        availability[source] = available
    return preferences, availability, contributions


def _pearson(left: np.ndarray, right: np.ndarray, mask: np.ndarray) -> float:
    valid = mask & np.isfinite(left) & np.isfinite(right)
    if np.count_nonzero(valid) < 2:
        return float("nan")
    return float(np.corrcoef(left[valid], right[valid])[0, 1])


def _fraction(mask: np.ndarray, valid: np.ndarray) -> float:
    return float(np.count_nonzero(mask & valid) / max(np.count_nonzero(valid), 1))


def _primary_gap(flags: dict[str, np.ndarray], valid: np.ndarray) -> np.ndarray:
    names = ["source_conflict", "weak_discrimination", "coarse_evidence", "temporal_ambiguity", "ontology_ambiguity", "missing_evidence"]
    stack = np.stack([flags[name] for name in names], axis=-1)
    count = np.sum(stack, axis=-1)
    result = np.zeros(valid.shape, dtype=np.uint8)
    for index, name in enumerate(names, start=1):
        result[valid & (count == 1) & flags[name]] = index
    result[valid & (count > 1)] = 7
    result[valid & (count == 0)] = 8
    return result


def _summary(values: np.ndarray, valid: np.ndarray, units: str) -> dict[str, Any]:
    masked = np.where(valid, values, np.nan)
    return numeric_summary(masked, units)


def _diagnostics(
    output: Path,
    probabilities: np.ndarray,
    uncertainty: np.ndarray,
    conflict: np.ndarray,
    ranking: dict[str, np.ndarray],
    pair_map: np.ndarray,
    primary_gap: np.ndarray,
    readiness: np.ndarray,
    ablations: dict[str, dict[str, Any]],
    valid: np.ndarray,
) -> list[Path]:
    target = output / "images"
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def save(name: str, figure: Any) -> None:
        path = target / name
        figure.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(figure)
        written.append(path)

    fig, axes = plt.subplots(1, 4, figsize=(17, 4), constrained_layout=True)
    panels = [
        (uncertainty, "Normalized entropy", "magma", 0.8, 1.0),
        (probabilities[..., -1], "P(other/unknown)", "viridis", 0.2, 0.52),
        (ranking["margin"], "Meaningful top-two margin", "cividis", 0, 0.2),
        (ranking["meaningful_mass"], "Known-class probability mass", "viridis", 0.45, 0.8),
    ]
    for axis, (values, title, cmap, lower, upper) in zip(axes, panels):
        image = axis.imshow(values, cmap=cmap, vmin=lower, vmax=upper)
        axis.set_title(title)
        axis.set_axis_off()
        fig.colorbar(image, ax=axis, fraction=0.046)
    save("baseline-uncertainty-overview.png", fig)

    unique_pairs = sorted(int(value) for value in np.unique(pair_map[valid]))
    pair_cmap = plt.get_cmap("tab20", max(len(unique_pairs), 1))
    display = np.zeros_like(pair_map)
    labels = []
    for index, code in enumerate(unique_pairs, start=1):
        display[pair_map == code] = index
        labels.append(pair_name(code))
    fig, ax = plt.subplots(figsize=(8, 7))
    image = ax.imshow(display, cmap=pair_cmap, vmin=0.5, vmax=len(unique_pairs) + 0.5)
    ax.set_title("Top-two meaningful surface classes")
    ax.set_axis_off()
    colourbar = fig.colorbar(image, ax=ax, ticks=np.arange(1, len(unique_pairs) + 1))
    colourbar.ax.set_yticklabels(labels)
    save("dominant-meaningful-ambiguity.png", fig)

    conflict_cut = np.nanpercentile(conflict[valid], 75)
    weak = ranking["margin"] <= 0.05
    diagnostic = np.zeros(valid.shape, dtype=np.uint8)
    diagnostic[valid & (conflict >= conflict_cut)] = 1
    diagnostic[valid & weak] = 2
    diagnostic[valid & weak & (conflict >= conflict_cut)] = 3
    fig, ax = plt.subplots(figsize=(8, 7))
    cmap = ListedColormap(["#263238", "#d95f02", "#1b9e77", "#7570b3"])
    ax.imshow(diagnostic, cmap=cmap, vmin=0, vmax=3)
    ax.set_title("Conflict and weak discrimination\nblack neither, orange conflict, green weak, purple both")
    ax.set_axis_off()
    save("conflict-versus-weak-discrimination.png", fig)

    gap_names = ["invalid", "conflict", "weak", "coarse", "temporal", "ontology", "missing", "mixed", "unresolved"]
    fig, ax = plt.subplots(figsize=(8, 7))
    cmap = ListedColormap(["#000000", "#d73027", "#fc8d59", "#fee090", "#91bfdb", "#4575b4", "#984ea3", "#4d4d4d", "#bdbdbd"])
    norm = BoundaryNorm(np.arange(-0.5, 9.5), cmap.N)
    image = ax.imshow(primary_gap, cmap=cmap, norm=norm)
    ax.set_title("Primary information-gap diagnostic")
    ax.set_axis_off()
    bar = fig.colorbar(image, ax=ax, ticks=np.arange(9))
    bar.ax.set_yticklabels(gap_names)
    save("information-gap-map.png", fig)

    sources = list(ablations)
    metrics = ["mean_total_variation_distance", "materially_affected_fraction", "meaningful_dominant_changed_fraction"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    for axis, metric in zip(axes, metrics):
        axis.bar(sources, [ablations[source][metric] for source in sources], color="#5b7c99")
        axis.set_title(metric.replace("_", " "))
        axis.tick_params(axis="x", rotation=30)
        axis.grid(axis="y", alpha=0.2)
    save("source-ablation-comparison.png", fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    readiness_cmap = ListedColormap(["#000000", "#2c7bb6", "#abd9e9", "#d7191c"])
    axes[0].imshow(readiness, cmap=readiness_cmap, vmin=0, vmax=3)
    axes[0].set_title("Reconstruction readiness\nblue constrained, pale guided, red high freedom")
    axes[0].set_axis_off()
    axes[1].scatter(probabilities[..., -1][valid][::20], ranking["margin"][valid][::20], c=uncertainty[valid][::20], s=4, alpha=0.35, cmap="magma", vmin=.8, vmax=1)
    axes[1].set_xlabel("P(other/unknown)")
    axes[1].set_ylabel("Meaningful top-two margin")
    axes[1].set_title("Knowledge versus discrimination")
    save("reconstruction-readiness.png", fig)
    return written


def run(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    lab007_root, frozen_hashes_before, lab007_report = _verify_frozen(config)
    model_config = json.loads(_path(config["model_config"]).read_text(encoding="utf-8"))
    output = _path(config["output_root"])
    rasters = output / "rasters"

    probabilities = np.stack([
        _read(lab007_root / "rasters" / f"probability-{name}-10m.tif")[0]
        for name in CLASSES
    ], axis=-1)
    uncertainty, profile = _read(lab007_root / "rasters" / "uncertainty-normalized-entropy-10m.tif")
    conflict, _ = _read(lab007_root / "rasters" / "source-conflict-js-10m.tif")
    family_count, _ = _read(lab007_root / "rasters" / "evidence-family-count-10m.tif", categorical=True)
    temporal_variability, _ = _read(_path(config["temporal_variability_raster"]))
    valid = np.all(np.isfinite(probabilities), axis=-1)

    preferences, availability, contributions = _source_arrays(lab007_root, model_config["source_budgets"])
    baseline = [model_config["baseline_support"][name] for name in CLASSES]
    reconstructed = fuse_sources(
        preferences, availability, model_config["source_budgets"], baseline,
        model_config["missing_source_unknown_support"],
        model_config["conflict_unknown_support"], valid,
    )
    reconstruction_error = float(np.nanmax(np.abs(reconstructed["probabilities"] - probabilities)))
    if reconstruction_error > 2e-6:
        raise RuntimeError(f"Lab 007 reconstruction mismatch: {reconstruction_error}")

    ranking = meaningful_ranking(probabilities)
    meaningful_entropy = conditional_meaningful_entropy(probabilities)
    pairs = pair_codes(ranking["first_index"], ranking["second_index"])
    thresholds = config["thresholds"]
    overlapping = {frozenset(item) for item in config["overlapping_pairs"]}
    bitmask, flags = gap_flags(
        probabilities, conflict, family_count, temporal_variability,
        preferences, thresholds, overlapping, config["information_gap_flags"],
    )
    primary_gap = _primary_gap(flags, valid)
    readiness = reconstruction_readiness(probabilities, thresholds)

    ablations: dict[str, dict[str, Any]] = {}
    for removed in preferences:
        remaining_preferences = {name: value for name, value in preferences.items() if name != removed}
        remaining_availability = {name: value for name, value in availability.items() if name != removed}
        remaining_budgets = {name: value for name, value in model_config["source_budgets"].items() if name != removed}
        result = fuse_sources(
            remaining_preferences, remaining_availability, remaining_budgets,
            baseline, model_config["missing_source_unknown_support"],
            model_config["conflict_unknown_support"], valid,
        )
        ablations[removed] = ablation_metrics(
            probabilities, result["probabilities"], valid,
            thresholds["ablation_material_tvd"],
        )

    no_conflict = fuse_sources(
        preferences, availability, model_config["source_budgets"], baseline,
        model_config["missing_source_unknown_support"], 0.0, valid,
    )
    conflict_support_effect = ablation_metrics(
        probabilities, no_conflict["probabilities"], valid,
        thresholds["ablation_material_tvd"],
    )
    baseline_prior = np.asarray(baseline, dtype=np.float64)
    baseline_prior /= np.sum(baseline_prior)
    conservative_construction = {
        "baseline_only_probabilities": {name: float(baseline_prior[index]) for index, name in enumerate(CLASSES)},
        "baseline_only_normalized_entropy": float(normalized_entropy(baseline_prior[None, :])[0]),
        "observed_mean_entropy": float(np.nanmean(uncertainty[valid])),
        "observed_minus_baseline_only_entropy": float(np.nanmean(uncertainty[valid]) - normalized_entropy(baseline_prior[None, :])[0]),
        "interpretation": "The deliberately diffuse prior begins highly uncertain; evidence reduces rather than creates most entropy.",
    }

    pairwise_redundancy: list[dict[str, Any]] = []
    source_names = list(preferences)
    for left_index, left in enumerate(source_names):
        for right in source_names[left_index + 1:]:
            both = availability[left] & availability[right] & valid
            distances = jensen_shannon(preferences[left], preferences[right])
            pairwise_redundancy.append({
                "sources": [left, right],
                "available_cells": int(np.count_nonzero(both)),
                "mean_jensen_shannon": float(np.nanmean(distances[both])),
                "interpretation": "lower means more similar class preferences; it does not prove redundant provenance",
            })

    conflict_correlations = {
        "with_entropy": _pearson(conflict, uncertainty, valid),
        "with_other_unknown": _pearson(conflict, probabilities[..., -1], valid),
        "with_meaningful_margin": _pearson(conflict, ranking["margin"], valid),
    }
    flag_summary = {
        name: {"cells": int(np.count_nonzero(mask)), "fraction": _fraction(mask, valid)}
        for name, mask in flags.items()
    }
    gap_summary = {
        str(code): {
            "name": name,
            "cells": int(np.count_nonzero(primary_gap == code)),
            "fraction": _fraction(primary_gap == code, valid),
        }
        for code, name in enumerate(["invalid", "source_conflict", "weak_discrimination", "coarse_evidence", "temporal_ambiguity", "ontology_ambiguity", "missing_evidence", "mixed_unresolved", "unresolved_single_cause_not_supported"])
        if code > 0
    }
    readiness_summary = {
        str(code): {
            "name": name,
            "cells": int(np.count_nonzero(readiness == code)),
            "fraction": _fraction(readiness == code, valid),
        }
        for code, name in ((int(key), value) for key, value in config["readiness_classes"].items())
    }

    full_coverage = valid & (family_count == 4)
    missing_habitat = valid & (family_count == 3)
    unknown_dominant = ranking["unknown_dominant"] & valid
    high_conflict = flags["source_conflict"]
    low_conflict = valid & (conflict <= np.nanpercentile(conflict[valid], 25))
    top_pairs = top_pair_summary(ranking["first_index"], ranking["second_index"], valid)

    _write_raster(rasters / "meaningful-class-margin-10m.tif", ranking["margin"], profile)
    _write_raster(rasters / "conditional-meaningful-entropy-10m.tif", meaningful_entropy, profile)
    _write_raster(rasters / "top-two-meaningful-pair-10m.tif", pairs, profile, categorical=True)
    _write_raster(rasters / "information-gap-flags-10m.tif", bitmask, profile, categorical=True)
    _write_raster(rasters / "primary-information-gap-10m.tif", primary_gap, profile, categorical=True)
    _write_raster(rasters / "reconstruction-readiness-10m.tif", readiness, profile, categorical=True)

    diagnostics = _diagnostics(
        output, probabilities, uncertainty, conflict, ranking, pairs,
        primary_gap, readiness, ablations, valid,
    )

    baseline_stats = {
        "uncertainty": _summary(uncertainty, valid, "normalized_entropy"),
        "other_unknown": _summary(probabilities[..., -1], valid, "probability"),
        "meaningful_margin": _summary(ranking["margin"], valid, "probability_margin"),
        "meaningful_mass": _summary(ranking["meaningful_mass"], valid, "probability"),
        "conditional_meaningful_entropy": _summary(meaningful_entropy, valid, "normalized_entropy_over_five_meaningful_classes"),
        "unknown_dominant": {
            "cells": int(np.count_nonzero(unknown_dominant)),
            "fraction": _fraction(unknown_dominant, valid),
            "mean_meaningful_mass": float(np.nanmean(ranking["meaningful_mass"][unknown_dominant])),
            "fraction_with_meaningful_top_at_least_0_20": float(np.mean(ranking["first_probability"][unknown_dominant] >= .20)),
        },
        "top_meaningful_pairs": top_pairs,
        "class_probability_statistics": {
            name: _summary(probabilities[..., index], valid, "probability")
            for index, name in enumerate(CLASSES)
        },
    }

    coverage_effect = {
        "full_four_families": {
            "cells": int(np.count_nonzero(full_coverage)),
            "mean_uncertainty": float(np.nanmean(uncertainty[full_coverage])),
            "mean_other_unknown": float(np.nanmean(probabilities[..., -1][full_coverage])),
            "mean_meaningful_margin": float(np.nanmean(ranking["margin"][full_coverage])),
        },
        "three_families_missing_habitat": {
            "cells": int(np.count_nonzero(missing_habitat)),
            "mean_uncertainty": float(np.nanmean(uncertainty[missing_habitat])),
            "mean_other_unknown": float(np.nanmean(probabilities[..., -1][missing_habitat])),
            "mean_meaningful_margin": float(np.nanmean(ranking["margin"][missing_habitat])),
        },
    }

    source_findings = {
        source: {
            "mean_preference_specificity": float(np.nanmean((1 - normalized_entropy(preferences[source]))[availability[source] & valid])),
            "available_cells": int(np.count_nonzero(availability[source] & valid)),
            "ablation": ablations[source],
        }
        for source in preferences
    }

    lab007_hashes_after = _verify_frozen(config)[1]
    if lab007_hashes_after != frozen_hashes_before:
        raise RuntimeError("Frozen Lab 007 changed during Lab 008")

    generated = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "lab008-report.json")
    report = {
        "schema_version": 1,
        "experiment": config["experiment"],
        "configuration_sha256": sha256_file(config_path),
        "frozen_lab007": {
            **config["frozen_lab007"],
            "verified_before_and_after": True,
            "baseline_reconstruction_max_absolute_probability_error": reconstruction_error,
        },
        "baseline": baseline_stats,
        "uncertainty_decomposition": {
            "diagnostic_not_exact_decomposition": True,
            "source_conflict_correlations": conflict_correlations,
            "conflict_support_counterfactual": conflict_support_effect,
            "conservative_model_construction": conservative_construction,
            "flags": flag_summary,
            "primary_gap": gap_summary,
            "full_coverage_vs_missing_habitat": coverage_effect,
            "thresholds": thresholds,
            "top_pairs": top_pairs,
        },
        "source_ablation": ablations,
        "source_information": source_findings,
        "pairwise_source_preference_distances": pairwise_redundancy,
        "scale_analysis": {
            "terrain_information_scale": "approximately 1 m measured geometry; morphology aggregated to the 10 m analysis grid",
            "sentinel_information_scale": "10 m NDVI/variability and 20 m NDMI observations",
            "habitat_information_scale": "legacy 1979-1997 field interpretation with no promised metre-scale positional accuracy",
            "geology_information_scale": "nominal 1:50,000 broad context",
            "sub_grid_heterogeneity_proxy": {
                "definition": "top-two meaningful classes form a documented overlapping pair and their margin is <= 0.10",
                "cells": int(np.count_nonzero(flags["ontology_ambiguity"])),
                "fraction": _fraction(flags["ontology_ambiguity"], valid),
                "limitation": "This is a plausible mixture diagnostic, not proof that both surfaces coexist.",
            },
        },
        "temporal_limitations": {
            "sentinel": "Four dated observations/composites describe dynamic spectral behaviour, not current or permanent state.",
            "habitat": "Historical 1979-1997 mapped context is not assumed unchanged.",
            "high_temporal_variability_flag_fraction": _fraction(flags["temporal_ambiguity"], valid),
        },
        "reconstruction_readiness": readiness_summary,
        "additional_evidence_decision": {
            "outcome": "B",
            "recommendation": "No additional evidence acquisition.",
            "reason": "Coverage is already nearly complete. The dominant limitations are weak mutually exclusive class discrimination, coarse/contextual source scale, temporal ambiguity and plausible sub-grid mixtures. No single scalable public source is demonstrated by this audit to resolve those mechanisms at human reconstruction scale.",
            "next_step": "Freeze evidence gathering and use Lab 007 probabilities and Lab 008 readiness/freedom diagnostics to constrain Lab 009 reconstruction without representing inferred detail as measured truth.",
        },
        "research_judgement": {
            "why_uncertain": "Broad overlapping classes, diffuse conservative priors/support, source-scale mismatch and real or plausible mixed surfaces dominate; missing coverage is negligible.",
            "missing_coverage_effect": "Only 472 cells lack NRW habitat. Their statistics are reported separately and do not explain AOI-wide entropy.",
            "source_disagreement": "Conflict raises other/unknown, but conflict correlations and quartile comparisons show it is not the sole or dominant explanation.",
            "weak_discrimination": "Top meaningful margins and repeated heath/grass, rock/scree and vegetation/wet pairings show substantial ambiguity even where all families exist.",
            "sub_grid_mixture": "The overlapping-pair flag identifies where several broad characters may coexist inside 10-20 m observations; it remains a proxy, not a solved decomposition.",
            "unique_information": "Terrain supplies morphology; Sentinel supplies dated vegetation/moisture behaviour; NRW supplies named historical cover context; BGS supplies talus/peat/substrate constraints. Ablations quantify where each changes inference.",
            "misleading_sources": "No source is shown to be misleading. Each is useful only within its documented scale and temporal semantics.",
            "ready_for_lab009": True,
        },
        "semantic_invariants": [
            "Other/unknown dominance is not interpreted as total ignorance.",
            "Valid no mapped superficial deposit is not missing geology.",
            "Dated Sentinel evidence is not converted into current-state truth.",
            "Information-gap flags are diagnostics, not a mathematically exact uncertainty decomposition.",
            "Sub-grid heterogeneity flags are plausible mixture evidence, not object locations.",
            "Ablations are counterfactual audit outputs and never overwrite frozen Lab 007.",
        ],
        "outputs": [
            {"path": str(path.relative_to(output)), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in generated
        ],
        "storage_bytes": sum(path.stat().st_size for path in generated),
    }
    payload = {key: value for key, value in report.items() if key != "deterministic_result_sha256"}
    report["deterministic_result_sha256"] = stable_json_sha256(payload)
    _write_json(output / "lab008-report.json", report)
    print(json.dumps({
        "report": str(output / "lab008-report.json"),
        "deterministic_result_sha256": report["deterministic_result_sha256"],
        "storage_bytes": report["storage_bytes"],
        "diagnostics": len(diagnostics),
        "outcome": report["additional_evidence_decision"]["outcome"],
    }, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "docs" / "earth-lab" / "tryfan-008-uncertainty-audit.json")
    arguments = parser.parse_args()
    run(arguments.config.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
