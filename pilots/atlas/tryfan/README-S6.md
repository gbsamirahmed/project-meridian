# Bounded retained Tryfan pilot — S6 exit

[S6 report](../../../docs/research/tryfan-pilot-s6.md), [exact exit matrix](../../../docs/research/tryfan-pilot-s6-acceptance.json), [frozen plan](../../../docs/research/tryfan-regional-pilot-plan.md). The bounded pilot is closed with **C - PILOT EXIT ACCEPTED**; no production readiness claim.

From the repository root with existing retained dependencies:

```powershell
node pilots/atlas/tryfan/server.mjs
```

Open **http://127.0.0.1:4191/**. Query retained summit: Welsh32.919°/ratio1.191, separate WorldCover30 and historical NRW D.1.1; southern remains AWS8.811°. Inspect provenance/date/rights, switch full/400m views, pan/zoom. Pin latest publication explicitly; source-derived imagery remains unchanged. No correction or physical relighting.

```powershell
node --test pilots/atlas/tryfan/tests/acceptance.test.mjs
node pilots/atlas/tryfan/measure.mjs --check
node pilots/atlas/tryfan/tests/warm-matrix-s6.mjs
node pilots/atlas/tryfan/tests/read-metrics-s6.mjs
..\meridian-data\earth-lab\.venv\Scripts\python.exe pilots/atlas/tryfan/validate_s6.py
```

The first `measure.mjs` run requires an absent external `s6-acceptance` root, builds independently and refuses to overwrite prior acceptance state. Use `--check` for persisted logical reproduction and repeated measurement; it neither republishes canonical current nor acquires data. Do not delete retained inputs. Rebuild harness requires an explicit absent store within S1's permitted pilot runtime area. Initial raw measurement receipts remain intact; repeat commands write `*-repeat.json` sidecars. Diagnostics/PNG QA stay external; read meter counts only Node synchronous requested reads. Single writer/local process failure only. Historical S1–S5 remain intact.

Exactly one next task: **Atlas measured storage, processing and serving architecture assessment**, not begun. No S7.
