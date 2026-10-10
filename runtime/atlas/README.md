# Local Atlas runtime: qualified evidence, queries and lifecycle

The runtime opens accepted seven-component publications and compatible eight-component registration,
nine-component derivation and ten-component registration/derivation
lifecycle extension, plus optional retained Exe water registration. Canonical qualified files and the filesystem publication root
remain authoritative; SQLite is a disposable candidate catalogue. It can now execute
one accepted native Riffelhorn slope method and its planar-area summary, inspect scoped
invalidation, stage/validate/publish immutable generations, and query their history.

The [Exe integration](../../docs/research/atlas-local-exe.md) extends those same
registration and retrieval interfaces; it is not a water service or simulation.

The [first read slice](../../docs/research/atlas-local-runtime.md) remains authoritative
for its original boundary. The [lifecycle report](../../docs/research/atlas-local-lifecycle.md)
and [frozen design](lifecycle-plan.json) describe this extension. No production application,
new physical observations or general workflow engine is involved.

## Setup and paths

Use Node **24.11 or later** with native TypeScript stripping, the repository's
installed npm dependencies, and the existing public-data GIS Python environment
(Python 3.12, sqlite3, numpy, shapely, rasterio, pyproj). `npm ci` sets up the Node
dependencies; it does not acquire geographical evidence. The retained public
inputs and prepared fixture must already be present. No external drive or network
service is required for this slice.

From the repository, PowerShell:

```powershell
$atlasData = (Resolve-Path ../meridian-data).Path
$atlasPython = Join-Path $atlasData 'earth-lab/.venv/Scripts/python.exe'
# This accepted research receipt locates an existing publication; it is not authority.
$atlasReceipt = Get-Content docs/research/atlas-multi-region-results.json -Raw | ConvertFrom-Json
$atlasPublication = $atlasReceipt.store
$atlasGeneration = $atlasReceipt.history[0]
# Choose a disposable directory outside the repository, public data and publication.
$atlasCatalogue = Join-Path $env:LOCALAPPDATA 'Meridian/atlas-local-catalogue'
$atlasFlags = @('--data-root', $atlasData, '--publication-root', $atlasPublication,
  '--catalogue', $atlasCatalogue, '--python', $atlasPython, '--generation', $atlasGeneration)
node runtime/atlas/cli.ts validate @atlasFlags --json
node runtime/atlas/cli.ts catalogue build @atlasFlags --json
node runtime/atlas/cli.ts catalogue verify @atlasFlags --json
node runtime/atlas/cli.ts query @atlasFlags --query '{"region":"riffelhorn","feature":"glaciers:683"}' --json
```

The receipt's locator is specific to its retained research installation. On another
machine, set `$atlasPublication` to the relocated canonical publication directory
and `$atlasData` to its public-data root. Logical identities do not contain drive
letters. Missing volumes fail explicitly. For the current generation, omit
`--generation`: it resolves once at open. For another historical generation, set
an exact committed SHA and build a catalogue for that pin. There is no fallback.

Every new CLI process fully validates authority before using the catalogue. A
long-lived library context amortizes opening but still rechecks canonical
membership/component identities and catalogue contents per query.

## Queries and returned qualifications

```powershell
node runtime/atlas/cli.ts query @atlasFlags --query '{"region":"riffelhorn","point":[2625000,1092000],"crs":"EPSG:2056"}' --json
node runtime/atlas/cli.ts query @atlasFlags --query '{"region":"riffelhorn","area":[2624975,1091975,2625025,1092025],"crs":"EPSG:2056","time":{"role":"evidence-epoch","start":2021,"end":2021}}' --json
node runtime/atlas/cli.ts query @atlasFlags --query '{"region":"riffelhorn","time":{"role":"evidence-epoch","unknown":true}}' --json
node runtime/atlas/cli.ts query @atlasFlags --query '{"region":"tryfan"}' --json
```

Predicates are conjunctions: optional exact `identity`, native `feature`, `region`,
`families`, `representation`, `product`, one `point` or `area`, and `time`.
Spatial queries require an explicit region and CRS: Riffelhorn EPSG:2056,
Tryfan EPSG:27700, or EPSG:4326/OGC:CRS84 for either. No arbitrary SQL or geometry
expression is exposed. Native raster affine support and vector exact predicates
run after bounds candidate selection. No cross-source fusion occurs.

Time is an inclusive **calendar-year qualifier**, with role `evidence-epoch` or
`product-reference`, or an explicit `unknown:true` selection. It is not validity
throughout an interval. Unknown time does not match every dated query. Exact
knowledge-time cutoffs and the later thirteen-component temporal publication
format are not supported in this adapter; historical generation pins preserve
the actual accepted administrative knowledge state. Unsupported predicates fail.

The 44 Riffelhorn records return complete accepted native envelopes with source,
prepared artifacts, geometry/support, scientific limitations, temporal roles,
uncertainty and source-specific rights. The five Tryfan records are canonical
**source-product metadata descriptors**, not new feature identities or physical
measurements at a point. Their registered-core spatial eligibility is distinct
from native source coverage; their original metadata remains attached. Identity
is the existing product SHA. For all results, the wrapper exposes publication
generation, exact component identity, evidence, support, temporal qualification,
provenance and rights. No match means no matching retained evidence, not physical
absence. Human output lists identities; `--json` exposes the full qualified body.

## TypeScript library

```typescript
import { openAtlas } from './runtime/atlas/index.ts'
const atlas = await openAtlas({ dataRoot, publicationRoot, catalogueRoot, python,
  generation: committedGeneration })
try {
  await atlas.buildCatalogue() // explicit; never silently repair canonical files
  const answer = await atlas.query({ region: 'riffelhorn', feature: 'glaciers:683' })
  console.log(answer.generation, answer.results[0].provenance)
  await atlas.verifyCatalogue()
} finally { await atlas.close() }
```

`AtlasContext` owns a bounded Python child process. It reuses accepted geometry,
CRS, raster and preparation verification functions; Python SQLite is the existing
embedded database interface. It executes no new scientific transformation. Close
the context and serialize build operations; this is a local single-writer slice.
`scanReference` is an explicit diagnostic oracle, never an automatic fallback.

## Recovery and disposable state

Layout: `staging/<uuid>` → completed `epochs/<uuid>/{index.sqlite,seal.json}` →
replace advisory `current.json` last. The seal binds schema, generation, canonical
closure fingerprint and database bytes. Build verification checks the complete
record/temporal selector population and conservative bounds against canonical
records. Failed builds leave the previous pointer and catalogue intact. The
read/query/catalogue commands never write the filesystem **publication** root;
only the explicit owned-world publication commands described below may advance it. No cross-filesystem transaction
or power-loss durability guarantee is claimed.

Missing, stale, incompatible or corrupt catalogues produce a nonzero CLI exit and
an actionable JSON diagnostic on stderr. Rebuild with the same explicit pin.
To demonstrate deletion and recovery, delete only the configured disposable
catalogue directory after checking its resolved path, then repeat `catalogue
build`, `catalogue verify` and the same query. Results and canonical history stay
identical. Never delete the canonical data or publication directory.

Each rebuild retains a completed disposable epoch; this slice has no cache garbage
collector. Unreferenced staging/epochs may be removed by deleting the disposable
directory while contexts are closed. Old pinned contexts continue using their
selected epoch until it is removed, at which point they fail explicitly.

Full validation checks present bytes at open. It is not proof of physical truth,
upstream authenticity, perpetual availability or continuous tamper-resistant
custody. Canonical and native files are assumed immutable during a live session.
Canonical object hashes are rechecked per query; opening anew rehashes payloads.
Metadata and catalogue audits remain population-wide in this bounded slice.

## Verification and measurements

```powershell
node node_modules/typescript/bin/tsc -p runtime/atlas/tsconfig.json
node --test runtime/atlas/test-runtime.mjs
```

`measure.mjs` and `run-checks.py` are repository-local assessment tooling, not
runtime prerequisites. Their outputs use the external Codex assessment directory;
operational CLI/library paths are entirely explicit. The original read adapter covers three accepted generations, seven components
and 49 real selectors; the lifecycle extension adds nine-component generations
and 32 finite derived quantities. See the
report for measured costs and limitations before extrapolating.


## Deterministic derivation and scoped lifecycle

Use a **new separate publication directory** for canonical runtime outputs. Neither
accepted research stores nor retained meridian-data inputs may be writer destinations.
`world init` fully validates and forks the selected existing publication (current by
default, exact historical pin with `--generation`). Source history remains unchanged.
It copies the small canonical store and portrayal assets; the 171 MB verified public
inputs remain externally referenced. A runtime ownership marker distinguishes the fork.
A missing marker is an error, not an instruction to adopt an accepted store.

The library exports `createWorld`, `stageDerivation`, `inspectLifecycle`,
`validateStage`, `publishStage`, `recoverWorld`, and `fullDerivationReference` from
[index.ts](index.ts). `openAtlas(config).derived({identity?, property?})` returns the
finite canonical scalar results, exact revisions, source/preparation/rights/support/time
qualifications, dependencies and pinned generation. Derived lookup currently performs
bounded canonical checks over 32 outputs; it is separate from the 49 native SQLite
selectors. Unknown physical observation time stays unknown. No arbitrary temporal
inference or physical-change claim is supported.

`stageDerivation(config, change)` accepts only declared per-probe stride1/2 parameters,
an exact source administrative qualification notice, and a labelled unrelated Tryfan
registration notice toggle. A notice has `key`, `bounds` and `text`: bounded support
matches exact consumed cell footprints; `bounds: null` explicitly means the whole
source, not unknown support. Notices do not change source payload bytes. New observations
and general evidence registration are outside this slice. Repeating a notice is a no-op.
The worker version1 DTO uses explicit verified data/preparation roots and returns native
cells plus an independent NumPy arithmetic oracle and interpreter/library versions.
Immutable `executions/<sha>.json` records retain those actual versions, sampler/oracle
source identities, Node/method identity and exact output references. They are processing
audit records, not reusable validation evidence; full validation still recomputes current
quantities. Historical execution versions remain recorded without requiring the currently
installed interpreter to have the same version string.

Full validation is mandatory. It rechecks all accepted payloads and all 32 outputs with
fresh native samples, even when processing reuses them. Processing saves selected work;
this slice makes no end-to-end speedup promise. `fullDerivationReference` performs a
clean all-probe comparison without writing output or switching a root.

### CLI commands

All commands use the existing `--data-root`, `--publication-root`, `--catalogue`,
`--python` flags and optional `--json`. Writer commands target the owned fork.

```text
node runtime/atlas/cli.ts world init ... --source-publication EXISTING_STORE
node runtime/atlas/cli.ts derive stage ...
node runtime/atlas/cli.ts derive inspect ... --change CHANGE_JSON
node runtime/atlas/cli.ts derive stage ... --change CHANGE_JSON
node runtime/atlas/cli.ts stage validate ... --stage STAGED_SHA256
node runtime/atlas/cli.ts stage publish ... --stage STAGED_SHA256
node runtime/atlas/cli.ts derived ... --generation COMMITTED_SHA256
node runtime/atlas/cli.ts catalogue build ... --generation COMMITTED_SHA256
node runtime/atlas/cli.ts query ... --generation COMMITTED_SHA256 --query QUERY_JSON
node runtime/atlas/cli.ts world recover ...
```

`derive stage` returns the proposed generation, exact affected closure, immutable output
references, reuse and processing counters. It never switches the root. Use its generation
with `stage validate` and `stage publish`. Publication repeats full validation under a
local writer lock, rejects a changed predecessor, installs committed membership, and
atomically replaces `current.json` last. A staged SHA is not queryable as published.
No-op stages return the unchanged current generation; they need no new publication.
After a real publication the old catalogue is explicitly stale. Rebuild for each pin.
Historical contexts never follow the moving current generation.

Recovery only removes a lock whose process is demonstrably dead; it will not steal a
live or ambiguous lock. Incomplete initialization directories, temporary objects and
unreferenced staging objects remain harmless for inspection/retry. No garbage collector,
backup policy, power-loss durability, hostile mutation or multi-writer guarantee is claimed.
Immutable object installation uses same-volume atomic no-overwrite links after file sync;
publication replacement relies on a local filesystem supporting these operations. A missing
or disconnected volume fails explicitly. An external disk is not a backup.

### Repeatable complete example

Create an external configuration file with five paths. Relative paths resolve against
that file's directory, making the example independent of the invocation directory:

```json
{
  "dataRoot": "PATH_TO_EXISTING_MERIDIAN_DATA",
  "publicationRoot": "NEW_EMPTY_RUNTIME_WORLD_PATH",
  "catalogueRoot": "SEPARATE_DISPOSABLE_CACHE_PATH",
  "python": "PATH_TO_EXISTING_GIS_PYTHON",
  "sourcePublication": "EXISTING_ACCEPTED_PUBLICATION_STORE_PATH"
}
```

The selected existing store location is recorded in
[the first runtime baseline](../../docs/research/atlas-local-runtime-baseline.json).
It is a locator, not scientific identity. Invoke:

```text
node runtime/atlas/example-lifecycle.mjs PATH_TO_CONFIG.json
```

The [example](example-lifecycle.mjs) invokes public CLI commands in fresh processes:
validate/fork, initial derivation, stage validation/publication, inspect a labelled local
knowledge correction, recompute eight outputs/reuse24, publish, build the disposable
catalogue, query native evidence, and query old/new derived pins. It prints complete
machine-readable qualifications. Use a new destination for each example run.

For focused integration checks use `node --test runtime/atlas/test-lifecycle.mjs`.
For the inherited regression set plus lifecycle checks use the existing GIS Python to
run `runtime/atlas/check-lifecycle.py`. Tests and measurements retain payload/cache worlds
outside this repository. [The task selected at that checkpoint](lifecycle-next-task.json)
is completed by the registration/update workflow below.


## Qualified evidence registration and regional updates

[The registration report](../../docs/research/atlas-local-registration.md) documents
this bounded native adapter. Initial onboarding uses the accepted Tryfan canonical
reference and verified Riffelhorn preparation files directly, without copying a
multi-region research publication. Source/prepared payloads remain in the configured
public data root; only canonical metadata and two existing portrayal assets are copied.
Use a new world outside public inputs, the repository and the disposable catalogue.

Library exports from `index.ts`: `inspectEvidence(config, inputs?)`,
`registerEvidence(config, inputs, request)`, `planEvidenceUpdate(config, request)` and
`stageEvidenceUpdate(config, request)`. Existing `validateStage` and `publishStage`
accept the proposed generation. `RegistrationInputs` contains explicit `tryfanRoot`
and `preparedRoot`; `RegistrationRequest` is a versioned typed DTO. Native and derived
answers now expose canonical registration knowledge separately from observation time.

### Inspect, register and revise

Use the existing four runtime flags for every command. Initial `evidence inspect`
also takes `--tryfan-root` and `--prepared-root` and emits **verified native templates**.
Write the `templates.riffelhorn` object to an external request JSON file. Preserve its
native identity/fields exactly. Register with the same two input flags and `--request`.

```text
node runtime/atlas/cli.ts evidence inspect ... --tryfan-root PATH --prepared-root PATH
node runtime/atlas/cli.ts evidence register ... --tryfan-root PATH --prepared-root PATH --request REQUEST.json
node runtime/atlas/cli.ts derive stage ...
node runtime/atlas/cli.ts stage validate ... --stage STAGED_SHA
node runtime/atlas/cli.ts stage publish ... --stage STAGED_SHA
node runtime/atlas/cli.ts evidence inspect ...
node runtime/atlas/cli.ts update plan ... --request REVISION.json
node runtime/atlas/cli.ts evidence revise ... --request REVISION.json
node runtime/atlas/cli.ts update validate ... --stage STAGED_SHA
node runtime/atlas/cli.ts update publish ... --stage STAGED_SHA
```

Request fields:

- `schema`: `atlas-runtime-registration-request/v1`.
- `operation`: `register`, `knowledge`, or `source-qualification`.
- `region`: `riffelhorn` or `tryfan`; initial world registration uses Riffelhorn.
- `expectedGeneration`: exact current SHA, or `null` for a new world.
- `expectedRevision`: exact current region revision from `evidence inspect`, or `null`
  on first registration. Repeated identity-based `register` may use `null`; it cannot
  overwrite knowledge or scientific metadata. A non-null stale revision is rejected.
- `native`: the complete verified template, including source/preparation/support/time/
  rights/uncertainty. Scientific overrides are rejected, never silently repaired.
- `explanation`: nonempty bounded accountability text.
- `sourceNotice`: required only for `source-qualification`; exact DTM source key,
  native EPSG:2056 `bounds` within that source or explicit whole-source `null`, and text.

`knowledge` appends an informational review and requires no numerical recomputation.
`source-qualification` describes a controlled qualification of existing retained source
bytes, not a new observation or product replacement. It requalifies only claims using
those exact native cell footprints. Numeric values/samples/method/support are reused;
immutable audit records identify them. Full publication validation independently samples
current native bytes and recomputes all supported quantities before root advancement.
An unused source qualification is retained without forcing computation.

The runtime records a separate knowledge acceptance clock and immutable direct
supersession. It never assigns that timestamp to physical observations. New observation,
source replacement, method replacement, licence/CRS/time overrides and unknown families
are unsupported by this adapter. A stale generation/revision requires explicit inspection
and restaging. Plans do not write; revisions stage only. No invalid/incomplete state is
visible until full validation and the existing filesystem-root commit protocol succeeds.
Historical pins remain unchanged, and the native SQLite catalogue must be rebuilt for a
new pin. No database row becomes evidence or publication authority.

### Complete CLI example

Save an external six-path configuration. Relative paths resolve against its directory.
Use a new destination for each run:

```json
{
  "dataRoot": "PATH_TO_MERIDIAN_DATA",
  "publicationRoot": "NEW_RUNTIME_WORLD_PATH",
  "catalogueRoot": "SEPARATE_DISPOSABLE_CACHE_PATH",
  "python": "PATH_TO_GIS_PYTHON",
  "tryfanRoot": "PATH_TO_ACCEPTED_TRYFAN_REFERENCE",
  "preparedRoot": "PATH_TO_VERIFIED_RIFFELHORN_PREPARATION_REVISION"
}
```

The existing relative input locations under the public data root are
`experiments/atlas/tryfan-regional-pilot-v1` and
`derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1/357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb`.

```text
node runtime/atlas/example-registration.mjs PATH_TO_CONFIG.json
node --test runtime/atlas/test-registration.mjs
```

[The example](example-registration.mjs) executes actual CLI inspection/registration,
derivation, local eight-output qualification update, validation/publication, catalogue
build and old/new queries in fresh processes. It creates external request files and
prints complete qualified results. Use the existing GIS Python to run
`runtime/atlas/check-registration.py` for inherited protections and all tests.
Source inspection has real integrity/reconstruction cost; a query or registration does
not establish physical truth or permanent custody. Full registration-history validation
follows explicit supersession records and reports its cost; normal publication membership
still uses zero ancestry traversal. No history deletion, GC, backups, remote service or
power-loss guarantee is implemented. [Exactly one next task](registration-next-task.json)
is selected, not begun.

## Unified qualified source and derived retrieval

Use `AtlasContext.retrieve` or CLI `retrieve` for one pinned answer containing native
source/prepared records and qualified derived results. The SQLite catalogue contains
selectors only. Canonical files determine identities, values, scientific qualifications,
dependencies and publication truth. Opening still performs full authoritative validation,
including native integrity and supported numerical replay. No SQL row advances a root.

```ts
import { openAtlas, type EvidenceQuery } from './runtime/atlas/index.ts'

const atlas = await openAtlas({
  dataRoot, publicationRoot, catalogueRoot, python,
  generation, // optional explicit committed SHA; omission pins current at open
})
try {
  await atlas.buildCatalogue({ qualified: true })
  const query: EvidenceQuery = {
    region: 'riffelhorn', point: [2624350.25, 1091350.25], crs: 'EPSG:2056',
  }
  const answer = await atlas.retrieve(query)
  for (const result of answer.results) {
    console.log(answer.generation, result.evidenceClass, result.identity, result.revision)
    console.log(answer.documents[result.qualificationRef])
    console.log(answer.documents[result.provenanceRef])
  }
} finally { await atlas.close() }
```

Run TypeScript using the repository's supported Node version; the Python path is the
existing GIS environment described above. Keep catalogue paths outside both the code
repository and canonical/publication roots. Every command below also requires
`--data-root DATA --publication-root WORLD --catalogue CACHE --python GIS_PYTHON`.
Use `--generation SHA` to select a committed historical generation and `--json` for
the complete structured answer. These commands never change canonical evidence:

```text
node runtime/atlas/cli.ts validate ... --generation SHA --json
node runtime/atlas/cli.ts catalogue build ... --qualified --generation SHA --json
node runtime/atlas/cli.ts catalogue verify ... --qualified --generation SHA --json
node runtime/atlas/cli.ts retrieve ... --generation SHA --query '{}' --json
node runtime/atlas/cli.ts retrieve ... --query '{"evidenceClass":"source"}' --json
node runtime/atlas/cli.ts retrieve ... --query '{"evidenceClass":"derived"}' --json
node runtime/atlas/cli.ts retrieve ... --query '{"identity":"dtm-cluster-0-0|slope"}' --json
node runtime/atlas/cli.ts retrieve ... --query '{"region":"riffelhorn","feature":"glaciers:683"}' --json
node runtime/atlas/cli.ts retrieve ... --query '{"relatedTo":{"identity":"dtm-cluster-0-0|area-ratio","direction":"inputs","depth":"transitive"}}' --json
```

In PowerShell, pass the JSON as one single-quoted argument. `...` denotes the four
explicit configuration flags, not an executable argument. To run a complete example
without constructing those command lines, save an external configuration:

```json
{
  "dataRoot": "PATH_TO_MERIDIAN_DATA",
  "publicationRoot": "EXISTING_OWNED_RUNTIME_WORLD",
  "catalogueRoot": "SEPARATE_DISPOSABLE_CACHE",
  "python": "PATH_TO_GIS_PYTHON",
  "generation": "EXACT_COMMITTED_GENERATION_SHA",
  "historicalGeneration": "OPTIONAL_OLDER_COMMITTED_SHA"
}
```

Paths resolve against that configuration file. Omit either optional selector field
rather than supplying a placeholder. Use a world produced by the registration example
above, or an existing retained runtime publication. Generation identities are in its
authoritative `current.json` and committed membership; the example does not invent or
register evidence.

```text
node runtime/atlas/example-retrieval.mjs CONFIG.json
node --test runtime/atlas/test-retrieval.mjs
```

The [example](example-retrieval.mjs) validates, builds/verifies the qualified catalogue,
queries both classes, inspects a derived result, follows its exact lineage, queries a
historical pin if supplied, and restores the selected pin's catalogue. Each CLI call
opens a fresh fully validated process. `check-retrieval.py`, run with the GIS Python,
executes inherited and new tests, types, lint, build and that example. Measurements
use [measure-retrieval.mjs](measure-retrieval.mjs); they write disposable caches outside
Git and compact raw receipts, never source payloads.

### Supported predicates and honest limitations

- Exact `identity`; exact SHA `revision`; `evidenceClass: source | derived`; `region`;
  `families`; `representation`; exact `product` (native source identity or derived
  method revision). Derived families are `terrain-slope` and `planar-area-ratio`;
  representation is `local-scalar`. Source families/representations remain native.
- Native feature identities only. Scalars do not acquire feature IDs by proximity.
- Spatial `point` or `area: [minX,minY,maxX,maxY]` requires a region and a supported
  explicit CRS. Native source geometries/raster support use accepted exact predicates.
  A scalar's default `spatialSupport: location` selects its exact anchor, with
  half-open area upper bounds. It never claims the scalar is valid everywhere in a
  bounding box. Point equality is exact after the declared support transform; no
  fuzzy nearest-location tolerance is implied. Derived-only `spatialSupport: consumed` selects actual consumed
  0.5m native cell footprints; coarse RTree bounds shortlist and exact filtering
  excludes gaps. This describes input use, not continuous physical applicability.
- `time: {role: evidence-epoch | product-reference, start: YEAR, end: YEAR}` uses
  closed calendar-year native qualification. Alternatively `{role, unknown:true}`
  selects explicitly unknown qualification. Current scalar observation/product-reference
  years are unknown; method identity/execution time does not supply them. No open-ended
  interval, arbitrary precision, validity-throughout or physical-change inference.
- `knowledge: {revision: SHA}` selects the active regional registration revision
  **within this pin**. `{start: UTC_MILLISECOND, end: UTC_MILLISECOND}` selects its
  closed acceptance-clock interval, e.g. `2026-10-09T12:00:00.000Z`.
  `{unknown:true}` selects older contexts lacking an accepted registration clock.
  Knowledge filters do not switch generations or reconstruct an earlier knowledge
  state inside a later publication. Select the earlier `generation` explicitly.
- `relatedTo: {identity, direction: inputs | dependents, depth: direct | transitive}`
  follows authoritative evidence adjacency. Source→slope is mediated by the exact
  qualified-use identity (`via`, recording both underlying dependency edges);
  slope→area-ratio consumes the exact slope revision. Other predicates filter the
  reachable evidence. Unknown relationship seeds fail explicitly; ordinary absent
  identity queries return a qualified gap. No location/property-based inferred lineage.

The response is `atlas-qualified-retrieval/v1`: stable keyed records, exact generation
and component membership, relationship records, and shared `documents` addressed by
response content fingerprints. These document fingerprints are references within the
answer, not new canonical artifacts or physical observation identities. Source `revision`
selects the accepted/prepared regional source representation; original source fingerprints
remain in provenance/shared native metadata. Derived `revision` is its canonical content
identity. The distinct `knowledgeRef` exposes immutable acceptance/supersession lineage.
Qualifications, CRS/datums, source/preparation lineage, method/parameters/execution,
uncertainty and rights remain available through those references. Shared `regions` native
metadata provides retained source/preparation time fields where actually documented.

`relationships` includes incident lineage for returned evidence and the traversed path.
`traversal.relationshipRefs` distinguishes the path actually selected; incident neighbour
edges need not have both endpoints in the filtered result. `EvidenceQuery`,
`EvidenceAnswer`, `EvidenceRecord` and `EvidenceRelationship` are exported from `index.ts`.
`scanEvidence` is the diagnostic authoritative full-scan reference, not a silent fallback.
All results are evidence-qualified; no matching record is never proof of physical absence.

### Catalogue recovery and compatibility

`--qualified` / `{qualified:true}` builds schema2 of the **same** catalogue/epoch/worker,
extending native selectors with derived, active knowledge and dependency rows. It stores
no raster, scalar numerical payload or authoritative document. Default schema1 preserves
existing `query` and lifecycle callers; those native queries require schema1, while unified
`retrieve` requires schema2. Rebuild explicitly for the intended interface. Incompatible,
missing, wrong-pin or corrupt catalogues fail with actionable diagnostics. A failed build
does not replace a valid pointer. Delete the disposable cache and rebuild for the same
pin to reproduce identical answers; no accepted source/history is repaired or rewritten.

Queries still audit canonical metadata, registration supersession, derived freshness and
catalogue selectors. That work is population-wide in this bounded implementation, and
native extra selector checks visit49 records. The index narrows exact geometry/results;
it does not establish constant-cost lookup or avoid full validation on open. There is no
production/global-scale claim, remote service, multiple-writer or power-loss guarantee.
Tryfan DTM/unknown datum, Swiss LN02 DTM, independent EGM2008 DSM, classifications and
dated features remain separate. See the [retrieval report](../../docs/research/atlas-local-retrieval.md)
and [exactly one next unbegun task](retrieval-next-task.json).

## Retained Exe water evidence through the shared runtime

Prerequisites: the accepted public water-check-v1 directory, existing retained
Tryfan/Riffelhorn runtime publication, Node/Python setup above and an empty owned
world destination. No acquisition/preparation campaign is performed. The adapter
admits WFD GB510804505600, RFO31383/group4124, March/September2024 P1 containing-cell
assignments and centre-count summaries, plus their two monthly crop products.
There are six source selectors and two derived summaries, not eight independent
physical observations. Other retained PHI/planning products are verified for
source accountability but are not admitted into this finite query population.

```powershell
# Set explicit relocated paths. The receipt is a locator, never publication authority.
$atlasSource = (Get-Content docs/research/atlas-local-exe-baseline.json -Raw | ConvertFrom-Json).selectedWorld
$atlasWorld = Join-Path $env:LOCALAPPDATA 'Meridian/atlas-exe-owned-world'
$atlasCache = Join-Path $env:LOCALAPPDATA 'Meridian/atlas-exe-disposable-catalogue'
$atlasFlags = @('--data-root', $atlasData, '--publication-root', $atlasWorld,
  '--catalogue', $atlasCache, '--python', $atlasPython)
node runtime/atlas/cli.ts world init @atlasFlags --source-publication $atlasSource --json
$atlasBefore = (node runtime/atlas/cli.ts validate @atlasFlags --json | ConvertFrom-Json).generation
$atlasInspect = node runtime/atlas/cli.ts evidence inspect @atlasFlags --family exe-water --json | ConvertFrom-Json
$atlasRequest = Join-Path $env:LOCALAPPDATA 'Meridian/exe-registration-request.json'
[IO.File]::WriteAllText($atlasRequest, ($atlasInspect.templates.exe | ConvertTo-Json -Depth 100), [Text.UTF8Encoding]::new($false))
node runtime/atlas/cli.ts update plan @atlasFlags --request $atlasRequest --json
$atlasStage = node runtime/atlas/cli.ts evidence register @atlasFlags --family exe-water --request $atlasRequest --json | ConvertFrom-Json
node runtime/atlas/cli.ts update validate @atlasFlags --stage $atlasStage.generation --json
node runtime/atlas/cli.ts update publish @atlasFlags --stage $atlasStage.generation --json
node runtime/atlas/cli.ts catalogue build @atlasFlags --qualified --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"region":"exe"}' --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"identity":"exe:wfd"}' --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"region":"exe","feature":"rfo:31383"}' --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"region":"exe","area":[296600,86550,296800,86750],"crs":"EPSG:27700","waterTime":{"role":"observation","start":"2024-03-01","end":"2024-03-31"}}' --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"relatedTo":{"identity":"exe:2024-03:support","direction":"inputs","depth":"direct"}}' --json
# Historical pin needs its own rebuilt catalogue; no generation fallback occurs.
node runtime/atlas/cli.ts catalogue build @atlasFlags --qualified --generation $atlasBefore --json
node runtime/atlas/cli.ts retrieve @atlasFlags --generation $atlasBefore --query '{"region":"exe"}' --json
```

For repeat registration, inspect a fresh template. Identical register is no-op;
do not validate/publish a no-op stage. For a knowledge-only revision, inspect a
fresh template and change only operation to `knowledge` and explanation. Use
`evidence revise`, then existing update validate/publish. The source/time/support
body cannot be overridden. Knowledge acceptance changes, physical observations
and source content do not. Missing/corrupt/stale catalogues require explicit
rebuild. Deleting the catalogue pointer or SQLite files does not affect authority.

Library: `inspectEvidence(config, {family:'exe-water'})` returns a verified
request; `registerEvidence(config, {family:'exe-water'}, request)` stages it.
`planEvidenceUpdate`, `stageEvidenceUpdate`, `validateStage`, `publishStage` and
`openAtlas(config).retrieve(query)` retain their existing roles. A current context
pins at open. `config.generation` selects exact history, including pre-Exe states.
The complete CLI-only example is `node runtime/atlas/example-exe.mjs CONFIG.json`.
Its config has dataRoot, publicationRoot (new destination), catalogueRoot, python
and sourcePublication. It demonstrates registration, old/new queries, an explicitly
administrative knowledge revision, restart and deleted-pointer rebuilding.

Qualified predicates add region `exe`, families `water-reference`, `water-event`,
`water-monthly` and representation `native-cell-summary`. The optional `waterTime`
profile applies to admitted Exe records: observation/event use inclusive ISO day
interval overlap; reference uses an exact calendar-year qualifier. `unknown:true`
means the requested role is unavailable, not all-time applicability. Combined
predicates are conjunctions, including knowledge. Existing year-only `time` stays
separate and compatible; knowledge selects active immutable ledger revision/time
in a pinned generation. WFD classification2019 is not observation time; RFO
February4-5,2014 is a published event interval, not local inundation seconds;
monthly bins are not exact Landsat exposures or continuous validity.

Spatial predicates select existing evidence support rather than recomputing a
new water measurement. EPSG:27700 or4326/CRS84 queries use original polygons,
native raster-cell rectangles and exact P1 centre populations after coarse index
selection. Vector/cell point support uses covers (closed geometric boundary);
area selection requires positive intersection. Summary area queries require an
actual selected centre strictly within the area; a point query must match an
actual centre. The study upper bounds are excluded for point eligibility. Native
geometries can extend beyond the10.5km² study without extending proof eligibility.
A smaller query returns the unchanged P1 summary when its support intersects;
it does not turn the77-cell composition into a new subarea summary.

Every returned record exposes native geometry/CRS, legacy year projections plus
native observation/event/reference qualifiers, retained acquisition/source dates,
unknown preparation completion time, immutable knowledge and publication identity,
source/product/retained/derived identities, accepted method/parameters and rights.
Two explicit summary-to-monthly-product dependencies are available. Single-cell
observations are not fabricated as inputs to77-cell summaries. WFD/event records
remain independent evidence, with no invented cross-source lineage.

March P1 counts0/0/77 and September76/1/0 refer respectively to code0 no observation,
code1 non-detection and code2 detection. Point codes2 and0 remain distinct from
summary counts. No-result means no matching evidence, never dry/physical absence.
Current water, flood level, discharge, tide and physical-change predicates are
unsupported. Keep EA/OS and JRC/Google/Pekel attribution and retained source notices;
local research admission is not blanket redistribution/service clearance.

Full opening and candidate validation verify current retained bytes and independently
rebuild accepted Exe claims/supports. Later queries retain the accepted immutable
local-custody assumption, with canonical closure/metadata and catalogue audits;
they are not a fresh full-payload hash sweep. The existing session-owned Python
worker performs GIS/SQLite work; no daemon, remote API or new database authority.

## Exe habitat inventory and planning references

The [integration report](../../docs/research/atlas-local-references.md) describes
52 additional source-native claims: 15 habitat components on 13 original PHI
features and 37 planning-zone features intersecting the six original 200m Exe probes.
This is selected coverage, not the complete 280/546 source feature population.
Original polygon support is retained. Two combined habitat features yield four
component claims without inventing fractions, dominant classes or new observations.

Use an owned copy of the existing retained Exe water world; accepted source worlds
remain read-only. Paths below use the setup variables defined above.

```powershell
$atlasSource = (Get-Content docs/research/atlas-local-references-baseline.json -Raw | ConvertFrom-Json).selectedWorld
$atlasWorld = Join-Path $env:LOCALAPPDATA 'Meridian/atlas-references-owned-world'
$atlasCache = Join-Path $env:LOCALAPPDATA 'Meridian/atlas-references-catalogue'
$atlasFlags = @('--data-root', $atlasData, '--publication-root', $atlasWorld,
  '--catalogue', $atlasCache, '--python', $atlasPython)
node runtime/atlas/cli.ts world init @atlasFlags --source-publication $atlasSource --json
$atlasBefore = (node runtime/atlas/cli.ts validate @atlasFlags --json | ConvertFrom-Json).generation
$atlasInspection = node runtime/atlas/cli.ts evidence inspect @atlasFlags --family exe-references --json | ConvertFrom-Json
$atlasRequest = Join-Path $env:LOCALAPPDATA 'Meridian/references-request.json'
[IO.File]::WriteAllText($atlasRequest, ($atlasInspection.templates.exeReferences | ConvertTo-Json -Depth 100), [Text.UTF8Encoding]::new($false))
node runtime/atlas/cli.ts update plan @atlasFlags --request $atlasRequest --json
$atlasStage = node runtime/atlas/cli.ts evidence register @atlasFlags --family exe-references --request $atlasRequest --json | ConvertFrom-Json
node runtime/atlas/cli.ts update validate @atlasFlags --stage $atlasStage.generation --json
node runtime/atlas/cli.ts update publish @atlasFlags --stage $atlasStage.generation --json
node runtime/atlas/cli.ts catalogue build @atlasFlags --qualified --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"families":["priority-habitat","planning-flood-zone","water-reference"]}' --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"nativeClassification":"SALTM","referenceTime":{"role":"survey","unknown":true}}' --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"families":["planning-flood-zone"],"nativeClassification":"FZ2","referenceTime":{"role":"effective","unknown":true}}' --json
node runtime/atlas/cli.ts retrieve @atlasFlags --query '{"region":"exe","area":[296600,86550,296800,86750],"crs":"EPSG:27700"}' --json
node runtime/atlas/cli.ts catalogue build @atlasFlags --qualified --generation $atlasBefore --json
node runtime/atlas/cli.ts retrieve @atlasFlags --generation $atlasBefore --query '{}' --json
```

Identical repeated registration is no-op; it has no stage to publish. Inspect a
fresh template before updates. For administrative knowledge revision, preserve
`scope:"exeReferences"`, region `exe` and native body, change only operation to
`knowledge` and explanation, then evidence revise/update validate/publish. This
supersedes reference knowledge only; the existing water knowledge is unchanged.
The complete CLI-only example is `node runtime/atlas/example-references.mjs CONFIG.json`,
with dataRoot, python, new publicationRoot, catalogueRoot and sourcePublication.

Library: existing `inspectEvidence(config,{family:'exe-references'})`,
`registerEvidence`, `planEvidenceUpdate`, `stageEvidenceUpdate`, `validateStage`,
`publishStage`, `openAtlas(config).retrieve()` and `scanEvidence()` are used.
Requests add an optional finite registration scope, not a new geography. Returned
reference records have region `exe` and registrationScope `exeReferences`; their
component, knowledge and native document refs identify that independent population.
`answer.regions.exeReferences` is a registration-scope context, not a fourth region.
Old records and contracts retain their prior shape. Schema 2 catalogue remains
disposable and exact-generation-bound; no canonical payload is stored in SQLite.

`nativeClassification` selects one admitted source code (CFPGM,LFENS,MUDFL,RBEDS,
SALTM,FZ2,FZ3), with exact source-specific meaning in the returned claim. The finite
`referenceTime` profile accepts survey/effective/publication ISO-day intervals,
contributor calendar-year intervals, or explicit unknown. Survey and contributor
apply to habitat; effective applies to planning; publication applies to both.
Unknown includes an unavailable applicable qualifier, never universal time.
Not-applicable roles are excluded. Survey/effective/publication dates are unknown
in this accepted claim projection. Contributor years are descriptive vintages,
not survey/validity dates. Native fields/retained notices carry snapshot/catalogue
dates separately; Atlas acceptance and publication are different clocks.

Original exact geometry is filtered after spatial candidates. The spatial query
selects a source record, not a claim of its current state or an analysis of planning
law. A no-result gap never proves no species, habitat, water or restriction. PHI
does not establish species presence or current ecological condition; Flood FZ2/FZ3
retains annual-probability, ignored-defence and native mixed Origin conventions.
It is not a current flood footprint or statutory restriction. Rights/attribution
and limitations remain attached; local research is not unrestricted public reuse.

The runtime is a Node/Python library/CLI, not browser code. First-prototype readiness
means a narrow application boundary can now be planned; it does not authorize private
access, a remote service or changes to production Atlas/Weather/Traverse. See the
[exactly one unbegun next task](references-next-task.json).


## Portable Atlas read reference — 9 October 2026

[Reference contract and fixtures established](../../docs/research/atlas-portable-read.md): 60 cases, three exact historical
pins and complete qualifications; three fresh replays passed 360 indexed/full comparisons.
F03/F12 gain an executable reference target; their portable/production decisions remain
provisional. Accepted evidence and statuses are unchanged; mobile, offline and renderer
feasibility remain unproven.

The user-authorised contract task supersedes prerequisite resolution as the current
engineering path, without resolving the physical-device gate. Exactly one next task:
**MERIDIAN ATLAS PORTABLE READ-ONLY PROJECTION AND INDEPENDENT READER SPIKE — NOT BEGUN**.
The linked report specifies its bounded, platform/framework-neutral scope and safeguards.


## Portable Atlas projection spike — 9 October 2026

[SEMANTIC PORTABILITY DEMONSTRATED](../../docs/research/atlas-portable-projection.md), bounded to the frozen Riffelhorn
profile and desktop GIS toolchain: three isolated 60/60 replays, exact full-envelope
agreement, 14 novel behaviour/failure tests and byte-identical 116.7 MB projection
reproduction. The independent Python reader requires no original source files,
authoritative query implementation, Node or network during tested reads.

F03/F12 gain semantic feasibility evidence; format/framework, mobile and robust offline
lifecycle remain provisional or unproven. Canonical authority, accepted evidence,
frozen fixtures and research statuses remain unchanged. Exactly one next bounded task:
**MERIDIAN ATLAS PORTABLE PROJECTION HARDENING AND OFFLINE FAILURE VALIDATION — NOT BEGUN**.
Its scope follows observed incomplete-install/post-open consistency gaps, not production
or private-repository integration. The linked report records commands, costs and limits.


## Independent projection lifecycle experiment — 9 October 2026

[DESKTOP OFFLINE CONSISTENCY DEMONSTRATED](../../docs/research/atlas-portable-projection-hardening.md), bounded to Windows/NTFS and the
retained finite read profile: complete closure before ready, separate installation
selection/exact scientific generation, failed-replacement preservation, restart,
explicit deletion and verified in-memory raster snapshots. Frozen semantic cases,
canonical authority and accepted research remain unchanged. The report records
commands, failure tests, measured storage/memory and unproven power-loss/authenticity/
mobile guarantees. Implementation stays under scripts/atlas/portable-spike; the
Atlas authority, Weather and production application are unchanged.

F03/F05/F12 and E02/E05 gain bounded desktop evidence; final formats/frameworks,
physical-device feasibility and legal redistribution remain open. Exactly one
subsequent task: **MERIDIAN ATLAS OFFLINE PROJECTION PORTABILITY AND RESOURCE-REDUCTION
STUDY — NOT BEGUN**. Its scope follows observed source-raster overhead, desktop GIS
dependencies and unresolved offline rights; no mobile deployment, production or
private-repository integration is begun.

## Atlas projection resource study — 9 October 2026

[Bounded study](../../docs/research/atlas-portable-projection-reduction.md): **PARTIALLY DEMONSTRATED**. One verified captured snapshot
serves three explicit Riffelhorn historical pins; median peak working set fell from
599.45 MB to 332.74 MB (about 45%). One-reader memory, the 116,692,961-byte package
and GIS dependencies remain unchanged. All 60 frozen cases passed in each of three
fresh processes per mode, plus 159 novel comparisons; full-grid qualifications,
readiness, restart and post-open consistency are preserved. This is desktop evidence,
not mobile or redistribution clearance; all accepted authority remains unchanged.
Implementation and reproducible commands are linked from the report.

Exactly one next bounded task, **NOT BEGUN**: **MERIDIAN ATLAS NATIVE-GRID WINDOW
PROJECTION AND SCIENTIFIC-CLOSURE FEASIBILITY**, limited to proving whole-profile
Copernicus window support, original grid identities and exact semantic/lifecycle
conformance. No mobile, private repository, production or framework decision.


## Atlas native-grid window feasibility — 9 October 2026

[Bounded experiment](../../docs/research/atlas-native-grid-window.md): **DEMONSTRATED** for the retained Riffelhorn read profile
and checked PROJ 9.5.1 operation. A conservative 366-column strip retains all original
rows/grid identities; no adoption of the unproved 94 × 66 crop. Package size falls
from 116,692,961 to 77,412,208 bytes; DSM from 42,594,792 to 3,306,806 bytes. All 60
unchanged cases pass in three isolated processes per representation, plus 436 novel
complete-envelope comparisons. Three-pin shared peak memory falls modestly from
332.87 to 320.32 MB; verified opening is essentially unchanged. Exact native indices,
full qualifications, all other members, historical pins, readiness, failed-replacement
preservation, restart and captured post-open consistency remain intact.

The isolated implementation/commands and scientific closure argument are linked from
the report. Canonical Atlas authority, accepted research, 42 status rows, 113 protected
hashes and Swiss/AWS negative reconciliation remain unchanged. This does not resolve
F04/F11 mobile rendering/framework or F17 legal distribution gates; F03/F05/F12 gain
bounded desktop evidence only. No mobile, Weather, UI, private or production integration.

Exactly one subsequent bounded task — **MERIDIAN ATLAS PORTABLE READER GEOMETRY AND
CRS DEPENDENCY FEASIBILITY — NOT BEGUN**, addressing the unchanged desktop GIS stack
and its deployment/semantic constraints rather than another minimum-crop optimisation.


## Atlas geometry and CRS dependency feasibility — 10 October 2026

[Bounded study](../../docs/research/atlas-geometry-crs-feasibility.md): **PARTIALLY DEMONSTRATED**. The complete retained operation
inventory and dependency/rights comparison are documented. One direct binding to the
already installed PROJ 9.5.1 C API agrees exactly with the accepted Windows reader:
60 frozen cases per path across three pins, 524 coordinate comparisons and 220 novel
complete envelopes. This is the same CRS engine with a different binding; GEOS/raster
operations remain unchanged. Full-reader peaks remain approximately 321 MB; no mobile,
Python-free reader, replacement geometry kernel or distribution clearance is established.

Accepted authority, window/shared-store implementation, frozen fixtures, 42 status rows,
113 protected hashes and negative Swiss/AWS reconciliation remain unchanged. F03/F12 gain
bounded binding evidence; mobile/framework, packaging and rights decisions remain open.
The report links isolated code, raw measurements, commands and exact validation limits.

Exactly one subsequent bounded task — **MERIDIAN ATLAS NATIVE GEOMETRY C-API CONFORMANCE
SPIKE — NOT BEGUN**, limited to the existing reference kernel's predicate, encoding,
ownership and complete-envelope compatibility. No custom GIS engine, private access,
SDK installation, mobile deployment or production integration.


## Atlas native geometry C-API conformance — 10 October 2026

[Bounded spike](../../docs/research/atlas-native-geometry.md): **DEMONSTRATED** for the installed Windows GEOS 3.13.1 /
CAPI 1.19.2 binding and retained Riffelhorn profile. A separately owned native context
preserves boundary-inclusive covers, positive-area clipping, holes/multipart, XY/XYZ
serialisation, ownership and explicit errors. All 60 frozen, 153 new and 436 adapted
window complete envelopes agree exactly. This is the same GEOS engine through another
binding, not independent algorithm validation or mobile portability.

The report links isolated code, commands, raw trials and validation receipts. Three-pin
peak memory remains about 321 MB; the accepted Python/NumPy/GDAL validation/raster stack
and one-time Shapely interchange remain. No production interface or kernel replacement.
Scientific authority, native-window/shared-store implementation, frozen fixtures,
42 status rows, 113 protected hashes and negative Swiss/AWS reconciliation are unchanged.
F03/F12 gain binding evidence; framework, renderer, packaging and rights gates remain open.

Exactly one subsequent bounded task — **MERIDIAN ATLAS PORTABILITY CONSOLIDATION AND
CROSS-PLATFORM ARCHITECTURE HANDOFF — NOT BEGUN**. Consolidate accepted semantic,
closure, ownership, resource and platform evidence for the dedicated architecture
study; no new GIS optimisation, private access, SDK, mobile deployment or implementation.


## Portability consolidation — 10 October 2026

The [architecture handoff](../../docs/research/atlas-portability-handoff.md) is the current
cross-platform evidence index. Canonical publications and this supported desktop authority
remain authoritative; projections remain read-only representations. Windows GEOS/PROJ
C bindings do not make the complete Python/GDAL reader mobile-ready or replace this runtime.
The handoff distinguishes semantics, kernels, decoding, verified ownership and OS installation,
with source-linked measurements and unresolved resource/rights requirements. No new runtime
interface or command is introduced.

Exactly one next task: **MERIDIAN WEB/MOBILE ARCHITECTURE AND CODE-SHARING FEASIBILITY STUDY —
NOT BEGUN**; no further Atlas optimisation, framework selection or production integration.


## Cross-platform architectural context — 10 October 2026

The [Meridian-wide feasibility study](../../docs/research/meridian-cross-platform-architecture.md)
separates this authoritative desktop runtime, portable scientific contracts/readers,
rendering and platform storage/device services. Shared native kernels are provisional
boundaries; the browser/mobile application must not depend on direct Node filesystem
access or a mandatory network service for field queries. No runtime interface changed.

Exactly one next task: **MERIDIAN MOBILE FEASIBILITY PREREQUISITE RESOLUTION — PHYSICAL
DEVICES AND BUILD ACCESS — NOT BEGUN**. Named hardware/build availability and lawful
trial resources precede mobile terrain, target-reader and offline recovery evidence.


## Non-device packaging prerequisites — 10 October 2026

[Platform closure and scientific packaging requirements](../../docs/research/meridian-non-device-prerequisites.md) distinguish versioned read semantics, native kernels/resources and platform custody. The desktop Python/Node reference remains authoritative for its accepted role; no complete Python-free target reader is established. No runtime, projection, query or publication changes accompany this report.

Exactly one next project task: **MERIDIAN WEATHER FOUNDATIONAL RESEARCH PROGRAMME — SCOPE, SCIENTIFIC REQUIREMENTS AND EVIDENCE INVENTORY — NOT BEGUN**. No additional Atlas optimisation prerequisite remains; target scientific conformance and physical-device resource/recovery gates still apply before deployment.
