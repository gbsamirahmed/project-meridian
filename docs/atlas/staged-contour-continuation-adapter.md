# Staged contour continuation adapter

**12 October 2026 — implementation and synthetic validation only. Genuine pilot remains Outcome C.** This supersedes the execution sequence proposed in the [pipeline recovery](contour-pipeline-recovery.md), without changing its historical results. No genuine stage, source acquisition, application operation, commit or publication has occurred.

## Stage boundary and product meaning

[The adapter](../../scripts/atlas/contour-pilot/staged_continuation.py) supports two separately authorised stages:

1. Derive **Swiss EGM2008 diagnostic** and **native Copernicus** once each. The former applies the pinned full compound LV95/LN02 → CRS84/EGM2008 operation to the strict 2 m Swiss reconstruction; the latter preserves native DSM point-post support and 250 m global-only context. Compare source-specific geometry and calculate the qualified height diagnostic. Retain canonical products and stop with an owner-review checkpoint.
2. After separate approval binding that checkpoint and its successful controller closure, derive both missing products again and independently recompute each of the three Swiss variants once. Compare each fresh contour level's counts, closed-line counts and canonical payload SHA-256 against the retained masters. This is **seven new derivations** across both stages, not seven new canonical products.

The seven input pins, 2 × 2 km EPSG:2056 core, 256 × 256 quad ownership, native 0.5 m comparison, strict/smoothed 2 m fields, 2000–3200 m levels every 10 m and identical 20 m subsets remain unchanged. Newly derived geometry uses the existing numerical extraction/stitching method; no simplification or DSM/DTM fusion is performed. Replay is independent recomputation with the same algorithm, not independent-algorithm conformance. Source meaning and operational method hashes are separate; historical method receipts are not rewritten.

## Immutable history and file transactions

All **seven inputs** and **867 retained files / 64,250,005 logical bytes** were verified against their existing seals before implementation. Historical geometry remains:

| Component | Vertices |
|---|---:|
| Canonical Swiss masters | 953,147 |
| Completed extraction fragments | 956,431 |
| Incomplete transformed fragments | 83,331 |
| Retained total | 1,992,909 |
| Already removed control writes | 6,962 |
| Historical cumulative charge | **1,999,871** |

[StageStore](../../scripts/atlas/contour-pilot/staged_store.py) seeds these roles and charges from the sealed inventory. It accepts only a fresh owned child, rejects unknown/missing files, reparse points and changed immutable evidence, and reconciles the **whole** owning directory. No historical file is disposable.

Extraction fragments and verification masters are explicitly disposable **new** files. Each fresh level is numerically checked during extraction, stitched, checked for simple/valid closed geometry and partition reassembly, then compared. A flushed/fsynced atomic progress receipt precedes retirement. Successful comparison hashes and counts survive deletion; cumulative write charges do not decrease. Stage 1 canonical masters are never retired. A mismatch retains the fresh failing level and unprocessed staging, with an incomplete receipt; no success checkpoint is published. An interrupted receipt transaction preserves its previous version and `.pending` evidence. An interrupted session is not silently resumed or cleaned up.

## Accounting and enforcement

Reservations precede serialisation and declared coordinate workspaces. Refused writes leave no successful charge; uncertain rollback poisons the ledger. Stage 2 inherits successful cumulative writes, work counters, storage, effective member cap and controller-measured active time. Historical processing-work counts are unknown and are **not fabricated**; the extracted/loaded/stitched counters below count new work only. Historical successful write charges remain included and unclassified by write-role where the old receipt cannot resolve them.

| Unapproved shared ceiling | Seed / available headroom | Stage use |
|---|---|---|
| Canonical final: 1,250,000 | 953,147 / **296,853** | Only one canonical copy of each missing product |
| Simultaneously retained: 3,500,000 | 1,992,909 / **1,507,091** | History + new canonical/staging + current replay level |
| Cumulative writes: 6,500,000 | 1,999,871 / **4,500,129** | Every successful new fragment/master write, including retired replay files |
| New extracted: 2,000,000 | 0 | All seven derivations; repeated extraction counts again |
| New loaded: 6,000,000 | 0 | Every geometry read for stitching/comparison, including repeated reads |
| New stitched: 2,000,000 | 0 | Fresh stitched master coordinates across both stages |
| Temporary: 200,000 | 0 | Simultaneously reserved logical coordinates, including native output and serialisation copies |
| Whole-directory bytes: 150,000,000 | 64,250,005 / **85,749,995** | History, new geometry/control files and 65,536-byte receipt reserve |
| Working set: 512 MiB | Conservative controller/member allocation | Actual process tree, lifetime peaks and allocation guards |
| Additional active time: 1,200 s | 0 new seconds | Setup, hash checks, worker, comparisons and closure across both stages; owner waiting excluded |

Known Swiss verification alone writes **1,909,578** coordinates: 956,431 fragments + 953,147 masters. It leaves **2,590,551** new write coordinates for both missing products' two derivations. If `F` and `V` are their combined first-derivation fragment/master counts, deterministic replays require `2(F+V)` writes. Extraction leaves 1,043,569 coordinates for `2F`; stitching leaves 1,046,853 for `2V`, while canonical headroom imposes the stricter `V ≤ 296,853`. These are refusal conditions, not predictions of missing-product density.

Known Swiss fragment loads plus both 20 m Swiss comparison passes charge **2,064,443** loaded coordinates; missing-product stitching/comparison loads remain unknown. Streaming the native replay level, rather than retaining its full new master, bounds the known peak at **2,973,210** stored coordinates if missing canonical geometry fills its allowance: history + 296,853 + 664,623 native fragments + largest native level 18,825. Headroom is 526,790. Missing-product fragment sizes, generated bytes, diagnostic cost and total genuine runtime still need Stage 1 measurements; no worldwide extrapolation is justified.

Raster scalar values are not contour-coordinate counts. The exact legacy million-sample height diagnostic retains scalar differences for quantiles; a conservative 64 MiB byte preflight now precedes its reader/array creation. It may refuse under the member cap. Coordinate reservations are not a census of internal Python/GEOS allocations; actual memory/private-commit guards remain necessary.

## Controller compatibility and remaining blockers

[The dormant controller](../../scripts/atlas/contour-pilot/supervise_stage.py) uses the installed base interpreter and existing scientific environment, avoiding a venv redirector as the controller. It starts the worker in the containing Windows job before execution. A worker-ready handshake locks and verifies the actual scientific process **before numerical imports**. The controller observes assigned descendants, monitors resident settings and lifetime peaks, enforces a shared deadline, kills the whole job and verifies handle/job cleanup. Worker attempts to relax the resident cap after acknowledgement cause failure; its local guard cannot request a larger cap. Parent-owned process/job private-commit caps cannot be raised by the worker. Polling can detect a resident-setting reset rather than making the Windows setter impossible to invoke.

The **128 MiB member default has not increased**. It was an intentional conservative allocation: controller 128 MiB + at most three 128 MiB members, job private commit 384 MiB. This task adds a per-member private-commit cap of the same 128 MiB, a stricter guard than before. Effective caps appear in configuration and receipts. Startup settings reset by Python launchers are reasserted before the handshake; post-handshake changes refuse the workload. Atomic controller receipts have a pre-write byte reservation and are published after verified cleanup. Missing/failed termination or unobserved process identities cannot count as success.

**The supplied [profile](../../scripts/atlas/contour-pilot/staged-profile-proposal.json) is explicitly unapproved and refuses execution**, for two independent reasons:

- A 256 × 256 quad allocation reserves at least **262,144** endpoint coordinates before ContourPy runs, exceeding the proposed 200,000 temporary ceiling. Serialisation can require additional simultaneous workspace; 262,144 alone is not a demonstrated sufficient replacement. A synthetic ring case reserved 262,548. The adapter does not reduce native resolution, partition size, extent or intervals to fit.
- The recorded genuine peak was **139,104,256 bytes / 132.7 MiB**, already above 128 MiB. This is not proof a revised worker fits the current cap. The diagnostic byte preflight and stricter commit cap may also refuse. Any new member/process allocation must be reviewed explicitly within the 512 MiB aggregate target, not silently adopted.

## Synthetic evidence and limitations

Final synthetic results are recorded in the [adapter receipt](../../scripts/atlas/contour-pilot/staged-adapter-receipt.json). Tests cover immutable seeds, reservations/refusals, shared cumulative/storage counters, bytes after retirement, partial transactions, changed geometry/profile/checkpoints, deterministic replay, closed contours spanning several windows, partition/nodata controls, disabled simplification, actual-worker memory stops, deadlines, cap overrides and descendant cleanup. Genuine readers remain dormant; the proposed profile is refused without raster imports.

**74 tests passed in 65.25 seconds.** Runner lifetime peak was **98,316,288 bytes (93.8 MiB)**; controlled children are separately measured, with maximum conservative controller/tree lifetime-peak sum **162,086,912 bytes (154.6 MiB)**. Measured owned synthetic temporary-file peak was **383,540 bytes**, including disposable synthetic histories; retained worker controls totalled 10,918 bytes. Maximum native generated output was 202 coordinates, versus a conservative simultaneous reservation peak of 262,548. These small fields validate enforcement/geometry cases, not genuine workload sizing. No genuine raster or provider was accessed.

All nine supervision checks passed again after exposing the aggregate ceiling in receipts. Read-only profile inspection returned `approved: false` / `readyToAttempt: false` with both compatibility blockers. A deadline stop includes verified cleanup; its final elapsed receipt can exceed the deadline by termination/closure time and must report failure, never retroactive conformity.

Static/preservation validation: 26 Python ASTs, eight JSON files, 45 document links/anchors, all 113 protected hashes, all 42 canonical research statuses, seven inputs and 867 genuine file hashes pass. The append-only development log retains prior authorised work. No genuine output, historical receipt or input pin changed.

Full-window synthetic tests use an explicit **300,000-coordinate synthetic-only** profile to exercise extraction/streaming; this is not approval of a genuine ceiling. Failed development receipts remain external, including a missing window counter, launcher working-set resets, premature descendant exit under a worker-owned nested job, one worker exiting before its intended partial file, and a clock-boundary assertion. Focused supervision passed after the controller-owned bootstrap correction; the unclassified early worker exit is preserved as a failure, not concealed as a successful partial-output test.

No synthetic success establishes genuine performance, all-level source topology, datum compatibility, source accuracy or complete scientific repeatability. Rejected whole-product simplification evidence and all genuine receipts remain unchanged. Existing Swiss unsimplified masters remain valid **single-run** evidence only.

## Exact next owner decision — no execution authorised

**Stage 1 is implemented but not ready to launch under the supplied profile.** Review the temporary-reservation policy and a scientifically plausible member/commit allocation first, retaining the aggregate 512 MiB target. Any revised ceilings must be explicit, separately configured and tested; current proposed numbers are not approved.

Then approve only two missing-product derivations once, qualified geometry/height comparisons and the immutable checkpoint in one fresh session under the accepted profile. Stage 1 must stop for owner review with actual counts/bytes/memory/time. Stage 2 needs a new approval binding the exact successful worker checkpoint **and controller closure**, remaining shared budget and five verification derivations. No simplification, source substitution, tile packaging or application integration is included.

Read-only inspection and synthetic validation require no genuine stage approval:

```powershell
& $terrainControllerPython -B scripts/atlas/contour-pilot/supervise_stage.py `
  --profile scripts/atlas/contour-pilot/staged-profile-proposal.json --inspect
& $terrainPython -B scripts/atlas/contour-pilot/check_synthetic.py `
  --output "$terrainData/experiments/atlas/staged-contour-adapter-v1/new-checks"
```

Use an existing environment and fresh external check directory. No genuine execution command is authorised here. Offline precomputation remains the [architectural direction](precomputed-terrain-products.md); no delivery format or service is selected by this adapter.
