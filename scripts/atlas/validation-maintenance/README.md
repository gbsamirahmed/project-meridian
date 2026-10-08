# Atlas validation-evidence maintenance and amortization experiment

This isolated research adapter imports the unchanged prior full-validation predicates and fixed moderate partitions. It is never imported by production Atlas or the accepted Tryfan pilot. See the prospectively frozen [plan](plan.json) and [durable report](../../../docs/research/atlas-validation-maintenance.md).

From the repository root, use `../meridian-data/earth-lab/.venv/Scripts/python.exe`:

```powershell
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/validation-maintenance/test_model.py
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/validation-maintenance/run.py --check
& ../meridian-data/earth-lab/.venv/Scripts/python.exe scripts/atlas/validation-maintenance/validate.py
```

For a new campaign, `run.py --campaign campaign-your-unique-label` refuses an existing directory. It executes the frozen 13 sequences, three independent repeats, full/incremental oracle comparisons, receipt maintenance and coherent publication; approximately several minutes locally. State and raw JSON stay in `C:/Users/gbsam/Documents/Codex/atlas-validation-maintenance-v1`. Do not point it at pilot/source storage. Measured implementation/source hashes and raw output hashes are pinned in compact results. `--check` reconstructs every proposal in the first repeat and verifies all raw files; it does not issue new evidence or rewrite accepted history.

`plot.py` reproduces the scientific SVG. `report.py` produces the report and decision manifest from measured outputs. Neither changes the timed adapter. No new dependency, receipt backend, garbage collector, provider trust or signing service.

The trust anchor is supplied independently by the known local verifier, not by a candidate. It binds exact membership, immutable receipt and relationship buckets, full rule/implementation identity and accepted context. Missing/mismatched evidence falls back to full predicates. Current component hashes and publication invariants still run. Receipt issuance occurs only after the adapter's own successful dispatch; historical roots are immutable. The lower-level `commit` helper is internal campaign orchestration; outside callers use `publish`, which validates and issues internally. All source/physical semantics remain pinned separately in the exact retained qualifier.

Initial issuance and ongoing maintenance are included in incremental elapsed time. Shared fixture/update construction and atomic publication are measured separately because both paths need them. This avoids charging receipts to neither path or requiring the full-only baseline to mint unnecessary receipts. Logical reads, checks, bytes and elapsed time remain separate dimensions. All objects remain retained; retirement is reachability analysis only. Local process interruption does not prove multiwriter, hostile concurrent mutation, power-loss or cloud safety.
