# Meridian decision register

Reviewed 9 October 2026. Owner is the Meridian project owner unless a later authorised audit assigns another owner. Deadlines are dependency gates, not dates. Supporting evidence is linked in the relevant foundation document and [source ledger](sources.md). Status describes the recommendation, not an implemented feature.

Priority: P0 blocks costly foundation decisions; P1 blocks the relevant maturity gate; P2 can wait. Reversibility refers to changing implementation without losing scientific/user identity. No final mobile framework, public brand, cloud provider or private restructuring is selected.

## DECIDE BEFORE PRIVATE REPOSITORY RESTRUCTURING

| ID / subject | Current recommendation | Alternatives | Supporting evidence | Risk and reversibility | Dependencies / deadline | Status |
|---|---|---|---|---|---|---|
| F01 P0 — new UI | New interaction design and implementation; experimental frontend is a technical reference | Migrate existing hierarchy; reuse only individual proven utilities | Established user direction; [reconciliation](reconciliation.md) | Inherited coupling/debt; UI choices reversible early, costly after migration | Product tasks; before moving UI code | DECIDED |
| F02 P0 — scientific authority | Canonical qualified files/root remain authoritative; indexes/render products do not | Database authority; frontend interpretation | Accepted Atlas proofs and runtime | Losing history/meaning expensive to reverse | Frozen contracts; before any adapter/package restructuring | DECIDED |
| F03 P0 — mobile/offline delivery boundary | Portable read-only publication projection and conforming readers; keep desktop processing separate | Phone Node/Python; always-connected desktop proxy | Current runtime imports/workers; [platform options](platform.md) | Hidden desktop dependency; exported format expensive after downloads | F04/F05 results; F03 supplies a provisional test boundary, not a prior implementation requirement; before declaring cross-platform package boundaries | PROVISIONAL |
| F04 P0 — terrain engine | Test exact native and GL JS device paths before selecting engine/framework | Native commercial SDK after rights review; defer high-quality terrain; custom engine | Native support table vs JS terrain; native roadmap | Missing central feature; renderer choice costly | Physical hardware, retained tiles and terms; before private map restructuring | REQUIRES FEASIBILITY TEST |
| F05 P0 — offline storage | Test deliberate file-backed package, completeness, deletion and process recovery | PWA-only caches; SDK offline packs; tile archive reader | Browser eviction, native offline APIs, accepted pinning | Silent incompleteness; package/reader choices costly once distributed | Joint F03/F04 feasibility inputs, not prerequisites for completing the study; before restructuring storage/app host | REQUIRES FEASIBILITY TEST |
| F06 P1 — desktop adapter | Retain read-only local in-process adapter and long-lived pinned context | Dedicated service; direct browser filesystem | Node/browser boundary; full-open cost | Host/cancellation/security mismatch; mostly reversible | Private audit must be separately authorised; before implementing host | PROVISIONAL |
| F07 P1 — reusable code licensing | Establish owner/contributor rights and deliberate package distribution terms | Keep source restricted; choose suitable open-source licence | README portfolio-review-only declaration | Unauthorised distribution; legal exposure less reversible | Contribution inventory; before external package distribution, screen during audit | REQUIRES LEGAL OR RIGHTS REVIEW |
| F08 P1 — package strategy | Narrow versioned contracts/runtime/adapters, local workspace while developing; no repository copying | Vendoring bounded reviewed utilities; Git dependency temporarily | Current unexported runtime/research imports; prior architecture | Accidental authority duplication; extraction reversible initially | F02/F03/F07 and private audit; before extraction | PROVISIONAL |
| F09 P1 — pilot | Retain Riffelhorn 4 km², with explicit limited evidence/terrain support | Tryfan richer pilot but runtime exposure gaps; Exe diverse evidence but not terrain-first | Accepted pilot comparison and Swiss support findings | Visual terrain continuity unresolved; region readily changed early | F04/F05; confirm before first integrated map | PROVISIONAL |
| F10 P1 — engineering baseline | en-GB, clear modules, explicit boundaries/errors, scoped tests/ADRs and full-diff review | Large universal framework; chat-dependent development | Established direction; [engineering](engineering.md) | Undocumented hidden state; low-cost adoption now | No restructuring prerequisite; applies now | DECIDED |

## DECIDE BEFORE FIRST MOBILE IMPLEMENTATION

| ID / subject | Current recommendation | Alternatives | Supporting evidence | Risk and reversibility | Dependencies / deadline | Status |
|---|---|---|---|---|---|---|
| F11 P0 — mobile framework | Shortlist native UI, React Native/native map, and native-file shell/GL JS; no winner yet | Flutter; PWA; Kotlin shared logic/native UI | [Platform comparison](platform.md); established-app primary sources | Framework lock-in, plugins and team burden; medium/high switching cost | F04/F05, hardware/skills; before substantial mobile UI | REQUIRES FEASIBILITY TEST |
| F12 P0 — portable client contract | Version identities, capability/coverage states, native times/provenance and supported query semantics; conformance fixtures | Node-shaped API; broad query language | Runtime qualifications, DTO proposal and offline gap | Semantic divergence; wire contracts expensive once published | F03, F04/F05; before reader implementation/distribution | PROVISIONAL |
| F13 P1 — shared computation | Share semantics first; share code only for a demonstrated computation need | Rust/C++ core now; Kotlin shared logic; platform-specific conforming readers | Current small query population; Organic Maps/OsmAnd examples | FFI/toolchain complexity; expensive premature core | Profiling and conformance; defer selection until justified | DEFERRED |
| F14 P1 — interaction architecture | Dedicated field/desktop/accessibility research before substantial UI; not final visual design here | Reuse old layout; framework-led screens | [Product requirements](product.md) | Poor outdoor usability/accessibility; redesign costly after coding | F11 scope and consented research plan; before UI implementation | DECIDED |
| F15 P1 — location/background services | Foreground purpose-specific positioning first; no tracking by default | Always-on tracking; app only without GPS initially | OS restrictions and opt-in policy | Privacy, battery, Play/store rejection; medium switching cost | F11, privacy flow; before adding location | DECIDED |
| F16 P1 — visual terrain package | Preserve source/datum/encoding/exaggeration and explicit support; test retained pure-Swiss subset | Existing global visual context with honest label; failed Swiss/AWS join | Accepted negative reconciliation and regional support | Seam/datum illusion; data choice reversible before distribution | F04/F05 and rights; before first terrain package | PROVISIONAL |

## DECIDE BEFORE PRIVATE BETA

| ID / subject | Current recommendation | Alternatives | Supporting evidence | Risk and reversibility | Dependencies / deadline | Status |
|---|---|---|---|---|---|---|
| F17 P0 — data/service rights | Per-source rights register including processing, display, commercial and offline permissions | Treat retention/open renderer as blanket permission | OSM service policy, swisstopo terms, Open-Meteo API/data distinction | Blocked distribution and unplanned cost; high legal impact | Exact included versions/products; before tester redistribution | REQUIRES LEGAL OR RIGHTS REVIEW |
| F18 P0 — privacy flows | Explicit opt-in, no default analytics/tracks; third-party request inventory, deletion/export and DPIA screening | Account-free therefore no privacy review; generic consent banner | Current ICO/EU guidance; tile/search/forecast transmissions | Trust/legal harm and leaked tracks; difficult to undo | Feature/recipient inventory; before external testers | DECIDED |
| F19 P1 — quality/security operations | Focused CI, clean builds, device/offline/accessibility suite, update/incident contact and restore tests | Manual-only releases; all enterprise controls immediately | No tracked workflows; SSDF/MASVS; OS lifecycle | Regressions/key/data loss; moderate setup effort | Exact supported platforms/fixtures; before repeated beta releases | PROVISIONAL |
| F20 P1 — Weather milestone | Follow first Atlas view, independent run/issue/valid clocks and delivery lifecycle | Single shared scientific transaction; delay all Weather indefinitely | Existing GFS architecture; accepted sequencing | Time conflation and added scope; sequencing reversible | First view passes; before offering Weather in beta | DECIDED |
| F21 P1 — identifiers/distribution | Check product, namespace and store/bundle identifiers before committing distribution identities | Keep all working names publicly without checking | HPE Meridian, Mapbox Atlas, Traverse listing | Migration/discoverability/legal burden; bundle IDs costly | Trademark/domain/store/package checks; before store/test distribution commitment | REQUIRES LEGAL OR RIGHTS REVIEW |
| F22 P1 — beta compatibility | Permit substantial internal/alpha and beta redesign; protect identities, user data, supported reader upgrades, export and recovery; record stage gates | Freeze everything; silently reset data | [Eight-stage roadmap](roadmap.md); immutable histories | User-data loss/trust; migration cost grows with users | Supported schemas, user-data scope; before invitations | DECIDED |

## DECIDE BEFORE PUBLIC RELEASE

| ID / subject | Current recommendation | Alternatives | Supporting evidence | Risk and reversibility | Dependencies / deadline | Status |
|---|---|---|---|---|---|---|
| F23 P0 — public branding/legal scope | Full relevant-territory naming and rights review; assess GDPR/PECR, CRA/EAA applicability | Assume basic web search clears product | [Roadmap](roadmap.md), official registry/legal sources | Public conflict or missed obligation; high migration/legal cost | Actual markets/distribution/legal entity; before release | REQUIRES LEGAL OR RIGHTS REVIEW |
| F24 P0 — safety scope | Exploration first; navigation requires separate graph, location, offline and safety validation | Add turn-by-turn with disclaimer only | [Outdoor risk table](product.md) | Physical harm/inappropriate reliance; high trust impact | Capability evidence and field validation; before navigation/public claims | DECIDED |
| F25 P1 — delivery/provider | Local-first now; choose reliable later delivery from measured workload/cost | Managed cloud, independent host, object/CDN hybrid | [Provider comparison](platform.md) and official pricing dimensions | Egress/operations/lock-in; storage interfaces moderately reversible | Measured requirements and F32; before delivery procurement; no provider selected now | DEFERRED |
| F26 P1 — release readiness | Eight maturity gates, supported scope, security/restore and F32 financial approval before unrestricted exposure; no calendar override | Ship by arbitrary date; perpetual unsupported beta | [Maturity roadmap](roadmap.md) | Unmaintained app/incompatible packages; high trust cost | Beta results, legal/privacy/quality and F32; before public release and any earlier unrestricted endpoint | DECIDED |

## CAN SAFELY WAIT

| ID / subject | Current recommendation | Alternatives | Supporting evidence | Risk and reversibility | Dependencies / deadline | Status |
|---|---|---|---|---|---|---|
| F27 P2 — routing/search expansion | Retain as later scoped capabilities; real graph/data/rights needed | Import a GPL/proprietary engine immediately | Current evidence explorer has no integrated routing population | Scope/licence/safety burden; data/core choices eventually costly | Demonstrated user need; before promising routing/search, not prototype prerequisite | DEFERRED |
| F28 P2 — package deltas/history scale | Correct whole-package updates first; profile before deltas | Complex delta store/automatic cross-version merging | Small current world; immutable archives may require replacement | Corruption/compatibility burden; reversible early | Real bandwidth/storage pressure; before large distribution, not now | DEFERRED |
| F29 P2 — accounts/billing/community/cloud sync | No initial billing/accounts; free-at-no-cost principle, transparent genuine cost recovery and new Meridian value may support sustainability | Default accounts, paid free capabilities, public forums | [Product policy](product.md) and [economics](economics.md) | Avoidable trust/operational/legal complexity | Actual product/cost requirement; before implementation | DEFERRED |
| F30 P2 — broader population | Existing retained regions suffice for bounded prototype; expand by user/scientific need | Integrate all families/regions before starting | Accepted readiness and mixed-family proofs | Indefinite research delays; expansion reversible | Useful task and rights; not an entry condition | DECIDED |

## AMENDMENT POLICIES AND EXPOSURE GATES

These four policies are **DECIDED**, not declarations that implementation, release evidence or spending approval exists. Their deadlines complement the groups above.

| ID / subject | Current recommendation | Alternatives | Supporting evidence | Risk and reversibility | Dependencies / deadline | Status |
|---|---|---|---|---|---|---|
| F31 P1 — development maturity | Eight evidence-led stages; long internal development and beta permitted; one terrain prototype does not admit testers | Prototype directly to invitations; calendar-led beta | [Roadmap](roadmap.md); bounded accepted readiness | Premature reliance and stranded data; process reversible, lost trust/data less so | Stage scope and evidence; apply now, alpha/beta gates before invitations | DECIDED |
| F32 P0 — operational economics/public exposure | Document architecture/dependencies, scenario costs and controls; obtain user-approved budget/exposure ceiling and rehearse suspension/recovery before unrestricted access | Assume budget alerts cap spend; unrestricted beta first | [Economics gate](economics.md); primary provider limitations S37 | Unbounded liability, abuse and unavailable service; incurred charges irreversible | Concrete delivery requirements, F17/F18, cost/control evidence; before any unrestricted endpoint, proportionate approval for earlier paid/remote trials | DECIDED |
| F33 P1 — subsystem evolution | Stable responsibilities with replaceable implementations; measured revisit triggers and compatible migration | Freeze every technology; speculative universal/distributed core | [Evolution register](evolution.md); accepted local proofs and limits | Premature lock-in or lost authority; format/history changes costly | F02 and relevant workload evidence; record before a material subsystem change | DECIDED |
| F34 P0 — document precedence | Current foundations override incompatible experimental/prototype planning; preserve scientific contracts, results and historical reports | Erase historical proposals; inherit old UI/engine/audit sequence | [Reconciliation](reconciliation.md#documentation-precedence) | Conflicting instructions and silent science changes; avoidable now | F01/F02 and explicit supersession; apply before planning/restructuring | DECIDED |

## Decision discipline

The next task is **only** the feasibility study scoped in the [summary](summary.md), not all tests listed here. F04/F05 are the highest-priority unresolved technical decisions. F07/F17/F21/F23 remain review gates, not claims that rights are cleared. Private-repository contents, hardware and team capacity remain unknown. Each authorised follow-up should update the affected rows with actual evidence, an owner and a revisit trigger, without rewriting accepted scientific contracts.

Amendment dependency clarification: F03 is a provisional input to the F04/F05 study; its final boundary depends on their results. This is a joint design/feasibility loop, not a circular blocking prerequisite. F25 provider selection and F29 billing remain deferred; F32 decides the gate now while actual prices, budget approval and control effectiveness remain unestablished. F31/F34 do not change accepted scientific readiness results or authorise any next stage.


## Portable Atlas read reference — 9 October 2026

[Reference contract and fixtures established](../research/atlas-portable-read.md): 60 cases, three exact historical
pins and complete qualifications; three fresh replays passed 360 indexed/full comparisons.
F03/F12 gain an executable reference target; their portable/production decisions remain
provisional. Accepted evidence and statuses are unchanged; mobile, offline and renderer
feasibility remain unproven.

The user-authorised contract task supersedes prerequisite resolution as the current
engineering path, without resolving the physical-device gate. Exactly one next task:
**MERIDIAN ATLAS PORTABLE READ-ONLY PROJECTION AND INDEPENDENT READER SPIKE — NOT BEGUN**.
The linked report specifies its bounded, platform/framework-neutral scope and safeguards.


## Portable Atlas projection spike — 9 October 2026

[SEMANTIC PORTABILITY DEMONSTRATED](../research/atlas-portable-projection.md), bounded to the frozen Riffelhorn
profile and desktop GIS toolchain: three isolated 60/60 replays, exact full-envelope
agreement, 14 novel behaviour/failure tests and byte-identical 116.7 MB projection
reproduction. The independent Python reader requires no original source files,
authoritative query implementation, Node or network during tested reads.

F03/F12 gain semantic feasibility evidence; format/framework, mobile and robust offline
lifecycle remain provisional or unproven. Canonical authority, accepted evidence,
frozen fixtures and research statuses remain unchanged. Exactly one next bounded task:
**MERIDIAN ATLAS PORTABLE PROJECTION HARDENING AND OFFLINE FAILURE VALIDATION — NOT BEGUN**.
Its scope follows observed incomplete-install/post-open consistency gaps, not production
or private-repository integration. The linked report records commands, costs and limits.


## Desktop projection lifecycle evidence — 9 October 2026

[DESKTOP OFFLINE CONSISTENCY DEMONSTRATED](../research/atlas-portable-projection-hardening.md), bounded to Windows/NTFS and the
retained finite read profile: complete closure before ready, separate installation
selection/exact scientific generation, failed-replacement preservation, restart,
explicit deletion and verified in-memory raster snapshots. Frozen semantic cases,
canonical authority and accepted research remain unchanged. The report records
commands, failure tests, measured storage/memory and unproven power-loss/authenticity/
mobile guarantees. Implementation stays under scripts/atlas/portable-spike; the
Atlas authority, Weather and production application are unchanged.

F03/F05/F12 and E02/E05 gain bounded desktop evidence; final formats/frameworks,
physical-device feasibility and legal redistribution remain open. Exactly one
subsequent task: **MERIDIAN ATLAS OFFLINE PROJECTION PORTABILITY AND RESOURCE-REDUCTION
STUDY — NOT BEGUN**. Its scope follows observed source-raster overhead, desktop GIS
dependencies and unresolved offline rights; no mobile deployment, production or
private-repository integration is begun.
