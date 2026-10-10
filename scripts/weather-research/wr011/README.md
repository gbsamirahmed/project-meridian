# WR011 — finite IFS contract-conformance research

[Scientific report](../../../docs/research/weather/cross-provider-ifs-field-conformance.md).
Outcome **B**: three genuine ECMWF IFS fields read by ecCodes; independent GDAL
metadata checked, but installed GDAL lacks libaec support for packing template5.42.
No independent numerical agreement is claimed. No acquisition code, installation,
production API or forecast-skill computation is provided here.

Inputs are immutable, external to Git, identified by [pins](input-pins.json).
`temperature.grib2`, `precipitation.grib2`, `wind_u.grib2`: one 2025-01-15 00 UTC
oper deterministic forecast, endpoint +24 h. The original public AWS parent and
JSONL index are pinned; acquisition used exactly three verified HTTP206 ranges.
Historical AWS retention is not guaranteed by this receipt.

Use the existing primary Python/ecCodes2.48.0/NumPy2.5.2 and independent
Python/rasterio1.4.3/GDAL3.9.3/NumPy2.5.3 runtimes. Set environment variables to
their local locations; never copy credentials or install packages during replay.
Disable bytecode and package update checks. TEMP/TMP should point to owned external
scratch. `$env:MERIDIAN_WR011_INPUTS` locates the three pinned source files;
`$env:MERIDIAN_WR007_GDAL_PYTHON` identifies the independent runtime. `$env:WR011_PYTHON`
and `$env:WR011_OUTPUT` below are user-set primary executable and a new external
output filename. Existing outputs are never overwritten.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
& $env:WR011_PYTHON -B scripts/weather-research/wr011/ifs_contract_pilot.py `
  --inputs $env:MERIDIAN_WR011_INPUTS `
  --gdal-python $env:MERIDIAN_WR007_GDAL_PYTHON `
  --allow-unavailable-independent --output $env:WR011_OUTPUT
& $env:WR011_PYTHON -B -m unittest discover `
  -s scripts/weather-research/wr011 -p test_*.py -v
```

Without `--allow-unavailable-independent`, the decoder failure stops the run.
The flag recognises only the explicit missing-libaec diagnostic after GDAL's exact
metadata and raw-PDT checks passed; it records zero compared cells and Outcome B.
Other decoding/metadata disagreements still fail. It is not a replacement decoder.
The numerical binary32 comparison remains a predeclared, synthetically tested
rule awaiting an independent capable decoder; no tolerance is fitted to values.

**34 tests**: 33 synthetic rejection/invariant tests and one opt-in genuine
three-field double replay. The genuine test checks byte-identical deterministic
scientific receipts against the committed [integrity receipt](integrity-receipt.json),
including the known installed-runtime limitation. Without the external input and
runtime variables it is explicitly skipped. Synthetic mathematics/QC rejections
do not validate other models or grid families. QC here means decoding integrity,
not observation quality control or forecast verification.

Source checksum, actual GRIB metadata, raw Section2/3/4/5/6 hashes, numerical
summaries, query nodes/weights and failures are recorded. ecCodes signed longitude
labels are compared modulo360 with encoded coordinates; arrays are never rotated.
GDAL metadata geometry independently selects the same nodes/weights, but its
numerical values are unavailable. Query values are single-decoder research evidence.
Resources/acquisition times are kept outside deterministic science. All raw inputs,
arrays and temporary outputs stay outside Git. The utility preserves earlier pins,
receipts and utilities and intentionally rejects unsupported grids/ensembles/statistics.

This research is based on data and products of the European Centre for Medium-Range
Weather Forecasts (ECMWF). Copyright 2025 ECMWF. Source:
[ECMWF Open Data](https://doi.org/10.21957/open-data),
[CC BY4.0](https://creativecommons.org/licenses/by/4.0/legalcode.en) and
[additional ECMWF conditions](https://apps.ecmwf.int/datasets/licences/general/).
These are modified derived research outputs; ECMWF does not endorse Meridian.
ECMWF provides no warranty of accuracy, completeness or availability and excludes
liability under its terms. Operational delivery/service agreements and future
commercial/offline distribution remain separately qualified; this is not legal clearance.
