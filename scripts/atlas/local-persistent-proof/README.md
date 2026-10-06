# Local persistent Tryfan proof

Research only; no production imports or data acquisition. Uses existing TerrainHierarchy,
Semantic Evidence Contract v1 and original scientific/lifecycle functions unchanged.

From repository root:

```powershell
node scripts/atlas/local-persistent-proof/run-proof.mjs ../meridian-data
node --test scripts/atlas/test_local_persistent_tryfan.mjs
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/local-persistent-proof/validate.py
```

`run-proof` creates new stores/traces under `meridian-data/derived/atlas/tryfan/local-persistent-proof-v1/runs`
and writes a small repository measurement receipt. Tests write only new external proof stores.
A run is not a production throughput promise. `MERIDIAN_DATA_ROOT` can locate test data;
the retained Python environment and declared assets must exist, otherwise execution fails honestly.

Each CLI invocation is a genuinely new process:

```powershell
node scripts/atlas/local-persistent-proof/cli.mjs init STORE DATA
node scripts/atlas/local-persistent-proof/cli.mjs inspect STORE DATA
node scripts/atlas/local-persistent-proof/cli.mjs update STORE DATA
node scripts/atlas/local-persistent-proof/cli.mjs replay STORE DATA
```

Use a fresh STORE path under the external data workspace. Initialization refuses an existing
accepted store. Schema/basis guards reject incompatible code/input changes rather than migrate.
The tests deliberately exit an update process with status73 before pointer publication and
mutate only newly generated test stores. Immutable retained sources/products are never changed.
The inspection batch includes current/historical claims, policy assessments, dependencies,
rights, unknown exposure and unavailable contributor-provenance request; no UI/API is built.

[Report](../../../docs/research/tryfan-local-persistent-proof.md),
[plan](../../../docs/research/tryfan-local-persistent-plan.json) and
[measurements](../../../docs/research/tryfan-local-persistent-results.json) give the scope.
One writer, canonical complete metadata snapshots and atomic pointer replacement are a
replaceable proof mechanism. They do not establish power-loss durability, concurrent writers,
incremental record storage, or a production technology decision.
