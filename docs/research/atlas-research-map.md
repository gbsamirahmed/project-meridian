# Atlas research map and fresh-session handoff

Updated 2026-10-03. The 012A–012G terrain-research epoch is **closed** at the
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
