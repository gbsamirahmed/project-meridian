# Atlas maintainable local runtime — first end-to-end vertical slice

## 1. Executive result

**C — VERTICAL SLICE SUCCESS**, bounded to the accepted seven-component local
single-writer publication format and retained Tryfan/Riffelhorn evidence.
A developer can open and fully validate authority, build/verify a disposable
SQLite catalogue, query a committed pin, inspect native qualification and restart
or delete/rebuild the catalogue. The runtime never writes a publication root.
This is usable read/index/query software, not a new scientific model or production
Atlas integration. Tryfan remains CLOSED / ACCEPTED.

## 2. Starting checkpoint

Clean main at `b2a57fdd4c942a79f5a10f8d675ec27ba33c9efc`; origin fetched,
divergence 0/0, no newer legitimate work displaced. The
[baseline](atlas-local-runtime-baseline.json) captures the frozen plan identity
and every selected retained store file before implementation. The
[local architecture decision](atlas-local-architecture.md) remains authoritative.

## 3. Selected retained publication

The existing [multi-region result receipt](atlas-multi-region-results.json)
locates the canonical store. The selected historical G0 is
`7f956d3bb640fb7262a3c46b1666306c88aff3418e966d39536882530350acf8`.
G1 is `a0952ff2a46af1772fe665a4bea303f94fd76f5b19963d95e919956b003d6c05`;
current G2 is `d58e5c911f1baaaec90f2d8a863ad070c6cc28b750f45709bf1b09d633d2e905`.
All three are tested. Their scientific Tryfan state is unchanged; administrative
regional notices differ. The later dependency/temporal publication adapters are
not migrated in this first slice. The root and files, not this receipt, determine
eligibility and query truth.

## 4. Frozen scope

[slice-plan.json](../../runtime/atlas/slice-plan.json) was written before code.
The current user instruction narrows the earlier proposed write/derivation slice
to **existing publication → validation → catalogue → qualified pinned query →
restart/rebuild**. No new registration, derivation execution or publication writer
is implemented. No accepted evidence, frozen contract or prior proof is changed.
Acceptance requires native-oracle agreement, complete qualifications, explicit
failure, immutable history, disposable rebuild and protected regressions.

## 5. Runtime module boundaries

- [authority.ts](../../runtime/atlas/authority.ts): read/verify committed membership,
  component hashes, canonical closure and accepted Tryfan payload guards.
- [index.ts](../../runtime/atlas/index.ts): public pinned context, full opening,
  cache build/install protocol and qualified query wrapper.
- [worker.ts](../../runtime/atlas/worker.ts) and
  [worker.py](../../runtime/atlas/worker.py): session-owned JSON-lines bridge,
  existing native geometry/CRS/raster predicates and SQLite.
- [types.ts](../../runtime/atlas/types.ts), [cli.ts](../../runtime/atlas/cli.ts):
  finite typed predicates and operable commands; no command framework or daemon.

## 6. Canonical authority model

Immutable source/prepared bytes, qualified metadata, seven component identities,
publication manifests and filesystem current+committed-membership root remain
authoritative. SHA-addressed objects are verified and exact canonical encoding
is required. Native closure is reconstructed and checked against its accepted
identity. Requested uncommitted identities fail; there is no generation fallback.
SQLite contains selectors and references, never a second evidence body or root.

## 7. Catalogue schema

Schema version1: `binding` (generation, closure fingerprint), `record` (49 scalar
identity/region/family/representation/product/feature selectors), `temporal`
(98 role/known/year rows), and Rtree `bounds` for 38 native vectors and five
Tryfan applicability descriptors. Rasters remain conservative unconditional
spatial candidates within the selected region; their native affine/window
predicate decides exact support. Btree indexes cover identity, feature, family
and temporal selectors. No raster/imagery payload or full geometry is in SQLite.

## 8. Build and rebuild semantics

Private staging is built transactionally by SQLite, closed, sealed and verified.
A completed epoch is installed; its advisory catalogue pointer is replaced last.
The seal binds schema, exact pin, component fingerprint and database hash.
Verification checks all scalar/time rows against canonical selectors, complete
coverage and conservative spatial bounds, including a resealed incorrect-time
negative test. Failed build/install before the pointer leaves the previous cache
valid. Epochs and unfinished staging are disposable; no cache garbage collector
or cross-filesystem transaction is implemented.

## 9. Library API

`openAtlas(config)` accepts explicit public data, publication, catalogue and Python
paths plus optional exact generation. It always performs full validation.
`buildCatalogue`, `verifyCatalogue`, `query`, `scanReference`, `close` operate a
fixed context. `scanReference` is diagnostic, not a silent fallback.
Queries return generation, seven membership identities, stable result identity,
component identity, native evidence, support, temporal qualification, provenance,
rights and a qualified gap. [README](../../runtime/atlas/README.md) has typed usage.

## 10. CLI interface

`node runtime/atlas/cli.ts validate`, `catalogue build`, `catalogue verify`,
and `query --query JSON` expose the workflow. Explicit path flags prevent reliance
on research harness globals. `--generation` pins an exact committed SHA; omission
pins current once. `--json` emits full bodies; human output lists identities and
inspection guidance. Errors produce nonzero status and a concise JSON diagnostic,
not raw internal tracebacks. No arbitrary SQL or unsupported predicate is accepted.

## 11. Query correctness

All **28 supported real Riffelhorn cases** agree on complete native evidence
envelopes with the independently executed accepted full-scan worker. The two
association cases are deliberately outside this API. The repeated measurement
adds **84 indexed/runtime-scan comparisons**, all agreeing. Test expectations for
Tryfan descriptors are independently read from exact canonical catalogue records.
Identities, metadata and qualifications are compared, not counts alone.

## 12. Qualification preservation

44 native Riffelhorn records retain full vector geometry, raster support/selection,
direct/derived source distinctions, preparation identity, method, CRS/datum
limitations, temporal roles, scientific definitions and rights references.
Five Tryfan records expose existing qualified source-product metadata with their
native fields. Their core eligibility does not assert native source coverage or
a measurement at every point. DTM/DSM and overlapping evidence remain separate.
Missing results never imply physical absence; no source ranking/fusion is added.

## 13. Generation pinning

Each query rechecks the selected committed membership and component closure,
then the catalogue binding. A context retains its generation and catalogue epoch
while current advances. An isolated root-advancement test confirms old pins stay
unchanged and a new current pin rejects the old-generation catalogue. Unpublished
staged JSON is ignored. No writer or publication-root mutation occurs in runtime.

## 14. Historical access

All G0/G1/G2 pins build and query after fresh-process restart, with equal native
scientific bodies and distinguishable publication/component identities. These
are administrative knowledge changes, not physical events. Membership reads the
direct 33-record eligibility path; **zero ancestry traversal**. Missing historical
objects fail explicitly. Catalogue deletion cannot erase historical authority.

## 15. Restart and recovery

Fresh CLI opening fully revalidates and reproduces qualified results. Deleted
SQLite files, missing seals and corrupt caches fail with rebuild instructions.
Explicit rebuild yields the same pin and body. Schema/generation mismatches fail;
there is no repair of canonical files. Cache path configuration excludes canonical
data/publication directories and the repository, including resolved existing
symlink targets. Missing configured volumes remain an operational error.

## 16. Negative tests

Tests cover unsupported/null predicates, unordered areas, unknown CRS, missing
region/CRS, unsupported exact temporal precision, unknown family/region, absent
feature, private paths, unsafe cache placement, unpublished generation, corrupt
or missing canonical component/root/membership, missing public payload, deleted
or corrupt SQLite, incompatible seal/schema, wrong pin, resealed wrong temporal
selectors, and interruptions before epoch install and before pointer switch.
All faults use isolated copies/cache state; no retained evidence is corrupted.

## 17. Validation behavior

Accepted `canonicalGeneration`, catalogue/relationship/lifecycle/delivery guards,
`verifyArtifacts`, `verifyDelivery`, and prepared `Session/prepare.verify` are
reused. Exact registration must match native preparation. Full payload validation
is mandatory at every open; no skip switch or receipt reuse. Declared logical
hash accounting is **329 operations / 171,482,433 bytes** including Tryfan source,
portrayal and Riffelhorn source/prepared bodies. Preparation verification performs
additional reconstruction/archive/GDAL reads and manifest hashing: these counters
are not an exact physical-I/O total or cold-disk measurement.

## 18. Structural measurements

49 real selectors, seven components, three historical generations; 41 selected
immutable metadata reads per canonical resolve (33 membership + one publication
+ seven components), plus the small root read. Canonical bytes requested per
measured query: 1,337,489. Query audits all49 scalar rows,98 time rows and43 bounds
in the cache and hashes its80KB. These remain population-wide residual work.
Point candidates:49 full scan →10 indexed; narrow10; broad44; exact feature1;
outside0; observation-year2015 selects1. Native point query reads three raster
windows; broad/narrow categorical-area query reads one. Native decoded-byte
counters exclude filesystem cache and Python/SQLite internal reads.

## 19. Performance and storage measurements

[Raw measurements](atlas-local-runtime-results.json) retain three repeats with
warm filesystem cache, Node24.11, Python3.12/GIS environment on the existing laptop.

| Operation | Median | Min–max |
| --- | ---: | ---: |
| Full open/validation | 2,294 ms | 2,268–2,481 ms |
| Build including seal/verify/install | 194 ms | 190–231 ms |
| Rebuild | 195 ms | 166–250 ms |
| Fresh process full open+feature query | 2,703 ms | 2,655–2,833 ms |
| Pinned point query, indexed | 106 ms | 105–131 ms |
| Pinned point query, runtime scan | 107 ms | 107–123 ms |
| Exact feature, indexed | 83 ms | 78–87 ms |
| Exact feature, runtime scan | 77 ms | 70–81 ms |
| Broad core, indexed | 186 ms | 182–236 ms |

SQLite is **81,920 bytes**, plus a small seal/pointer per active epoch. There is
no payload duplication. Multiple measurement/fault epochs remain only in external
assessment cache directories. Parent-process sample RSS median261MB/min256/max263MB
is not combined Python/native peak memory. Storage remains negligible beside the
accepted29.16GiB public-data inventory and flexible80GB working budget. No new
geographical source or extensive processing output was created. Similar query
timings do not establish a speedup; no cache/hashing optimization follows.

## 20. Reproducible commands

[Runtime README](../../runtime/atlas/README.md) supplies PowerShell variables,
receipt-based locator discovery, explicit path/generation flags, validate/build/
verify/query commands, exact feature, point, area/time and unknown-time examples,
library usage and deletion/rebuild instructions. Opening an installed retained
publication needs no manual research orchestration. Python is used for accepted
native predicates and embedded SQLite, not forced derivation execution.

## 21. Maintainability assessment

Separate authority, session, native worker, schema/types, CLI and tests keep one
authority boundary visible. No new npm dependency, generic ingestion framework,
background worker or package restructuring. TypeScript is independently checked;
existing application build boundaries stay unchanged. Public failures explain
what to validate/rebuild. Full validation costs are practical for this workflow.

## 22. Reusable versus proof-specific code

Path-configured context, worker protocol, cache install/recovery, pin/error types
and CLI form a reusable runtime boundary. The seven-kind adapter, exact accepted
scientific identity, Riffelhorn preparation and five Tryfan descriptors are explicit
first-slice adapters. Tests/measurements use baseline locators for this installation.
Canonical read/ref/hash/qualification functions are reused from accepted modules;
their research globals/hooks are not mutated. General temporal/dependency runtime
migration and scientific job execution remain future work.

## 23. Known limitations

Local single-writer; serialize builds, close contexts. Files remain immutable
during sessions; full validation inspects current bytes at open, object hashes
are rechecked per query. This is not continuous cryptographic custody, physical
truth, upstream authenticity, power-loss durability or multi-writer safety.
Whole metadata/cache audits remain; no latency claim at global population.
Time is native year/unknown qualification, not an arbitrary physical-validity or
knowledge-time engine. Tryfan physical sampling and newer temporal13-component
formats are explicitly unsupported. Cache retirement and external-disk performance
are untested. Production Atlas and its client interfaces remain unchanged.

## 24. DECIDE NOW

Canonical files/root determine eligibility; disposable selectors cannot grant
truth. Full open validation and exact post-selection native predicates are required.
No silent generation switch, unknown-time match, source fusion or canonical repair.
Rebuild must preserve complete qualified results and historical identities.

## 25. PROVISIONAL DIRECTION

Keep the small Node/TypeScript library+CLI with session-owned native Python worker,
sealed SQLite epochs and explicit configurable roots. Extend accepted methods and
lifecycle through this boundary next; preserve the user-operable read workflow.
Scientific processing remains selected but not exercised by this first slice.

## 26. DEFER PENDING EVIDENCE

Wider adapter migration, arbitrary temporal/geometry queries, cache retirement,
optimizations, more regions, external-drive benchmarks, HTTP/public service and
global storage remain deferred. Full validation remains default; receipt optimization
remains CLOSED. Appearance limitations and parked Swiss multiview are unchanged.

## 27. REJECT

Dual SQLite/canonical authority, catalogue fingerprints substituting for full
validation, automatic evidence repair, hidden scan fallback, invented physical
timestamps/features, unsupported scientific fusion, new production dependencies
or services, and expanding this task into runtime write/derivation implementation.

## 28. Regression results

[Validation receipt](atlas-local-runtime-validation.json) records **65 safeguards
and 508 passing tests** (446 inherited plus62 runtime), runtime/semantic/application types, lint/build,
navigation links and full-diff protections. S1–S6, Riffelhorn, multi-region,
derivation, temporal and architecture reports remain unchanged. All42 canonical
research statuses and113 protected production hashes remain unchanged. Source,
prepared and accepted publication-store checks guard data outside Git. No private
access, acquisition, S7, cloud or production infrastructure.

## 29. Overall result

**C — VERTICAL SLICE SUCCESS**: the explicit CLI/library workflow opens, fully
validates, indexes and queries real retained authority, preserves qualified pins,
replays after restart and recovers by catalogue rebuild. Scope does not establish
new regional registration, derivation/publication writing or service readiness.

## 30. Exactly one next bounded Atlas task

**Atlas local runtime deterministic derivation and scoped lifecycle integration —
NOT BEGUN.** [Precise task](../../runtime/atlas/next-task.json).
The concrete gap is execution/lifecycle coordination after a usable read boundary.
Use one accepted real method and downstream summary, explicit worker/input/method/
parameter/output identities, scoped invalidation, immutable staging and the smallest
isolated publication coordinator with full guards. Require full-derivation oracle
agreement, other-region reuse, incomplete-job isolation, coherent old/new pins and
restart/rebuild. No new source, algorithm, general orchestrator or production code.
Stop after that one processing vertical slice is tested/documented/checkpointed;
do not begin it in this task.
