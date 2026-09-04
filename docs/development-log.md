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
