# Meridian product principles

Reviewed 9 October 2026. These principles govern a newly designed application, not a migration of the experimental UI. See [platform options](platform.md) for delivery constraints and [roadmap](roadmap.md) for maturity gates.

## Product purpose and scope

Meridian is a map-first geographical explorer with terrain central to understanding place. Atlas supplies qualified evidence; Weather supplies distinct atmospheric observations, analyses and forecasts. The application presents them together without inventing agreement. Mobile is the primary field-use product; web supports planning, exploration, research and detailed inspection. A desktop prototype may precede a mobile implementation without changing that direction.

The first useful experience is a bounded Riffelhorn terrain/evidence explorer with a clearly marked coverage footprint, selectable qualified records and an inspector. It is **exploratory mapping, not safety-critical navigation**. It needs neither accounts, routing, collaboration, billing, all evidence families nor global coverage. A newly researched interaction design precedes substantial UI construction. Existing frontend code is a technical reference; individual proven utilities may be retained after review.

Use en-GB throughout new text and documentation. Preserve source classification codes and established technical identifiers. British spelling does not justify changing a scientific identity or external API.

## Offline and connectivity

Online, limited-connectivity and offline operation are separate product states. Deliberately downloaded, verified packages are different from incidental caches. Show what is available locally, what is incomplete, what is unsupported and what requires a connection. A missing overlay must not look like an empty physical world.

Offline evidence keeps its provenance and historical publication pin. An offline forecast is an issued forecast snapshot with an ageing warning and valid horizon, not live weather. Download controls must disclose expected size, included layers, time coverage, rights and dependency completeness. Users must be able to pause, cancel and delete geographical packages without deleting their personal routes or waypoints. See [offline architecture](platform.md#offline-architecture).

## Interaction research before visual styling

Conduct a dedicated later design study of representative field and desktop tasks, not final mock-ups in this review. Test finding a place, interpreting coverage, changing terrain viewpoint, selecting overlapping evidence, checking provenance, understanding time and diagnosing unavailable offline data. Include novice geographical users, experienced outdoor users and people with access needs. Recruitment and recorded research need explicit consent and purpose; no study is begun here.

| Interaction concern | Foundation requirement |
|---|---|
| Map-first navigation | Clear camera reset, north/tilt state and 2D fallback; preserve context when opening inspection |
| Field use | Large targets, one-handed primary actions, sunlight-readable contrast, gloves/wet-screen consideration; no precise gesture as the only route to an important action |
| Layers | Organise by understandable purpose, retain scientific family distinctions, show coverage and unavailable states; avoid a wall of mutually indistinguishable switches |
| Evidence inspection | Summary first: kind, source, time, principal limitation. Expand for native classifications, method, datum, rights and lineage |
| Time | Separate Atlas historical knowledge/publication selection from Weather issue and valid-time controls; make active context visible |
| Desktop planning | Keyboard operation, wide-map context and detailed side inspection; do not stretch a phone layout as the entire desktop design |
| Search and routes | Search must disclose external transmission. Routing is later, contingent on a defensible graph and navigation tests |
| Downloads | Explicit packages, progress, completeness, quota errors and local deletion; no silent background tracking to obtain downloads |
| Accessibility | Keyboard and screen-reader evidence list, text alternatives for map-only results, focus restoration, scaling and reduced motion; no colour-only meaning |

Use WCAG 2.2 AA as the web engineering target, with a testable interpretation for map content. Its minimum target-size criterion is not an outdoor usability target. Prefer Android 48 dp and iOS 44 pt hit regions for primary controls, adjusting for density and task. Contrast and accessible alternatives need actual testing; a map canvas does not exempt its surrounding controls. [WCAG 2.2](https://www.w3.org/TR/WCAG22/), [Android accessibility](https://developer.android.com/guide/topics/ui/accessibility/views/apps-views), [Apple buttons guidance](https://developer.apple.com/design/human-interface-guidelines/buttons).

## Four different correctness questions

| Kind | Question | Example of a failure |
|---|---|---|
| SCIENTIFIC CORRECTNESS | Is the evidence faithfully represented, with qualifications? | Calling DSM terrain a DTM or a planning boundary a current legal restriction |
| VISUAL CORRECTNESS | Does the rendering preserve the intended spatial relationships and disclose distortion? | Joining incompatible height references, hiding a coverage gap or presenting exaggerated relief as measured height |
| OPERATIONAL CORRECTNESS | Does the application load, pin, update and recover the intended data? | A partial offline package or mixed publication revisions labelled ready |
| DECISION SUITABILITY | Does the evidence support the user's intended decision? | Using an old mapped water feature to decide a crossing is safe today |

Passing one does not establish the others. No invented confidence percentage, safety score or inferred agreement is acceptable.

## Scientific and geographical presentation

Default inspection should answer **what this is, where it applies, which source supports it, when it describes or records something, and the main limitation**. Details preserve exact evidence/revision identity, publication generation, native units/CRS/datum, provenance, uncertainty and rights. Provide plain-language explanations rather than exposing every research field initially.

Observed, mapped, interpreted, derived and administrative evidence remain distinguishable. Habitat inventories are not current ecological observations or species guarantees. Planning references are not automatic current legal restrictions. Water maps are not observations of current wetness. No result is not proof of absence. Stale information is not necessarily false; an administrative correction is not necessarily a physical change.

Coordinate conversion belongs in verified adapters, not ad hoc UI arithmetic. Name coordinate order and units. Do not mix Swiss LN02 and EGM2008 heights into a seamless surface. Terrain exaggeration must be visible and resettable; a measured-height inspection uses qualified native evidence, not the renderer's height. Lighting is visual interpretation, not material observation. Occlusion, projection and zoom generalisation can hide or distort features: preserve footprint outlines and alternate 2D/list inspection. Pixels imply neither source resolution nor positional accuracy.

Separate observation/survey interval, source edition/publication, administrative effective time, preparation, knowledge acceptance and Atlas publication generation. Unknowns stay unknown. Historical generations remain labelled historical. Weather displays model, run issue, valid time, accumulation interval where relevant, units and expiry/unavailability; forecast time is not an Atlas knowledge clock. Avoid implying a precise epoch from a broad survey period.

## Outdoor safety and reliability

| Plausible risk | Design and test response | Initial scope boundary |
|---|---|---|
| Missing path or incorrect route guidance | Preserve source/coverage; later routing requires independent graph and route validation | No turn-by-turn navigation promise |
| Inaccurate terrain, occlusion or exaggerated slopes | Visible exaggeration, 2D fallback, source/datum inspection and fixed-view visual comparisons | Rendered surface is not safety evidence |
| Stale weather or absent avalanche information | Issue/valid-time age, explicit unavailable state and regional-service links; never substitute an unrelated model silently | No avalanche assessment inferred from global weather |
| Unreliable GPS | Label fix age and reported accuracy; handle approximate permission, denial and loss; avoid unexplained snapping | Position display is not guaranteed position truth |
| Suspension or termination | Restore selected package/pin/view; expose interruption; test actual OS lifecycle | No background continuity guarantee without testing |
| Battery or memory pressure | Conservative default camera, optional 2D, bounded resources; device profiling and low-power tests | Do not promise a duration from emulator measurements |
| Lost connectivity or incomplete download | Airplane-mode tests, verified completeness, local availability status and honest gaps | No cached tile assumed deliberately retained |
| Mixed generations or unavailable history | Pin queries and compatible render manifests; fail explicitly | No automatic fallback to another generation |
| Inappropriate reliance | State intended use, source limits and alternatives at relevant decisions | Disclaimers do not replace correct functions |

Location access should start as a foreground, purpose-specific action. Background tracking is a later separately justified capability, not an implementation convenience. Android documents stricter background access and update limits; iOS lifecycle behaviour also requires device testing. [Android background location](https://developer.android.com/develop/sensors-and-location/location/background).

## Privacy, services, research and monetisation

Personal data collection/use is explicit opt-in with a clear purpose. No accounts, behavioural analytics or persistent location tracking are needed for the first prototype. A tile request, coordinate-based forecast request or external search can transmit information even without an account. The interface must distinguish local operations from third-party transmission. Privacy flows, retention and legal assessments are specified in the [roadmap](roadmap.md).

Complement trusted regional services. Prefer source-labelled links to Met Office, swisstopo, Walkhighlands and SAIS until display, API and offline rights are established. Do not scrape or white-label their advice, and do not imply their endorsement. Link availability is not evidence that Meridian can reproduce a specialist's forecasts or judgement.

Do not charge merely for information, data or functionality Meridian can provide at no cost. Genuine licensed-data, paid-service, computation and delivery costs may be recovered transparently; new value created by Meridian may also support a sustainable business model. This amends the earlier cost-recovery-only wording, not source rights or opt-in privacy. Service terms may change when charging or commercial use begins; review them before that transition. Billing remains deferred under F29. Before unrestricted access, pass the [operational economics and exposure gate](economics.md), including owner-approved budget, exposure controls and safe suspension. No price, business model or expenditure is approved here.

A future Research section should publish cited sources, methods, limitations and suitable evidence, with rights review and clear distinction between research and operational products. Personal data, restricted payloads and unreviewed claims stay excluded. Community forums are not an initial requirement.

## Development readiness

A scientifically honest terrain/evidence demonstration is an internal technical milestone. It does not establish integrated alpha, tester support, reliable offline use or beta readiness. The [eight-stage roadmap](roadmap.md) permits substantial development and redesign while preserving qualifications, user data, upgrade compatibility and recovery.
