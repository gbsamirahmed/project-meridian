# Tryfan pilot planning validation

This folder validates the [frozen architecture/implementation plan](../../../docs/research/tryfan-regional-pilot-plan.md).
It is read-only evidence/plan accounting, not pilot runtime code. No service, store, query execution,
derivation or source preparation is implemented here. The future code directory `pilots/atlas/tryfan/`
and external pilot store must remain absent for this checkpoint.

From repository root, using the existing external geospatial runtime:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/regional-pilot-plan/test_plan.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/regional-pilot-plan/check_plan.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/regional-pilot-plan/validate.py
```

`check_plan.py` validates dependency order, finite scope/interfaces/publication obligations and pins310
required retained files (15 selected inputs plus295 Welsh tiles) against SHA256/size. It writes only a
compact repository results receipt. `validate.py` additionally checks all1575 prior acceptance files,
unchanged historical reports/scripts/status columns, frozen tooling,113 protected production hashes,
references/anchors and focused tests. It writes a repository validation receipt. No network acquisition,
retained writes, corrected/duplicate rasters, production build or private evidence inspection.

The report and JSON freeze U1/U2, F1-F3,21 queries and A-P exit acceptance before implementation.
The commit/result hashes bind this plan. A necessary later protocol change must be explicit, revisioned
and documented; never silently rewrite prior outcomes or claim unimplemented serving/publication passes.

Exactly one next task: **Tryfan pilot retained catalogue and immutable generation foundation**, S1 only;
not begun. Each implementation slice runs its own real runtime tests later; these planning safeguards
cannot replace them.
