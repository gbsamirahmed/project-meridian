# Lab 012E — Robust cliff heightfield estimation

**Outcome F — INCONCLUSIVE. The Riffelhorn heightfield-reconstruction branch is
CLOSED for now. No reconstructed surface is accepted.**

Reliable local planes recover two of the previously identified positions, but
they do not establish a stable continuous cliff. The estimator refuses many
otherwise plausible local continuations and performs worse on held-out returns.
The full survey also has gaps between observed lower and upper bands. These are
different problems: estimator refusal is not proof that no observation exists,
and observing a local plane is not proof of the intervening face. Neither a
fundamental heightfield limitation nor sufficient evidence for another estimator
experiment has been established. There is no automatic Lab 012F continuation.

## Question and immutable evidence

Can measured construction-only local orientation constrain a better-supported,
stable single-valued cliff surface, and distinguish estimator failure from
observation/support limitations?

Reuse exactly [012D](riffelhorn-012d-adaptive-cliff-heightfield.md):

- LV95 / EPSG:2056 bounds `[2624780,1092222,2624840,1092282]`, 60 × 60 m.
- Original 45,056 returns in the unchanged 012C subset, LN02 metre heights,
  Z 2827.22–2930.45 m. No coordinate/datum conversion or exaggeration.
- Source tile `2624-1092`, flights 5100/5101/5102, 24/26 August 2021.
- Source LAS SHA-256
  `39d4def2a9154a664799297429e24da133e07bf0a859d768cede32452203e423`.
- Frozen construction / held-out / guard counts **28,866 / 11,179 / 5,011**;
  evaluate the identical **9,652** held-out interior returns.
- The original 2 m block rule and 0.2 m Euclidean exclusion buffer are unchanged.
  No random repartition, flight leakage, held-out fitting or parameter sweep.
- The unchanged provider, 012D regular 0.125 m and adaptive arrays/distances are
  read directly. This Lab does not regenerate historical baselines.

Only the **27,933 class-2 construction returns** fit planes or constrain heights.
Class 2 is the provider's classification, not a semantic rock/ground assertion.
All held-out classes and returns remain in evaluation. The provider is a privileged
benchmark that used observations excluded from construction here. Block hold-out
deliberately withholds whole small features; it is not a full-survey reconstruction.

Originals and all **209 / 46 / 51** canonical 012B/C/D products are verified
without writing to their directories. See [acquisition/terms](../atlas/riffelhorn-data-discovery.md),
[source catalogue](../atlas/riffelhorn-data-catalog.json),
[012B](riffelhorn-012b-mountain-reconstruction.md) and
[012C](riffelhorn-012c-raw-lidar-retention.md).

**OBSERVED:** classified XYZ and provider products. **DERIVED:** local planes,
one scalar height per XY, support diagnostics and error measurements.
**RENDERED:** neutral completed-triangle diagnostics. Connectivity and local
continuation are interpolation, not independently measured surfaces. No semantic
classification, synthetic structure, true-3D reconstruction or new normal map.

## One explainable estimator

The primary method is a robust local-plane vote followed by scalar-height fitting.
All parameters were fixed before examining real held-out results. Synthetic tests
validate refusal and geometric invariants; thresholds are physical heuristic
screens, not calibrated probabilities or a claim of optimal estimation.

1. At each construction return, fit PCA planes in **1 m and 2 m 3-D spherical**
   contexts. Trim gross perpendicular departures twice using the larger of 0.15 m
   or three scaled median absolute deviations. Require ≥10 retained returns,
   planarity ≥0.30, RMS ≤0.10/0.15 m at 1/2 m, and interleaved-subset normal
   disagreement ≤10°. An anchor must lie within 0.20 m of its plane.
2. Choose the smallest reliable context. Cap correlated overlapping estimates to
   one best anchor per **0.5 m XYZ voxel**. Retain both-scale quality arrays,
   original source indices, normals, RMS, planarity, counts and flight support.
3. For each unchanged 0.125 m output node, query anchors within 2.2 m XY. A plane
   predicts scalar Z only if `abs(normal_z) ≥ 0.10`, and its predicted XYZ lies
   within its physical context radius +0.20 m. A nearly vertical fit is retained
   as evidence but can be unsuitable for stable Z prediction; this is not a
   topological verdict.
4. Weight by planarity, capped return count, physical distance and perpendicular
   RMS with a 0.10 m uncertainty floor. Use a weighted median height hypothesis;
   require ≥3 distinct anchors and ≥80% agreeing weight within 0.30 m perpendicular
   departure and 20° orientation. Conflicting hypotheses are refused, not averaged
   into a fictitious middle sheet.
5. Three scalar Huber iterations with 0.10 m perpendicular transition fit Z.
   Plane signs are aligned before averaging normals. Require ≥10 nearby
   construction returns within 2 m XYZ and 0.30 m of the consensus plane, and
   bracket the query in their XY convex hull. No extrapolation, provider fallback,
   smoothing or hole filling.
6. Keep the provider-aligned 477 × 477 node grid and original diagonal. Node
   centres span E=2624780.25–2624839.75, N=1092222.25–1092281.75 m, preserving
   the native centre footprint without a half-cell shift. Omit
   unsupported-node faces and edges departing more than 0.30 m from either
   endpoint's measured plane. This rejects narrow connections inconsistent with
   their supporting orientations rather than merely making them smooth.

The 0.10–0.30 m departures relate to the documented nominal source uncertainty
and coarse contextual fitting; they are not precise cliffs' error bars. The 1/2 m
contexts come from 012C and target metre-scale continuity. The limited extension
permits local continuation without joining an entire unobserved cliff. The
consensus rule is deliberately conservative at discontinuities. It can reject
valid terrain and is explicitly an estimator limitation. No held-out metric chose
or relaxed these parameters. No output spacing finer than 0.125 m is tested.

## Support and separate observability audit

Node codes describe constraints, not whether a reconstructed height is correct:

| Code | Meaning |
| --- | --- |
| 1 supported | Consistent votes/returns, nearest XYZ ≤0.5 m, XY hull margin ≥0.2 m, ≥3 reliable 1 m planes. |
| 2 interpolated | Accepted plane continuation and XY bracketing, without all strong conditions. |
| 3 weak | Conflicting predictions, conditioning/local-span failure, too few distinct anchors/returns, or unbracketed XY. No emitted height. |
| 0 unsupported | No reliable nearby plane. No emitted height. |

`observability.png` and arrays preserve reasons, anchor/return counts, physical
nearest-return distance, XY bracketing margin, consensus fraction, fit departure,
inclination and flight count. Nominal propagation
`sqrt(0.20²*(n_e²+n_n²)+0.10²*n_z²)/abs(n_z)` illustrates height conditioning.
The provider's ±0.20 m XY / ±0.10 m Z specification is not independently verified;
correlations are unknown. This expression is **not** a fitted confidence interval,
relative plane-noise estimate or hard acceptance gate.

At the historical 19 measured positions, a **post-fit** construction-only local
plane audit checks whether a reliable lower-band estimate exists even when the XY
estimator refuses it. Measured validation Z is used only to locate this diagnostic,
never passed back into reconstruction. Fifteen positions have reliable 2 m local
planes; fourteen of those still have no accepted represented height. Thus absence
of an accepted node must not be described as absence of measured local shape.

A separate post-fit **full-survey position audit**, including withheld/buffer
returns, never fits or supplies a plane/height to the estimator:

- In 1 m XY cylinders about the 19 positions, observed lower/upper Z bands have
  largest gaps **16.42–35.47 m**, despite 52–120 full-survey returns. A finite XY
  cylinder can miss sloping continuation outside it; this is a coverage warning,
  not proof of an empty wall, vertical sheet or overhang.
- Along the exact provider section surfaces, 1,741 physical 0.5 m-spaced probes
  have full-survey nearest XYZ median/p95/max **0.277/2.629/5.369 m**. **132**
  probes are >2 m from any full-survey return. Only **25** additional >2 m gaps
  are introduced by construction exclusion where the full survey has closer data.
  Provider probes are not ground truth: lack of nearby points can indicate a
  displaced provider ramp as well as an unobserved face.

The evidence therefore demonstrates both real anisotropic/gappy sampling and
restrictive/conflicting local reconstruction. It does not identify a unique
continuous face between bands or prove that the entire source is insufficient.

## Frozen held-out results

Globally nearest point-to-triangle distances reuse 012C/D's validated projection
and expanding XY search. Include every query, including distances to hole edges.
Signed distance is projection on the upward closest facet normal, not a closed
solid inside/outside test. Full tails, signed and local statistics are in the
[measurements](riffelhorn-012e-measurements.json).

| Representation | Median | p75 | p90 | p95 | p99 | Max | Represented held-out XY |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Provider 0.5 m | 0.056 | 0.124 | 0.347 | 0.842 | 2.832 | 6.613 | 100% |
| 012D regular 0.125 m | 0.210 | 0.548 | 1.090 | 1.448 | 2.253 | 5.782 | 66.15% |
| 012D adaptive | 0.234 | 0.672 | 1.340 | 1.891 | 3.178 | 7.194 | 62.10% |
| 012E robust plane | 0.521 | 1.098 | 2.231 | 3.555 | 8.057 | 13.593 | 21.20% |

All distances are metres; maxima depend on finite edges, gaps and sample selection.
The provider distance baseline remains exactly 012D's full-AOI result, including
its documented finite-patch edge asymmetry. This is not a subtly refitted baseline.

The 2,048-return fixed construction audit has robust median/p95 **0.117/3.264 m**,
versus held-out **0.521/3.555 m**. On represented construction XY these are
**0.048/0.323 m**. On represented held-out XY they are **0.097/1.688 m**, versus
provider **0.041/0.210 m on the identical cohort**. Neither the low fitting error
nor a support code demonstrates correct held-out geometry. No improvement is
accepted, and no classical resolution-sweep overfit onset is asserted.

| Frozen stratum | Returns | Provider median/p95 | 012E median/p95 | 012E represented XY |
| --- | ---: | ---: | ---: | ---: |
| Lower, Z <2890 m | 3,973 | 0.057/1.428 | 0.551/3.052 | 18.45% |
| Upper, Z ≥2890 m | 5,679 | 0.054/0.511 | 0.500/4.143 | 23.12% |
| Strong original error >0.5 m | 748 | 1.070/3.654 | 1.923/6.399 | 8.82% |
| Ordinary agreement ≤0.1 m | 6,695 | 0.034/0.090 | 0.399/2.346 | 25.42% |

The estimator degrades ordinary areas too; this alone forbids general application
to Atlas terrain. Of held-out XY, 340 have strong node constraints, 2,376
interpolated constraints, 6,935 weak and one absent. Actual emitted-face coverage
is lower than accepted node coverage; surrounding missing nodes can remove a face.

## Exact candidates, sections and continuity

Of the **19** unchanged 012C candidates, two have represented XY and substantially
improve: held-out index **27098**, provider 2.577 m → **0.143 m**, and construction
index **43232** → **0.002 m**. Seventeen remain unresolved with no accepted height:
sixteen have conflicting vote hypotheses and one lacks XY bracketing. These are
four coherent groups, not nineteen independent ground truths. The independent
local recovery is useful evidence that orientation can retain a lower-face patch;
it does not establish the missing continuous cliff or rescue aggregate performance.

All **nine** original finite-XY multiple-height groups remain ambiguous. Seven
have conflicting hypotheses, one lacks enough consistent returns and one lacks
XY bracketing. No independent overlapping coherent sheets/overhang are established.
Plane selection or rejection cannot resolve topology. Nearly vertical orientation,
large Z range and large provider residual are not heightfield-incompatibility tests.

The identical six sections are N=1092247/1092252/1092257, E=2624790/2624810 and
Z=2875.505 m. Raw full thickness 0.2 m, mesh intersections zero-width, equal metre
axes. Actual inspection shows upper/sloping portions broadly follow observations;
lower isolated bands sometimes receive local segments, but the face between lower
and upper bands is not recovered. At N=1092252, observed lower points around
2880–2893 m remain disconnected from the upper edge around 2920–2927 m. The method
mostly refuses continuation rather than constructing a justified replacement for
the provider's curtain. No section is moved to favour the new estimator.

The maximum emitted 3-D edge is **1.886 m**, versus 012D regular's **36.54 m**.
Six otherwise finite faces fail the orientation-edge check; 239,419 have unsupported
vertices. Long bridges are reduced mainly because their nodes are never emitted,
not because a supported continuous face replaces them. Inspected views retain
small isolated islands, fragmented strips and jagged hole boundaries. No systematic
large spike/bridge is accepted; no claim of a complete spike/pit detector is made.
A smooth-looking unsupported connection would still be rejected.

## Controlled visual inspection and cost

Use exact 012C/D cameras/targets, 50° HFOV, 1280×720, 0.1 m near clip and the same
flat neutral light/material formula. Every variant has no RGB, atmosphere,
exposure grading, detail normals or procedural effects. Heights stay LN02 metres;
camera subtraction is translation only. No Unreal assets or previous renderer
are changed. All nine historical provider/regular/adaptive frames are byte-identical
to 012D. This is a completed-triangle software diagnostic, not a production
Unreal shading benchmark or user-perceptual study.

Actual native frames and sections were inspected:

- **60 m:** provider curtain occupies the face; 012D retains fragile strips;
  robust geometry becomes scattered small panels and holes. Local lower-position
  recovery does not improve a continuous profile, silhouette or stable shading.
- **180 m:** the crest remains approximately located, but the robust cliff face is
  perforated and incomplete. Reduced long bridging is bought by visibly missing
  surface, not a trustworthy shape improvement.
- **600 m:** broad envelope dominates while artificial holes remain visible.
  Most meaningful small displacement shrinks toward/below output-pixel scale;
  visible artifacts are not evidence of useful distant recovery.

Patch cut edges and near framing prevent claims about the whole mountain silhouette.
Individual frames at 100% should be used for pixel significance, not scaled contact
sheets. There is no accepted cliff-position/shading improvement at any distance.

The working grid has **227,529 allocated nodes**, **121,965 finite nodes**,
**120,871 used vertices** and **213,727 triangles**. It represents **1,669.742 m²**,
**47.16%** of the 59.5 ×59.5 m provider-centre footprint; **52.84%** is missing.
Strong/interpolated/weak/absent node fractions are approximately
32.58/21.02/46.38/0.01%. Node/index buffers occupy **10,590,144 bytes**; quality,
support, query and diagnostic arrays add external storage. Fine sampling is not
fine independent measurement. Preparation takes approximately three minutes;
`performance.json` records noncanonical wall-clock time. GPU/peak RSS and Unreal
import cost are unmeasured; no new GPU renderer is introduced.

The **30 canonical external products total 52,481,747 bytes**. Two complete final
runs reproduce every product hash and identity
`1e2ceedb56b935cc6666423efccb380d87835bdbb4247ef026375fe6341715de`;
their preparation times were approximately 178 and 184 seconds. Arrays preserve
native coordinates and emitted Z ranges 2827.441–2930.482 m LN02.

## Decision and branch closure

**Is the estimator unable to connect observations, or do the observations fail to
justify the missing surface?** Both mechanisms occur locally, and this experiment
cannot responsibly assign the whole failure to one. Fifteen candidate locations
retain reliable construction planes, so rejecting their continuation cannot be
called pure absence of evidence. Conversely, the full-survey band gaps and
unobserved provider-face intervals do not justify filling a continuous cliff from
those planes. A local scalar vote cannot determine which conflicting sheet/transition
to retain solely from nearby orientations. That is a methodological limitation,
not proof that a different global estimator would succeed.

- A is rejected by held-out, support and visual failure.
- B is locally plausible but not established for all missing structure; fixed
  hold-out and conservative local continuation contribute substantially.
- C is unsupported: no defensible non-heightfield topology is demonstrated.
- D would require evidence of sufficient continuous support and a specific new
  experiment likely to resolve one deficiency. Neither is established; disappointing
  metrics alone are not a reason for another estimator Lab.
- E is not the primary result: source hashes/provenance are valid; uncertainty
  remains documented but does not alone explain this experiment's mixed failure.
- **F is selected:** failed recovery is clear; causal attribution remains mixed.

**After 012B–012E, there is not enough evidence to justify another increasingly
sophisticated Riffelhorn interpolation experiment. This branch is CLOSED for now.**
Keep the provider surface as the existing reference, retain the measured patches
and diagnostics, and do not deploy the rejected estimator. A new true-3D experiment
is not justified by this evidence. No automatic next Lab or production architecture.

The problem is local to difficult cliff sampling/representation. Ordinary slopes
and rough ground already work well in 012C; most displacement diminishes at landscape
distance. No blanket fine remesh or detail-normal enhancement follows. For Tryfan,
only construction/held-out discipline and explicit observation-versus-estimator
support checks transfer; Swiss numerical scales/thresholds do not.

The broader question worth reviewing separately is: **at useful mountain viewing
distances, which remaining appearance deficits arise from imagery projection,
material/lighting representation and source mismatch rather than missing geometry?**
This question is not implemented here. Production Meridian, Tryfan and earlier
Labs remain untouched.

## Reproduce, verify and inspect

Use the existing external scientific Python environment; no dependency added:
Python 3.12.6, NumPy 2.5.3, rasterio 1.4.3, matplotlib 3.10.6, Pillow 12.3.0.
All immutable sources and frozen B/C/D products must exist. From repository root:

```powershell
$labDataRoot = if ($env:MERIDIAN_DATA_ROOT) { $env:MERIDIAN_DATA_ROOT } else { (Resolve-Path ..\meridian-data).Path }
$labPython = Join-Path $labDataRoot 'earth-lab\.venv\Scripts\python.exe'
& $labPython scripts/earth_lab/riffelhorn_012e.py --verify
& $labPython -m unittest discover -s scripts/earth_lab -p test_riffelhorn_012e.py -v
$labOutput = Join-Path $labDataRoot 'experiments\earth-lab\riffelhorn-012e\robust-plane-heightfield-v1'
Invoke-Item (Join-Path $labOutput 'sections.png')
Invoke-Item (Join-Path $labOutput 'observability.png')
Invoke-Item (Join-Path $labOutput 'survey-continuation-support.png')
Invoke-Item (Join-Path $labOutput 'cliff-180m-comparison.png')
```

Existing products require only verification/viewing. To repeat processing run
`& $labPython scripts/earth_lab/riffelhorn_012e.py` sequentially. It writes only
the versioned 012E external directory. Inspect all three comparison sheets and
individual `cliff-60m/180m/600m-robust.png` and baseline frames at native size.
No SceneCapture/ImagePlate automation or Unreal lighting build is used.

[Metadata](riffelhorn-012e-metadata.json), [measurements](riffelhorn-012e-measurements.json)
and [validation](riffelhorn-012e-validation.json) record identity, actual values,
frozen-input hashes, product hashes and validation. Two complete final runs must
reproduce canonical products; timings and validation are excluded from identity.
Eight focused tests cover physical PCA/outlier trimming, scatter rejection,
exact scalar-plane prediction/refusal, conflicting sheets, vertical conditioning,
unsigned normal alignment, bridge rejection and independent support diagnostics.
Verification also checks source/old products, complete split and construction
membership, repeated node diagnostics, indexed distances against brute force,
native units, six sections, three cameras and historical frame equality.

All source, arrays, meshes, quality maps and captures stay outside Git. Tracked
outputs are code/tests, small metadata/measurements/report and the development log.
Official swisstopo terms and **© swisstopo** attribution remain attached to figures,
products and documentation. No source licence or historical identity is changed.
