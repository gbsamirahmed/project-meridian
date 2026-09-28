"""Read-only Unreal validation for Meridian Earth Lab 009."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unreal

from photo_overlay import camera_mismatches

CAMERA_LABEL = "Meridian_Lab004_Geometric_Camera"
EXPECTED_MAP = "/Game/Tryfan_Lab004.Tryfan_Lab004"
REPORT_NAME = "meridian-lab009-validation.json"
TRANSFORM_TOLERANCE = 1e-4


def _actors() -> list[unreal.Actor]:
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())


def _one(actor_type: type, label: str | None = None):
    matches = [actor for actor in _actors() if isinstance(actor, actor_type)]
    if label is not None:
        matches = [actor for actor in matches if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {actor_type.__name__} {label or ''}; found {len(matches)}")
    return matches[0]


def _vector(value) -> list[float]:
    return [float(value.x), float(value.y), float(value.z)]


def _observe_camera(camera: unreal.CameraActor) -> dict[str, Any]:
    location = camera.get_actor_location()
    rotation = camera.get_actor_rotation()
    component = camera.camera_component
    return {
        "location_cm": {"x": float(location.x), "y": float(location.y), "z": float(location.z)},
        "rotation_degrees": {"pitch": float(rotation.pitch), "yaw": float(rotation.yaw), "roll": float(rotation.roll)},
        "horizontal_fov_degrees": float(component.field_of_view),
        "aspect_ratio": float(component.aspect_ratio),
        "constrain_aspect_ratio": bool(component.constrain_aspect_ratio),
    }


def _transform(actor: unreal.Actor) -> dict[str, list[float]]:
    rotation = actor.get_actor_rotation()
    return {
        "location_cm": _vector(actor.get_actor_location()),
        "rotation_degrees": [float(rotation.pitch), float(rotation.yaw), float(rotation.roll)],
        "scale": _vector(actor.get_actor_scale3d()),
    }


def _close_vector(observed: list[float], expected: list[float], tolerance: float = TRANSFORM_TOLERANCE) -> bool:
    return len(observed) == len(expected) and all(abs(a - b) <= tolerance for a, b in zip(observed, expected))


def validate() -> dict[str, Any]:
    project_root = Path(unreal.Paths.project_dir())
    pointer = json.loads((project_root / "meridian-lab009-source.json").read_text(encoding="utf-8"))
    config_path = Path(pointer["config"]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = Path(pointer["output_root"]).resolve()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, observed: Any, expected: Any) -> None:
        status = "PASS" if passed else "FAIL"
        checks.append({"status": status, "name": name, "observed": observed, "expected": expected})
        unreal.log(f"[{status}] {name}: observed={observed!r}; expected={expected!r}")

    check("map", world.get_path_name() == EXPECTED_MAP, world.get_path_name(), EXPECTED_MAP)

    camera = _one(unreal.CameraActor, CAMERA_LABEL)
    camera_pointer = json.loads((project_root / "meridian-photo-overlay-source.json").read_text(encoding="utf-8"))
    expected_camera = json.loads(Path(camera_pointer["config"]).read_text(encoding="utf-8"))["camera"]
    observed_camera = _observe_camera(camera)
    camera_errors = camera_mismatches(observed_camera, expected_camera)
    check("canonical_lab004a_camera", not camera_errors, camera_errors or observed_camera, expected_camera)

    landscape = _one(unreal.Landscape)
    observed_transform = _transform(landscape)
    expected_transform = {
        "location_cm": [float(value) for value in config["unreal"]["landscape_location_cm"]],
        "rotation_degrees": [0.0, 0.0, 0.0],
        "scale": [99.206349206, 99.206349206, 150.0],
    }
    transform_ok = all(
        _close_vector(observed_transform[key], expected_transform[key], 0.001)
        for key in expected_transform
    )
    check("landscape_transform", transform_ok, observed_transform, expected_transform)

    material = landscape.get_editor_property("landscape_material")
    material_path = material.get_path_name() if material is not None else None
    expected_material = config["unreal"]["material_asset"] + "." + config["unreal"]["material_asset"].rsplit("/", 1)[1]
    check("landscape_material", material_path == expected_material, material_path, expected_material)

    expected_texture_paths = [
        config["unreal"]["surface_texture_asset"],
        config["unreal"]["context_texture_asset"],
    ]
    texture_records = []
    loaded_textures = []
    for asset_path in expected_texture_paths:
        texture = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not isinstance(texture, unreal.Texture2D):
            texture_records.append({"asset": asset_path, "loaded": False})
            continue
        loaded_textures.append(texture)
        record = {
            "asset": texture.get_path_name(),
            "loaded": True,
            "size": [int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())],
            "srgb": bool(texture.get_editor_property("srgb")),
            "compression": str(texture.get_editor_property("compression_settings")),
        }
        texture_records.append(record)
    textures_ok = (
        len(loaded_textures) == 2
        and all(item["size"] == [3025, 3025] for item in texture_records)
        and all(not item["srgb"] for item in texture_records)
        and all("MASKS" in item["compression"].upper() for item in texture_records)
    )
    check("control_textures", textures_ok, texture_records, "two 3025x3025 non-sRGB TC_MASKS textures")

    sampler_records = []
    if material is not None:
        for obj in unreal.MaterialEditingLibrary.get_material_expressions(material):
            if isinstance(obj, unreal.MaterialExpressionTextureSampleParameter2D):
                texture = obj.get_editor_property("texture")
                sampler_records.append({
                    "parameter": str(obj.get_editor_property("parameter_name")),
                    "sampler": str(obj.get_editor_property("sampler_type")),
                    "texture": texture.get_path_name() if texture is not None else None,
                })
    observed_texture_paths = {item["texture"] for item in sampler_records}
    expected_texture_object_paths = {texture.get_path_name() for texture in loaded_textures}
    sampler_ok = (
        len(sampler_records) == 2
        and all("MASKS" in item["sampler"].upper() for item in sampler_records)
        and observed_texture_paths == expected_texture_object_paths
    )
    check(
        "material_texture_samples",
        sampler_ok,
        sampler_records,
        "two SAMPLERTYPE_MASKS samples referencing the two control textures",
    )

    baseline_path = Path(unreal.Paths.project_saved_dir()) / "meridian-lab009-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.is_file() else None
    baseline_ok = bool(
        baseline
        and baseline.get("map") == EXPECTED_MAP
        and baseline.get("landscape_transform") == observed_transform
    )
    check("reversible_baseline_record", baseline_ok, baseline, "saved pre-009 material and unchanged Landscape transform")

    package_path = output_root / "lab009-reconstruction-package.json"
    package = json.loads(package_path.read_text(encoding="utf-8")) if package_path.is_file() else None
    check(
        "external_reconstruction_package",
        bool(package and package["grid"]["shape"] == [3025, 3025]),
        package_path.is_file(),
        "existing 3025x3025 Lab 009 package",
    )

    result = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    report = {
        "schema_version": 1,
        "result": result,
        "engine_version": unreal.SystemLibrary.get_engine_version(),
        "map": world.get_path_name(),
        "config": str(config_path),
        "checks": checks,
        "camera": observed_camera,
        "landscape": {"path": landscape.get_path_name(), "transform": observed_transform, "material": material_path},
        "read_only": True,
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"OVERALL {result}: Meridian Earth Lab 009; report: {report_path}")
    if result != "PASS":
        raise RuntimeError("Lab 009 Unreal validation failed")
    return report


if __name__ == "__main__":
    RESULT = validate()
