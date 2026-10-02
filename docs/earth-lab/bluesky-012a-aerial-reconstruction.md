# Lab 012A — Bluesky high-resolution aerial reconstruction

## Question and scope

At fixed 25 cm surface geometry, how much useful 3D visual information do the
supplied 25 cm, 12.5 cm and 5 cm orthophotos add? At which distances does texture
detail exceed what that geometry can support? This is a local urban/suburban
sample experiment, not Tryfan integration, semantic classification, a new numbered
Meridian phase, or an Atlas architecture change.

**Rights:** the ZIPs contain Bluesky copyright but no redistribution licence.
Treat them as local research/evaluation inputs. No source imagery, meshes,
textures, Unreal assets or captures are published in Git or the web application.
The original four ZIPs remain unchanged in the external data root.

## Source evidence and registration

All four packages cover SK5639: BNG edge bounds
`[456000,339000,457000,340000]`, 1000 × 1000 m. World-file transforms, raster
dimensions and the ASCII grid independently establish the same footprint.

| Product | Native dimensions | Spacing | Pixels/m² | RGB pixels/DSM cell |
| --- | --- | --- | --- | --- |
| RGB 25 cm | 4000 × 4000 | 0.25 m | 16 | 1 |
| RGB 12.5 cm | 8000 × 8000 | 0.125 m | 64 | 4 |
| RGB 5 cm | 20000 × 20000 | 0.05 m | 400 | 25 |
| Photogrammetric DSM | 4000 × 4000 | 0.25 m | 16 height samples | — |

Imagery is vendor-compressed JPEG, decoded RGB uint8, with no supplied NoData mask.
Black pixels are not silently removed. The DSM is float32 when read from ESRI
ASCII, range approximately 23.30–103.415, with declared -9999 NoData but **zero
missing cells**. Rows run north to south; columns west to east.

The 25/12.5 cm PRJs describe OSGB36/Airy British National Grid; 5 cm XML identifies
`osgb:BNG`. The DSM has no separate CRS/vertical metadata. Its BNG interpretation
is supported by the exact common grid coordinates and paired sample package.
Vertical metres are an explicit evaluation assumption; the absolute vertical
datum is unspecified. No claim of independently verified survey accuracy is made.

The 25 cm TAB references `SK5609.jpg`, while its coordinates, JGW and actual JPEG
identify SK5639. Both TABs assign corner coordinates to pixel indices whose JGW
positions are half a cell inward. **Use the explicit JGW pixel-centre convention**;
do not alter vendor originals. First DSM/25 cm centre is
`(456000.125,339999.875)`. The finer pixels partition each DSM cell exactly;
their individual centres do not all coincide with the DSM centre.

Only the 5 cm package supplies a flight date: **2018-09-01**, Leica CityMapper,
orthorectified, GPS + OSTN02 control, nominal 2888 m flight height, 100.5 mm focal
length; product completion 2019-06-26. Its embedded EXIF save timestamp in 2020
is not the flight date. Lower-resolution imagery and DSM acquisition dates are
not supplied. Different cars and shadows in matching crops demonstrate that
**the products are not an established same-observation resolution pyramid**.
Differences cannot all be attributed causally to pixel spacing.

## Derived representation

[Ingestion code](../../scripts/earth_lab/bluesky_012a.py) verifies metadata and
hashes, then writes only under
`MERIDIAN_DATA_ROOT/experiments/earth-lab/bluesky-012a/native-surface-v1`.
Sources are safely extracted there without changing downloaded ZIPs. Native JPEG
pixels are read in bounded scanline strips; the entire 20k image is not decoded
into a single in-memory array. No new scientific dependency is required.

The DSM uses every measured cell centre: **16,000,000 unique vertices and
31,984,002 triangles**. There is no smoothing, height interpolation, simplification
or vertical exaggeration. Sixty-four mesh patches duplicate shared boundary
vertices (16,056,049 submitted vertices). Normals use the same finite-difference
DSM gradient with a one-cell apron so adjoining patches share normals exactly.
The mesh spans 999.75 m between cell centres; the outer 0.125 m half-cell borders
are not invented. Heightfields cannot represent overhangs or vertical facades.

glTF uses local east/up/south metres, with 70 m subtracted from heights for a local
origin. Unreal converts this to east/south/up centimetres. Numeric imported bounds,
triangle counts and LOD counts are checked. Nanite, collision generation and
automatic LOD simplification are disabled. UVs use full float precision.

Each imagery source supplies 64 native PNG tiles with the same nominal 125 m
footprint and a 0.25 m apron. Tile dimensions are **502, 1004 and 2510 pixels**
respectively. PNG stores the decoded JPEG values losslessly; it cannot undo vendor
JPEG compression. Edge aprons replicate boundary pixels outside the AOI only.
No texture is resized or sharpened. The three source RGB arrays would require
48 MB, 192 MB and 1.2 GB; tiled GPU BGRA base levels approximately 64.5 MB,
258.1 MB and 1.613 GB, plus average mip chains (approximately one third extra).
This cost is experimental evidence, not a proposed production Atlas design.

## Controlled renderer and views

The existing UE 5.8.2 toolchain with Direct3D 11 / SM5 is reused in a **separate generated project** in the
external Lab folder. The preserved Tryfan project/map is never opened or modified.
[Renderer helper](../../scripts/earth_lab/unreal_bluesky_012a.py) offers:

- `neutral`: identical DSM, fixed grey;
- `rgb25`, `rgb125`, `rgb5`: identical DSM, corresponding native source pixels.

All materials are unlit with the same simple analytic normal shading:
`colour * (0.65 + 0.35 * max(dot(normal,(0.4,-0.3,0.8660254)),0))`.
No atmosphere, procedural detail, generated buildings/vegetation or displacement
is added. Orthophoto shadows remain baked into the source. Exposure adaptation,
motion blur, bloom and anti-aliasing are disabled consistently. Unreal's common
tone treatment applies to all variants.

Sampling is sRGB, uncompressed BGRA, clamped, trilinear, simple-average mipmaps,
LOD bias zero. Full chains have 9, 10 and 12 mip levels; measured GPU totals are
85,944,064 / 343,996,160 / 2,150,048,512 bytes. Tiles are fully resident (`never_stream`) for controlled capture;
this is deliberately costly, and does not remove normal distance-dependent mip
sampling. Built GPU dimensions are checked, not just source import dimensions.
There is no browser/MapLibre texture-size bottleneck: largest tile is 2510².

Four fixed views target the residential roofs/gardens seen in native source crops:

| View | Position local m | Target local m | Approx screen footprint at target |
| --- | --- | --- | --- |
| overview | (500,520,1250) | (500,500,0) | 0.607 m/pixel |
| moderate | (430,680,230) | (430,500,15) | 0.136 m/pixel |
| low | (430,610,65) | (430,500,15) | 0.059 m/pixel |
| close | (402,543,36) | (425,520,12) | 0.020 m/pixel |

All use 50° horizontal FOV, 1920 × 1080, identical camera transforms and render
settings across A/B/C/D. These estimates are perpendicular target-plane sampling,
not exact GSD throughout an oblique image. The overview covers the central area,
not the full kilometre square. No visual result is inferred solely from those estimates.

## Run and inspect locally

From the repository root, using the established Earth Lab scientific environment:

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\bluesky_012a.py --validate-only
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\bluesky_012a.py
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts\earth_lab\bluesky_012a.py --verify-products
..\meridian-data\earth-lab\.venv\Scripts\python.exe -m unittest discover -s scripts\earth_lab -p test_bluesky_012a.py
```

The complete build is deterministic but substantial. Existing prepared products
need not be rebuilt for inspection. `--prepare-renderer` refreshes only the generated
project/helper, without rebuilding native geometry/textures. Set an absolute
`MERIDIAN_DATA_ROOT` if using a non-default root; see
[scientific environment setup](../../scripts/earth_lab/README.md).

Open external `unreal/BlueskyLab012A.uproject` in UE 5.8.2. In its Python console:

```python
import unreal, sys
sys.path.insert(0, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir() + 'Python'))
import lab012a
lab012a.setup()  # first-time native import only
# For the already prepared project, load the existing map instead:
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012A/Lab012A')
lab012a.view('close')  # also overview, moderate, low
lab012a.variant('neutral')
lab012a.variant('rgb25')
lab012a.variant('rgb125')
lab012a.variant('rgb5')
```

Pilot `Lab012A_Camera`; do not move it between variants. `lab012a.comparisons()`
can export sixteen fixed SceneCapture images under external `captures/`. Prefer
one variant per process on this machine to bound accumulated CPU/GPU resources:

```powershell
$labDataRoot = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { (Resolve-Path ..\meridian-data).Path }
$labProject = Join-Path $labDataRoot 'experiments\earth-lab\bluesky-012a\native-surface-v1\unreal'
$ueCmd = Join-Path ${env:ProgramFiles} 'Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
foreach ($state in @('neutral','rgb25','rgb125','rgb5')) {
    & $ueCmd "$labProject\BlueskyLab012A.uproject" -run=pythonscript "-script=$labProject\Content\Python\capture_$state.py" -AllowCommandletRendering -unattended -nop4 -nosplash -d3d11
    if ($LASTEXITCODE -ne 0) { throw "Capture failed: $state" }
}
```

The generated `setup_all.py` can similarly be run with `-NullRHI` for first-time
import. Existing assets do not need reimporting. This new
project has no ImagePlate; it does not revive Tryfan's camera-bound overlay capture
pipeline. Vendor imagery and captures remain private local evaluation outputs.

## Validation and observations

All sixteen 1920 × 1080 captures were produced and checked: four states at each
fixed view, identical numeric camera poses and mesh/actor transforms across states.
All 192 texture resources retain native base dimensions and complete uncompressed
BGRA mip chains. Four source ZIP hashes and 260 native product hashes pass;
independent samples check 27 texture pixels and three DSM-to-mesh heights.
All native products reproduced byte-for-byte across three processing runs.
The [metadata](bluesky-012a-metadata.json) and
[validation measurements](bluesky-012a-validation.json) contain hashes and exact values.

The first all-variant D3D12 preparation lost the GPU device with severe memory
pressure. Its partial captures were discarded. A generated texture interrupted
by that crash was reimported from its verified native PNG; nominal dimensions
alone were insufficient, so full mip byte counts are now also required. Final
acceptance used separate sequential D3D11 processes, all with zero commandlet
errors. This machine has 16 GB RAM; import/capture peaks reached approximately
19–21 GB private virtual memory during the densest preparation and approximately
5.8 GB resident memory in the final 5 cm capture. Free resources/page-file capacity
matter. D3D12 recoverability is not claimed by this Lab.

Inspection of source crops and exported 3D views showed:

- **Overview (~1.25 km):** all imagery states locate roads, roofs and crowns beyond
  the neutral geometry. Extra fine source pixels are mostly below output-pixel
  scale here; tonal/seasonal differences are conspicuous and cannot be assigned
  to resolution.
- **Moderate (~280 m):** 25 → 12.5 cm is a modest change in these supplied products.
  The 5 cm product makes roof edges, markings and small colour features clearer;
  its different shadows/acquisition also change appearance.
- **Low (~121 m):** finer image detail survives, but heightfield walls and tree
  curtains already dominate several regions. Orthophoto paint stretches down
  steep height transitions; no facade/branch evidence is invented.
- **Close (~40 m):** 25 and 12.5 cm products both look soft, with some finer edges
  in 12.5 cm. The 5 cm product visibly resolves finer roof pattern, roof openings,
  road markings and crown colour structure. Those features remain painted on the
  same irregular roof surfaces and vertical skirts; texture improvement does not
  repair geometry.

Narrow lines and small objects are easier to distinguish in the 5 cm native
source crops; their stable identity/3D form is not independently validated.
Nominal pixel spacing does not establish effective optical sharpness. The 12.5 cm
sample's relatively modest improvement is not a verdict on every 12.5 cm survey.
There is no universal winner or single geometry-limited distance: roofs can gain
texture detail while adjacent facades/crowns remain limited by the heightfield.
No purchasing decision is made.

## What Lab 012A tells us

The sources have matching numeric footprints, and native imagery density increases
fourfold and then 6.25-fold while geometry remains fixed. Native preservation is
possible with small tiles rather than silently shrinking a 20k image.

## What Lab 012A cannot tell us

It cannot isolate acquisition, processing, illumination and resolution differences;
prove actual positional accuracy; recover omitted DSM geometry; establish an
absolute vertical datum; or establish visibility of Tryfan's mountain surfaces.

## Questions that require Tryfan

Observability of exposed bedrock, individual boulders, scree, grass/heath, paths,
wet ground, gullies/fissures and ambiguous boundaries remains untested. Urban
roof/road evidence is not a direct demonstration of those mountain features.

## Recommended next experiment

First obtain same-acquisition metadata or perform an explicitly controlled
resolution comparison from one observation. Then, subject to this evidence and
separate approval/licensing, consider a small Tryfan 12.5 cm pilot. Do not infer
rocks or vegetation, purchase data, or implement another Lab from this result alone.
