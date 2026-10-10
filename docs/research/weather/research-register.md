# Weather research coverage register v1

WR001, 10 October 2026. This register is independent of Atlas's 42 protected canonical statuses. Stable W identifiers track **investigations, not implemented capabilities**. Coverage is broad; evidence depth is selective. The landscape, taxonomy, access investigation and legacy inventory completed by WR001 do not complete research into the subjects below.

Statuses: **IDENTIFIED** — relevant question, not bounded/deeply reviewed; **SCOPED** — question, prerequisites and next evidence specified, not answered; **RESEARCHED** — bounded question answered with a cited evidence assessment; **EXPERIMENTALLY VALIDATED** — stated operation/profile tested with reproducible inputs/results; **PARTIALLY VALIDATED** — precise subset tested, gaps retained; **DEFERRED** — useful but not current priority, revisit condition required; **EXCLUDED** — reasoned exclusion from a stated scope, not scientific impossibility. No topic is marked RESEARCHED or VALIDATED merely for having a link. No experiments occurred here; no topic is excluded permanently.

Evidence quality: **P** primary science/standard/agency documentation, discovery-level; **R** peer-reviewed result limited to the cited experiment; **L** actual legacy code/retained receipt, engineering evidence; **U** insufficient source/product evidence. P does not mean Meridian-tested. Links below specify existing evidence, while next actions specify unanswered work. Priorities: **gate** prevents wasted/invalid experiments; **early** substantial initial depth; **later** specialised track after prerequisites; **deferred** revisit when product/evidence requires. Dependencies are prerequisites for an eventual experiment, not a requirement to finish whole disciplines before scoping another.

| ID / topic / domain | Why it matters / potential Meridian relevance | Dependencies / existing evidence / quality | Major uncertainty, access implication / priority / status / next investigation |
|---|---|---|---|
| W01 Thermodynamics/stability — atmosphere | Foundations for temperature, humidity, phase and vertical interpretation | [Landscape](scientific-landscape.md); P | Formula/level/domain assumptions; native fields needed / early / SCOPED / identify required definitions before deriving quantities |
| W02 Dynamics/synoptic structure — atmosphere | Wind/pressure and large-scale context | Landscape; P | Model versus local exposure, vector basis / early / SCOPED / scope retained wind/pressure semantics, not local flow inference |
| W03 Orography/local circulation — atmosphere | Central mountain representativeness limitation | W01/W02; landscape; P | Unresolved valley/ridge flow, observations sparse / early / SCOPED / define terrain-regime validation needs |
| W04 Boundary layer/turbulence — atmosphere | Gusts, fog and near-surface behaviour | W01/W02; landscape; P | Parameterised turbulence/exposure, specialised observations / early / SCOPED / distinguish diagnostics from resolved events |
| W05 Microphysics/cloud/precipitation — atmosphere | Phase/amount/cloud interpretation | W01; landscape; P | Process assumptions, vertical profiles, radar/gauge differences / early / SCOPED / define quantity and support prerequisites |
| W06 Land/snow/surface exchange — coupled systems | Surface versus atmospheric conditions | W01/W05; taxonomy; P | Snow state/depth/SWE and exposure; source/verification scope incomplete / later / IDENTIFIED / identify state products and limits |
| W07 Radiation — atmosphere | Flux/energy/UV and surface energy | W01; taxonomy/CF; P | Direction/interval/spectral support / later / IDENTIFIED / pin field semantics before terrain irradiance claims |
| W08 Severe phenomena — hazards | Warnings, convection and explicit reliance limits | W04/W05/W25/W30; landscape; P | Rare-event verification and specialist competence / later / IDENTIFIED / scope authority and event-specific evaluation |
| W09 Composition — coupled atmosphere | Air quality/aerosol/pollen relevance | [S15](source-landscape.md); P/U | Species/vertical/exposure semantics and provider rights / later / IDENTIFIED / separate CAMS quantities from health inference |
| W10 Source access/rights/economics — access | Determines lawful, feasible experiments and delivery | [Rights register](source-access-rights.md); P/U | Exact products, archive, quotas, redistribution and fees / gate / SCOPED / product-level documentary audit before acquisition |
| W11 Identity/grid/time/quantity semantics — representation | Prevents incompatible fields being combined | Landscape/GRIB/CF; P; legacy L | Product templates, intervals, vertical/grid support, revision / gate / SCOPED / draft finite semantic examples from selected product documentation |
| W12 Temperature/pressure/upper-air — quantities | Useful basic atmospheric context | W01/W10/W11/W30; C01–C02; P/L | Reduction, below-ground levels, local representativeness / early / SCOPED / design independent source/decoder/observation checks |
| W13 Wind/gust/vertical velocity — quantities | Outdoor relevance with high interpretation risk | W02/W04/W10/W11/W30; C03–C04; P/L | Gust interval versus instant, rotation, exposure / early / SCOPED / specify native reference and comparison support |
| W14 Moisture/dew point/wet bulb — quantities | Condensation/phase and derived-formula basis | W01/W10/W11/W30; C05; P | Saturation convention/pressure/QC / later / IDENTIFIED / scope formula and independent analytic validation |
| W15 Precipitation amounts/rates — quantities | High-value interval and verification problem | W05/W10/W11/W30; C06; P/L | Reset/deaccumulation, grid versus gauge, extremes / early / SCOPED / define temporal/support tests before hourly conversion |
| W16 Precipitation type/snow — quantities | Water equivalent, phase and state separation | W05/W06/W10/W11/W30; C07–C08; P | Density/phase, vertical profiles and sparse mountain truth / later / IDENTIFIED / separate snowfall and snowpack study |
| W17 Freezing/cloud/fog/visibility — diagnostics | Avoid misleading summit/ceiling information | W01/W04/W05/W10/W11/W30; C09–C11; P/L | Multiple crossings, datum, ceiling sentinel, local visibility / early / SCOPED / specify diagnostic definitions and unverifiable claims |
| W18 Radiation/UV products — quantities | Exposure context distinct from rendered shadow | W07/W10/W11/W30; C12; P | Native interval/plane and retrieval calibration / later / IDENTIFIED / assess exact product definitions |
| W19 Convection/storm/lightning — diagnostics | Process and nowcast uncertainty | W05/W08/W30/W37; C13–C14; P | CAPE not event, lightning sampling, displacement / later / IDENTIFIED / select event-specific methods before modelling |
| W20 Icing/turbulence — specialised | Potential high-consequence interpretation | W04/W08/W10/W30; C15; P/U | Dedicated vertical/exposure data and competence / deferred / DEFERRED / revisit only for separately scoped specialist need |
| W21 Wind chill/heat stress — indices | Formula/assumption transparency | W01/W10/W11/W30; C16; P | Applicability/exposure and health interpretation / later / IDENTIFIED / validate named formula/domain rather than generic score |
| W22 Air quality/pollen/exposure — products | Broader weather-linked information | W09/W10/W11/W30; C17; P/U | Threshold meaning, health and rights / deferred / DEFERRED / revisit with concrete product purpose |
| W23 Ground/surface conditions — impacts | Wetness/snow/ice not determined by air alone | W06/W10/W30; C18; P/U | Local surface state and observations / later / IDENTIFIED / inventory support without route-safety inference |
| W24 Mountain-weather suitability — application science | Translate scales into honest outdoor context | W03/W11/W30/W38/W39; C19; P/L | Elevation mismatch, summit/valley exposure, sampling / early / SCOPED / define region/variable-specific validation question |
| W25 Official warning/alert handling — authority | Preserve issuer, region, urgency and cancellation | W10/W11; CAP/agency terms; P | Feed completeness, licence, offline expiry / early / SCOPED / document authority and warning lifecycle, not hazard generation |
| W26 Marine/hydrometeorology — adjacent science | Coupled/coastal/flood relevance not generic forecast | W06/W08/W10/W30; C21–C22; P/U | Waves/catchment state/official expertise / deferred / DEFERRED / revisit geographical use case and independent science scope |
| W27 Fire/drought impacts — adjacent science | Fuel/state and weather distinctions | W06/W08/W10/W30; C23; P/U | Index calibration versus danger / deferred / DEFERRED / revisit with specialist authority and purpose |
| W28 Seasonal/climate context — prediction scale | Probabilistic anomalies not daily local forecasts | W10/W11/W30; C24; P | Hindcasts/calibration and use case / deferred / DEFERRED / revisit long-horizon product need |
| W29 Space weather — adjacent domain | Broad discovery; separate processes/models | C25; P/U | Terrestrial product relevance limited / deferred / DEFERRED / revisit positioning/communication disruption need |
| W30 Validation/verification/uncertainty — methods | Distinguish decoding, interpretation, skill and usefulness | [Landscape validation](scientific-landscape.md#validation-and-uncertainty); P/R | Baselines, independent observations, calibration, sample/event power / gate / SCOPED / design protocol tied to accessible W38 evidence |
| W31 Provenance/publication/revisions — scientific lifecycle | Reproducibility and stale/unknown handling | Landscape; [legacy inventory](legacy-evidence-inventory.md); P/L | Source replacement, cycle/issue distinctions and reproducible closure / gate / SCOPED / define minimal versioned experiment record after source choice |
| W32 Offline forecast snapshots — delivery | Honest forecast horizon and recovery | W10/W11/W31; [Atlas handoff](../atlas-portability-handoff.md); L/EI | Weather expiry differs from Atlas knowledge history, target storage unproved / later / SCOPED / specify lifecycle obligations after scientific products exist |
| W33 Resource/cost control — operations | Fields/members/archives can dominate cost | W10/W31; [economics](../../foundations/economics.md); P/EI | Measured experiment volume and exposure / gate / SCOPED / bound storage/compute before authorised acquisition; no infrastructure now |
| W34 Scientific query/render separation — architecture | Scientific evolution independent of UI/tiles | W11/W31; [cross-platform study](../meridian-cross-platform-architecture.md); L/EI | Product-specific queries and renderer precision / later / SCOPED / compare representations only after a finite scientific profile |
| W35 ML/hybrid prediction — methods | Operational and research alternatives now important | S02; NeuralGCM/Ciarán papers; P/R | Training rights, extremes, shift, independent skill / early / SCOPED / investigate product provenance/access before ranking |
| W36 Assimilation/ensemble/post-processing — methods | Initial-state and probability quality | Landscape; P | Member dependence, observational leakage, calibration identity / early / SCOPED / define required uncertainty representation and independent reference |
| W37 Nowcasting/radar/satellite retrieval — observations/prediction | Rapid events and transitions to NWP | S12/S13/S16; P/U | Sampling, growth/decay, latency, mountain blockage / later / IDENTIFIED / select retrieval and validation scope separately |
| W38 Observations/archives/reference suitability — validation access | Forecast access alone cannot support skill claims | S11/S12/S14 plus national archives; P/U | UK/Alpine QC, exposure, overlapping history, assimilation independence / gate / SCOPED / documentary matching feasibility before benchmarking |
| W39 Uncertainty/freshness communication — interpretation | Prevent apparent precision/safety claims | W11/W25/W30; [product principles](../../foundations/product.md); P/EI | User understanding, forecast versus observation and known coverage / early / SCOPED / define plain-language evidence obligations; no UI design |
| W40 Reanalysis/hindcast/reference dependence — retrospective science | Historical forecasts and estimated past states differ | S14/W35/W36/W38; P/R | Analysis revision, training/assimilation overlap and archive cost / early / SCOPED / identify independent evaluation path, not reanalysis-as-truth |

## Coverage and maintenance

This version has **40 topics: 23 SCOPED, 11 IDENTIFIED, 6 DEFERRED**. Counts are status bookkeeping, not measures of scientific achievement. Twenty-five capability families and twenty source families cross-reference these questions. Revise priorities with reasons, retain identifiers and record negative findings; split a topic only when a bounded question genuinely needs separate evidence. Preserve source dates and study limitations. Weather statuses never update Atlas's canonical ledger.

The [programme](research-programme.md) groups these topics into manageable evidence gates. The only recommended subsequent task is defined there and is **NOT BEGUN**. Identified/deferred rows are alternatives to revisit, not concurrent instructions or an implementation backlog.


## WR002 documentary findings and priorities

10 October 2026. This append-only refinement retains W01–W40 and the original **23 SCOPED, 11 IDENTIFIED, 6 DEFERRED** statuses. The following finite questions are **RESEARCHED at documentary feasibility scope**, not validation of their parent disciplines. Sources and limitations are in [WR002](global-regional-source-feasibility.md); current access/rights are in its companion register.

| Bounded identifier / parent | Question and evidence | Status / outstanding gate |
|---|---|---|
| WR2-Q01 / W10, W31, W35 | Are there distinct global physical/ensemble/ML product opportunities? G1/G2/G3 exact delivery and history distinctions documented | RESEARCHED (documentary); historic permissions, version and finite field profile unresolved; no skill finding |
| WR2-Q02 / W10, W38, W40 | Can a UK regional forecast have retrospective overlap with a global forecast and stations? R1/G2/O2 documentary ranges support a candidate January 2025 cohort | RESEARCHED (documentary); files, heights, station exposure/QC and historic licence still conditional |
| WR2-Q03 / W10, W38, W40 | Does the selected Alpine feed supply retrospective forecasts? R2's 24-hour retrieval window does not establish such an archive | RESEARCHED (negative documentary finding); retrospective opportunity blocked, not proof that no separate archive exists |
| WR2-Q04 / W38, W40 | Can ISD be assumed current? NOAA's 23 June 2026 notice supersedes that assumption and directs GHCNh use | RESEARCHED (documentary correction); exact successor edition, QC and contributing rights need investigation |
| WR2-Q05 / W11, W30, W36, W38 | Can shared observations establish global–regional skill or independence automatically? Height/support and assimilation/initial-boundary dependencies prevent that shortcut | RESEARCHED (requirements analysis); semantic/verification protocol SCOPED, no numerical or empirical validation |
| WR2-Q06 / W10, W38 | Are access, reuse and offline pathways identical? Thirteen exact delivery/edition rows distinguish nine intentions and remaining terms | RESEARCHED (documentary); no legal clearance, acquisition authorisation or production costing |

Prioritise W11/W30/W36/W38 semantic/reference design alongside W10 rights/archive gates. Station height/exposure, actual QC, version migration and rolling history are now more useful than another provider catalogue. ML/ensemble, mountains and wider geography remain important alternatives, not excluded capabilities. Exactly one next bounded task: **WEATHER RESEARCH 003 — NEAR-SURFACE TEMPERATURE SEMANTICS AND FORECAST–REFERENCE VERIFICATION DESIGN — NOT BEGUN**, defined in the [compatibility report](forecast-reference-compatibility.md#exactly-one-next-bounded-task). No later investigation has begun.


## WR003 bounded documentary answers and open parameters

10 October 2026. W01–W40 and their **23 SCOPED, 11 IDENTIFIED, 6 DEFERRED** statuses, and all WR2 rows, remain unchanged. [WR003 design](temperature-verification-protocol.md) researches the following finite documentary questions; it does not experimentally validate their parent topics or declare the draft fully preregistered.

| Identifier / parents | Bounded answer / evidence | Status and remaining gate |
|---|---|---|
| WR3-Q01 / W11, W12, W24 | Same-height temperature equivalence is not established: 2 m GFS, 1.5 m UKV and documented 1.25 m reference practice. Qualified unit conversion/proxy estimand distinguish constructs | RESEARCHED (documentary); actual station-height/history and forecast diagnostic metadata unresolved |
| WR3-Q02 / W11, W38 | Nominal hour need not be effective observation time; historic HH−10/CDL differences and short averaging need message-era evidence | RESEARCHED (documentary prerequisite); exact-time eligible cohort unproven |
| WR3-Q03 / W30, W38 | Version directory is not passed QC; define field-specific acceptance, duplicate/era audit, error-blind completeness and paired exclusions | RESEARCHED (design); current dictionaries and station metadata BLOCKED, no QC counts measured |
| WR3-Q04 / W30, W36, W40 | Station-balanced paired MAE contrast, separate leads and descriptive diagnostics specified; joint blocks address weather dependence conditional on cohort | RESEARCHED (design); L/B/GAMMA/minimum-block and sample sufficiency open, no interval/skill finding |
| WR3-Q05 / W10, W31, W33 | Exact historical editions, actual object closure, terms and bounded resource authority remain acquisition gates; ≤620 planned triplets is not independent sample size | RESEARCHED (gate specification); no archive completeness, approved acquisition or redistribution clearance |
| WR3-Q06 / W30, W39 | A/B/C protocol design differs from D skill/E outdoor suitability; January/00 UTC pilot is nocturnal and cannot establish regional/global superiority | RESEARCHED (claim-boundary design); parameters prevent full preregistration, broad programme remains intact |

No broad topic is promoted to RESEARCHED or VALIDATED. Parameter statuses FIXED BY EVIDENCE / PROVISIONAL / BLOCKED / NOT APPLICABLE in the protocol describe a design, not Weather register maturity. Exactly one current next task: **WEATHER RESEARCH 004 — REFERENCE MEASUREMENT METADATA AND HISTORICAL TEMPERATURE PRODUCT CLOSURE — NOT BEGUN**, [scope and stop gate](temperature-acquisition-gates.md#exactly-one-next-bounded-task).


## WR004 bounded documentary closure

10 October 2026. [WR004](reference-metadata-and-historical-product-closure.md) records the following finite answers, **OUTCOME B — PARTIAL CLOSURE**. All W01–W40 rows and **23 SCOPED, 11 IDENTIFIED, 6 DEFERRED** statuses, WR2 and WR3 rows remain unchanged. No broad topic is promoted to RESEARCHED or VALIDATED; these documentary questions do not establish observed skill.

| Identifier / parents | Bounded finding | Status / remaining gate |
|---|---|---|
| WR4-Q01 / W11, W38 | Current MIDAS guide retrieved; message/equipment clocks and minute support prevent universal nominal-hour correction | RESEARCHED (documentary); 2025 station-era applicability and exact physical matching unresolved |
| WR4-Q02 / W11, W24, W38 | Nominal 1.25 m screen practice distinguished from actual historical height/exposure; release changes do not establish sensor history | RESEARCHED (documentary); strict eligible cohort unproven |
| WR4-Q03 / W30, W38 | QC components/revisions documented; v202607 CSV packing, temperature J/state/missing dictionaries still required | RESEARCHED (conditional rule design); no actual accepted-QC records or dictionary encoding validated |
| WR4-Q04 / W10, W31 | Two GDEX and three UKV historical paths observed; corrected UKV valid-time lookup avoids false absence | RESEARCHED (public non-value metadata); no scientific content or complete 62-object inventories verified |
| WR4-Q05 / W10, W38 | Public listing, registered retrieval, source licences and redistribution remain separate; current manuals/OGL retrieval gap refined | RESEARCHED (documentary); no authentication, service entitlement or legal clearance |
| WR4-Q06 / W30, W39, W40 | Deterministic error-blind selection and bounded metadata-first handoff can return a meaningful negative result | RESEARCHED (design); no acquisition, ten-station guarantee or preregistered skill experiment |

Exactly one current next task: **WEATHER RESEARCH 005 — MIDAS OPEN REFERENCE INTERPRETATION AND ERROR-BLIND ELIGIBILITY PILOT — NOT BEGUN**, [finite definition](reference-metadata-and-historical-product-closure.md#13-programme-implication-and-exactly-one-next-bounded-task). Earlier next-task notes remain historical.


## WR005 bounded real-metadata evidence

10 October 2026. [WR005](midas-reference-interpretation-pilot.md): **OUTCOME B — PARTIAL INTERPRETATION**. All W01–W40 rows/statuses and historical WR2–WR4 rows remain unchanged. No forecast-skill or reference-record topic is experimentally validated.

| Identifier / parents | Bounded result | Status / remaining gate |
|---|---|---|
| WR5-Q01 / W10, W11, W38 | Three real supplied v202607 files pinned; actual ten-column BADC metadata schema inspected, 1,544 unique IDs | RESEARCHED (real metadata inspection); provider authenticity/download session not independently captured |
| WR5-Q02 / W11, W31, W38 | 390 year-range nominations exactly match qcv-1 source IDs in 692 release-listed 2025 filenames; county/stem/ID joins pass | RESEARCHED (real metadata join); annual objects/slots/QC contents uninspected |
| WR5-Q03 / W11, W24, W38 | Current locations/year endpoints lack historical height, instrument, exposure, capability and physical-time support; zero strict eras established | RESEARCHED (bounded negative evidence); no proof that suitable stations do not exist |
| WR5-Q04 / W30, W38 | Isolated parser/pins/receipt reproducibility tested; 22 synthetic cases; annual acceptance path intentionally unavailable | PARTIALLY VALIDATED (metadata utility only); temperature encoding/missingness/revisions/time not validated |

The next single gate is [WR006 historical measurement support/reference-target decision](midas-reference-interpretation-pilot.md#9-exactly-one-subsequent-task--not-begun), **NOT BEGUN**. It does not automatically authorise another station, an annual file or forecast verification.


## WR006 bounded historical-support decision

10 October 2026. [WR006](midas-historical-measurement-support.md): **Outcome C — EVIDENCE
BLOCKED**, separately **reference-target Decision C**. All W01–W40 statuses and historic
WR2–WR5 rows remain unchanged; no reference/skill topic is experimentally validated.

| Identifier / parents | Bounded result | Status / remaining gate |
|---|---|---|
| WR6-Q01 / W11, W38 | Frozen Caithness metadata-group order nominates source 00032; repeat selection content and pinned audit receipts agree | PARTIALLY VALIDATED (selection/audit utility only); no historically eligible era |
| WR6-Q02 / W11, W24, W38 | Selected capability listed but body redirects to sign-in; dated height/location/equipment/clock unsupported | RESEARCHED (bounded evidence/access decision); historical support BLOCKED, not station ineligibility |
| WR6-Q03 / W30, W38 | Historical public QC/J document read: MESQL layout and temperature descriptors; prior retrieval gap refined | RESEARCHED (documentary); exact v202607 header/missing/revision applicability and real-record decoding unresolved |
| WR6-Q04 / W30, W31, W40 | Strict and nominal-proxy targets blocked; independent one-field global decode is a legitimate next experiment distinct from skill | RESEARCHED (decision/dependency boundary); no acquisition, decoder or forecast skill begun |

The sole next task is [the bounded historical GFS field pilot](midas-historical-measurement-support.md#9-programme-consequence-and-exactly-one-next-task),
**NOT BEGUN**. Missing reference evidence does not automatically block source-format
engineering, or permit a skill claim based on model agreement.


## WR007 single-field numerical integrity

10 October 2026. [WR007](historical-gfs-temperature-field-pilot.md) reaches **Outcome A —
VERIFIED NUMERICAL FIELD**. W01–W40 and WR2–WR6 historical rows remain unchanged.
Experimental status below applies only to this field/profile, never forecast skill.

| Identifier / parents | Bounded result | Status / remaining gate |
|---|---|---|
| WR7-Q01 / W10, W38, W40 | Exact Jan 15 2025 00 UTC f024 NOAA inventory and HTTP 206 message extraction; 874,115 bytes pinned | EXPERIMENTALLY VALIDATED (one object's bounded acquisition); continuity/suite revision unresolved |
| WR7-Q02 / W11, W31, W38 | Actual numeric parameter/2 m/time/K, 1440×721 scan/coordinates/sphere and no-missingness profile checked | EXPERIMENTALLY VALIDATED (retained field interpretation); other grids/packing/masks unsupported |
| WR7-Q03 / W30, W38 | 1,038,240 independent ecCodes/GDAL values compared; every rounding residual explained; repeat receipts/input seals exact | EXPERIMENTALLY VALIDATED (decoding integrity only); no observational accuracy or skill |
| WR7-Q04 / W31, W39, W40 | Field/source/decoder metadata must remain distinct from downstream querying, derived products and rendering | RESEARCHED (bounded engineering implications); no production architecture or global economics validated |

Exactly one next task: [native-grid point-sampling and query-semantics pilot](historical-gfs-temperature-field-pilot.md#9-exactly-one-next-bounded-task--not-begun),
**NOT BEGUN**. The historical MIDAS reference decision remains blocked.
