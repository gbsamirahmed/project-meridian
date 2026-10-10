# WR009 single historical precipitation-interval pilot

Isolated research, no production imports or acquisition client. Read the
[scientific report](../../../docs/research/weather/historical-gfs-precipitation-interval-pilot.md),
[input pins](input-pins.json), [integrity receipt](integrity-receipt.json) and
[interval receipt](interval-interpretation-receipt.json). Raw input and generated
arrays/temporary outputs remain outside Git.

## Exact input and acquisition evidence

NOAA/NCEP GFS Jan 15 2025 00 UTC, f024 delivered 0.25° product, **message 596**:
`APCP:surface:18-24 hour acc fcst`, **343,228 bytes**, SHA256
`e2a311fa2089ab1982d9b09e7ec82f483e07ef06f38457d9e379fe9cef970848`.
The interval is **Jan 15 18 UTC to Jan 16 00 UTC**, six hours. Another APCP
message ending at the same lead has a different interval; it was not acquired.

Anonymous NOAA byte range **426116442–426459669 inclusive** returned HTTP 206,
matching Content-Range, length, ETag and actual body bytes. The 537,858,357-byte
parent was not downloaded. [Source/index](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250115/00/atmos/gfs.t00z.pgrb2.0p25.f024.idx)
and HTTP ledger are pinned. Reacquisition needs its own authorisation/budget:
recheck index identity and next offset, parent HEAD and If-Match, refuse a 200 or
wrong Content-Range before reading its body, stream within the remaining byte
ceiling, and verify framing/checksum. Do not substitute a different field if the pin fails.

NOAA/NCEP GFS accessed through [NOAA NODD](https://registry.opendata.aws/noaa-gfs-bdp-pds/)
on **10 October 2026**. Attribute NOAA; no implied affiliation/endorsement.
Receipts/statistics are Meridian-derived research outputs. No product distribution
or software-binary redistribution clearance is claimed.

## Finite interpretation

Actual GRIB 2 **0/1/8**, surface **1**, PDT **4.8**, statistical process **1**,
one time range, increment type **2**, zero increment. `forecastTime=18` is the
start offset, **not** the end lead: `endStep=24`, duration six hours. PDT octets,
ecCodes aliases and GDAL's raw template/time tags are cross-checked. Missing
increment-unit code 255 with zero increment is retained; no cadence is invented.
Other templates, multiple/nested ranges, positive increments and missing
statistical input counts fail closed, without claiming that those products are invalid.

Native units **kg m⁻²** are accumulated precipitation mass per area. No conversion
is applied to the field. A labelled synthetic conversion helper stipulates water
density 1000 kg/m³: one kg/m² then corresponds to one mm water-equivalent depth,
not snow depth or instantaneous rain rate. No phase or within-interval intensity follows.

Packing R=0, E=−4, D=0 makes an exact **1/16 kg/m²** lattice. Before values,
comparison required all reconstructed integers in [0,2²⁴), exact binary scaling
and **zero decoder tolerance**. Every real cell satisfies this proof domain.
No temperature-specific decimal-rounding allowance is copied or relaxed.
Real missingness is zero; masked-array checks are synthetic, not bitmap decoding.

The exact encoded Section 3 matches WR007. WR008 angular-nearest/qualified-bilinear
geometry is reusable in principle, with the interval attached. **No precipitation
point sampling is executed**, no new interpolation programme or production API created.

## Existing environment and replay

Windows Python 3.12.6; primary ecCodes Python/native 2.48.0, NumPy 2.5.2.
Separate existing Python/rasterio 1.4.3/GDAL 3.9.3/NumPy 2.5.3 uses independent
degrib/g2clib. No new package/version/framework. WR007 decoding/framing and
WR008 Windows PSAPI measurements are imported unchanged; dependency byte hashes
reflect this checked Windows checkout. Line-ending changes on another checkout
need explicit reconciliation rather than bypassing identity checks.

```powershell
$env:npm_config_update_notifier = 'false'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:MERIDIAN_WR009_INPUT = '<external-owned-input>/gfs-2025011500-f024-apcp-18-24h.grib2'
$env:MERIDIAN_WR007_GDAL_PYTHON = '<existing-gdal-environment>/Scripts/python.exe'
$env:TEMP = '<external-owned-wr009-scratch>'
$env:TMP = $env:TEMP
& '<existing-eccodes-python>' -B scripts/weather-research/wr009/gfs_precipitation_pilot.py `
  --input $env:MERIDIAN_WR009_INPUT --gdal-python $env:MERIDIAN_WR007_GDAL_PYTHON `
  --output '<external-owned-wr009-scratch>/receipt.json'
& '<existing-eccodes-python>' -B -m unittest discover `
  -s scripts/weather-research/wr009 -p 'test_*.py' -v
```

Choose new outputs; existing inputs/receipts/intermediates are never overwritten.
The complete deterministic receipt is **11,360 bytes**, SHA256
`3fd4ca223e8377872c0c77fb99b758240c2a6cddfb55976e7b354a0b63405451`.
The committed receipt adds separately labelled acquisition/resource observations;
these additions are not part of the replay fingerprint. Temporary GDAL values/mask
and metadata occupy **9,347,284 bytes** and are removed by owned temporary-directory
lifecycle. Outputs must be outside Git in dedicated scratch. The utility reserves
20 MB temporary headroom below 150 MB; never point it at authoritative collections.
PSAPI counters are Windows-specific; this is not a cross-platform runtime.

**48 synthetic tests + one opt-in real test** were run, zero skips. The real test
repeats both decodes, compares receipts, checks accepted SHA/interval, refuses
overwrite and verifies immutable input. Without both environment variables it
explicitly skips. Synthetic metadata, masks, timestamps, conversion and framing
cases are not real forecasts or forecast-verification evidence. Existing
rasterio/NumPy shape-deprecation warnings remain visible. No test makes network requests.

No forecast skill, MIDAS reinterpretation, precipitation phase, local intensity,
orographic accuracy, terrain correction or safety suitability is established.
The next multi-variable task is only proposed in the report, **NOT BEGUN**.
