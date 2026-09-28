from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unreal

from photo_overlay import camera_mismatches


CAMERA_LABEL = "Meridian_Lab004_Geometric_Camera"
CONFIG_POINTER_NAME = "meridian-photo-overlay-source.json"
EXPECTED_MAP = "/Game/Tryfan_Lab004.Tryfan_Lab004"
REPORT_NAME = "meridian-camera-restoration.json"


def _load_expected_camera() -> tuple[Path, dict[str, Any]]:
    pointer_path = Path(unreal.Paths.project_dir()) / CONFIG_POINTER_NAME
    if not pointer_path.is_file():
        raise RuntimeError(f"Missing canonical overlay pointer: {pointer_path}")
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    config_path = Path(pointer["config"]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return config_path, config["camera"]


def _current_map() -> str:
    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    return world.get_path_name()


def _one_camera() -> unreal.CameraActor:
    actors = list(
        unreal.get_editor_subsystem(
            unreal.EditorActorSubsystem
        ).get_all_level_actors()
    )
    matches = [
        actor
        for actor in actors
        if isinstance(actor, unreal.CameraActor)
        and actor.get_actor_label() == CAMERA_LABEL
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {CAMERA_LABEL!r}; found {len(matches)}"
        )
    return matches[0]


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


def _landscape_snapshot() -> list[dict[str, Any]]:
    actors = list(
        unreal.get_editor_subsystem(
            unreal.EditorActorSubsystem
        ).get_all_level_actors()
    )
    landscape_class = getattr(unreal, "Landscape", None)
    proxy_class = getattr(unreal, "LandscapeStreamingProxy", None)
    result: list[dict[str, Any]] = []
    for actor in actors:
        if (
            landscape_class is not None
            and isinstance(actor, landscape_class)
        ) or (
            proxy_class is not None
            and isinstance(actor, proxy_class)
        ):
            location = actor.get_actor_location()
            rotation = actor.get_actor_rotation()
            scale = actor.get_actor_scale3d()
            result.append(
                {
                    "path": actor.get_path_name(),
                    "location": [location.x, location.y, location.z],
                    "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
                    "scale": [scale.x, scale.y, scale.z],
                }
            )
    return sorted(result, key=lambda item: item["path"])


def restore_and_save() -> dict[str, Any]:
    current_map = _current_map()
    if current_map != EXPECTED_MAP:
        raise RuntimeError(
            f"Open {EXPECTED_MAP} before restoring the camera; current map is "
            f"{current_map}"
        )
    config_path, expected = _load_expected_camera()
    camera = _one_camera()
    before = _observe(camera)
    landscape_before = _landscape_snapshot()

    camera.modify()
    camera.camera_component.modify()
    location = expected["location_cm"]
    rotation = expected["rotation_degrees"]
    camera.set_actor_location_and_rotation(
        unreal.Vector(
            float(location["x"]),
            float(location["y"]),
            float(location["z"]),
        ),
        unreal.Rotator(
            pitch=float(rotation["pitch"]),
            yaw=float(rotation["yaw"]),
            roll=float(rotation["roll"]),
        ),
        False,
        False,
    )
    component = camera.camera_component
    component.set_field_of_view(float(expected["horizontal_fov_degrees"]))
    component.set_aspect_ratio(float(expected["aspect_ratio"]))
    component.set_constraint_aspect_ratio(
        bool(expected["constrain_aspect_ratio"])
    )

    after = _observe(camera)
    mismatches = camera_mismatches(after, expected)
    if mismatches:
        raise RuntimeError(
            "Canonical camera restoration did not converge: "
            + "; ".join(mismatches)
        )
    landscape_after = _landscape_snapshot()
    if landscape_after != landscape_before:
        raise RuntimeError(
            "Landscape state changed during camera restoration; refusing to save"
        )

    world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem
    ).get_editor_world()
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/Tryfan_Lab004"):
        raise RuntimeError("Unreal failed to save the corrected Tryfan_Lab004 level")

    persisted = _observe(camera)
    persisted_mismatches = camera_mismatches(persisted, expected)
    if persisted_mismatches:
        raise RuntimeError(
            "Camera changed while saving: " + "; ".join(persisted_mismatches)
        )

    report = {
        "schema_version": 1,
        "map": current_map,
        "config": str(config_path),
        "camera_label": CAMERA_LABEL,
        "before": before,
        "canonical": expected,
        "after_save": persisted,
        "strict_mismatches_after_save": persisted_mismatches,
        "landscape_unchanged": landscape_after == landscape_before,
        "level_saved": True,
        "fresh_process_validation_required": True,
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        "Meridian Lab 004A camera restored from canonical configuration and "
        "Tryfan_Lab004 saved successfully."
    )
    unreal.log(f"Camera restoration report: {report_path}")
    return report


if __name__ == "__main__":
    RESULT = restore_and_save()
