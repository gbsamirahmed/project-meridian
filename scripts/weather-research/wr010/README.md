# WR010: finite multi-variable compatibility evidence

Research only. Read the [report](../../../docs/research/weather/multi-variable-field-compatibility-pilot.md),
[pins](input-pins.json), [receipt](integrity-receipt.json) and
[tests](test_field_compatibility.py). No production API, acquisition client, provider
selection or change to earlier experiments. The finite adapter accepts only the
five evidenced parameters and two temporal profiles; the conceptual contract in
the report is broader than this small executable adapter.

Reuse installed Python 3.12.6, NumPy 2.5.2/ecCodes 2.48.0 and a separate interpreter
with rasterio 1.4.3/GDAL 3.9.3/NumPy 2.5.3. Install nothing. Disable incidental update
checks. Source inputs/output remain outside Git. `INPUTS` is an owned research
directory containing pinned `u10.grib2`, `v10.grib2`, `cloud.grib2`; `TEMPERATURE`
and `PRECIPITATION` point to the unchanged WR007/WR009 raw inputs. Paths are supplied
explicitly, never inferred from a filename alone. SHA256/size/message framing,
metadata and dependencies must match before values. A missing pin stops replay;
no implicit acquisition or substitution.

From the repository, substitute actual local paths for these placeholders:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PIP_DISABLE_PIP_VERSION_CHECK='1'
$env:TEMP='OWNED-SCRATCH'
$env:TMP=$env:TEMP
& 'PRIMARY-PYTHON' -B scripts/weather-research/wr010/field_compatibility.py `
  --inputs 'INPUTS' --output 'OWNED-SCRATCH/new-receipt.json' `
  --temperature-input 'TEMPERATURE' --precipitation-input 'PRECIPITATION' `
  --gdal-python 'GDAL-PYTHON'
```

The output must not exist. Scientific JSON is deterministic; resource observations
are in a separate companion. Three sequential fields keep one primary full array
and one temporary independent array, rather than five simultaneous fields. Each
temporary GDAL values/mask/metadata output is removed. Inputs are never written.
The child decoder sets native units and original longitude layout explicitly.
No networking is present in this utility. Check owned scratch before each replay;
the 150 MB cap includes inputs, outputs, logs, temporary files and any build output.
Input size is capped at 50 MB per file; actual WR010 controlled acquisition total
has a separate externally retained 50 MB/20-request ledger.

Tests use edited copies of actual metadata as **synthetic rejection fixtures**;
they are not new historical evidence. Default discovery skips the real test if
its explicit external inputs/interpreter are absent:

```powershell
$env:MERIDIAN_WR010_INPUTS='INPUTS'
$env:MERIDIAN_WR007_INPUT='TEMPERATURE'
$env:MERIDIAN_WR009_INPUT='PRECIPITATION'
$env:MERIDIAN_WR007_GDAL_PYTHON='GDAL-PYTHON'
& 'PRIMARY-PYTHON' -B -m unittest discover -s scripts/weather-research/wr010 -p 'test_*.py' -v
```

The real test makes two complete three-field decodes and requires identical
scientific JSON plus equality with the committed scientific receipt. Prior
WR007–009 tests are separately opt-in using the same retained input variables.
Synthetic success alone cannot justify Outcome A.

WR008's isolated sampler has temperature-labelled result keys. WR010 reuses its
mathematics unchanged and explicitly relabels outputs as `native_value`, with the
field's own unit/identity/context. This is a research adapter, not a recommended
shared module. Nearest means angular-axis nearest, with south/east ties; longitude
is periodic, latitude is not. Four-node bilinear excludes polar caps; no fallback,
missing-node renormalisation, category interpolation or terrain correction. Wind
pole components have a degenerate directional basis even when numerical indexing
succeeds. No forecast skill, cloud truth, wind accuracy or local resolution claim.
