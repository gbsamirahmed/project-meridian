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

### Architectural decisions

Strava activity labels are catalogue context rather than movement truth. Recorded stops, explicit pauses, gaps, and movement remain separate evidence, and device elevation remains diagnostic rather than canonical terrain. Reusable code lives in Meridian, while source recordings and generated research outputs stay outside Git.

### Known limitations

The descriptive movement signatures are not calibrated profiles or model classes. Thresholds are intentionally conservative, FIT field conflicts remain visible as diagnostics, and terrain/gradient enrichment plus held-out journey validation are deferred.

### Verification

The importer was exercised against the private archive after a representative-sample pass. Synthetic tests cover formats, gzip input, missing fields, malformed XML, catalogue associations, timestamp ordering, pauses, stationary and slow movement, GPS anomalies, and complementary FIT records sharing timestamps. Existing production journey constants were not changed.

### Next direction

Enrich a bounded representative subset with the same Terrarium and terrain-metric conventions as planned routes, then compare a small interpretable personal gradient-to-speed relationship against Meridian's unchanged generic model on held-out complete activities.
