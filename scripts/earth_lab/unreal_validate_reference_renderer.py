"""Read-only map validation and generated-dependency smoke test for the renderer."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

import setup_lab009_surface
import setup_photo_overlay
import validate_lab004a_camera
import validate_lab009_surface
import validate_landscape


EXPECTED_MAP = "/Game/Tryfan_Lab004.Tryfan_Lab004"
REPORT_NAME = "meridian-reference-renderer-validation.json"


def validate_reference_renderer() -> dict[str, object]:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name() != EXPECTED_MAP:
        raise RuntimeError(
            f"Open {EXPECTED_MAP} before validation; current map is {world.get_path_name()}"
        )

    # Recreate ignored dependencies without saving or changing the calibrated map.
    setup_lab009_surface.apply_lab009(enabled=True, save_map=False)
    setup_photo_overlay.apply_overlay(enabled=False, opacity=0.5)

    landscape = validate_landscape.main()
    camera = validate_lab004a_camera.validate_saved_camera(load_map=False)
    surface = validate_lab009_surface.validate()
    passed = (
        landscape.get("overall") == "PASS"
        and camera.get("result") == "PASS"
        and surface.get("result") == "PASS"
    )
    report = {
        "schema_version": 1,
        "result": "PASS" if passed else "FAIL",
        "engine_version": unreal.SystemLibrary.get_engine_version(),
        "map": world.get_path_name(),
        "map_saved_by_validation": False,
        "generated_dependencies_recreated": True,
        "landscape": landscape.get("overall"),
        "camera": camera.get("result"),
        "surface_reconstruction": surface.get("result"),
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not passed:
        raise RuntimeError(f"Tryfan Reference Renderer validation failed: {report}")
    unreal.log(f"PASS: Tryfan Reference Renderer; report: {report_path}")
    return report


if __name__ == "__main__":
    RESULT = validate_reference_renderer()
