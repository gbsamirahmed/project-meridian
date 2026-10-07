# Tryfan pilot S5 — scoped and mixed-family publication

[Report](../../../docs/research/tryfan-pilot-s5.md), [frozen plan](../../../docs/research/tryfan-regional-pilot-plan.md). S1–S4 remain successful. No S6/full pilot exit, production Atlas, Weather or Traverse work.

From the repository root, existing Node/Python dependencies only:

```powershell
node pilots/atlas/tryfan/update-cli.mjs apply --scenario U1
node pilots/atlas/tryfan/server.mjs
```

Open **http://127.0.0.1:4191/**. Query retained summit: Welsh slope32.919°, planar ratio1.191, separate WorldCover30/NRW D.1.1 and July2026 appearance. The southern observer keeps AWS8.811°. An existing scene keeps its generation until **Pin latest publication** explicitly replaces the complete scene. Source-derived appearance is unchanged; no correction or physical relighting.

U1 is idempotent on its already applied root. U2 is an independent controlled applicability test, not a new source release or a replacement for U1. The measured U2 store is under the external runtime `s5-mixed`; serve it with an explicit `--store`. All staging/diagnostics/history stay outside Git. No automatic orphan adoption, GC or lock recovery. After an injected abrupt exit, inspect `writer.lock`, then `recover-lock --operation <exact nonce>` only once its PID is demonstrably dead. Retry `apply`; old current remains authoritative until success.

```powershell
node --test pilots/atlas/tryfan/tests/publication.test.mjs pilots/atlas/tryfan/tests/restart.test.mjs
node pilots/atlas/tryfan/tests/publication-browser.mjs
node pilots/atlas/tryfan/measure_s5.mjs --check
..\meridian-data\earth-lab\.venv\Scripts\python.exe pilots/atlas/tryfan/validate_s5.py
```

Destructive failure injection runs in explicit isolated test stores and never changes source evidence. Browser QA uses the existing Playwright Chromium. `measure_s5.mjs` without `--check` is the one-time measured real publication from S4, intentionally refuses an already-updated root. Measurements are observations, not SLAs. Whole metadata is rewritten despite two selective recomputations. Single-writer/local process-interruption guarantees only; no power-loss/cloud/distributed/public-service claim.

Exactly one next task: **Tryfan pilot measured exit acceptance - S6 only**, not begun.
