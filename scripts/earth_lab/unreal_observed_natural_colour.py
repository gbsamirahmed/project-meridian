"""Concrete reversible Lab 010 material; never saves or edits terrain/camera."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal
import setup_lab009_surface as lab009
import setup_photo_overlay
from photo_overlay import camera_mismatches


TEXTURE = "/Game/MeridianLab010/T_Lab010_NaturalColour"
MATERIAL = "/Game/MeridianLab010/M_Lab010_ObservedNaturalColour"


def configuration():
    pointer = json.loads((Path(unreal.Paths.project_dir()) / "meridian-lab010-source.json").read_text())
    root = Path(pointer["output_root"])
    manifest = json.loads((root / "lab010-manifest.json").read_text(encoding="utf-8"))
    for item in manifest["products"]:
        if hashlib.sha256((root / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Lab 010 product hash mismatch")
    repo = Path(pointer["repository_root"])
    fixture = json.loads((repo / "renderers/unreal/tryfan-reference/renderer-manifest.json").read_text())
    camera = json.loads((repo / "docs/earth-lab/tryfan-004-photo-overlay.json").read_text())["camera"]
    return root, fixture, camera


def build_material(root):
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename": str(root / "lab010-natural-colour-10m.png"),
        "destination_path": "/Game/MeridianLab010", "destination_name": "T_Lab010_NaturalColour",
        "automated": True, "replace_existing": True, "save": True})
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError("Natural colour texture import failed")
    texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_EDITOR_ICON,
        "filter": unreal.TextureFilter.TF_BILINEAR, "address_x": unreal.TextureAddress.TA_CLAMP,
        "address_y": unreal.TextureAddress.TA_CLAMP, "mip_gen_settings": unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS})
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    material = unreal.EditorAssetLibrary.load_asset(MATERIAL) if unreal.EditorAssetLibrary.does_asset_exist(MATERIAL) else None
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_Lab010_ObservedNaturalColour", "/Game/MeridianLab010", unreal.Material, unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    material.set_editor_properties({"material_domain": unreal.MaterialDomain.MD_SURFACE,
                                    "blend_mode": unreal.BlendMode.BLEND_OPAQUE, "two_sided": False})
    uv = lab009._build_uv(material)  # Existing +X east / +Y south registration only.
    sample = lab009._expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    sample.set_editor_properties({"parameter_name": "ObservedRGB", "texture": texture,
                                  "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
    lab009._connect(uv, "", sample, "UVs")
    if not unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR):
        raise RuntimeError("RGB Base Color connection failed")
    for property_name, value in [(unreal.MaterialProperty.MP_ROUGHNESS, 0.88), (unreal.MaterialProperty.MP_SPECULAR, 0.0)]:
        node = lab009._expression(material, unreal.MaterialExpressionConstant, 0, 100)
        node.set_editor_property("r", value)
        if not unreal.MaterialEditingLibrary.connect_material_property(node, "", property_name):
            raise RuntimeError("Fixed material property connection failed")
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def apply(state="lab010", overlay=False):
    if state not in ("baseline", "lab009", "lab010"):
        raise ValueError("Choose baseline, lab009 or lab010")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name() != lab009.EXPECTED_MAP:
        raise RuntimeError("Open the canonical Tryfan map first")
    root, fixture, camera_expected = configuration()
    landscape = lab009._one_landscape()
    camera = lab009._one_actor(lab009.CAMERA_LABEL, unreal.CameraActor)
    before = lab009._observe_transform(landscape)
    camera_before = lab009._observe_camera(camera)
    if camera_mismatches(camera_before, camera_expected):
        raise RuntimeError("Fixed camera differs from the preserved fixture")
    for key in ("location_cm", "rotation_degrees", "scale"):
        if any(abs(x-y) > 1e-4 for x,y in zip(before[key],fixture["terrain"][key])):
            raise RuntimeError("Landscape transform differs from preserved fixture")
    baseline_path = Path(unreal.Paths.project_saved_dir()) / lab009.BASELINE_REPORT
    if not baseline_path.is_file():
        raise RuntimeError("Run the established reference-renderer smoke validation to establish reversible baseline first")
    baseline = json.loads(baseline_path.read_text())
    if state == "baseline":
        material = lab009._load_material(baseline["baseline_material"])
    elif state == "lab009":
        material = lab009._load_material("/Game/MeridianLab009/M_Lab009_Surface")
    else:
        material = build_material(root)
    landscape.set_editor_property("landscape_material", material)
    setup_photo_overlay.apply_overlay(enabled=overlay, opacity=0.5)
    if lab009._observe_transform(landscape) != before or lab009._observe_camera(camera) != camera_before:
        raise RuntimeError("Surface switching modified fixed terrain transform or camera")
    report = {"state": state, "overlay_enabled": overlay, "material": lab009._material_path(material),
              "camera_unchanged": True, "landscape_transform_unchanged": True, "map_saved": False,
              "camera": camera_before, "landscape_transform": before}
    (Path(unreal.Paths.project_saved_dir()) / "meridian-lab010-state.json").write_text(json.dumps(report, indent=2))
    unreal.log("Lab 010 state: " + state + "; map not saved")
    return report


def validate():
    import validate_landscape
    import validate_lab004a_camera
    import validate_lab009_surface
    import validate_reference_renderer

    validate_reference_renderer.validate_reference_renderer()
    reports = [apply("baseline"), apply("lab009")]
    if validate_lab009_surface.validate()["result"] != "PASS":
        raise RuntimeError("Lab 009 failed after reversible switching")
    reports += [apply("lab010"), apply("lab010", overlay=True)]
    if validate_landscape.main()["overall"] != "PASS":
        raise RuntimeError("Landscape geometry/collision validation failed")
    if validate_lab004a_camera.validate_saved_camera(load_map=False)["result"] != "PASS":
        raise RuntimeError("Fixed-camera validation failed")
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE)
    checks = {"native_width": texture.blueprint_get_size_x() == 300,
              "native_height": texture.blueprint_get_size_y() == 300,
              "srgb": texture.get_editor_property("srgb"),
              "uncompressed": texture.get_editor_property("compression_settings") == unreal.TextureCompressionSettings.TC_EDITOR_ICON,
              "bilinear": texture.get_editor_property("filter") == unreal.TextureFilter.TF_BILINEAR,
              "clamp_x": texture.get_editor_property("address_x") == unreal.TextureAddress.TA_CLAMP,
              "clamp_y": texture.get_editor_property("address_y") == unreal.TextureAddress.TA_CLAMP}
    if not all(checks.values()):
        raise RuntimeError("Observed texture settings failed")
    apply("lab009")  # Restore the canonical saved material state in memory, without saving.
    report = {"result": "PASS", "states": reports, "texture_checks": checks,
              "geometry_validator": "PASS", "camera_validator": "PASS", "lab009_validator": "PASS",
              "map_saved": False, "visual_acceptance": "pending_manual_fixed_camera_comparison"}
    (Path(unreal.Paths.project_saved_dir()) / "meridian-lab010-validation.json").write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    if globals().get("MERIDIAN_LAB010_VALIDATE", False):
        RESULT = validate()
    else:
        RESULT = apply(globals().get("MERIDIAN_LAB010_STATE", "lab010"), bool(globals().get("MERIDIAN_LAB010_OVERLAY", False)))
