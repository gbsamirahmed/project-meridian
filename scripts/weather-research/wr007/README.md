# WR007 single historical GFS field pilot

Isolated research; no production imports or provider selection. See the
[scientific report](../../../docs/research/weather/historical-gfs-temperature-field-pilot.md).
Original scientific input and generated numerical arrays remain outside Git.

## Pinned input and acquisition

[Input pins](input-pins.json) identify one NOAA NODD message, 2025-01-15 00 UTC
f024, TMP at 2 m. [Integrity receipt](integrity-receipt.json) retains exact source,
HTTP, native-library and comparison evidence, with the full local receipt's hash.
No raw GRIB payload is included. The original parent is 537,858,357 bytes; **do not
download it**. The verified byte interval is 415390073–416264187 inclusive,
874,115 bytes. Acquisition used an anonymous bounded request, no redirects or cookie
jar, and checked HTTP 206, Content-Range, Content-Length and actual byte count
before accepting the body. The index's next offset bounds this single message.
An ETag is retained as object metadata, not treated as a cryptographic checksum.

To repeat acquisition only under a separately appropriate budget, request the
pinned `.idx`, verify its SHA256 and exact TMP line/next offset, HEAD the parent
and compare its size/ETag, then request that interval. Refuse a 200 response or
different range **before reading its body**; enforce remaining byte/request bounds
while streaming. Verify the raw SHA256 and single-message framing before decoding.
Do not retry or switch dates/models silently. A manual exact-message provision
with the pinned checksum is also sufficient. Archive continuity is not guaranteed.

NOAA/NCEP Global Forecast System was accessed on 10 October 2026 through the
[NODD registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/). Credit NOAA,
do not imply endorsement and identify derived/modified material. This research
does not establish product distribution clearance or unlimited service access.

## Environment and commands

No packages were installed. Primary existing Windows Python 3.12.6 has ecCodes
Python/native 2.48.0, NumPy 2.5.2, cffi 2.1.1, findlibs 0.1.3, attrs 26.1.0.
Separate existing Earth Lab Python 3.12.6 has rasterio 1.4.3, GDAL 3.9.3,
NumPy 2.5.3. GDAL's degrib/g2clib is independent of ecCodes for this template.
Two ecCodes wrappers would not be an independent comparison.

Run from the repository root, setting paths to existing local environments and
the pinned external input. Use an **external owned scratch directory** for outputs
and temporary tests. These placeholders are configuration, not hidden machine paths:

```powershell
$env:MERIDIAN_WR007_INPUT = '<external-input>/gfs-2025011500-f024-t2m.grib2'
$env:MERIDIAN_WR007_GDAL_PYTHON = '<existing-earth-lab-environment>/Scripts/python.exe'
$env:TEMP = '<external-owned-wr007-scratch>'
$env:TMP = $env:TEMP
& '<existing-eccodes-python>' -B scripts/weather-research/wr007/gfs_field_pilot.py `
  --input $env:MERIDIAN_WR007_INPUT --gdal-python $env:MERIDIAN_WR007_GDAL_PYTHON `
  --output '<external-owned-wr007-scratch>/receipt.json'
& '<existing-eccodes-python>' -B -m unittest discover `
  -s scripts/weather-research/wr007 -p 'test_*.py' -v
```

Receipt generation creates a separate `receipt-gdal.npz` and `receipt-gdal.json`
plus the deterministic final receipt. Choose new output names; existing files are
not overwritten. Each GDAL intermediate is approximately 9.35 MB. Keep total
owned scratch below 150 MB; the 50 MB/20-attempt acquisition budget includes
metadata and software documentation. No network request occurs during decoding/tests.
The opt-in real test executes only when both environment variables are supplied;
without them it is explicitly skipped. **WR007 ran it: zero skips.**

## Deliberately finite support

The exact metadata/packing profile is checked before values: regular 1440×721 grid,
scan mode 0, template 5.3 second-order spatial differencing, E=0/D=2, no bitmap or
internal missing values. Other grids, packing or missingness are unsupported and
fail closed. Synthetic mask tests validate comparison logic, not real bitmap decoding.
No sentinel is guessed from a friendly decoder property. GDAL unit normalisation
and longitude rearrangement are disabled explicitly; ecCodes values stay float64 K.

The comparison requires the analytical per-cell binary32 bound **and** exact agreement
with the documented g2clib rounding profile. Reconstructing packed integers from
ecCodes values is a rounding diagnostic, not a third decoder. The two actual decodes
come from separate ecCodes and GDAL native implementations. This script does not
implement GRIB unpacking, interpolate, resample, correct altitude or compute skill.

Twenty-nine synthetic tests cover rejected parameter/height/time/unit/grid/packing,
missing metadata/masks, framing, checksum, wrap and disagreement. One opt-in real
test repeats the complete comparison, requires identical receipts, refusal to
overwrite and byte-identical input. A rasterio/NumPy 2.5 deprecation warning arises
inside the existing reader; it did not prevent checks. Full arrays and samples are
local research outputs, not new Weather publications.

Resource-accounting qualification: the 12 controlled research requests total
1,218,601 body bytes. An automatic npm update lookup during lint was not byte-
instrumented; 13 known research/tooling attempts, total task-network transfer not
fully certified. See the report/receipt; no package was installed. Disable
`npm_config_update_notifier` when running unrelated npm validation in bounded research.
