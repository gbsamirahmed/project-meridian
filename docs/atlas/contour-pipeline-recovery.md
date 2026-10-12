# Contour pipeline recovery — accounting, supervision and topology

**Later adapter checkpoint:** [staged continuation](staged-contour-continuation-adapter.md) replaces this record's proposed whole-product replay sequence with per-level verification retirement. Historical evidence below remains intact. No proposed ceiling or genuine stage has been approved; workspace/member-cap blockers remain.

**12 October 2026. Offline recovery validated; genuine continuation requires owner approval.** Public baseline `c952b8050c1259fe6d3f674e6f84195a3491d95a`, main/local origin 0/0. No fetch. The [genuine pilot](source-aware-contour-pilot.md) remains **Outcome C**, with three completed single-run Swiss products. This checkpoint does not complete the transformed/Copernicus experiment or promote a scientific publication.

## Preservation and diagnosis

Seven pinned input sizes/SHA-256 values and all **867 genuine evidence files** match their retained seals. The original inventory hash remains `44dd7740b36baefca97d8e2261205885e2eecd4ca816ade9feb2fb312206d481`. No raster was decoded or regenerated. Genuine fragments, masters, manifests and historical receipts were not edited. The private application repository was not accessed or modified.

The historical vertex ledger charged every successful serialisation, including staging and temporary controls. Its arithmetic was correct for **cumulative writes**, but its “stored vertices” label obscured what was retained:

| Historical component | Vertices |
|---|---:|
| Three canonical Swiss masters | 953,147 |
| Their extraction fragments | 956,431 |
| Incomplete transformed fragments | 83,331 |
| Persistent geometry total | 1,992,909 |
| Temporary control writes, already removed | 6,962 |
| Shared cumulative charge | **1,999,871** |

The next fragment was refused before writing. No original allowance is refunded or enlarged. Intermediate copies dominated the stop; simplifying final geometry alone cannot resolve it. Partial-write failures previously lacked reconciliation, and a memory/time refusal could also prevent the failure receipt from being written.

## Corrected accounting

[GeometryAccount](../../scripts/atlas/contour-pilot/accounting.py) distinguishes:

- Cumulative attempted, successful and rejected vertex writes; rolled-back writes are separate. Released disposable files never refund the cumulative charge.
- Cumulative successful writes by final/intermediate/control/diagnostic role, with inherited historical charges explicitly unclassified until a verified inventory supplies their interpretation.
- Currently persistent vertices by role and their peak, including registered immutable evidence. Final geometry and all persistent geometry have independent optional ceilings; defaults do not enlarge the original 2-million gate.
- Stage-specific processing work: extracted, loaded and stitched coordinates. Re-reading counts again; these counters are not retained-vertex counts or CPU-time estimates. Optional stage ceilings refuse work before charging it.
- Explicitly reserved temporary in-memory geometry and its peak. This is a caller-managed logical-coordinate measure, **not an inventory of every Python/GEOS allocation**. The existing 100,000-coordinate per-level bound and process-memory guards remain necessary. A continuation adapter must register combined input/output workspace before allocation.

The windowed writer retains the original cumulative 2-million allowance, classifies fragments/masters, checks actual stream byte lengths and rolls short writes back to the previous complete record. Failed rollback poisons the ledger and prevents further successful processing. Seeded evidence cannot be appended to or released. Byte accounting remains logical file size, not filesystem allocation or storage hardware usage. Continuation must inventory the whole owning directory, including controller outputs, rather than relying only on writer counters.

The genuine driver's exception path now uses its already reserved 64 KiB for an exclusive stop receipt, including current/peak worker memory, observed scratch bytes and geometry counters. This path has been statically checked; it has **not** been tested on genuine data. An OS kill may prevent a worker receipt, so the independent controller receipt is essential. Historical receipts remain unchanged.

## Actual-worker supervision

[The controller](../../scripts/atlas/contour-pilot/worker_supervision.py) creates the launcher suspended, assigns it to an unnamed Windows Job Object, and then resumes it. Descendants inherit containment; breakaway is not enabled. Job process IDs, not a laptop-wide process scan, identify workers. It retains identity handles, samples each process and reads lifetime peaks, verifies hard per-process working-set settings, applies a tree-wide private-commit guard, and includes its own memory in the receipt.

Default resident allocations are **128 MiB for the controller and 128 MiB per member, at most three active job members**; the job private-commit limit is 384 MiB. The synthetic descendant case uses four members at 96 MiB each within the same 512 MiB target. These are conservative test/controller profiles, not proof the remaining genuine work fits. Per-member caps can cause paging. A job-wide working-set setting required an unavailable quota privilege and was rejected; no privilege/system change was made.

On deadline, memory stop or controller failure, termination targets the **whole job**, even after the actual root has exited. Cleanup requires an empty job, signalled retained process handles and non-active exit codes. Missing member capture, unavailable counters or unsuccessful termination cannot produce a successful receipt. Kill-on-close provides additional containment. The old launcher-only PowerShell entry point now refuses execution.

Resident samples are not an allocation-proof predictor. The sum of individual lifetime peaks is a conservative upper bound, not a measured simultaneous peak. Newly detected members receive hard caps; a short-lived member missed by sampling invalidates the result through the job's total-process count. A reviewed genuine entry point must establish guards before scientific imports and must not later relax these maxima. Arbitrary third-party subprocess behaviour is not certified.

## Synthetic and retained-output evidence

**52 focused tests pass**, including the existing numerical/stitching/nodata/deterministic controls, staging/final/inherited charges, rejected fragments, rollback/poisoning, temporary/stage caps, immutable seeds, ring collapse, moved shared intersections, nearby contours, partition reconstruction and deterministic generalisation. Controlled workers prove actual venv-worker observation, memory termination, allocation refusal, timeout cleanup of a surviving descendant, partial-output preservation and unsuccessful-termination reporting. Test receipts verify all assigned identities and signalled handles.

Final suite: **2.88 s**, actual runner peak **97,665,024 bytes (93.1 MiB)**, measured legacy temporary-file peak **32,038 bytes**, retained worker controls **5,501 bytes**. The runner peak excludes controlled children; their separate receipts report aggregate samples and sums of individual peaks. For example the prior successful controls measured a memory-stop peak sum of 158,035,968 bytes, then verified tree termination. Test thresholds are deliberately smaller than 512 MiB. No terrain inputs or requests were used.

Failed development tests remain recorded, including the unavailable privilege, a too-small soft threshold, descendant process-count setup and missing synchronisation rights. Termination verification was corrected to wait on retained handles with `SYNCHRONIZE`, avoiding PID reuse and premature exit-code assumptions.

## Simplification decision

Per-line Douglas–Peucker `preserve_topology` preserves the individual feature, not contour-family relationships; the genuine 2 m candidate remains rejected. A conservative alternative simplifies one stitched master at a time with deterministic 2/1/0.5/0.25 m backoff. It preserves endpoints/ring anchors, simplicity, ring validity/nesting, inter-line DE-9IM relationships and shared-intersection positions (1e-9 m comparison tolerance), with a displacement ceiling. Unsafe candidates revert to originals. Generalisation precedes delivery clipping; separately simplifying neighbouring tiles is excluded.

Read-only checks cover **all lines at 2490/2500/2510 m in each product**, twice, with identical candidate hashes/statistics. No candidate geometry file was adopted or written:

| Selected family | Original → candidate vertices | Maximum displacement |
|---|---:|---:|
| Native, 36 lines | 23,883 → 23,866 | 0.2354 m |
| Strict 2 m, 3 lines | 5,304 → 1,885 | 0.4989 m |
| Smoothed 2 m, 3 lines | 4,890 → 494 | 1.9772 m |

These are algorithmic displacements, not terrain accuracy. Native compression is negligible. Checks do **not** include every other contour level, so whole-product simplification remains unresolved. Keep all genuine masters unsimplified. A globally constrained vertex-removal algorithm may be worth later investigation; polygon-coverage simplification is not automatically appropriate for separate/nested contour lines. No new package or processor is selected.

The first retained check hit its **60 s timeout**, and whole-tree termination passed. Removing redundant Hausdorff computations for exactly unchanged geometry allowed the identical scope to complete. Final strengthened check: **7.89 s worker / 8.39 s supervised**, worker peak **74,297,344 bytes (70.9 MiB)**, aggregate sampled peak **103,092,224 bytes**, conservative lifetime-peak sum **103,948,288 bytes (99.1 MiB)**. Maximum declared logical-coordinate reservation was 71,649; this is a reservation, not a measured GEOS coordinate census.

External evidence remains under `${MERIDIAN_DATA_ROOT}/experiments/atlas/contour-pipeline-recovery-v1`: preservation snapshot, `checks-9`, `retained-checks-3`, corresponding supervision and earlier failed receipts. A compact [recovery receipt](../../scripts/atlas/contour-pilot/pipeline-recovery-receipt.json) seals the evidence. No data publication, new services, packages, licences, app operations or commits.

## Exactly one proposed continuation — NOT APPROVED OR EXECUTED

**Complete the missing products and verify genuine repeatability**, using only the unchanged seven pins, core/250 m context, native 0.5 m comparison, strict/smoothed 2 m reconstructions, all 10 m levels/20 m subsets and exact compound diagnostic. No failed simplification enters the products.

1. Prepare/test a small continuation adapter that imports verified immutable masters and registers historical charges/storage. Use a standalone installed base-Python controller to avoid an unobserved controller redirector. Start guards before scientific imports; refuse extra processes, unknown files or incomplete resource receipts.
2. In a fresh `execution-4` child, derive the transformed Swiss diagnostic and Copernicus product **twice**, with full seams, elevations, nodata/support, partition, transformation/height and mixed-source checks. The partial transformed fragments remain historical, never assumed complete. Retain one canonical set and replay hashes/receipts.
3. Reuse the three existing Swiss masters for comparisons. **One explicitly authorised verification replay per Swiss variant** is required only to establish their missing genuine repeatability; compare every master payload hash/count and scientific semantics with the immutable originals. Operational code/receipt hashes will legitimately differ and must remain declared, not erased to manufacture byte equality.
4. Retire only newly created, explicitly disposable staging/replay files after their hashes/checks are sealed. Never retire historical outputs. Stop on any mismatch, unsupported seam/reference, limit or failed cleanup; no alternative sources, simplification, tiles or app integration.

| Proposed continuation ceiling | Definition / change from original approval |
|---|---|
| Canonical final vertices: **1,250,000** | Includes the existing 953,147 master coordinates; one retained canonical set, not two copies |
| Simultaneously stored vertices: **3,500,000** | Includes all 1,992,909 historical persistent vertices and new staging/replays; **increases the original allowance, requires approval** |
| Cumulative successful vertex writes: **6,500,000** | Includes the historical 1,999,871 charge; at most 4,500,129 further writes, no refund on deletion; **new approval required** |
| New extraction work: **2,000,000 coordinates** | Across all seven new derivations/verification replays; not a retained-output allowance |
| New loaded / stitched work: **6,000,000 / 2,000,000 coordinates** | Independent stage counts; expensive failed all-level simplification is not repeated |
| Temporary in-memory geometry: **200,000 logical coordinates** | Aggregate registered input/output/control workspace; retain 100,000 per-level input bound. Not a replacement for memory monitoring |
| Scratch: **150,000,000 logical bytes** | Whole owning experiment directory, including existing 64,250,005 bytes, new data/control files and reserved receipts; unchanged maximum |
| Working set: **512 MiB** | Controller plus actual workload tree, conservative member caps/peak accounting; unchanged target |
| Time: **20 minutes for the proposed continuation** | Includes setup/hash checks, controls, processing and final evidence. **Additional to the stopped attempt**, not retroactive conformity with its shared clock |
| Processing: **one numerical thread** | Seven new source derivations: two each for the two missing products, one verification each for the three retained products. No redundant two-run Swiss regeneration |

These are refusal ceilings, not density/runtime forecasts. The known Swiss verification geometry plus historical outputs can temporarily approach 3.47 million stored vertices when missing-product canonical geometry is also retained; that motivates the explicit 3.5-million proposal, not hidden removal of evidence. Transformed/global counts remain unknown and may still refuse. No new allowance is active in the current legacy driver. The continuation adapter and its complete workspace/disk inventory wiring require review and controls before any scientific execution.

Success requires unchanged source/evidence hashes, completed source-specific scientific checks, matching genuine payloads and qualified receipts, and complete resource/termination evidence. Equal transformed labels do not establish DSM/DTM equivalence or acquisition/accuracy compatibility. Global coverage, source fusion, full-product generalisation, vector packaging, offline/mobile suitability and worldwide cost remain unresolved. The [precomputed-product architecture](precomputed-terrain-products.md) remains appropriate; no delivery system is implemented.

## Repeat these recovery checks only

Final static/preservation checks pass: **19 Python AST parses, six JSON parses, 42 relative links/anchors, all 113 protected production hashes, 42 unchanged canonical research statuses, seven source hashes and 867 genuine evidence hashes**. Recovery evidence occupies approximately **0.34 MB**, including failed controls; no scientific payloads were generated. The only pre-existing tracked change is an append-only development-log entry. All other edits are confined to the authorised uncommitted contour R&D files. App builds and unrelated scientific replays were not run.

From the public repository, use the existing scientific Python/data root and a fresh child directory:

```powershell
& $terrainPython -B scripts/atlas/contour-pilot/check_synthetic.py `
  --output "$terrainData/experiments/atlas/contour-pipeline-recovery-v1/new-checks"
$terrainControllerPython = & $terrainPython -c "import sys; print(sys._base_executable)"
& $terrainControllerPython -B scripts/atlas/contour-pilot/supervise_retained.py `
  --python $terrainPython --data-root $terrainData `
  --output "$terrainData/experiments/atlas/contour-pipeline-recovery-v1/new-retained-review"
```

No genuine pipeline command is authorised by these instructions. **Stop for owner review of the proposed continuation and changed vertex/time budgets.**
