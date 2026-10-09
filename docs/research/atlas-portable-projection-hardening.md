# Atlas portable projection hardening and desktop offline failure validation

9 October 2026. **DESKTOP OFFLINE CONSISTENCY DEMONSTRATED**, bounded to the retained
Riffelhorn v1 profile, Windows/NTFS, installed GIS toolchain and single-writer local
store. This is not a production installer, mobile offline result, trusted-publisher
proof, legal redistribution clearance or power-loss guarantee.

## Checkpoint, design and authority

Required and observed start: `5528dda72acb41f641966d5c269c5a30b6a8562e`, public
`gbsamirahmed/project-meridian`, clean main/origin/main, fetched 0/0. Read the actual
Foundations decisions, engineering, platform/evolution and roadmap; frozen
[contract](../atlas/portable-read-contract.md), [reference report](atlas-portable-read.md),
[accepted spike](atlas-portable-projection.md), its builder, reader, adapter and tests.
The [hardening design](../../scripts/atlas/portable-spike/HARDENING.md) was recorded
before implementation. The earlier reports and frozen v1 expectations remain unchanged.

Canonical evidence, scientific contracts, original source/preparation records and
immutable Atlas publications remain authoritative. This work changes only the
isolated read projection experiment. Its ready receipts and installation selection
are not Atlas publication roots. Full authoritative validation still occurs during
projection generation; local projection verification does not replace it.

Retained projection identity:
`a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c`.
Its 12 members total **116,692,961 bytes**; six native rasters total 108,207,242 bytes,
full geometry 5,386,941 bytes. No terrain pyramid or new source is copied. Three exact
scientific pins remain:

| Alias | Publication generation | Qualified records / explicit relationships |
| --- | --- | --- |
| before | `65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd` | 81 / 32 |
| after | `5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289` | 81 / 32 |
| legacy | `7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8` | 49 / 0 |

The former two include 32 derived scalars and administrative knowledge revisions;
legacy preserves unknown acceptance time. Swiss DTM/LN02, Copernicus DSM/EGM2008,
native classes, unknown units/time, discrete support and the negative Swiss/AWS
reconciliation remain distinct. No physical change, source fusion or scientific
reinterpretation is introduced.

## Verification and captured-reader policy

[verification.py](../../scripts/atlas/portable-spike/verification.py) validates the
complete projection, including every pin, before it can become ready. Limits are
64 KiB manifest, 16 declared members, 160 MiB total declared member bytes, 8 MiB per
JSON member, depth 64 and one million decoded JSON nodes. The finite profile allows
up to three pins, 128 records/pin, 512 qualified documents/pin, 256 relationships,
38 native geometries, six rasters and 64 consumed cells/scalar. Native TIFFs are
single-band, with at most 13 million pixels; arbitrary drivers are not accepted.
These are spike compatibility/resource bounds, not universal Atlas limits.

Reject unexpected files, path traversal, symlink/reparse members, non-ordinary files,
missing/truncated/tampered members, invalid seals, duplicate JSON keys, nonfinite
numbers, unsafe JSON integers, invalid Unicode and malformed/incompatible structures.
Metadata is decoded from the same bytes whose seals were checked. Verify generation
identity, qualified component membership and regional knowledge binding, document
content IDs and required references, native geometry/support and raster/header binding,
scalar selectors/consumed cells, exact relationship identities/revisions, derived
input closure and cycles. Rejection is an integrity/availability error, never a valid
empty scientific result. Native dependency vulnerabilities are not certified away
by these finite bounds.

The old reader reopened mutable raster paths after initial verification. The
[reader](../../scripts/atlas/portable-spike/reader.py) now captures sealed raster
bytes in read-only GDAL MemoryFiles and holds qualified metadata/geometry in memory.
Scientific reads access those captured resources; changing, replacing or deleting
package files cannot change an already-open reader's answer. New opens revalidate
and reject a damaged package. Two simultaneous historical readers were tested during
atomic raster-path replacement, metadata corruption/deletion and directory deletion.
They keep their original pinned answers. No original package file handle is retained
across queries; raster handles refer to captured memory. Explicit `close()` releases
native buffers and further queries fail with `projection-closed`.

Returned answers remain copies, so callers cannot mutate the reader through a result.
Internal Python objects are not a security boundary against hostile in-process code.
Deleting a package does not erase snapshots already held by another reader; callers
must close them to release those buffers. No global reader registry or forced close
is added. The policy deliberately trades desktop memory for post-open consistency.

Hashes and self-consistent manifests prove integrity **relative to the requested
projection identity**, not origin. The operator must obtain that identity from a
trusted source. A hostile publisher can construct self-consistent false content;
this study neither authenticates publishers nor independently proves scientific
truth. Generation membership is checked inside the sealed exported closure; the
portable store cannot reconstruct full canonical publications from their digests.

## Owned local store and commit boundaries

[store.py](../../scripts/atlas/portable-spike/store.py) uses one explicitly initialised
new directory:

```text
store.json                     experiment ownership/schema marker
staging/candidate-.../          incomplete, never selectable
packages/<projectionIdentity>/ immutable installation identity directory
ready/<projectionIdentity>.json complete verified closure receipt
selection.json                 optional explicitly selected installation identity
```

Stage bounded full copies, including chunked writes and flush/fsync. Verify all
members and pins, rename the candidate into its identity directory, reverify there,
then publish its small ready receipt with same-directory `os.replace`. The receipt
replacement is the **readiness commit**. Selection is a separate record replacement,
after reopening and verifying readiness. `selection.json` binds installation identity,
not scientific chronology; every open still requires an exact publication generation.
A receipt alone never substitutes for full projection verification on reopen.

| Tested interruption/failure | Visible state on restart |
| --- | --- |
| Partial stage/member write; before verification | Abandoned owned stage, no new ready receipt; last selection works |
| Immediately before ready commit | Unready identity directory; old selection works |
| After ready commit, before selection | New compatible package ready but unselected; old selection works |
| Before/after selection commit | Old/new complete selection respectively; previous ready package retained |
| Ready/selection temporary-record write failure | Previous selection preserved; no partial record becomes selected |
| Invalid selection or missing/corrupt receipt/member | Explicit failure; no silent fallback to another installation or generation |
| Selected package deletion | Selection cleared first; future implicit opens fail until an explicit selection |
| Obsolete package deletion | Selected package remains unchanged; already-open snapshots still work |
| Interrupted selected deletion | No selection; still-ready orphan can only be recovered by explicit selection |

Interrupted child processes exit at five deterministic stage/commit hooks. Disk-full
is **injected ENOSPC/write failure**, not exhaustion of the user's disk. Unready
stages are inspectable and explicitly discardable under the owned store only.
Idempotent identical installation is supported; existing identity directories are
never overwritten or silently repaired, even when corrupt. Store allocation checks
reject growth beyond a 512 MiB spike ceiling; explicit deletion/discard is required.

Single writer and benign concurrent readers are the tested model. There is no writer
lock, adversarial filesystem sandbox or general transaction engine. The owned stage
and identity directories must not be modified concurrently by another writer.
Filesystem mutation after readiness makes subsequent opens fail; a historical ready
receipt is not a perpetual claim that bytes remain intact. Ordinary file capture is
not an atomic snapshot of a hostile filesystem, although captured bytes must match
all declared seals before they are used.

File fsync and observed NTFS replacement boundaries support the tested process
interruption result. Directory flush/durability, controller caches, machine power
loss, multi-volume moves, network/cloud filesystems, OS upgrade and mobile storage
behaviour remain unproven. No ordinary interruption trial is labelled power-loss
safety. No remote download, authentication/signature, archive, delta update or
production migration framework is introduced.

## Correctness, failure tests and measurements

The unchanged 60 frozen cases compare the complete semantic envelope, exact numbers,
array order, qualifications, provenance, rights, source/derived revisions, traversal
and historical pins. Nine expected query errors count as passes, not skips. Only
operational metrics are excluded. The independent path calls no authority, original
source reader or network service; isolated processes deny those accesses.

Final counts, measurements and preservation receipts follow. Commands are reproducible using the existing GIS interpreter;
no dependency was installed. Process-cold measurements retain OS caches and include
imports where explicitly stated; these are not storage-cold or phone measurements.

**Semantic validation:** three final isolated fresh processes each passed 60/60;
**180 independent comparisons, zero failed/skipped**, nine expected rejections/process.
The unchanged authoritative replay passed 60/60 with **120 indexed/full comparisons**.
An independent builder run reproduced all 12 original member bytes/identities; build
12.076 s, Node completion RSS 279,089,152 bytes (not combined worker peak).

**Automated tests:** 44 isolated reader/hardening/lifecycle tests passed (14 existing,
30 new), including five actual forced child-process termination boundaries, injected
partial TIFF/record writes, closure/encoding failures, restart/deletion and post-open
mutation. Final suite 170.969 s. Unchanged fixture tests 12/12; native reader 31/31;
unified runtime 92/92 (130.941 s). **179 focused automated tests passed**; conformance
comparisons above are reported separately, not inflated into that test total.

Root lint, TypeScript and the application-only Vite build passed (113 modules), with
the existing large-chunk warning. All nine spike Python files parse successfully.
Existing affine/NumPy dependency deprecation warnings remain. Earlier development
checks found and corrected malformed-JSON diagnostics, test quoting and validation
identifier/kind assumptions; no scientific expectation was changed.

Host: Intel Core i7-12700H, Windows 10.0.26200, NTFS on C:, 16,436,484 KiB visible
memory. Node 24.11.0, Python 3.12.6; installed NumPy 2.5.3, rasterio 1.4.3/GDAL 3.9.3,
Shapely 2.1.2 and pyproj 3.7.2/PROJ 9.5.1. Final lifecycle trials were serial after
fault tests; three repetitions, OS caches retained, no power/battery/device test.
Replacement carries a filesystem footprint-observation hook, so its staging time
is not a clean intrinsic comparison with uninstrumented initial staging.

| Lifecycle work | Median ms | Min–max ms |
| --- | ---: | ---: |
| Initial staging | 569.13 | 537.40–606.56 |
| Initial complete verification | 1242.70 | 1186.50–1320.04 |
| Initial final verification at identity directory | 1160.47 | 1087.86–1204.03 |
| Initial ready publication, excluding final verification | 17.17 | 15.81–17.74 |
| Initial selection, including reopening verification | 1233.75 | 1200.70–1296.02 |
| Initial install through selected state | 4223.80 | 4124.95–4347.15 |
| Instrumented replacement staging | 1104.85 | 1104.46–1143.23 |
| Replacement complete verification | 1333.71 | 1276.22–1356.67 |
| Replacement final verification | 1223.66 | 1218.25–1242.64 |
| Replacement ready publication, excluding final verification | 29.90 | 27.29–31.66 |
| Replacement through selected state | 4958.39 | 4823.84–4971.60 |
| Restarted store open + identity read | 1228.57 | 1227.96–1322.12 |
| Fresh process imports/store open | 1590.26 | 1572.31–1600.96 |
| Injected failed stage + explicit cleanup + reopen | 1251.93 | 1190.04–1256.03 |

The last and selected ready packages occupy **233,386,109 bytes** combined (the
packaging-only variant adds a small manifest suffix). Measured extra scratch peak
including candidate source and stage/ready copies was **350,080,532 bytes** in all
three trials; receipts are included. Original retained inputs/projections are not
counted as generated scratch. Two ready packages plus another full stage are about
350 MB before any separately held candidate source; planning another source copy
would bring this to about 467 MB. Store growth checks count abandoned stages too.
The final serial trials fit the frozen 512 MiB additional-scratch planning bound;
earlier development tests/measurement trials overlapped and are excluded from these
formal timing/peak-disk results. Their separate owned stores remained bounded.

Windows peak working set: lifecycle **407,113,728 bytes**; standalone open/warm reader
benchmark **380,231,680 bytes**; a separate fresh process holding all three pinned
readers **599,416,832 bytes**, below the declared 768 MiB desktop planning bound.
This is substantially above the earlier 111,267,840-byte reader benchmark: native
raster bytes are now captured, and all pin closures are checked at each open. Warm
scientific predicates still operate on the same data; no phone memory inference.

Independent-reader benchmark: three opens/pin, 30 warm queries/type/pin. Times include
complete semantic assembly; no source/network access is needed.

| Pin | Verified open median ms | Native point median ms | Native area median ms | Identity median ms | Transitive lineage median ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| after | 1053.906 | 36.534 | 26.459 | 1.103 | 13.493 |
| before | 1218.381 | 35.949 | 17.141 | 1.215 | 13.548 |
| legacy | 1205.764 | 33.930 | 17.290 | 1.040 | 0.368 |

Overall opens ranged 1,038.07–1,248.62 ms. After-pin warm native point p95 43.47 ms,
area p95 33.03 ms, identity p95 1.47 ms and lineage p95 23.54 ms. Legacy's lineage
result is empty because that publication has no derived dependency graph; it is not
an equivalent populated traversal benchmark. Three complete isolated fresh-process
imports/opens/60-case replays took **5.136 / 4.838 / 4.851 s**. These query/startup
results are different workloads from full canonical Atlas validation or mobile use.

**Preservation/navigation: 42/42 safeguards passed.** The external baseline
checker produced the final receipt. It checks all 1,145 pre-existing tracked files outside
12 permitted edited files, all 42 canonical research rows, 113 production hashes,
frozen fixtures/reference drivers, accepted Tryfan/Riffelhorn/Exe source and retained
publication hashes, original projection seals, exact pins and byte-identical rebuild,
append-only navigation, links, scope, decision rows and whitespace. No private access,
S7, source acquisition, data-repository change, binary/catalogue, credential or
infrastructure is introduced. The old accepted spike/design findings are preserved
as history; new lifecycle commands are an explicit supplement.

Not run: mobile/device/renderer tests, real disk exhaustion, power cuts, network or
cloud filesystem trials, malicious multi-writer tests, security certification and
unrelated historical suites. The full Weather/data-materialising build was excluded;
the app-only build disables that publication plugin/public-directory copying. No
previous 903-test count is claimed as freshly rerun. Recovery timings cover the
named staging-failure scenario; other failures have deterministic functional trials,
not dedicated statistical performance claims.

## Reproduction and maintainability

The [spike guide](../../scripts/atlas/portable-spike/README.md) has exact workflow and
measurement commands. Existing reference config discovers the three retained pins
and original sources only for generation/reference replay; do not commit local paths.
Reader/store require the projection plus Python, NumPy, rasterio/GDAL, Shapely and
pyproj/its local PROJ database. Network is disabled. No Node authority is needed for
independent reads, but this desktop GIS dependency set is not a phone implementation.

Library use: `Store.create(new_root)`, `store.install(source, expected_identity)`,
`store.open(exact_generation, optional_installation_identity)` as a context manager;
`select`, `delete` and `discard_stage` are explicit. No active/latest generation
selection is added. Candidate scientific records remain byte-identical in the
administrative packaging variants used to exercise different installation identities.
They are not new observations or canonical publication generations.

Responsibilities are confined to bounded validation/snapshot capture, finite existing
query logic, store lifecycle, conformance and disposable measurement/failure drivers.
The builder and scientific authority are unchanged. No separate universal reader,
package manager, service, UI or application integration is created.

**DECIDE NOW:** complete compatible closure before readiness; exact generation on
open; failed updates preserve last ready selection; explicit deletion and captured
post-open semantics; distinguish integrity and origin.

**PROVISIONAL DIRECTION:** this directory store and in-memory GIS reader are effective
desktop consistency experiments. They are not selected formats/platform technologies.

**DEFER:** power-loss and adversarial writers, publisher authentication, redistribution
rights, mobile storage/toolchain/performance, compact raster representation and general
cross-language numeric coverage. F03/F05/F12/E02/E05 gain bounded evidence, without
closing the physical-device gate or changing framework/production statuses.

**REJECT:** incomplete caches declared ready; generation fallback; weakening frozen
expectations; a mandatory field-use authority service; hashes called authenticity;
failed Swiss/AWS fusion; extrapolation from this host to global or phone operation.

## Exactly one subsequent bounded task — NOT BEGUN

**MERIDIAN ATLAS OFFLINE PROJECTION PORTABILITY AND RESOURCE-REDUCTION STUDY.**

Objective: determine whether the measured native-raster and snapshot overhead can
be reduced while preserving all frozen semantics and complete qualified closure.
Starting evidence: this hardened store/reader, exact projection identity, measured
resource costs and 60-case/three-pin corpus. Scope: inventory required native windows
versus excess one-degree DSM/full tiles; investigate bounded source-derived descriptors
or crops only with explicit native row/column, CRS/datum and lineage preservation;
compare practical reader dependencies/portability; review exact source rights for
lawful offline redistribution, preserving unknown clearance. No data acquisition,
mobile deployment/SDK, production integration, final format/framework/shared core,
private restructuring or infrastructure.

Deliverables: resource/dependency/rights inventory, at most a small bounded reduction
experiment if scientifically justified, unchanged-case comparison and a provisional
portable direction or precise blocker. Acceptance: all qualified envelopes and native
selection identities remain unchanged; reductions and memory measured; complete
closure and failure behaviour retained; legal uncertainty explicit, no invented
clearance. Stop at a reproducible reduction/portability result or bounded obstacle.
The subsequent task is **NOT BEGUN**.
