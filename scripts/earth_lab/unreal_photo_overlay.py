from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import unreal

from photo_overlay import (
    aspect_ratio,
    camera_mismatches,
    resolve_repo_path,
    validate_opacity,
)


CAMERA_LABEL = "Meridian_Lab004_Geometric_Camera"
OVERLAY_LABEL = "Meridian_Lab004_Photographic_Reference"
TEXTURE_ASSET = "/Game/MeridianLab004/Reference/T_TonyEdwards_2009"
MATERIAL_ASSET = "/Game/MeridianLab004/Reference/M_TonyEdwards_Overlay"
ASSET_DIRECTORY = "/Game/MeridianLab004/Reference"
DEFAULT_OPACITY = 0.5
PLATE_DISTANCE_CM = 100.0
CONFIG_POINTER_NAME = "meridian-photo-overlay-source.json"
REPORT_NAME = "meridian-photo-overlay.json"


def _load_config() -> tuple[Path, dict[str, Any]]:
    pointer_path = Path(unreal.Paths.project_dir()) / CONFIG_POINTER_NAME
    if not pointer_path.is_file():
        raise RuntimeError(
            f"Missing {pointer_path}. Re-run the Earth Lab project preparation "
            "with --photo-overlay."
        )
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    config_path = Path(pointer["config"]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return config_path, config


def _one_actor_with_label(
    actors: list[unreal.Actor],
    label: str,
    actor_class: type,
) -> unreal.Actor | None:
    matches = [
        actor
        for actor in actors
        if isinstance(actor, actor_class) and actor.get_actor_label() == label
    ]
    if len(matches) > 1:
        raise RuntimeError(f"Expected at most one {label!r}; found {len(matches)}")
    return matches[0] if matches else None


def _camera_observation(camera: unreal.CameraActor) -> dict[str, Any]:
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


def _verify_camera(
    camera: unreal.CameraActor,
    expected: dict[str, Any],
) -> dict[str, Any]:
    observed = _camera_observation(camera)
    mismatches = camera_mismatches(observed, expected)
    if mismatches:
        raise RuntimeError(
            "The photographic overlay was not attached because the calibrated "
            f"{CAMERA_LABEL} no longer matches Lab 004A: " + "; ".join(mismatches)
        )
    return observed


def _import_texture(image_path: Path) -> unreal.Texture2D:
    if not image_path.is_file():
        raise FileNotFoundError(f"Photographic reference not found: {image_path}")
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE_ASSET)
    if texture is None:
        task = unreal.AssetImportTask()
        task.set_editor_properties(
            {
                "filename": str(image_path),
                "destination_path": ASSET_DIRECTORY,
                "destination_name": TEXTURE_ASSET.rsplit("/", 1)[-1],
                "automated": True,
                "replace_existing": False,
                "save": True,
            }
        )
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = unreal.EditorAssetLibrary.load_asset(TEXTURE_ASSET)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError(f"Could not import Texture2D at {TEXTURE_ASSET}")
    return texture


def _create_or_update_material(
    texture: unreal.Texture2D,
    opacity: float,
) -> unreal.Material:
    material = unreal.EditorAssetLibrary.load_asset(MATERIAL_ASSET)
    if material is None:
        package_path, asset_name = MATERIAL_ASSET.rsplit("/", 1)
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name,
            package_path,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Expected Material at {MATERIAL_ASSET}")

    material.set_editor_properties(
        {
            "material_domain": unreal.MaterialDomain.MD_SURFACE,
            "blend_mode": unreal.BlendMode.BLEND_TRANSLUCENT,
            "two_sided": True,
        }
    )
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)

    texture_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionTextureSampleParameter2D,
        -300,
        -100,
    )
    texture_node.set_editor_properties(
        {
            "parameter_name": "InputTexture",
            "texture": texture,
        }
    )
    opacity_node = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionScalarParameter,
        -300,
        150,
    )
    opacity_node.set_editor_properties(
        {
            "parameter_name": "OverlayOpacity",
            "default_value": opacity,
        }
    )
    if not unreal.MaterialEditingLibrary.connect_material_property(
        texture_node,
        "RGB",
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
    ):
        raise RuntimeError("Could not connect the reference texture to Emissive Color")
    if not unreal.MaterialEditingLibrary.connect_material_property(
        opacity_node,
        "",
        unreal.MaterialProperty.MP_OPACITY,
    ):
        raise RuntimeError("Could not connect overlay opacity to Material Opacity")
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def _texture_dimensions(texture: unreal.Texture2D) -> tuple[int, int]:
    return (
        int(texture.blueprint_get_size_x()),
        int(texture.blueprint_get_size_y()),
    )


def _ensure_plate_actor(
    camera: unreal.CameraActor,
    material: unreal.Material,
    texture: unreal.Texture2D,
    enabled: bool,
) -> unreal.ImagePlate:
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(actor_subsystem.get_all_level_actors())
    plate_actor = _one_actor_with_label(actors, OVERLAY_LABEL, unreal.ImagePlate)
    if plate_actor is None:
        location = camera.get_actor_location()
        forward = camera.get_actor_forward_vector()
        plate_location = unreal.Vector(
            float(location.x) + float(forward.x) * PLATE_DISTANCE_CM,
            float(location.y) + float(forward.y) * PLATE_DISTANCE_CM,
            float(location.z) + float(forward.z) * PLATE_DISTANCE_CM,
        )
        plate_actor = actor_subsystem.spawn_actor_from_class(
            unreal.ImagePlate,
            plate_location,
            camera.get_actor_rotation(),
        )
        if plate_actor is None:
            raise RuntimeError("Unreal failed to spawn the photographic ImagePlate")
        plate_actor.set_actor_label(OVERLAY_LABEL, True)

    attached = plate_actor.attach_to_component(
        camera.camera_component,
        "",
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        False,
    )
    if not attached:
        raise RuntimeError("Could not attach the photographic ImagePlate to the camera")

    location = camera.get_actor_location()
    forward = camera.get_actor_forward_vector()
    plate_actor.set_actor_location_and_rotation(
        unreal.Vector(
            float(location.x) + float(forward.x) * PLATE_DISTANCE_CM,
            float(location.y) + float(forward.y) * PLATE_DISTANCE_CM,
            float(location.z) + float(forward.z) * PLATE_DISTANCE_CM,
        ),
        camera.get_actor_rotation(),
        False,
        False,
    )

    parameters = unreal.ImagePlateParameters()
    parameters.set_editor_properties(
        {
            "material": material,
            "texture_parameter_name": "InputTexture",
            "fill_screen": True,
            "fill_screen_amount": unreal.Vector2D(100.0, 100.0),
            "render_texture": texture,
        }
    )
    plate_actor.image_plate.set_image_plate(parameters)
    plate_actor.image_plate.set_visibility(enabled, True)
    plate_actor.image_plate.set_editor_property("is_editor_only", True)
    return plate_actor


def apply_overlay(
    *,
    enabled: bool = True,
    opacity: float = DEFAULT_OPACITY,
) -> dict[str, Any]:
    opacity = validate_opacity(opacity)
    config_path, config = _load_config()
    expected_camera = config["camera"]
    image = config["reference_image"]
    image_path = resolve_repo_path(config_path, image["path_convention"])

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(actor_subsystem.get_all_level_actors())
    camera = _one_actor_with_label(actors, CAMERA_LABEL, unreal.CameraActor)
    if camera is None:
        raise RuntimeError(
            f"Could not find {CAMERA_LABEL!r} in the current level. "
            "Open Tryfan_Lab004 and run the calibrated observer placement first."
        )
    observed_camera = _verify_camera(camera, expected_camera)

    texture = _import_texture(image_path)
    width, height = _texture_dimensions(texture)
    expected_width = int(image["native_width"])
    expected_height = int(image["native_height"])
    if (width, height) != (expected_width, expected_height):
        raise RuntimeError(
            f"Imported reference is {width}x{height}; expected "
            f"{expected_width}x{expected_height}"
        )
    actual_aspect = aspect_ratio(width, height)
    expected_aspect = float(image["aspect_ratio"])
    if not math.isclose(actual_aspect, expected_aspect, rel_tol=0.0, abs_tol=1e-9):
        raise RuntimeError(
            f"Reference aspect ratio {actual_aspect:.9f} does not match "
            f"configured {expected_aspect:.9f}"
        )
    if not math.isclose(
        observed_camera["aspect_ratio"],
        actual_aspect,
        rel_tol=0.0,
        abs_tol=1e-5,
    ):
        raise RuntimeError(
            "The calibrated camera frame is not the same 4:3 aspect ratio as "
            "the photographic reference"
        )

    material = _create_or_update_material(texture, opacity)
    plate_actor = _ensure_plate_actor(camera, material, texture, bool(enabled))

    report = {
        "schema_version": 1,
        "purpose": "VISUAL_VALIDATION_ONLY",
        "map": unreal.get_editor_subsystem(
            unreal.UnrealEditorSubsystem
        ).get_editor_world().get_path_name(),
        "config": str(config_path),
        "reference_image": {
            "source": str(image_path),
            "native_dimensions": [width, height],
            "aspect_ratio": actual_aspect,
            "texture_asset": TEXTURE_ASSET,
        },
        "camera": {
            "label": CAMERA_LABEL,
            "path": camera.get_path_name(),
            "observed": observed_camera,
            "verified_against_fixed_lab004a_calibration": True,
            "modified_by_overlay": False,
        },
        "overlay": {
            "label": OVERLAY_LABEL,
            "path": plate_actor.get_path_name(),
            "material_asset": MATERIAL_ASSET,
            "enabled": bool(enabled),
            "opacity": opacity,
            "fill_screen_percent": [100.0, 100.0],
            "aspect_preservation": (
                "The ImagePlate fills the camera's constrained 4:3 frame; "
                "the 640x480 source is not stretched to the editor viewport."
            ),
        },
        "saved_automatically": False,
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / REPORT_NAME
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(
        "Meridian Lab 004A photographic overlay "
        f"{'enabled' if enabled else 'disabled'} at opacity {opacity:.3f}. "
        f"Camera {CAMERA_LABEL} was verified and not modified."
    )
    unreal.log(f"Overlay report: {report_path}")
    unreal.log(
        "Save the level if you want the ImagePlate actor to persist; otherwise "
        "re-run this script after reopening."
    )
    return report


def main() -> dict[str, Any]:
    return apply_overlay(
        enabled=bool(globals().get("MERIDIAN_REFERENCE_OVERLAY_ENABLED", True)),
        opacity=float(
            globals().get("MERIDIAN_REFERENCE_OVERLAY_OPACITY", DEFAULT_OPACITY)
        ),
    )


if __name__ == "__main__":
    RESULT = main()
