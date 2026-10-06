# Retained Tryfan residual normalization entry and stopping result

This isolated experiment executes the [frozen protocol](../illumination-assessment/future-evaluation.json)
from 9695757. The [execution plan](execution-plan.json) was written before the first baseline
and only specifies grid, ray and metric details; it does not change eligibility or criteria.
The whole-design eligibility gate failed: SE has 12 eligible SCL5 cells, below 20.
The code therefore stops **INCONCLUSIVE** before fitting. It intentionally contains no
correction path. Different inputs or a passing gate require a separately authorized protocol,
not automatic execution of another experiment.

Run from the repository with the retained scientific environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/tryfan-illumination-normalization/experiment.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/tryfan-illumination-normalization/test_experiment.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/tryfan-illumination-normalization/validate.py
```

The first command verifies exact source/terrain hashes, persists a baseline before inspecting
the gate, emits an explicit stopped-result receipt and two baseline-only figures. All inputs
are read-only. Nothing is downloaded. No corrected raster, cache or payload is created.
`--baseline` executes only the pre-fit characterization.

[Durable report](../../../docs/research/tryfan-illumination-normalization.md),
[baseline](../../../docs/research/tryfan-illumination-normalization-baseline.json),
[outcome](../../../docs/research/tryfan-illumination-normalization-results.json),
[validation](../../../docs/research/tryfan-illumination-normalization-validation.json).

Numerical baseline: float64 decoded RGB, single bilinear reprojection; SCL nearest.
Normals use10m means of native1m terrain; rays use native1m geometry at2..1000m.
The source scene Sun is rotated from true north into the BNG grid. Data outside1km,
non-terrain occluders and exact pixel Sun remain unknown. Display clips only the fixed
010 transfer, never the analytical data. NumPy2.5/rasterio emits a known dependency
warning about shape assignment; it does not alter retained inputs or outputs.
