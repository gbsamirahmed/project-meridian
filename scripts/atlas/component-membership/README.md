# Isolated Atlas component-membership proof

This is architecture evidence, not the accepted pilot or production storage. State is confined to the absolute `stateRoot` frozen in [plan.json](plan.json). Retained sources are read-only. Existing S4 serving and separate consumers are reused by guarded process-local load hooks; original pilot files are never rewritten.

The prospectively frozen model uses five content-addressed collection manifests and explicit direct publication membership. A fixed-width immutable byte-radix eligibility witness is committed alongside current identity. It is an experimental logical witness, not a selected production index. Selected identity closure is verified every request; unselected archive audit is explicit and independent.

Run from repository root with Node24 and the existing earth-lab Python environment:

```powershell
node scripts/atlas/component-membership/fixtures.mjs
../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/component-membership/run.py
node scripts/atlas/component-membership/lifecycle-worker.mjs
node --test scripts/atlas/component-membership/test-proof.mjs
../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/component-membership/validate.py
```

Construction writes immutable external proof objects. A new timing campaign should use a deliberately distinct state root and a separately frozen plan; do not silently overwrite the accepted measurements. `run.py` resumes existing SHA-pinned raw cells and initially writes an UNJUDGED result. The committed decision/first lifecycle/failure/historical receipts record the evaluation. Use `run.py --check` for read-only reproduction of those existing receipts. Tests create uniquely named diagnostic stores and retain first measurement receipts, writing later repeats separately.

The guarded runtime replaces only generation load/current and serving published eligibility inside proof processes. Frozen canonical domain, source verification, native queries, derivation/freshness/replay and HTTP/consumer code execute unchanged. The proof writer validates before atomically committing both current and eligibility-root identities. It enforces a local single writer; abrupt exits require explicit demonstrably-dead PID lock recovery. Complete pre-switch candidates remain unpublished. No distributed/power-loss guarantee is claimed.

[Report](../../../docs/research/atlas-component-membership.md), [results](../../../docs/research/atlas-component-membership-results.json) and [decision record](../../../docs/research/atlas-component-membership-decisions.json) explain limits, measurements and the exactly-one next task. Do not begin that task here.
