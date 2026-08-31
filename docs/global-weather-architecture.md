# Global gridded weather architecture

## Status

The provider-neutral architecture now has a locally updated precipitation proof of concept, not a production feed. Meridian resolves the latest verified usable NOAA GFS 0.25° run, generates 24 hourly precipitation steps, publishes immutable static numeric tiles behind an atomic `latest.json` pointer, and loads them through a manifest client, bounded browser tile cache, geographic sampler, and persistent MapLibre renderer. Open-Meteo remains the active source for point weather and every unmigrated map variable. Scheduled ingestion, hosting, retention, monitoring, and model selection remain unimplemented and require product and cost decisions.

Generated timestamped run directories and `public/weather/gfs/latest.json` are local build products and are excluded from Git. A clean checkout remains runnable and reports GFS precipitation as unavailable until the documented generator publishes a validated local dataset; it does not silently change precipitation provider.

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

## Web tile representation

The implemented proof uses versioned numeric tiles:

- Scalar values are quantised to unsigned 16-bit hundredths of a millimetre. Lossless PNG stores the high byte in red and low byte in green; scale, offset and the `65535` no-data code live in the run manifest.
- Vector tiles contain two signed or offset-encoded 16-bit components, such as U and V wind.
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

The client should depend on metadata and field capabilities rather than GFS or ECMWF filenames:

```ts
interface WeatherRunManifest {
  datasetId: string;
  model: string;
  runTime: string;
  validTimes: string[];
  attribution: string;
  variables: WeatherVariableDescriptor[];
}

interface WeatherFieldSource {
  kind: "scalar" | "vector";
  variable: string;
  units: string;
  nativeResolution: { longitudeDegrees: number; latitudeDegrees: number };
  nativeMaxZoom: number;
  tileTemplate: string;
  encoding: NumericTileEncoding;
}
```

A shared tile store should fetch, decode, cache and sample tiles. Scalar and vector field adapters should expose geographic sampling without knowing which model supplied the values.

- Precipitation and cloud surfaces colour scalar tiles.
- Temperature and pressure contours build geometry from a bounded mosaic of visible scalar tiles, including a one-cell neighbour margin.
- Wind particles sample U/V vector tiles.
- The inspector samples the decoded tile covering the pointer and reports source, run and valid time.

Renderers should continue to own presentation only. Model download details, GRIB parameter names and unit conversion belong in preprocessing and manifest generation.

## Transitional ownership

Migration should be variable by variable, beginning with precipitation, then cloud, wind, temperature and pressure.

Use one explicit source registry for each variable. Once global precipitation is enabled, the map and inspector obtain precipitation from that source; they must not silently mix it with Open-Meteo precipitation. Open-Meteo can continue to supply the selected-location forecast and all not-yet-migrated map variables. The inspector can compose variables from both systems, but should show provenance and use one source per variable and valid time.

The timeline should be manifest-driven. During transition, choose valid times shared by the enabled global fields and the local forecast where possible; otherwise show a field as unavailable rather than temporally interpolating between different providers without an explicit scientific decision.

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

The current generated proof uses GFS run `2026083012`, surface `APCP`, and forecast hours +1 through +24. The updater finds the newest archive date, tests recent cycles newest-first, and accepts a candidate only if every required inventory supports a valid one-hour derivation. On 2026-08-30 it rejected the incomplete 18Z cycle and selected 12Z. GRIB packing noise below 0.1 mm may be clamped only after larger negative differences are rejected.

- `scripts/weather/build_gfs_precipitation_poc.py` resolves the latest usable run, selects indexed byte ranges, validates ecCodes metadata, derives intervals, creates z0–z3 tiles, writes validation statistics, and atomically publishes `latest.json` after success.
- `public/weather/gfs/<run>/manifest.json` and immutable timestep tile folders are served by Vite.
- `src/types/globalWeather.ts` contains provider-neutral run, timestep and scalar-source contracts.
- `src/services/globalWeatherService.ts` and `numericTileCache.ts` load metadata, bound decoded tile memory, and sample values geographically.
- `src/services/globalPrecipitationLayer.ts` converts decoded scalar tiles to Meridian's precipitation palette and double-buffers timestep changes in MapLibre.

The canonical 1440×721 GFS grid is resampled deterministically to Web Mercator z0–z3. z3 is the useful display ceiling; closer views overzoom it with linear interpolation. Longitude sampling is periodic across ±180°, and coverage is explicitly clipped to ±85.051°. The current proof generated 2,040 tiles and 36.53 MiB of tile data. Run paths remain immutable, while `latest.json` is the only mutable publication pointer. No production host is required.

## Cost and performance expectations

A 0.25° global grid contains roughly 1.04 million source cells. One unsigned 16-bit scalar field is about 2 MiB per timestep before compression and tiling. A Web Mercator pyramid adds resampling and tile overhead, so actual storage must be benchmarked with real precipitation: sparse rain fields should compress well, but hundreds of timesteps and multiple retained runs still grow into hundreds of megabytes or more per variable.

The browser should normally fetch only a handful of visible tiles for one valid time. Globe view may require more low-level parent tiles; regional and local views should reuse or overzoom a small number of native-level tiles. Immutable caching makes repeated locations and forecast playback practical. Adding cloud, wind and pressure multiplies storage, processing and bandwidth, so retention, timestep horizon and ensemble support are product and cost decisions, not implementation defaults.

## Decisions required before production implementation

- Decide whether GFS, ECMWF, or a multi-model approach should be the first maintained product source.
- Decide the operational forecast horizon and whether later multi-hour accumulations appear as honest interval totals.
- Benchmark packed PNG against a binary/GPU-native encoding using production-scale runs and mobile devices.
- Define run-retention and maximum storage/CDN budget.
- Decide whether deterministic output is sufficient or uncertainty/ensembles must influence the first product.
- Decide how model provenance and native resolution appear in the interface.
- Define whether polar coverage is required in the first global release.
- Establish objective comparison criteria before choosing a long-term model, rather than treating the proof provider as permanent.
