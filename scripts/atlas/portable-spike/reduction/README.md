# Projection resource experiment — frozen design

9 October 2026. Start `d006e4515794909d2e5ad00d8617aabdb6abbd4e`, clean public main,
fetched origin/main 0/0. [Contract](../../../../docs/atlas/portable-read-contract.md),
[baseline](../../../../docs/research/atlas-portable-projection-hardening.md) and all
60 frozen cases/three pins remain unchanged.

## Inventory and selected experiment

The four 2000 × 2000 Swiss DTM tiles partition the entire supported 4 km² core;
all their cells remain queryable. WorldCover is already a small native-grid subset.
The Copernicus one-degree DSM is much larger than applicability: a 128-segment
transformed-envelope inventory estimates a 94 × 66 source-cell window. That estimate
is not a completeness proof for every transformed query, nor a replacement raster.
All six are already losslessly compressed. Full native features, qualification
references and scalar selectors are independently necessary; bounding boxes or the
60 requests cannot define a smaller scientific support.

Implement **one memory-ownership variant**, `shared-snapshot-experiment/v1`, using
Python and the unchanged v1 JSON/GeoTIFF projection. It shares one completely verified
captured Snapshot between explicit generation views in one process. Reuse the accepted
independent Reader's query implementation unchanged; do not build another scientific
engine. No package bytes, identity, schema, raster indices, qualifications or scientific
coverage change. Storage reduction and removing GIS dependencies are analysed only.
This low-risk experiment tests option A, rather than implementing crops and a new
installer together. The existing baseline builder, reader, verification and store
remain byte-identical. No final reader language, format or mobile choice follows.

## Ownership, readiness and consistency

Opening an owner verifies all package members and all three pins once, including
captured raster bytes. A generation view borrows those resources and binds exactly
one available pin; unknown pins fail without fallback. Views execute the unchanged
native geometry, raster, temporal and relationship predicates and return copied
complete envelopes. A view's close releases only its lease. Owner close is rejected
while leases exist; after their explicit close it releases the underlying snapshot.
No global cache, cross-process sharing, mutable-path rereads or automatic generation
selection is added. Sequential use on this host is supported; parallel thread use
and hostile in-process mutation are not claimed.

For installed packages, check the existing Store's exact ready receipt/selection,
then open and fully verify a new owner. Existing staging, ready and selection commit
boundaries are reused unchanged. Failed replacement cannot change an already captured
owner. New owner/restart always rechecks files; no previous owner is used to disguise
a corrupted new open. Post-open path corruption, replacement and deletion must leave
held views' exact historical answers unchanged. Test only disposable owned copies.
Hashes remain integrity checks, not publisher authenticity or legal clearance.

## Acceptance, measurements and budget

Baseline and variant must each pass all 60 unchanged complete semantic outcomes across
three exact pins, nine expected errors included. Add novel core corners/seams/nearby
points, WorldCover area, CRS conversion, conjunction, time/knowledge and lineage
checks beyond frozen requests. Exercise leases, bad pin/identity, corruption,
incompatibility, missing members, store failure/restart/deletion and post-open changes.
A fail is an integrity/availability error, never empty evidence. Any semantic mismatch
stops the experiment; do not refresh expectations.

Measure fresh-process one versus three pinned views in both modes, complete open and
warm-query distributions and Windows peak working set. Repeat three times, retain OS
caches, report process-cold rather than storage-cold timings. Reuse unchanged lifecycle
measurements/commands and rerun relevant recovery tests. Package storage and staging
are expected to remain unchanged; no false storage-reduction claim. Serial owned
fault copies remain within the inherited 512 MiB scratch/768 MiB desktop memory bounds;
no raster pyramid, installed toolchain, source acquisition or committed payload.

Stop with a measured partial/full reduction conclusion or a precise blocker. No
mobile, renderer, UI, Weather, production installer, distribution, private access or
scientific reinterpretation. Subsequent task is selected from observed results, not
begun here. Source-by-source rights and dependency inventories accompany the report.

## Reproduce the completed experiment

Run from the public repository with the **existing** GIS Python environment. No
installation is prescribed. Keep projections, stores, local configuration and logs
outside Git; the committed JSON files contain compact diagnostics, not payloads.
Replace placeholders with explicit paths. Isolation config uses the unchanged
baseline fields `dataRoot`, `registrationWorld`, `legacyWorld` and `python`.

```powershell
$spikePython = 'EXISTING_GIS_PYTHON'
$projection = 'EXISTING_VERIFIED_V1_PROJECTION'
$config = 'EXISTING_LOCAL_AUTHORITY_CONFIG_JSON'
$store = 'NEW_OWNED_EXTERNAL_STORE'
$projectionIdentity = 'a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c'
$generation = '5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289'
$env:ATLAS_SPIKE_PROJECTION = $projection
& $spikePython -B scripts/atlas/portable-spike/reduction/inventory.py --projection $projection
& $spikePython -B scripts/atlas/portable-spike/reduction/replay.py --projection $projection --fixtures fixtures/atlas-read/v1
& $spikePython -B scripts/atlas/portable-spike/reduction/isolation.py --projection $projection --config $config --fixtures fixtures/atlas-read/v1
& $spikePython -B -m unittest discover -s scripts/atlas/portable-spike/reduction -p 'test_*.py' -v
& $spikePython -B -m unittest discover -s scripts/atlas/portable-spike -p 'test_*.py' -v
# Twelve serial fresh processes: three repetitions per mode and reader count.
foreach ($mode in @('baseline','shared')) {
  foreach ($count in @(1,3)) {
    foreach ($trial in @(1,2,3)) {
      & $spikePython -B scripts/atlas/portable-spike/reduction/measure.py --projection $projection --mode $mode --readers $count
    }
  }
}
& $spikePython -B scripts/atlas/portable-spike/reduction/lifecycle.py --projection $projection
# Reuse unchanged installer and its ready-state boundaries.
& $spikePython -B scripts/atlas/portable-spike/store.py init --store $store
& $spikePython -B scripts/atlas/portable-spike/store.py install --store $store --projection $projection --identity $projectionIdentity
& $spikePython -B scripts/atlas/portable-spike/reduction/shared.py --store $store --identity $projectionIdentity --generation $generation --query '{"identity":"glaciers:683"}'
```

Regeneration uses the unchanged `build.mjs --config LOCAL_CONFIG --output NEW_DIRECTORY`
command and byte-hash comparison of every member including manifest. Authority replay
uses `node scripts/atlas/read-conformance/run.mjs --config LOCAL_CONFIG`.
See the unchanged [baseline commands](../README.md) and [store design](../HARDENING.md)
for explicit selection/deletion. Never delete or inject faults into original packages,
canonical data or fixture directories. These tests create and clean owned temporary
copies. Incomplete stages are not scientific query inputs.

Library use (put the experiment directory on the spike driver's import path):

```python
from shared import SharedProjection
from store import Store

with SharedProjection.from_store(Store(store_path), exact_package_identity) as owner:
    with owner.pin(exact_before_generation) as before, owner.pin(exact_after_generation) as after:
        old = before.outcome({"identity": "glaciers:683"})
        current = after.outcome({"identity": "glaciers:683"})
# Each view must close before owner close; queries after close fail explicitly.
```

`SharedProjection(path, expected_identity)` also opens a direct verified package.
`pin()` always requires the exact scientific generation. No implicit fallback or
cross-process cache. `read()` raises a `ReadError`; `outcome()` returns the unchanged
semantic answer/error envelope. The small CLI reports JSON and non-zero failure status.
Integrity/availability errors must not be presented as valid empty results.

## Recorded outcome

**PARTIALLY DEMONSTRATED:** sharing three captured views reduces desktop memory by
about 45%; package bytes and GIS dependencies are unchanged, and one-reader memory is
essentially unchanged. [Measured report](../../../../docs/research/atlas-portable-projection-reduction.md),
[source inventory](source-inventory.json) and [results](results.json) record complete
scientific/resource boundaries. The 60 frozen outcomes remain exact in both modes,
with three fresh isolated runs each; nine new tests include 159 novel comparisons.
No mobile, public distribution, final representation or next-task implementation.

Additional regression commands actually executed:

```powershell
node --test scripts/atlas/read-conformance/test-fixtures.mjs
& $spikePython -B scripts/atlas/riffelhorn-retrieval/test_query.py
node --test runtime/atlas/test-runtime.mjs runtime/atlas/test-lifecycle.mjs runtime/atlas/test-registration.mjs runtime/atlas/test-retrieval.mjs
npm.cmd run lint
node node_modules/typescript/bin/tsc -b --pretty false
node node_modules/vite/bin/vite.js build --config EXISTING_EXTERNAL_APP_ONLY_CONFIG
```

The external app-only config excludes Weather processing and public-data copying;
this does not claim the full data/Weather build was run. Frozen reference replay and
regeneration additionally require the twelve sealed retained inputs and exact worlds
identified by the unchanged fixture manifest. Direct independent tests need only the
accepted projection and existing GIS libraries.
