# Atlas native geometry C-API conformance spike

Reviewed 10 October 2026. **DEMONSTRATED — Windows GEOS binding conformance within the retained Riffelhorn read profile.** A separately owned GEOS 3.13.1 C-API context reproduces the tested Shapely geometry behaviour, including full query envelopes. This is the **same GEOS engine**, not independent validation of its algorithms, a Python-free reader or demonstrated mobile portability.

Start: clean public `main` at `e7a655cc2f2c9d41381fae71680dc1cf4b2149bd`; fetched `origin/main`, 0/0. The [previous feasibility study](atlas-geometry-crs-feasibility.md) established direct PROJ binding equivalence and left geometry binding unresolved. This task changes neither that historical result nor scientific authority. Read the [portable contract](../atlas/portable-read-contract.md), [projection](atlas-portable-projection.md), [hardening](atlas-portable-projection-hardening.md), [resource reduction](atlas-portable-projection-reduction.md) and [native window](atlas-native-grid-window.md) together. Experimental [design and commands](../../scripts/atlas/portable-spike/native-geos/README.md), [binding](../../scripts/atlas/portable-spike/native-geos/native.py), [adapter](../../scripts/atlas/portable-spike/native-geos/adapter.py), [tests](../../scripts/atlas/portable-spike/native-geos/test_native.py) and [raw measurements](../../scripts/atlas/portable-spike/native-geos/results.json) are isolated and removable.

## Frozen scope and evidence

The question is whether existing native geometry operations can be called safely through an independently owned C context while preserving the complete finite read profile. No new geometry engine, query language, source, projection, production dependency or mobile toolchain is introduced. Primitive comparisons preceded query substitution. Full envelopes, novel valid queries and existing installation/recovery tests then supplied the stopping evidence.

The unchanged experimental window projection is **77,412,208 bytes**, identity `ec6308b7c195af38190eebd4239fcfbe32b416308e2404b80777c598538363f9`. The accepted original remains **116,692,961 bytes**, identity `a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c`. All member seals and scientific identities remain unchanged. The three exact pins are:

| Alias | Publication generation |
|---|---|
| before | `65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd` |
| after | `5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289` |
| legacy | `7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8` |

Before/after retain 81 qualified records and 32 relationships each; legacy retains 49 records and no derived relationships. No registration, publication or knowledge revision occurs here. Exact identities, source/preparation/method lineage, rights, uncertainty, unknown temporal values, DSM/DTM distinctions, LN02/EGM2008 qualifications, original affine indices and historical membership come from the accepted scientific records.

The vector closure has **38 features: 32 MultiPolygon and six Polygon**, 45,383 vertices and **990,868 bytes of WKB**. Actual retained geometries include both XY and XYZ. This matters: an XY-only interchange would discard source geometry information even if point predicates still matched. The full native geometry is retained; no bounding-box substitute, simplification or precision reduction is used. The 4 km² EPSG:2056 core remains `[2624000,1091000,2626000,1093000]`.

## Environment and native identity

Windows 11 `10.0.26200`, NTFS, Intel Core i7-12700H, approximately 16 GiB RAM; Python 3.12.6, Shapely 2.1.2, GEOS **3.13.1 / CAPI 1.19.2**, NumPy 2.5.3, rasterio 1.4.3 / GDAL 3.9.3, pyproj 3.7.2 / PROJ 9.5.1, Node 24.11.0. These are inventoried local distributions, not a new supported deployment matrix. No locally bundled `geos_c.h` was found in the Shapely distribution; the exact tagged primary header was consulted. No GEOS build or new installation was needed.

| Existing Shapely-wheel companion | Bytes | SHA256 |
|---|---:|---|
| `geos-ae6efa0782962b98e358f10ea539ae5f.dll` | 2,564,608 | `094508747b6bb6eb785b2aa67d7899724ce78ee6cc375e7a66e11be3bcf5a08e` |
| `geos_c-072b7a9224d16d3e4ab2395bb855b2d3.dll` | 451,072 | `7e4d87ccb640eda92f150b7cee178ef13abe282acd36af08f6dca5eddaf931a4` |
| `msvcp140-90bc62d4947a5878f1dc1057312f3be2.dll` | 557,704 | `90bc62d4947a5878f1dc1057312f3be2137eb376039f4afda2f64c06353f2198` |

The three companion DLLs total **3,573,384 bytes**. System Windows runtime dependencies are additional; this is not an audited distributable binary closure. Java/javac 21.0.2 and .NET were available; CMake, clang/GCC, Emscripten, Gradle, adb and xcodebuild were not found on the checked PATH. No compiler, device or cross-build was attempted. GDAL and pyproj have separate bundled kernels/resources: opaque objects are never passed between library instances. The experiment requires the inventoried Shapely distribution to locate its DLLs, even when the standalone binding does not import Shapely's runtime.

## Required operations and native mapping

The [exact reader](../../scripts/atlas/portable-spike/reader.py) and shared/window owners were inspected. The table describes this implementation, not a universal GIS interface. All functions below use the re-entrant `_r` form where available. Signatures were checked against the [GEOS 3.13.1 header](https://raw.githubusercontent.com/libgeos/geos/3.13.1/capi/geos_c.h.in); the [C-API guide](https://libgeos.org/usage/c_api/) identifies the supported ABI and explicit resource management. Checked 10 October 2026.

| Retained responsibility | Functions used by the spike | Scientific/error obligation |
|---|---|---|
| Context and callbacks | `GEOS_init_r`, `GEOS_finish_r`, `GEOSContext_setErrorMessageHandler_r`, `GEOSContext_setNoticeMessageHandler_r` | Independently owned context; bounded diagnostics; callback objects live through context closure |
| Point and bounded query polygon construction | `GEOSGeom_createPointFromXY_r`, `GEOSGeom_createEmptyPolygon_r`, GeoJSON reader create/read/destroy | Finite XY inputs; preserve rings, holes and multipart order; no silent repair |
| Full native feature interchange | WKB reader/writer create/read/write/destroy; output dimension, byte order, flavour and SRID settings | Preserve XY/XYZ coordinates and order; reject M; no opaque Shapely-pointer transfer |
| Geometry inspection | Type, empty, validity, area, extent, X/Y | Failure distinct from false or empty; empty bounds remain NaN at the primitive layer |
| Exact predicates and clipping | `GEOSCovers_r`, `GEOSIntersection_r` | Boundary-inclusive covers; strictly positive-area selection; edge/vertex touching is not positive support |
| Full mapping | Borrowed exterior/interior ring, component and coordinate-sequence access | Preserve holes, component order and each ordinate; borrowed pointers remain within the owning call |
| Query CRS transformation | `GEOSGeom_transformXY_r` with accepted direct PROJ callback | Same always-xy transformation; Z preserved; callback failure aborts the operation |
| WorldCover cell-centre coverage | `GEOSPrepare_r`, `GEOSPreparedCovers_r`, prepared destroy | Exact categorical centre inclusion; aligned bounded arrays; no inferred area fraction |
| Release | `GEOSGeom_destroy_r`, `GEOSFree_r` | Release owned objects and returned WKB buffers; never free borrowed children separately |

Geometry construction/serialisation/bounds are convenient binding responsibilities; they are not separate scientific algorithms. Runtime clipping, exact point coverage, positive-area support and WorldCover centre predicates genuinely need a geometry kernel for arbitrary valid requests. Query-area densification remains the accepted 32 subdivisions per edge before transformation. Affine arithmetic, half-open raster indexing, DSM window translation, nodata handling and raster decoding remain unchanged outside GEOS. Metadata filters, time/knowledge roles, graph traversal, qualification documents and envelope assembly have no intrinsic GEOS dependency.

GEOS uses planar operations and finite-precision coordinates; this experiment does not establish geodetic geometry or universal exact arithmetic. The profile's projected core and existing transformations remain the boundary. Representable one-ULP slivers are tested without an added tolerance. Future transformed/intersection coordinates must not be assumed to lie on theoretical boundaries merely because a drawing suggests it. [GEOS spatial model and robustness FAQ](https://libgeos.org/usage/faq/), checked 10 October 2026.

## Binding ownership, serialisation and scoped integration

`native.py` uses standard-library ctypes and the existing C API. Its context owns readers/writers, callback references and a tokenised geometry registry. A wrapper must match both pointer and allocation token; stale wrappers cannot release a newly allocated geometry at a reused address. Explicit close is idempotent, cross-context arguments are rejected, and use after geometry/context closure raises `GeometryError`. Query arenas release transient results and preserve the 38 feature copies. Prepared geometries and temporary centre points are destroyed in `finally`, including an injected NumPy result-allocation failure; serialised native buffers are freed after copying. The registry tests detect owned-handle leaks in the tested cycles; no native allocator instrumentation or general memory-safety certification is claimed.

Callbacks use the non-variadic message-handler API. They retain at most 16 messages of 4,096 characters each and contain Python exceptions. Native null pointers, scalar failure and predicate return 2 are errors, never scientific empty answers. Invalid geometry is reported without make-valid or precision changes. The transform callback contains errors, returns failure to GEOS and preserves Z. The [re-entrant C-API design](https://libgeos.org/project/rfcs/rfc03/) supports context isolation; the temporary Python substitution is deliberately sequential and has no concurrent-reader/thread-safety claim.

Source features cross the boundary as explicit WKB, not pointers. Byte order, flavour, dimension and SRID settings reproduce this reference version. All 38 retained WKB streams and mappings match exactly. This does not make WKB topology-equivalent representations interchangeable as scientific byte identities, or promise identical output ordering after a kernel upgrade. Source document identities are not recomputed or changed.

`adapter.py` preserves the accepted window/shared snapshot, verification and full scientific query assembly. Opening still uses Shapely for existing validation and one-time feature serialisation; the resulting 38 geometries are copied into the new native context. The original feature objects remain with the accepted owner. Each query temporarily substitutes the reader's Point, Polygon, box, mapping, projected and WorldCover functions and restores them on success or exception. Native GEOS calls handle query geometry and feature predicates; the accepted direct PROJ binding handles horizontal transforms. The accepted reader is never edited. This test-only override is not a production abstraction or parallel-safe API.

During 153 novel queries, guards make the relevant Shapely kernel dispatches and pyproj transformation creation raise if called. All native query envelopes still match. This establishes substitution of those query operations, not removal of Shapely from opening, NumPy from centre arrays, GDAL from raster decoding or Python from orchestration. No frozen IDs, expected answers or request-specific tables enter the binding/adapter.

## Conformance, boundaries and errors

| Comparison | Exact passes | Numerical equivalence used | Unexplained differences / unsupported / unexecuted |
|---|---:|---:|---|
| Boundary point cases | 6 | 0 | 0 in the defined cases |
| WorldCover-style centre-mask points | 6 | 0 | 0 |
| Overlay cases | 7 | 0 | 0 |
| Retained XY/XYZ feature interchange | 38 | 0 | 0 |
| Frozen full-envelope replay, three exact pins | 60 | 0 | 0; nine expected rejections count as passes |
| New full envelopes, 51 queries per pin | 153 | 0 | 0 |
| Adapted unchanged native-window suite | 436 | 0 | 0 |

The **649 native full-envelope comparisons** are 60 frozen + 153 new + 436 existing window comparisons; they are not 649 independent scientific observations. The full result includes publication, evidence/revision identity, source/derived classifications, native support, time/knowledge roles, lineage, rights, uncertainty and complete documents. Historical selection remains explicit. Positive, absent, unsupported and invalid outcomes retain their distinctions.

Primitive polygons and malformed inputs are synthetic kernel diagnostics, not new source observations or registrations. Primitive tests cover interior/exterior boundary, interior-ring boundary, hole interior, multipart component and outside points; positive overlap, edge touch, vertex touch, a representable tiny positive overlap, empty/multipart intersections and core-edge clipping. The unchanged window cases additionally exercise support seams, affine anchors, DSM crop/source-grid offsets, corners, geographic CRS transformations and partially intersecting areas. New queries use deterministic seed `20261011`, 24 arbitrary core points, nine corners/seams, geographic CRS variants, three areas and combined temporal/derived-support, absent identity and unsupported CRS cases.

Empty polygons retain type, zero area, validity, mapping and WKB. A self-intersecting polygon reports invalidity and a notice; its failing intersection raises a native error just as the reference raises a GEOS exception. Malformed/truncated WKB, malformed polygon input, unsupported XYZ query constructors and non-finite coordinates are rejected. Error class/text at the isolated primitive boundary is not a newly frozen public API. Invalid native operations are not converted into empty scientific results.

Ownership tests perform **1,000 creation/release cycles**, double-close, cross-context misuse, arena failure, stale wrappers, pointer-reuse protection, context closure and attempted use after closure. Adapter tests verify restoration after injected exceptions, the 38 retained handles after repeated queries, busy-owner rejection with open pins, subsequent valid querying and rejection of an unavailable generation.

The initial primitive run exposed empty-polygon and MultiPolygon Python container conventions in the adapter. Correcting tuple/list and empty-coordinate presentation made exact mappings agree; coordinates, predicates, source geometry and frozen expectations were unchanged. Final review also found and corrected a prepared-handle cleanup gap on result-buffer allocation failure; an injected MemoryError test confirms destruction and error propagation. There are no remaining observed scientific or numerical discrepancies. Arbitrary invalid polygon recovery, M semantics, other CRS profiles, different GEOS versions and concurrent overrides remain unsupported or untested; no broader capability is advertised.

## Offline consistency and unchanged authority

The accepted shared snapshot still captures verified raster/metadata bytes and owns decoding handles. A scoped native query cannot change those bytes. The unchanged eight-test native-window suite also runs with its query owner substituted: corrupt candidates, altered crop bindings, failed replacement, restart/selection, explicit generation rejection, post-open member replacement/deletion and selected deletion retain their tested outcomes. No incomplete candidate becomes ready and the last compatible ready package survives a failed replacement.

The existing store's child-process restart test still opens the accepted reader. Separately, the new frozen replay starts a fresh process and opens native views for all three pins. These are bounded process tests, not native mobile lifecycle validation or general power-loss/concurrent-writer guarantees. Hashes establish integrity, not a trusted publisher or authentic native DLL origin. Registry ownership and snapshot capture do not protect against arbitrary in-process native corruption. No package bytes, schema, ready-state selection protocol or canonical publication is modified.

## Desktop measurements

[Raw receipts](../../scripts/atlas/portable-spike/native-geos/results.json) contain **18 fresh serial trials**: six primitive and twelve full-reader trials. Storage caches were retained; these are process-cold, not storage-cold. No other benchmark ran concurrently. Initialisation costs are import/context workloads, not equivalent kernel computation: Shapely imports its Python/NumPy interface; direct GEOS loads/hashes existing DLLs and allocates its context.

| Measurement, median across three fresh trials | Shapely reference | Direct native binding |
|---|---:|---:|
| Primitive initialisation | 83.56 ms | 9.85 ms |
| Box + point + covers + destruction, 1,000 repetitions | 0.01830 ms | 0.01930 ms |
| Covers, 1,000 repetitions | 0.00300 ms | 0.00180 ms |
| Intersection + area + result disposal, 500 repetitions | 0.02170 ms | 0.01870 ms |
| WKB writing, 500 repetitions | 0.00450 ms | 0.00360 ms |
| WKB writing + reading roundtrip, 500 repetitions | 0.00670 ms | 0.00710 ms |
| Mapping, 500 repetitions | 0.02090 ms | 0.02540 ms |
| Primitive process peak range | 37.77–38.08 MB | 29.70–29.84 MB |

Primitive operation inputs are small boxes/points, not representative large-overlay throughput. The native roundtrip uses explicit copies; mappings read coordinates through ctypes. Tiny timing differences do not establish a general speed-up. Standalone primitive trials confirm no Shapely, NumPy, pyproj or rasterio runtime imports in the direct path; the DLLs remain required. The integrated WorldCover array path does use NumPy.

| Full-reader measurement | Reference | Native query substitution |
|---|---:|---:|
| One pin complete open median | 1,107.42 ms | 1,138.28 ms |
| Three pins/shared owner complete open median | 1,120.27 ms | 1,152.14 ms |
| One pin process peak range | 320.58–321.24 MB | 320.96–321.18 MB |
| Three-pin process peak range | 320.72–321.04 MB | 320.57–321.40 MB |
| Three-pin after-generation warm point median | 11.98 ms | 9.48 ms |
| Three-pin after-generation warm area median | 16.77 ms | 17.84 ms |
| Three-pin after-generation warm identity median | 1.08 ms | 1.13 ms |
| Three-pin after-generation warm lineage median | 13.89 ms | 14.03 ms |

Full opening includes verification/decoding, explicit views, native context and all 38 WKB copies; module imports precede the timer. Each warm query has an unmeasured warm-up and ten timed repetitions per trial/pin. Representative point is `[2624123.875,1091567.125]`; area is `[2624111.125,1091555.125,2624222.625,1091777.375]`, EPSG:2056. Identity and transitive lineage use accepted records; legacy has no derived graph, so its lineage cost is not the same workload. A large-core WorldCover centre loop can cost more than this small area; the functional suite covers larger areas without claiming this latency for them.

Full-reader peak memory has **no demonstrated reduction**. Native feature copies coexist with reference validation objects and the same captured raster/metadata owner. Working sets are not per-library allocation accounting, and the approximately 321 MB peak cannot be attributed to geometry. Installation storage and accepted recovery costs are unchanged because the package/store are unchanged; this task measures reader/context costs rather than rerunning an installation-performance benchmark. Owned lifecycle fault copies remain under the inherited 512 MiB scratch budget; measured processes remain below 768 MiB. No raster or native binary is committed, and no extra accepted projection is generated.

## Portability, licensing and remaining prerequisites

| Direction | Established here | Remaining evidence |
|---|---|---|
| Windows desktop | Tested GEOS C context, ownership, complete envelope substitution and installed DLL identity | A production host would need an audited binary/resource closure, no test-only global overrides, reviewed trust model and packaging |
| Android native | C API is a credible binding boundary, not a tested Android binary | Authorised ABI/compiler/build access; GEOS/PROJ and database/decoder linkage, notices, ownership/error checks, full conformance and physical-device resource/lifecycle tests |
| iOS native | Same semantic responsibilities can be tested behind another binding | Authorised toolchain/signing/device; linking/relinking and distribution review, native builds, complete conformance and storage/suspension tests |
| Browser/WASM | A C API may be exposed by a separately built compatible kernel | No Emscripten/build or browser binding tested; version, memory/FS/PROJ-resource closure, complete semantics and wrapper licence remain unresolved |

A stable C ABI is a useful implementation boundary, not a guarantee of identical geometry ordering or numerical results across kernels/platforms. A compatible GEOS kernel alone does not supply the CRS database or raster decoder. The accepted PROJ comparison remains separate evidence. There is no final implementation language, shared core, mobile framework, renderer, storage format or web/mobile code-sharing decision.

Installed `LICENSE_GEOS` and [GEOS 3.13.1 COPYING](https://github.com/libgeos/geos/blob/3.13.1/COPYING), checked 10 October 2026, contain LGPL 2.1 terms. Exact linkage, modification, notices, corresponding source/relinking arrangements and signed-store restrictions require a concrete redistribution review. The installed `LICENSE_win32` adds Microsoft runtime conditions; Shapely's own BSD licence does not supersede GEOS or runtime obligations. No legal clearance is asserted. DLL hashes are identification, not permission or authenticity. Scientific source/projection rights and Copernicus modification notices remain as recorded in the [resource rights inventory](atlas-portable-projection-reduction.md) and [window assessment](atlas-native-grid-window.md); the LGPL experiment grants no raster redistribution rights. Meridian's own public package reuse/distribution gate remains unresolved.

## Provisional recommendation

**DECIDE NOW:** the checked GEOS and PROJ C APIs are credible binding boundaries for the demonstrated Windows profile. Require complete envelopes, original/native grids, exact predicates, serialisation/order, explicit failure, rights and historical pins whenever a binding/kernel/resource version changes. Keep the accepted reader as reference.

**PROVISIONAL DIRECTION:** isolate three small responsibilities: horizontal XY transformation with operation/resources; exact query geometry/clipping/predicates; native-grid selection/decoding and verified snapshot ownership. Keep scientific filtering, documents, identities, lineage and time separate. This does not require a universal plugin system. Preparation can validate/export full geometries, immutable qualified documents and native raster descriptors. Arbitrary valid runtime points/areas still require transforms, clipping, coverage and centre predicates; precomputed fixture answers cannot replace them.

**DEFER:** language, production bindings, platform deployment, shared computation, application host, renderer, package/distribution mechanisms and licence clearance. **REJECT:** pointer exchange between kernels, bounds as exact predicates, silent repair, arbitrary tolerances, empty success on native failure, or removal of libraries merely to reduce a dependency count. Revisit on platform build/rights blockers, semantic divergence, measured resource requirements, changed kernel/database or serialisation semantics. F03/F12 gain bounded evidence; F04/F05/F11/F13/F17 remain open for their respective device, architecture and rights decisions.

## Verification and scope

**385 runner tests passed, 0 failed / skipped:** 9 new geometry tests, 8 adapted unchanged window tests, 44 accepted reader/hardening/lifecycle tests, 8 accepted native-window tests, 9 shared-owner tests, 5 preceding PROJ binding tests, 31 authoritative native-reader tests, 12 fixture tests and 259 Atlas runtime/lifecycle/registration/retrieval tests. Primitive-only checks ran before integration. Frozen replays are counted separately: accepted window 60/60, new native geometry 60/60, preceding PROJ comparison 60/60, and authoritative runtime 60/60 with 120 indexed/full comparisons. Nine expected errors pass in each replay. The preceding PROJ tests also preserve 524 coordinate and 220 novel-envelope comparisons; accepted shared tests preserve 159 novel envelopes.

Executed commands: the isolated primitive/query/adapted suite and replay commands in the linked README; `python -B -m unittest discover -s scripts/atlas/portable-spike -p test_*.py -v` and equivalent discovery for `native-window`, `reduction`, `geometry-crs` and `native-geos`; `python -B scripts/atlas/riffelhorn-retrieval/test_query.py`; `node --test scripts/atlas/read-conformance/test-fixtures.mjs`; `node --test runtime/atlas/test-runtime.mjs runtime/atlas/test-lifecycle.mjs runtime/atlas/test-registration.mjs runtime/atlas/test-retrieval.mjs`; and `node scripts/atlas/read-conformance/run.mjs --config EXISTING_LOCAL_CONFIG_JSON`. All Python executions used the existing GIS interpreter, `-B` and explicit external projection paths. The nine new tests, 60 native frozen comparisons, eight adapted window tests and eighteen serial measurement trials were repeated after the allocation-failure cleanup fix; unchanged accepted suites were not needlessly repeated.

`npm.cmd run lint`, `node node_modules/typescript/bin/tsc -b --pretty false` and `node node_modules/vite/bin/vite.js build --config EXISTING_APP_ONLY_CONFIG` passed. The existing external Vite configuration excludes Weather processing/public-data copying and writes to owned scratch. Existing NumPy/Affine deprecation and Vite large-chunk warnings remain. No accepted projection is regenerated: representation/bytes are unchanged, every seal is checked, and all window members match the prior independent regeneration.

**58/58 preservation, scope, receipt, resource and navigation safeguards passed.** The owned, uncommitted preservation checker verifies all **1,186 existing files outside seven append-only navigation notes**, 42 canonical status rows, 113 production SHA256 hashes, source admission, accepted Tryfan/Riffelhorn/Exe evidence and retained world/publication stores, frozen fixture member seals and three pins, twelve retained input fingerprints, both projection identities/member seals, unchanged accepted spike implementations, negative Swiss/AWS reconciliation, exact bounded scope, parsed drivers, path-free receipts, test/resource receipts, new internal links and whitespace. No S7, private access, source acquisition, endpoint, paid resource or unrelated implementation change occurs. The complete code/report/navigation diff is reviewed before commit.

The full Weather/data-materialising build, unrelated UI suites, mobile/emulator/device tests, native Android/iOS/WASM builds, different GEOS engines/versions, storage-cold trials, native allocator instrumentation, parallel overrides, power cuts and hostile in-process mutation were **not run**. There is no security, redistribution or production-readiness certification.

Exact bounded changed-file set: new `docs/research/atlas-native-geometry.md`; new `scripts/atlas/portable-spike/native-geos/README.md`, `native.py`, `adapter.py`, `compare.py`, `test_native.py`, `test_existing.py`, `measure.py`, `results.json`; append-only notes in `README.md`, `runtime/atlas/README.md`, `docs/foundations/summary.md`, `docs/foundations/decisions.md`, `docs/development-log.md`, `docs/research/atlas-research-map.md`, `docs/research/atlas-research-state.md`. Accepted historical reports and all implementations outside that new experiment remain unchanged.

## Exactly one subsequent bounded task — NOT BEGUN

**MERIDIAN ATLAS PORTABILITY CONSOLIDATION AND CROSS-PLATFORM ARCHITECTURE HANDOFF — NOT BEGUN.**

Objective: consolidate accepted portable-contract, projection, hardening, shared snapshot, native-window, PROJ and GEOS binding evidence into a precise handoff for Meridian's dedicated web/mobile architecture and code-sharing study. Starting evidence is the unchanged 60-case/three-pin profile and recorded closure, ownership, resource, rights and platform limitations. Scope: distinguish stable scientific responsibilities from replaceable implementations, identify tested versus untested capabilities and exact build/device/licensing prerequisites, and prepare bounded candidate comparisons without selecting a final framework/shared core. Deliver a concise evidence matrix and architecture-study entry/acceptance gates. Acceptance: no desktop result recast as mobile proof, no inferred rights clearance, no hidden Node/Python/network mandate, no weakened offline/scientific obligations and exactly one bounded future study proposal. Stop after that handoff; no new GIS optimisation, SDK installation, mobile deployment, private audit, UI or production integration. This task has not begun.
