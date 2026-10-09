# Atlas local runtime deterministic derivation and scoped lifecycle integration

2026-10-09.

## 1. Executive result

**C — LIFECYCLE INTEGRATION SUCCESS**, bounded to the retained local single-writer model. The reusable runtime now executes accepted Riffelhorn native DTM slope and its planar-area summary, records qualified immutable outputs and exact dependencies, stages scoped updates, fully validates and publishes coherent generations, and queries old/new pins after restart. It does not change accepted stores or production Atlas.

[Measurements](atlas-local-lifecycle-results.json), [protection receipt](atlas-local-lifecycle-validation.json), [frozen design](../../runtime/atlas/lifecycle-plan.json), [library/CLI guide](../../runtime/atlas/README.md) and [focused tests](../../runtime/atlas/test-lifecycle.mjs) make the result reviewable.

## 2. Starting checkpoint

Clean main at `5842fde7d86c5623906721cd21e67aeb80552c6f`, fetched origin and confirmed upstream origin/main at 0/0. No newer legitimate work required reconciliation. [Baseline](atlas-local-lifecycle-baseline.json) captures the starting tracked-file identities and design hash before runtime edits.

## 3. Frozen scope

The [plan](../../runtime/atlas/lifecycle-plan.json) was written before implementation. Use exactly the 16 accepted `dtm-cluster-*` probes from the [regional dependency plan](../../scripts/atlas/regional-dependencies/plan.json), two accepted quantities per probe, and explicit stride1/2 parameters. Fork the existing current seven-component multi-region publication into an owned separate directory. Require exact scoped/full identity agreement, independent numerical agreement, unpublished failure states, historical restart and unchanged protections. No acquisition, new method, terrain fusion, generic workflow engine, production application or infrastructure.

## 4. Selected accepted derivation

Reuse the frozen [Horn/ratio implementation](../../scripts/atlas/qualified-query-proof/proof.ts), SHA256 `bcd85ff5101ddd079e2e4d3c0c32054b6a75c0525797bc9258a8cfe9e59e3bcc`, through the accepted method loader. Method revision `7fe3f0c3ed6152177dfcb97b7be190dcda8fd45ddb18b27c2a8eb2b2b398f8d9`. Horn consumes a finite 3x3 native height stencil; the planar ratio consumes the exact slope result. No algorithm was rewritten.

## 5. Real retained input population

Retained prepared revision `357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb` contains twelve verified inputs (120,347,916 bytes) and six prepared artifacts (5,605,110 bytes). Four original Swiss DTM bindings are registered; the selected 16 real stencils consume one original tile, `swissalti3d_2024_2624-1091_0.5_2056_5728.tif`, SHA256 `c68c305e4a142da416b46b555a80916ecc52f8fa50bf1efd5cd2c3f24f9cd4bc`. The other three DTM identities remain accountable but unconsumed by this narrow slice. The accepted Tryfan 310 artifacts and five families, Riffelhorn 44 native records and all source/preparation receipts remain unchanged.

Base current generation is `d58e5c911f1baaaec90f2d8a863ad070c6cc28b750f45709bf1b09d633d2e905`; the three earlier base generations remain readable. [Source assessment](atlas-regional-expansion.md), [preparation](atlas-riffelhorn-preparation.md), [retrieval](atlas-riffelhorn-retrieval.md) and [multi-region proof](atlas-multi-region.md) establish the input boundary.

## 6. Scientific meaning and limitations

This is local represented-heightfield slope in degrees and a dimensionless local planar represented-surface/map-plane ratio. It is not traversability, physical accuracy, independent observation, true rough-surface area or calibrated material property. Native DTM is distinct from DSM. EPSG:2056 horizontal metres, source-documented LN02 / EPSG:5728 vertical reference, native band metres and cell centres are retained; no resampling, interpolation or vertical transformation. Exact stencil observation epoch remains unknown; dataset edition dates are not observation dates. Missing data is rejected rather than treated as absence.

## 7. Runtime processing interface

[index.ts](../../runtime/atlas/index.ts) exports `createWorld`, `stageDerivation`, `inspectLifecycle`, `validateStage`, `publishStage`, `recoverWorld` and `fullDerivationReference`. [lifecycle.ts](../../runtime/atlas/lifecycle.ts) coordinates explicit-root verified input resolution, accepted processing, immutable outputs, scoped policy and publication. [lifecycle-model.ts](../../runtime/atlas/lifecycle-model.ts) owns the finite qualified dependency semantics. These are reusable library functions and CLI commands; research harness invocation is not required.

## 8. Python worker contract

[worker.ts](../../runtime/atlas/worker.ts) owns a session-local Python process; [worker.py](../../runtime/atlas/worker.py) adds one versioned terrain operation. Request `atlas-runtime-terrain-request/v1` contains only bounded task IDs and stride parameters, on an explicitly initialized and fully verified data/preparation context. Response `atlas-runtime-terrain-response/v1` contains native sample rows, exact cell scopes, source registry, independent oracle, versions and logical counters. [terrain-worker.py](../../runtime/atlas/terrain-worker.py) adapts rasterio reads without changing the accepted arithmetic. It verifies native grid/CRS/units, nodata and exact centres. Python 3.12.6, NumPy 2.5.3, rasterio 1.4.3, pyproj 3.7.2 were captured. No daemon, implicit mutable dataset selection or network source is used.

## 9. Method and parameter identity

Method revision is exact and frozen. Parameters distinguish stride1 at 0.5 m from declared stride2 at 1 m. The latter is subsampling of native cells, not a new terrain model or increase in accuracy. Task IDs and support coordinates are constrained to the accepted 16 probes. Invalid methods, unknown tasks, unsupported fusion or stride are rejected. The accepted NumPy sampling/oracle source is SHA-pinned separately.

## 10. Derived artifact identity

Each canonical JSON result has a SHA256 content address under `artifacts/<sha>.json`. Its body identifies task, property, method/revision, parameters, exact inputs, support, native qualifications, rights and scientific meaning. Slope embeds the nine actual cells and values; ratio refers to the exact slope artifact. Use identities hash native cell records plus their projected source/knowledge qualifications. A two-component lifecycle/derived extension references 32 active immutable results. Superseded files are retained rather than overwritten. Each result also refers to an immutable execution record capturing actual worker/coordinator versions, sampler/oracle source hashes, tasks and output identities. These records are scientific-processing provenance, not validation receipts. Full validation is never skipped because they exist.

## 11. Qualification propagation

Every result retains complete source/product and retained artifact identity; the pinned response also exposes the unchanged regional registration and its exact prepared revision/artifact identities, preparation method and rights boundary. Original paths are configurable-data-root locators. Source documentation, native headers, preparation qualification, rights/attribution references, consumed spatial support and temporal unknowns are retained. Administrative notices are explicitly knowledge qualifications, not physical events. Local notices propagate only through actual consumed cells; full-source notices are intentionally global to that source. `bounds:null` means an explicit whole-source notice, never an inferred unknown spatial scope. Source hashes establish content identity, not upstream authenticity or physical truth.

## 12. Dependency relationships

The slice registers 4 source nodes, 16 qualified-use nodes and 32 result nodes:52 nodes,48 explicit edges (16 source-use,16 use-slope,16 slope-ratio), maximum depth3. Three registered sources have no consumed edges; the one consumed source has fan-out 16. Uses and slopes have fan-out 1; ratios 0. Each derived result has immediate fan-in 1; no cross-region physical edges. Use nodes are content-addressed embedded records rather than an extra physical file per use. `derive inspect` exposes graph edges and the affected closure. Existing accepted Tryfan understanding remains a separate unchanged base component; these are slice-specific graph counts, not the full Atlas graph.

## 13. Invalidation cases

The frozen cases are initial 32, no-op 0, a controlled cell-local source qualification revision 8, one-probe stride revision 2, unrelated Tryfan administrative notice 0, source-wide qualification revision 32, and identical-notice 0. The local bounds are `[2624350,1091350,2624350.5,1091350.5]`; four overlapping stencils and their four downstream ratios are affected. Independent tests enumerate native centres to establish expected closure. No physical source bytes are changed. An upstream qualified-use revision is therefore a knowledge revision; a newly surveyed physical dataset is not simulated.

## 14. Scoped recomputation

`stageDerivation` samples only affected terrain tasks and invokes accepted Horn/ratio on those rows. Local correction processes 4 stencils (36 cells), parameter correction 1 (9 cells), source-wide 16 (144 cells), no-op/unrelated 0. Local update reuses 24 results, parameter update 30, unrelated 32. Unaffected revisions and base component identities remain identical. Stale means changed derivation assumptions, not scientifically false historical content. Old results are current within their original pinned context and remain independently readable.

## 15. Full recomputation oracle

`fullDerivationReference` starts with all 16 tasks and compares exact current content identities, without writing artifacts or publication. All 21 measured initial/case comparisons agree across three isolated worlds. Numerical arithmetic is checked against independently expressed NumPy dot kernels with 1e-10 degree and 1e-12 ratio tolerances; native inputs are finite Float32 samples promoted to double. In addition 96 actual comparisons against unchanged accepted regional derivation receipts agree. Full/scoped paths share the accepted scientific method and artifact builder, so receipt and independent arithmetic checks supplement that agreement rather than claiming wholly independent implementations.

## 16. Publication workflow

[publication.ts](../../runtime/atlas/publication.ts) implements an owned separate canonical writer using the accepted component/publication/root and radix membership schemas. Seven unchanged accepted components plus `terrainLifecycle` and `terrainDerived` constitute one coherent nine-member context. The native Tryfan scientific closure is reconstructed unchanged; the added qualified closure contributes to the exact publication identity.

Stage writes synced temporary immutable objects and installs them with same-volume atomic no-overwrite links. It never advances a root. Publication holds a local process lock, verifies exact predecessor and ordinal, performs full native and output validation, extends committed membership without ancestry traversal, and atomically replaces `current.json` last. The prior root remains visible during work. There is no database/filesystem joint transaction; SQLite is rebuilt separately after publication. Existing canonical stores require no schema mutation.

## 17. Generation-pinned queries

`openAtlas` fully validates accepted payloads plus all 32 current outputs with fresh native recomputation. `context.derived({identity?,property?})` returns pinned qualified scalar artifacts, exact revisions, dependencies, component and generation. It uses bounded canonical selection; it does not pretend the native 49-record SQLite index contains derived scalar records. Native spatial/feature/year queries remain the accepted first-runtime path. Unsupported derived spatial/time predicates fail explicitly. Old contexts keep exact old result revisions while current advances; staged generations cannot be queried as committed.

## 18. Historical replay

Three fresh processes each open the base plus five newly committed contexts, reproduce exact result identities and qualifications, and observe no ancestry traversal. The base pin has no runtime-derived component; subsequent pins have 32 results. All three initial worlds reproduce the same initial publication identity `6f445088858b39e08e464a2d64aeb5c111e77e9babfe12d2fedbe71429b62156`. Administrative corrections alter knowledge lineage; old physical-time unknowns remain unknown. Root advancement never rewrites prior membership, source identities or derived artifacts.

## 19. Negative and failure cases

Focused tests cover missing/mismatched dependencies, invalid source/datum, method/parameter mismatch, unsupported fusion, invalid support, unknown task, worker startup/request failures, numerical corruption/nondeterminism, malformed/missing/tampered derived artifact, cycle/self-reference, stale state, incomplete membership and publication conflicts. Source availability/hash failures continue through the unchanged accepted full-validation path and inherited runtime tests.

An actual child exit 92 after writing derived artifacts leaves the old root current; deterministic retry succeeds. Actual exit 91 after full validation/membership preparation but before root replacement leaves the stage unpublished and a dead-writer lock; explicit recovery preserves the old root and permits same-stage retry. Live/ambiguous locks cannot be stolen. Corrupt/stale SQLite catalogues fail and rebuild without canonical mutation. Partial files, temporary initialization and unreferenced staging debris are not publication eligibility. No power-loss, malicious mutation or multi-writer safety claim is made.

## 20. Structural measurements

Full accepted payload validation hashes 329 artifacts/171,482,433 bytes on an initial open, excluding additional GDAL/archive reconstruction traffic. Source and output validation remain population-wide. A nine-member committed closure reads 33 membership nodes, one publication and nine components:43 metadata records, zero ancestry. Full derived structural validation reads 48 artifact bodies (16 slope checks plus 32 typed relationship checks), plus each distinct referenced execution record. An execution record is checked once within that audit. Exact scalar lookup reads its returned execution record as well; all costs are included in counters. An exact scalar query still performs that full structural audit and then reads the selected body; counters disclose this amplification.

Stage validation additionally recomputes all 16 stencils and compares all 32 bodies; its current-base validation is also retained. A publication therefore does not claim changed-state-only validation. Read/write counters distinguish artifact metadata, canonical reuse reads, JSON bytes encoded, actual newly written immutable content, membership writes, and root bytes. They are logical operations, not cold disk block traffic.

## 21. Timing, memory and storage measurements

<!-- measurements -->
| Operation | Median ms | Min-max ms |
| --- | ---: | ---: |
| Initial staging | 3960.6 | 3191.5-5699.4 |
| Read-only full derivation reference | 3889.5 | 3829.0-4043.1 |
| Full current publication open | 3497.5 | 3466.1-3512.5 |
| SQLite build | 252.8 | 244.3-260.2 |
| SQLite deletion/rebuild | 244.5 | 240.3-252.8 |
| Native point query | 144.8 | 140.2-147.6 |
| Exact derived identity query | 135.2 | 131.3-154.7 |
| Fresh six-generation historical replay | 23592.9 | 23429.5-24340.5 |

| Lifecycle case | Affected / reused | Processing cells | Scoped staging median ms | Full reference median ms |
| --- | ---: | ---: | ---: | ---: |
| no-op | 0 / 32 | 0 | 3188.0 | 3933.8 |
| local-qualification | 8 / 24 | 36 | 3879.2 | 3799.5 |
| parameter | 2 / 30 | 9 | 3898.5 | 3850.6 |
| unrelated-region | 0 / 32 | 0 | 3921.6 | 2838.4 |
| global-qualification | 32 / 0 | 144 | 3992.2 | 2901.2 |
| identical-notice | 0 / 32 | 0 | 2940.5 | 3793.4 |

Initial publication median 4151.4ms (range 3330.0-4180.7); its full-validation median 3988.7ms. Catalogue 80 KB/49 native selectors remains unchanged. Each final world is 9,464,739 bytes / 372 files, versus 8,765,880 bytes / 116 files in the copied base. Net retained canonical growth is 698,859 bytes; `artifacts` includes original portrayal assets as well as new scalars and totals 3,615,120 bytes. Node RSS observations span 247.9-259.8MiB; no combined peak is inferred.

local-qualification: actual newly written immutable content 87,565 bytes/12 records; canonical reuse equality reads 1,329,386 bytes/7 records; immutable write-candidate JSON encoded 1,416,951 bytes. Separate publication membership/root writes are in the raw receipt.
parameter: actual newly written immutable content 40,029 bytes/6 records; canonical reuse equality reads 1,329,386 bytes/7 records; immutable write-candidate JSON encoded 1,369,415 bytes. Separate publication membership/root writes are in the raw receipt.
no-op: actual newly written immutable content 0 bytes/0 records; canonical reuse equality reads 0 bytes/0 records; immutable write-candidate JSON encoded 0 bytes. Separate publication membership/root writes are in the raw receipt.
<!-- /measurements -->

Three isolated worlds, sequential repetitions, consistent real inputs, medians and minimum/maximum are used. Python restarts for each full open; the Node accepted method loader is warm after its first load, while fresh-process historical replay includes loader/startup and full validation. No timings are compared with incomparable historical research harness totals. Node RSS observations are reported, not aggregate Python/Node peak memory. Storage remains far below the flexible 80 GB laptop planning boundary; no external disk, acquisition or cloud is needed.

Selective processing is structurally smaller, but tiny stencil arithmetic is inexpensive and full validation dominates; scoped wall-clock staging is not demonstrated faster than read-only full reference here. Staging also writes/validates canonical state whereas the oracle does not. This is a correctness and usability result, not an amortization claim. No cost justifies reopening receipt or integrity optimization.

## 22. Reproducible CLI commands

The [README](../../runtime/atlas/README.md) documents explicit data/publication/catalogue/Python paths. Commands: `world init`, `derive stage`, `derive inspect --change JSON`, `stage validate --stage SHA`, `stage publish --stage SHA`, `derived --generation SHA`, existing `catalogue build/verify` and `query`, and `world recover`. `--json` is available and unknown arguments/actions fail clearly.

The [runnable developer example](../../runtime/atlas/example-lifecycle.mjs) accepts an external five-path JSON configuration, invokes the CLI in fresh processes, forks a validated store, derives, stages/validates/publishes, performs the local knowledge correction, builds the disposable catalogue, and queries both historical and current pins. It is executed by the regression runner. No manual research-harness invocation or hardcoded drive identity is required. An explicit historical selector forks that exact pin instead of silently switching to current.

## 23. Maintainability assessment

Typed `DerivationStage`, `DerivedQuery` and `DerivedAnswer` DTOs expose stable generation/result/closure fields while preserving canonical qualification metadata. Responsibilities are separated: authority resolution/full verification, scientific processing worker, finite lifecycle model, immutable publication coordinator, pinned query context and small CLI. Interfaces reuse accepted method code and native input verification instead of creating competing algorithms. Source DTOs and method pins are versioned; paths are configuration, not evidence identity. Errors have stable runtime codes and normal CLI diagnostics rather than raw traceback. Writer destinations need explicit ownership and separation from retained input/repository/cache paths. This is a bounded usable local workflow, not a generic scheduler or plugin system.

## 24. Reusable versus proof-specific code

Runtime library, processing DTO/worker, owned immutable writer, CLI, graph inspection, pinned derived query and recovery are delivered functionality. Test and measurement runners are secondary. The accepted Horn/ratio loader, native session verification and independent oracle are reused read-only from accepted modules. The sixteen fixed probes, finite method allowlist, source registry and existing seven-component base adapter remain deliberately narrow. They do not establish arbitrary ingestion, arbitrary DAG scheduling or world-scale serving.

## 25. Remaining limitations

Initial onboarding still forks a research-created retained publication; native registration is a fixed adapter and Riffelhorn source/preparation replacement is not exposed. New physical observations, full dated-revision runtime queries, additional derivation families, general spatial derived queries and large dependency populations remain outside this slice. Raw payload changes require a future qualified registration workflow, not metadata-only notice substitution. Catalogue retention and orphan reclamation are not implemented. The filesystem requires same-volume safe installation/replacement and single-writer discipline; backups and power-loss/remote-filesystem behaviour remain operational questions.

## 26. DECIDE NOW

Preserve canonical files and filesystem root as authority, full native/output validation, exact input/method/parameter identity, local scientific qualifications and immutable historical pins. Administrative revisions are knowledge changes; source epochs/unknowns and DSM/DTM/datum distinctions remain explicit. Reject stale or incomplete publication. Use reusable library/CLI processing rather than research orchestration as the user workflow.

## 27. PROVISIONAL DIRECTION

Adopt this finite worker/lifecycle/writer module boundary for the local runtime. Keep the native 49-record SQLite catalogue disposable and derived 32 scalar lookup canonical until a real workload justifies expansion. Use a configured separate owned world and fixed accepted slope/ratio workflow. The actual next gap is accountable runtime registration/onboarding, not processing microoptimization.

## 28. DEFER PENDING EVIDENCE

General source admission, new physical surveys, extra methods, dense arbitrary dependencies, full temporal runtime integration, external-volume performance, crash durability beyond process interruption, backups, catalogue/orphan retention, concurrent writers, HTTP/global serving and production integration. Defer storage/database changes until real larger workloads demonstrate a requirement.

## 29. REJECT

Dual SQLite/canonical authority; bypassing full validation with cached receipts; source fusion or unsupported physical change; treating nodata/no-result as physical absence; metadata repair that fabricates source truth; switching a historical pin to current; publishing stale dependency closure; generic workflow orchestration or cloud/distributed work. Receipt optimisation remains CLOSED. No S7 or production Atlas/Weather/Traverse modifications.

## 30. Regression results

[Validation receipt](atlas-local-lifecycle-validation.json) records **73 safeguards and 569 tests passed** (508 inherited and 61 focused lifecycle tests), the complete CLI example, runtime/semantic/application types, lint and build. Protection checks cover unchanged accepted Tryfan S1-S6, all Riffelhorn/multi-region/dependency/temporal/source evidence and reports, frozen contracts, 42 canonical statuses and 113 protected production hashes. All starting tracked files outside the exact runtime/navigation boundary are compared by Git blob identity; original external stores and retained bytes are verified. Generated canonical worlds, catalogues and logs remain external. Full diff/untracked and whitespace review precede commit; no private access, new physical evidence, S7, infrastructure or unnecessary large payload is introduced.

## 31. Overall result

**C — LIFECYCLE INTEGRATION SUCCESS.** One accepted deterministic method and downstream summary now execute through the maintainable local runtime, with explicit qualified dependencies, correct scoped lifecycle, coherent publication, pinned historical serving and process-interruption recovery. The conclusion is bounded to retained inputs, controlled knowledge revisions and a local single writer. It is not production readiness or a global scalability claim.

## 32. Exactly one next bounded Atlas task

**Atlas local runtime qualified evidence registration and regional update workflow — NOT BEGUN.** [Exact task record](../../runtime/atlas/lifecycle-next-task.json).

Uncertainty: can retained prepared regional evidence be registered and revised through runtime library/CLI boundaries without copying a research-generated publication store? Importance: this is now the concrete onboarding gap toward a broader reusable local world. Prerequisites are the accepted architecture, read/lifecycle runtime, existing retained Tryfan reference and prepared Riffelhorn manifests, and frozen source/semantic/temporal/publication contracts.

Permitted work: one bounded retained Riffelhorn registration adapter plus unchanged Tryfan reference, accountable canonical registration from source/preparation manifests, one labelled administrative regional update, exact scoped dependent handling and coherent historical publication. No new data, new method, universal ingestion platform, production or service. Deliver a documented library/CLI workflow with identity/qualification/failure/historical tests. Acceptance: no research-harness or research-store bootstrap dependency; exact lineage/rights/support/time; incomplete/invalid registrations unpublished; exact affected closure and unrelated reuse; old/new restart replay; disposable catalogue; all protections pass. Stop after that one measured/tested/documented registration workflow, commit and push. Do not begin it here.
