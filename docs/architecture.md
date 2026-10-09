# Meridian architecture contract

This document records Meridian's current architectural direction. It defines the
rules for implementation and records the completed storage migration and current
active application ownership. Historical experiments retain their original identities.

## Repository status and historical markers

`main` is the canonical active Meridian development line. Phase 5 is complete at
`6f6491c6cb72b203e71693318a719b227bf2c662`, marked by the annotated
`phase-5-complete` tag. The App / Atlas / Weather / Traverse ownership below is the
current implementation, not a proposed next refactor.

Phase 6 is complete. Phase 6B fast-forwarded local main without a merge commit,
content reconciliation or history rewriting. Phase 6D validated and normally
published `8a9bdee956d9e881639ce20a99ccd337a0cf3fc4` to `origin/main`, together
with the annotated `phase-5-complete` tag. Both local and remote main are canonical;
historical branches remain frozen. Phase 6 ended with 6D; there is no Phase 6E.

Phase 7 consists only of 7A clean-start reproduction and 7B foundation corrections,
validation and checkpoint. Phase 7A is complete as an experiment. Phase 7B remains
subject to the final independent clean-start acceptance gate before publication;
there is no Phase 7C and no new application architecture work in this stage.

The retained historical refs have these meanings:

| Ref | Meaning |
| --- | --- |
| `earth-lab` | Frozen historical development line through Tryfan/Earth Lab and the architecture/storage cleanup, at the Phase 5 checkpoint. Not required for ongoing development. |
| `legacy/journey-weather` | Historical pre-world-pivot lineage, at `6383ed2`. |
| `pre-world-pivot` | Final Journey/Forecast state before the Earth-world pivot. |
| `pre-atlas-restructure` | Protected Earth Lab checkpoint before the architecture/storage restructuring. |
| `phase-5-complete` | Completed architecture cleanup before Phase 6 repository-semantic changes; points to the Phase 5 commit, not the later documentation commit. |
| `v0.4-terrain` | Earlier terrain milestone, retained unchanged. |

No historical branch or existing tag is renamed, moved or deleted. Branch deletion
is a separate optional decision after Phase 6, not a reunification requirement.
Historical experiment names, frozen identities and the renderer bootstrap remain
traceable from main. The [development log](development-log.md) records the audit and
fast-forward; the historical Phase 4/5 plans and dated entries retain their original
planning and review context.

## Product vocabulary

- **Meridian** is the overall ecosystem and platform.
- **Meridian Core** means only stable infrastructure or concepts with multiple real
  consumers. It is a boundary, not a miscellaneous package or a directory that must
  exist today.
- **Atlas** represents and explores the physical world: terrain, elevation, surface
  evidence, imagery and spatial reference locations.
- **Weather** represents atmospheric observations, forecasts and visualisation.
- **Traverse** is the provisional product name for route, journey and movement
  planning. Technical code should continue to use precise terms such as route, path,
  waypoint, segment and journey.
- **Tryfan** is Atlas's first reference location. It is data and a validation target,
  not an architectural layer.
- A **Reference Renderer** is an environment used to inspect and validate Atlas
  representations. It consumes Meridian representations; it does not define them.
- **Lab NNN** and **Experiment** identify bounded historical investigations. Existing
  Earth Lab names remain part of their provenance.

Product names define ownership boundaries, not every implementation term. Traverse
may be renamed without renaming generic route concepts. Historical Lab identifiers
remain stable even when useful implementation is later promoted into shared Atlas or
renderer infrastructure.

## Modularity without fragmentation

The design test is: **a change inside one domain should have the smallest reasonable
blast radius outside that domain**. Prefer cohesive modules with explicit
responsibilities and small stable contracts. Introduce a package or interface only
when a real ownership, consumer or replacement boundary exists.

The current React application remains one deployable client-side application. Atlas,
Weather and Traverse are conceptual boundaries inside it. Separate deployable apps,
microservices and a speculative package hierarchy are not justified yet.

Phase 5B organised the active TypeScript code under `src/app`, `src/atlas`,
`src/weather` and `src/traverse`. Phase 5C then established the three frozen domain
boundaries without splitting the deployable application:

- Atlas owns the concrete MapLibre lifecycle and reports style-ready and renderable
  lifecycle states to app composition.
- Weather owns a concrete map controller, Weather layers and provider-specific route
  sampling. A pending Weather update is retained until Atlas reports a renderable map,
  so terrain/style transitions cannot permanently lose a requested render.
- Traverse owns a concrete route-map controller and route-relative interpretation of
  provider-neutral Weather samples.
- App composes those modules, adapts a Traverse schedule to Weather's narrow forecast
  coverage window, and orchestrates route Weather sampling without exposing GFS or
  numeric-tile implementation to Traverse.

Phase 5D removed the obsolete mixed configuration, ordering and type compatibility
files plus the empty SearchBar. Mixed overlay selection now lives explicitly in
`app/state/mapOverlayState`; basemap types remain Atlas-owned. Traverse owns its
analysis-mode choices and no longer imports app control metadata. Combined
status/inspection, ForecastTimeline and ForecastWorkspace remain app composition;
Weather owns their forecast/coverage models and Atlas owns location identity.

Weather's physical atmospheric catalogue and field IDs live in
`weather/types/atmosphericFields`, independent of manifest validation. Traverse's
base coverage and field-key types live in `traverse/types/routeConditionBase`;
aggregate conditions depend on derived results, which depend on those base types.
Both audited type cycles are resolved without duplicating types or weakening them.

The final active roots are `app`, `atlas`, `weather`, `traverse`, `main.tsx` and
`index.css`. App may compose all domains; domains do not import app. Atlas imports
neither Weather nor Traverse, Weather imports neither Traverse nor JourneySchedule,
and Traverse uses Weather's provider-neutral sample types, never its data/map
implementation. Atlas map anchors/types are intentionally reusable by domain map
controllers. `src/shared` remains absent because no current responsibility has a
justified domain-neutral owner. The [Phase 5 architecture plan](phase-5-architecture-plan.md)
records the final validation and bounded completion criteria. Phase 5 ends with 5D;
historical experiments and renderer source are outside this refactor.

Atlas configures visual terrain and analytical elevation independently:
`src/atlas/map/visualTerrainConfig.ts` owns MapLibre DEM delivery and credits;
`src/atlas/terrain/analyticalElevationConfig.ts` owns the numeric sampler's fixed
Terrarium/XYZ/Web Mercator, 256-pixel, z15 contract. Both currently select the same
AWS Terrarium dataset by policy, not architectural necessity. Visual source changes
must not silently change analytical elevation. Analytical source changes require
explicit assessment of route profiles, gradients, timing, arrival-time Weather
sampling and derived route conditions. App still orchestrates sampling; Traverse
continues to receive provider-neutral numeric terrain profiles.

Atlas visual presentation retains native MapLibre IGOR relief, map-anchored at
315°, with a continuous zoom-strength curve peaking at 0.54 at z11 and tapering
to 0.30 from z15. Satellite continues to suppress hillshade. Geometry exaggeration
remains 1.45; no physical surface lighting or custom terrain material is implied.
The bounded [native relief evaluation](atlas/native-relief-evaluation.md) records
the frozen baseline, alternatives, cameras, evidence and limitations. This policy
changes presentation only, independently of both terrain source policies.

The bounded [global terrain foundation evaluation](atlas/global-terrain-foundation-evaluation.md)
verified Mapterhorn and found useful regional visual-source gains, while retaining
the AWS production default. Its source substitution exists only in evaluation
tooling; no runtime provider selector or source resolver is implied. Sparse delivery,
vertical/water semantics, attribution and point-provenance limits remain explicit
inputs to a later adoption decision. Analytical elevation stays independently AWS.

The bounded [Riffelhorn regional prototype](atlas/riffelhorn-regional-terrain-prototype.md)
prepares four retained official swissALTI3D TIFFs into an attributed, versioned
Terrarium product outside Git. Evaluation-only tooling supplies one composed DEM
endpoint because MapLibre does not automatically combine regional/global terrain
sources. Interior detail improves, but the unadjusted LN02/AWS crop boundary creates
false walls and unacceptable discontinuities. This establishes neither a production
Swiss source nor a general resolver architecture. Normal visual and analytical AWS
policies, rendering and client-only application behavior remain unchanged.

The bounded [Riffelhorn reconciliation investigation](atlas/riffelhorn-terrain-reconciliation.md)
finds broad and fine-scale product disagreement, not a justified constant datum
shift. Tested overlap controls improve continuity while distorting the collar or
regional interior; no reconciled product is accepted. A protected regional interior,
adequate source support/overlap, height-reference accounting and contributor/processing
metadata are prerequisites for a later composition decision. The 2 km research
crop is not an accepted production source boundary. Production remains unchanged.

Atlas's [terrain source/product architecture](atlas/terrain-source-product-architecture.md)
now records upstream datasets separately from derived delivery products. Owned types,
validation and four evidence examples live in `src/atlas/terrain/metadata/`, beside
production configuration. Source/product identity, height/surface semantics, scoped
coverage/support, resolution, lineage, revisions and rights remain independent of
MapLibre visual style and the analytical sampler. Unknowns are explicit; immediate
contributor completeness does not imply complete measurement lineage. No production
module adopts this metadata yet. It establishes no resolver, accepted seamline,
reconciled terrain, new provider or acquisition requirement on normal startup.

The bounded [larger Swiss support product](atlas/riffelhorn-swiss-support-product.md)
actively uses the metadata foundation for 100 official 2024 swissALTI3D tiles,
a protected benchmark interior and an unreconciled regional surface. Full native
source coverage and per-zoom delivery support differ; transition support remains
unknown. One uniform immediate contributor does not imply uniform measurement
technology or epoch. Evaluation-only delivery omits unsupported tiles instead of
inventing terrain; coarse/edge gaps remain a later composition requirement. This
is a data asset, not production regional integration or an accepted AWS reference.

The bounded [global-reference/stable-overlap assessment](atlas/global-reference-assessment.md)
recommends published Copernicus GLO-30 as a candidate accountable common/coarse
reference, distinct from best available visual terrain and analytical policy.
The tested public COG selection is explicitly the older 2021 distribution;
its known EGM2008 semantics do not resolve AWS's unknown hosted height lineage.
Independent stable-terrain candidates support a tighter local relationship,
with uneven support and important coarse-ridge/ice residuals. No registration
correction, accepted transition, terrain hierarchy or production source change
follows from this assessment. Existing Atlas metadata describes the retained
source, COG derivative and separate height diagnostic without a model extension.

The bounded [Copernicus common/coarse product](atlas/copernicus-common-product.md)
now prepares six frozen 2021 COG inputs into two complete z8 roots and their
z9–13 descendants. EGM2008 heights are preserved; unencoded mean aggregation
produces deterministic parents, and finer renderer zoom adds no observations.
Owned source/product metadata describes scoped support and immutable lineage
without production adoption. Local terrain is coherent inside coverage, but
finite perimeter gaps and absent z0–7/global water support remain explicit.
This is the coarse-side asset for a later bounded hierarchy evaluation, not a
Swiss join, general resolver, complete global hierarchy or production migration.

The subsequent [bounded Copernicus/Swiss hierarchy](atlas/terrain-hierarchy-prototype.md)
retained native EGM2008/LN02 heights and exact selected Swiss tiles, using actual
per-level delivery support and a separate regional-detail gate. It demonstrated
usable coarse context and useful close detail, but neither hard substitution nor
scale gating established safe spatial or parent/child continuity. Metadata can
represent its contributors and heterogeneous heights without a new model extension.
Per-level support, actual geometry/relief loading scales and parent compatibility
are now empirical requirements; no general hierarchy algorithm or production
resolver is accepted. Production and independent analytical AWS remain unchanged.

The [regional-parent diagnostic](atlas/regional-parent-diagnostic.md) subsequently
derived Swiss coarse parents with explicit full/partial/absent support. At the
same protected points, Swiss-derived13→Swiss14 reduces the source-change RMS from
39.82 to0.71 m without altering fine terrain. Same-level common disagreement
persists through10; complete regional tiles cease below12. The large first
delivered source change moves to11→12 and geographic walls remain. A supported
regional pyramid is justified for internal LOD consistency, while spatial/common
handoff remains a separate unresolved problem. No general contract, source
fusion, production dependency or height correction is accepted.

The [spatial reconciliation research review](atlas/spatial-terrain-reconciliation-research.md)
keeps three questions distinct: elevation/reference reconciliation, construction
of a derived terrain representation, and render-time continuity. A regional
pyramid supports internal LOD but does not establish a spatial join. Common
height semantics and an accepted registration/error model must be explicit before
claiming numerical fusion; no correction or blend is accepted here. The suggested
next seam-corridor feasibility diagnostic is research, not a production seamline
or hierarchy contract. Current metadata is sufficient without extension.

### Atlas Terrain Hierarchy Contract

The canonical [Terrain Hierarchy Contract](atlas/terrain-hierarchy-contract.md)
now freezes declarations for common/regional families, coherent regional pyramids,
per-level spatial/scale support, exact product revisions, height/time semantics,
optional derived transitions, scoped validation evidence and explicit fallback.
It extends the existing Atlas metadata foundation in `atlas/terrain/metadata`;
a [small registry, pure selector and MapLibre adapter](atlas/terrain-runtime-selection.md)
now resolve current AWS visual delivery without changing its output. Regional
eligibility, same-family parent reuse and explicit common/unavailable fallback are
tested against canonical metadata; composition remains unimplemented.

Within-family LOD refinement is distinct from source-family handoff. Synthetic
terrain requires recoverable processing/contribution identity; numerical continuity
does not establish morphology or accuracy. The final Riffelhorn pits, unresolved
coarse handoff, heterogeneous native heights and independent close-camera rendering
limitation remain explicit. Source products stay immutable; rendering owns portrayal.
Analytical elevation, Weather/Traverse and production AWS remain independent and unchanged.

The contract contains bounded first-implementation and Wales/Tryfan proof plans.
The runtime slice and [bounded Wales/Tryfan second-region proof](atlas/tryfan-second-region-proof.md) are complete. The real Welsh pyramid uses the unchanged registry/selector/adapter with normalized assessed support, explicit parent/fallback and unknown native vertical semantics. Regional elevation portability is established; reconciliation remains unresolved. No further elevation benchmark is recommended. The next programme boundary is imagery/appearance under a separate task. Production and analytical AWS remain unchanged.
Earlier investigation summaries above retain
their historical decisions; no further Riffelhorn elevation-method experiment follows.

### Atlas appearance architecture — proposal

The regional elevation foundation is established; its unresolved reconciliation,
height, coarse-handoff and rendering limits remain recorded without reopening
experiments. The [appearance baseline and architecture](atlas/appearance-baseline-and-architecture.md)
now separates geometry, source observations, prepared appearance and rendering.
The decision is a separate AppearanceHierarchy sharing small identity/provenance,
rights, spatial and scale primitives with terrain, rather than a universal terrain
framework. AppearanceSource/Product/Representation and regional imagery families
need their own bands/colour, acquisition/illumination, visibility, processing and
geometry-revision dependencies. Corrected and synthetic appearance must be
identifiable; orthophoto RGB is not albedo. These are architecture declarations,
not implemented generic imagery types, registry or selector. The isolated baseline preparation is experimental.

Production remains MapTiler satellite-v2 through the existing satellite lifecycle,
with IGOR suppressed in satellite mode, independent elevation colour overlay and
unchanged AWS visual/analytical terrain. The [source-derived SWISSIMAGE baseline](atlas/swissimage-source-derived-baseline.md)
is now complete: an immutable four-tile imagery pyramid, matched Atlas captures and
source/display probes demonstrate useful regional appearance, persistent steep
projection limitations and unknown acquisition geometry/Sun. The traceable opposed
close patch does not reproduce Unreal black crushing. Experimental preparation and
delivery are isolated; no AppearanceHierarchy runtime or correction was introduced.
The bounded [acquisition/multiview-support assessment](atlas/riffelhorn-observation-support.md)
is PARTIAL: two 2023 strip footprints cover the frozen patches, but actual calibrated
scan-line geometry and visibility remain unavailable. Newer frame metadata is
separate and supplies no local candidate in the assessed catalogue. That assessment
remains a completed limitation. A separate
[Swiss 2026 frame benchmark](atlas/swiss-multiview-benchmark.md) now freezes two
observations with public camera geometry; actual pixels are deferred and require
individual provisioning/quotation. No contact/order or source pixels acquired. Observation
provenance must accommodate time-dependent pushbroom geometry as well as frame
poses; no appearance runtime or TerrainHierarchy change is introduced.

### Atlas multiscale representation — research status

The [baseline](atlas/multiscale-representation.md), [negative scale-separated relief
control](atlas/scale-separated-relief.md) and [information-aware display synthesis](atlas/information-aware-display-selection.md)
complete the current bounded multiscale research programme. Identity/support/eligible
levels/coherent parents remain TerrainHierarchy responsibilities. Camera projection,
actual CSS/framebuffer sampling and local directional footprints belong to a separate
optional view-local diagnostic/policy boundary. Eligibility does not guarantee useful
additional information at a particular view. Unknown effective source resolution and
perception prevent automatic quality ranking from nominal sampling ratios.

No runtime/schema change is adopted here. Future numerical metadata must retain scope,
units, evidence kind, contributor revision and unknowns. AppearanceHierarchy remains
a separate proposal; distributed pixels, nominal GSD/information and surface-projected
orthophoto support are distinct. Renderer filtering/portrayal cannot create observations.
No universal three modes/zoom thresholds, replacement IGOR, zoom blocking or blanket
geometry generalisation is justified. Morphology preparation is not activated.
Production, analytical elevation, Weather/Traverse and lifecycle remain unchanged.
Elevation is closed; multiview awaits external provisioning. No further foundational
multiscale experiment is required before moving to another separately authorised area.

### Atlas physical surface semantics — domain review

The [physical-surface review](atlas/physical-surface-semantics.md) and
[source inventory](atlas/physical-surface-sources.md) propose independent cover/exposure
properties, physical features/vertical structure and time-qualified state, with
source-native semantic evidence and mapping lineage. This is a candidate decomposition,
not a frozen contract or runtime. Cover is distinct from use; fractions, classification
probabilities and validation accuracy have different meanings. Layer/support/time and
unknowns must survive interpretation. Water extent, network identity and water geometry
are distinct; canopy/ground and snow/substrate can coexist.

No semantics are attached to TerrainProduct or AppearanceProduct. Small provenance
primitives may eventually be shared; physical claims, geometry, observations,
processed appearance and portrayal stay independent. Property-compatible regional
fallback needs explicit ontology/epoch/grain/rights, not automatic provider priority.
Human land use, full ecology/subsurface models, hydrological simulation and application
suitability remain separate. Dynamic physical state is not automatically Weather-owned.
The source-native comparison is complete; the water-feature/state check and then
a minimal evidence contract remain separate next work. No runtime is adopted here.
Production is unchanged; multiscale stays closed and multiview stays parked.

The [bounded source-native semantic comparison](atlas/source-native-semantic-comparison.md)
now supplies empirical requirements for that proposal: independent properties and
native evidence survive mixed habitat, glacier/debris and substrate/cover contrasts.
No semantic entities or runtime are frozen. The separate water-feature/state check
remains next, before a minimal evidence contract.

The conceptual relationship is:

```text
                         MERIDIAN
                             |
                     MERIDIAN CORE
              shared infrastructure/concepts
                             |
                   +---------+---------+
                   |                   |
                 ATLAS          other future domains
            physical world
                   |
             +-----+-----+
             |           |
          WEATHER     TRAVERSE
```

The dependency rules are more important than the diagram:

- Atlas must not depend on Weather or Traverse.
- Weather may consume narrow Atlas world, coordinate and rendering contracts.
- Traverse may consume Atlas terrain/world contracts.
- Traverse may query Weather through a narrow position-and-time sampling contract.
- Traverse must not know GFS-specific acquisition or tile details.
- Weather must not depend on Traverse scheduling or UI models merely for convenience.
- UI components should not become the canonical domain or data model.
- Provider acquisition, canonical representation, analysis and rendering should stay
  separable where the implementation presents a real replacement boundary.
- Shared/Core code is appropriate only for stable concepts with multiple real
  consumers. Keeping a small duplication temporarily is preferable to a false
  abstraction.

## Representation and source-of-truth pipeline

Meridian's conceptual pipeline is:

```text
source observation
  -> normalized / canonical data
  -> inference / analysis
  -> reconstruction
  -> renderer-neutral Meridian representation
  -> renderer
  -> pixels / user experience
```

A canonical representation is a stable, documented Meridian interpretation of source
information. It is not defined by an Unreal package, a browser texture, or another
renderer-specific asset. Renderers may change without changing scientific identity.

Every product and report must retain its role:

- **Observed**: values supplied by an identified source observation.
- **Derived**: deterministic quantities calculated from observations or canonical
  data.
- **Inferred**: uncertain interpretation supported by evidence.
- **Reconstructed**: plausible spatial or visual detail generated below the
  information resolution of the evidence.
- **Rendered**: platform-specific assets and pixels.

Missing data is not zero. Inferred or reconstructed values must not be relabelled as
measurement. Reconstruction may add plausible sub-resolution detail, but provenance
must say that it was reconstructed.

Tryfan demonstrates the full chain: LiDAR, Sentinel, habitat and geology are source
evidence; Labs 005-008 derive and audit interpretation; Lab 009 reconstructs
continuous renderer controls; renderer-neutral rasters and packages feed Unreal. The
preserved Unreal project is the **Tryfan Reference Renderer**, not Atlas's canonical
world model. Future web, mobile or other renderers should consume equivalent
renderer-neutral representations.

## Repository and external-storage contract

`project-meridian` contains version-controlled implementation, lightweight
configuration, manifests, tests, documentation and carefully justified durable
assets. Large observations, derived products, experiment outputs and caches do not
enter Git merely because code consumes them.

Repository tooling resolves external roots through `scripts/meridian_paths.py` and
its small Node counterpart `scripts/meridian_paths.mjs`:

- `MERIDIAN_DATA_ROOT`: non-private Meridian source, derived, experiment, cache and
  scratch data.
- `MERIDIAN_PRIVATE_ROOT`: personal or user-specific data such as private
  activities, routes and exports.

Environment overrides must be absolute, outside the Git repository and mutually
non-overlapping. A required missing root fails clearly. The explicit local
development defaults are sibling directories named `meridian-data` and
`meridian-private`; tools report whether a root came from the environment or that
documented default. The private root may be absent until a tool requires it.

These are local Python/tooling variables. They are not `VITE_` variables and must
not be exposed in the browser bundle or committed with personal values.

```powershell
$env:MERIDIAN_DATA_ROOT = 'D:\Meridian\data'
$env:MERIDIAN_PRIVATE_ROOT = 'D:\Meridian\private'
py scripts\meridian_paths.py --require-data
```

Historical configs using `../meridian-data/...` or
`../meridian-private/...` are supported by the resolver as compatibility syntax.
Root-aware historical experiment tooling resolves the legacy Earth Lab prefix to
`MERIDIAN_DATA_ROOT/experiments/earth-lab`. Entry points that accept explicit paths
retain that documented behaviour. Setting an environment variable does not secretly
alter a script that does not call the resolver.

## Current external data layout

Phase 4 established this contract through copy, validation and hash comparison before
any approved old-copy removal. Phase 4B has preserved historical Earth experiments under `experiments`,
and Phase 4C has created validated Tryfan source and derived products under `sources/atlas`
and `derived/atlas`. Phase 4D has created the separate private root and copied private
Traverse source, benchmark, experiment and cache data into it. Phase 4E has copied the
current and previous complete GFS runs into `derived/weather/gfs`; generation now targets
that authoritative external root while Vite retains the `/weather/gfs` browser contract.
Phase 4F removed stale/reacquirable GFS source caches, one incomplete inspection cache
and the obsolete legacy updater lock. Phase 4G then independently revalidated the external
publication and retired the complete in-repository GFS rollback copy. Other migrated
original trees remain subject to their own explicit deletion gates:

```text
Projects/
  project-meridian/
  meridian-data/
    sources/
    derived/
    experiments/
    cache/
    scratch/
  meridian-private/
    traverse/
```

The meanings are:

- **sources**: retained external observations in native or faithfully extracted form,
  with provider, licence, acquisition and native-resolution provenance.
- **derived**: reproducible Meridian products created from source or canonical data
  and worth retaining beyond a temporary run.
- **experiments**: outputs and reports tied to bounded historical investigations,
  including frozen identities.
- **cache**: reacquirable or recomputable performance state.
- **scratch**: disposable temporary work with no durability guarantee.
- **private**: personal/user data kept outside both Git and the general world-data
  estate.

**Canonical** is a semantic status, not necessarily another top-level directory. A
canonical product may live under `derived` when its manifest, hash, provenance and
compatibility guarantees identify it clearly.

The current private Traverse hierarchy is `sources/strava-export`,
`benchmarks/routes`, `experiments/{activity-research,terrain-research}` and matching
private caches under `cache`. Detailed private filenames and hashes live only in the
private validation inventory. Git records aggregate migration evidence and its inventory
hash, never route geometry or activity contents. The four old data-root estates remain
temporary rollback copies pending separately approved removal. Phase 4G retired only
the legacy GFS publication; it did not remove these private estates. Their presence
is not permission for new private data to enter the general data root.

Classification precedes movement. A mixed historical directory may be preserved
under `experiments` rather than split if splitting would damage provenance or create
fragile references.

## Experiments and compatibility

Historical experiments retain their original names, configs, hashes and output
identities. Code becomes shared infrastructure only after it has a continuing role
beyond the experiment that created it. Promotion gives code a role-based name and an
explicit contract; it does not rewrite the experiment record.

`scripts/earth_lab` and `docs/earth-lab` remain historical repository source and
configuration. Phase 4B preserved experiment data under
`MERIDIAN_DATA_ROOT/experiments/earth-lab`; the original external `earth-lab` tree
remains a recovery copy. Legacy sibling-relative config paths are deliberate
compatibility syntax resolved by active tooling, not permission to rewrite frozen
Lab provenance or to use the historical branch for ongoing development.

“Earth Lab” is historical terminology, not the permanent name for shared Atlas
infrastructure.

## Tryfan Reference Renderer

The durable renderer source now lives at
`renderers/unreal/tryfan-reference`. The project and map retain the historical
`TryfanLab004.uproject` and `Tryfan_Lab004.umap` names so preservation was not
combined with an Unreal package rename.

Normal Git stores the project descriptor, curated secret-free configuration,
manifest, bootstrap and documentation. A path-specific Git LFS rule stores the unique
calibrated map. Generated photo-overlay packages, Lab 009 material/textures, deployed
Python, source-pointer JSON and Unreal build/cache/Saved state remain ignored and are
recreated by the documented bootstrap and validation process.

The bootstrap consumes verified dependencies through `MERIDIAN_DATA_ROOT`. Its
ignored `meridian-*-source.json` files contain machine-local absolute pointers
because Unreal Python needs concrete filesystem paths at runtime; they are generated
local state and must never be committed. Historical absolute import metadata embedded
inside the binary map records how the original asset was imported and is not an
active storage contract.

The renderer may eventually receive role-based Unreal project/package names through
an Unreal-aware migration. Historical Lab 004 documentation and provenance will not
be renamed.

## Reproducibility and privacy rules

- Record source identity, licence, acquisition, CRS/resolution where relevant, hashes
  and deterministic parameters.
- Fail on an unexpected frozen identity rather than silently regenerating it.
- Keep secrets, private GPX/activity data, exports and machine-local source pointers
  outside Git and `MERIDIAN_DATA_ROOT`.
- Generated data belongs outside Git unless a reviewed durable asset has a specific
  versioning policy, such as the canonical LFS-tracked map.
- Data providers should be replaceable without rewriting consumers of canonical
  representations.
- Platform-specific implementations belong behind the narrowest useful boundary.
- Do not invent a global ontology or a generic provider framework before multiple
  real use cases justify it.

The concrete, non-destructive Phase 4 inventory is recorded in
[Phase 4 data migration inventory](phase-4-migration-inventory.md).

## Atlas semantic evidence foundation

The [Atlas Semantic Evidence Contract v1](atlas/semantic-evidence-contract.md) is
frozen after the physical-surface domain review and the Tryfan/Riffelhorn and Exe
empirical stress tests. Physical-surface semantics foundation is established/closed.
The unused declaration/validation boundary is `scripts/atlas/semantic-evidence`; no
application consumer, semantic registry/runtime, layer, inference or hydrology is
introduced. Source-native claims, optional qualified/lossy mapping, claim-local
space/time/reference, feature/event association, evidence mode/lineage, scoped
quality, unknown reason and shared rights remain independent of resolved world truth.

TerrainHierarchy selects geometry; Appearance retains observations/processed colour.
Semantic evidence may reference either as an input without modifying those domains.
Future interpretation and ingestion are separate work; no automatic source winner,
cover ontology, feature database or camera/render policy is frozen by this contract.
Elevation/multiscale remain closed; externally provisioned multiview stays parked.
Weather/Traverse and production lifecycle remain unchanged.

## Atlas research status and synthesis boundary

The [current research-state register](research/atlas-research-state.md), reached
through the [research map](research/atlas-research-map.md), separates established
foundations from partial appearance results, parked acquisition, future implementation
and surviving research. Historical investigation/next-step summaries above retain
their checkpoint context; the register records their completion or supersession.

The [completed lifecycle assessment](research/atlas-derived-understanding-lifecycle.md)
closes the audit’s pre-synthesis gate. Stable revision snapshots preserve evidence while
qualified current interpretation can evolve. Most result provenance is already in v1;
actual scoped input uses and policy-relative current assessment need a small compatible
companion description before automation. This is an assessed boundary, not an implemented
subsystem or modification of frozen contracts/current dependency policy.

The [world-model architecture synthesis](research/atlas-world-model-architecture-synthesis.md)
now defines Atlas target responsibilities: coordinated source evidence, domain preparation,
qualified claims/features/state, reproducible derivations, question-local resolution and
independent presentation. **Decision C:** sufficiently founded for a bounded integrated
retained-region proof; no operational world model or production capability is implied.
Domain-specific representations remain distinct, with v1 semantic evidence and small linked
input-use/current-assessment responsibilities. Current client-only ownership and Atlas/Weather/
Traverse dependency boundaries remain unchanged.

The [retained Tryfan proof](research/tryfan-qualified-query-proof.md) now composes one
research-only vertical slice (**C — SUCCESS**): domain selection, v1 claims and scoped
input-use receipts support selective recomputation and historical replay. No production
consumer or general query/dependency runtime is introduced. The
[storage/processing/serving requirements assessment](research/atlas-storage-processing-serving-requirements.md)
now completes the proof recommendation (**decision C**): logical storage responsibilities,
shared qualified knowledge, scoped indexes/dependencies, coherent publication/recovery and
separate serving classes. These are requirements, not selected technologies or deployments.
The [local persistent Tryfan proof](research/tryfan-local-persistent-proof.md) now completes that
recommendation (**C — SUCCESS**): explicit input-use receipts, qualified v1 claims and
stored hierarchy declarations survive real restarts, scoped update and historical
replay. Accepted publication is coherent; freshness/reverse lookup rebuild from facts.
JSON snapshots are a replaceable single-writer proof, not a production store decision.
The [WorldCover binding proof](research/tryfan-worldcover-binding-proof.md) now completes
that recommendation (**C — SUCCESS**): native categorical assignments resolve through
shared v1 templates, qualified cell/support queries, time/quality/mapping-loss and
coexisting habitat evidence. Real restart preserves meaning; no contract/runtime changes.
This does not establish all semantic input forms. The
[retained Riffelhorn appearance assessment](research/riffelhorn-appearance-assessment.md)
now completes that recommendation (**C — SUCCESS**, resolution conclusion **B**).
Shared source/product/representation provenance plus bounded appearance eligibility suffice
for retained source-derived imagery; no full AppearanceHierarchy/runtime is introduced.
Support, information scale, acquisition unknowns and render-only effects stay distinct;
physical/corrected appearance requests remain unsupported. The
[illumination/shadow assessment](research/illumination-identifiability.md) completes that recommendation
(**B — PARTIAL IDENTIFIABILITY**): documented, reconstructed and conditional illumination use
existing provenance/input-use machinery; no universal illumination contract is needed. Unknown
pixel contribution/time and source transfer prevent a precise Riffelhorn physical correction.
The [frozen residual trial](research/tryfan-illumination-normalization.md) completed at its
minimum-evidence stop (**D — INCONCLUSIVE**, SE SCL5 has 12<20 cells). No corrected
appearance product is justified or published; source identity and unknown outcomes remain
separate. The [registration/epoch assessment](research/riffelhorn-registration-epoch.md) now
completes that recommendation (**B - SCALE-CONDITIONAL CONSISTENCY**). Coordinate/preparation checks
agree, while mixed epochs and ambiguous steep/dark controls limit fine physical matching. No
registration correction is justified by proxy optima. The [vegetation-only protocol assessment](research/tryfan-vegetation-protocol.md)
now completes that recommendation (**A - NOT JUSTIFIED**): three candidate masks/fixed spatial
holdouts do not provide sufficient controlled support; counts do not prove current homogeneous
vegetation. No model fitting, corrected bands or new executable correction protocol.
Original1842008 remains INCONCLUSIVE; all42 status columns and old criteria remain unchanged.
The [dark-source signal assessment](research/riffelhorn-dark-source-signal.md) completes that
recommendation (**B - PARTIAL RETAINED SIGNAL**): coherent 0.5-1 m image-space variation survives
in fixed dark supports, with low range, JPEG-phase/colour variation and deepest-support ambiguity.
Source/prepared hashes/encoding agree. Diagnostic lifting is a view, not corrected physical appearance;
steep projection and fine registration remain qualifications. All 42 status columns are preserved.
The [display-transfer experiment](research/riffelhorn-display-transfer.md) now completes that
recommendation (**B - PARTIAL**). A fixed global bounded toe4 modestly improves recorded dark
structure visibility, with bright/deep anchors unchanged; toe8 fails codec amplification limits.
Toe4 remains visually constrained by mottling and limited benefit: research-only, no production
prototype justified. This is a render-only operation, not illumination normalization or corrected
appearance. The [retained Exe query proof](research/exe-water-query-proof.md) completes that recommendation
(**C - SUCCESS**):75 frozen native point/support/feature/time/reference queries preserve WFD
identity, monthly detection/no-observation, PHI contributor vintages, mixed planning lineage,
event intervals and incompatible fallback rejection. Real restart/rebuild preserves qualifications;
no current hydraulic state or hydrological model is inferred. No foundation/production change.
The [programme acceptance](research/atlas-regional-pilot-acceptance.md) completes that recommendation
(**C - READY FOR BOUNDED REGIONAL PILOT**):37 retained proof records,50 required capabilities
plus3 explicit unproven/excluded classes,42 thread dispositions and9 frozen admission gates.
No demonstrated foundational blocker; integrated mixed-family publication/serving and operational
measurements become pilot exit obligations. Admission does not mean the pilot exists or science is complete.
The [bounded Tryfan pilot plan](research/tryfan-regional-pilot-plan.md) at `7809147`
(**C - IMPLEMENTABLE AS PLANNED**) defines six ordered slices following admission at `f16ce63`.
The [S1 catalogue/generation foundation](research/tryfan-pilot-s1.md) is now **C - S1 SUCCESS**:
five retained families,310 hash-verified artifacts/42.47MB, eight native/prepared representation
references, immutable external JSON generations, one coherent root, explicit writer recovery and
fresh-process/history/interruption tests. Median fresh hash-verifying load was251.39ms in the
[local measurements](research/tryfan-pilot-s1-results.json); this is not a production SLA.
S1 remains **C - S1 SUCCESS** at `b5ac715`; its published seed remains registration-only.
The [S2 native evidence/query layer](research/tryfan-pilot-s2.md) is now **C - S2 SUCCESS**:
WorldCover native cells/templates and all193 NRW records/28 code strings are readable through the
pinned published generation, with coexistence, mapping loss, native time/support, rights/provenance
and honest unsupported/unavailable states. July appearance is metadata only. Independent fresh
processes reproduce the same qualified matrix. [Measurements](research/tryfan-pilot-s2-results.json)
record about1.2ms median initialized queries and1.64s median fresh-process matrix execution;
these are local observations, not SLAs. No foundational/technology deviation; runtime reader
capability is separate from immutable seed capability. The checkpoint is the commit introducing
this S2 report (`7db385a`). S1 and S2 remain successful; their historical reports stay intact.
The [S3 derivation/lifecycle integration](research/tryfan-pilot-s3.md) is **C - S3 SUCCESS**:
four exact original AWS results persist in full G0 with explicit methods/input-use scopes,
computed freshness and pixel replay. Isolated Welsh-context recomputation adds only two summit
revisions and reuses southern results; no applicability update is published. Q21 composes six
separate generation-pinned evidence contexts. Median baseline436.85ms/freshness10.00ms/fixture
recomputation443.22ms; full metadata1.09MB ([observations](research/tryfan-pilot-s3-results.json)).
The [S4 serving/isolated consumer](research/tryfan-pilot-s4.md) is **C - S4 SUCCESS**:
read-only generation-pinned loopback HTTP, native/derived answers, exact retained artifacts,
provenance/rights and isolated Canvas2D consumer. A separate writer publishes a same-evidence
successor while the old consumer stays G1 and a new consumer sees G2. No scientific update.
Warm query medians213-305ms; fresh service+consumer about3.46s; generation1.21MB
([measurements](research/tryfan-pilot-s4-results.json)). Port4191 replaces Fetch-blocked4190;
this is a reversible pilot detail. Production Atlas, Weather, Traverse and frozen contracts
remain unchanged. Appearance remains unresolved/non-blocking and Swiss multiview parked.
The [S5 scoped/mixed-family publication](research/tryfan-pilot-s5.md) now passes **C - S5 SUCCESS**: U1 and isolated U2 activate retained applicability, recompute only two summit revisions, reuse southern/native state and preserve all history. Eight abrupt exits and fresh/pinned HTTP consumers keep old roots coherent; retry reuses identical closed candidates. Actual browser refresh changes the whole scene explicitly. Assembly1.22–1.34s/validation584–651ms/root switch~5ms,1.24MB generations ([observations](research/tryfan-pilot-s5-results.json)). No new source revision or foundational deviation. S1–S4 remain successful. Appearance remains unresolved/non-blocking and Swiss multiview remains parked. The [S6 measured exit](research/tryfan-pilot-s6.md) now records **C - PILOT EXIT ACCEPTED**: all16 original A–P criteria and nine bounded exit gates PASS, independent empty rebuilds and fresh services/consumers reproduce the coherent pilot, and six records replay from retained pixels. The bounded Tryfan pilot is **closed**; S1–S5 remain SUCCESS. [Measured results](research/tryfan-pilot-s6-results.json) retain five fresh runs,20 warm batches and1/4-reader100-request workloads: native query medians263–266ms,4-reader median1.06s,0 errors. Eight repeated interruption cases preserve prior roots. Measurement-only Node metering exposes about31.8MB of synchronous requested reads for a32.8KB WorldCover response; this is not physical disk traffic or a production SLA. No foundational contradiction, runtime change or closure of unresolved science. That recorded next task is now completed by the [measured architecture assessment](research/atlas-measured-storage-processing-serving.md) with **C - ARCHITECTURE DIRECTION ESTABLISHED**. That experiment is now completed with **C - EXPERIMENT RESOLVED**; see the current scaling entry below. That recorded proof is now completed with **C - PROOF SUCCESS**; see the current component-membership entry below. That recorded experiment is now completed with **C - EXPERIMENT RESOLVED**; see the current granularity entry below. That recorded proof is now completed with **C - PROOF SUCCESS**; see the validated-reuse entry below. That recorded experiment is now completed with **C - EXPERIMENT RESOLVED**; see the maintenance entry below. That recorded proof is now completed with **C - PROOF SUCCESS**; see the packing entry below. That recorded assessment is now completed with **C - ASSESSMENT RESOLVED**; see the current integrity-cost entry below. That assessment is now completed with **C - ASSESSMENT RESOLVED**; see the current regional-expansion entry below. That recorded preparation is now completed with **C - PROOF SUCCESS**; see the current Riffelhorn preparation entry below. No S7, vendor choice, deployment or post-pilot implementation is authorized by closure.
A6-A11/A14 remain unresolved separately; Swiss pixels remain parked.
Open/parked appearance science remains non-blocking, not solved; Swiss pixels remain parked.
Frozen contracts/current production remain unchanged.

## 2026-10-08 - Atlas measured storage, processing and serving architecture

The [measured architecture assessment](research/atlas-measured-storage-processing-serving.md) records **C - ARCHITECTURE DIRECTION ESTABLISHED**. The Tryfan pilot remains **CLOSED / ACCEPTED** at `bae7c3e`; S1–S5 remain SUCCESS and S6 remains **C - PILOT EXIT ACCEPTED**, with all16 cases/nine gates intact. **DECIDE NOW:** immutable source/result identity, native qualifications/rights/actual-use dependencies, scoped freshness, validated publications and generation-pinned isolated consumers. **PROVISIONAL DIRECTION:** immutable payload objects plus one shared structured/indexable metadata catalogue, component-reference manifests, separate bulk/query responsibilities and finite local/batch processing. **DEFER PENDING EVIDENCE:** database/vendor, component/shard size, multiple writers, remote durability, packing/CDN/deployment, graph/cardinality and dynamic cadence. **REJECT:** semantic flattening, latest-only/path identities, blanket invalidation, copy-world publication, cache-only lineage and unjustified service/workflow fleets.

S6 measured31.8MB synchronous requested Node reads per32.8KB WorldCover response;1/4-reader throughput~3.8requests/s with higher four-reader latency. These are bounded warm-cache observations, not physical disk/egress or production capacity. The assessment extracts existing receipts only and implements no architecture. Exactly one next bounded task: **Atlas retained generation metadata read-amplification and verified-reuse scaling experiment**; not begun. Appearance remains unresolved/non-blocking, Swiss multiview remains parked and all42 historical research statuses are unchanged.


## 2026-10-08 - Atlas retained-generation scaling experiment

The [retained-generation experiment](research/atlas-generation-scaling.md) records **C - EXPERIMENT RESOLVED**. The Tryfan pilot remains **CLOSED / ACCEPTED**, S1–S5 remain SUCCESS, S6 remains accepted and the architecture direction remains established. [Frozen baseline](research/atlas-generation-scaling-baseline.json), [measurements](research/atlas-generation-scaling-results.json), [decision updates](research/atlas-generation-scaling-decisions.json) and [validation](research/atlas-generation-scaling-validation.json) retain the evidence. All 18 primary cases use the original scientific state at 7/28/112 generations, with five fresh processes and 20 repeated requests each; six historical pins and seven labelled metadata-only controls distinguish resolution, verification, footprint and publication costs.

At 112 generations, one historical query requests 25,016 generation reads / 29.77 GB of metadata, taking about 299 seconds. Request-scoped verified reuse reduces this to 112 reads / 136 MB / 5.8 seconds, while whole parsed ancestry raises observed memory use. These are local requested-read observations, not physical disk traffic, production capacity or payload-scale evidence. **DECIDE NOW:** separate cost classes and retain integrity, qualification, identity, history and pins. **PROVISIONAL DIRECTION:** shared immutable metadata components, lightweight publication manifests and bounded membership resolution. **DEFER PENDING EVIDENCE:** exact component/index/checkpoint strategy, spatial selectivity, distinct revisions, infrastructure and distributed guarantees. **REJECT:** repeated whole-ancestry closure validation as the interactive default, trusted mutable-path caches, skipped checks and unjustified infrastructure.

At the e88b575 checkpoint, the recorded next bounded task was **Atlas retained component-manifest and publication-membership resolution proof**. It is now completed by the entry below, preserving scientific qualification and rejection of unpublished state with a bounded retained applicability transition. Accepted pilot/source/frozen/production files and all 42 historical research statuses remain unchanged. Appearance remains unresolved/non-blocking and Swiss multiview remains parked. No S7, production implementation or new evidence.


## Atlas component-manifest and publication-membership proof

The [retained proof](research/atlas-component-membership.md) records **C - PROOF SUCCESS**. Tryfan remains **CLOSED / ACCEPTED**, S1–S6 remain intact, and the measured architecture direction remains established. The [e88b575 scaling evidence](research/atlas-generation-scaling.md) remains authoritative. Current/recent/oldest access at 7/28/112 publications reads 33 committed membership records, one publication and five shared components when hydrated, with zero publication ancestry traversal. Qualified WorldCover/composed-evidence/provenance answers match the prior experiment.

The exact retained U1 lifecycle recomputes only two summit results and reuses two southern results; ten pixel replay checks are exact. Original separate consumers remain pinned while a new generation publishes. Two abrupt exits leave old state current and complete pre-switch candidates ineligible. [Measurements](research/atlas-component-membership-results.json), [decisions](research/atlas-component-membership-decisions.json) and [regression receipt](research/atlas-component-membership-validation.json) retain the proof.

DECIDE NOW: bounded explicit publication membership, coherent current/eligibility commitment and fresh selected-closure verification. PROVISIONAL DIRECTION: shared immutable component metadata with a bounded membership witness. The byte-radix witness is not a production index choice. Unselected archived publications are independently verified when selected/audited, rather than automatically traversed as current dependencies. At 112 publications, shared component/publication/index metadata is 2.582 MB versus 141.241 MB whole snapshots/locators. No hidden component ancestry is observed; coarse interior metadata duplication and 33 new small index nodes per publication remain explicit costs.

DEFER PENDING EVIDENCE: component granularity/selective reads, metadata-cardinality scaling, exact database/index/compaction technology, remote durability and concurrency. REJECT unbounded ancestor closure as normal eligibility, existence-as-publication, hidden delta chains and weakening qualification/integrity. Appearance remains unresolved/non-blocking and Swiss multiview parked. All 42 historical research statuses remain unchanged.

At the `97c31c8` checkpoint, the recorded next task was **Atlas retained component granularity and selective metadata-read scaling experiment**. It is now completed by the experiment below. It tests selective metadata reads and component boundaries using isolated retained-semantic populations, without new evidence, physical methods or production infrastructure. No S7 or post-proof implementation. The checkpoint is the commit introducing this report/navigation entry.

## Atlas component granularity and selective metadata-read experiment

[Measured report](research/atlas-component-granularity.md) records **C - EXPERIMENT RESOLVED** from clean `97c31c8`. Tryfan remains CLOSED / ACCEPTED and the architecture direction remains established. [e88b575](research/atlas-generation-scaling.md) and [97c31c8](research/atlas-component-membership.md) remain authoritative and unchanged. [Frozen plan](../scripts/atlas/component-granularity/plan.json), [results](research/atlas-component-granularity-results.json), [decisions](research/atlas-component-granularity-decisions.json) and [validation](research/atlas-component-granularity-validation.json) preserve this bounded experiment.

148 query cases, 48 scoped metadata updates and 24 historical pins compare whole, 64-record spatial partitions, flat one-record components and authenticated key-ordered internal lookup. At 2,048 terrain records, a narrow moderate query inspects 64 records / 25,715 requested bytes; fine inspects one but requests 263,232 bytes through its flat directory. Broad fine reads 2,083 objects versus 36 whole. Spatial inventory queries favour spatial partitions; feature-ID queries favour key lookup. All 172 query/history observations retain 33 eligibility reads and zero ancestry. No hidden component ancestry appeared.

DECIDE NOW N11/N12: separate membership, logical identity, selective organisation and integrity/completeness cost; count directories and shared qualifiers. PROVISIONAL DIRECTION P08: family/access-specific moderate partitions or selective internals, not a universal size/tile scheme. DEFER D08: exact sizes/backend, real 2D/cardinality, dual lookup and safe incremental validation. REJECT R08: blanket one-record flat membership, universal geographic partitioning, whole-family-only hydration and weakened qualification/integrity. Scoped writes reuse immutable interiors, but every construction and publication audit still visits all 2,048 records. No database/cloud/index product is selected or implemented.

At `38f9ba7`, the next task was **Atlas retained validated-component reuse and incremental publication-validation proof**. It is now completed by the proof below; its conclusions and original measurements remain authoritative. Test reusable validation receipts/changed-path references against full closure while preserving corruption detection, completeness, historical identity and coherent publication. No accepted pilot, retained source, frozen contract, production Atlas, Weather or Traverse change; all 42 historical research statuses and 113 protected hashes remain intact. Appearance remains unresolved/non-blocking and Swiss multiview parked. No S7, new data/methods or production-service readiness work. This entry’s introducing commit is the experiment checkpoint.

## 2026-10-08 - Atlas validated-component reuse and incremental publication-validation proof

[Durable report](research/atlas-validation-reuse.md) records **C - PROOF SUCCESS** from clean `38f9ba7`. Tryfan remains **CLOSED / ACCEPTED**, S1-S5 remain SUCCESS, S6 accepted, and the architecture direction remains established. [e88b575](research/atlas-generation-scaling.md), [97c31c8](research/atlas-component-membership.md) and [38f9ba7](research/atlas-component-granularity.md) remain authoritative. [Frozen plan](../scripts/atlas/validation-reuse/plan.json), [check inventory](../scripts/atlas/validation-reuse/inventory.json), [results](research/atlas-validation-reuse-results.json), [decisions](research/atlas-validation-reuse-decisions.json) and [validation](research/atlas-validation-reuse-validation.json) retain the evidence; the introducing commit is this proof checkpoint.

All 46 measured proposals (29 valid/17 invalid) agree with full validation. At 192 components / 12,288 synthetic records, a localized fan-out-one update validates 128 rows and one relationship instead of 12,288/64. Trusted receipts skip semantic work only: every current component is still hashed, completeness and membership comparisons still scan all slots, and receipt lookup increases reads from 193 to 387. The final measured timing distribution is in the report. Rule changes disable local reuse; context changes rerun relationships; bad reuse evidence falls back to full validation. Stale historical claims remain valid. Six historical pins retain 33 eligibility reads and zero ancestry; four abrupt pre-switch exits preserve the previous root, and retries/pinned history remain coherent.

DECIDE NOW N13/N14: exact content/rule/trust/scope binding, contextual versus current-integrity separation, mandatory completeness/root checks and honest residual accounting. PROVISIONAL DIRECTION P09: qualified local receipts and trusted reverse relationship buckets, with full oracle/fallback. DEFER D09: evidence issuance/maintenance amortization, packing, general graph/rights/applicability and deployed trust/backend choices. REJECT R09: permanent valid booleans, candidate trust, skipped current integrity/context/completeness, stale-as-false and hidden population/ancestry work. No production validator adopts the shortcut; evidence preparation and the builder still visit the full population.

At `35e4fbd`, the recorded next task was **Atlas retained validation-evidence maintenance and amortization experiment**. It is now completed by the experiment below; the original proof remains authoritative. Compare full evidence reissuance with safe immutable receipt/affected-bucket carry-forward across repeated localized publications, keeping oracle equivalence, corruption/context/rule/history/publication checks. Measure end-to-end costs before adoption. No backend, production issuer, evidence/method change or service-readiness work. Accepted pilot/sources/frozen contracts, all 42 historical statuses and 113 protected production hashes remain unchanged. Appearance remains unresolved/non-blocking and Swiss multiview parked. No S7.

## 2026-10-08 - Atlas validation-evidence maintenance and amortization experiment

[Durable report](research/atlas-validation-maintenance.md) records **C - EXPERIMENT RESOLVED** from clean `35e4fbd6730acf43ad3e0e33c69111f7431ec896`. Accepted Tryfan remains **CLOSED / ACCEPTED**, S1-S5 SUCCESS/S6 accepted, and the architecture direction remains established. [e88b575](research/atlas-generation-scaling.md), [97c31c8](research/atlas-component-membership.md), [38f9ba7](research/atlas-component-granularity.md) and [35e4fbd](research/atlas-validation-reuse.md) remain authoritative. [Results](research/atlas-validation-maintenance-results.json), [decisions](research/atlas-validation-maintenance-decisions.json) and [validation](research/atlas-validation-maintenance-validation.json) retain the measured evidence; this entry's introducing commit is the experiment checkpoint.

All 1,296 paired sequence proposals agree; ten additional correctness/publication controls preserve rejection, full fallback, historical staleness and root safety. Three repeats of 13 isolated sequences include creation, lookup/eligibility, selective issuance, supersession and retained evidence. **No sequence reaches a sustained elapsed break-even within its tested range in any repeat**, despite semantic savings. At 192 components, localized 32-publication cumulative full/incremental medians are 3,209/4,950ms;112-publication medians 10,129/15,399ms. The 112-publication run stores 414 unique local receipts/152,681 bytes, but trust directories take 6,958,896 bytes. Current integrity/completeness and directory work remain population-wide. Historical receipt lookup is direct; old/recent/current pins retain 33 eligibility reads, zero ancestry. This is evidence against adopting this small-file receipt issuer unconditionally, not against qualified logical reuse.

DECIDE NOW N15/N16: include the complete evidence lifecycle, bind exact input/rule/trust/scope and share immutable receipts while retaining referenced historical acceptance. PROVISIONAL DIRECTION P10: conditional reuse only after measured lifecycle break-even; full validation remains the economic baseline for these lightweight predicates. DEFER D10: packed evidence/shared-directory economics, deployed trust/retention and backend choices. REJECT R10: always-incremental based on row savings, omitted maintenance/current integrity, context-free validity, historical deletion or hidden ancestry. No production issuer or garbage collector is implemented.

Exactly one next bounded task: **Atlas retained validation-evidence packing and shared-directory amortization proof**; **NOT BEGUN**. Test whether modest immutable packing/shared evidence-directory organisation changes these economics while preserving full-oracle equivalence, current component integrity, coherent publication and independent history. No backend, new data/physical method, accepted-pilot/frozen/production Atlas/Weather/Traverse change. All 42 historical research statuses and 113 protected hashes remain unchanged. Appearance unresolved/non-blocking; Swiss multiview parked. No S7 or service transition.

## 2026-10-08 - Validation-evidence packing and shared-directory amortization proof

[Durable report](research/atlas-validation-packing.md), [frozen plan](../scripts/atlas/validation-packing/plan.json), [measurements](research/atlas-validation-packing-results.json), [decisions](research/atlas-validation-packing-decisions.json) and [validation](research/atlas-validation-packing-validation.json): **C - PROOF SUCCESS, within the tested model**. Tryfan remains **CLOSED / ACCEPTED**; architecture direction established. `e88b575`, `97c31c8`, `38f9ba7`, `35e4fbd` and `a027ec7`, including the negative individual-receipt amortization result, remain authoritative and unchanged.

All 4,464 sequence oracle comparisons and 36 boundary comparisons agree on semantic validation verdicts. Three repeats compare full, individual receipts, immutable packs and packed/shared directories across 15 deterministic workloads. At 192 components / 112 publications, cumulative medians are **8.58 / 16.06 / 11.04 / 10.08 seconds**. Shared packing reduces requested reads from 43,960 to 23,282 and retained evidence from 7.15 MB to 2.37 MB, but fails the frozen material-win rule. The 768-component localized case is a positive exception: shared packing saves 19.4% paired median (16.0-41.9% range). Smaller/scattered/broad and rule/context workloads do not provide a reliable general win. Full current integrity/completeness remain population-wide; direct old/recent/current pins retain 33 eligibility reads and zero ancestry. Pack/directory corruption and staged interruption preserve current-root safety. Scientific validity and evidence-issuance availability are reported separately.

**Full validation is the PROVISIONAL DIRECTION default for the measured lightweight-rule workloads. The receipt-optimisation line is CLOSED pending new evidence.** No further receipt representation is proposed. N17 DECIDE NOW retains complete cost/trust/identity/current-integrity accounting. P11 records the conditional measured result and default. D11 defers real payload/custody/failure costs, expensive predicates, deployed trust/retention and backend choices. R11 rejects adoption from row counts, omitted maintenance, skipped current hashes, stale-as-false, ancestry and indefinite receipt optimisation. No infrastructure or production implementation. Appearance remains unresolved/non-blocking; Swiss multiview parked; all 42 canonical statuses and 113 protected production hashes remain unchanged.

Exactly one next bounded task: **Atlas retained payload-integrity and publication-validation cost assessment**, **NOT BEGUN**. Assess and measure actual retained payload/current-integrity and publication-guard costs and failure/custody assumptions without changing guards, optimising receipts again, acquiring evidence or choosing production infrastructure. Introducing commit is this proof checkpoint.

## 2026-10-08 — retained payload-integrity/publication-validation cost assessment

[Assessment](research/atlas-integrity-cost.md): **C - ASSESSMENT RESOLVED**. [Frozen baseline](research/atlas-integrity-cost-baseline.json), [measurements](research/atlas-integrity-cost-results.json), [classifications](research/atlas-integrity-cost-decisions.json) and [validation](research/atlas-integrity-cost-validation.json) preserve the decision. Tryfan artifact verification median 213 ms; full administrative registration/publication 670 ms. Read-only existing 100 km² Swiss preparation: 11,429 tiles / 930.91 MB, 9.61 s; 1.29 GB imagery-field check 1.73 s. Larger byte checks are not new-region world-model acceptance. Nested exclusive instrumentation shows per-file path work dominates many-tile checks; hashing matters for large fields. Metadata parsing/encoding, completeness, current integrity and final publication guards remain explicit and population-wide.

DECIDE NOW: distinguish present byte identity/availability, metadata consistency, coherent acceptance, physical truth and future custody. Ordinary files/locators remain mutable; checks establish integrity at read time. Single-writer local atomic rename/process interruption is demonstrated; power loss, remote custody, multiple writers and permanent availability are not. PROVISIONAL DIRECTION: full validation remains the default for the next bounded local batch regional work; no measured cost blocks that capability, and no further validation investigation is justified now. Receipt optimisation remains CLOSED, with its earlier negative adoption result and bounded 19.4% positive exception preserved. DEFER actual larger integrated GIS/remote/production durability economics; REJECT counts-as-hash-dominance and checksums-as-scientific truth. All previous architecture/scaling/component proofs remain authoritative.

The bounded Tryfan pilot remains CLOSED / ACCEPTED; S1–S6, accepted evidence, frozen contracts, all 42 canonical research statuses and 113 protected production hashes are unchanged. Appearance remains unresolved/non-blocking; Swiss multiview parked. Exactly one next bounded task: **Atlas retained regional expansion and source-accountability assessment**, **NOT BEGUN**. Recover retained coverage/support/source/product/provenance/rights gaps and a bounded real regional integration candidate before acquisition or implementation. No S7, production infrastructure, validation redesign, Weather/Traverse or service transition. Introducing commit is this assessment checkpoint.

## 2026-10-08 — retained regional expansion and source accountability

[Assessment](research/atlas-regional-expansion.md): **C - ASSESSMENT RESOLVED**. [Inventory](research/atlas-regional-expansion-inventory.json), [frozen baseline](research/atlas-regional-expansion-baseline.json), [fixture specification](research/atlas-regional-expansion-fixture.json) and [validation](research/atlas-regional-expansion-validation.json) preserve the boundary. Select the Riffelhorn4 km² native EPSG2056 core, with accepted Tryfan9 km² as a separate unchanged reference. Twelve current-hash-checked retained inputs /120,347,916 bytes: four Swiss DTM originals, one independent Copernicus DSM COG, native WorldCover crop/window, two GeoCover responses and GLAMOS original/subsets. Read-only original GLAMOS selection reproduces one glacier and six debris records. No fixture is built or ingested.

DECIDE NOW: source/product/snapshot/preparation/locator identities, source-specific rights, native support/time and unknowns stay distinct. LN02, EGM2008 and unknown Welsh height reference are not reconciled. GeoCover snapshot completeness/release/third-coordinate height and survey dates remain unknown; geology is not exposure, annual class is not truth/fraction, inventory date is not current ice. OGD/CCBY/GLO30 terms support this local retained proof with source-specific notices; future distribution/service obligations remain separate. PROVISIONAL: prepare a native-qualified region offline from retained bytes, without rebuilding tiles, then assess realistic retrieval and independent-region integration as evidence warrants. DEFER larger full100 km² integration, actual dated revisions, datum harmonisation and technology selection. REJECT visual AWS-padded terrain as analytical source, new acquisition to inflate coverage and further validation optimisation. Full validation remains the provisional local default; receipt optimisation stays CLOSED.

The pilot remains CLOSED / ACCEPTED; S1–S6, established architecture direction, e88b575/97c31c8/38f9ba7 and later positive/negative validation evidence remain authoritative. All42 canonical statuses and113 protected production hashes remain unchanged. Appearance unresolved/non-blocking; Swiss multiview parked. Exactly one next bounded task: **Atlas retained Riffelhorn qualified regional fixture preparation proof**, **NOT BEGUN**. Prove exact source/context/support/rights bindings, offline deterministic preparation and fresh-process recovery, with explicit corrupt/missing/unsupported failures and source/pilot protection. Stop before realistic retrieval, new derivations or multi-region publication. No S7, backend, production Atlas, Weather/Traverse or service-readiness work. Introducing commit is this assessment checkpoint.

## Atlas retained Riffelhorn qualified fixture preparation — 2026-10-08

The [preparation proof](research/atlas-riffelhorn-preparation.md) records **C - PROOF SUCCESS**, following the frozen c53c478 specification: all twelve retained inputs (120,347,916 bytes) produce six prepared artifacts (5,605,110 bytes), six native raster bindings,38 full features and50 qualified declarations. Three empty rebuilds and three fresh-process loads reproduce exact revision `357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb`. [Observations](research/atlas-riffelhorn-preparation-results.json) record preparation median2.861s and verification median1.302s; no raster payload is copied or transformed.

DECIDE NOW: preserve source/retained-byte/preparation identities, full native geometry, separate core applicability, source-specific rights and DTM/LN02 versus DSM/EGM2008. PROVISIONAL DIRECTION: this prepared second-region fixture is ready for bounded qualified retrieval. Unknown observation/release/completeness and GeoCover z meaning remain qualified. Full validation remains the default; receipt optimisation remains CLOSED. Prior e88b575/97c31c8/38f9ba7/35e4fbd/a027ec7/eb34593/aa920d9/c53c478 positive and negative results remain authoritative. At that preparation checkpoint, Tryfan remained CLOSED / ACCEPTED and Riffelhorn registration/publication/retrieval was not implemented. Appearance remains unresolved/non-blocking; Swiss multiview remains parked.

That recorded retrieval is now completed with **C - PROOF SUCCESS**; see the current Riffelhorn retrieval entry below. The proof demonstrates native cell/support, feature-ID/intersection, glacier associations and explicit known/unknown observation/product-time semantics before coherent multi-region integration. No new methods, source acquisition, infrastructure or production changes are authorised by this result.

## Atlas prepared Riffelhorn qualified retrieval — 2026-10-08

The [retrieval proof](research/atlas-riffelhorn-retrieval.md) records **C - PROOF SUCCESS** within the actual 44-record fixture (38 features/six raster supports). All 435 repeated comparisons across 29 queries/three organisations and three fresh processes agree on qualified envelopes. Native point/support, feature-ID/parent association and known/unknown year predicates compose without inventing temporal history, units or scientific equivalence. [Measurements](research/atlas-riffelhorn-retrieval-results.json): point 44→10 candidates; feature-ID 44→1; broad 44→44. Startup hydrates 5.60 MB, median 1.401 s; warm candidate savings are not selective physical disk reads.

DECIDE NOW: exact predicates after candidates; source-scoped identities, provenance/rights, full native versus core support and temporal roles/unknowns survive. PROVISIONAL: family grouping/native window access and simple ephemeral feature/parent/spatial lookup suffice for bounded integration. DEFER persistent indexing, dense temporal populations, storage technology and metric-dependent derivations until their required unit qualifications are established. No retrieval-specific investigation is justified before integration. Tryfan remains CLOSED / ACCEPTED; Riffelhorn remains prepared/retrievable evidence, unregistered and unpublished. Full validation remains adequate; receipt optimisation CLOSED. Earlier positive/negative architecture/source/preparation evidence is unchanged. Appearance unresolved/non-blocking; Swiss multiview parked.

That recorded integration task is now complete; see the current multi-region entry below. Use existing immutable component/publication/pinning semantics in isolated two-region state; preserve accepted stores and scientific qualifications. No acquisition, new physical methods, production infrastructure or service transition.

## Atlas retained coherent two-region integration — 2026-10-08

The [integration proof](research/atlas-multi-region.md) records **C - PROOF SUCCESS** within isolated local single-writer state: exact Tryfan reference plus prepared Riffelhorn under one composite root/seven explicit components. All 342 native-envelope comparisons and three fresh historical replays agree. Riffelhorn and inverse Tryfan administrative updates each replace one component/reuse six; old pins remain coherent and new consumers see the new context. Invalid, staged, interrupted and unavailable historical state fail explicitly. No native scientific result/source is revised. [Measurements](research/atlas-multi-region-results.json): selected membership 33 records, seven components, zero ancestry; publication total 2.53–3.49s including full integrity; full three-generation query replay median 20.25s. Composite requests hydrate all seven components; native candidate savings are not selective composite metadata I/O.

DECIDE NOW: one pinned composite closure with explicit regional source/preparation/registration identities, native CRS/time/rights and exact current-byte validation. PROVISIONAL: this composite membership/independent registration model suffices for bounded integration. DEFER multi-writer/distributed regional roots, dense temporal histories, storage technology and metric derivations until required unit/support qualifications are accountable. Tryfan remains CLOSED / ACCEPTED. Riffelhorn is registered/published only in this isolated proof, never production or the accepted pilot. Earlier evidence/contracts are unchanged; receipt optimisation CLOSED, full validation adequate, Appearance unresolved/non-blocking and Swiss multiview parked.

That recorded derivation task is now complete; see the current retained dependency proof below. Existing methods and accountable native input-use scopes preserve lifecycle/history without acquisition, scientific fusion or production changes.

## Atlas retained regional derivation and scoped dependency density — 2026-10-08

The [dependency proof](research/atlas-regional-dependencies.md) records **C - PROOF SUCCESS** within isolated local single-writer state. Existing Horn slope, dependent planar ratio and native WorldCover count methods produce 184 current outputs from actual retained inputs: 293 source/use/result nodes and 294 edges; eight seam stencils have genuine two-file fan-in, maximum source fan-out 36 and transitive depth 3 including input uses. All 24 full/scoped comparisons and three fresh five-publication/two-region replays agree. One-cell Riffelhorn notices stale/recompute eight results, shared-file notices 72, Tryfan summit two, unrelated administration/no-op zero; unchanged branches retain exact identity. Revisions are administrative qualification/use-policy or supported parameters, never fabricated physical change. Native band-unit/provider records establish Swiss metre/LN02 requirements separately from unchanged preparation/query qualifications.

[Measurements](research/atlas-regional-dependencies-results.json): localized Swiss full/scoped median 3.19/2.20s; no-op scoped 54ms with no sampling. Selected membership 33 records/eleven components/zero ancestry. Metadata discovery and full current-byte/closure guards remain population-wide. Five publication totals 7.79–8.19s include full proof-only numerical replay; three complete fresh replay median 35.00s. This is selective recomputation, not global-scale performance or wholly selective publication. Nine members are reused on regional context/derived changes; old pins, exact historical results and interruption/rejection isolation remain coherent.

DECIDE NOW: exact scoped/immediate/transitive identity and method/parameter-relative freshness, qualifications, regional isolation and coherent current/fixed historical consumption. PROVISIONAL DIRECTION: existing scoped lifecycle plus separate regional context/derived components suffices for the next local capability; full validation remains adequate. DEFER PENDING EVIDENCE: dense complete fields, arbitrary DAGs, real source-byte revisions, dated histories, general runtime/storage technology. REJECT unsupported datum/DSM–DTM fusion, synthetic physical-change claims and another optimisation without a blocker. Tryfan remains CLOSED / ACCEPTED; accepted Riffelhorn and multi-region proofs/contracts unchanged. Receipt optimisation CLOSED; Appearance unresolved/non-blocking, Swiss multiview parked; no S7 or production Atlas/Weather/Traverse change.

That recorded temporal task is now complete; see the dated-observation entry below. Prior evidence and limitations remain authoritative. No acquisition, new algorithms, infrastructure or service transition.

## Atlas dated observation and knowledge-revision integration — 2026-10-08

The [temporal proof](research/atlas-temporal-integration.md) records **C - PROOF SUCCESS** within retained regional/Exe evidence and explicitly controlled local knowledge events. Seventeen source-qualified assignments preserve physical, source-publication, acquisition/preparation, knowledge-acceptance and coherent-publication time distinctions. Five G0–G4 contexts contain 13/15/15/17/17 current assignments, 20 retained revisions and three supersession edges. All 477 repeated independent temporal comparisons and three fresh five-context replays agree. Late accepted inclusion leaves old pins unchanged; corrections preserve physical periods and native values; unknowns and observation gaps remain qualified. Exe is a disconnected dated-evidence branch, never water assigned to Tryfan or Riffelhorn.

[Measurements](research/atlas-temporal-integration-results.json): scoped Riffelhorn correction changes eight of 184 results and reuses 176; full/scoped medians 3.28/2.17s. Publication-note-only changes no derived receipts. Transitions reuse 11/9/11/12 of 13 members. Each query resolves 33 membership records and 13 components with zero ancestry traversal, while hydrating 3.01–3.22MB of component metadata. Publication totals 11.10–12.50s include full source validation and proof numerical replay; complete fresh historical replay median 60.54s. These bounded costs do not establish globally selective serving or production maturity.

DECIDE NOW: independent clock roles/precision/unknowns, immutable supersession, knowledge-cutoff/pinned visibility, exact qualified closure and native rights/provenance. PROVISIONAL DIRECTION: finite temporal components compose with regional lifecycle; full validation remains adequate. DEFER PENDING EVIDENCE: actual provider corrections, dense histories, continuous validity and runtime technology. REJECT invented dates/change/absence, rewritten history and another optimisation without a blocker. Tryfan remains CLOSED / ACCEPTED; accepted Riffelhorn, multi-region and dependency proofs/contracts remain unchanged. Receipt optimisation CLOSED; Appearance unresolved/non-blocking, Swiss multiview parked; no S7 or production Atlas/Weather/Traverse change.

That recorded local-architecture decision is complete; the current decision and unbegun implementation task are below.


## Atlas evidence-based local implementation decision — 2026-10-08

The [local architecture decision](research/atlas-local-architecture.md) records **C — DECISION READY** for the offline local single-writer runtime. Choose immutable payload/canonical qualified component/publication files plus a rebuildable sealed SQLite query catalogue; the filesystem current+committed-eligibility root remains the visibility authority. Deterministic Node/TypeScript library/CLI coordinates bounded Python native/catalogue workers; no daemon, HTTP, cloud or production application integration. Index build/validation precedes canonical root switch; no database/filesystem atomic transaction is claimed. Missing volume/index/closure is explicit; fallback/rebuild cannot grant publication eligibility.

[Comparison](research/atlas-local-architecture-results.json): 250 actual retained feature/temporal/result records, 1,006 membership rows across five generations,192 agreeing identity/qualification comparisons; SQLite 3.06 MB versus 2.63 MB compact JSON. Five build median333 ms, hash/reopen3.85 ms, fresh metadata-process95 ms; warm in-memory IDs faster and broad geometry work unchanged. These are candidate-metadata measurements, not native payload query/validation speedups. Retained public directory 31.31 GB/29.16 GiB; configurable laptop active metadata/data and optional external archives preserve logical identities. No runtime implemented here.

DECIDE NOW: scientific contracts/qualifications, authority versus projection, exact predicates, committed coherent pins/history and full validation. PROVISIONAL DIRECTION: chosen hybrid catalogue/files, library/CLI, explicit job/transaction/recovery boundaries. DEFER authoritative SQL acceptance, HTTP/global/distributed workloads, external-drive performance and optional catalogue optimization. REJECT dual authority, unsupported atomicity/fusion/physical-change claims and receipt reopening. Tryfan remains CLOSED / ACCEPTED; all Riffelhorn, regional/dependency/temporal proofs remain authoritative and unchanged. Full validation remains adequate; receipt optimisation CLOSED; Appearance unresolved/non-blocking, Swiss multiview parked. No S7 or production Atlas/Weather/Traverse change.

**Exactly one next task: Atlas maintainable local runtime — first end-to-end vertical slice — NOT BEGUN.** Implement the bounded isolated two-generation real Tryfan/Riffelhorn slice through configured storage, qualified registration, accepted slope→ratio/categorical methods, scoped lifecycle, coherent publication, pinned query and fresh historical replay. Preserve accepted inputs/contracts/production; test index/root ordering, missing-volume/rebuild/recovery and oracle equivalence. No archive migration, new data, HTTP or infrastructure. The report section23 and next-task record define the precise permitted boundary and stopping condition.


## Atlas maintainable local runtime first vertical slice — 2026-10-08

The [runtime report](research/atlas-local-runtime.md) records **C — VERTICAL SLICE SUCCESS** for the accepted seven-component Tryfan/Riffelhorn retained publication. The [library and CLI](../runtime/atlas/README.md) now perform explicit-path full validation, disposable SQLite build/verify, qualified pinned queries, fresh restart and deletion/rebuild. Canonical files/component manifests and the filesystem publication root remain authority; SQLite contains only rebuildable selectors and references. No runtime publication writer, new registration or scientific derivation execution is claimed. This completes the current user's narrowed read/index/query slice; the earlier wider write/derivation proposal remains historical context.

Real population: 44 Riffelhorn records plus five qualified Tryfan source-product descriptors, seven components and three retained generations. All 28 supported independent native-oracle cases and 84 repeated indexed/runtime-scan comparisons agree. Full open median2.29s, build/rebuild about195ms, SQLite80KB; point candidates10, exact feature1, broad44. Metadata closure and cache audits remain population-wide; elapsed queries are similar to scans at this scale. Temporal unknowns, rights/provenance, native support and exact publication identities remain visible. Tryfan descriptors are metadata inspection, not a new point-measurement method.

Tryfan remains CLOSED / ACCEPTED; accepted Riffelhorn source/preparation/retrieval, multi-region, regional derivation, temporal integration and local architecture evidence remain authoritative and unchanged. Full validation remains default; receipt optimisation CLOSED; Swiss multiview parked. No S7, new data, private access, production Atlas/Weather/Traverse or infrastructure change. Later temporal/dependency adapters, cache retirement and global performance remain deferred.

**Exactly one current next task: Atlas local runtime deterministic derivation and scoped lifecycle integration — NOT BEGUN.** [Task boundary](../runtime/atlas/next-task.json): reuse one accepted real method and downstream summary, integrate explicit worker/output identities and scoped lifecycle, minimal isolated coherent publication, old/new pinned replay and oracle/recovery tests. Advance the usable local workflow; no new scientific algorithm, generic orchestration or production service. The earlier first-slice next-task entry is superseded by this completed result.

Verification: **65 safeguards and 508 tests passed; runtime/semantic/application types, lint and build passed.** All 42 canonical research statuses, 113 protected production hashes and accepted canonical/source/prepared evidence remain unchanged.


## Atlas local runtime deterministic derivation/lifecycle integration - 2026-10-09

The [lifecycle report](research/atlas-local-lifecycle.md) records **C — LIFECYCLE INTEGRATION SUCCESS**. The [runtime library/CLI](../runtime/atlas/README.md) now executes accepted native Riffelhorn Horn slope and planar-area ratio on 16 real probes/32 outputs, preserves qualified immutable input/use/method/parameter identities, inspects scoped dependencies, stages and fully validates coherent nine-component publications, and queries pinned history. Canonical files and the filesystem root remain authoritative; SQLite remains disposable. `world init`, `derive stage/inspect`, `stage validate/publish`, `derived` and `world recover` provide the operational workflow. The [complete CLI example](../runtime/atlas/example-lifecycle.mjs) avoids manual research-harness operation.

Three identical initial publications and 21 selective/full comparisons agree; 96 accepted numerical comparisons agree. Local knowledge correction affects 8/reuses 24, one-probe parameter affects 2/reuses 30, unrelated Tryfan notice affects 0/reuses 32, shared-source correction affects 32. Three fresh historical replays remain coherent with zero ancestry traversal. Real graph: 4 registered sources (one consumed), 16 uses, 32 derived outputs, 48 edges, depth 3. Full validation remains population-wide and dominates this small workload; selective processing is not an end-to-end speedup claim. [Measurements](research/atlas-local-lifecycle-results.json) disclose timing spreads, logical read/write counts and external storage. Actual abrupt processing/publication exits remain unpublished and recover without changing old pins.

Tryfan remains CLOSED / ACCEPTED; Riffelhorn source/preparation/retrieval, multi-region, dependency and temporal proofs remain authoritative and unchanged. Frozen contracts, 42 research statuses and 113 protected production hashes remain unchanged. Full validation default and receipt optimisation CLOSED are preserved; Swiss multiview parked. No S7, acquisition, private access, production Atlas/Weather/Traverse or infrastructure change. DECIDE NOW: qualified exact dependencies and canonical full-validated publication. PROVISIONAL: finite runtime processing/lifecycle and canonical 32-result lookup. DEFER generic registration/methods/temporal runtime and larger operational workloads until bounded integration. REJECT dual authority, unsupported source fusion/physical change, stale publication or optimization reopening.

**Exactly one current next task: Atlas local runtime qualified evidence registration and regional update workflow — NOT BEGUN.** [Task boundary](../runtime/atlas/lifecycle-next-task.json): eliminate the research-store bootstrap dependency with accountable runtime registration of existing prepared regional evidence, one bounded administrative update, scoped dependent handling and pinned historical/recovery tests. No new datasets, scientific methods, general ingestion or production service. This completed lifecycle result supersedes the preceding unbegun task entry without altering accepted research history.

Final workflow medians: full open 3.50 s, SQLite build 253 ms/80 KB, exact derived lookup 135 ms; six-generation fresh replay 23.59 s. Each measured world 9.46 MB; immutable execution records retain worker/coordinator versions and source hashes without replacing validation. Verification: **73 safeguards and 569 tests passed; types, lint and build passed.** The complete CLI example also passed.


## Atlas local runtime qualified evidence registration/update - 2026-10-09

The [registration/update report](research/atlas-local-registration.md) records **C — REGISTRATION AND UPDATE SUCCESS**. The [runtime library/CLI](../runtime/atlas/README.md) now assembles native Tryfan/Riffelhorn canonical registration directly from the accepted reference and preparation manifests, without copying a multi-region research store. `evidence inspect/register/revise` and `update plan/validate/publish` expose exact native identities, immutable knowledge acceptance/supersession, accountable request files and explicit dependency effects. Canonical files/root remain authoritative; SQLite is rebuildable.

Informational and unrelated-region knowledge revisions reuse all 32 quantities. A controlled retained-source qualification requalifies exactly eight and reuses 24 using unchanged samples/values/method/support; independent full native derivation validates publication. Unconsumed-source qualification does not force numerical work. Native observation/source times and unknowns remain unchanged; registration or knowledge correction never implies physical change. Invalid/discarded/forked/incomplete knowledge/dependency states remain unpublished, actual process interruption recovers, and historical pins survive restart/catalogue rebuild. [Measurements](research/atlas-local-registration-results.json) distinguish verification, metadata requalification, full publication, query, storage and replay costs. Source/product replacement and new physical observations remain unsupported by this bounded retained adapter.

Tryfan remains CLOSED / ACCEPTED; accepted Riffelhorn preparation/retrieval, multi-region/dependency/temporal research and earlier runtime findings remain authoritative and unchanged. Frozen contracts, 42 research statuses and 113 protected production hashes are preserved. Full validation remains default; receipt optimisation CLOSED; Swiss multiview parked. No S7, acquisition/private access, production Atlas/Weather/Traverse, cloud or public-service work. DECIDE NOW: source/prepared/derived/knowledge/publication identity separation and exact revision guards. PROVISIONAL: finite native registration ledger and metadata-only requalification. DEFER generic source replacement, arbitrary ingestion and operational/global scale. REJECT physical-change inference, history rewrites and duplicate database authority.

**Exactly one current next task: Atlas local runtime qualified retrieval across registered source and derived evidence — NOT BEGUN.** [Task boundary](../runtime/atlas/registration-next-task.json): make existing native spatial/feature/year and derived quantities usable through one scientifically qualified pinned workflow, with explicit native/stencil/quantity support and unknown temporal/knowledge semantics. No new datasets/methods, general query platform or service. This completed result supersedes the preceding unbegun registration task entry while preserving historical records.

Workflow medians: verified native inspection 2.27 s; initial registration 4.82 s; current full open 2.32 s; source-qualification stage 2.77 s and publication 3.21 s; catalogue build 235 ms / 80 KB; five-generation fresh replay 27.92 s. Each measured world retains 4.91 MB. All nine scoped/full comparisons and six query/rebuild comparisons agreed; three fresh historical replays agreed. **80 safeguards and 613 tests passed; types, lint and build passed.** Full validation and explicit registration-chain maintenance remain included.
