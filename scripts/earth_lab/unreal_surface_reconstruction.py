"""Install, apply, or restore the reversible Lab 009 Landscape material."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unreal

from photo_overlay import camera_mismatches

POINTER_NAME = "meridian-lab009-source.json"
CAMERA_LABEL = "Meridian_Lab004_Geometric_Camera"
EXPECTED_MAP = "/Game/Tryfan_Lab004.Tryfan_Lab004"
BASELINE_REPORT = "meridian-lab009-baseline.json"
SETUP_REPORT = "meridian-lab009-setup.json"


def _load_configuration() -> tuple[Path, dict[str, Any], Path]:
    pointer_path = Path(unreal.Paths.project_dir()) / POINTER_NAME
    if not pointer_path.is_file():
        raise RuntimeError(f"Missing Lab 009 pointer: {pointer_path}")
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    config_path = Path(pointer["config"]).resolve()
    return config_path, json.loads(config_path.read_text(encoding="utf-8")), Path(pointer["output_root"]).resolve()


def _actors() -> list[unreal.Actor]:
    return list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())


def _one_actor(label: str, actor_type: type) -> unreal.Actor:
    matches = [actor for actor in _actors() if isinstance(actor, actor_type) and actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {label!r}; found {len(matches)}")
    return matches[0]


def _one_landscape() -> unreal.Landscape:
    matches = [actor for actor in _actors() if isinstance(actor, unreal.Landscape)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one root Landscape; found {len(matches)}")
    return matches[0]


def _observe_transform(actor: unreal.Actor) -> dict[str, list[float]]:
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    scale = actor.get_actor_scale3d()
    return {
        "location_cm": [float(location.x), float(location.y), float(location.z)],
        "rotation_degrees": [float(rotation.pitch), float(rotation.yaw), float(rotation.roll)],
        "scale": [float(scale.x), float(scale.y), float(scale.z)],
    }


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


def _import_mask_texture(source: Path, asset_path: str) -> unreal.Texture2D:
    if not source.is_file():
        raise FileNotFoundError(f"Lab 009 packed texture is missing: {source}")
    package_path, asset_name = asset_path.rsplit("/", 1)
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source), "destination_path": package_path,
        "destination_name": asset_name, "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError(f"Could not import Texture2D at {asset_path}")
    texture.set_editor_property("srgb", False)
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    texture.set_editor_property("filter", unreal.TextureFilter.TF_BILINEAR)
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def _expression(material: unreal.Material, expression_type: type, x: int, y: int):
    return unreal.MaterialEditingLibrary.create_material_expression(material, expression_type, x, y)


def _connect(source, output: str, target, input_name: str) -> None:
    if not unreal.MaterialEditingLibrary.connect_material_expressions(source, output, target, input_name):
        raise RuntimeError(f"Could not connect {source.get_class().get_name()}.{output} to {target.get_class().get_name()}.{input_name}")


def _mask(material: unreal.Material, source, channel: str, x: int, y: int):
    node = _expression(material, unreal.MaterialExpressionComponentMask, x, y)
    node.set_editor_properties({name: name == channel for name in ("r", "g", "b", "a")})
    _connect(source, "", node, "Input")
    return node


def _build_uv(material: unreal.Material):
    world = _expression(material, unreal.MaterialExpressionWorldPosition, -1500, -50)
    divisor = _expression(material, unreal.MaterialExpressionConstant, -1300, 100)
    divisor.set_editor_property("r", 300000.0)
    divide = _expression(material, unreal.MaterialExpressionDivide, -1100, -50)
    _connect(world, "XY", divide, "A")
    _connect(divisor, "", divide, "B")
    offset = _expression(material, unreal.MaterialExpressionConstant2Vector, -1100, 100)
    offset.set_editor_properties({"r": 0.5, "g": 0.5})
    add = _expression(material, unreal.MaterialExpressionAdd, -900, -50)
    _connect(divide, "", add, "A")
    _connect(offset, "", add, "B")
    return add


def _colour(material: unreal.Material, rgb: tuple[float, float, float], x: int, y: int):
    node = _expression(material, unreal.MaterialExpressionConstant3Vector, x, y)
    node.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return node


def _build_material(surface: unreal.Texture2D, context: unreal.Texture2D, asset_path: str) -> unreal.Material:
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path) and not unreal.EditorAssetLibrary.delete_asset(asset_path):
        raise RuntimeError(f"Could not replace generated Lab 009 Material at {asset_path}")
    package_path, asset_name = asset_path.rsplit("/", 1)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, package_path, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Expected Material at {asset_path}")
    material.set_editor_properties({"material_domain": unreal.MaterialDomain.MD_SURFACE, "blend_mode": unreal.BlendMode.BLEND_OPAQUE, "two_sided": False})
    uv = _build_uv(material)
    surface_node = _expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -650, -180)
    surface_node.set_editor_properties({
        "parameter_name": "SurfaceControls",
        "texture": surface,
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    })
    context_node = _expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -650, 160)
    context_node.set_editor_properties({
        "parameter_name": "ContextControls",
        "texture": context,
        "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
    })
    _connect(uv, "", surface_node, "UVs")
    _connect(uv, "", context_node, "UVs")
    sources = [
        (surface_node, "R"),
        (surface_node, "G"),
        (surface_node, "B"),
        (surface_node, "A"),
        (context_node, "R"),
    ]
    colours = [(0.19, 0.20, 0.19), (0.32, 0.29, 0.25), (0.16, 0.23, 0.09), (0.27, 0.36, 0.12), (0.06, 0.10, 0.065)]
    products = []
    for index, ((source, output_name), colour) in enumerate(zip(sources, colours)):
        constant = _colour(material, colour, -150, -320 + index * 120)
        multiply = _expression(material, unreal.MaterialExpressionMultiply, 80, -320 + index * 120)
        _connect(source, output_name, multiply, "A")
        _connect(constant, "", multiply, "B")
        products.append(multiply)
    combined = products[0]
    for index, product in enumerate(products[1:], start=1):
        add = _expression(material, unreal.MaterialExpressionAdd, 300 + index * 180, -100)
        _connect(combined, "", add, "A")
        _connect(product, "", add, "B")
        combined = add
    if not unreal.MaterialEditingLibrary.connect_material_property(combined, "", unreal.MaterialProperty.MP_BASE_COLOR):
        raise RuntimeError("Could not connect Lab 009 mixture to Base Color")
    roughness = _expression(material, unreal.MaterialExpressionConstant, 450, 260)
    roughness.set_editor_property("r", 0.88)
    if not unreal.MaterialEditingLibrary.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS):
        raise RuntimeError("Could not connect Lab 009 roughness")
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def _material_path(material) -> str | None:
    return material.get_path_name() if material is not None else None


def _load_material(path: str | None):
    if path in (None, "", "None"):
        return None
    material = unreal.EditorAssetLibrary.load_asset(path)
    if material is None:
        raise RuntimeError(f"Recorded baseline material no longer exists: {path}")
    return material


def apply_lab009(*, enabled: bool = True, save_map: bool = True) -> dict[str, Any]:
    config_path, config, output_root = _load_configuration()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name() != EXPECTED_MAP:
        raise RuntimeError(f"Open {EXPECTED_MAP} before applying Lab 009; current map is {world.get_path_name()}")
    camera = _one_actor(CAMERA_LABEL, unreal.CameraActor)
    camera_pointer = json.loads((Path(unreal.Paths.project_dir()) / "meridian-photo-overlay-source.json").read_text(encoding="utf-8"))
    expected_camera = json.loads(Path(camera_pointer["config"]).read_text(encoding="utf-8"))["camera"]
    camera_before = _observe_camera(camera)
    mismatches = camera_mismatches(camera_before, expected_camera)
    if mismatches:
        raise RuntimeError("Lab 004A camera is not canonical: " + "; ".join(mismatches))
    landscape = _one_landscape()
    landscape_before = _observe_transform(landscape)
    baseline_path = Path(unreal.Paths.project_saved_dir()) / BASELINE_REPORT
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.is_file() else None
    current_material = landscape.get_editor_property("landscape_material")
    lab_material_path = config["unreal"]["material_asset"]
    if baseline is None:
        current_path = _material_path(current_material)
        if current_path == lab_material_path:
            raise RuntimeError("Lab 009 is already assigned but no baseline material record exists")
        baseline = {"schema_version": 1, "map": EXPECTED_MAP, "landscape_path": landscape.get_path_name(), "baseline_material": current_path, "landscape_transform": landscape_before}
        baseline_path.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    if baseline["landscape_transform"] != landscape_before:
        raise RuntimeError("Landscape transform differs from the recorded pre-Lab009 baseline")
    surface_texture = _import_mask_texture(output_root / "unreal" / "lab009-surface-controls-rgba.png", config["unreal"]["surface_texture_asset"])
    context_texture = _import_mask_texture(output_root / "unreal" / "lab009-context-controls-rgba.png", config["unreal"]["context_texture_asset"])
    material = _build_material(surface_texture, context_texture, lab_material_path)
    landscape.modify()
    landscape.set_editor_property("landscape_material", material if enabled else _load_material(baseline["baseline_material"]))
    if _observe_transform(landscape) != landscape_before:
        raise RuntimeError("Landscape transform changed while applying Lab 009")
    camera_after = _observe_camera(camera)
    if camera_mismatches(camera_after, expected_camera):
        raise RuntimeError("Lab 004A camera changed while applying Lab 009")
    if save_map and not unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/Tryfan_Lab004"):
        raise RuntimeError("Unreal failed to save Tryfan_Lab004")
    report = {
        "schema_version": 1, "map": world.get_path_name(), "config": str(config_path), "enabled": bool(enabled),
        "landscape": {"path": landscape.get_path_name(), "transform": landscape_before, "material": _material_path(landscape.get_editor_property("landscape_material"))},
        "baseline_material": baseline["baseline_material"], "lab009_material": lab_material_path,
        "camera": {"label": CAMERA_LABEL, "canonical": True, "unchanged": camera_after == camera_before, "observed": camera_after},
        "saved": bool(save_map), "reversible": True,
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / SETUP_REPORT
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"Meridian Lab 009 {'enabled' if enabled else 'baseline restored'}; report: {report_path}")
    return report


def main() -> dict[str, Any]:
    return apply_lab009(enabled=bool(globals().get("MERIDIAN_LAB009_ENABLED", True)), save_map=bool(globals().get("MERIDIAN_LAB009_SAVE_MAP", True)))


if __name__ == "__main__":
    RESULT = main()
