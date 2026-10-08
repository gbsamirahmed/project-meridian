# Retained-generation metadata scaling experiment

Experiment-only tooling after `c4f50a4`. The [prospective plan](plan.json),
[report](../../../docs/research/atlas-generation-scaling.md),
[results](../../../docs/research/atlas-generation-scaling-results.json) and
[validation](../../../docs/research/atlas-generation-scaling-validation.json)
define its limits. The accepted Tryfan pilot is never edited or republished.

From the repository root, using retained dependencies:

```powershell
node scripts/atlas/generation-scaling/fixtures.mjs
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts/atlas/generation-scaling/run.py
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts/atlas/generation-scaling/run.py --check
node --test scripts/atlas/generation-scaling/test-experiment.mjs
..\meridian-data\earth-lab\.venv\Scripts\python.exe scripts/atlas/generation-scaling/validate.py
```

`fixtures.mjs` copies seven exact metadata/locator generations and two existing
portrayals into the explicit external `stateRoot` in the plan. It appends labelled
administrative successors through the original S1 writer to reach depths28/112.
It reuses retained source references, never payload-copies a DEM or source image.
Construction uses the actual validation/publication path; its costs are recorded
separately from reads. Existing fixtures are checked, not overwritten to repair
conflicts. Diagnostic staging is retained and is not published knowledge.

`run.py` executes18 fixed cases sequentially, five fresh processes and one
twenty-request warm session each. Raw samples stay in that external root;
completed files are resumed only with the same prospective plan hash. To collect
a wholly new campaign, select a separately named isolated state root in a new
explicit prospective plan; do not delete accepted or historical evidence.
The supplementary seven metadata-only controls are not scientific pilot states.
`--check` revalidates the retained raw/compact receipt equivalence and accepted
store hashes without retiming or replacing the final judgement. The v2 answer
comparison also normalizes exact pin IDs in provenance arrays; original timing
receipts are retained, with separate equivalence rechecks.

The two primary variants both execute the existing S4 delivery boundary, S2
readers and S3 results. `runtime.mjs` uses a hash-guarded Node24 module-load hook
only in these experiment processes. The accepted variant adds counters. The
experimental variant substitutes only read-only `generations.load`, validates
and hashes each distinct generation once, and shares parsed immutable metadata
inside one `AsyncLocalStorage` request. It keeps selected-generation canonical
checks, full ancestry/cycle checks, required locator and portrayal verification,
and the existing source-specific checks. A new request starts empty; nothing
is trusted across requests. No production import references this directory.

Timing covers the S4 delivery-library operation, not HTTP/network transport.
Fresh process is not cold physical storage. Counters measure synchronous Node
requested bytes, not disk traffic, Python IO, egress or billing. Node RSS is an
observation, not peak/total memory. Corruption/missing/orphan tests operate only
on newly owned fixture copies. An actual administrative root transition checks
old/new pinned answers in both variants. Tests do not corrupt retained evidence.

The stage-aware validator runs the established regressions without rewriting
historical S1–S6 or assessment receipts. Its logs are external; only compact
metadata/results/reporting are committed. This is not a production loader,
index, database, cache, compactor, API or another pilot slice.
