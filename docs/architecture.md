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
