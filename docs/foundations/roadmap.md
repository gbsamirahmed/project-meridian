# Meridian private-beta and pre-release roadmap

Reviewed 9 October 2026. Gates are evidence-based, not calendar commitments. See [engineering](engineering.md), [product](product.md), [platform](platform.md) and [decisions](decisions.md) for detailed requirements. The extended private beta can include substantial redesign.

## Maturity stages

These eight stages describe **maturity**, not dates or a required sequence of large releases. Internal development and private beta may each be long. Work can return to an earlier stage when evidence exposes a gap. A stage change needs a short dated gate record linking scope, tests, unresolved risks and owner acceptance; it does not require a release committee.

**READY FOR BOUNDED PROTOTYPE INTEGRATION** establishes that accepted Atlas evidence can support a narrow internal experiment. One terrain/evidence prototype does **not** establish integrated alpha or external-tester readiness. Current scientific results remain accepted; product, offline, device, upgrade and operational readiness must be demonstrated separately.

| Stage | Entry conditions | Exit evidence | Acceptable changes / what stays stable |
|---|---|---|---|
| FOUNDATIONAL RESEARCH AND ARCHITECTURAL FEASIBILITY | Explicit question, existing evidence, bounded method and exclusions | Reproducible findings, rejected options and bounded unresolved feasibility questions recorded | Alternatives and prototypes can be discarded; preserve accepted scientific identities, qualifications, provenance and negative results |
| CORE PLATFORM ENGINEERING | Enough evidence for a scoped responsibility and interfaces; relevant feasibility prerequisites identified | Maintainable modules, reproducible setup, contracts, conformance, validation and recovery tests for the declared scope | Significant internal architecture changes allowed; preserve scientific authority/history and explicit format compatibility. No requirement for every future subsystem |
| INTERNAL TECHNICAL PROTOTYPES | Narrow capability hypothesis, named platform/fixtures, resources and rights appropriate to the test | Measured technical capability and limitations, including actual hardware gaps; reproducible driver and stopping decision | Disposable UI/test drivers and implementation changes allowed; do not confuse emulator/desktop proof with field behaviour or a complete product |
| INTEGRATED INTERNAL ALPHA DEVELOPMENT | Relevant technical feasibility and platform boundaries sufficient; interaction requirements and coherent vertical scope agreed | Complete core user tasks tested internally across declared devices/connectivity; known coverage, diagnostics, interruption/upgrade/export/restore behaviour; tester-facing rights/privacy and support gates prepared | Substantial UI/architecture redesign expected; record interfaces/versions and migration or explicit consented reset. Scientific history, user data and recovery cannot be silently discarded |
| CONTROLLED PRIVATE BETA | Integrated alpha evidence supports specified external tasks; informed invited group, supported devices/regions, distribution rights, privacy flows, upgrade recovery and support/contact ready | Task-based voluntary feedback, repeated releases and field/device/offline/accessibility results; defects triaged, support and operating limits understood | Communicated breaking changes remain allowed. Stable qualification/identity meanings, explicit offline completeness, permission choices, supported upgrade path and user-data export/recovery required |
| EXTENDED PRIVATE BETA | Controlled trials show core tasks recover and support is workable; expansion scope and residual risks accepted | Dependable use over time and upgrades, real-device battery/thermal/storage tests, high-impact faults resolved, rights/security/support/cost plan credible | Long development and major redesign remain legitimate; version contracts/readers, migration fixtures, notices and consented resets. Preserve scientific pins and personal data through supported updates |
| RELEASE CANDIDATE | Declared functionality/regions/devices and compatibility fixed for this release; beta evidence and release gates available | Relevant regression, accessibility/security, restore/migration and incident exercises pass; notices/help and operational owners ready; financial gate passed before unrestricted access | Justified fixes rather than uncontrolled scope changes; rehearse recovery/hotfix, record residual risks. No arbitrary calendar deadline overrides unmet gates |
| PUBLIC RELEASE AND ONGOING MAINTENANCE | Declared readiness plus owner-approved [public-exposure gate](economics.md); supported distribution and update route | Continued supported operation, security updates, cost/service review, periodic restore evidence and maintained documentation; each expansion separately gated | Document compatibility/deprecation and migrations; preserve supported user data and historical identity. Withdraw unavailable capabilities honestly; no silent destructive updates |

Evidence can be a small release/gate note with links to fixtures, test receipts, named devices, rights/privacy reviews and recovery commands. Record unsupported cases and unresolved gates explicitly. A local alpha with no delivery costs does not need a cloud operations programme; a remotely delivered beta needs bounded access, approved costs and useful diagnostics. An unrestricted endpoint must pass F32 regardless of its maturity label.

Android/iOS stores may constrain downgrade or review timing: retaining a previous geographical package is not a guarantee of instant binary rollback. Use forward-compatible readers and a hotfix route; verify actual distribution mechanics before beta. No testers, accounts, services or distribution resources are created by this review.

Before inviting testers, stabilise the meaning of qualifications, identities, offline completeness and permission prompts—not every layout or feature. Feedback should be task-based and voluntary: local diagnostic export, issue reports and consented interviews before broad telemetry. Do not request live location history to diagnose an unrelated UI defect.

## Staged development through those gates

The next task is the bounded mobile terrain/offline feasibility study in the [summary](summary.md). It resolves the most expensive unresolved platform risk first. It does not build the application. Afterwards, separately authorised private-repository audit reconciles actual contents; then interaction research, clean UI foundation and portable interfaces; then the first terrain/evidence view; then Weather and verified offline/user workflows as justified. This supersedes the old immediate-private-audit ordering, not its useful checklist.

Every later implementation stage must enter with a scoped contract and known retained input, produce an executable user journey and regression evidence, and stop before the next scope. Do not use the maturity table as permission to start multiple stages. Keep code migration incremental: inventory, narrow package/adapter, one view, conformance, then expansion. Do not copy the experimental hierarchy or rewrite scientific methods to fit a UI framework.

## Licensing and ownership gates

The public README permits portfolio review and explicitly grants no open-source licence. Visibility is not permission for third-party reuse. Select distribution terms and document ownership/contributor rights before publishing reusable packages; do not infer that Meridian's owner is forbidden to reuse their own code, or that all contributions belong to one person. Record collaborator permissions in a lightweight written contribution agreement appropriate to the project. A DCO or CLA is a choice to assess, not mandatory bureaucracy. Keep generated code provenance and review copied material; AI output is not a licence clearance.

Open renderer code, native SDKs, map databases, rendered tiles, fonts, imagery, weather APIs and offline packages each have separate rights. Copyleft code may impose source/notice obligations; permissive licences still impose conditions. ODbL database obligations differ from the licence of an application or a produced map. Derived, cached and offline data must be assessed explicitly. Obtain legal review for ambiguous combinations before distribution; do not assume research retention grants public redistribution or commercial service use.

### Proposed rights register

Maintain a versioned register per exact source/product/edition and dependency version, linked to immutable source/preparation identities. Required fields: **source; licence/terms URL and archived reference; attribution; permitted processing; storage; transformation; public display; redistribution; commercial use; offline availability; restrictions; review date; owner; evidence status and review trigger**. Archive appropriate terms text or hashes where permitted. Do not bulk-copy restricted documents into the code repository.

The following is a review inventory, not blanket clearance. Checked 9 October 2026. Each future release needs a resolved register for its exact included products.

| Source/category | Confirmed basis | Processing/storage/transformation | Display/redistribution/commercial/offline | Restrictions and next review |
|---|---|---|---|---|
| Meridian code | README: portfolio review only; no open-source grant | Owner/contributor permissions must be established | Public package permission not yet selected | Before distribution or accepting external contributions |
| MapLibre GL JS / Native | BSD-3-Clause / BSD-2-Clause code licences | Allowed subject to notices and exact dependencies | Code permissions do not cover hosted map assets | Exact version/notice audit before beta |
| Organic Maps / OsmAnd material | Separate code, asset, binary and data conditions; OsmAnd repository GPL with exceptions | No copying is proposed | Linking/reuse obligations need exact component review | Only if reuse is proposed; do not infer licence from screenshots |
| OpenStreetMap database | ODbL and attribution requirements | Derived database/produced work distinctions need review | Provider delivery and offline terms are separate | Standard OSM raster tile service prohibits bulk offline downloading |
| OpenFreeMap / AWS terrain | Current frontend uses hosted resources; terrain has mixed source credits | Current technical use does not establish every package right | Do not infer unlimited offline redistribution or service guarantee | Review exact style, fonts, sprites, tile/data terms before downloads |
| swisstopo retained products | OGD terms, source-specific attribution; not simply a CC licence | Retained preparation documents establish identities/qualifications | Check exact redistribution/offline products against provider terms | Before exporting a device package; retain source credits |
| Other retained Atlas sources: Copernicus, ESA WorldCover, Exe/EA/PHI references | Existing source-accountability records remain authoritative | Keep original preparation and licence references | New display/redistribution/derived-product use needs per-source decision | Do not infer current legal restriction, ecological condition or blanket commercial clearance |
| NOAA GFS through NODD | Public-use terms request attribution; prohibit implied NOAA endorsement or mislabelling modifications | Preserve model/run/preparation identity | Delivery cost and other providers' terms remain independent | Check chosen variables/product and modifications before display |
| Open-Meteo | Data licence and API service terms are distinct | Free API service currently limited to non-commercial use | Paid/commercial endpoint terms are a separate obligation | Review before commercial use; no assumption CC data grants unrestricted free API access |
| Met Office / SAIS / Walkhighlands | Link/reference initially; precise product/service rights not cleared here | No scraping, advice replication or bulk downloads proposed | Display/redistribution/offline permission unresolved | Obtain exact terms before integration; retain independent specialist identity |
| Imagery, fonts, app-store assets and research publications | Product-specific rights | Transform/cache permission cannot be assumed | Commercial/offline redistribution often separate | Per artefact review before packaging/public Research publication |
| User/collaborator contributions | Explicit consent/licence and purpose required | Minimise retention, respect withdrawal/deletion duties | No automatic right to publish routes/photos or personal metadata | Before any upload/contribution feature |

Primary terms: [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js/blob/main/LICENSE.txt), [MapLibre Native](https://github.com/maplibre/maplibre-native/blob/main/LICENSE.md), [OSM copyright](https://www.openstreetmap.org/copyright), [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/), [terrain credits](https://github.com/tilezen/joerd/blob/master/docs/attribution.md), [swisstopo terms](https://www.swisstopo.admin.ch/en/terms-and-conditions), [NOAA GFS registry terms](https://registry.opendata.aws/noaa-gfs-bdp-pds/), [Open-Meteo terms](https://open-meteo.com/en/terms), [Met Office DataHub FAQ](https://datahub.metoffice.gov.uk/support/faqs). These are primary documentary observations, not legal advice or a release clearance.

## Naming and identifiers

Keep Meridian, Atlas, Weather and Traverse as working/repository names for now. Do not rename, buy domains or register accounts. Basic research found **HPE Meridian** in indoor mapping, **Mapbox Atlas** in geospatial delivery, and a **Traverse: Maps and Navigation** outdoor app listing. These are credible naming/discoverability conflicts; they do not prove trademark infringement or clearance. Weather is descriptive and difficult to distinguish. [HPE Meridian](https://docs.meridianapps.com/hc/en-us/articles/360040165673-Meridian-Platform-Overview), [Mapbox Atlas](https://www.mapbox.com/atlas), [Traverse listing](https://play.google.com/store/apps/details?id=io.traverse.app).

Distinguish working name, repository name, package namespace, public product name and legal entity. Repository renames are usually reversible with redirects, but Actions references, package consumers and publication URLs have exceptions. App bundle identifiers, signing relationships, store records and deployed package identities can be expensive to migrate. Choose provisional internal namespaces without claiming availability; perform UK/target-territory trademark, similar-name, domain, store and package checks before public distribution/committed identifiers. No live domain availability or registry clearance is established here. [GitHub rename behaviour](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository), [UK trademark search](https://www.gov.uk/search-for-trademark), [EUIPO search](https://www.euipo.europa.eu/search-ip).

## Privacy, security and governance

Make a data-flow inventory before beta: local GPS/fix age; coordinates sent to tiles/search/weather; search/route history; saved positions; uploaded photos and EXIF; accounts; logs; crash reports; analytics; distribution-provider metadata. Record purpose, collection/transmission, recipient/controller/processor role, retention, lawful basis assessment, user control, deletion/export and security. Even a tile viewport can disclose geographical interest, and IP addresses reach third parties. A proxy changes who processes information; it does not remove privacy risk.

Foreground location, downloading, cloud synchronisation and telemetry need separate choices. OS permission is not blanket informed consent for all uses. Denied or approximate location must leave exploration usable. No persistent location or third-party analytics by default. Provide local export and deletion without an account where feasible; before uploads, minimise EXIF and clearly disclose recipients. Avoid sending confidential search terms to public geocoders. The public Nominatim endpoint has restrictive usage and privacy rules, including no client-side autocomplete; any future search provider must be selected against actual behaviour. [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/).

UK GDPR/PECR and potentially EU GDPR need applicability/lawful-basis review, not an assertion that every feature requires the same legal mechanism. Current ICO guidance covers storage/access technologies beyond cookies and includes conditional exceptions following legal changes. Meridian's **explicit opt-in product policy remains stricter than a possible legal exception**. Screen DPIA need for high-risk processing, precise tracks, uploads and vulnerable users; do not assume either automatic exemption or universal mandatory DPIA. Assess international transfers and processor terms before third-party collection. [ICO PECR guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/what-are-the-exceptions/), [ICO DPIAs](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/accountability-and-governance/data-protection-impact-assessments-dpias/), [EU GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/).

Before controlled private beta: owner/contact for security reports; dependency/update policy; least-privilege repository/agent access; protected release secrets; trusted package origin; retention limits; backups and restore exercise. Before release: incident triage, containment, affected-version assessment, communications and jurisdiction-specific reporting review; update support period and vulnerability handling. Do not promise an SLA without operational capacity.

Screen emerging product obligations rather than discovering them at store submission. EU Cyber Resilience Act reporting provisions started on 11 September 2026, with main obligations scheduled for 11 December 2027. Scope and open-source/commercial distinctions require legal assessment for Meridian's actual distribution. The European Accessibility Act has specified product/service scope; it does not automatically cover every map application. Accessibility remains an engineering requirement regardless. [CRA summary](https://digital-strategy.ec.europa.eu/en/policies/cra-summary), [CRA reporting](https://digital-strategy.ec.europa.eu/en/policies/cra-reporting), [EAA scope](https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/disability/european-accessibility-act-eaa_en).

## Concrete first-prototype acceptance checklist

- [ ] Selected Riffelhorn support and available capabilities are visible; unavailable areas are honest.
- [ ] A new UI provides map exploration, 2D fallback and qualified inspection without inherited layout assumptions.
- [ ] Atlas results retain identities, provenance, uncertainty, separate times and the publication pin.
- [ ] Visual terrain is labelled with its product, datum and exaggeration; no failed Swiss/AWS fusion is adopted.
- [ ] Native classes are not transformed into current physical, ecological or legal conclusions.
- [ ] Supported desktop/device query and rendering budgets are measured, not inferred.
- [ ] Offline demonstration has an explicit package/capability boundary and no concealed remote dependency.
- [ ] Incomplete/corrupt data fails explicitly; restart preserves the selected compatible state.
- [ ] Privacy-sensitive requests are known and purpose-specific; no implicit tracking or telemetry.
- [ ] Keyboard/screen-reader evidence alternatives and touch/accessibility controls are tested.
- [ ] Weather remains a separate subsequent milestone with issue/valid-time semantics.
- [ ] No route-safety, global coverage or production-readiness claim is made.

These are future internal-prototype acceptance criteria, not results claimed in this review and not sufficient by themselves to invite external testers. Integrated alpha and controlled-beta entry require the broader evidence above. The [financial gate](economics.md) applies before any unrestricted public access; budget, provider, controls and approval are not established by this checklist.


## Current architecture-study handoff — 10 October 2026

The [Atlas portability consolidation](../research/atlas-portability-handoff.md) supplies
sufficient bounded evidence for **MERIDIAN WEB/MOBILE ARCHITECTURE AND CODE-SHARING
FEASIBILITY STUDY — NOT BEGUN**, the current single next task. This refines the historical
staged-development ordering above; it neither erases earlier decisions nor relaxes gates.

Proceed by dependencies: whole-system architecture comparison; physical-device terrain/
offline validation; provisional platform/sharing decisions; separately authorised repository
reconciliation; new minimal adaptable foundation; Atlas/verified offline integration.
Substantial Weather foundations are intended as an early parallel scientific programme,
with separately validated incremental application integration. Guide/route planning follows
its own evidence/safety gates. Long internal alpha/beta remains legitimate; one desktop
Atlas result is not field, tester or release readiness. The original physical-device
scope, rights/privacy requirements and F32 exposure gate remain unchanged. No stage begins
through this note, and no private access, implementation or Weather R&D occurs here.


## Architecture comparison complete; prerequisite gate next — 10 October 2026

The [Meridian web/mobile feasibility study](../research/meridian-cross-platform-architecture.md)
has compared presentation, shared logic, native/WASM science, rendering and offline
responsibilities. It selects no final framework, renderer, provider or package format.
No implementation or maturity-stage entry is implied; scientific semantics remain
stable while target implementations require conformance and real-device evidence.

Exactly one next task is **MERIDIAN MOBILE FEASIBILITY PREREQUISITE RESOLUTION — PHYSICAL
DEVICES AND BUILD ACCESS — NOT BEGUN**. Resolve G0 access, renderer/source rights and
bounded trial resources. G1 terrain/2D field measurements and G2 target reader/offline
recovery can share later trials rather than become an indefinite Atlas optimisation
programme. The original mobile-study safeguards, integrated-alpha/beta gates and F32
financial approval before exposure remain unchanged. Interaction research precedes
substantial UI; separately authorised private audit follows sufficient platform evidence.
Weather foundations can later proceed as an early parallel scientific programme; Guide
retains its own routing/navigation evidence gates. No later stage has begun here.


## Non-device phase complete; revised priorities — 10 October 2026

The [prerequisite closure](../research/meridian-non-device-prerequisites.md) resolves useful manuals/build/resource questions and assigns remaining evidence to target builds, physical hardware or concrete distribution decisions. No further generic Atlas optimisation or platform catalogue is required before Weather scope research.

The current user-authorised priority order is: **Phase 1** useful non-device closure; **Phase 2** substantial Weather scientific research/foundational engineering; **Phase 3** physical-device terrain/scientific-runtime/offline/lifecycle feasibility; **Phase 4** evidence-based choices, separately authorised repository reconciliation and new modular application foundation/integration. This is dependency-informed, not calendar-led; no stage begins automatically. G0–G2, original trial limits, new UI, integrated-alpha/beta and F32 financial gates remain intact. F20 concerns user-facing Weather integration, not the timing of independent scientific research.

Exactly one next task: **MERIDIAN WEATHER FOUNDATIONAL RESEARCH PROGRAMME — SCOPE, SCIENTIFIC REQUIREMENTS AND EVIDENCE INVENTORY — NOT BEGUN**. Scope and acceptance are in the report; no Weather implementation, device experiment, private audit or infrastructure is authorised by this note.


## Weather independent discovery complete — 10 October 2026

[WR001 entry](../research/weather/README.md) records broad scientific discovery, selective-depth priorities, source/access/rights/economics findings and an independent legacy inventory. This is research progress, not Weather scientific readiness or entry into internal alpha/beta. The programme places lawful source/reference feasibility, semantic design and validation methods ahead of numerical/preparation engineering; they can be investigated in parallel where dependencies permit. It does not require every identified discipline to be completed first. Weather research remains distinct from later application integration and from physical-device/platform evidence.

Exactly one next task: **WEATHER RESEARCH 002 — FORECAST AND OBSERVATION SOURCE FEASIBILITY FOR A BOUNDED UK/ALPINE VALIDATION STUDY — NOT BEGUN**. Rights, retrospective coverage and observation suitability can change candidate region/quantity/source. Original device-study, new-UI, maturity, privacy and F32 financial gates remain unchanged. No later stage begins automatically.


## Weather source/reference feasibility — 10 October 2026

[WR002](../research/weather/global-regional-source-feasibility.md) establishes documentary global/regional opportunities and product-specific access/rights gaps. It does not demonstrate forecast skill, Weather readiness or advance alpha/beta maturity. UK GFS/UKV/MIDAS retrospective design is conditional; selected Alpine forecast history is blocked. Source-specific height/support, station QC, assimilation and archive identity govern the next evidence gate. Original device, new-UI, privacy, rights and F32 controls remain unchanged.

Exactly one next bounded task: **WEATHER RESEARCH 003 — NEAR-SURFACE TEMPERATURE SEMANTICS AND FORECAST–REFERENCE VERIFICATION DESIGN — NOT BEGUN**, [defined here](../research/weather/forecast-reference-compatibility.md#exactly-one-next-bounded-task). No data acquisition, experiment, later programme stage or application implementation begins automatically.


## Weather temperature protocol design — 10 October 2026

[WR003](../research/weather/temperature-verification-protocol.md) establishes a conditional documentary station-proxy verification design, not forecast skill, a fully preregistered experiment or Weather/application maturity. Measurement time/height, element QC, actual historical products/terms and sample/uncertainty parameters prevent automatic acquisition. No alpha/beta, provider/platform selection or scientific-readiness gate is passed. Original privacy, preservation, physical-device, new-UI and F32 requirements remain unchanged.

Exactly one next bounded task: **WEATHER RESEARCH 004 — REFERENCE MEASUREMENT METADATA AND HISTORICAL TEMPERATURE PRODUCT CLOSURE — NOT BEGUN**, [scope](../research/weather/temperature-acquisition-gates.md#exactly-one-next-bounded-task). Weather's broader research programme and distinct global/regional tracks remain; no later task or implementation starts through this note.


## Weather reference/product closure — 10 October 2026

[WR004](../research/weather/reference-metadata-and-historical-product-closure.md) reaches **OUTCOME B — PARTIAL CLOSURE**, with selected historical object identifiers and current observation-manual semantics documented. Scientific input contents, reference station-era/QC interpretation and full preregistration remain open. This is research progress, not empirical forecast skill, Weather readiness or application-stage entry. No provider/framework, acquisition, deployment or distribution choice follows; preservation, privacy and F32 exposure safeguards remain unchanged.

Exactly one next bounded task: **WEATHER RESEARCH 005 — MIDAS OPEN REFERENCE INTERPRETATION AND ERROR-BLIND ELIGIBILITY PILOT — NOT BEGUN**, [definition](../research/weather/reference-metadata-and-historical-product-closure.md#13-programme-implication-and-exactly-one-next-bounded-task). It is a conditional reference interpretation pilot with lawful-access and resource gates, independent of regional archive urgency. No subsequent task begins here.


## WR005 reference-metadata pilot checkpoint — 10 October 2026

[WR005](../research/weather/midas-reference-interpretation-pilot.md) completes the authorised real metadata pilot, **OUTCOME B — PARTIAL INTERPRETATION**. Three local files are pinned; metadata/year-range and change-log joins reproduce. Historical thermometer/clock/QC support does not establish a strict eligible era; no annual observation or forecast acquisition occurs. The isolated research utility is not a production Weather subsystem. All accepted Atlas and Weather evidence remains; no application/platform/maturity/provider decision changes.

Exactly one subsequent task is the report's **WR006 historical measurement support and reference-target decision — NOT BEGUN**. No physical-device work, framework/renderer implementation or forecast benchmarking begins.


## WR006 reference decision and independent global engineering — 10 October 2026

[WR006](../research/weather/midas-historical-measurement-support.md) reaches **scientific
Outcome C — EVIDENCE BLOCKED; reference-target Decision C**. One pinned metadata
nominee was investigated; height/history/clock and actual record interpretation do
not establish a strict or revised eligible reference. No annual file or forecast
magnitudes were inspected. Generic QC documentation retrieval improved; no skill,
Weather readiness, application-stage or provider decision follows.

The next independent evidence gate is [one bounded historical GFS temperature-field
acquisition/decoding/integrity pilot](../research/weather/midas-historical-measurement-support.md#9-programme-consequence-and-exactly-one-next-task),
**NOT BEGUN**. It can progress global source-format research without replacing
independent reference verification. Device/application/F32 gates and the broader
Weather scientific programme remain unchanged; no further task starts here.
