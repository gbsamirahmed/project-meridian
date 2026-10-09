# Atlas offline projection portability and resource-reduction study

9 October 2026. Starting checkpoint `d006e4515794909d2e5ad00d8617aabdb6abbd4e`.
Public `gbsamirahmed/project-meridian`, clean main/origin/main; fetched alignment 0/0.

## Result and boundary

**PARTIALLY DEMONSTRATED.** One explicit captured snapshot can serve all three exact
historical pins with complete unchanged scientific results. Median three-reader peak
working set fell from 599,445,504 to 332,742,656 bytes (44.5%); a single reader
has essentially the same footprint. Package storage remains **116,692,961 bytes**,
and all GIS dependencies remain. Storage reduction and mobile suitability are unproven.

All 60 unchanged cases passed in each of three isolated processes for each mode:
**180 baseline + 180 shared comparisons**, including expected rejections. Another
**159 novel complete-envelope comparisons** and **188 automated tests** passed.
The unchanged authority replay passed 60 cases / 120 indexed/full comparisons.
No fixture expectations, package members or accepted source/publication identities changed.

This is a bounded Windows desktop experiment. The canonical Atlas files, scientific
contracts, retained publications, negative Swiss/AWS reconciliation and frozen v1
expectations remain authoritative and unchanged. No mobile, renderer, production
installer, private repository, new geographical source or distribution deployment.
The earlier [semantic spike](atlas-portable-projection.md) and
[offline hardening](atlas-portable-projection-hardening.md) remain accepted baselines.

Read the committed Foundations summary, decisions, engineering, platform/evolution,
economics and roadmap; [read contract](../atlas/portable-read-contract.md), reference
report/fixtures and the existing builder, reader, verification, store, isolation,
tests and measurements. The [frozen experiment design](../../scripts/atlas/portable-spike/reduction/README.md)
preceded implementation. The initial approval-review command was not executed when
account usage prevented review; after the user's continuation, normal approval and
the exact unchanged gate succeeded. No bypass or unrelated reconciliation occurred.

## Scientific closure and source inventory

Projection identity remains
`a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c`;
12 members, **116,692,961 bytes**, including **108,207,242 raster bytes**.
Preparation remains
`357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb`.
The compact [source inventory](../../scripts/atlas/portable-spike/reduction/source-inventory.json)
is a reproducible diagnostic record, not a new scientific artefact. It records each
full identity, byte seal, provider/product/source locator, preparation revision,
rights document/reference, native shape/dtype/affine/nodata/CRS, vertical/time
qualification, compression, blocks and overview levels. The
[inventory driver](../../scripts/atlas/portable-spike/reduction/inventory.py) verifies
all original members and pins before recording headers; no pixels are transformed.

| Label / source-native member SHA256 | Bytes | Native shape (rows × columns), footprint | Grid / role / datum |
|---|---:|---|---|
| D01 `c68c305e4a142da416b46b555a80916ecc52f8fa50bf1efd5cd2c3f24f9cd4bc` | 16,490,312 | 2000 × 2000; [2624000,1091000,2625000,1092000] | swissALTI3D2024 DTM; 0.5 m; EPSG:2056; LN02/EPSG:5728 provider lineage |
| D02 `9fa4a4391e2e1bfd650f2f31c7d38ed9a5a94494a967011468e6c44559bbcb2c` | 16,862,345 | 2000 × 2000; [2624000,1092000,2625000,1093000] | Same product/grid/datum, separate source tile |
| D03 `0d2ebc6d0b4fd06ab2191cbf2a2f5ab77728249fa8c835075040bce4dc4899de` | 15,925,644 | 2000 × 2000; [2625000,1091000,2626000,1092000] | Same product/grid/datum, separate source tile |
| D04 `4dffaad9efb82d3bf327a86b4f82d55762165ea5f825c386c23380a9320ff875` | 16,329,103 | 2000 × 2000; [2625000,1092000,2626000,1093000] | Same product/grid/datum, separate source tile |
| C01 `638c155dd9a5f0b7ee818146def740093da33cee4606071b2bbf7ce3fa00ab95` | 42,594,792 | 3600 × 3600; [6.9998611111111115,45.00013888888889,7.9998611111111115,46.00013888888889] | Copernicus GLO30-F distribution2021 DSM; 1/3600°; EPSG:4326; EGM2008/EPSG:3855 provider lineage |
| W01 `86579f0b5f87e9c50e499c3ab0752b39357fe7379ab227a11c31c2dee1e676ee` | 5,046 | 218 × 312; [7.74825,45.97,7.774249999999999,45.988166666666665] | ESA WorldCover2021v200 native categorical subset; 1/12000°; EPSG:4326; no height datum |

Evidence identities are `dtm:`, `dsm:` or `worldcover:` followed by these hashes.
Member filenames are the hash plus `.tif`; these bindings are not physical-world
identity or local drive paths. All height bands are float32; WorldCover is uint8.
DTM nodata is -9999, DSM has no declared nodata, WorldCover nodata is 0, with its
explicit no-observation claim retained. No missing data is interpreted as absence.

DTM affine coefficients are `(0.5,0,x_origin,0,-0.5,y_origin)`, with north-west
origins (2624000,1092000), (2624000,1093000), (2625000,1092000),
(2625000,1093000) respectively. C01's affine is
`(1/3600,0,6.9998611111111115,0,-1/3600,46.00013888888889)`;
`AREA_OR_POINT=Point` and the retained half-post registration remain unchanged.
W01's affine is `(1/12000,0,7.74825,0,-1/12000,45.988166666666665)`.
Its original parent window is `[20979,24142,312,218]` on a 36000 × 36000 grid,
origin (6,48). Query indices refer to the accepted prepared subset; parent indexing
is separate lineage. The whole parent byte hash remains unknown.

### Required support versus physical payload

The supported profile is the entire EPSG:2056 core
`[2624000,1091000,2626000,1093000]`, not a collection of the 60 request coordinates.
Each DTM tile's whole native footprint is required: their four interiors partition
the core and new valid point requests may address every cell. These LZW tiles are
already compressed; cropping around known queries would discard supported evidence.
W01 is already a 5 KB LZW native subset spanning the transformed core envelope.
Its cell-centre counts and nodata classification still require native pixels.

C01 is a DEFLATE floating-predictor COG with a much larger full source footprint.
A 128-segment densified core-envelope transformation yields an **inventory estimate**
`[column=2694,row=43,width=94,height=66]`, 6,204 cells / 24,816 uncompressed
float32 bytes. It is not an implemented crop or proof of every transformed-query
extremum/boundary. A future crop needs justified conservative support, margins,
original affine/dimensions/absolute row-column descriptors and a separate stored-grid
origin. Source scientific identity must retain the original full-tile hash. Do not
claim that a cropped local hash is that source's byte identity.

Point height queries read the selected native pixel. Height-area queries return
conservative absolute native window/support descriptors **without reading height
pixels or aggregating them**; such descriptors need source-grid metadata even if
physical pixel payload is smaller. WorldCover point/area operations need native
codes, with exact transformed polygon and cell-centre coverage. Boundary selection
is half-open floor indexing, not nearest-neighbour interpolation; vectors use covers
for points and positive-area intersection for areas. No datum conversion or fusion.

### Other required and optional components

Full `features.json` is **5,386,941 bytes**, 38 geometries: 23 bedrock, eight
unconsolidated, one glacier and six debris features. They extend beyond the core;
no bounding-box approximation, geometry clipping or vertex simplification is used.
WorldCover semantic claims occupy 8,798 bytes; all 12 codes including 0 remain.
Three generation documents retain complete unfiltered populations, qualified
references, regional knowledge, source/preparation/derived method/parameter lineage
and scalar anchor/consumed-cell selectors. Remaining metadata including manifest
and geometry is **8,485,719 bytes**. The first two pins have 81 records/32 explicit
relationships each; legacy has 49 records/no runtime derived relationships.

Exact pins remain before `65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd`,
after `5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289`,
legacy `7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8`.
Unknown knowledge in legacy, original source years, product years and derived unknown
years stay separate. A knowledge correction does not imply physical change.

The original GLAMOS ZIP, original API response files, full WorldCover parent,
rendering DEM pyramid, imagery and research PDFs are not read dependencies of this
projection; source provenance and selected full geometries/definitions remain.
They are archival/processing or other-capability material, not resources a reader
may silently reopen. Removing *references* to them would lose lineage. Removing
any of the six present rasters without an alternative native payload would lose
valid point/category operations; raster headers alone cannot answer heights.

## Reduction alternatives

| Approach | Storage / memory | Fidelity and consistency | Complexity, dependencies and rights |
|---|---|---|---|
| A — full rasters, one shared verified captured snapshot | Package unchanged; avoids duplicate buffers/metadata per pin within one process | Entire existing profile retained; no path rereads after capture | Small explicit ownership layer; same GIS stack/not a mobile runtime. Selected experiment |
| A — reopen verified file paths or mmap mutable files | May reduce resident copies; package unchanged | Initial hash alone cannot protect future writes/replacement; safe handles do not prevent writes through other handles | OS ownership/share-mode/immutable custody proof needed; not implemented, no tamper guarantee claimed |
| B — native DSM window, whole Swiss tiles and W01 | Large potential DSM-byte reduction; full four DTM footprints still required | Must preserve source-grid indices, descriptor windows, nodata/datum/time and conservative core closure for novel requests | New experimental schema/bindings and store validation needed. Promising, not demonstrated; modified-source notices needed |
| C — lossless source-derived arrays or recompressed windows | Potential compression and simpler raster access; actual saving unknown | Bit-exact values/grid/masks required; no quantisation, resampling or invented coverage | Codec, bounded allocation, float/endianness and source-grid proof; may remove GDAL raster decoding, not automatically GEOS/PROJ. Not implemented |
| C — support descriptors only | Very small | Sufficient for height-area descriptors; insufficient for point heights and WorldCover counts | Could only advertise a narrower profile; rejected as replacement for current profile |
| D — separate optional originals from query essentials | Already avoids original ZIP/parent/imagery/pyramid | Retain selected geometry, all qualifications and source references | Already applied by baseline; no extra saving measured. Rights attach to extracts as well as originals |

Compression ratios, crop bytes, phone memory and install improvements are not
manufactured from these alternatives. One experiment is enough to establish the
memory opportunity; introducing a new crop format and installer here would combine
independent uncertainties. Neither the finite corpus nor a bounded footprint estimate
justifies source-grid replacement by itself.

## Implemented ownership variant and offline guarantees

`shared-snapshot-experiment/v1` is a **code experiment version**, not a new projection
schema. No member or scientific closure changes, so the exact v1 identity remains.
[SharedProjection](../../scripts/atlas/portable-spike/reduction/shared.py) opens the
unchanged bounded `Snapshot`, verifies all pins and captures raster bytes once.
`pin(exact_generation)` creates a borrowed view using every unchanged independent
`Reader` predicate/assembly method. Only view construction and close differ. The
variant is not a newly independent scientific implementation; it reuses the accepted
independent Python reader, not the Node/Python Atlas authority.

View close releases its lease only. Owner close with active views fails explicitly;
closing one historical view cannot invalidate another. After all views close,
owner close releases MemoryFiles. Returned answers remain copies. No global cache,
automatic pin choice, cross-process sharing or filesystem-backed scientific reread.
Trusted sequential in-process callers are the bound; internal Python attributes
are not a hostile-code security boundary, and thread-safe closing is not claimed.

`from_store` checks the existing Store's exact receipt/selection, then fully opens a
new verified snapshot. Staging/ready/selection and replacement/deletion use unchanged
baseline code. Installation identity stays separate from scientific pin. Fresh owners
never reuse old snapshots to conceal new disk corruption. Held views remain stable
after package replacement, metadata corruption and deletion; fresh opens reject those
files. Failed updates preserve the selected ready package; no unready stage is queried.
An old captured snapshot can remain queryable after user deletion until its owner is
closed; deletion is not a promise to erase already-held RAM.

Process restart/termination and injected ENOSPC are tested on owned scratch. NTFS
pointer replacement is not general power-loss durability; hostile concurrent writers,
shared-memory between processes, machine power cuts, network filesystems, publisher
authenticity and mobile lifecycle remain unproven. No installer logic is duplicated.

## Resource measurements and methodology

[Versioned measurements](../../scripts/atlas/portable-spike/reduction/results.json)
record three fresh processes per mode/count, 15 warm repetitions per predicate/pin,
with all requested readers kept open. This is process-cold, **not storage-cold**:
OS caches were retained; no other test suite was run concurrently. Windows process
PeakWorkingSet includes interpreter, GIS libraries, verification allocations and
queries, not just raster bytes. Min–max is between three trials; query tables use
medians of each trial's median. No universal performance guarantee or phone inference.

| Mode / simultaneously open pins | Complete open median (min–max), ms | Peak working set median (min–max), bytes |
|---|---:|---:|
| baseline / 1 | 1049.81 (1045.81–1050.65) | 332,210,176 (332,136,448–332,500,992) |
| shared / 1 | 1061.98 (1042.82–1160.49) | 332,775,424 (332,623,872–332,931,072) |
| baseline / 3 | 3257.72 (3234.92–3286.47) | 599,445,504 (599,027,712–599,633,920) |
| shared / 3 | 1075.91 (1071.92–1081.93) | 332,742,656 (332,328,960–332,881,920) |

The three-pin saving removes duplicate snapshots/geometry and verification work;
it does not reduce the first reader's ~332 MB host footprint or share memory between
processes. Warm calls still execute exact predicates and construct complete envelopes.

| After-generation warm query | Baseline three readers median, ms | Shared three views median, ms |
|---|---:|---:|
| nativePoint | 35.139 | 32.603 |
| nativeArea | 18.648 | 17.291 |
| identity | 1.138 | 1.105 |
| lineage | 15.873 | 14.243 |

Point/area coordinates and exact identity are explicit in `measure.py`. Lineage uses
an actual `consumes-qualified-source` seed for before/after, preserving populated
transitive traversal; legacy has no derived edges and returns empty dependants.
An initial empty-seed timing was discarded and the twelve process trials repeated
with this corrected workload. Repeated medians are not evidence for optimising small
query differences. Full per-pin spread is retained in the versioned results.

Unchanged installer, three serial owned-store trials:

| Operation | Median (min–max), ms |
|---|---:|
| Staging | 580.91 (567.21–595.96) |
| Candidate verification | 1307.17 (1200.72–1345.74) |
| Ready record excluding final verification | 15.87 (5.21–16.12) |
| Whole install/selection | 4469.64 (4173.71–4537.30) |
| Shared three-pin reopen and identity reads | 1238.52 (1237.54–1255.85) |
| Fresh interpreter / shared store reopen / identity | 1581.36 (1572.08–1590.08) |
| Injected early stage failure / cleanup / shared reopen | 1197.53 (1179.04–1334.10) |

Lifecycle peak working set was **418,459,648 bytes**, including unchanged
installer verification snapshots. Sharing query owners does not optimise those
transients. Observed owned bytes after the early failed-stage injection were
**116,697,519** each trial (one ready package plus small records/partial stage).
This is not a full replacement peak. The accepted hardening run measured
350,080,532 bytes at its full replacement peak; that historical measurement remains
separate. Three full copies imply about 350 MB and an external fourth candidate about
467 MB before metadata (**estimates**, not new observations). A one-package candidate
needs ~116.7 MB; the unchanged store's 512 MiB owned ceiling remains. No full Swiss
pyramid or new payload was created. Serial regeneration/copies were budgeted before
processing and kept in owned external scratch.

Unchanged builder regeneration took **13.754 seconds**;
all twelve members including manifest reproduced byte-for-byte. Completion Node RSS
was 278,290,432 bytes, not a combined worker peak. The installed
projection identity and member closure are identical, so neither store schema nor
scientific membership is revised. Isolated fresh-process import/open/60-case medians
were 4808.82 ms baseline and
2376.95 ms shared; these include fixture
comparison work and differ from direct-open timings.

## Correctness, failure validation and safeguards

| Executed check | Passed | Failed / skipped |
|---|---:|---:|
| Baseline frozen corpus, three fresh isolated processes | 180 comparisons | 0 / 0 |
| Shared frozen corpus, three fresh isolated processes | 180 comparisons | 0 / 0 |
| Authoritative existing runtime, 60 cases | 120 indexed/full comparisons | 0 / 0 |
| Novel whole-core/shared–baseline complete envelopes | 159 comparisons | 0 / 0 |
| Shared ownership/behaviour/store tests | 9 tests | 0 / 0 |
| Unchanged reader and hardening/lifecycle suite | 44 tests | 0 / 0 |
| Frozen-fixture tests | 12 tests | 0 / 0 |
| Native-reader regression suite | 31 tests | 0 / 0 |
| Atlas runtime regression suite | 92 tests | 0 / 0 |

Expected error outcomes count as passing comparisons (nine per frozen replay), never
skips. Frozen expected documents/arrays/numbers remain exact. Novel cases cover the
whole core's corners/seams/interiors, CRS84 transformations, partial/core areas,
WorldCover masks, conjunctive family/class/time, unknown knowledge and explicit
lineage directions. Independent anchors assert four full 2000 × 2000 windows, a
native seam index, unknown height unit and no physical-absence inference. These are
not frozen coordinate lookups; the unchanged baseline remains the differential
reference, and independent native anchors supplement that shared-implementation limit.

New tests cover one capture/three pins, lease closing, wrong generation/identity,
returned-answer mutation, missing/corrupt/incompatible members, malformed selection,
explicit installed identity, failure/restart/deletion and post-open replacement of a
TIFF, metadata overwrite and removal of the complete owned directory. Captured views
keep their exact answers; fresh owners reject damage. The 44 unchanged tests also
exercise forced child termination around ready/selection boundaries, injected write
failure, invalid closure, corruption and failed different-identity replacement. No
fault targets the original projection, fixtures, canonical evidence or publications.

Executed `npm.cmd run lint`,
`node node_modules/typescript/bin/tsc -b --pretty false`, and an app-only Vite build with an
existing external config excluding Weather processing/public-data copying. All passed;
Vite retained its existing large-chunk warning. Python syntax and preservation/link/
scope checks passed: **50/50 safeguards**, including all 42 canonical status rows,
113 protected production hashes, 1,156 existing non-navigation files, retained
canonical/publication hashes and unchanged Swiss/AWS negative reconciliation.
All seven navigation additions are append-only; added links resolve. The complete
staged diff and whitespace are inspected before commit. No claim that the full Weather/data build,
unrelated full test suite, mobile tests, storage-cold trials, actual disk exhaustion,
power cuts, hostile concurrent writers, thread safety, authenticity or legal release
certification were tested. The installed GIS library stack remains necessary.

## Portability and dependency assessment

Existing host: Intel Core i7-12700H, Windows NT 10.0.26200 (Python identifies Windows 11),
NTFS on C:, about 16 GiB visible memory. Node 24.11.0 is required only for authority
export/reference tests; independent reads require Python 3.12.6, NumPy 2.5.3,
rasterio 1.4.3/GDAL 3.9.3, Shapely 2.1.2/GEOS 3.13.1 and pyproj 3.7.2/PROJ 9.5.1.
The shared variant removes **no dependency**. No software or SDK was installed.

| Dependency | Semantics it currently supplies | Smaller-reader possibility / unresolved proof |
|---|---|---|
| Python/standard library | JSON bounds, canonical identity encoding, predicates, knowledge clocks, lineage and lifecycle | Ordinary portable operations, but Unicode/numeric canonical IDs and schema/error conformance need independent proof; corpus is finite |
| NumPy | Native category counting and cell-centre array construction | Simple iteration/counts possible; same mask, nodata and exact numeric meaning required |
| rasterio/GDAL + TIFF codecs | Native TIFF decoding, MemoryFiles, affine objects/windows/header verification | Explicit native lossless arrays and source-grid descriptors could reduce raster dependencies; no second raster engine or codec implementation here |
| Shapely/GEOS | Polygon intersection/covers, full native geometry and vectorised centre tests | Robust boundary/degenerate geometry behaviour requires an equivalent tested kernel; bounding boxes are insufficient |
| pyproj/PROJ/local database | Always-xy CRS transformations and transformed/densified query geometry | Fixed operations could be investigated; do not assume a simplified Swiss/geographic conversion is equivalent or remove operation metadata |

Installed distribution inventory finds Windows CPython `.pyd` extensions and bundled
DLLs, including GDAL, TIFF, GeoTIFF, LZW/DEFLATE-related codecs, GEOS and multiple
PROJ/SQLite/curl copies; NumPy includes OpenBLAS. A bundled DLL is not proof the query
uses its network feature, database or BLAS operation. The four main package directories
are not a complete deployable-runtime size: sibling `.libs`, Python runtime, PROJ
resources and notices also matter. No browser/phone portability follows from their
presence. Network/child dispatch and original source/authority opens are denied in
fresh isolated conformance trials, while local interpreter/GIS resources remain allowed.

Plausible later directions remain: retain this host-only GIS reference; independently
implement smaller file/array read primitives with an existing conforming geometry/CRS
library; or assess available platform-specific GIS bindings. Share scientific meaning
first. No Rust, WASM, native core, reader language, mobile framework or renderer is
selected; moving Python unchanged to a phone has not been tested.

## Source-by-source rights and redistribution register

Reviewed **9 October 2026**, existing accepted source/preparation records first, then
primary provider pages. This is an evidence register, **not package release clearance**.
Original qualification/rights documents and references are not changed. Permission for
copying data is distinct from publisher authenticity, delivery-service terms and
Meridian code/assembly ownership.

| Members/components | Internal research/local use | Derived projections / crop/lossless change | Original-byte redistribution / end-user offline | Conditions, uncertainty and review gate |
|---|---|---|---|---|
| D01, D02, D03, D04 individually: swissALTI3D2024 | Supported by accepted retention and OGD terms | OGD processing basis; mark Meridian preparation | OGD distribution basis, with source credit; no online-only dependency identified | Mandatory swisstopo reference. Geoservice excessive-use limits differ from local files. Check exact assembly notices before release |
| C01: Copernicus GLO30-F | Free/open licence acceptance required | Article 4 permits modification; adapted notice applies to crops | Distribution grant supports offline copies subject to Article 6 | Full appropriate original/modified credit, downstream liability notice and non-endorsement obligations; no GLO30-R/EEA10 inference. Final notice assembly/legal review outstanding |
| W01: WorldCover2021v200 prepared subset | Accepted native subset; CC BY 4.0 basis | Adaptation/sharing permitted with retained change/credit record | CC BY 4.0 basis; offline is not a separate blanket clearance | ESA/modified Sentinel credit, source/licence link and changed-subset notice. Complete parent hash unknown. No share-alike/non-commercial restriction identified in CC BY 4.0 |
| Full GeoCover features (bedrock/unconsolidated) | Retained API snapshot/local preparation | swisstopo OGD processing basis | Same credit/distribution basis; provider API usage is separate | Preserve native source-scoped identifiers, snapshot limitations and source reference |
| Full GLAMOS glacier/debris features | Accepted SGI2016r2020 retention | CC BY 4.0 adaptation basis | CC BY 4.0 sharing basis, including retained subsets | GLAMOS edition/citation, licence and Meridian subset notice; not current glacier condition |
| Qualified documents, derived slopes/ratios/selectors and Meridian reader code | Existing local authority/projection proof | Preserve every upstream right/reference and method/qualification identity | Assembly/code distribution is **unresolved** | Public repository grants no open-source licence. F07/F17 ownership, third-party/native notices and exact product release review remain gates |

Sources: [swisstopo OGD terms](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices)
(version 1 March 2021; page published 26 August 2022),
[WorldCover access/licence and credits](https://esa-worldcover.org/en/data-access),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
[GLAMOS SGI2016r2020 licence](https://doi.glamos.ch/data/inventory/inventory_sgi2016_r2020.html),
[Copernicus GLO30-F Annex pp.20–22](https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf).
The Annex URL contains an older date but currently serves a document headed
15 February 2024; record actual content/version before delivery, not just its filename.
The [COG publisher documentation](https://copernicus-dem-30m.s3.amazonaws.com/readme.html)
separately describes east/south edge removal and overviews; its software/mirror rights
are not the selected F-instance licence. No geographical data was downloaded.

Existing [source notices](../atlas/semantic-comparison-sources.json),
[Copernicus metadata](../atlas/copernicus-common-metadata.json) and
[regional source-accountability boundary](atlas-regional-expansion.md#13-rights-attribution-and-redistribution-boundaries)
remain intact. No new non-commercial, share-alike, geographic or forced-update
restriction is inferred for these selected free/open/CC BY inputs; this is not a
universal statement about provider APIs, trademarks, ancillary assets or other editions.
Use exact licence texts and bundled notices for the eventual included products.
Research processing is not a substitute for offline delivery review.

Installed package metadata reports NumPy's compound BSD/0BSD/MIT/Zlib/CC0 expression,
rasterio BSD, Shapely BSD-3-Clause and pyproj MIT. This does not clear every bundled
native library. A dependency/notice and ownership audit is needed before binaries
or a data-plus-code package leave controlled research use; no licence file is changed.

## Commands and operational limits

The [experiment guide](../../scripts/atlas/portable-spike/reduction/README.md) specifies
library ownership and exact commands. The original builder/store remain the baseline
workflow; projection creation still uses the existing fully validating Node authority,
while independent queries need no original data, Node authority or network. All new
faults operate on complete disposable owned copies, never accepted evidence/packages.
Generated packages, raw timing logs and local configuration stay outside Git;
compact versioned diagnostic summaries are committed.

## Decisions

**DECIDE NOW:** within a single desktop process, multiple explicit historical views
can share one fully verified captured native snapshot without losing qualified read
semantics or weakening the tested post-open policy. Keep full verification before
ready and new owner creation; failed updates cannot become scientific empty results.

**PROVISIONAL:** the ownership variant is an isolated resource experiment. Bounded
native DSM windows are promising but require their own source-grid/closure proof;
compression, format, reader technology and distribution remain unselected.

**DEFER:** mobile resources/storage/device lifecycle, dependency reduction, lossless
representation choice, crop completeness, cross-process/thread sharing, power-loss,
trusted origin, legal/notice assembly and public distribution.

**REJECT:** query-specific crops/precomputed answers, lossy resampling, inferred
coverage, source hash reassignment, changed frozen expectations, mutable file-backed
reads called tamper-proof, datum harmonisation or Swiss/AWS fusion, and national or
phone extrapolation from this host.

## Exactly one subsequent bounded task — NOT BEGUN

**MERIDIAN ATLAS NATIVE-GRID WINDOW PROJECTION AND SCIENTIFIC-CLOSURE FEASIBILITY.**

**Objective:** establish whether the oversized Copernicus DSM payload can be reduced
while retaining the entire declared core profile, original absolute row/column,
source/support descriptors and exact qualified point/area results.

**Starting evidence:** this source inventory, promising 94 × 66 envelope estimate,
unchanged v1 baseline/60 cases, novel whole-core comparisons and captured-owner policy.

**Scope:** one versioned experimental native-window binding over retained C01, with
justified conservative core support and source-grid/stored-grid separation; preserve
whole Swiss tiles, W01, full geometries/metadata and all provenance. No resampling,
new method, new data, private repository, mobile/renderer, final format/language,
production installer or distribution. Inspect original-byte versus modified notices
and retain unresolved assembly rights; do not acquire legal clearance by assertion.

**Deliverables:** crop-closure argument and bounded builder/reader adapter if feasible,
exact conformance/novel boundary results, deterministic identities, full-readiness/
mutation/restart tests and storage/memory/dependency measurements or a precise blocker.

**Acceptance:** all 60 unchanged cases plus novel valid core queries, including
DSM/native boundary and geographic areas, preserve complete envelopes; missing stored
cells never become valid empty evidence; exact generations/ready replacement/recovery
and snapshot integrity hold. Stop if complete support needs a broad raster engine,
scientific change or unbounded payload. Stop after one measured feasibility result.
This subsequent task is **NOT BEGUN**.
