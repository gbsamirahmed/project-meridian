# Native geometry C-API spike — frozen design

10 October 2026. Start `e7a655cc2f2c9d41381fae71680dc1cf4b2149bd`, clean public
main/origin/main, fetched 0/0. Existing scientific records, reader, PROJ binding,
window/shared owner, installation code, projections and frozen expectations are unchanged.

Inventory first: query Point/Polygon/box construction; core/raster-support intersection;
boundary-inclusive covers; positive area; bounds/XY/empty/type; full multipart and
holes; mapping order; WorldCover centre masks; native transform of query geometry.
Metadata/lineage/time filtering, affine arithmetic and decoding are separate responsibilities.
The existing GEOS 3.13.1 / CAPI 1.19.2 wheel is available locally. No local header is
bundled; use the exact tagged public header as documentation, not a new toolchain.

One isolated ctypes binding, one independently owned re-entrant context; only its
own geometry pointers enter the C API. WKB interchange from verified retained shapes
preserves two/three dimensions, order and values; never pass Shapely opaque pointers.
Use native point and empty-polygon creation, native GeoJSON deserialisation for bounded
2D query polygons/holes/multipart construction, WKB reader/writer for interchange,
borrowed const coordinate/ring/component access for exact mapping, covers/intersection/
area/validity, and prepared covers for centre arrays. No custom geometry algorithm,
normalisation, make-valid, precision reduction or unsupported scientific query.

Keep callback references alive; collect bounded native notices/errors without throwing
through C. Null/error return is failure, not empty evidence. Owned geometries/readers/
writers/prepared handles and returned buffers have explicit destruction. Borrowed
children/sequences are not destroyed. Context close invalidates handles; tokenised
ownership detects stale wrappers, double-close and cross-context arguments. Sequential
query arenas release temporary geometries without destroying pinned feature copies.
No threading, hostile native memory corruption or security certification claim.

Run primitive comparisons first, including all 18 requested boundary/error/lifetime
categories and retained feature WKB/mapping. Only then scope reader constructors,
mapping, projected and WorldCover functions and temporarily swap pinned features to
owned WKB copies. Existing direct PROJ handles query transforms. Restore every field
on success/failure. Frozen results are comparison targets only; no IDs/answers enter
native query logic. Full substitution may retain Shapely during validation and one-time
interchange, and Python/GDAL/NumPy; it is not a Python-free complete reader.

Compare complete envelopes across all 60 unchanged cases/three pins and deterministic
novel core/CRS/window/lineage queries, then rerun accepted regressions and owned lifecycle
failures. Measure three fresh desktop trials for initialisation, construction/destruction,
predicates/intersection, WKB/mapping and one/three-reader warm workloads. No cache clearing
or mobile inference. Reuse existing packages, no new projection copies except bounded
owned lifecycle faults. Extra diagnostics aim below 10 MB; inherited 512 MiB scratch/store
and 768 MiB process budgets apply. Stop on semantic discrepancy or a substantial reader
rewrite. No production interface, renderer, SDK, new source, private access or next task.

## Reproduction and observed result

[Research report](../../../../docs/research/atlas-native-geometry.md) and
[path-free raw receipts](results.json). **DEMONSTRATED**, limited to the checked
Windows GEOS 3.13.1 CAPI 1.19.2 binding and retained Riffelhorn profile. This is
another binding to the same engine, not independent geometry-engine validation,
a Python-free reader or mobile deployment.

Prerequisites: existing Windows GIS Python 3.12.6 with Shapely 2.1.2 and its installed
GEOS DLLs, pyproj 3.7.2/PROJ 9.5.1 resources, rasterio/GDAL and NumPy; the unchanged
original and native-window projections outside Git; all three frozen pins. `-B`
prevents Python bytecode writes. No compiler, download, data acquisition or install.
The accepted projection manifests supply identities and member seals. Never point
fault tests at accepted source directories: the unchanged lifecycle tests create
only owned temporary copies.

From the public repository root, substitute explicit existing external paths:

```powershell
$studyPython = 'EXISTING_GIS_PYTHON'
$windowProjection = 'EXISTING_VERIFIED_NATIVE_WINDOW_PROJECTION'
$originalProjection = 'EXISTING_VERIFIED_ORIGINAL_PROJECTION'
$env:ATLAS_WINDOW_PROJECTION = $windowProjection
$env:ATLAS_SPIKE_PROJECTION = $originalProjection
# Primitive comparisons first (six primitive tests and retained-feature interchange).
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/native-geos -p test_native.py -v -k Primitive
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/native-geos -p test_native.py -v -k RetainedFeatures
# Then complete query substitution, novel envelopes and unchanged lifecycle cases.
& $studyPython -B -m unittest discover -s scripts/atlas/portable-spike/native-geos -p test_native.py -v
& $studyPython -B scripts/atlas/portable-spike/native-geos/test_existing.py
& $studyPython -B scripts/atlas/portable-spike/native-window/replay.py --projection $windowProjection --fixtures fixtures/atlas-read/v1
& $studyPython -B scripts/atlas/portable-spike/native-geos/compare.py --projection $windowProjection --fixtures fixtures/atlas-read/v1
# Repeat each measurement combination in three fresh, sequential processes.
foreach ($bindingMode in @('reference','native')) {
  & $studyPython -B scripts/atlas/portable-spike/native-geos/measure.py --mode $bindingMode --workload primitive
  & $studyPython -B scripts/atlas/portable-spike/native-geos/measure.py --mode $bindingMode --workload reader --projection $windowProjection --views 1
  & $studyPython -B scripts/atlas/portable-spike/native-geos/measure.py --mode $bindingMode --workload reader --projection $windowProjection --views 3
}
```

The reference fixture adapter verifies frozen member hashes and compares complete
semantic outcomes, reporting the first differing path. Nine expected rejections
count as passing comparisons. `native.py` and `adapter.py` never inspect fixture IDs
or expected answers. Query assembly, scientific documents and captured raster
semantics remain in the unchanged accepted reader. The scoped substitution restores
constructors/functions after every query; it is sequential and not production-safe
for simultaneous overrides.

Results: 60 frozen, 153 new and 436 adapted existing window envelopes agree exactly;
no numerical tolerance or expected-result edits. Six point, six centre-mask, seven
overlay cases and 38 full XY/XYZ feature interchanges agree, plus 1,000 release cycles.
The nine new tests and eight adapted tests pass. The report records all regression
commands, preservation verification, measurements and checks deliberately not run.

`measure.py` compares import/context costs and small representative geometry operations.
The field named `wkbRead` includes WKB writing: it measures a roundtrip. Full opening
includes verified snapshot/decoding, view selection, native context and 38 feature copies;
imports precede the timer. Working-set peaks are process measurements, not per-library
allocation attribution. The complete three-pin reader remains about 321 MB; no whole-
reader memory reduction or mobile performance claim. WKB equality is version-specific;
no general geometrically equivalent byte-identity promise. Licences, binary closure,
threading, target platforms and native allocator instrumentation remain unresolved.
