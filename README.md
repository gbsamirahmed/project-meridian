# Meridian

Meridian is an exploratory, client-only weather map that aims to make conditions spatially understandable. It combines weather, geography, terrain, and forecast time in an interactive MapLibre view, with a particular interest in outdoor and mountain use.

The application is a working prototype rather than a safety system or finished product. [Product direction](docs/product-direction.md) records what Meridian is trying to learn and which decisions remain open. [Agent instructions](AGENTS.md) describe how Codex should work in this repository.

## Current features

- Interactive globe with atmospheric horizon, standard map gestures, and 3D terrain
- Location selection by map click or place search
- Current conditions and a seven-day temperature forecast
- A 25-hour forecast slider with playback
- DEM-native elevation colour relief and automatic, zoom-responsive hillshade
- Distinct primary views for terrain, elevation, precipitation, and temporary two-dimensional cloud cover
- Independently combinable temperature contours, pressure isobars, and adaptive wind-flow arrows
- A universal hover/tap inspector for temperature, precipitation, cloud, pressure, wind, elevation, and forecast time
- A nonlinear precipitation field with sparse intensity symbols; values are millimetres accumulated over the preceding hour
- Deliberately tuned visual strength for each terrain and weather view

## Architecture

Meridian uses React, TypeScript, Vite, and MapLibre GL JS. It has no backend, database, authentication, or server-side processing.

React owns application state and the control panel. `MapView` keeps MapLibre's imperative lifecycle separate, managing the globe, terrain, sources, layers, markers, and pointer events.

Terrain geometry, elevation colour relief, and automatic hillshade are derived from the same Terrarium DEM tile dataset. MapLibre uses separate internal source instances for terrain and analysis, as recommended when a DEM has both roles. Forecast rendering is separate: the browser requests one 9 by 9 Open-Meteo sample grid around a generously padded camera footprint, caches recent regions, cancels stale requests, and crossfades replacement surfaces. Cloud and precipitation use the shared terrain-draped surface path. Temperature and pressure use shared contour geometry, while wind vectors are interpolated into an adaptive screen-spaced arrow field. The point inspector reads every forecast variable from that same sampled field regardless of the visible view or overlays. Roads, boundaries, water, and labels remain deliberately legible around these layers.

The main code areas are:

- `src/App.tsx`: shared state and data orchestration
- `src/components/`: map and control-panel UI
- `src/services/`: external data access, grid processing, interpolation, and layer rendering
- `src/types/`: shared TypeScript types
- `src/config/`: grid configuration

The source code remains authoritative for implementation details.

## External providers

The browser currently connects directly to:

- [Open-Meteo](https://open-meteo.com/) for current weather, forecasts, and gridded forecast samples
- [Nominatim / OpenStreetMap](https://nominatim.org/) for place search and reverse geocoding
- [OpenFreeMap](https://openfreemap.org/) for the basemap style and tiles
- [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) for Terrarium elevation tiles used by 3D terrain

No API keys or environment variables are required. Internet access is required, and each provider's availability, usage policy, and rate limits apply.

## Local setup

Requirements:

- Node.js `^20.19.0` or `>=22.12.0`
- npm
- A modern browser with WebGL support
- Internet access for live data and map tiles

From PowerShell in the repository root:

```powershell
npm.cmd install
npm.cmd run dev
```

Open the URL printed by Vite, normally [http://localhost:5173](http://localhost:5173). This project uses `npm.cmd` in PowerShell because the current execution policy blocks the `npm.ps1` shim.

## Commands

| Command | Purpose |
| --- | --- |
| `npm.cmd install` | Install locked dependencies |
| `npm.cmd run dev` | Start the development server with hot reload |
| `npm.cmd run lint` | Run ESLint |
| `npm.cmd run build` | Type-check and create a production build in `dist/` |
| `npm.cmd run preview` | Serve the production build locally |

## Prototype limitations

- Meridian must not be relied upon for safety-critical navigation or weather decisions.
- Forecast surfaces, contours, wind arrows, and point values are visual approximations interpolated from 9 by 9 viewport samples, not full-resolution meteorological model layers.
- The sampling extent changes with zoom but remains a regular latitude/longitude grid; it does not reproduce the source model's native grid or add detail to it.
- Forecast surfaces are intentionally hidden at world scale, where a small browser-side sample cannot represent a global field honestly.
- DEM colour relief and hillshade are more detailed than the forecast fields, but remain limited by the Terrarium tile resolution and MapLibre's browser rendering.
- Forecast playback currently covers 25 hourly points.
- Raster generation, contouring, symbol placement, and interpolation run on the browser's main thread.
- Loading, retry, empty-state, and user-facing error handling are limited.
- Search returns the first matching Nominatim result without disambiguation.
- External availability, rate limits, network access, and browser cross-origin behaviour can affect the app.
- Automated tests, accessibility review, and production operations are not yet established.
