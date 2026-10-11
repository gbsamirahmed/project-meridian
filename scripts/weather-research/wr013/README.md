# WR013 scientific packaging apparatus

**Outcome A**, three genuine subsets, exact preservation and offline query replay.
See the [report](../../../docs/research/weather/scientific-field-packaging-offline-replay.md),
[frozen profile](input-pins.json), [integrity receipt](package-integrity-receipt.json)
and [query receipt](offline-query-replay-receipt.json). This is disposable research
apparatus, not a production format, service or application dependency.

## Inputs and construction

Use the three original filenames and SHA256 seals in `input-pins.json`, wherever
their accepted local copies are retained. No retrieval or installation is performed.
The constructor requires the existing WR007/WR011 Python/ecCodes/NumPy environment;
it checks all pinned WR007–WR012 utility/evidence dependencies and each complete
decoded-array seal before extracting the frozen subset. Originals stay immutable.

```powershell
python -B scripts/weather-research/wr013/package_pilot.py `
  --gfs-temperature <pinned-WR007-GRIB> `
  --gfs-apcp <pinned-WR009-GRIB> `
  --ifs-precipitation <pinned-WR011-GRIB> `
  --output <new-owned-scratch-directory>
```

Use a new output path under dedicated external scratch; the constructor refuses
overwriting existing output. The parent must already exist and have enough room
under the 150 MB owned scratch ceiling. The generated `package/` contains
`manifest.json` and three 4,200-byte little-endian binary64 payloads. Raw inputs,
packages and generated application/test artefacts stay outside Git. Do not place
the output in an authoritative collection. No external data-root reorganisation.

The package is not byte-equivalent to GRIB: it preserves interpreted native values,
source metadata and provenance, not the original compressed bitstream. The three
units and two accumulation intervals are deliberately retained separately.

## Offline reader

Copy only the generated package directory, `offline_reader.py` and a JSON list of
query requests into a fresh directory. Take the expected manifest SHA256 from the
integrity receipt through a trusted channel. No decoder, scientific package or
original GRIB belongs in that directory.

```powershell
python -I -S -B offline_reader.py --package package `
  --identity <trusted-manifest-SHA256> --requests requests.json --isolate
```

Example request, with optional scientific expectations:

```json
[{"field_id":"gfs-apcp","latitude":56.5,"longitude":-5,
  "method":"BILINEAR","expect":{"native_unit":"kg m**-2","temporal_kind":"accumulation"}}]
```

The constructor runs this isolated process automatically and compares all results
with unchanged WR008 or WR011 source-native sampling. The reader has standard-library
imports only. Its cooperative audit guard rejects reads outside the finite package
and requests, writes, network/subprocess operations and scientific-module imports.
Startup imports of the standard library precede the guard; this is **not an OS
security sandbox**. Optional Windows PSAPI counters are resource diagnostics only.

## Supported finite profile

Three deterministic regular latitude/longitude fields, scanning mode 0, sphere
6, native 0.25-degree grid nodes. Subset 54–59°N, 8–2°W; no periodic subset edges,
polar cells, missing values or masks. Finite longitudes normalise modulo360;
latitude never wraps. Nearest means angular-grid axes, ties east/south. Bilinear
uses four finite nodes, with an inward stencil on the closed south/east edges.
All out-of-subset requests fail even if a nearby node lies inside. No extrapolation,
unit conversion, temporal interpolation, terrain correction or weather-skill claim.

`expect` can assert `native_unit`, `vertical`, `temporal_kind` or the complete
`temporal` object. A mismatch fails explicitly. Other geometry, member, missingness
and temporal families fail closed rather than inheriting this profile's assumptions.
Package SHA256 is an integrity anchor, not a meteorological-accuracy certificate or
an authenticity signature. Two fields' common valid time does not make their
accumulations comparable observations of the same interval.

## Tests

```powershell
python -B -m unittest discover -s scripts/weather-research/wr013 -p test_*.py -v
$env:MERIDIAN_WR013_PACKAGE = '<generated-output>/package'
python -B -m unittest discover -s scripts/weather-research/wr013 -p test_*.py -v
```

Without that opt-in, the genuine test is **skipped, not passed**. With it, 43 tests
run: 42 explicitly synthetic rejection/mathematical/guard tests and one genuine
three-field package test with two independent process replays. The constructor's
receipt establishes all 1,575 original-to-reopened cell comparisons; the opted-in
test verifies pinned payload integrity and deterministic package-only replay without
reopening source GRIBs. Keep temporary test directories in owned scratch using
`TEMP`/`TMP` where necessary. Receipt resources are separate from deterministic
scientific content. Repeating the construction is optional; offline replay needs
only the package, reader and requests.

## Attribution and limits

NOAA/NCEP GFS and ECMWF IFS remain research candidates. This research is based on
data and products of the European Centre for Medium-Range Weather Forecasts
(ECMWF). Copyright 2025 ECMWF; retained CC BY4.0/source notices accompany the
modified research subset, with no endorsement. The original source-specific
rights/access evidence is carried from WR007/WR009/WR011; this experiment does not
establish commercial redistribution, hosted-service or offline application clearance.
Do not publish generated scientific packages as production artefacts.
