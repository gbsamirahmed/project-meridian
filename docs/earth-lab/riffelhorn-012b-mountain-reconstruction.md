# Lab 012B - Riffelhorn mountain reconstruction

2026-10-02. Bounded comparison of observations and representations, not production
Atlas integration. Question: what physical mountain structure survives raw LiDAR,
derived raster products, native raster meshes and rendered views?

## Evidence and provenance

The [acquisition report](../atlas/riffelhorn-data-discovery.md) and
[complete official asset catalogue](../atlas/riffelhorn-data-catalog.json) remain
unchanged. AOI: EPSG:2056 [2624000, 1091000, 2626000, 1093000], 2000 x 2000 m,
4 km2. Heights are metres LN02 (EPSG:5728 provenance), not ellipsoidal heights.
The four tiles are 2624-1091, 2624-1092, 2625-1091 and 2625-1092.

- OBSERVED: 50,546,426 original classified LiDAR returns, August 24/26 2021 and
  northeast-only August 23 2022; 2023 SWISSIMAGE RGB mosaic.
- DERIVED PROVIDER REPRESENTATIONS: spike-free TIN/water-derived swissSURFACE3D
  Raster, and swissALTI3D 2024 with LiDAR base and 2023 photogrammetric updates.
  Both have 0.5 m grid spacing, not independent 0.5 m measurements.
- LAB DERIVATION: unchanged raster samples assembled into native meshes,
  lossless imagery tiles, residual/spacing/terrain diagnostics.
- RENDERED: controlled Unreal geometry and RGB views and offline diagnostics.
- INFERRED: explicitly tentative explanations of disagreement; no semantic labels
  or reconstructed/synthetic surface detail.

Imagery has **25 cm native information resolution, distributed and rendered on a
10 cm sample grid**. It is not 10 cm native imagery. The mosaic's exact per-pixel
dates/seamlines remain unknown; September 7 2023 is only a plausible source flight.
LiDAR, imagery and updated DTM are not co-temporal. Ice, snow, loose material,
water and ground cover can change. Differences do not automatically establish
representation error, object height, rock or vegetation.

Official swisstopo OGD terms linked in the acquisition report permit reuse,
derivation, redistribution and public display with source acknowledgement.
Outputs retain **©swisstopo**. Originals/extracted LAS are immutable and external;
no source download, private data or production integration is added here.

## Representation and registration

A and B use respectively swissALTI3D and swissSURFACE3D Raster. Each uses exactly
16,000,000 native cell-centre vertices and 31,984,002 triangles across 64 patches.
Seam duplication submits 16,056,049 vertices. There is no simplification, LOD,
Nanite, smoothing, collision geometry, vertical exaggeration or invented border.
The outer mesh centres are [2624000.25,1091000.25,2625999.75,1092999.75]; the
outer half-cell is not extrapolated. Normals use finite differences with a shared
one-cell apron; seam heights/normals match exactly. The fixed diagonal topology
is interpolation between measured/provider-derived samples, not new evidence.

Local origin is northwest [2624000,1093000], with LN02 height offset 2500 m.
glTF axes: X east, Y up, Z south, metres. Unreal axes: X east, Y south, Z up,
centimetres; importer conversion 100 cm/m, actor scale one. Bounds are validated
against the actual imported static meshes. The same cameras are used for both
height products; neutral/RGB switching preserves actor transforms and cameras.

Four imagery COGs contain 400,000,000 distributed RGB samples. Sixty-four
2510 x 2510 lossless PNG tiles retain the decoded source, including a 0.5 m
apron; only outside-AOI apron pixels are edge-replicated. Raster and imagery
pixel-edge alignment is shared, but centres differ. UVs explicitly map height
centres to the correct image samples. No sharpening, recolouring or source
resizing occurs. The 267 unflagged black pixels are preserved; none is inside
a selected 60 m diagnostic patch. Their meaning remains unresolved.

Unreal uses native BGRA textures, sRGB, trilinear filtering, simple-average mips,
clamping, zero LOD bias and fully resident textures for capture. Native base
sizes and complete mip-chain byte counts must pass, rather than relying on nominal
asset dimensions. Full texture resources total approximately 2.15 GB per RGB pass.
Mip filtering at distance intentionally reduces effective display detail; it is
not additional observed information. Native GLBs total about 897.7 MB per surface,
PNG tiles 619.8 MB. Exact bytes and all hashes are in the metadata.

## Controlled conditions and views

The isolated external UE 5.8 project does not open Tryfan or Lab 012A.
Both surfaces use the same unlit analytic form-revealing material:
`colour * (0.65 + 0.35 * max(dot(vertexNormalWS,(0.4,-0.3,0.8660254)),0))`.
Neutral colour is linear RGB (0.5,0.5,0.5); the RGB variant uses decoded imagery.
This is diagnostic normal shading, not physical sun reconstruction. No atmosphere,
cast-shadow additions, exposure adaptation, motion blur, bloom or artificial
surface detail. Baked acquisition shadows in the RGB cannot be removed by it.

Seven fixed views: AOI overview, summit oblique, closer steep face, loose-deposit
area, alpine/path transition, lake edge, ice/debris transition. Exact positions,
targets, orientation inputs, 50 degree horizontal FOV, 1920 x 1080 output and
0.1 m near clip are recorded in metadata. No finite far clip is overridden.
Target distances are 4600, 488, 156, 146, 142, 158 and 244 m respectively.
Approximate perpendicular target-plane screen spacing is 2.234, 0.237, 0.076,
0.071, 0.069, 0.077 and 0.119 m/pixel; oblique ground footprints vary.

For each view capture DTM/neutral, DTM/RGB, DSM/neutral, DSM/RGB. Source-context
and raw-return diagnostic figures provide independent evidence, not a triangulated
point-cloud reconstruction. Full exported frames stay external. Attribution adds
a footer without changing the 1920 x 1080 original frame; reduced contact sheets
are explicitly inspection previews. No ImagePlate automation or lighting build.

## Raw observations and representative patches

Seven 60 m squares were selected by source-imagery inspection: summit, shadowed
steep face, loose deposits, alpine/path ground, lake edge, ice/debris margin, and
an auxiliary ice-interior control. Context names are selection labels, not semantic
classification of returns. The loose-deposit and margin locations were revised
before acceptance when initial crops proved to show bedrock and ice interior.
Locations and source-context figures make this selection reproducible.

All 50.5 million returns are scanned. Plan-area density averages 12.636607/m2
(all returns) and 12.477214/m2 (first returns). Across 0.5 m horizontal cells,
5.511775% contain no raw return; count p25/p50/p75/p95/p99 is 2/3/4/6/9.
Raster completeness therefore includes interpolation and is not proof of a direct
observation at every cell. Original class counts are 4,487,455 / 46,053,413 / 214 / 5,203 / 141
for classes 1/2/3/6/9 respectively. First returns number 49,908,855; second
returns 615,400, with 22,171 third-or-later returns. Class 2 can include
boulders under provider classification. No point is renamed a rock or tree.

Exact nearest-other-return distances are queried for 256 deterministic interior
points against all returns in each patch. They are not population-random estimates
or a universal resolution limit; duplicates/overlapping returns are retained.
Patch plan-area density spans 4.92-13.19/m2; median 3-D neighbour spacing spans
0.153-0.215 m, with p95 0.291-0.519 m. Cliff surface-area density and visibility
are not established by horizontal density.

Raster-minus-point vertical differences are accompanied by slope-normal
approximations and, importantly, nearest native-triangle geometric distances for
256 deterministic first ground-class returns per patch. The latter searches an
XY box enclosing +/-2 m: values below 2 m are globally exact; larger values are
local upper bounds with a 2 m lower bound, not exact global distances. No meshing
of raw returns is introduced. Profile strips include +/-0.25 m northing and are
not identical to a mathematical zero-width raster cross-section.

## Quantitative findings

Global DSM-DTM: median 0.003906 m, mean 3.994342 m, standard deviation 6.430026 m,
range -50.825684 to 66.968506 m. p01 -0.336670; p05 -0.007568; p25 -0.001221;
p75 7.971436; p90 14.321777; p95 16.497070; p99 22.343750; p99.5 25.097900;
p99.9 39.298829 m. Absolute difference exceeds 0.1/0.25/0.5/1/2/5 m across
40.304/38.359/36.620/35.248/33.466/29.363% of the AOI. These are geometric
product differences, not object heights.

| Selected context | DSM-DTM median (m) | Point-to-DSM mesh median / p95 (m) |
| --- | ---: | ---: |
| summit | 0.000 | 0.049 / 0.944 |
| steep face | 0.001 | 0.048 / 0.543 |
| loose deposits | 3.864 | 0.050 / 0.200 |
| alpine/path | 0.003 | 0.019 / 0.062 |
| lake edge | -0.414 | 0.026 / 0.336 |
| ice/debris margin | 17.376 | 0.028 / 0.096 |
| ice interior control | 13.402 | 0.022 / 0.076 |

Small median geometric distances coexist with steep-face tails: 1.95% of summit
queries and 0.39% of steep-face queries are at least 2 m from any native mesh
triangle. Those deterministic fractions describe queries, not population area.
Raw profiles contain lower elevations around sharp transitions that the single-valued
heightfield cannot retain. Large vertical residuals alone substantially overstate
loss on slopes; three-dimensional distances are the safer diagnostic.

The large southern DSM-DTM differences coincide with ice/debris contexts. Original
LiDAR fits the older DSM much more closely than the later DTM there. Temporal
updates are a plausible major explanation, not independently proved per pixel.
The provider's unavailable per-cell update lineage prevents assigning all of it to
ice loss or all of it to representation. Water also combines different acquisitions
and provider synthetic-water treatment. Stable bedrock and northern alpine patches
are much more alike between DTM and DSM; ground classification already retains
substantial natural surface structure.

Local departures from the mean are measured at 1.5/3.5/10.5 m windows to expose
scale persistence. They measure terrain form rather than semantic objects; neither
roughness nor curvature establishes rock/vegetation identity.

## Rendered inspection and feature scales

All 28 full captures were inspected through seven four-state contact sheets,
with native-size checks of the oblique rock, close cliff, alpine ground, loose-deposit and ice/debris views. Exact records are in the
[metadata](riffelhorn-012b-metadata.json), [measurements](riffelhorn-012b-measurements.json)
and [validation](riffelhorn-012b-validation.json).

**Observed in the exported views:**

- Overview: both height products retain the broad ridge, bowls and gullies. RGB
  locates alpine ground, lake and ice/debris boundaries which neutral geometry does
  not identify. Fine differences fall below output-pixel scale; large southern
  surface differences are much easier to diagnose numerically than in this view.
- Riffelhorn oblique: major silhouettes and ledges remain broadly alike between
  terrain and surface. Cliff faces show corrugated heightfield skirts; the RGB
  stretches across them. More triangles at the same sample spacing cannot recover
  omitted vertical surface observations or photographic views of a wall.
- Close north face: both neutral variants expose steps and steep relief, while
  both RGB variants are nearly black over much of the face. Source imagery is
  deeply shadowed here. No shadow removal or fabricated cliff colour is added.
- Loose-deposit view: DSM has visibly rougher small protrusions/undulation than
  DTM, while imagery paints angular boundaries onto both. At the selected patch,
  departure-from-local-mean standard deviation is 0.139 versus 0.037 m over 1.5 m
  windows, and 0.235 versus 0.110 m over 3.5 m windows (DSM versus DTM).
  At 10.5 m it is 0.363 versus 0.303 m. This supports retained short-scale roughness
  in the older DSM, but the 3.864 m median elevation difference and update history
  prevent assigning every discrepancy to smoothing or removed boulders.
- Alpine/path view: large raised masses and ground undulations are already visible
  in neutral DTM; DSM changes the selected ground very little. RGB adds paths,
  ground-cover boundaries and fine rock markings, many without corresponding
  small 3-D relief. Large rock-like forms plausibly have both geometric and
  photographic support; identities/absolute accuracy are not independently proved.
- Lake view: RGB gives a sharp shoreline and colour boundary; neutral surfaces
  show different shallow water/edge form. The local -0.414 m difference is not a
  measured bathymetric change. Provider water construction and observation dates
  remain competing explanations. No physically animated water is introduced.
- Ice/debris view: DSM changes apparent ice steps, channels and the surface-to-debris
  boundary substantially. Some RGB cracks/blocks sit on, or stretch over, different
  geometric forms in the two representations. This is a warning about mismatched
  epochs, not evidence that all DSM geometry is more accurate for the 2023 image.

**Feature-scale assessment:**

| Physical scale / setting | Evidence retained and lost |
| --- | --- |
| Tens to hundreds of metres | Strong geometric support for ridge, bowls, gullies and major cliff form; temporal ice elevations remain distinct. |
| Several metres on sampled exposed ground | Raised masses, ledges and depressions survive both provider rasters and native meshes; DSM retains extra roughness in some deposits. Sharp walls remain heightfield approximations. |
| Around one metre | Some local relief is geometrically sampled, but shape/edges are smoothed or faceted and position/classification/epoch uncertainty matters. A few pixels or points do not establish a complete object. |
| Sub-metre | Raw returns can contain finer or multiple-height evidence than a 0.5 m raster; median neighbouring returns are 0.15-0.22 m apart locally. This is not independently verified sub-0.25 m reconstruction accuracy. Imagery supplies fine colour edges, not unseen geometry. |
| Steep/vertical face | Information is orientation-dependent: plan-area density overstates face sampling, a single-valued grid discards topology, and orthophoto shadows/projection can leave little usable wall appearance. |

The native mesh removes no sample beyond the provider raster's representational
limits; triangle interpolation, smoothed normals and the half-cell exterior are
explicit. Raw profiles show information around discontinuities absent from that
representation. Most queried ground returns nevertheless lie within centimetres
of it: rasterisation loss is localized, not wholesale. It is not yet possible to
name all omitted structures, prove overhangs from these strip profiles, or separate
provider interpolation effects from original observation errors at every tail point.

**Current bottlenecks:** overview is mainly output-pixel/mip scale and temporal
interpretation; intermediate views combine the 0.5 m geometric representation,
25 cm image information and baked shadows; close views reveal heightfield topology,
faceting and orthophoto projection/shadow gaps. Fully native texture resources
prove that an accidental Unreal texture resize is not the cause. Raw observation
gaps/accuracy and unseen surfaces remain limits even if another representation
retains more points.

**Implications for Tryfan:** a DTM can already contain substantial natural block
and ledge form; DSM-DTM is not a list of missing rocks. Finer mountain RGB can locate
surface boundaries yet cannot repair wall geometry or supply shadowed/unseen
appearance. The Swiss scales and dates do not establish equivalent Welsh sampling,
Tryfan semantics, or the value of buying a particular imagery product.

**Next bounded research question, not implemented:** compare a small, stable
steep-rock patch using the retained three-dimensional observations against the
heightfield, explicitly documenting gaps/topology assumptions and its available
photographic evidence. That would test whether retaining multiple heights improves
cliff representation before introducing any inferred surface structure. This Lab
sets no production Atlas architecture requirement and begins no subsequent Lab.

## Reproduce and inspect

From the repository root, use the established external scientific environment.
Alternatively create an external venv from the tracked terrain-research requirements
and Pillow, as described in the acquisition/Lab 012A setup. Recorded versions:
Python 3.12.6, NumPy 2.5.3, rasterio 1.4.3, matplotlib 3.10.6, Pillow 12.3.0.
No new dependency is installed; nearest-neighbour/triangle calculations use NumPy.

```powershell
$labDataRoot = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { (Resolve-Path ..\meridian-data).Path }
$labPython = Join-Path $labDataRoot 'earth-lab\.venv\Scripts\python.exe'
& $labPython scripts/earth_lab/riffelhorn_012b.py
& $labPython scripts/earth_lab/riffelhorn_012b.py --verify
& $labPython -m unittest discover -s scripts/earth_lab -p test_riffelhorn_012b.py -v
$labProject = Join-Path $labDataRoot 'experiments\earth-lab\riffelhorn-012b\observed-mountain-v1\unreal'
$ueCmd = Join-Path ${env:ProgramFiles} 'Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
foreach ($kind in @('dtm','dsm')) {
    & $ueCmd "$labProject\RiffelhornLab012B.uproject" -run=pythonscript "-script=$labProject\Content\Python\setup_$kind.py" -NullRHI -unattended -nop4 -nosplash
    if ($LASTEXITCODE -ne 0) { throw "Import failed: $kind" }
    foreach ($state in @('neutral','rgb')) {
        & $ueCmd "$labProject\RiffelhornLab012B.uproject" -run=pythonscript "-script=$labProject\Content\Python\capture_${kind}_${state}.py" -AllowCommandletRendering -unattended -nop4 -nosplash -d3d11
        if ($LASTEXITCODE -ne 0) { throw "Capture failed: $kind / $state" }
    }
}
& $labPython scripts/earth_lab/riffelhorn_012b.py --validate-captures
```

Run heavyweight Unreal passes sequentially with free RAM/page-file capacity;
do not run production builds concurrently. Generated project/assets/captures live
only under `MERIDIAN_DATA_ROOT/experiments/earth-lab/riffelhorn-012b/observed-mountain-v1/`.
Preparation is deterministic and repeatable but not necessary to view existing
verified products. Open `unreal/RiffelhornLab012B.uproject` in UE 5.8, load
`/Game/Lab012B/dtm` or `/Game/Lab012B/dsm`, use Python `import lab012b`,
`lab012b.view('riffelhorn_structure')`, `lab012b.variant('neutral')` or
`lab012b.variant('rgb')`, then pilot `Lab012B_Camera`. After loading the other map,
apply the same named view. Existing assets need no reimport.

## Validation and limits

All sixteen original and four extracted LAS source hashes pass. Two complete final
preparations produce the same identity and all 209 product hashes. Independent
samples check six source-to-mesh heights and nine unchanged source RGB pixels.
All 28 exported frames pass actual dimensions/nonblank checks, identical camera
poses against manifest positions/targets, material-switch geometry invariance,
128 imported mesh bounds/topology checks and 64 full texture resources per RGB pass.
Compiled external Unreal assets total 1,525,209,712 bytes; their separate inventory
records hashes but does not claim byte-identical Unreal package regeneration.
Original frames total 80,431,663 bytes; attributed derivatives and contact sheets
are separate. Two final native preparations took approximately 73 seconds each;
canonical products total 2,437,254,856 bytes.

All four D3D11 capture processes exit successfully with zero commandlet errors.
The first capture required 364 seconds within the commandlet for initial GPU/shader
preparation; later passes required about 56, 4 and 12 seconds, excluding startup.
Capture peaks reached 7,426 MB resident / 13,294 MB private virtual memory; imports
reached 16,368 MB private virtual memory on this 16 GB machine. Native GPU geometry
allocation was not separately instrumented. Texture resource bytes were measured.
Import emits 64 expected material-less GLB warnings before assigning the Lab
material, plus an Interchange path-length configuration warning. The first RGB
pass retains that path warning; every intended asset/capture validates. Initial
compilation logged FXC/Niagara diagnostics for unused engine debug materials,
with no Lab material failure and a zero-error commandlet summary. D3D12 is not
validated here. Rasterio emits an existing affine deprecation warning; build retains
existing chunk-size/plugin-timing warnings.

All 157 Earth Lab tests, 16 terrain-research tests, ESLint and TypeScript/Vite build
pass. JSON, documentation links, whitespace and scope/privacy checks pass.
Synthetic tests cover centre registration, orientation/winding/scale, UV alignment,
shared seam normals, exact spacing/duplicates and geometric versus vertical distance.

This is a 2.5-D representation experiment, not complete mountain reality. It does
not establish correct undercuts/overhangs, independent absolute positional accuracy,
per-pixel update lineage, semantic object identity, co-temporal texture agreement,
or a general production world model. Source LAS quantization is not measurement
accuracy. Frozen Tryfan/Lab 011/Lab 012A and production Meridian remain unchanged.
No subsequent experiment is implemented.
