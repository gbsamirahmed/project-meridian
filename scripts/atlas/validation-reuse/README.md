# Atlas validated-component reuse proof

This isolated architecture model follows clean `38f9ba7`. It changes no pilot,
production imports, retained evidence or foundational contract.

The prospectively frozen [plan](plan.json) and [check inventory](inventory.json)
distinguish component-local, cross-component, publication, policy and current
external-state guarantees. Read the [report](../../../docs/research/atlas-validation-reuse.md)
for the trust boundary and remaining population-wide work.

From the repository root, use the existing environment:

```powershell
& '../meridian-data/earth-lab/.venv/Scripts/python.exe' scripts/atlas/validation-reuse/test_proof.py
& '../meridian-data/earth-lab/.venv/Scripts/python.exe' scripts/atlas/validation-reuse/run.py --check
& '../meridian-data/earth-lab/.venv/Scripts/python.exe' scripts/atlas/validation-reuse/validate.py
```

`run.py` refuses an existing campaign. A deliberate new measurement requires a
separately named `--campaign campaign-name`; retain earlier raw evidence. Final
state is in `C:/Users/gbsam/Documents/Codex/atlas-validation-reuse-v1/campaign-final4`.
Synthetic benchmark objects stay outside Git. `--check` reproduces decisions,
counters, raw hashes and six independent historical eligibility pins, without
rewriting measured fixtures or accepted pilot state. Timings are observations,
not exact replay assertions.

The full and incremental dispatches share the same pure predicates. Incremental
selection is separately exercised against the full oracle and expected verdicts.
Both read/hash every currently referenced component. Current source payload
verification remains in established regressions; synthetic reads do not rehash
42.47 MB of source data. Every validation request clears process caches. OS cache
is not flushed. Five repetitions and five-process subsets are recorded.

`prepare()` is a trusted local verifier: it runs full acceptance, then issues
immutable local receipts and anchored outgoing/reverse directories. The caller
must pin its returned root independently of the proposed publication. A candidate
cannot name its own root. A receipt digest proves bytes, not issuer authority.
The verifier/anchor must be trusted; replacing that trust boundary, hostile root
issuance and concurrent external writes are excluded. Missing/corrupt/ineligible
optimization evidence falls back to full validation; invalid science does not
become acceptable. Rule identity binds core.py and the unchanged reused granular
helper source. Policy/context is checked separately. No CA/signatures/cache
product, database or distributed trust service is introduced.

`publish_checked()` invokes validation itself and rechecks current component
integrity immediately before the single-writer switch. It uses the previous
proof's fixed 33-record committed eligibility trie and atomic current/membership
root pair. Pre-switch staged files remain ineligible. Tests remove/corrupt only
owned temporary experiment files, use real abrupt child exits, and retain pinned
immutable historical publications. There is no cloud/power-loss/multiwriter claim.

`plot.py` reads completed receipts and renders the structural SVG. The report
uses these frozen observations, without optimizing the measured implementation.
The final next task is recorded but not begun.
