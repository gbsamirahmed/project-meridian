# Geometry and CRS dependency experiment — frozen scope

10 October 2026. Clean public main/origin/main at
`695b855c1440206f2082db28fe1eefbadba71e54`, fetched divergence 0/0.

Inventory precedes implementation: the finite reader requires horizontal always-xy
EPSG:2056 ↔ EPSG:4326 (CRS84 alias), fixed 32-segment area boundaries, exact core
intersection, boundary-inclusive covers, positive-area intersection, full polygons/
holes/multipart features, affine floor/ceil indexing and WorldCover centre masks.
Identity, time and lineage selection have no intrinsic GIS dependency. No vertical
conversion, geodesic geometry, arbitrary CRS or invalid-geometry repair is supported.

One locally available deployment alternative: Python ctypes calls the existing PROJ
9.5.1 C API directly, through its explicitly located pyproj wheel DLL and proj.db.
This uses the same numerical engine with a different binding, not an independent
CRS algorithm. No dependency is installed and no binary is copied or distributed.
The scoped callback replaces only independent reader.projected during sequential
comparisons, restoring it afterwards. Accepted reader, window, shared snapshot,
verification and Store code remain unchanged. Shapely/GEOS and GDAL remain required.
The adapter cannot establish a complete replacement reader or mobile packaging.

Use existing v1 and native-window projections read-only. No member/schema/identity
changes, no projected answers or case-ID dispatch. Compare all 60 unchanged fixture
outcomes over their three exact pins; independent novel queries and native affine
anchors; direct bidirectional/axis/edge transforms; retained GEOS boundary, holes,
multipart, sliver and invalid-shape diagnostics. Differences are reported exactly,
without rounding or tolerance changes. Invalid-shape diagnostics do not enlarge the
scientific query API. Do not silently repair invalid content or library errors.

Measure fresh-process import stages and one shared window owner with one/three views,
plus a small repeated coordinate batch and complete warm query workload. Windows
current/peak working sets are process observations, not allocation attribution.
Disk inventory records installed wheel directories plus companion DLL directories;
these are not minimal mobile binary estimates. Additional scratch/logs aim below
10 MB; no package copies for this comparison. Existing 512 MiB scratch and 768 MiB
process budgets apply. Existing lifecycle tests use only their owned temporary copies.

Acceptance: exact frozen envelopes, no unexplained operation differences in the tested
subset, explicit retained GIS dependencies/rights and platform gaps, preserved package
integrity/history, proportional regressions. Stop at this bounded binding result or
precise blocker. No replacement authority, custom GIS engine, new format, renderer,
SDK, device test, acquisition, private access, production integration or next task.

## Reproduction and observed result

[Research report](../../../../docs/research/atlas-geometry-crs-feasibility.md) and
[path-free measurement receipts](results.json). This directory is a sequential test
driver, not a replacement runtime package. `native_proj.py` directly binds the
existing wheel DLL and database; it installs nothing. `compare.py` reuses the
unchanged fixture replay. `test_binding.py` adds novel envelopes, native anchors,
reference geometry diagnostics and failure/ownership checks. `resources.py` inventories
installed dependencies and observes import, shared-reader and coordinate-batch costs.

Prerequisites: Windows, existing Python 3.12.6 GIS environment, pyproj 3.7.2 / PROJ
9.5.1, retained unchanged native-window projection and all three exact fixture pins.
The full comparison retains Shapely 2.1.2 / GEOS 3.13.1, rasterio 1.4.3 / GDAL 3.9.3
and NumPy 2.5.3. Native contexts are owned and sequential; the temporary callback is
restored on exit, including injected failure. No concurrent callback-use guarantee.

From the public repository root, using explicit existing external paths:

```powershell
$studyPython = 'EXISTING_GIS_PYTHON'
$windowProjection = 'EXISTING_VERIFIED_NATIVE_WINDOW_PROJECTION'
$env:ATLAS_WINDOW_PROJECTION = $windowProjection
& $studyPython -B scripts/atlas/portable-spike/native-window/replay.py --projection $windowProjection --fixtures fixtures/atlas-read/v1
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/compare.py --projection $windowProjection --fixtures fixtures/atlas-read/v1
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/geometry-crs -p test_*.py -v
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode inventory
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode imports
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode native
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode batch
# Run each combination in three separate sequential processes; do not clear OS caches.
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode reader --projection $windowProjection --binding reference --views 1
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode reader --projection $windowProjection --binding reference --views 3
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode reader --projection $windowProjection --binding native --views 1
& $studyPython -B scripts/atlas/portable-spike/geometry-crs/resources.py --mode reader --projection $windowProjection --binding native --views 3
```

Actual results: 60/60 frozen outcomes per path, 0 failures/skips, nine expected
rejections per replay; 5/5 new tests, 524 coordinate and 220 novel envelope comparisons.
No rounding or changed expectations. Warm query trials use 15 repetitions per kind/pin;
three fresh processes per binding/view count. Cached batches use 30 repetitions of
2,000 pairs in each of three processes. Open timing observes the unchanged verified
owner/views before the alternative context is constructed; direct context setup is
reported separately. OS storage caches remain warm. Full-reader memory is essentially
unchanged at about 321 MB; direct-XY import independence is not full-reader independence.

The projection and captured post-open member policy are unchanged. Existing lifecycle/
window/shared tests are rerun, not reimplemented. Hashes establish package consistency,
not authenticity or protection against future host DLL/database mutation. No native
mobile build, independent geometry kernel, device performance or legal clearance.

Relevant retained regression commands, with both projections explicitly configured:

```powershell
$env:ATLAS_SPIKE_PROJECTION = 'EXISTING_VERIFIED_ORIGINAL_PROJECTION'
$env:ATLAS_WINDOW_PROJECTION = $windowProjection
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike -p test_*.py -v
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/native-window -p test_*.py -v
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/reduction -p test_*.py -v
& $studyPython -B scripts/atlas/riffelhorn-retrieval/test_query.py
node --test scripts/atlas/read-conformance/test-fixtures.mjs
node --test runtime/atlas/test-runtime.mjs runtime/atlas/test-lifecycle.mjs runtime/atlas/test-registration.mjs runtime/atlas/test-retrieval.mjs
node scripts/atlas/read-conformance/run.mjs --config LOCAL_CONFIG_JSON
npm.cmd run lint
node node_modules/typescript/bin/tsc -b --pretty false
node node_modules/vite/bin/vite.js build --config EXISTING_APP_ONLY_CONFIG
```

The app-only configuration must exclude Weather/data materialisation as in the
accepted reference workflow; do not substitute the full package build. The study's
52 preservation/scope/receipt/link checks use an owned external checker and the
starting-checkpoint baseline, not a new permanent scientific receipt or contract.
