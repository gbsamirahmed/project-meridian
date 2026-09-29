# Phase 4 filesystem migration execution plan

**Status: PHASE 4D COPIED AND VALIDATED — all old data retained; Phase 4E has not begun.**

This plan refines the [Phase 4 migration inventory](phase-4-migration-inventory.md)
using read-only inspection performed in Phase 4A. A later task must execute only one
subphase at a time.

Path notation:

- `[REPO]` = `project-meridian`
- `[DATA]` = `MERIDIAN_DATA_ROOT`
- `[PRIVATE]` = `MERIDIAN_PRIVATE_ROOT`

The governing rule is:

```text
COPY -> UPDATE ACTIVE REFERENCES -> VALIDATE -> COMPARE
     -> ONLY THEN, IN A SEPARATE REVIEWED STEP, REMOVE OLD COPY
```

Frozen experiment configs, reports and names remain historical evidence. Moving their
files does not permit rewriting what the experiments recorded.

## Verified Phase 4A snapshot

| Area | Files | Bytes | Interpretation |
| --- | ---: | ---: | --- |
| `[DATA]/earth-lab` | 5,796 | 1,845,508,901 | Mixed Python environment, experiments, source subsets, derived products and old Unreal state |
| `[DATA]/terrain-research` | 385 | 166,167,590 | Private route-conditioned experiments and reacquirable terrain caches |
| `[DATA]/activity-research` | 2,268 | 157,302,730 | Private analysis, derived reports and DEM cache |
| `[DATA]/strava-export` | 341 | 34,779,474 | Private source export |
| `[DATA]/route-benchmarks` | 11 | 2,212,283 | Private GPX benchmark inputs |
| `[REPO]/public/weather/gfs` | 42,283 | 2,591,121,422 | Ignored generated publication, source cache and interrupted/partial history |

The general external estate totals 8,801 files and 2,205,970,978 bytes. The ignored
GFS tree is additional. `[PRIVATE]` does not exist yet.

Earth experiment sizes:

| Directory | Files | Bytes | Dominant formats |
| --- | ---: | ---: | --- |
| `earth-lab/.venv` | 4,878 | 230,777,822 | Python environment — regenerate |
| `tryfan-001` | 392 | 312,666,399 | Old Unreal packages plus terrain experiment |
| `tryfan-004` | 171 | 1,012,754,486 | Terrain/source products, diagnostics and old Unreal workspace |
| `tryfan-005b` | 64 | 11,205,616 | Sentinel GeoTIFFs and diagnostics |
| `tryfan-005c` | 171 | 28,865,253 | Multiseason Sentinel GeoTIFFs and diagnostics |
| `tryfan-006` | 33 | 14,357,751 | Habitat/geology source extracts, aligned products and diagnostics |
| `tryfan-007` | 49 | 11,287,793 | Surface inference package, rasters and diagnostics |
| `tryfan-008` | 13 | 4,319,474 | Uncertainty audit rasters and diagnostics |
| `tryfan-009` | 25 | 219,274,307 | Reconstruction rasters, renderer transports and invalid capture attempts |

The canonical repository map remains SHA-256
`85ef8f1cc9a9fda9b6f2ab3b911bd57831fe75c4009e5ad168ea4956165a260d`
and is byte-identical to the external Lab 004 map.

## Dependency graph

| Consumer/reference | Current dependency | Class | Migration treatment |
| --- | --- | --- | --- |
| Tryfan Reference Renderer bootstrap and manifest | Lab 004 terrain manifest/R16/photo; Lab 009 report/package/packed controls below `[DATA]/earth-lab` | **ACTIVE** | Update only after promoted products exist and hashes match. Regenerate ignored absolute source pointers. No map save. |
| Lab 005A–009 analysis scripts | Config values resolved directly from `../meridian-data/earth-lab/...` by several local helper functions | **ACTIVE HISTORICAL ENTRYPOINT** | Preserve config text; adopt `resolve_project_path` in entrypoints/tests and map the legacy prefix to `[DATA]/experiments/earth-lab`. |
| Lab acquisition/Unreal preparation commands | Explicit `--data-root`, `--terrain-root`, `--output-root` or `--project-root` paths | **ACTIVE, CALLER-SUPPLIED** | Update current examples after copy. Historical report/config values remain unchanged. |
| `docs/earth-lab/*.json` and frozen reports | Original `../meridian-data/earth-lab` and some generated absolute paths | **HISTORICAL REFERENCE** | Do not rewrite. Compatibility belongs in the resolver/entrypoint, not the provenance record. |
| Ignored renderer `meridian-*-source.json` | Concrete absolute paths used by Unreal Python | **GENERATED POINTER** | Bootstrap rewrites after active paths change. Never commit. |
| Earth Lab README command lines | Sibling-layout examples | **DOCUMENTATION EXAMPLE** | Update current run instructions when the matching subphase executes; retain historical narrative. |
| Terrain-research runners | Required explicit GPX, output and repository roots | **ACTIVE, LOCATION-INDEPENDENT** | Supply `[PRIVATE]` paths after migration. No algorithm change. |
| Activity-research runners | Required explicit export/ingestion/output roots | **ACTIVE, LOCATION-INDEPENDENT** | Supply `[PRIVATE]` paths after migration. No private path enters Git. |
| Route benchmark GPX | No fixed repository path found | **NO HARD-CODED DEPENDENCY** | Move as a private source set with a non-disclosing private manifest. |
| GFS builder/updater | Defaults to `[REPO]/public/weather/gfs` | **ACTIVE STORAGE DEPENDENCY** | Change generation to an external derived root in Phase 4E. |
| Browser weather client | Fetches `/weather/gfs/latest.json` | **ACTIVE PUBLICATION CONTRACT** | Keep URL stable; add a local publication adapter. Browser must never receive a filesystem path. |
| Vite build plugin | Copies all of `public` except the updater lock | **ACTIVE BUILD DEPENDENCY** | Stop treating bulk weather storage as ordinary public source; publish selected output deliberately. |
| Visual smoke test | Reads `public/weather/gfs/latest.json` before intercepting requests | **ACTIVE TEST DEPENDENCY** | Resolve a fixture/publication view independently of authoritative storage. |
| Old external Unreal logs, IMPORT files and pointer JSON | Machine-local absolute paths | **GENERATED/HISTORICAL** | Do not promote. Preserve only in the pre-restructure backup where needed. |
| Old external `DefaultEngine.ini` files | Generated Android file-server credentials in both legacy projects | **SECRET-BEARING LOCAL STATE** | Never copy wholesale into the general hierarchy or Git. Use curated secret-free config only. |

## Classification decisions

### Historical experiments

| ID | Current source | Destination | Status | Notes |
| --- | --- | --- | --- | --- |
| EXP-001 | `[DATA]/earth-lab/tryfan-001` excluding its raw Unreal workspace initially | `[DATA]/experiments/earth-lab/tryfan-001` | PLANNED | Copy terrain outputs, manifests and diagnostics intact. |
| EXP-002-U | Secret-free historical subset of `tryfan-001/unreal-project/TryfanLab002` | `[DATA]/experiments/earth-lab/tryfan-001/unreal-project/TryfanLab002` | REVIEW REQUIRED | Preserve `.uproject`, complete `Content` including corrected map and external actors, and a curated config. Exclude Saved, Intermediate, DDC, bytecode, pointers and the credential-bearing config section. |
| EXP-004 | `[DATA]/earth-lab/tryfan-004` excluding `unreal-project` | `[DATA]/experiments/earth-lab/tryfan-004` | PLANNED | Retains source subsets, reports, diagnostics and frozen reconstruction inputs. |
| EXP-004-U | Old external TryfanLab004 project | No new destination | DO NOT MOVE | Repository renderer is canonical and the backup preserves recovery evidence. Retain old copy until Phase 4G review; never copy its credential-bearing config. |
| EXP-005B/C | `tryfan-005b`, `tryfan-005c` | `[DATA]/experiments/earth-lab/<same-id>` | PLANNED | Preserve reports, source subsets, aligned products and diagnostics intact. |
| EXP-006 | `tryfan-006` | `[DATA]/experiments/earth-lab/tryfan-006` | PLANNED | Preserve source acquisition evidence and scale semantics. |
| EXP-007/8/9 | `tryfan-007`, `tryfan-008`, `tryfan-009` | `[DATA]/experiments/earth-lab/<same-id>` | PLANNED | Preserve complete frozen outputs even when selected products are promoted separately. |

The Lab 001/002 Unreal project is not a cache: its corrected map and older World
Partition packages are historical binary state. Its `Intermediate`, DDC and routine
`Saved` contents are transient. Its generated Android credential prevents blind
copying.

### Atlas source observations

These source subsets are small enough, scientifically relevant and potentially harder
to reacquire exactly than to retain:

| ID | Product | Proposed destination | Status |
| --- | --- | --- | --- |
| SRC-LIDAR | Lab 004 1 m DTM/DSM AOI rasters plus acquisition catalogues/manifest | `[DATA]/sources/atlas/tryfan/welsh-lidar-1m/` | KEEP |
| SRC-PHOTO | Tony Edwards and Robert Heath source images plus licence/source metadata | `[DATA]/sources/atlas/tryfan/reference-photography/` | KEEP |
| SRC-S2 | Lab 005B native subset and Lab 005C seasonal observation subsets, organised by official product ID | `[DATA]/sources/atlas/tryfan/sentinel-2-l2a/` | KEEP |
| SRC-CONTEXT | Lab 006 retrieved/clipped NRW/BGS evidence and service/licence records | `[DATA]/sources/atlas/tryfan/context/` | KEEP |

The promoted source manifest must record the originating experiment path and hashes.
It must describe subset/clip status honestly; a clip is not the provider's complete
native dataset.

### Reusable Atlas-derived products

A product is promoted only when a consumer can use it without understanding the Lab's
directory layout.

| ID | Promoted product | Destination | Size | Decision |
| --- | --- | --- | ---: | --- |
| DER-TERRAIN | Canonical DTM R16 and landscape manifest | `[DATA]/derived/atlas/tryfan/terrain/unreal-landscape-v1/` | about 18 MiB plus manifest | PROMOTE; canonical status remains manifest metadata |
| DER-MORPH | Lab 005A elevation, slope, aspect, three curvature and three roughness GeoTIFFs | `[DATA]/derived/atlas/tryfan/terrain/surface-metrics-v1/` | about 250 MiB | PROMOTE; reusable measured-terrain derivatives |
| DER-007 | Lab 007 model package; six probability rasters; entropy, conflict and evidence-family-count rasters | `[DATA]/derived/atlas/tryfan/surface/inference-v1/` | 10 files / 2,101,577 bytes | PROMOTE; Tryfan ontology and 10 m information scale stay explicit |
| DER-008 | Reconstruction-readiness raster plus a new neutral manifest defining category codes and frozen Lab 008 identity | `[DATA]/derived/atlas/tryfan/surface/reconstruction-readiness-v1/` | 13,858 bytes plus manifest | PROMOTE ONLY THIS CONTROL; other Lab 008 rasters remain audit evidence |
| DER-009 | Lab 009 package plus eight 3025×3025 GeoTIFF controls | `[DATA]/derived/atlas/tryfan/surface/reconstruction-v0.1/` | 9 files / 187,776,580 bytes | PROMOTE; manifest must state 0.992 m renderer grid is reconstructed, not 1 m observation |

Do not promote:

- Lab 007 contribution rasters or diagnostic PNGs: experiment explainability.
- Most Lab 008 flags/plots/ablations: audit evidence, not a current renderer contract.
- Lab 009 diagnostic images or automated captures: experiment evidence.
- Lab 009 packed RGBA PNGs as renderer-neutral data: Unreal transport generated from
  the reconstruction controls.
- A hard dominant class as the canonical surface: probabilities remain authoritative.

The Unreal transport packer should eventually generate the two RGBA images into
`[DATA]/cache/renderers/unreal/tryfan-reference/` from DER-009 and verify the known
hashes. Until that small extraction exists, the bootstrap may consume the frozen
experiment copies; this dependency must be explicit and temporary.

### Private Traverse estate

| ID | Current source | Destination | Status |
| --- | --- | --- | --- |
| PRIV-STRAVA | `[DATA]/strava-export` | `[PRIVATE]/traverse/sources/strava-export/` | PRIVATE / IRREPLACEABLE |
| PRIV-ROUTES | `[DATA]/route-benchmarks/gpx` | `[PRIVATE]/traverse/benchmarks/routes/` | PRIVATE unless public status is positively proved |
| PRIV-ACTIVITY | `[DATA]/activity-research` excluding separable cache | `[PRIVATE]/traverse/experiments/activity-research/` | PRIVATE |
| PRIV-TERRAIN | `[DATA]/terrain-research/{wales-v1,england-v2}` experiment results | `[PRIVATE]/traverse/experiments/terrain-research/` | PRIVATE |
| PRIV-CACHE | Activity DEM cache and route-conditioned terrain caches | `[PRIVATE]/traverse/cache/` | PRIVATE / REACQUIRABLE |

Terrain-research is not a general Atlas data product: its source provider adapters are
reusable Git code, but the stored profiles, reports and plots are conditioned on
private routes. The Wales cache is 34,613,561 bytes; England cache is 127,192,115
bytes. Derived/report/plot output is small and historically useful.

Private manifests must remain under `[PRIVATE]`. Git may record aggregate counts,
bytes and an aggregate manifest digest, but not private filenames, coordinates,
activity identifiers or hashes that expose naming.

### Weather publication

Current GFS storage consists of:

| Class | Files | Bytes | Status |
| --- | ---: | ---: | --- |
| Two complete immutable runs | 40,840 | 1,268,047,795 | DERIVED PUBLICATION; current plus previous |
| Eleven atmospheric source-building caches | 1,320 | 1,212,538,419 | CACHE; stale cycles, not removed by current prune functions |
| Older partial run | 121 | 110,532,448 | GENERATED/SUPERSEDED |
| `latest.json` and updater lock | 2 | 2,760 | Mutable publication pointer / transient lock |

Recommended authoritative storage:

`[DATA]/derived/weather/gfs/`

The browser URL remains `/weather/gfs/...`. Storage and publication are separated by
a local publication adapter:

1. the updater writes/retains current plus one previous complete run externally;
2. a repository command creates an ignored local publication view at
   `public/weather/gfs` (directory junction on Windows, symlink where supported,
   or explicit copy mode);
3. Vite serves the view without learning the private filesystem path;
4. production publication synchronises selected immutable runs and `latest.json`
   separately rather than treating the source store as committed public assets;
5. visual tests resolve the prepared publication view or a checked fixture.

The adapter must refuse an unexpected target, never delete through an unverified
junction, and report source/destination identities. The browser needs no code change
to its URL contract. A later deployment may replace the local adapter with an object
store/CDN base URL without changing GFS model semantics.

## Source retention policy

| Source class | Policy | Reason |
| --- | --- | --- |
| Welsh LiDAR AOI DTM/DSM and catalogues | **KEEP** | Exact bounded extracts are modest (about 31.6 MiB), underpin canonical terrain, and upstream catalogues/COGs may change. |
| Sentinel-2 native AOI subsets for four observations | **KEEP** | Approximately 5.7 MiB total source windows; exact processing baselines/products are recorded but provider collection access can evolve. Storage is cheaper than risking exact reacquisition. |
| NRW/BGS retrieved context evidence and licence/service records | **KEEP** | About 10.4 MiB; preserves what was actually queried/rendered, including scale and release context. |
| Terrain block caches | **CACHE** | Reacquirable from official providers; keep only while useful, under private root when route-conditioned. |
| GFS GRIB source caches | **CACHE / REACQUIRE** | Large, short-lived and not needed after validated tile publication. Optionally archive one named cycle only for a declared benchmark. |
| Complete GFS tile publications | **ROLLING KEEP** | Retain current plus one previous valid run, matching existing code policy. Long-term archive only for explicit benchmarks. |
| Python virtual environments | **REGENERATE** | Requirements are version-controlled; environments are machine-specific. |
| Unreal imported materials/textures/Python deployments | **REGENERATE** | Repository bootstrap and source products reproduce them. |
| Unique Unreal maps | **KEEP WITH STRONG HASHES** | Binary calibrated state is not otherwise reproducible byte-for-byte. |

## Duplicate and superseded candidates

| Candidate | Finding | Later treatment |
| --- | --- | --- |
| Repository and external Tryfan Lab 004 map | **Confirmed duplicate** by SHA-256 | Repository LFS map is source of truth; keep external copy only through final recovery review. |
| External Lab 004 generated materials/textures/Python | **Generated/reproducible** | Do not migrate as durable source. |
| External Lab 004 DDC, Intermediate and most Saved state (about 538 MiB) | **Transient** | Do not copy; eligible for Phase 4G removal after recovery validation. |
| Lab 001/002 DDC, Intermediate and routine Saved state | **Transient**, but Content contains historical unique packages | Exclude transient trees; hash and preserve curated Content separately. |
| Earth Lab `.venv` (230,777,822 bytes) | **Generated** | Recreate; do not migrate. |
| Lab 009 extensionless capture files and `.png` files | Same size and PNG signature but **different hashes**, so not duplicates | Keep as invalid/historical capture evidence with experiment or mark obsolete; do not deduplicate by size. |
| Lab 009 automated captures generally | **Obsolete but historically meaningful**; report says visual acceptance remained pending | Do not promote. Later experiment-retention policy may archive or omit them only with explicit review. |
| GFS source-building directories and old partial run | **Generated/reacquirable/superseded** | Do not migrate to derived publication; retain old tree until Phase 4G gate. |
| Lab 005B summer native observation in Lab 005C | **Referenced reuse**, not an unexplained duplicate | Preserve one source identity and explicit cross-reference when promoted. |
| Pre-restructure backup | **Intentional safety duplicate** | Never treat as cleanup candidate during Phase 4. |

## Execution order

### Phase 4B — historical Earth experiments

**Status: COPIED AND VALIDATED; REVIEW PENDING. No old copy has been removed.**

The explicit selection is recorded in
[`phase-4b-migration-manifest.json`](phase-4b-migration-manifest.json). The generated
full comparison inventory is stored at
`[DATA]/experiments/phase-4b-earth-lab-validation.json` with SHA-256
`c8c33c5c32624794dc3ff7fcc097a18d7d60a0bd735b8197d690373fa0a6278b`.
The payload contains 712 files and 814,688,394 bytes: 711 source files match their
destination SHA-256 exactly, and one 88-byte `DefaultEngine.ini` is the approved
secret-free projection of the Lab 001/002 project settings. The source tree remains
5,796 files and 1,845,508,901 bytes. Phase 4C promotion has not begun.

**Reasoning:** high.

**Scope**

- Copy EXP-001 and EXP-004–009 into `[DATA]/experiments/earth-lab`.
- Exclude `earth-lab/.venv`.
- Exclude the old Lab 004 Unreal project.
- Handle EXP-002-U as a separately reviewed, secret-free copy set.

**Prerequisites**

- Confirm free space for both old and copied trees.
- Generate a pre-copy inventory outside the source tree.
- Reverify all 27 backup-critical hashes and frozen Lab 007–009 identities.
- Define exact include/exclude lists before the copy command.

**Copy method**

Use one PowerShell/robocopy invocation per experiment, source to destination, with
`/E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ` and explicit exclusions. Do not compose
paths across shells. Do not use `/MOVE`, `/MIR` or deletion flags.

**References**

- Adopt `resolve_project_path` in historical analysis entrypoints/tests while leaving
  config strings unchanged.
- Change the resolver's legacy `../meridian-data/earth-lab` mapping to
  `[DATA]/experiments/earth-lab` only after the destination validates.
- Update current command examples; do not rewrite frozen reports/configs.
- Leave renderer bootstrap references unchanged until Phase 4C.

**Validation/compare**

- Complete SHA-256 manifests for each experiment's non-cache files.
- Existing report output inventories and deterministic identities.
- Raster header/CRS/dimension checks.
- Full Earth Lab suite with an environment override pointing at the new root.
- Lab 001/002 Content: complete tree hash plus corrected-map critical hash.
- Credentials scan on any curated Unreal config.

**Rollback**

Delete only the incomplete destination created by this subphase after confirming its
resolved absolute path is within `[DATA]/experiments`. Source remains untouched.

**Deletion gate**

None in 4B. Old `[DATA]/earth-lab` stays intact until 4G.

**Expected Git changes**

Resolver adoption, tests and current documentation. Frozen JSON identities unchanged.

**Unreal**

No Unreal launch for ordinary experiment copies. EXP-002-U needs a later headless
open/validator only if it is intended to be a recoverable historical project rather
than a binary archive.

### Phase 4C — Atlas sources and reusable Tryfan products

**Status: COPIED AND VALIDATED; REVIEW PENDING. No old copy has been removed.**

The explicit 9-product, 93-file selection is recorded in
[`phase-4c-promotion-manifest.json`](phase-4c-promotion-manifest.json); the neutral
consumer catalogue is [`atlas/tryfan-data-catalog.json`](atlas/tryfan-data-catalog.json).
The payload is 522,051,687 bytes: 62 retained-source files (76,593,256 bytes) and 31
derived payload files (445,458,431 bytes). Full validation is recorded at
`[DATA]/derived/atlas/tryfan/phase-4c-validation.json` with SHA-256
`37faf10aab6dc62895a19fcafbe58098741ef2776ea347772e203d02cb58e788`.

**Reasoning:** high.

**Scope**

Copy SRC-LIDAR, SRC-PHOTO, SRC-S2 and SRC-CONTEXT to `sources`; copy DER-TERRAIN,
DER-MORPH and DER-007/8/9 to `derived`. Create neutral manifests without editing the
frozen source products.

**Prerequisites**

Phase 4B experiment copies and hashes must pass. Define product schemas and relative
paths before copying.

**References**

- **Phase 4C decision:** do not repoint the Tryfan Reference Renderer in this phase. It
  continues to consume the hash-verified historical experiment inputs.
- Packed RGBA textures remain renderer-specific transport artefacts. The integrated
  historical packer remains in place; extraction is not required to use the promoted
  eight renderer-neutral GeoTIFF controls.
- New Atlas consumers use the neutral catalogue, never Lab directory knowledge.
- Historical Lab references remain unchanged.

**Copy/compare**

Use explicit file lists, not broad directory copies. Verify every promoted file
against the existing authoritative SHA where available; otherwise create source and
destination hashes in one manifest. Validate raster CRS, dimensions, transforms,
dtype/nodata, probability sums and reconstruction hashes.

**Renderer validation**

Because renderer dependencies were deliberately unchanged, verify the existing seven
external-input hashes and canonical map hash without launching or saving Unreal. A future
renderer integration phase may deliberately switch to promoted products.

**Rollback/deletion gate**

No active renderer or frozen-Lab reference changed. Rollback consists only of removing
the new promoted destination and reverting the new catalogue/manifest before checkpointing.
Experiment and original copies remain. No original source/derived file is removed in 4C.

**Expected Git changes**

Neutral promotion manifest/catalogue and current architecture documentation. No
bootstrap, renderer package, LFS map, frozen config or scientific implementation change.

### Phase 4D — private Traverse data

**Status: COPIED AND VALIDATED; REVIEW PENDING. No old copy has been removed.**

The privacy-safe aggregate selection and validation result are recorded in
[`phase-4d-private-migration-manifest.json`](phase-4d-private-migration-manifest.json).
The private copy contains 3,005 payload files / 360,462,077 bytes. A detailed private
inventory remains outside Git under `[PRIVATE]/traverse` and has SHA-256
`ec92b799b1e59da7ab955e5805983ec652c57f6b0581f88a3d658bc7885b66cc`.

**Reasoning:** high because data is private and partly irreplaceable.

**Scope**

Create `[PRIVATE]/traverse` only in this authorised execution phase. Copy
PRIV-STRAVA, PRIV-ROUTES, PRIV-ACTIVITY, PRIV-TERRAIN and private caches.

**Prerequisites**

- Verify `[PRIVATE]` is outside Git and does not overlap `[DATA]`.
- Confirm sufficient free space and local backup.
- Create a private full SHA-256 manifest for Strava exports and all GPX/FIT/GZ source
  files without printing names or hashes to the public log.

**References**

The activity and terrain runners already accept explicit roots, so no implementation
change was required. Future invocations use `[PRIVATE]` paths or the root resolver. No
browser/environment bundle exposure was introduced.

**Validation**

Complete hashes for private sources; complete or manifest-led hashes for small
derived reports; file count/size plus sampled hashes for reacquirable caches. Run
activity and terrain synthetic tests and read-only report checks.

**Rollback**

Before checkpointing, remove only an incomplete new private destination after review.
After validation, retain both copies until Phase 4G. Never modify source exports.

**Deletion gate**

Private manifest matches, tools run against destination, privacy scan confirms no
private paths/data entered Git or `[DATA]`, and backup remains available.

**Expected Git changes**

Privacy-safe aggregate manifest and current architecture/migration documentation only.
No detailed private inventory or payload in Git.

**Unreal**

None.

### Phase 4E — Weather/GFS external storage and publication

**Status: copied and validated; legacy publication retained pending Phase 4G.**

**Reasoning:** high for publication safety; medium for file copying.

**Scope**

Copy only the two validated complete immutable runs and `latest.json` to
`[DATA]/derived/weather/gfs`. Do not copy stale source-building caches, lock or old
partial run into the derived store.

**Prerequisites**

Run existing GFS semantic validators on both complete runs and confirm `latest.json`
names one of them. Design and test the local publication adapter in a temporary
directory.

**References**

- Builder/updater output root becomes explicit/root-aware.
- Browser URL stays `/weather/gfs`.
- Vite and visual-test filesystem assumptions use the publication adapter.
- Current documentation distinguishes storage, local publication and production
  deployment.

**Validation**

Existing field/tile validators for all ten fields and 24 timesteps; exact
`latest.json` and manifest hashes; expected 20,420 files per complete run; web unit
tests, production build and visual smoke. Confirm missing publication remains an
explicit unavailable state.

**Rollback**

Point the adapter back at the existing ignored tree. External copied runs remain
isolated. Never alter the browser to consume a local absolute path.

**Deletion gate**

The copied current and previous runs, guarded dev adapter and bounded production build
have validated. Removal remains blocked until an updater successfully publishes a newer
run externally, retention preserves current plus previous, and Phase 4G explicitly
reviews the unchanged legacy publication and stale/partial material.

**Implemented validation**

The two retained runs contribute 40,841 payload files / 1,268,050,554 bytes. Every
source/destination SHA-256 matched; both runs passed the existing ten-field, 24-timestep
PNG validator. Development HTTP requests, a production build and representative
catalogue/manifest/tile hashes validated the stable browser contract. The detailed
external inventory is recorded by the tracked Phase 4E manifest.

**Expected Git changes**

Weather launcher/config, publication adapter, Vite/visual-test integration, tests and
docs.

**Unreal**

None.

### Phase 4F — cache, scratch and generated-state disposition

**Status: GFS generated/cache subset disposed; complete publication rollback retained for Phase 4G.**

**Reasoning:** medium, with high caution for path verification.

**Scope**

Classify but do not automatically carry forward Earth Lab `.venv`, stale GFS source
caches/partial run, old Unreal DDC/Intermediate/routine Saved state, bytecode and
private terrain/DEM caches.

**Method**

Recreate needed environments/caches at their destination, prove consumers work, then
produce an explicit removal candidate list. No wildcard deletion and no recursive
operation without resolved-path containment checks.

**Validation**

Rebuild tests for environments; provider reacquisition smoke checks for caches;
renderer bootstrap for Unreal generated state; GFS validation for publication.

**Rollback**

Caches can be regenerated; the pre-restructure backup is not modified.

**Deletion gate**

Each candidate is positively identified as generated/reacquirable, no unique source
or report shares its directory, and the owning workflow has passed from the new
location.

**Expected Git changes**

Ignore rules and documentation only where gaps exist.

**Implemented GFS disposition**

After verifying the external authoritative publication and proving no active consumer used
the legacy candidates, Phase 4F removed eleven stale atmospheric source-building caches,
the incomplete `20260902T18Z` atmospheric inspection cache and the obsolete legacy updater
lock. The operation named and containment-checked all thirteen paths individually; it did
not use wildcard deletion or follow reparse points. The removed set was 1,442 files /
1,323,070,868 bytes. The legacy tree now contains only the two complete validated runs and
`latest.json` (40,841 files / 1,268,050,554 bytes), matching the external aggregate by
inventory. Those complete rollback copies remain subject to the Phase 4G gate.

### Phase 4G — final validation and removal of superseded copies

**Status: GFS rollback category independently validated and retired; no other category removed.**

**Reasoning:** maximum.

**Scope**

No new classification or feature work. Audit old and new roots, then remove approved
old physical copies one bounded category at a time.

**Required evidence**

1. Destination manifests/hashes match.
2. Active references resolve only to destination or documented generated pointers.
3. Full Earth Lab, private-tool, renderer and web/weather validations pass as
   applicable.
4. Frozen identities and canonical map hash remain unchanged.
5. Privacy scans pass.
6. Restore backup remains valid.
7. Git checkpoints for 4B–4F are pushed and recoverable.
8. Human approval names the exact old path to remove.

The old external TryfanLab004 project and credential-bearing legacy config require an
explicit final decision. The pre-restructure backup remains untouched even after
active-copy cleanup.

**Implemented GFS retirement**

The external current and previous runs passed the full ten-field, 24-timestep PNG validator.
Their exact relative path/size inventory matched the legacy rollback copy; `latest.json`
and all twenty run manifests matched by SHA-256. Development HTTP serving, direct
publication validation and a production build consumed external storage. After explicit
root-separation, containment and reparse-point checks, Phase 4G removed the three named
legacy payload entries and then the empty `public/weather/gfs` root: 40,841 files /
1,268,050,554 bytes. `public/weather` remains. No other old-copy category was removed.

## Comparison standards

| Data class | Required comparison |
| --- | --- |
| Unique maps, private sources, canonical R16, reference images | Complete SHA-256 for every file plus bytes/count |
| Frozen experiment products with output inventories | Existing hashes plus complete tree manifest for non-cache content |
| Promoted source/derived bundle | Complete explicit manifest with relative path, bytes and SHA-256; semantic raster validation |
| Large complete GFS publication | Catalogue/manifest hashes, semantic full-run validator, exact file count and bytes; no need to hash stale cache |
| Reacquirable cache | File count/bytes plus targeted sample hashes and provider/rebuild smoke test |
| Virtual environment/build cache | Recreate and run tests; do not compare binary tree |
| Renderer | Bootstrap input hashes, generated-asset validator, map hash before/after; Unreal launch only where dependency recovery changes |

File count and size alone are never sufficient for unique, canonical or private source
data.

## Remaining blockers/decisions

- **Resolved in Phase 4B:** the Lab 001/002 historical Unreal set preserves the project,
  complete package Content except bytecode, historical import note and input settings;
  cache/build/Saved state, the generated pointer and secret-bearing configuration
  section are excluded. The authoritative map and external-actor packages are retained.
- **Resolved in Phase 4C:** the Lab 009 packer remains integrated with the historical
  implementation. Packed PNGs are renderer-specific and were not promoted; the renderer
  continues using frozen hash-verified inputs until a separate integration phase.
- **Resolved in Phases 4E-4G:** guarded Vite middleware serves external authoritative
  GFS data in development, production builds materialize only the selected run, and the
  superseded in-repository rollback copy has been retired.
- Retention remains rolling current plus previous unless a later operational Weather
  policy explicitly changes it.
