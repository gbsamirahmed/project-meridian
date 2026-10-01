"""Reversible continuous residual display; no terrain, camera or lighting edits."""
import hashlib
import json
from pathlib import Path

import unreal
import setup_lab010_surface as lab010

TEXTURE = "/Game/MeridianLab011/T_Lab011_Residual"
MATERIAL = "/Game/MeridianLab011/M_Lab011_Residual"


def configuration():
    pointer = json.loads((Path(unreal.Paths.project_dir()) / "meridian-lab011-source.json").read_text())
    root = Path(pointer["output_root"])
    manifest = json.loads((root / "lab011-manifest.json").read_text(encoding="utf-8"))
    for item in manifest["products"]:
        if hashlib.sha256((root / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Lab 011 product identity mismatch")
    return root


def material(root):
    helper = lab010.lab009
    task = unreal.AssetImportTask()
    task.set_editor_properties({"filename": str(root / "lab011-positive-residual-diagnostic-1m.png"),
        "destination_path": "/Game/MeridianLab011", "destination_name": "T_Lab011_Residual",
        "automated": True, "replace_existing": True, "save": True})
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError("Residual texture import failed")
    texture.set_editor_properties({"srgb": True, "compression_settings": unreal.TextureCompressionSettings.TC_EDITOR_ICON,
        "filter": unreal.TextureFilter.TF_BILINEAR, "address_x": unreal.TextureAddress.TA_CLAMP,
        "address_y": unreal.TextureAddress.TA_CLAMP, "mip_gen_settings": unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS})
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    result = unreal.EditorAssetLibrary.load_asset(MATERIAL) if unreal.EditorAssetLibrary.does_asset_exist(MATERIAL) else None
    if result is None:
        result = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_Lab011_Residual", "/Game/MeridianLab011", unreal.Material, unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(result)
    result.set_editor_properties({"material_domain": unreal.MaterialDomain.MD_SURFACE,
        "blend_mode": unreal.BlendMode.BLEND_OPAQUE, "shading_model": unreal.MaterialShadingModel.MSM_UNLIT})
    uv = helper._build_uv(result)
    sample = helper._expression(result, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    sample.set_editor_properties({"parameter_name": "ResidualDiagnostic", "texture": texture,
                                  "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR})
    helper._connect(uv, "", sample, "UVs")
    if not unreal.MaterialEditingLibrary.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("Unlit diagnostic connection failed")
    unreal.MaterialEditingLibrary.recompile_material(result)
    unreal.EditorAssetLibrary.save_loaded_asset(result)
    return result


def apply(state="lab011", overlay=False):
    if state in ("baseline", "lab009", "lab010"):
        return lab010.apply(state, overlay=overlay)
    if state != "lab011":
        raise ValueError("Choose baseline, lab009, lab010 or lab011")
    root = configuration()
    # Reuse the preserved baseline/fixture checks and established overlay mechanism.
    lab010.apply("baseline")
    helper = lab010.lab009
    landscape = helper._one_landscape()
    camera = helper._one_actor(helper.CAMERA_LABEL, unreal.CameraActor)
    before, camera_before = helper._observe_transform(landscape), helper._observe_camera(camera)
    result = material(root)
    landscape.set_editor_property("landscape_material", result)
    lab010.setup_photo_overlay.apply_overlay(enabled=overlay, opacity=0.5)
    if before != helper._observe_transform(landscape) or camera_before != helper._observe_camera(camera):
        raise RuntimeError("Diagnostic changed camera or Landscape transform")
    report = {"state":state,"overlay_enabled":overlay,"camera_unchanged":True,"landscape_transform_unchanged":True,
              "camera":camera_before,"landscape_transform":before,"map_saved":False,
              "material":helper._material_path(result)}
    (Path(unreal.Paths.project_saved_dir()) / "meridian-lab011-state.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


def validate():
    lab010_report = lab010.validate()
    states = [apply("baseline"), apply("lab009"), apply("lab010"), apply("lab011"), apply("lab011",overlay=True)]
    import validate_landscape
    import validate_lab004a_camera
    import validate_lab009_surface
    if validate_landscape.main()["overall"] != "PASS":
        raise RuntimeError("Landscape validation failed")
    if validate_lab004a_camera.validate_saved_camera(load_map=False)["result"] != "PASS":
        raise RuntimeError("Fixed camera validation failed")
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE)
    if (texture.blueprint_get_size_x(),texture.blueprint_get_size_y()) != (3000,3000):
        raise RuntimeError("Residual texture dimensions changed")
    apply("lab009")
    if validate_lab009_surface.validate()["result"] != "PASS":
        raise RuntimeError("Lab 009 restoration failed")
    report = {"result":"PASS","states":states,"lab010_validation":lab010_report["result"],
              "landscape_validator":"PASS","camera_validator":"PASS","lab009_restoration":"PASS",
              "texture_dimensions":[3000,3000],"map_saved":False,"manual_visual_acceptance":"pending",
              "lighting":"No lighting build or atmospheric calibration; existing unbuilt-lighting warning remains a known limitation"}
    (Path(unreal.Paths.project_saved_dir()) / "meridian-lab011-validation.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


if __name__ == "__main__":
    validate()
