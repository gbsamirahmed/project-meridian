# Atlas evidence-based local storage, processing and serving implementation decision

2026-10-08. **C — DECISION READY**, bounded to the first offline local single-writer runtime. This is a decision, not an implemented runtime.

## 1. Executive result

Choose immutable payload and canonical qualified/component/publication files, plus a **rebuildable embedded SQLite query catalogue**. Canonical files and the atomically replaced committed-publication root remain authoritative. SQLite owns candidate lookup and reverse relationship access, not scientific acceptance, publication visibility or historical truth. A deterministic Node/TypeScript library and CLI coordinate bounded Python native-processing/catalogue workers. Start without HTTP, a daemon, queue or cloud service.

This is a practical choice, not a claim that a database wins every query. The actual 250-record comparison shows warm memory dictionaries faster for small identities, broad geometry work essentially unchanged, and SQLite inexpensive to build/reopen while retaining indexed access between commands. Persisted lookup is valuable without moving the scientific contracts into relational columns. Full validation remains the default; receipt optimisation remains CLOSED. No additional architecture experiment is required before the first slice in section 23.

## 2. Starting checkpoint

Clean `main` at `d6a5514cdbee799d9a018b1660080568537428fa`, “Atlas dated observation and knowledge-revision integration proof”. Origin was fetched before changes; divergence was 0/0. No newer commit or legitimate changes required reconciliation. The [baseline](atlas-local-architecture-baseline.json) freezes the plan and every file in the accepted external temporal store before comparison. Only a disposable metadata comparison, safeguards and decision documentation are implemented here.

## 3. Evidence reviewed

Primary foundations: [Tryfan S1](tryfan-pilot-s1.md), [S2](tryfan-pilot-s2.md), [S3](tryfan-pilot-s3.md), [S4](tryfan-pilot-s4.md), [S5](tryfan-pilot-s5.md), [S6 exit](tryfan-pilot-s6.md); [world-model synthesis](atlas-world-model-architecture-synthesis.md); [semantic contract](../atlas/semantic-evidence-contract.md); [derived lifecycle](atlas-derived-understanding-lifecycle.md); [storage requirements](atlas-storage-processing-serving-requirements.md); [measured architecture](atlas-measured-storage-processing-serving.md); [generation scaling](atlas-generation-scaling.md); [component membership](atlas-component-membership.md); [granularity](atlas-component-granularity.md); [validation reuse](atlas-validation-reuse.md), [maintenance](atlas-validation-maintenance.md), [packing](atlas-validation-packing.md) and [integrity costs](atlas-integrity-cost.md); [source accountability](atlas-regional-expansion.md); [preparation](atlas-riffelhorn-preparation.md); [retrieval](atlas-riffelhorn-retrieval.md); [multi-region](atlas-multi-region.md); [dependencies](atlas-regional-dependencies.md); [temporal integration](atlas-temporal-integration.md). Prior positive and negative results remain authoritative.

Code inspected: pilot identity/catalogue/generations/lifecycle/serving, component `core.mjs`, Riffelhorn preparation/query Python, regional/dependency/temporal adapters and validators. Production terrain configuration/delivery/sampling was read only for consumer boundaries. The public data directory was inventoried by file sizes, without reading activity/export content or accessing meridian-private.

Official references: [SQLite atomic commit](https://sqlite.org/atomiccommit.html), [WAL](https://sqlite.org/wal.html), [R*Tree](https://sqlite.org/rtree.html), [installed Node 24.11 SQLite API](https://nodejs.org/download/release/v24.11.0/docs/api/sqlite.html). These inform constraints; they do not establish a tested complete hybrid or power-loss guarantee.

## 4. Frozen evaluation criteria

The [plan](../../scripts/atlas/local-architecture/plan.json) and its hash were frozen **before comparison and selection**. Mandatory: immutable identity independent of location; native meaning, rights, temporal precision/unknowns and dependencies; full validation and committed eligibility; coherent pins/history; interruption isolation; offline one-writer restart; explicit missing-volume failures; bounded working memory; one authority and rebuildable accelerators; no runtime implementation here.

Final Git review normalized new artifacts to the repository's UTF-8/LF policy. The baseline preserves the original prefreeze byte digest and external original; exact parsed criteria/workloads are unchanged. The portable plan digest is used by the committed receipts. This is encoding normalization, not a revised experiment or post-result acceptance criterion.

Prefer existing dependencies, understandable modules, selective metadata/reverse access, reproducible setup, portable roots, observable failures, versioned adapters and reversible indexes. Global throughput, multi-writer/remote storage and public HTTP are not requirements. Small noisy timing differences cannot select infrastructure. Any candidate identity/qualification disagreement disqualifies performance evidence. Stop after one bounded material comparison and a concrete decision; do not reopen receipts or scientific proofs.

## 5. Actual retained workloads

| Operation | Measured boundary | Implementation pressure |
|---|---|---|
| Initial registration | Tryfan five families/eight representations, 310 artifacts/42,473,107 B; Riff 12 inputs/120,347,916 B | Accountable import, no duplicate payloads |
| Source verification | Tryfan integrity median213 ms; existing11,429 Swiss tiles/930,914,852 B median9.61 s | Full bytes and file-operation population |
| Preparation | Six Riff prepared artifacts/5,605,110 B; three identical preparations median2.861 s | Exact native parameters and versions |
| Qualified insertion | 44 Riff supports,38 features/six raster bindings;50 declarations | Native collections, not one row per raster cell |
| Spatial/feature lookup | Point44→10; exact feature44→1; broad44→44 candidates | Separate paths plus exact predicates |
| Physical/knowledge lookup | 17 assignments,20 retained revisions,three supersessions,five contexts;477 comparisons | Clock roles/unknowns; no physical chronology from generations |
| Dependency traversal | 293 nodes/294 edges,184 active outputs,fan-out36,depth3 including uses | Actual input-use scope and reverse access |
| Scoped invalidation | Local correction8/reused176; shared source72; unrelated/no-op0 | Exact affected closure |
| Selective recomputation | 24 prior scoped/full comparisons; later Swiss full/scoped3.28/2.17 s | Native windows and exact method identity |
| Composite publication | Seven original components,13 with temporal branches | Complete composite closure,one writer |
| Current pin | 33 eligibility records,13 components,zero ancestry;3.01–3.22 MB hydration | Persisted candidates; existing full hydration acknowledged |
| Historical generation | Five independently resolved generations | Exact membership,not parent replay |
| Fresh process | Three complete temporal historical replays median60.54 s | NOT isolated restart latency; includes numerical/oracle replay |
| Interrupted recovery | Invalid/pre-switch state invisible; explicit ownership recovery | Job status is not publication eligibility |
| Regional expansion | Existing100 km² Swiss delivery/larger sources and imagery | Configurable archives and scratch |

Exe is a disconnected dated branch,31 selected source/document artifacts/9,892,590 B; its accepted reader also inspects66 retained directory files. It is not Tryfan/Riffelhorn water evidence. Growth means more unique supports, sources, methods, outputs and history; no request rates/users/global forecasts were invented.

## 6. Current implementation inventory

Production remains a client MapLibre application. Terrain hierarchy/delivery and the independent analytical sampler (96-tile decoded cache) do not implement the retained world model. This decision does not change production.

Reusable pure boundaries: finite canonical JSON/SHA256, safe relative locators, semantic v1 validation, native raster/vector selection, temporal extent/unknown predicates, exact actual-use/method/parameter freshness, explicit publication membership and qualified pinned envelopes. Horn slope, planar ratio and categorical count definitions retain accepted parameters/oracles.

Research orchestration needs adaptation: fixed accepted supports/generations/task lists, mutable global domain/component hooks, absolute experiment roots, duplicated worker management, Vite test-time loading, broad hydration and proof-only full numerical replay. Pilot `validateGeneration` pins exact Tryfan support/knowledge hashes: it is a reference validator, not a generic registry. Do not copy it wholesale into a general runtime.

## 7. Storage alternatives

| Alternative | Benefit | Cost/risk | Selection |
|---|---|---|---|
| Canonical files/per-command scan | Inspectable,closest to proofs | Repeated hydration; ad hoc relationship lookup | Reference/fallback |
| Files plus warm dictionaries/STRtree | Fast small identities,accepted exact geometry | Rebuild/process memory grows with admission | Bounded session caches |
| Files plus rebuildable SQLite | Persisted identity/membership/reverse/bounds access,consistent view | Build/seal and duplicate projections; second format | **Chosen** catalogue |
| Payload files plus authoritative SQL metadata/root | SQL acceptance transactions | Still no atomic payload inclusion; larger authority/serialization/migration change | Not first slice |

Large native payloads stay outside SQLite. No need for PostGIS, graph store, cloud object storage or distributed roots was found. Files are not rejected because proofs used them; SQLite is not selected because it is conventional.

## 8. Metadata and indexing alternatives

Canonical versioned JSON retains complete qualifications, rights, sources/preparations, temporal roles/precision, uses/results and component membership. Projection keys do not redefine scientific identities.

Choose SQLite B-tree indexes for revision identity, source-scoped feature, region/family/representation, generation/component membership and forward/reverse dependency references. Store temporal role, known/unknown status, precision and conservative bounds for candidates; run accepted exact temporal/knowledge predicates afterward. Separate observation/applicability from source/acquisition/preparation/publication. Observation intervals do not imply continuous validity.

Choose R*Tree bounds for actual vector/support populations per known working CRS; retain native CRS/geometry and exact filtering. Never combine CRSs into one coordinate index. Raster support points to native windows/COG/tile addressing, not per-pixel rows. Unknown CRS fails or remains explicitly unresolved. R*Tree float32 bounds round outward: use overlap candidates and exact filtering, not unqualified containment ([official contract](https://sqlite.org/rtree.html)). Unknown temporal records need a distinct candidate path to avoid false negatives. No universal partition size, source ranking or fusion is selected.

## 9. Processing alternatives

Choose deterministic CLI jobs with exact inputs/method revisions/parameters, owned staging, manifests, receipts and logs. States: planned→preparing→prepared→validated→publication-ready→committed, or failed/interrupted. Partial outputs never count as prepared evidence. Commands/session are bounded; publication has one writer.

Node/TypeScript owns scientific identity, semantic/lifecycle interfaces, job coordination and publication. Python owns native GIS/array work and the embedded catalogue through existing stdlib SQLite/rasterio/pyproj/Shapely. Exchange bounded versioned JSON, relative locators, exact IDs and explicit failures. Node canonicalizes scientific bodies; Python must not create a new identity by changing float serialization. Worker lifetime may equal a library session, with explicit close; no resident service.

Dependency closure selects accepted methods; publication coordination is not a scientific engine. No queue/workflow/event platform. Historical numerical replay is explicit testing/audit, not mandatory on every normal query/restart. This removes proof orchestration, not required acceptance checks.

## 10. Serving alternatives

Choose typed `openPinnedSession(generation?)`, qualified queries, inspection and `close()`, plus JSON CLI. Read canonical root once, verify committed eligibility and explicit membership, then select a bound index view. Every response reports generation and qualified identities. Never follow mutable current roots mid-query.

Library/CLI fit reproducible local work. Later HTTP may wrap the same interface if a real consumer needs process-independent access; S4 is a pin/error reference, not a requirement for HTTP now. No map rebuild, public API, Weather or Traverse integration.

## 11. Publication and transaction analysis

**Canonical filesystem root contains current generation and committed eligibility together.** Each immutable publication explicitly names components; predecessor is lineage only. Keep the accepted bounded keyed eligibility mechanism for the first slice:33 records is adequate. No membership optimization.

SQLite transactions provide internally consistent derived views, not atomic database/filesystem publication. Select **sealed immutable catalogue epochs** with unique shared record projections and explicit generation/component joins. A staged generation may be indexed only if canonical eligibility gates every query. The catalogue is not a second acceptance root. Per-generation fingerprints bind component IDs/extractor version; closed-file digests/build receipts bind index epochs.

Build a private temporary DB, rollback journal and `synchronous=FULL`, one transaction, constraints, integrity/completeness checks, close then hash/seal; install by same-volume rename. Never rename an open/hot-journal DB. Open sealed epochs read-only. No WAL sidecars or long-lived database writer needed. Atomic commit depends on filesystem/locking/sync and does not guarantee the hybrid ([SQLite](https://sqlite.org/atomiccommit.html)); WAL retains one-writer/same-host constraints ([WAL](https://sqlite.org/wal.html)).

## 12. Recovery and historical access

Recover canonical root/closure independently of query cache. Cache pointer may be missing, behind or ahead without making staging visible. Wrong/corrupt catalogue: refuse it as a view, explicitly rebuild or use canonical scan within memory limits. Never return an empty answer due to a missing index row/view. Check candidate completeness against canonical population during build, including unknown qualifiers; matching returned bodies alone is insufficient.

Pins retain their generation/epoch. Old generations use later epochs containing exact old components, or rebuild from immutable closure; no ancestor reconstruction. Old epochs are disposable after readers close, not historical evidence. Keep canonical histories, payloads and source/preparation receipts; no production GC.

Never auto-promote staging. Verify current root/closure, report incomplete jobs/orphans, retry only with exact owned inputs. Dead-writer recovery uses ownership/operation evidence, not age. Missing external volume is payload unavailable: provenance inspection may work, analytical answers requiring bytes fail. Historical unavailability is not physical absence. Single-writer process evidence does not prove remote/multi-writer/power-loss durability.

## 13. Local hardware/storage constraints

[Hardware](atlas-local-architecture-hardware.json): i7-12700H,14 cores/20 logical processors;16,830,959,616 B RAM (15.68 GiB); one mounted internal volume ~1.02 TB with158.70 GB free at inspection. External4 TB disk not mounted; stated≥3 TB free is a planning assumption, not measured dependency.

[Public stat inventory](atlas-local-architecture-data-inventory.json):31,314,398,677 B =31.31 decimal GB/**29.16 GiB**. Units explain the earlier~29.1 figure. This is whole-directory occupancy, including environments/unrelated research, not the Atlas active set: sources4.40 GB,derived9.98 GB,experiments14.23 GB,earth-lab1.92 GB. Metadata-only walk26.9 s; no full31 GB content sweep/activity-export inspection. Flexible80 GB budget is not disk capacity or scientific coverage limit.

Keep metadata/indexes/active preparations internal. Config maps volume roles (`public-source`,`prepared`,`runtime`,`scratch`,optional`archive`) to paths. Drive letters only in machine config. Identity uses exact bytes and qualified IDs; locators are replaceable materialization addresses. Reference existing files read-only instead of duplicating29 GiB. New immutable writes use SHA256-prefix paths; retain original names/receipts as lineage.

Existing100 km² Swiss tiles0.93 GB/source terrain~1.67 GB and image working/delivery1.29/0.27 GB sum~4.16 GB before scratch/original imagery/revisions; NOT universal area economics. Ten similarly configured workloads~41.6 GB is transparent capacity arithmetic, not measured new coverage/forecast. Estimate scratch/output before processing, use native windows/blocks. Optional external archives extend budget; they are not needed here. A single external disk is not backup: independently copy/verify authoritative records, receipts and irreplaceable payloads; indexes/scratch are rebuildable.

## 14. Benchmarks and existing measurements

[Comparison](../../scripts/atlas/local-architecture/compare.py), [results](atlas-local-architecture-results.json), [tests](../../scripts/atlas/local-architecture/test_compare.py) are disposable; DB/projected payloads stay outside Git. Python3.12.6/SQLite3.45.3 on recorded hardware, exact retained input hashes, five timings under identical tracemalloc instrumentation. OS cache not flushed. Fresh subprocess measures start/hash/open/binding/count, not native GIS/payload acceptance.

38 feature bodies+20 temporal revisions+192 result revisions =250 records;1,006 membership rows/five generations;200 direct result-input edges. This subset is **not** the entire accepted293/294 graph. All192 candidate identity/body comparisons agree. Twelve cases: feature,absent,known,unknown,five pins,reverse-use,narrow,broad. Nullable feature IDs preserved. Known-time predicate here is qualifier presence, not a replacement physical-interval oracle;477 prior comparisons remain temporal evidence.

| Cost | New result |
|---|---|
| Verified source projection setup |457.7 ms,one sample |
| SQLite build/constraints/integrity |median333.5 ms,326.4–337.9 |
| Memory dictionary build after parse |1.25 ms,one sample |
| Whole index hash/reopen/feature select |median3.85 ms,3.73–5.53,warm OS |
| Fresh process/hash/open/count |median94.88 ms,91.65–101.85 |
| Compact projected JSON/SQLite |2,631,413/3,055,616 B,SQLite+16.1%;selected canonical files9,442,905 B |
| Traced peak |29.96 MB,includes setup/bodies;excludes native/OS allocations |

Warm medians file parse/scan / memory / SQLite in ms: feature 181.088/0.003/0.124; G0 history 159.446/0.003/0.201; reverse-use 158.383/0.002/0.065; narrow exact geometry 171.002/4.273/4.237; broad 167.968/6.732/5.509. Avoided parsing is clear; tiny memory/SQLite differences do not justify a speedup claim. File baseline is compact projection, not original components. Tracemalloc inflates parse/encoding, small counts/warm OS/concurrent regressions limit absolute interpretation. No arbitrary score combines bytes,operations,time.

Prior distinct campaigns: Tryfan213 ms integrity/670 ms administrative publication;Swiss sweep9.61 s;112-publication full/packed8.58/10.08 s; Riff startup1.401 s/point44→10; scoped Swiss3.28/2.17 s; temporal complete envelope~211–230 ms; five distinct publications11.10–12.50 s each including proof-only full numerical replay; complete fresh historical replay60.54 s. These cannot be added as one benchmark. New95 ms metadata count is not runtime restart with payload validation.

## 15. Chosen architecture

| Responsibility | Concrete choice | Limitation/revisit trigger |
|---|---|---|
| Payloads |Native files/configured roots,exact size/hash;staged new writes |Placement changes when active capacity/I/O blocks real work |
| Qualified metadata |Versioned immutable canonical JSON,scientific bodies unchanged |Partition large collections when bounded parsing becomes a constraint |
| Indexes |Rebuildable SQLite plus native exact spatial/temporal checks |Larger real workloads may change access structures |
| Dependencies |Canonical source/use/result edges,SQLite reverse/scope candidates |No graph service requirement |
| Components |Explicit immutable family/region qualified identities |No universal component size |
| Publications |One complete composite manifest |Disconnected regions are permitted |
| Root |Atomic same-directory current+eligibility replacement |Process model;revisit only for actual durability/writer requirement |
| History |Direct exact membership/retained revisions and locators |Unavailable bytes explicitly fail |
| Processing |Node domain CLI/library,Python native/catalogue worker |No always-on scheduler |
| Recovery |Canonical closure verification,owned retry,index rebuild/scan |Complete hybrid tests required in slice |
| Serving |Typed pinned library and JSON CLI |HTTP only for a real consumer |
| Integrity |Full current byte/metadata/dependency/closure checks |No receipt/hash policy optimization |
| Data roots |Internal metadata/active data,optional configured archive |External unavailable is explicit |
| Migration |Compatible versioned adapters/rebuild index,retain old bytes |Scientific identity is not SQL schema version |

Database role, authority, language ownership and interface are selected; no essential infrastructure menu remains unresolved.

## 16. Rejected alternatives

Per-command full scan alone repeats hydration; retain as reference/fallback. Universal individual components recreate membership overhead. Large raster/imagery BLOBs lose native addressing without demonstrated benefit. Authoritative SQL acceptance could simplify a future runtime but adds a larger authority/migration boundary now. PostGIS, graph store, cloud service, broker/workflow platform/public HTTP add unsupported requirements. Full numerical replay on ordinary queries is proof validation, not a serving plan.

No receipt packing, incremental hashing/custody certificates, source fusion or universal partitions. Revisit only after material measured workload/operational constraints, not possible optimization.

## 17. Module/interface boundaries

Proposed modules, not created: `identity/contracts`,`volumes/artifacts`,`canonical-store`,`catalogue`,`native-adapters`,`derivation/lifecycle`,`jobs`,`publication`,`query-session`,`cli`. Explicit injected contexts replace mutable global arrays/hooks. Distinct typed ArtifactId,QualifiedRevisionId,MethodRevisionId,ComponentId,GenerationId prevent collapsing identities that all happen to contain hashes.

`ArtifactResolver.resolve(ref)` reports locator/availability; `CanonicalStore.getVerified(id)` verifies immutable bytes/schema; `Catalogue.candidates(pin,predicates)` returns IDs/binding/counters; query loads original qualification and exact predicates. `Lifecycle.affected(changes,context)` returns scope; `Method.execute(uses,parameters)` returns qualified receipts/results; `Publication.stage/validate/commit` alone owns visibility; `PinnedSession.query/inspect` never changes its generation. Errors distinguish unavailable,identity-mismatch,unpublished,unknown-qualification,invalid-context.

Catalogue owns SQL/extractor versions; domain owns scientific rules. Python stdlib SQLite avoids native npm dependencies and uses the existing GIS environment. Installed Node24.11 `node:sqlite` is marked active development in its version-specific official docs; it is an interchangeable future adapter, not required. Keep Node API stable if binding changes. No synchronous command implies service concurrency guarantees.

## 18. Logical layout

Proposed only:

```text
runtime/
  objects/sha256/<prefix>/<hash>.json       # canonical qualified/components
  publications/<generation>.json          # explicit references
  eligibility/<hash>.json                 # committed membership nodes
  current.json                            # authoritative current+eligibility
  jobs/<operation>/plan.json, receipt.json # operational,not observation time
  indexes/<schema>/<epoch>.sqlite          # sealed derived shared projections
  indexes/<schema>/<epoch>.receipt.json    # digest/extractor/coverage binding
  index-current.json                      # advisory readiness only
  staging/<operation>/                     # owned incomplete state
configured public/prepared/archive roots  # native retained payloads
configured scratch                       # bounded disposable processing
```

Preserve imported exact IDs/source receipts. Absolute location only in config/materialization. Versioned adapters never rewrite old scientific bytes. Catalogue joins generation→exact component→revision, not region→mutable latest.

## 19. Transaction/recovery protocol

First slice must implement/test:

1. Acquire one-writer lock/operation; capture predecessor. Resolve required volumes, estimate scratch/output.
2. Prepare in owned staging; verify inputs, execute accepted methods, finish manifests, flush/finalize immutable outputs. Orphan objects are not publications.
3. Write verified metadata/uses/results/components and candidate explicit publication. Full artifact/metadata/cross-reference/freshness/closure validation; incompatible stale current results reject.
4. Build private catalogue epoch from verified canonical history and explicit membership. Shared unique bodies; transaction/constraints/completeness and qualification oracle; integrity-check,close/hash/seal/install. Full rebuild is acceptable for the small slice and must be measured, not claimed selective.
5. Persist candidate eligibility nodes/pending root; recheck predecessor/lock/final closure. Advisory index pointer may name an epoch containing both old/new state but never grants eligibility.
6. Flush/atomically replace canonical same-directory root **last**, sole visibility commit. Pin canonical eligibility before querying bound catalogue. DB/staged manifest existence never means committed.
7. Record completion. If interrupted after root switch, canonical committed closure prevails even if job receipt incomplete; do not publish twice. Earlier interruption retains old root; cache readiness can rebuild independently.

No cross-filesystem/database transaction is claimed. Immutable epochs isolate readers. Later epochs share unique revision projections across retained generations; old index files are dispensable after readers close, canonical history is not. Future full-build cost may justify finer shared projections, not a prerequisite research task now. Missing catalogue cannot produce false absence: rebuild/explicit bounded scan or fail. Missing canonical closure never uses an index body as authority.

## 20. Scientific qualification preservation

DTM≠DSM; LN02/EGM2008/unknown Tryfan vertical references remain distinct. Visual/surface height is not bare-earth truth. Categorical counts retain mapping/nodata meaning. Overlap is not agreement. GLAMOS survey/source release and Exe event/month/observation/source dates remain separate; unknowns/precision honest. Administrative knowledge correction is not physical change.

Supersession preserves old claims,methods,input-use and rights. SQL shortlists; original qualification determines exact eligibility. Source hash establishes identity, not authenticity,custody,physical truth or legal clearance. Evidence gaps never imply absence. No reconciliation/ranking/universal ontology/new method introduced.

## 21. Reusable versus research-only

Reuse pure identities/validators/scientific methods/native predicates/time/supersession behind adapters and reference tests; preserve frozen files. Adapt proof-only roots/kinds/templates, not mutate accepted stores. Compile accepted TypeScript methods for runtime instead of starting Vite to load them.

Do not inherit globals, fixed task templates or exact pilot validators as a universal registry. Keep independent proof oracles for regression. Disposable SQL is not final runtime schema; its direct edges and known-time projection test indexing mechanism only. Ordinary runtime must keep required validation guards, while proof-wide fresh numerical replay remains explicit audit/testing.

## 22. Migration approach

Separate runtime root/import manifest,read-only retained references; migrate one slice,not every experiment. Original scientific/source/preparation identities and rights unchanged; new registration/publication envelope IDs remain traceably distinct. Version adapters and compare accepted/native outputs. Original stores/reports untouched.

Do not masquerade new runtime IDs as old pilot generations. Log import mapping. Broader migration waits for rollback/recovery/volume/pinning tests. Rebuild index,never destructively upgrade canonical records. Rollback selects an already validated committed closure with logged operation,retaining intervening histories.

## 23. First-runtime implementation plan

**Exactly one next task: Atlas maintainable local runtime — first end-to-end vertical slice — NOT BEGUN.** Uncertainty: can explicit modules implement real storage→registration→derivation→publication→pinned query→history without proof globals,machine identities or duplicate authorities? Required scientific/visibility semantics already have bounded evidence; this has higher value than another optimization.

Prerequisites: this decision,frozen contracts,unchanged Tryfan reference and Riff prepared revision `357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb`,existing native environment,isolated configured runtime/scratch. External drive unnecessary.

Retained boundary: exact read-only Tryfan reference plus selected four-km² Riff fixture/twelve inputs. Import complete qualifications/support but compute only a bounded accepted Horn slope→planar ratio chain on one declared stencil and one native WorldCover summary support. Retain unchanged Tryfan reference. A controlled qualification revision on the stencil yields G1 from G0,not a physical observation. Include one real dated GLAMOS record and unknown terrain time for physical/knowledge inspection. Do not migrate all184 results or acquire data to fill the slice.

Required interfaces: configured artifacts,canonical store/contract adapters,catalogue builder/binding,native methods/actual-use receipts,scoped lifecycle,one-writer publisher/eligibility,pinned query and CLI. Permitted implementation: isolated offline modules/schema/adapters/tests/commands, no production browser/service. Commands to implement: `doctor`,`import`,`derive`,`publish`,`query --generation`,`inspect`,`replay`,`recover`,`rebuild-index`. These are planned, not available commands.

Acceptance: qualified identities/values/support/rights and provenance agree with accepted independent oracles; scoped/full derivation agrees with accepted tolerances; unchanged region/components reused; G0/G1 pins/history reproduce fresh; staged/invalid/stale hidden; interrupt before/after index installation/root switch; missing volume/index/canonical/schema mismatch explicit; rebuild gives identical qualified answers; full validation retained; cost/storage/restart measured. Tests cover scientific/native predicates,unknowns,index completeness,reverse scope,lock/root races,recovery and process failures, not implementation mirrors.

Protect all accepted evidence/proofs/contracts,42 statuses,113 hashes and production Atlas/Weather/Traverse;no S7/private/cloud/receipts. Stop after the two-generation real-data slice,setup/recovery documentation and regressions. Do not migrate the archive,build general ingestion,add HTTP,expand regions or begin another runtime task. Deliver bounded reusable slice plus readiness decision.

## 24. Risks/limitations

Hybrid root/index protocol is selected,not proven by the DB comparison: readiness races,lifetimes,fallback must be tested next. Small tracemalloc results do not prove arbitrary-region memory or total latency. Full build/whole index seal reads canonical metadata/catalogue; unique retained history adds footprint/build work despite zero-ancestry lookup. Keep unique component bodies shared,not copied per publication. Full publication validation remains population-wide.

Stable local files/trusted expected metadata/one writer/fsync/rename are custody assumptions; SQLite does not establish hybrid power-loss guarantees. External performance unmeasured. Existing sampled derivations are not dense truthful reconstruction. Two languages require reproducible setup/versioned messages. Larger metadata,dense time,actual source corrections,multiple writers or real remote consumers may change architecture; none blocks this slice.

## 25. DECIDE NOW

Keep scientific identities,rights,input-use/method dependencies,clock roles/unknowns,immutable supersession. Separate authority from projection and identity from locator. Exact predicates follow conservative candidates; complete eligibility precedes pins; one root/full validation. Missing/corrupt/staged state explicit. Accepted evidence/production boundaries protected. Begin the bounded runtime slice next,not another optional optimization.

## 26. PROVISIONAL DIRECTION

Filesystem payload/canonical components/publications plus sealed rebuildable SQLite catalogue; Node domain library/CLI,Python native/catalogue worker,no daemon/HTTP; laptop metadata/active data,optional configured archive. Moderate family-specific components,reverse scoped candidates,native geometry/windows. Scan fallback/reference;full validation adequate. This is a concrete reversible local choice,not final global architecture.

## 27. DEFER PENDING EVIDENCE

Cloud/hosting,PostGIS/graph/distribution,multiple writers,public/local HTTP consumers,full custody/backup operations,external performance,dense global spatial/time,automatic retention/GC,incremental catalogue-build optimization,authoritative SQL acceptance. Actual requirements or constraints must justify revisiting. Scientific fusion,continuous validity/provider correction history separate. Appearance unresolved/non-blocking; Swiss multiview parked.

## 28. REJECT

Reject infrastructure menus replacing decisions; DB row granting publication; claimed filesystem+DB atomicity; SQL-only unqualified truth; absolute drive identity; raster BLOB/per-cell catalogue default; rewritten history; unknown universal temporal matches; stale=false; gaps=absence; hypothetical receipt reopening; global claims from tiny timing; adoption by copying proof globals.

## 29. Regression results

The [validation receipt](atlas-local-architecture-validation.json) records **61 safeguards and 446 tests passed**, with fresh relevant inherited tests and eight comparison tests,source/preparation reproduction,semantic/application types,lint/build and protections/navigation. Guard all starting non-navigation tracked files,42 statuses,113 hashes,17 Tryfan store files,six Riff prepared artifacts,unit/source receipts,66 Exe files and complete accepted temporal store. Previous multi-region/dependency stores remain verified/present. No accepted proof/contract or production change;no acquisition/private/S7/payload DB in Git/runtime implementation.

Full diff/untracked review is confined to decision/compact measurements/disposable comparison/check code and five navigation documents. Development log append-only. All prior conclusions unchanged. Exact totals/timings in final receipt,not inherited claims.

## 30. Overall result

**C — DECISION READY.** Actual regional/temporal/lifecycle workloads plus bounded comparison support concrete local architecture. No essential storage/processing/serving/authority decision remains unresolved. Complete selected protocol must be implemented/tested in the slice,not begun here. Tryfan remains CLOSED / ACCEPTED. This is offline local implementation readiness,not global performance,production durability or application integration.

## 31. Exactly one next bounded Atlas task

**Atlas maintainable local runtime — first end-to-end vertical slice — NOT BEGUN.** Section23 supplies uncertainty,interfaces,exact retained boundary,permitted implementation,acceptance,protections and stop; [next-task record](../../scripts/atlas/local-architecture/next-task.json) is the current selection. No additional optimizer/architecture experiment is scheduled first. Stop this task after regressions,commit/push and clean upstream confirmation; do not begin the slice.
