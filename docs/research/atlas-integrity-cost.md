# Atlas retained payload-integrity and publication-validation cost assessment

## 1. Executive result

**C - ASSESSMENT RESOLVED.** Existing full validation is adequate for the next bounded local batch regional integration, within measured custody and workload limits. No validation cost has been demonstrated to obstruct that capability. Full validation remains the provisional default. Receipt optimisation is CLOSED pending genuinely new evidence; this assessment does not reopen it.

The retained Tryfan artifact sweep takes a plain median 213.11ms; a real administrative generation registration/publication takes 669.97ms. An existing 100km² terrain product's 11,429 files / 930.91MB take 9.61s to check. A 1.29GB retained imagery-field sweep takes 1.73s. Per-file path work dominates the many-tile sweep; SHA is substantial for the larger imagery fields. There is no universal hashing bottleneck. These are repeated local measurements, not production SLAs, cold-disk rates or integrated geographic acceptance.

## 2. Starting checkpoint

`eb3459353b40a1305928a870645d5d5d3be3d114`, clean `main`, upstream `origin/main`, divergence 0/0, confirmed after fetch. The [frozen baseline](atlas-integrity-cost-baseline.json) retains branch, upstream, source/current/history identities and protected hashes. The final introducing commit is the commit containing this assessment, not a replacement of an earlier proof. No legitimate newer work was discarded.

## 3. Exact uncertainty

What cost establishes current retained payload integrity, metadata consistency, publication completeness and coherent acceptance? Which costs scale with bytes, artifact population, component/relationship population, membership, changed state or history? Is that cost a practical obstruction to the next retained regional integration? Previous population-wide counters did not answer elapsed-time attribution or custody boundaries.

## 4. Existing evidence and accepted foundations

Primary evidence remains authoritative: [S1](tryfan-pilot-s1.md), [S2](tryfan-pilot-s2.md), [S3](tryfan-pilot-s3.md), [S4](tryfan-pilot-s4.md), [S5](tryfan-pilot-s5.md), [S6 accepted exit](tryfan-pilot-s6.md); [storage requirements](atlas-storage-processing-serving-requirements.md), [world-model synthesis](atlas-world-model-architecture-synthesis.md), [derived lifecycle](atlas-derived-understanding-lifecycle.md), and [semantic contract](../atlas/semantic-evidence-contract.md). The pilot remains CLOSED / ACCEPTED with all nine gates and 16 cases passed.

Architecture history: [c4f50a4 assessment](atlas-measured-storage-processing-serving.md), [e88b575 amplification](atlas-generation-scaling.md), [97c31c8 membership](atlas-component-membership.md), [38f9ba7 granularity](atlas-component-granularity.md), [35e4fbd validated reuse](atlas-validation-reuse.md), [a027ec7 maintenance](atlas-validation-maintenance.md), and [eb34593 packing](atlas-validation-packing.md). The latter's exact next rationale is to assess remaining current-integrity/publication guards, without more receipts or backend selection. Its high-long full/shared medians 8.58s/10.08s failed adoption; the larger localized 19.4% saving remains a bounded exception, not a default. Original reports/results and validation rules are unchanged and hash-pinned in the frozen plan.

## 5. Scope and exclusions

Measure unchanged retained validation paths and guarantees, with wrappers and isolated labelled fixtures only. Read retained Tryfan and larger already-present Riffelhorn products. No acquisition, new physical derivation, optimization, cache, incremental hashing, receipt representation, custody index, Merkle tree, policy redesign, production infrastructure or database. Weather, Traverse, production Atlas, Appearance research and Swiss multiview are untouched. Reading retained NPZ bytes for checksum timing does not unpark imagery research.

## 6. Frozen assessment criteria

[Plan](../../scripts/atlas/integrity-cost/plan.json) was written before implementation and measurement, SHA-256 `48f3cc4b0c3ae8cf2da7d5494ef4352b5d1f045bbca165b820b6ea8c6baaafce`. Freeze: outcome/counter equivalence between metered and plain original calls, invalid controls rejected, root preserved; five repetitions and nested/exclusive timers; known OS-cache uncertainty. Screening budgets were 60s median largest payload sweep and 5s median pilot publication: deliberately local batch engineering screens, not SLAs, production limits or retrospective pilot exit criteria.

Proceed if retained workloads validate at manageable batch cost without custody/acceptance contradiction. A separate future verification-boundary study requires an observed cost that materially obstructs an identified capability, or a concrete custody contradiction. Counts alone are insufficient. Stop after a decision and exactly one next regional/source-accountability task, unless a demonstrated blocker. All screens passed; nothing was modified to force a pass.

## 7. Actual validation execution paths

`pilots/atlas/tryfan/identity.mjs`: `safePath` resolves allowed root and file real paths; `sha` hashes supplied bytes; canonical encoding defines metadata identity. `catalogue.mjs`: catalogue identities, family/source/representation references and locators are validated; `verifyArtifacts` checks current paths, registered size and SHA-256 for every artifact. Real paths are not immutable identifiers.

`generations.mjs`: `validateGeneration` checks metadata closure through catalogue, dependency, update and delivery validators; `canonicalGeneration` repeats structural checks before identity encoding. `load` verifies stored canonical generation identity, reads current locators, verifies artifacts/materialized delivery and follows the accepted pilot's required bounded retained parents. `register` loads the parent, validates the candidate, verifies current artifacts/delivery, stages immutable generation bytes, then uses the established publication guard/current-root switch. Parent load and candidate verification can inspect the same unchanged bytes twice. This is measured existing behaviour, not a new preferred ancestry model.

`delivery-schema.mjs` checks pinned publication/delivery references and retained portrayal sizes/hashes. `dependencies.mjs` retains question/method/result distinction, native support, actual evidence use and policy-relative freshness. `update-schema.mjs` checks scoped transition/closure; it does not equate stale with false. The component proof `core.mjs` resolves explicit membership and validates selected component identities with no generation ancestry. Python `validation-maintenance/model.py.full` calls unchanged component integrity, local rows, relationships and publication checks; `commit` repeats current-byte integrity before immutable publication/root advancement. No receipt path is used here. Native low-level `load` establishes retained byte/metadata closure, not committed-publication eligibility by itself: a complete pre-switch orphan can exist on disk. S4 `delivery.mjs.published` restricts serving to the current published ancestry; the later component proof checks its committed membership trie before resolution. These are distinct guards. The component proof runtime substitutes explicit eligibility for the earlier ancestry selector only in proof processes. This assessment times native load/register and known-root component load separately; it does not time an entire HTTP query or install that runtime substitution in production.

## 8. Cost/guarantee classification

| Category | Actual work | Guarantee | Not guaranteed |
|---|---|---|---|
| Availability/custody | exists/open/realpath/stat | allowed current locator exists/is accessible at inspection | future availability, immutable filesystem, remote custody |
| Payload integrity | exact size, current read, SHA comparison | inspected bytes match registered identity | physical truth, source quality, rights compliance, race-free custody |
| Structured metadata | decode, canonical identity, native invariants | known content/structure and references consistent | universal ontology/science correctness |
| Component/relationships | current digest, qualifier/support/dependency checks | tested component and cross-component obligations hold | arbitrary future predicates |
| Closure/membership | completeness, uniqueness, required roles, transition checks | proposed world-model state complete under tested rules | arbitrary global coverage |
| Root/publication | prior root/eligibility, staged validation, final guard, fsync/rename | coherent single-writer local publication/process-interruption behaviour | power-loss durability, distributed atomicity, multiple writers |
| History | explicit retained identities and current retained byte checks | selected historical state reproducible when bytes retained | permanent archive custody |

## 9. Custody and failure assumptions

Ordinary local files are externally mutable despite immutable logical identity. SHA checks establish identity at read time; they do not enforce continued immutability or prevent mutation between validation and later consumption. The process trusts registered metadata and rules as the expected identity/semantic authority. Checksums do not authenticate a maliciously replaced complete catalogue, prove a publisher signature, establish legal entitlement or repair absent source bytes.

Single writer, local filesystem and same-directory atomic rename underpin publication. Fsync and rejection/interruption tests provide a local process-failure boundary; hostile locator races, power loss, provider failure and multiple writers were not tested. Changed verification policy would require an explicit custody/trust model, not simply a faster implementation. Current byte checks are retained in full.

## 10. Tryfan retained baseline

Real baseline: five evidence families, 310 registered files, 42,473,107B. Seven retained pilot generations total 5,658,085B. Seventeen accepted store files, source admission's 1,575 files, immutable generations, two delivery portrayals and current/locator state are protected by exact hashes. Current is `5f2c1b1f25c45ddea7e640f8c286a6caec5dc61aa55e8f678062bdc5704fca06`. S3/S5 historical results remain referenceable/replayable; stale remains a context-relative qualifier. Real baseline/previous component memberships, receipt counts and custody limits are retained in the baseline JSON. No accepted generation or source file is rewritten.

## 11. Isolated measurement fixtures

External state lives under `C:/Users/gbsam/Documents/Codex/atlas-integrity-cost-v1`. Four metadata populations: 48/192/768 components with 16/64/256 relationships and a 192-component/256-edge density contrast, each 64 rows/component across terrain, native semantic and derived/dependency metadata. Two eight-publication sequences, unchanged versus one-local change, use established full validation and commit. These are deterministic synthetic structural workloads, not new physical evidence.

Three existing read-only product sweeps: Swiss support 11,429 tiles/930,914,852B, Copernicus common 2,730 tiles/327,636,998B, Swissimage baseline 542 fields/1,294,380,168B. The first covers an existing 100km² preparation product and screens next-region file/byte cost; a checksum sweep is not full Swiss world-model acceptance. Three labelled byte controls hold 16MiB constant at 1 versus 256 files, then 256 files at 1MiB. No new source data. Existing component proof fixtures supply 7-current,112-current,112-oldest independent lookup controls. Pilot registration copies original store bytes into isolated state; current scientific evidence remains unchanged.

## 12. Instrumentation and methodology

[Harness](../../scripts/atlas/integrity-cost/README.md), [results](atlas-integrity-cost-results.json) and 38 external raw files preserve identities, counters and samples. Original source hashes and measured harness hashes are pinned. Node load hooks wrap unchanged exported bodies and synchronous file/JSON operations only in the metered process. Plain processes call original bodies without hooks. Nested calls record inclusive and child-subtracted exclusive time; no double-counting read/open or nested validation phases. Timer/bookkeeping overhead is not subtracted. Python uses unchanged full/commit bodies with inactive wrappers in plain mode; that dispatch is a limitation, not zero overhead.

Five repeats per case and mode, first sample retained, alternating mode order by case. Fresh process means no inherited module caches, not a flushed OS cache. Setup/fixture generation is outside read/validation timings; sequence construction and final commit are separate. Bytes requested are synchronous user-space reads, not measured disk traffic. Record counters are not physical IOPS. End-process RSS is observed, not peak private memory; Python/native aggregate memory is UNKNOWN.

## 13. Payload availability results

The 310-file sweep makes 620 realpath calls and 620 stat calls before/around reads; each file performs containment/path and size work. All 310 expected files are present and accessible. Larger Swiss sweep makes 22,858 realpath and 22,858 stat operations. This is intentionally existing ordinary-file custody verification, with no path cache introduced. Missing current and historical payload controls fail explicitly. Remote-outage/access-denied-specific timing is untested. Path count and latency vary by file granularity and local filesystem environment.

## 14. Payload hashing and byte-read results

| Case | Plain median [min, max] ms | Metered median ms | Files / selected records | Registered payload bytes |
|---|---:|---:|---:|---:|
| pilot-artifacts | 213.11 [205.98, 225.12] | 224.88 | see counters | see counters |
| pilot-structure | 40.38 [39.02, 50.91] | 42.65 | see counters | see counters |
| pilot-delivery | 4.39 [4.21, 12.44] | 4.55 | see counters | see counters |
| pilot-load | 347.59 [336.63, 377.42] | 352.38 | see counters | see counters |
| pilot-register | 669.97 [648.75, 860.71] | 705.24 | see counters | see counters |
| riffelhorn-swiss-support-v1 | 9612.12 [9219.57, 9849.10] | 10121.43 | 11429 | 930914852 |
| riffelhorn-copernicus-common-v1 | 2707.13 [2570.99, 3454.82] | 2602.29 | 2730 | 327636998 |
| riffelhorn-swissimage-baseline-v1 | 1727.19 [1458.42, 1981.78] | 1745.09 | 542 | 1294380168 |
| S1-16MiB | 13.83 [13.08, 26.99] | 13.60 | 1 | 16777216 |
| S256-16MiB | 129.41 [126.86, 143.60] | 131.76 | 256 | 16777216 |
| S256-1MiB | 113.26 [108.81, 186.03] | 114.79 | 256 | 1048576 |
| history-7-current | 284.94 [274.60, 302.31] | 302.35 | see counters | see counters |
| history-112-current | 283.84 [274.62, 321.21] | 307.31 | see counters | see counters |
| history-112-oldest | 284.47 [276.21, 311.64] | 318.38 | see counters | see counters |


Tryfan artifact verification hashes exactly 42,473,107 payload bytes in 310 buffer SHA calls plus 10 small metadata-text hashes/1,605B. Full load reads 313 payload-phase files/45,532,304B; that phase includes a 1,706B recipe as well as 3,057,491B of retained portrayal files. Registration reads 626 payload-phase files/91,064,608B: unchanged parent plus candidate verification, including portrayal/recipe twice. File categories distinguish these from source artifacts. Buffer SHA in registration includes metadata as well as payload; do not call every buffer hash a source hash.

At equal 16MiB, 256 files take 129.41ms versus one file 13.83ms. Reducing 256 files to 1MiB still takes 113.26ms. File-count/path overhead is structurally and temporally visible. Imagery-field SHA is substantial despite fewer files. Data are synthetic or existing prepared bytes, not equivalent geographic processing cost.

## 15. Metadata validation results

| Population | Components | Rows checked | Relationships checked | Plain median [min, max] ms |
|---|---:|---:|---:|---:|
| C48-E16 | 48 | 3072 | 16 | 15.19 [14.18, 349.51] |
| C192-E64 | 192 | 12288 | 64 | 56.97 [55.75, 1410.35] |
| C768-E256 | 768 | 49152 | 256 | 301.40 [270.76, 6339.87] |
| C192-E256 | 192 | 12288 | 256 | 60.91 [58.26, 733.93] |


Pilot structure-only checks take 40.38ms plain, reading 22 metadata records/867,436B in the measured path. Canonical identity construction intentionally revalidates metadata. Metered C192 exclusive medians: read 16.27ms, encode 14.88ms, parse 8.41ms, local predicates 11.54ms, SHA 1.61ms. These are operation observations, not an optimized schema/index recommendation. The first C48 sample is visibly slower than repeats; raw spread is retained rather than hidden.

## 16. Component/relationship results

Full synthetic validation examines 48/192/768 component digests and 3,072/12,288/49,152 native rows, with 16/64/256 edges. Density contrast keeps 192 components/12,288 rows but checks 256 rather than 64 edges. Relationship checks are small in these finite deterministic fixtures; broader dependency fan-out and actual expensive physical predicates remain unmeasured. Full validation does not select only changed components. This is a full-path cost assessment, not repeated receipt economics.

## 17. Publication-completeness and root-guard results

Membership checks equal current component population, including completeness/uniqueness/required families. Final Python commit rehashes all current components; its write/guard cost is separate from initial full validation. Native Tryfan administrative registration performs one final root rename after validation. Instrumented exclusive rename median is about0.37ms, fsync6.79ms, while the complete operation takes669.97ms plain. Root switch alone is not the price of publication acceptance. This administrative operation excludes S5 preparation/recomputation/closure assembly; S5's independently recorded assembly1.22–1.34s/validation584–651ms remain authoritative.

## 18. Repeated-publication costs

| Eight-publication sequence | Full validation cumulative median ms | Final commit guards + writes cumulative median ms |
|---|---:|---:|
| unchanged | 774.81 | 1111.04 |
| localized | 792.99 | 568.20 |


For every proposed publication, both sequences run 192 component integrity,12,288 row,64 relationship and192 membership checks, followed by192 integrity checks at final commit. Unchanged content is not trusted forever. Setup, new immutable component construction and final commit costs remain separate in raw results. Different commit medians reflect filesystem/timing variability, not proof that localized updates are inherently cheaper to publish. No receipt creation/lookup or new optimization is hidden in these full paths.

## 19. Scaling observations

Current payload work grows with bytes read and hashes, but many small objects also incur path/stat/open work. Full structured work grows with current metadata/row/membership population, not merely changes. Relationship count independently affects checks; its simple predicates remain inexpensive here. Publication encoding/write volume contributes beyond acceptance. Controlled samples are consistent with these structural drivers, not a formal asymptotic proof or global projection.

At 7 and112 retained component publications, selected current/old lookup remains33 membership records,one publication andfive shared components,zero ancestry. Directory branch byte size grows (5,823 versus12,375 membership bytes) even with fixed read count. Component bytes are1,287,421. Current/history plain latencies around284ms overlap. Thus bounded path depth is demonstrated, not constant total bytes for arbitrary growth. Accepted pilot parent loading remains disclosed separately; it is not the preferred scalable component model.

## 20. Failure-case results

Fourteen distinct controls reject and preserve prior root: native missing payload, same-size changed bytes, wrong size, wrong expected hash, corrupt generation metadata, invalid reference, invalid closure, historical payload absence, and abrupt pre-switch exit; Python incomplete membership, broken reference, malformed component JSON, invalid support and historical corruption. Metered/plain full decisions agree. Native malformed generation bytes fail digest first; separately, canonical-addressed malformed JSON reaches and fails parsing in the Python full path.

Pre-switch child calls the actual `register` interruption boundary and exits91; old current bytes remain identical. Isolated dead lock/staging remains recoverable under established S1/S5 semantics; this assessment does not silently clean or publish it. No full failure matrix, hostile race, remote outage or power-loss trial was added. [Measurement tests](../../scripts/atlas/integrity-cost/test_measurement.py) verify counters, equivalent paths, history and failure instrumentation. Prior pinned consumers/retry/historical replay suites are rerun in regression.

## 21. Historical access and integrity assumptions

Five fresh Tryfan loads return the same current identity and310/42,473,107B verification. Known historical component publications independently resolve with no ancestors; historical payload availability/corruption is checked explicitly, and failure does not erase historical identity or advance current. Exact reconstruction still requires retained bytes, locators and rules. Current root is not a history archive. The synthetic helper's discovery of the oldest ID happens outside measured selected lookup; known-root reconstruction itself is ancestry independent, and discovery is not claimed free.

## 22. Timing/memory observations

| Instrumented case | Path resolution | Stat | Read exclusive | SHA | Canonical encoding | ms, exclusive medians |
|---|---:|---:|---:|---:|---:|---|
| pilot-artifacts | 136.68 | 14.32 | 28.34 | 22.95 | 2.72 | nested child costs removed |
| pilot-register | 278.36 | 29.81 | 99.55 | 71.11 | 107.20 | nested child costs removed |
| riffelhorn-swiss-support-v1 | 7416.78 | 647.38 | 972.51 | 526.55 | 0.00 | nested child costs removed |
| riffelhorn-swissimage-baseline-v1 | 443.66 | 38.64 | 529.63 | 665.92 | 0.00 | nested child costs removed |


Five fresh whole-process Tryfan loads: 557.63 [552.42, 600.03]ms median[min,max], including startup. Plain and metered distributions are both retained. A metered sample can be faster due to ordering/cache/noise; do not subtract them as a calibrated overhead estimator. These local synchronous Windows observations include filesystem/security/cache behaviour; no OS cache flush or physical storage telemetry. Plain end-sample RSS spans143.26–252.96MB for pilot load,145.22–234.44MB for registration, and111.17–172.88MB for the Swiss tile sweep (decimal MB). Repeated samples in one process include allocator/GC retention; these are not incremental payload-storage footprints. No peak RSS guarantee or memory scaling conclusion follows from end-process RSS. Raw `RSS` samples remain available; Python memory is unknown.

## 23. Hidden amplification audit

Current registration parent/candidate reads duplicate source/delivery verification; load's13 generation-body reads span seven retained pilot generations, about10.07MB in that path. Metadata load totals69 reads/12.29MB; registration106/14.88MB. Serialization and JSON parsing are repeated, recorded. These are disclosed existing pilot mechanisms, not suppressed by instrumentation.

Component proof resolution retains33 membership nodes/one publication/five components; component metadata read/hash is complete, not selective magic. No ancestry is hidden inside selected historical lookup. Synthetic full validation scans all current components/rows/edges/membership, and commit repeats integrity. Membership discovery, fixture construction and inventory scans are outside read timing and are separately identified. No new directory, receipt, payload cache, incremental verification or trust shortcut was inserted.

## 24. Dominant measured costs

Dominance depends on workload. Many-tile Swiss validation is dominated by realpath work (~7.42s exclusive), versus ~0.97s read and0.53s SHA. Imagery fields spend ~0.67s SHA and0.53s read versus0.44s realpath. Tryfan current registration spends ~278ms path,107ms encoding,100ms reads,71ms SHA,30ms stat, with other nested predicates/guards. Do not add per-operation medians into an exact median total; child-subtracted timers avoid nested double counting but distribution summaries need not add.

Metadata predicates/current parsing, integrity and final writes remain population-wide. Their measured cost is manageable locally. Current-byte hashing is required by the existing ordinary-file trust boundary; using prior accepted identities alone would establish a different guarantee. Scientific/physical correctness and permanent custody are not purchased by more SHA operations.

## 25. Practical regional-expansion implications

All frozen screening cases pass, with a substantial margin. Full checks can run as explicit local batch work for the next bounded retained region; this is not permission to perform 9.61s sweeps on every interactive query. No measured cost materially blocks regional/source-accountability assessment or a subsequent authorized local integration. A real larger integrated closure still needs measurement when it exists. Adequacy concerns the bounded next regional batch scope and the established explicit-membership direction, not unrestricted growth of the old prototype ancestry-loading path already rejected by e88b575. The 112-publication controls measure the later membership model separately from the seven-generation native pilot. Geography, source applicability, quality, licensing, actual retrieval and maintainable world-model integration are higher-value next uncertainties than another validation microoptimization.

## 26. DECIDE NOW

**N18.** Preserve separate evidence for present availability, byte identity, metadata consistency, publication closure, custody assumptions and physical meaning. Root switching must follow complete existing validation. Stale derived claims remain historically valid/referenceable unless an actual integrity/contract check fails. Content-addressed names do not enforce ordinary-file immutability. Verification-policy changes require a stated new trust boundary.

## 27. PROVISIONAL DIRECTION

**P12.** Full validation remains the default for measured local retained regional batch work. Preserve explicit bounded component membership and independent historical roots. Receipt optimisation remains CLOSED, including its bounded positive exception. No additional validation investigation is justified now. Reassess only against an identified capability/real workload, not population-wide counters alone.

## 28. DEFER PENDING EVIDENCE

**D12.** Remote custody, multiple writers, power loss, cold storage latency, much larger integrated closures, repeated real revisions, licensing/provider availability, physical I/O and specific backend selection are unresolved. A future verification-boundary study is justified only by concrete obstruction or custody contradiction; it is not the selected next task. No production deployment or permanent archive guarantee is inferred.

## 29. REJECT

**R12.** Reject hashing-dominance claims based only on operation counts, checksum-as-science/licence proof, stale-as-invalid, byte sweep-as-regional-world acceptance, small root-switch cost-as-total-acceptance cost, ancestry reconstruction as normal scalable membership and hypothetical-benefit reopening of receipts. No guards were weakened or redesigned.

## 30. Remaining uncertainty and limitations

One local host, cache uncontrolled, ordinary mutable locators, finite existing predicates, limited history and source products. Synthetic component populations model established qualifiers/dependencies but not larger realistic GIS cost or database performance. Larger retained bytes are read-only preparation products, not qualified integrated new regions. Five samples reveal spread but are not statistical confidence bounds. Timed wrappers add overhead; control samples guard outcomes, not perfect profiling calibration. Single-writer local atomic publication/process interruption is supported; hostile custody and distributed durability are untested. Appearance unresolved/non-blocking; Swiss multiview parked. No foundational contradiction found.

## 31. Regression validation

The [validation receipt](atlas-integrity-cost-validation.json) records exact commands, test totals, errors and hashes. It reruns all established checks/tests from the last proof, eight new measurement tests, metering outcome/counter checks, frozen plan/raw/source hash checks, and lint/build/types. All original tracked non-navigation bytes are checked before and after, protecting S1–S6, all architecture reports, frozen contracts, production Atlas, Weather and Traverse. All42 canonical research statuses,113 protected production hashes,17 accepted store files and1,575 source-admission files are checked;310 retained evidence hashes/current remain identical. Only assessment scripts/reports and canonical navigation are allowed changes. No `meridian-private` access, real acquisition, production infrastructure or committed large payloads. The receipt is authoritative for final counts, not a guessed total.

## 32. Overall result A/B/C/D

**C - ASSESSMENT RESOLVED.** Cost and guarantee boundaries are sufficiently understood to proceed toward broader retained regional integration without another validation investigation. This resolves the selected question, not production custody, all geographic scale or universal validation economics. No new acceptance criterion was invented after measurement, and no validator was optimized to meet a screen.

## 33. Exactly one next bounded Atlas task

**Atlas retained regional expansion and source-accountability assessment — NOT BEGUN.** Recover retained regional/source inventories beyond Tryfan, identify qualified support/coverage/source/product/provenance/rights gaps and the smallest coherent real regional integration candidate. Decide what the retained public evidence can support before acquisition or implementation. This advances physical-world coverage/accountability and tests the expected broader direction against actual programme evidence. It is not S7, production storage/service transition, Weather, Traverse, Appearance or Swiss multiview. Do not begin it in this assessment.
