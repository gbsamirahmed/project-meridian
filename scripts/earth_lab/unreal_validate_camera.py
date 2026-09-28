from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unreal

from photo_overlay import camera_mismatches


CAMERA_LABEL = "Meridian_Lab004_Geometric_Camera"
CONFIG_POINTER_NAME = "meridian-photo-overlay-source.json"
MAP_ASSET = "/Game/Tryfan_Lab004"
EXPECTED_MAP = "/Game/Tryfan_Lab004.Tryfan_Lab004"
REPORT_NAME = "meridian-saved-camera-validation.json"


def _expected() -> tuple[Path, dict[str, Any]]:
    pointer_path = Path(unreal.Paths.project_dir()) / CONFIG_POINTER_NAME
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    config_path = Path(pointer["config"]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return config_path, config["camera"]


def _observe(camera: unreal.CameraActor) -> dict[str, Any]:
    location = camera.get_actor_location()
    rotation = camera.get_actor_rotation()
    component = camera.camera_component
    return {
        "location_cm": {
            "x": float(location.x),
            "y": float(location.y),
            "z": float(location.z),
        },
        "rotation_degrees": {
            "pitch": float(rotation.pitch),
            "yaw": float(rotation.yaw),
            "roll": float(rotation.roll),
        },
        "horizontal_fov_degrees": float(component.field_of_view),
        "aspect_ratio": float(component.aspect_ratio),
        "constrain_aspect_ratio": bool(component.constrain_aspect_ratio),
    }


def validate_saved_camera(*, load_map: bool = False) -> dict[str, Any]:
    if load_map:
        unreal.EditorLoadingAndSavingUtils.load_map(MAP_ASSET)
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    current_map = world.get_path_name()
    if current_map != EXPECTED_MAP:
        raise RuntimeError(
            f"Expected saved map {EXPECTED_MAP}; current map is {current_map}"
        )

    config_path, expected = _expected()
    actors = list(
        unreal.get_editor_subsystem(
            unreal.EditorActorSubsystem
        ).get_all_level_actors()
    )
    cameras = [
        actor
        for actor in actors
        if isinstance(actor, unreal.CameraActor)
        and actor.get_actor_label() == CAMERA_LABEL
    ]
    if len(cameras) != 1:
        raise RuntimeError(
            f"Expected exactly one {CAMERA_LABEL!r}; found {len(cameras)}"
        )
    observed = _observe(cameras[0])
    mismatches = camera_mismatches(observed, expected)
    report = {
        "schema_version": 1,
        "map": current_map,
        "config": str(config_path),
        "camera_label": CAMERA_LABEL,
        "observed": observed,
        "canonical": expected,
        "mismatches": mismatches,
        "result": "PASS" if not mismatches else "FAIL",
        "validation_scope": (
            "Camera state loaded from the saved .umap in this editor process"
        ),
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if mismatches:
        raise RuntimeError(
            "Saved Lab 004A camera validation failed: " + "; ".join(mismatches)
        )
    unreal.log(
        "PASS: saved Tryfan_Lab004 camera matches canonical Lab 004A "
        "position, rotation, HFOV and constrained 4:3 aspect."
    )
    unreal.log(f"Saved-camera validation report: {report_path}")
    return report


if __name__ == "__main__":
    RESULT = validate_saved_camera(
        load_map=bool(globals().get("MERIDIAN_CAMERA_VALIDATION_LOAD_MAP", False))
    )
