# Local Atlas runtime: first read/index/query slice

This entry point opens the accepted seven-component Tryfan/Riffelhorn retained
publication. It fully validates canonical metadata and retained payloads, builds a
disposable SQLite catalogue, and answers pinned qualified queries. It does not
register new evidence, run derivations, write publications, or change production
Atlas. The [frozen scope](slice-plan.json) and
[result report](../../docs/research/atlas-local-runtime.md) describe the boundary.

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
filesystem **publication** root is never written. No cross-filesystem transaction
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
operational CLI/library paths are entirely explicit. The first adapter is bounded
to three committed generations, seven components and 49 real selectors. See the
report for measured costs and limitations before extrapolating.
