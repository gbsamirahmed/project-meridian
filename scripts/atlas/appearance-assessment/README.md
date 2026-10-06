# Riffelhorn appearance metadata assessment tooling

`assess.py` is a finite scenario evaluator against retained manifests. It verifies source,
prepared and parked metadata hashes, inspects five alpha samples, and emits the small
`docs/research/riffelhorn-appearance-assessment-results.json` receipt. It never changes
external data or makes network requests. Queries use LV95 native support; only delivery
lookup transforms to Web Mercator. It is not a general resolver or production hierarchy.

Run from the repository with the retained scientific Python environment:

```powershell
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts/atlas/appearance-assessment/assess.py
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts/atlas/appearance-assessment/test_assess.py
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts/atlas/appearance-assessment/validate.py
```

See the [report](../../../docs/research/riffelhorn-appearance-assessment.md) for limits.
F is conceptual, not a multiview pixel proof. No external payloads or stores are committed.
