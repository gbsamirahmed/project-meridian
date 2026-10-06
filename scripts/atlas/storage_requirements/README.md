# Retained Atlas infrastructure requirements measurements

Read-only, named-product inventory for the [assessment](../../../docs/research/atlas-storage-processing-serving-requirements.md).
No acquisition, payload reprocessing, private inspection or production consumer.
The existing Meridian storage-root resolver locates the sibling/environment-configured
`meridian-data`; only the five named derived product manifests and their listed files
are accessed. Repository source receipts remain unchanged.

From repository root, with the retained Earth Lab Python environment:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/storage_requirements/test_measure.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/storage_requirements/measure.py --check
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/storage_requirements/validate.py
```

`measure.py` without `--check` records the lightweight deterministic measurement JSON
in `docs/research`; `--check` writes nothing. Manifest hashes are verified; payload
sizes are stat-checked, not freshly content-hashed. Reported historical timings,
archive receipts and hypothetical raw-grid calculations remain distinct from the
new inventory. No capacity, network or memory benchmark is performed.

`validate.py` is the assessment's precommit validator: it expects main/origin-main
0/0, compares protected/history bytes against `1c2d10e`, runs six new tests and
64 unchanged contract/domain tests, repeats the inventory check twice, validates
links/anchors/navigation/JSON and writes only its assessment receipt. Rerun it on a
clean, synchronized main after committing as well if needed. Its historical receipt
records validation at the assessment checkpoint rather than claiming future status.
