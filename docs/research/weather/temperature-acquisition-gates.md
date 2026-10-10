# WR003: temperature acquisition gates and research handoff

Reviewed **10 October 2026**. Companion to [semantics](temperature-semantics.md) and [draft protocol](temperature-verification-protocol.md). This is **documentation only**: no object listing through authenticated services, account/terms acceptance, provider contact, dataset download, decoding or verification experiment. Scientific-product availability and permissions remain conditional. WR002's [rights detail](source-rights-detail.md) remains the product-pathway baseline; refinements below do not erase its history.

## Executive decision

The candidate GFS/UKV/MIDAS design can be specified as a **qualified station-proxy comparison**, with clear rejection rules and an explicit finite estimand. It cannot yet be frozen for execution. The highest-value unanswered question is whether the proposed reference edition contains a defensible measurement-time/height/QC cohort that the exact historic forecast products can match. A rolling archive is also a time-sensitive dependency, not evidence of all required objects. Numerical comparison is not automatically next.

### Gates before acquisition or errors

| Gate / evidence status | Required closure and decision | Experiment versus eventual product |
|---|---|---|
| T01 GFS exact archive — PARTIALLY CONFIRMED | Pin GDEX **d084001**, DOI `10.5065/D65D8PWK`, or separately verified equivalent NOAA archive. Inventory January 2025 00 UTC +24/+48 forecast object identifiers, message indices/field levels and actual gaps. Typical NOAA naming `gfs.YYYYMMDD/00/atmos/gfs.t00z.pgrb2.0p25.f024` / `f048` is a **candidate route pattern**, not a confirmed GDEX path. Distinguish operational forecasts from f000 analyses/GDAS/FNL/reanalysis; retain model/suite changes and grid/packing/time metadata | Confirm selected route's login/subsetting, retention, fees, request limits and notices. GDEX CC BY 4.0 documentation does not mean every NOAA-hosted service has identical terms |
| T02 UKV historical delivery — PARTIALLY CONFIRMED | ASDI bucket `met-office-atmospheric-model-data`, eu-west-2, 2-year rolling documentation. Pin exact pre-2026 screen-temperature NetCDF objects, reference/valid/forecast period, +24/+48 availability, grid/coordinates/orography/land mask and historical suite/diagnostic status. 2019 filename template is guidance, not actual 2025 inventory. Record missing/replaced cycles and static-resource versions | Registry documents unsigned access without AWS account; actual entitlement/object checks not performed. Unsupported access/latency is not guaranteed service. No DataHub credentials or substitute contracted product |
| T03 MIDAS exact edition — PARTIALLY CONFIRMED | Hourly weather **v202607**, DOI `10.5285/d04207b551674c07801b7d4e6d883e50`, published 23 July 2026. Candidate station/year paths, file headers/checksums, January and February 2025 coverage; catalogue family extent is not individual completeness | Registered CEDA access documented, no account/authentication used. OGL v3 plus dataset citation documented; restricted full MIDAS rights are different |
| T04 Reference physical time/height — UNRESOLVED | Resolve actual `ob_time` versus nominal hour, effective timestamp/average support per selected message and station era; 1.25 m network guidance applicability, screen/instrument/history/elevation/exposure. Public historic HH−10 guidance cannot be blindly applied | If mandatory evidence unavailable, stop exact-time cohort or explicitly redesign qualified nominal-time question **before** errors. No generic instrument uncertainty or universal clock correction |
| T05 Temperature QC/revisions — UNRESOLVED with CONTRADICTED shortcut | Resolve edition-specific `_q`, `_j`, state/version/missing-code meanings and duplicate precedence; `qc-version-1` does not mean all data passed QC. Temperature-specific code/descriptor dictionaries were not available through the checked public links | Research requires interpretable observations, not just download permission. Unknown flag codes cannot be guessed; commissioning 99999 exclusion is documented |
| T06 Quantity/grid support — UNRESOLVED | Actual GFS instantaneous 2 m message and UKV 1.5 m diagnostic compatibility; model versus delivery grid, native scanning/CRS/earth shape, source-specific surface elevation/land mask and point/area meaning | No common-grid regridding or altitude adjustment used to hide differences. Missing model terrain metadata blocks unqualified representativeness assessment |
| T07 Paired population and statistics — PROVISIONAL | Freeze domain/station-era selection, availability thresholds, method/ties, sample counts, metrics/weights, uncertainty/replicates/interval/multiplicity and exploratory list; establish adequate information for intended inference | Metadata screening is not empirical validation. Too few effective blocks permits only a preregistered descriptive downgrade, no power invented |
| T08 Assimilation/tuning — UNRESOLVED | Retain historic producer configurations, UKV boundary lineage, available station-use/QC/post-processing evidence, known overlaps and unknowns | Later-lead network verification may remain useful; independent initial-state or tuning-free claim cannot be made without evidence |
| T09 Lawful bounded resource plan — BLOCKED for execution | Pin exact source terms applicable to historic edition/route; retention/processing and possible restricted notice excerpts; approve total wire bytes, requests/retries, local peak storage and costs before acquisition | Research terms do not clear commercial display, raw/derived/offline redistribution. Public delivery separately requires F32 and source-specific rights review |
| T10 Freeze and reproducibility — BLOCKED | Reviewed protocol/parameters and planned exclusions dated before error access, original object identities/checksums, source metadata/terms, decoder/environment/method versions, immutable receipts and lawful retention | Integrity hashes are not source authenticity or independent preregistration. Changes/negative outcomes recorded; no automatic acquisition authority |

No historical file presence, station list, QC distribution or sensor record was verified here. The [GDEX catalogue](https://gdex.ucar.edu/datasets/d084001/) has a future-dated endpoint relative to this review and an early-2026 update-stop notice; its summary is not a trustworthy complete-object calendar. [ASDI registry](https://registry.opendata.aws/met-office-uk-deterministic/) describes rolling retention, not a permanent archive. If January 2025 objects disappear, a revised period requires an independent overlap rationale and frozen protocol, not retrospective substitution for a desired result.

## Rights and costs: separate intentions

These are research assessments, **not legal approvals**. No licence was accepted on the user's behalf and no fees, quotas or service guarantees are invented. UNKNOWN is not free, unlimited or forbidden.

| Selected pathway | Documentary basis / experiment permissions | Distribution and outstanding limitations |
|---|---|---|
| GFS through GDEX d084001 | Catalogue assigns **CC BY 4.0**; attribution/source identification required. Internal retention and transformation potentially usable under those terms, subject to archive access/service conditions | Verify exact object/licence scope, metadata/notices and service policy; NOAA channel's attribution/no-endorsement rules remain relevant if substituted. Actual extraction charges/quotas/authentication unresolved. Research route not a selected production dependency |
| UKV through ASDI current archive | Registry links **CC BY-SA 4.0** for the documented dataset; unsigned technical access. Historical applicability and conflicting older CC BY-NC-ND channel remain an explicit WR002 gate | Under the documented CC licence, attribution and modification notices apply and adapted material share-alike must be considered. Whether a specific derived numerical package is an adaptation requires review; no blanket off-line/commercial clearance. Older Planetary/DataHub products cannot inherit ASDI permissions automatically |
| MIDAS Open hourly weather v202607 | Exact catalogue explicitly names **OGL v3**, registered-user access and required dataset citation; suitable documentary basis for research/processing if applicable conditions satisfied | Capture complete licence/exclusions and exact station/metadata terms before an approved retained experiment. OGL full-page retrieval failed here; permissive catalogue text is not review of every third-party/metadata condition. No restricted full MIDAS/METAR substitute |
| Study outputs | Methods and summary statistics are distinct from source files; retain derivation and notices | Assess licences of each incorporated component before publishing raw records, reproducing headers/restricted flag dictionaries or offline forecast packages. Do not assume a metric output clears every raw-data obligation |

References: [WR002 product-pathway rights](source-rights-detail.md), [CC BY-SA 4.0 deed](https://creativecommons.org/licenses/by-sa/4.0/deed.en), [MIDAS edition licence/citation](https://catalogue.ceda.ac.uk/uuid/d04207b551674c07801b7d4e6d883e50/), [OGL v3](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). The deed is a summary; exact legal code and historic grant should be retained before distribution. The current Met Office third-party landing page did not itself resolve the old/current licence discrepancy. No provider contact or legal clearance.

A zero-price source can incur transfer, decoding, archive storage, temporary copies, backups and distribution costs. Local-first research remains preferred. No operational provider, billable infrastructure or revenue model is chosen. Free-at-no-cost provision and transparent genuine-cost recovery remain as established in [F32 economics](../../foundations/economics.md); alerts are not enforceable spending caps.

## Resource envelope: documentary arithmetic only

| Component | Assumptions / calculation | Limit |
|---|---|---|
| Forecast fields | 31 initialisations × 2 leads × 1 field × 1 level = **62 logical fields per model**, 124 total | Not actual file/request count; indices, full multi-variable GRIB files and static resources may add volume |
| GFS full delivered grid values | 1440 × 721 × 4 bytes × 62 = **257,483,520 bytes (~245.56 MiB)** | Float32 planning values only, not original precision, wire size, decoder memory or total storage; preserve source fidelity |
| UKV decoded values | 62 × historical `Nx` × `Ny` × bytes/value | Historical dimensions/packing UNKNOWN; current native 1.5 km dimensions must not substitute for delivered 2 km archive |
| Maximum planned paired triplets | ≤10 stations ×31 initialisations ×2 leads = **≤620 triplets**, yielding ≤1,240 forecast–reference discrepancies | Actual eligibility/completeness unknown; only two target leads, not 7,440 independent samples |
| Reference screening | WR002's ≤7,440 January hourly slots, plus February spillover and annual files | Screening slots are not target comparisons; v202607 annual file grouping/bytes, station metadata and QC are unmeasured |
| Static closure and scratch | coordinates, orography/land mask, station history, dictionaries, indices, raw retained inputs + decoded working subset + outputs + bounded temporary copies | Peak storage, request count, CPU time and source charges UNKNOWN. User-approved ceiling required before transfer, with stop-on-exceed rule and bounded retry accounting |
| Time mismatch alternative | HH−10 interpolation would require additional bracketing leads/resources and a new question | Not included in 62-field estimate or current protocol; no implicit expansion |

No scientific download was performed to measure sizes. The 41×41 hypothetical aligned subset in WR002 is not adopted as an actual delivery or native UK domain. One-field decoding and finite station matching could bound work, but no implementation/memory estimate is asserted. Worldwide operation remains a separate economics/rights/coverage problem.

## Checks to require in a later authorised experiment

Before errors: independent decoding/tool agreement under source-derived packing tolerances; native coordinates/scanning and row/index anchors; mask/sentinel/unit/height/time checks; forecast reference + step = valid time; reject statistical extrema/analysis/wrong level; observation header and flag-dictionary interpretation; station-era mapping and no unexplained duplicates; complete planned-versus-eligible denominator and rights/input receipt. No decoder is written here. Then execute only the frozen matched comparison; retain negative results, versioned commands/environment, raw-to-value-to-pair provenance and exact exclusions. A later numerical conformance test and a skill experiment are distinct evidence.

Checks executed for **WR003 documentation** are recorded in the development log: starting gate, complete diff/Markdown scope, links/anchors/source references, stable register/status checks, protocol parameter/metric/time/resource consistency, preserved tracked and retained hashes. Scientific/runtime regression suites, conformance replay, lint, types and builds are deliberately omitted because no executable code, data, contracts or dependencies changed. No data-materialising pipeline. External documents were reviewed with dated links; failed retrievals are recorded, not treated as read. No private repository access occurred.

## Research continuity and direction changes

The design refines WR002's exact-hour proposal: stored hour is not guaranteed physical time, and latest version is not passed QC. It does not invalidate WR002's documentary source opportunity or establish a usable sample. A qualified proxy estimand replaces the unsupported idea of identical-height validation; no accepted scientific contract is changed. Global validation can still proceed as a distinct GFS/reference track if regional archive/terms fail, but reference-time/QC eligibility is common to both and cannot be bypassed.

Keep broad Weather research intact. Ensembles and calibration need adequate members/history and independent methods; ML needs training/version provenance; mountains need local representativeness; nowcasting, other variables, preparation, offline snapshots and Atlas/Guide integration retain separate evidence gates. If reference metadata fail, reconsider message cohort/reference rather than download data or choose another model blindly. If inference lacks sufficient temporal information, choose a documentary or descriptive method pilot before a skill claim. A better-supported region/product remains possible through a recorded programme revision.

## Exactly one next bounded task

**WEATHER RESEARCH 004 — REFERENCE MEASUREMENT METADATA AND HISTORICAL TEMPERATURE PRODUCT CLOSURE — NOT BEGUN.**

**Objective:** determine whether the proposed UK temperature cohort can close its physical measurement-time, sensor-height/history and field-QC prerequisites, together with exact historic forecast edition/access/terms evidence, sufficiently to freeze a bounded protocol. This has higher information value than computing errors while the reference construct is unknown.

**Required evidence:** WR003 T01–T10 and parameter table; exact MIDAS Open v202607 catalogue/release documentation and current message/QC dictionaries; station metadata documentation; historic GFS and UKV product/index/catalogue documentation and applicable terms; prior WR002 rights conflicts. No physical device is needed.

**Scope:** documentation and publicly accessible non-value metadata only; no forecast/observation value acquisition, decoding, model comparison, API client, account creation, agreement acceptance or provider contact. Resolve nominal versus physical time/short averaging for eligible message eras, defensible height/exposure assumptions and duplicate/QC rules. Establish an error-blind station-selection method and what station-era evidence is actually available; verify exact historical object identifiers/availability only where public catalogue/index evidence permits, distinguishing listing from a dataset download. Record exact historical licence/access applicability and resource fields still needed. Do not guess missing dictionaries or inherit DataHub/full MIDAS rights.

**Dependencies:** authoritative documentation lawfully accessible without authentication. If essential metadata are available only behind a login/approval or require scientific-file acquisition, document the exact access/authorisation prerequisite and stop that branch; this task definition does not grant it. No private repository or commercial service.

**Acceptance criteria:** an explicit usable reference-message/height/QC rule and historic product closure with source citations and retained unknowns, or a precise negative result requiring a different cohort/reference/access step. Each open protocol parameter has a justified fixed choice or a named blocker; sample size/uncertainty requirements remain honest. Both global and regional tracks retain their distinct claims. No errors viewed and no topic marked experimentally validated.

**Stop conditions:** conclude once one candidate metadata closure or a reproducible blocker is established. Do not widen into another provider survey, create accounts, contact providers, acquire scientific values or implement a decoder. Failure of physical-time/QC/height evidence redirects the reference/cohort; failure of UKV archive/rights can defer regional comparison while retaining a qualified global track. Short history or inadequate effective blocks can limit the next proposal to decoding/interpretation, rather than promised skill. Any acquisition/experiment requires separate explicit authority after this result. The subsequent task has **not begun**.


## WR004 refinement — 10 October 2026

The T01–T10 rows above are the historical WR003 gate state. [WR004](reference-metadata-and-historical-product-closure.md#10-gate-reconciliation-and-globalregional-feasibility) now confirms selected GDEX/UKV identifiers through non-value listings, reads the current MIDAS guide/release note and full OGL, and separates public metadata listing from authenticated metadata retrieval. It does not close actual scientific field metadata, the full January inventory, station-era clock/height or exact v202607 QC encoding. No source, period, reference estimand or parameter was silently substituted. Both GFS-only and paired comparisons remain conditional; common reference failure is independent of regional-source failure.

Outcome **B — PARTIAL CLOSURE** supports a smaller interpretation pilot, with access/rights/byte preflight, not an executable forecast-skill study. The sole current next task supersedes the historical next-task note: **WEATHER RESEARCH 005 — MIDAS OPEN REFERENCE INTERPRETATION AND ERROR-BLIND ELIGIBILITY PILOT — NOT BEGUN**, [scope, acceptance, resource limits and stops](reference-metadata-and-historical-product-closure.md#13-programme-implication-and-exactly-one-next-bounded-task).


## WR005 refinement — 10 October 2026

[WR005](midas-reference-interpretation-pilot.md) advances T03 to real edition metadata/change-log inspection: 1,544 IDs, 390 year-range nominations and matching qcv-1 IDs. T04 historical sensor/clock/location and T05 exact temperature dictionaries remain unresolved; zero strict eras are established and the annual-file gate stays BLOCKED. T07/T10 cohort/domain/freeze remain blocked. T01/T02/T06/T08 forecast/independence evidence is unchanged; no forecast body was acquired. T09 local metadata-use notices were inspected, but no commercial/offline legal clearance follows.

**OUTCOME B — PARTIAL INTERPRETATION**, zero observation files/values examined. Do not obtain an arbitrary annual file to bypass missing historical support, assign network 1.25 m as observed height, treat year endpoints as continuity, or infer passed QC from qcv-1. The sole next task is [WR006 historical measurement support/reference-target decision](midas-reference-interpretation-pilot.md#9-exactly-one-subsequent-task--not-begun), **NOT BEGUN**. Historical gate rows and next-task notes above remain unchanged records.


## WR006 formal closure of the reference-target decision — 10 October 2026

[WR006](midas-historical-measurement-support.md) fixes source 00032 as one audit nominee
and records **Outcome C / reference-target Decision C**. T04 history/height/physical
clock remains BLOCKED. T05 improves to inspected historical MESQL/J documentation,
but actual v202607 header, missing encodings, dictionary applicability and revision
handling remain unverified; it is not closed. T03 pinned metadata, T07 cohort and
T10 preregistration retain their prior distinctions. No historical field bodies,
cohort, reference pair or production rights are silently established.

The [smallest outstanding manual checklist](midas-historical-measurement-support.md#smallest-outstanding-manual-evidence-checklist)
is retained without initiating an account, enquiry or another MIDAS task. Strict
support stays BLOCKED; a nominal-hour proxy stays PROPOSED. Independent forecast
format/decoding evidence can proceed under its own acquisition/rights/byte gates.
Exactly one next task: [bounded historical GFS temperature-field pilot](midas-historical-measurement-support.md#9-programme-consequence-and-exactly-one-next-task),
**NOT BEGUN**. No skill evaluation or full January forecast acquisition is approved here.
