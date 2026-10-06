# Retained illumination identifiability assessment

Research-only, read-only retained inputs. No correction, normalization, fitted illumination, imagery acquisition or production consumption.

From repository root, using the existing scientific environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/illumination-assessment/assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/illumination-assessment/test_assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/illumination-assessment/validate.py
```

[Report](../../../docs/research/illumination-identifiability.md), [deterministic results](../../../docs/research/illumination-identifiability-results.json), [validation](../../../docs/research/illumination-identifiability-validation.json).

`protocol.json` fixes inherited four patches, pre-existing961source probes each, dates,10-minute possibility envelope, fixedUTC sensitivity scenarios and1km sampled solar rays. Its halo was expanded after a containment error before any completed diagnostic; no fitting. `future-evaluation.json` preregisters a separately authorized possible residual experiment. This folder does not execute that experiment.

`assess.py` uses NOAA published fractional-year equations, explicit UTC/east-positive longitude, true-to-LV95 basis, native0.5 m DTM normals and finite nearest-height rays. The output is conditional geometry, not actual exposure time or observed shadow state. Luma is encoded RGB brightness, not radiance. It reuses the unchanged appearance hash verifier and source probe receipt. No extra dependencies are installed. A NumPy/rasterio deprecation warning is an environment compatibility note, not a failed geometry result.

Only source/product/hash checks and small aggregate diagnostic output are written to Git. Large originals/prepared products remain in meridian-data. No new resampled imagery, persistent stores, corrections or inferred physical appearance are produced. All10 scenarios are recorded rather than selecting the strongest covariance.
