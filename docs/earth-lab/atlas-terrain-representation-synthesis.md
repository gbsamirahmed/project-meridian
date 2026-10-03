# Atlas terrain representation research synthesis

2026-10-03. Final durable handoff for the **closed 012A–012G research epoch**.
Evidence checkpoint: `abf95bcfb50c681244a146626565a471ba791418`.
Read with the [architecture contract](../architecture.md),
[research map/onboarding](../research/atlas-research-map.md) and
[terrain literature record](../research/literature/terrain-representation.md).
This is documentation and research closure, not a new Lab, phase or Atlas design.

## Executive conclusion

**MERIDIAN EVIDENCE:** strong ordinary terrain geometry is already present.
High-resolution imagery supplies important appearance but cannot repair missing
geometry or guarantee observation of steep faces. Coherent cliff shape can be
altered by rasterisation; the tested finer/adaptive and orientation-aware surfaces
did not provide a stable, supported replacement. Terrain illumination improves
communication of existing form. Projection stretching remains measurable, and
final display conversion conceals some source variation. No satisfactory close
steep-face appearance or defensible overhang requirement was established.

The Riffelhorn heightfield branch and finite visual programme are **closed**.
012E and 012G were inconclusive about causal attribution, not devoid of findings.
Do not mistake their failed acceptance for proof that all established techniques
in the relevant scientific fields fail.

**EXTERNAL EVIDENCE:** topographic correction, inverse rendering, visibility-aware
texturing, cartographic shading, terrain generalisation and geospatial streaming
are established fields. The [literature record](../research/literature/terrain-representation.md)
documents methods and limits rather than translating them into implementation orders.

**RESEARCH DIRECTION:** return to deliberate Atlas design/planning with geometry,
observation quality, appearance and rendering separated, and viewing scale explicit.
No next architecture, dataset acquisition or experiment is selected here.

## Source evidence and scope

| Site / source | What was retained | Limitation that must travel with it |
| --- | --- | --- |
| Bluesky SK5639 sample, EPSG:27700 [456000,339000,457000,340000] | 1 km², 25 cm photogrammetric DSM; 25/12.5/5 cm RGB, verified numerical registration | Only 5 cm image supplies 2018-09-01 flight metadata. Other dates and absolute DSM vertical datum unresolved. Evaluation rights do not establish redistribution/public display rights. |
| Riffelhorn/Riffelsee, EPSG:2056 [2624000,1091000,2626000,1093000] | 4 km²; LV95 horizontal, LN02 metre heights; 2021/2022 classified LiDAR; 0.5 m provider DSM/DTM grids; 2023 SWISSIMAGE | 0.5 m grid is a derived representation, not independent measurements. RGB has 25 cm native information on a 10 cm distributed grid. |
| Tryfan, EPSG:27700 [264900,357800,267900,360800] | 9 km²; Welsh Government matching 2021-03-02 1 m DTM/DSM; retained Sentinel observations; historical inferred/reconstructed controls | No spatially verified finer NRW replacement was found. Swiss scales/thresholds and sample-city results do not automatically transfer. |

Riffelhorn uses tiles 2624-1091, 2624-1092, 2625-1091, 2625-1092. Its measured
DTM range is approximately 2189.6–2977.8 m LN02. Raw LiDAR dates are August 24/26
2021, with northeast August 23 2022 returns. SWISSIMAGE is a 2023 mosaic; September
7 is only a plausible source flight, not a per-pixel date. swissALTI3D's 2024 release
combines the LiDAR base and 2023 photogrammetric updates. Snow/ice, water, vegetation,
debris, erosion and infrastructure disagreement may be temporal. DSM−DTM is not
object height, rock or vegetation semantics. See the exact
[acquisition report](../atlas/riffelhorn-data-discovery.md) and
[asset catalogue](../atlas/riffelhorn-data-catalog.json) for file hashes, acquisition
lineage, datums, source accuracy claims and official terms. Standard Swiss outputs
retain **© swisstopo**; Bluesky evaluation captures are not cleared for publication.

Tryfan context remains in [source reconnaissance](../atlas/tryfan-lidar-reconnaissance.md),
[catalogue](../atlas/tryfan-data-catalog.json),
[Lab 010](tryfan-010-observed-natural-colour.md) and
[Lab 011](tryfan-011-observed-surface-height.md). Lab 010 showed useful large-scale
10 m observed colour, not sub-pixel reconstruction. Lab 011 found coherent residuals
at 3–20 m scales strongly entangled with slope/classification. It motivated better
observational evidence, not semantic classification or an architectural phase.

## Experimental sequence

Each linked report retains its original knowledge and proposed next step.
Later closure decisions below govern the current handoff. Metadata, measurements
and validation JSON sit beside each report; scripts are under `scripts/earth_lab`.
This section records **MERIDIAN EVIDENCE**, not externally established capability.

| Experiment / checkpoint | Controlled question and result | What it does not establish |
| --- | --- | --- |
| [012A — aerial reconstruction](bluesky-012a-aerial-reconstruction.md), `3412738` | Fixed 25 cm DSM: 16M unique vertices / 31,984,002 triangles. Native RGB at 25/12.5/5 cm yields 16/64/400 pixels/m²; 5 cm 20k source preserved through 64 native tiles. Finer supplied imagery exposes roof, road and crown appearance at close range; geometry remains fixed. | Resolution-only causal improvement is confounded by acquisitions/shadows. Finer RGB does not repair walls/crowns or validate Tryfan rock structure. No purchasing or licensing conclusion. |
| [012B — mountain reconstruction](riffelhorn-012b-mountain-reconstruction.md), `eb1cca1` | Whole 4 km² terrain and surface meshes each retain 16M unique vertices / 31,984,002 triangles / 64 chunks, no simplification/LOD/exaggeration. Broad form, ledges and ground undulation survive; RGB adds paths/boundaries/fine marks. Cliff curtains and stretched colour remain local limits. | No universal geometry resolution or co-temporal source stack. DSM−DTM median 0.0039 m, mean 3.994 m is dominated by southern ice/debris differences; not a semantic height field. |
| [012C — raw retention](riffelhorn-012c-raw-lidar-retention.md), `a33e793` | Three patches: ordinary control distance median/p95 0.017/0.053 m; rough ground 0.025/0.116 m; summit cliff 0.060/1.109 m, max 6.613 m. Nineteen coherent 2 m-context geometry candidates and lower-face bands identify local metre-to-several-metre loss. | Nine multiple-height screens remain ambiguous. No defensible overhang/non-heightfield requirement. Raw/rendered-normal medians at 1 m radius 4.18° cliff, 1.22° control, 1.48° rough; blanket detail normals unjustified. |
| [012D — adaptive heightfield](riffelhorn-012d-adaptive-cliff-heightfield.md), `44dc05d` | Frozen 2 m blocks with 0.2 m buffer: construction/held-out/buffer 28,866/11,179/5,011; 9,652 interior held-out. Finer/adaptive sampling of construction-only interpolation lowers parts of the extreme tail but worsens overall held-out fit and leaves holes/bridges/strips. **Outcome E.** | Excellent construction fit is not generalisation. No accepted surface, saturation point, classical overfit onset, adaptive preference or true-3D need. Provider benchmark had access to withheld returns. |
| [012E — robust estimation](riffelhorn-012e-robust-cliff-heightfield.md), `d01218f` | Same patch/split/baseline. Construction-only reliable 1/2 m PCA planes constrain robust scalar-height voting. Held-out median/p95 0.521/3.555 m; only 21.20% query XY represented. Two supported positions improve, but fragmentation and full-survey gaps prevent an accepted continuous face. **Outcome F; branch closed.** | Refused nodes do not prove absent local measurements; measured planes do not uniquely constrain intervening surface. Mixed estimator/support limits remain. No defensible topology verdict or evidence-backed next interpolator. |
| [012F — lighting](riffelhorn-012f-terrain-lighting.md), `45d1013` | Frozen whole mountain/cameras; baseline ambient/directional 0.65/0.35 versus 0.35/0.65, NE/SW azimuth controls and bounded terrain cast visibility. Ridges/channels/shoulders/ledges become clearer, more in neutral than RGB. Dark face remains ~84.2% near-black, opposing light conflicts. **Outcome B.** | No geometry recovery or production light choice. Close shadow-map mottling, direction dependence and extra darkening reject cast shadows as a blanket improvement. Not a comprehensive cartographic lighting evaluation. |
| [012G — projection/illumination](riffelhorn-012g-projection-and-illumination.md), `abf95bc` | Same geometry, imagery and four cameras. `16 cos(slope)` native-information-density accounting independently demonstrates severe projection stretching. One bounded low-frequency gain leaves final dark region 84.00→83.41% near-black. HDR probes prove positive upstream variation/gain survives to scene colour; final display suppresses some of it. **Outcome F; conditional normals NO; programme closed.** | No intrinsic albedo, exact source flight ray, usable geological identity/SNR or dominant-cause ranking. Rejected gain is not evidence against physical topographic correction/inverse rendering. |

Raw Riffelhorn returns number **50,546,426**, averaging 12.64 per horizontal m²;
5.51% of horizontal 0.5 m cells have no return. Sampled neighbour spacing around
0.153–0.215 m is not isotropic independent resolution, accuracy or face visibility.
Grid completeness includes provider interpolation. Class 2 can contain boulders.

Frozen 012D/E held-out geometric distances (metres):

| Representation | Median | p95 | p99 |
| --- | ---: | ---: | ---: |
| Provider 0.5 m | 0.056 | 0.842 | 2.832 |
| Raw-derived 0.5 m | 0.243 | 2.610 | 4.562 |
| Regular 0.25 m | 0.219 | 1.842 | 3.211 |
| Regular 0.125 m | 0.210 | 1.448 | 2.253 |
| Adaptive 0.5→0.25 m | 0.234 | 1.891 | 3.178 |
| Robust plane 0.125 m | 0.521 | 3.555 | 8.057 |

Distances use exact point-to-triangle projection, not nearest-cell vertical errors.
Missing regions can yield distances to hole edges; represented-XY cohorts and
finite-patch boundary differences are reported in the historical measurements.
012D's finest construction median ~0.019 m does not validate its 0.210 m held-out
median. A lower tail alone cannot accept an unstable/unsupported completed surface.
The provider remains a privileged reference using the full observations. One
spatial split and deterministic query screens are not an unbiased population study.

## What is established and what remains local

Ordinary control geometry and most rough-ground form are strongly retained in the
sampled areas. Coherent cliff position/shape can be lost near steep discontinuities;
normals cannot correct positional or silhouette errors. This is localized, not a
reason to rebuild all terrain or add blanket high-frequency detail.

At 60/180 m, cliff point/mesh differences are visible, but point-only overlays are
not completed-surface perceptual ground truth. At ~600 m most projected displacement
is sub-pixel; some extreme tails survive. Rejected D/E holes remain visible but do
not constitute useful recovery. No universal threshold or user study is claimed.

Whole-mountain appearance has distinct limits. 012F improves actual ridge/gully
readability without moving vertices; RGB contributes fine colour marks that need
not have measured relief. The orthophoto is useful at landscape scale and across
ordinary slopes, yet satisfactory close steep-face appearance remains unestablished.
Dark photographic regions, projection, source temporal mismatch and display
sampling must not all be assigned to the known local geometry defect.

012G dark-window queries had median slope 63.51° and nominal native density
7.14/m²; fifth-percentile density 0.299/m² and 95th-percentile steepest-tangent
footprint 13.38 m. These derive from represented triangle orientation, not actual
flight visibility, optical sharpness or an independently calibrated accuracy model.
Occlusion and source orthorectification can add limits beyond the ideal projection.

The full displayed dark ROI and systematic source samples are different populations:
84.00% rendered near-black versus 2.92% sampled source near-black cannot be compared
as identical footprints. Twelve fixed HDR probes show median linear luminance
0.006018 unlit, 0.004602 lit and 0.013696 corrected-lit. This establishes upstream
signal and suppression by final conversion, not a complete tone-curve diagnosis,
physical reflectance recovery or usability of every dark speck.

## Closed / do not reopen without new evidence

| Branch | Current closure and required distinction |
| --- | --- |
| Riffelhorn heightfield reconstruction | Closed after 012E. Further interpolation/refinement of the same patch/observations has no evidence-backed justification. Local planes plus gaps do not supply a unique continuous cliff. |
| True-3D cliff topology as the next remedy | No defensible measured overhang or multivalued requirement established. Do not reopen without new observations/evidence. This is not a claim that true 3D is universally unnecessary. |
| Blanket LiDAR detail normals | Not justified by 012C; ordinary orientation largely retained. This does not prove every material/normal rendering representation is useless. |
| Finite Riffelhorn visual programme | Closed after 012F/G. Conditional normal experiment **NO**; no named ordinary-terrain normal discrepancy meets its gate. No 012H continuation. |

New external literature is a reason to improve framing and examine requirements,
not permission to restart a closed experiment with another parameter choice.

## Problem taxonomy and scale

| Layer | Questions to preserve independently |
| --- | --- |
| Observation | Sensor, raw images/returns, acquisition rays/time, native resolution, datum, provenance and uncertainty. |
| Geometry | Provider classification, DTM/DSM, points, heightfields, interpolation and reconstructed/local meshes only where justified. |
| Visibility / observation quality | Was a face seen? Angle, occlusion, projected sampling, support, radiometry and confidence. |
| Surface appearance | Photographed illumination/shadow versus reflectance, radiometric processing, source-image lineage. |
| Representation | Appropriate geometry and appearance by terrain and scale; neither must be inseparably defined by one baked texture. |
| Rendering | Physical or cartographic lighting, atmosphere, filtering, exposure and tone/display transfer. |
| Multiscale delivery | Landscape/intermediate/close information selection, LOD/streaming and possibly heterogeneous products. |

A failure at one layer must not automatically be repaired at another. Texture
cannot honestly supply unmeasured relief; a mesh cannot recover an unobserved face's
photographic appearance; lighting cannot recreate absent source information;
display conversion can conceal information present upstream.

Landscape/intermediate/close are possible different **representation regimes**, not
just camera distances. Geometry/normal generalisation, cartographic emphasis,
imagery/filter choice, atmosphere and local detail may need separate assessment.
This is a research direction, not a new LOD or world-model architecture.

The retained whole-mountain benchmark is `overview`, `riffelhorn_oblique`,
`alpine_path`, plus `riffelhorn_structure` projection control: 50° HFOV, 1920×1080,
target-plane footprints ~2.234/0.237/0.069/0.076 m/pixel. Exact poses/settings
remain in [012G metadata](riffelhorn-012g-metadata.json). C–E cliff diagnostics use
1280×720 and 60/180/600 m cameras: do not conflate them with whole-AOI acceptance.

## External research changes the framing, not the findings

The [literature record](../research/literature/terrain-representation.md) identifies
established fields with explicit inputs, outputs and failure modes. Physically
informed topographic correction and outdoor intrinsic decomposition require more
than a blurred brightness field. Visibility-aware multiview appearance selection
requires appropriate images/poses. Cartographic legibility is not synonymous with
real-Sun photorealism. Delivery standards do not choose the scientific source model.

**012G did not test** acquisition-Sun reconstruction, terrain cast shadow at capture,
diffuse skylight, terrain-reflected illumination, physical topographic correction,
inverse rendering, intrinsic albedo recovery or multiview illumination separation.
Its HDR result forbids attributing final black appearance solely to empty source.
These methods remain untested by Meridian; success elsewhere is not local success.

FATMAP public evidence is limited to the qualified developer account retained in
the [pre-012F synthesis](riffelhorn-visual-synthesis-and-experiment-design.md#fatmap-evidence-and-its-limits).
It does not establish proprietary shaders, normal source, source-resolution policy
or arbitrary true-3D cliff meshes. Treat it as a reference for scale/readability,
not a reverse-engineered specification.

## Unresolved questions

- What useful dark-source contrast can survive a documented display transfer without
  misrepresenting uncertainty? The exact frozen transfer has not been isolated.
- Can a physically informed appearance method work with a processed mosaic lacking
  exact per-pixel acquisition/RAW radiometry? Requirements must be reviewed first.
- Which steep faces were actually observed, at what angles, and with what radiometric
  confidence? The mosaic does not provide this lineage.
- What is the scale/task-specific desired Atlas fidelity? An unspecified comparison
  with a tourism photo is not an acceptance test.
- Which established cartographic/generalisation methods serve map comprehension
  while maintaining measured geometry and appearance provenance?
- What can Tryfan's different data support? Transfer evaluation discipline, not Swiss
  thresholds/resolution, urban sample semantics or Riffelhorn failure attribution.

These are planning/research questions, not an authorized new experiment queue.

## Provisional representation principle and research model

**H — design principle, not frozen architecture:** Atlas should aim to construct
the most faithful, legible and provenance-aware representation of physical terrain
that available observations justify at the user's viewing scale.

Faithful means measured/reconstructed/inferred remain distinct. Legible permits
declared cartographic transformations for comprehension. Provenance-aware means
geometry and appearance retain independent sources and limitations. Scale-aware
means no assumption that one representation suits every distance. Adaptive means
better regional/local evidence can be considered without requiring it globally.
No production refactor follows from these words.

```text
Source resolution / selection
  elevation / LiDAR + imagery / observations + acquisition metadata + provenance
       -> geometry normalization (coordinates, units, representation)
       -> observation quality / visibility
       -> appearance reconstruction, if evidence and purpose justify it
       -> provenance / confidence
       -> scale-appropriate Atlas products
       -> cartographic / physical rendering
       -> Meridian
```

This conceptual model prevents conflation. Geometry, raw observations, processed
appearance and rendering should remain separable in provenance; it specifies no
new service, class hierarchy or permanent data model. Apply the
[research-first workflow and contribution discipline](../research/atlas-research-map.md#default-research-workflow)
before implementation proposals.

## External data and product map

Resolve `MERIDIAN_DATA_ROOT` using `scripts/meridian_paths.py`; the explicit local
default is sibling `meridian-data`. Do not embed a user's absolute filesystem path
in tracked manifests. No private root is needed for these Labs. Private activity
rollback estates elsewhere are not Atlas data. Leave the overall filesystem alone.

| Location beneath data root | Contents / inspection entry points |
| --- | --- |
| `sources/atlas/tryfan/`, `derived/atlas/tryfan/` | Promoted immutable Welsh/Sentinel/context sources and reusable products; exact map in Tryfan catalogue. Historical experiments remain under `experiments/earth-lab/tryfan-*`. |
| `bluesky/` | Four unchanged ZIPs: `25-RGB.zip`, `12.5-RGB.zip`, `5cm-RGB.zip`, `25cm-DSM-sample.zip`. Evaluation rights only until established otherwise. |
| `sources/atlas/riffelhorn/swisstopo-2021-2024/` | `originals/` four collections (16 files); `extracted/` four immutable LAS; `metadata/` official API/terms/receipts; `diagnostics/` attributed source previews. |
| `experiments/earth-lab/bluesky-012a/native-surface-v1/` | `vendor-extracted/`, `meshes/`, `textures/`, `captures/`, `unreal/BlueskyLab012A.uproject`; source-patch comparison, manifests/validation. 260 canonical products. |
| `experiments/earth-lab/riffelhorn-012b/observed-mountain-v1/` | DTM/DSM `meshes/`, native `textures/`, `raw-patches/`, `captures/`, `unreal/RiffelhornLab012B.uproject`; overview/residual/patch diagnostics and 28 historical frames. 209 canonical products. |
| `experiments/earth-lab/riffelhorn-012c/raw-retention-v1/` | Native XYZ/records/source indices, PCA normal arrays, residual maps, sections, raw/mesh/overlay frames. `summit_cliff-sections.png`, `cliff-180m-comparison.png`. 46 products. |
| `experiments/earth-lab/riffelhorn-012d/adaptive-heightfield-v1/` | Frozen `split.npy`, support/vertices/faces/error arrays, `split.png`, `held-out-maps.png`, `sections.png`, 60/180/600 m frames. 51 products. |
| `experiments/earth-lab/riffelhorn-012e/robust-plane-heightfield-v1/` | Construction planes, anchors, support/observability arrays, `observability.png`, `survey-continuation-support.png`, sections, residuals and completed-surface frames. 30 products. |
| `experiments/earth-lab/riffelhorn-012f/terrain-lighting-v1/` | `captures/first/` and repeat; `comparisons/`; frozen form-control profiles; independent `unreal/RiffelhornLab012F.uproject`, metadata/measurements. 39 products, including 30 native frames. |
| `experiments/earth-lab/riffelhorn-012g/projection-illumination-v1/` | Separate corrected `textures/`, original/corrected source windows, `traces/`, `illumination-field.npz`, `captures/first/` and repeat, `comparisons/`, separate Unreal project; 113 canonical products. Supplementary `pre-tone-probe-first.json`/repeat are separately hashed HDR scalar evidence. |
| `earth-lab/.venv/` | Existing scientific environment, retained outside Git; not a generated canonical product or global Python. |

All generated geometry/textures/arrays/Unreal assets/captures stay external. Runtime
logs/caches and performance timings are not automatically canonical. Existing products
do not need rebuilding to view them. Use native frames at 100%; contacts are navigation.
Reports contain exact map names, switching/capture and reproduction commands.

Read-only epoch verification from repository root (PowerShell):

```powershell
$labDataRoot = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { (Resolve-Path ..\meridian-data).Path }
$labPython = Join-Path $labDataRoot 'earth-lab\.venv\Scripts\python.exe'
& $labPython scripts/earth_lab/riffelhorn_012g.py verify
```

This checks source/parent/canonical inventories without rebuilding. `audit`,
`prepare`, `analyse` and `reproduce` can write experiment products: do not run them
just to onboard. Supplementary HDR hash and frozen source ZIP checks should also
use recorded inventories. [Scientific setup](../../scripts/earth_lab/README.md)
documents the existing external venv; Python 3.12.6 / NumPy 2.5.3 / rasterio 1.4.3 /
Pillow 12.3.0 / matplotlib 3.10.6 were used, with pyproj 3.7.2 for acquisition.
No scipy/new package is required. Original requirements and Lab toolchain records
govern any recreation; Unreal whole-AOI captures used UE 5.8.2/D3D11, whereas C–E
used bounded CPU diagnostic rendering. Do not revive Tryfan's ImagePlate automation.

## Handoff validation and historical preservation

This closure edits documentation only: this synthesis, the research index/literature,
README navigation and an appended development-log entry. Architecture, historical
reports/metadata, processing code, production, Tryfan and refs remain unchanged.
No renderer, source acquisition, new Lab, image processing or generated product run.

Read-only preservation verifies **748** canonical A–G hashes
(260/209/46/51/30/39/113), Swiss source hashes, 28 B raw frames, 322 B packages
and frozen F/G copied assets. The separate G HDR probe inventory remains unchanged.
Documentation validation covers local targets/anchors, citation URL syntax,
JSON parseability of referenced records, privacy/credential checks, whitespace,
complete diff and changed-path scope. Literature access limits are stated in its
source-status section; syntactic URLs are not claims of perpetual availability.
No expensive render/build/reprocessing suite is needed for this documentation-only
checkpoint. Historical test/build successes are evidence, not newly executed tests.
