# Local architecture decision comparison

This folder contains an isolated metadata comparison and decision safeguards, not
an Atlas runtime, a production database, or a new publication implementation.

Read `plan.json` and `docs/research/atlas-local-architecture.md` first. Accepted
source/fixture/store paths come from their existing receipts. Generated compact
JSON, SQLite files and raw regression logs stay in the configured external
decision directory. The literal path in this disposable harness is an experiment
locator, never an evidence identity or a selected runtime drive configuration.

From the repository, using the existing public-data Python environment:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/local-architecture/compare.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/local-architecture/test_compare.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/local-architecture/validate.py
```

Comparison measures candidate identity selection and preserved bodies, not native
payload query/validation latency. SQLite creation/reopen/sealing, rollback,
null identities and exact spatial filtering are included. Real temporal interval
semantics and canonical publication safety retain their independent accepted
regression suites. `next-task.json` defines the unbegun first runtime slice.
