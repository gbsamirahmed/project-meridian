# Meridian product and research direction

## Purpose and status

This document is Meridian's living design and research notebook. It records product direction, candidate capabilities, hypotheses, unresolved questions, and approaches that evidence has weakened or rejected. It is not a delivery roadmap or a promise that every idea will be implemented.

- `README.md` describes what currently works and how to run it.
- `docs/development-log.md` records completed implementation and research milestones.
- Source code remains authoritative for implementation details.

Terms such as **direction**, **candidate**, **potential**, **research question**, and **not yet implemented** are deliberate. When an experiment changes a decision, retain the hypothesis → experiment → finding → decision trail rather than rewriting history.

## Product idea

Meridian is moving toward a terrain-first outdoor journey intelligence system, while retaining the exploratory global weather map as a valuable way to understand the wider atmosphere.

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

Current global GFS fields are precipitation, total cloud cover, 10 m wind, and 2 m temperature. Pressure remains regional/legacy, but being the final unmigrated map variable does not automatically make it the highest-value next migration.

Future priorities should follow route usefulness. Candidates include gusts, freezing level, snowfall, snow cover/depth, cloud base, visibility, antecedent precipitation, and convection/lightning-related fields. Availability, semantics, licensing, storage, and honest interpretation must be evaluated before selection.

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
