# Tryfan pilot S2 — qualified native evidence readers and queries

## 1. Executive result

**C - S2 SUCCESS.** A fresh local process opens the immutable S1 published generation and answers bounded native WorldCover, historical NRW inventory and dated appearance-metadata questions. Raster/vector claims coexist without a winner. Native definitions, mapping loss, time, support, rights and catalogue provenance survive. S1 publication semantics and all retained bytes remain unchanged. S3-S6 have not begun.

## 2. Starting checkpoint

Clean `main` at `b5ac71508776c289ec93a0a894ee6641d62fb879`; fetched `origin`, confirmed `origin/main` and0/0 divergence. No newer commit or legitimate work required reconciliation. The genuine S1 current generation is `2ffa20f9ac33123c3babb62381ba4559cbd045fb180d978a9ed6228514ed9b92`; its parent is `3408e5e9909c47b7e16d9d136f39cffa548c86808893468aa4a0de3d599c1f8c`. This task reads these states, never publishes a fabricated scientific revision.

## 3. S2 objective

Turn published catalogue registrations into qualified native-evidence answers. The question is what the retained evidence supports saying at a place, rather than which canonical value Meridian should assign there.

## 4. Scope

Exactly [plan S2](tryfan-regional-pilot-plan.md#30-implementation-slices): WorldCover lazy native cell/support queries, all193 NRW native vector records, common mappings, unsupported requests, provenance and dated July appearance metadata. Appearance queries return metadata only, never a pixel-derived physical claim. Developer CLI/library and one bounded Python worker; no production consumer.

## 5. Explicit exclusions

No terrain selection/derivative execution, slope/aspect, dependency/freshness traversal, invalidation, recomputation, scientific updates, HTTP, tile serving or client. No data acquisition, source mutation, imagery normalization, classification, universal cover truth, current-state inference, ecological/source accuracy assessment, vegetation fraction, source superiority, suitability or hazard. Weather/Traverse/production Atlas remain unchanged. No private data access.

## 6. Authoritative foundations

The [plan](tryfan-regional-pilot-plan.md), [S1 implementation](tryfan-pilot-s1.md), [Semantic Evidence Contract v1](../atlas/semantic-evidence-contract.md), [native WorldCover proof](tryfan-worldcover-binding-proof.md), [native semantic comparison](../atlas/source-native-semantic-comparison.md), [Tryfan query/revision proof](tryfan-qualified-query-proof.md), [world-model synthesis](atlas-world-model-architecture-synthesis.md) and [Exe query precedent](exe-water-query-proof.md) govern this slice. All11 registered metadata receipts are verified before loading dictionary/fixture definitions. Existing domain declarations/validators and WorldCover template/instantiation functions are reused, not forked into another contract.

## 7. Published-generation integration

`openEvidence({store,generation,dataRoot,locators})` calls S1 `load`. Default reads current once; explicit history remains supported. Generation identity/hash, canonical catalogue, root/reference/ancestor integrity are mandatory. Native paths are resolved exclusively from registered artifact IDs and that generation's locator map: no arbitrary directory discovery.

S1's `verify:false` permits loading intact metadata while a particular required native file is unavailable. S2 then independently verifies every used artifact's byte count/SHA, in both Node and the worker before native I/O; appearance metadata queries verify its seven referenced assets. Thus a missing WC file is operationally unavailable while intact NRW remains readable. Hash mismatch fails explicitly. Full310-file verification remains the S1 developer command and regression, not an unqualified per-query availability claim about terrain that S2 does not read.

The published seed still honestly advertises registration-only capabilities. S2 advertises separate **reader capabilities**, never retroactively mutates the seed or claims completed integrated G0. Query/definition objects are deterministically reconstructed from pinned catalogue metadata. Their publication with the full integrated state remains subsequent work.

## 8. Evidence readers implemented

[Native adapter](../../pilots/atlas/tryfan/adapters/native.py), [semantic wrapper](../../pilots/atlas/tryfan/semantic.mjs), [query interface](../../pilots/atlas/tryfan/query.mjs), [CLI](../../pilots/atlas/tryfan/query-cli.mjs), [measurement recipe](../../pilots/atlas/tryfan/measure_s2.mjs) and [focused tests](../../pilots/atlas/tryfan/tests/query.test.mjs). Read-only JSON-lines worker, one initialization, max32 pending requests,30s watchdog; no scheduler/database/network service. PROJ network acquisition is disabled. Disposable in-memory arrays/bbox candidates have no independent knowledge identity.

## 9. WorldCover reader

Registered TIFF SHA `9a0ad7162b1fb5fdc276a90c219c8d1d1daa0e83650ccd22d1dfbb51cbe98f6d`:334×554 uint8 native EPSG:4326 cells, nodata0, exact receipt affine,185,036 assignments. No reprojection/resampling of categories. Native codes10/20/30/50/60/80/100; eight shared templates include code0. A cell claim preserves the existing parent-row/column ID and `native-code-cell/v1@rasterSHA` revision. Nominal10m grid is not semantic accuracy, homogeneous physical ground or a fractional-cover measurement.

## 10. NRW reader

Registered native JSON SHA `d6d389a7c2a853a15e5a592c08d06f81d500c8778b7370144d246c62c2b7fab8`:193 EPSG:27700 native polygon/multipolygon records,28 code strings. Exact original scalar fields/nulls and objectids survive. Sorted source-scoped objectids make multiplicity independent of file iteration. Finite bbox prefilter followed by native geometric predicates; invalid/duplicate/empty geometry fails, without repair.

Earlier claims486814/486820/486832 retain revision1 and their bodies, apart from the asset's relocatable `href`; this is a storage locator substitution, not a new scientific claim. Existing common mapping is attached in the answer envelope without rewriting those claims. New records use the same deterministic ID pattern plus native-record/context hash revisions. Original geometry is referenced by artifact/selector, never copied into each claim. Opaque codes retain fields and an `unknown` gap rather than an invented habitat assertion or inferred absence.

## 11. Query model

```javascript
const e = await openEvidence();
try {
  const answer = await e.query({
    point: [266405,359387], crs: 'EPSG:27700',
    property: 'coexisting-semantic', time: null
  });
} finally { e.close(); }
```

Finite properties: `worldcover-native`, `worldcover-common`, `worldcover-support`, `nrw-native`, `coexisting-semantic`, `appearance`, `provenance`, and explicitly unsupported stronger `current-cover`, `physical-appearance`, `geological-substrate`. Other properties return unsupported, including S3 derivations. Optional `family` limits compatible evidence, never selects a winner. `support` is an explicit ordered BNG rectangle inside core. Responses expose generation, native claim/context/definitions, mapping, cell or feature support and catalogue trace. Irrelevant fields are omitted. Returned inspection/result mutations cannot change the next query.

## 12. Frozen query matrix

The [matrix](../../pilots/atlas/tryfan/query-matrix.json) was frozen before new query evaluation. It preserves Q05-Q11/Q13-Q20, the three inherited probes, outside point,400m supports and summit20m. Additional prospective southwest core-corner diagnostic and labelled digital/geometry/error fixtures do not select interesting source pixels retrospectively.

| Cases | Result |
|---|---|
| Q05/Q06 | Summit30 Grassland; qualified common crosswalk and native loss |
| Q07/Q07-20m | Summit400m:3096 assignments (29 tree,3039 grass,28 bare);20m:10 grass assignments |
| Q08/Q09 | Summit486832 D.1.1 dry acid heath; coexists with WC30 |
| Q10 | July12,2026 source/Lab010 metadata; no corrected appearance |
| Q11 | Northern80 annual persistent-water class, no instantaneous wetness |
| Q13/Q14 | Unsupported current cover/physical appearance; no substitute |
| Q15 | Rejected unmappable substrate target; native cover retained |
| Q16 | Outside pilot support, not absence |
| Q17 | Missing test-local WC locator: unavailable, no NRW fallback |
| Q18 | Source/product/representation/rights/artifact/generation trace; no fabricated derivation method |
| Q19 | Southern3090 assignments:9 tree,2668 grass,77 built,336 bare |
| Q20 | Northern3092 assignments:18 tree,794 grass,46 built,2234 water |
| Prospective core corner | WC30 plus opaque NRW `mosaic`/unknown; separate supports and claims |

All four population counts exactly match the earlier proof. [Results](tryfan-pilot-s2-results.json) contain compact qualified outputs and canonical full-matrix SHA `b4162d71186a5b110dd1282a5ea50f965b67f2c1bc7161d60593d6636943a74e`; full outputs are reproducible from the CLI, not duplicated source data.

## 13. Native semantic preservation

WC definitions retain PUM class thresholds and annual semantics. NRW retains source code, label, survey attributes, native nulls and dictionary Welsh/JNCC names. `mosaic` labels are not parsed into newly inferred per-cell fractions. NA does not mean bare/nonvegetated land. This slice does not turn opaque retained encodings into physical classifications.

## 14. Common interpretation/mapping behaviour

Only retained c4da565 crosswalks supply common concepts. Source term/target, direction, method record, relationship, loss and qualification remain visible. `PARTIAL OVERLAP` is encoded using v1 `partial`; D.5 remains `ambiguous`/unresolved because Welsh/JNCC wet/dry names differ. No mapping is invented for opaque codes. Substrate mapping is rejected/unmappable; no positive target assertion. A mapped concept supplements native evidence, not replaces it.

## 15. Spatial-support semantics

Pilot core EPSG:27700 `[264900,357800,267900,360800]` is half-open west/south included, east/north excluded. Native WC addressing uses west/north included, east/south excluded. Addressing compares against exact declared rectilinear grid edges using binary search; inverse-affine cancellation at an exact retained corner cannot assign the preceding column. No epsilon, snapping or extra geospatial precision is introduced. Point results retain the whole native cell. Support counts use transformed native centres, half-open BNG selection, never physical fractions.

NRW uses native `covers(point)`; own/outer/hole boundaries included and flagged; hole interiors excluded; all overlaps returned. Rectangle queries use exact intersection after bbox candidates and report intersection area separately from original support. Empty native membership within admitted study support is `missing-inventory`, not physical absence; outside core/native support is `outside-support`.

The frozen retained probes did **not** supply a real case outside one family's spatial coverage while inside the other's. This is reported honestly, not manufactured by moving a probe. Synthetic native addressing/hole/empty-inventory fixtures test those predicate distinctions; Q17 independently proves missing-family isolation against real NRW support. The core-corner real opaque result is not relabelled a coverage miss.

## 16. Temporal semantics

WC nominal annual2021 epoch and unknown per-cell acquisition times remain separate; publication2022 is not observation time. NRW survey context is historical with unknown exact local observation/validity; retention2026 is not survey epoch. Dated appearance preserves exact retained July observation/product/preparation fields. Null query time means native qualified context. Other/current requested epochs cannot be asserted from these historical classifications; no generic temporal engine.

## 17. Status/unknown semantics

Operational `available`, `unavailable` and `excluded-by-context` surround frozen v1 ClaimResult; malformed requests throw coded errors. v1 gaps used here: `not-classified` (labelled code0 fixture), `unknown` (opaque inventory interpretation), `missing-inventory` (native no membership), `outside-support`, `unsupported`. The actual WC window has no0 cells, so its no-data test is explicitly synthetic. No non-detection/current absence is invented from cover. Not-applicable is not asserted where it has no source basis.

## 18. Property-specific resolution

WorldCover questions request WorldCover evidence; NRW questions request inventory evidence. A geology/current/physical-appearance question has no compatible fallback. A WorldCover query restricted to NRW is excluded-by-context/unsupported even at their shared summit. Missing WorldCover does not select habitat as a replacement.

## 19. Coexistence behaviour

At summit WC30 Grassland and NRW486832 D.1.1 dry acid heath are both returned with separate feature/cell support, vocabulary, modes, time and mapping qualifications. Annual remote-sensing classification and older ecological survey are not a contradiction or asserted simultaneous state. There is no average, ranking, shared canonical raster or categorical merge.

## 20. Provenance trace

Answer → lazy native cell template or source-scoped NRW objectid → representation/product/source catalogue keys → retained SHA artifact + use/alias → immutable publication generation. Query provenance retains rights/resources, registration receipt pins and source/product revisions. Physical locators stay outside semantic identity; query outputs use `meridian-data://` aliases and artifact IDs. Missing files are not silently skipped and unregistered files are never eligible.

## 21. Rights/attribution

Existing WorldCover CC-BY4/Copernicus and NRW OGL3/NRW/OS/JNCC notices remain in linked resource metadata. Appearance retains its established Copernicus rights. No full licensing engine, new licensing survey or inferred redistribution permission. Serving/access-control decisions remain later work.

## 22. CRS handling

Explicit EPSG:27700 or OGC:CRS84 xy input. Native WorldCover EPSG:4326 and NRW27700 are checked against actual files/receipts. Existing pyproj `always_xy` transformations, operation description/runtime/accuracy qualification are exposed. Nonfinite/out-of-range coordinates and unsupported CRS fail. Operation accuracy is not measured local registration accuracy; no new datum/geometry research or network grid download.

## 23. Failure semantics

S1 codes remain authoritative for missing/unknown/malformed generation/root/reference/hash state. S2 explicitly rejects invalid-request, invalid-crs, invalid-coordinate, invalid-support, unsupported-representation, corrupt-native-code/value, invalid-native-geometry/semantic-reference, invalid-locator, worker-unavailable and hash-mismatch. Missing artifact is operationally unavailable. Python protocol errors are bounded/visible; stdout carries deterministic JSON only. No silent geometry repair, code substitution, unrelated source fallback or source repair.

## 24. Fresh-process reproduction

Five separate CLI processes each load the persisted root, construct native readers and execute the complete real matrix; canonical full-output SHA is identical in all five. Focused tests additionally compare independent subprocess output to library output. No module registry/construction history or persisted query cache is required. Q17 is reproduced with a separate locator override, never altered retained data.

## 25. Historical-generation behaviour

The genuine S1 parent is explicitly loaded and queried; identical summit native claims reproduce while generation identity differs. This is administrative retained metadata history, **not** evidence of scientific change. Scientific cross-generation update/freshness/replay remains S3/S5. No generation/root/locator bytes are written by S2 readers.

## 26. Performance measurements

[Measurements](tryfan-pilot-s2-results.json) are observations, not SLAs:30 initialized requests per property and five independent full-matrix processes.

| Observation | Measured |
|---|---|
| Native worker initialization | 124.98ms |
| Whole reader initialization (Python/fixture loader included) | 1234.93ms |
| WorldCover median / p95 | 1.211 / 1.505ms |
| NRW median / p95 | 1.163 / 1.312ms |
| Coexistence median / p95 | 1.188 / 1.288ms |
| Fresh process + initialization + complete matrix median | 1641.89ms (range 1599.24–2415.80) |
| Native raster/centre arrays | 3,145,612 bytes |
|193 rebuilt bbox coordinate values | 6,176 bytes |
| Native geometry WKB size proxy | 211,666 bytes |

Measurement-process Node RSS after multiple reader/fixture-loader sessions is 454,057,984 bytes; it is **not** attributable solely to evidence/indexes and excludes worker process memory. Array/bbox/WKB sizes are narrow allocation/storage proxies, not complete process footprint. Runtime/fixture loader overhead remains a pilot measurement question; no premature caching/database choice.

## 27. Tests and validation

33 Node S2 tests and9 Python native fixture tests cover public query semantics, retained assignments, reuse of original NRW claims, mappings, time/rights/provenance, CRS, copy isolation, native boundaries/holes/multiplicity, code/geometry corruption, missing-family isolation, source immutability, explicit history and fresh subprocess reproduction. [Stage-aware validation](tryfan-pilot-s2-validation.json) also runs22 S1 tests,22 planning safeguards,64 frozen domain tests and isolated semantic TypeScript checks; verifies all310 pilot assets, the1575 admission sources, all42 historical statuses,113 protected production hashes and all historical reports/tooling. Historical S1/planning validators' no-later-code gates remain historical rather than being rewritten.

## 28. Plan deviations, if any

No foundational/technology deviation or contract change. Final boundary review replaced inverse-affine floor with exact native-edge addressing to satisfy the frozen half-open convention; tests now exercise real retained NW/E/S/interior corners. All frozen query results/hash remain unchanged. Two bounded implementation clarifications: S2 reconstructs qualified query metadata over the unchanged registration-only published S1 seed and advertises runtime reader capability separately; full integrated G0 publication is not pulled forward. Three original NRW claim records are reused exactly except storage href, with new common interpretation in an envelope; 190 additional inventory records extend the source-scoped pattern. Empty/missing spatial cases without a real retained frozen probe remain labelled fixtures, not fabricated observations.

## 29. Risks discovered

Fixture loader/Python startup costs dominate cold reading; quantified, not optimized. Historical NRW lookup vocabulary has opaque/mosaic codes and ambiguous D.5: future consumers must show native unknowns/qualifications. Geographic conversion accuracy is not local source accuracy. Retained read buffers are pinned to verified initialization; hostile concurrent external source mutation/power-loss/distributed coherence is not newly proven here. Query processes must close the worker. Copy isolation prevents developer inspection from mutating subsequent meaning. No S2 query result is promoted to a canonical derived truth.

## 30. Remaining pilot work

S3 derivation/lifecycle, S4 serving/isolated consumer, S5 scoped and mixed-family publication/interruption, S6 instrumented acceptance remain incomplete. Integrated serving and mixed-family scientific publication remain the two pilot admission exit tests. Appearance science remains unresolved/non-blocking; Swiss multiview parked. Historic INCONCLUSIVE/NOT JUSTIFIED/PARTIAL/SCALE-CONDITIONAL research findings are unchanged.

## 31. Decision A/B/C/D

**C - S2 SUCCESS.** The14 S2 requirements hold: generation-backed native reads; WC/NRW meanings and raster/vector coexistence; qualified mappings/time/support; incompatible fallback rejection; catalogue trace; deterministic/fresh-process outputs; immutable sources/contracts; no S3 execution. This is a bounded semantic-read milestone, not current land-cover truth, source validation, global architecture or completed regional pilot acceptance.

## 32. Exactly one next bounded task

**Tryfan pilot retained derivation and lifecycle integration - S3 only.** Execute the next frozen plan slice using its retained original methods and scoped receipts. It has not begun; no implementation follows automatically from this report.
