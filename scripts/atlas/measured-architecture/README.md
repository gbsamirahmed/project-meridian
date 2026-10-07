# Atlas measured architecture assessment tooling

Read-only receipt extraction and assessment validation. No new workload benchmark, pilot/runtime modification or architecture implementation.

From the repository root using the retained Python runtime:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/measured-architecture/assess.py --check
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/measured-architecture/test_assess.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/measured-architecture/validate.py
```

`assess.py` without `--check` explicitly rebuilds only the compact Git evidence receipt from hash-pinned historical receipts. It does not construct or publish a generation, execute derivations, start serving, benchmark or acquire evidence. `validate.py` preserves all non-navigation files at `bae7c3e`, verifies retained sources/history, runs established regressions and writes only the new architecture-validation receipt. Logs remain in the external pilot acceptance directory; historical receipts are never overwritten.
