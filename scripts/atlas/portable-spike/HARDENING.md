# Atlas projection hardening — frozen desktop design

9 October 2026. Start `5528dda72acb41f641966d5c269c5a30b6a8562e`, clean public main,
fetched origin/main 0/0. No authority, fixture or source change is permitted.

## Trust and validation

The existing directory seals establish consistency, not publisher authenticity.
Retain its v1 identity and three explicit publication pins. Bound manifest/member
bytes, counts, names and JSON shape before allocation. Reject duplicate keys,
nonfinite numbers, invalid Unicode, unsafe links, unexpected files, incompatible
profiles and inconsistent qualified membership, documents, selectors and dependencies.
Verify every generation, native geometry binding and raster header before readiness.
A self-consistent malicious publisher remains outside this experiment's trust boundary.

The old reader verified on open then reopened raster paths during queries. Replace
that vulnerability with a bounded snapshot: parse metadata from the exact verified
bytes and retain verified native raster bytes in read-only GDAL MemoryFiles. Once
open, no scientific query reads mutable package paths. Later file replacement,
corruption or deletion cannot alter that reader's captured generation; a fresh open
must revalidate and reject corruption. Explicit close releases the snapshot and
subsequent reads fail. Independent concurrent readers have separate snapshots.
This is a desktop memory trade-off, not a mobile storage recommendation. File hashing
alone never claims authenticity or arbitrary future filesystem immutability.

## Local store and commit boundaries

Use an explicitly initialised owned scratch store with `staging/`, `packages/`,
`ready/` and one optional `selection.json`. Single writer; concurrent pinned readers.
Stage a bounded full copy into a newly owned temporary directory. Verify the complete
candidate, then rename it to its immutable identity directory. Atomically replace a
small ready receipt only after verification; that receipt is the readiness commit.
Selection is a separate atomic record replacement, after verifying compatibility.
An interruption before readiness leaves no new ready package. After readiness but
before selection it leaves a ready, unselected candidate. After selection the new
ready package is selected; the previous package and receipt remain available.

Installation identity selects a package, never a scientific generation. Opening
requires an exact generation; missing/mismatched pins never fall back. Every open
revalidates receipt, package identity and closure. Invalid selection fails explicitly.
Deleting a selected package first clears selection, then removes its receipt/package;
no automatic fallback. Already-open snapshots stay valid until closed. Deleting an
obsolete package leaves selection intact. Abandoned stages can be explicitly discarded
only under the owned store; restarting never promotes them. No automatic recovery or
silent repair of corruption. Fault hooks deterministically model interrupted writes,
disk-full, ready/selection boundaries and deletion in owned copies only.

File flush + fsync followed by same-volume `os.replace` is the pointer commit boundary.
Measure Windows/NTFS process interruption behaviour. Directory durability, power-loss
recovery, adversarial concurrent writers, trusted signatures, downloads, mobile storage,
rights clearance and a production installer are explicitly unproven. Do not infer
that filesystem operations and scientific validation form one general transaction.

## Budget, acceptance and exclusions

Existing projection: 116,692,961 bytes, 12 members including manifest. Estimate each
owned stage/ready/fault copy at 112 MiB. Keep additional scratch below 512 MiB by
serial fault trials and retaining at most two ready copies plus a stage. Reader
snapshot target below 768 MiB desktop peak with three pinned readers; measure actual
use and document any excess rather than extrapolate phone performance. No full Swiss
pyramid, new data or committed generated package.

All 60 unchanged semantic cases must pass across three exact pins, including nine
expected errors. Novel closure/resource tests, staged/replacement/restart/deletion
faults and post-open mutation must pass. Full reference/native/runtime regressions,
lint/types and app-only build remain proportional checks. Independently rebuild if
retained prerequisites allow; member identities must remain unchanged. No incomplete
or incompatible candidate becomes ready in tested paths; failed replacement preserves
last ready selection; explicit generations and restart are deterministic. Stop on
unbounded closure, scientific discrepancy or a production filesystem/installer need.

Next task will be selected from measured costs: **MERIDIAN ATLAS OFFLINE PROJECTION
PORTABILITY AND RESOURCE-REDUCTION STUDY — NOT BEGUN**. No mobile, UI, renderer,
Weather, private repository, service, framework or final package-format work here.
