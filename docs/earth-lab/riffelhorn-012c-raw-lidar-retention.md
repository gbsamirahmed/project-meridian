# Lab 012C — raw LiDAR information retention

2026-10-02. Which useful measured XYZ information is absent from the 0.5 m
swissSURFACE3D representation, and would retaining it require shape, orientation
detail, or neither? This is a bounded evidence experiment, not a production
representation, hybrid terrain system or reconstruction of unseen surfaces.

## Evidence and selection

The unchanged [acquisition catalogue](../atlas/riffelhorn-data-catalog.json),
[acquisition report](../atlas/riffelhorn-data-discovery.md) and
[Lab 012B](riffelhorn-012b-mountain-reconstruction.md) identify immutable sources.
Horizontal coordinates are EPSG:2056 / LV95; vertical coordinates are LN02 metres
(EPSG:5728 provenance). No datum conversion or vertical exaggeration occurs.
The sources have stated horizontal/vertical sigma approximately 0.20/0.10 m;
these are provider claims, not independently established accuracy here.

Three patches occupy 5,400 m², 0.135% of the existing AOI. Selection followed
inspection of 012B's north-up source imagery and profiles, before this analysis:

| Patch | LV95 edge bounds [west,south,east,north] | Rationale |
| --- | --- | --- |
| summit_cliff | [2624780,1092222,2624840,1092282] | Existing 60 m summit patch: exposed rock and strong raw/raster tails; no glacier/water test. |
| sloping_control | [2625210,1092500,2625240,1092530] | Southwest 30 m subpatch of alpine_path: comparatively smooth sloping ground. |
| rough_ground | [2625240,1092530,2625270,1092560] | Northeast 30 m subpatch of alpine_path: raised forms and rougher rock/ground context visible in imagery. |

Context labels are not classification of individual points. The controls share
one original 60 m region but are non-overlapping and have different slope/roughness.
The loose-deposit, ice and lake patches were excluded to avoid obvious temporal
and synthetic-water confounds. The observed cliff also contains discontinuities;
its exact geomorphology is not independently labelled.

Extraction reads only the two intersecting northern LAS tiles, 2624-1092 and
2625-1092. Half-open bounds preserve all original records inside each patch.
Every 28-byte format-1 record is retained, including integer coordinates,
intensity, complete return/classification flag bytes, scan angle, user data,
point source ID and GPS time. Separate float64 XYZ preserves the original scale
and offset. Original file record indices permit independent recovery checks.
Neither sources nor 012B products are rewritten.

Summit observations are August 24/26 2021 (6,618/38,438 returns); both controls
are August 23 2022. Dates use the recorded GPS timescale, not an assumed UTC
conversion. Raw observations and the corresponding provider DSM share their
LiDAR base; 2023 RGB context remains a different epoch. No updated DTM or colour
is used to create point normals or infer missing geometry.

## Methods and reproducibility

[Processing](../../scripts/earth_lab/riffelhorn_012c.py) uses the established
external scientific environment without installing dependencies. The
[metadata](riffelhorn-012c-metadata.json),
[measurements](riffelhorn-012c-measurements.json) and
[validation](riffelhorn-012c-validation.json) record identities, source hashes,
parameters, native attributes, output hashes, toolchain and exact camera poses.
OBSERVED: original LAS XYZ/attributes. DERIVED: PCA, distances and diagnostics.
RENDERED: direct points and unchanged provider-raster triangles. INFERRED:
explicitly tentative interpretation below. RECONSTRUCTED: none.

- Spacing: 256 deterministic interior queries against every other patch return,
  with a 5 m XY margin. Both XY and 3-D nearest-neighbour distributions retain
  duplicate/flight-overlap observations; spacing is not independent resolution.
- Surface distance: 1,024 lexicographically spread queries per patch, all classes,
  with a 2 m XY margin. Compare to the exact 012B native cell-centre triangles,
  including its NW–SW–NE / NE–SW–SE diagonal. Search expands until the closest
  distance is smaller than the excluded XY bound, proving global nearest distance.
  No large tail is reported as a local upper bound. Signed distance is projection
  onto the upward nearest facet normal, not inside/outside a closed surface.
- Orientation: exact 3-D spherical PCA at radii 0.5, 1 and 2 m (diameters 1, 2,
  4 m). Normals are unsigned; acute angular differences do not infer an overhang
  from an arbitrary eigenvector sign. Plane RMS measures local departure from a
  plane, combining roughness, curvature, discontinuities and measurement variation.
- Reliability screen: at least ten returns, planarity `(lambda1-lambda0)/lambda2`
  at least 0.3, RMS at most `min(0.1,0.1*radius)` m, and interleaved half-fit angle
  at most 10°. This is a documented heuristic, not an accuracy confidence interval.
  Rejecting a fit means insufficient evidence for that plane, not absent structure.
- Compare both exact facet normals and the finite-difference/interpolated vertex
  normals used in 012B. Mixing a 4 m PCA plane and a 0.5 m facet is explicitly a
  scale comparison, not a like-for-like instrument error.
- Coherence screen: two other reliable queries within twice the PCA radius with
  acute normal separation below 15°. Geometry candidates also exceed 0.5 m
  distance; detail candidates have distance at most 0.25 m and rendered-normal
  difference above 15°. Counts describe sampled evidence, not area fractions.
- Sections: three east–west and two north–south cuts per patch. Raw points occupy
  0.20 m full-thickness strips; the mesh is intersected with an exact zero-width
  plane. All axes use equal metre scales. A strip can combine distinct off-axis
  surfaces and cannot independently prove topology. The cliff also has a horizontal
  slice at median return height minus 20 m, comparing XY traces at a fixed LN02 height.

## Quantitative findings

| Patch | Returns / plan-area density | Median 3-D neighbour (m) | Exact distance median / p95 / maximum (m) | Queries >0.5 / >2 m |
| --- | --- | --- | --- | --- |
| summit_cliff | 45,056 / 12.52 m⁻² | 0.216 | 0.060 / 1.109 / 6.613 | 8.59% / 2.83% |
| sloping_control | 11,484 / 12.76 m⁻² | 0.139 | 0.017 / 0.053 / 1.213 | 0.10% / 0% |
| rough_ground | 11,832 / 13.15 m⁻² | 0.166 | 0.025 / 0.116 / 1.309 | 0.49% / 0% |

These are deterministic query fractions, not unbiased population/area estimates.
Summit one-metre horizontal density bins span 0–66 returns, versus 8–19 and 8–21
in the controls. Horizontal density masks highly anisotropic face sampling.
Original classifications are 1/2 only in these patches; class 2 explicitly can
include natural raised rock form. The summit's largest tail is class 2, not an
isolated non-ground class. In the controls, large maxima are class 1: class-2 p95
is 0.053/0.097 m and maximum 0.378/0.640 m respectively. Those isolated maxima
must not be converted automatically into added geometry.

| Patch | Reliable fits at radii 0.5 / 1 / 2 m | Raw versus rendered normal, median / p95 at radius 1 m |
| --- | --- | --- |
| summit_cliff | 25 / 428 / 231 | 4.18° / 29.87° |
| sloping_control | 201 / 1002 / 901 | 1.22° / 3.16° |
| rough_ground | 67 / 922 / 768 | 1.48° / 4.36° |

The cliff has 35 reliable geometry candidates at 2 m radius, 19 supported by the
coherence screen. Their measured plane RMS can be centimetres despite metre-scale
distance from the raster. Thus the strongest loss is spatially organised shape,
not just isolated/noisy points. The displaced lower-face band spans several to
tens of metres along the discontinuity. A local example near
[2624795.73,1092252.07,2892.44] is 3.579 m from the mesh, with 2 m-radius plane
RMS 0.047 m and split-fit angle 0.67°. This is not an absolute accuracy claim.

At 1 m radius the cliff has 44 detail candidates, but none passes the two-neighbour
coherence screen. Rough ground has 12, of which only two have that support.
The smooth control has none. Most raw orientation is already preserved by the
rendered normals; disagreement with facets alone overstates loss caused by the
actual shaded representation. There is no evidence for a blanket new detail-normal
layer. Small coherent rough-ground candidates merit only localized further testing.
At 0.5 m radius, reliable support is sparse, especially on the cliff: no general
sub-metre detail completeness or accuracy has been established.

Reliable-query distance versus inclination correlation is weak (about 0.10 at
1 m radius on the cliff). Distance versus neighbourhood count is negative
(-0.23 cliff, -0.26 control, -0.53 rough ground). Neither is causal proof:
reliability filtering excludes many sharp/near-vertical transitions. The spatial
maps and thin sections give stronger evidence for loss around discontinuities
than one universal slope/density regression.

## Is genuinely non-heightfield geometry demonstrated?

**No defensible overhang or two-sheet reconstruction is established.** The
summit has nine 0.1 m XY bins with at least two returns on each side of a Z gap
above 1 m; the largest gap is 27.34 m. Some groups share one original flight ID,
so inter-flight registration alone cannot explain every candidate. However,
finite-width bins on steep surfaces, positional uncertainty and sparse sampling
can all produce apparent overlapping heights without a mathematical overhang.

For each candidate, a local ±1 m XY box tests upper/lower point groups, planar
support, and common XY support inside their actual convex footprints. Neither
group may rely on extrapolation: both require ten points, RMS ≤0.15 m, planarity
≥0.3, `abs(normal.Z)>0.1`, at least 0.4 m interior support margin (twice the stated
horizontal sigma), and predicted separation >1 m. **Zero candidates pass.**
Near-vertical groups often have poor planar footprint conditioning and little
defensible horizontal support. A steep heightfield can also trigger the initial
screen; the synthetic tests explicitly demonstrate that counterexample. This
conservative screen can miss real topology: it is not an exhaustive overhang test.

Classification: controls are **heightfield-compatible**; the cliff is
**heightfield-compatible but poorly retained by the current raster, with ambiguous
near-vertical topology**. That describes demonstrated representation failure
without claiming all of the actual cliff is mathematically single-valued.
Multiple-height evidence remains unresolved, not disproved. The provider TIN,
classification and 0.5 m sampling may each contribute; this Lab cannot separate
their processing stages from the available products.

## Controlled visual inspection and distance significance

Nine 1280×720 native diagnostic frames and three contact sheets were actually
inspected, together with all patch sections, source context and cliff distance/
orientation maps. A small CPU perspective z-buffer draws native raster triangles
and direct, unconnected XYZ returns; it is not a new Unreal or production renderer.
Measured points occupy one screen pixel, not a fabricated physical surfel radius.
No holes are filled. The mesh uses fixed flat-facet analytic shading, deliberately
revealing triangle form; it differs from 012B's interpolated shading. Consequently
stripe contrast is not a measurement of Unreal's shading defect.

The target is the summit patch centre at median point elevation. One view direction
and 50° HFOV are held fixed across raw / mesh / overlay at distances 60, 180 and
600 m. These span approximately one, three and ten patch widths, bracketing 012B's
156–488 m structural/oblique regime. Width/height, near clip (0.1 m), projection,
point size and mesh shading remain fixed. Coordinates are float64 native metres;
camera subtraction is a translation only. No vertical or axis scale changes.

| Distance | Target-plane m/pixel | Projected query displacement median / p95 | Observed diagnostic significance |
| --- | --- | --- | --- |
| 60 m | 0.0437 | 1.02 / 17.03 px | Point traces expose ledge/lower-face form absent from the filled curtain. Close framing clips part of the 60 m patch. Sparse point coverage is conspicuous. |
| 180 m | 0.1311 | 0.30 / 3.57 px | Broad crest agrees, but lower measured bands and diagonal relief differ visibly from the long interpolated face. This is localized shape loss. |
| 600 m | 0.4372 | 0.088 / 1.01 px | Broad form dominates; most displacement is sub-pixel. Local tails remain a few pixels and can affect an exposed edge, but do not justify replacing all terrain. |

Projected distances include occluded queries and are not a perceptual score.
Raw points are transparent between samples; they do not provide a closed surface
or a validated silhouette/shading ground truth. Patch cut edges are artificial
boundaries, not mountain features. The overlays demonstrate where measured points
sit in front of or behind the interpolated surface. No filled true-3D mesh is
required to expose that evidence. A user study or equivalent filled/shaded
representation comparison has not been performed.

Control sections closely track the native raster, with local unsupported strip
gaps. Rough-ground sections retain metre-scale steps with small edge rounding.
Cliff sections repeatedly show lower measured bands and an abrupt raster bridge;
the bands are not merely an isolated maximum. No RGB reconstruction or new source
acquisition was needed. Existing 2023 context cannot validate 2021/2022 wall colour
or assign identities to individual returns.

## What is worth retaining?

| Evidence | Interpretation | Efficient representation hypothesis, not implemented |
| --- | --- | --- |
| Ordinary control form and most rough-ground form | RETAINED | Existing heightfield and rendered normals are adequate for these samples. |
| Coherent several-metre cliff displacement, sharp lower-face/ledge transition | GEOMETRY LOSS plus PROCESSING / INTERPOLATION | Geometry must preserve position/shape if close views matter. Test localized adaptive/finer heightfield first; true-3D topology is not yet proved necessary. Normals cannot move a face or repair silhouette. |
| A few stable local orientation differences with small displacement | DETAIL / ORIENTATION LOSS candidates | Measured normal/detail descriptor could help local shading, only where support repeats. No blanket normal-map pipeline is justified. |
| Sparse sub-metre fits, rejected planes, isolated class-1 tails | SAMPLING LIMIT / UNRESOLVED | Preserve evidence, add neither geometry nor detail without stronger support. |
| Near-coincident XY with large Z separation | Ambiguous NON-HEIGHTFIELD EVIDENCE screen | Do not infer overhangs or fill unseen faces. Better evidence/registration and oriented support are required. |

Riffelhorn's current close render is limited by local shape retention and wall
appearance, rather than global triangle count. At intermediate views the local
cliff loss can matter; ordinary ground remains adequate. At normal landscape
distance output scale suppresses most of the difference. This does not establish
the same LiDAR coverage/accuracy or classification behaviour at Tryfan. It supports
testing retained shape and orientation there independently, without deriving rock
semantics from DSM–DTM or colour.

**Single next experiment, not implemented:** on this same cliff patch, compare a
bounded adaptive/finer single-valued surface against the unchanged 0.5 m mesh,
using held-out raw returns and the same distance cameras. Test whether coherent
metre-scale displacement can be reduced without inventing topology. Only residual
failure backed by coherent overlapping surfaces would justify a true-3D alternative.
This sets no permanent Atlas requirement and begins no subsequent Lab.

## Reproduce and view

From the repository root:

```powershell
$labDataRoot = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { (Resolve-Path ..\meridian-data).Path }
$labPython = Join-Path $labDataRoot 'earth-lab\.venv\Scripts\python.exe'
& $labPython scripts/earth_lab/riffelhorn_012c.py
& $labPython scripts/earth_lab/riffelhorn_012c.py --verify
& $labPython -m unittest discover -s scripts/earth_lab -p test_riffelhorn_012c.py -v
$labOutput = Join-Path $labDataRoot 'experiments\earth-lab\riffelhorn-012c\raw-retention-v1'
Invoke-Item (Join-Path $labOutput 'cliff-180m-comparison.png')
Invoke-Item (Join-Path $labOutput 'summit_cliff-sections.png')
```

Compare `cliff-60m-comparison.png`, `cliff-180m-comparison.png`, and
`cliff-600m-comparison.png` at 100% image scale. Each holds camera fixed while
switching raw / mesh / overlay. Sections and maps exist for all three patches.
Existing products need only verification, not regeneration. Originals, point
subsets, full attribute/index arrays, normals and all figures remain external.
The environment is documented in [Lab 012B setup](riffelhorn-012b-mountain-reconstruction.md#reproduce-and-inspect);
no global Python installation is required. All products retain ©swisstopo.

## Verification and limitations

Two identical final runs must reproduce the complete manifest identity and all
46 canonical product hashes. Verification checks 16 original and four extracted
source hashes, all 64 existing 012B DSM mesh hashes during preparation, 45 independent
original record/coordinate samples, 24 exact-distance rerun queries, three camera
poses and nine nonblank native frames. Synthetic tests cover exact planes/edges,
adaptive distances, 3-D PCA, insufficient sampling, steep versus stacked sheets,
native render-normal interpolation, strip thickness and perspective scaling.

All Earth Lab and terrain-research tests, ESLint, TypeScript and the production
build are required. Existing NumPy/rasterio deprecation and bundle-size warnings
are unrelated. No production, Tryfan or previous Lab implementation changes; no
new dependencies, raw payloads, inferred surfaces or Unreal assets enter Git.
PCA thresholds and deterministic queries are limited evidence screens, not formal
uncertainty estimates or unbiased terrain-wide statistics. Point-only visibility
does not prove what a completed shaded surface would look like. No universal
sub-metre resolution, overhang inventory, semantic object label or final Atlas
representation follows from these results.
