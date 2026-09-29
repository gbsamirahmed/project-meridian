# Meridian architecture contract

This document records Meridian's current architectural direction. It defines the
rules for later migration and implementation; it does not claim that the repository
or external data have already been reorganised to match them.

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

Python tooling resolves two external roots through
`scripts/meridian_paths.py`:

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
Frozen entry points that still accept explicit paths retain their documented
behaviour until Phase 4 deliberately updates their references. Setting an environment
variable does not secretly alter a script that does not call the resolver.

## Target external data layout

Phase 4 uses this contract through copy, validation and hash comparison before any old
copy is removed. Phase 4B has preserved historical Earth experiments under `experiments`,
and Phase 4C has created validated Tryfan source and derived products under `sources/atlas`
and `derived/atlas`. Phase 4D has created the separate private root and copied private
Traverse source, benchmark, experiment and cache data into it. The original trees remain
until the Phase 4G deletion gate:

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
temporary rollback copies until Phase 4G; their presence is not permission for new
private data to enter the general data root.

Classification precedes movement. A mixed historical directory may be preserved
under `experiments` rather than split if splitting would damage provenance or create
fragile references.

## Experiments and compatibility

Historical experiments retain their original names, configs, hashes and output
identities. Code becomes shared infrastructure only after it has a continuing role
beyond the experiment that created it. Promotion gives code a role-based name and an
explicit contract; it does not rewrite the experiment record.

The current `scripts/earth_lab`, `docs/earth-lab` and
`meridian-data/earth-lab` paths remain in place during Phase 3. Their legacy
sibling-relative paths are deliberate compatibility exceptions. They are catalogued
for controlled migration rather than edited across frozen Labs.

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
