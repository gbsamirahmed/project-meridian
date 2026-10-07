# Retained Riffelhorn display-transfer experiment

Research-only global pointwise display operators. Source/product bytes remain read-only.
The [protocol](protocol.json) was written before candidate outputs. Two amplitudes of one
bounded smooth toe curve use the prior four patches/intensity strata, with no fit or mask tuning.
The operation consumes encoded RGB8; it is not calibrated luminance, physical correction,
illumination normalization, albedo, denoising or reconstructed texture. No production imports.

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-display-transfer/experiment.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-display-transfer/test_experiment.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/riffelhorn-display-transfer/validate.py
```

The existing scientific runtime and retained external data are required. Native windows are the
highest retained source reference; a secondary check applies the same operator after existing
z18 PNG decoding. No transformed source/pyramid is written. Only metrics and three compact
matched figures are generated. Source intensity assigns populations BEFORE transfer, at all
scales and codec phases. Local gradients/contrast are visibility proxies, not information gain.
The JSON stores exact transient RGB8 output hashes; output pixels need not be persisted.

[Report](../../../docs/research/riffelhorn-display-transfer.md),
[metrics](../../../docs/research/riffelhorn-display-transfer-results.json),
[validation](../../../docs/research/riffelhorn-display-transfer-validation.json).
