# Tryfan Reference Renderer

This Unreal Engine project is Meridian's high-fidelity reference environment for
inspecting and validating Atlas representations at Tryfan. It consumes Meridian
terrain and reconstruction products; it does not define the canonical scientific
representation.

The project originated in historical Lab 004 and later accumulated the validated
camera, overlay and Lab 009 material state. The first preservation checkpoint keeps
`TryfanLab004.uproject`, `/Game/Tryfan_Lab004` and historical actor names unchanged so
that relocation and durable versioning are not mixed with an Unreal package rename.

## Durable source

Normal Git stores the project descriptor, curated configuration, this documentation,
the manifest and bootstrap logic. Git LFS stores only
`Content/Tryfan_Lab004.umap`, the unique calibrated map. The map contains the
validated 3025 x 3025 Landscape, fixed Lab 004A camera, actor/component state and
material bindings. It is a normal single-Landscape level with no World Partition
external-actor packages.

The committed `DefaultEngine.ini` intentionally omits the generated Android file
server section and its credential. The unused Android File Server plugin is explicitly
disabled in the project descriptor so UE does not regenerate that credential.
`DefaultInput.ini` is not source: its contents
were engine-generated defaults, while camera HFOV and aspect are established and
validated by repository configuration and Python.

## Generated and external state

The following are deliberately excluded from version control:

- `Content/Python`: deployed copies of `scripts/earth_lab` implementation;
- `Content/MeridianLab004`: imported validation photograph and overlay material;
- `Content/MeridianLab009`: imported control textures and generated material;
- `Content/MeridianLab010`: observed Sentinel natural-colour texture/material;
- `Saved`, `Intermediate`, `DerivedDataCache`, `Binaries`, logs and autosaves;
- machine-local `meridian-*-source.json` pointers.

The generated packages are referenced by the saved map, but are reproducible at the
same Unreal asset paths. Their source image, packed controls, hashes and provenance
remain below `MERIDIAN_DATA_ROOT/experiments/earth-lab`. The historical absolute R16 import filename
embedded in the map is import metadata, not the runtime data-location contract.

## Bootstrap

Install Unreal Engine 5.8.2 with the Python Script, Editor Scripting Utilities and
Image Plate plugins available. From the repository root, set `MERIDIAN_DATA_ROOT`
to the external Meridian data directory when it is not the default sibling directory,
then run:

```powershell
python renderers/unreal/tryfan-reference/bootstrap_renderer.py
```

The bootstrap verifies the canonical terrain, photograph and Lab 009 inputs by
SHA-256. It then deploys repository-owned Python and writes ignored machine-local
source pointers. It never opens, edits or saves the map.

Open `TryfanLab004.uproject` in Unreal Engine 5.8.2 and open
`/Game/Tryfan_Lab004`. Before deliberately saving anything, run this from Unreal's
Python console:

```python
import unreal; exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir() + "Python/validate_reference_renderer.py"), encoding="utf-8").read())
```

The first map load may report those deliberately absent generated packages. The
smoke validator recreates the ignored Lab 009 and photo-overlay packages at their
recorded asset paths, with the overlay disabled, then runs the Landscape, fixed-camera
and Lab 009 validators.
It writes reports below ignored `Saved` and does not save the map. A successful run
reports `PASS` for all three. The committed map must retain SHA-256
`85ef8f1cc9a9fda9b6f2ab3b911bd57831fe75c4009e5ad168ea4956165a260d`.

The Landscape acceptance checks topology, 3 km extent, registration, transform and
collision heights against the canonical R16. The fixed camera must remain at the
manifested position and rotation with 35.2 degree horizontal FOV and constrained 4:3
aspect. The Lab 009 validator checks its two 3025 x 3025 non-sRGB mask textures,
material bindings, unchanged Landscape transform and unchanged camera.

## Reference photograph

The Tony Edwards image and screen-space overlay are validation instruments. Ground
photography is not canonical reconstruction input. To show the overlay at 50 percent
after a successful smoke validation, run:

```python
MERIDIAN_REFERENCE_OVERLAY_ENABLED = True; MERIDIAN_REFERENCE_OVERLAY_OPACITY = 0.5; exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir() + "Python/setup_photo_overlay.py"), encoding="utf-8").read())
```

Do not save an incidental editor change to the calibrated map. Lab 009's fixed-camera
visual acceptance remains pending the documented manual baseline/reconstruction
comparison.

## Version-control rules

Lab 010 is an optional observed-colour comparison on this same preserved map.
See [the Lab 010 procedure](../../../docs/earth-lab/tryfan-010-observed-natural-colour.md)
for building/deploying retained Sentinel RGB and switching baseline, Lab 009,
Lab 010 and Lab 010 with 50% photographic overlay without saving the map.
Its 300 × 300 texture retains 10 m observed resolution. Default bootstrap and
Lab 009 validation remain unchanged; Lab 010 has a separate optional deployment.

Never commit credentials, personal absolute paths, source-pointer JSON, downloaded
source data, generated control rasters, imported/generated `.uasset` packages,
Unreal caches, logs, autosaves or routine `Saved` state. Changes to the LFS-tracked
map require an intentional Unreal edit, complete renderer validation, an updated
manifest hash and focused review. The external pre-preservation project remains a
recovery copy; do not use it as the repository renderer's source of truth after this
checkpoint.
