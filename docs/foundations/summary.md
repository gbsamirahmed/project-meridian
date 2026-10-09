# Meridian foundations review summary

9 October 2026. Starting checkpoint **68756976467aeef4bc647bc2b5fe11cae5bfd904**; public `project-meridian`, `main`, upstream `origin/main`, clean initial tree, origin fetched and 0/0 divergence.

## Executive result

**C — FOUNDATIONS REVIEW READY.** Engineering principles, product requirements, platform alternatives, offline architecture, release gates and a prioritised decision register are documented. The accepted prototype plan is explicitly reconciled. Remaining platform, rights and private-repository uncertainties are bounded; no application implementation, private access, new geographical acquisition or infrastructure was undertaken.

The most important choice is to share **scientific meaning and data contracts**, not assume one frontend or runtime can meet every platform's needs. Atlas's canonical files/publication root remain authoritative. Weather remains independent. Mobile field use, a new UI and deliberate offline availability become design requirements now; final mobile technology remains undecided.

## Reading path and durable deliverables

| Document | Purpose |
|---|---|
| [Engineering foundations](engineering.md) | Human-readable code, staged standards, tests, review, reproducibility, security and AI-assisted definition of done |
| [Product principles](product.md) | Mobile/desktop tasks, scientific presentation, accessibility, outdoor reliability, opt-in privacy and monetisation |
| [Platform and infrastructure options](platform.md) | Six architecture families, three feasibility candidates, offline packages, local/provider choices and performance limits |
| [Decision register](decisions.md) | Thirty prioritised decisions with alternatives, evidence, risk, reversibility, dependencies, event-based deadlines and status |
| [Private-beta and pre-release roadmap](roadmap.md) | Five maturity stages, rights register proposal, naming/privacy/security gates and prototype checklist |
| [Architecture reconciliation](reconciliation.md) | Ten explicit retain/revise/supersede/defer findings and authority/package diagrams |
| [Source ledger](sources.md) | Dated primary external references and repository evidence; verified claims separated from inference |

These documents distribute responsibilities rather than duplicate the accepted Atlas research. They are a planning foundation, not a claim that CI, packages, offline readers or new UI already exist.

## What is established and what changes

**DECIDE NOW:** en-GB; cohesive modules and explicit errors; clear scientific authority; new UI rather than hierarchy migration; mobile field-use direction; offline as a designed capability; opt-in privacy including third-party requests; no unnecessary accounts/cloud/billing; readiness-based release; specialist-service complementarity. Frozen scientific identifiers and historical evidence are preserved.

**PROVISIONAL DIRECTION:** Riffelhorn remains the first compact terrain explorer. Keep a read-only long-lived local Atlas adapter for desktop. Expose portable versioned view semantics and eventually validated read-only regional packages. Build new interactions after a dedicated design study. Weather follows the first Atlas milestone with its own issue/valid clock.

**DEFER PENDING EVIDENCE:** mobile framework/renderer, exact offline format/reader, shared computational core, private host/package extraction, commercial redistribution, final brand, provider and supported-device budgets. These are actionable gates rather than an unresolved architecture menu.

**REJECT:** migrating the old experimental UI by default; equating native offline support with 3D terrain parity; making Node/Python reachable over a connection mandatory for field use; turning SQLite/render products into authority; caches treated as complete packages; source overlap treated as scientific agreement; unknown treated as absence; a disclaimer replacing correct navigation; premature cloud/event/workflow platforms.

## Most significant findings and overlooked risks

Likelihood is a qualitative assessment of the current direction, not a statistical estimate.

| Finding | Likelihood / impact / reversibility | Why it matters and response |
|---|---|---|
| Native terrain parity is not established by MapLibre's published support table | High decision uncertainty / central feature / costly renderer switch | Terrain is central; test exact SDKs on physical devices before map/framework restructuring. A roadmap is not shipped proof |
| Current Atlas is a desktop Node/Python runtime, not a portable phone reader | Certain present boundary / high / costly downloaded-format change | A browser DTO cannot provide offline device querying. Define faithful export/reader semantics and conformance, not a parallel scientific engine |
| Rendering/offline dependency closure and rights are broader than tiles | High / high / costly once packages distributed | Fonts, styles, sprites, DEM, source credits and provider terms matter. Standard OSM raster service cannot be used for bulk offline maps; assess exact delivery rights |
| Public code is deliberately not open-source licensed | Certain declaration / distribution gate / legal exposure | Versioned reusable packages need intentional terms and ownership review. No root licence file is not permission to copy |
| External services expose viewport/coordinates even without accounts | High for current network design / privacy/trust / disclosure cannot be undone | Inventory tiles, search, Weather and crash flows; local-first and explicit purpose-specific choices; a proxy does not erase processing |
| Working names overlap actual mapping/outdoor products | Verified preliminary examples / branding and migration / published IDs costly | HPE Meridian, Mapbox Atlas and Traverse merit due diligence before store/package commitments; no clearance claimed |
| Beta upgrade and app-store rollback constraints can strand data | Plausible / high / costly after testers | Separate package and binary compatibility, preserve personal data and rehearse forward recovery |
| Device hardware, iOS build access, native skills and support capacity are unknown | Certain uncertainty / delivery constraint / moderately reversible | Feasibility must report missing hardware instead of claiming emulator parity; one-person maintenance affects the shortlist |
| Current safeguards do not equal maintained CI/security/distribution | Certain inspection limit / beta reliability / reversible before release | No tracked Actions workflows; remote protections unknown. Add proportional automation and restore-tested keys/data during authorised implementation |
| New regulatory/product duties may be discovered too late | Market-dependent / potentially high / legal gate | Screen UK/EU privacy, CRA and accessibility applicability with actual product/distribution; not blanket claims or a last-minute checklist |

Primary evidence for these claims and limitations is cited in the [platform review](platform.md), [roadmap](roadmap.md) and [source ledger](sources.md). No naming, rights or legal assessment here constitutes clearance.

## Scientific and geographical limits

The current world has 141 qualified records, not comprehensive terrain/ecology/legal coverage. Tryfan's richer accepted pilot is not wholly exposed by today's runtime. Riffelhorn's 4 km² evidence support differs from the larger rendering research area, with incomplete low-zoom/perimeter terrain support. Exe's selected probe evidence is not a complete regional inventory. These limits are sufficient for a bounded evidence explorer but not navigation or public safety conclusions.

The latest accepted baseline is 9.11 s median full open, 838 ms catalogue build and 220 KiB catalogue. Validation startup and interactive queries are different workloads. Keep a pinned context and measure request cancellation/inspection/render responsiveness; do not weaken full validation to achieve an animation target. No new performance benchmark or national-scale extrapolation is claimed.

## Regression verification

**59 safeguards passed.** The external, uncommitted runner checked the exact checkpoint/upstream; all 1,119 tracked files outside six append-only navigation files; accepted retained-store/source hashes; all 42 canonical research status rows; all 113 production hashes; unchanged prototype report, runtime, Weather, Traverse and frozen contracts; new-document links, bounded scope and whitespace. New review content was also inspected against the evidence and the requested boundaries.

No executable application changes were made. The inherited 903 tests are **not reported as freshly rerun**. Appropriate documentation/scope/protection checks replace unrelated expensive test suites. No private repository, new geographical data, S7, cloud service or generated payload enters the change. Accepted research results remain historical and unchanged.

## Exactly one next bounded task — NOT BEGUN

**MERIDIAN MOBILE TERRAIN AND OFFLINE EVIDENCE FEASIBILITY STUDY.**

**Objective and uncertainty:** establish whether the required terrain-first experience and qualified read-only offline evidence can work on representative Android/iOS hardware using credible native and GL JS device paths. This resolves F04/F05 before expensive private map/storage restructuring; it does not select a framework from documentation alone.

**Starting evidence:** this review; unchanged prototype plan; accepted Riffelhorn support/preparation/query records; existing pure-Swiss complete tiles and render metadata; canonical query fixtures; published SDK capabilities. Baseline desktop Node/Python queries serve as reference, not an assumed mobile runtime.

**Permitted scope:** isolated disposable technical test drivers outside production; at most three candidate shells and two genuinely distinct renderer paths, beginning with a capability/terms check to avoid duplicate wrapper benchmarks. Use only a small already retained complete-tile/support subset and qualified metadata; estimate selected bytes first, aim for at most 250 MB payload plus bounded temporary copies, and report a precise storage blocker rather than expanding silently. No new geographical acquisition, private access, cloud resources, paid service commitment, new scientific method or production UI. A missing basemap/labels remains an explicit test limitation, not permission to download one.

**Hardware prerequisite:** identify named physical Android/iOS devices, OS/build/SDK versions and iOS build access. If unavailable, record exactly which platform cannot be tested and which decision remains open. Do not infer field performance from a desktop browser or emulator. Real location history is unnecessary; use controlled permission/lifecycle cases and obtain consent before any personal data is involved.

**Deliverables:** capability matrix; reproducible minimal drivers/commands; exact retained-input manifest; fixed-view visual/height-encoding comparisons; offline asset-closure audit; read-only evidence contract conformance; latency/memory/thermal/battery observations; suspension/termination/restart results; rights limitations; a justified preferred path or specific blocker. Do not build a native scientific core, universal package framework or custom terrain renderer to force success.

**Acceptance:** demonstrate actual 3D terrain rather than hillshade alone; preserve source/datum/exaggeration/support labels; declare low-zoom/edge gaps. On each tested platform, airplane-mode launch and restart reproduce at least 25 predetermined identity/qualification queries, including unknown time, coverage boundary and historical pin; no hidden network resources or canonical metadata changes. Interrupted/corrupt/incomplete package cannot become ready. Compare named-device interaction distributions against provisional 30 fps terrain/2 s warm inspection targets, report memory and a controlled battery/thermal trial, and explain limitations rather than claiming universal efficiency. An unavailable capability must remain unsupported, not silently return empty evidence.

**Stop condition:** once those bounded capability, conformance, offline/recovery and resource comparisons support a provisional platform recommendation, or expose an exact blocker. Select one subsequent task from the findings; do not implement the application, restructure the private repository or expand the experiment into optimisation. The separately scoped private audit remains later and requires **explicit user authorisation before any private access**.

The feasibility study is selected but **not begun** by this review.
