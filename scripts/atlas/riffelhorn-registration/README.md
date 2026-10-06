# Retained Riffelhorn registration/epoch assessment

Research-only, read-only retained inspection. From the repository root:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-registration/assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-registration/test_assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-registration/validate.py
```

Uses existing NumPy/rasterio/pyproj/Pillow/matplotlib environment, no dependencies added.
Verifies sources/prepared files before diagnostics. Initial plan and explicit numerical
halo correction preserved. Fixed patches/support/proxies/search, no brightness tuning.
Black RGB retained, not classified as shadow/no-data. Proxy optima are not physical shifts.
Writes compact metrics and two figures to docs/research; never retained data or new rasters.

[Report](../../../docs/research/riffelhorn-registration-epoch.md) and
[validation](../../../docs/research/riffelhorn-registration-epoch-validation.json).
