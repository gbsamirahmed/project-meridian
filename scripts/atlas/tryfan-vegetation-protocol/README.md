# Retained Tryfan vegetation population assessment

Protocol feasibility only: no correction, parameter estimation, acquisition or source writes.

Run from repository root with retained sibling `meridian-data` and its scientific environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/tryfan-vegetation-protocol/assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/tryfan-vegetation-protocol/test_assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/tryfan-vegetation-protocol/validate.py
```

The [plan](assessment-plan.json) fixes three candidates,20m boundary guard and spatial support gates
before new statistics. `assess.py` reuses only read-only geometry/loading helpers, checks retained
hashes, constructs native support geometry and computes descriptive baseline diagnostics.
No call to the historical experiment's output-writing `baseline()` or `run()` is made.

Outputs are compact metrics and two figures linked from the [report](../../../docs/research/tryfan-vegetation-protocol.md).
Logical masks are hashed, not duplicated as raster files. No future executable correction protocol
is published when the candidates fail eligibility gates. The original 1842008 trial stays INCONCLUSIVE.

Warnings from rasterio under NumPy2.5 concern its internal array-shape assignment; retained reads
and deterministic results are checked. No library modification or new dependency is required.
