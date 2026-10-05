# Atlas Terrain Hierarchy Contract

Decision: **accepted declaration contract, 2026-10-05**. Baseline `019486f72ae88090b5bcebd7151e6d34b88bb216`, clean main, recorded origin relationship 0/0. This freezes responsibilities and semantic invariants, not a reconciliation algorithm, resolver implementation or production adoption.

Atlas must be able to describe common terrain, zero or more regional families, their multiscale representations and optional derived transitions without claiming that independent surfaces agree. An unresolved boundary is an expressible limitation, not permission to fabricate terrain. Source products remain intact; prepared representations may be synthetic if their identity, operations and limitations are explicit.

## Evidence behind the decision

**MERIDIAN EVIDENCE** refers to the retained bounded observations below, not independent Earth accuracy. These records remain historical; their proposed next experiments are superseded by this contract where completed.

| Evidence | Contract consequence |
| --- | --- |
| [Production ownership audit and visual/analytical separation](../architecture.md#modularity-without-fragmentation), [policy-separation tests](../../scripts/atlas/test_terrain_policies.mjs), [native relief](native-relief-evaluation.md) | Visual representation, analytical sampling and portrayal have separate policies. Rendering parameters are not source metadata. |
| [Mapterhorn evaluation](global-terrain-foundation-evaluation.md) | A service endpoint is not a source, software rights are not dataset rights, sparse children need explicit fallback, catalogue lineage is not point provenance. |
| [Direct regional prototype](riffelhorn-regional-terrain-prototype.md), [earlier reconciliation](riffelhorn-terrain-reconciliation.md), [metadata ADR](terrain-source-product-architecture.md) | Preserve authority, input/revision identity, distinct support geometries and native height semantics. Bounds + URL + priority is insufficient. |
| [Larger Swiss support product](riffelhorn-swiss-support-product.md), [global-reference assessment](global-reference-assessment.md), [common product](copernicus-common-product.md) | Common/reference role differs from best visual detail. Grid/posting, delivery level, information and preparation fidelity are distinct. Finite common coverage is not global completeness. |
| [First hierarchy](terrain-hierarchy-prototype.md), [regional parents](regional-parent-diagnostic.md) | Same-family regional parents reduce protected-point z13→14 change from 39.82 to 0.71 m RMS. These are LOD displacements, not accuracy or registration. Explicit parent identity is required; coarsening through z10 did not produce a natural common handoff. |
| [Reconciliation research](spatial-terrain-reconciliation-research.md), [corridor diagnostic](seam-corridor-feasibility.md), [glacier-aware extent](support-extent-assessment.md) | Stable overlap is valuable but a closed stable island is not universally required. National territory, inventory coverage, source support and transition support differ. Real change must not be fitted away as error. |
| [Detail/broad decomposition](terrain-scale-decomposition.md), [terminal transition](protected-priority-two-band-transition.md) | Detail withdrawal differs from broad-surface accommodation. Derived terrain is first-class. Endpoint continuity passed while synthetic 3.19/1.35 m closed depressions remained. Common z9→derived z10 retained 41.84 m RMS. No generic reconciliation method is accepted. |

**EXTERNAL EVIDENCE:** the existing [metadata ADR](terrain-source-product-architecture.md#bounded-external-metadata-review) retains STAC identity/assets/time/projection, GDAL raster semantics, PROV lineage and CRS identifiers. The two retained methods reviews above distinguish DEM production from graphics-only continuity. This task adds no standards-compliance claim or new literature survey.

**RESEARCH HYPOTHESES / DIRECTIONS:** the declaration contract is now partially implemented by the [first runtime slice](terrain-runtime-selection.md); the second-region plan remains unimplemented. The contract permits testing them without representing unresolved scientific or rendering questions as solved.

## Entities and terminology

| Entity/concept | Responsibility |
| --- | --- |
| `TerrainSource` | Upstream observation/dataset or explicitly scoped selection: authority, release, acquisition basis, horizontal/vertical reference, surface semantics, grid/posting, measurement statements, assets, rights and limitations. Answers “what evidence exists?” |
| `TerrainProduct` | Prepared asset: immutable revision where established, contributors/processing, delivery, support, information ceiling, height semantics, build identity, rights and limitations. Answers “what was prepared?” |
| `TerrainRepresentation` | Consumption form at a declared level/context, referencing an exact product. Answers “what portrays terrain here?” Current heightfield interface is reused; `other` requires an explicit form and adapter-contract reference. Mesh/photogrammetric/3D adapters are not implemented. |
| `TerrainFamily` / `RegionalTerrainPyramid` | A coherent representation family with named level scheme, available levels, parent identities/operations and per-level support. A regional family includes regional-derived parents where available; no requirement for every level or a closed island. |
| `TerrainHierarchy` | One common family, regional families, optional transition families, product bindings, separate composition and selection policies, fallback and limitations. It describes selection/composition responsibilities; it executes neither. |
| `TerrainCompositionPolicy` | Recorded operations, exact inputs, support/protection, explicit height-use policy, contribution reconstruction, validation and limitations for a derived representation. No universal formula is prescribed. |
| Source-derived terrain | From one identified source family through declared processing/resampling/generalisation; not synonymous with measured or accurate. |
| Regional detail residual | Higher-frequency representation information relative to a declared generalisation operator; not automatically independent observations, source error or truth. |
| Regional-derived parent | A coarser summary in the same regional family, with its operation and support declared. |
| Derived transition terrain | Intentionally composed/modified to let source families coexist; may be useful without being authoritative physical terrain. |
| Render-only continuity | Portrayal such as morphing/skirt/crack hiding that does not reconcile the underlying terrain evidence. |

Common and regional are **hierarchy roles**. Source-derived and derived-transition are **origin classes**; unresolved origin remains representable with a reason. A role never implies accuracy, datum compatibility or complete lineage. A source can produce several products; a product can supply several levels. A synthetic family can have its own internally related parents. Family identifiers group declared representations; unknown external lineage/coherence cannot be upgraded merely by assigning an identifier.

## Invariants, policies and implementation details

| Architectural invariant | Current policy/evidence | Implementation detail outside the contract |
| --- | --- | --- |
| Recoverable source/product identity and rights | Copernicus is the working common-reference candidate | Production uses AWS Terrarium; current experimental tiles are XYZ PNG |
| Visual terrain is separate from analytical elevation | Both production policies currently use AWS independently | Analytical z15, worker/cache settings and route calculations |
| Regional LOD family identity and derivation are explicit | Prefer eligible regional-derived parents before crossing families | Swiss diagnostic z10–13; no required universal zooms |
| Spatial eligibility and scale eligibility are separate | Distant common terrain, supported close regional detail | No universal camera-zoom gate or 1.5/3/4 km bands |
| Composition requires explicit operations/height/provenance policy | Terminal two-band experiment is partial, not adopted | Its equation, quintic controls and radius parameters |
| Continuity and morphology/accuracy are independent assessments | Synthetic pits and lower handoff remain unresolved | No accepted smoothing operator, seam width or pit repair |
| Representation choice and rendering portrayal are separate | Keep current MapLibre architecture | Single active terrain source, mesh128, IGOR, exaggeration1.45, projection guards |

## Spatial and scale support

Source coverage is an upstream claim/selection. Product coverage is the deliverable extent. Valid support is purpose-scoped evidence of usable data. Protected interior is an explicit constraint on composition; legitimate coarse summarisation is not fine-source mutation. Transition support is available/assessed overlap for a specified operation, never an automatic validation of a join. Each uses the existing `SpatialArea`/`Knowledge<SpatialSupport>` model; polygons can be non-island/multipart or asset-backed masks. A national border is none of these by default.

Each hierarchy level additionally declares **complete / partial / absent / unknown** support over its documented envelope. Partial support requires a referenced partition separating complete, partial and absent cells/tiles; fraction means observational support, not confidence. The valid-support reference must resolve level-specific geometry/counts. An observed-subset parent mean is not a complete-cell height. First raster adapters must decline partial/unknown terrain where complete support is required, then use declared fallback. No extrapolation or zero-height fill is implied.

| Quantity | Canonical location/meaning |
| --- | --- |
| Distributed grid/posting | `TerrainSource.resolution.gridSpacing`, with units and CRS |
| Measurement resolution | `measurementResolution`, explicitly known/unknown; never derived from grid spacing |
| Effective information scale/ceiling | Product `sourceInformation` and scoped family `informationCeiling`; descriptions need source/processing evidence |
| Delivery level | Family level ID/order and declared scheme; increasing order means increasing detail only within that scheme |
| Delivery sample spacing | Scoped `sampleSpacing`; depends on CRS, latitude, tile dimensions and processing |
| Generalised parent | Level derivation plus declared parent operation, not additional observations |
| Overzoom | Explicit family permission/description; resampling adds no information |
| Rendered mesh/screen error | Renderer/adapter responsibility; camera zoom, geometry levels and hillshade levels can differ |

A regional family generally enters as an internally coherent pyramid, rather than fine children under an unrelated common DEM. Missing parents are permitted, but must be explicit. Same coherent `sourceFamily` identity means **within-family LOD refinement**, not proof of zero numerical change. A change of coherent family means **source-family handoff**, even if delivery levels are adjacent. Shared upstream dataset names alone do not certify a coherent family: derivation and support evidence must establish it. Parent graphs must be acyclic. Cross-scheme levels require policy/adapter interpretation; the contract does not compare their numeric orders.

## Heights, surface meaning and time

Reuse known, unknown, preserved, transformed and heterogeneous product-height states. Optional `HeightReference` details state ellipsoidal/orthometric/normal/national-system/other height kind and geoid/model where established. Absence is unknown; a datum identifier/name must not be used to invent transformation equivalence. Existing transformations retain source/target reference, method, accuracy knowledge and limitations.

DTM, DSM (including an explicitly described edited DSM), heterogeneous mosaic, other and unknown surface meanings remain first-class in `TerrainSurface`. Height reference and surface meaning are separate. Product encoding does not change either.

Products can enter the catalogue with unknown or different heights. **Representability is not permission for numerical fusion.** Composition must declare no numerical combination, a documented common frame, or explicitly heterogeneous native-height use. The currently demonstrated heterogeneous path is synthetic **visual representation only**; it must not be labelled a geodetically harmonised or analytical product. A declared common-frame product needs lineage/transformation evidence and limitations; the enum is not scientific approval.

Source `acquisition` remains separate from release, access and product generation time. Optional `TerrainTemporalSupport` supplements that lineage with known/unknown/heterogeneous epoch descriptions, spatial epoch mapping and classified change-mask references. Absence means no additional established temporal evidence. Product-level epoch claims must resolve contributors or retain uncertainty. A glacier inventory/change proxy is not a measured DEM-error field. Temporal priority, if used, must appear in composition/selection policy; no “newest is always true” rule is imposed.

## Identity, contribution and validation

Prepared bindings pin **product ID/revision + preparation record + frozen content-manifest SHA-256**. Hash scope explicitly distinguishes manifest-file bytes from a declared canonical inventory. The referenced evidence record is not itself claimed to have that hash. A recipe hash does not freeze an expanding lazy tile cache. The historical terminal recipe and final sparse inventory have distinct identities; the example binds both, without rewriting those records. Adding terrain or materially changing processing/content requires a new prepared revision. Unknown/mutable external services use `external-unpinned` with a reason; they cannot claim immutable prepared status. The hierarchy itself also has an ID/revision. Cache keys in a later implementation must include prepared revision/content identity, representation level and relevant policy revision. Updating scoped validation assessments alone does not change prepared content; it requires a new hierarchy/evidence declaration, not a fictitious terrain rebuild.

Existing lineage retains immediate source/product contributors, complete/partial/unknown contributor lists, processing identities/parameters/software and spatial mapping. Uniform single-family products may use product-level lineage. Spatially varying substitution or composition needs a contribution map/declared reconstruction sufficient to identify local contributors, exact revisions and processing roles. Masks may encode categorical identity, composition weights or signed operators. None imply confidence, probability or accuracy. A weight map alone is insufficient if reconstruction also requires broad/detail fields or parent operations. Support/change masks retain their independent meanings.

`TerrainValidationEvidence` records category, scoped state, evidence references and limitations. Categories separate preparation fidelity, Earth accuracy, source preservation, parent consistency, numerical continuity, morphology, edges, visual continuity, navigation and provenance. States are not-assessed/passed/qualified/failed; assessed states require references. No universal confidence/quality score or `continuous=true` can approve a product. Passing a semantic validator proves declaration consistency, not terrain fidelity, rights clearance, topology or safe composition.

## Selection, fallback and rendering boundary

A future resolver may consider location/footprint, requested representation scale/scheme, available levels, support, information ceiling, explicit ordering/eligibility policy, provenance needs, prepared transition availability and fallback. Structured source/product epochs and temporal policy can be consulted. A later adapter may add viewport/screen-space-error inputs. The current context type does not require a viewport-aware resolver or invent a camera-to-level mapping.

Eligibility must check **spatial and scale support**; ordering only breaks ties among eligible families. Footprints, not just their centre, matter when a representation crosses support. Boundary coexistence needs an explicitly declared policy and limitations; an unresolved handoff cannot silently count as validated refinement.

| Condition | Declared first-slice behaviour |
| --- | --- |
| Eligible regional level exists | Select the eligible representation under the declared policy; report product/family identity |
| Fine child missing | Search eligible same-family parents; crossing to common is an explicitly identified handoff |
| Regional absent/unsupported at requested scale | Common/generalised terrain, or explicit unavailable if policy disallows it |
| Prepared transition unavailable | Declared common fallback or unavailable; never generate an implicit blend |
| Common unavailable | Report unsupported/unavailable; no fabricated global surface |
| Common overzoom allowed | Retain information ceiling and overzoom classification |

Selection is visual policy. The existing analytical sampler retains ownership of numeric route elevation, gradient/ascent/descent, movement timing and Weather sampling altitude. A visual representation never becomes those inputs implicitly. Changing analytical policy needs its own decision and validation.

Atlas data/terrain owns declarations; the renderer adapter owns delivery decoding, mesh resolution, portrayal, projection and continuity mechanisms. A render-only mechanism is identified by a renderer contract and cannot relabel synthetic terrain as observed. Existing one imperative MapLibre lifecycle, bundled worker, style restoration, terrain/projection order, satellite behaviour and controller boundaries remain intact. The model imports neither React, MapLibre, Weather nor Traverse.

## Concrete cases and unresolved limitations

`terrainHierarchyExamples.ts` builds typed examples from the existing lightweight records; it is not a production registry. AWS is an honest external-unpinned common visual example with unknown hosted height/lineage. Frozen Copernicus is a source-derived local common family preserving EGM2008/edited DSM, z8–13 delivery and explicit overzoom. Swiss support plus its separate regional-parent product form one LN02 regional family with per-level complete/partial support and protected intent. The terminal transition is a separate synthetic family, signed reconstruction policy, heterogeneous heights and independent passed-continuity/failed-morphology evidence. A synthetic second-region DTM fixture uses British National Grid geometry, unknown unverified heights/rights/epoch and no transition; it is not acquired/processed Wales terrain.

The contract preserves these unresolved limits:

- **Morphology:** terminal synthetic closed depressions approximately 3.19/1.35 m; no generally accepted reconciliation algorithm.
- **Height:** native or uncertain references are representable; safe numerical fusion needs explicit, supported policy.
- **Coarse handoff:** common z9→derived z10 approximately 41.84 m RMS; not ordinary same-family LOD and not solved here.
- **Spatial reconciliation:** a stable surrounding corridor is preferred, not mandatory; no universal seam/transition method. Protected constraints and source support cannot be erased to obtain continuity.
- **Time:** glacier/change terrain can be genuinely different physical states; agreement is not accuracy and disagreement is not automatically error.
- **Rendering:** close-camera clipping/faceting occurs in matched pure-common controls; cause unknown and separate from hierarchy declarations.
- **Coverage/geometry:** local common missing lower/global perimeter/ocean/polar support persists. True 3D/overhang/photogrammetric adapters remain future work.

## Bounded first implementation — runtime slice implemented

Status: [registry, pure selector and heightfield delivery adapter](terrain-runtime-selection.md) implement the bounded slice. Production resolves the same AWS service through an explicit legacy compatibility policy; no regional or transition product is adopted. The following frozen plan remains the scope boundary.

1. Register one common heightfield family and zero or more regional heightfield pyramids using these records, pinned revisions and explicit per-level support. No new fusion operator.
2. Implement a pure deterministic selector over explicit requested level/footprint and declared eligibility/order. Return product/revision, family/level, derivation/overzoom, support, fallback reason and within-family versus handoff classification. Unknown/partial unsupported requests decline honestly. Test tie-breaking, empty regional sets, missing child/parent, missing common and revision changes.
3. Adapt selection to the existing single terrain delivery path in isolated evaluation tooling. Preserve regional-family parents; do not call unrelated common fallback continuous regional LOD. No viewport-aware framework or production source change in this slice. Unresolved boundary policies may return common/unavailable instead of asserting acceptable coexistence.
4. Optional prepared transitions may be registered through the same product binding/policy contract; availability must not imply adoption. Terminal Riffelhorn failure evidence remains attached. Do not implement a new reconciliation method.
5. Validate metadata/support/provenance and existing application boundaries without external-data CI requirements. Review adoption separately. Stop at a working bounded mechanism and the second-region proof below.

## Wales/Tryfan proof — completed

The [completed real Welsh proof](tryfan-second-region-proof.md) required no contract/runtime redesign. Its native vertical datum is honestly unknown, support normalization is preparer-owned, and unreconciled source handoff is explicit. The original proof requirements follow as the maintained acceptance record: use one justified Welsh regional DTM selection after independently verifying authority, source assets/revision, actual horizontal/height references, acquisition/rights and support. Do not assume the synthetic fixture establishes those facts or reuse LN02. Prepare an immutable regional pyramid through the proven preparation boundary with its own level/support declarations; do not reopen terrain-method research.

Acceptance: register it without Switzerland-specific code/schema changes; resolve common/eligible regional levels deterministically; reuse valid same-family parents and explicitly identify common handoffs; recover source/product/revision and applicable rights; preserve common outside support; decline unsupported/unknown requests; retain information/overzoom and change semantics. Test a second region alone and coexistence of two registered regions/tie policy. Optional transition absence must work without inventing a blend. Normal analytical AWS, Weather/Traverse results and map lifecycle must remain unchanged. Then stop; failures should identify a contract/implementation defect or a documented reconciliation limitation, not launch another research programme.

## Acceptance responsibility map and validation

| Acceptance questions | Responsible contract |
| --- | --- |
| 1–3 upstream evidence/prepared asset/form | Existing source/product metadata + representation product reference |
| 4–6 validity/scales/information ceiling | Independent spatial roles, per-level support, scheme/derivation and ceiling/overzoom |
| 7–8 heights/surface/acquisition/change | Height states/reference details, surface semantics, source acquisition and temporal supplements |
| 9–10 family/refinement versus handoff | Coherent family identity, explicit parent graph/operation and classification |
| 11–12 source-derived/synthetic/contributors/policy | Product binding origin, lineage and separate composition policy/reconstruction |
| 13–14 protection/transition availability | Optional protected support, explicit transition families/support; absence normal |
| 15–17 missing regional/fine/common | Declared fallback and eligibility policy; unsupported state not fabricated data |
| 18–20 rights/evidence/limitations | Existing rights, scoped validation categories and retained product/family/hierarchy limits |
| 21 provider neutrality | Real retained cases plus synthetic second-region typed fixture |
| 22 visual/analytical independence | Existing analytical policy; no hierarchy/runtime import or implicit migration |

Code lives alongside the earlier foundation in `src/atlas/terrain/metadata/terrainHierarchy.ts`, `terrainHierarchyValidation.ts` and `terrainHierarchyExamples.ts`. Existing `terrainMetadata.ts` gains only compatible optional height/time detail. Validators check owned typed declarations, exact revision references, parent graphs, support claims, explicit synthetic permission/maps and immutable reuse; they are not an untrusted-input parser, geometric containment engine or resolver.

Focused validation: `node --test scripts/atlas/test_terrain_hierarchy_contract.mjs scripts/atlas/test_terrain_metadata.mjs scripts/atlas/test_terrain_policies.mjs`. Type/lint and application-only bundling require no experimental assets. No external terrain was read, regenerated or acquired. No further Riffelhorn elevation-method experiment is performed or recommended. The bounded runtime slice is now implemented; the [Wales/Tryfan proof](tryfan-second-region-proof.md) is complete. The regional elevation foundation is established; imagery/appearance is the next separate programme boundary. No reconciliation or further Riffelhorn elevation-method work follows.
