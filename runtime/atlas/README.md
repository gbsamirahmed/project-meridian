# Local Atlas runtime: qualified evidence, queries and lifecycle

The runtime opens accepted seven-component publications and compatible eight-component registration,
nine-component derivation and ten-component registration/derivation
lifecycle extension. Canonical qualified files and the filesystem publication root
remain authoritative; SQLite is a disposable candidate catalogue. It can now execute
one accepted native Riffelhorn slope method and its planar-area summary, inspect scoped
invalidation, stage/validate/publish immutable generations, and query their history.

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
