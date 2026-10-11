# WR012 — qualified independent CCSDS conformance

Research-only Windows64 utility for the **three unchanged WR011 inputs**. No
acquisition, installation, production decoder or forecast-skill calculation.

The reference child imports only the Python standard library. It parses GRIB2
sections itself, calls the already installed, checksummed `aec.dll` buffer API,
reads big-endian unsigned integers and applies encoded scaling. It never imports
or loads ecCodes. The primary uses unchanged WR011/ecCodes decoding.

**Independence B:** separate GRIB interpretation, shared low-level libaec. This
does not independently validate the CCSDS entropy algorithm. The installed DLL's
upstream libaec version is unknown; its exact bytes and ecCodes distribution
RECORD are established. Header documentation v1.1.3 is not binary-version evidence.
No fallback to ecCodes is permitted for the reference.

## Inputs and environment

- Python 3.12.6 Windows64; existing ecCodes 2.48.0 and NumPy 2.5.2 for the coordinator.
- Set `MERIDIAN_WR011_INPUTS` to the directory containing the pinned
  `temperature.grib2`, `precipitation.grib2` and `wind_u.grib2`.
- Set `MERIDIAN_WR012_LIBAEC` to the existing installed `aec.dll` matching
  [input-pins.json](input-pins.json). No binary is included or fetched.
- Keep `TEMP`/`TMP` and receipt paths in a dedicated external scratch directory;
  set `PYTHONDONTWRITEBYTECODE=1` and `PIP_DISABLE_PIP_VERSION_CHECK=1`.
- Historical source, field meanings and rights: [WR011](../../../docs/research/weather/cross-provider-ifs-field-conformance.md).

From the repository root, with those environment variables set in PowerShell:

```powershell
& $ResearchPython -B scripts/weather-research/wr012/ccsds_conformance.py `
  --inputs $env:MERIDIAN_WR011_INPUTS --libaec $env:MERIDIAN_WR012_LIBAEC `
  --output "$ResearchScratch/comparison.json" --resources "$ResearchScratch/resources.json"
& $ResearchPython -B -m unittest discover -s scripts/weather-research/wr012 -p 'test_*.py' -v
```

`ResearchPython` and `ResearchScratch` are caller-supplied existing interpreter
and external directory paths, not machine-specific pins. Outputs must be new;
existing receipts and source files are never overwritten. The executable is
optional only in the sense that its absence produces an explicit failure. The
genuine replay test skips with a stated reason if inputs are absent; a skip is
not a passed numerical comparison.

## Finite acceptance and receipts

Only template 5.42, no bitmap, D0, the three pinned parameter/level/time profiles,
and the actual 1440×721 Section3 identity are allowed. Native calls follow raw
size/hash and ABI verification. Unsupported grid, statistic, packing, byte order
or missingness fails closed; no arbitrary GRIB input support is offered.

The predeclared criterion is **exact binary64 agreement, zero tolerance** across
all 1,038,240 cells per field. The encoded reference value R is binary32, and the integer
domains/binary scales make scaling exactly representable in binary64. GDAL's
historical float32 comparison rule is not silently reused for this different path.
Coordinates are checked before comparing native indices. There is no rotation,
regridding, physical-unit conversion, interpolation, clamping or data repair.

[Numerical receipt](numerical-comparison-receipt.json) is deterministic; transient
process-memory/time measurements stay outside Git. [Capability receipt](decoder-capability-receipt.json)
records the original GDAL failure and actual DLL/provenance boundary. Temporary
binary64 output is one field at a time and removed automatically. Source hashes
are rechecked after reading. Tests distinguish 35 synthetic checks from one genuine
three-field double replay. No HTTP or package-update code is used.

The libaec interface/constants are documented by its
[v1.1.3 header](https://raw.githubusercontent.com/MathisRosenhauer/libaec/v1.1.3/include/libaec.h.in)
and [BSD-2-Clause licence](https://raw.githubusercontent.com/MathisRosenhauer/libaec/v1.1.3/LICENSE.txt).
No upstream entropy algorithm or binary is redistributed here. Interpretation,
limitations and the sole next task are in the [WR012 report](../../../docs/research/weather/independent-ccsds-numerical-conformance.md).
