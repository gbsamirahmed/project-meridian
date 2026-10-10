# Weather Research 002: forecast–reference compatibility

Reviewed **10 October 2026**. [Candidate identities and primary evidence](global-regional-source-feasibility.md) and [rights pathways](source-rights-detail.md) are prerequisites to this report. All opportunities below are **proposed future investigations**, not executed protocols, available-file confirmations or forecast-skill findings. No datasets were acquired. UNKNOWN remains a reason to withhold a claim, not fill a value.

## Matching and independence obligations

A defensible comparison needs a named estimand: the physical quantity, height/support, time meaning and population being evaluated. Model output at a nominal near-surface height is a diagnostic over model land/orography, not necessarily the value at a station's actual altitude/exposure. A common unit label does not eliminate that mismatch. These obligations refine W11/W30/W36/W38/W40 and follow [WR001's validation distinctions](scientific-landscape.md).

| Match dimension | Required evidence before a numerical comparison | Invalid shortcut |
|---|---|---|
| Product identity | Producer, delivery route, edition/run, deterministic/control/member, native and delivered grid, file/index identity | Treating all products labelled IFS, GFS or UKV as one interchangeable forecast |
| Forecast reference | Initialisation and lead; actual release/availability separately recorded; valid time computed and checked against metadata | Treating retrieval time as initialisation or using the most recent run retrospectively |
| Observation support | Observation/measurement timestamp, averaging/accumulation support, instrument height and station exposure/history | Matching hourly mean to instantaneous field solely by timestamp |
| Quantity and units | Parameter definition and level, unit conversion, sign/vector conventions, missing/QC codes | Screen temperature, skin temperature and daily maximum all labelled temperature |
| Spatial support | Station coordinates/elevation at that date; grid coordinates/orography, land/coast and valid domain; declared point-to-cell matching | Regional grid cell as truth; bounding boxes as complete usable coverage |
| Temporal windows | Shared UTC valid time or exactly matched start/end interval; daylight-saving handling and calendar | Cumulative precipitation from initialisation compared directly to preceding-hour rain |
| Vertical support | AGL versus MSL, nominal sensor height, terrain-following/pressure level and below-ground validity | Generic lapse-rate correction presented as observed summit temperature |
| QC and missingness | Edition-specific accepted flags, duplicates/replacements, rejection reason, gaps and paired-sample accounting | Missing station record counted as zero error or physical absence |
| Population and uncertainty | Stations/period chosen before seeing errors; sample dependence and elevation/exposure strata recorded | One month/one valley extrapolated to global or mountain safety |

### Independence is a dependency assessment

O1/O2/O3 reports may be transmitted through meteorological networks and assimilated. The same observation on a different website is not independent. Exact station/cycle assimilation status is **UNRESOLVED** here. That does not disqualify later-lead verification; it limits claims of an independent initial-state test. Distinguish the observation available at initialisation, later verifying observation, future analysis assimilating that observation, tuning/calibration data and an ML training sample.

G1/G3 share ECMWF analyses. R2 uses KENDA and IFS ENS lateral boundaries in the [documented ICON configuration](https://gmd.copernicus.org/articles/19/755/2026/). R1's selected historical boundary-model identity is not established. Thus model errors and improvements can be correlated. AIFS training/tuning period and any post-processing dataset must be traced before an out-of-sample claim. Provider/source separation is not enough. Operational forecasts actually issued at the time are different evidence from retrospective hindcasts with later data or revised code.

Station instruments are qualified references, not unquestionable ground truth. Analysis/reanalysis, gridded station analyses, radar and satellite retrievals have further model/retrieval dependencies. Do not verify a forecast against its own analysis without stating the weaker claim. Two forecasts agreeing demonstrates agreement, not accuracy. Later experiments should retain a per-pair dependency note and report what independence was established, assumed or unknown.

## Forecast/reference compatibility matrix

**Candidate** means a documentary route to investigating a pair; **conditional** requires named metadata/access closure; **blocked** identifies a specific missing prerequisite. None means validation completed.

| Forecast / reference | Spatial and temporal opportunity | Compatibility and dependence | Documentary judgement |
|---|---|---|---|
| G2 GFS / O2 MIDAS Open v202607 | UK station sample, January 2025 initialisations; +24/+48 h forecasts; reference coverage through spillover into February | Confirm instantaneous 2 m GRIB K against actual station air-temperature C support, height and QC; assimilation unknown. Exact historical forecast objects unverified | **Candidate, conditional**: strongest global-product pilot; no worldwide skill conclusion |
| R1 UKV ASDI / O2 MIDAS Open | Same period/stations/leads as G2; 00 UTC short runs nominally include both leads | UKV screen is 1.5 m; station height must be documented. Compare each product against a stated reference estimand, not an identical-height claim. Historical delivery/version/rights need closure | **Candidate, conditional**: regional comparative question; cannot isolate resolution as causal explanation |
| G2 GFS / O1 pinned legacy ISD | Completed historic period before supersession, station-specific geographic expansion possible | Full flags/measurement times and histories needed; QC codes are format-specific. Historical files still documented through NODD; do not silently migrate to GHCNh | **Conditional**: multi-network exposure/edition and reference rights investigation before global expansion |
| G1 IFS / O1 or O2 | TIGGE/MARS catalogue suggests historical operational possibilities | Exact cycle/lead/field/grid/month, entitlement and licence not closed; chosen subset might differ from current open IFS | **Blocked for an approved experiment**, pending exact archive/access profile; documentary alternative remains |
| G3 AIFS / O1 or O2 | 2025–2026 operational history is version-limited; experimental pre-operational history separate | MARS access, product-version boundary and training/analysis dependence unresolved; available station years are not proof of forecast overlap | **Blocked** pending archive entitlement and out-of-sample scope |
| R2 ICON / O3 SwissMetNet | Current Alpine forecasts and station historical products share geography | Forecast history not supplied by 24-hour retrieval feed; need grid UUID/static files and invalid-boundary support; parameter-specific observations/QC | **Retrospective blocked**; a separately authorised prospective capture could be investigated later |
| G1 IFS / R2 ICON / O3 | Later common-cycle prospective comparison could address complementary Alpine information | Regional lateral IFS lineage means dependent errors; exact valid times, ensemble/control interpretation and usable support required | **Conditional prospective concept only**; no retrospectively available three-way cohort established |

A UK station pilot provides a coherent starting point without claiming UK and Alps both need to be validated first. Reject an apparently convenient pair when support or historical access does not match. This is not selecting Meridian's provider.

## Opportunity A: global forecast validation

**Question:** can a pinned operational global forecast's near-surface temperature be correctly matched to qualified point observations, and what errors/limitations are apparent in a small, explicitly defined UK cohort?

**Candidate forecast:** G2 GFS 0.25-degree GRIB2 operational historical product, GDEX d084001 or another explicitly equivalent lawful historical channel. **Reference:** O2 MIDAS Open hourly weather v202607. **Candidate initialisation period:** 1–31 January 2025, 00 UTC, +24 and +48 hours. This period lies within the documented archive ranges and the nominal UKV rolling window as checked on 10 October 2026; **exact file and station completeness is unverified**. Matching observations extend to 2 February 2025, not merely January. If a rolling archive loses this period, document a newly justified overlap before any experiment rather than silently replacing inputs.

**Geography:** at most ten metadata-screened UK stations, with ordinary lowland/complex-terrain exposure explicitly described if the open metadata can support those distinctions. No station names, elevations or records are invented. Do not force a mountain subgroup when suitable reference histories do not exist.

**Quantity:** candidate instantaneous air temperature at 2 m above model ground in K. Verify the selected GRIB parameter, level and time-support keys; selected observations are air temperature in degrees C, whose measurement height/sampling must be confirmed. Unit conversion alone is insufficient. A mismatch may lead to evaluating a declared near-surface proxy with limitations, narrowing the scientific claim, changing the reference or stopping; never alter source meanings.

**Matching/QC:** preregister point-to-grid selection and an optional distinct sensitivity method, retaining actual cell coordinates and model–station elevation/land mismatch. No automatic elevation correction, observation interpolation or arbitrary tolerance. Confirm UTC measurement support, QC codes, duplicates, source flags and changes; preserve unmatched records and reasons. No QC-directory label counts as a passed flag. Minimum usable sample and exclusions must be justified before errors are seen.

**Verification:** proposed signed bias, MAE and RMSE on paired cases by lead, with matched sample counts, missingness and station-level results. Error uncertainty must consider dependence across stations/cycles; no invented confidence interval or power claim. An observed climatology/persistence baseline, if scientifically defensible and available without leakage, would contextualise a later skill claim; reference/baseline design belongs to WR003. Correct decoding and interpretation are separate prerequisites. A small sample can validate the method and report conditional errors, not establish universal skill, extremes or outdoor decision suitability.

**Prerequisites:** [rights/acquisition gates](source-rights-detail.md#gates-before-acquisition-and-distribution), fixed forecast/reference edition, lawful archive route, field/orography availability, station metadata/QC and bounded storage. **Failure modes:** archive gaps, wrong analysis/message selection, height/time mismatch, inadequate reference siting, QC ambiguity, insufficient pairs, version discontinuities, unexpectedly large whole-file retrieval. Any can produce a valuable negative feasibility result.

## Opportunity B: regional enhancement comparison

**Question:** for the same qualified station/valid-time pairs, does regional UKV offer measurably different error behaviour from GFS, and where does reference representativeness limit the comparison?

Use R1's historical ASDI `temperature_at_screen_level` and G2 with O2, the same proposed January 2025 00 UTC/+24/+48 cohort, and separately verified historical coordinates/orography. UKV's field is **1.5 m**, not GFS's 2 m. The effect of model physics, post-processing, height, initial/boundary conditions and grid support is confounded with nominal resolution. Do not call a difference proof that finer grids are intrinsically better.

Compare each against the same declared observational target and use only shared eligible pairs for a paired product contrast, while reporting each product's missingness separately. Inspect elevation/coast/exposure mismatch without retrospectively cherry-picking stations. Repeat the basic methods from Opportunity A, with paired differences and an appropriate dependency-aware uncertainty design. Hypotheses/exclusions must precede acquisition/evaluation; no blending, replacement or model-ranking league table.

The opportunity could establish a reproducible comparison method and **sample-specific** performance differences. It cannot establish national, seasonal or mountain-wide superiority, explain causal resolution effects, calibrate hazard products or justify route safety. Rolling archive loss, changed precision, historic licence ambiguity or incompatible station support can block it. R2's Alpine track remains valuable but does not have a documented retrospective forecast cohort through the selected public feed. A current forecast plus historical observations at different dates is not a valid substitute.

## Resource worksheet: estimates, not downloads

All numbers below are planning arithmetic. Only cited grid dimensions and proposed sample counts are inputs; wire sizes, compression, source charges and actual file availability are unmeasured. Binary MiB = 1,048,576 bytes. No ensemble or upper-air field is required for the candidate temperature pilot.

| Component | Transparent assumption/formula | Result and limitation |
|---|---|---|
| Logical GFS fields | 31 initialisations × 2 lead times × 1 variable × 1 level × 1 deterministic product | **62 fields**; not necessarily 62 downloadable files because products contain other parameters/index objects |
| Whole-grid decoded GFS values | 1440 × 721 × 4-byte float × 62 | **257,483,520 bytes (~245.56 MiB)** of values only; excludes masks, coordinates, metadata, compressed source files and workspace |
| Hypothetical aligned UK subset | 10 degrees in each axis at 0.25-degree spacing: 41 × 41 × 4 × 62 | **416,888 bytes** of decoded values if exact aligned extraction is available; no claim that an archive supports or charges for this extraction |
| UKV fields | Same 62 logical selected fields; delivered grid dimensions/packing UNKNOWN for selected 2025 objects | Decoded bytes = 62 × Nx × Ny × bytes/value; compressed wire volume **UNKNOWN**. Parameter/time object grouping must be checked, not inferred |
| Reference screening | ≤10 stations × 31 days × 24 hourly candidate slots | ≤7,440 January slots as a screening estimate, plus February spillover and QC/metadata. Actual times/gaps/annual download bytes UNKNOWN |
| Ensemble extension | Replace one product with M members; levels L, variables V and leads H multiply field count | Cost grows with M × L × V × H; member dependence does not create equivalent independent samples |
| Local peak storage | retained raw inputs + decoded subset + metadata/QC + verification outputs + bounded temporary copy | **UNKNOWN total** until file inventory; set an approved acquisition ceiling before transfer. Do not treat 245.56 MiB as total storage |
| Requests/transfer | selected files + indices/static resources + reference annual files + bounded retries | **UNKNOWN request count/wire bytes**; subset services may have authentication or extraction costs |

One-at-a-time decoding and retaining only lawful selected messages may limit memory/storage, but no implementation or measured speed is claimed. CPU/decoder cost and reference screening work are unmeasured. Production worldwide fields/ensembles/cycles, backups, retained versions, delivery and egress need a separate [F32 economic assessment](../../foundations/economics.md); this experiment worksheet cannot answer them.

## High-impact questions and programme refinement

1. **Archive reproducibility:** rolling UKV/Swiss feeds and changing catalogue endpoints mean reproducibility requires immutable acquired file identities, actual edition metadata and retained source terms. Do not assume a website's live date is a valid historical pin.
2. **Reference edition migration:** ISD-to-GHCNh changes identity, flags and histories; an O1 extension needs a separate edition/measurement review. It is not a reason to postpone all O2-based semantic design.
3. **Reference height/exposure:** the 1.5 m/2 m and grid-versus-point mismatch could change the estimand. This has higher information value now than additional models.
4. **Shared information:** IFS/AIFS analysis, Swiss boundary forcing, tuning and station assimilation mean independence requires an explicit provenance assessment; later-lead verification can remain useful with qualified claims.
5. **Regional claims:** complex-terrain representation improvements and sample-specific forecast skill are different claims. Evaluate variables/leads/conditions separately; no general regional enhancement is established.
6. **Ensembles and ML:** finite temperature semantics are a foundation, not a reason to abandon probability/calibration or new forecast approaches. Consider these later when lawful members, adequate history and independent evaluation scope exist.

The next programme stage is a finite semantic/verification design with an archive/rights stop gate, not automatic acquisition or model benchmarking. Broad W topics remain scoped/identified/deferred; this task completes documentary feasibility questions only. UKV/MIDAS selection can change if height, QC, rights or sample requirements fail.

## Exactly one next bounded task

**WEATHER RESEARCH 003 — NEAR-SURFACE TEMPERATURE SEMANTICS AND FORECAST–REFERENCE VERIFICATION DESIGN — NOT BEGUN.**

**Objective:** establish whether a defensible common reference estimand and preregistered comparison design can be specified for the documentary GFS/UKV/MIDAS opportunity, before authorising any acquisition or scientific experiment.

**Required evidence:** WR002 exact G2/R1/O2 documentation and gaps; historic field/time/grid/orography specifications; MIDAS measurement/QC/station-history guidance; applicable source terms; primary verification-method literature. Begin from January 2025 as a candidate overlap, not confirmed files or a selected provider. Retain W11/W30/W36/W38/W40 and source-rights gates.

**Scope:** documentation only. Define one temperature profile, height/point-cell estimand, UTC cycle/valid-time matching, unit/missing/QC rules, station eligibility, assimilation/dependence limits, baseline choice, paired comparison and dependence-aware uncertainty method. Specify exact archive/metadata checks and bounded acquisition/resource plan that a later authorised task would require. Investigate alternatives or a precise negative outcome if 1.5 m/2 m/reference support cannot sustain the intended claim. No download, parser, API client, account, empirical benchmark, final model/provider/format choice or private access.

**Dependencies:** existing primary documents and lawfully accessible metadata guidance; no physical device. Unverified service entitlements, historic licence applicability, source objects and station exposure are explicit gates, not assumed resolved by this design.

**Deliverables:** concise semantic profile and preregistered protocol; evidence/QC/independence ledger; exact acquisition prerequisites, size/request assumptions and stopping rules; expected decoding/interpretation checks and claim boundaries. No numerical validation result is required or permitted.

**Acceptance criteria:** temperature and time roles are source-specific; no unsupported height correction or equivalence; station QC/exposure requirements and missingness explicit; lawful archive route and unresolved gates distinguished; proposed metrics/baselines/sample limits defensible; one finite protocol or precise blocker, with no empirical skill claim. Preserve all accepted science, Weather publications and Atlas statuses/hashes.

**Stop conditions:** stop when the design or a reproducible scientific/access blocker is documented. If metadata cannot support the estimand, archive terms fail or sample/resources cannot be bounded, recommend changing/narrowing the later experiment rather than acquiring data. Do not begin acquisition, implementation, benchmarking or any subsequent task.


## WR003 refinement: compatibility is still conditional

10 October 2026. The [semantic assessment](temperature-semantics.md) and [draft protocol](temperature-verification-protocol.md) refine the G2/R1/O2 opportunity above without rewriting its historical proposal. Met Office's documented 1.25 m instruments differ from both forecast heights; the defensible target is a qualified station-proxy discrepancy, not identical-height validation. Historic nominal reporting hours may differ from physical measurement times, so +24/+48 hourly matching requires message-specific evidence. `qc-version-1` does not prove passed element QC. January 2025 00 UTC testing is nocturnal; station and archive completeness remain unverified.

The proposed paired metrics/weights, eligibility and dependence-aware design do not close actual metadata, rights, sample sufficiency or preregistration parameters. Opportunity A and B remain conditional; no superiority, resolution benefit, outdoor fitness or blending claim. Exact acquisition gates are now [T01–T10](temperature-acquisition-gates.md#gates-before-acquisition-or-errors).

Exactly one current next task: **WEATHER RESEARCH 004 — REFERENCE MEASUREMENT METADATA AND HISTORICAL TEMPERATURE PRODUCT CLOSURE — NOT BEGUN**, [defined here](temperature-acquisition-gates.md#exactly-one-next-bounded-task). The earlier WR003 next-task definition remains historical; no numerical experiment begins automatically.
