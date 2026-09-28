"""Attach Unreal integration and visual-acceptance status to the Lab 009 report.

The reconstruction identity remains the deterministic hash emitted by
analyze_surface_reconstruction.py. This finalizer records editor-side validation
and the deliberately separate, human visual-acceptance state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finalize(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    repo = config_path.parents[2]
    output_root = (repo / config["output_root"]).resolve()
    report_path = output_root / "lab009-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    project_root = (repo / config["unreal"]["project"]).resolve().parent
    saved = project_root / "Saved"
    setup_path = saved / "meridian-lab009-setup.json"
    validation_path = saved / "meridian-lab009-validation.json"
    setup = json.loads(setup_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("result") != "PASS":
        raise RuntimeError("Saved Lab 009 Unreal validation is not PASS")
    if not setup.get("enabled") or not setup.get("reversible"):
        raise RuntimeError("Saved Lab 009 setup is not enabled and reversible")

    capture_root = output_root / "unreal" / "captures"
    capture_paths = [
        capture_root / "lab009-baseline.png",
        capture_root / "lab009-reconstruction.png",
        capture_root / "lab009-reconstruction-overlay-50.png",
    ]
    capture_inventory = [
        {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in capture_paths
        if path.is_file()
    ]

    report["unreal"].update({
        "setup_status": "PASS",
        "validation_status": "PASS",
        "saved_map": validation["map"],
        "saved_landscape_material": validation["landscape"]["material"],
        "baseline_material": setup["baseline_material"],
        "lab009_material": setup["lab009_material"],
        "reversible": True,
        "canonical_camera_unchanged": True,
        "landscape_transform_unchanged": True,
        "benchmark_status": "MANUAL_FIXED_CAMERA_CAPTURE_REQUIRED",
    })
    report["visual_acceptance"] = {
        "offline_diagnostics_inspected": True,
        "offline_findings": [
            "All five continuous controls are spatially coherent and retain terrain-linked structure.",
            "No obvious checkerboard, salt-and-pepper pattern, or visible 10 m evidence grid was found in the renderer controls or material-control preview.",
            "The categorical Lab 008 readiness map remains coarse by design but is used only to bound procedural amplitude, not as a rendered material.",
            "The restrained material-control preview is spatially varying but is not evidence of a successful perspective render.",
        ],
        "automated_capture_valid_for_acceptance": False,
        "automated_capture_failure": (
            "UE 5.8 SceneCapture renders the camera-bound ImagePlate proxy in front of the "
            "terrain even when the ImagePlate actor/component is hidden, moved, or removed "
            "in the unsaved capture world. The resulting frames are obstructed and must not "
            "be used to judge the Landscape material."
        ),
        "material_sampler_defect_fixed": (
            "Texture samples now use SAMPLERTYPE_MASKS; the generated Material was rebuilt "
            "cleanly and the saved graph validates with exactly two mask samples."
        ),
        "invalid_capture_inventory": capture_inventory,
        "pending_manual_frames": [
            "fixed-camera baseline",
            "fixed-camera Lab 009 reconstruction",
            "fixed-camera Lab 009 reconstruction plus 50% reference overlay",
        ],
        "questions_pending_manual_inspection": [
            "visible improvement over baseline",
            "perspective-view grid or tiling artefacts",
            "material transition plausibility from the benchmark camera",
            "photographic-overlay usefulness",
        ],
    }
    report["research_judgement"] = {
        "evidence_model_drives_coherent_reconstruction_fields": True,
        "reconstruction_connected_to_saved_unreal_landscape": True,
        "visible_difference_from_baseline": "PENDING_MANUAL_FIXED_CAMERA_CAPTURE",
        "visibly_better_or_more_plausible": "PENDING_MANUAL_FIXED_CAMERA_CAPTURE",
        "coarse_grid_artefacts": "NONE_OBVIOUS_IN_OFFLINE_DIAGNOSTICS; PERSPECTIVE_VIEW_PENDING",
        "evidence_constrained": [
            "broad five-family mixture tendencies from frozen Lab 007",
            "reconstruction-amplitude regime from frozen Lab 008",
            "bounded placement response to measured slope, 15 m roughness, and terrain form",
        ],
        "reconstructed": [
            "correlated sub-cell placement at approximately 8 m, 29 m, and 97 m",
            "specific local blend pattern",
            "v0.1 colour palette and uniform roughness",
        ],
        "high_freedom_limit": "16.70% of Lab 008 cells permit the largest bounded procedural amplitude.",
        "current_visual_fidelity_limit": (
            "The v0.1 material has only broad colours and uniform roughness, with no measured "
            "albedo, material microstructure, vegetation geometry, rock normals, or object detail."
        ),
        "architecture_progressive": True,
        "next_visual_experiment": (
            "After the required manual benchmark frames are inspected, improve the restrained "
            "material vocabulary and scale-aware detail response without changing evidence, "
            "terrain, or camera calibration."
        ),
        "completion_status": "IMPLEMENTATION_AND_NUMERICAL_VALIDATION_COMPLETE; VISUAL_ACCEPTANCE_PENDING_MANUAL_FRAMES",
    }
    report["integration_reports"] = {
        "setup": {"path": str(setup_path), "sha256": sha256_file(setup_path)},
        "validation": {"path": str(validation_path), "sha256": sha256_file(validation_path)},
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    report = finalize(args.config)
    print(json.dumps({
        "report": str((args.config.resolve().parents[2] / json.loads(args.config.read_text(encoding="utf-8"))["output_root"] / "lab009-report.json").resolve()),
        "deterministic_result_sha256": report["deterministic_result_sha256"],
        "completion_status": report["research_judgement"]["completion_status"],
    }, indent=2))


if __name__ == "__main__":
    main()
