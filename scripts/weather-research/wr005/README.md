# WR005 MIDAS metadata pilot

An isolated Python 3.12 standard-library experiment, independent of the accepted
Weather pipeline. It reads **three pinned, user-supplied v202607 metadata files**,
checks the inspected BADC-CSV schema and joins 2025 change-log filenames to source
IDs. It cannot decode or accept observations. No network code or GIS imports.

The [WR005 report](../../../docs/research/weather/midas-reference-interpretation-pilot.md)
defines the scientific limits and evidence. `input-pins.json` records local byte
identity, not publisher authenticity or distribution clearance. Original inputs
and full receipts stay outside Git. Do not publish licensed source files.

From the repository root, with an existing Python 3.12 interpreter:

```powershell
# Set these to existing local directories; do not copy inputs into this repository.
$MidasInput = '<directory containing the three original files>'
$Wr005Scratch = '<owned scratch directory outside the repository and data inputs>'
$env:MERIDIAN_WR005_SCRATCH = $Wr005Scratch
python -B -m unittest discover -s scripts/weather-research/wr005 -p 'test_*.py' -v
python -B scripts/weather-research/wr005/metadata_pilot.py --input-dir $MidasInput --receipt "$Wr005Scratch/receipt-1.json"
python -B scripts/weather-research/wr005/metadata_pilot.py --input-dir $MidasInput --receipt "$Wr005Scratch/receipt-2.json"
(Get-FileHash "$Wr005Scratch/receipt-1.json").Hash -eq (Get-FileHash "$Wr005Scratch/receipt-2.json").Hash
```

Create the scratch directory first and use new receipt names: the CLI refuses to
overwrite outputs or write inside the input directory. In the checked environment
the existing `meridian-data/earth-lab/.venv/Scripts/python.exe` was used; no package
installation is required. Input location is configurable, content identity is not.

Success exit 0 means **successful metadata inspection**, even when strict reference
eligibility is empty. Missing, altered, unsupported or malformed inputs produce
exit 2 and a bounded error code on stderr. A blocked annual-file gate is scientific
indeterminacy, not an empty valid observation series. No path opens annual files.

Bounds: each pinned member ≤2,000,000 bytes, ≤200 preamble rows, ≤10,000 station
rows, ≤65,536 characters per CSV field. All inputs are hashed again after inspection.
This detects ordinary changes during the run; it is not protection against a
hostile concurrent writer. Do not repin changed inputs automatically.

All 22 unit tests use **synthetic metadata**. Observation/QC/time columns and
station-era assertions are rejected as outside this inspected metadata schema.
These tests establish metadata-parser and fail-closed boundaries; they do not
validate QC decoding, temperature missingness or observation revision precedence.
Those operation-level tests remain blocked until their dictionaries and actual
observation schema can lawfully be inspected. Tests use owned temporary folders;
`MERIDIAN_WR005_SCRATCH` permits an explicitly writable parent on restricted hosts.
