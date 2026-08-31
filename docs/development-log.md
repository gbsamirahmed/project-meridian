# Meridian development log

This is Meridian's concise chronological engineering history. Substantial tasks should append a dated entry; implementation details remain authoritative in source code, and exploratory ideas remain distinct from settled decisions.

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
