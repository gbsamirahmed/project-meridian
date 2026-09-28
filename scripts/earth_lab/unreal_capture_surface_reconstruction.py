"""Capture fixed-camera baseline, Lab 009, and 50% reference-overlay views."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unreal

from photo_overlay import camera_mismatches

CAMERA_LABEL = "Meridian_Lab004_Geometric_Camera"
PLATE_LABEL = "Meridian_Lab004_Photographic_Reference"
EXPECTED_MAP = "/Game/Tryfan_Lab004.Tryfan_Lab004"
REPORT_NAME = "meridian-lab009-captures.json"


def _actors():
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())


def _one(label, actor_type):
    matches = [actor for actor in _actors() if isinstance(actor, actor_type) and actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label!r}; found {len(matches)}")
    return matches[0]


def _material(path):
    if path in (None, "", "None"):
        return None
    result = unreal.EditorAssetLibrary.load_asset(path)
    if result is None:
        raise RuntimeError(f"Material not found: {path}")
    return result


def _plate_visibility(actor, visible: bool):
    if actor is not None:
        actor.image_plate.set_visibility(bool(visible), True)
        actor.set_actor_hidden_in_game(not bool(visible))
        actor.set_is_temporarily_hidden_in_editor(not bool(visible))


def _capture(world, camera, output_dir: Path, name: str, *, hidden_actors=None):
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    optical_component = camera.camera_component
    optical_location = optical_component.get_world_location()
    optical_rotation = optical_component.get_world_rotation()
    capture = actor_subsystem.spawn_actor_from_class(unreal.SceneCapture2D, optical_location, optical_rotation)
    if capture is None:
        raise RuntimeError("Could not spawn transient SceneCapture2D")
    if not capture.set_actor_location(optical_location, False, True):
        raise RuntimeError("Could not place transient capture at the camera optical position")
    if not capture.set_actor_rotation(optical_rotation, False):
        raise RuntimeError("Could not orient transient capture to the camera optical rotation")
    capture.set_actor_label("Meridian_Lab009_Transient_Capture", True)
    target = unreal.RenderingLibrary.create_render_target2d(
        world, 1280, 960,
        format=unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB,
        clear_color=unreal.LinearColor(0.0, 0.0, 0.0, 1.0),
        auto_generate_mip_maps=False,
    )
    component = capture.capture_component2d
    component.set_editor_properties({
        "texture_target": target,
        "fov_angle": float(camera.camera_component.field_of_view),
        "capture_source": unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
        "capture_every_frame": False,
        "capture_on_movement": False,
    })
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    component.capture_scene()
    output_dir.mkdir(parents=True, exist_ok=True)
    unreal.RenderingLibrary.export_render_target(world, target, str(output_dir), name + ".png")
    capture.destroy_actor()
    candidates = [output_dir / f"{name}.png", output_dir / name, output_dir / f"{name}.hdr"]
    existing = next((path for path in candidates if path.is_file()), None)
    if existing is None:
        raise RuntimeError(f"Render target export did not create {name} in {output_dir}")
    return existing


def capture_benchmark() -> dict[str, Any]:
    project_root = Path(unreal.Paths.project_dir())
    pointer = json.loads((project_root / "meridian-lab009-source.json").read_text(encoding="utf-8"))
    config = json.loads(Path(pointer["config"]).read_text(encoding="utf-8"))
    output_root = Path(pointer["output_root"])
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name() != EXPECTED_MAP:
        raise RuntimeError(f"Expected {EXPECTED_MAP}; current map is {world.get_path_name()}")
    camera = _one(CAMERA_LABEL, unreal.CameraActor)
    camera_pointer = json.loads((project_root / "meridian-photo-overlay-source.json").read_text(encoding="utf-8"))
    expected_camera = json.loads(Path(camera_pointer["config"]).read_text(encoding="utf-8"))["camera"]
    location = camera.get_actor_location(); rotation = camera.get_actor_rotation(); component = camera.camera_component
    observed = {
        "location_cm": {"x": float(location.x), "y": float(location.y), "z": float(location.z)},
        "rotation_degrees": {"pitch": float(rotation.pitch), "yaw": float(rotation.yaw), "roll": float(rotation.roll)},
        "horizontal_fov_degrees": float(component.field_of_view),
        "aspect_ratio": float(component.aspect_ratio),
        "constrain_aspect_ratio": bool(component.constrain_aspect_ratio),
    }
    mismatches = camera_mismatches(observed, expected_camera)
    if mismatches:
        raise RuntimeError("Lab 004A camera is not canonical: " + "; ".join(mismatches))
    if not component.constrain_aspect_ratio or abs(float(component.aspect_ratio) - 4.0 / 3.0) > 1e-5:
        raise RuntimeError("Fixed camera is not constrained to 4:3")
    landscape = _one("Landscape", unreal.Landscape) if any(actor.get_actor_label() == "Landscape" for actor in _actors()) else [actor for actor in _actors() if isinstance(actor, unreal.Landscape)][0]
    baseline = json.loads((Path(unreal.Paths.project_saved_dir()) / "meridian-lab009-baseline.json").read_text(encoding="utf-8"))
    lab_material = _material(config["unreal"]["material_asset"])
    plate_matches = [actor for actor in _actors() if isinstance(actor, unreal.ImagePlate) and actor.get_actor_label() == PLATE_LABEL]
    plate = plate_matches[0] if len(plate_matches) == 1 else None
    original_plate_visible = bool(plate.image_plate.is_visible()) if plate is not None else False
    original_plate_location = plate.get_actor_location() if plate is not None else None
    original_plate_rotation = plate.get_actor_rotation() if plate is not None else None
    original_plate_scale = plate.get_actor_scale3d() if plate is not None else None
    output_dir = output_root / "unreal" / "captures"
    plate_moved_only_for_capture = False
    try:
        overlay_path = None
        if plate is not None:
            landscape.set_editor_property("landscape_material", lab_material)
            _plate_visibility(plate, True)
            overlay_path = _capture(world, camera, output_dir, "lab009-reconstruction-overlay-50")
            if not plate.set_actor_location(unreal.Vector(0.0, 0.0, -100000000.0), False, True):
                raise RuntimeError("Could not move ImagePlate out of the unsaved capture world")
            plate.set_actor_scale3d(unreal.Vector(0.001, 0.001, 0.001))
            plate_moved_only_for_capture = True
            unreal.AutomationLibrary.finish_loading_before_screenshot()
        landscape.set_editor_property("landscape_material", _material(baseline["baseline_material"]))
        baseline_path = _capture(world, camera, output_dir, "lab009-baseline")
        landscape.set_editor_property("landscape_material", lab_material)
        reconstruction_path = _capture(world, camera, output_dir, "lab009-reconstruction")
    finally:
        landscape.set_editor_property("landscape_material", lab_material)
        if plate is not None:
            plate.set_actor_location(original_plate_location, False, True)
            plate.set_actor_rotation(original_plate_rotation, False)
            plate.set_actor_scale3d(original_plate_scale)
            _plate_visibility(plate, original_plate_visible)
    report = {
        "schema_version": 1, "map": world.get_path_name(), "camera": observed,
        "camera_verified": True, "landscape_transform_modified": False,
        "captures": {
            "baseline": str(baseline_path),
            "reconstruction": str(reconstruction_path),
            "overlay_50_percent": str(overlay_path) if overlay_path is not None else None,
        },
        "overlay_actor_available": plate is not None,
        "plate_moved_only_in_unsaved_capture_world": plate_moved_only_for_capture,
        "capture_resolution": [1280, 960],
        "valid_for_visual_acceptance": False,
        "invalid_reason": "UE 5.8 SceneCapture retains the camera-bound ImagePlate render proxy; use the documented real-editor CameraActor workflow.",
        "final_landscape_material": lab_material.get_path_name(),
        "note": "The transient SceneCapture copied the immutable Lab 004A optical transform/HFOV into a 4:3 render target. The ImagePlate was moved outside only the unsaved capture world after the overlay frame; the benchmark camera and persisted map were unchanged.",
    }
    report_path = output_dir / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log_warning(f"Meridian Lab 009 automated captures are diagnostic-only and invalid for visual acceptance: {report_path}")
    return report


if __name__ == "__main__":
    RESULT = capture_benchmark()
