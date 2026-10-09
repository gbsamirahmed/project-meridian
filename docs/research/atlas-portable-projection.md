# Atlas portable read-only projection and independent reader spike

9 October 2026. **SEMANTIC PORTABILITY DEMONSTRATED**, bounded to the frozen
Riffelhorn profile, three retained generations and this desktop GIS toolchain.
This is neither a production reader nor a mobile/offline-package readiness result.

## Starting gate and design

Public `gbsamirahmed/project-meridian`, main / origin/main, exact clean start
`5c93074f9773815111af96f89c3a73fcbb3b526a`; fetched origin, divergence 0/0.
Read committed Foundations, the [read contract](../atlas/portable-read-contract.md),
[accepted fixture report](atlas-portable-read.md), exact fixture pins/seals, runtime
registration/retrieval models and native Riffelhorn query/preparation boundaries.
The [design](../../scripts/atlas/portable-spike/README.md) was written before implementation.
No private access, canonical writes, acquisition, SDK, service or production change.

The smallest faithful closure was not just metadata: full native vector geometries,
six native raster files, static qualified record/document populations and derived
anchor/consumed-cell selectors are required. This remains bounded; no rendering
pyramid, prepared physical fusion, new observation or derivation was introduced.

Spike-local choice: **Python independent reader**, existing NumPy/rasterio/Shapely/
pyproj libraries; **one file-backed JSON/GeoTIFF projection directory**. A Node bridge
is required only to export the existing Node authority. This is not a permanent
language, package-format, mobile GIS dependency or shared-native-core decision.
The independent path does not import or call the Atlas query implementation.

## Projection generation and closure

`build.mjs` opens and fully validates all three exact pins, verifies frozen reference
source fingerprints and materialises `scanEvidence({})` once per pin. It never reads
requests.json or expected.json. The unfiltered population is query data, not a table
of answers to the 60 cases. The builder copies original scientific records/qualified
documents and accepted source-processing selectors, then reads prepared features and
native rasters. Inputs remain read-only; output is a new external staged directory.
The manifest is written last and the owned directory renamed on completion. No root
advancement or catalogue authority; process-interruption behaviour is not yet tested.

| Members | Exact source and purpose |
| --- | --- |
| `manifest.json` | `atlas-read-projection-spike/v1`, profile, projection content identity, core/CRS, generation-to-file bindings, authoritative closure fingerprints, member sizes/hashes and raster identity-to-local-file bindings |
| Three generation JSON members | `atlas-read-projection-generation/v1`: complete unfiltered semantic response, scalar selectors and knowledge acceptance descriptors from the accepted retrieval view |
| `features.json` | Byte-identical accepted full native geometries, 38 features; source hashes/provenance still refer to the original prepared artefact |
| `worldcover.json` | Original accepted semantic collection/claims, definitions and context needed to select source-native categories independently |
| Six hash-named `.tif` members | Four Swiss 0.5 m DTM tiles, retained one-degree Copernicus DSM and selected WorldCover raster; no change to native coordinates, affine indices, nodata or bytes |

A source path remains scientific lineage, not a local file address. The local raster
map is explicit and sealed. No absolute personal path enters the projection. The
projection identity is the existing canonical content encoding/hash of the manifest
without its identity field; it is not a signature or publisher-authenticity proof.
`Reader(root, generation, expected_projection=None)` checks schema/profile, optional
caller-supplied identity, manifest identity, exact closure, all member hashes/sizes,
selected pin, referenced document identities and relationship endpoints/cycles.
No generation fallback. Copies require their own rights review before redistribution.

Exact historical pins are unchanged:

- `before`: `65989736a06f72182fba9d9ad9d47955869f51ce943ef120effcad2df91352fd`.
- `after`: `5d364e9947040f705699416e9094d8ad59463b5b2c2fcae2e3efdf79a7410289`.
- `legacy`: `7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8`.

The first two expose 81 whole-world records (49 native, 32 derived), legacy 49.
Whole-publication membership and Tryfan regional metadata are retained, while
independent spatial operations support only Riffelhorn. Its native population remains
44 descriptors: 38 features and six raster supports. This is not new Tryfan/Exe
query-profile coverage. The preparation revision and all source identities match
[the frozen manifest](../../fixtures/atlas-read/v1/manifest.json).

## Independent query implementation

`reader.py` uses only Python standard libraries and the installed GIS libraries.
It never reads fixture IDs, frozen requests/answers, authoritative code, original
payload paths or a network service. It independently executes structured predicate
validation, conjunction, exact identity/product/class/family filters, year-role and
knowledge filters, direct/transitive dependency closure, transformed/densified area
selection, core intersection, vector covers/positive-area intersection, half-open
native affine cell/window selection, WorldCover cell-centre counts and scalar anchor/
consumed-cell selection. No scientific transformation or terrain renderer is added.

Complete envelopes preserve native support, CRS/datums, times, source/preparation/
method lineage, qualifications, rights, uncertainty, revisions, generation members,
region references, selected/traversed relationships and all applicable documents.
Only operational metrics are absent. Query-dependent raster documents and their
identities are computed at read time, not copied from frozen answers. Height unit
unknowns, DSM/DTM and LN02/EGM2008 distinctions, no-match physicalAbsenceInferred:false
and the negative Swiss/AWS finding remain intact. No nodata case was invented.

Known/unknown years, knowledge acceptance and publication order are separate; a
qualification correction changes qualified references without implying physical
change. Raw input revisions are not silently replaced by preparation revisions.
Unsupported/malformed predicates and missing relationship seeds retain exact frozen
error envelopes. Missing/corrupt/incompatible projections fail explicitly instead
of masquerading as empty evidence. Other regional spatial readers, Exe-specific
qualifiers, arbitrary geospatial algebra and unrestricted query combinations are
outside this finite spike; passing the corpus does not prove them.

The Python identity serializer required explicit UTF-8 and ECMAScript integer-key
ordering. These were implementation fixes: no fixture or scientific meaning changed.
Exact agreement is established only on the recorded finite corpus/toolchain, not all
possible cross-language numbers or schema evolution. The reader shares numerical
GIS libraries with the reference; it independently implements selection/assembly,
not an independent physical truth or independently implemented geometry kernel.

## Conformance and novel behaviour

The separate adapter loads unchanged sealed requests/expected documents and calls
`Reader.outcome(query)` with only the query and selected pin. It compares complete
semantic structures, array order and exact values, reporting the first differing
path. Expected rejections pass; no weakened expectations, skips or case-ID dispatch.

**Three fresh isolated processes: 60/60 each, 180 exact independent comparisons,
zero failures/skips, nine expected rejection cases per process.** Earlier development
checks are not added to that final total. All 12 final projection members, including
the manifest, reproduced byte-for-byte in an independent build.

**14 novel behaviour/failure tests passed.** They read neither frozen requests nor
expected answers: unseen native affine point and nearby seam offsets; multi-predicate
identity/family/representation/time conjunction; slope-to-source and source transitive
lineage; explicit old/new/legacy pins; malformed/unsupported inputs; successful absent
identity; unknown knowledge; numeric-key/Unicode content identity; corrupt member,
missing member/directory, incompatible schema, manifest tampering and resealed missing
closure rejection; modifying returned answers cannot alter the pinned reader state. The affine point checks independent 0.5 m row/column arithmetic.
Immutable raster hard links are used only inside owned desktop test directories,
never written; small metadata copies are removed afterwards.

`isolation.py` copies only the reader, adapter and frozen fixtures to an owned temporary
working directory and starts a separate Python process. Python audit hooks deny opens
under the public authority repository, original source/prepared/publication roots,
network connection/name-resolution and child-process/system dispatch. All 60 reads
still pass. This proves no such runtime access was required in these executions;
it is not a security sandbox, browser deployment or comprehensive offline failure proof.
The GIS interpreter/libraries and their local PROJ database remain required.

## Resource measurements

Host: Intel Core i7-12700H, Windows 10.0.26200, approximately 16 GiB visible memory.
Node 24.11.0, Python 3.12.6; existing NumPy 2.5.3, rasterio 1.4.3/GDAL 3.9.3,
Shapely 2.1.2, pyproj 3.7.2/PROJ 9.5.1. No toolchain installation.

Final projection identity:
`a34ac6745abe92904d6af089ae8dff888d3527d6588c395ee3b03750d9e08a1c`.

| Work | Observed measurement |
| --- | --- |
| Complete projection | 12 members, **116,692,961 bytes** (111.3 MiB); native raster bytes 108,207,242; full features 5,386,941 |
| Two final builds | 10.98 s / 11.77 s; byte-identical; timer includes full authoritative opens and copying/hashing, after native-input preflight |
| Node builder RSS at completion | 290,627,584 / 280,059,904 bytes; samples, not combined Node/worker peak |
| Verified independent open | Three repetitions per pin: medians 216.93 ms after, 249.38 ms before, 217.81 ms legacy; overall range 203.12–264.81 ms |
| Warm native point | 30 trials per pin: medians 33.11 / 40.97 / 39.10 ms; after p95 40.37 ms |
| Warm native area | Medians 17.51 / 17.77 / 18.08 ms; after p95 19.10 ms |
| Warm identity | Medians 1.148 / 1.098 / 2.028 ms |
| Populated transitive lineage | After median 13.57 ms, p95 24.61 ms; before median 14.42 ms. Legacy has no runtime derived relationships (0.732 ms empty result) |
| Python benchmark peak working set | **111,267,840 bytes**; measured Windows process peak, below 512 MiB planning bound |
| Isolated fresh process, imports + three opens + 60 comparisons | 1.888 / 1.871 / 1.873 seconds |

Warm trials include full semantic assembly/content hashing and raster opens where
needed. Verified opens include complete projection hashing, but OS caches were not
flushed; these are process-cold, not storage-cold timings. No desktop-authority
speed-up or phone budget follows from incomparable workflows. Temporary planning
allowed two external projections plus small copies below 300 MiB; obsolete development
copies were removed before regeneration. No generated projection/payload is committed.

## Validation and maintainability

Executed: 14 new tests; 12 frozen fixture tests; 31 accepted native-reader tests;
92 existing unified runtime tests (132.81 s), all passing. Three isolated final
conformance runs and exact regeneration as above. New Python syntax and export
bridge syntax/explicit ESLint checks passed; root lint and TypeScript passed.
Application-only Vite bundle passed (113 modules), with existing large-chunk warning;
the external Weather-publication materialisation and public-directory copy were
excluded. Full Weather/data build and unrelated historical suites were not rerun.
Existing affine/NumPy dependency deprecation warnings remain visible.

The implementation is isolated under scripts/atlas/portable-spike. No dependency
was added, runtime authority rewritten or second complete scientific engine built.
The read-only finite selector can be reviewed separately from the generation bridge,
conformance adapter, novel tests and measurement/isolation tools. Reproduction and
library/CLI commands are in the design README. **38/38 preservation/navigation safeguards passed.** All 1,142 pre-existing tracked
files outside seven append-only navigation files are unchanged, including frozen
fixtures/drivers and scientific contracts. All 42 status rows, 113 production hashes,
accepted Tryfan/Riffelhorn/Exe evidence and retained publication hashes match the
starting baseline; the negative Swiss/AWS finding remains intact. New-file scope,
links, byte-identical projection reproduction, source fingerprints and whitespace
passed. Initial audit-only size/encoding/wording checks were corrected to inspect new
files separately and read UTF-8; no protected file or scientific expectation changed.

## Decision and remaining limits

**DECIDE NOW:** the finite accepted semantics can be projected and independently
queried without live access to the desktop authority. Keep canonical publication
truth and all scientific qualifiers unchanged.

**PROVISIONAL DIRECTION:** this JSON/native-raster directory and Python reader are
useful semantic feasibility tools. They are not selected device/package technologies.

**DEFER:** cross-language universal numeric encoding, reader distribution, rights
clearance, mobile dependencies/performance, browser/storage limits, update format,
trusted origin/signatures, concurrent mutation and maintained SDK/toolchain support.

**REJECT:** a mandatory field-use authority service, fixture lookup masquerading as
query logic, approximate bounds replacing geometry, changed expected semantics,
source-locator-based identity, unknown-as-unrestricted and failed Swiss/AWS fusion.

Observed weaknesses include no install/ready-state protocol; no interruption,
disk-full, deletion, concurrent file replacement or post-open tamper proof; checksums
alone do not authenticate publisher; one desktop GIS toolchain and finite serializer
coverage; the retained one-degree DSM is much larger than the 4 km² applicability.
No renderer, Weather, UI, navigation, power-loss or mobile reliability result.

## Exactly one subsequent bounded task — NOT BEGUN

**MERIDIAN ATLAS PORTABLE PROJECTION HARDENING AND OFFLINE FAILURE VALIDATION.**

Objective: resolve the observed projection-consistency and incomplete-install gaps
without changing frozen semantics. Starting evidence: this projection/schema, reader,
exact 60-case corpus and measured desktop closure. Scope: bound manifest parsing and
resource use; verify pin-to-qualified-membership/reference closure; exercise corrupt,
partial, interrupted, disk-full and post-open mutation cases; establish an explicit
compatible-ready-state selection that preserves the last good projection. Include
restart and user-controlled deletion; assess numeric/encoding edges surfaced here.
No mobile deployment, production integration, new acquisition, private access,
renderer, provider or permanent format selection.

Deliverables: minimal hardening changes, reproducible fault-injection tests and a
measured recovery report. Acceptance: unchanged 60 semantic expectations; incomplete/
incompatible states never become ready; last compatible state survives tested failures;
all unsupported guarantees remain explicit; authority and protected evidence unchanged.
Stop after one bounded desktop offline-consistency result or precise blocker.
This follow-up is **NOT BEGUN**.
