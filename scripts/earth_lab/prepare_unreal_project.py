from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_DESCRIPTOR = {
    "FileVersion": 3,
    "EngineAssociation": "5.8",
    "Category": "Meridian Earth Laboratory",
    "Description": "Measured terrain Landscape import validation",
    "Plugins": [
        {"Name": "PythonScriptPlugin", "Enabled": True},
        {"Name": "EditorScriptingUtilities", "Enabled": True},
        {"Name": "ImagePlate", "Enabled": True},
    ],
}


def _import_guide(manifest: dict, manifest_path: Path) -> str:
    landscape = manifest["unreal_landscape"]
    origin = manifest["coordinate_frame"]["local_origin_bng"]
    level_name = str(
        manifest.get("suggested_level_name")
        or manifest.get("aoi_identifier", "Meridian_Earth_Landscape")
    ).replace("-", "_")
    r16 = manifest["surfaces"]["dtm"]["output"]["files"]["r16"]
    r16_path = (manifest_path.parent / "heightmaps" / r16["path"]).resolve()
    half_width_cm = landscape["expected_world_dimensions_m"][0] * 50.0
    half_height_cm = landscape["expected_world_dimensions_m"][1] * 50.0
    return f"""# Meridian Earth Landscape import

This procedure creates the measured DTM as a new Landscape. Do not apply smoothing,
erosion, noise, vertical exaggeration, missing-data fill, or an existing edit layer.

## Canonical input

- File: `{r16_path}`
- SHA-256: `{r16["sha256"]}`
- Format: little-endian uint16 R16
- Resolution: `{landscape["quads_per_axis"] + 1} x {landscape["quads_per_axis"] + 1}` vertices

## Safest corrective import

1. Create a clean **Empty Level** for this AOI. If reusing a level, first confirm it
   contains no Landscape. This procedure creates a new normal Landscape and does not
   require World Partition.
2. Enter **Landscape** mode, choose creation/import for a **new Landscape**, and
   select **Import from File**.
3. Select the canonical R16 above. If Unreal does not detect
   `{landscape["quads_per_axis"] + 1} x {landscape["quads_per_axis"] + 1}`, stop.
4. Set **Flip Y Axis** off and **Enable Edit Layers** off.
5. Set section size to `{landscape["quads_per_section"]} x {landscape["quads_per_section"]}` quads,
   sections per component to `2 x 2`, and components to
   `{landscape["components"][0]} x {landscape["components"][1]}`. Confirm overall
   resolution `{landscape["quads_per_axis"] + 1} x {landscape["quads_per_axis"] + 1}` and
   `{landscape["components"][0] * landscape["components"][1]}` total components.
6. Set location to `X=-{half_width_cm:.6f}, Y=-{half_height_cm:.6f}, Z=0` cm,
   rotation to `0, 0, 0`, and scale to
   `X={landscape["xy_scale_cm"]:.9f}, Y={landscape["xy_scale_cm"]:.9f}, Z={landscape["z_scale"]:.6f}`.
7. Import once, save the level as `{level_name}`, and do not rescale after import.

The location is derived from the manifest: {landscape["quads_per_axis"]} quads at
{landscape["xy_scale_cm"]:.9f} cm span exactly
{landscape["expected_world_dimensions_m"][0] * 100:.6f} cm. Placing the first northwest
vertex at (-{half_width_cm:.6f}, -{half_height_cm:.6f}) makes the opposite vertex
(+{half_width_cm:.6f}, +{half_height_cm:.6f}), so Unreal (0,0) is BNG E
{origin["easting"]}, N {origin["northing"]}. +X is east, +Y is south, and encoded
midpoint 32768 at actor Z=0 represents {origin["elevation_m_odn"]} m ODN.

## Acceptance

Run `Content/Python/validate_landscape.py` from Unreal's **Execute Python Script**
command. It uses UE 5.8's `EditorActorSubsystem`, treats the logical Landscape and
World Partition streaming proxies as one terrain, derives component topology and
bounds, and compares collision heights with the canonical R16, including the AOI
centre and Tryfan references. It writes `Saved/meridian-landscape-validation.json`
without modifying the Landscape. Continue only when the overall result is PASS.
"""


def prepare_project(
    manifest_path: Path,
    project_root: Path,
    benchmark_path: Path | None = None,
    photo_overlay_path: Path | None = None,
) -> Path:
    manifest_path = manifest_path.resolve()
    project_root = project_root.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "Config").mkdir(exist_ok=True)
    python_root = project_root / "Content" / "Python"
    python_root.mkdir(parents=True, exist_ok=True)

    descriptor = dict(PROJECT_DESCRIPTOR)
    descriptor["Description"] = (
        f'{manifest.get("representation", {}).get("type", "Measured terrain")} '
        "import validation"
    )
    project_file = project_root / f"{project_root.name}.uproject"
    project_file.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")
    (project_root / "meridian-landscape-source.json").write_text(
        json.dumps({"manifest": str(manifest_path)}, indent=2) + "\n",
        encoding="utf-8",
    )
    if benchmark_path is not None:
        benchmark_path = benchmark_path.resolve()
        json.loads(benchmark_path.read_text(encoding="utf-8"))
        (project_root / "meridian-benchmark-source.json").write_text(
            json.dumps({"benchmark": str(benchmark_path)}, indent=2) + "\n",
            encoding="utf-8",
        )
    if photo_overlay_path is not None:
        photo_overlay_path = photo_overlay_path.resolve()
        json.loads(photo_overlay_path.read_text(encoding="utf-8"))
        (project_root / "meridian-photo-overlay-source.json").write_text(
            json.dumps({"config": str(photo_overlay_path)}, indent=2) + "\n",
            encoding="utf-8",
        )
    (project_root / "Config" / "DefaultEngine.ini").write_text(
        "[/Script/EngineSettings.GeneralProjectSettings]\n"
        "ProjectName=Meridian Earth Laboratory\n",
        encoding="utf-8",
    )
    python_sources = {
        "validate_landscape.py": Path(__file__).with_name("unreal_validate_landscape.py"),
        "place_observer.py": Path(__file__).with_name("unreal_place_observer.py"),
        "observer_geometry.py": Path(__file__).with_name("observer_geometry.py"),
        "photo_overlay.py": Path(__file__).with_name("photo_overlay.py"),
        "setup_photo_overlay.py": Path(__file__).with_name("unreal_photo_overlay.py"),
        "restore_lab004a_camera.py": Path(__file__).with_name(
            "unreal_restore_camera.py"
        ),
        "validate_lab004a_camera.py": Path(__file__).with_name(
            "unreal_validate_camera.py"
        ),
    }
    for target_name, source_path in python_sources.items():
        (python_root / target_name).write_text(
            source_path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    (project_root / "IMPORT.md").write_text(
        _import_guide(manifest, manifest_path), encoding="utf-8"
    )
    return project_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a minimal Unreal project for a generated Landscape manifest."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path)
    parser.add_argument("--photo-overlay", type=Path)
    arguments = parser.parse_args()
    print(
        prepare_project(
            arguments.manifest,
            arguments.project_root,
            benchmark_path=arguments.benchmark,
            photo_overlay_path=arguments.photo_overlay,
        )
    )


if __name__ == "__main__":
    main()
