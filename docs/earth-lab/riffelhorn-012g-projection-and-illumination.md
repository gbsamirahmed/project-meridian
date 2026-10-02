# Lab 012G — orthophoto projection and baked illumination

Second experiment in the [finite visual programme](riffelhorn-visual-synthesis-and-experiment-design.md).
Starting main: `45d101351d9dbcab29845f73b2364e0be7b3e319`.
Processing/inspection began 2026-10-02; final verification 2026-10-03.
The heightfield-reconstruction branch remains **closed**. No third experiment is
implemented. The latest task explicitly permits one conservative illumination
normalisation, extending the synthesis's original diagnostic-only/no-de-shadowing
scope. This is an experimental appearance proxy, not corrected source albedo.

## Result and programme closure

**Outcome F — source-causal ranking is inconclusive.** Projection loss is directly
quantified, and photographed darkness is a persistent appearance constraint. The
one bounded normalisation is **not accepted** as a readable cliff-appearance
replacement. However, the pre-display audit establishes that positive source
variation reaches the shader and is strongly suppressed by the frozen final
display conversion. A mostly black displayed face is therefore not evidence
that its source texels contain no information. It would be unjustified to select
“observation dominates” solely because this conservative treatment fails in LDR.
The experiment cannot reliably apportion the remaining deficit between baked
illumination, true surface colour, projected information loss and display transfer.

**CONDITIONAL NORMAL EXPERIMENT JUSTIFIED: NO.** Ordinary observed ground retains
source markings and responds to the existing geometric lighting. The remaining
identified discrepancies concern texture-fixed darkness, display transfer,
steep-face sampling and already-known local geometry loss. There is no specific
normal-sampling/normal-normalisation discrepancy on well-observed ordinary terrain
that meets the synthesis's third-slot gate. No RGB-derived, procedural or blanket
LiDAR normals are justified. The finite programme **ends after 012G** and is ready
for synthesis. No extra imagery/lighting Lab or third experiment is begun.

### Measured appearance and sampling

| Fixed image window | Median represented slope | Nominal native elements/surface m², p05 / median | Native tangent footprint, median / p95 |
| --- | ---: | ---: | ---: |
| Alpine ground control | 21.50° | 12.83 / 14.89 | 0.269 / 0.312 m |
| Exact 012F dark face | 63.51° | 0.299 / 7.14 | 0.561 / 13.38 m |
| Steep projection control | 46.64° | 1.54 / 10.98 | 0.364 / 2.59 m |

In the dark-face systematic queries, 55.52% have a surface/horizontal-area factor
over two and 25.00% over five; the ordinary control is 0.80% / zero. Distributed
sample density is always 6.25 times the nominal native-information density; this
does not create independent information. Nominal elements/output pixel have
medians 0.217 on the close ground control, 0.612 in the oblique dark window and
0.065 in the steep control. These view-specific area ratios conceal anisotropy;
the tangent footprint and full density frames expose it separately.

The exact dark window has 2.92% near-black **sampled source** values and no exact
black source texels in those queries. Its source linear luminance p05/median/p95
is 0.00169 / 0.00416 / 0.00976. The image-window and systematic-source fractions
have different sampling/filtering; they are not interchangeable area estimates.

| Exact full-resolution dark window | Encoded luma ≤5 | Linear p95−p05 |
| --- | ---: | ---: |
| Original RGB, no added illumination | 84.00% | 0.002428 |
| Original RGB, frozen L1 NE | 84.00% | 0.002428 |
| Experimental RGB, same L1 NE | 83.41% | 0.002428 |

012F recorded approximately 84.2%; cross-project display dither accounts for the
small difference, with unchanged packages/equation/poses. The native 012G frames
repeat exactly. The correction requests median gain **3.06** at the traced dark
positions; it is not failing because a per-camera brightness setting was omitted.

A [supplementary scalar audit](../../scripts/earth_lab/unreal_riffelhorn_012g_probe.py) reads 12 fixed dark-window pixels and four ground
control pixels in floating-point scene colour **before final LDR conversion**,
using the same geometry, cameras, inputs and material states. No new image state
or tone/exposure adjustment is introduced. At the 12 dark probes:

| Shader scene-colour state | Median linear luminance | p95−p05 |
| --- | ---: | ---: |
| Original unlit | 0.006018 | 0.005128 |
| Original L1 NE | 0.004602 | 0.003031 |
| Experimental L1 NE | 0.013696 | 0.012285 |

These are a small deterministic probe set, not the full-window distribution.
They confirm that the gain reaches the renderer and exposes/amplifies existing
variation before display. They do not establish true albedo, signal-to-noise,
rock identity, or a particular undocumented tone-curve algorithm. The contrast
loss after final conversion is measured; exactly which transfer parameters cause
it remains outside this frozen experiment. Do not call the source empty, silently
change exposure, or increase gain until the face looks attractive.

### Native visual inspection by scale

- **Landscape:** paths, lake/ice and broad ground boundaries remain readable.
  The gain redistributes broad brightness and reduces some ice/ground contrast;
  it adds no accepted ridge/gully-readability gain beyond 012F geometric lighting.
  The large photographed dark patch remains. Source imagery is useful for
  landscape context, without complete face appearance.
- **Intermediate:** the foreground bright ledges become brighter; the main dark
  face remains largely unreadable. Texture-fixed darkness persists under the
  opposed 012F light directions while neutral form changes. This supports a
  photographed-illumination conflict, but is not a perfect albedo/shadow separation.
  Vertical colour bands still run down the unchanged steep facets after gain.
  Ordinary lit slopes remain useful; steep-face appearance is not adequate.
- **Close ground:** the path junction, grass/rock colour boundaries and fine
  photographic markings survive. Undulations respond to the same geometric light.
  Native 25 cm information is larger than the ~6.9 cm target-plane output pixel;
  interpolation cannot supply smaller observed relief or photographic detail.
- **Close steep control:** bright ledges and the small blue source mark persist;
  more blue/grain-like variation is exposed, without an accepted continuous readable
  face. Density shows large surface footprints and the same stretched bands.
  Existing curtains/positional cliff loss remain geometry-related and unchanged.

Source-crop 0.5 m high-pass correlation is 0.9717 (steep), 0.9989 (alpine),
0.9763 (summit transition) and 0.9844 (dark context). Paths/boundaries survive
inspection; correlation alone does not prove semantic or geometric truth. Absolute
grain grows where gain exceeds one; its signal-to-noise is not improved, and the
survey supplies no calibration distinguishing every small marking from noise,
resampling or compression. No manufactured texture is counted as recovery.
Only 0.006061% of source samples encounter the common channel ceiling. All 267
unflagged black anomalies remain black; none is painted over.

## Validation and limitations

All 16 immutable Swiss originals/four LAS, 635 canonical 012A–012F products,
28 historical raw frames and 322 historical 012B packages pass preservation.
The 257 frozen 012F scene copies and its two reused lighting packages also remain
unchanged. All 259 copied inputs pass hashes; all 64 actor/mesh signatures and
four camera poses match their historical fixtures. Original/corrected texture
resources retain 2510² dimensions and identical mip policy/bytes.

The numerical/source/texture pipeline reproduces **113 canonical hashes** and
identity `9e35329cf81527d037d058415f68bd965c96730765976b019e12dfe851cd8042`;
91 source-diagnostic/texture outputs are freshly regenerated. Two independent
Unreal processes reproduce all 16 RGB frames exactly after omitting unused
nondeterministic alpha. The supplementary floating-point probe JSON also repeats
byte-for-byte and is separately hashed in metadata. Canonical products occupy
737,802,829 bytes; each original/corrected full texture set requires 2,150,048,512
GPU-resource bytes. Simultaneously resident sets are a research cost, not Atlas design.

Cold commandlet preparation/capture took 405.20 s, with 5702 MB peak resident /
20,601 MB private virtual memory; warm capture took 19.19 s, 7561 / 15,403 MB.
The cold run has the established Interchange path-length configuration warning;
all final capture/probe passes exit successfully with no errors. No Unreal package
byte-identical fresh reimport claim is made. Performance timings are noncanonical.

192 Earth Lab tests (five new focused controls), 16 terrain-research tests, ESLint
and TypeScript/Vite production build pass. Existing NumPy/rasterio deprecation and
Vite size/timing warnings remain. JSON, documentation-link, whitespace, privacy
and Git scope checks pass; see [validation](riffelhorn-012g-validation.json).
Production, Tryfan, previous Lab implementation and historical refs are unchanged.

The experiment establishes no intrinsic albedo, missing-face completion, exact
optical resolution, per-pixel acquisition ray, microgeometry or co-temporal match.
It does not prove that every more capable illumination/display treatment must
fail. It does establish that this bounded correction is insufficient, projected
sampling deteriorates strongly on steep represented faces, and the frozen final
transfer suppresses some real input variation. Synthesis must keep those three
findings separate. No production change, acquisition or follow-up Lab is made.

## Frozen evidence

Read the [012F report](riffelhorn-012f-terrain-lighting.md), actual native frames and
opposed-light contact sheets before processing. Reuse the compiled 012B
swissSURFACE3D scene in a physical external copy, including its vertex normals,
triangle diagonal, transforms and UVs. No writable hard links, mesh import,
geometry edit, normal enhancement, new imagery or production integration.

AOI EPSG:2056 `[2624000,1091000,2626000,1093000]`, 4 km². Heights remain LN02
metres; local origin northwest `(2624000,1093000)`, vertical offset 2500 m,
east/south/up axes, 100 Unreal cm/m. The 64 chunks retain 16,000,000 unique
vertices and 31,984,002 triangles, without simplification or exaggeration.
Sources retain the [acquisition provenance and terms](../atlas/riffelhorn-data-discovery.md):
2021/2022 LiDAR, derived surface raster, 2023 SWISSIMAGE mosaic; not co-temporal.
Exact image flight rays, per-pixel dates, seamlines and intrinsic albedo are unknown.
Attribution: **© swisstopo**. All sources and large products remain external.

SWISSIMAGE has **25 cm native information resolution**, distributed/rendered on
the official 10 cm grid. Both original and experimental textures use 64 × 2510²
samples, unchanged apron/UV registration, sRGB, trilinear filtering, simple-average
mips, LOD bias zero and full-size resident resources. Interpolation/mipmaps do
not recover additional observed information.

## Benchmark and independent controls

Exact existing position/target arrays are retained in [metadata](riffelhorn-012g-metadata.json):
`overview` (4600 m target distance), `riffelhorn_oblique` (488.36 m), `alpine_path`
(141.51 m), `riffelhorn_structure` (156.20 m projection control). Target-plane
sampling is approximately 2.234/0.237/0.069/0.076 m/output pixel respectively;
oblique surface footprints vary.

50° horizontal FOV, 1920×1080, identical cameras, exposure/tone transfer, no
atmosphere, bloom, motion blur or anti-aliasing. Use 012F's compiled L1 northeast
material unchanged: `C × (0.35 + 0.65 max(n·l,0))`,
`l=(0.4,-0.3,0.8660254)` in east/south/up axes, azimuth 53.1301°, elevation 60°.
No new shadow test or lighting adjustment; 012F close shadow-map mottling was not
accepted. Opposite-direction photographic conflicts reuse its immutable frames.

Four states × four cameras = **16 native frames**:

1. `original_unlit`: RGB only, removing added illumination but retaining the
   common display transfer; not an exposure correction.
2. `original_lit`: original RGB under the frozen L1 northeast control.
3. `normalised_lit`: experimental RGB under exactly the same L1 control.
4. `density`: continuous red-to-green diagnostic from actual triangle orientation;
   red means greater stretching, green horizontal. This measurement material is
   not photographic appearance or a replacement shading-normal representation.

## Source and projection audit

Use the existing 012F image windows and exact dark-face box
`[1150,800,1500,1020]` in `riffelhorn_oblique`; projection-control box
`[500,350,1450,1000]`. Trace their pixel centres at 8-pixel stride to the **first
exact intersection** with the unchanged 012B triangles using XY grid traversal.
Whole-view sampling uses 16-pixel stride. No bilinear-height ray approximation.
Store source texel coordinates, hit positions and triangle gradients externally.
Independently compare selected tiled RGB values with original COG pixels.
These systematic queries are diagnostics, not unbiased area-population estimates.

Native-sample source crops: 60 m steep-face and alpine controls from 012B; 150 m
summit illuminated/shadow transition; 150 m dark-face context enclosing the exact
image-window traces. Rows run north to south, columns west to east. Coordinates,
contrast and source-information preservation are in
[measurements](riffelhorn-012g-measurements.json).

For a triangle inclined by θ, surface area is horizontal area divided by
`cos(θ)`. Thus the nominal information density is `16 cos(θ)` elements/m² of
surface; distributed samples are `100 cos(θ)`/m². The nominal native footprint
along steepest tangent is `0.25/cos(θ)` m. Examples:

| Slope | Nominal native density / surface m² | Steepest-tangent footprint |
| --- | ---: | ---: |
| 0° | 16.00 | 0.25 m |
| 60° | 8.00 | 0.50 m |
| 80° | 2.78 | 1.44 m |
| 89° | 0.28 | 14.32 m |

This ideal horizontal-mapping model describes the actual UV/surface area change,
not original camera visibility, occlusion, optical MTF or independent measurement
accuracy. It becomes singular at a vertical face. Existing raster curtains are
also part of the represented slope. Complete XY coverage does not establish face
observation. Perspective area Jacobians give nominal source elements/output pixel;
these are footprint estimates, not measured GPU mip choices or optical sharpness.

## One bounded normalisation

[Processing code](../../scripts/earth_lab/riffelhorn_012g.py) decodes sRGB into linear
RGB; forms 2 m block-mean Rec.709 luminance; applies one separable Gaussian with
σ=30 m, ±90 m support, edge replication. This coarse field **L** is only a
low-frequency illumination proxy. It mixes illumination with real surface colour.

```text
g = clip(sqrt(median(L) / max(L, 1e-6)), 0.5, 4)
Cexperimental = Csource × min(g, 1/max(Csource))
```

Evaluate the common gain field bilinearly at original 10 cm sample centres.
The square root partially redistributes broad brightness, rather than flattening
everything to grey. The two-stop brightening cap prevents division-driven extreme
amplification; the common RGB channel ceiling prevents clipping/chromaticity loss.
Encode by the standard sRGB transfer with nearest-integer quantisation.
No sharpening, retouching, local-content enhancement, semantic mask, texture fill
or intrinsic-image decomposition. The 267 exact-black anomalies stay exact black.
Tile aprons must agree exactly. The 2 m estimator grid is not a replacement texture
or source-resolution claim. Parameters apply to the whole AOI, not individual
cameras; no post-result gain/scale sweep.

Quantify source luminance/range, encoded near-black fraction (Rec.709 luma ≤5),
gradients, 0.5 m high-pass correlation, clipping and visible boundaries. High-pass
analysis is a diagnostic only: the textures are never high-pass filtered. Increased
absolute variation does not prove increased information or independently observed
fine relief. Source noise/compression/resampling effects cannot all be separated.

## Reproduce and inspect

Existing products need not be rebuilt for viewing. Use the scientific environment
from [Earth Lab setup](../../scripts/earth_lab/README.md), with no new dependency:

```powershell
$labDataRoot = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { (Resolve-Path ..\meridian-data).Path }
$labPython = Join-Path $labDataRoot 'earth-lab\.venv\Scripts\python.exe'
& $labPython scripts/earth_lab/riffelhorn_012g.py audit
& $labPython scripts/earth_lab/riffelhorn_012g.py prepare
$labProject = Join-Path $labDataRoot 'experiments\earth-lab\riffelhorn-012g\projection-illumination-v1\unreal'
$ueCmd = Join-Path ${env:ProgramFiles} 'Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
foreach ($run in @('first','repeat')) {
    & $ueCmd "$labProject\RiffelhornLab012G.uproject" -run=pythonscript "-script=$labProject\Content\Python\capture_$run.py" -AllowCommandletRendering -unattended -nop4 -nosplash -d3d11
    if ($LASTEXITCODE -ne 0) { throw "Capture failed: $run" }
}
& $labPython scripts/earth_lab/riffelhorn_012g.py analyse
& $labPython scripts/earth_lab/riffelhorn_012g.py verify
# Optional full numerical/texture repetition; reuses already repeated captures:
& $labPython scripts/earth_lab/riffelhorn_012g.py reproduce
& $labPython -m unittest discover -s scripts/earth_lab -p test_riffelhorn_012g.py -v
```

To repeat the separate pre-display scalar audit without changing any benchmark
frame, run the same project with the tracked probe script:

```powershell
$probeScript = Join-Path (Get-Location).Path 'scripts\earth_lab\unreal_riffelhorn_012g_probe.py'
foreach ($run in @('first','repeat')) {
    $env:MERIDIAN_012G_PROBE_RUN = $run
    & $ueCmd "$labProject\RiffelhornLab012G.uproject" -run=pythonscript "-script=$probeScript" -AllowCommandletRendering -unattended -nop4 -nosplash -d3d11
    if ($LASTEXITCODE -ne 0) { throw "Probe failed: $run" }
}
Remove-Item Env:\MERIDIAN_012G_PROBE_RUN
```

Generated root:
`MERIDIAN_DATA_ROOT/experiments/earth-lab/riffelhorn-012g/projection-illumination-v1/`.
Inspect `comparisons/` for navigation, then `captures/first/` at 100%, alongside
`*-source-comparison.png`. Density colours pass through the same display transfer;
use quantitative metadata rather than reading their RGB as calibrated numbers.

For manual switching, open the external `.uproject`, then its Python console:

```python
import unreal, sys
sys.path.insert(0, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()+'Python'))
import lab012g
unreal.EditorLoadingAndSavingUtils.load_map('/Game/Lab012B/dsm')
lab012g.view('riffelhorn_oblique')  # also overview, alpine_path, riffelhorn_structure
lab012g.variant('original_lit')    # also original_unlit, normalised_lit, density
```

Pilot `Lab012B_Camera`; do not move it between states. Heavy passes run sequentially.
Only this generated project is opened; prior projects and Tryfan remain immutable.
