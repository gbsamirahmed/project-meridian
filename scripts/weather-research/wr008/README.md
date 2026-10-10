# WR008 native-grid temperature sampling

Isolated Windows research, not a production query API. Read the
[report](../../../docs/research/weather/gfs-native-grid-point-sampling.md),
[frozen query profile](query-profile.json), [pins](input-pins.json) and
[compact receipt](sampling-receipt.json) together. Source/arrays/full query receipts
stay outside Git; no acquisition code or dependency installation is included.

## Input and scientific meaning

Reuse the exact [WR007](../wr007/README.md) raw message: SHA256
`0b95fc06fe9ca08de57f9c5089b8fcd5d7b6a42977b35f669da65ec0f43f40e4`,
874,115 bytes. The unchanged WR007 decoder validates actual GRIB parameter/height,
reference/valid time, grid/scan/Earth shape, units, packing and no-missing profile.
WR008 checks the accepted decoded-array hash and its own frozen profile before queries.
Do not reacquire/substitute data if the pin fails. WR007 implementation/evidence
byte hashes assume the checked Windows checkout; another checkout's line endings
need explicit reconciliation rather than disabling identity checks.

Query records are meaningful **only inside their receipt context**: original field,
source/hash, grid, 2 m above model ground, Kelvin, Jan 15 2025 00 UTC +24 h, valid
Jan 16 00 UTC and decoder versions. They are not actual real-terrain station
measurements. No lapse rate, downscaling, predictive skill or resolution gain is inferred.

`Sampler.query` accepts exactly `latitude`, `longitude`, `method`. Degrees are named,
never positionally swapped. Finite numeric longitudes are reduced modulo 360 and
labelled in both [0,360) and [−180,180). Latitude is never wrapped/clipped. Binary64
coordinate arithmetic has finite precision; a sub-ULP negative modulo endpoint
rounding to 360 is canonicalised to zero. Methods are exactly `NEAREST`, `BILINEAR`.
Malformed/types/non-finite/out-of-range/method failures are explicit statuses.

**NEAREST** means independent-axis distance in angular grid-coordinate space,
not minimum great-circle/geodesic distance. Exact halfway ties choose increasing
index (south/east); columns wrap. Pole rows use canonical column zero. Synthetic
spherical-distance counterexample demonstrates why these definitions differ.

**BILINEAR** uses four native nodes, including cyclic last/first columns. Both
bounding latitude rows must be non-polar: this field supports [−89.75,89.75].
The southern endpoint uses the two adjacent interior rows. Polar caps/poles return
`UNSUPPORTED_POLAR_CAP_BILINEAR`; no nearest fallback/extrapolation. Every node must
be interpretable, including zero-weight nodes: masks fail with
`MISSING_CONTRIBUTING_NODE`, unmasked non-finite nodes with `UNINTERPRETABLE_NODE`.
No weights are renormalised. The actual field has no missing values; mask cases
are synthetic and do not establish bitmap decoding.

## Existing tools and reproducibility

Primary existing Python 3.12.6/ecCodes 2.48.0/NumPy 2.5.2; separate existing
Earth Lab Python 3.12.6/rasterio 1.4.3/GDAL 3.9.3/NumPy 2.5.3. No SciPy is
available or installed. Reference uses independent GDAL georeferenced sample and
warp-bilinear on a four-node patch from the original field, with units/longitude
normalisation disabled and the actual source sphere. The tiny destination pixel
is a GDAL centre probe, not a finer meteorological product. Boundary/missing policy
is shared explicit research policy, not independently discovered by GDAL.

Run from the repository root with existing environments and **owned external scratch**:

```powershell
$env:npm_config_update_notifier = 'false'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$env:TEMP = '<external-owned-wr008-scratch>'
$env:TMP = $env:TEMP
$env:MERIDIAN_WR007_INPUT = '<external-input>/gfs-2025011500-f024-t2m.grib2'
$env:MERIDIAN_WR007_GDAL_PYTHON = '<existing-earth-lab-environment>/Scripts/python.exe'
& '<existing-eccodes-python>' -B scripts/weather-research/wr008/gfs_point_sampling.py `
  --input $env:MERIDIAN_WR007_INPUT --gdal-python $env:MERIDIAN_WR007_GDAL_PYTHON `
  --output '<external-owned-wr008-scratch>/sampling.json'
& '<existing-eccodes-python>' -B -m unittest discover `
  -s scripts/weather-research/wr008 -p 'test_*.py' -v
& '<existing-eccodes-python>' -B -m unittest discover `
  -s scripts/weather-research/wr007 -p 'test_*.py' -v
```

Choose new output names; refuse overwrite. Complete deterministic scientific
receipt has SHA256 `f2bfcbc338217744b5aafaa1311ab0a0b76ce500a0e6527729c2ffd65e720a21`,
50,170 bytes. Variable working-set/timing observations are in a separate resource
receipt, never included in the replay identity. Process-memory measurement uses
Windows PSAPI, includes imports/native decoding and is not a mobile result.
One 9,346,222-byte GDAL decode intermediate is removed after each reference run;
no permanent full-field copies. Keep total owned scratch under 150 MB.

Real test is opt-in via both variables, repeats the full query comparison and
checks receipt hash/input/arrays immutability. It was executed with zero skips.
Synthetic cases isolate geometry, masks, affine/constant fields, errors and ties;
they are not meteorological validation. Existing rasterio/NumPy shape deprecation
warnings remain visible. No test or sampling code makes network requests.

NOAA-derived samples retain WR007's source credit/reuse qualifications. No binary
is redistributed and no new commercial/offline clearance is asserted. Git control
traffic is separate and unmetered; do not claim zero total network activity.
