# Lab 012F — terrain lighting and readability

2026-10-02. Starting main: `00395605ed046ff2f16f427b4d10ed6be2d55ee4`.
Contract: [finite visual programme](riffelhorn-visual-synthesis-and-experiment-design.md).
This is its first experiment. The heightfield-reconstruction branch remains
**closed**; the projection/baked-illumination experiment is **not begun**.

## Result

**Outcome B — lighting helps but source imagery limits it.** Stronger directional
response communicates existing ridges, channels, shoulders and ledges more clearly.
This survives the landscape and mountain-face views and both azimuth controls,
although individual faces benefit differently. It does not repair the large
photographically dark face, stretched steep-face colour or local raster curtains.
Neutral geometry improves much more consistently than RGB appearance.

The 0.35 ambient / 0.65 directional treatment is a useful research control, not
an accepted production lighting specification. The cast-shadow variant exposes
additional relief but has direction-dependent darkening and close-range shadow-map
mottling. It is not accepted as a universal enhancement. No fraction of the entire
visual deficit can honestly be assigned a single numerical percentage: illumination
explains faint neutral relief, while source appearance still dominates dark faces.

## Frozen evidence and benchmark

Use the actual compiled [012B](riffelhorn-012b-mountain-reconstruction.md)
swissSURFACE3D scene, physically copied into a separate external Unreal project.
No import, re-meshing, vertex/normal/UV edit, simplification, LOD or exaggeration.
No writable hard links. Both old and copied asset hashes are checked.

- AOI: EPSG:2056 `[2624000,1091000,2626000,1093000]`, 4 km²; LN02 metres.
- Native surface: 0.5 m grid, 16,000,000 unique vertices, 31,984,002 triangles,
  64 chunks; 16,056,049 submitted vertices including existing shared borders.
- SWISSIMAGE: **25 cm native information**, official 10 cm distributed sampling;
  unchanged 64 × 2510² RGB textures, sRGB decoding, trilinear filtering,
  simple-average mipmaps, LOD bias zero, full-size resident resources.
- Local coordinates: east, south, up; LV95 origin `(2624000,1093000)`, LN02
  height offset 2500 m, 100 Unreal cm per metre. No coordinate change.
- D3D11, UE 5.8.2; 50° horizontal FOV, 1920×1080, 0.1 m near clip,
  unchanged far behaviour, tone treatment and disabled exposure adaptation.
  Atmosphere, bloom, motion blur and anti-aliasing remain absent/disabled.

Exact arrays and historical poses are retained in [metadata](riffelhorn-012f-metadata.json).

| Camera | Position m | Target m | Target distance / pixel footprint |
| --- | --- | --- | --- |
| `overview` | `[1000,1000,4600]` | `[1000,1000,0]` | 4600 m / 2.2344 m |
| `riffelhorn_oblique` | `[1030,398,690.280029296875]` | `[810,748,430.280029296875]` | 488.36 m / 0.2372 m |
| `alpine_path` | `[1310,580,346.282470703125]` | `[1240,470,291.282470703125]` | 141.51 m / 0.0687 m |

These are landscape, intermediate and close controls respectively; footprint is
at the target plane, not constant across an oblique frame. The separate historical
`riffelhorn_structure` projection control is retained unchanged for the second
experiment. The oblique frame already exposes steep-face colour stretching, so
no extra projection-camera sweep is needed here.

## Illumination-only design

Let `C` be unchanged linear-decoded orthophoto colour, or fixed neutral RGB
`(0.5,0.5,0.5)`; `n` is the existing imported geometric normal. Use the original
unlit/emissive material path and unchanged display transfer to isolate illumination.
This is conventional diffuse directional-plus-ambient shading, not a calibrated
PBR/albedo, sun/skylight or global-illumination model.

```text
L0 baseline:    C × (0.65 + 0.35 × max(n·l_NE,0))
L1 directional:C × (0.35 + 0.65 × max(n·l,0))
L2 visibility: C × (0.35 + 0.65 × max(n·l,0) × V)
```

| Direction towards light | Unreal east/south/up vector | Azimuth clockwise from north | Elevation |
| --- | --- | --- | --- |
| Northeast | `(0.4,-0.3,0.8660254)` | 53.1301° | 60° |
| Southwest | `(-0.4,0.3,0.8660254)` | 233.1301° | 60° |

Northeast reproduces the original direction. Its opposite horizontal azimuth
tests whether a gain depends on flattering one face, with elevation/peak unchanged.
These are readability controls, not a claim about the orthophoto's acquisition sun.
One ambient/lighting equation applies to every camera; no camera-specific tuning.

Five conditions (`baseline`, L1 NE, L2 NE, L1 SW, L2 SW) × three cameras ×
neutral/RGB = **30 native frames**, plus six navigation contact sheets. This extends
the synthesis's 18-frame single-direction matrix only by the explicitly requested
two-direction robustness control; no parameter sweep or extra views.

### Cast/self-shadow control

L2 captures the unchanged opaque scene into one 4096² float32 light-space depth
target per direction, then applies ordinary depth visibility only to the directional
term. Orthographic light camera: 5 km from the AOI bounding-box centre; width about
2838.51 m, 20 m margin; light-plane texel about **0.693 m**. No new height/normal map.
Use actor right/up/forward axes for projection, a 3×3 uniform PCF comparison and
receiver bias in cm `15 + 0.5*shadow_texel_cm*(1-max(n·l,0))`. Ambient remains 0.35.
Depth capture precedes depth-reading material assignment; no feedback loop.

The shadow target is a renderer sampling constraint, not 0.693 m source information.
Its close-range mottling/stepping is visible, especially under SW illumination on
alpine ground. This bounded test does not become a shadow-resolution/bias sweep.
No AO, atmosphere, extra fill lights or synthetic normal enhancement is added.

## Baseline and reproduction

The six baselines use the byte-identical copied historical materials, textures and
meshes, exact poses and equation. Historical PNG RGB is **not pixel-identical**:
Unreal's display-quantisation dither pattern differs. Signed encoded mean difference
is below 0.0011 levels; 8×8 block mean absolute differences are 0.078–0.326 levels,
maximum 2.125 levels. Pointwise maxima reach 12 in neutral and 21 in RGB dark pixels.
Neutral foreground coverage is identical. This is recorded explicitly rather than
claiming byte-identical historical captures or disabling their display treatment.
Block averaging is an audit only; published native frames are not filtered.

Two independent final Unreal processes reproduce all **30 decoded RGB arrays
exactly**. UE LDR export's unused alpha is nondeterministic. Canonical output stores
the exact decoded RGB pixels, with PNG `Attribution: © swisstopo`; all 30 canonical
PNG hashes then match. This changes no visible pixel, exposure or source texture.

## Geometric and image-space controls

Seven image windows were fixed from historical neutral/RGB frames before testing:
overview mountain relief and alpine channels; oblique ridge face, foreground
shoulder and photographed dark face; close ground undulation and convex protrusion.
Bounds and complete metrics are in [measurements](riffelhorn-012f-measurements.json).
These are supporting diagnostics, not a universal readability score.

Read-only cell-centre profiles independently confirm form in the same native DSM:
summit east/west section at N1092252.25 spans 60.82 m vertically; alpine east/west
section at N1092530.25 spans 11.24 m; northern channel context at E2625100.25 spans
11.90 m. Endpoints and native heights are retained externally. The summit profile's
33.06 m adjacent jump is an existing raster discontinuity, not new lighting detail.
Neutral frames establish ridge/channel and shoulder identities; RGB never defines
whether a mark is measured relief. These profiles do not certify every photographic
fracture or revisit raw cliff reconstruction.

Convert PNG sRGB to linear Rec.709 luminance for ranges/gradients. Count dark pixels
separately at encoded luminance ≤5; highlight diagnostic is any channel ≥250.
Window results include their fixed contents; e.g. the ridge window has a small
silhouette/background strip. Snow, ice, water and tile-cut edges are not acceptance
structures; they remain visible in the full-AOI context.

| Neutral window | L0 p95−p05 | L1 NE | L2 NE | L1 SW | L2 SW |
| --- | ---: | ---: | ---: | ---: | ---: |
| Overview mountain relief | 0.1009 | 0.2384 | 0.2217 | 0.1437 | 0.2180 |
| Overview alpine channels | 0.0950 | 0.2160 | 0.2183 | 0.1371 | 0.2109 |
| Oblique ridge face | 0.0637 | 0.0963 | 0.1843 | 0.2105 | 0.1778 |
| Close ground undulation | 0.0785 | 0.1263 | 0.1158 | 0.0614 | 0.1336 |

Landscape neutral contrast increases under both azimuths. The close ground response
does **not** improve monotonically: L1 SW compresses that window, while L2 SW adds
aliasing along with contrast. Larger gradient/range alone is therefore not acceptance.
No tested window has a channel reaching 250. RGB dark-face window remains about
**84.2%** at luminance ≤5 in all five conditions; its linear range stays about 0.0024
despite neutral geometric range increasing from 0.0919 to as much as 0.2518.

## Actual visual inspection

Inspected the six contact sheets and native 1920×1080 baseline/directional/shadow
frames, including both azimuths, overview relief, oblique foreground/summit and close
alpine ground. Contacts are five-times-reduced navigation aids, not the acceptance
resolution. Results below separate observation from explanation.

| Scale | OBSERVATION | INTERPRETATION / established limits |
| --- | --- | --- |
| Landscape | Major ridge branches and northern channels separate better in neutral L1 under both directions; L2 introduces broad occlusion that reinforces some ridge/gully relationships. RGB gain is smaller, but shallow ground relief becomes more readable outside photographed dark regions. | High ambient was compressing existing form. Cast visibility adds information beyond local normal shading, but source photographic contrast competes. No geometry was added. |
| Intermediate | Summit-face grooves and convex shoulders become easier to follow. SW makes the large foreground ledges much more distinct in neutral shading. RGB foreground face remains largely black; SW additionally darkens portions of the summit that were photographically illuminated. | Geometry can communicate more than the baseline showed. Multiplication cannot recover obscured reflectance. Competing baked and rendered illumination prevents a single reliable RGB treatment. |
| Close | NE directional response clarifies shallow alpine undulation and the upper-right protrusion. SW directional response helps some facing surfaces but weakens others. Cast shadows create conspicuous mottled/stepped shading on ground; RGB retains paths and boundaries but gains little comparable geometric richness. | Direction sensitivity and shadow-map sampling matter. Reject mottling as false-looking apparent fine structure. Source imagery, output sampling and known raster form limits remain independent. |
| Steep foreground faces | Vertical colour bands and curtain-like shapes persist in the oblique RGB comparisons. Neutral ledges are clearer, but their positions/silhouette do not change. | Lighting neither corrects orthophoto projection nor restores lost cliff shape. Heightfield branch remains closed. |

### Baked photographic illumination conflict

- **L0 NE:** original relatively mild multiplication; dark foreground already
  concealed. Exact source light direction remains unknown, so this is not proof
  of physically aligned acquisition illumination.
- **L1 NE:** partially compatible on photographed light-facing rock/ground, but
  dark face remains obscured. Reduced ambient does not expose hidden colour.
- **L2 NE:** additional dark pockets around terrain breaks stack with photographed
  darkness. Some occlusion is useful in neutral, but is harder to interpret in RGB.
- **L1 SW:** strongest visual contradiction in the oblique pair: neutral foreground
  ledges face the light while their draped appearance remains black; portions of
  the previously bright summit become darker. This is a plausible competing-shadow
  effect, not a recovered photographic sun azimuth.
- **L2 SW:** further darkening compounds the conflict and close shadow aliasing.
  No camera-specific exposure compensation or de-shadowing is used.

Thus there is partial conflict under NE and strong apparent conflict under SW in
the key oblique view. Some dark pixels could also reflect material/projection
limits; not every dark pixel is classified as a shadow. The 267 black source
anomalies remain untouched and do not explain this extensive face.

## Cost, provenance and validation

Scene copy: 257 unchanged compiled packages, 1,097,816,955 bytes. No fresh terrain
generation/import. Existing RGB GPU resources total 2,150,048,512 bytes. Two 4096²
R32F depth targets require 134,217,728 nominal bytes; each RGB output target requires
8,294,400 bytes, allocated per capture (up to 248,832,000 transient bytes before
garbage collection across 30 frames). These are resource sizes, not a whole-engine
GPU-memory measurement or performance target. There are 39 canonical products
(30 frames, six contacts, measurements, validation and form controls), 70.67 MB.
The complete local estate including the copied project and repeat frames is about
1.24 GB. Cached capture passes took 17.51 / 17.00 s, excluding editor startup;
the final commandlet reported peak physical/virtual memory 7303 / 14102 MB.
Timings and hashes are in metadata/validation. First cold shader setup
was considerably slower than cached passes; no geometry was simplified to fit.

Validation checks immutable Swiss originals/extracted LAS; all **596** canonical
012A–012E products; 28 recorded historical raw frames; 322 historical Unreal
packages; 257 copied packages; exact geometry/texture resources and camera poses;
baseline equivalence; fixed dimensions/exposure/atmosphere; shadows never increasing
directional brightness; foreground coverage; two-process RGB and canonical PNG
reproducibility. Focused tests cover axes, illumination, light-space projection,
linear luminance and rejection of a changed baseline. Earth Lab and terrain-research
tests, ESLint, TypeScript/production build, JSON/link/privacy and diff checks pass.
Existing deprecation and build size/timing warnings remain.

See [identity and products](riffelhorn-012f-metadata.json),
[quantitative diagnostics](riffelhorn-012f-measurements.json),
[validation](riffelhorn-012f-validation.json),
[preparation/analysis](../../scripts/earth_lab/riffelhorn_012f.py) and
[Unreal adapter](../../scripts/earth_lab/unreal_riffelhorn_012f.py).

## Reproduce / inspect

Existing products suffice for inspection; do not rebuild previous Labs.
From the repository root, use the established external scientific environment:

```powershell
$data = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { [IO.Path]::GetFullPath('..\meridian-data') }
$python = Join-Path $data 'earth-lab\.venv\Scripts\python.exe'
$lab = Join-Path $data 'experiments\earth-lab\riffelhorn-012f\terrain-lighting-v1'
# Open overview contact, then individual native frames at 100%.
Invoke-Item "$lab\comparisons\overview-neutral.png"
Invoke-Item "$lab\captures\first\riffelhorn_oblique-rgb-baseline.png"
Invoke-Item "$lab\captures\first\riffelhorn_oblique-rgb-directional_southwest.png"
Invoke-Item "$lab\captures\first\alpine_path-neutral-shadow_southwest.png"
```

Contacts are named `<view>-<neutral|rgb>.png`; native frames are
`<view>-<neutral|rgb>-<condition>.png`. Compare identical views at 100%, first neutral
then RGB. Inspect ridge/channel separation, foreground ledges, the black face and
close shadow mottling; do not judge only a reduced contact.

For full reproduction (existing UE 5.8, substantial RAM/GPU resources):

```powershell
& $python scripts/earth_lab/riffelhorn_012f.py
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
$project = Join-Path $lab 'unreal'
$editor = Join-Path $env:ProgramFiles 'Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
foreach ($run in @('first','repeat')) {
  & $editor "$project\RiffelhornLab012F.uproject" -run=pythonscript "-script=$project\Content\Python\capture_$run.py" -AllowCommandletRendering -unattended -nop4 -nosplash -d3d11 "-abslog=$project\$run.log"
  if ($LASTEXITCODE -ne 0) { throw 'Capture failed' }
}
& $python scripts/earth_lab/riffelhorn_012f.py --analyse
& $python -m unittest discover -s scripts/earth_lab -p 'test_riffelhorn_012f.py'
```

The adapter refuses any other project. Baseline is reversible by assigning the
copied old materials; all dynamic candidate assignments are transient. Reloading
the copied DSM map restores its saved state. Do not save over historical projects.

## Carry forward, then stop

Carry the neutral/RGB paired evidence, fixed windows and NE/SW controls into the
already-planned projection/baked-illumination experiment. It should separate absent
face observation, source darkness and renderer shadow conflict, using the same
frozen geometry. Lighting is a significant communication variable, but not a remedy
for missing albedo/steep-face evidence. No new normal/detail slot is automatically
justified by this result; shadow aliasing is not evidence of missing terrain normals.

This Lab establishes no permanent Atlas shader, terrain architecture or production
integration. Tryfan, production Meridian, previous Lab implementations, immutable
Swiss data and historical refs are unchanged. No new source acquisition, normal
map, material classification, imagery correction or geometry reconstruction.
**Lab 012F stops here. Experiment 2 is not implemented.**
