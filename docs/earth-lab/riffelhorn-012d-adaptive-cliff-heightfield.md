# Lab 012D — Adaptive cliff heightfield

**Outcome E — INCONCLUSIVE. No candidate is accepted as a recovered cliff surface.**

Finer sampling recovers some positional evidence, including part of the extreme
error tail, but the tested construction-only interpolant does not generalize well
enough or produce a sufficiently supported, stable surface. Its holes and narrow
bridges prevent a trustworthy completed-surface improvement. This is neither proof
that the provider raster is adequate nor evidence that true-3D topology is needed.
Useful improvement has not been shown to saturate, and adaptive refinement has
not earned its complexity as an accepted representation.

## Question and protected evidence

Can a locally finer/adaptive **single-valued `z=f(x,y)`** recover coherent
metre-to-several-metre cliff form lost in the provider's 0.5 m raster, while
improving held-out observations and visible shape?

Only the existing summit-cliff patch is reconstructed:

- EPSG:2056 / LV95: `[2624780, 1092222, 2624840, 1092282]`, 60 × 60 m.
- 45,056 original returns; Z 2827.22–2930.45 m LN02. No datum conversion,
  horizontal/vertical scale change or exaggeration.
- Same source tile `2624-1092`, flight IDs 5100/5101/5102, 24/26 August 2021.
  All original attributes and extraction indices remain in the immutable 012C
  subset; this Lab stores partition/used-point indices rather than duplicating it.
- Source LAS SHA-256:
  `39d4def2a9154a664799297429e24da133e07bf0a859d768cede32452203e423`.
- Exact 012B/012C native swissSURFACE3D triangles are the baseline. Their original
  NW–SW–NE / NE–SW–SE diagonal and float32 elevation values are preserved.

See [acquisition and terms](../atlas/riffelhorn-data-discovery.md),
[asset catalogue](../atlas/riffelhorn-data-catalog.json),
[012B](riffelhorn-012b-mountain-reconstruction.md) and
[012C](riffelhorn-012c-raw-lidar-retention.md). Original sources, all **209** 012B
canonical products and all **46** 012C canonical products are checked without
regenerating or writing to those Labs. No control-patch reconstruction is needed.

**OBSERVED:** original classified XYZ returns and provider products.
**DERIVED:** partition, supported XY interpolant, sampled single-valued surfaces,
support records and held-out distances. Triangle connectivity is interpolation,
not independently measured topology.
**RENDERED:** neutral diagnostic surfaces, with no RGB, added normal/detail layer,
atmosphere or procedural enhancement. No semantic objects are inferred.

## Frozen spatial hold-out

Flights overlap spatially. A flight-only or point-random split would leave nearby
observations on both sides. Partition all flights/classes/returns together in 2 m
XY blocks, relative to the southwest patch corner. Hold out blocks satisfying
`(block_east + 2*block_north) % 4 == 0`. Remove construction observations within
**0.2 m Euclidean XY distance** of any held-out block. Buffer observations are
neither construction nor validation inputs. Duplicate XY never crosses partitions.
The rule is fixed before fitting; no seed or validation-driven partition change.

| Partition | Returns | Class 1 / class 2 | Density over entire patch |
| --- | ---: | ---: | ---: |
| Construction | 28,866 | 933 / 27,933 | 8.02 returns/m² |
| Held out | 11,179 | 405 / 10,774 | 3.11 returns/m² |
| Exclusion buffer | 5,011 | 181 / 4,830 | 1.39 returns/m² |

Every flight contributes to both construction and validation. The geographic
pattern is shown in `split.png`. All **9,652** held-out returns inside an unchanged
2 m patch-edge margin are evaluated, including unclassified returns. A fixed
2,048-point lexicographic construction audit checks fitting behaviour; 1,818 of
its returns were actually accepted into the interpolant. It is not a population
sample matched to the validation distribution.

Holding out entire 2 m blocks is deliberately harder than withholding individual
points: some metre-scale structures can fall inside a withheld block. The 0.2 m
guard prevents very near duplicate-flight leakage but is not a proof of statistical
independence. Along-flight correlation and the single frozen partition limit
generalization. Provider interpolation implicitly had access to held-out returns;
it is a privileged existing-product benchmark, not a freshly refitted competitor.

## Explainable reconstruction and support

Only class-2 construction returns are eligible, preserving all return numbers.
Class 2 is a provider classification, not a claim of true ground or rock identity.
In a **1 m 3-D spherical** neighbourhood require at least six observations,
PCA planarity ≥0.05, plane RMS ≤0.25 m and query-to-plane offset ≤0.30 m. This
broad screen excludes isolated support without claiming formal accuracy. It
accepts 25,600 returns. Coincident XY with Z spread ≤0.2 m uses median Z; four
conflicting groups are excluded. There are **25,586 unique supporting XY locations**.
The sparse-support rule also excludes two of the 13 construction anchors among
012C's 19 candidates: a limitation for several-metre structures supported only
at a larger radius.

Construct a deterministic **2-D Delaunay / piecewise-linear interpolant** using
the already installed matplotlib triangulation implementation. At most one Z
exists per XY. No extrapolation, hole filling, provider-height fallback, smoothing,
watertight meshing or completion is allowed. All grids use the same interpolant.

Mask source triangles with an XY edge span >4 m. A 4 m limit can span the guarded
2 m hold-out block diagonal; it does not claim a 4 m measurement resolution. For
a 3-D edge span >4 m, require agreement within 20° between the triangle plane and
at least two construction-only **2 m spherical PCA normals**, each with ≥10
returns, RMS ≤0.2 m and planarity ≥0.1. This admits a coherent steep plane without
equating steepness with a gap. These are heuristic support rules, not confidence
intervals or proof of support between every observation. Of 51,142 raw triangles,
5,301 are masked.

A preparatory hard-span rule erased most validation coverage and rejected a
synthetic steep plane. It was corrected to the plane-supported rule above rather
than relaxing the partition or fitting to validation errors. This was a support
logic correction, not a parameter sweep. All final candidates share one frozen
support rule. Remaining long narrow bridges show that this rule is still
insufficient as a reliable reconstruction acceptance criterion.

At each output node preserve support code and source-triangle XY span:

- **1:** nearby interpolation, span ≤0.75 m;
- **2:** longer horizontal interpolation, span ≤4 m;
- **3:** long 3-D interpolation supported by the plane screen;
- **0:** unsupported/outside, NaN Z, omitted geometry.

Codes describe interpolation support, not independent measured cells. Candidate
triangles with unsupported vertices, edge midpoints or centroid are omitted.
These probes are a bounded gap screen, not an exact polygonal clipping proof;
very narrow gaps between probes can still be bridged. Source evidence stays intact.

## Candidate set and adaptivity

All use the identical baseline cell-centre footprint: east 2624780.25–2624839.75,
north 1092222.25–1092281.75. The 59.5 × 59.5 m mesh footprint lies within the
60 m extraction AOI. This prevents a half-cell shift or invented outer samples.

- **Provider 0.5 m:** unchanged baseline.
- **Raw-derived 0.5 m:** interpolation/control comparison at provider spacing.
- **Regular 0.25 m:** finer output scale near measured neighbour spacing.
- **Regular 0.125 m:** stress test finer than dependable observation support,
  not a claim of 12.5 cm measurement accuracy.
- **Adaptive 0.5→0.25 m:** base nodes plus fine nodes only where supported
  construction returns disagree with provider triangles by >0.5 m. Require
  ≥3 such returns in a 1 m XY bin, occupying ≥2 distinct 0.25 m XY subcells.
  Buffer selected bins by 1 m. There are 184 selected and **692 buffered m²**,
  **19.22%** of the extraction patch. No held-out error or 012C query membership
  chooses the refinement. XY Delaunay connectivity between selected nodes avoids
  hanging nodes; it is a local experimental surface, not an Atlas LOD/quadtree.

The regular grids retain the provider diagonal. Adaptive connectivity can change
local diagonal choice, so its differences are not attributable only to vertex
count. All node heights are construction-only. Raw 3-D median neighbour spacing
around 0.215 m is not a universal horizontal resolution guarantee, especially
on steep faces. Fine output sampling does not create finer measured information.

## Held-out geometric results

Distances are globally nearest point-to-triangle distances, reusing 012C's exact
projection/edge method. The candidate XY index expands until the nearest distance
is below the excluded horizontal search bound; independent full-face searches
check it. Distances include unsupported-hole edges, which are reported separately
from queries with a represented height at their own XY. No tail is discarded.

| Surface | Median | p75 | p90 | p95 | p99 | Max | Represented query XY |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Provider 0.5 m | 0.056 | 0.124 | 0.347 | 0.842 | 2.832 | 6.613 | 100% |
| Raw-derived 0.5 m | 0.243 | 0.732 | 1.636 | 2.610 | 4.562 | 8.609 | 60.37% |
| Regular 0.25 m | 0.219 | 0.607 | 1.261 | 1.842 | 3.211 | 8.674 | 63.72% |
| Regular 0.125 m | 0.210 | 0.548 | 1.090 | 1.448 | 2.253 | 5.782 | 66.15% |
| Adaptive 0.5→0.25 m | 0.234 | 0.672 | 1.340 | 1.891 | 3.178 | 7.194 | 62.10% |

All distances are metres. Maxima depend on sampling, finite patch boundaries and
hole edges. Provider search remains the exact full-AOI 012C baseline; 38 queries
have their closest provider XY outside the finite patch mesh. The measurements
also report the inside-patch cohort so this asymmetry is visible, not silently
redefined. Class-2-only results have the same direction: provider median/p95
0.055/0.857 m, finest grid 0.213/1.459 m.

The 748 held-out points where provider distance exceeds 0.5 m provide a harder
cliff stratum. Provider median/p95 is **1.070/3.654 m**, finest regular
**1.221/2.657 m**. The tail improves, but only **22.99%** of this stratum has a
represented finest-grid height at its own XY. A nearer edge cannot be promoted
to recovered cliff shape. Ordinary/easy queries also worsen. Even on each
candidate's represented-XY cohort, its p95 versus the provider on the **same
queries** is 0.495/0.209 m (raw 0.5), 0.543/0.225 m (0.25), 0.584/0.254 m
(0.125), and 0.529/0.220 m (adaptive). Gaps alone do not explain the regression.

Signed distance is `dot(point-closest, upward closest facet normal)`, not a
closed-solid inside/outside test. Provider signed median is −0.009 m and finest
grid +0.015 m; p05/p95 broadens from −0.763/+0.129 to −0.572/+0.587 m. Medians
alone would conceal poor spatial fit. Full signed, upper/lower-height, strong-tail,
easy-region and classification statistics are in the
[measurements](riffelhorn-012d-measurements.json).

### Construction versus validation

Actually used construction audit median/p95 distances fall from **0.063/1.829 m**
at raw 0.5 m, to **0.034/0.962 m** at 0.25 m and **0.019/0.399 m** at 0.125 m.
The finest held-out median/p95 is **0.210/1.448 m**. Its excellent construction
fit does not establish recovery. Both construction and validation aggregate errors
decrease with finer grids: a classical reversal/overfit onset or saturation point
is **not** established. Nonetheless, increasing output density samples an unstable
interpolant more faithfully and preserves narrow bridges that cannot be accepted
as meaningful improvement. No additional resolution/parameter search is performed.

## Returning to the 012C evidence

The exact 19 source-query indices are recovered from the unchanged 2 m PCA and
coherent-neighbour screen. They form four connected 4 m XYZ groups, not 19
independent truths. Partition membership: **13 construction, 3 held out, 3 buffer**.
The finest grid has a represented height at only four of their XY positions:
three substantially improved training anchors and one partially improved held-out
anchor; the other 15 remain unsupported/ambiguous. At the independent represented
anchor `[2624785.86,1092256.19,2880.63]`, distance improves **1.424→1.094 m**.
The other two held-out anchors are closer to finest-mesh edges (1.066→0.844 and
2.577→1.570 m), but there is no represented height at their own XY. They are
**not** declared recovered. Thresholds for the retrospective status are explicit:
substantial = gain ≥0.25 m and ≥25%, partial = gain >0.05 m, only if represented.
This is a diagnostic status, not independent ground truth for construction anchors.

All nine ambiguous near-coincident-XY groups are revisited. The measurements
retain original group indices/Z ranges, partition membership and each candidate's
single predicted height or lack of support. None supplies new independent evidence
of two coherent overlapping sheets. Selecting one interpolated height does not
resolve topology. **No overhang or defensibly non-heightfield structure is proved.**

Identical six sections are reused: N=1092247/1092252/1092257 m,
E=2624790/2624810 m, Z=2875.505 m LN02. Raw full slice thickness is 0.2 m;
mesh intersections have zero width and equal metre scales. Upper and ordinary
sloping forms broadly track all surfaces. Coherent lower-face bands around
2880–2893 m remain separated from the provider bridge; candidate sections often
stop rather than supply a justified continuous face. Fine nodes partly follow
local transitions but do not reliably connect the supported lower structure.

## Surface quality, cost and controlled inspection

The surfaces remain single-valued: unique XY nodes, nonoverlapping planar XY
triangles, no stacked/vertical triangles or non-heightfield topology. Single-valued
does not mean stable. Inspected sections/frames show holes, sharp artificial gap
edges, narrow near-vertical strips, irregular faceting and long bridges. Extreme
edge occurrences >4 m are 197/317/555/227 for raw0.5/0.25/0.125/adaptive;
finest-grid maximum edge length is **36.54 m**. Edges are counted per face and
can repeat; these are warning screens, not automatic proof that a measured cliff
edge is noise. Both genuine steep support and interpolation pathology can contribute.
All candidates are rejected as deployable recovered surfaces.

| Representation | Allocated height nodes | Used mesh vertices | Triangles after support removal | Node/index array bytes |
| --- | ---: | ---: | ---: | ---: |
| Provider | 14,400 | 14,400 | 28,322 | native patch reference |
| Raw 0.5 | 14,400 | 12,102 | 21,606 | 864,144 |
| Regular 0.25 | 57,121 | 48,614 | 91,128 | 3,557,976 |
| Regular 0.125 | 227,529 | 195,092 | 376,040 | 14,485,656 |
| Adaptive | 22,620 | 17,035 | 29,886 | 901,512 |

Unsupported samples remain NaN; allocated/finite/actually referenced counts differ.
Array bytes are CPU node/index buffers, not GPU/total resident memory. Regular
faces use int64 indices and adaptive Delaunay faces int32, so memory ratios also
reflect serialization choices. Expanded triangles and Python spatial indices add
memory; peak RSS/GPU memory and Unreal import cost are not measured. This Lab
uses the established 012C deterministic software rasterizer, without new UE assets.
Preparation is about two minutes; individual generation/index passes approximately
0.25/1.27/6.13/0.58 s in one run. Noncanonical `performance.json` records timings.

Adaptivity refines 19.22% of area, allocating 57% more nodes than the coarse grid,
but only 40% of uniform 0.25 m nodes and 33% of its emitted triangles. Its global
p95 is 1.891 versus uniform 0.25 m's 1.842 m; hard-stratum p95 is 4.801 versus
5.609 m. This is a promising **cost observation**, not a representation win:
both lack coverage and regress against the provider. Uniform 0.125 m costs much
more and improves tails, without meeting the shape/support acceptance gate.

Actual fixed-camera completed-triangle frames and sections were inspected.
All cameras/targets are byte-equivalent to 012C's recorded JSON: 50° HFOV,
1280×720, 0.1 m near clip, same flat neutral material/light formula, no atmosphere,
no texture, no detail normals, no per-variant tuning. Heights stay LN02 metres
in native coordinates, translated by camera subtraction only. Optional RGB is
deliberately absent from **every** variant so appearance does not conceal shape.

| Distance | Observation | What cannot be claimed |
| --- | --- | --- |
| 60 m | Lower-face strips and gap edges dominate; fine geometry changes ledge position locally, but produces incomplete/fragile sheets. | No stable improvement in cliff face or silhouette. Close framing clips the patch. |
| 180 m | Crest/broad envelope is broadly retained; missing lower bands and narrow bridges remain conspicuous. | Reduced extreme distances do not repair the completed face. |
| 600 m | Broad patch outline dominates; regular/adaptive differences largely shrink, but artificial gap/strip patterns remain visible. | This is not evidence that useful recovered shape matters at 600 m. Gap artifacts are larger than many real displacements. |

Use native individual frames at 100% to assess output-pixel significance, not
scaled contact sheets. Patch cut edges are artificial and cannot validate the
whole mountain silhouette. Fixed neutral shading is a geometry diagnostic, not an
Unreal production material benchmark or a user-perceptual study. No normal map
could correct the demonstrated positional/gap errors. No genuine filled-surface
improvement at any distance is accepted.

## Decision and next question

**Did useful measured cliff geometry get recovered while remaining a heightfield?**
Partial positional recovery is demonstrated, including one independent supported
anchor and the extreme tail. A robust recovered cliff surface is **not** demonstrated.
The tested estimator's sensitivity to narrow XY support, block gaps and steep
interpolation prevents deciding whether another defensible heightfield would be
sufficient. Thus **Outcome E**, rather than A, B, C or D. No reliable saturation
scale, adaptive preference or need for true-3D topology follows.

The same held-out split shows that ordinary provider-agreeing areas should not
automatically be rebuilt. It cannot isolate provider interpolation causally from
construction coverage, because provider heights use observations withheld from
this experiment. Several-metre lower cliff structure remains the useful target;
there is no new claim of dependable sub-metre geometry.

**Single next experiment, not implemented:** test a robust local plane-constrained
single-valued estimator on this exact patch and frozen hold-out, explicitly rejecting
narrow unsupported bridges and retaining supported discontinuities. Compare on
common supported cohorts before adding more sampling density. This investigates
an estimator/support limitation before escalating to true-3D topology. It is not
a permanent Atlas design or permission to begin another Lab.

For Tryfan, only the validation discipline transfers. Different acquisition,
density, geometry and uncertainty require an independent test; 0.125/0.25 m output
spacings here establish no Tryfan resolution. No Tryfan/production changes occur.

## Reproduce, verify and view

Use the existing external scientific Python environment, described in
[012B setup](riffelhorn-012b-mountain-reconstruction.md#reproduce-and-inspect).
No new dependency is installed: Python 3.12.6, NumPy 2.5.3, rasterio 1.4.3,
matplotlib 3.10.6, Pillow 12.3.0. Originals and frozen 012B/012C products must exist.

```powershell
$labDataRoot = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { (Resolve-Path ..\meridian-data).Path }
$labPython = Join-Path $labDataRoot 'earth-lab\.venv\Scripts\python.exe'
& $labPython scripts/earth_lab/riffelhorn_012d.py --verify
& $labPython -m unittest discover -s scripts/earth_lab -p test_riffelhorn_012d.py -v
$labOutput = Join-Path $labDataRoot 'experiments\earth-lab\riffelhorn-012d\adaptive-heightfield-v1'
Invoke-Item (Join-Path $labOutput 'cliff-180m-comparison.png')
Invoke-Item (Join-Path $labOutput 'sections.png')
```

Existing validated products need only verification, not regeneration. To repeat
preparation, run `& $labPython scripts/earth_lab/riffelhorn_012d.py` sequentially.
It writes only the Lab 012D versioned external directory. Compare `cliff-60m`,
`cliff-180m`, `cliff-600m` contact sheets, then their provider / regular_0.25 /
regular_0.125 / adaptive individual PNGs at 100%. `split.png`, `held-out-maps.png`,
support arrays, native-coordinate node/face arrays and per-query distances provide
the numerical context. All products retain **© swisstopo** under the official
terms already documented in acquisition; no sources or captures enter Git.

## Validation and limits

[Metadata/identity](riffelhorn-012d-metadata.json),
[measurements](riffelhorn-012d-measurements.json) and
[validation](riffelhorn-012d-validation.json) record the actual run. Two complete
final preparations must match all 51 canonical product hashes and one identity.
Wall-clock timings and the validation record are excluded from canonical identity.
Verification checks original sources, all frozen previous products, the entire
partition/guard, construction membership, exact baseline triangle equality,
80 repeated distances, eight independent global brute-force candidate searches,
three camera definitions, six sections and 12 nonblank native diagnostic frames.

Nine focused synthetic tests cover partition/guard grouping, coincident-height
conflicts, planar interpolation/extrapolation, unsupported bridges, coherent versus
inconsistent steep-span support, analytical distances, refinement support rules,
native centre/diagonal registration and exact sections. All Earth Lab and
terrain-research tests, lint, TypeScript and production build are required;
results are recorded separately from the **failed reconstruction acceptance**.
No raw/source/mesh/raster/capture payload, private path, secret or vendor binary
is tracked. No previous Lab implementation, historical ref or application code
changes. No true-3D reconstruction, production normal pipeline, Atlas architecture
decision or subsequent Lab is implemented.
