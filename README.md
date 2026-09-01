# Meridian

Meridian is an interactive 3D weather map for exploring forecast conditions across terrain, place, and time.

![Meridian showing precipitation and animated wind over 3D terrain near Chamonix](docs/assets/meridian-terrain-hero.png)

## Technical highlights

- **Global numerical weather pipeline:** Python selects the latest usable complete NOAA GFS cycle, downloads indexed GRIB2 byte ranges, validates precipitation, cloud and wind semantics, and generates numeric Web Mercator weather tiles.
- **Numeric weather data:** precipitation, total cloud cover and 10 m wind vectors remain numerical in the browser instead of being baked into imagery, supporting client-side styling, point inspection, and forecast playback.
- **Custom WebGL wind rendering:** a projection-aware MapLibre particle layer samples geographic GFS U/V vectors to show forecast wind direction and relative speed across the globe.
- **Resilient interactive data lifecycle:** cancellation, bounded caching, last-valid-field reuse, rate-limit backoff, and persistent renderers keep the map responsive while data and camera state change.

## What it does

- Terrain and optional Satellite basemaps with 3D relief and globe-scale navigation.
- Global NOAA GFS precipitation, total cloud cover and 10 m wind with 24-hour playback.
- Independently combinable elevation, precipitation, cloud, temperature-contour, pressure-isobar, and animated wind overlays.
- A point inspector for elevation and weather values at the selected forecast time.
- Place search, map selection, current conditions, and responsive map-first controls.

## Architecture

Meridian is a client-side React and MapLibre application. It requires no runtime application server, database, or authentication system.

Precipitation, total cloud cover and 10 m wind have migrated to global, geographically fixed numeric tiled fields:

```text
NOAA GFS GRIB2
  → Python preprocessing and validation
  → numeric Web Mercator tiles
  → immutable manifest and latest pointer
  → MapLibre client rendering
```

![Global NOAA GFS precipitation rendered as numeric forecast tiles over the Satellite globe](docs/assets/meridian-global-gfs.png)

*Global NOAA GFS precipitation rendered as numeric forecast tiles over the Satellite globe.*

Open-Meteo remains the transitional regional source for temperature and pressure. Those fields interpolate a cached 9 × 9 sample grid for presentation; interpolation does not create additional meteorological information. See [Global weather architecture](docs/global-weather-architecture.md) for the detailed data model and migration design.

## Stack

- **Frontend:** React 19, TypeScript, Vite, MapLibre GL JS, WebGL
- **Preprocessing:** Python, NumPy, Pillow, ecCodes
- **Data and maps:** NOAA GFS, Open-Meteo, OpenFreeMap/OpenStreetMap, AWS Terrarium, MapTiler Satellite, Nominatim

## Run locally

Requirements:

- Node.js `^20.19.0` or `>=22.12.0`
- npm
- A modern WebGL-capable browser
- Internet access for live weather, map tiles, terrain, and search

```sh
npm ci
npm run dev
```

Open the URL printed by Vite, normally [http://localhost:5173](http://localhost:5173).

On Windows PowerShell systems where the execution policy blocks npm's PowerShell shim, use:

```powershell
npm.cmd ci
npm.cmd run dev
```

### Optional satellite imagery

Satellite requires a client-visible MapTiler key. Create `.env.local` from `.env.example`, set `VITE_MAPTILER_KEY`, and restart the development server. Terrain and all non-satellite functionality work without it.

Never commit `.env.local`. A public deployment should use a dedicated MapTiler key restricted to its allowed HTTP origins and an appropriate provider plan.

### Generate current GFS weather fields

Generated GFS runs and `public/weather/gfs/latest.json` are local and ignored by Git. A clean clone still starts normally, but precipitation, cloud cover and wind are reported as unavailable until data are generated; Meridian does not silently substitute regional map fields.

With Python 3.12 or newer:

```sh
python -m pip install -r scripts/weather/requirements.txt
python scripts/weather/build_gfs_weather.py
python -m unittest discover -s scripts/weather -p "test_*.py"
```

The generator finds the latest usable complete GFS cycle, falls back when the newest run is incomplete, and downloads only indexed APCP, instantaneous entire-atmosphere TCDC, and instantaneous earth-relative 10 m UGRD/VGRD ranges. It validates each field's semantics and publishes entries independently through an atomic `latest.json` catalogue. It requires no API key. On Windows, `py` may be used instead of `python`.

## Commands and verification

| Command | Purpose |
| --- | --- |
| `npm ci` | Reproduce dependencies from `package-lock.json` |
| `npm run dev` | Start the development server |
| `npm run lint` | Run ESLint |
| `npm run build` | Type-check and build production assets |
| `npm run preview` | Serve the production build locally |
| `python -m unittest discover -s scripts/weather -p "test_*.py"` | Run preprocessing tests |

## Data sources and attribution

- [OpenFreeMap](https://openfreemap.org/) provides the vector basemap style and tiles; its source metadata supplies map attribution.
- [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) provide geographic and search data used through OpenFreeMap and [Nominatim](https://nominatim.org/).
- [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) provide the Terrarium DEM; Meridian links the [full terrain dataset credits](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) at runtime.
- [Open-Meteo](https://open-meteo.com/) provides live point forecasts and the transitional regional temperature and pressure field under CC BY 4.0; runtime credit identifies Meridian's interpolated presentation.
- [NOAA GFS](https://registry.opendata.aws/noaa-gfs-bdp-pds/) provides the source numerical forecast data. Generated precipitation, cloud and wind tiles are derived products and retain linked provenance.
- [MapTiler Satellite](https://www.maptiler.com/satellite/) is the optional imagery provider; provider-supplied attribution and branding are preserved.

Provider availability, acceptable-use policies, rate limits, attribution requirements, and licensing remain applicable.

## Prototype limitations

- Meridian is an engineering prototype and should not be used for safety-critical navigation or forecasting decisions.
- Open-Meteo temperature and pressure fields still interpolate a regional 9 × 9 sample grid.
- GFS precipitation, total cloud cover and 10 m wind are 0.25° model fields; close zooms overzoom the same data rather than creating finer meteorological detail.
- The generated GFS horizon is +24 hours and updates are manually invoked rather than scheduled or published as a production service.
- Terrain and weather detail remain constrained by their source datasets.

## Further reading

- [Product direction](docs/product-direction.md) — the problem Meridian is exploring and the decisions still open.
- [Global weather architecture](docs/global-weather-architecture.md) — the provider-neutral migration design and implemented global precipitation pipeline.
- [Development log](docs/development-log.md) — concise engineering milestones and durable decisions.

## Licence

Source is available for portfolio review. No open-source licence is currently granted. Third-party software, services, and datasets retain their own licences and terms.
