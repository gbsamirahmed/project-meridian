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
    ],
}


def _import_guide(manifest: dict, manifest_path: Path) -> str:
    landscape = manifest["unreal_landscape"]
    origin = manifest["coordinate_frame"]["local_origin_bng"]
    dtm_png = manifest["surfaces"]["dtm"]["output"]["files"]["png"]["path"]
    return f"""# Meridian Earth Landscape import

This project imports measured terrain. The DTM is the default surface; do not apply
smoothing, erosion, noise, vertical exaggeration, or missing-data fill.

## Import settings

1. Open the project and enter **Landscape** mode.
2. Choose **Import from File** and select:
   `{(manifest_path.parent / "heightmaps" / dtm_png).resolve()}`
3. Confirm the detected heightmap resolution is
   `{landscape["quads_per_axis"] + 1} x {landscape["quads_per_axis"] + 1}`.
4. Use `{landscape["quads_per_section"]}` quads per section,
   `{landscape["sections_per_component"]}` sections per component, and
   `{landscape["components"][0]} x {landscape["components"][1]}` components.
5. Set X and Y scale to `{landscape["xy_scale_cm"]:.9f}` cm and Z scale to
   `{landscape["z_scale"]:.6f}`. Leave **Flip Y Axis** off.
6. Set Landscape location to `X=-100000, Y=-100000, Z=0` cm so its centre is the
   local Unreal origin, then import and save the level.

The resulting Landscape is `{landscape["expected_world_dimensions_m"][0]:.3f} x {landscape["expected_world_dimensions_m"][1]:.3f}` m. Local `(0, 0, 0)` represents
BNG E `{origin["easting"]}`, N `{origin["northing"]}`, elevation
`{origin["elevation_m_odn"]}` m ODN. +X is east, +Y is south, and +Z is up.

## Validation

After import, run `Content/Python/validate_landscape.py` from Unreal's **Execute
Python Script** command. The project records the generated manifest path in its local
source configuration. The script checks
that exactly one Landscape exists, its actor scale matches the manifest, and its
world bounds are approximately 2 km square. It writes
`Saved/meridian-landscape-validation.json`.
"""


def prepare_project(manifest_path: Path, project_root: Path) -> Path:
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
    (project_root / "Config" / "DefaultEngine.ini").write_text(
        "[/Script/EngineSettings.GeneralProjectSettings]\n"
        "ProjectName=Meridian Earth Laboratory\n",
        encoding="utf-8",
    )
    validator_source = Path(__file__).with_name("unreal_validate_landscape.py")
    (python_root / "validate_landscape.py").write_text(
        validator_source.read_text(encoding="utf-8"), encoding="utf-8"
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
    arguments = parser.parse_args()
    print(prepare_project(arguments.manifest, arguments.project_root))


if __name__ == "__main__":
    main()
