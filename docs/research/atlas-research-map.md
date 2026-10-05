# Atlas research map and fresh-session handoff

Updated 2026-10-05. The 012A–012G terrain-research epoch is **closed** at the
Lab 012G evidence checkpoint `abf95bcfb50c681244a146626565a471ba791418`.
This index records knowledge and research status, not a roadmap, new Lab or
production architecture. It is the starting point for humans and fresh tooling.

## Read before changing Atlas

1. Read the [architecture contract](../architecture.md): Atlas represents the
   physical world; Weather the atmosphere; Traverse movement; App composition.
   The current client-only application and its ownership boundaries are implemented.
2. Read the [final terrain-representation synthesis](../earth-lab/atlas-terrain-representation-synthesis.md).
3. Read this map and the relevant [terrain literature record](literature/terrain-representation.md).
4. Read the relevant [development-log history](../development-log.md), then inspect
   branch, HEAD, index, working tree, recent history and origin relationship.
5. Read the [external-storage contract](../architecture.md#repository-and-external-storage-contract),
   [data/product map](../earth-lab/atlas-terrain-representation-synthesis.md#external-data-and-product-map)
   and applicable source catalogue. Individual Lab reports supply detailed methods.
6. Assume no conversational context exists. Historical proposed next steps are not
   current authorizations. Do not reopen closed branches without new evidence or
   begin a Lab merely because a question is unresolved.
7. Review established academic/industry methods before proposing a novel algorithm.
   Keep experiments bounded, products external, provenance reproducible and evidence
   classes distinct. Never silently promote experimental findings into architecture.

Recommended return point: **deliberate Atlas design / implementation planning informed
by accumulated Meridian evidence and external research**. This handoff chooses no
next architecture or experiment. The pre-012F
[finite programme](../earth-lab/riffelhorn-visual-synthesis-and-experiment-design.md)
is historical; its two core slots were used and its conditional third was refused.

## Bounded post-epoch production evaluations

The closed terrain epoch is followed by deliberate product evaluations, not new
Labs: [native relief](../atlas/native-relief-evaluation.md) retained IGOR with a
modest strength increase; [global terrain foundation](../atlas/global-terrain-foundation-evaluation.md)
verified Mapterhorn and compared visual sources under that frozen treatment. The
latter found regional gains but retained AWS as the production default. Independent
analytical AWS elevation and the closed research branches remain unchanged.

The [direct Riffelhorn regional prototype](../atlas/riffelhorn-regional-terrain-prototype.md)
then prepared retained official swissALTI3D for the real web renderer. It reproduced
interior detail gains with explicit source/product identities, while hard regional
joins exposed large spatially varying height discontinuities. A single composed
DEM endpoint is feasible; seamless substitution and vertical reconciliation are
not established. AWS remains the production default. This is bounded integration
evidence, not a reopened Lab, universal resolver or imagery programme.

The [bounded reconciliation investigation](../atlas/riffelhorn-terrain-reconciliation.md)
characterizes the mixed-scale Swiss/AWS disagreement and reviews established DEM
fusion practice. Numerical and frozen-renderer controls remove the edge step but
reshape terrain or consume interior information. No method is adopted; source
support, stable-terrain evidence, height semantics and contributor masks constrain
the next decision. AWS and the closed terrain-research branches remain unchanged.

The [terrain source/product architecture decision](../atlas/terrain-source-product-architecture.md)
derives a minimal Atlas metadata foundation from those evaluations. It distinguishes
datasets, delivery products, representations, support roles, resolution, vertical
semantics and incomplete provenance. Four typed cases describe current AWS, retained
swissALTI3D, the Swiss/AWS Riffelhorn product and Mapterhorn without adopting them
as a resolver. At that checkpoint the support-selection task was deferred; production stayed AWS.

The [larger Swiss support product](../atlas/riffelhorn-swiss-support-product.md)
now retains a 1.5 km protected interior within 100 km² of official 2024 terrain,
with a minimum 3.5 km source collar. It exercises the metadata model and improves
disagreement characterization without reconciling or accepting a seamline. Pure
regional web delivery has coarse-level/perimeter gaps; native support and delivery
coverage remain separate. At that checkpoint the reference/stable-terrain assessment was deferred.
Production remains independently AWS and the closed research epoch stays closed.

The [global-reference/stable-overlap assessment](../atlas/global-reference-assessment.md)
then reviewed AWS and one alternative, Copernicus GLO-30, using independently
screened glacier/land-cover/slope support. It recommends an accountable
Copernicus common/coarse reference role while preserving separate visual and
analytical policies. The local relationship is tighter, but narrow-ridge
outliers, unequal stable support and registration/height limitations remain.
The 2021 public COG distribution is not called the latest release. No correction,
reconciliation, hierarchy or production migration was performed. The smallest
next step is a separate local common/coarse product with explicit support and
revision policy, not an accepted Swiss seam or general resolver.

The [bounded Copernicus common/coarse product](../atlas/copernicus-common-product.md)
then froze six 2021 COG inputs and prepared complete z8–13 local terrain delivery.
Independent rebuilds and numerical checks establish preparation and parent fidelity;
real-app views retain broad terrain structure under the unchanged renderer. Delivery
z13 oversamples source postings, with higher map zoom only overzoom. The external
perimeter and missing lower/global support are negative findings. No Swiss composition
or production migration occurred. The asset supports a later bounded hierarchy
experiment with explicit height, contributor and support policy; it does not establish
that experiment's result or authorize a generic resolver.

The [bounded Copernicus/Swiss hierarchy](../atlas/terrain-hierarchy-prototype.md)
then tested hard per-level substitution and scale-gated regional children. Fine
Swiss terrain remains exact and coarse common context loads, but moving support
frontiers, spatial bands/walls and large common-to-Swiss LOD changes remain.
This negative result distinguishes scale selection from spatial continuity and
height semantics. No transformation, smoothing collar, general resolver or
production adoption was accepted; the suggested regional-parent diagnostic is
a future direction, not an automatically started phase.

The [regional-preserving parent diagnostic](../atlas/regional-parent-diagnostic.md)
then tested recursive Swiss coarse summaries with explicit partial support.
It demonstrates internally related regional refinement (13→14 RMS0.71 m versus
39.82 m for the unrelated common parent), with unchanged fine Swiss/protected
terrain. Coarsening through10 does not yield a natural common handoff; incomplete
tiles are not invented and the spatial edge remains. LOD and spatial continuity
are distinct evidenced problems. A regional-pyramid concept is supported, but
no final hierarchy contract or production adoption follows. The smallest next
direction is one bounded support-aware same-level boundary assessment.

The [spatial reconciliation research/design review](../atlas/spatial-terrain-reconciliation-research.md)
then separates datum accounting, demonstrated registration error, surface/epoch
differences, spatial source reconciliation and render-time continuity. Established
priority/weighted mosaicking does not justify a broad arbitrary deformation of
protected terrain. Existing support permits a next **seam-corridor feasibility
diagnostic**, not a blend: examine connected, supported routes and bottlenecks
around the protected interior before deriving another surface. Sparse stable
support and glacier sectors may defeat that test. No terrain, hierarchy algorithm,
height correction or production behavior changed; this direction remains untested.

## Evidence classes

- **MERIDIAN EVIDENCE (M):** measurements, inspected outputs and negative results
  from identified repository experiments. Scope and limitations travel with claims.
- **EXTERNAL EVIDENCE (E):** published methods, standards, official documentation
  and explicitly qualified first-hand industry accounts. Mature externally does
  not mean demonstrated by Meridian.
- **RESEARCH HYPOTHESIS / DIRECTION (H):** a possible interpretation, evaluation or
  design idea. Neither external familiarity nor an attractive result establishes it.

Observed / derived / inferred / reconstructed / rendered are additional provenance
roles, not substitutes for these three evidence classes.

## Research status — no priority ranking

| Status | Topic and bounded meaning | Evidence / reading |
| --- | --- | --- |
| Established / reusable | CRS/datum accounting, immutable sources, held-out validation, native texture tiling and exact geometry registration already used in Meridian | [Synthesis](../earth-lab/atlas-terrain-representation-synthesis.md#experimental-sequence), [012A](../earth-lab/bluesky-012a-aerial-reconstruction.md), [012D](../earth-lab/riffelhorn-012d-adaptive-cliff-heightfield.md) |
| Established / reusable externally | Solar ephemerides and geospatial delivery specifications exist; assess existing tools instead of inventing their fundamentals | [Sun reconstruction](literature/terrain-representation.md#acquisition-sun-and-illumination-reconstruction), [delivery](literature/terrain-representation.md#large-scale-terrain-delivery); [012G limitation](../earth-lab/riffelhorn-012g-projection-and-illumination.md) |
| Candidate for Meridian evaluation | Physically informed topographic correction and outdoor albedo recovery; unknown suitability for processed Swiss mosaics and missing acquisition lineage | [Correction](literature/terrain-representation.md#topographic-correction), [inverse rendering](literature/terrain-representation.md#inverse-rendering-and-albedo-recovery), [012G](../earth-lab/riffelhorn-012g-projection-and-illumination.md) |
| Candidate for Meridian evaluation | Visibility-aware multiview appearance selection; requires observations/poses not supplied by a single orthophoto mosaic | [Steep observation](literature/terrain-representation.md#steep-terrain-photogrammetry-and-observation), [texturing](literature/terrain-representation.md#multiview-texture-reconstruction), [source catalogue](../atlas/riffelhorn-data-catalog.json) |
| Candidate for Meridian evaluation | Cartographic lighting and structural scale generalisation; 012F tested only a small directional/shadow subset | [Relief shading](literature/terrain-representation.md#terrain-visualization-and-cartographic-lighting), [scale](literature/terrain-representation.md#terrain-generalisation-and-scale), [012F](../earth-lab/riffelhorn-012f-terrain-lighting.md) |
| Untested / open | Exact source-to-display transfer and dark-signal usability; 012G proves upstream variation, not calibrated albedo or usable rock identity | [Unresolved questions](../earth-lab/atlas-terrain-representation-synthesis.md#unresolved-questions), [012G](../earth-lab/riffelhorn-012g-projection-and-illumination.md) |
| Untested / open | Whether landscape/intermediate/close require distinct representation regimes; whether Tryfan observations support comparable appearance | [Scale model](../earth-lab/atlas-terrain-representation-synthesis.md#problem-taxonomy-and-scale), [Tryfan](../earth-lab/tryfan-010-observed-natural-colour.md), [scale literature](literature/terrain-representation.md#terrain-generalisation-and-scale) |
| Deferred | Olbedo evaluation, learned appearance recovery and view-dependent appearance: external baselines, no installed dependency or Meridian result | [Olbedo](literature/terrain-representation.md#olbedo-2026), [view dependence](literature/terrain-representation.md#view-dependent-appearance), [012G](../earth-lab/riffelhorn-012g-projection-and-illumination.md) |
| Deferred | New Swiss frame imagery/multiview acquisition opportunity; availability, rights, radiometry, lineage and LHN95/LN02 conversion require a separate audit | [Swiss opportunity](literature/terrain-representation.md#swisstopo-2026-opportunity), [current acquisition](../atlas/riffelhorn-data-discovery.md) |
| Closed | Riffelhorn interpolation/refinement of the same cliff evidence; neither 012D nor 012E produced an accepted surface | [Closure rules](../earth-lab/atlas-terrain-representation-synthesis.md#closed--do-not-reopen-without-new-evidence), [012E](../earth-lab/riffelhorn-012e-robust-cliff-heightfield.md) |
| Closed | True-3D cliff topology as an evidence-backed next step; not demonstrated, not universally disproved | [012C](../earth-lab/riffelhorn-012c-raw-lidar-retention.md), [012E](../earth-lab/riffelhorn-012e-robust-cliff-heightfield.md), [closure](../earth-lab/atlas-terrain-representation-synthesis.md#closed--do-not-reopen-without-new-evidence) |
| Closed | Blanket LiDAR detail normals and the finite Riffelhorn visual programme; no conditional normal slot or automatic 012H | [012C](../earth-lab/riffelhorn-012c-raw-lidar-retention.md), [012G](../earth-lab/riffelhorn-012g-projection-and-illumination.md), [closure](../earth-lab/atlas-terrain-representation-synthesis.md#closed--do-not-reopen-without-new-evidence) |

## Default research workflow

```text
Observe a problem -> characterize it precisely -> identify the relevant field
-> review established academic / industry methods -> determine what is solved
-> identify the Meridian-specific unknown -> bounded experiment only if needed
-> record results -> update this knowledge base
```

Do not jump from a visible problem directly to a custom algorithm and an open-ended
experiment sequence. Define the target task, scale, source support, baseline,
controls, failure criteria and stopping rule before implementation. Negative and
inconclusive findings can close a branch; unsuccessful acceptance is compatible
with successful technical validation. No residual or photographic mark is a semantic
object label by itself.

Research work owns terminology, prior art, mature methods, limitations, citations
and genuine gaps. Experimental/implementation work reproduces or adapts a selected
method, tests Meridian-specific behaviour and records deterministic evidence.
Integration is a later explicit decision. Neither responsibility depends on a
particular AI product, session or conversation.

## Contribution and maintenance discipline

For future publication or engineering review, label each contribution: established
method reproduced; established method adapted; engineering integration; genuinely
new method; empirical finding; negative result; or benchmark/evaluation contribution.
Combining disciplines does not establish novelty. Potential novelty requires closest
prior art, precise differences, comparison baselines, failure cases, evidence and
reproduction information. Keep sampling bias, temporal confounds and unavailable
ground truth explicit; do not manufacture an accuracy claim from an internal fit.

When evidence changes, update the synthesis/status here and the relevant literature
section with date and sources. Preserve historical Lab identities and historical
knowledge. Keep this area to an index and one terrain literature record until real
maintenance needs justify another document. External references were checked on
2026-10-03; recheck living standards, release availability and licences before use.
