# WR006 one-station historical-support audit

Isolated Python standard-library research. It reuses the unchanged
[WR005 pinned metadata parser](../wr005/README.md), freezes one error-blind audit
nominee and verifies the public evidence bundle in
[the WR006 report](../../../docs/research/weather/midas-historical-measurement-support.md).
No annual observation, QC or forecast decoder; no production/runtime import.

The only implemented profile is v202607 / 2025 / metadata `caithness` / ascending
numeric source ID, excluding commissioning. It nominates 00032 for an audit, **not an
eligible historical station-era**. Changed first candidate fails; no fallback.
An added sensor-height, clock, QC or historical assertion in the frozen receipt fails.
The audit reproduces the report's manually reviewed **C/C decision for these pinned
inputs**; it does not evaluate new scientific evidence or choose a reference target.

Use existing Python 3.12, original supplied files and owned scratch outside Git/data:

```powershell
$MidasInput = '<directory containing the three pinned original files>'
$Wr006Scratch = '<new owned scratch outside the repository and scientific inputs>'
$Wr006Public = '<directory containing the six retained public response snapshots>'
$env:MERIDIAN_WR006_SCRATCH = $Wr006Scratch
$env:MERIDIAN_WR005_SCRATCH = $Wr006Scratch
python -B -m unittest discover -s scripts/weather-research/wr006 -p 'test_*.py' -v
python -B -m unittest discover -s scripts/weather-research/wr005 -p 'test_*.py'
python -B scripts/weather-research/wr006/measurement_support.py freeze --input-dir $MidasInput --receipt "$Wr006Scratch/selection.json"
python -B scripts/weather-research/wr006/measurement_support.py audit --input-dir $MidasInput --frozen-selection "$Wr006Scratch/selection.json" --public-evidence-dir $Wr006Public --receipt "$Wr006Scratch/audit-1.json"
python -B scripts/weather-research/wr006/measurement_support.py audit --input-dir $MidasInput --frozen-selection "$Wr006Scratch/selection.json" --public-evidence-dir $Wr006Public --receipt "$Wr006Scratch/audit-2.json"
(Get-FileHash "$Wr006Scratch/audit-1.json").Hash -eq (Get-FileHash "$Wr006Scratch/audit-2.json").Hash
```

Create directories first. Public response bodies remain outside Git, with original
snapshot filenames, sizes and hashes in [public-evidence-pins.json](public-evidence-pins.json).
The report records the six exact public routes/statuses. A future live page can change;
absence or changed bytes is an explicit prerequisite/error, not permission to repin
or follow a login. No retrieval client is part of this utility. Offline reproduction
requires those retained snapshots or identical lawfully supplied copies. This is not
a portable publisher-authentication scheme. The report's audit seal uses the original
Windows-newline frozen selection; a regenerated LF selection has a different input
receipt hash, with the same candidate/decision and byte-identical repeated audits.

Source members and response bodies are each bounded to 2,000,000 bytes by the reused
fingerprint function. Hashes are rechecked; ordinary post-read changes fail. No hostile
concurrent-writer guarantee. Receipts cannot overwrite files or be written within
source/response directories or the repository. Success exit 0 means evidence auditing,
**not historical reference success**; missing/altered/unsupported inputs return exit 2.

All **12 new tests are synthetic**, not fabricated historical evidence. They test
selection, immutable pins/output and rejection of unsupported claims. The unchanged
22 WR005 tests cover the inspected metadata schema. Actual QC integer decoding,
physical-time interpretation, observation duplicates and station history are not
implemented/tested; the report records those scientific gates as blocked. A changed
live dictionary or newly supplied capability needs separate scientific review.
