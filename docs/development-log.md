# Meridian development log

This is Meridian's concise chronological engineering history. Entries record substantial engineering milestones rather than individual commits or pushes, and dates normally indicate when a milestone was completed or recorded. The first prototype-foundations entry is a retrospective summary of earlier development: its date records when that summary was written, not Meridian's start date or the implementation date of every feature it lists. Implementation details remain authoritative in source code, and exploratory ideas remain distinct from settled decisions.

## 2026-08-30 — Prototype foundations and rendering milestones

### Goal

Summarise the important architectural work that preceded the global-weather migration.

### Changes

- Established the React, TypeScript, Vite, MapLibre, OpenFreeMap, globe, navigation, and Terrarium terrain foundation.
- Added the local Open-Meteo 9×9 forecast prototype, universal inspector, timeline, cloud and precipitation surfaces, temperature contours, pressure isobars, and animated wind.
- Made hillshade permanent, separated terrain and analysis DEM source roles, retained `igor` shading and a non-zero close-range hillshade floor, and documented the z15 analysis ceiling and underlying approximately 30 m EU-DEM limitation.
- Replaced static wind arrows with a custom MapLibre WebGL particle layer driven by interpolated vectors.
- Added settled-camera debounce, cancellation, bounded regional caching, last-valid-field reuse, retry/backoff, persistent renderers, and viewport-aware labels.
- Replaced giant local weather images with double-buffered generated raster-tile surfaces to stabilise zooming, without disguising the 9×9 information limit.
- Added a replaceable MapTiler `satellite-v2` provider and made Satellite a permanent basemap concept with no analytical hillshade.
- Reduced the basemap model to Terrain/Satellite and made Elevation, Precipitation, Cloud, Temperature contours, Pressure isobars, and Wind independent overlays.

### Architectural decisions

Meridian is terrain-first and map-first. Visual effects may be stylistic, but their meteorological meaning must remain honest. The local 9×9 field is transitional; weather rendering should migrate toward numeric global model fields without reverting overlays to mutually exclusive views.

### Known limitations

Terrain detail remains bounded by current DEM data. Open-Meteo map fields remain coarse and region-limited. Satellite depends on a configured client-visible MapTiler key.

### Verification

The milestones were repeatedly checked with lint, production builds, browser interaction, desktop/mobile layouts, and terrain/weather layer combinations.

### Next direction

Prove one global numeric precipitation field before migrating other variables.

## 2026-08-30 — Global GFS precipitation proof of concept

### Goal

Render one real NOAA GFS precipitation run as a numeric Earth-wide field that remains fixed while the user pans, zooms, changes basemap, and advances forecast time.

### Changes

- Added `scripts/weather/build_gfs_precipitation_poc.py` and preprocessing requirements for indexed NOAA download, ecCodes decoding, interval derivation, numeric tiling, manifest generation, and validation.
- Generated GFS run `2025082900`, +1 through +12, as 1,020 z0–z3 uint16 packed-PNG tiles (18.70 MiB).
- Added provider-neutral run/source types, manifest loading, a bounded 96-tile decoded cache, geographic scalar sampling, and a persistent double-buffered global precipitation MapLibre layer.
- Made GFS the explicit precipitation owner when its manifest is present; Open-Meteo remains responsible for all unmigrated variables and legacy fallback.
- Added GFS provenance, accumulation interval, dynamic 12-step timeline, and numeric GFS values to the panel, legend, map badge, and point inspector.

### Architectural decisions

The browser receives numeric values, not a baked palette. Packed lossless PNG stores uint16 values at 0.01 mm scale, with encoding declared in the manifest. The canonical 0.25° field is deterministically tiled through z3 and then overzoomed; display zoom never creates meteorological detail. Run/time URLs are immutable, and GFS filenames and GRIB semantics stop at preprocessing.

### Known limitations

This is one fixed historical run with 12 hours, no scheduled updates or production host. Web Mercator excludes the poles. The packed-PNG decoder colourises tiles on the main thread. Other variables still come from the live local Open-Meteo prototype, so cross-provider valid-time coordination is incomplete.

### Verification

Validated 1440×721 source grids, hourly interval metadata, no substantive negative precipitation, min/max values, duplicate APCP records, representative source/export samples, and antimeridian wrapping. Browser-tested Britain, Europe, North America, Japan/East Asia, the Pacific antimeridian, Terrain/Satellite, forecast playback, point inspection, and 390×844 mobile. Lint, production build, and diff checks were run.

### Next direction

Turn the local proof into a small scheduled/static publishing pipeline and resolve production encoding, hosting, retention, and cross-source timeline policy before migrating cloud.

## 2026-08-30 — Latest usable GFS run and 24-hour precipitation

### Goal

Replace the fixed historical GFS proof with a reproducible local update that publishes the newest verified usable run and approximately the next 24 hours of precipitation.

### Changes

- Extended the existing generator to discover recent NOAA archive dates, probe candidate cycles through f024, reject incomplete runs, and fall back newest-first.
- Generalised APCP derivation around the intervals present in each inventory, including direct one-hour messages and differences between accumulations with a shared six-hour bucket start.
- Expanded output to +1 through +24, retained immutable run assets, enriched validation metadata, and made `latest.json` an atomic, schema-versioned publication pointer.
- Tightened the frontend pointer/manifest consistency checks and removed the silent Open-Meteo precipitation fallback when GFS metadata is unavailable.
- Made the first GFS timeline selection prefer the earliest generated valid time that is not already past, while retaining every generated step.

### Architectural decisions

“Latest” means the latest fully verified usable cycle, not the nominal current cycle. Run assets remain immutable; only `latest.json` is mutable. The immutable manifest owns valid-time and accumulation semantics. Failed or incomplete updates never replace the last working pointer. GFS generation remains a manually invoked local/development workflow.

### Known limitations

There is no scheduler, hosted tile publication, automated retention, or production monitoring. Only precipitation has migrated; no ensembles are present, and GFS 0.25° remains approximately a 25 km information source. Cross-provider timeline coordination with Open-Meteo remains transitional.

### Verification

At 2026-08-30 19:42 UTC, the updater rejected GFS 18Z because f024 was unavailable and selected the complete 12Z cycle. It generated 24 hourly timesteps from 13:00 UTC on 30 August to 12:00 UTC on 31 August, 2,040 tiles, and 36.53 MiB of tile payload. All source grids were 1440 × 721; no negative interval values required clamping. Lint and production build passed; browser and final diff validation are recorded in the task report.

### Next direction

Normal Meridian feature development is intentionally paused. The next task should be a separate portfolio/public-GitHub assessment and cleanup, not another feature expansion.

## 2026-08-31 — Public repository readiness cleanup

### Goal

Prepare Meridian for a controlled public repository review without adding product features or changing its terrain and weather architecture.

### Changes

- Reworked the README around a concise project explanation, engineering highlights, reproducible setup, honest limitations, data provenance, and licensing status.
- Added runtime credit for Open-Meteo, Nominatim/OpenStreetMap search data, and the Terrarium dataset chain while preserving source-provided OpenFreeMap, MapTiler, and GFS attribution.
- Routed search and reverse geocoding through one one-request-per-second Nominatim coordinator with bounded session caching and cancellation of obsolete requests.
- Excluded generated GFS runs and `latest.json` from Git while retaining every local dataset; documented the clean-checkout unavailable state and generation command.
- Added an explicit Node engine range, repository line-ending policy, and removed verified unused starter/experimental assets.

### Architectural decisions

Generated model runs remain reproducible local products rather than a rotating source-controlled weather archive; the public repository exposes the preprocessing pipeline instead. A missing GFS dataset is an explicit, non-fatal state and never changes precipitation ownership. Runtime provider credits live with the map/data source wherever practical. Public Nominatim use remains user-triggered, centrally rate-limited, cached, and replaceable. No map, terrain, or weather feature architecture changed in this cleanup.

### Known limitations

There is still no hosted GFS publication pipeline or live deployment configuration. The JavaScript production bundle remains comparatively large, browser automation is not part of the checked-in test suite, and the repository intentionally has no open-source licence.

### Verification

The cleanup was checked with the Python preprocessing tests, ESLint, the production build, `git diff --check`, ignored-file validation, credential/privacy scans, desktop browser interaction, and a temporary no-GFS-data browser run. The responsive CSS breakpoint was reviewed separately because the available browser viewport override did not apply reliably.

### Next direction

Keep normal feature development paused. The next portfolio steps are visual-asset capture, an optional static-deployment assessment, and a final Git/publication review.

## 2026-08-31 — Global GFS total cloud cover

### Goal

Move the map-level Cloud cover overlay from the regional Open-Meteo sample field to the global provider-neutral NOAA GFS architecture without changing wind, temperature, pressure, or point-current-weather ownership.

### Changes

- Extended the local GFS builder to select exact instantaneous `TCDC:entire atmosphere` records for f001–f024 while reusing each forecast inventory already fetched for precipitation.
- Added lossless uint8 cloud tiles (0–100 percentage points in red; 255 no-data), scalar manifest schema v2, and an atomic multi-field `latest.json` catalogue with independently publishable precipitation and cloud entries.
- Generalised browser manifest loading, numeric decoding/sampling, and the double-buffered scalar surface lifecycle so cloud and precipitation render simultaneously with independent state and crossfades.
- Removed cloud and precipitation from the regional map grid request and inspector ownership. Open-Meteo still supplies regional temperature, pressure, and wind plus selected-location current conditions.
- Made the forecast timeline use one active global field's valid times or the exact intersection when precipitation and cloud are both enabled.

### Architectural decisions

Global map cloud means instantaneous GFS total cloud cover for the entire atmosphere. Averaged and layer-specific TCDC are rejected. Field catalogue entries publish independently and retain their real run metadata; no failed or absent GFS field silently falls back to the regional map grid. Rendering remains numeric and stylistically restrained, with no inferred altitude, procedural texture, or volumetric geometry.

### Known limitations

Cloud is a 0.25° total-column fraction, not a depiction of individual cloud bodies or vertical layers. The uint8 cloud field is larger than sparse precipitation under PNG compression. Generation is still a manually invoked local workflow, the horizon is +24 hours, and temperature/pressure/wind remain regional Open-Meteo fields.

### Verification

The live updater rejected incomplete GFS 2026-08-31 18Z and selected 12Z. It generated 24 cloud timesteps, 2,040 tiles, and 51.93 MiB of cloud tile payload with validated 0–100% values. Deterministic tests covered exact TCDC selection, averaged/wrong-layer rejection, no-data versus zero, byte-exact encoding, and independent catalogue updates. Browser checks covered Terrain, Satellite, globe and regional views, combined overlays, playback, inspector provenance, Fiji near the antimeridian, and a genuine 390×844 viewport. ESLint, production build, Python tests, and diff checks were run.

### Next direction

The shared scalar path makes global temperature/pressure technically straightforward, while the next highest-value architectural migration is global vector wind. Low/mid/high cloud should precede any procedural or volumetric-looking cloud work.

## 2026-09-01 — Global GFS 10 m wind

### Goal

Move map-level wind and wind inspection from the regional Open-Meteo sample field to a global, provider-neutral NOAA GFS vector field while retaining Meridian's established particle presentation.

### Changes

- Extended the local GFS build to select paired instantaneous `UGRD`/`VGRD` records at 10 m for f001–f024, validate earth-relative vector metadata, and publish independently validated immutable wind assets.
- Added a lossless RGB representation containing two biased 10-bit components at 0.2 m/s scale, with paired code zero reserved for no-data.
- Added vector manifest/timestep contracts, field-catalogue discovery, exact packed-tile decoding, a shared byte-bounded scalar/vector tile cache, viewport/globe tile preparation, geographic vector sampling, and inspector values.
- Made the WebGL wind layer projection-aware for both globe and Mercator and replaced forecast-vector interpolation with a visual crossfade between separate particle populations sampling exact timesteps.
- Removed wind from the regional map-grid request and map inspector ownership. Open-Meteo remains responsible for selected-location current conditions plus regional temperature and pressure.
- Added `scripts/weather/build_gfs_weather.py` as the canonical local multi-field generation command.

### Architectural decisions

GFS 10 m wind is stored as paired eastward/northward components, never speed/direction. U/V components are bilinearly interpolated spatially before speed and meteorological “from” direction are derived. Wind, cloud, and precipitation publish independently through one catalogue and use exact valid-time intersections when combined. A missing GFS wind field never silently falls back to regional map wind.

### Known limitations

Wind retains GFS 0.25° information resolution despite smooth interpolation and overzooming. Close-zoom particles remain smaller than desired; pitched terrain can make traces appear too close to or below the surface, and globe-scale distribution can concentrate near the visible limb before redistributing during rotation. Particle motion does not interact with terrain-scale topography and will need further visual refinement. Generated wind tiles are relatively large under PNG compression. The pipeline remains manually invoked, spans +24 hours, clips to Web Mercator latitude limits, and has no production host or scheduler.

### Verification

The live builder selected GFS 2026-08-31 18Z and generated 24 wind timesteps, 2,040 tiles, and 103.85 MiB of wind tile payload. Values covered U −42.98…41.39 m/s, V −40.37…42.11 m/s, and speeds up to 43.44 m/s. Deterministic tests cover exact inventory selection, paired metadata, earth-relative vectors, packed-code round trips, paired no-data, antimeridian continuity, and independent catalogue publication. ESLint, the production build, local HTTP asset checks, and diff validation were run.

### Next direction

The closest architectural follow-up is global temperature and pressure using the established numeric field catalogue and cache. Low/mid/high cloud layers should be considered before procedural cloud presentation; neither requires changing wind ownership.

## 2026-09-01 — Global GFS 2 m temperature

### Goal

Move map-level temperature contours and inspection from the regional Open-Meteo sample field to an honest global NOAA GFS 2 m temperature field without adding a filled heatmap or terrain downscaling.

### Changes

- Extended the GFS builder to select exact instantaneous `TMP:2 m above ground` records for f001–f024, validate run/grid/time metadata, convert Kelvin to Celsius, and publish independently staged temperature assets.
- Added 0.1 °C uint16 numeric tiles with a −150 °C offset and 65535 no-data code, plus strict scalar-manifest/catalogue loading and shared-cache sampling.
- Replaced regional 9×9 temperature contours with atomically prepared, viewport-aware isolines generated over one continuous padded numeric sampling domain; globe mode prepares complete z2 coverage so rotation does not drive tile-boundary rebuilds.
- Added stable zoom/range contour intervals, no-data-aware and linear-time contour assembly, global inspector provenance, and exact valid-time intersection with other enabled GFS fields.
- Made the regional Open-Meteo map grid pressure-only. Point current conditions remain unchanged.
- Renamed the implementation module to `gfs_weather_builder.py`; the canonical multi-field command and historical precipitation filename remain small entry-point wrappers.

### Architectural decisions

Map temperature means raw instantaneous GFS 2 m temperature at 0.25° resolution. No lapse-rate correction or terrain-scale modelling is applied. Storage tiles are loading units only: contours are generated from a logically continuous geographic scalar domain after every required tile is ready, and stale camera/timeline generations cannot replace the active geometry.

### Known limitations

The 0.25° model does not resolve terrain-scale temperature variation, and close zooms only interpolate/overzoom the same field. Globe contours intentionally use coarser prepared z2 delivery coverage and broad intervals. Contour generation remains on the main thread, the horizon is +24 hours, and generation/publication is still manually invoked.

### Verification

The live builder rejected unavailable 18Z and 12Z cycles and selected GFS 2026-09-01 06Z. It generated 24 temperature timesteps from 07:00 UTC on 1 September through 06:00 UTC on 2 September: 2,040 tiles, 54.24 MiB payload, and validated extrema of −70.16…48.25 °C (202.99…321.40 K). The combined four-field run is 246.45 MiB. Deterministic tests cover exact TMP selection, metadata, signed/no-data encoding, quantisation, antimeridian sampling, catalogue preservation, contour intervals, no-data holes, and a continuous synthetic isotherm across a tile boundary. Browser control was unavailable during this milestone, so no visual browser acceptance is claimed; automated lint/build and local asset checks provide the non-visual verification record.

### Next direction

Global mean-sea-level pressure is now the remaining regional map field and is the most direct next migration. Higher-value cloud-layer or wind visual work can proceed later without changing temperature ownership.

## 2026-09-01 — Route Foundation v1

### Goal

Establish a provider-neutral route and journey model that answers where an imported hiking route goes and when a user is expected to reach each part, without coupling route analysis to weather providers.

### Changes

- Added client-side GPX track/route import, controlled 40 m geographic resampling with a 6,000-sample cap, antimeridian-safe geometry, and prominent persistent route rendering.
- Added batched, cached Terrarium DEM sampling, elevation smoothing, cumulative distance/ascent/descent, and stable local gradients.
- Added a segment-by-segment Tobler-shaped hiking model with explicit pace, party, load, moving-time, break-time, departure, target-duration, and target-finish assumptions.
- Added expected arrivals and a deliberately approximate timing range throughout the route, plus a linked interactive elevation/time profile and concise route summary.
- Added deterministic tests for GPX selection, geometry, terrain metrics, walking behaviour, target scaling, breaks, schedules, uncertainty, and degenerate routes.

### Architectural decisions

GPX is an input format rather than the route domain model. Terrain enrichment is prepared once and remains independent of journey timing; movement modelling remains independent of weather. Target durations scale terrain-aware segment times instead of replacing them with uniform speed. Generic break time is distributed through movement progress and remains separate from moving time. The resulting per-sample schedule is the future attachment point for location-by-time weather.

### Known limitations

The importer selects the longest usable continuous track/route candidate and does not manage multiple routes or explicit stops. Terrain elevation comes from the existing DEM and incomplete coverage withholds journey timing rather than substituting zero. The walking profile and uncertainty range are general planning assumptions, not personalised predictions; routes are not persisted, edited, generated, or weather-adjusted.

### Verification

Deterministic route tests cover GPX parsing, resampling, antimeridian continuity, terrain smoothing, ascent/descent, gradients, movement speeds, break separation, target constraints, schedules, and uncertainty. ESLint, production build, dependency audit, and diff checks were run. Browser control was unavailable in the test environment, so no automated visual or mobile acceptance is claimed.

### Next direction

After Route Foundation v1 is visually reviewed, Meridian can sample existing weather fields against the predicted location-and-time schedule as a separate route-weather milestone. Explicit stops, additional activity models, and personal calibration remain later work.

## 2026-09-02 — Offline activity research foundation

### Goal

Establish a privacy-preserving evidence layer for investigating whether historical activity recordings can later calibrate Meridian's generic walking model, without changing production journey estimates.

### Changes

- Added offline FIT/FIT.GZ, GPX/GPX.GZ, and TCX/TCX.GZ ingestion with a common optional-field activity model, source provenance, catalogue/file inventory checks, and aggregate private reporting.
- Added explicit evidence states for plausible movement, stationary recording, timer pauses, timestamp gaps, GPS anomalies, and uncertain data, plus deterministic synthetic tests.
- Added a terrain-enrichment boundary for a later experiment using Meridian's existing DEM methodology; this milestone performs no bulk elevation download and stores no private activity data in the repository.
- Added deterministic blind context-inference tooling that preserves the source catalogue, keeps generated annotations private, never uses activity names/descriptions, and places blank human-review columns beside frozen recording-derived guesses.

### Architectural decisions

Strava activity labels are catalogue context rather than movement truth. Recorded stops, explicit pauses, gaps, and movement remain separate evidence, and device elevation remains diagnostic rather than canonical terrain. Passively observable movement/terrain evidence remains distinct from user-provided context such as party, load, conditions, intent, or technicality. Reusable code lives in Meridian, while source recordings and generated research outputs stay outside Git.

### Known limitations

The descriptive movement signatures are not calibrated profiles or model classes. Thresholds are intentionally conservative, FIT field conflicts remain visible as diagnostics, and terrain/gradient enrichment plus held-out journey validation are deferred.

### Verification

The importer was exercised against the private archive after a representative-sample pass. Synthetic tests cover formats, gzip input, missing fields, malformed XML, catalogue associations, timestamp ordering, pauses, stationary and slow movement, GPS anomalies, and complementary FIT records sharing timestamps. Existing production journey constants were not changed.

### Next direction

Enrich a bounded representative subset with the same Terrarium and terrain-metric conventions as planned routes, then compare a small interpretable personal gradient-to-speed relationship against Meridian's unchanged generic model on held-out complete activities.

## 2026-09-02 — Terrain resolution and personal calibration experiment v1

### Goal

Test, without changing production behaviour, whether denser sampling recovers meaningful terrain variation and whether an interpretable personal slope-response model improves whole-activity journey estimates.

### Changes

- Added reusable modules for bounded behaviour-based activity selection, timestamp-derived movement evidence, cached Terrarium enrichment, and structured comparisons of sample spacing, smoothing footprint, hysteresis, and gradient windows.
- Added a robust binned slope-response model with shrinkage toward Meridian's unchanged generic curve, repeated whole-activity validation, progression checks, and private report/chart generation.
- Added synthetic tests for coherent very-slow movement, GPS jitter, label-independent selection, Terrarium decoding, terrain-filter sensitivity, leakage-safe folds, and interpretable calibration behaviour.
- Kept all archive-derived datasets, reports, charts, identifiers, and results outside the repository.

### Architectural decisions

Raw timestamped geographic progression is the primary timing evidence; provider summaries, activity labels, device speed, and recorded altitude are diagnostic only. Movement, stationary recording, timer pauses, gaps, anomalies, and uncertainty remain separate. Denser 10–20 m sampling of the same roughly 30 m DEM did not independently recover trustworthy relief; smoothing/filter choice, not nominal sample spacing alone, materially affects cumulative ascent. Model evaluation holds out complete activities and shrinks sparse slope evidence toward Meridian's unchanged generic curve.

### Known limitations

The bounded archive sample mixes movement contexts that cannot yet be identified reliably from recording data alone. Terrain-source resolution, technical ground, weather, party, load, intent, injury, and pause meaning remain confounders. A single personal curve improved some aggregate diagnostics but did not generalise across all contexts. The experiment therefore does not justify a universal personal profile, automatic behaviour classification, or production terrain/timing changes.

### Verification

The source archive was checked for immutability before and after the run. Synthetic research tests and the existing route, weather, contour, lint, build, dependency-audit, and diff checks were run. Private results remain outside Git and production route constants were unchanged.

### Next direction

Before any Calibration v2, compare frozen recording-derived context guesses with independent user annotations. Constrain later calibration to explicit movement contexts and independently validate any terrain-filter adjustment against authoritative route profiles before considering production changes.

## 2026-09-02 — High-resolution Welsh terrain experiment v1

### Goal

Determine what authoritative one-metre terrain adds beyond Meridian's Terrarium baseline, where route sampling/filtering removes vertical signal, and whether bounded remote access is practical without changing production behaviour.

### Changes

- Added a generic offline terrain-research pipeline for GPX geometry, WGS84-to-national-grid transformation, bounded Cloud Optimized GeoTIFF block caching, Terrarium comparison, physically defined filtering, ascent/descent decomposition, multi-scale 2D terrain metrics, private reports, and plots.
- Tested route sampling at 1–40 m against transparent median/hysteresis variants while keeping both DEM sources on the same geometry and processing semantics.
- Added deterministic synthetic tests for CRS transformation, geodesic resampling, raster interpolation, nodata/partial coverage, physical-distance filtering, ascent semantics, planar slope, and neighbourhood terrain metrics.

### Architectural decisions

High-resolution analytical terrain is distinct from visual map terrain. Regional authoritative sources may eventually enrich route analysis behind a small provider boundary while the existing global DEM continues to serve MapLibre terrain. Sampling/filtering must be expressed in physical distance, source differences must remain separate from processing differences, and external route totals are diagnostic rather than optimisation targets.

### Known limitations

The private experiment used only two Welsh benchmark geometries and cannot establish a universal production filter. One-metre DTM detail may include path-alignment effects, bridge decks, inadequately filtered vegetation, or other artefacts. Local roughness and curvature are terrain signals, not evidence of technicality or difficulty.

### Verification

The official national DTM served bounded HTTP ranges and tiled Rasterio window reads; the complete national raster was never downloaded. Private GPXs, raster blocks, derived profiles, reports, and plots remained outside Git. Synthetic terrain tests and the full established repository verification suite passed, and no production terrain, route, movement, rendering, or weather code changed.

### Next direction

Validate a small set of physically defined filters against surveyed or otherwise high-confidence terrain sections and repeated route geometries across Wales plus a second authoritative regional DEM before considering an analytical terrain resolver or production constants.

## 2026-09-02 — High-resolution terrain generalisation experiment v2

### Goal

Test whether the Welsh analytical-terrain findings generalise to a second
authoritative national one-metre DTM across flat, rolling, and mountainous
private benchmark geometries, without changing production behaviour.

### Changes

- Added a bounded Environment Agency WCS research provider with current coverage
  metadata validation, numerical GeoTIFF subset decoding, request pacing,
  retries, hard route/aggregate limits, byte-accounted private caching, and
  synthetic provider tests.
- Reused the Welsh route geometry, Terrarium baseline, physical filtering,
  ascent decomposition, two-dimensional metrics, plotting, and reporting
  semantics for a private England experiment and cross-region comparison.
- Recorded only durable, privacy-safe conclusions in public documentation;
  benchmark GPXs, raster blocks, profiles, reports, and plots remain outside Git.

### Architectural decisions

The evidence now supports designing a provider-neutral analytical terrain
resolver later, while keeping visual MapLibre terrain independent. COG range
reads and WCS coverage subsets require different retrieval adapters but can
share projected numerical sampling and derived terrain semantics. High
resolution is not a universal ascent correction: source and processing effects
remain separate, route-dependent evidence.

### Known limitations

The bounded route set does not establish universal production filters. The
Environment Agency composite combines surveys from different dates and source
resolutions, and numerical zero outside composite coverage needs explicit
handling distinct from valid low elevation. Very small-scale roughness remains
sensitive to alignment and raster artefacts, and long routes can exceed prudent
route-local access limits.

### Verification

The official WCS advertised and returned bounded one-metre Float32 terrain
coverages in British National Grid. Synthetic terrain/provider tests and the
established route, activity, weather, contour, lint, build, audit, compilation,
and diff checks were run. No production terrain, routing, movement, map, or
weather behavior changed.

### Next direction

Validate the proposed resolver requirements against a third delivery/source
environment or surveyed repeated route sections, focusing on coverage
resolution, cache lifecycle, provenance, and filter stability rather than
matching third-party ascent totals.

## 2026-09-02 — Route Conditions Foundation v1

### Goal

Attach existing environmental fields to the route journey schedule so Meridian
can show what conditions are expected at each location when the traveller is
likely to reach it, without changing the movement estimate.

### Changes

- Added a composed route-condition domain joining terrain samples and expected,
  earliest, and latest arrivals to global GFS temperature, one-hour
  precipitation, total cloud, and 10 m wind.
- Added deterministic per-field forecast-time selection, actual-valid-time
  provenance, batched numeric-tile preparation, synchronous cached sampling,
  field-independent missing states, and stale-generation cancellation.
- Added raw U/V preservation plus route-relative headwind, tailwind, and
  crosswind components with explicit sign conventions.
- Added normal, temperature, precipitation, wind-speed, and gradient route
  modes through one data-driven MapLibre segment layer, plus physical-unit
  legends, a linked profile strip, descriptive summary, and focused journey
  condition inspector.

### Architectural decisions

Map forecast time and journey departure time are separate controls. Temperature,
cloud, and wind select the nearest available instantaneous GFS step within
coverage; ties choose the earlier step. Precipitation selects the actual
one-hour accumulation interval containing the journey time and is never treated
as an instantaneous interpolated field. Weather values do not affect route
speed. Route display density does not imply meteorological resolution, and raw
conditions remain separate from later interpretation.

### Known limitations

Expected-arrival conditions are the v1 display; earliest/latest timestamps are
retained but their weather fields are not yet evaluated or classified.
Conditions are limited to the existing GFS +24 h dataset and 0.25° resolution.
The summary is descriptive, route colouring uses sampled segment values, and
there is no gust, visibility, freezing-level, snow, ground-state, hazard, or
weather-adjusted journey model.

### Verification

Deterministic tests cover temporal boundaries and gaps, precipitation interval
semantics, cardinal and antimeridian bearings, head/tail/crosswind conventions,
calm and zero values, missing/partial states, provenance, summaries, and
gradient presentation without weather. Route/journey, weather preprocessing,
temperature-contour, lint, build, dependency-audit, and diff checks were run.
The in-app browser runtime was blocked by a Windows sandbox ACL failure, so no
automated visual or mobile acceptance is claimed for this milestone.

### Post-acceptance correction — 2026-09-03

Manual route testing initially found every GFS-backed journey condition
unavailable. The retained local catalogue and all referenced tiles were complete,
but its manually generated +24 h run had expired before the tested departures;
the route-condition forecast bounds were therefore behaving honestly. A fresh
equivalent run confirmed current short-route coverage and mixed coverage on a
journey extending past the horizon. The ordinary point inspector also had an
independent lifecycle issue: its delayed sample requests could be repeatedly
cancelled as inspection state changed, leaving matching results unresolved in
the UI. Point sampling now starts immediately while retaining URL deduplication,
cache reuse, and stale-result suppression. Expanded deterministic tests cover
direct scalar/vector sampling, complete and partial horizons, missing steps,
field/tile isolation and retry, valid zeroes, and superseded builds.

### Visual/debug correction — 2026-09-03

Condition-route darkening at overview zooms came from GeoJSON tile simplification,
not line widths or weather availability: the default tolerance discarded short
independently coloured segments while retaining the continuous dark casing.
The already-resampled route source now disables that simplification; Normal
paint, condition paint, layer order, and sample-level forecast coverage remain
unchanged.

The isolated precipitation discontinuity was a display-path issue. A hard
0.1 mm colourisation cutoff made valid trace amounts transparent, and independently
clamped raster edges amplified adjacent values into a geometric join. The shared
scalar renderer now interpolates neighbouring numeric pixels before colourisation
on an edge-inclusive visual grid. Bounded neighbour preparation reuses the
existing numeric cache; immutable tiles, numeric inspector values, meteorological
resolution, and forecast semantics are unchanged. Positive trace amounts fade
continuously into the unchanged light-rain palette and are not labelled dry.

Journey precipitation now shows its local accumulation interval instead of an
instantaneous valid-time offset. The map inspector and forecast timeline also
identify the interval. Instantaneous fields retain valid-time/arrival-offset
wording. Overlapping route passes remain a known limitation: later-rendered
traversals can dominate the same map geometry, including directional gradient
and time-dependent conditions.

Regression tests reproduce overview segment loss using the installed MapLibre
tiler, then verify retained segments, unchanged Normal paint, partial coverage,
numeric/no-data and cache semantics, matching raster boundaries, trace/zero
amounts, and interval formatting. Retained precipitation assets at three adjacent
forecast hours were served successfully and passed the real numeric-to-display
edge comparison. Route/journey/condition, contour, weather preprocessing, lint,
build, audit, and diff checks passed. Browser launch and a runtime-reset retry
both failed before the application opened with a Windows sandbox ACL error;
visual and mobile acceptance are not claimed.

### Next direction

Visually validate the route-condition interaction across realistic journey
times, then evaluate which additional raw fields—such as gusts, cloud base,
visibility, or freezing level—provide the greatest route-planning value before
introducing any condition interpretation.

## 2026-09-03 — Environmental Enrichment v1

### Goal

Add useful raw atmospheric context to the route × expected-arrival pipeline
without changing journey timing, map layers, terrain or condition interpretation.

### Changes

- Added surface `GUST` and `VIS`, plus `HGT` at `0C isotherm`,
  `highest tropospheric freezing level` and `cloud ceiling` through the canonical
  GFS builder. The shared atmospheric writer reuses indexed acquisition, grid
  sampling and independent atomic catalogue publication; inventories are cached
  within an invocation and HTTP range responses are checked before reading.
- Extended scalar contracts and grouped route sampling rather than creating five
  sources or caches. Three scalar workers plus wind bound preparation concurrency;
  each timestep is sampled synchronously after preparation. Invalid catalogue
  entries no longer invalidate otherwise healthy fields.
- Added approximate gust, model visibility, freezing-level and experimental
  ceiling values to the journey inspector, with highest freezing level and
  per-field provenance in details. Peak gust and minimum visibility summaries
  state scheduled-sample coverage. Existing profile linking and colour modes
  remain unchanged; aligned height samples prepare, but do not implement, future
  atmospheric-height profile views.

### Architectural decisions

Live f001–f024 ecCodes inspection confirmed `gust` / wind speed (gust), `vis` /
visibility, and `gh` / geopotential height. Surface units are `m s**-1` and `m`;
height units are `gpm`. Level types are `surface`, `isothermZero`,
`highestTroposphericFreezing` and `cloudCeiling`. All five use instantaneous
PDT 0, start/end/forecast step equal to the requested hour, no statistical
processing, and run + forecast-hour valid time. Every field used the validated
1440×721, north-to-south 0.25° regular grid with scanning mode 0 and no bitmap
missing cells. Gust is not described as a preceding-hour maximum.

The bounded global inspection selected 2026-09-02 18Z after newer candidates'
f024 inventories were unavailable. Each row below represents 24,917,760 source
values over f001–f024; these are grid-point distributions, not area-weighted
climate statistics. Percentiles are raw, including the ceiling sentinel.

| Field | Minimum–maximum | P1 | P50 | P99 |
| --- | --- | --- | --- | --- |
| Gust, m/s | 0–57.017 | 0.702 | 7.204 | 23.817 |
| Visibility, m | 18.048–24135.656 | 123.300 | 24134.971 | 24135.299 |
| 0°C height, gpm | 0–7536.640 | 0 | 2858.720 | 5586.400 |
| Highest freezing height, gpm | 0–7572.960 | 0 | 2890.720 | 5600 |
| Ceiling, gpm | 8.315–20000.152 | 9.697 | 15424.109 | 20000.152 |

Visibility's strong ~24.1 km saturation and the ceiling's ~20 km concentration
required explicit interpretation. [NOAA UPP documentation](https://noaa-emc.github.io/UPP/upp_v11.0.0/AVIATION_8f.html)
identifies 20000 as no ceiling, with ceiling measured above the model surface.
The 11,680,874 near-sentinel cells (46.88%) are therefore unavailable before
interpolation, not literal high clouds. A 1 gpm tolerance covers observed
packing displacement; bitmap missing and no-ceiling counts remain separate in
validation. Freezing heights retain sea-level reference and valid zeroes.

All new tiles use lossless uint16 RG, no-data 65535, constant blue/alpha, and
schema-v2 scale/offset metadata. Gust uses 0.1 m/s; visibility uses 10 m;
heights use 5 gpm with −1000 offset. The measured visibility range does not
justify a nonlinear contract: 10 m linear precision is compact and retains low
visibility detail without another decoder. Client sampling continues to use
manifest metadata. Physical references and missing-value meaning are explicit;
cloud ceiling is neither cloud base nor a cloud-immersion test, and freezing
height is not an ice detector.

The current usable run was refreshed through the established command, reusing
its four already-validated immutable fields and generating the five new fields
for the same run. All nine cover valid times 2026-09-02 19Z through 2026-09-03 18Z;
precipitation retains its real one-hour intervals. There are 2040 tiles per field:
gust 64.15 MiB, visibility 75.64 MiB, freezing height 48.30 MiB, highest freezing
height 48.92 MiB, and ceiling 76.81 MiB. New PNG payload is 313.82 MiB; all nine
fields total 560.53 MiB of PNGs. Inspection took about 104 s and successful new
field generation/validation about 557 s, excluding an initial Windows rename
failure corrected by reusing the existing builder's move/copy fallback.
Source messages remain in a disposable ignored cache (~105.41 MiB), separate
from the published field contracts. No generated assets are tracked.

### Known limitations

The horizon remains f001–f024, updates are manual, and GFS 0.25° remains the
meteorological resolution. Sampling expected arrivals does not evaluate the
earliest/latest weather window. Ceiling edges touching no-data are conservatively
unavailable, and no-ceiling versus bitmap missing is combined in the web no-data
code, with the distinction retained in source validation. No ice, cloud
immersion, ground state, hazard, wind amplification or weather-adjusted speed is
inferred. Atmospheric-height profile drawing is deferred, especially because
ceiling and route elevation have different vertical references.

### Verification

Synthetic tests cover all five exact selectors, metadata, ranges, zero/no-data,
PNG byte/quantisation round trips, grid orientation, antimeridian, publication
failure isolation, scalar sampling/interpolation, partial horizons, earlier ties,
cache reuse/cancellation, malformed manifests, independent freezing fields, and
inspector formatting. Existing route/journey/conditions, contour and scalar
rendering tests remain passing. Every generated PNG was decoded and compared
against its sampled source field within half a quantisation step.

A real served-asset smoke test resolved all nine manifests and compared direct
scalar sampling with Route Conditions at public coarse test coordinates,
including antimeridian points and a 34-hour partial-horizon schedule. It used
54 decoded tiles / 7.13 MiB of the unchanged 64 MiB cache, transferred 2.09 MiB
of PNGs, ended with no pending requests, and made no new requests for a repeated
route. Lint, production build, Python compilation, dependency audit and diff
checks passed; existing Vite bundle-size/plugin-timing notices remain.

The dev server started normally. Browser launch and a runtime-reset retry both
failed before Meridian opened: `trusted Node process exited unexpectedly;
kernel reset, rerun your request`. This is a browser tooling failure, not an
observed application error. Actual visual/mobile acceptance and the earlier
overview-route/precipitation-seam visual checks remain unverified; server-rendered
inspector text and real data-path tests do not substitute for them.

### Next direction

Manually validate atmospheric values, provenance and partial coverage across
short and long journeys before considering any separate derived-condition
design. No further environmental milestone is implemented here.

## 2026-09-03 — Derived Environmental Conditions v1

### Goal

Turn already sampled expected-arrival atmospheric fields into explainable route
context without changing terrain, movement, forecast products or arrival times.

### Changes

- Added a pure typed derived layer with independent freezing, sustained wind,
  gust and visibility/ceiling availability. Aligned indexes and field keys link
  interpretations to original raw values, terrain and forecast provenance.
- Added approximate signed route/freezing separation, multiple-level caveats,
  debounced crossing events, contiguous poor-visibility sections and one set of
  wind/gust/visibility extrema. No severity or confidence score is introduced.
- Inspector now leads with arrival/terrain and grouped context; raw values and
  provenance remain expandable. Summary adds coverage-qualified freezing context,
  selectable crossings and secondary sustained head/crosswind information.
- Added a subtle gapped freezing-level profile line using the existing route
  samples/focus interaction. It is clipped to the elevation scale with an
  off-scale/range notice rather than compressing the terrain profile.

### Architectural decisions

Terrarium's documented sea-level elevations and GFS mean-sea-level geopotential
heights support an approximate comparison, not a survey-datum claim. Explicit
spherical conversion `R × H / (R − H)` changes the retained heights by less than
10 m. Raw gpm values remain intact. A ±100 m near band is a display/debounce
policy, not atmospheric error bounds or an ice forecast.

Inspection of all 24 native retained grids found paired freezing differences
of ≤1.12 gpm at P95, 1304.64 gpm at P99 and 3429.44 gpm maximum. A >100 m
separation flags materially distinct diagnostics; absent or different-time/run
highest-level evidence leaves structure unknown. Crossing continuity resets
through unknown/multiple structures and unavailable samples. Locators use
sample brackets, not interpolated forecast fields, with coarse UI rounding.

Visibility vocabulary uses Met Office distance conventions (<1000 m, <2 nautical
miles, <5 nautical miles, and greater visibility). The retained global values
span these bands: 1,424,439 / 1,159,599 / 1,213,862 / 21,119,860 native samples.
Calm/light wind uses one/three-knot display boundaries; a one-knot component
dominance margin avoids emphasising tiny directional differences. Existing
along/cross signs are unchanged. Gust remains directionless; signed excess is
only calculated against a matching sustained forecast, without calm ratios.
Sources, exact thresholds and caveats are in
[derived route conditions](derived-route-conditions.md).

Ceiling remains raw model-surface-relative context. No model orography is
currently sampled, so no ceiling/route comparison or ceiling profile is made.
No new GFS field, manifest, preprocessing, dependency or cache is required.
The retained nine-field 2026-09-02 18Z f001–f024 run was not regenerated.

### Known limitations

GFS remains 0.25° and expected-arrival only. Approximate vertical comparison does
not resolve every datum in the composite terrain source. Multiple freezing
levels cannot describe a full temperature profile. No ice/snow, cloud immersion,
wind amplification, risk score or weather-adjusted movement is inferred.
Off-scale freezing heights are reported numerically; only the lower diagnostic
is drawn. Event locations and sample-count coverage are not precise boundaries
or percentages of elapsed journey time.

### Verification

Added 21 synthetic tests covering references/conversion, freezing bands and
crossings, missing/zero values, independent families, wind conventions, gust
separation, visibility boundaries, ceiling semantics, events, purity and gapped
profile markup. All 65 relevant frontend tests pass, including the existing
route/journey, weather-source, precipitation-rendering and temperature-contour
suites and the extended real served-asset test. One initial concurrent run had
a transient served-tile availability assertion failure; the isolated test and
complete serial rerun passed. No application/cache workaround was added.

Retained numeric assets were checked directly and through Route Conditions;
34-hour synthetic schedules retain early coverage and unavailable later samples.
Two privately held lowland/mountain benchmarks were checked in memory with cached
Terrarium terrain and the unchanged production resampling/terrain/schedule logic.
Their expected-arrival contexts were available and below the forecast freezing
level; no crossing was invented. Derived computation averaged under 0.2 ms per
benchmark build and made no network requests. The served smoke test retained
54 tiles / 7.13 MiB in the unchanged 64 MiB cache, with zero pending requests and
no repeated-route tile downloads.

The bounded South Downs real-route replay subsequently completed with explicit
approval: 161.95 km / 4,050 samples, using the unchanged terrain and journey
pipeline and retained GFS run. For the tested 2026-09-03 03:00 BST departure,
1,892 samples had weather/derived coverage through 75.64 km; the next sample at
75.68 km fell beyond the 18:00 UTC forecast cutoff and remained unavailable.
Departing at 05:00 BST moved the last covered point to 66.08 km (1,653 samples).
Cloud ceiling was independently unavailable at 538 otherwise-covered samples
in the first replay without disabling the other fields. Freezing-profile gaps
remained honest beyond coverage, and no freezing crossings or multiple-level
events were invented. The replay supports the existing milestone conclusions.

Only the 249 required AWS Terrarium tiles were fetched, strictly in memory:
17.65 MiB externally, or 23.50 MiB including local GFS response data, below the
32 MiB cap. No additional external source was used and no fetched data was
persisted. The source GPX SHA-256 remained unchanged. Terrain preparation took
about 34 s, initial weather preparation 21 s, and derived computation averaged
1.14 ms for the full route without additional requests. This completed the
real partial-horizon replay; browser visual acceptance remains separate.

Private recordings/GPXs, annotations and generated GFS assets were not modified
or copied into tracked files. Lint, production build, dependency audit (zero
production vulnerabilities) and diff checks pass; existing Vite large-bundle
and output-directory timing notices remain. No Python source changed, so Python
and unrelated research suites were not rerun.

Vite served the application and numeric assets. Browser launch and a reset retry
both failed before opening Meridian: `windows sandbox failed:
helper_unknown_error: apply deny-read ACLs`. Visual/mobile acceptance, including
the earlier overview-colour and precipitation-seam checks, remains pending;
server-rendered markup and numeric tests are not visual acceptance.

### Next direction

Manual acceptance of context, profile gaps and linked focus is required before
further product changes. Arrival-window analysis and other derived families
remain separate, unimplemented milestones.


## 2026-09-03 — Automatic GFS Updates v1

### Goal

Remove the need to manually regenerate a stale local GFS run while preserving the
client-only application, the nine established fields, the +24 h horizon and all
existing route-condition semantics.

### Changes

- Extended the canonical Python builder with one-shot, inventory-only and
  continuous watch orchestration. Watch mode checks hourly (with a guarded
  minimum of 15 minutes), probes cycles newest-first and requires all nine
  f001–f024 inventories before selecting a run.
- Added a kernel-held cross-process lock, restartable marked transactions and a
  single publication boundary. Field builders publish only to a private
  catalogue; the public `latest.json` changes once, after the complete run and
  every numeric PNG validate.
- Immutable-run promotion first retries a same-volume directory rename. When a
  Windows file watcher keeps the directory busy, it uses a marked, resumable
  copy and validates the destination again. Neither path exposes the run through
  `latest.json` until it is complete. Failed generation, validation, promotion
  or cleanup leaves the prior catalogue live and is retried on a later check.
- Retention runs after publication and keeps the current plus one previous
  complete nine-field run. It removes only recognized generated tiles,
  manifests and validation records from older run directories. Active builds,
  source caches, links, unknown files and unrelated project data are excluded;
  old marked generated transactions can be recovered or pruned safely.
- Added `npm run weather:check`, `weather:update` and `weather:watch` through a
  small cross-platform Python launcher. Normal `npm run dev` remains independent
  of NOAA; local live development uses two terminals.
- The browser now checks only cache-busted `latest.json` every five minutes and
  whenever a hidden tab becomes visible, with a 20-second timeout and one
  in-flight request maximum. Identical/older catalogues stop before manifest
  requests. A newer catalogue must be one coherent nine-field +24 h run and all
  immutable manifests must load before one state swap occurs.
- Catalogue checks retain current renderer/source state. A swap preserves the
  exact selected valid time when it overlaps, otherwise advances to the first
  current time in the new horizon. Existing generation/abort guards rebuild
  Route Conditions once for the new source set; terrain and DEM state are not
  touched. Point-inspector result keys now include run identity.
- Added a compact active-run/check-time indicator with coverage-based ending,
  expired and journey-outside-horizon wording. The generic “model samples” copy
  now says “Regional pressure · 9 × 9 samples” so it cannot be mistaken for the
  global GFS fields.

### Architectural decisions

Weather generation is independent of frontend deployment. Run URLs stay
immutable and `latest.json` is the only mutable browser discovery object.
Stale-but-valid data remains preferable to a broken update. Automatic generation
therefore combines complete-run publication with bounded retention rather than
advancing fields independently.

The hourly local cadence is conservative relative to six-hour GFS cycles and
allows incomplete publication to settle without hammering NOAA/AWS. Browser
checks are cheaper and use five minutes because they request one tiny local/CDN
metadata object, never tiles. Immutable tile URLs keep the shared 64 MiB cache
useful across checks and prevent freshness polling from causing tile or DEM
requests.

### Real local validation

The live catalogue started at 2026-09-02 18Z. The updater rejected the theoretical
2026-09-03 18Z candidate because f024 was not yet published, then selected the
complete 2026-09-03 12Z run and generated all nine fields. With Vite deliberately
left running, Windows denied the final directory rename after the first full
validation. The public pointer correctly remained at 18Z. The marked transaction
was resumed without rebuilding or redownloading fields; the copy fallback
validated the destination again and atomically published 12Z. The successful
resume took 332.92 seconds; the complete generation/recovery exercise ran about
31 minutes. A subsequent inventory-only restart again rejected incomplete 18Z,
reported no newer usable run and generated nothing. A bounded watch start also
reported the same no-op result, retained both runs, entered its 15-minute test
sleep and left no updater process after Ctrl+C.

Retention kept `20260902T18Z` and `20260903T12Z`, and removed generated output for
`20250829T00Z`, `20260830T12Z`, `20260831T12Z`, `20260831T18Z` and
`20260901T06Z`. Retained timestamped run directories use 1,227.19 MiB
(1.198 GiB), down from 1.219 GiB across six timestamped directories before the
update. Total weather-root storage is 1,332.24 MiB (1.301 GiB), including the
105.05 MiB atmospheric source cache that retention intentionally preserves.
There are no update transaction directories or publication markers left.

The real served-asset test loaded all nine 12Z manifests and sampled the normal
Route Conditions path at public coarse coordinates, including partial-horizon
coverage and antimeridian points. A repeated route added no requests; 50 decoded
tiles occupied 6.88 MiB of the unchanged 64 MiB cache, 2.11 MiB of PNG data was
transferred, and no requests remained pending.

### Verification

The final deterministic suites cover offline/incomplete discovery, no-op restart,
failed generation/validation, atomic publication order, duplicate locking,
Windows promotion fallback, interrupted-copy/staging recovery, retention safety,
cleanup failure, cache-busted metadata requests, identical/older/newer catalogue
handling, manifest failure, poll overlap, visibility resume, stale async results,
timeline selection, retained visuals and freshness wording/presentation. The
Python weather suite has 57 tests. The frontend weather/rendering/route/derived
suites have 76 deterministic tests, plus the opt-in real served-asset test.

ESLint, TypeScript, the production build, Python compilation, production
dependency audit and Git whitespace checks pass. The audit reports zero production
vulnerabilities. The existing large JavaScript chunk and `vite:prepare-out-dir`
timing notices remain; the final build, including two local weather runs, took
about 34 seconds.

Vite started and served the new run. Browser automation and one reset retry both
failed before Meridian opened with `node_repl kernel exited unexpectedly` and
`windows sandbox failed: helper_unknown_error: apply deny-read ACLs`. No browser
or security setting was weakened. Visual desktop/mobile acceptance, live
no-reload adoption and Route Conditions interaction therefore remain unclaimed.

Generated weather/source assets, `.env.local`, private GPXs/activities,
credentials and personal paths remain untracked. The milestone changes no route
timing, derived-condition meaning, pressure ownership, field set, forecast
horizon, backend or production infrastructure.

### Known limitations

Watch mode is a foreground local process; production scheduling, object storage,
CDN publication, monitoring and alerting remain deferred. The forecast remains
+24 h with discrete model steps and no run interpolation. Full nine-field output
and validation are intentionally storage/CPU intensive. Source caches are outside
the generated-run retention policy. On Windows, watcher contention may require
the slower marked-copy promotion, but publication remains pointer-atomic and
failure-safe.


## 2026-09-03 — Desktop Workspace Redesign v1

### Goal

Replace the desktop's long, scroll-led sidebar with a map-first workspace that gives Location, Journey, map display and route analysis distinct homes while preserving all existing route, weather and map state.

### Changes

- Added an explicit UI-only desktop state model for Location/Journey context, left workspace, right map controls, bottom route analysis, global settings, journey settings, clear-map mode and Map Inspector state. Domain data remains owned by `App`; presentation actions are absent from route, terrain, catalogue and weather-loading effect dependencies.
- Kept the existing mobile panel below 701 px and composed a desktop shell above that breakpoint. The left workspace now switches between a focused location workflow and a compact journey overview without unmounting or clearing domain state.
- Separated route facts (distance, ascent and descent) from the derived journey estimate (duration, moving time, breaks, departure/finish and likely range). Existing activity, pace, party, load, break and planning controls moved into a contained journey-settings dialog.
- Added a restrained journey-weather summary led by temperature range, rain when encountered, peak gust and minimum visibility. Complete coverage is silent; partial coverage is described using the last continuously covered route distance when available. Terrain reporting remains limited to DEM coverage, ascent/descent and sampled gradient; no surface or technicality classes were invented.
- Moved the linked elevation/journey profile, freezing-level line and condition strip into a collapsible horizontal route-analysis surface. Route colour modes remain available there. Selecting the map route or profile continues to use the same focused sample index.
- Moved Terrain/Satellite, all existing overlays, forecast timeline and playback into a compact right map-control surface. The legacy 9 × 9 label is now explicitly subordinate to regional Open-Meteo pressure, and the legend is disclosed on demand.
- Added a compact global-settings dialog with Map Inspector as the only setting. The inspector is off by default; map clicks still select a location, route hover/click still links focus, and ordinary MapLibre navigation remains untouched. An inspector-session token prevents a popup created before disabling the tool from reappearing later.
- Removed the map instruction pill. Independent restore controls keep each surface accessible; clear-map mode exposes a persistent Meridian-mark restore control and preserves camera, basemap, overlays, route, analysis focus, location, journey assumptions and forecast state.
- Regrouped selected-route-point data into concise model values, one shared GFS run/time source block and an `About this data` disclosure for resolution, visibility, ceiling, gust-direction, expected-arrival and freezing caveats.

### Architectural decisions

Desktop panel state is presentation state. It may change visibility and composition, but must not trigger DEM/weather refetches or reset analytical state. Location and Journey remain parallel contexts over the same map. MapLibre's imperative lifecycle remains inside `MapView`; the shell passes only stable data and callbacks.

The primary desktop overview uses progressive disclosure. Route facts are measurements, journey duration is an estimate, weather values are raw model evidence, derived context remains traceable to that evidence, and caveats sit below the decision-oriented overview. Mobile keeps the established layout until a dedicated mobile design milestone.

### Verification

Nine focused UI tests cover context/panel state, clear-map preservation, Map Inspector default and session behavior, journey-settings schedule effects, route-fact versus estimate presentation, silent complete coverage, spatial partial coverage, grouped provenance, map-control ownership, route-profile focus/condition strips and absence of network work from presentation actions. The full deterministic frontend run covered 86 tests: 85 passed and one opt-in served-data smoke test was skipped. The atmospheric suite initially hit Vite's 60-second local module-transport timeout; parallel module setup removed that harness bottleneck and all nine atmospheric assertions passed.

ESLint and the production build pass. The cached offline production dependency audit reports zero vulnerabilities; the registry-backed audit endpoint timed out. The build retains the existing large-chunk warning and spent two minutes primarily copying ignored local weather output. Browser automation failed before opening Meridian on the initial attempt with `trusted Node process exited unexpectedly; kernel reset, rerun your request`. After one reset, it failed with `node_repl kernel exited unexpectedly` and `windows sandbox failed: helper_unknown_error: apply deny-read ACLs`. No browser or security setting was changed. Visual acceptance at 1920×1080, 1440×900 and 1366×768 therefore remains manual and unclaimed.

### Known limitations

The desktop visual treatment is a first implementation and still needs manual inspection at the target viewports, with and without a route. The left workspace permits contained scrolling for a long location forecast or deep details; core journey navigation no longer depends on scrolling between unrelated controls. Mobile intentionally retains the previous panel and needs its own future redesign. Full weather-condition analysis tabs, condition-click map actions, route-colour automation, viewsheds, inferred terrain-surface classes, arrival-window analysis and weather-adjusted timing remain deferred.

## 2026-09-04 — Desktop UI Refinement v2

### Goal

Refine the successful desktop workspace structure after manual v1 inspection showed excessive card padding, a map-obscuring right panel and bottom dock, cramped point details, duplicate analysis entry points, and an elevation-profile pointer that aligned only near the centre.

### Changes

- Kept a stable full-height Location/Journey workspace and reduced its desktop width, header, segmented control, gaps, card padding, search row, current-condition metrics, forecast rows, route facts, estimate and weather summaries. Successful terrain/timing status is now silent; loading, partial and error states remain visible. Long route names truncate independently of the fixed Clear route action.
- Replaced the centred journey-settings treatment with a viewport-contained popover anchored beside Tune. It retains activity, pace, party, load, breaks, planning mode, departure, target-duration and target-finish inputs.
- Made Journey Overview content lead into analysis. Elevation and Gradient affordances open their modes; Temperature, Rain and Wind/Gust summaries open the corresponding existing route-colour and condition analysis. The duplicate Open analysis/View profile actions, large miscellaneous Terrain Overview and permanent “profile ready” messaging were removed.
- Replaced the Route Colour select with labelled Elevation, Temperature, Rain, Wind and Gradient mode buttons. They still drive the single established route-condition mode passed to both MapView and the analysis strip, preserving map colouring, legends and field gaps.
- Shortened the route-analysis dock and rebalanced it into a responsive plot area and a wider point-detail region. Point fields use concise tiles and one shared GFS run/time block; environmental context and caveats remain available through disclosures. When every field is outside the horizon, one grouped message replaces nine repetitions, while mixed availability remains field-specific.
- Corrected profile pointer mapping by transforming the rendered pointer coordinate into the responsive SVG view box and then normalising it against the actual drawable rectangle, including its left and right plot margins. ResizeObserver keeps the view box matched to the rendered plot. Hover previews; click pins; another click moves the pin; clicking the same sample toggles it off; a small Unpin action clears it. A pinned sample takes precedence over map/profile preview without changing route data.
- Replaced the large right Display & Forecast panel with a one-column map tool strip and an independent compact forecast time/slider/play control. Active states and accessible labels cover both basemaps and all existing overlays. GFS run/check/coverage, useful active-layer legends and the pressure-only 9 × 9 explanation now live in a Data disclosure; no empty legend control is shown.
- Shell dimensions and dock height use desktop CSS custom properties, with a shorter laptop-height fallback. Map attribution/logo offsets follow the dock, map tools avoid the MapLibre navigation stack, and all new desktop rules remain above the existing 701 px mobile boundary. Clear-map mode continues to hide shell controls without resetting application state.

### Architectural decisions

Preview and pinned selection are distinct presentation state. The active journey point is the pin when one exists and otherwise the transient preview, so UI movement cannot dislodge a deliberate selection. Neither state participates in route, terrain or weather loading dependencies.

Density is preferred before adding tabs or scroll-led navigation. The stable left workspace keeps related current and outlook information together, contextual actions open beside their source, the horizontal dock remains the shared route-distance/time analysis surface, and map-layer controls remain lightweight map chrome. Raw forecast evidence, derived context, missing-data semantics and shared provenance remain unchanged.

### Verification

Fifteen focused desktop tests cover presentation-only state, Map Inspector default-off, compact successful/degraded status, long names, content-led mode mappings, labelled analysis controls, schedule settings, grouped provenance, outside-horizon treatment, map-tool ownership, profile focus and condition strips, five-position pointer geometry at two sizes, pin precedence/move/toggle behavior, and absence of presentation-triggered network work. The full deterministic frontend/weather/rendering/route suite passes 91 tests with one opt-in served-data test skipped.

ESLint, TypeScript and the production build pass. The build retains the existing large JavaScript chunk and output-directory timing notices. The production dependency audit reports zero vulnerabilities from the cached offline advisory data, and Git whitespace checks pass.

Vite started at http://127.0.0.1:5173/. Browser automation failed before opening the page with trusted Node process exited unexpectedly; kernel reset, rerun your request. After one CUA reset, the retry returned the same error. No browser or security setting was changed. Visual acceptance at 1920×1080, 1440×900 and 1366×768 therefore remains manual and unclaimed, including final no-scroll, collision, hover alignment and popover-fit checks.

### Known limitations

Mobile retains the existing layout. The current analysis modes remain limited to elevation/normal, temperature, precipitation, wind and gradient; visibility analysis, viewsheds, new terrain inference, arrival-window weather and weather-adjusted timing remain deferred. Exact desktop density and dimensions should be adjusted only after the pending manual browser pass.

## 2026-09-04 — Visual browser validation tooling

### Goal

Establish a repeatable repository-local way for Codex to render, interact with, screenshot, and inspect Meridian after the built-in browser runtime repeatedly failed across UI milestones.

### Diagnosis

A controlled reproduction started Meridian with the unchanged `npm run dev` workflow. Vite bound only to localhost, returned HTTP 200 with the Meridian document title, served application assets, and logged no application error. Calling the built-in in-app browser against that live page failed before a tab was returned or navigation began with `trusted Node process exited unexpectedly; kernel reset, rerun your request`. Earlier recorded variants include `node_repl kernel exited unexpectedly` and the Windows sandbox `apply deny-read ACLs` failure. The failing layer is the Codex trusted-Node/browser/sandbox runtime, not Vite or Meridian, and no safe repository change can repair it.

### Tooling

- Added the single repo-local `@playwright/test` development dependency and Playwright's pinned Chromium. Browser binaries live in Playwright's standard user cache, outside the repository.
- Added a focused Playwright configuration with three desktop projects, one worker, deterministic locale/timezone, retained failure traces, and a built-in Vite web server on strict loopback port 4173. The server uses the normal `dev` script without `--host` and is stopped automatically.
- Added one desktop shell smoke flow for workspace switching, Settings, an overlay toggle, forecast playback, map-control hide/restore, screenshots, and DOM/map-canvas readiness. It captures console messages, page exceptions, failed requests, and HTTP error responses to JSON; unhandled page errors fail the test.
- Reused the public `snowdonia-smoke.gpx` fixture for one representative route test. Only Terrarium tile requests are fulfilled from a neutral checked-in 256 px test tile; route parsing, terrain decoding, journey construction, route analysis, profile hover, pin movement, and unpin behavior use the real application paths.
- Added `visual:install` and the single default `visual:test` command. Screenshots and diagnostics use deterministic paths under `test-results/visual`; Playwright traces use `test-results/playwright`. Both are ignored.
- The first real Chromium run captured screenshots and diagnostics and exposed an unbound browser `setTimeout` in the catalogue watcher. Wrapping the default timer calls through `globalThis` fixed the genuine `Illegal invocation` page exception while preserving injected deterministic timers in existing tests.

### Validation

The complete headless workflow passed twice without changes: four tests passed and two intentionally non-representative route-project cases were skipped on each run. It rendered 1920×1080, 1440×900, and 1366×768; captured initial and post-interaction screenshots at each size; loaded the Snowdonia route at 1440×900; exercised profile preview/pin/unpin; and left port 4173 closed. The second-run diagnostics contain zero page errors, failed requests, or HTTP error responses.

The complete deterministic frontend, weather, route, and UI suite passes 91 tests with one opt-in served-data smoke test skipped. The focused desktop suite, ESLint, TypeScript, production build, and cached offline production and full dependency audits also pass; both audits report zero vulnerabilities. The production build retains the existing large JavaScript chunk and output-directory timing notices.

Codex read and visually inspected generated screenshots, including the 1440×900 loaded-route analysis and 1366×768 post-interaction state. Direct image-tool access still encounters the same Windows ACL helper failure, but the files are readable through the repository shell and were inspected through an ignored thumbnail/base64 bridge. The deterministic artifact path makes that fallback repeatable.

A bounded headed-Chromium check reached Playwright but Windows rejected browser process creation with `browserType.launch: spawn UNKNOWN`. Headed launch is therefore not part of the supported Codex-host workflow. Headless Chromium is fully functional and is the verified visual-validation path.

### Limitations

The shell/layout proof does not require NOAA or a live terrain provider. Real basemap, weather, and search rendering still reflect external provider availability, and their failures are reported separately in diagnostics. The neutral DEM fixture proves route UI plumbing rather than real elevation values. This remains a lightweight smoke and screenshot workflow, not a pixel-baseline suite or a replacement for existing deterministic domain tests.

## 2026-09-04 — Map-control rail and empty Journey refinement

### Goal

Refine the desktop right-hand map controls into one deliberate rail, improve the route-free Journey hierarchy, and reclaim modest map width without starting the deferred Route Analysis or workspace architecture redesign.

### Changes

- Unified MapLibre navigation and Meridian layer controls around shared desktop tokens: a 12 px top/right inset, 36 px outer rail width, 10 px inter-group gap, and the measured 104 px navigation-group height. Removed MapLibre's independent control margin so both groups share one centreline and viewport inset.
- Shortened visible rail labels to Ter, Sat, Elev, Rain, Cloud, Temp, Pres, and Wind while retaining full accessible names and tooltips. Pressure now uses Pres rather than Press.
- Rebuilt the route-free Journey card as a vertical heading, benefit-led description, Import GPX action, and secondary “Processed locally in your browser.” privacy note. Import remains entirely local and unchanged.
- Reduced the desktop workspace from 326 px to 296 px after comparing rendered 300 px and 296 px passes. The final width keeps the header, Location content, empty Journey state, loaded route facts, forecast rows, and actions comfortable while giving more map area.
- Hardened the loaded-route title flex chain with `min-width: 0`, contained overflow, a fixed-width Clear route action, and single-line ellipsis. The workspace content now explicitly hides horizontal overflow.
- Extended the lightweight Playwright workflow to screenshot the empty Journey state at every target size, assert measured rail geometry, and load the public Snowdonia fixture with an intentionally long in-memory route name. The browser assertion confirms the title truncates, Clear route does not shrink, and workspace content does not overflow horizontally.

### Validation

The required Playwright workflow rendered and was visually inspected at 1920×1080, 1440×900, and 1366×768. The first 300 px pass confirmed the rail and hierarchy; a second 296 px refinement pass completed with four tests passed and two intentionally skipped duplicate route cases. Final screenshots show equal rail widths/insets, centred icons and labels, clean active states, no wrapping or clipping, a balanced empty Journey card, and a stable loaded Journey layout with the long title ellipsized. The visual timeout was raised from 45 to 90 seconds after the first 1920 px capture exceeded the old ceiling despite zero page or network errors; no waits or application readiness checks were weakened.

The focused desktop suite passes 15 tests. The complete deterministic frontend, weather, route, and UI suite passes 91 tests with one opt-in served-data smoke test skipped. ESLint, TypeScript, and the production build pass; the build retains the existing large JavaScript chunk and output-directory timing notices.

### Limitations

Map and weather imagery still reflect external provider availability, so an occasional screenshot may show the fully rendered shell before external tiles arrive. The bottom Route Analysis dock, forecast timeline placement, broader workspace modes, panel-aware camera padding, environmental details, and mobile layout remain intentionally deferred.


## 2026-09-06 — Route analysis moves into the desktop workspace

### Goal

Consolidate route planning and detailed route analysis into the existing map-first desktop workspace, remove the oversized bottom dock, and preserve route, schedule, forecast, camera and selection state across presentation changes.

### Changes

- Expanded the fixed 296 px desktop workspace from Location/Journey to Location/Journey/Analysis. Analysis appears only after terrain preparation produces a route, and switching modes changes presentation state without reloading route, DEM or weather data.
- Moved forecast time, playback and the compact Data/freshness disclosure to the bottom of Location. The floating map timeline was removed; the existing forecast hour and playback state remain owned by App and continue while another mode is visible.
- Added a compact elevation profile near the top of Journey. Its Analyse action and the existing Elevation, Gradient, Temperature, Rain and Wind entry points open the route-gated Analysis mode through the established shared route-condition mode.
- Replaced the bottom Route Analysis dock with a vertical Analysis workspace. It retains responsive profile preview, click-to-pin, click-again-to-unpin, pin movement, map-linked focus, missing profile gaps, arrival timing, condition strips, legends and all five established modes.
- Reordered point evidence for the vertical space: selected measurements lead, derived condition context follows directly, one shared GFS source/time block is used where available, and a single About this data disclosure holds deeper caveats. Outside-horizon and field-specific missing states remain explicit.
- Replaced the anchored Tune popover with an in-panel Journey Settings subview and Back action. Activity, pace, party, load, breaks, planning mode, departure, target-duration and target-finish controls retain their existing model behavior. The permanent explanatory disclaimer was removed.
- Removed the Journey Environmental details disclosure because freezing, cloud, visibility and related diagnostics now have a direct home in Analysis.
- Made the 36 px right map-layer rail persistent in ordinary desktop use, removed its close control, and shortened its buttons to 30 px while preserving 12 px top/right alignment, the 10 px navigation gap, compact labels and full accessible names. Clear-map mode still hides the whole interface intentionally.
- Removed route-analysis-dependent map furniture offsets. Attribution, MapTiler branding and map information controls remain at stable map-edge positions when the workspace mode changes.

### Visual findings and refinement

The repository Playwright workflow rendered Location and empty Journey at 1920×1080, 1440×900 and 1366×768, plus loaded Journey, in-panel Tune and pinned Analysis at 1440×900. The first complete route screenshots showed that the degraded-weather status competed with a long truncated Analysis title. A deliberate refinement moved that subordinate status beneath the title, giving the route name the full row. The rerender confirmed a readable vertical evidence hierarchy, no horizontal overflow, stable map furniture, compact rail alignment and substantially more vertical map space than the removed dock.

Location and Journey fit without normal vertical scrolling at all target sizes in the tested states. The representative Analysis state fits at 1440×900; deeper available scientific content may use the workspace's single vertical scroll. No nested analysis scroll region remains.

### Verification

The final visual workflow passed four representative tests with two intentional duplicate route-project skips. It exercised forecast playback across Location/Journey switching, route import using the public fixture, long-name truncation, Tune/Back, every analysis mode, profile preview/pin/move/unpin, persistent layer controls and stable attribution geometry. Final browser diagnostics contain no unhandled page errors.

Sixteen focused desktop tests pass. The full deterministic frontend, weather, route, rendering and UI suite ran 93 tests: 92 passed and one opt-in served-data test was skipped. ESLint and the TypeScript/production build pass. The build retains the existing large JavaScript chunk and output-directory timing notices; Git whitespace checks pass.

### Limitations

The compact checked-in DEM fixture validates interaction and layout rather than real terrain variation. External basemap and weather availability can change screenshot imagery; failures remain separated in browser diagnostics. Mobile layout, panel-aware camera padding, new analysis modes, arrival-window analysis and richer terrain/weather interpretation remain deferred.

## 2026-09-06 — Desktop map furniture and route-fit cleanup

### Goal

Clean up desktop map furniture and focus-mode entry without changing the established Location/Journey/Analysis information architecture, then make imported-route framing respect the map area that remains visible beside the primary workspace.

### Changes

- Formalised the existing 12 px desktop edge spacing as the **workspace gutter**. The primary workspace, top-right navigation/layer rail, focus restore control, bottom-right map information control, and provider-branding placement now derive their relevant edge positions from `--workspace-gutter`.
- Simplified the primary-workspace header to the Meridian brand and global Settings. Removed the separate Focus and close actions and the retired left-open state. Clicking the brand enters focus mode; the compact Meridian restore control exits it. This remains presentation-only state and preserves route, location, forecast, analysis and camera state.
- Replaced the old CSS-drawn orange/white mark with the canonical `/favicon.svg` asset in both normal and restore controls, so the browser tab and in-app identity use the same mark.
- Kept the 36 px right-hand rail persistent in normal Location, Journey and Analysis modes, with its existing 12 px top/right inset, 10 px navigation gap and compact layer buttons.
- Positioned MapLibre's compact information button exactly one workspace gutter from the bottom-right corner by removing its nested default margin. Satellite-only MapTiler branding uses the provider's existing official horizontal logo URL at the bottom-left of the usable map, one gutter beyond the primary workspace; focus mode returns it to the viewport gutter. The logo was not rotated because the repository contains no provider guidance confirming that rotation is permitted. Required textual attribution remains MapLibre-managed.
- Replaced fixed route-fit padding with measured effective-viewport padding. App-driven import fitting reads the rendered primary-workspace edge and workspace gutter, then supplies MapLibre with asymmetric padding plus a 48 px geometry margin. Focus mode uses symmetric margins. The existing route-id guard still fits each imported route once, so workspace switching, focus restore and manual camera work do not trigger refits.
- Fixed an initial-load race exposed by the Ben Nevis visual fixture. Camera fitting no longer waits for all style sources, and route layers are initialised at MapLibre's `style.load` boundary before terrain source loading makes `isStyleLoaded()` temporarily false.

### Visual validation

The Playwright workflow now uses deterministic test-only satellite metadata, raster imagery and provider-logo dimensions while production continues to reference MapTiler's official endpoints. It asserts the 12 px information-control corner offset, provider/info non-overlap, Terrain-only logo absence, canonical Meridian asset, removed header actions, brand focus/restore, persistent rail geometry and horizontal-overflow containment.

Screenshots were rendered and inspected at 1920×1080, 1440×900 and 1366×768 for Terrain Location, Satellite Location, focus and restore, plus Ben Nevis route framing at every size. At 1440×900, additional public-coordinate fixtures cover West Highland Way, Box Hill, loaded Journey and pinned Analysis. The first settled route pass exposed the initial style/source readiness race; after the lifecycle refinement and rerender, Ben Nevis, West Highland Way and Box Hill all remain fully visible in the effective map area. Map furniture remains stable across workspace modes, Terrain/Satellite and focus restoration.

### Limitations

This is an initial/imported-route fit, not continuous panel-aware camera management. Manual pan, zoom, pitch and bearing remain authoritative after fitting. The official MapTiler logo remains horizontal until provider guidance supports another treatment. Profile sizing, Analysis scrolling, mobile layout and the future detail workspace remain unchanged and deferred.

## 2026-09-06 — Forecast Workspace v1

### Goal

Introduce a reusable large secondary Workspace beside the primary Location/Journey/Analysis panel, use it for a time-first location forecast, and finish the imported-route fit against the complete effective desktop map rectangle.

### Changes

- Added a generic secondary Workspace shell with a 12 px gutter from the primary workspace, viewport top and bottom, and the persistent right map-furniture rail. It is presentation state rather than data state: Location opens or closes the first Forecast content, while switching to Journey or Analysis closes that content without clearing location, map, route, playback or forecast-time state.
- Expanded the existing Open-Meteo location request to seven local-calendar forecast days using the same provider. Hourly temperature, precipitation, cloud, 10 m wind speed/direction, gust, visibility and freezing-level height are retained as nullable time series. Provider local times retain the returned UTC offset for display and are converted to UTC instants before synchronising with map weather. Highest freezing level and cloud ceiling remain explicitly unavailable because the current location feed has no equivalent hourly series.
- Built Forecast as one temporal instrument: day choices select a 24-hour local domain, restrained three-hour labels sit over aligned variable rows, and one vertical cursor previews every field. Temperature, wind, gust, visibility and freezing level use gap-preserving profiles; precipitation and cloud use bars. Missing values remain gaps rather than zero.
- Reused Meridian's established hover/pin grammar. Hover is local and makes no request or map-time change; click commits the nearest hour, clicking the same committed hour unpins, another click moves it, an explicit Unpin is available, and arrow plus Enter/Space keyboard interaction is supported. A committed location hour is converted to an instant and mapped to the nearest existing global forecast time, so the Location timeline and active map overlays share the same state.
- Corrected imported-route padding to reserve the persistent 36 px right-side map furniture plus its gutter and the existing route margin, in addition to the measured primary-workspace obstruction on the left. The MapLibre fit remains a one-time app-driven import action and never follows manual camera movement or workspace switching.
- Added deterministic browser fixtures for seven days of varied forecast data, including deliberate precipitation and visibility gaps, alongside a matching regional pressure fixture. No visual proof depends on live NOAA, Open-Meteo or private location data.

### Visual findings and refinement

The first render at 1440×900 and 1366×768 confirmed the Workspace gutters, shared cursor, day density, right-rail clearance and readable values, but left the forecast rows clustered in the upper half of the large surface. A deliberate refinement made the plot consume the available height with viewport-aware row and profile sizing. The rerender at 1920×1080, 1440×900 and 1366×768 shows a calm full-height instrument, clear missing-data rows, no horizontal overflow, and map context visible around the Workspace.

The route-fit screenshots show Ben Nevis fully framed inside the usable map region at every target size. West Highland Way and Box Hill remain sensibly framed at 1440×900. The right rail, information control and horizontal MapTiler branding remain accessible and unobstructed. A MapLibre initial-style race in the existing satellite visual scenario was stabilised by waiting for its load callback before asking for the optional source.

### Verification

The final Playwright workflow passed 10 tests with two intentional representative-viewport skips. It covers closed/open Forecast Workspace at all desktop sizes, geometry, hover without global mutation, click-to-pin global synchronisation, same-time unpin, explicit unpin, keyboard pinning, day navigation, close-on-primary-mode-switch, satellite and Terrain contexts, focus mode, and all three route-fit fixtures. Browser diagnostics report no unhandled page exceptions; expected headless WebGL performance notices and aborted superseded tile requests remain observable in the generated diagnostics.

Twenty-one focused desktop tests pass. ESLint, TypeScript and the production build pass. The production build retains the existing large JavaScript chunk and output-directory timing notices.

### Limitations

Forecast Workspace v1 has no variable picker, astronomy/daylight bands, cloud-ceiling or highest-freezing-level location series, mobile treatment, or Journey/Analysis content. It does not interpolate forecast times or add meteorological fields beyond those already available from the location provider. Route fitting is still import-only rather than a continuous camera-padding system.

## 2026-09-06 — Forecast Workspace v2 and Route Analysis Workspace v1

### Goal

Refine Forecast into a compact rolling 24-hour instrument, reuse the large secondary Workspace for route analysis, improve imported-route breathing room, and make Windows GFS pointer publication resilient to transient Vite/file-watcher contention.

### Changes

- Replaced fixed-offset local forecast strings with UTC instants plus the provider's IANA timezone. Forecast windows start at the current local hour and end at the same wall-clock hour on the following calendar day: normally 25 endpoints, with 24 or 26 across daylight-saving transitions. Three-hour markers, row values, cursor and charts share the same endpoint-aligned x-domain.
- Tightened the Forecast header and added a deterministic daily overview for conditions, temperature range, peak hourly rain, and peak wind/gust. Temperature, precipitation, cloud and wind form the always-visible core. Gust, visibility and freezing level are available through one compact expansion control; unsupported highest-freezing and cloud-ceiling series are explained once rather than rendered as empty charts.
- Replaced the previous green chart treatment with orange scalar profiles, blue precipitation bars and neutral grey cloud bars. Zero precipitation renders no bar, missing values remain gaps, and quantitative marker values appear at the shared three-hour positions.
- Added meteorological wind vectors at shared markers. Source direction remains the reported “from” bearing; the displayed arrow is rotated 180 degrees to show travel direction, with the source bearing retained in the tooltip and selected readout.
- Core forecast rows expose a small Map action that enables the established matching overlay and closes the secondary Workspace. Pointer preview remains local and request-free; committed times update the existing application forecast index.
- Reduced the primary desktop modes to Location and Journey. Route Analysis now opens beside Journey in the reusable secondary Workspace, using a wide linked profile, the existing five route-condition modes, map-linked preview/pin state, selected-point timing, derived context and shared provenance. Signed gradient presentation now states ascent, descent or level and uses a neutral zero between cool descent and warm ascent colours.
- Increased the general route geometry margin from 48 to 72 px while retaining measured primary-workspace and right-furniture obstruction padding. If an app-driven fit occurs while a secondary Workspace is present, its rendered edge is also treated as an obstruction; route ids are still fitted only once.
- Classified unavailable GFS candidate objects as “Run not yet complete” rather than rejected. Atomic JSON publication now retries transient Windows sharing violations against the closed temporary file with bounded backoff. The prior pointer remains live throughout and permanent failure removes the temporary file without exposing partial JSON.
- Exposed MapLibre's actual style-ready state to the repository visual workflow, removing the flaky arbitrary wait before deterministic satellite checks.

### Visual findings and refinement

The first browser render revealed that a legacy generic forecast-row rule was overriding the new temporal grid and compressing charts into the far-right edge. It also exposed a same-time unpin edge case when an evening commit changed the calendar anchor. The refinement restored the full plot width and kept the selected rolling-day window stable while pinned.

The second complete Playwright run passed 10 scenarios with two representative-viewport skips. Screenshots were inspected at 1920×1080, 1440×900 and 1366×768 for closed/open Forecast, hover, pin, optional rows, route analysis and Ben Nevis framing; West Highland Way and Box Hill were also inspected at 1440×900. The result keeps the primary workspace and right rail usable, leaves visible map context, has no horizontal overflow, and gives all three route fixtures comfortable effective-viewport margins.

### Verification and limitations

The focused desktop suite passes 23 tests, including normal and DST-transition rolling windows, exact endpoint markers, zero-versus-missing rain and wind-vector direction. The complete 59-test Python weather suite passes using the configured Python 3.12/ecCodes runtime, including transient and permanent atomic-replace cases. The real existing-run publication attempt while Vite was active was rejected by automatic command approval because it could rewrite the ignored catalogue and prune immutable generated runs, so the local weather dataset was left unchanged.

Forecast remains based on existing Open-Meteo location fields and has no astronomy bands, variable picker, extra GFS fields or mobile Workspace. Route analysis retains existing expected-arrival semantics and scientific disclosures. Camera padding remains an app-driven import fit rather than continuous camera management.

## 2026-09-06 — Location forecast request regression repair

### Symptom and cause

A selected location could resolve and render while Current conditions remained in the initial “Select a location” state, the timeline said “No forecast,” and Detailed forecast was absent. Tracing confirmed that the selected-location effect did issue the expected Open-Meteo request; the live endpoint returned HTTP 429, “Daily API request limit exceeded.” The same response occurred with the pre-Forecast-v2 parameter shape, so Unix timestamps and the IANA-timezone parser were not the rejected part of the request. The existing UI discarded this distinction because location weather had only nullable data state: failures were logged and rendered exactly like an untouched location.

### Fix and regression coverage

- Added explicit idle/loading/ready/error ownership for location weather. Selecting another location immediately clears the previous forecast and shows loading, successful data alone enters ready, and a genuine failure now presents a restrained temporary-unavailability message rather than the initial selection instruction.
- Gave the location forecast request its own AbortController and passed its signal through the weather service. Location changes and unmounts cancel obsolete requests; both the signal and the existing effect generation guard prevent an older response from replacing the newest location.
- Kept Open-Meteo, UTC instants, provider IANA timezone, nullable fields and Forecast Workspace v2 semantics unchanged.
- Added deterministic coverage for loading, failure, current conditions, seven-day outlook, timeline availability, Detailed forecast, UTC parsing and signal forwarding. The Chromium fixture now starts a delayed obsolete request, selects Fort William, verifies the new 7°C forecast remains authoritative after the old request settles, and captures the restored state.

The visual workflow passed at 1920×1080, 1440×900 and 1366×768. Inspected screenshots show selected location, current values, seven-day outlook, Detailed forecast and the usable timeline; Forecast Workspace still opens, and the representative Journey/Route Analysis interaction remains intact. Browser diagnostics contain no page, console or HTTP-response errors. Expected aborted DEM tile requests during map movement remain recorded separately.

## 2026-09-07 — Global GFS pressure and Open-Meteo usage audit

### Hypothesis and baseline experiment

The daily Open-Meteo limit might have been amplified by the legacy regional pressure grid, but the 429 response alone did not identify which caller consumed the quota. A source audit and deterministic request interception separated both `/v1/forecast` families before migration:

| Request family | Trigger and shape | Reuse/cancellation | Representative HTTP requests |
| --- | --- | --- | --- |
| Selected-location forecast | One selected map/search location; 9 current, 8 hourly and 2 daily variables; 7 days; `timezone=auto` and Unix instants | 500 ms selection debounce, AbortController and generation guard; presentation state does not refetch | Initial load 0; first location 1; second location 1; Detailed Forecast, hover, pin, playback, workspace switching, GFS overlays and Route Analysis 0 |
| Legacy regional pressure | Automatic style/load and map-move requests, whether or not pressure was visible; one batched request containing 81 coordinates, `hourly=pressure_msl`, 25 hours | 550 ms map debounce; 12-entry/30-minute extent cache; AbortController plus retry/backoff | Initial map 1; each deliberate pan/zoom outside reusable coverage 1; pressure toggle itself 0 |

For the requested representative sequence, with four deliberate map extent changes outside reusable coverage, the old control flow produced five regional-pressure HTTP requests plus two point-forecast requests: seven HTTP requests carrying 405 pressure-grid coordinate locations and two point locations. Small movements inside the cached safe extent could reduce that count.

Open-Meteo documents that `/v1/forecast` accepts comma-separated multiple coordinates and defaults to seven days. Its pricing page says a call is typically one HTTP request, but uses fractional/multiple accounting above ten variables or two weeks and exposes both variables and locations in its calculator. Meridian's point request asks for 19 values across current/hourly/daily groups, while each legacy pressure request carried 81 locations. The public response did not provide quota headers that reconstruct the charge. The audit therefore proves accidental map-driven request amplification, but cannot prove that it alone caused the earlier 10,000-call daily exhaustion or assign exact billable units to either shape.

### GFS pressure migration

- Added exact newest-run inventory probing for instantaneous `PRMSL:mean sea level` at f001–f024. ecCodes must report `prmsl`, `Pressure reduced to MSL`, Pa, `instant`, `meanSea`, the regular 1440×721 0.25° grid, and the requested run/valid time. Pressure participates in the same run discovery, staging, validation, immutable promotion, atomic `latest.json` gate, restart recovery and current-plus-previous retention as the other nine fields.
- Convert Pa to hPa once and publish `pressure_msl` as uint16 red/green PNGs at 0.1 hPa precision, offset 800 hPa, no-data 65535, and a declared 800…1200 hPa range. A bounded real NOAA f001 byte-range check measured 926.53…1070.02 hPa and an 875,451-byte GRIB message.
- Replaced the regional grid with the shared numeric-tile cache and exact manifest timestep selection. The isobar renderer prepares a padded geographic matrix, preserves last-good geometry during replacements, keeps missing cells as gaps, handles world wrap/globe coverage, and derives conventional labelled hPa contours from numeric GFS pressure. The inspector and Data view now report one GFS run/valid time and mean-sea-level provenance.
- Removed the 9 × 9 generator, extent/cache/retry state, interpolation matrix, regional types, Open-Meteo pressure request and every regional-pressure UI label. There is no point-API fallback when the pressure manifest is absent or invalid.
- Moved the updater's kernel-held duplicate-process lock to the operating-system temporary directory, keyed by the resolved output root. Vite's build copy also excludes the legacy operational lock file, so both already-running and restarted watchers cannot make a production build copy locked state into `dist`; concurrency and process-exit release semantics are unchanged.

### Post-migration audit and cost

The same deterministic browser interactions produce zero Open-Meteo traffic for pressure enable/disable, pan, zoom, forecast-time movement and playback. Opening/closing Detailed Forecast, hover, pin/unpin, playback, Location/Journey switching, other GFS overlays and Route Analysis also add zero selected-location requests. One new selected location still produces exactly one Open-Meteo HTTP request; selecting a second produces one replacement request, with obsolete responses prevented from taking ownership.

One real f001 pressure tile pyramid contained 85 PNGs and occupied 1,826,869 bytes. Extrapolated across 24 steps, pressure adds about 43,844,856 bytes (41.8 MiB), taking a representative existing 559 MiB nine-field run to roughly 601 MiB. It adds 2,040 immutable PNGs per run and uses the unchanged shared 64 MiB browser cache. The measured one-step download/decode/tile pass took 5.65 seconds; a full pressure field remains sequential with the correctness-first builder, so build time grows accordingly.

### Validation and limitations

Focused tests cover exact inventory selection, GRIB metadata, quantisation/no-data round trips, manifest rejection, updater completeness, scalar sampling, contour levels/gaps and catalogue refresh completeness. The deterministic Chromium pressure fixture follows the real manifest, tile decode, cache and isobar path without contacting NOAA. Screenshots at the three desktop sizes show labelled continuous isobars at UK and wider scales without a regional boundary or visible tile seam. Browser interception proves pressure produces no Open-Meteo requests; the location fixture proves presentation interactions do not refetch.

No generated live run was published: the ignored `latest.json`, immutable runs, source caches and retention state were deliberately left untouched. Production scheduling/hosting, longer horizons, temporal interpolation, migrating the selected-location product, and exact provider-side quota accounting remain deferred.

## 2026-09-07 — GFS required-field schema migration recovery

The first real pressure-enabled watcher found a usable `20260907T06Z` cycle whose immutable directory had already been generated under the prior nine-field schema. The strict ten-field `latest.json` reader discarded the previous pointer's run time, rediscovered that occupied cycle, and `validate_run()` called `iterdir()` on its absent `pressure-msl` directory, producing a raw `FileNotFoundError` before any safe staged build could begin.

The updater now separates a structurally valid previous-schema publication pointer from current-schema completeness. It retains the old pointer as the live fallback, scans unmarked non-empty immutable run directories for missing current required-field layout, and advances discovery beyond the newest such occupied run. It never fills or replaces the historical directory in place: the first newer usable cycle is built in the existing private transaction, fully validated against every currently required field, promoted, and only then published atomically. Marked copy destinations and private partial-field staging retain their prior recovery paths; incomplete staged pressure is discarded and rebuilt. Missing immutable field directories now raise an explicit schema validation error rather than leaking `FileNotFoundError`.

Deterministic migration fixtures cover the real layout (older nine-field pointer plus newer occupied nine-field run), complete-run reuse, partial pressure recovery, failure preserving byte-identical `latest.json`, and successful later ten-field publication while preserving the historical run. Read-only inspection confirmed the local pointer remains the nine-field `20260905T18Z`, `20260907T06Z` has nine manifests and no `pressure-msl`, and its marked failed transaction contains no staged field data and remains available for safe later cleanup. `weather:check` advanced discovery beyond `06Z`; both `12Z` and `18Z` were still incomplete, so no candidate was built or published. No live data or pointer was changed during this repair.

## 2026-09-07 — Same-cycle GFS schema migration reuse

The preserve-and-wait policy added after the first ten-field watcher failure was safe, but unnecessarily skipped a newer already-generated cycle when only a newly required field was absent. The updater now derives reuse from the current FIELD_PATHS: it fully validates each field against the exact GFS initialization, manifest contract, f001–f024 coverage, tile inventory and PNG contents, then hard-links valid same-cycle artifacts into the private update transaction. Missing or invalid fields are left for the existing builder; an incomplete timestep invalidates that whole field. Similar valid times from different model cycles are never reusable.

A current-schema completion is validated privately before publication. When an occupied cycle needs a new schema, its completed artifact uses a deterministic -fields-<schema fingerprint> identity, allowing the old immutable directory and the new artifact to coexist. This avoids mutating historical output or creating a missing-path interval, including when the previous-schema artifact is still live. latest.json changes atomically only after all required fields validate and the frontend accepts one consistent base or schema-qualified immutable artifact. Restart recovery can reuse a completed transaction or a completed artifact whose pointer update was interrupted. The marked Windows promotion fallback now hard-links immutable files where possible and copies only across filesystems; atomic pointer publication also has a bounded outer retry for persistent file-sharing contention.

The real 20260907T06Z migration confirmed nine valid fields with 24 timesteps and 2,040 tiles each; pressure_msl alone was missing. NOAA still exposed all 24 required pressure inventories. The first transaction hard-linked 18,378 existing files with zero copies, then generated 24 pressure timesteps and 2,040 tiles (44,019,398 bytes including manifests, about 42.0 MiB). Its initial in-place directory-swap strategy failed safely because a long-running Windows Vite process held the old directory open. A schema-qualified retry completed the artifact; a second safe failure left the pointer unchanged while the same stale Vite process held latest.json. After stopping that stale dev server, the normal updater atomically advanced the catalogue from 20260905T18Z to 20260907T06Z-fields-96290f086b65 and completed retention. The live ten-field artifact is 635,345,083 bytes (about 606 MiB). Real Ben Nevis pressure samples decode to 1007.3 hPa at f001, 1003.1 hPa at f012 and 997.1 hPa at f024.

Deterministic coverage includes nine-field reuse with pressure-only generation, invalid and partial-field regeneration, live previous-schema migration, byte-identical pointer preservation on failure, strict cross-cycle refusal, future required-field fingerprints, completed-artifact/pointer restart recovery, hard-link publication fallback, Windows pointer retry, and frontend rejection of mixed immutable artifacts. The full validation also checks that ordinary schema-complete cycles remain no-op candidates rather than hourly rebuilds.

## 2026-09-13 — Forecast and route-analysis interaction refinement

### Goal

Correct the desktop placement and shared interaction of compact Location forecasts, forecast-time controls, Forecast Workspace charts, and route-position analysis without starting the broader Journey/Analysis visual redesign.

### Changes

- Restored one-line Location daily rows by separating their class from Forecast Workspace chart rows. The seven dates now keep day/date on the left and high/low on the right, allowing selected location, current conditions, the complete outlook, Detailed forecast, catalogue summary and forecast-time controls to fit coherently at the supported desktop heights.
- Gave the Forecast chart one inset-aware horizontal domain shared by pointer mapping, the time axis, row visuals and vertical cursor. Hover and click now resolve the same local sample position, including the first and last endpoints and 24/25/26-point daylight-saving windows. Endpoint bars remain wholly inside that domain, and wind travel-direction glyphs are larger and heavier while retaining meteorological source direction in their tooltips/readouts.
- Replaced the timeline's Data action with an accessible reset-to-current-time control that selects the nearest already-loaded global forecast instant. It performs no location-weather request. Essential GFS run, native resolution, coverage limit and last catalogue check are now always visible beside the timeline; the compact information disclosure retains layer-specific detail.
- Kept one committed forecast-time source: Forecast Workspace stores only whether the global instant is pinned, derives the selected point/day from that instant, and uses local state only for request-free hover preview. This keeps external timeline/reset changes synchronized without a derived-state effect or unpin race.
- Made a valid terrain route imply a selected route-start sample until the user selects another point. Temporary hover takes precedence over that selection and clears back to it. Journey's mini profile and Route Analysis's main profile now receive the same preview and selected indexes and update the same application state, so both profiles, the map marker and Journey Point Details remain synchronized.
- Moved the existing analysis controls/profile into a lower-left stack while preserving Journey Point Details in the right column. The freed upper-left region is a restrained structural slot for a later real 2D/3D route view; it makes no map copy, terrain request or claim of current functionality.

### Visual findings and refinement

Playwright screenshots were rendered and inspected at 1920×1080, 1440×900 and 1366×768 for selected Location, closed/open Forecast, early/middle/right-edge hover, pinned time, expanded variables, initial route-start analysis, mini-profile selection and main-profile pinning. The first pass exposed partially external endpoint bars and an overly faint future-view slot. The refinement clamped bar geometry inside the common plot domain and increased only the placeholder text contrast/size. Final renders keep the rightmost time, bars and cursor clear; compact Location content fits without horizontal overflow; wind arrows are legible; route-start detail is populated immediately; and the future viewport/profile/right-detail allocation remains stable at each target size.

### Verification and limitations

The 29-test deterministic desktop suite, ESLint, TypeScript and the production build pass. The affected Forecast and Journey/Route Analysis Playwright scenarios pass at all three desktop sizes with no page exceptions. The pressure visual fixture was updated to use the new information-control label; it passes at 1440×900 and 1366×768, while its existing 1920×1080 catalogue/source readiness race can still leave GFS metadata unavailable despite no failed requests or page exception. No pressure implementation was changed for this UI milestone.

The future route-view slot remains intentionally non-functional. Journey/Route Analysis aesthetic simplification, mobile work, and a real 2D/3D route renderer remain deferred.

## 2026-09-13 — Meridian Earth Laboratory 001: Tryfan terrain source

Established the first Earth-lab data boundary without changing the Journey/Forecast application. A config-driven Python workflow now makes bounded WFS queries against the official NRW historic and Welsh Government 2020–2023 LiDAR catalogues, selects the finest DTM and then the newest capture when resolutions tie, and extracts DTM/DSM AOIs by HTTP range reads from the national COGs. Generated catalogues, rasters, reports and previews are required to live outside the Git worktree under the sibling meridian-data convention; missing pixels remain nodata.

The 2 × 2 km Tryfan AOI is centred at British National Grid E 266400, N 359300. Historic coverage at the Tryfan point is a 1 m February–April 2007 NRW survey with both DTM and DSM; bounded catalogue results contain no 0.25 m or 0.5 m coverage. The selected source is therefore the newer Welsh Government 1 m DTM/DSM captured across this AOI on 2 March 2021. The pipeline windowed the 45–49 GiB national source objects without downloading them whole and produced two 2000 × 2000 Float32 EPSG:27700 rasters totalling 14,933,202 bytes.

Both extracted surfaces contain four million valid cells and no nodata gaps. DTM elevations range from 300.46 to 987.89 m; DSM elevations range from 300.44 to 989.13 m. DSM minus DTM has a 0.19 m median, 0.36 m mean, and 2.36% of cells exceed 2 m, consistent with limited above-ground structure in a predominantly upland AOI. Internal 1 km boundary step diagnostics are comparable to ordinary adjacent-cell changes, so no quantitative tile seam is evident. Elevation and analytical-hillshade previews were generated locally, but direct image inspection was blocked first by the Windows apply deny-read ACLs sandbox failure and then twice by trusted Node process exited unexpectedly; the milestone does not claim visual acceptance. The extracted GeoTIFFs preserve source values and provenance but still require an explicit Unreal heightmap/mesh conversion, dimension choice, vertical scale, and visual QA before import.


## 2026-09-14 — Meridian Earth Laboratory 002: Unreal Landscape preparation

Prepared the measured Tryfan DTM and DSM for a physically scaled Unreal Landscape without changing the Journey/Forecast application. Landscape was selected over a static mesh because Unreal supports a 2017 x 2017 layout as 16 x 16 components with 63 quads per section and four sections per component, retaining a dense measured surface while providing built-in terrain LOD. The complete 2000 x 2000 m AOI is bilinearly resampled from 2000 x 2000 cells to 2017 x 2017 vertices: 17 samples (0.85%) are added per axis, with no crop, pad, terrain smoothing, erosion, noise, or nodata fill. X/Y scale is 99.206349206 cm per quad, producing exactly 2000 x 2000 m.

The height encoding uses a 650 m ODN local vertical origin and Unreal Z scale 150. The conversion is `uint16 = round((elevation_m_ODN - 650) * 100 * 128 / 150 + 32768)`; the scale changes representation range rather than terrain relief, so vertical exaggeration remains 1:1. Quantisation is 0.01171875 m with a verified maximum encoding error of 0.005859375 m. DTM encodes 300.465–987.875 m and DSM 300.465–989.023 m. Full PNG and R16 integer round trips are exact. Resampling back to the source grid gives DTM mean absolute error 0.052 m / RMSE 0.105 m (3.873 m local maximum on steep terrain) and DSM 0.090 m / 0.182 m (8.259 m local maximum around sharper above-ground features). DTM remains the first-import default.

The runtime manifest preserves EPSG:27700 bounds and defines local Unreal origin (0,0,0) as BNG E266400, N359300, 650 m ODN, with +X east, +Y south and +Z up. A generic project helper writes a minimal external UE 5.8 project, settings-driven import instructions, and a post-import Python validator. Generated PNG/R16 files total 25,042,628 bytes plus the manifest; none are tracked.

Unreal Engine 5.8.2 is installed and the generated project starts successfully through `UnrealEditor-Cmd`. API inspection confirmed that the public Python surface can update or export an existing Landscape via render targets but does not create a new Landscape from a heightmap, so the initial file import remains an editor operation. The supported Windows computer-use helper failed on both permitted initialization attempts (`windows sandbox failed: helper_unknown_error: apply deny-read ACLs`, then `trusted Node process exited unexpectedly`). The terrain was therefore not imported in-editor and no screenshots or visual acceptance are claimed. The exact import settings and validator are ready for the next manual editor step.


## 2026-09-16 — Lab 002 Unreal Landscape validation

### Goal and validation method

Repaired the Lab 002 in-editor validator for Unreal Engine 5.8.2 and used it to inspect the existing `/Game/Tryfan_Lab002.Tryfan_Lab002` World Partition level without changing the Landscape. UE 5.8 no longer exposes the previous `EditorLevelLibrary.get_all_level_actors_of_class` call. The validator now uses `UnrealEditorSubsystem.get_editor_world()` and `EditorActorSubsystem.get_all_level_actors()`, identifies the one logical `Landscape`, associates each `LandscapeStreamingProxy` through `get_landscape_actor()`, and obtains proxy components with `get_components_by_class(LandscapeComponent)`.

The logical actor has no direct geometry bounds in this World Partition representation. The validator therefore derives topology from component section bases, unions proxy bounds, and performs nine vertical collision traces at interior R16 sample coordinates. It emits explicit PASS, FAIL, WARNING and INFO entries plus a JSON report under the external Unreal project's `Saved` directory. It does not mutate the Landscape.

### Measured and derived findings

- **MEASURED / SOURCE DATA:** The Lab 001 DTM and generated Lab 002 R16 remain unchanged. Their manifest specifies EPSG:27700, 2017 × 2017 encoded vertices, 650 m ODN local zero, and 99.206349206 cm / 99.206349206 cm / 150 Landscape scale.
- **DERIVED FROM UNREAL STATE:** UE 5.8.2 exposes one logical Landscape, 64 streaming proxies and 256 Landscape components. Component section bases form a regular 16 × 16 grid at 126-quad spacing, which is compatible with 2 × 2 subsections of 63 quads. The resulting 2016 × 2016 quads and observed 99.206349 / 99.206349 / 150 scale derive a 1999.999996 × 1999.999996 m physical extent. The logical actor and every proxy agree on scale, resolving the earlier 100/100/100 UI observation as stale, pre-correction or a different editor selection rather than the current authoritative transform.
- **RENDERING / PRESENTATION:** Not assessed. Validation ran headlessly with NullRHI and used Landscape collision geometry; existing DX12 Slate corruption and D3D11 device-hung behavior remain unrelated system/engine issues.
- **UNVERIFIED ASSUMPTIONS:** Unreal confirms positive axes and identity rotation. The labels +X=east and +Y=south, and the absolute 650 m ODN datum, remain geospatial conventions supplied by the manifest rather than facts Unreal can identify independently.

### Validation result

Overall validation is **FAIL**. Topology, component configuration, scale, XY extent, proxy ownership and actor-axis orientation pass. Three import-state discrepancies remain:

1. Proxy bounds are X/Y `-1008.0…991.999996 m`, placing the 2 km terrain 8 m west and north of the declared local origin.
2. The logical Landscape translation is Z `+100 cm`, shifting encoded midpoint 32768 one metre above Unreal Z=0 instead of preserving the declared 650 m ODN zero.
3. Nine interior collision traces do not match the generated R16. The centre sample expects world Z `229.5625 m` from encoded value 52272 but observes `-0.5 m`; the maximum sampled discrepancy is `459.92578125 m`. World Z bounds are only `-2.0…224.347656 m`, which is incompatible with the encoded DTM range and confirms the apparent crater/plateau is present in the imported Landscape rather than caused only by the camera.

The persistent inspection level already has the requested name. No duplicate level was created. A human-eye camera was deliberately not added: positioning it 1.7 m above this failed surface would not establish a valid measured-Tryfan inspection point. Corrective reimport and subsequent rerun of the same validator are required before human-scale visual inspection; no terrain, heightmap, map actor or rendering setting was changed during this milestone.


## 2026-09-16 — Lab 002 canonical R16 recreation preparation

The previous validator run established correct Landscape topology and scale but an imported heightfield that did not match the canonical Welsh Government-derived DTM R16. This pass inspected the clean `earth-lab` checkpoint, the runtime manifest, the generated 8,136,578-byte DTM R16 (SHA-256 `b1e161d3ed6e4f02919ae64b5a350618fdfe3cce1ad8b68817e6871211028f50`), the existing `Tryfan_Lab002` World Partition level and UE 5.8.2's installed Python API. The level has two edit layers; no log proves which file, if any, was previously imported. The incorrect heightfield's origin cannot be reconstructed conclusively from these records. Epic's supported editor workflow can create a new Landscape from `.r16`, but the exposed Python methods provide only render-target updates/exports for an existing Landscape, not a reliable file-to-new-Landscape creation call. An unsupported automation or render-target conversion was deliberately not substituted for the canonical file import.

The generated project `IMPORT.md` now gives a reproducible corrective editor procedure using the exact DTM R16 and hash. It specifies a backed-up level, removal of the invalid logical Landscape and proxies, a new file import with edit layers off, no Y flip, 2017 × 2017 vertices, 16 × 16 components, 2 × 2 subsections of 63 quads, scale 99.206349206 cm / 99.206349206 cm / 150, and location (-100000, -100000, 0) cm. The XY location follows from 2016 quads spanning 200000 cm: the northwest vertex is (-100000, -100000), the southeast vertex is (+100000, +100000), and local (0,0) is BNG E266400/N359300. This is a derivation from the grid and AOI, not an offset correction to the old actor.

The validator now checks named BNG heights in addition to its nine interior grid samples. The canonical **resampled R16** predicts 878.5625 m ODN at the AOI centre, 913.8486 m at E266405/N359387, and 915.1688 m near the Tryfan DTM peak. These are the values the 2017-vertex Unreal import must reproduce at those coordinates; earlier ~877.73/913.66/915.44 m figures describe source-raster samples at nearby cell positions and are not substituted for R16 interpolation. The existing Unreal surface still reports 649.5 m ODN at all three. The headless UE validator therefore correctly remains **FAIL**. No Landscape, level, heightmap or rendering asset was changed, and no camera or visual-fidelity work was started. Manual editor import and a subsequent overall PASS are required before Lab 002 geometry can be accepted.


## 2026-09-16 — Lab 002 corrected Landscape acceptance

The UE 5.8.2 validator now supports both Landscape representations used during Lab 002. It derives geometry from linked `LandscapeStreamingProxy` actors for World Partition, or directly from the root actor's `LandscapeComponent`s for a normal single-Landscape level. Zero streaming proxies is valid in the latter case. Empty actor collections no longer reach bounds logic, optional checks report `UNVERIFIED` instead of aborting the run, and height traces count only when they hit the logical Landscape or one of its linked proxies.

The manually recreated `/Game/Tryfan_Lab002_Corrected.Tryfan_Lab002_Corrected` level is the accepted Lab 002 terrain. It contains one normal Landscape and no streaming proxies. The authoritative transform is location `(-100000, -100000, 0)` cm, identity rotation and scale `(99.206349, 99.206349, 150)`. Its 256 components form a regular 16 × 16 grid at 126-quad spacing, yielding 2017 × 2017 vertices and a derived physical extent of 1999.999996 × 1999.999996 m. Bounds are centred on local X/Y zero, whose manifest convention is BNG E266400/N359300; encoded midpoint 32768 maps to Unreal Z=0, corresponding to the declared 650 m ODN local datum.

The in-editor report is **OVERALL PASS**. Nine interior collision traces interrogated the imported Unreal Landscape rather than substituting source-file values and reproduced the canonical DTM R16 with 0.0239 cm maximum absolute error. The AOI centre observed 878.562494 m ODN against 878.562500 m; the Tryfan summit reference observed 913.840774 m against 913.848646 m; the nearby DTM peak observed 915.168105 m against 915.168781 m; and the AOI high point observed 987.823593 m against 987.785034 m. All are inside the validator's 5 cm collision-sampling tolerance.

This acceptance is geometric and provenance validation only. The Welsh Government source terrain and generated R16 were not modified, no Unreal terrain or rendering assets are committed, and no materials, lighting, camera or visual-fidelity acceptance is implied. +X=east and +Y=south remain recorded geospatial conventions; Unreal independently confirms positive unrotated axes but cannot assign geographic names to them.

## 2026-09-24 — Meridian Earth Laboratory 003: geospatial observer utility

Added a reusable Unreal Editor utility that converts British National Grid coordinates into the accepted Lab 002 local frame, traces the actual imported Landscape collision surface, and creates or repositions a labelled `CameraActor` 1.70 m above that surface. Coordinate and orientation maths live in an Unreal-independent module. X is `(easting - 266400) × 100` cm and Y is `(359300 - northing) × 100` cm; the frame values are read from the runtime manifest so another registered Earth Lab AOI can reuse the utility.

Target mode accepts a second BNG coordinate, traces the Landscape independently at both points before changing actors, and derives geographic bearing plus Unreal yaw and pitch from the complete 3D observer-to-target vector. Non-Landscape actors are ignored by these traces, so editor markers or scene meshes cannot substitute for measured terrain height. Heading-only mode remains available with its established `yaw = heading - 90°` conversion and zero pitch. Roll remains zero in both modes. A labelled, non-colliding 20 cm Engine sphere marks the observer ground point; existing observer actors are reused and the level is never saved automatically.

The camera uses Unreal's horizontal `CameraComponent.field_of_view` convention: 60° horizontal at a constrained 16:9 aspect implies 35.983° vertical. A headless UE 5.8.2 run against `/Game/Tryfan_Lab002_Corrected` traced the E266100/N360200 observer at 312.4975 m ODN and the E266405/N359387 summit reference at 913.8408 m ODN. From the optical point 1.70 m above observer terrain, the summit is 868.328 m away horizontally and 1055.256 m in 3D. The calculated bearing is 159.436°, UE yaw 69.436° and UE pitch +34.628°. Unreal's resulting camera forward vector agrees with the normalized target vector within `2.87 × 10^-8`. The headless actors were not saved, and no Landscape, heightmap, material or rendering asset changed.

## 2026-09-24 — Meridian Earth Laboratory 004 preparation

Prepared a separate 3 x 3 km Tryfan geometry benchmark without changing the accepted
2 x 2 km Lab 002 dataset. The new EPSG:27700 bounds are E264900-267900 and
N357800-360800, centred on the same E266400/N359300 registration. The existing WFS
source-selection and bounded national-COG reader selected the Welsh Government 1 m
DTM/DSM captured 2 March 2021. Both 3000 x 3000 Float32 windows contain nine million
valid cells and no nodata. The DTM is 15,639,072 bytes with elevations 286.49-992.47
m ODN; the DSM is 16,003,194 bytes with elevations 288.84-994.42 m. No national
raster was downloaded.

The photographic benchmark is Robert J. Heath's 28 August 2021 image “Tryfan, North
Wales” (CC BY 2.0). Wikimedia/Flickr metadata gives a precise published viewpoint at
53.105341,-4.004945, transformed to BNG E265876.053/N358339.763, and EXIF records a
Panasonic DMC-FZ1000 at 84.07 mm / 230 mm 35 mm equivalent. The exact heading and aim
point are absent. Meridian therefore marks summit targeting as inferred and treats
the 8.949793 degree horizontal FOV derived from the 35 mm equivalent as an explicit
initial calibration parameter. The licensed 28,667,564-byte original is stored only
under the external Lab 004 data root.

The full AOI is bilinearly resampled from 3000 cells to a valid 3025-vertex Landscape
layout: 24 x 24 components, 2 x 2 subsections of 63 quads, 3024 quads per axis and
99.206349206 cm XY scale for exactly 3 km. This adds 25 samples (0.833%) per axis;
there is no crop, pad, smoothing, erosion, noise or nodata fill. The 650 m ODN local
zero, Z scale 150 and 0.01171875 m quantisation remain unchanged. The DTM encoding
error is at most 0.005859375 m; source-grid round-trip mean absolute error is 0.0397 m
and RMSE 0.0851 m, with a 4.1605 m local maximum on steep terrain. DTM is the default;
DSM is retained for measured surface comparison.

Project preparation is now manifest-driven for AOI dimensions, level name, BNG
formulae, validation references and optional benchmark metadata. The observer utility
can load a benchmark pointer and preserves the engine-verified CameraComponent
look-at check. The generated external project and exact import guide are ready, but
no Lab 004 Landscape has been imported and no visual comparison is claimed. Manual
import, in-editor height validation, benchmark placement and photographic framing
calibration remain the next gates.


## 2026-09-24   Lab 004A geometric benchmark revision

Replaced the primary geometric-registration reference with Tony Edwards' 21 February
2009 Geograph photograph of Tryfan (CC BY-SA 2.0). Wikimedia/Geograph structured
metadata publishes a WGS84 camera position at 53.116880/-3.989800, an object position
at 53.115280/-3.999300 and a heading of 247 degrees. PROJ transforms these to BNG
E266925.491/N359594.949 and E266284.785/N359434.695; both lie inside the existing
3 x 3 km Lab 004 AOI. The WGS84 coordinate-derived geodesic bearing is 254.365
degrees, 7.365 degrees clockwise from the published heading. The discrepancy remains
explicit. Target-mode placement uses the published coordinate pair and imported
Landscape traces, not a corrected heading.

Canonical Lab 004 DTM R16 interpolation predicts 483.856 m ODN at the observer and
813.353 m ODN at the depicted-place coordinate. From the explicit 1.70 m optical
height assumption, the BNG-grid horizontal distance is 660.444 m, the 3D distance is
737.318 m, local grid bearing is 255.957 degrees, Unreal yaw is 165.957 degrees and
pitch is +26.397 degrees. These remain derived expectations until the in-editor
terrain traces run. The source provides no usable lens or FOV metadata. FOV is marked
unknown/calibration-required; 60 degrees is retained only as an explicit initial
placement parameter.

The observer utility now uses Lab 004 actor labels, reuses those actors on repeated
execution, accepts an explicit FOV override, and continues to reject placement unless
both Landscape traces and the rendered CameraComponent forward-vector check succeed.
The previous Robert J. Heath reference is preserved as historical visual-benchmark
provenance. Lab 004B visual-quality reference selection remains deferred. No terrain,
Landscape transform, generated heightmap or import pipeline was changed.


## 2026-09-24 — Lab 004A geographic diagnosis

Added a read-only source-DTM diagnostic before any further camera or rendering work.
The north-up plan and profiles show that the published 247 degree heading crosses the
canonical Tryfan summit almost exactly: the camera-to-summit WGS84 bearing is 246.630
degrees at 560.579 m. By contrast, the published depicted-place coordinate bears
254.365 degrees at 660.544 m and lies beyond Tryfan's nearer high flank. The straight
eye-to-depicted-place line is obstructed by up to 146.8 m around BNG
E266474/N359482, where the terrain reaches about 863.4 m ODN. The current exact-target
camera therefore looks into/through the mountain shoulder rather than at a visible
subject point.

The 247 degree profile reaches its maximum terrain angle at about 559 m, BNG
E266405/N359391 and 913.6 m ODN, immediately beside the canonical summit reference.
This supports the geographic plausibility of the published camera plus heading while
showing that Geograph's depicted-place point must not be treated as an exact optical
target. Geograph documents subject location as an approximate primary-subject point
and view direction as an independently stored optional heading; camera positions may
also be best-effort map placements when GPS is unavailable. The Tony Edwards record
remains useful diagnostically, but its current camera-to-depicted-place target model
is not a defensible exact geometric calibration. No terrain, Landscape, camera,
benchmark metadata, FOV, lighting, or generated heightmap was modified.
## 2026-09-24 — Lab 004A photographic orientation correction

Applied the completed geographic diagnosis to observer placement without changing the
validated Landscape or terrain products. The primary camera now uses Tony Edwards'
published 247 degree geographic heading for its horizontal direction. Because Unreal
operates in the local BNG-aligned frame, PROJ converts that true heading at the camera
position to grid bearing 248.591999 degrees, which maps to Unreal yaw 158.591999
degrees. The script independently traces the actual imported Landscape at the camera
and canonical Tryfan summit, then uses their vertical separation to derive pitch; the
canonical R16 predicts +37.384679 degrees from the 1.70 m eye point. Roll remains zero.

The published depicted-place coordinate is preserved as diagnostic provenance and is
written into the placement report, but no longer controls the camera. This reflects
the DTM finding that the approximate subject marker lies behind Tryfan's nearer
shoulder. With no published lens metadata, 40 degrees is recorded as an explicit
horizontal-FOV calibration override rather than a measured value. Runtime placement
continues to reuse the Lab 004 camera and marker and verifies the resulting Unreal
CameraComponent and rendered camera-view forward vectors. No Landscape, AOI,
heightmap, lighting, atmosphere, or source-data asset changed.

## 2026-09-24 — Lab 004A controlled photographic calibration

Separated photographic calibration from the geometric summit reference. Camera BNG
position, imported-Landscape terrain trace, 1.70 m eye height, published 247 degree
true heading, projection-aware Unreal yaw 158.591999 degrees, and zero roll remain
fixed. `MERIDIAN_CAMERA_PITCH_DEGREES` now supplies the unknown photographic pitch,
while `MERIDIAN_HORIZONTAL_FOV_DEGREES` supplies the unknown horizontal field of
view. The Lab 004A benchmark requires an explicit pitch rather than silently aiming
at the summit.

The canonical summit is still traced from the actual Landscape and its approximately
+37.384679 degree elevation angle is reported as geometric diagnostic provenance.
The approximate depicted-place coordinate and its earlier line-of-sight calculations
also remain intact. Placement JSON and editor output identify pitch and HFOV as
calibrated parameters rather than measured image metadata, and repeated trials reuse
the same Lab 004 camera and marker. No terrain, Landscape, heightmap, AOI, lighting,
atmosphere, or source data changed.

## 2026-09-24 — Lab 004A source-DTM skyline calibration

Added a read-only skyline calibration against the original Lab 004 1 m DTM. The
640×480 Tony Edwards photograph has a strong sky/terrain edge over most of its width;
the cloud-affected normalized interval x=0.275–0.475 is retained in diagnostics at
20% weight and is also excluded entirely in a sensitivity run. Terrain horizons use
1 m distance sampling and 0.025 degree bearing steps. Each heading/HFOV candidate
solves pitch analytically, then scores angular shape and slope so vertical translation
alone cannot create a false fit.

The best fixed-camera result is centre true heading 253.55 degrees, HFOV 35.20 degrees
and pitch +30.341841 degrees. Weighted angular RMSE is 0.547919 degrees, weighted MAE
0.468376 degrees, and shape correlation 0.962091. Removing every cloud-affected
column returns the same heading and HFOV. The published 247 degree heading is a poor
photographic centre: its best solution has 2.058258 degrees RMSE and a 2.636-times
worse objective. The recovered view projects the canonical summit to image x≈197,
left of centre inside the clouded region, while measured northern shoulder terrain
at bearings 253.6–271.1 degrees continues across the right side.

Conclusion A is supported: Tony Edwards remains a defensible Lab 004A benchmark using
the recovered photographic calibration. The published heading is approximately 6.55
degrees different from the recovered centre and should be treated as approximate.
Cloud prevents direct summit-silhouette validation; the bare-earth DTM also omits
rocks, vegetation and sub-metre crag form. Because the fixed published camera gives a
stable clear-skyline fit, no camera-position perturbation search was run. Unreal,
Landscape, terrain, benchmark metadata, camera actors, lighting and heightmaps were
not modified.

## 2026-09-24 — Lab 004A recovered-heading calibration override

Added `MERIDIAN_CAMERA_HEADING_DEGREES` alongside the existing pitch and horizontal
FOV calibration globals. The published 247 degree true heading remains immutable
source metadata; an override is recorded separately as an explicit recovered
photographic calibration. The utility applies the same locally derived BNG
grid-convergence correction used by the published-heading path, so the skyline-fit
heading 253.55 degrees maps to BNG grid bearing 255.141999 degrees and Unreal yaw
165.141999 degrees.

The override affects orientation only. Camera BNG/Unreal XY, runtime Landscape trace,
1.70 m eye height, roll, AOI, terrain, Landscape and source data remain unchanged.
Placement JSON and editor output report both the published heading and the applied
heading with its provenance.

## 2026-09-24 — Lab 004A photographic reference overlay

Added a minimal Unreal photographic validation overlay using Epic's built-in Image
Plate plugin. The external 640×480 Tony Edwards photograph is imported only into the
external Lab 004 project. A translucent unlit plate fills the calibrated camera's
constrained 4:3 frame at 50% default opacity, with rerunnable enabled/disabled and
opacity globals.

The setup script validates the named camera's world location, pitch 30.3418 degrees,
yaw 165.141999 degrees, zero roll, 35.20 degree horizontal FOV, and constrained 4:3
aspect before attaching anything. It does not set camera or terrain properties. A
disposable UE 5.8 project-copy smoke test verified texture import, material creation,
Image Plate attachment, 640×480 dimensions, default opacity, and fixed-camera
validation without changing the real level. Generated Unreal assets and reports
remain outside Git.

## 2026-09-24 — Lab 004A persisted-camera repair

The first overlay run after restarting Unreal correctly rejected the saved camera:
the `.umap` still contained the earlier summit-derived 37.383705 degree pitch,
158.591995 degree yaw and 40 degree HFOV. The calibrated 30.3418 / 165.141999 /
35.20 degree state had existed only in the earlier editor session and placement
report because observer placement deliberately did not save levels automatically.

Added a narrow canonical restore-and-save utility and a separate read-only saved-map
validator. Restoration reads the existing photo-overlay configuration, snapshots all
Landscape transforms, changes only the named CameraActor and CameraComponent, checks
the strict calibration, confirms the Landscape snapshot is unchanged, marks camera
objects modified, and saves `/Game/Tryfan_Lab004` through UE 5.8's explicit
`save_map` API. The validator can load the `.umap` in a fresh editor process and
applies the same strict comparison used by the overlay.

A three-process disposable-project test reproduced the stale map, restored and saved
it, reopened it in a fresh UE 5.8 process, passed position/rotation/HFOV/aspect
validation, and then attached the 50% Image Plate while reporting the camera
unchanged. The real project remains awaiting execution of the deployed restore script
inside its currently open editor because remote Python and Windows UI automation were
unavailable; no second process was allowed to overwrite a map held open by Unreal.

## 2026-09-24 — Meridian Earth Laboratory 004B quantitative alignment

Added a bounded, reproducible photographic-alignment analysis without changing Lab
004A, Unreal actors, Landscape, R16, lighting or overlay behavior. The fitter verifies
the final 3025-vertex DTM R16 by SHA-256, decodes the exact Unreal height encoding,
and measures the Tony Edwards photographic skyline against that surface. It uses the
existing deterministic cloud-aware skyline extraction and reports angular, pixel and
skyline-slope residuals. Roll, 4:3 aspect, terrain transform and 1.70 m eye height are
fixed. A tracked configuration declares all uncertainty bounds before fitting and
contains an exact immutable snapshot of the canonical 004A camera.

004A already measures 0.547642 degrees weighted angular RMSE, 9.78517 pixels weighted
RMSE, and 0.962054 shape correlation against the final R16. With camera position fixed,
the best sensitivity solution changes true heading +0.05 degrees, pitch -0.0178
degrees and HFOV +0.025 degrees; its improvement is negligible. Allowing a ±20 m
Geograph-marker envelope finds a mathematical minimum 20 m east and 16 m north,
plus -1.0 degree heading, -0.3264 degree pitch and -1.625 degree HFOV. Angular RMSE
falls to 0.523267 degrees and the combined objective improves 4.42%, but pixel RMSE
slightly worsens to 9.81365 pixels and the easting bound is reached.

The diagnostic classification is therefore boundary-limited, not a justified fitted
camera. No `Meridian_Lab004B_PhotoFitted_Camera` is created or deployed. The evidence
shows that the imported R16 preserves the same broad skyline agreement as the source
DTM, while the residual is too small and too confounded by cloud, automatic edge
extraction, unknown camera metadata, bare-earth representation and missing sub-metre
crags to attribute to a terrain/georeferencing defect. Generated overlays, residual
plots and the machine-readable report remain external under the Lab 004 diagnostics
folder.

## 2026-09-24 — Meridian Earth Laboratory 005A terrain-derived surface analysis

Derived surface evidence from the exact final Tryfan DTM R16 without changing Lab
004, Unreal, terrain, camera, overlay or rendering. The analysis verifies the R16
SHA-256 before and after execution and records measured geometry separately from all
derived products. Horn's 3 x 3 gradient produces slope and downhill grid-north aspect;
a small binomial prefilter supports physically defined Laplacian, profile and plan
curvature; plane-detrended RMS residual supplies roughness at approximately 5, 15 and
51 m windows. Missing neighbourhoods and flat aspects remain undefined.

Across the 3 km AOI, median slope is 18.52 degrees and p95 is 50.05 degrees. Median
roughness rises from 0.069 m at 5 m to 0.266 m at 15 m and 1.082 m at 51 m. Within
600 m of the canonical Tryfan summit the corresponding medians are 0.125, 0.455 and
1.645 m, showing stronger irregularity at every scale. The 51 m maximum of 11.70 m
lies near E266422.8/N359346.6 on the Tryfan high mass; fine-scale and 15 m maxima
occur on steep western crags elsewhere in the AOI. Curvature maps expose alternating
convex ridge and concave gully lineaments that slope alone does not distinguish.

A deliberately relative relationship diagnostic combines fixed gentle/steep slope
thresholds with roughness and absolute-curvature quartiles. It identifies substantial
steep+rough and gentle+smooth regions, but is explicitly not a material or land-cover
map. The analysis cannot identify rock, grass, scree, paths, vegetation, wetness or
sub-metre blocks. Ten north-up diagnostic maps, nine derived/elevation GeoTIFFs and a
machine-readable report are generated outside Git. Two complete runs produced
byte-identical hashes for all 20 outputs; the canonical input hash remained unchanged.

## 2026-09-24 — Meridian Earth Laboratory 005B scalable surface evidence

Added the first independently observed surface layer to the frozen Tryfan geometry.
The official CDSE catalogue supplied product selection and provenance; anonymous
range reads use the matching Earth Search Collection-1 COG because official CDSE
asset access requires credentials. Candidate quality was measured over the actual
3 km Tryfan AOI rather than inferred from tile-wide cloud percentage. The selected
12 July 2026 Sentinel-2A L2A product has 100% usable AOI SCL cells and no classified
cloud, cloud shadow, snow/ice or nodata. A 500 m retrieval margin keeps the retained
native windows to 4 x 4 km.

The first processing pass caught an important access-mirror issue: the legacy Earth
Search collection advertised a -0.1 offset while serving pixels that were already
offset-adjusted, which produced physically impossible normalized-index tails. The
pipeline now uses the Collection-1 COG for the same ESA product; raw values retain
the processing-baseline offset and the published 0.0001 scale/-0.1 offset produces
plausible BOA reflectance. Low-signal or negative-band normalized differences remain
missing rather than being forced into an index.

B02/B03/B04/B08 remain 10 m evidence. Red-edge, narrow-NIR, B11/B12 and SCL remain
20 m evidence. Native EPSG:32630 windows are preserved separately, while analysis
uses exact 10 m and 20 m EPSG:27700 grids. Terrain is aggregated upward from frozen
005A fields using area-weighted mean/maximum and circular aspect handling; Sentinel
is never upsampled to the ~1 m terrain grid. Generated data, GeoTIFFs, PNGs and the
machine-readable report remain external.

The AOI median NDVI is 0.725, median NDMI 0.201 and median NDRE 0.501. NDMI decreases
moderately with elevation (r=-0.437); B11/B12 contrast also decreases with elevation
(r=-0.398) and with 5 m roughness (r=-0.315). These are associations, not material
labels. Cells with similarly gentle/smooth geometry span a large NDVI range, while
cells with NDVI 0.4-0.5 span roughly 42 degrees between their slope p10 and p90. The
experiment therefore shows complementary information: Sentinel distinguishes broad
vegetation, water/brightness and moisture-related behaviour that geometry cannot,
while the DTM supplies slope, landform, roughness and sub-10 m structure absent from
Sentinel. Ten-to-twenty-metre observation is useful as a regional constraint for
human-scale reconstruction, but cannot identify individual rocks, paths, vegetation
structure or surface material; those require stronger observations and/or explicitly
procedural sub-resolution reconstruction.

## 2026-09-25 — Meridian Earth Laboratory 005C temporal surface evidence

Completed the final planned Sentinel-focused evidence experiment without changing
Lab 004, Unreal, the canonical R16, or the frozen 005A/005B outputs. Three bounded
Collection-1 COG observations were added around the frozen 12 July 2026 summer
reference: 17 January 2024 (winter), 30 April 2026 (spring), and 27 November 2024
(autumn). Actual Tryfan AOI cloud/cirrus-free fractions are 98.67%, 99.67%, 100% and
98.47%. Winter deliberately retains a real 25.28% snow/ice state. Winter and late
autumn also contain about 59.20% and 62.35% SCL class-2 topographic/cast shadow under
roughly 15.7-degree sun elevation, compared with 6.00% in spring and 1.84% in summer.

The processing reuses the corrected 005B reflectance scale/offset path and exact
10 m/20 m BNG grids. Snow is retained in environmental summaries and excluded from
persistent-surface summaries; cloud, cloud shadow, cirrus, invalid and nodata remain
masked. A terrain-derived cosine-incidence field records changing illumination from
the aggregated 005A slope/aspect, but no aggressive topographic correction is
applied. The large low-sun shadow fractions make winter and autumn raw brightness and
some normalized indices illumination-sensitive; they are evidence of observation
state, not direct proof of surface-material change.

Snow-excluded median AOI NDVI changes from 0.015 in winter to 0.488 in spring, 0.725
in summer and 0.510 in autumn. Median per-cell NDVI range is 0.534 (p95 0.927);
median brightness range is 0.124; and median NDMI range is 0.700. Winter NDMI is
especially confounded by low illumination and snow-adjacent/low-signal behaviour and
must not be read as a literal AOI-wide moisture measurement. The simple incidence
model explains only modest whole-AOI brightness association (r=0.343 winter,
0.197 autumn, -0.128 spring, -0.264 summer), confirming that atmosphere, BRDF,
phenology, snow and surface differences remain mixed with illumination.

Temporal NDVI variability relates most strongly to northness (r about 0.475), while
NDMI range relates moderately to slope (r=0.357) and weakly to roughness at all three
005A scales (r about 0.224-0.228). Curvature relationships are small. About 17.0% of
10 m cells meet the relative low-NDVI/low-brightness-variability diagnostic, and 5.5%
meet the stricter persistent-low-NDVI diagnostic; these remain evidence masks, not
rock or substrate labels. Four dates materially improve separation of persistent
spectral behaviour from phenology, snow and illumination compared with one excellent
summer scene, but do not add human-scale material or structure resolution beyond the
10-20 m sensor limit.

The external result contains 171 files and occupies 28,865,253 bytes (27.53 MiB):
11.10 MiB aligned rasters, 6.76 MiB temporal fields, 5.36 MiB diagnostics and
4.14 MiB observation metadata/products. Two complete cached runs produced result
SHA-256 553de696cf8f6880624397f09a7604ad25f88f9eee79caf3e13d312938ce3289
and identical output hash lists. The next experiment should use independent free
Welsh habitat/land-cover and geological evidence before any classification or
procedural surface reconstruction.


## 2026-09-25 — Meridian Earth Laboratory 006 contextual evidence

Completed the final planned evidence-gathering experiment before Lab 007 without
changing Lab 004, Unreal, the canonical R16, or frozen 005A/005B/005C outputs. The
pipeline SHA-verifies the 005A and 005C reports, then retrieves only a 3 x 3 km
Tryfan subset from NRW's official Phase 1 habitat WFS and bounded BGS Geology 50K
bedrock/superficial WMS evidence. Original NRW vector attributes and rendered BGS
source products are retained externally. All categorical alignment uses rasterize,
nearest category or categorical mode; identifiers are never interpolated.

The NRW survey adds independently field-mapped habitat names but is legacy evidence:
field recording began in 1979 and Wales coverage was completed during 1979-1997.
Dry heath and acid grassland account for about 33.8% and 29.3% of the AOI; scree
4.2%, flush/spring 4.1%, bog 2.5%, and mapped natural-rock exposure only 0.2%.
Mapped rock/scree is generally steep, mapped bog gentle and smooth, and the broad
terrain relationships are physically plausible. Only 2.4% of mapped rock/scree
cells meet 005C's deliberately strict persistent-low-NDVI diagnostic. That weak
overlap is retained as evidence of different semantics, dates and scales, rather
than “corrected” into agreement.

BGS 1:50,000 evidence identifies sandstone and siltstone units, Ordovician
rhyolite/microgranite intrusions, felsic tuffs and volcaniclastic units across the
AOI. Superficial contexts include till (11.6%), talus (8.6%), peat (8.3%), hummocky
glacial deposits (4.5%) and head (3.9%); roughly 60% has no mapped superficial
deposit in the rendered layer. The canonical Tryfan point lies in mapped acid dry
dwarf-shrub heath, on Capel Curig Volcanic Formation felsic tuff, with no mapped
superficial deposit. This constrains broad surface interpretation but cannot specify
exposure, fracture geometry, visual texture or boulders.

A first diagnostic pass revealed that WMS boundary strokes and labels created an
artificial 14.3% “unknown bedrock” fraction. The derived categorical grid now fills
only opaque cartographic artifacts from the nearest recovered unit while preserving
transparent superficial absence; the source PNG remains unchanged. Six diagnostics
were inspected for north-up alignment, category continuity, map/terrain
relationships and 005C comparison. The output is 14,261,964 bytes (13.60 MiB).
Two cached reruns produced the same deterministic result SHA-256
f0b85ebfa28ecf9bad63c7db9a515b15b442fd2cdf5a3c51c71cc0989df51280.

The experiment supplies a machine-readable evidence package with independent
terrain, Sentinel, habitat and geology channels and explicit source-scale metadata.
It is sufficient to constrain Lab 007's first uncertain surface interpretation.
Lab 007 must not infer square-metre material truth, individual rocks, present-day
habitat unchanged since the survey, or visual texture directly from these sources.


## 2026-09-25 — Meridian Earth Laboratory 007 uncertain underlying surface

Implemented the first deterministic inference stage without changing Labs 003-006,
Unreal, terrain or rendering. The model keeps source fact, derived evidence, model
inference, temporal state and unsupported detail separate. It combines capped
preferences from structural terrain morphology, dated four-season Sentinel
summaries, historical 1979-1997 NRW Phase 1 habitat context and broad BGS geological
context. No machine learning or new dataset is introduced. Missing families and
specificity-weighted disagreement raise explicit other/unknown support; normalized
Shannon entropy records uncertainty. Bedrock, no mapped superficial deposit, steep
or rough terrain and low NDVI are each prevented from independently proving rock.

The 10 m grid is alignment geometry. All 90,000 valid terrain cells have normalized
six-class vectors, but this is complete computation rather than complete knowledge.
Terrain, Sentinel and BGS cover 100%; NRW habitat covers 99.48%. BGS distinguishes
35,982 cells with mapped superficial deposits from 54,018 valid cells with none
mapped. Mean uncertainty is 0.929 and mean other/unknown probability 0.303;
other/unknown is dominant in 79.14% of cells. The model therefore reports the AOI as
substantially underconstrained despite broad source coverage.

Relationships are physically plausible but remain weak probabilities: mean rock
rises from 0.078 on slopes below 10 degrees to 0.139 above 60 degrees, while wet
ground falls from 0.181 to 0.086. Mapped scree averages 0.247 scree/talus; mapped
bog 0.301 wet ground; BGS talus 0.185 scree/talus; and BGS peat 0.237 wet ground.
High-conflict cells carry more other/unknown support than the low-conflict quartile.
At the canonical Tryfan point, acid dry dwarf-shrub heath, felsic-tuff bedrock, no
mapped superficial deposit, steep/rough terrain and dated Sentinel observations
produce rock 0.134, scree/talus 0.111, heath 0.240, grass 0.119, wet ground 0.080,
other/unknown 0.317 and uncertainty 0.934.

Twelve diagnostics were visually inspected. They show coherent terrain-linked
rock/scree tendencies, habitat-shaped heath/grass/wet regions, mapped talus bands,
near-complete evidence-family coverage and widespread high uncertainty. No source
disagreement was hidden. The report's 48-file hashed payload occupies 11,240,488 bytes; including the report, 49 files occupy 11,287,793 bytes (10.76 MiB). Two cached
runs produced identical deterministic SHA-256
574ce8e07fb8752e90b149ef9c5638adcd1d5845818df608b94a65a5c75ccbc8 and
verified that every consumed frozen source product remained unchanged. The evidence
is sufficient for a later explicitly uncertainty-aware experiment, but not for
confident material truth or high-frequency procedural reconstruction.


## 2026-09-25 — Meridian Earth Laboratory 008 uncertainty audit

Audited frozen Lab 007 rather than tuning it. The workflow verifies deterministic
identity 574ce8e07fb8752e90b149ef9c5638adcd1d5845818df608b94a65a5c75ccbc8,
all listed outputs and the stored source contributions before running analytical
counterfactuals in a separate output tree. Other/unknown dominance is separated from
known-class mass, meaningful-class margin, conditional entropy, source conflict,
coverage and plausible class mixture.

The high mean entropy is not mainly a coverage problem. Lab 007's deliberately
diffuse baseline has entropy 0.979 before evidence; evidence lowers it to 0.929.
Unknown-dominant cells still retain 0.683 mean known-class mass, and 85.75% have a
meaningful leading class of at least 0.20. Conditional meaningful entropy remains
0.943. Heath/grass and grass/wet-ground are the top pair in 58.89% and 20.37% of
cells, showing that mutually exclusive broad classes and plausible sub-grid mixture
are central limitations.

Overlapping diagnostic flags identify 45.13% ontology ambiguity, 25.00% high source
conflict, 22.68% weak discrimination, 22.38% dependence on coarse/contextual
evidence, 3.32% temporal ambiguity and 0.52% missing habitat. Conflict correlates
with other/unknown (r=0.422) but not entropy (r=-0.045). Removing conflict support
reduces other/unknown by 0.020 while increasing entropy by 0.007; disagreement changes
the representation of uncertainty rather than explaining all broad overlap.

NRW habitat provides the strongest unique categorical discrimination: removal changes
the meaningful leader in 50.72% of cells. Terrain uniquely constrains morphology;
removal changes it in 6.34%. BGS changes probabilities widely but meaningful leaders
only 3.84%, confirming broad talus/peat/substrate and uncertainty context rather than
direct cover classification. Sentinel has small global ablation influence (0.46%
leader changes) but remains the only recent dated spectral channel. No source is
shown to be misleading within its declared scale and temporal role.

Six diagnostics were inspected. They show coherent heath/grass and grass/wet
ambiguity, ridge-linked conflict, broad mixed-cause regions, negligible spatial
impact from missing habitat and clear zones of reconstruction freedom. Readiness is
46.21% broad-tendency constrained, 37.10% guided mixture and 16.70% high freedom.

Outcome B: no additional evidence acquisition clears the information-value bar.
No single scalable public source is demonstrated to resolve the combined class
overlap, coarse scale, temporal ambiguity and sub-grid mixture at human scale.
Evidence gathering should freeze and Lab 009 should use probabilities plus readiness
as constraints while keeping reconstructed detail explicitly separate from measured
and observed evidence. Thirteen generated files occupy 4,319,474 bytes (4.12 MiB).
Two cached runs produced deterministic SHA-256
3996360c3ea9b379362704b22c5e06e8ecaf16870e14118ff8eabb1bcd02fac7.

## 2026-09-28 — Meridian Earth Laboratory 009 reconstruction v0.1

Implemented the first renderer-facing reconstruction without changing frozen Labs 007/008, the canonical R16, Landscape geometry or Lab 004A camera. Frozen hashes and all consumed terrain products are checked before processing and after output. Lab 007 probabilities remain scientific inference. Lab 008 readiness controls bounded procedural amplitude. Other/unknown remains reconstruction freedom rather than a material class.

The renderer grid matches all 3025 x 3025 Landscape vertices. Five normalized continuous controls combine registered Lab 007 tendencies, bounded measured-terrain conditioning and deterministic correlated variation at approximately 8, 29 and 97 m. The cell-centre/AOI-edge mismatch was corrected by extending only the outermost evidence cell to the boundary. Complete coverage was achieved without inventing a new evidence cell. Two reruns produced identical result SHA-256 `14f90941468166dc3937879e022e8fedff2d9d212eed5cfb1c5deb0407c6a859` and identical file inventories. Probability sums are within 2.39e-7, neighbour correlations are 0.993-0.997, and aggregate known-class drift is at most 0.0077.

The reversible Unreal setup imports two non-sRGB mask textures and builds `/Game/MeridianLab009/M_Lab009_Surface`. A real editor run exposed and corrected a sampler mismatch: texture nodes now use `SAMPLERTYPE_MASKS`, and setup replaces only its generated material asset so no orphaned expression remains. Saving baseline and Lab 009 states in both directions confirmed reversibility. Final read-only validation passes for the 3025 x 3025 textures, clean material graph, Landscape material, recorded baseline, unchanged Landscape transform and immutable Lab 004A camera. The existing Landscape and camera validators also pass.

Automated benchmark capture remains unsuitable. UE 5.8's camera-bound ImagePlate proxy obstructs transient SceneCapture frames despite component/actor hiding and unsaved-world removal. This is a capture-path limitation rather than a terrain/material failure; generated frames are marked invalid. Further capture engineering was deliberately stopped. Exact minimal steps now use the real piloted Lab 004A CameraActor to capture baseline, Lab 009 and 50% reference-overlay frames at 1280 x 960.

All six offline diagnostics were inspected. Controls and the restrained material preview are coherent, terrain-linked and free of obvious checkerboard, salt-and-pepper or 10 m grid artefacts. Lab 008 readiness remains visibly coarse but is not rendered directly. The fixed-camera judgement of whether v0.1 is visibly better than baseline remains pending the manual frames; no claim of photographic improvement or Lab 009 visual completion is made before those images are inspected. The current limiting vocabulary is broad colour plus uniform roughness, without measured albedo, detailed normals, vegetation geometry or individual rocks.

## 2026-09-28 — Meridian architecture and storage foundations

Recorded a concise architecture contract before any filesystem migration. Meridian
is the ecosystem; Atlas owns world representation, Weather owns atmospheric data,
and provisional Traverse owns route/journey/movement planning while retaining
normal technical route vocabulary. The current web application remains one
client-side deployment. Dependency direction, renderer independence, experiment
provenance and the observed/derived/inferred/reconstructed/rendered hierarchy are
now explicit.

Added a small Python-only storage-root resolver for `MERIDIAN_DATA_ROOT` and
`MERIDIAN_PRIVATE_ROOT`. Defaults preserve the existing sibling-directory layout;
overrides must be absolute and outside Git, missing required roots fail clearly,
and historical `../meridian-data/...` conventions can map to a configured root
without editing frozen configs. No private data was moved and no path is exposed to
the browser bundle.

Audited the external UE 5.8 Tryfan project without modifying it. The canonical
72,016,185-byte map is the unique calibrated scene package; the photo-overlay and
Lab 009 assets are reproducible imports, and `Content/Python` is deployment output.
The recommended later preservation step is narrowly scoped Git LFS in the existing
repository, after explicit approval and removal/review of machine-generated config
such as the Android file-server token. No LFS configuration, Unreal copy, rename or
bulk data migration was performed in this phase.

## 2026-09-28 — Preserve Tryfan Reference Renderer

Preserved the unique calibrated Unreal scene as durable Meridian source under
`renderers/unreal/tryfan-reference` without renaming its historical project, map or
actors. Normal Git contains the UE 5.8 project descriptor, a curated secret-free
`DefaultEngine.ini`, renderer manifest, recovery documentation and bootstrap logic.
Only `Content/Tryfan_Lab004.umap` uses a path-specific Git LFS rule. The copied
72,016,185-byte map matches the external canonical SHA-256
`85ef8f1cc9a9fda9b6f2ab3b911bd57831fe75c4009e5ad168ea4956165a260d`.

The generated Android file-server section was omitted rather than retaining its
credential or a placeholder. An initial smoke launch showed UE would regenerate the
section; disabling the unused Android File Server plugin prevented regeneration on a
second launch while leaving renderer validation unchanged. `DefaultInput.ini` was
not retained because it consists
of generated engine input defaults; the calibrated camera's HFOV and constrained
aspect are established by repository configuration and validators. Imported Tony
Edwards assets, Lab 009 textures/material, deployed Python, source-pointer files and
Unreal build/cache/Saved state remain ignored and reproducible.

A storage-root-aware bootstrap verifies the canonical R16, terrain manifest,
photograph, Lab 009 report/package and packed controls before deploying Python and
local pointers. A clean repository copy was opened headlessly in UE
5.8.2-56702186. The map initially reported the expected missing generated material
packages; the smoke validator recreated them without saving the map. Landscape,
fixed Lab 004A camera and Lab 009 material validation all passed. The map hash was
identical before and after. Lab 009 fixed-camera visual acceptance remains pending;
this preservation work does not make a new visual-quality claim.

## 2026-09-29 — Meridian Phase 3 architecture and path rules

Hardened the shared Python storage contract without moving any data. `MERIDIAN_DATA_ROOT`
and `MERIDIAN_PRIVATE_ROOT` remain explicit absolute roots outside Git with documented
sibling defaults; they must now be non-overlapping, repository-relative paths cannot
escape the worktree accidentally, and both historical data/private prefixes have
focused coverage. Frozen Lab entry points and configs retain their original
`../meridian-data/earth-lab/...` conventions until the controlled Phase 4 migration.
Ignored Unreal source-pointer JSON remains machine-local runtime state, not committed
configuration.

Updated the architecture contract to the post-preservation state. Meridian/Atlas/
Weather/provisional Traverse ownership, modularity, dependency direction, the
renderer-neutral representation pipeline, provenance classes, external/private
storage meanings, and the current Git LFS-backed Tryfan Reference Renderer boundary
are explicit. The web application remains one composed client application; no product
split or shared-package hierarchy was introduced.

Added a non-destructive Phase 4 inventory covering frozen Tryfan experiments, terrain
research, generated GFS publication, private activity/Strava data, ambiguous route
benchmarks and renderer dependencies. The required migration order is copy, update
references, validate, compare hashes, and only then consider removing an old copy.
No files were copied or moved.

Validation passed: 13 storage-root tests, 134/134 full Earth Lab tests, five focused
renderer tests, syntax parsing for 90 tracked Python files, strict parsing for 17
experiment/config JSON files, seven renderer external-input hashes, frozen Lab
007-009 identities, canonical map SHA-256, all 27 backup-critical current/backup hash
pairs, `git diff --check`, and the tracked privacy/credential scan. Unreal was not
launched because calibrated renderer state and configuration were unchanged. The next
step is human review of Phase 3, followed by a separately authorised Phase 4 copy-first
migration; route-benchmark GPX provenance/privacy must be decided before placement.

## 2026-09-29 — Meridian Phase 4A migration planning

Converted the Phase 3 migration inventory into an evidence-based execution plan without
copying, moving, renaming or deleting data. The plan records the measured external
estate, distinguishes active path dependencies from historical provenance and generated
pointers, classifies each migration target, and defines bounded Phase 4B–4G scopes with
copy, validation, rollback and deletion gates.

The main decisions are to keep frozen Earth Lab outputs under historical experiments;
promote only explicitly reusable Tryfan terrain, surface-inference, reconstruction-
readiness and renderer-neutral reconstruction products; move all activity, Strava,
route-benchmark and route-conditioned terrain research into private Traverse storage;
and separate authoritative external GFS storage from its browser publication path.
Exact Sentinel subsets and source/context acquisition evidence remain retained sources,
while virtual environments, stale weather source caches and Unreal build state remain
regenerable candidates rather than durable products.

Read-only validation passed: the external directory file/byte inventories were unchanged,
`MERIDIAN_PRIVATE_ROOT` had not been created, frozen Lab 007–009 deterministic identities
were unchanged, the repository and external canonical Unreal maps still matched SHA-256
`85ef8f1cc9a9fda9b6f2ab3b911bd57831fe75c4009e5ad168ea4956165a260d`, and all 27
backup-critical current/backup hash pairs matched. Only planning documentation changed;
no Unreal launch or broad test suite was necessary. Phase 4B remains separately
authorised future work.

## 2026-09-29 — Meridian Phase 4B historical experiment preservation

Copied the curated historical Earth Lab payload to
`MERIDIAN_DATA_ROOT/experiments/earth-lab` without moving, renaming or deleting the
original tree. The repository manifest records every included and excluded source area.
The destination contains 712 files and 814,688,394 bytes: 711 copied files match their
source SHA-256 exactly, and one 88-byte Lab 001/002 `DefaultEngine.ini` preserves the
non-secret project setting while omitting the generated credential-bearing section.
The historical Unreal project, maps and external-actor packages were retained; virtual
environments, engine caches/build state, routine Saved data, bytecode, a generated
pointer and the later external Lab 004 renderer workspace were deliberately excluded.

Active config-driven Lab 004B and Lab 005A–009 tooling now resolves the frozen sibling
path convention through the shared Meridian path layer to the new experiment location.
The repository Tryfan Reference Renderer bootstrap and manifest use the new external
location. Frozen experiment configs, reports and historical documentation remain
unchanged, and the original data tree remains the rollback source until Phase 4G.

Validation passed: the full selected relative-path/SHA-256 comparison; exact source and
destination file/byte inventories; 294 raster opens; 27 destination JSON parses; 14
storage-root tests; 11 focused Lab 009 tests; 135 full Earth Lab tests; renderer
external-input verification; frozen Lab 007–009 identities at both locations; canonical
map SHA-256; and all 27 backup-critical source/backup comparisons. Private activity,
Strava, route-benchmark and terrain-research inventories were unchanged. Unreal was not
launched because no calibrated renderer package was changed. Phase 4C has not begun;
the next action is human review of this uncommitted copy and active-reference checkpoint.

## 2026-09-29 — Meridian Phase 4C Atlas source and Tryfan product promotion

Promoted a deliberately narrow, renderer-neutral Tryfan data estate without running new
research or altering frozen experiment products. Four retained-source products now hold
the bounded Welsh LiDAR DTM/DSM and catalogues, two licensed reference photographs, four
exact Sentinel-2 Level-2A AOI observation sets, and the retrieved/clipped NRW/BGS/JNCC
context evidence. Five derived products now hold the canonical DTM R16, nine terrain
morphology fields, the selected Lab 007 probabilistic inference controls, the single
Lab 008 reconstruction-readiness control, and the Lab 009 package plus eight GeoTIFF
reconstruction controls.

The neutral catalogue preserves observed, derived, inferred, audited-control and
reconstructed semantics, source licences, effective resolution, CRS/registration,
limitations and historical Lab lineage. The 93 promoted payload files total 522,051,687
bytes. Every destination file matches its historical source SHA-256. Seventy-three
rasters opened with matching metadata; JSON/XML and photograph checks passed; Lab 007
probabilities and Lab 009 mixtures remain normalized; readiness codes remain 1–3. The
external validation inventory is `[DATA]/derived/atlas/tryfan/phase-4c-validation.json`
(SHA-256 `37faf10aab6dc62895a19fcafbe58098741ef2776ea347772e203d02cb58e788`).

Packed Lab 009 RGBA PNGs remain renderer-specific historical transport artefacts, and
the integrated packer was not extracted. The Tryfan Reference Renderer remains on its
seven hash-verified historical inputs; Unreal was not launched and the canonical map was
not changed. No route-conditioned terrain, activity, Strava, route-benchmark, GFS or
private data was copied. Both historical Earth Lab trees and the Phase 1 backup remain
intact. Focused checks passed: 14 storage-root tests, five renderer-source tests, all
seven renderer input hashes, the canonical map hash, frozen Lab 007–009 identities and
all 27 backup-critical comparisons. Phase 4D has not begun; the next action is human
review of this uncommitted promotion checkpoint.

## 2026-09-29 — Meridian Phase 4D private Traverse data migration

Created the sibling `MERIDIAN_PRIVATE_ROOT` and copied the existing private movement and
route research into a purpose-specific Traverse hierarchy. Private source exports now
live under `sources`, eleven conservatively private benchmark files under `benchmarks`,
activity and route-conditioned terrain results under `experiments`, and their separable
reacquirable terrain caches under `cache`. No private source was parsed, transformed or
published during migration.

The copy contains 3,005 payload files / 360,462,077 bytes. Every source and destination
SHA-256 matched. The detailed filename/hash inventory remains private; the tracked
aggregate manifest records only its SHA-256,
`ec92b799b1e59da7ab955e5805983ec652c57f6b0581f88a3d658bc7885b66cc`. The four original
data-root estates retain their exact Phase 4A counts and sizes as rollback copies until
Phase 4G. This is a deliberate transitional exception, not a continuing general-data
location for private material.

No active code path was changed: activity and terrain tooling already accepts explicit
roots, and the storage resolver recognizes the new sibling private root. Fourteen root
tests, 28 activity-research tests and ten terrain-research tests passed. Historical Earth
trees, promoted Atlas data, GFS, frozen Lab identities, seven renderer inputs, the
canonical map and all 27 backup-critical pairs remained unchanged. Phase 4E has not
begun; the next action is human review of this uncommitted private-data checkpoint.

## 2026-09-29 — Meridian Phase 4E external Weather/GFS storage

Separated authoritative generated GFS storage from browser publication without changing
weather fields, tile encoding or the `/weather/gfs` client contract. The current and
previous complete ten-field runs plus `latest.json` were copied to
`[DATA]/derived/weather/gfs`; 40,841 payload files / 1,268,050,554 bytes match the old
publication SHA-256-for-SHA-256. Both destination runs passed the existing complete-run
validator across all ten fields, 24 timesteps and 20,400 PNGs per run. The detailed
external inventory is `phase-4e-validation.json` with SHA-256
`b0e50edbff5dd2fadd914ca34b5564b20c7b8ce7387be7627a610e005c81eade`.

Generation now defaults through `MERIDIAN_DATA_ROOT` to the external authoritative root.
A small guarded Vite adapter serves only `latest.json` and its selected immutable run in
development; production builds materialize that same bounded view into `dist`. Local HTTP
checks returned the external catalogue, manifest and representative numeric tile
byte-identically, and the production publication contained 20,421 files / 633,781,652
bytes with neither the previous run nor the external validation report.

The eleven stale source-building trees, older partial run and runtime lock were classified
but not promoted or deleted. The original 42,283-file / 2,591,121,422-byte
`public/weather/gfs` estate remains unchanged as rollback state until Phase 4G. Private
Traverse, Atlas, historical experiments, the reference renderer and the Phase 1 backup
were not part of this migration. Phase 4F has not begun.

## 2026-09-29 — Meridian Phase 4F legacy GFS cache disposition

Disposed only the legacy GFS material classified as generated, incomplete or reacquirable.
The explicit removal set comprised eleven stale atmospheric source-building directories,
the incomplete `20260902T18Z` atmospheric inspection cache and the obsolete one-byte legacy
updater lock: 1,442 files / 1,323,070,868 bytes in total. Every path was inventoried,
resolved beneath `public/weather/gfs`, checked for reparse points and removed individually.

No active runtime, development, build, test, publication or recovery path referenced the
removed concrete locations. The external authoritative publication remained 40,841 files /
1,268,050,554 bytes with the validated catalogue selecting `20260907T18Z`. The legacy tree
now contains only the complete `20260907T12Z` and `20260907T18Z` runs plus `latest.json`,
with the same aggregate count and size. These complete copies remain deliberately as
rollback state until Phase 4G; Phase 4G has not begun.


## 2026-09-29 — Meridian Phase 4G legacy GFS retirement

Independently revalidated external authoritative GFS storage before retiring the final
in-repository rollback copy. Both complete external runs passed the full ten-field,
24-timestep semantic and PNG validator. External and legacy relative path/size inventories
matched exactly; `latest.json` and all twenty run manifests matched by SHA-256. Vite
development served the external catalogue, manifest and representative tile byte-for-byte,
and the established generation and production paths resolved external storage.

After confirming non-overlapping roots, explicit containment, exact inventory and absence
of reparse points, removed `20260907T12Z`, `20260907T18Z`, `latest.json` and then the
empty `public/weather/gfs` directory: 40,841 files / 1,268,050,554 bytes. The
`public/weather` parent remains. The external authoritative estate was not modified.
No other migrated old-copy category was removed, and no later phase has begun.


## 2026-09-29 — Meridian Phase 5A active-code architecture audit

Audited all 81 active TypeScript/TSX files, their relative imports, source ownership,
runtime side effects and Vite-loaded UI, route, Weather and visual test seams. The
generic `components/services/types/config` layout hides clear domain groupings. `App`
is the correct composition root but also owns complete Weather and Traverse workflows;
`MapView` combines the Atlas map lifecycle with Weather rendering/sampling and Traverse
route interaction, so it is currently an app-level integration component rather than an
Atlas component.

The frozen Phase 5 plan contains only 5B structural moves, 5C resolution of the
`App`/map, Weather/journey and Traverse/GFS seams, and 5D transitional cleanup plus
full validation. Weather will receive only a generic journey coverage window, Traverse
will consume normalized Weather samples rather than GFS manifests/tile caches, and an
Atlas map host will be composed with Weather and Traverse map controllers by app. No
implementation file was moved or changed in 5A, no feature work was added, and optional
architecture improvements were placed in a post-cleanup backlog rather than extending
Phase 5.

## 2026-09-29 — Meridian Phase 5B structural reorganisation

Moved 80 active source/style files into the frozen app, Atlas, Weather and Traverse
ownership structure and repaired imports plus Vite test-loader paths. `App` remains
the composition root. The mixed `MapView` moved intact to app-owned `MeridianMap`;
`WeatherPanel` became `MobileWorkspace`, and `ForecastDetails` became
`RoutePointDetails`. Mixed timeline, workspace, layer state/visuals/attribution and
ordering remain app compatibility code. The empty `SearchBar` remains for 5D and no
`shared` abstraction was introduced.

This phase deliberately retained the Weather-to-journey and Traverse-to-GFS
dependencies, the mixed map responsibilities and both audited type cycles for the
bounded 5C/5D work. TypeScript, ESLint, production build, external GFS publication,
29 UI tests, 56 route tests and 32 Weather tests passed. Browser validation passed
all scenarios at 1920x1080 and 1440x900 and four of five scenarios at 1366x768. The
1366 pressure readiness marker timed out twice with no page/network errors. Focused
diagnosis reproduced the same scheduling failure at 1440x900 and at the isolated
Phase 5A baseline. Terrain configuration can leave `map.isStyleLoaded()` false after
`style.load`; if the pressure effect and camera `moveend` both occur during that
window, the guarded update is skipped and no later trigger sets the readiness marker.
Phase 5B changed no executable pressure lifecycle code, so this is a pre-existing
map lifecycle/render-retry issue assigned to the already-frozen 5C map/controller
work. The 5D browser gate must verify its resolution without weakening the test.
Phase 5C has not begun.
## 2026-09-30 — Meridian Phase 5C domain boundaries

Implemented the three frozen coupling fixes without adding a framework or changing
product semantics. Atlas now owns the concrete MapLibre lifecycle, Weather owns its
map controller and provider-specific route sampler, Traverse owns its route-map
controller and route-relative interpretation, and app composes the domains. Combined
inspection/status presentation remains app-owned.

The Weather map controller retains requested work while terrain or style changes make
the map temporarily unrenderable, then applies it once when Atlas reports the map idle
and renderable. This replaces the timing assumption that caused pressure updates to be
lost after `style.load`; the formerly failing 1366x768 pressure scenario and its
1440x900 control both pass without a longer timeout. Weather now receives only a
two-time forecast coverage window adapted by app, so it imports no `JourneySchedule`.
Weather also owns GFS timestep selection and numeric tile sampling; app passes its
provider-neutral samples to Traverse, which no longer imports GFS or numeric-tile
implementation and retains route-relative plus provider provenance.

No `shared` directory was introduced. The two audited type cycles, transitional
compatibility files and empty SearchBar remain for the already-frozen 5D cleanup.
The final gate passed 117 focused deterministic tests with one intentionally skipped
live-publication integration case, TypeScript/Vite build, ESLint and the external GFS
publication check. All 15 established Playwright scenarios passed across 1920x1080,
1440x900 and 1366x768, including the formerly failing 1366 pressure scenario under its
unchanged timeout. Phase 5D remains the final Phase 5 task and has not begun.

## 2026-09-30 - Meridian Phase 5D final cleanup and validation

Completed only the frozen final cleanup. Weather's physical atmospheric catalogue
and field IDs now live independently of validation; Traverse's base coverage/key
types no longer depend on aggregate derived results. Both audited cycles are gone.
Removed the empty SearchBar and four obsolete app compatibility files, retained
mixed overlay selection as app state, and placed analysis choices in Traverse.
No shared package, new framework or product behaviour was introduced.

The import audit includes type-only edges: zero cycles, zero unresolved imports,
no domain-to-app imports, zero Weather JourneySchedule references and zero Traverse
Weather-data/map implementation imports. The three Phase 5C seams, provider-neutral
provenance and pressure lifecycle correction remain intact. Architecture, frozen
plan, README and current Weather path references now reflect the actual layout.
The opt-in real-asset test now uses the approved sampling seam and an asynchronous
PNG test decoder; its prior blocking shim could starve local HTTP requests.

Validation passed 125/125 active Node tests with live-publication integration
enabled, 82 Weather Python tests, 15 storage-root tests, TypeScript, ESLint, Vite
build and bounded GFS publication (20260907T18Z, ten fields, 24 timesteps).
The complete Playwright matrix passed 15/15, five at each established viewport;
1366x768 pressure passed in 24.8 seconds without increasing its timeout. The normal
Node run's one opt-in skip was also exercised separately and in the full suite.
Browser diagnostics contain zero page exceptions/HTTP errors and no failed GFS
requests; 74 external-provider request cancellations are `net::ERR_ABORTED`.
Documentation links/whitespace, diff and privacy checks passed. The existing bundle
size warning remains backlog. No visual baseline or browser assertion was changed.
Historical experiments, renderer/Unreal, private data and external estates were not
modified; there was no Unreal launch or bulk estate hashing.

Phase 5D is ready for review and the explicitly authorised final Phase 5 checkpoint.
No commit or push has been made. Phase 5 ends with 5D; there is no Phase 5E and no
new backlog scope has been implemented.


## 2026-09-30 — Phase 5 checkpoint and Phase 6A–6C repository reunification

Phase 5 was reviewed, approved and checkpointed as
`6f6491c6cb72b203e71693318a719b227bf2c662` (`Complete Phase 5 architecture cleanup`).
The preceding 5D entry records its pre-checkpoint review state. No further Phase 5
implementation or later architecture subphase was added.

Phase 6A audited local and live remote history without modifying the repository.
Main at `6383ed2d729efb8a61fd6d03c0cdedb751d26007` was the strict ancestor and merge
base of earth-lab at the Phase 5 checkpoint: zero main-only commits and 28 ordinary
single-parent descendants. The legacy Journey/Weather branch had no unique work.
Fast-forward was selected; no history rewriting or content reconciliation was needed.
Existing restore tags and Git-recorded Lab/renderer provenance remained reachable.

Phase 6B switched normally to main and fast-forwarded it only to the Phase 5 commit.
No merge commit or new commit was created; the resulting tree was exactly
`d849c29bff0feb06c6e0b472c87168313236efaf`. Earth-lab, legacy branches, remote refs
and existing tags were unchanged. The canonical LFS map remained locally available.

Phase 6C created the local annotated `phase-5-complete` marker at that Phase 5 commit,
with the annotation describing completion of architecture cleanup before canonical-main
reunification. Main is the active development line; earth-lab remains frozen historical
research/cleanup history, and legacy/journey-weather retains the pre-world-pivot lineage.
The existing milestone tags remain unchanged. No branch deletion is required.

README and current architecture/status documentation now describe completed Phase 5,
main-based development, migrated storage and historical branch roles. Earlier dated
records, frozen plans, experiment identities and research/renderer implementation were
preserved. No application, external/private data or Unreal state was changed.

Phase 6C validation passed: documentation links, whitespace, the complete documentation-
only diff, privacy/credential scans and unchanged implementation content against Phase 5.
Origin/main remains at `6383ed2`; the Phase 6C documentation commit and new tag stay
local pending the Phase 6D validation/publication gate. Phase 6D has not begun.
Phase 6 is not complete: it ends with 6D, and no Phase 6E is proposed.

## 2026-10-01 — Phase 6 completion and Phase 7 clean-start corrections

Phase 6D completed the validation/publication gate. Canonical main and origin/main
were published normally at `8a9bdee956d9e881639ce20a99ccd337a0cf3fc4`, and the
annotated `phase-5-complete` marker was published at the unchanged Phase 5 checkpoint.
Only the four approved repository-facing documents differed from Phase 5; history
was preserved without rewriting. Earth-lab and legacy/journey-weather remain frozen
historical branches. The earlier Phase 6C entry records the then-pending state.
Phase 6 is complete and ends at 6D.

Phase 7A reproduced canonical main in an independent clone with normal Git LFS
recovery, lockfile installation and a fresh Python environment. Documented external
data configuration worked without private activities or original-checkout artifacts.
It exposed an environment-dependent publication fixture, production materialization
on Vite server shutdown, resource-sensitive browser timeouts, stale current status
text and six npm advisory-bearing packages. No accidental original-checkout hidden
state was found. This was an observation-only experiment, not a repair phase.

Phase 7B corrects the sibling-default test by explicitly supplying an empty
environment. Production root resolution is unchanged. Two regression tests exercise
actual middleware and listening Vite servers in isolated child-process environments.
Vite's publication plugin now gates its existing closeBundle work on the resolved
`build` command: development/test shutdown serves no production materialization,
while standalone builds still publish only latest.json and its selected immutable
run. No application/domain architecture, browser URL or Weather format changed.

The unchanged shell tests initially timed out in all three sizes even when run alone,
with about 1.3 GB of free RAM. After the developer freed memory, all three isolated
checks and the complete 15-scenario matrix passed unchanged; 1366x768 pressure took
31.3 seconds in that matrix. The evidence supports environmental resource timing,
not a browser assertion or application defect. No timeout, test assertion, visual
baseline or application rendering change was made. Browser validation is documented
as a quiet run without competing builds/tests. Current status text now records the
completed Phase 6 publication rather than rewriting earlier historical entries.

### Phase 7B dependency advisory disposition

The audit initially reported one moderate, four high and one critical package.
Only compatible transitive lockfile updates were applied; package.json, direct
dependency versions and application code remain unchanged. Companion Browserslist
data packages were updated as required by its existing dependency constraints.
No automatic audit fix, suppression or override was used.

| Package / dependency path | Original severity / version | Advisory and affected range | First fixed version / disposition |
| --- | --- | --- | --- |
| baseline-browser-mapping via React Hooks ESLint plugin → Babel → Browserslist | Moderate / 2.10.33 | GHSA-w5vr-8v7q-w6rv; >=2.0.0 <2.11.0 | 2.11.0; locked 2.11.26 |
| brace-expansion via ESLint → minimatch | High / 5.0.6 | GHSA-3jxr-9vmj-r5cp (<5.0.7), GHSA-mh99-v99m-4gvg (<5.0.8), GHSA-rgw5-rvv9-x895 (<5.0.9), GHSA-6j4f-fj2g-mc7p (<5.0.10), GHSA-qhr7-859c-m2p7 (<5.0.11), GHSA-q2hr-2g5m-vwhr (<5.0.12), for the affected 5.x line | 5.0.12; locked 5.0.12 |
| browserslist via React Hooks ESLint plugin → Babel | High / 4.28.2 | GHSA-c83g-rgw3-j3cx and GHSA-73wf-gq98-2v4g; <=4.28.6 | 4.28.7; locked 4.29.3 |
| nanoid via Vite → PostCSS | High / 3.3.12 | GHSA-28wg-ghj8-5hjv (<3.3.16) and GHSA-2v37-7h3g-55p8 (<3.3.18), for the affected 3.x line | 3.3.18; locked 3.3.19 |
| postcss via Vite | High / 8.5.15 | GHSA-r28c-9q8g-f849 (<=8.5.17) and GHSA-fxqj-rqcc-2cmp (<=8.5.22) | 8.5.23 for both; locked 8.5.28 |
| maplibre-gl, direct browser dependency | Critical / 5.24.0 | [GHSA-jrc7-96c5-q579](https://github.com/advisories/GHSA-jrc7-96c5-q579); <=6.4.0 | 6.4.1; major-version migration deferred to immediate post-Phase-7 maintenance |

The five transitive packages process build/lint inputs rather than user route or
Weather data. Their advisories concern invalid input, glob expansion, Browserslist
cache/custom statistics, Nano ID argument handling, and untrusted CSS source-map
paths. Meridian normally supplies repository-controlled configuration/CSS; PostCSS
calls its non-secure ID generator with a fixed positive size of six. Compatible
updates remove these advisories without declaring their risk nonexistent.

The remaining MapLibre advisory materially applies: Meridian uses MapLibre's
attribution control and accepts third-party style/source attribution, including
MapTiler metadata validated only as a string. The sanitizer bypass can therefore
affect externally supplied attribution HTML. It is not dismissed as a tooling-only
issue. The [MapLibre 6 release](https://github.com/maplibre/maplibre-gl-js/releases/tag/v6.0.0)
changes default-import/ESM APIs, event types, workers and WebGL requirements; Meridian
has multiple default imports and custom Weather renderers requiring application
migration and validation. That work exceeds this bounded foundation correction.
Immediate maintenance should migrate to a supported fixed release (at least 6.4.1),
validate attribution handling and all map/custom-renderer/browser paths before public
deployment. npm audit remains unsuppressed with one critical advisory; this checkpoint
does not claim a vulnerability-free application.

Canonical candidate validation passed TypeScript, ESLint, all 127 active Node tests
(125 established tests plus two lifecycle regressions, with real-publication sampling
enabled), 82 Weather Python tests and 15 storage-root tests. The 95-file import audit
has zero cycles/unresolved imports; documentation links/whitespace and bounded privacy
checks pass. Standalone production publication is 20,421 files / 633,781,652 bytes,
with the unchanged 20260907T18Z catalogue, ten fields and 24 timesteps. Legacy
public/weather/gfs remains absent and storage-root names are absent from browser
assets. The existing bundle-size warning remains outside this task.

The corrected canonical browser matrix passed 15/15, five per established viewport;
1366x768 pressure took 38.3 seconds under the unchanged timeout. Diagnostics report
zero page exceptions, HTTP errors and GFS request failures; the 105 recorded failed
requests are Terrarium URL cancellations with net::ERR_ABORTED. No historical,
renderer/Unreal, private or authoritative external data was changed.

Phase 7B remains a candidate until canonical validation and a second independent
clean-start acceptance gate pass, followed by normal publication. The final commit
and validation report establish that outcome; no completion is claimed here in
advance. Phase 7 contains only 7A and 7B. No Phase 7C, architecture work or next
development programme is introduced.

## 2026-10-01 — Post-foundation maintenance

### MapLibre security maintenance

Migrated the direct MapLibre dependency from 5.24.0 to exact 6.11.2 to resolve
[GHSA-jrc7-96c5-q579 / CVE-2026-85061](https://github.com/advisories/GHSA-jrc7-96c5-q579).
The attribution sanitizer bypass affects versions through 6.4.0; 6.4.1 is the
minimum patched release. Meridian accepts third-party attribution, so the advisory
applies. The earlier Phase 7 entry records the then-unresolved state accurately.

Compared 6.4.1 with the current stable 6.11.2 before editing. Chose 6.11.2 for
subsequent attribution hardening, custom-layer fixes and terrain/camera fixes within
the same v6 migration surface. See the [v6 changelog](https://github.com/maplibre/maplibre-gl-js/blob/v6.11.2/CHANGELOG.md)
and [migration guide](https://github.com/maplibre/maplibre-gl-js/blob/v6.11.2/docs/guides/v5-to-v6-migration-guide.md).
Only MapLibre and its required transitive dependency graph changed; no unrelated
dependency upgrade, override or advisory suppression was introduced.

The compatibility changes are bounded: namespace imports replace removed default
exports; route/contour modules explicitly import their existing GeoJSON types;
the global mouse-exit listener uses the supported `mouseout` event. Atlas explicitly
retains v5 vector-tile overscaling with `zoomLevelsToOverscale: undefined`.
An initial production build emitted no worker, and its fallback worker URL returned
HTML. Atlas now configures the [upstream Vite worker setup](https://github.com/maplibre/maplibre-gl-js/blob/v6.11.2/docs/index.md#installation)
using `?worker&url`, bundling the worker and shared ESM dependencies into one emitted
asset. Development and production browser checks confirm it loads normally.

MapLibre v6 requires WebGL2; the custom wind renderer already uses WebGL2/GLSL ES 3
and needs no rendering rewrite. Its lifecycle, shader projection inputs, repaint,
cleanup and layer ordering remain unchanged. The required style-spec dependency
now brings a Node-22-only JSON parser, so package engines and current setup docs
require Node >=22.12.0. No App/Atlas/Weather/Traverse ownership boundary changed.

Before migration, TypeScript, ESLint and all 127 active Node tests passed, with one
critical npm advisory. After migration: TypeScript and ESLint pass; all 128 active
Node tests pass without skips, including real-publication sampling and a new
installed/locked-version regression assertion; 82 Weather Python and 15 storage-root
tests pass. The 95-file active import audit reports zero cycles/unresolved relative
imports. Documentation links, whitespace, diff and bounded privacy checks pass.
The production build emits the self-contained worker and retains the existing
large-bundle warning. npm audit reports zero advisories, including zero instances
of the attribution vulnerability.

The unchanged browser matrix passes 15/15: five per 1920x1080, 1440x900 and 1366x768.
Pressure takes 24.7, 22.1 and 22.3 seconds respectively, under unchanged timeouts.
Diagnostics show zero page exceptions, HTTP errors and GFS failures; 51 external
request cancellations are `ERR_ABORTED` (50 Terrarium, one Open-Meteo). Third-party
basemap shield-filter warnings remain descriptive warnings, not worker/module/GL
failures. No browser assertion, scenario, timeout or visual baseline was changed.

Inspected initial-map comparisons and rendered terrain, hillshade, elevation,
satellite fixtures, weather overlays, pressure and route screenshots. The separate
production smoke uses real Terrarium/GFS data, verifies 55-degree pitch and bearing,
terrain/globe transitions, two wind shader variants and visible route features.
Early tile-loading edges disappear in fully loaded captures. One supplementary
all-remote-tiles-settled wait timed out; the identical wait passed on rerun without
changing its condition or timeout. No visible migration regression was found.
Satellite imagery uses the existing neutral browser fixture, not a live account test.

Phase 7 publication lifecycle regressions and real sampling remain green. Dev/test
shutdown does not materialize production GFS; standalone builds still publish only
latest.json and 20260907T18Z: 20,421 files / 633,781,652 bytes, ten fields / 24 timesteps.
External latest.json remains SHA-256
`84878adcacf13463e9c2a5ffd76b6f1a934b3da654ad7f6421fb70ec3b8d0b92`.
Legacy public/weather/gfs remains absent; storage-root names are absent from browser
assets. No authoritative/private data, historical experiment, renderer/Unreal file,
historical ref or phase marker changed. Generated diagnostics remain ignored.

This is post-foundation security maintenance, not a new numbered cleanup phase.
Atlas/world-model development and the next development programme have not begun.

### Tryfan historic open-data reconnaissance

Inventoried the live NRW historic LiDAR tile catalogue over the canonical Tryfan
EPSG:27700 reference bounds `[264900, 357800, 267900, 360800]`, a 3 km × 3 km AOI.
The current and original official WFS layers each return all eight matching
records, independently corroborated by the NRW-linked ArcGIS catalogue and WFS
hit counts. There are no intersecting 0.25 m, 0.5 m or 2 m records; all eight are
1 m with DTM and DSM links. Ten distinct archive URLs respond HTTP 200 to HEAD.
No ZIP or raster payload was downloaded.

Original survey identifiers and acquisition intervals distinguish P_5024
(2007-02-07–2007-04-02), P_6405 (2009-03-18) and P_9378 (2014-03-10). Their
catalogue tile unions intersect 93.33%, 16.89% and 23.56% of the AOI respectively.
These are tile-envelope percentages, not actual valid-data coverage: original
`PERCENT_CO` metadata reports partial coverage within those tiles. Exact historic
swath/valid-cell overlap remains unknown and is explicitly null in the inventory.
No historic group is described as a full-AOI replacement.

The current national 1 m DTM/DSM, acquired 2021-03-02, remains the best verified
open raster source among those examined. Its retained canonical manifest records
9,000,000 valid cells and zero nodata cells for both products; the live national
catalogue confirms 16 delivery-11 tiles covering the reference extent. Lab 009's
3025-vertex reconstruction is resampling, not a finer LiDAR acquisition.

See the [report](atlas/tryfan-lidar-reconnaissance.md) and
[metadata inventory](atlas/tryfan-lidar-reconnaissance.json) for every record,
footprint, URL, query/evidence hash, CRS handling and uncertainty. JSON and coverage
consistency, documentation links, whitespace and bounded diff/privacy checks were
validated. This metadata-only task changes no application, renderer, historical
Lab identity or canonical terrain. Retain the current source; any future historic
comparison must first establish valid-data masks. No new numbered phase, Lab or
Atlas/world-model implementation is introduced.

### Lab 010 — observed natural-colour surface

Created the next Tryfan visual experiment after Lab 009: unchanged measured terrain
plus one actual Sentinel-2 natural-colour observation. Audited all four retained
Lab 005C seasonal observations and verified all 44 retained band files against
their recorded hashes. Selected the summer 2026-07-12 Level-2A product for zero AOI
cloud/cloud-shadow/snow/nodata and higher sun; retained its 1.84% SCL topographic
shadow rather than correcting it. Summer reuses existing Lab 005B native RGB; no
source observation was downloaded, copied or rewritten.

B04/B03/B02 retain 10 m native measurements. DN scale/offset is 0.0001/-0.1;
bilinear EPSG:32630 → EPSG:27700 reprojection produces exact 300 × 300 products
over `[264900, 357800, 267900, 360800]`. Float reflectance remains separate from
the fixed Lab 005C 0.02–0.30, gamma-1 display transform. No sharpening, composite,
classification colour, procedural material, shadow correction or inferred detail
is introduced. Canonical products and PNG remain external, beneath the new
`experiments/earth-lab/tryfan-010/observed-natural-colour-v1` estate.

The optional Unreal adapter connects the same 300 × 300 sRGB texture to Base Color,
with bilinear/clamped sampling, fixed roughness 0.88 and specular zero. Existing
world-space UVs preserve +X east/+Y south registration. Baseline, Lab 009, Lab 010
and Lab 010 plus the existing 50% photographic overlay were exercised without
saving the map. Null-RHI and normal D3D12 validation pass, including measured
Landscape geometry/collision, fixed camera and Lab 009 validators. Map SHA-256
remains `85ef8f1cc9a9fda9b6f2ab3b911bd57831fe75c4009e5ad168ea4956165a260d`;
canonical R16 and Lab 009 identity are unchanged. Four Lab-specific tests and five
existing reference-renderer tests pass. Repeat outputs/manifests are byte-identical,
and independent inverse-coordinate RGB checks detect flips/rotation/band swaps.

See [the Lab procedure](earth-lab/tryfan-010-observed-natural-colour.md),
[provenance manifest](earth-lab/tryfan-010-observed-natural-colour.json) and
[validation evidence](earth-lab/tryfan-010-validation.json). The overhead RGB preview
shows actual spatial colour variation; fixed-camera improvement remains pending
manual A–D inspection. No unreliable SceneCapture frames are accepted. Sentinel
shadows and existing Unreal lighting can compound, and 2026 imagery differs in date
from the 2021 terrain and 2009 photograph. Ten-metre observations cannot resolve
individual rocks, vegetation geometry or material microstructure. This is a visual
research Lab, not a new numbered cleanup phase or Atlas runtime programme.

### 2026-10-01 — Lab 011: observed surface-height structure

The product owner reports that Lab 010's fixed-camera A–D inspection is complete:
the measured terrain captures broad form, observed colour adds real spatial
variation, but 10 m imagery cannot supply the missing fine structure. This is a
subsequent status record; Lab 010's frozen identity and outputs remain unchanged.

Lab 011 measures the signed difference between the retained Welsh Government
2021-03-02 delivery-11 DSM and DTM. Source hashes, identical EPSG:27700 3000×3000
1 m grids and complete valid-cell coverage were verified before subtraction.
No source acquisition, resampling, smoothing, semantic classes or reconstructed
geometry was introduced. Metre/ODN provenance is distinguished from the absence
of an explicitly encoded vertical CRS in the retained TIFFs. Exact rocky-ground
classification rules remain unknown; the difference is not object height.

The median difference is 0.140 m, mean 0.301 m and standard deviation 0.663 m;
70.767% has magnitude ≤0.25 m. Above 1 m, 67.78% of thresholded area lies in
four-connected regions ≥9 m², while 8.88% is isolated cells. Signed negatives and
extrema remain intact. Residual and measured-DTM diagnostics across 1–20 m show
coherent additional information and substantial form already represented by terrain.
Strong steep-slope dependence cautions against treating residuals as added objects.
Weak 10 m colour correlations do not establish semantic classes.

Large diagnostic products remain external in the new tryfan-011 experiment directory;
Git holds code, metadata and documentation only. Two full runs produced identical
outputs/manifests. Six Lab-specific tests and five preserved-renderer tests pass.
UE 5.8.2 commandlet validation exercised baseline, Lab 009, Lab 010 and the new
unlit quantitative residual/50%-photo states; camera, Landscape geometry/collision
and Lab 009 restoration passed, and the canonical map was not saved. Source,
canonical R16 and Labs 009/010 hashes remain unchanged. No lighting build was run;
the previously reported 578 unbuilt objects remain a known fixture limitation.

See [the Lab 011 procedure](earth-lab/tryfan-011-observed-surface-height.md),
[measurement manifest](earth-lab/tryfan-011-observed-surface-height.json) and
[validation evidence](earth-lab/tryfan-011-validation.json). Lab 011 manual
fixed-camera interpretation remains pending; no perspective visual acceptance is
claimed. The DSM contains spatially supported information worth retaining for
later independent evidence fusion, not a semantic inventory of rocks or vegetation.

### 2026-10-02 — Lab 012A: Bluesky high-resolution aerial reconstruction

This isolated evaluation compares a fixed native 25 cm photogrammetric DSM with
neutral, 25 cm, 12.5 cm and 5 cm imagery over SK5639. All four immutable sample
archives have matching British National Grid edge bounds
`[456000, 339000, 457000, 340000]`. Pixel-centre registration, the 25 cm TAB
filename inconsistency and half-pixel TAB/world-file differences are recorded.
The DSM's vertical units/datum are not supplied; metres are an explicit evaluation
assumption. Only the 5 cm imagery supplies a flight date (2018-09-01). Different
vehicles/shadows and unspecified other dates prevent a resolution-only causal claim.

External products preserve all 16 million DSM samples in 64 meshes, with 31,984,002
triangles and no smoothing, simplification or vertical exaggeration. Native RGB
tiles retain 502, 1004 and 2510 pixel dimensions including aprons; the 20k image is
not reduced to fit a GPU texture. Identical analytic shading, geometry, cameras,
exposure and sampling policy control four views across four states. Full GPU mip
byte counts establish native resource residency, rather than trusting dimensions
alone. Source data, generated meshes/textures, Unreal assets and captures remain
outside Git. The samples contain copyright but no supplied redistribution licence;
neither vendor imagery nor rendered images are published by this checkpoint.

An initial D3D12 preparation lost the GPU device under severe memory pressure.
Partial captures were rejected and one incomplete texture reimported from its
verified PNG. Final acceptance used sequential D3D11 processes with zero commandlet
errors. Sixteen 1920×1080 captures retain identical numeric camera and mesh/actor
transforms between states. All 192 native texture resources have complete mip
chains. Four archive hashes, 260 product hashes, 27 independent RGB samples and
three DSM/mesh samples pass; native products reproduce byte-for-byte across three
processing runs. The 152 Earth Lab tests, ESLint and TypeScript/Vite production
build pass. Existing build chunk-size warnings remain unrelated to this Lab.

Inspected views show a modest 25→12.5 cm improvement in these supplied products and
clearer 5 cm roof/marking/crown colour detail at closer distances. Fine texture
does not repair heightfield facades, tree curtains or missing overhangs. Overview
detail is limited by output pixels/mips; acquisition and illumination differences
remain confounds. Urban evidence does not establish Tryfan surface observability.
See [the Lab procedure](earth-lab/bluesky-012a-aerial-reconstruction.md),
[metadata](earth-lab/bluesky-012a-metadata.json) and
[validation measurements](earth-lab/bluesky-012a-validation.json).
The next recommendation is a same-observation controlled comparison, then a
separately approved/licensed small Tryfan pilot if justified. No purchase, Tryfan
integration, production Atlas change, new architecture phase or Lab 012B is begun.

## 2026-10-02 — Riffelhorn / Riffelsee official Swiss source acquisition

Selected a compact 2 × 2 km LV95 rectangle around Riffelhorn/Riffelsee for a bounded
mountain-data suitability investigation. Four official kilometre tiles in each of
SWISSIMAGE, swissSURFACE3D point cloud, swissSURFACE3D Raster and swissALTI3D were
downloaded into the external Atlas source estate. Sixteen originals total
896,360,770 bytes and match the federal STAC SHA-256 values; four extracted LAS
files retain 50,546,426 measured points. All original/extracted hashes, exact native
raster grids and synthetic acquisition tests pass.

Actual tile metadata distinguishes native 25 cm 2023 RGB from its distributed
10 cm grid. LiDAR timestamps establish August 2021 measurements and substantial
August 2022 coverage in the northeast tile despite its collection-2021 name.
The 2024 Valais DTM release uses 2021/2022 LiDAR and 2023 photogrammetric updates;
0.5 m output spacing is not an independent measurement-resolution claim.
Exact image mosaic seamlines, LiDAR instrument details and per-cell DTM update
lineage remain unavailable. Official product terms permit reuse, derivatives,
redistribution and public display with swisstopo attribution.

Offline imagery inspection confirms fractured rock, steep faces, loose deposits,
alpine ground cover, paths, lakes and southern ice/moraine transitions. Deep
shadows, possible tiny unflagged black-image holes, changing ice/water and different
acquisition dates remain explicit limitations. The conclusion is **suitable with
documented limitations**, not co-temporal or a semantic surface inventory.
See [the acquisition report](atlas/riffelhorn-data-discovery.md) and
[asset provenance](atlas/riffelhorn-data-catalog.json).

Only metadata, offline acquisition/inspection code and synthetic tests enter Git.
Sources, extracted LAS, official evidence and attributed 2-D previews remain
external. Production Atlas, Tryfan/reference renderer and Lab 012A are unchanged.
No renderer, common terrain grid, Lab 012B, classification or new architecture
phase was created. A separately authorised mountain representation experiment is
the recommended next action; no purchasing decision was made.

## 2026-10-02 - Lab 012B: observed Riffelhorn mountain representations

Compared complete 2 x 2 km swissALTI3D and swissSURFACE3D raster surfaces in an
isolated external UE 5.8 project, retaining every 0.5 m cell-centre sample:
16 million unique vertices and 31,984,002 triangles per representation. Tiled
SWISSIMAGE retains the official 10 cm distributed grid while explicitly remaining
25 cm native image information. Seven deterministic cameras produce 28 neutral/RGB
comparisons with unchanged transforms and complete native texture mip resources.

Scanned all 50,546,426 retained classified LiDAR returns and examined seven small
contrasting patches with sampled exact neighbour spacing, slope/scale diagnostics,
raw profiles and native triangle distances. Major rock/ledge/protrusion geometry
is often already retained by the DTM. Local DSM deposit roughness survives better
at short scales; steep cliffs still show heightfield curtains and texture stretch.
Some raw observations around discontinuities do not survive that representation,
although most queried ground returns fit the DSM within centimetres. Large ice/debris
product differences remain confounded by earlier observations versus later updates;
shadowed orthophotos do not supply missing cliff appearance. No semantic classes,
inferred geometry, procedural detail or production architecture requirement follows.

Two complete native preparations reproduce the same identity and all 209 product
hashes; 16 original and four extracted source hashes remain unchanged. All 28
captures, imported topology/bounds, camera poses and native texture resources pass.
All 157 Earth Lab tests, 16 terrain-research tests, ESLint and TypeScript/Vite build
pass, with documented existing build/deprecation and non-blocking UE import warnings.
Sequential D3D11 captures use paging; native geometry and textures were inspected.
Sources, products, compiled UE assets and captures remain external. Production,
Tryfan, Lab 011 and Lab 012A are untouched.

See [Lab 012B findings and viewing procedure](earth-lab/riffelhorn-012b-mountain-reconstruction.md),
[identity/provenance](earth-lab/riffelhorn-012b-metadata.json),
[measurements](earth-lab/riffelhorn-012b-measurements.json) and
[validation](earth-lab/riffelhorn-012b-validation.json).
A small stable steep-rock observation-versus-heightfield comparison is the next
research question, requiring separate authorization. No subsequent Lab or Atlas
world-model development is begun.

## 2026-10-02 — Lab 012C: raw LiDAR information retention

Examined three bounded Riffelhorn patches from Lab 012B: the 60 m summit cliff,
a 30 m sloping-ground control and a distinct 30 m rough-ground subpatch. Preserved
68,372 original LAS records/XYZ values and native LV95/LN02 coordinates outside
Git. Compared deterministic queries to the exact unchanged native DSM triangles
with an adaptive globally-exact nearest search, multi-scale spherical PCA,
quality/split-repeatability screens, thin equal-scale cross sections and fixed
60/180/600 m direct-point/mesh/overlay views. No reconstructed point topology,
surface completion, synthetic normals or production representation was introduced.

The cliff's exact distance median/p95 is 0.060/1.109 m, versus 0.017/0.053 m and
0.025/0.116 m for the controls. Coherent several-metre lower-face structure is
bridged by the current raster; 19 reliable sampled geometry candidates have
neighbouring support at 2 m PCA radius. Most ordinary ground orientation is
already retained by the actual interpolated render normals. Reliable sub-metre
support is sparse, and a blanket new detail-normal layer is not justified.
Nine finite-XY multiple-height candidates do not pass the conservative coherent
two-sheet test: overhangs/non-heightfield topology remain ambiguous. Large residual
and steep slope alone do not prove true-3D geometry is necessary.

Inspected diagnostics show localized shape loss at close/intermediate distances;
most query displacement falls below a pixel at 600 m. Point-only holes, patch
edges and flat-facet diagnostic shading are explicitly not a completed surface,
production shading benchmark or perceptual user study. A localized adaptive/finer
heightfield test with held-out returns is the single recommended next experiment,
not implemented. Normals cannot repair displaced faces or silhouette.

Two complete final serialized preparations reproduce one identity and all 46
product hashes. Sixteen original/four extracted source hashes, 64 existing DSM
mesh hashes, 45 independent original record/coordinate samples, 24 exact-distance
checks and nine fixed-camera frames pass. All 165 Earth Lab tests (eight new),
16 terrain-research tests, ESLint and TypeScript/Vite build pass; existing
deprecation and bundle-size warnings remain. Sources, arrays and captures stay
external. Production, Tryfan, Labs 011/012A/012B and historical refs are unchanged.
See [Lab 012C methods and findings](earth-lab/riffelhorn-012c-raw-lidar-retention.md),
[provenance](earth-lab/riffelhorn-012c-metadata.json),
[measurements](earth-lab/riffelhorn-012c-measurements.json) and
[validation](earth-lab/riffelhorn-012c-validation.json).

## 2026-10-02 — Lab 012D: adaptive cliff heightfield

Reused only the 60 m summit-cliff patch, with a frozen interleaved 2 m spatial
hold-out across all overlapping flights and a 0.2 m exclusion buffer. Construction,
validation and buffer contain 28,866 / 11,179 / 5,011 returns. Built an explainable
construction-only XY interpolant with explicit support, conflicting-height rejection
and no extrapolation/completion. Tested raw-derived 0.5 / 0.25 / 0.125 m output
grids and one 0.5→0.25 m locally refined heightfield against the exact native provider
triangles. All candidates remain single-valued; finer samples are interpolation,
not new independent measurements. The adaptive mask uses construction evidence only.

Outcome **E — inconclusive**, with no candidate accepted as a recovered surface.
Across 9,652 held-out interior returns, provider median/p95 is 0.056/0.842 m;
finest regular is 0.210/1.448 m. Its extreme p99 improves 2.832→2.253 m, but only
66.15% of query XY has represented support and numerical fit worsens even on common
represented cohorts. Construction fit improves far more than held-out fit. Three
training anchors among the 19 supported 012C candidates improve substantially;
only one held-out anchor has represented XY and improves partially. Nine ambiguous
multiple-height groups remain ambiguous; no non-heightfield topology is proved.

Inspected identical 012C sections and completed-triangle diagnostic frames at
60/180/600 m show partly retained lower bands but holes, narrow bridges and fragile
near-vertical strips. The finest output costs 227,529 allocated samples / 376,040
emitted triangles without a trustworthy shape improvement. Refinement covers
19.22% of area and uses 22,620 samples / 29,886 triangles, versus uniform 0.25 m's
57,121 / 91,128; it reduces cost but does not establish a representation win.
Neither a saturation resolution, adaptive architecture nor true-3D requirement
follows. A robust plane-constrained estimator on the same frozen split is the
single next experimental question, not implemented; Tryfan needs independent evidence.

Two complete final runs reproduce one identity and all 51 external product hashes.
All original source hashes, 209 frozen 012B products, 46 frozen 012C products,
45,056 split memberships/buffer, exact baseline, 80 repeated distances, eight full
brute-force candidate checks and fixed camera/section identities pass. All 174
Earth Lab tests (nine new), 16 terrain-research tests, ESLint and TypeScript/Vite
production build pass. Existing NumPy/rasterio deprecation and Vite bundle/plugin
warnings remain. Validation of the experiment is separate from its unsuccessful
surface acceptance. Arrays, meshes, support fields and captures remain external;
production, Tryfan, previous Labs and historical refs are unchanged.

See [Lab 012D methods, outcome and viewing commands](earth-lab/riffelhorn-012d-adaptive-cliff-heightfield.md),
[identity](earth-lab/riffelhorn-012d-metadata.json),
[measurements](earth-lab/riffelhorn-012d-measurements.json) and
[validation](earth-lab/riffelhorn-012d-validation.json).
No subsequent Lab, true-3D reconstruction or production Atlas change is begun.

## 2026-10-02 — Lab 012E: robust cliff heightfield estimation

Completed the final planned Riffelhorn heightfield experiment on the exact 60 m
summit patch and frozen 012D construction/held-out/guard split. One construction-only
robust local-plane estimator uses the already studied 1/2 m physical contexts,
repeatability/planarity screens, robust scalar-height prediction, explicit XY/XYZ
support and orientation-consistent edge rejection. The unchanged 0.125 m working
grid is interpolation, not new measured resolution. Historical provider, regular
and adaptive baselines are read directly; no prior Lab implementation is changed.

Outcome **F — inconclusive**, and the reconstruction branch is **closed for now**.
The 9,652 held-out returns have robust median/p95/p99 0.521/3.555/8.057 m, versus
provider 0.056/0.842/2.832 m. Emitted surface covers 47.16% of the native-centre
footprint and only 21.20% of held-out XY. Two historical candidate positions
improve substantially, including an independent held-out lower-face anchor,
but seventeen remain unresolved. Fifteen positions have reliable construction
planes at 2 m context, showing that estimator refusal is not simply missing local
evidence. All nine ambiguous multiple-height groups remain ambiguous; no defensible
non-heightfield topology is demonstrated.

The new observability diagnostic separates fit conflict, bracketing, nearest
physical support and nominal steep-surface conditioning. An independent post-fit
full-survey audit finds substantial gaps between lower/upper bands, not just
hold-out gaps. Those gaps do not identify a unique intervening face, while strict
local prediction also rejects some measured structure. The experiment does not
cleanly separate all estimator restrictions from survey support limits. It provides
no evidence-backed reason for an automatic further interpolation Lab.

Exact sections and native 60/180/600 m frames were inspected: long unsupported
bridges are reduced by refusal, leaving fragmented panels/holes rather than a
recovered stable cliff. No completed-surface visual improvement is accepted.
The result remains a local difficult-cliff issue, not a reason to rebuild ordinary
Atlas slopes or add blanket detail normals. Tryfan needs its own source/support
analysis; no Swiss numerical thresholds transfer automatically.

Two complete final runs reproduce one identity and all 30 external product hashes.
Source hashes and 209/46/51 frozen B/C/D products pass, together with all 45,056
split memberships, construction-only fitting, repeated diagnostics/distances,
brute-force checks, six sections, three cameras and nine byte-identical historical
frames. All 182 Earth Lab tests (eight new), 16 terrain-research tests, ESLint,
TypeScript/Vite production build and JSON/link/privacy checks pass. Existing
deprecation and build-size/plugin-timing warnings remain. Products/captures stay
external; production, Tryfan, prior Labs and historical refs remain unchanged.

See [Lab 012E outcome, methods and inspection commands](earth-lab/riffelhorn-012e-robust-cliff-heightfield.md),
[identity](earth-lab/riffelhorn-012e-metadata.json),
[measurements](earth-lab/riffelhorn-012e-measurements.json) and
[validation](earth-lab/riffelhorn-012e-validation.json).
No new Lab, true-3D reconstruction or production integration is begun.

## 2026-10-02 — Riffelhorn visual synthesis and finite experiment design

Synthesised Labs 011 and 012A–012E after the closed heightfield-reconstruction
branch. Inspected native 1920×1080 whole-AOI, mountain-face, alpine-ground and
steep-face captures, complementary contacts, the downloaded orthophoto crop and
the existing cliff diagnostics. Relief is present but faintly shaded; RGB adds
useful boundaries while dark faces and stretched steep-face colour remain.
The actual 012B material is unlit RGB/neutral colour multiplied by a fixed
0.65–1 normal factor, with no cast-shadow or atmospheric additions. Its output
does not establish whether controlled terrain lighting can communicate the
already-strong measured geometry adequately.

Documented two core experiments: fixed-geometry lighting/readability, then
orthophoto projection and photographed illumination. A third same-terrain normal
representation test is conditional on a specific remaining shader/input
discrepancy; it must not become invented sub-metre detail or another LiDAR
reconstruction branch. Three existing core cameras plus one projection control,
bounded comparison sets, explicit acceptance/termination rules and a final
scale-dependent synthesis prevent an open-ended sequence. A limited historical
first-person FATMAP account supports investigating exaggerated normal lighting
and its conflict with photographed shadows, without establishing proprietary
algorithms, normal sources or true-3D cliff topology.

Read-only checks preserve Swiss originals/extracted LAS, all 260/209/46/51/30
canonical 012A/B/C/D/E products and 28 recorded 012B raw frames. Documentation
links, referenced paths, JSON, privacy and diff/scope checks pass. No experiment,
new product, renderer change, source acquisition, production change or Tryfan
change is made; previous Labs and historical refs remain unchanged. The next
recommended action is the bounded lighting experiment, not implemented here.

See [Riffelhorn synthesis and finite visual programme](earth-lab/riffelhorn-visual-synthesis-and-experiment-design.md).

## 2026-10-02 — Lab 012F: terrain lighting and readability

Implemented only the first finite-programme experiment on a physical copy of the
unchanged 012B surface scene. Reused overview, Riffelhorn-oblique and alpine-path
cameras at 1920×1080 / 50° HFOV. Compared the original 0.65/0.35 normal response
with fixed 0.35/0.65 directional illumination, then the same illumination with
terrain depth visibility. Opposing NE/SW azimuths at 60° elevation provide a small
direction-sensitivity control; neutral/RGB pairs isolate source appearance.
Thirty native frames and six contacts remain external. No vertex, normal, UV,
source image, exposure or atmosphere changes; no reconstruction branch reopened.

Outcome B: illumination communicates existing ridge/channel separation and ledges
more clearly, especially in neutral geometry. RGB gains are smaller; the large
photographically dark face remains about 84.2% near-black in its fixed window.
Opposing light produces apparent competing illumination, while close cast shadows
show mottled sampling artefacts. Cast visibility is not accepted as a blanket
enhancement. Steep-face colour stretching and local raster curtains persist.
These are evidence for the already-planned projection/baked-illumination experiment,
which is not begun. No new normal/detail experiment is automatically justified.

Two independent final captures reproduce all 30 RGB arrays and canonical PNG
hashes exactly. Unused UE export alpha is omitted; attribution remains in PNG
metadata/contacts. Historical baseline materials/inputs/poses are unchanged, but
display dither differs from old PNGs: signed mean differences below 0.0011 encoded
levels and 8×8 block mean differences below 0.326, documented without filtering
published frames. All 596 previous canonical products, 28 raw frames, Swiss sources
and historical/copy assets pass hash checks. All 187 Earth Lab tests (five focused
new tests), 16 terrain-research tests, ESLint, TypeScript/production build and
JSON/link/privacy/diff checks pass; existing dependency deprecation and build
size/timing warnings remain. Production Meridian, Tryfan and previous Labs are
unchanged. No second experiment, new source acquisition or architecture change.

See [Lab 012F result and exact viewing/reproduction commands](earth-lab/riffelhorn-012f-terrain-lighting.md),
[identity](earth-lab/riffelhorn-012f-metadata.json),
[measurements](earth-lab/riffelhorn-012f-measurements.json) and
[validation](earth-lab/riffelhorn-012f-validation.json).


## 2026-10-03 — Lab 012G: orthophoto projection and baked illumination

Continued from 45d101351d9dbcab29845f73b2364e0be7b3e319. Reused the unchanged
012B surface, source RGB, four benchmark cameras and compiled 012F L1 northeast
lighting. Added one bounded global low-frequency RGB gain, a separate continuous
surface-texel-density diagnostic, source-window tracing and a pre-display scalar
audit. All raw/corrected textures, diagnostic arrays, projects and captures stay
under external `experiments/earth-lab/riffelhorn-012g/projection-illumination-v1/`.

Outcome F: source-causal ranking inconclusive, with projection loss independently
established. The exact dark-face window remains 84.00% near-black originally and
83.41% after correction. Its sampled source is only 2.92% near-black; shader probes
confirm real positive variation reaches the renderer and is suppressed by final
display conversion. Do not mistake black output for empty source data. Steep
facets spread nominal 25 cm information over metres; brightening cannot repair
that mapping. Paths/boundaries survive; dark grain is amplified without improving
measurement confidence. The gain is not an accepted cliff-appearance replacement.

CONDITIONAL NORMAL EXPERIMENT JUSTIFIED: NO. No specific ordinary-terrain normal
representation discrepancy meets the finite programme's gate. The programme ends
after 012G for synthesis; geometry reconstruction remains closed. No third Lab,
new data, production architecture, Tryfan change or previous Lab implementation
change. The report separates observations, ideal projection accounting and source/
display uncertainty, rather than forcing a source-empty or resolution-only verdict.

Verification: 16 frames repeat byte-identically; full processing repeats 113
canonical hashes (91 regenerated source/texture diagnostics), plus a separately
hashed byte-identical HDR scalar audit. All 635 prior canonical products, 20 Swiss
source files and historical captures/packages remain unchanged. 192 Earth Lab and
16 terrain-research tests, ESLint, TypeScript/Vite build, JSON/link/privacy/whitespace
and scoped Git checks pass. Existing deprecation/build warnings remain. Detailed
measurements, provenance, commands and limitations are in
[Lab 012G](earth-lab/riffelhorn-012g-projection-and-illumination.md).

## 2026-10-03 — Close Atlas terrain research epoch

Closed the 012A–012G epoch at the 012G evidence checkpoint. Created the
[final terrain synthesis](earth-lab/atlas-terrain-representation-synthesis.md),
[research map/fresh-session handoff](research/atlas-research-map.md) and
[sourced literature record](research/literature/terrain-representation.md).
Historical Labs remain faithful to their original results. Riffelhorn heightfield
reconstruction and the finite visual programme remain closed; no conditional normal
experiment or automatic continuation is authorized.

The handoff separates Meridian measurements, external methods and untested directions.
It records negative results, source/display/projection uncertainty, physically informed
appearance recovery as untested, future Swiss acquisition caveats, external-product
locations and research-contribution discipline. Future Atlas work should characterize
the problem and review established scientific/engineering methods before proposing
a bounded experiment. Return to deliberate design/planning, not another Lab by default.

Documentation/link/anchor, referenced-JSON, citation-URL syntax, privacy, whitespace
and scoped Git checks pass. Read-only verification confirms all 748 canonical A–G
products, historical captures/packages, Swiss sources, Bluesky originals and supplementary
HDR probes unchanged. No production/architecture, Tryfan, implementation, source-data
or generated-product changes; no new acquisition or experiment. Unrelated builds and
rendering suites were not rerun for this documentation-only checkpoint.

## 2026-10-03 — Separate visual terrain and analytical elevation policies

Confirmed clean canonical main at `4c15639`. The numeric elevation sampler imported
its AWS tile URL and z15 ceiling from the visual MapLibre layer module, so a visual
provider change could unintentionally alter route analysis. Added independent Atlas
policies in `map/visualTerrainConfig.ts` and `terrain/analyticalElevationConfig.ts`.
Both intentionally retain the same AWS Terrarium dataset. Visual credits now live
with the visual DEM policy; geometry/relief delivery ceilings remain z14/z15 and
are no longer described as native scientific resolution. The analytical policy
states the fixed Terrarium RGB / XYZ Web Mercator / 256-pixel / z15 contract.

No App, Traverse or Weather code changed. Exaggeration, relief, projection/lifecycle,
pixel registration, image decoding, bilinear/cross-tile sampling, wrapping, latitude
handling, six-worker concurrency, 96-tile cache and cancellation/failure behavior
are preserved. The historical `terrain-analysis-dem` source ID remains; its comment
clarifies that it belongs to visual relief, not analytical route sampling. Existing
MapLibre/sampler differences and ineffective IGOR altitude/accent settings remain
outside this change. Future analytical source changes require explicit assessment
of profiles, gradients, timing, arrival-time Weather sampling and derived conditions.

Six new deterministic Node/Vite tests in
`scripts/atlas/test_terrain_policies.mjs` pass, including substitution of different
visual settings while analytical AWS requests/values remain unchanged. Additional
repository-only comparison against checkpoint source confirms exact equality of
31 captured visual configuration/lifecycle operations and ten analytical fixtures,
including repeat/cache values, requests and progress. ESLint, TypeScript and Vite
application bundling pass; existing large-chunk and plugin-timing warnings remain.
The normal build command used an ignored temporary Vite config retaining React and
omitting external GFS materialization/public copying. Production data publication
and live browser/provider validation were not run; actual meridian-data/private
were not inspected.

The active Node suite reports 132 passes, one failure and one live-publication test
skipped. The unchanged Forecast Workspace test at
`scripts/ui/test_desktop_workspace.mjs:190` depends on the current wall-clock hour:
at 02:00 its selected fixture precipitation is unavailable, so the expected
`mm / h` unit is absent. An isolated controlled-clock run passes. This unrelated
fixture issue is recorded, not fixed. Tests used an empty data-root stand-in and
synthetic publication fixtures, never the real data estate. Architecture documentation
records the independent policies. No provider migration, new Lab or subsequent
visual-improvement work is included.

## 2026-10-03 — Bounded production Atlas native relief evaluation

Started from clean canonical main at `669fbd0`, equal to locally recorded
origin/main. Held AWS Terrarium, both independent source policies, z14/z15 visual
ceilings, analytical z15 sampling, geometry exaggeration 1.45, camera/projection,
imagery and domain behavior constant. Inspected MapLibre 6.11.2's actual shaders,
illumination uniforms, derivative preparation and terrain texture caching. IGOR's
configured altitude/accent are inactive, so were not counted as baseline controls.

Compared the frozen IGOR baseline with IGOR strength ×1.5, restrained native
four-direction cosine relief and a limited single-direction basic control.
Fixed Tryfan landscape/planning/close cameras, South Downs and Cambridge controls,
90°/180° rotation, optional elevation colors, normal GPX import, substantial
synthetic numeric precipitation through production Weather, and real configured
satellite imagery. No mocked terrain/imagery or external data/private inspection.

Accepted the modest IGOR strength increase: clearer ridges, valley walls and
connected slopes, strongest at planning scale, with smaller gains in landscape
and close views. Controls and route/label/rain legibility remain usable. Retained
the continuous zoom taper, map anchor/direction, colors and satellite suppression.
Multidirectional relief exposes some boundaries but is more banded and models
broad slopes less continuously in the restrained configuration; it is not a clear
overall replacement. Weak satellite relief changes tone without a convincing
comprehension gain. These are bounded qualitative observations, not a blinded
user study or universal rejection of multidirectional relief.

Added a bounded Playwright reproducer, with capture-only Vite map access and
ignored PNG/style/camera/network/hash manifests; no production experiment controls.
38 comparison captures and three fresh-production captures record the result.
Some in-place scalar paint updates retained stale terrain RTT textures; captures
refresh layer visibility with zero-duration strength transitions and wait for
rendering to settle. Fresh default captures independently verify the choice.
No runtime caching/lifecycle workaround is shipped. High-pitch fog, other overlay
combinations, live paint caching, source quality and physical appearance remain
separate questions; closed Riffelhorn branches are unchanged.

Verification: seven focused terrain-policy tests pass, including actual native
expression evaluation, satellite suppression/restoration, reconfiguration and the
existing analytical independence/decoding/addressing tests. The active Node suite
reports 134 passes, zero failures and one live-publication test skipped, using an
empty data-root stand-in and synthetic fixtures. The previously clock-sensitive
Forecast Workspace test passes unchanged in this run. ESLint and TypeScript/Vite
application build pass; the existing large-chunk warning remains. Build used the
ignored application-only Vite config to omit external GFS publication and public
copying; full Weather publication and unrelated Python research suites were not run.
Browser captures have no page exceptions or HTTP errors. Diagnostics retain
`ERR_ABORTED` tile cancellations during view/visibility/projection changes; loaded
captures retain valid terrain. OpenFreeMap shield-filter warnings remain. Repeated globe/terrain transitions pass.

The [evaluation record](atlas/native-relief-evaluation.md) freezes baseline,
methods, exact cameras, evidence limits and reproduction commands. Architecture
records the selected presentation policy. No new Lab, provider migration, physical
lighting, custom terrain renderer, analytical/Weather/Traverse change or next phase.


## 2026-10-03 — Bounded Atlas global terrain foundation evaluation

Started from clean canonical main at `d05f054`, equal to locally recorded
origin/main. Externally verified Mapterhorn before browser integration, against
current official documentation, live TileJSON/catalogues, upstream source records
and repository `077e6530`. The service passed a bounded experimental gate:
512-pixel lossless WebP Terrarium, XYZ/Web Mercator, direct browser/CORS access,
global Copernicus DSM fallback and finer regional terrain. This is not blanket
production rights clearance or an operational service guarantee.

Held strengthened IGOR, colors/direction/anchor, exaggeration 1.45, atmosphere,
projection, imagery, route styling and analytical AWS policy constant. A private
Vite loader substitutes only visual configuration; default AWS and every production
source file remain unchanged. No user-facing provider selector, dependency, source
resolver or provenance implementation. Added a bounded capture reproducer, live
numeric probe and two deterministic policy tests; generated products remain ignored.
No meridian-data or meridian-private access, new Lab or provider archive acquisition.

42 controlled captures cover Tryfan/Riffelhorn landscape, planning, close and
limited extended delivery; rolling/flat controls; rotation; optional elevation
colors; real GPX route/analytical sampling with synthetic rain; satellite;
coast/open water; Nepal global fallback; one public Swiss source-coverage edge.
Regional mountain definition improves substantially at planning/close scales.
English sampled tiles are nearly unchanged because AWS already uses UK LiDAR.
Higher local tiles contain additional information, with modest incremental display
gains. Steep-face striping remains unresolved. No appearance-based accuracy claim.

512 pixels changes native tile selection and mesh LOD; MapLibre's unchanged
hillshade shader also applies tile-zoom-dependent amplification. That confound is
recorded separately from matched-grid decoded elevation differences. Three short
transects show no isolated height step at the inspected coverage edge, not global
seam validation. Sparse children produce 58 actual 404 responses; native parent
fallback retains terrain in inspected views. Zero page exceptions; diagnostics
retain ordinary ERR_ABORTED cancellations. Globe/terrain transitions pass.

Production remains AWS. Common vertical datum, zero/nodata/water semantics,
source-specific global attribution, sparse-delivery expectations, service/versioning
commitments and exact clicked-point provenance need an explicit adoption decision.
Coverage metadata identifies candidate sources, not a per-pixel winner or confidence.
The [evaluation record](atlas/global-terrain-foundation-evaluation.md) preserves
primary references, date, contract, dataset/resolution distinctions, cameras,
quantitative/visual findings, limitations and reproduction commands, labelled M/E/H.
Closed Riffelhorn branches and analytical/Weather/Traverse behavior remain unchanged.

Validation: nine focused policy tests pass; active Node suite 136 passes, zero
failures, one live-publication skip (137 tests), using an empty data-root stand-in
and synthetic fixtures. The clock-sensitive Forecast Workspace test passes unchanged.
ESLint, TypeScript/application Vite build, new JS syntax checks, Python compilation,
diff checks and unchanged production-source checks pass. Build uses the existing
ignored application-only config to avoid external GFS publication/public copying;
existing large-chunk warning remains. Full publication, unrelated research suites,
other browser families and performance load tests were not run. No migration or
subsequent Atlas programme was begun.

## 2026-10-03 — Direct Riffelhorn regional visual-terrain prototype

Started from clean canonical main at `340bf521`, equal to locally recorded
origin/main. Verified only the four retained official 2024 swissALTI3D 0.5 m
float32 LV95 TIFFs, receipts/item provenance and relevant release records. No new
Swiss acquisition, private estate, imagery, swissSURFACE3D or historical cliff
preprocessing. The distributed grid is not independent 0.5 m measurement resolution.

Added isolated deterministic preparation, verification, loopback delivery and
private-Vite visual override/capture tooling. Direct TIFF mosaic→horizontal Web
Mercator reprojection→256-pixel XYZ Terrarium PNG, average through z17/bilinear z18,
547 terrain tiles plus 547 contributor masks, 42.095 MB plus manifest. Swiss LN02
heights remain unchanged; outside cells use frozen AWS input heights and explicit
cross-parent z15 overzoom at higher delivery levels. Every production source file,
AWS default/analytical policy, IGOR curve, exaggeration 1.45, imagery, domain
contracts and lifecycle behavior remain unchanged. No normal experimental UI/startup
hook or generic resolver was added.

MapLibre has one active terrain source and no automatic regional/global DEM
composition; the bounded prototype supplies a composed endpoint to its two existing
visual DEM caches. Clearer interior ledges, channels and moraine reproduce earlier
Mapterhorn gains: a retained matching-grid tile differs by about 0.063 m RMS, not
independent accuracy evidence. Finer delivery converges toward source-grid samples;
native heightfield LOD/steep-face limitations remain. Actual z16.2 geometry reaches
z16 and relief z18, rather than every finest sample becoming a vertex.

The hard 2×2 km AOI join fails acceptance. Twelve transects expose spatially varying
Swiss-minus-AWS differences roughly −112 to +51 m at the boundary and up to 70.17 m
adjacent 1 m composed-sample changes. Multiple boundary cameras/rotations show false
walls and abrupt shading. Source/measurement/datum differences are not separable
from these overlaps; no constant correction or invented vertical transformation
was applied. Available horizontal operation reports 1 m accuracy, independently
of encoding precision. Codec error is ≤0.001953125 m, while an independent z18
source-grid transfer check gives 0.047 m RMS and 0.654 m maximum: total preparation
is not claimed to have 2 mm fidelity. Production remains AWS.

28 accepted captures cover landscape/planning/close/detail, five boundaries,
rotation, outside control, normal synthetic GPX import and real satellite. Route
distance/ascent/descent/moving/break estimates agree; absolute departure follows
wall clock. Weather is honestly unavailable through explicit 503 fixtures, not
changed or newly evaluated. Initial missing redirect CORS and pre-imagery-idle
captures were retained as negative diagnostics and corrected in tooling only.
No accepted DEM HTTP errors/page exceptions; ordinary cancelled requests remain.
Repeated globe/Mercator transitions pass. The compact product is practical locally,
but redirects and globally available overzoom increase request/delivery burden;
bounded response-body counts are not a wire-transfer/FPS/CDN benchmark.

Verified all 1,094 generated file hashes identical across independent rebuilds.
The final manifest records source authority/release, CRS/LN02/grid spacing, exact
inputs/receipts, frozen AWS hashes, processing/toolchain, contributor masks and
output identity; the verifier rejects catalogue/source provenance drift and uses
canonical LF hashes for repository text across clean Git checkouts. Canonical
sources and large products remain outside Git. Six synthetic Python tests and ten
focused policy tests pass. Active Node suite: 137 passes, zero failures, one live
publication skip (138 tests); an initial unexplained temperature-contour test-process
failure passes isolated/full rerun without edits. Clock-sensitive Forecast Workspace
passes unchanged. Lint, TypeScript/application-only build, syntax/compilation,
product/manifest verification, source-equivalence and diff checks pass; existing
large-chunk warning remains. Full external Weather publication, unrelated research
suites, cross-browser testing and load benchmarks were not run.

The [evaluation record](atlas/riffelhorn-regional-terrain-prototype.md) and
[lightweight product identity](atlas/riffelhorn-regional-product.json) preserve
contracts, exact inputs/cameras, M/E/H findings, regeneration and limitations.
Architecture/navigation record only the established composition constraint and
failed hard join. Next decision concerns source support, defensible boundary behavior
and vertical accounting before any general resolver. No adoption, Swiss imagery,
analytical migration or subsequent Atlas phase was begun.


## 2026-10-03 — Bounded Riffelhorn terrain reconciliation investigation

Started from clean canonical main at fe8addc, equal to locally recorded origin/main.
Verified four official Swiss inputs, the prepared product and cached AWS contributors.
Nine z15 headers identify EU-DEM; upstream DSM/reference semantics do not establish
the hosted derivative's exact height datum. Public joerd source lacks the relevant
EU-DEM ingestion module. Swiss LN02/LHN95 differences are sub-metre, far smaller
than the measured field, but do not justify an invented LN02-to-AWS operation.

Reviewed primary stable-terrain co-registration, source-priority mosaics, vertical
operations, fixed/adaptive overlap methods, production edge/provenance requirements
and conditional frequency fusion before experiments. The 2 m diagnostic field has
mean −35.55 m, median −8.31 m and RMS 68.84 m, with broad southern negative disagreement
and positive ridge lobes. Mixed scales and unstable quadrant translation fits do
not isolate measurement, misregistration, datum or possible glacier change causes.

Only two blending controls were tested: a 250 m feather and an uncapped adaptive 3°
overlap diagnostic, with contribution masks. Twenty edge/four corner profiles remove
the ideal edge step and leave outside AWS unchanged. Fixed overlap retains 56.25%
pure Swiss cells but reshapes the collar. Adaptive retains 33.28%, changes ≥500 m
interior by 37.95 m RMS, and retains 0.794 of its sigma10 m detail RMS. Nearest-edge
width handling also adds lateral artifacts; this does not indict all GRASS methods.
24 paired application captures preserve renderer/exaggeration and show altered
transition terrain, including an adaptive depression. Neither method is accepted.

A protected interior, adequate external source support/overlap, height/epoch/error
accounting and contributor/product identities constrain the next decision. The 2 km
research crop is not an accepted production seamline. No larger acquisition,
resolver, imagery, new provider, datum correction or reopened Lab followed. Every
src file and visual/analytical AWS, Weather/Traverse, rendering and lifecycle remain
unchanged. Generated grids/profiles/figures (~61.83 MB) stay in external experiments;
no new tile pyramid or source duplication. The [record](atlas/riffelhorn-terrain-reconciliation.md)
links exact identities, compact results/capture hashes and reproduction commands.

Independent rebuild reproduces complete identity/output hashes. Thirteen synthetic
Python tests and ten expanded policy tests pass. Active Node suite 137 passes, one
live-publication skip, zero failures; Forecast Workspace passes unchanged. Lint,
TypeScript/application-only build, syntax, provenance and diff checks pass; existing
chunk warning remains. Capture-only cancellation handling and basemap sprite warnings are documented. No new Weather/satellite/globe claim, other-browser/load
test or full external GFS publication validation. Local evaluation services stopped.

## 2026-10-03 — Atlas terrain source/product metadata foundation

Starting clean main at `6d36b46`, derived source/product requirements from the
global foundation, direct Riffelhorn and rejected reconciliation reports. Reviewed
primary STAC Item/Projection/Raster/Processing, RFC 7946 and W3C PROV concepts;
the [decision](atlas/terrain-source-product-architecture.md) records sources,
evidence table, terminology, model, examples, limitations and next-step rationale.
No standards-compliance claim or new dependency.

Added owned types, focused validation and typed evidence snapshots under
`src/atlas/terrain/metadata/`. Source identity, release, acquisition, grid,
height/surface semantics and rights are separate from derived delivery, contributors,
processes and revisions. Coverage, assessed support, protected interior and
transition support are independent spatial roles; footprints may be geographic,
explicit native-CRS rectangles or referenced inventories/masks. Unknowns remain
explicit. Products need not be tiled or Terrarium; no renderer configuration is
required. Riffelhorn v1 correctly retains heterogeneous Swiss LN02/AWS-unknown
heights and immediate input masks. Mapterhorn retains partial catalogue lineage
and sparse fine coverage; it is not a production dependency.

Twelve semantic tests cross-check all four official input hashes and prepared
identity/manifest/encoding against the original record, plus unknown height/CRS,
resolution/delivery separation, independent support, fallback, contributor masks,
non-tiled output and recorded transformation semantics. Existing ten terrain-policy
tests pass. Existing active application suite separately: 138 tests, 137 pass,
one live-publication skip, zero failures; Forecast Workspace passes unchanged.
New model tests: 12 pass. Combined focused model/policy invocation: 22 pass.
Two combined full-suite invocations completed all 149 assertions but the unchanged
route-foundation test process then exited with Windows code 3221225477, adding one
file-level failure (151 total including that failure and the skip). Its ten tests
pass isolated, and the existing suite passes without the new test process. Cause
unresolved; do not label the combined invocation clean or silently modify route
tests. Lint, TypeScript and application-only build pass (external GFS/public
materialization omitted with the existing ignored validation config; existing
chunk-size warning). Focused documentation/reference and diff checks pass.

All prior production runtime files, visual AWS policy, independent analytical
AWS z15/256, IGOR, 1.45 exaggeration, camera/lifecycle, Weather and Traverse are
unchanged. No metadata imports from production and no external data access,
generation, acquisition, resolver or provenance UI. The smallest recommended next
implementation is a deliberately supported larger Riffelhorn source selection
and unreconciled product using this model, after defining protected purpose/area
and support/epoch/quality requirements. Unknown AWS height semantics still block
claiming physical harmonization; additional support alone does not accept blending.
That next task was not performed.

## 2026-10-04 — Larger authoritative Riffelhorn support product

### Goal

Replace the research crop as an analysis asset with one justified, unreconciled
Swiss support selection, preserving production and the protected benchmark.

### Result

Defined a 1.5 km protected circle and acquired whole kilometre tiles covering a
10×10 km LV95 selection, giving at least 3.5 km source collar. Reused four files,
downloaded 96 official 2024 swissALTI3D assets, and verified all 100 against official
SHA-256 hashes. Source storage is 1.67 GB, with zero nodata cells. LN02 and 0.5 m
distributed-grid semantics remain explicit; measurement resolution/epoch per cell
are not invented.

Generated a pure Swiss z12–18 Terrarium product: 11,429 tiles / 931 MB in 12.8 minutes.
An independent complete rebuild matches all tile, VRT and manifest hashes. Sampled
z18 transfer/join discrepancies are at millimetre scale. Atlas metadata actively
describes the source, lineage, coverage and protected interior; a minimal uniform
immediate-contribution case avoids an unnecessary constant mask. Transition support
remains unknown. No AWS fill, datum correction, reconciliation or fallback occurs.

Expanded 10 m diagnostics show a continuing broad southern/eastern negative corridor
and finer sign-changing differences: full range −163.64…+195.12 m, RMS 30.23 m.
Northern quadrants are closer on average, but neither a stable mask nor physical
reference equivalence is established. The larger asset materially improves support
analysis without accepting its rectangle as a seamline.

Real-app captures retain benchmark detail with unchanged IGOR/exaggeration. The
pure hierarchy also fails to supply coarse landscape/planning terrain and has
perimeter/parent gaps, including walls/black voids. Those negative delivery findings
are preserved. Production remains AWS; analytical AWS z15, Weather and Traverse
are unchanged. Normal startup has no external terrain dependency.

### Verification and next boundary

151 active Node tests passed, 1 optional skip; 17 synthetic terrain tests passed;
lint, TypeScript/application bundle, metadata/hash/reference checks passed. The
application-only build omits external GFS publication/public copying and retains
the existing large-bundle warning. Eighteen controlled captures are external.
The [support-product report](atlas/riffelhorn-swiss-support-product.md) contains
contracts, numerical/visual findings, limitations and reproduction commands.

The next bounded decision is physical global-reference/overlap assessment with
defensible stable-terrain evidence, using this asset. No subsequent reference
evaluation, reconciliation, acquisition, resolver or imagery work is performed.


## 2026-10-04 — Global terrain reference and stable-overlap assessment

Started clean main at `68fccda`, local origin/main 0/0. Verified all retained
Swiss source/tile hashes and production invariants. Defined reference role,
decision criteria and independent mask protocol before numerical comparison.
Reviewed authoritative AWS/Joerd, Copernicus, Nuth & Kääb/later co-registration,
GLAMOS/WorldCover and Swiss/NGA vertical-grid evidence. One alternative only:
Copernicus GLO-30; no general provider survey or Mapterhorn rerun.

Retained two official-distribution public COGs (84.37 MB), explicit older 2021
mirror identity, three glacier inventories, a bounded WorldCover window and
defined local geoid grids. Total frozen acquisition is 215.84 MB; all source
hashes/URLs and limitations are in the acquisition record. Offline diagnostic
arrays/masks/maps remain external (about 10.8 MB), not terrain pyramids in Git.

On 7.003 km² of conservative independently selected candidate stable terrain,
Swiss-minus-AWS median/NMAD/RMS is +7.85/9.46/14.88 m. Copernicus common-height
diagnostic gives -0.22/1.79/5.93 m; raw LN02 comparison is also retained.
The defined LN02-to-EGM2008 diagnostic changes heights by +0.17...+0.75 m,
not enough to explain large terrain disagreement; combined geodetic accuracy
remains unknown. No source/product height correction was applied.

Sensitivity supports the comparison, but only 299 cells qualify in the southeast.
Large ridge outliers remain (Copernicus +116.78 m; AWS +173.16 m); ice/temporal
and DSM/DTM differences are not assigned invented causes. Translation signatures
are smaller for Copernicus but vary by sector: no shift is accepted or applied.
Average COG parents agree with direct means within float32 rounding. Global
support/missing-land/ocean and revision decisions remain explicit prerequisites.

The [assessment](atlas/global-reference-assessment.md) recommends Copernicus as
the candidate accountable common/coarse reference, distinct from best available
visual terrain. Existing Atlas types describe the retained published source,
COG derivative and transformed diagnostic; no production metadata adoption or
new resolver abstraction. Production AWS, independent analytical z15, IGOR,
exaggeration 1.45, satellite, camera/lifecycle, Weather and Traverse have no diff.

Verification: repeat matched all 18 array hashes and build identity; 23 synthetic
Atlas Python tests and 156 active Node tests passed, 1 existing optional skip.
Lint, TypeScript and application-only production build passed, retaining the
large-chunk warning; external GFS publication/public copying omitted. Metadata,
source/hash and document references checked. One invalid test-root invocation
was corrected to an empty external root; no unrelated tests changed.

Next bounded step: prepare a separate local Copernicus common/coarse delivery
product with frozen release, explicit height, missing-support and parent policy;
repeat overlap evidence before substituting a newer CDSE release. No blended
hierarchy, reconciliation, imagery or subsequent implementation performed here.

## 2026-10-04 — Copernicus common/coarse terrain product

Prepared the [bounded common/coarse product](atlas/copernicus-common-product.md)
from the frozen public 2021 GLO-30 distribution. Reused the two hash-verified
assessment inputs; four additional whole COGs supply two complete z8 parents
and northern context. Six sources total 254.11 MB; no Swiss data was composed.
Horizontal-only bilinear transfer preserves EGM2008 heights, followed by recursive
2×2 means of unencoded elevations and separate Terrarium encoding at z8–13.
The 2,730 PNG tiles total 327.64 MB; no higher delivery level adds invented detail.

Every tile and working-raster hash matched an independent rebuild. Seeded source
sampling differs by at most 0.000122 m; encoding by 0.001953 m. All parent pixels
match the declared rule; direct patch means agree within 0.000199 m, with expected
extrema smoothing and no systematic mean drift. An initial GDAL axis-override
failure was rejected, corrected and covered synthetically, not published as terrain.

Evaluation-only Atlas delivery preserves production presentation. Landscape/planning,
rotation, an internal parent join and zoom controls show usable broad terrain.
Close overzoom stays coarse; similar faceting exists in the AWS control. Outer
perimeter falls to flat terrain and z0–7 are absent: this is no complete global
product. All 344 completed local responses succeeded; 25 navigation cancellations
were retained. Normal Weather/Traverse and independent analytical AWS remain untouched.
No production source, relief, exaggeration, satellite or lifecycle file changed.

Existing Atlas metadata describes source selection, derived identity, preserved
heights, information/delivery scale, scoped coverage and rights. No protected
interior, fallback or transition is invented. Public modified-product legal notices
and global missing-land/ocean/polar coverage remain prerequisites for broader use.

Verification: 29 synthetic Atlas Python tests and 160 active Node tests passed,
1 existing optional skip. Lint, TypeScript and application-only build passed;
existing chunk warning retained, external GFS publication/copying omitted.
Checksums, owned metadata and documentation references verified; products/captures
remain external and normal CI/startup requires none of them.

Next bounded step: test this coarse product with the identified Swiss regional
asset under explicit scale, contributor, height-reference and finite-support
rules. No hierarchy, reconciliation, resolver, imagery or next phase started here.

## 2026-10-05 — Bounded Copernicus/Swiss terrain hierarchy

Tested the [first controlled hierarchy](atlas/terrain-hierarchy-prototype.md)
from frozen common/coarse and authoritative regional products. An isolated
loopback tile service selects exact source tiles by per-level support and an
explicit z14 requested-DEM gate; common above13 is labelled delivery overzoom.
Native EGM2008/LN02 semantics are retained and every evaluated tile/cell has a
contributor label, source identities and deterministic hashes. No runtime module,
analytical elevation, Weather, Traverse, IGOR or exaggeration changed.

The result is negative for adoption: coarse context works and Swiss close/detail
structure remains useful and unchanged, but hard substitution and scale gating
retain spatial walls/bands and substantial parent/child discontinuity. Protected
interior sampled differences from selected Swiss are zero. Common13→Swiss14
differences reach about103 m; later Swiss refinements are much smaller. Twelve
fixed boundary strips at each tested level expose jumps up to167 m at14 and
about45 m at16/18. Rotation and lateral navigation do not remove the join.
No broad smoothing, datum correction, third fusion method or general resolver
was added. The existing metadata model represents the experiment without extension.

Validation:33 Python tests and164 active Node tests passed,1 existing optional
skip; lint, TypeScript and application-only build passed. All evaluated tiles/masks
match the independent rebuild; source identities, metadata and links verified.
Exact identities, numerical strata and controlled static/moving records are
linked from the report. Large products and
captures remain external; normal startup/CI requires none of them. Existing
application-only build warnings remain; unrelated publication ingestion omitted.

Next suggested bounded investigation: a regional-preserving parent diagnostic on
one protected-interior tile and neighboring support, keeping common reference
and best available representation distinct. Spatial seam/transition support and
global coverage remain separate unresolved decisions. No next phase started.


## 2026-10-05 — Regional-preserving terrain parent diagnostic

Completed the [bounded Swiss parent diagnostic](atlas/regional-parent-diagnostic.md)
from checkpoint6e2687e. Both frozen products and source hashes verified. A separate
unencoded z14 Swiss basis reproduces all25 original basis tiles; recursive sum/count
parents at13–10 retain full, partial and absent support. Only complete12/13 tiles
are eligible for the isolated web stream; fine Swiss14–18 remains exact.

On705 protected points, common13→Swiss14 RMS39.82 m becomes Swiss-parent13→Swiss14
RMS0.71 m. Fine modification is zero. Coarsening does not establish a natural
common handoff: protected Swiss/common RMS remains38.37 m at10, and whole regional
tiles cease below12. The first delivered source jump moves to11→12 (39.77 m RMS).
Same-level coarse edges reach48.40/61.77 m at12/13; west/south walls persist.
Pitched parent views recover the summit form and fine views converge; sampled
continuous zoom and rotation preserve supported internal refinement, not a global
continuity guarantee. Native LN02/EGM2008 remain distinct, with no correction/blend.

Independent rebuild matches all35 diagnostic files/support fields (14.69 MB).
Normal runtime and all source/product inputs remain unchanged. All1935 completed
local tile responses succeeded;24 failures were navigation cancellations. Captures
and products remain external and owned evaluation servers are stopped.

Validation:38 Atlas Python tests;167 active Node application/model tests with one
existing optional skip; lint, TypeScript, application-only build, metadata/hash
and reference checks passed. Existing deprecation/bundle warnings retained; no
unrelated test changed. New tools are CLI-only; no production metadata imports or
startup/CI dependency on external terrain. Regional pyramid is a supported concept,
not a final hierarchy contract. Suggested smallest next investigation: one
support-aware same-level boundary patch assessment preserving the interior.
No spatial reconciliation, additional source acquisition or next phase started.

## 2026-10-05 — Spatial terrain reconciliation research/design review

Completed a [bounded primary-literature and production-practice review](atlas/spatial-terrain-reconciliation-research.md)
from checkpoint `3e54ca8`. The problem was frozen before external review: related
Swiss parents address internal LOD, while independent DTM/DSM source disagreement,
height semantics, registration, epoch and spatial support remain distinct.
Reviewed co-registration, height transformations, priority mosaicking, weighted
fusion, seam selection, constrained transitions, national production examples
and nested rendering. Reference retrieval limits are recorded explicitly.

No new diagnostic, correction, blend, terrain hierarchy or external-data access
was needed. Existing stable support is uneven; a common frame does not explain
the much larger terrain discrepancy. The next proposed bounded experiment is a
same-level, support-constrained seam-corridor feasibility assessment with no height
modification. The 10 km asset is sufficient to attempt that assessment, not proven
sufficient for a defensible closed transition. Protected terrain, source identity
and partial support remain constraints. No generic contract is adopted.

Documentation/navigation only; production AWS, analytical AWS z15, IGOR,
exaggeration, Weather, Traverse, satellite and lifecycle remain unchanged.
Validation: all 33 focused terrain-policy/model/hierarchy Node tests passed;
132 local documentation links/anchors, UTF-8, retained numerical claims and diff
checks passed. Implementation/configuration diff is empty. No lint, TypeScript,
full application suite, build, browser run or external checksum pass was rerun
for these documentation-only changes.

## 2026-10-05 — Same-level seam-corridor feasibility

Completed the [bounded corridor diagnostic](atlas/seam-corridor-feasibility.md)
from `9827b17`. Frozen native-reference Swiss-derived parents and common delivery
at z12/13 are compared on identical cell centres with explicit complete support.
Thresholded planar cycles/dual escape certificates test enclosure of the protected
1.5 km circle; no rectangular seam, composite confidence score or height changes.

Result: no admissible enclosing cycle even at unlimited disagreement, robust to
100–500 m source-edge and glacier-buffer sensitivities. The southern excluded
glacier/change system reaches the regional edge. Glacier-only and snow-only
attribution checks independently fail. Removing change constraints permits
19.42/19.86 m minimax witness loops, but these are mostly glacier-excluded and
are not seam candidates. No transition experiment is justified. Next prerequisite:
glacier-aware support-extent feasibility using retained inventories, before any
additional terrain acquisition. No follow-on work performed.

All 106 canonical terrain source files, parent fields and used common tiles,
retained overlap masks and glacier archives verify. Independent rebuild matches
all seven external diagnostic files and the manifest; 37.44 MB per diagnostic.
Large fields/maps remain external. Lightweight plan/results/hash records and
synthetic tests are in Git; no runtime or CI dependency on the estate is added.

Validation: 46 Atlas Python tests, 171 active Node tests with one existing optional
skip, lint, TypeScript, application-only Vite build, metadata/reference and diff
checks pass. Existing deprecation/bundle warnings retained. The normal build was
also inadvertently run and copied existing Weather publication into ignored dist;
no forecast calculation/update occurred. Application-only build was then verified
separately. Production AWS, analytical AWS z15, IGOR, exaggeration, Weather,
Traverse, satellite and lifecycle remain unchanged.

## 2026-10-05 — Glacier-aware Riffelhorn support-extent assessment

The [inventory/support diagnostic](atlas/support-extent-assessment.md) from
`28f677c` reused verified official SGI1973/2016/2023 and acquired only a lightweight
official country polygon and two 2024 STAC metadata responses. No DEM downloaded
or read, no terrain/pyramid/height/reference operation and no production change.

The Gorner-connected exclusion network reaches beyond a 26×18 km observed window
west/east/north and reaches national inventory coverage south. Recent-only,
unbuffered SGI2023 also connects to the border. 25/50 m grids, 100/250/500 m glacier
buffers and 100/200/500 m edge guards retain failed enclosure. Territory is not
exact DEM support: a listed border tile demonstrates why inventory coverage and
source-cell validity must remain separate. Minimum/robust extents are deliberately
null; censored rectangle storage estimates are not acquisition recommendations.

Outcome: no additional elevation acquisition justified. Single next prerequisite:
a bounded transboundary glacier/change and valid-source-support audit at the
southern passage, before selecting any expanded terrain estate. No follow-on work.

Offline tooling/tests/plan/results/hash records retained; compressed fields/map
external. Four outputs reproduce exactly. 54 Python and 40 focused Node tests,
references/metadata/diff checks pass; Windows text hashing corrected to UTF-8.
No runtime/dependency/UI change; no broader app build needed for isolated research.

### 2026-10-05 — Separate Atlas detail bands from broad terrain disagreement

Bounded design/diagnostic from `4130fa20`: identical recursive Mercator-area means
and cell-centred prediction on immutable Swiss/common z13, z12 plus z11 sensitivity;
42 hash-verified fine Swiss profile tiles add smaller-scale context. No terrain
transition, acquisition, height/reference/registration operation or runtime change.

Whole-support raw/broad z12 RMS20.35/19.94m; stable candidates5.56/5.06m;
steep non-ice16.32/14.34m; change proxy27.62/27.18m. Decomposition is useful but
broad mismatch persists. Residual bands/cross terms are retained; no causal error
percentage or accuracy claim. Same-family LOD evidence remains0.71m refinement,
not translation/accuracy. Closed stable enclosure is preferred rather than universal;
stable support still constrains physically justified fitting and validation.

One terminal protected-priority two-band visual representation test is specified
in `docs/atlas/riffelhorn-final-reconciliation-experiment.json`, not implemented.
Existing source products/pyramids remain immutable; synthetic transition would
have explicit signed operator/support/change metadata and heterogeneous native
height semantics. Fixed1.5km protected/4km outer footprint, separate broad/detail
controls, numerical deformation guards plus renderer/navigation failure tests.
No width search or additional crop. After its outcome, freeze the hierarchy contract
with limitations in a separate task; no generic implementation begins here.

60 Python tests and27 focused Node model/policy/record tests pass. All28 diagnostic
files (~183MB per run, external) reproduce exactly; input/used-tile hashes rechecked;
independent norm/scalar statistics and closure validated. Documentation/reference
and diff checks complete before commit. No broad app/build/lint/TypeScript rerun
because no runtime, build, package or TypeScript changes. Production AWS visual and
independent analytical z15, strengthened IGOR, exaggeration1.45, Weather, Traverse,
satellite/projection/lifecycle remain unchanged.


## 2026-10-05 — Terminal protected-priority Riffelhorn transition

Implemented [one frozen two-band representation](atlas/protected-priority-two-band-transition.md)
from `53b9efb`: protected1500m, broad accommodation1500–4000m, independent detail
withdrawal3000–4000m, z12 broad controls, quintic weights and signed full operator.
No tuning, new acquisition, source mutation, correction or height transformation.
Swiss remainsLN02, commonEGM2008, mixed terrain explicitly synthetic/heterogeneous.
Runtime AWS/analyticalz15, IGOR/exaggeration1.45, Weather, Traverse and lifecycle
are unchanged. Prepared outputs/service/captures remain opt-in and external.

Outcome **PARTIAL / ARCHITECTURALLY USEFUL**. Fine protected terrain is exact;
endpoint introduced intercept≤1.62e−8m; induced-gradep950.02332 passes frozen guards.
Regional13→14 remains0.71m RMS. Collar changes exceed100m; independent checks find
new3.19m/1.35m local synthetic closed pits. Common9→derived10 remains41.84m RMS.
128boundary views/four bearings,40navigation segments and three satellite checks
complete. Severe southern foreground clipping is also reproduced by the matched
pure-common navigation control; it prevents all-view success and is not explained
as a source seam. Large local source accommodation does not imply accuracy.

4251terrain tiles/masks reproduce exactly (2297transition,1954controls);21numerical
outputs rebuild identically. All evaluated protected/outer endpoint cells and weights,
source/product hashes and support are verified. 7476local responses are200; sixbody
cancellations,221terrain request cancellations, no terrain HTTP/page exception.
Weather503console messages are explicit fixture isolation. 68Python tests and
180Node tests pass (one existing optional skip), lint/TypeScript/app-only build,
metadata/reference and diff checks pass. No normal CI external-data dependency.

The experiment is closed. Next task: **Atlas Terrain Hierarchy Contract**, retaining
synthetic morphology, low-scale handoff, height/support and renderer limitations.
No further Riffelhorn elevation-method experiment is recommended; no contract or
generic resolver implemented here. Historical Lab/design records remain unchanged.

## 2026-10-05 — Freeze Atlas Terrain Hierarchy Contract

Confirmed clean main at `019486f`, recorded origin divergence 0/0. Reviewed the
completed terrain programme and froze the canonical
[Terrain Hierarchy Contract](atlas/terrain-hierarchy-contract.md). It reuses the
source/product metadata foundation, adds provider-neutral representation families,
regional pyramid levels/parent relationships, per-level complete/partial/absent
support, explicit selection/fallback declarations and separate composition policy.
Prepared recipe identity and frozen content-manifest/inventory identity remain
distinct. Mutable external AWS identity and incomplete origin remain honest.

Optional height-reference details and temporal/change supplements extend existing
types compatibly. Scoped validation separates preparation, continuity, morphology,
accuracy, provenance and renderer evidence. Heterogeneous native heights require
explicit visual composition permission; weights/signed operators are not confidence.
Same-family LOD and source-family handoff are classified independently. The final
3.19/1.35m synthetic pits, 41.84m RMS coarse handoff, unresolved reconciliation,
height/change semantics and independently reproduced close-camera clipping remain
limitations. No experimental rule, provider, band width or tile encoding is made a
generic invariant.

Typed evidence examples exercise current AWS, Copernicus common, Swiss regional
pyramid and the synthetic transition using retained repository records. A synthetic
second-region fixture uses non-Swiss geometry and unknown unverified heights/rights/
epochs; no Wales terrain is acquired. The contract contains bounded implementation
and Wales/Tryfan proof plans, neither performed. No external terrain/product read,
regeneration, new experiment, resolver or production adoption occurred.

Validation: 12 focused contract tests, 36 combined model/policy tests, and the
application suite (192 passed, one existing optional external-data skip); ESLint,
TypeScript and application-only Vite build pass. Existing large-chunk warning remains.
Local/reference links and anchors, source/product record bindings, immutable reuse,
support/height/scale/family/provenance/fallback invariants and final diff are checked.
Normal tests require no external research assets. Production visual AWS, independent
analytical AWSz15, IGOR/exaggeration1.45, Weather, Traverse, satellite and map lifecycle
remain unchanged. No further Riffelhorn elevation-method experiment is recommended.

## 2026-10-05 — First Atlas terrain hierarchy runtime slice

Confirmed clean main at `53d75f2`, fetched origin and verified divergence0/0.
Implemented the frozen contract's bounded path: canonical metadata registration,
conservative point/footprint eligibility, declared scale ordering, same-source-family
regional parent reuse, explicit common/unavailable fallback and a small MapLibre
heightfield delivery adapter. Registration snapshots are validated/frozen; duplicate
identities, broken revisions/parents, cycles and conflicting scale catalogues fail.
Prepared immutable reuse can be checked against a previous registry.

Selection exposes exact product/family/representation/level identity, information
ceiling, derivation/overzoom, composition-policy reference and an ordered trace.
Direct selection, within-family LOD and source-family handoff remain distinct.
Prepared transitions require explicit enablement/request; no processing operator runs.
Partial/unknown regional support is declined, and unresolved asset geometries remain
unknown unless an owned assessed geometry is supplied. No projection/GIS engine or
viewport-aware resolver is added. Offline partial Swiss parent diagnostics remain
registered without falsely becoming raster-deliverable levels.

Extracted the existing canonical AWS record unchanged from research examples,
retaining compatibility re-export. Production registers only that external common
service. An explicit legacy operational policy preserves unknown assessed support
rather than inventing a validity polygon: selection reports legacy-unassessed and
retains unknown provenance/height/information semantics. Geometry z14 and relief z15
resolve through the generic selector/adapter to the exact prior configuration.
The existing MapLibre lifecycle, IGOR/exaggeration1.45, satellite and projection code
are untouched. Analytical AWS256/z15, Weather and Traverse remain independent.

The [runtime record](atlas/terrain-runtime-selection.md) documents ownership, API,
policy/error semantics, limitations and reproduction. Contract edits record partial
implementation status only; no frozen entity/schema redesign was required. No
external terrain was read/acquired/regenerated, no Riffelhorn method experiment or
reconciliation was performed. The bounded Wales/Tryfan second-source proof remains
next, not part of this task.

Validation:19 focused runtime tests and one added matched lifecycle test;56 combined
runtime/model/policy tests; application suite212 passed with one existing optional
external-data skip. Exact legacy/generic source configurations and all lifecycle
calls/snapshots match across zoom, satellite and style restoration. ESLint,
TypeScript, application-only Vite bundle, metadata/local references and final diff
checks pass. A concurrent build/test run had two transient test-file startup
failures; isolated reruns and the full four-process suite passed. Cause not
established; no assertion or application defect was reproduced. Existing
large-chunk warning remains. Normal CI/startup requires no
experimental terrain or local evaluation service.
## 2026-10-05 — Wales/Tryfan second-region terrain proof

Completed the [bounded second-region proof](atlas/tryfan-second-region-proof.md):
SUCCESS. Reused the hash-verified 9km² Welsh Government 2021 DTM subset under
its official OGL download terms; no regional elevation acquisition. Prepared295
complete z14–17 Terrarium tiles (23.89MB) with strict support propagation and
Welsh-derived parents. Independent rebuild matches every tile/support/working
hash. Unknown native vertical datum is explicit, not inferred from BNG or local
ODN labels; no datum/registration correction, reconciliation or blending.

The real family uses the frozen metadata, registry, selector and MapLibre
adapter unchanged. Normalized exact support polygons allow full-tile eligibility;
a preparation-only fragmentation defect was corrected in immutable v2 without
changing any height tile bytes. Fine/interior/parent/missing-child/common-fallback
and handoff decisions are recorded. Nine matched cameras and seven continuous
sequences per provider confirm regional detail/refinement; straight support-edge
relief and coarse handoff remain unreconciled. All474 hierarchy and221 control
endpoint requests completed200; four browser navigation cancellations in the
hierarchy run. No contract contradiction or Swiss-specific selection branch.

Seven new semantic tests, four synthetic preparation tests, independent transfer/
parent checks, metadata/source/support hashes, deterministic rebuild and renderer
capture passed. Full application suite219 passed, one existing optional-data skip;
lint, TypeScript, application-only bundle and reference/diff checks pass. Production
AWS geometry14/relief15, independent analytical AWSz15, IGOR, exaggeration1.45,
Weather/Traverse/satellite/projection/lifecycle remain unchanged. No normal CI or
startup dependency on external assets or the evaluation gateway. Regional elevation
foundation established; no additional elevation benchmark recommended. Next
programme boundary is imagery/appearance, not started here.

## 2026-10-05 — Atlas appearance baseline and architecture

Completed the bounded [appearance architecture investigation](atlas/appearance-baseline-and-architecture.md)
at baseline `8598c30`, clean main and fetched origin 0/0. Regional elevation foundation
is established and closed; no further benchmark, reconciliation or terrain-contract
change. Audited actual MapTiler satellite-v2 delivery, TileJSON metadata limits,
cache/failure/style restoration, branding and deliberate satellite IGOR suppression.
One existing-service TileJSON request verified z0–22/JPEG, omitted scheme (XYZ
default), 512 configured tiles and returned attribution; sanitized receipt retained.
Geometry, observations, processed appearance and display effects remain distinct.
Retained 012F/G evidence includes useful ordinary-ground appearance, steep projection
loss and inconclusive dark-face causality: final display suppressed real source
variation, so darkness is not proof of absent imagery.

Bounded primary/provider/standards review supports separate AppearanceHierarchy and
TerrainHierarchy sharing small provenance primitives. Proposed appearance records
retain source/product/representation identity, colour/bands, support/scale,
time/illumination basis, derived/synthetic provenance and exact geometry dependencies
where known. No universal hierarchy or executable schema/runtime is added. Official
SWISSIMAGE generation transition and source-access limits are recorded without
assuming new Riffelhorn coverage. Defined one next source-derived regional appearance
baseline with the retained four-tile 2023 selection and frozen Atlas cameras; no
correction/albedo/multiview experiment is started.

Validation: primary references checked, local document/code/camera references,
storage arithmetic, architecture consistency, final whitespace/diff and unchanged
production file scope verified. Documentation-only; application tests/build not
rerun and historical results not relabelled as new checks. No terrain/imagery assets accessed,
acquired, processed or regenerated, no external-data CI requirement. AWS visual
terrain via generic hierarchy, independent analytical AWS z15, MapTiler imagery,
IGOR, exaggeration 1.45, Weather/Traverse/satellite/projection/lifecycle unchanged.
Next task is the bounded SWISSIMAGE/Riffelhorn source-derived appearance baseline.


## 2026-10-05 — source-derived SWISSIMAGE/Riffelhorn appearance baseline

Completed the frozen four-tile 2023 / 4km² baseline after checkpoint6f2eb02.
Retained hashes match; no acquisition, expansion or correction. New opt-in scripts
prepare deterministic linear-light/alpha-aware XYZ512 PNG parents z12–18, register
fixed existing Swiss geometry through the terrain runtime, and capture eight matched
MapTiler/regional views with satellite IGOR suppressed. A connected-support harness
defect was corrected and rejected captures segregated before accepted evaluation.

The [report](atlas/swissimage-source-derived-baseline.md) and lightweight JSON retain
identity, rights/unknown acquisition semantics, fidelity, actual delivery levels,
stretch and source/display evidence. Useful regional rock/path information is most
clear in the opposed close view. Steep source/display median luminance0.00481/0.00485
and correlation0.90 do not reproduce Unreal black crushing. Projection support and
source darkness remain, with no justified Sun reconstruction or albedo claim.

Validation: independent full rebuild/hash equality, source/geometry hashes, parent
arithmetic and repeated diagnostics; eight Python/five Node focused tests; application
tests, lint, TypeScript, application-only build, metadata/references/final diff.
No application code or defaults changed: AWS visual through TerrainHierarchy,
independent analytical AWSz15, MapTiler/satellite/IGOR/exaggeration1.45 and
Weather/Traverse/lifecycle remain unchanged. No external-data CI requirement.
Elevation remains closed. Next: one bounded same-footprint acquisition/multiview-
support feasibility assessment; no correction, frame acquisition or reconstruction
starts automatically.


## 2026-10-06 — Riffelhorn acquisition/multiview-support feasibility

After 1de9e44, completed a metadata-only assessment on the unchanged 4 km² benchmark
and exact steep/summit/dark patches. [Record](atlas/riffelhorn-observation-support.md):
PARTIAL — COVERAGE WITHOUT SUFFICIENT GEOMETRY. Official 2023 strip polygons cover
the targets but do not expose calibrated per-line trajectories/rays or exact times.
The separately retained 2026 frame CSV publishes poses but has no local camera centre.
Normal/aspect distributions and orthographic stretch are reproduced with native
frozen geometry; no incidence or visibility claim is invented.

Added one offline metadata/normal/footprint diagnostic and eight synthetic tests;
raw lightweight metadata and map remain in meridian-data, small identities/results
in Git. Verified source/product/geometry/production hashes, catalogue checksum, CRS,
normal signs, repeated output hashes, JSON/local references and final diff. No shared
runtime change or external-data CI dependency; application checks are not rerun.
An upstream rasterio/NumPy shape-deprecation warning remains non-failing.

Production terrain/analytical elevation, MapTiler, IGOR, exaggeration 1.45,
Weather/Traverse/projection/lifecycle and the source-derived baseline are unchanged.
No aerial frames, correction/reconstruction, texture product or elevation research.
Next is one precisely scoped metadata-only swisstopo query; no contact sent or image
order placed, and no frame-acquisition set justified until that geometry is supplied.

## 2026-10-06 — Swiss 2026 multiview benchmark discovery

Completed [metadata-first selection](atlas/swiss-multiview-benchmark.md) from clean
e14148a. The2026 catalogue sufficed; no secondary-source survey or renewedRiffelhorn
search/contact. Frozen criteria precede candidate screening:60m patches, ≥50° median
slope, incidence≤60° on half difficult cells, ≥15° ray diversity.14 lightweight
profiles/three2m DTM tiles yield768 screened patches,80 steep and29 geometry-gate
patches; three candidates. Freeze LV95[2713830,1206710], frames
20260813_004_082750_001_41216 /009_41216, ten seconds apart. Better incidence43.26°
vs59.71°,17.30° separation,219/342 vs5/342 difficult cells. Nine sampled LOS rays
per view pass; actual visibility/texture remains unproved. Output-composite camera
calibration is distinct from physical heads; nativeLHN95/LN02 references are explicit.

Added offline discovery/geometry tooling,12 asset-free synthetic tests, lightweight
benchmark/hash records and navigation.12 orientation JSON/GORI/provider checksums,
three DTM checksums, CSV/schema/CRS/pose/footprint checks, byte-identical10-output
rebuilds and8 production hashes pass. One high-west candidate's edge projection
mismatch is recorded rather than tuned away. Source frames are individually
orderable by quotation, not currently public TIFF assets; no contact/order made.
No aerial pixels, thumbnails, reconstruction/correction, runtime or production
changes; no normal-CI external assets. Next is the bounded two-frame source-pixel
comparison after provisioning confirmation, not executed here. Elevation remains closed.

## 2026-10-06 — Atlas multiscale representation baseline

Completed [research and production characterization](atlas/multiscale-representation.md)
from clean e3edd0f with origin divergence 0/0. Frozen physical 128→0.125 m/CSS-pixel
mountain sequences and two existing rolling/low-relief controls produce 54 matched
captures on unchanged production or explicit research configurations. Actual tile
telemetry distinguishes geometry from relief refinement; pitched surface probes show
anisotropic sampling. The pinned MapLibre hillshade shader adds implicit source-level
derivative gain to the unchanged explicit IGOR curve. Retained SWISSIMAGE gains remain
useful but screenshot frequency is not a universal quality measure. Fixed read-only
terrain spectra express physical wavelengths without accuracy/morphology claims.

Bounded primary-source review supports discrete product eligibility/coherent parents,
local screen-space footprints and independent continuous portrayal. No universal three
modes, new geometry-generalization requirement or production strength tuning. Next is
one isolated relief-depiction experiment with fixed geometry, then a scoped display/
selection envelope; morphology preparation is conditional, not another elevation branch.
TerrainHierarchy/Appearance proposal remain intact; multiview waits on provisioning.

Ten asset-free synthetic tests, repeated byte-identical diagnostics, all 100 Swiss DEM
source hashes/four imagery sources, product/capture/camera checks and 113 production
source hashes pass. Lint, syntax, local-reference and diff checks pass. Upstream
rasterio/NumPy warnings are non-failing. No runtime edits require application tests/build;
normal CI has no external-data requirement. Large captures stay in meridian-data.
No production, IGOR, exaggeration 1.45, satellite, Weather/Traverse or analytical elevation
changes, new source data, correction, multiview work or reopened elevation research.

## 2026-10-06 — Scale-separated terrain relief depiction

Completed [one frozen derivative-only control](atlas/scale-separated-relief.md) from
clean 3d406ae, origin divergence 0/0. Gaussian scale-space uses sigma equal to one
nominal map-plane CSS pixel in metres before unchanged nonlinear IGOR; no height,
mesh, source, camera, colour or strength tuning. Reused four benchmarks/22 cameras
and two nine-step settled sequences: 80 captures, all 40 geometry/data/LOD pairs
verified. Prepared-derivative RMS falls, while useful narrow structure also softens;
low-relief controls show no obvious added prominence/noise but no material gain.
Result **NEGATIVE for this control**, not a claim against all multiscale depiction.
Discrete source-level contrast/refinement persists; interactive continuity/performance
is not established. Clipped input, limited halo and nominal scale under pitch remain
explicit. One stale navigation metadata field was removed without changing captures.

Added research-only shader/capture tooling, offline diagnostics, nine asset-free
synthetic tests, frozen plan/results and navigation; large captures remain external.
Regional product hashes, 100 Swiss source assets, all 113 production source hashes,
matched cameras, lint, syntax, local references and deterministic rebuilds pass.
No application/shared runtime changes require broader application tests/build.

Source-faithful geometry remains; no demonstrated deficiency activates conditional
morphology preparation. Next is the bounded information-aware display/selection
experiment, not executed here. Production AWS visual/analytical terrain, IGOR,
exaggeration 1.45, satellite/opacity/suppression, Weather/Traverse and lifecycle remain
unchanged. No appearance/multiview work, source acquisition or reopened elevation.
