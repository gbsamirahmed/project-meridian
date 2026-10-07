# Tryfan pilot retained catalogue and immutable generation foundation — S1

2026-10-07. First bounded regional-pilot implementation slice.

## 1. Executive result

**C - S1 SUCCESS.** The retained catalogue and immutable-generation foundation work within the frozen local single-writer boundary. The genuine external pilot store registers the five admitted families and310 retained artifacts, verifies42,473,107 bytes, publishes a registration-only generation and recovers it from a separate process. Eight representation references preserve native/prepared distinctions. No query, derivation, freshness or serving capability is advertised.

[Measurements and logical receipt](tryfan-pilot-s1-results.json), [validation](tryfan-pilot-s1-validation.json) and [developer commands](../../pilots/atlas/tryfan/README.md) record evidence. This passes the S1 registration/restart portion of pilot tests A/O, not the later qualified-query form of A or complete pilot acceptance. Exactly one next task is **Tryfan pilot qualified native evidence readers and queries - S2 only**; it has not begun.

## 2. Starting checkpoint

Started clean `main` at **7809147ae86b14a19d195e0cdc9791b47caa59eb**. `git fetch origin` confirmed the expected checkpoint, existing `origin/main` upstream and0/0 divergence. No newer legitimate commits or local changes required reconciliation. Nothing was discarded. Implementation is isolated from production.

## 3. S1 objective

Make retained catalogue identity, immutable generation publication and recovery operational. A constructing process can terminate and a fresh reader can recover complete catalogue state using only the declared store, asset locator map and retained files. This is foundation infrastructure, not a resolved world model.

## 4. Scope

Create the five prospective S1 modules and focused tests under `pilots/atlas/tryfan/`, a README, bounded measurement/validation tooling and compact report receipts. Register exactly the frozen15 assets and295 Welsh manifest payloads. Core remains EPSG:27700 `[264900,357800,267900,360800]`,9km², with the accepted half-open boundary. No new scientific observation or regional expansion.

## 5. Explicit exclusions

No S2 native pixel/vector readers or semantic queries; no S3 derivation/dependency/freshness traversal; no S4 HTTP/tile/provenance API/client; no S5 scoped/mixed scientific update or S6 full acceptance. No data acquisition, source mutation, database, source replacement, classification, normalized appearance, shadow recovery, albedo, lighting, hydrology, Weather, Traverse or production Atlas change. Existing typed declarations/metadata are read through Vite, whose loader closes; it is not a pilot service.

## 6. Authoritative plan and contract references

The [frozen plan](tryfan-regional-pilot-plan.md#30-implementation-slices) and [machine-readable plan](tryfan-regional-pilot-plan.json) define S1, schemas, identities, external runtime placement and single-writer publication. [Pilot admission](atlas-regional-pilot-acceptance.md), [world-model synthesis](atlas-world-model-architecture-synthesis.md), [storage requirements](atlas-storage-processing-serving-requirements.md) and [persistent Tryfan proof](tryfan-local-persistent-proof.md) supply boundaries, not new technologies.

Reuse [Terrain Hierarchy Contract](../atlas/terrain-hierarchy-contract.md), [generic runtime](../atlas/terrain-runtime-selection.md), [Welsh proof metadata](../atlas/tryfan-second-region-proof.md), [Semantic Evidence Contract v1](../atlas/semantic-evidence-contract.md), [WorldCover binding proof](tryfan-worldcover-binding-proof.md) and [qualified Tryfan proof](tryfan-qualified-query-proof.md). All14 foundation reports and11 registration receipts remain hash-pinned by the plan. S1 invokes the frozen terrain registry validation and semantic-fixture validator without selection/query execution. It registers selected resources and context metadata, not all fixture claims.

## 7. Implemented module structure

| Module | S1 responsibility |
|---|---|
| [identity.mjs](../../pilots/atlas/tryfan/identity.mjs) | Finite canonical JSON, SHA256, typed errors, safe locators, reference keys |
| [catalogue.mjs](../../pilots/atlas/tryfan/catalogue.mjs) | Pinned retained registration, metadata reuse, reference/schema/integrity validation |
| [generations.mjs](../../pilots/atlas/tryfan/generations.mjs) | Immutable generation/root, staging, writer lock, explicit recovery/rollback, fresh load |
| [cli.mjs](../../pilots/atlas/tryfan/cli.mjs) | Register/stage/publish/inspect/validate/recover-lock/rollback; no listener |
| [catalogue.test.mjs](../../pilots/atlas/tryfan/tests/catalogue.test.mjs) | Public-interface tests, tiny destructive fixtures and actual retained/fresh processes |
| [worker.mjs](../../pilots/atlas/tryfan/tests/worker.mjs) | Labelled test-only subprocess writer/reader/failure driver |
| [measure_s1.mjs](../../pilots/atlas/tryfan/measure_s1.mjs) | Five independent construction/load observations outside identity |
| [validate_s1.py](../../pilots/atlas/tryfan/validate_s1.py) | Stage-aware regression/preservation/reference checks |

No production module imports the pilot. No new package dependency or package manifest change.

## 8. Retained evidence registered

| Family | Exact registered support | Qualifications retained |
|---|---|---|
| AWS common | Two retained z14 probe PNGs and z5/15/10 PNG/receipt | Global revision/measurement epoch/rights incomplete; no live fallback, no transfer of z5 contributor toz14 |
| Welsh regional | Original1m DTM, v2 manifest and295 complete z14–17 tiles | EPSG:27700 native /3857 delivery; native vertical datum unknown; strict complete support; no new observations in finer delivery |
| WorldCover | Native334×5542021v200 window | EPSG:4326 native angular cells; annual classification, not2026 cover or local truth |
| NRW | Original193-feature native extract | EPSG:27700; historical Phase1 inventory,28 native strings; no habitat/current-state query yet |
| Appearance | July12,2026 nativeB02/B03/B04/SCL and existing three Lab010 products | Native32630 RGB10m/SCL20m; prepared2770010m; fixed display, not illumination correction |

All source filenames/hashes and Welsh tile identities come from the frozen plan/manifest, not scanning neighbouring datasets. The catalogue retains rights, CRS, support, time, native semantics and processing metadata. It does not copy raster bytes into JSON/Git. Five sources/products, eight representations,310 materializations and310 locator entries are present.

## 9. Catalogue model

Research schema `atlas-tryfan-retained-catalogue/v1` contains a pinned registration basis, source references, product references linked to sources, representations linked to products, five family descriptors with original qualified metadata, and immutable materializations with family/source/product/representation uses. Source and product records reuse existing domain IDs/revision knowledge; content-addressed keys provide local reference closure. This is a finite retained registry, not a universal Meridian object model.

The single Welsh manifest is expanded only to its295 complete delivered entries. Partial/absent terrain support stays in imported product/level metadata, never padded. WorldCover/NRW resources/context remain separate; registration does not select a semantic winner. Native feature geometry remains in the external NRW extract, with193/28 counts qualified by the plan, not materialized as193 new claims in S1.

## 10. Identity rules

Source/product `kind,id,revision` remain established domain references with known/unknown revision shape. A catalogue key is SHA256 of that canonical reference; it is an address for a qualified reference, not a replacement physical identity. A materialization is `sha256:<exact-byte-hash>`, with source/product/use relations separate. Identical bytes can support several relations. Original `meridian-data://...` aliases remain stable symbolic evidence references.

WorldCover reuses `worldcover-v200-2021-N51W006-native-window`; Lab010 reuses its exact prepared identity. Welsh source DTM and prepared family have separate representation records. Sentinel nativeRGB and nativeSCL have separate sampling references, distinct from Lab010. Definition, claim, feature and derivation identities remain future contract consumers; S1 creates none of their resolution machinery. Imported semantic fixture contexts are explicitly labelled example-specific, not blanket spatial/time support for every registered WorldCover cell or NRW feature.

## 11. Identity and location separation

Generation identity excludes the physical data root and locator map. A map binds materialization IDs to safe root-relative paths. Tests move an identical tiny operational fixture to another filename/root and recover the identical generation; shuffled unordered registration collections also yield the same ID. Five independent real retained constructions yield the same parent-null seed. Stable original aliases are not rewritten merely because physical files relocate. A changed hash/size fails rather than silently retargeting an immutable reference.

## 12. Source immutability

Read-only hashing/metadata loading is the only operation on retained evidence. The310 selected files and1575 admission inventory files are verified unchanged; no original terrain, raster, vector or imagery is written/moved/repaired. Failure tests corrupt/remove only tiny labelled operational fixtures in temporary isolated stores. Runtime output goes to the admitted external experiment directory, not source/archive paths. No private contents are inspected; explicit private-path arguments are rejected before filesystem inspection.

## 13. Serialization and canonicalization

CanonicalUTF8 JSON uses sorted object keys, two-space indentation and a trailing LF. Unordered source/product/representation/family/artifact collections sort by stable ID; receipt paths, family representation sets, artifact aliases/uses have explicit stable sorting. Ordered arrays (RGB bands, source processing, geometry coordinates, temporal fields) keep their order. Undefined optional fields from typed metadata are omitted at JSON extraction; null remains null. Nonfinite/non-JSON values fail.

The store format `atlas-tryfan-pilot-store/v1` and catalogue schema are distinct from frozen `atlas-semantic-evidence/v1`. Unknown versions are rejected, not migrated. Canonical generation loading checks both checksum and canonical bytes. No wall-clock, host root, PID, operation UUID or measurements enter logical identity.

## 14. Generation model

A complete registration-only generation embeds format, semantic contract version, explicit capability flags, deterministic core, parent ID and full catalogue. All non-registration flags are false. A generation is write-once under `generations/{sha}.json`; a byte-different existing object fails `immutable-conflict`. No mutation/GC API exists. Direct external writes are detected by hashes, not prevented by a claimed filesystem ACL. Parent metadata integrity/ancestry closure is checked on load; an old generation is loadable explicitly.

## 15. Generation identity

Generation ID is SHA256 of the complete canonical logical payload, including parent. The independent parent-null retained seed is `14a6105c60241ba68c1f5765e2bec0f411cf4818d702ec34aacf8dc147edaab2`. The genuine currently published generation is `2ffa20f9ac33123c3babb62381ba4559cbd045fb180d978a9ed6228514ed9b92`, parent `3408e5e9909c47b7e16d9d136f39cffa548c86808893468aa4a0de3d599c1f8c`.

The first development registration was already persisted. Refining native/prepared representation addresses and labelling fixture context as example-specific created administrative successors rather than rewriting that first generation. The two earlier development registrations remain retained; source/product IDs and all310 bytes/hashes are unchanged. This is metadata registration history, not a scientific release or the U1/U2 update. Parent-null rebuild and published successor naturally have different IDs. Inspection can directly recover either; measurements report which is used.

## 16. Published-root mechanism

`current.json` contains only `{format,generation}` and is130 bytes. A reader reads it once and loads that immutable generation; it never inspects staging to infer truth. Generation and matching external `locators/{sha}.json` are complete before root switch. The locator file is not semantic identity; a declared alternative map is verified for relocation. Missing required map/assets is operational failure, never physical absence.

Default runtime: `meridian-data/experiments/atlas/tryfan-regional-pilot-v1/`, with generation/locator/staging directories and one writer lock. No actual runtime store or locator map is tracked in Git.

## 17. Publication sequence

```mermaid
flowchart LR
  L[Exclusive writer lock] --> S[Stage candidate and locators]
  S --> V[Validate schema, refs, assets and parent]
  V --> G[Flush immutable generation and locator closure]
  G --> P[Flush same-directory pending pointer]
  P --> R[Atomic current rename]
  R --> U[Release owned lock]
```

`register` performs this under one writer lock. `stage` validates but does not publish; explicit `publish --operation` revalidates the candidate and requires its parent to equal current. A stale parent fails, without automatic merge. Re-registering forms an explicit administrative successor; it does not claim a new measurement. Matching immutable objects can be reused on retry. Normal failures leave root/history intact and release owned locks.

## 18. Atomicity guarantees and limitations

Synchronous exclusive creation (`wx`), file write/fsync/close, then Node `renameSync` of a same-directory pending pointer over current provides the tested local publication boundary on this Windows filesystem. Separate reader processes observe a complete old/new generation in the bounded race test. No separate mutable current catalogue index exists. A reader explicitly pinned to history still resolves history after switch. No guarantee is claimed for power loss/directory durability, network filesystems, malicious/manual filesystem races or distributed/concurrent writers. Interrupted rename errors preserve the old root rather than bypassing validation.

## 19. Interrupted-publication behaviour

Three real writer subprocesses exit91: **after-staging**, **after-validation**, and **before-switch** (after the closed immutable generation exists). Fresh reader subprocesses still recover the exact old root at each point. Interrupted writer locks/stages remain for inspection. No orphan is automatically adopted.

`recover-lock --operation <id>` compares the exact nonce and requires PID liveness to return definitely dead. Alive, unknown or reused PID refuses; never reclaim by age. Explicit publish of the orphan operation rechecks assets, schema, parent and immutable objects, then switches. Wrong operation, concurrent writer, stale parent and immutable object conflict fail. This is S1 safety; F2 scientific recomputation and mixed-family update failure tests remain S5.

## 20. Fresh-process recovery

The constructing CLI returned/exited before another `node cli.mjs validate` process loaded current, checked metadata ancestry and rehashed310 files. Tests also build actual retained state in an independent empty runtime and recover it with a separateCLI. Five independent construction processes reproduce the same seed ID, while five independent readers recover the current successor. Load does not run the Vite metadata loader or use module-global construction registries or test setup; it reads declared persistent metadata/locators and retained files only.

## 21. Historical-generation retention

All accepted generation objects/locator closures remain on disk. A second administrative fixture generation leaves old bytes exactly unchanged, and explicit historical load works. Rollback validates the chosen root/assets before one coherent root switch; it does not edit the old generation. The real first registration also remains loadable. No automatically adopted/deleted staging, history expiry or archive migration. Historical **catalogue** recovery is proven; derived AWS pixel/method replay remains S3/S5.

## 22. Inspection tooling

From repository root:

```powershell
node pilots/atlas/tryfan/cli.mjs validate
node pilots/atlas/tryfan/cli.mjs inspect
node pilots/atlas/tryfan/cli.mjs inspect --generation <sha>
node pilots/atlas/tryfan/cli.mjs stage --store <isolated-directory>
node pilots/atlas/tryfan/cli.mjs publish --store <isolated-directory> --operation <operation>
```

Inspect exposes capability flags, source/product/representation relationships, aliases/hash/size/use records, locators and original metadata/rights plus verification. This is developer output, not a public provenance API. [README](../../pilots/atlas/tryfan/README.md) documents overrides, lock recovery, rollback and intentionally destructive test-only exit flags. No rendering/UI verification is required because S1 has none.

## 23. Error semantics

| Error family | Behaviour |
|---|---|
| `artifact-unavailable`, `hash-mismatch`, `invalid-locator` | Required evidence unavailable/corrupt/unsafe; never skipped or repaired |
| `unknown-catalogue-schema`, `unknown-generation-schema`, `contract-invalid`, `unsupported-capability` | Explicit incompatible structure/capability rejection |
| `duplicate-identity`, `invalid-reference`, `invalid-artifact`, `invalid-scope`, `invalid-value` | Conflicting/dangling/invalid data rejected before root switch |
| `store-absent`, `invalid-published-root`, `generation-missing`, `generation-unavailable`, `malformed-generation`, `generation-integrity`, `required-state-unavailable` | Current/history/locator closure unusable; no staging fallback |
| `immutable-conflict`, `publication-conflict` | Existing object differs or parent/current changed; no overwrite/merge |
| `writer-locked`, `writer-alive-or-unknown`, `lock-conflict`, `invalid-operation` | Single-writer ownership/recovery enforced |
| `plan-drift`, `metadata-drift`, `inventory-mismatch`, `invalid-store`, `invalid-command` | Frozen registration/configuration boundary violated |

CLI emits a structured error and nonzero status. Generic I/O failures remain visible with their OS code; no falsely successful partial registration.

## 24. Rights and provenance preservation

Welsh OGL3/attribution, ESA WorldCover CC-BY4 plus Copernicus notices, NRW OGL3/OS/JNCC retained notices and Sentinel legal-notice/credit remain attached through family source/product metadata. AWS universal source-specific licence remains explicitly unknown and linked to Tilezen/Joerd credits. Native acquisition/survey uncertainty, semantic epoch, official/mirror product identity and processing record remain distinct. Presence does not grant redistribution rights. This is provenance retention, not a licensing engine or complete point-specific lineage.

## 25. Tests

Focused [S1 tests](../../pilots/atlas/tryfan/tests/catalogue.test.mjs) exercise actual retained registration, independent construction/load, unordered determinism, relocation, missing/corrupt fixtures, identity/reference/schema rejection, immutable conflict, explicit history/rollback, staged publication and parent conflicts, three real abrupt writer exits, dead/live lock recovery and a reader spanning a switch. A final real-source verification follows fixture operations.22 focused cases pass.

Stage-aware regression reuses the existing22 planning safeguards and64 frozen domain tests, isolated semantic TypeScript validation, authoritative admission accounting/source hashing and original historical/protected hash checks. The historical planning validator's **no-implementation-yet** assertion is intentionally not a valid S1 acceptance condition; the frozen script/report/receipts stay unchanged. New validation reuses its structural/source invariants, verifies the exact310-file inventory against the old planning receipt, and replaces only stage-status assertions with S1 checks. No historical proof is rewritten.

## 26. S1 metrics

Five fresh independent builds and five fresh published loads; OS filesystem cache warm, not flushed. Raw runs/conditions are in the [receipt](tryfan-pilot-s1-results.json).

| Observation | Measured value |
|---|---:|
| Sources / products / representations / families |5 /5 /8 /5|
| Referenced artifacts / bytes |310 /42,473,107|
| Canonical catalogue / parent-null generation |324,627 /343,202 bytes|
| Published successor generation / current pointer |343,264 /130 bytes|
| Median construction including retained verification/typed metadata |887.62 ms|
| Median candidate validation |216.07 ms|
| Median pointer write/flush/switch |3.73 ms|
| Median fresh load with310 asset hashes + parent integrity |251.39 ms|
| Median full process wall time: build / load |1468.10 /427.06 ms|
| Median end-of-command RSS: build / load |252,141,568 /103,014,400 bytes|

These are local observations, notSLAs or global extrapolation. Build loads Vite once then closes it; RSS is end-of-command, not peak. Load validates current asset hashes plus ancestor metadata; it does not rehash every ancestor's identical asset set. A whole metadata generation is rewritten even for registration metadata refinement; no selective-storage claim. Future query/serving/recompute/fan-out metrics are not reported.

## 27. Deviations from the plan

No architectural or technology deviation. Native/prepared representation registration was made explicit during S1, as the plan requires; a successor preserves the first development registration instead of mutating it. A dedicated `locators/{generation}.json` map realizes the planned external configurable locator responsibility. Additional read-only measurement/validation and tiny worker files are supporting S1 tooling. Planned Contract-v1/DAG/freshness/serving validation is capability-specific: S1 validates reused declarations/resources and catalogue closure; absent claims/derivations/serving are explicit false, not fabricated completed validation.

## 28. Risks discovered

Full construction loads typed metadata via existing Vite and has materially higher RSS than fresh load; record it before considering optimization. Whole-file hashing and metadata snapshots are adequate for the finite42.47MB catalogue but not a scaling promise. A PID reused by another process intentionally prevents automatic recovery; explicit investigation is needed. Existing relative symbolic aliases are stable logical references, while relocation maps are external. Manual disk corruption, source loss, ancestry loss or unknown format fail visibly; no silent repair or stronger durability guarantee. Registration does not establish fine-scale appearance registration or physical colour.

## 29. Remaining pilot acceptance work

S2: qualified native evidence readers/queries and193 source-scoped NRW records with native meaning/time/unknowns. S3: exact original derivation receipts/freshness/replay. S4: generation-pinned integrated HTTP/artifact delivery and isolated consumer. S5: U1 scoped and U2 mixed-family coherence, scientific failure/restart and pinned reader tests. S6: full A–P measured exit suite. Integrated serving and mixed-family coherent **scientific** publication remain the two admission obligations; S1 root mechanics alone do not close them. Appearance remains unresolved/non-blocking, Swiss multiview parked, and every historical thread status remains unchanged.

## 30. Decision A/B/C/D

**C - S1 SUCCESS.** Real retained registration, stable identity/location separation, immutable root/history, safe local interruption and independent restart meet the bounded first-slice requirements. No foundational contradiction or S2 prerequisite was demonstrated. This is not complete pilot success, production readiness or resolution of scientific appearance debt.

## 31. Exactly one next bounded task

**Tryfan pilot qualified native evidence readers and queries - S2 only.** Implement only the second frozen slice: retained source-specific readers and bounded native/qualified queries, with WorldCover templates/lazy binding, original193 NRW feature references/opaque codes and dated appearance metadata. Stop before derivation/lifecycle, HTTP/client or mixed update. S2 has not begun.
