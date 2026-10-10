# Atlas portability consolidation and cross-platform architecture handoff

10 October 2026. Starting checkpoint **e560464c35094742cb523709bf6e553d12d1d009**,
public `gbsamirahmed/project-meridian`, clean `main`, fetched `origin/main`, divergence
0/0. Documentation synthesis only: no new experiment, production interface or revision
of scientific authority.

## 1. Executive conclusion

**Atlas portability evidence is sufficient to proceed to Meridian's dedicated
web/mobile architecture and code-sharing study.** No additional Atlas optimisation
or kernel experiment is a demonstrated prerequisite. The study must address terrain,
offline storage, application composition and the other scientific systems together.
Platform implementation and field validation remain separate gates.

Established here means established within the **retained Windows Riffelhorn profile**:
independent qualified querying, historical pins, complete verified projection closure,
process-interruption recovery, shared captured ownership, conservative DSM windowing
and direct bindings to the same GEOS and PROJ engines. It does not mean a portable
binary, Python-free complete reader, mobile readiness, production shared core,
universal numerical equivalence, legal clearance or power-loss durability.

The [portable read contract](../atlas/portable-read-contract.md) governs semantics;
canonical evidence and immutable filesystem publications remain authoritative.
This handoff is an index and architectural interpretation of primary reports, not a
competing scientific specification. Source code establishes actual implementation.
[Foundations precedence](../foundations/reconciliation.md#documentation-precedence)
preserves historical reports while superseding incompatible planning recommendations.
The new UI is designed from scratch; experimental React/MapLibre code is reference
material. No framework, renderer, language, package format or shared core is chosen.

## 2. Evidence ledger

Each checkpoint is the **completed stage's commit**, rather than the starting commit
printed inside its report. Original classifications are retained. Quantities are
historical observations; no benchmark, scientific replay or external licence recheck
is newly claimed by this synthesis.

The tested host throughout is Windows `10.0.26200`, Intel i7-12700H, approximately
16 GiB RAM; NTFS is explicitly tested in the offline stages. The reader stack is
Python 3.12.6, NumPy 2.5.3, rasterio 1.4.3 / GDAL 3.9.3, Shapely 2.1.2 /
GEOS 3.13.1, pyproj 3.7.2 / PROJ 9.5.1. Node 24.11.0 is used for authority/export
and reference tests, not independent queries. Contract generation also records
SQLite 3.45.3; native geometry checks identify CAPI 1.19.2. These inventories are
not supported-platform declarations.

| Stage / completed checkpoint | Original question and demonstrated result | Profile, guarantees and recorded measurements | Limits, remaining prerequisites and implementation |
|---|---|---|---|
| [Portable read reference](atlas-portable-read.md), `5c93074f9773815111af96f89c3a73fcbb3b526a` | Can authoritative reads establish a platform-neutral semantic target? **REFERENCE CONTRACT AND FIXTURES ESTABLISHED**; reference replay **DEMONSTRATED** | 60 cases / three pins, nine expected errors per replay; three fresh processes, 360 indexed/full comparisons. Complete qualifications/document identities; four fixture files total 2,074,957 B | No independent reader/offline/device result then; finite corpus is not universal support. [Fixtures](../../fixtures/atlas-read/v1/manifest.json), [drivers](../../scripts/atlas/read-conformance/README.md); another implementation must preserve full semantics |
| [Independent projection](atlas-portable-projection.md), `5528dda72acb41f641966d5c269c5a30b6a8562e` | Can an independent selector answer without authority/source/network access? **SEMANTIC PORTABILITY DEMONSTRATED** on desktop | 180 exact comparisons in three isolated processes; 14 novel tests; deterministic 116,692,961 B projection. Pre-hardening open medians 216.93–249.38 ms across pins; process peak 111,267,840 B | No robust installer/post-open policy then; same GIS kernels, finite encoding evidence. [Builder/design](../../scripts/atlas/portable-spike/README.md), [reader](../../scripts/atlas/portable-spike/reader.py); later hardening resolves operational weaknesses, not historical timings |
| [Offline hardening](atlas-portable-projection-hardening.md), `d006e4515794909d2e5ad00d8617aabdb6abbd4e` | Can complete compatible packages become ready while preserving the last ready state? **DESKTOP OFFLINE CONSISTENCY DEMONSTRATED** | 180 frozen comparisons; 44 reader/lifecycle tests. Bounded closure, captured rasters, explicit pins, failed-update preservation, deletion/restart; initial install median 4,223.80 ms. Three independent readers peak 599,416,832 B | Single-writer NTFS/process faults; no power-loss, hostile-writer, authenticity or phone guarantee. [Design](../../scripts/atlas/portable-spike/HARDENING.md), [verifier](../../scripts/atlas/portable-spike/verification.py), [store](../../scripts/atlas/portable-spike/store.py); target custody/durability needs proof |
| [Shared-snapshot reduction](atlas-portable-projection-reduction.md), `ebbc0cc305dc9f31c443d8c2a916da12722bddf4` | Can storage/dependency/memory overhead shrink safely? Overall **PARTIALLY DEMONSTRATED**; single-process shared ownership **DEMONSTRATED** | 180 baseline + 180 shared comparisons, 159 novel envelopes. Three-reader median peak 599,445,504 → 332,742,656 B; package unchanged; twelve-member deterministic regeneration | First-reader memory/all GIS dependencies remain; no cross-process/thread sharing. [Shared owner](../../scripts/atlas/portable-spike/reduction/shared.py), [inventory](../../scripts/atlas/portable-spike/reduction/source-inventory.json); crop was only an estimate then |
| [Native-grid window](atlas-native-grid-window.md), `695b855c1440206f2082db28fe1eefbadba71e54` | Can smaller DSM storage cover **every valid declared-profile request**, beyond fixtures? **DEMONSTRATED** for fixed operation/desktop | Conservative 366-column/full-row strip, bit-exact pixels, original affine/indices/source identity. 180 baseline + 180 window frozen comparisons and 436 novel envelopes; 77,412,208 B package, three shared views median peak 320.32 MB | Real-arithmetic enclosure plus checked machine behaviour, not universal PROJ proof/another region. No dependency removal. [Closure](../../scripts/atlas/portable-spike/native-window/closure.py), [build](../../scripts/atlas/portable-spike/native-window/build.py), [binding/store factories](../../scripts/atlas/portable-spike/native-window/window.py) |
| [Geometry/CRS feasibility](atlas-geometry-crs-feasibility.md), `e7a655cc2f2c9d41381fae71680dc1cf4b2149bd` | Which GIS operations can transfer; can one available alternative preserve semantics? Overall **PARTIALLY DEMONSTRATED**; direct PROJ binding **DEMONSTRATED** on Windows | Same PROJ 9.5.1 horizontal operation/resources: 60 frozen, 524 coordinate-pair and 220 novel-envelope comparisons exact. Whole reader remains about 321 MB | Geometry binding then unresolved; no alternate CRS engine/native build/mobile proof. [Design](../../scripts/atlas/portable-spike/geometry-crs/README.md), [NativeProj](../../scripts/atlas/portable-spike/geometry-crs/native_proj.py); target operation/resource parity required |
| [Native GEOS conformance](atlas-native-geometry.md), `e560464c35094742cb523709bf6e553d12d1d009` | Can owned GEOS C contexts substitute geometry operations? **DEMONSTRATED — Windows binding conformance** | 6 boundary + 6 centre + 7 overlay comparisons; 38 XY/XYZ interchanges; 1,000 release cycles. 649 exact envelopes = 60 frozen + 153 new + 436 adapted window cases. Native three-pin peak 320.57–321.40 MB | Same GEOS, not independent kernel validation. Opening retains Shapely; Python/NumPy/GDAL remain. Sequential override, not production concurrency. [Binding](../../scripts/atlas/portable-spike/native-geos/native.py), [adapter](../../scripts/atlas/portable-spike/native-geos/adapter.py), [commands/receipts](../../scripts/atlas/portable-spike/native-geos/README.md) |

**Scope anchor:** `meridian-atlas-read-contract/v1`, EPSG:2056 core
`[2624000,1091000,2626000,1093000]`, 4 km²; native DTM, DSM, WorldCover,
GeoCover bedrock/unconsolidated, glacier/debris, plus slope/area-ratio scalars.
Whole-world metadata preserves Tryfan references; portable spatial conformance does
not cover Tryfan or Exe. There are 38 full native features and six raster bindings.

| Alias | Exact immutable publication | Records / relationships |
|---|---|---|
| before | `65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd` | 81 / 32 |
| after | `5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289` | 81 / 32 |
| legacy | `7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8` | 49 / 0 |

Capability labels are local: desktop read/lifecycle/binding behaviour above is
**DEMONSTRATED** within its bounds; complete Python-free/cross-platform reader
equivalence is **NOT DEMONSTRATED**; Android/iOS/browser execution, field resource/
lifecycle behaviour and power-loss trials are **NOT INVESTIGATED** by these experiments.
The [mobile prerequisite gate](meridian-mobile-feasibility-gate.md) is inventory,
not device validation. Broader dependency reduction was **PARTIALLY DEMONSTRATED**;
later bindings do not convert it into complete portability.

## 3. Capability and dependency boundaries

These are responsibilities for comparison, **not new production APIs**. Replacing
current reference/spike implementation requires equivalent scientific behaviour,
not inherited Python module structure.

| Responsibility | Stable contract and current implementation | Dependencies, demonstrated portability and unresolved target needs |
|---|---|---|
| A. Identity/provenance | Source, prepared/derived identities; methods/parameters, qualifications, rights, revisions and publication membership. Canonical files/root remain authority; projection copies records/documents | Node authority exports to independent Python documents/identity encoder. Desktop semantic transfer proven; source paths are lineage, not device addresses. Cross-language encoding and rights-complete distribution unresolved |
| B. Query semantics | `retrieve(query)` on explicitly opened pin; conjunction, ordered envelopes/documents/relationships, native time roles, error/unsupported/empty distinctions. Python validation/filtering/graph traversal | Non-spatial selection has no intrinsic GIS requirement; spatial uses C–E. No capability operation/top-level indeterminate/arbitrary algebra in v1. Target reader/transport conformance required |
| C. Coordinate transformation | Always-xy EPSG:2056/4326/CRS84 horizontal transforms; fixed operation/local resources, finite output/error checks; no vertical conversion | pyproj/PROJ, experimental owned C context; exact Windows substitution. Target binaries/resource paths/database/operation versions/arithmetic/errors unresolved |
| D. Geometry | Densified polygons, core clipping, full holes/multipart/XY/XYZ features, boundary covers, positive-area intersection and cell-centre masks; no repair/tolerance | Shapely/GEOS; direct owned query binding demonstrated. Construction/interchange is binding work, predicates need runtime kernel. Target contexts/order/threading/version unresolved |
| E. Raster access | Original grids/affines/dimensions, half-open floor selection, conservative area windows, nodata/exact values, source-index/window translation | rasterio/GDAL TIFF, Affine, NumPy categories, captured MemoryFiles. Window fidelity proven; target decoder subset/resources/array execution unproven |
| F. Offline ownership | Complete sealed compatible closure before ready; installation separate from scientific generation; no fallback; captured answers/fresh-open verification | Python bounded parsing/hashing, directory Store/NTFS replacement, shared leases. Process recovery tested; target APIs/eviction/suspension/permissions/durability/trusted origin unresolved |
| G. Resources | Explicit lifetime/close, bounded allocations/store growth, owner with borrowed historical views, actionable unavailable state | Python/native allocators/caches, OS working set/filesystem. Sharing measured; phone/browser budgets, simultaneous renderer and allocation attribution unresolved |

Successful empty retrieval keeps `physicalAbsenceInferred:false`; unknown time is not
unrestricted time. The generic v1 no-match also covers outside-support queries.
`evidence-epoch` and `product-reference` select native known calendar years or
explicit unknowns, not an inferred current observation date. Knowledge selectors use
registration revisions/accepted UTC instants or unknown knowledge; preparation time,
source release, observation/survey time and Atlas generation remain distinct. Derived
method/execution identity does not supply missing physical time.
Eight frozen rejections use `query-invalid`; the missing lineage seed uses
`relationship-missing`. Do not redesign scientific expectations into finer application
error categories without reviewed contract work. Native failures and corrupt/unavailable/
incompatible packages never become empty success. A prepared source `revision` may
stay constant through knowledge correction: qualified identity also needs the pin,
qualification and knowledge references.

## 4. Component portability matrix

**A — SHARED IMPLEMENTATION CANDIDATE:** same source logic might run on multiple
platforms after host/language evidence. **B — SHARED CONTRACT, PLATFORM-SPECIFIC
IMPLEMENTATION:** equivalent semantics, potentially different bindings/readers.
**C — PLATFORM-SPECIFIC CAPABILITY:** materially OS/runtime-dependent.
**D — CURRENTLY UNSUPPORTED OR UNRESOLVED:** insufficient implementation evidence.
Provisional categories, not tested platform support. Confidence concerns the boundary,
not confidence that a phone implementation works.

| Component / category | Evidence, conformance obligation and principal risk | Confidence / evidence changing classification |
|---|---|---|
| Identity/documents/metadata filters — A | Independent selection/assembly preserves records. Need exact IDs, time/unknown semantics, arrays/envelopes; numeric/Unicode encoders may differ | Medium; cross-language conformance may support direct sharing or require B |
| Lineage/pin-bound query state — A | Explicit graphs/history, no intrinsic GIS. Need revisions/traversal ordering/missing-seed errors; no implicit pin change | Medium; selected language/worker model and reader lifetime |
| Affine indexing/window translation/category counts — A | Small arithmetic/iteration separate from decoding. Need floor/ceil/half-open edges/indices/centre masks; masks still use B geometry | Medium; target arithmetic/endianness and seam/anchor tests |
| Horizontal transformation — B | Direct PROJ same-resource parity. Need axis/operation/database/errors; C ABI is not portable computation | High boundary, low deployment; target builds and boundary/envelope replay |
| Geometry operations — B | Owned GEOS/WKB parity; exact predicates/order, no opaque pointer exchange or precision fixes | High boundary, low deployment; target version/serialisation/ownership/concurrency tests |
| Raster decoder — B | GDAL handles finite TIFF subset. Need header/pixel/nodata identity; smaller decoder cannot be assumed equivalent | Medium; target decoder closure, corruption and complete-profile comparison |
| Bounded closure verification — A | Hash/schema/document/member/graph checks are ordinary computation. Reject malformed/incomplete content, bound allocation; authenticity separate | Medium; equivalent parser/hash/identity behaviour and resource measurements |
| Snapshot/lease ownership — B | One captured owner stable across three pins/path mutation. Need consistency/close/reopen; zero-copy custody unproved | Medium; target handles/memory strategy and mutation tests |
| Installation/selection/deletion — C | NTFS commit boundaries/no fallback; preserve last ready and exact scientific pins | High; target recovery may allow shared orchestration, not assumed OS guarantees |
| Resource loading/scheduling/quotas — C | Library paths/lifecycle/limits differ. Need availability/cancellation/lifetimes and no hidden network | High; named-target measurements and actual host restrictions |
| Complete Python-free/mobile/browser reader — D | No complete target implementation/build; bindings leave decoding/open validation/orchestration intact | High that unresolved; complete build/conformance/rights/device evidence |

Requirements below are **expected work, not demonstrated capabilities**. Groups refer
to rows above; no candidate framework is favoured.

| Group | Desktop | Android | iOS | Browser |
|---|---|---|---|---|
| A semantic logic/verification | Supported authority/reference; deliberate deployable encoder/language | Host/language and validated local references | Same plus build/distribution access | Browser-safe module/worker, local documents; no Node filesystem assumptions |
| B CRS/geometry | Installed Windows kernels tested; other desktops untested | Compatible ABI/compiler, resources/notices/callbacks/full replay | Linking/signing/relinking review, native contexts/resources/replay | Tested WASM or conforming alternative plus resources; no demonstrated build |
| B raster/snapshot | Captured MemoryFiles reference; explicit close | Decoder/memory ownership and storage mutation policy | Same under OS lifecycle/storage behaviour | Decoder and bounded worker/WASM heaps; no native DLL assumption |
| C store/resources | Owned single-writer NTFS process model | App storage/quota/permissions, termination/update/delete/recovery | Container/download/suspension/recovery tests | Selected persistence/quota/eviction/restart proof; caches never imply ready |
| D complete deployment | Python host usable; production distribution unresolved | Build/device prerequisites outstanding | Build/signing/device prerequisites outstanding | Complete execution/offline closure unresolved |

Source-code portability, binary portability, shared interfaces and equivalent scientific
behaviour are separate claims. A C API suggests a reusable kernel **source/build
boundary**, not Windows binaries everywhere or a mandatory shared core. A documented
WASM wrapper is not Meridian browser conformance evidence.

## 5. GEOS and PROJ consolidation

Treat established kernels as **credible provisional native boundaries**, with
replaceable bindings. This is the best evidenced boundary today, not a ranked
cross-platform architecture or proof that other kernels cannot conform.

PROJ comparison replaces horizontal transformation access, normalises axes, disables
network and checks the fixed operation/resources. It preserves complete envelopes
using the same PROJ 9.5.1 engine. The native-window enclosure is tied to that operation;
changing `proj.db`, available grids, kernel/build or axis policy needs review, not
merely successful loading. No elevation/datum transformation is proved.

GEOS comparison owns a separate re-entrant context, callbacks and allocation registry;
features cross as WKB, never Shapely pointers. It preserves all 38 XY/XYZ mappings/
streams, boundary-inclusive covers and positive-area semantics. Empty, invalid and
failing operations remain distinct. Z survives interchange; planar XY predicates do
not establish 3D topology. Exact WKB/order agreement concerns checked settings/version:
topological equivalence does not guarantee scientific document-byte identity after
another build. Opening still uses Shapely validation/interchange; sequential temporary
overrides are test mechanisms, not a production concurrency interface.

Target evidence must cover native compilation/ABI, Android runtime compatibility,
iOS linking/signing/distribution, browser/WASM exports/heaps, complete binary/resource
closure, contexts/callbacks/ownership/error translation, threading/cancellation,
version/database changes and numerical boundaries. Native failure is not a scientific
no-match. No build or new binding occurs here. [Dated primary documentation/licences](atlas-geometry-crs-feasibility.md)
and [GEOS ownership evidence](atlas-native-geometry.md) retain their review dates.

GEOS LGPL 2.1 obligations need concrete linkage, notices, source/relinking and
signed-store assessment; Microsoft runtime conditions also apply to the tested DLL
closure. PROJ's permissive code terms do not clear dependencies/resources or scientific
data. Wrappers may impose different terms. Hashes and parity neither authenticate
distributed kernels nor grant redistribution permission.

## 6. Raster and offline portability

The finite raster requirement is six single-band GeoTIFF bindings: four complete
Swiss 2000 × 2000 float32 DTM tiles with LZW/nodata -9999; Copernicus float32 DSM
with DEFLATE/predictor 3, Point registration and no declared nodata; WorldCover
218 × 312 uint8/LZW subset with code 0 explicitly no observation. Preserve affine/
CRS, native headers, original grids and provider vertical lineage. Swiss LN02 and DSM
EGM2008 are not fused; accepted unknown scalar unit is not inferred from context.

Runtime points read one original-grid cell; height areas return conservative source
support/windows, **not height aggregation**. WorldCover areas read categorical windows
and select exact covered cell centres, not physical fractions. Derived consumed-cell
support is discrete. Headers cannot replace point values or counts. Source overviews/
full terrain pyramids are not read requirements; query projection is not render package.

The [native-window closure](atlas-native-grid-window.md#scientific-closure-over-every-supported-query)
clips transformed/densified queries to the entire core before native selection,
including oversized partially intersecting areas. Conservative stored window:
`[column=2554,row=0,width=366,height=3600]`, **not** the unproved 94 × 66 estimate.
All original rows survive; absoluteColumn = localColumn + 2554. Original source hash/
dimensions/affine are distinct from cropped storage identity. Unexpected selection
outside the strip is integrity failure. The enclosure is operation/profile-specific,
not general Swiss/global support.

GDAL currently supplies TIFF decoding/headers and MemoryFiles; NumPy arrays/counts;
Python orchestration/parsing/filtering. These are implementations, not scientific
requirements for those libraries/languages. A smaller existing decoder or lossless
representation **could** be assessed after the wider study identifies a concrete
target dependency/resource blocker. It needs all required codecs, exact values/
endianness/nodata/affine behaviour, bounded parsing and complete-profile conformance,
not only 60-case matching. No decoder experiment is prerequisite to architectural
comparison and none begins here.

Verification and ownership are separate: readers capture sealed bytes and hold
decoding/geometry/documents; the store stages full copies, verifies, renames,
reverifies and replaces a ready record. Selection is another commit. Receipt alone
cannot replace verification on reopen. Failed candidate preserves last compatible
selection; exact scientific generations never fall back. Deletion clears selection
but does not erase a held snapshot's RAM; close releases its buffers.

These are portable **contracts**; NTFS replacement/fsync, app containers, browser
eviction, background transfers, quota and suspension need platform evidence. Process
interruption is not power-loss durability. One-time hashes do not protect future
mutable reads; zero-copy/mmap/shared memory would need a tested custody policy.
Sharing is single-process with explicit leases, not cross-process/parallel-safe.
Trusted publisher, hostile concurrent writers and runtime-library mutation are outside
proved protection. Incidental cache never constitutes complete offline readiness.

Rights remain as reviewed **9–10 October 2026** in the accepted
[source register](atlas-portable-projection-reduction.md#source-by-source-rights-and-redistribution-register)
and [crop notice assessment](atlas-native-grid-window.md#scientific-rights-and-portability-assessment):
swisstopo OGD credits, WorldCover/GLAMOS CC BY 4.0 basis, Copernicus GLO30-F adapted
credit/downstream notices and non-endorsement. Exact assembly, licence acceptance and
end-user redistribution remain unresolved. Meridian's portfolio-review-only public
code needs deliberate distribution terms. Internal research is not blanket offline
clearance. No raster, native binary or licence file is published/changed here.

## 7. Resource and performance summary

Numbers below are **accepted measurements**, not new trials. Their raw receipt links
and reproducible experiment commands are retained in each primary report. Decimal MB
and binary MiB remain distinct. Complete-query/import/verification/view/context timer boundaries
differ; preserve each experiment's comparison rather than combine claimed speed-ups.

| Accepted experiment | Storage / working set | Opening / operation context |
|---|---|---|
| [Original projection](atlas-portable-projection.md) | 116,692,961 B; six rasters 108,207,242 B, DSM 42,594,792 B | Initial independent reader preceded captured-byte policy; 111,267,840 B peak and ~217–249 ms opens are not equivalent hardened workloads |
| [Hardening](atlas-portable-projection-hardening.md) | Same package; three independent snapshots peak 599,416,832 B; lifecycle peak 407,113,728 B | Initial verification 1,242.70 ms median; install/selection 4,223.80 ms. Capture/full closure increases memory |
| [Shared-owner controlled comparison](atlas-portable-projection-reduction.md) | Three independent median 599,445,504 versus shared 332,742,656 B (44.5% reduction); one reader essentially unchanged | 3,257.72 versus 1,075.91 ms complete open; avoids duplicate captures/validation; package/dependencies unchanged |
| [Window comparison, both shared](atlas-native-grid-window.md) | Original 116,692,961 versus window 77,412,208 B; DSM 42,594,792 versus 3,306,806 B; package −33.66%, DSM −92.24% | Original/window one-pin peaks 333.31/320.37 MB; three-pin 332.87/320.32 MB. Three-pin opens 1,050.40/1,075.18 ms; about 3.8% memory reduction, essentially unchanged opening |
| [Latest GEOS binding, window/shared](atlas-native-geometry.md) | Reference three-pin peak 320.72–321.04 MB; native 320.57–321.40 MB; **no full-reader memory reduction** | One-pin opens 1,107.42/1,138.28 ms; three-pin 1,120.27/1,152.14 ms. Native context/38 feature copies included; imports excluded |

Window warm medians (original/window three shared pins): point 32.43/12.46 ms,
area 19.34/17.20 ms, identity 1.15/1.14 ms, lineage 14.82/14.12 ms. Latest GEOS
warm medians (reference/native): point 11.98/9.48 ms, area 16.77/17.84 ms,
identity 1.08/1.13 ms, lineage 13.89/14.03 ms. Workloads/repetitions belong to their
own trials, not a compounded improvement. Legacy empty lineage is not populated
traversal. Process-cold trials retain OS caches; no storage-cold/phone/thermal/battery
inference. Older 9.11 s canonical authority full-open is different work from projection
verification. Three shared views are not three independent processes/readers.

Installation is separate. Hardening measured 350,080,532 B extra scratch peak in
instrumented replacement/candidate trials. Window trials measured original install
4,822.08 ms versus window replacement 4,611.13 ms median: different states preclude
universal improvement claims. Window stage 546.87 ms, candidate verify 1,467.40 ms,
final verify 1,260.11 ms; fresh-process reopen 1,717.59 ms; injected failed-stage
cleanup/reopen 1,319.78 ms. Ready publication 15.50 ms excludes final verification;
it is not whole installation.

One original ready + one window ready occupies about 194.11 MB; another window stage
adds an **estimated** 77.41 MB. With separate regeneration outputs, conservative
combined scratch maximum was **estimated** about 465.63 MB under 512 MiB. Store growth
separately enforces 512 MiB; process planning limit is 768 MiB. These are experiment
limits, **not mobile budgets**. Window regeneration reproduced all members exactly in
3,227.25 / 3,283.97 ms; no regeneration or installation is performed in this handoff.

Unattributed costs: captured compressed bytes versus decoded arrays/caches, JSON/
envelope copies, verification transients and native allocator retention. No allocation
profiler establishes how much of ~321 MB belongs to GEOS, PROJ or rasters. Order-dependent
import observations (25.12 MB standard-library process to 66.26 MB after NumPy/Shapely/
pyproj/rasterio) are not additive accounting. Installed wheel-directory inventories:
NumPy 53,695,241 B, Shapely 6,365,854 B, pyproj 25,463,599 B, rasterio 69,886,974 B;
exclude distribution metadata and are not minimal shipped/loaded target closure.
GEOS's three inventoried DLL companions total 3,573,384 B, with other system runtime
requirements additional. Direct bindings remove neither kernels nor resources.

Targets must repeat verified opening, simultaneous historical views, representative
large/small queries, renderer+reader memory, install/recovery scratch, quota/deletion/
suspension, thermal/battery tests on named hardware. No resource-reduction task or
mobile budget follows from Windows alone.

## 8. Cross-platform architectural requirements

| Requirement | Classification for the forthcoming study |
|---|---|
| Scientific computation sharing | **Mandatory:** accepted semantics/identity equivalent. **Open:** same implementation, different bindings or independent readers; Python removal is not itself a goal |
| Shared models/contracts | **Mandatory:** exact pins, qualifications/lineage, ordering and unknown/absent/unsupported/errors. **Preferred:** minimal versioned models, not raw SQLite/Node APIs |
| Native bindings | **Mandatory if used:** versions/resources, ownership/errors/serialisation conformance. **Open:** target builds/linkage; no selected shared core |
| Browser execution | **Mandatory:** no Node filesystem/DLL assumption or required workstation for offline field queries. **Open:** browser reader/WASM or another supported route |
| Offline storage | **Mandatory:** explicit completeness/capability boundary, compatible verified ready state, user deletion. **Open:** persistence/eviction/trusted delivery |
| Updates/recovery | **Mandatory:** last-ready preservation, exact pin, explicit failure, compatible restart. **Open:** target commit/durability. **Deferred:** deltas until measured need |
| Runtime memory | **Mandatory:** bounded ownership/close and measured declared-target limits. **Preferred:** share captures when justified. **Open:** budgets/workers/render coexistence |
| Renderer independence | **Mandatory:** rendering is display product, not scientific authority. **Open:** true native 3D/disabled 2D paths, complete offline assets |
| Application state | **Mandatory:** separate scientific pins/render products/camera/selection/Weather issue-valid clocks. **Preferred:** simple replaceable composition/new UI |
| Testing | **Mandatory:** frozen 60 plus novel full-profile boundaries/anchors and lifecycle faults for each claimed reader; no automatic expectation refresh |
| Versioning | **Mandatory:** kernel/resources, contract/profile, package, publication and app versions separate; review changed pipeline/database/encoding/order |
| Redistribution | **Mandatory before distribution:** exact code/data/binary notices, permission and trusted-origin review, local attribution. **Open:** concrete linkage/assembly |
| Small-team maintenance | **Preferred:** smallest proven components, reproducible builds/owners. **Open:** skills/hardware/support. **Deferred:** accounts/routing/providers until relevant gates |

Keep Atlas and Weather scientific lifecycles separate. Guide's future navigation/
planning duties cannot be inferred from Atlas's evidence graph. A minimal map/inspector
consumes qualified results without coupling to reader internals, hierarchy or shared
UI implementation. Location/telemetry is purpose-specific opt-in including third-party
requests. No provider is needed; [F32 economics](../foundations/economics.md) continues
to gate unrestricted exposure and does not approve paid delivery.

## 9. Architecture comparison criteria

Reusable **unranked** framework: compare separate native/web apps, shared logic with
platform UI, cross-platform UI, web-based mobile shells, native scientific libraries,
WASM and independent conforming readers. Use common requirements, named versions and
evidence levels, rather than counting shared lines.

| Criterion | Existing evidence | Evidence needed / decision rule |
|---|---|---|
| Terrain rendering | Retained terrain/visual records; experimental GL JS reference, no native field parity | Exact engine/version, true 3D/genuinely disabled 2D, fixed views/support/encoding; hardware validation later |
| Scientific correctness | Desktop complete envelopes/native-grid closure and same-engine bindings | Candidate complete-profile/adversarial parity; reject qualifier loss, tolerance fixes/bbox-only selection |
| Offline reliability | NTFS ready/recovery and captured ownership | Full evidence/render/style/font/notice closure, interruption/quota/relaunch; partial cache never ready |
| Mobile performance/resources | Desktop quantities only | Named devices, combined render/reader memory, frame distributions, warm inspection, thermal/battery; emulator insufficient |
| Browser compatibility | Experimental web UI, no browser reader | Browser/worker/WASM/persistence matrix, unavailable states and resources |
| Development complexity | Thin tested research boundaries, production host unresolved | Actual language/FFI/build/toolchain/onboarding work; wrappers around one renderer not independent solutions |
| Maintainability/build/release | Contracts and replaceable UI direction | Reproducible target builds, owners, signing/update/support burden and small-team capacity |
| Licensing/distribution | Dated code/data/kernel records; assembly unresolved | Exact included versions/binaries/resources, LGPL/linkage/notices and distribution route; technical success does not waive rights |
| UI redesign/evolution | New interactions required; science separate | State/responsibility boundaries; no inherited React/layout mandate or universal plugin framework |
| Future scientific capabilities | Atlas developed; Weather/Guide separate and less evidenced | Independent contracts/lifecycles/clocks and integration routes; no fabricated portability for unresearched functions |

Record options as repository-tested, target-built, physical-device-tested,
documentation-only, inferred, unsupported or unknown. Separate hard disqualifiers,
cost and reversibility from preferences; agree weights in the study with actual
priorities. Architecture research can shortlist **provisional** paths while missing
hardware tests remain open. Expensive decisions stay conditional on relevant device,
offline and rights gates. Equivalent science need not require identical UI or renderer.

## 10. Unresolved-questions register

A question can **block a final architecture decision** without blocking comparative
research. Legal/access prerequisites do not authorise installation, acquisition or
private access now. Priority is the affected gate, not another Atlas experiment queue.

| ID / gate | Why it matters; evidence and remaining unknown | Resolving evidence; hardware / platform / rights dependencies |
|---|---|---|
| U01 — BLOCKS ARCHITECTURE DECISION | Native true 3D/useful 2D fallback untested; reader does not render terrain | Exact SDK/assets review then device comparisons. Hardware: yes for field claims; shortlist/toolchain first; SDK/asset rights |
| U02 — BLOCKS ARCHITECTURE DECISION | Complete mobile/browser reader route unresolved despite C bindings; decoding/metadata/storage still needed | Next study compares real options; later authorised builds/conformance. Hardware: not for initial semantics, yes for suitability; target shortlist and dependency rights |
| U03 — BLOCKS ARCHITECTURE DECISION | Offline custody/persistence differs by container/browser; NTFS not suspension/quota proof | Candidate API research then lifecycle tests. Hardware: yes for native lifecycle; storage/platform choice first; rights before redistribution |
| U04 — BLOCKS ARCHITECTURE DECISION | Build/signing access/team maintenance capacity unknown; shared UI can conceal native work | Skills/hardware/authorised build-route/workload inventory. Access before tests, no final framework prerequisite; tool/SDK terms |
| U05 — BLOCKS IMPLEMENTATION | Cross-build GEOS/PROJ arithmetic, resource pipeline and serialisation ordering unproved | Target builds, frozen/novel/anchor replay, ownership/error/thread tests. Hardware later for resources; ABI/resources shortlist; kernel/runtime notices |
| U06 — BLOCKS IMPLEMENTATION | GDAL-free decoding/NumPy-free masks unproved and not automatically necessary | Only if host reveals a blocker, compare an existing decoder/representation over complete native profile. Hardware later; target constraints first; codec/data rights |
| U07 — BLOCKS IMPLEMENTATION | Numeric/Unicode identity beyond finite corpus, production cancellation/native errors not generalised | Encoders, malformed-input and lifetime tests without refreshing expectations. Hardware not essential initially; runtime first; code ownership |
| U08 — BLOCKS IMPLEMENTATION | New UI host/package/private state unknown; public hierarchy is not the new design | Interaction research and separately authorised private audit after platform evidence. Hardware for later interaction validation; explicit private permission; ownership terms |
| U09 — BLOCKS BETA OR DISTRIBUTION | Data/code/assembly permissions unresolved: crop notices, signed-store LGPL obligations | Exact shipped rights/notices/source/relinking review. Hardware: no; concrete linkage/distribution first; rights review: yes |
| U10 — BLOCKS BETA OR DISTRIBUTION | Hashes do not authenticate publisher/runtime; trust/update delivery absent | Trusted origin/key/dependency inventory, bounded parser/security/recovery review. Hardware for host tests; delivery scope first; permissions |
| U11 — BLOCKS BETA OR DISTRIBUTION | Supported resources, offline assets/upgrade recovery unknown; ~321 MB excludes combined renderer workload | Named-device memory/storage/thermal/battery/termination/upgrade trials. Hardware: yes; build/package scope first; lawful assets |
| U12 — BLOCKS BETA OR DISTRIBUTION | Privacy, operating exposure/budget and support still gates, not solved by conformance | Actual flow and F17/F18/F19/F31/F32 reviews before invitations/exposure. Hardware as relevant; delivery scope first; rights/privacy review |
| U13 — CAN BE DEFERRED | Cross-process/mmap sharing, minimum crop, deltas/global scale/general CRS outside need | Only measured workload/custody/version issue justifies reconsideration. Hardware/target/rights depend on change; no prerequisite optimisation |
| U14 — CAN BE DEFERRED | Weather/Guide full foundations/shared execution not established by Atlas | Separate scientific programmes; consider boundaries in whole-system study, not Weather R&D here. Build/device/rights evidence when relevant |

No item demonstrates a need for another Atlas experiment before the architecture
study. U01–U04 are study inputs; U05–U12 prevent unsupported implementation/distribution
claims. U06 blocks only a proposed dependency-removal implementation, not continued
use of an available conforming decoder. Complete power-loss durability is unproved:
future guarantees must be scoped/tested, not an abstract universal precondition for
architectural research. Weather research can start early in parallel when separately
authorised; deferring its complete implementation does not defer all scientific work.

## 11. Readiness, authority and verification

**Established for this research phase:** faithful read projection without live
source/authority/network; three explicit historical pins; qualified semantics and
whole declared-core closure through tested representation/ownership variants; verified
process-level recovery; credible owned Windows GEOS/PROJ C binding boundaries.

**Provisional:** projection schemas/layouts, Python reader, captured-memory strategy,
NTFS store, target builds/libraries and A/B/C classifications. **Explicitly unsupported
or unproved:** complete production native reader, other-platform conformance, arbitrary
CRS/vertical conversion, Tryfan/Exe portable spatial profiles, full rendering/offline map
closure, navigation/safety suitability, hostile multi-writer/general power-loss guarantees,
mobile resources and redistribution clearance. Swiss/AWS reconciliation remains negative.

Canonical scientific records/contracts/publications and accepted research retain
subject-specific authority; this handoff adds engineering interpretation and sequencing.
It closes neither the 42 canonical research statuses nor Foundations decision-row
statuses. F03/F12 gain bounded semantic/native-binding evidence, F05 desktop lifecycle;
F04/F11/F16 need terrain/platform evidence, F07/F17 rights review, F13 sharing choice.
Earlier next-task paragraphs are historical, superseded by section 12 for sequencing,
not erased. The unchanged [prototype plan](meridian-prototype-architecture.md) is read
through Foundations reconciliation; accepted readiness is not beta/device readiness.

Documentation-only verification: primary reports/contract, relevant Foundations and
actual query/verifier/store/binding code inspected; numbers/classifications, checkpoint
ancestors, paths and links/anchors checked. Recheck append-only notes, decision rows,
whitespace, frozen fixture seals/pins, retained source/store hashes, original/window
seals, 42 statuses, 113 hashes and all tracked files outside navigation against the
captured start. The dated development entry records actual check results. No generated
package, binary, personal locator, dependency, canonical write or private access.

Scientific replay, executable regression suites, lint, types and builds are **not
rerun**: code/data/dependencies/fixtures/contracts unchanged. [Engineering's documentation-only
rule](../foundations/engineering.md#testing-responsibilities) calls for links/scope/
preservation rather than expensive unrelated suites. Historical counts are accepted
evidence, not new passes. No full Weather/data-materialising build, projection or
scientific experiment runs.

## 12. Recommended next stage — NOT BEGUN

Exactly one subsequent bounded task:
**MERIDIAN WEB/MOBILE ARCHITECTURE AND CODE-SHARING FEASIBILITY STUDY — NOT BEGUN.**

**Objective:** compare Meridian as a whole: directly shared implementations, equivalent
platform implementations and materially platform-specific/unavailable capabilities.
No final framework choice from documentation or desktop parity alone.

**Starting evidence:** this ledger/matrix/questions; Foundations and reconciled prototype;
public Atlas/Weather implementations and Guide requirements; retained terrain/support;
frozen conformance and unresolved device/build gate.

**Scope:** bounded architectural research covering Atlas, Weather, Guide, terrain,
offline storage/recovery, resource ownership, application state and UI composition.
Compare separate native/web, shared logic/platform UI, cross-platform UI and web shells;
separate scientific contracts/computation from rendering/device services. Reassess
shortlists without inheriting the experimental hierarchy. Distinguish documentation,
build evidence and physical validation; record prerequisites/resources for later tests.
No private access, production implementation, final framework, new GIS optimisation,
acquisition, paid/cloud resource, Weather R&D or physical-device experiment is begun
under this handoff.

**Deliverables:** whole-system sharing/coupling matrix, evidence-led candidate comparison,
explicit platform/rights/build/device gates, provisional shortlist, bounded physical-device
validation plan and reconciliation of earlier planning. Keep the first map simple and
scientific systems independently extensible.

**Acceptance:** section 8 constraints/section 9 criteria addressed; Atlas semantics/offline
obligations retained; Weather issue/valid lifecycle and Guide future responsibilities
honest; maintenance/licence/resource costs visible; source/binary/semantic sharing distinct;
no final framework unsupported by evidence; exactly one justified next bounded task.

**Stop:** defensible provisional direction with tests assigned, or precise blocker;
no implementation, private restructuring or field validation during architectural research.

Dependency-informed priorities: essential Atlas research (now sufficiently consolidated),
wider architecture study, physical-device terrain/offline feasibility, provisional
platform/shared-component decisions, separately authorised repository reconciliation,
then minimal adaptable application foundation and Atlas/verified offline integration.
Develop substantial Weather scientific foundations as an **early parallel programme**,
integrating verified capabilities incrementally; develop Guide/route planning under
separate evidence/safety gates; progress through alpha/private beta by readiness.
This is not a requirement to finish every workstream before starting another.
Weather **research timing** is distinct from F20's user-facing integration milestone
after Atlas. The sequence refines historical feasibility/private-audit planning,
without changing scientific results, maturity/financial gates or authorising next work.
