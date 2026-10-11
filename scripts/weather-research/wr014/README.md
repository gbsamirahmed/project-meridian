# WR014 — Fixed GEFS selected-member experiment

Research apparatus: 2025-01-15 00UTC/+24h instantaneous2mK, control0/type1 and positive1/type3/positive2/type3, 720×361/0.5° delivered grid. Not a production API/probability engine.

Modified Meridian research derived from NOAA GEFS; attribution retained, no endorsement. Product notice and individual HTTP/provenance receipts are in [pins](input-pins.json). A checksum is not a meteorological-accuracy certificate.

## Replay

Place immutable pinned files `control.grib2`, `perturbed01.grib2`, `perturbed02.grib2` in a new external owned directory; verify sizes/hashes. Never overwrite preserved inputs. Raw scientific files are not in Git.

Using existing ecCodes2.48.0/NumPy and independent GDAL3.9.3/rasterio1.4.3 environments:

```text
python -B scripts/weather-research/wr014/ensemble_pilot.py --inputs <owned-inputs> --gdal-python <existing-reference-python> --output <new-owned-scratch>/receipt.json
```

Set `PYTHONDONTWRITEBYTECODE=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1` and owned TEMP/TMP. No installation/network lookup/silent fallback. Missing packages/interpreter, identity or metadata fail explicitly. Outputs cannot overwrite existing receipts/reference files/sources.

`integrity-receipt.json` combines numerical/member/conformance and five selected-subset statistics receipts. Volatile `.resources.json` separates per-process peaks from deterministic science. Intermediate independent arrays are removable/sequential/outside Git.

## Tests

```text
python -B -m unittest discover -s scripts/weather-research/wr014 -p "test_*.py" -v
```

36 synthetic invariants explicitly labelled; no unacquired member validation. Set `MERIDIAN_WR014_INPUTS` and `MERIDIAN_WR007_GDAL_PYTHON` for genuine test: two three-member full-grid independent replays, identical receipts equal to committed result. Otherwise genuine test explicitly skipped, not passed. Tests never acquire data.

Support/table/PDT definitions precede values. Prospective amendment retains original freeze and uses unchanged WR007 two-operation decimal-packing/binary32 bounds plus exact g2clib predictions. Fixed before numerical differences, never replace with fitted tolerances.

## Limits

Three messages/one run/lead/scalar/grid; no acquisition in utility. Total20requests/50MB transfer/150MB owned scratch. GDAL/degrib/g2clib is independent GRIB interpretation from ecCodes, no CCSDS path here.

Encoded count30/documented31/registry21/selected3 stay separate. Complete-population mapping/weights unresolved. Arithmetic mean/range/population SD are **SELECTED SUBSET ONLY**, not operational distribution/calibration/skill. Full-ensemble probability/mean/confidence operations unsupported and rejected.

Exact native-node lookups only, no global interpolation/lapse correction/orography interpretation/offline ensemble packaging/accuracy claim. [Report/sole next task](../../../docs/research/weather/ensemble-member-identity-uncertainty-semantics.md).
