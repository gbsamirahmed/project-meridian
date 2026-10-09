# Portable read-only projection spike — frozen design

9 October 2026; start `5c93074f9773815111af96f89c3a73fcbb3b526a`.
Public main, fetched origin/main 0/0, clean initial tree. The unchanged
[reference profile](../../../docs/atlas/portable-read-contract.md) and its 60 cases,
three exact pins and sealed expected outcomes are the acceptance reference.

## Question, implementation and authority

Can one self-contained, read-only projection reproduce the finite Riffelhorn profile
without importing the authority or looking up frozen answers? Choose **Python** for
the independent reader, using the already installed NumPy, rasterio, Shapely and
pyproj numerical/geometry libraries. These libraries are not Atlas query code.
Choose **one file-backed projection directory**: versioned JSON metadata with sealed
native GeoTIFF members. This avoids a custom raster encoding or database. Choices
are spike-local; no phone Python requirement, final format or framework is selected.
A small Node export bridge may invoke the existing Node authority to materialise
records. All independent query logic is Python; the bridge is not a reader dependency.

Export unrestricted authoritative metadata once per pin, not the 60 answers: all
qualified records/documents, regional references, membership, explicit relationships,
method and knowledge revisions. Copy the accepted full native vector geometries
from prepared features.json, six byte-identical raster inputs and scalar consumed
cell descriptors from the accepted retrieval view. Preserve full geometries rather
than bounding-box approximations. Scientific references keep original identities
and source locators; projection-local file names are storage bindings only.

Each generation entry binds exact pin, authoritative closure fingerprint and metadata
checksum. The projection manifest seals every required member, schema/profile and
coverage. Original source/publication files remain read-only. No publication creation
or active-root advancement. Static qualified documents may be copied; spatial selection,
native affine cells/windows, WorldCover counts, conjunction, time/knowledge matching,
lineage traversal and query-specific evidence/document identities must be computed
independently. No fixture ID or expected-answer table enters the reader or export.

## Resource boundary and support

Inspected native closure: six raster files **108,207,242 bytes**; prepared full features
**5,386,941 bytes**. Estimate less than 125 MiB final projection, at most two external
copies plus owned temporary metadata below 300 MiB. Stop at 160 MiB per projection;
no terrain pyramid. Initial memory planning: under 512 MiB desktop working set,
measured rather than claimed. The full one-degree DSM source is retained to preserve
native row/column identities; no silent window reindexing. No geographical acquisition.

Support only the documented Riffelhorn source/derived read profile, with full
whole-publication regional references retained. No new scientific method, Tryfan
spatial implementation, Exe semantics, general polygon algebra, routing, rendering,
mobile, network service or production package. Unknown remains unknown; LN02/EGM2008,
DSM/DTM and the negative Swiss/AWS finding remain distinct. Geometry/CRS libraries
must run with network disabled. A local GDAL/PROJ dependency is an explicit limit.

## Acceptance, independent checks and stop

All 60 unchanged complete semantic outcomes across the three pins must match, including
nine expected errors; only operational metrics excluded. Test novel nearby/boundary,
combined identity/time/spatial, lineage, generation, malformed request and corrupt/
missing/incompatible projection cases. Rebuild must reproduce the same member hashes.
Measure generation/storage, cold open, warm queries and memory on this desktop.
Demonstrate answering from only projection + reader + installed libraries in a
separate process, without the repository authority, original source paths or network.
Integrity checks are not authenticity, legal redistribution clearance or safe updates.

Stop on unbounded closure, lost scientific meaning, unavailable inputs or a required
second complete scientific engine. A partial result must keep failed cases visible;
never change frozen expectations to pass. Follow-up is exactly **MERIDIAN ATLAS
PORTABLE PROJECTION HARDENING AND OFFLINE FAILURE VALIDATION — NOT BEGUN**, scoped
from actual observed weaknesses. See the eventual study report for results and commands.

## Projection schema and reproducible commands

`manifest.json` declares schema/profile, core/CRS, prepared revision, exact generation
entries (metadata member, authority fingerprint, alias/count), identity-to-native-raster
bindings and all required member size/hash seals. `projectionIdentity` is the accepted
canonical hash of the manifest without that field. Generation members contain the
unfiltered qualified answer plus scalar selectors and knowledge descriptors. Shared
assets are full prepared features, source-native WorldCover claims and six original
rasters. No source locator becomes a device path; the explicit binding resolves it.
All metadata/geometry/native payload required for this profile must be present before
opening. Hashes establish consistency, not trusted publisher or redistribution rights.

[Study results and limits](../../../docs/research/atlas-portable-projection.md).
Use the same external local config and installed toolchain as the
[reference commands](../read-conformance/README.md). Outputs must be new external
directories outside the repository, retained data and publication roots. No install.

```powershell
node scripts/atlas/portable-spike/build.mjs --config LOCAL_CONFIG_JSON --output NEW_EXTERNAL_PROJECTION
$spikePython = 'EXISTING_GIS_PYTHON'
& $spikePython -B scripts/atlas/portable-spike/conformance.py --projection EXTERNAL_PROJECTION --fixtures fixtures/atlas-read/v1
$env:ATLAS_SPIKE_PROJECTION = 'EXTERNAL_PROJECTION'
& $spikePython -B -m unittest discover -s scripts/atlas/portable-spike -p test_reader.py -v
& $spikePython -B scripts/atlas/portable-spike/isolation.py --projection EXTERNAL_PROJECTION --config LOCAL_CONFIG_JSON --fixtures fixtures/atlas-read/v1
& $spikePython -B scripts/atlas/portable-spike/benchmark.py --projection EXTERNAL_PROJECTION
# Pass an exact manifest generation key and JSON query; no active/latest fallback.
& $spikePython -B scripts/atlas/portable-spike/reader.py --projection EXTERNAL_PROJECTION --generation EXACT_GENERATION --query '{"identity":"glaciers:683"}' --identity EXPECTED_PROJECTION_IDENTITY
```

Library: `Reader(root, exact_generation, expected_projection=None).read(query)` returns
the complete semantic answer; `.outcome(query)` wraps expected query rejection.
Projection-open failures raise `ReadError` with `projection-*` codes; malformed CLI
JSON exits nonzero. `profile-unsupported` identifies regional spatial operations
outside this spike. It is not an added authoritative error taxonomy. Do not equate
empty evidence, unknown time, unsupported request and unavailable projection.

Builder needs Node authority, retained inputs/publications and installed GIS Python.
Reader needs only its projection, Python and NumPy/rasterio/Shapely/pyproj (local
GDAL/PROJ resources), not Node, the repository, original source files or network.
Conformance additionally reads the frozen fixture files; they are never reader input.
The isolation tool denies original authority/source opens and network/child dispatch
in its separate process. Its audit hook is evidence, not a security sandbox.

Rebuild to another new external directory, compare all member hashes including manifest,
then deliberately remove only owned scratch if appropriate. There is no in-place update,
installer, download protocol, ready-state manager, delta or mobile storage guarantee.
`build.mjs` validates authority fully; opening a projection verifies the exported closure,
not the original scientific publication afresh. Staged output/rename has not yet been
fault-injection tested. A passing finite corpus does not establish arbitrary predicates.

## Hardened desktop store experiment

The [hardening design](HARDENING.md) and [measured report](../../../docs/research/atlas-portable-projection-hardening.md)
supplement the original spike; its frozen semantic profile and projection identity
remain unchanged. `verification.py` bounds parsing/closure, `reader.py` captures sealed
native rasters in memory, and `store.py` keeps staging, ready receipts and selection
separate. Exact scientific generation is always supplied independently.

```powershell
$spikePython = 'EXISTING_GIS_PYTHON'
$projection = 'EXISTING_EXTERNAL_PROJECTION'
$store = 'NEW_OWNED_EXTERNAL_STORE'
$projectionIdentity = 'a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c'
$generation = '5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289'
& $spikePython -B scripts/atlas/portable-spike/store.py init --store $store
& $spikePython -B scripts/atlas/portable-spike/store.py install --store $store --projection $projection --identity $projectionIdentity
& $spikePython -B scripts/atlas/portable-spike/store.py open --store $store --generation $generation
# Explicit selection or historical installation; never a generation fallback.
& $spikePython -B scripts/atlas/portable-spike/store.py select --store $store --identity $projectionIdentity
& $spikePython -B scripts/atlas/portable-spike/store.py open --store $store --identity $projectionIdentity --generation $generation
$env:ATLAS_SPIKE_PROJECTION = $projection
& $spikePython -B -m unittest discover -s scripts/atlas/portable-spike -p 'test_*.py' -v
& $spikePython -B scripts/atlas/portable-spike/measure_store.py --projection $projection
& $spikePython -B scripts/atlas/portable-spike/benchmark.py --projection $projection
& $spikePython -B scripts/atlas/portable-spike/isolation.py --projection $projection --config LOCAL_CONFIG_JSON --fixtures fixtures/atlas-read/v1
```

Library queries: `with Store(store_root).open(exact_generation) as reader:` then
`reader.read(query)` or `outcome(query)`. Keep that context open for pinned reads;
`close()` releases native snapshots and later queries fail. An open snapshot survives
file replacement/deletion; fresh opens reject corrupted files. All pins are verified
before readiness. Direct `Reader(...)` still accepts the same exact generation and
optional expected projection identity.

Explicit destructive operations operate **only on the initialised owned store**:
`store.py delete --store OWNED_STORE --identity EXACT_PACKAGE_ID`; deleting the selected
package clears selection, with no automatic fallback. `discard-stage --store OWNED_STORE
--stage candidate-NAME` removes a named abandoned stage. Close existing readers to
release their snapshots. Never point fault trials/deletion at canonical data or the
original generated projection. Tests make full disposable copies; no raster hard
links are mutated. `measure_store.py` cleans its own temporary stores/candidate copies.

The 512 MiB store ceiling counts current packages and abandoned stages before a new
full copy; it is a spike bound, not an offline product quota. Ready and selection
records are flushed/fsynced then replaced in the same directory. Windows/NTFS
process interruptions are tested; power-loss/directory durability, hostile writers,
trusted origin and mobile storage are not. No automatic repair, downloader or
production format commitment. The report states measured storage/memory limits.
