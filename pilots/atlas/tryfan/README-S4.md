# Tryfan pilot S4 — local serving and isolated consumer

[S4 report](../../../docs/research/tryfan-pilot-s4.md), [frozen plan](../../../docs/research/tryfan-regional-pilot-plan.md). S1/S2/S3 remain successful. No S5 update, production Atlas, Weather or Traverse integration.

Existing Node/Python/repository dependencies only. From repository root:

```powershell
node pilots/atlas/tryfan/delivery-cli.mjs initialize
node pilots/atlas/tryfan/server.mjs
```

Open **http://127.0.0.1:4191/**. Port4190 from the plan is rejected by Fetch's unsafe-port rules;4191 is the sole pilot-level deviation. `--port`, `--store`, `--data-root` are explicit local options; no public bind/auth/API. Initialization writes only immutable generated portrayal/publication state under the existing external pilot store; it does not alter source evidence or activate Welsh applicability. Repeating identical initialization preserves current. Stop with Ctrl+C.

Select full core or inherited400m views, drag/wheel, click a place or **Query retained summit**. Inspect separate2021 WorldCover/historical NRW/July2026 appearance and original derived values/freshness. Toggle image/inventory outlines. The linked native-grid and native-Mercator inspectors avoid false cross-CRS corner stretches. **Inspect provenance** follows service references. **Pin latest publication** replaces the complete scene explicitly; ordinary queries keep the pinned generation. Missing retained tiles/evidence remain explicit; no network fallback. The original Lab010 camera gate remains pending.

```powershell
node --test pilots/atlas/tryfan/tests/http.test.mjs
node pilots/atlas/tryfan/tests/browser-runner.mjs
node pilots/atlas/tryfan/client/http-consumer.mjs http://127.0.0.1:4191
node pilots/atlas/tryfan/measure_s4.mjs --check
..\meridian-data\earth-lab\.venv\Scripts\python.exe pilots/atlas/tryfan/validate_s4.py
```

Visual checks require the existing Playwright Chromium installation. Measurements start independent ephemeral-port services. Actual bulk/QA PNGs/runtime generations remain outside Git. SHA256/rights/generation accompany byte delivery; query/current are uncached. Single native worker queue32,64KiB request body,64MiB read cap,16 service contexts; explicit restart after worker failure/availability change. Read-only `methodRevision` on retained derived questions assesses policy staleness without computation. Unknown/unpublished addresses404, malformed400, infrastructure unavailable503, valid semantic gaps200.

Exactly one next task: **Tryfan pilot scoped and mixed-family publication with interruption - S5 only**, not begun.
