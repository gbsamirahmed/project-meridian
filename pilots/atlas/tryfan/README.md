# Retained Tryfan pilot — S1

S1 only: retained catalogue, immutable JSON generations and developer CLI. No qualified queries, raster/vector I/O, derivation execution, freshness, HTTP, client, Weather or Traverse integration. [S1 report](../../../docs/research/tryfan-pilot-s1.md); [frozen plan](../../../docs/research/tryfan-regional-pilot-plan.md).

Requires existing Node >=22.12 and repository dependencies (`vite` loads the unchanged typed metadata/validators, then closes). No new dependency or network request. Commands run from repository root:

```powershell
node pilots/atlas/tryfan/cli.mjs register
node pilots/atlas/tryfan/cli.mjs validate
node pilots/atlas/tryfan/cli.mjs inspect
node --test pilots/atlas/tryfan/tests/catalogue.test.mjs
..\meridian-data\earth-lab\.venv\Scripts\python.exe pilots/atlas/tryfan/validate_s1.py
```

Default retained root: sibling `meridian-data`. Default store: `meridian-data/experiments/atlas/tryfan-regional-pilot-v1`. `--data-root <directory>` changes physical asset root; `--store <isolated-directory>` creates/uses an independent store. No private paths, production-directory stores or retained-input-directory stores. Inspection/validation fully verify all310 assets by SHA256, plus current and parent generation metadata integrity. Operational failure is never physical absence.

`register` builds from the hash-pinned plan/metadata, stages, validates and publishes. Registering again creates an administrative successor with current as parent, without inventing a scientific source revision. Independent empty-store builds yield the same parent-null identity. Unordered registrations sort by stable ID; ordered scientific arrays remain ordered. Host root/locator map, PID, operation nonce and timings stay outside logical hashes.

`inspect` prints catalogue identities, original rights/provenance/support/time metadata and the locator map. `validate` emits a compact receipt. `--generation <sha>` loads explicit retained history; it never scans staging to find current. `--locators <JSON-file>` permits a validated alternative `{assetID: relativeLocator}` map for relocation; it changes neither scientific refs nor generation bytes. Files must remain identical and inside the declared root.

```powershell
node pilots/atlas/tryfan/cli.mjs stage --store <directory>
node pilots/atlas/tryfan/cli.mjs publish --store <directory> --operation <returned-operation>
node pilots/atlas/tryfan/cli.mjs recover-lock --store <directory> --operation <lock-operation>
node pilots/atlas/tryfan/cli.mjs rollback --store <directory> --generation <previous-sha>
```

Only explicit `publish` accepts a staged candidate, after all validations and parent/current checks. `rollback` verifies history/assets before switching the root. No mutation/delete/GC command exists. A stale staged parent is a publication conflict, not an implicit merge. Operations and stages stay available for inspection.

`writer.lock` uses exclusive creation, PID and UUID. Never reclaim by age. Recovery requires the exact operation and a PID probe proving the writer dead. Alive/unknown/PID-reuse refuses. An abrupt writer exit retains its lock and staged evidence; the old root remains usable by readers. For operational tests, `register`/`stage`/`publish --fail-at after-staging|after-validation|before-switch` deliberately exit91 at supported boundaries (only register/stage can reach after-staging). Normal errors release owned locks. No automatic adoption/recovery.

Layout: `generations/{sha}.json`, `locators/{sha}.json`, `staging/{operation}/{candidate,locators}.json`, `current.json`, `writer.lock`. Write/flush/close immutable objects, then write/flush/close a same-directory pending pointer and `renameSync` over current. This tests local process interruption, not power loss, distributed/multi-writer transactions or hostile filesystem races. External manual mutation is detected by content checks; filesystem ACL enforcement is not claimed. Root readers capture one immutable generation.

`node pilots/atlas/tryfan/measure_s1.mjs` writes compact research results after five fresh independent builds and five fresh loads. It cleans only its own generated temporary measurement stores, never retained evidence or the genuine published store. Metrics remain outside identity. Test corruption/removal occurs only in labelled tiny fixtures. No source payload, generated runtime generation or locator file belongs in Git.

Exactly one next task: **Tryfan pilot qualified native evidence readers and queries — S2 only**. It has not begun. Integrated serving and coherent mixed-family scientific updates remain later acceptance work; appearance remains unresolved/non-blocking and Swiss multiview parked.
