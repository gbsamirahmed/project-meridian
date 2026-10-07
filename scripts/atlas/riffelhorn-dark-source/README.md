# Retained Riffelhorn dark-source diagnostics

Research only; no application imports, acquisitions, correction, calibrated noise model or source writes.
The [assessment plan](assessment-plan.json) was written before new statistics. Four existing LV95 patches,
fixed encoded RGB intensity strata and 5 m blocks prevent interesting-patch selection. Source RGB8 is
already processed and JPEG-compressed. Aggregation and sqrt display lifting are diagnostic views,
not denoising, recovered texture, illumination normalization or publication of a new appearance product.

From the repository root with the existing retained data/scientific environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-dark-source/assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-dark-source/test_assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-dark-source/validate.py
```

The reader uses original source windows without resampling. Full source/product hashes are checked;
only intersecting prepared z18 fields regenerate in memory. Prepared RGB is compared to its declared
continuous delivery field and exact RGBA encoder, not to a mismatched native pixel grid. No terrain
resampling, source shadow labels or physical surface attribution. Patch coverage and zero-valued
pixels are distinct. Undefined constant/empty statistics serialize as null, not as physical absence.

[Report](../../../docs/research/riffelhorn-dark-source-signal.md),
[metrics](../../../docs/research/riffelhorn-dark-source-signal-results.json) and
[validation](../../../docs/research/riffelhorn-dark-source-signal-validation.json).
Only compact figures and JSON are written under docs/research; no scratch stores or raster copies.
