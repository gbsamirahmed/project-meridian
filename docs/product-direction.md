# Meridian product and research direction

## Purpose and status

This document is Meridian's living design and research notebook. It records product direction, candidate capabilities, hypotheses, unresolved questions, and approaches that evidence has weakened or rejected. It is not a delivery roadmap or a promise that every idea will be implemented.

- `README.md` describes what currently works and how to run it.
- `docs/development-log.md` records completed implementation and research milestones.
- Source code remains authoritative for implementation details.

Terms such as **direction**, **candidate**, **potential**, **research question**, and **not yet implemented** are deliberate. When an experiment changes a decision, retain the hypothesis → experiment → finding → decision trail rather than rewriting history.

## Current Atlas research direction — 2026-10-07

The [research map](research/atlas-research-map.md) and
[current research-state register](research/atlas-research-state.md) govern Atlas
research status and supersession. Terrain, multiscale and physical-surface semantic
foundations are closed; Swiss frame pixels remain externally parked. This notebook's
route-first hypotheses preserve product history and downstream Traverse possibilities;
Atlas's physical-world foundation is not optimised for that application.

The [derived-understanding lifecycle assessment](research/atlas-derived-understanding-lifecycle.md)
closes the audit’s pre-synthesis gate using retained cases. Immutable revision snapshots
can support revisable understanding; scoped input-use/current-assessment descriptions are
justified beside existing v1. The [world-model architecture synthesis](research/atlas-world-model-architecture-synthesis.md)
is now complete (decision C), with domain-specific evidence and question-local answers.
The [retained Tryfan qualified-query/revision proof](research/tryfan-qualified-query-proof.md)
now completes that recommendation (**C — SUCCESS**), without production or contract changes.
The [storage/processing/serving requirements assessment](research/atlas-storage-processing-serving-requirements.md)
now completes that recommendation (**decision C**). Five logical storage responsibilities,
scoped lookup/freshness and coherent publication/recovery are established requirements;
technologies and production capacity remain provisional/unmeasured. The next recommendation
was the local persistent retained Tryfan proof, now complete
([report](research/tryfan-local-persistent-proof.md), **C — SUCCESS**). Real restart, coherent publication,
scoped update and historical replay survive; whole-metadata snapshots remain a small
replaceable single-writer mechanism. The [WorldCover binding proof](research/tryfan-worldcover-binding-proof.md)
now completes that recommendation (**C — SUCCESS**) for one native categorical raster,
qualified queries and semantic restart; other semantic input forms remain conceptual.
The [retained Riffelhorn appearance assessment](research/riffelhorn-appearance-assessment.md)
now completes that recommendation (**C — SUCCESS**, resolution conclusion **B**): source-derived
imagery fits shared identity/provenance plus bounded appearance eligibility, without a full
hierarchy/runtime. Exact 2023 geometry/illumination and physical appearance remain unknown;
correction/recovery/BRDF/relighting/fusion/registration science is still unresolved.
The [illumination/shadow identifiability assessment](research/illumination-identifiability.md)
now completes that recommendation (**B — PARTIAL IDENTIFIABILITY**). Date-conditioned terrain
geometry does not recover pixel exposure/shadow truth; source RGB is not calibrated reflectance.
Only a constrained post-L2A residual test is justified on retained dated Tryfan evidence.
The [frozen residual experiment](research/tryfan-illumination-normalization.md) now completes
that recommendation (**D — INCONCLUSIVE**): SE SCL5 count 12<20 fails the entry gate.
No C coefficient or corrected representation exists; no benefit/physical claim follows.
The [registration/epoch assessment](research/riffelhorn-registration-epoch.md) now completes that
recommendation (**B - SCALE-CONDITIONAL CONSISTENCY**). Coordinate/preparation checks agree, while
mixed epochs and ambiguous steep/dark controls limit fine physical matching. No registration
correction is justified by proxy optima. The [vegetation-only protocol assessment](research/tryfan-vegetation-protocol.md)
now completes that recommendation (**A - NOT JUSTIFIED**): three candidate masks/fixed spatial
holdouts do not provide sufficient controlled support; counts do not prove current homogeneous
vegetation. No model fitting, corrected bands or new executable correction protocol.
Original1842008 remains INCONCLUSIVE; all42 status columns and old criteria remain unchanged.
The [dark-source signal assessment](research/riffelhorn-dark-source-signal.md) completes that
recommendation (**B - PARTIAL RETAINED SIGNAL**): coherent 0.5-1 m image-space variation survives
in fixed dark supports, with low range, JPEG-phase/colour variation and deepest-support ambiguity.
Source/prepared hashes/encoding agree. Diagnostic lifting is a view, not corrected physical appearance;
steep projection and fine registration remain qualifications. All 42 status columns are preserved.
The [display-transfer experiment](research/riffelhorn-display-transfer.md) now completes that
recommendation (**B - PARTIAL**). A fixed global bounded toe4 modestly improves recorded dark
structure visibility, with bright/deep anchors unchanged; toe8 fails codec amplification limits.
Toe4 remains visually constrained by mottling and limited benefit: research-only, no production
prototype justified. This is a render-only operation, not illumination normalization or corrected
appearance. The [retained Exe query proof](research/exe-water-query-proof.md) completes that recommendation
(**C - SUCCESS**):75 frozen native point/support/feature/time/reference queries preserve WFD
identity, monthly detection/no-observation, PHI contributor vintages, mixed planning lineage,
event intervals and incompatible fallback rejection. Real restart/rebuild preserves qualifications;
no current hydraulic state or hydrological model is inferred. No foundation/production change.
The [programme acceptance](research/atlas-regional-pilot-acceptance.md) completes that recommendation
(**C - READY FOR BOUNDED REGIONAL PILOT**):37 retained proof records,50 required capabilities
plus3 explicit unproven/excluded classes,42 thread dispositions and9 frozen admission gates.
No demonstrated foundational blocker; integrated mixed-family publication/serving and operational
measurements become pilot exit obligations. Admission does not mean the pilot exists or science is complete.
The [bounded Tryfan pilot plan](research/tryfan-regional-pilot-plan.md) at `7809147`
(**C - IMPLEMENTABLE AS PLANNED**) defines six ordered slices following admission at `f16ce63`.
The [S1 catalogue/generation foundation](research/tryfan-pilot-s1.md) is now **C - S1 SUCCESS**:
five retained families,310 hash-verified artifacts/42.47MB, eight native/prepared representation
references, immutable external JSON generations, one coherent root, explicit writer recovery and
fresh-process/history/interruption tests. Median fresh hash-verifying load was251.39ms in the
[local measurements](research/tryfan-pilot-s1-results.json); this is not a production SLA.
S1 remains **C - S1 SUCCESS** at `b5ac715`; its published seed remains registration-only.
The [S2 native evidence/query layer](research/tryfan-pilot-s2.md) is now **C - S2 SUCCESS**:
WorldCover native cells/templates and all193 NRW records/28 code strings are readable through the
pinned published generation, with coexistence, mapping loss, native time/support, rights/provenance
and honest unsupported/unavailable states. July appearance is metadata only. Independent fresh
processes reproduce the same qualified matrix. [Measurements](research/tryfan-pilot-s2-results.json)
record about1.2ms median initialized queries and1.64s median fresh-process matrix execution;
these are local observations, not SLAs. No foundational/technology deviation; runtime reader
capability is separate from immutable seed capability. The checkpoint is the commit introducing
this S2 report (`7db385a`). S1 and S2 remain successful; their historical reports stay intact.
The [S3 derivation/lifecycle integration](research/tryfan-pilot-s3.md) is **C - S3 SUCCESS**:
four exact original AWS results persist in full G0 with explicit methods/input-use scopes,
computed freshness and pixel replay. Isolated Welsh-context recomputation adds only two summit
revisions and reuses southern results; no applicability update is published. Q21 composes six
separate generation-pinned evidence contexts. Median baseline436.85ms/freshness10.00ms/fixture
recomputation443.22ms; full metadata1.09MB ([observations](research/tryfan-pilot-s3-results.json)).
The [S4 serving/isolated consumer](research/tryfan-pilot-s4.md) is **C - S4 SUCCESS**:
read-only generation-pinned loopback HTTP, native/derived answers, exact retained artifacts,
provenance/rights and isolated Canvas2D consumer. A separate writer publishes a same-evidence
successor while the old consumer stays G1 and a new consumer sees G2. No scientific update.
Warm query medians213-305ms; fresh service+consumer about3.46s; generation1.21MB
([measurements](research/tryfan-pilot-s4-results.json)). Port4191 replaces Fetch-blocked4190;
this is a reversible pilot detail. Production Atlas, Weather, Traverse and frozen contracts
remain unchanged. Appearance remains unresolved/non-blocking and Swiss multiview parked.
The [S5 scoped/mixed-family publication](research/tryfan-pilot-s5.md) now passes **C - S5 SUCCESS**: U1 and isolated U2 activate retained applicability, recompute only two summit revisions, reuse southern/native state and preserve all history. Eight abrupt exits and fresh/pinned HTTP consumers keep old roots coherent; retry reuses identical closed candidates. Actual browser refresh changes the whole scene explicitly. Assembly1.22–1.34s/validation584–651ms/root switch~5ms,1.24MB generations ([observations](research/tryfan-pilot-s5-results.json)). No new source revision or foundational deviation. S1–S4 remain successful. Appearance remains unresolved/non-blocking and Swiss multiview remains parked. The [S6 measured exit](research/tryfan-pilot-s6.md) now records **C - PILOT EXIT ACCEPTED**: all16 original A–P criteria and nine bounded exit gates PASS, independent empty rebuilds and fresh services/consumers reproduce the coherent pilot, and six records replay from retained pixels. The bounded Tryfan pilot is **closed**; S1–S5 remain SUCCESS. [Measured results](research/tryfan-pilot-s6-results.json) retain five fresh runs,20 warm batches and1/4-reader100-request workloads: native query medians263–266ms,4-reader median1.06s,0 errors. Eight repeated interruption cases preserve prior roots. Measurement-only Node metering exposes about31.8MB of synchronous requested reads for a32.8KB WorldCover response; this is not physical disk traffic or a production SLA. No foundational contradiction, runtime change or closure of unresolved science. That recorded next task is now completed by the [measured architecture assessment](research/atlas-measured-storage-processing-serving.md) with **C - ARCHITECTURE DIRECTION ESTABLISHED**. That experiment is now completed with **C - EXPERIMENT RESOLVED**; see the current scaling entry below. That recorded proof is now completed with **C - PROOF SUCCESS**; see the current component-membership entry below. That recorded experiment is now completed with **C - EXPERIMENT RESOLVED**; see the current granularity entry below. That recorded proof is now completed with **C - PROOF SUCCESS**; see the validated-reuse entry below. Exactly one next task is **Atlas retained validation-evidence maintenance and amortization experiment**, not begun. No S7, vendor choice, deployment or post-pilot implementation is authorized by closure.
A6-A11/A14 remain unresolved separately; Swiss pixels remain parked.
Historical analytical filter/calibration
suggestions are separate from closed visual-terrain research. No Weather/Traverse redesign follows.

## Product idea

Meridian is moving toward a terrain-first outdoor journey intelligence system, while retaining the exploratory global weather map as a valuable way to understand the wider atmosphere.

Map weather fields should come from Meridian's immutable global model-field architecture. Point APIs should be reserved for products genuinely tied to one selected location, rather than sampled repeatedly to construct a regional map field.

The central route-planning question is:

> I already have a route. What should I expect along the way, and when?

A route supplies the spatial backbone. A journey model turns that geometry into scheduled positions. Terrain and environmental data then become useful in the context of where the traveller is expected to be at a particular time.

Current implementation establishes global weather exploration, Route Foundation v1, and a first raw route-condition layer. Contextual terrain interpretation, personalised timing, stages, and conditions-adjusted travel remain future work.

## Route-first workflow

The preferred conceptual chain is:

```text
route geometry
  → terrain understanding
  → movement and journey model
  → scheduled position along the route
  → environmental sampling
  → route conditions
  → potential conditions-adjusted journey model
```

The boundaries matter:

- GPX is an input format, not the route domain model.
- Terrain enrichment should not depend on a weather provider.
- Physical movement should remain separate from journey organisation and stops.
- Weather should attach to scheduled route samples rather than remain an unrelated map overlay.
- A later feedback step from conditions into travel time must be transparent and evidence-based, not an unexplained penalty.

## Journey modelling

The physical movement model describes travel over terrain. Journey organisation describes how that movement is arranged.

Potential movement or planning context includes:

- walking, hiking, running, or another explicit travel mode;
- solo or group travel;
- experience and personal calibration;
- load;
- breaks, planned stops, camps, and waypoints.

The model should support both planning directions:

1. Given a route and travel profile, estimate duration and arrival windows.
2. Given a desired duration or finish time, estimate the required pace while retaining terrain-aware relative timing.

Movement time, short breaks, major planned stops, and overnight camps should remain distinct. Predictions should use useful arrival windows rather than imply false precision.

### Stages, not automatic “days”

A long GPX does not imply a multi-day walk. The same geometry could represent an ultra, one long day, several stages, or a much longer itinerary. The internal abstraction should therefore be a **stage**, not an automatically inferred day.

Potential stage controls include:

- number of stages;
- target movement duration;
- desired finish time;
- a selected or dragged route position;
- a named waypoint, camp, bothy, accommodation, or transport deadline.

Useful bidirectional questions include:

- “If I move for eight hours, where might I reach?”
- “If this is the stage endpoint, what arrival window and pace does it imply?”

Stage boundaries also change route × time weather exposure, so they should remain first-class planning decisions controlled by the user.

## Terrain intelligence

Terrain is more than elevation gain. Potential descriptors include gradient, aspect, sustained climbing and descending, rolling relief, ridge/valley form, exposure, local shape, cliffs, and—where suitable external evidence exists—surface or technical character.

An important distinction is now established:

- **Terrain profile** can often be estimated reasonably from GPS geometry plus a DEM: broad relief, gradients, sustained climbs, and vertical range.
- **Terrain surface or technicality** generally cannot be inferred from an approximately 30 m DEM alone.

Consequently:

```text
steep ≠ technical
slow ≠ rough
mountainous ≠ scrambling
```

Potential future surface evidence may include higher-resolution authoritative terrain, OpenStreetMap path/surface data, land cover, geology, mapped route information, or other appropriately licensed datasets. These are candidates, not current capabilities.

### Terrain-resolution research finding

The completed privacy-preserving experiment found that the production-style terrain pipeline materially suppresses repeated small vertical variation. However, sampling the same roughly 30 m Terrarium source at 10–20 m spacing did not independently recover trustworthy extra relief. Denser sampling can merely interpolate the same information.

The useful research question is therefore:

> What spatial filtering best separates genuine relief from DEM noise and interpolation?

It is not simply “How finely can the existing DEM be oversampled?” A future benchmark should compare selected profiles with higher-resolution authoritative terrain and external route evidence before changing production filtering.

A later bounded comparison against the official Welsh Government 1 m bare-earth DTM found that source resolution can materially change a route profile, but the effect varies by route. With the same physically defined filter, cumulative ascent on two private Welsh benchmark geometries was already stable across 1–40 m sampling; one-metre route sampling mainly added diagnostic local variation rather than a better basic ascent total. High-resolution 2D terrain remained valuable for local slope, relief, convexity/concavity, and artefact investigation.

The national Cloud Optimized GeoTIFF also supported efficient range/window reads: an offline route-corridor experiment needed only a small fraction of the national raster. This supports a future provider-neutral **analytical** terrain resolver that can select a suitable authoritative regional source while MapLibre's visual terrain continues to use a global fallback. It does not yet justify production integration, a universal filter change, or direct public-browser access to national rasters.

## Personal journey calibration

With explicit consent, historical activity data could potentially calibrate flat speed, uphill/downhill response, steep-terrain slowdown, fatigue, stop tendencies, or multiple movement regimes.

The preferred approach is interpretable and testable:

- reconstruct movement from timestamps and geographic progression;
- keep movement, stationary recording, pauses, gaps, and anomalies distinct;
- evaluate historical and planned routes against compatible terrain data;
- hold out complete activities rather than splitting neighbouring segments across train/test;
- shrink sparse evidence toward a generic model;
- compare progression through a route as well as final duration.

The first experiment weakened the idea of one universal personal speed curve. A single curve improved some aggregate diagnostics but did not generalise across all movement contexts. No production terrain or timing constant changed.

Possible contextual regimes include walking, hiking, running, trail running, technical terrain, group travel, heavy load, recovery/injury, and difficult conditions. These labels must not be assumed to be passively inferable from activity tracks.

### Activity-context inference finding

The frozen context experiment separated passively observable evidence from context only the user or another source can provide.

Recording plus DEM evidence can sometimes support:

- broad movement behaviour;
- sustained walking/running phases;
- pauses, gaps, and recording-quality evidence;
- large-scale terrain profile.

It generally cannot defensibly establish:

- terrain surface or technicality;
- party composition;
- pack/load;
- environmental conditions;
- injury or intent;
- why a stop occurred.

This suggests three distinct future input classes:

1. **Passively observable data** from the recording and terrain.
2. **User-provided context** such as load, party, intent, injury, or known technicality.
3. **External environmental data** such as forecast weather, ground state, or authoritative hazards.

Calibration v2 has not begun. Any future work should compare frozen recording-derived guesses with independent user annotations before selecting model contexts.

## Privacy as a product principle

Personal data use should be explicit, opt-in, purpose-specific, understandable, inspectable, and revocable where feasible. Possessing data for one feature does not imply permission to use it for another.

For example:

- “Use my activities to calibrate my own journey model” is distinct from
- “Use my activities to improve general Meridian research or models.”

Potential future privacy UX includes consent per purpose, a data-use dashboard, visibility into derived profiles, deletion/reset controls, and local/private processing where practical. These are directions, not claims about the current UI.

## Route conditions

Long-term route intelligence may combine weather, terrain, ground/surface, time, and exposure. It should avoid collapsing evidence into one unexplained risk score.

Prefer answering:

> What is happening, where, when, why, and what evidence supports it?

Candidate factual or derived conditions include:

- temperature, precipitation, wind and gusts;
- cloud, visibility, and terrain-cloud intersection;
- freezing level, snowfall, snow cover/depth, ice, and freeze/thaw;
- recent rainfall, ground saturation, and water crossings;
- slope, aspect, ridge exposure, and solar exposure;
- thunder/lightning-related conditions;
- route-relative headwind, crosswind, and tailwind.

Derived conditions should expose inputs, provenance, resolution, and uncertainty.

Route Conditions Foundation v1 now distinguishes **conditions now**—the map
weather field at one selected forecast time—from **journey conditions** sampled
at each route position's expected arrival time. The route-condition domain keeps
terrain, schedule, raw GFS values, route-relative wind, requested time, actual
forecast valid time, and source provenance distinct. Expected-arrival conditions
are displayed first; the existing earliest/latest arrival window is preserved
for later timing-sensitivity analysis rather than collapsed into an arbitrary
classification.

Route geometry remains visually smooth at its display spacing, while weather
values retain GFS 0.25° information resolution and discrete forecast times.
Precipitation keeps its one-hour interval-total semantics and is not interpolated
as an instantaneous value. Temperature, precipitation, wind, and gradient are
separate route colour modes with physical-unit legends; Meridian does not combine
them into an opaque condition or safety score.

Forecast availability is section-specific rather than all-or-nothing. A journey
may therefore retain valid conditions on covered sections and explicit
unavailability beyond the generated horizon; an expired catalogue must resolve
to unavailable rather than remain in a loading state.

Overlapping and out-and-back passes currently collapse onto the same map
geometry, so later-rendered traversals can visually dominate earlier passes.
This affects directional gradient and time-dependent journey conditions at the
same place. An eventual general pass-aware treatment may use offsets, direction
marks, or pass selection; no such design is settled or implemented.

Early route-use feedback suggests precipitation and gradient may be especially
well suited to continuous colouring. Temperature may ultimately be clearer as
sparse numeric route/time or profile information, while wind may benefit from
numeric values plus direction and route-relative context. These are future UX
hypotheses, not replacements for the existing Temperature/Wind colour modes.

### Snow, ice, avalanche, and cornices

Snow and ice interpretation may eventually combine snowfall, freezing level, snow depth/cover, temperature history, freeze/thaw, elevation, aspect, and wind redistribution.

Avalanche risk should use authoritative forecasts wherever available. In Scotland, the Scottish Avalanche Information Service is a key example. Raw GFS fields plus slope are not a substitute for an authoritative avalanche forecast.

Likewise, ridge + snow + wind may indicate potentially cornice-prone terrain, but Meridian should not claim exact cornice prediction without an appropriate model and data.

### Cloud and visibility

Total cloud cover is useful for broad visualisation. Route planning will benefit more directly from cloud base, visibility, precipitation, elevation, and their uncertainty. “Will this route position likely be inside cloud?” is more actionable than total cloud percentage alone.

### Wind

Current GFS wind is honest large-scale 10 m model wind. Visual improvements remain possible for particle sizing, globe distribution, terrain/depth interaction, and polish.

GFS 0.25° does not resolve mountain-scale airflow around individual ridges and valleys. Any future terrain-aware wind must be labelled as a derived visualisation, downscaling method, or separate model—not silently presented as native GFS detail.

## Global weather architecture and priorities

Preserve the implemented provider-neutral path:

```text
numerical model
  → preprocessing and validation
  → provider-neutral global fields
  → numeric web tiles
  → renderers and inspectors
```

Weather belongs to Earth, not to a temporary viewport sampling rectangle. Overzooming must not imply new meteorological information, and sources must not be silently blended.

Current global GFS fields are precipitation, total cloud cover, 10 m wind, 2 m temperature, mean sea-level pressure, surface gust and visibility, 0°C freezing level, highest tropospheric freezing level, and cloud ceiling. Open-Meteo remains reserved for selected-location point forecasts rather than map-field construction.

Future priorities should follow route usefulness. Candidates include gusts, freezing level, snowfall, snow cover/depth, cloud base, visibility, antecedent precipitation, and convection/lightning-related fields. Availability, semantics, licensing, storage, and honest interpretation must be evaluated before selection.

### Weather publication lifecycle

Weather data updates should remain independent of frontend deployment. Generated model runs use immutable paths, with one small mutable `latest.json` pointer switched only after a complete run validates. A stale but valid published run is preferable to replacing it with a partial or broken update.

Automatic generation requires bounded retention. The local workflow keeps the active complete run and one previous complete run while preserving source caches. The browser watches only catalogue metadata, including when a hidden tab becomes visible, and loads immutable manifests only after a newer complete pointer appears. It must not poll weather tiles or clear working renderers merely to check freshness. Production scheduling, storage and monitoring remain separate deployment decisions.

## Stage endpoints and live landscape information

### Potential stage-end or camping terrain

A future tool could identify terrain that appears **potentially suitable** for stopping or camping. It should never instruct “Camp here.”

Candidate evidence includes local slope and contiguous flat area, elevation, exposure, forecast wind/weather, rainfall and wetness, streams/flood risk, land cover, cliffs, access restrictions, and distance/time along the route.

Physical suitability must remain separate from legality, access, environmental appropriateness, and user judgement. Link to authoritative local guidance where possible.

### Live landscape events

Potential route intelligence includes wildfires, path closures, landslips, bridge failures, flooding, reopenings, access restrictions, and temporary hazards. Prefer authoritative sources and retain geometry, provenance, freshness, and confidence/status.

If a route intersects an issue, do not silently reroute it. Explain the affected section, optionally present alternatives with distance/ascent/time/weather implications, and let the user decide.

## Specialist services and ecosystem

Meridian should not pretend to replace every specialist outdoor service. It can integrate or deep-link to authoritative and specialist sources while respecting licensing and terms.

Examples include Met Office mountain forecasts, SAIS, Walkhighlands, and country-specific mapping services such as swisstopo. The principle is:

> Here is Meridian's analysis, where it came from, and the relevant specialist evidence.

Merlin Maps remains a separate hiking-routing project. A useful conceptual distinction is “Where do I go?” versus “What conditions will I encounter?” Possible integration remains undecided and requires an explicit decision with its owner; do not assume shared code, ownership, or product direction.

## Visual and rendering direction

Retain the FATMAP/mapped.earth-inspired ambition for legible terrain-first exploration without copying another product. MapLibre remains the geographic and navigation engine; custom renderers can progressively handle scalar, vector, terrain-derived, and atmospheric fields.

Potential reusable concepts include `ScalarFieldRenderer`, `VectorFieldRenderer`, and `TerrainFieldRenderer`, introduced only when real implementation reuse justifies them.

Visualisation can be expressive without falsifying data:

> Never invent the underlying meteorology, but do not be afraid to invent the pixels used to communicate it.

Wind particles are not literal tracked air parcels. Future procedural cloud detail could be visually generated while constrained by honest cloud amount, altitude, and motion. Data, interpolation, derivation, and stylisation must remain distinguishable.

## Desktop information architecture

Meridian remains map-first: desktop navigation should preserve the map as the dominant surface and avoid using a long page-level sidebar as the route between core workflows. Location exploration and Journey planning are parallel workspace contexts. Switching context changes presentation only; it must not discard a route, selected location, journey assumptions, forecast state, overlays, or camera state.

Map-display controls belong with the map. Journey keeps a compact route profile and overview; detailed elevation, condition and arrival-time evidence opens in the reusable secondary Workspace. Clear-map mode should remove substantial interface chrome without changing analytical or map state. The Meridian mark is the persistent way back from a map-focused state.

Global preferences and journey assumptions are different scopes. Global settings cover application behavior such as the optional Map Inspector; journey settings change the schedule and expected-arrival context for one route. Both use progressive disclosure rather than permanent dashboard space.

On desktop, the left primary workspace keeps a stable, full-height geometry across Location and Journey. Meridian should first reduce padding, use available space and make successful states terse before hiding related information behind extra views; clicks have a cost, and desktop navigation should not depend on scrolling. Journey tuning is an in-panel subview so it retains the workspace context without becoming floating map chrome.

Route analysis uses the same secondary Workspace shell as Forecast and remains owned by the Journey context. Its modes express the user's question—elevation, temperature, rain, wind or gradient—rather than a GIS-style “route colour” property. Hover previews a journey position and click pins it for comparison with the map and detailed evidence. Map layers belong in persistent lightweight map-native controls rather than a second sidebar.

The primary workspace should remain a compact overview and control surface. Deeper tasks belong in one reusable secondary **Workspace** beside it: a large map-aware instrument surface rather than a modal, page or second permanent sidebar. Location Forecast and Journey Route Analysis now share this shell. Linked 2D route, 3D terrain and elevation exploration may extend it later without creating simultaneous competing workspaces.

Forecast detail should be organised by time. One horizontal daily domain and one shared preview/pin selection apply across all variables; a committed time synchronises with the map forecast, while hover remains a local preview. Future sunlight bands can enrich that axis when reliable astronomy data exists. Future map capabilities such as contours, zoom-responsive grids and a scale indicator remain separate deferred work.

Journey summaries should lead with relevant conditions and honest extremes, then reveal exhaustive raw values and technical caveats on demand. Route measurements, derived journey estimates, raw forecast values, route-relative context, derived interpretation, and visual presentation remain distinct. Complete coverage needs no engineering label; incomplete coverage should be expressed in human spatial or temporal terms where the evidence permits.

## Source, inference, and decision principles

- Prefer authoritative data where available.
- Make provenance visible and label derived inference as derived.
- Communicate uncertainty explicitly.
- Do not imply finer spatial or temporal resolution than the source provides.
- Do not silently mix sources or fabricate intermediate forecast times.
- Do not turn uncertainty into precise-looking scores.
- Keep consequential route choices under user control.
- Treat absence of evidence as unknown, not evidence of normality or safety.
- Preserve specialist warnings rather than replacing them with a general model.

## Raw atmospheric context before interpretation

Environmental Enrichment v1 keeps gust, model visibility, both freezing-level
heights and experimental cloud ceiling as raw model fields attached to expected
arrival times. No weather-adjusted timing or hazard inference follows from
their presence. In particular, cloud ceiling is not cloud base; ceiling above
the model surface cannot be compared directly with route elevation above sea
level. A freezing level is not an ice detector. Multiple freezing crossings
remain distinct rather than being silently collapsed.

GFS 0.25° resolution must stay explicit: dense route sampling adds journey-time
context, not local meteorological detail. Not every environmental quantity
needs a map layer or route colour mode. Atmospheric heights may later be useful
on the elevation/time profile once reference levels and missing/no-ceiling
states can be presented clearly. Derived cloud intersection, icing or other
conditions require a separate, transparent evidence-based design.

## Transparent derived route context

Keep raw forecast, route context and interpretation separate. Derived context
must resolve back to the original sample's terrain, expected arrival and field
provenance, fail independently when inputs are unavailable, and never silently
feed back into movement time. Expected-arrival context comes before any future
arrival-window environmental analysis.

Freezing-level separation is atmospheric context, not ice or snow prediction;
multiple levels limit any simple boundary interpretation. Route-relative wind
is coarse forecast airflow projected onto the direction of travel, not terrain
downscaling. Gust magnitude does not supply a direction. Model visibility is
not exact human sight distance, and cloud ceiling is not cloud base or proof of
cloud immersion. Reference frames must be compatible before comparing heights.

Use explainable evidence, approximate wording and honest coverage gaps rather
than an opaque risk score. Atmospheric-height lines can help explain route
progress without adding map layers, but must preserve GFS resolution, multiple
level caveats, and the readability of the underlying elevation profile.

## Open research questions

- Which route × time conditions provide the greatest planning value?
- What terrain filtering is defensible against authoritative high-resolution benchmarks?
- Which movement contexts can be inferred, and which must be user-supplied?
- Can contextual personal calibration improve held-out long and high-ascent journeys without hiding failure modes?
- How should stages, explicit stops, and uncertainty interact?
- Which weather fields justify the preprocessing/storage cost for route use?
- How can route-condition explanations remain useful without becoming a false safety score?
- Which specialist datasets permit integration or linking under their current terms?

## Analytical terrain research direction

Controlled experiments with authoritative one-metre DTMs in Wales and England
support a provider-neutral analytical terrain direction, separate from visual
MapLibre terrain. Regional sources can be accessed as bounded route corridors
through different delivery mechanisms—COG byte ranges or WCS coverage
subsets—behind the same projected numeric sampling boundary, without mirroring
national rasters.

The cross-region evidence does not support a universal high-resolution ascent
correction. Source effects are route-dependent, filtered ascent is generally
stable across practical sampling intervals, and one-to-two-metre route sampling
mostly adds raw variation rather than trustworthy basic ascent. Five-to-ten
metres remains useful for research into local structure, while 10–20 m slope
and 50–200 m relief/landscape-position measures are more interpretable than
micro-roughness. Flat terrain requires special care because small absolute
changes can appear large proportionally.

A future analytical terrain resolver should therefore select an authoritative
regional source when available, retain a global fallback, enforce provider
rights and bounded access, distinguish coverage from numerical zero, express
filters in physical distance, expose provenance, and permit raw raster blocks
to be discarded after compact route features are derived. Production constants
and integration remain undecided.

## Approaches currently rejected or weakened

- Oversampling the current DEM as if it creates higher-resolution terrain truth.
- Treating activity labels, provider moving time, or a universal minimum speed as calibration truth.
- Inferring surface technicality, party, load, or conditions from slow/irregular movement alone.
- Using one opaque personal model before interpretable contextual evidence is validated.
- Automatically dividing long routes into “days.”
- Presenting GFS wind as ridge-scale airflow.
- Replacing authoritative avalanche or access information with generic inference.
- Silently rerouting a user's plan around detected issues.

These positions can change if future evidence justifies it. If they do, record the evidence and decision rather than removing the earlier reasoning.

## Free-first world evidence hierarchy

Meridian Earth should establish a reproducible free global baseline before treating
commercial or specialist data as an enhancement. Global observations such as
Sentinel-2 supply scalable, time-stamped spectral evidence at their honest native
resolution. Regional public sources such as Welsh Government one-metre LiDAR can
then improve measured geometry where available. Commercial imagery or specialist
surveys may later improve particular places, but must remain optional evidence
providers rather than hidden requirements for the baseline world model.

The catalogue must preserve whether a quantity was measured, derived from measured
geometry, observed at 10 or 20 metres, interpolated for display, or procedurally
reconstructed. A higher-resolution display grid never upgrades the resolution of its
source evidence. Terrain and spectral observations are complementary inputs; neither
should be silently promoted into a surface-material classification without supporting
evidence and explicit uncertainty.

## 2026-10-08 - Atlas measured storage, processing and serving architecture

The [measured architecture assessment](research/atlas-measured-storage-processing-serving.md) records **C - ARCHITECTURE DIRECTION ESTABLISHED**. The Tryfan pilot remains **CLOSED / ACCEPTED** at `bae7c3e`; S1–S5 remain SUCCESS and S6 remains **C - PILOT EXIT ACCEPTED**, with all16 cases/nine gates intact. **DECIDE NOW:** immutable source/result identity, native qualifications/rights/actual-use dependencies, scoped freshness, validated publications and generation-pinned isolated consumers. **PROVISIONAL DIRECTION:** immutable payload objects plus one shared structured/indexable metadata catalogue, component-reference manifests, separate bulk/query responsibilities and finite local/batch processing. **DEFER PENDING EVIDENCE:** database/vendor, component/shard size, multiple writers, remote durability, packing/CDN/deployment, graph/cardinality and dynamic cadence. **REJECT:** semantic flattening, latest-only/path identities, blanket invalidation, copy-world publication, cache-only lineage and unjustified service/workflow fleets.

S6 measured31.8MB synchronous requested Node reads per32.8KB WorldCover response;1/4-reader throughput~3.8requests/s with higher four-reader latency. These are bounded warm-cache observations, not physical disk/egress or production capacity. The assessment extracts existing receipts only and implements no architecture. Exactly one next bounded task: **Atlas retained generation metadata read-amplification and verified-reuse scaling experiment**; not begun. Appearance remains unresolved/non-blocking, Swiss multiview remains parked and all42 historical research statuses are unchanged.


## 2026-10-08 - Atlas retained-generation scaling experiment

The [retained-generation experiment](research/atlas-generation-scaling.md) records **C - EXPERIMENT RESOLVED**. The Tryfan pilot remains **CLOSED / ACCEPTED**, S1–S5 remain SUCCESS, S6 remains accepted and the architecture direction remains established. [Frozen baseline](research/atlas-generation-scaling-baseline.json), [measurements](research/atlas-generation-scaling-results.json), [decision updates](research/atlas-generation-scaling-decisions.json) and [validation](research/atlas-generation-scaling-validation.json) retain the evidence. All 18 primary cases use the original scientific state at 7/28/112 generations, with five fresh processes and 20 repeated requests each; six historical pins and seven labelled metadata-only controls distinguish resolution, verification, footprint and publication costs.

At 112 generations, one historical query requests 25,016 generation reads / 29.77 GB of metadata, taking about 299 seconds. Request-scoped verified reuse reduces this to 112 reads / 136 MB / 5.8 seconds, while whole parsed ancestry raises observed memory use. These are local requested-read observations, not physical disk traffic, production capacity or payload-scale evidence. **DECIDE NOW:** separate cost classes and retain integrity, qualification, identity, history and pins. **PROVISIONAL DIRECTION:** shared immutable metadata components, lightweight publication manifests and bounded membership resolution. **DEFER PENDING EVIDENCE:** exact component/index/checkpoint strategy, spatial selectivity, distinct revisions, infrastructure and distributed guarantees. **REJECT:** repeated whole-ancestry closure validation as the interactive default, trusted mutable-path caches, skipped checks and unjustified infrastructure.

At the e88b575 checkpoint, the recorded next bounded task was **Atlas retained component-manifest and publication-membership resolution proof**. It is now completed by the entry below, preserving scientific qualification and rejection of unpublished state with a bounded retained applicability transition. Accepted pilot/source/frozen/production files and all 42 historical research statuses remain unchanged. Appearance remains unresolved/non-blocking and Swiss multiview remains parked. No S7, production implementation or new evidence.


## Atlas component-manifest and publication-membership proof

The [retained proof](research/atlas-component-membership.md) records **C - PROOF SUCCESS**. Tryfan remains **CLOSED / ACCEPTED**, S1–S6 remain intact, and the measured architecture direction remains established. The [e88b575 scaling evidence](research/atlas-generation-scaling.md) remains authoritative. Current/recent/oldest access at 7/28/112 publications reads 33 committed membership records, one publication and five shared components when hydrated, with zero publication ancestry traversal. Qualified WorldCover/composed-evidence/provenance answers match the prior experiment.

The exact retained U1 lifecycle recomputes only two summit results and reuses two southern results; ten pixel replay checks are exact. Original separate consumers remain pinned while a new generation publishes. Two abrupt exits leave old state current and complete pre-switch candidates ineligible. [Measurements](research/atlas-component-membership-results.json), [decisions](research/atlas-component-membership-decisions.json) and [regression receipt](research/atlas-component-membership-validation.json) retain the proof.

DECIDE NOW: bounded explicit publication membership, coherent current/eligibility commitment and fresh selected-closure verification. PROVISIONAL DIRECTION: shared immutable component metadata with a bounded membership witness. The byte-radix witness is not a production index choice. Unselected archived publications are independently verified when selected/audited, rather than automatically traversed as current dependencies. At 112 publications, shared component/publication/index metadata is 2.582 MB versus 141.241 MB whole snapshots/locators. No hidden component ancestry is observed; coarse interior metadata duplication and 33 new small index nodes per publication remain explicit costs.

DEFER PENDING EVIDENCE: component granularity/selective reads, metadata-cardinality scaling, exact database/index/compaction technology, remote durability and concurrency. REJECT unbounded ancestor closure as normal eligibility, existence-as-publication, hidden delta chains and weakening qualification/integrity. Appearance remains unresolved/non-blocking and Swiss multiview parked. All 42 historical research statuses remain unchanged.

At the `97c31c8` checkpoint, the recorded next task was **Atlas retained component granularity and selective metadata-read scaling experiment**. It is now completed by the experiment below. It tests selective metadata reads and component boundaries using isolated retained-semantic populations, without new evidence, physical methods or production infrastructure. No S7 or post-proof implementation. The checkpoint is the commit introducing this report/navigation entry.

## Atlas component granularity and selective metadata-read experiment

[Measured report](research/atlas-component-granularity.md) records **C - EXPERIMENT RESOLVED** from clean `97c31c8`. Tryfan remains CLOSED / ACCEPTED and the architecture direction remains established. [e88b575](research/atlas-generation-scaling.md) and [97c31c8](research/atlas-component-membership.md) remain authoritative and unchanged. [Frozen plan](../scripts/atlas/component-granularity/plan.json), [results](research/atlas-component-granularity-results.json), [decisions](research/atlas-component-granularity-decisions.json) and [validation](research/atlas-component-granularity-validation.json) preserve this bounded experiment.

148 query cases, 48 scoped metadata updates and 24 historical pins compare whole, 64-record spatial partitions, flat one-record components and authenticated key-ordered internal lookup. At 2,048 terrain records, a narrow moderate query inspects 64 records / 25,715 requested bytes; fine inspects one but requests 263,232 bytes through its flat directory. Broad fine reads 2,083 objects versus 36 whole. Spatial inventory queries favour spatial partitions; feature-ID queries favour key lookup. All 172 query/history observations retain 33 eligibility reads and zero ancestry. No hidden component ancestry appeared.

DECIDE NOW N11/N12: separate membership, logical identity, selective organisation and integrity/completeness cost; count directories and shared qualifiers. PROVISIONAL DIRECTION P08: family/access-specific moderate partitions or selective internals, not a universal size/tile scheme. DEFER D08: exact sizes/backend, real 2D/cardinality, dual lookup and safe incremental validation. REJECT R08: blanket one-record flat membership, universal geographic partitioning, whole-family-only hydration and weakened qualification/integrity. Scoped writes reuse immutable interiors, but every construction and publication audit still visits all 2,048 records. No database/cloud/index product is selected or implemented.

At `38f9ba7`, the next task was **Atlas retained validated-component reuse and incremental publication-validation proof**. It is now completed by the proof below; its conclusions and original measurements remain authoritative. Test reusable validation receipts/changed-path references against full closure while preserving corruption detection, completeness, historical identity and coherent publication. No accepted pilot, retained source, frozen contract, production Atlas, Weather or Traverse change; all 42 historical research statuses and 113 protected hashes remain intact. Appearance remains unresolved/non-blocking and Swiss multiview parked. No S7, new data/methods or production-service readiness work. This entry’s introducing commit is the experiment checkpoint.

## 2026-10-08 - Atlas validated-component reuse and incremental publication-validation proof

[Durable report](research/atlas-validation-reuse.md) records **C - PROOF SUCCESS** from clean `38f9ba7`. Tryfan remains **CLOSED / ACCEPTED**, S1-S5 remain SUCCESS, S6 accepted, and the architecture direction remains established. [e88b575](research/atlas-generation-scaling.md), [97c31c8](research/atlas-component-membership.md) and [38f9ba7](research/atlas-component-granularity.md) remain authoritative. [Frozen plan](../scripts/atlas/validation-reuse/plan.json), [check inventory](../scripts/atlas/validation-reuse/inventory.json), [results](research/atlas-validation-reuse-results.json), [decisions](research/atlas-validation-reuse-decisions.json) and [validation](research/atlas-validation-reuse-validation.json) retain the evidence; the introducing commit is this proof checkpoint.

All 46 measured proposals (29 valid/17 invalid) agree with full validation. At 192 components / 12,288 synthetic records, a localized fan-out-one update validates 128 rows and one relationship instead of 12,288/64. Trusted receipts skip semantic work only: every current component is still hashed, completeness and membership comparisons still scan all slots, and receipt lookup increases reads from 193 to 387. The final measured timing distribution is in the report. Rule changes disable local reuse; context changes rerun relationships; bad reuse evidence falls back to full validation. Stale historical claims remain valid. Six historical pins retain 33 eligibility reads and zero ancestry; four abrupt pre-switch exits preserve the previous root, and retries/pinned history remain coherent.

DECIDE NOW N13/N14: exact content/rule/trust/scope binding, contextual versus current-integrity separation, mandatory completeness/root checks and honest residual accounting. PROVISIONAL DIRECTION P09: qualified local receipts and trusted reverse relationship buckets, with full oracle/fallback. DEFER D09: evidence issuance/maintenance amortization, packing, general graph/rights/applicability and deployed trust/backend choices. REJECT R09: permanent valid booleans, candidate trust, skipped current integrity/context/completeness, stale-as-false and hidden population/ancestry work. No production validator adopts the shortcut; evidence preparation and the builder still visit the full population.

Exactly one next bounded task: **Atlas retained validation-evidence maintenance and amortization experiment**; **NOT BEGUN**. Compare full evidence reissuance with safe immutable receipt/affected-bucket carry-forward across repeated localized publications, keeping oracle equivalence, corruption/context/rule/history/publication checks. Measure end-to-end costs before adoption. No backend, production issuer, evidence/method change or service-readiness work. Accepted pilot/sources/frozen contracts, all 42 historical statuses and 113 protected production hashes remain unchanged. Appearance remains unresolved/non-blocking and Swiss multiview parked. No S7.
