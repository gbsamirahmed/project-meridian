# Global gridded weather architecture

## Status

The provider-neutral architecture now serves locally generated global precipitation, total cloud cover, 10 m wind, and 2 m temperature, not a production feed. Meridian resolves the latest verified usable NOAA GFS 0.25° run, generates 24 hourly steps, publishes independently validated immutable numeric scalar/vector fields behind an atomic `latest.json` catalogue, and loads them through manifest clients, a bounded shared tile cache, geographic samplers, and persistent MapLibre renderers. Open-Meteo remains the active source for point weather plus regional map pressure. Scheduled ingestion, hosting, retention, monitoring, and model selection remain unimplemented and require product and cost decisions.

Generated timestamped run directories and `public/weather/gfs/latest.json` are local build products and are excluded from Git. A clean checkout remains runnable and reports missing GFS fields as unavailable until the documented generator publishes validated local datasets; it does not silently change field ownership.

## Why the current field should be replaced

The local Open-Meteo field was useful for proving terrain-draped weather surfaces, contours, wind animation, caching, and inspection. It is not an Earth-wide weather source. It samples a moving rectangle, interpolates only 81 points, and must be refreshed as the camera leaves that rectangle. Enlarging it would increase request cost without fixing geographic continuity, native model resolution, or stable zoom behaviour.

The next architecture should treat every weather variable as a time-indexed field anchored to a model grid. The browser should request only the tiles visible for a chosen model run and valid time.

## Candidate global models

| | NOAA GFS | ECMWF IFS Open Data |
| --- | --- | --- |
| Public product | Global 0.25° latitude/longitude GRIB2, with a 13 km operational model core | Global 0.25° latitude/longitude GRIB2 open product |
| Runs | 00, 06, 12 and 18 UTC | 00, 06, 12 and 18 UTC |
| Horizon and steps | Files through forecast hour 384; the current 0.25° feed is hourly through hour 120, then less frequent | 00/12 runs: 3-hour steps through 144, then 6-hour steps through 360; 06/18 runs: 3-hour steps through 144 |
| Useful fields | APCP/PRATE, total cloud, 2 m temperature, 10 m U/V wind, mean sea-level pressure, and pressure levels | `tp`/`tprate`, `tcc`, `2t`, `10u`/`10v`, `msl`, and pressure levels |
| Access | NOAA NOMADS and a public AWS bucket with no AWS account required | ECMWF portal and replicas on AWS, Azure and Google Cloud |
| Terms | NOAA data is open for public use; attribution is requested and endorsement must not be implied | CC BY 4.0 with required attribution and ECMWF terms |
| Operational consideration | Straightforward public-cloud feed and hourly short-range output fit Meridian's current timeline well | Strong field catalogue and a clear open licence, but the public deterministic cadence is three-hourly in the near range |

Sources: [NCEP GFS product inventory](https://www.nco.ncep.noaa.gov/pmb/products/gfs/), [NOAA GFS Open Data registry](https://registry.opendata.aws/noaa-gfs-bdp-pds/), [NOAA GFS archive description](https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast), and [ECMWF Open Data catalogue](https://www.ecmwf.int/en/forecasts/datasets/open-data).

GFS is the recommended first proof-of-concept source. Its public AWS access and hourly short-range files reduce the number of new questions in a precipitation-first prototype. This is not a permanent provider choice: the generated manifest and client interfaces must be model-neutral, and ECMWF should be compared for forecast quality before production selection.

## Precipitation semantics

The first migrated variable should be total precipitation accumulated over a stated interval, not an ambiguously labelled colour field.

For the GFS proof of concept, extract the surface `APCP` total-precipitation message at the hourly forecast steps available through hour 120. Current inventories reset their short accumulation bucket every six hours: +1/+7/+13/+19 provide direct one-hour messages, while intervening hours are derived by subtracting consecutive accumulations that have the same bucket start. Preprocessing discovers and validates those intervals instead of assuming every message is one-hour or run-to-date. GRIB uses kg/m² of water; 1 kg/m² is 1 mm. The manifest and validation output preserve interval start, interval end, valid time, source unit, and derivation. The Meridian legend can therefore accurately say “precipitation in previous hour (mm)”.

Do not silently divide a three-hour accumulation by three and present it as an hourly forecast. Beyond the hourly portion of a run, either expose the real three-hour interval with a “previous 3 hours” label or stop the first prototype timeline. An instantaneous or averaged precipitation-rate field answers a different question and should be labelled as a rate, not an accumulation.

ECMWF offers both total precipitation (`tp`) and total precipitation rate (`tprate`). If it is adopted later, preprocessing must decode each GRIB message's statistical interval rather than infer semantics from the short name alone.

## Cloud semantics

The first cloud migration uses GFS `TCDC` at the exact `entire atmosphere` level. Each exported value is the instantaneous total cloud fraction at its forecast valid time, expressed as 0–100 percent. The inventory also contains averaged TCDC and TCDC for low, middle, high, convective, boundary-layer, and pressure levels; preprocessing requires the exact instantaneous `N hour fcst` record and rejects ambiguous or statistically processed alternatives.

Cloud tiles use one lossless uint8 red channel: codes 0–100 are percentage points and 255 is no-data. Zero remains valid clear sky. This deliberately does not infer cloud altitude, physical geometry, or fine-scale texture. Low/mid/high fields and procedural presentation remain separate future decisions.

## Wind semantics

The first vector migration uses the exact instantaneous GFS `UGRD` and `VGRD` records at `10 m above ground`. ecCodes metadata must identify a regular 0.25° latitude/longitude grid, metre-per-second units, the requested valid time, and earth-relative components (`uvRelativeToGrid = 0`). The two messages are validated as a pair with identical run, valid time, grid, level, scanning, units, and missing-value masks.

U is positive eastward and V is positive northward. Speed and meteorological “from” direction are derived in the browser from the interpolated components; speed or direction is never interpolated independently. Wind is instantaneous at each valid time and has no accumulation metadata.

## Temperature semantics

Global map temperature uses the exact instantaneous GFS `TMP` record at `2 m above ground` for each forecast valid time. Preprocessing rejects surface/skin, pressure-level, other-height, maximum/minimum, averaged, and ambiguous records. ecCodes supplies Kelvin values, which are converted once to Celsius without lapse-rate correction, terrain downscaling, or other local modelling.

Temperature tiles use unsigned 16-bit red/green encoding at 0.1 °C precision with an offset of −150 °C and code 65535 reserved for no-data. The declared valid range is −150…100 °C. Isotherms are generated from a padded, logically continuous viewport sampling domain after all required numeric tiles are prepared, so storage tile boundaries do not become contour boundaries.

## Web tile representation

The implemented proof uses versioned numeric tiles:

- Precipitation is quantised to unsigned 16-bit hundredths of a millimetre. Lossless PNG stores the high byte in red and low byte in green; scale, offset and the `65535` no-data code live in its manifest.
- Cloud cover uses unsigned 8-bit percentage points in red, with 255 reserved for no-data.
- Wind packs two biased 10-bit component codes into one RGB PNG: `U = (R << 2) | (G >> 6)` and `V = ((G & 63) << 4) | (B >> 4)`. Code zero is paired no-data; physical values are `(code - 512) × 0.2 m/s`.
- Temperature uses unsigned 16-bit red/green codes with `value = code × 0.1 − 150 °C`; 65535 is no-data.
- PNG compression, immutable run/time URLs and normal HTTP caching keep transfer costs bounded for the proof.
- Each tile includes or inherits model, run, valid time, variable, units, bounds, native resolution and attribution.

This preserves numeric values for inspection, contours, recolouring and later GPU use. It also keeps the palette in Meridian rather than baking it permanently into an image.

Other options have narrower roles:

- Pre-rendered PNG/WebP raster tiles are simple and cache well, but lose values and force every palette change to regenerate data. Lossy WebP must not encode scientific values.
- Lossless packed PNG was selected for the proof because sparse precipitation compressed to 36.53 MiB for 24 global timesteps, while preserving numeric inspection and avoiding a browser runtime dependency. A binary/GPU-native payload remains worth benchmarking before production.
- A Cloud Optimized GeoTIFF is useful as an intermediate archive and for range-based analytical clients, but browser reprojection and timestep switching are more complex than viewport tiles.
- Direct GRIB2 decoding in the browser would transfer large operational files, duplicate specialist decoding work on every device, and perform poorly on mobile. It should not be Meridian's delivery path.

The current custom MapLibre tile protocol provides a useful migration seam: it can fetch and decode a numeric tile, apply the existing colour ramp, and return an image tile for terrain draping. A later custom WebGL scalar renderer can consume the same decoded tile cache without changing the provider manifest.

## Stable zoom and level of detail

All display levels must derive from one canonical model field and grid. Generate a small deterministic tile pyramid for globe and regional display, with shared edge samples or gutters so adjacent tiles agree. Parent levels should be downsampled from the same canonical field; children must never be generated from a different forecast query.

For a 0.25° field, the useful native ceiling is around Web Mercator z3. Higher map zooms should overzoom that same highest-detail weather level with linear interpolation. This makes the same rain system remain in the same place and shape while the basemap gains detail. It also makes the data limitation honest: a local zoom does not create mountain-scale meteorology.

MapLibre can retain loaded parent tiles while a child level arrives. The renderer should crossfade timesteps, not geographic versions of the same field. Tile URLs should be immutable by model run and valid time so normal HTTP and MapLibre caches can safely reuse them.

Web Mercator does not cover the poles. The first prototype can explicitly support the normal ±85.051° extent used by the map; true polar rendering is a later projection decision rather than something to hide.

## Provider-neutral client boundary

The client depends on metadata and field capabilities rather than GFS or ECMWF filenames. Scalar manifest schema v2 describes field identity, source parameter and level, units, valid range, time semantics, native resolution, encoding, timesteps, coverage, and provenance. Schema-v1 precipitation manifests are normalised at the loading boundary for compatibility.

```ts
interface ScalarFieldManifest {
  schemaVersion: 2;
  id: string;
  model: string;
  product: string;
  runTime: string;
  field: ScalarFieldDescriptor;
  timesteps: ScalarFieldTimestep[];
  tiles: NumericTileEncoding;
}

interface GlobalWeatherFieldSource {
  manifest: ScalarFieldManifest | VectorFieldManifest;
  manifestUrl: string;
  baseUrl: string;
}
```

A shared tile store should fetch, decode, cache and sample tiles. Scalar and vector field adapters should expose geographic sampling without knowing which model supplied the values.

- Precipitation and cloud surfaces colour scalar tiles.
- Temperature contours build geometry from a padded continuous geographic sampling domain backed by prepared numeric tiles; pressure still uses the regional sampled field.
- Wind particles sample U/V vector tiles.
- The inspector samples the decoded tile covering the pointer and reports source, run and valid time.

Renderers should continue to own presentation only. Model download details, GRIB parameter names and unit conversion belong in preprocessing and manifest generation.

## Transitional ownership

Migration remains variable by variable. Precipitation, cloud, 10 m wind, and 2 m temperature are now global GFS owners; pressure remains a regional Open-Meteo map field.

The browser loads a schema-v2 field catalogue whose precipitation, cloud, wind, and temperature entries are resolved and validated independently. One field may advance while another retains an older valid run with its real metadata. A failed field is unavailable (or retains its prior published entry); it never silently falls back to the regional map grid. The inspector composes GFS precipitation/cloud/wind/temperature with Open-Meteo pressure and reports concise provenance.

The timeline is manifest-driven. With one enabled global field it uses that field's valid times; with multiple global fields it uses their exact valid-time intersection. Regional Open-Meteo pressure chooses its nearest available hour. Cloud, wind, and temperature are not temporally interpolated. During a wind timestep change, separate old and new particle populations sample their exact fields and crossfade visually; U/V values are not blended between forecast times. Temperature retains the last complete contour geometry until padded coverage for the requested exact timestep is ready.

## Lightweight preprocessing and publishing

The appropriate infrastructure is a scheduled data job, not a user-facing application server:

1. Detect a complete new model run.
2. Download only required GRIB messages, using index/byte-range access where available.
3. Decode with a mature server-side tool such as ecCodes or wgrib2.
4. Validate bounds, units, missing values, intervals and valid times.
5. Regrid once to the canonical delivery grid and create numeric tiles.
6. Upload immutable run assets to object storage/CDN.
7. Atomically publish a small `latest.json` manifest after validation.
8. Retire old runs with a bounded storage policy.

This can run as a scheduled container, CI job or cloud worker with enough memory and execution time. Object storage serves all tiles and metadata. A dynamic metadata API is optional; static JSON is sufficient initially. This keeps the React application client-only while acknowledging that operational GRIB preprocessing cannot reasonably happen in each browser.

## Implemented local update proof

The current workflow generates surface `APCP`, instantaneous entire-atmosphere `TCDC`, instantaneous earth-relative 10 m `UGRD`/`VGRD`, and instantaneous 2 m `TMP` for forecast hours +1 through +24. The updater fetches each forecast inventory once, tests recent cycles newest-first, and accepts a candidate only if every required precipitation interval and exact cloud/vector/temperature record is usable. GRIB packing noise below 0.1 mm may be clamped only for precipitation after larger negative differences are rejected.

- `scripts/weather/build_gfs_weather.py` is the canonical local command; the shared builder resolves the latest usable run, reuses inventory probing, selects indexed byte ranges, validates variable-specific ecCodes metadata, creates z0–z3 tiles, writes validation statistics, and publishes field entries independently.
- `public/weather/gfs/<run>/manifest.json` remains the precipitation manifest; `cloud-cover/manifest.json`, `wind-10m/manifest.json`, and `temperature-2m/manifest.json` describe the other immutable fields. Existing schema-v1 precipitation runs remain loadable.
- `latest.json` schema v2 is a mutable field catalogue. Updating one entry preserves the other entry and its actual run time.
- `src/types/globalWeather.ts` contains provider-neutral run, scalar/vector timestep, encoding, and source contracts.
- `src/services/globalWeatherService.ts` and `numericTileCache.ts` load metadata, bound decoded tile memory, and sample values geographically.
- `src/services/globalScalarSurface.ts` owns the reusable instance-based double-buffer lifecycle; thin precipitation and cloud adapters own their palettes and opacity. Wind reuses the numeric cache through a global vector sampler and the existing custom WebGL particle layer. Temperature prepares shared-cache scalar coverage asynchronously and atomically replaces viewport-aware GeoJSON isolines only after the continuous sampling domain is complete.

The canonical 1440×721 GFS grid is resampled deterministically to Web Mercator z0–z3. z3 is the useful display ceiling; closer views overzoom it with linear interpolation. Longitude sampling is periodic across ±180°, and coverage is explicitly clipped to ±85.051°. A 24-step run contains 2,040 tiles per scalar field. Run paths remain immutable, while `latest.json` is the only mutable publication object. No production host is required.

## Atmospheric route fields

Environmental Enrichment v1 adds five independently published schema-v2 scalar
entries without changing the existing scalar PNG decoder or map layers:

| Field ID | Exact inventory record | Logical units | Scale / offset |
| --- | --- | --- | --- |
| `gust_surface` | `GUST:surface` | m/s | 0.1 / 0 |
| `visibility_surface` | `VIS:surface` | m | 10 / 0 |
| `freezing_level` | `HGT:0C isotherm` | gpm | 5 / −1000 |
| `highest_freezing_level` | `HGT:highest tropospheric freezing level` | gpm | 5 / −1000 |
| `cloud_ceiling` | `HGT:cloud ceiling` | gpm | 5 / −1000 |

These are instantaneous PDT-0 records, not hourly maxima, averages or totals.
Every hour is checked against exact parameter/level, units, run/valid time,
1440×721 regular 0.25° grid, and scanning metadata. `gfs_atmospheric.py` supplies
field contracts and a shared writer behind the canonical weather builder; it
reuses inventory retrieval, byte ranges, decoding, grid sampling and catalogue
publication. `python scripts/weather/gfs_atmospheric.py` provides a bounded,
non-publishing distribution inspection; its disposable source cache is ignored.
The five immutable directories use hyphenated field IDs under the selected run.
An atmospheric-field failure retains that field's prior catalogue entry while
the other fields continue independently. Existing schema-v1 precipitation and
schema-v2 runs without these entries remain supported.

All five use RG uint16 PNG, reserved no-data 65535, blue 0 and opaque alpha.
Manifest `scale`, `offset`, physical `validRange`, `verticalReference`,
`noDataMeaning` and `interpretation` describe the contract. Zero is valid.
The validated source ranges are 0–200 m/s, 0–100000 m visibility, −1000–30000 gpm
freezing heights, and −1000–20001 gpm ceiling before sentinel removal. These
are generous validation bounds, not claims about expected weather. Visibility's
observed ~24.1 km cap permits simple 10 m linear quantisation (at most 5 m storage
error), avoiding a nonlinear decoder for no demonstrated practical benefit.

[NOAA UPP's ceiling documentation](https://noaa-emc.github.io/UPP/upp_v11.0.0/AVIATION_8f.html)
identifies a 20000 m no-ceiling sentinel and a surface-relative ceiling. Values
within 1 gpm of that sentinel are mapped to no-data **before** spatial
interpolation; the tolerance covers observed GRIB packing displacement. Bitmap
missing counts and no-ceiling counts are retained separately in validation.
Interpolation touching unavailable ceiling cells stays unavailable rather than
mixing 20 km into a real ceiling. The freezing heights retain their sea-level
reference and remain separate; a ceiling cannot simply be compared to DEM
elevation as though both had the same datum.

Route preparation now uses three scalar workers plus the existing vector path,
with grouped per-timestep coordinates and immediate synchronous sampling from
the shared 64 MiB cache. Each raw value retains field/units, model run, native
resolution, requested arrival, selected valid time and offset. New fields use
the existing bounded nearest-step/earlier-tie rule; precipitation retains its
real accumulation intervals. Presentation-mode changes do not refetch weather.
The inspector exposes raw atmospheric values and secondary provenance; peak
gust/minimum visibility summaries state their scheduled-sample coverage.
Height-versus-elevation profile drawing is deferred; aligned raw height samples
and vertical references are available in `RouteConditions` for later evaluation.

## Cost and performance expectations

A 0.25° global grid contains roughly 1.04 million source cells. One unsigned 16-bit scalar field is about 2 MiB per timestep before compression and tiling. A Web Mercator pyramid adds resampling and tile overhead, so actual storage must be benchmarked with real precipitation: sparse rain fields should compress well, but hundreds of timesteps and multiple retained runs still grow into hundreds of megabytes or more per variable.

The browser should normally fetch only a handful of visible tiles for one valid time. Globe view may require more low-level parent tiles; regional and local views should reuse or overzoom a small number of native-level tiles. Immutable caching makes repeated locations and forecast playback practical. Adding further fields such as pressure multiplies storage, processing and bandwidth, so retention, timestep horizon and ensemble support are product and cost decisions, not implementation defaults.

## Decisions required before production implementation

- Decide whether GFS, ECMWF, or a multi-model approach should be the first maintained product source.
- Decide the operational forecast horizon and whether later multi-hour accumulations appear as honest interval totals.
- Benchmark packed PNG against a binary/GPU-native encoding using production-scale runs and mobile devices.
- Define run-retention and maximum storage/CDN budget.
- Decide whether deterministic output is sufficient or uncertainty/ensembles must influence the first product.
- Decide how model provenance and native resolution appear in the interface.
- Define whether polar coverage is required in the first global release.
- Establish objective comparison criteria before choosing a long-term model, rather than treating the proof provider as permanent.
