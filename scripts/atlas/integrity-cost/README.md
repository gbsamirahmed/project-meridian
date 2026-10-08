# Retained payload-integrity/publication-validation cost assessment

Assessment-only wrappers around unchanged Tryfan and retained-component/full-validation bodies. No guards, optimization policy, production runtime, source datasets or accepted state are modified.

- [Frozen matrix and criteria](plan.json); SHA in the [report](../../../docs/research/atlas-integrity-cost.md).
- [Baseline](../../../docs/research/atlas-integrity-cost-baseline.json), [results](../../../docs/research/atlas-integrity-cost-results.json), [classification](../../../docs/research/atlas-integrity-cost-decisions.json), [regression receipt](../../../docs/research/atlas-integrity-cost-validation.json).
- `meter.mjs`: nested inclusive/exclusive Node filesystem, identity and existing validator instrumentation.
- `worker.mjs`: plain/metered native paths, read-only larger prepared-byte sweeps, explicit known component roots.
- `metadata.py` / `metadata-worker.py`: unchanged Python full-validation/commit population and sequence paths; no receipts.
- `failures.mjs`: isolated actual native rejection/pre-switch interruption boundaries.
- `test_measurement.py`: focused instrumentation, equivalence and failure/history checks.
- `report.py`: deterministic synthesis of measured JSON; no measurement rerun.

From repository root, using the retained data environment:

```powershell
$env:PYTHONIOENCODING='utf-8'
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/integrity-cost/run.py --check
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/integrity-cost/test_measurement.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/integrity-cost/validate.py
```

`run.py` without `--check` creates the frozen isolated campaign and refuses to overwrite existing campaign state. The current raw campaign is `C:/Users/gbsam/Documents/Codex/atlas-integrity-cost-v1`, with every raw output pinned in results. Do not delete it or edit frozen inputs to obtain a preferred result. A separate authorized reproduction requires a fresh isolated state and records its distinct environment; do not change the accepted baseline. Fixture generation/setup, read/validation, construction, commit and process-startup costs are separate. Five repetitions include the first sample; OS caches are uncontrolled. Requested bytes are logical user-space reads, not disk traffic. End RSS is not peak memory.

Larger-product verification uses the unchanged path/size/SHA mechanism on existing prepared tiles/fields; it is not an integrated new-region generation or science acceptance. Historical roots are selected explicitly, with discovery outside timed known-root resolution. Atomic publication is tested through actual native registration in an isolated store. All accepted source/store paths are read-only. Receipt optimisation remains closed, full validation remains provisional, and the next regional/source-accountability assessment has not begun.
