# Phase 5 active-code architecture audit and frozen refactor plan

**Status:** Phase 5A complete; implementation has not begun.

**Boundary:** Phase 5 consists only of 5A (this audit), 5B (structural
reorganisation), 5C (the three defined coupling fixes) and 5D (transitional
cleanup, documentation and final validation). There is no Phase 5E. Useful work
outside those outcomes is backlog, not permission to extend Phase 5.

## Audit basis

The audit traced all 81 active TypeScript/TSX files under `src`, their relative
imports, the `App` and `MapView` state/effect flows, the route and weather
pipelines, and the Vite-loaded tests under `scripts/ui`, `scripts/route`,
`scripts/weather` and `scripts/visual`. The dependency rules in
[`architecture.md`](architecture.md) remain authoritative.

The current tree is organised by technical kind rather than ownership:

```text
src/
  App.tsx / App.css
  main.tsx / index.css
  components/       React UI from every domain
  services/         application, Atlas, Weather and Traverse logic
  types/            Atlas, Weather and Traverse models
  config/           Atlas and Weather provider/visual configuration
```

This layout makes cross-domain imports look local. The import graph also has two
type-level cycles: `types/globalWeather.ts` <->
`services/atmosphericFields.ts`, and `types/routeConditions.ts` <->
`types/derivedRouteConditions.ts`. They should disappear when the affected
models are consolidated under their owner. The empty, unimported
`components/SearchBar.tsx` is transitional debris. `App.tsx` and `main.tsx` are
expected import-graph roots.

## Current architecture map

### Runtime composition

```text
main.tsx
  -> App.tsx
       -> workspace/layout UI
       -> Atlas location, search, terrain and route-elevation services
       -> Open-Meteo selected-location Weather
       -> GFS catalogue, source registry, forecast clock and playback
       -> Traverse GPX import, terrain route, journey schedule and selection
       -> route-at-time weather preparation
       -> MapView
            -> MapLibre lifecycle and base map
            -> terrain and satellite presentation
            -> all Weather layers, sampling and inspector presentation
            -> route rendering, hit testing, focus and camera fitting
```

### State and side-effect ownership today

| Area | Current owner | Important side effects | Finding |
| --- | --- | --- | --- |
| Workspace/layout | `App` + `desktopWorkspaceState` | media listener, workspace transitions | Correctly application-owned, but hidden in generic folders. |
| Selected location | `App`; interaction in `MapView` | debounce, search/reverse lookup, Open-Meteo, camera/marker | App should orchestrate; Atlas owns map/location mechanics and Weather its request. |
| Global Weather | `App` | catalogue watcher, source adoption, forecast playback | Weather lifecycle embedded in `App`. |
| Map lifecycle | `MapView` | MapLibre create/destroy, styles, resize, camera | Atlas responsibility mixed with two consumers. |
| Weather map | `MapView` + Weather services | layers, numeric tiles, inspector samples | Weather work is partly implemented and presented in the mixed component. |
| Route/journey | `App` + Traverse services | file read, DEM, abort/generation guards, schedule | Traverse workflow embedded in `App`; schedule itself is correctly Weather-independent. |
| Route Weather | `App` effect -> `routeConditions` | GFS timestep/tile sampling | App is the right orchestration level, but Traverse knows GFS internals. |
| Route map | `MapView` + route services | layer, hit testing, focus, fit camera | Traverse presentation mixed into Atlas lifecycle. |

### Domain inventory

- **Atlas:** `locationService`, `searchService`, `nominatimClient`,
  `terrainLayers`, `satelliteLayer`, `terrainElevationSampler`, satellite config,
  location/place types, and Atlas portions of `MapView`, `layerVisuals`,
  `dataAttribution`, `mapLayerOrder` and `types/layer`.
- **Weather:** Open-Meteo model/service and forecast UI; GFS catalogue,
  manifests, tile cache, scalar/vector sampling, freshness, formatting,
  contour/surface/wind renderers, and Weather portions of mixed map/config files.
- **Traverse:** GPX/route geometry, terrain enrichment, journey schedule,
  route-at-time conditions, derived conditions, route presentation and route map
  interaction. Its types are `route`, `routeConditions` and
  `derivedRouteConditions`.
- **App:** `App`, workspace reducer/shells/settings, desktop/mobile composition
  and controls that intentionally combine domains.
- **Shared:** no current file has a strong enough domain-neutral, multi-consumer
  case to promote immediately. Phase 5 must not populate `shared` for symmetry.

### Test ownership and seams

| Test area | Current coverage | Phase 5 role |
| --- | --- | --- |
| `scripts/ui/test_desktop_workspace.mjs` | workspace reducer, journey model, profiles, controls, forecast/location and workspace components | App composition plus representative domain UI; exact Vite module paths must follow 5B moves. |
| `scripts/weather/*.mjs` and Weather Python tests | catalogue refresh, publication, atmospheric fields, contours, scalar rendering, updater/builder | Weather domain and external publication; route imports in `test_local_atmosphere` expose the current coupling. |
| `scripts/route/*.mjs` | geometry, terrain, schedule, conditions, rendering and derived context | Traverse domain; imports of numeric tiles/global Weather identify the 5C sampling seam. |
| `scripts/visual/meridian.visual.spec.mjs` | composed desktop/mobile map, Weather, journey and route-analysis behaviour | Cross-domain browser acceptance owned by app. |
| TypeScript, ESLint and Vite build | complete active graph | Required after every implementation subphase. |

## Responsibility map and mismatches

| Current item | Target owner | Required action |
| --- | --- | --- |
| `App.tsx` | `app` | Retain as composition root; delegate cohesive domain lifecycles while keeping cross-domain wiring. |
| `MapView.tsx` | app composition around `atlas/map/AtlasMap` | It cannot simply become Atlas because it depends on Weather and Traverse. |
| `MapOverlayState` | app composition of Atlas and Weather state | Split elevation from Weather flags. |
| `mapLayerOrder` | Atlas anchors + app ordering | Split stable map anchors from cross-domain layer order. |
| `layerVisuals` | Atlas + Weather | Split by consumer rather than moving to shared. |
| `dataAttribution` | Atlas + Weather | Split by provider ownership. |
| `desktopControlOptions` | app + Traverse | App composes controls; Traverse owns analysis modes. |
| `ForecastWorkspace` | Weather content + app wrapper | Remove Weather -> app shell dependency. |
| `ForecastTimeline` / `WeatherFreshness` | Weather | Accept a small forecast-coverage window, not `JourneySchedule`. |
| `routeConditions` | Traverse builder + Weather sampler | Remove GFS types/cache from Traverse. |
| `routeConditions` types | Traverse using narrow Weather provenance | Remove manifest-shaped type coupling. |
| `weatherTimeLabel` | Weather + Traverse | Split functions by semantic owner. |
| `atmosphericFormatting` | Traverse | Its consumers and coverage type are Traverse-specific. |
| `SearchBar.tsx` | none | Remove in 5D after confirming it remains empty/unimported. |

## Required coupling findings

### 1. `App.tsx` / `MapView.tsx`

`App` owns state across all four ownership areas. It loads and watches GFS,
chooses forecast time, fetches location Weather, imports and terrain-enriches a
GPX, calculates a journey schedule, samples route Weather and renders every
workspace. Composition belongs here; complete catalogue and route workflows do
not.

`MapView` receives location, base/overlay state, five Weather sources, Weather
status/time, route geometry/terrain/conditions/mode, workspace state and two
callbacks. It owns MapLibre lifecycle, terrain/satellite, all Weather renderers
and point samples, the combined inspector, route rendering/hit testing and route
camera fitting.

The smallest safe boundary is not a size-based split. In 5B the current mixed
component moves intact to `app/map/MeridianMap.tsx`, so its location does not
falsely assert Atlas ownership. In 5C it becomes app-level composition around:

- `atlas/map/AtlasMap.tsx`: MapLibre lifecycle, base terrain/satellite,
  location/camera mechanics and a narrow map-handle/layer-anchor contract;
- a Weather-owned controller: Weather layers, timesteps and field sampling;
- a Traverse-owned controller: route layer, hit testing, focus and fit requests;
- app-owned combined badge/inspector UI where multiple domains are intentionally
  presented together.

The web adapters may use the MapLibre map handle; Phase 5 does not invent a
universal renderer interface. Weather should own a catalogue/source/time hook,
Traverse should own route/journey state, and app should own selected-location
and route/Weather orchestration. Existing abort controllers, generation guards,
first-timeline behaviour and UI semantics must remain unchanged.

### 2. Weather <-> journey scheduling

Journey scheduling is initiated in `App` from Traverse route/profile/plan state
and calculated by pure `buildJourneySchedule`. Weather does not affect travel
time. That direction is correct.

The reverse dependency is unnecessary: `ForecastTimeline`, `WeatherPanel`,
`WeatherFreshness` and `weatherFreshness` import `JourneySchedule` only to read
departure and finish times for a coverage warning. 5C will define a small
Weather-owned input such as:

```ts
interface ForecastCoverageWindow {
  startTime: string;
  endTime: string;
}
```

App adapts the optional journey schedule to this value. Weather must not import
Traverse, and the schedule remains Traverse-owned.

### 3. Traverse <-> GFS

The dependency is concentrated but deep:

- `routeConditions.ts` imports GFS-shaped scalar/vector sources and timesteps,
  uses `numericTileCache`, selects timesteps and builds manifest provenance;
- `types/routeConditions.ts` imports `GlobalWeatherFieldId` and
  `ScalarFieldManifest`;
- route tests load Weather/GFS internals directly;
- Traverse presentation imports several Weather formatting helpers.

The schedule has no Weather dependency. The inappropriate part is that the
Traverse condition builder is also the GFS adapter. 5C will add one concrete
Weather sampling seam, not a provider framework:

1. Traverse produces position/time requests from route and schedule.
2. App passes requests and active Weather sources to a Weather-owned sampler.
3. Weather selects timesteps, reads numeric tiles and returns normalized values,
   availability reasons and provenance.
4. Traverse combines samples with terrain/journey context and calculates
   route-relative wind, coverage, summaries and derived conditions.

The contract retains model, product, run/valid/request times, resolution, units,
vertical reference, interval semantics and missing-data reasons. It exposes no
GFS tile URLs, cache operations or manifest object shapes. GFS may remain a
provenance value. Existing bounded sampling/concurrency and cache semantics stay
in Weather.

## Target dependency policy

1. `app` may import public Atlas, Weather and Traverse surfaces and owns
   cross-domain composition.
2. `atlas` imports neither Weather nor Traverse.
3. Weather may consume Atlas's narrow web-map handle/anchor contract for map
   rendering. Weather data/domain modules import neither app nor Traverse.
4. Traverse may consume Atlas terrain/coordinate contracts and a narrow,
   provider-neutral Weather sampling contract. It must not import GFS manifests,
   URLs, tile caches or Weather renderer internals.
5. `shared` imports no domain and receives a file only when at least two domains
   need the same neutral concept for the same reason.
6. Cross-domain imports use explicit small public seams; app UI may combine
   domains, but domain UI must not import app shells.
7. Historical experiments are not active `src` dependencies.
8. Missing data, aborts and errors retain their meaning; refactoring must not
   create zeroes, fallbacks or fabricated data.

## Concrete target source tree

```text
src/
  main.tsx
  index.css
  app/
    App.tsx
    App.css
    components/
      DesktopWorkspace.tsx
      DetailWorkspace.tsx
      GlobalSettings.tsx
      LayerLegend.tsx
      LayerPanel.tsx
      MapControls.tsx
      MobileWorkspace.tsx
    map/
      MeridianMap.tsx
      mapLayerOrder.ts
    orchestration/
      useLocationContext.ts
      useJourneyWeather.ts
    state/
      desktopControlOptions.ts
      desktopWorkspaceState.ts
  atlas/
    public.ts
    location/
      locationService.ts
      searchService.ts
      nominatimClient.ts
      types.ts
    map/
      AtlasMap.tsx
      layerAnchors.ts
      satelliteLayer.ts
      satelliteProvider.ts
      terrainLayers.ts
      types.ts
    terrain/
      terrainElevationSampler.ts
  weather/
    public.ts
    components/
      ForecastPanel.tsx
      ForecastTimeline.tsx
      ForecastWorkspaceContent.tsx
      LocationWorkspace.tsx
      TimeSlider.tsx
      WeatherFreshness.tsx
    data/
      atmosphericFields.ts
      globalWeatherService.ts
      numericTileCache.ts
      routeWeatherSampler.ts
      weatherCatalogueRefresh.ts
      weatherService.ts
    map/
      WeatherMapController.tsx
      cloudStyle.ts
      contourGeometry.ts
      globalCloudLayer.ts
      globalPrecipitationLayer.ts
      globalScalarSurface.ts
      globalWindSource.ts
      interpolation.ts
      pressureContourModel.ts
      pressureLayer.ts
      scalarRaster.ts
      temperatureContourLayer.ts
      temperatureContourModel.ts
      windField.ts
      windLayer.ts
      windParticleLayer.ts
      windVector.ts
    presentation/
      forecastWorkspaceModel.ts
      precipitationStyle.ts
      weatherFreshness.ts
      weatherTimeLabel.ts
    types.ts
    visuals.ts
  traverse/
    public.ts
    components/
      DerivedConditionContext.tsx
      JourneyOverview.tsx
      JourneySettings.tsx
      RouteAnalysis.tsx
      RoutePlannerPanel.tsx
      RoutePointDetails.tsx
      RouteProfile.tsx
    map/
      TraverseMapController.tsx
      routeCamera.ts
      routeLayer.ts
    model/
      atmosphericFormatting.ts
      derivedConditionFormatting.ts
      derivedRouteConditions.ts
      journeyModel.ts
      journeyPresentation.ts
      routeConditions.ts
      routeConditionStyle.ts
      routeGeometry.ts
      routeProfileInteraction.ts
      routeTerrain.ts
    types.ts
  shared/                 # only if 5C proves a real neutral owner
```

`ForecastWorkspaceContent` deliberately excludes the app-owned shell.
`MobileWorkspace` is the current `WeatherPanel`; the rename reflects its Weather,
map-control and route composition. The current `MapView` becomes `MeridianMap`
before it is split. Ordinary terms such as route and journey are not prefixed
with the provisional product name.

## File disposition

### App and mixed composition

| Current files | 5B disposition | 5C/5D disposition |
| --- | --- | --- |
| `App.tsx`, `App.css` | Move to `app/`. | Delegate workflows; retain composition. |
| `DesktopWorkspace`, `DetailWorkspace`, `GlobalSettings`, `MapControls`, `LayerLegend`, `LayerPanel` | Move to `app/components`. | Keep intentionally mixed UI in app. |
| `WeatherPanel` | Rename/move to `app/components/MobileWorkspace`. | Preserve mobile behaviour. |
| `MapView` | Rename/move intact to `app/map/MeridianMap`. | Extract Atlas host and Weather/Traverse controllers. |
| `desktopWorkspaceState`, `desktopControlOptions`, `mapLayerOrder` | Move to `app/state` or `app/map`. | Split domain constants/anchors only where required. |
| `types/layer`, `config/layerVisuals`, `config/dataAttribution` | Move temporarily to app compatibility locations. | Split Atlas/Weather ownership; remove transitional files in 5D. |

### Atlas

| Current files | Disposition |
| --- | --- |
| `locationService`, `searchService`, `nominatimClient`; `types/location`, `types/place` | Move to `atlas/location`; expose from `atlas/public.ts`. |
| `terrainLayers`, `satelliteLayer`, `config/satelliteProvider` | Move to `atlas/map`. |
| `terrainElevationSampler` | Move to `atlas/terrain`; expose a terrain-sampling operation. |
| Atlas parts of mixed map/config/type files | Extract in 5C into `AtlasMap`, anchors/types and Atlas visuals/attribution. |

### Weather

| Current files | Disposition |
| --- | --- |
| `ForecastPanel`, `LocationWorkspace`, `TimeSlider`, `WeatherFreshness` | Move to `weather/components`. |
| `ForecastTimeline` | Move after its mixed legend/journey input is removed in 5C; app compatibility location is allowed in 5B. |
| `ForecastWorkspace` | Move content/model to Weather in 5C; app owns the shell wrapper. |
| `weatherService`, `globalWeatherService`, `weatherCatalogueRefresh`, `numericTileCache`, `atmosphericFields` | Move to `weather/data`. |
| `cloudStyle`, `contourGeometry`, `globalCloudLayer`, `globalPrecipitationLayer`, `globalScalarSurface`, `globalWindSource`, `interpolation`, `pressureContourModel`, `pressureLayer`, `scalarRaster`, `temperatureContourLayer`, `temperatureContourModel`, `windField`, `windLayer`, `windParticleLayer`, `windVector` | Move to `weather/map`; preserve singleton/cache/layer identities. |
| `forecastWorkspaceModel`, `precipitationStyle`, `weatherFreshness`, Weather part of `weatherTimeLabel` | Move to `weather/presentation`. |
| `types/weather`, `types/globalWeather` | Consolidate under Weather and remove the atmospheric type cycle. |
| Weather parts of mixed map/config/type files | Extract in 5C into Weather visuals, overlay types and map controller. |

### Traverse

| Current files | Disposition |
| --- | --- |
| `DerivedConditionContext`, `JourneyOverview`, `JourneySettings`, `RouteAnalysis`, `RoutePlannerPanel`, `RouteProfile` | Move to `traverse/components`. |
| `ForecastDetails` | Rename/move to `traverse/components/RoutePointDetails`. |
| `journeyModel`, `journeyPresentation`, `routeGeometry`, `routeTerrain`, `routeProfileInteraction`, `routeConditionStyle`, `derivedRouteConditions`, `derivedConditionFormatting`, `atmosphericFormatting` | Move to `traverse/model`. |
| `routeLayer`, `routeCamera` | Move to `traverse/map`. |
| `routeConditions` | Move initially with Traverse; split GFS sampling in 5C. |
| `types/route`, `types/routeConditions`, `types/derivedRouteConditions` | Consolidate under Traverse; remove Weather manifest coupling and the type cycle. |
| Traverse parts of `MapView` | Extract to `TraverseMapController` in 5C. |

### Remain or remove

- `main.tsx` and `index.css` remain the minimal root bootstrap/global style.
- `components/SearchBar.tsx` remains in 5B and is removed in 5D.
- Historical Earth Lab, renderer and research source remain untouched.
- Script tests remain grouped by UI, Weather, route and visual concerns; their
  exact source-loader paths change with 5B.
- `shared` remains absent unless 5C proves a neutral owner.

## Frozen Phase 5B plan — structural reorganisation

5B performs path and naming work only:

1. Create the `app`, `atlas`, `weather` and `traverse` ownership directories.
2. Move unambiguous files and update imports and test loader paths.
3. Move `App`; rename `WeatherPanel` to `MobileWorkspace`, `MapView` to
   `MeridianMap`, and `ForecastDetails` to `RoutePointDetails`.
4. Keep mixed configuration/types and mixed timeline/workspace code at a
   documented app compatibility location if moving it would create a domain ->
   app cycle.
5. Add only minimal public seams needed by moved callers. Do not add hooks,
   sampling abstractions or logic changes.
6. Preserve CSS classes, runtime URLs, provider behaviour, props, singleton
   caches, abort/generation guards and UI behaviour.

5B must not split the map, change state ownership, alter route/Weather sampling,
create a state library or introduce product behaviour.

### 5B validation gate

- no accidental old generic-path references beyond documented compatibility;
- TypeScript, ESLint and Vite production build;
- UI, route and Weather deterministic suites;
- publication/storage checks;
- representative Playwright smoke for location Weather, global overlay, route
  import, journey schedule, route analysis and map interaction;
- `git diff --check`, privacy and credential scans.

## Frozen Phase 5C plan — defined coupling fixes

1. **App/map:** extract `AtlasMap`, `WeatherMapController` and
   `TraverseMapController`; keep combined status/inspector composition in
   `MeridianMap`; delegate cohesive Weather and Traverse workflows from `App`
   while keeping cross-domain wiring there.
2. **Weather/journey:** replace Weather imports of `JourneySchedule` with the
   forecast coverage window adapted by app.
3. **Traverse/GFS:** create the Weather route sampler, make app orchestrate it,
   and make Traverse assemble route conditions from normalized results. Remove
   GFS manifest/tile-cache imports from Traverse.
4. Split mixed overlay state, visuals, attribution, layer anchors/order and time
   labels only as required for consistent dependency direction.
5. Add focused contract and import-boundary tests. Preserve missing-data,
   temporal, provenance, abort and cache semantics.

5C must not change journey timing from Weather, add providers, redesign UI,
alter map styling or generalize beyond the concrete browser/GFS implementation.

### 5C validation gate

- static test proves Atlas imports neither Weather nor Traverse, Weather imports
  neither app nor Traverse, shared imports no domain, and Traverse has no
  GFS/tile-cache/internal Weather imports;
- contract tests cover forecast-window adaptation and route Weather sampling for
  available, outside-horizon, no-data, abort and provenance cases;
- existing route-condition numerical, coverage and derived-condition assertions;
- map lifecycle seams cover setup/update/cleanup without duplicate layers or
  listeners;
- UI, route, Weather, TypeScript, ESLint, build and representative Playwright.

## Frozen Phase 5D plan — cleanup, validation and end

1. Remove the empty `SearchBar` and compatibility forwarding files,
   transitional mixed types/configs or generic directories made redundant by
   5B/5C.
2. Resolve the two audited type cycles if they remain.
3. Inspect every cross-domain import and document intentional public-seam use.
4. Reconcile architecture, README source-layout/setup text and development log
   with the code that exists.
5. Run the complete validation gate and prepare one clean Phase 5 checkpoint.

5D does not absorb backlog work. Phase 5 ends when this plan's structure and
three coupling seams are complete, behaviour is equivalent, docs are truthful
and validation passes.

### 5D validation gate

- all established UI, route and Weather deterministic tests;
- relevant storage/publication checks;
- TypeScript, ESLint and Vite production build;
- established Playwright visual/browser workflow at representative desktop
  sizes, including location, GFS overlay, journey and route analysis;
- import-boundary test and obsolete-path/name search;
- `git diff --check`, config parsing, privacy/credential scan and Git review;
- historical Labs, renderer source, external data and private data unchanged.

## Frozen Phase 5 completion criteria

At the end of 5D:

- active code is owned under `app`, `atlas`, `weather` and `traverse`; `shared`
  exists only if justified;
- app owns composition, Atlas does not depend on Weather/Traverse, Weather does
  not depend on journey models, and Traverse does not depend on GFS/tile internals;
- the map has an Atlas lifecycle with app-composed Weather and Traverse adapters;
- application behaviour, data meaning, missing-data semantics and publication
  contracts remain equivalent;
- required automated/browser validation passes;
- docs describe actual code, transitional files are gone, and optional work is
  backlog;
- historical experiments and renderer identities remain untouched.

## Post-cleanup backlog (outside Phase 5)

- Decompose the large wind-particle renderer, numeric tile cache or individual
  layers beyond the ownership moves.
- Introduce a renderer-independent map engine abstraction or plugin system.
- Split Meridian into separate deployable Atlas, Weather or Traverse apps.
- Add state management or generalized dependency injection/provider machinery.
- Redesign mobile UI, route analysis, forecast visuals or map aesthetics.
- Replace providers or add data products.
- Reorganise historical Earth Lab, Python research or Unreal assets.
- Generalise the Weather sampling seam before a second real consumer exists.

## Risks and review points

- MapLibre style reloads, StrictMode and imperative listener lifetimes make the
  map split the highest regression risk.
- `numericTileCache` is a module singleton with pin ownership. Duplicate module
  identity or changed cleanup order can alter requests and memory.
- Route preparation and route Weather use abort controllers plus generation
  counters; stale promises must never regain ownership.
- Forecast time combines Open-Meteo and intersected GFS times; moving state must
  preserve selection, playback and first-overlay initialization.
- Layer order is intentionally cross-domain. App owns order while domains own
  layers; duplicating order rules in each domain is unsafe.
- CSS is global and class-name coupled. Phase 5 moves files, not styles/markup,
  unless a required boundary split needs a wrapper change.
- Vite SSR tests load exact paths; Playwright fixtures depend on current network
  interception and labels. Paths must change without weakening assertions.
- Forecast and mobile workspaces need app wrappers. Moving them wholesale into
  Weather would create the wrong dependency direction.
- If a seam requires a generic framework or product behaviour change, stop for
  review rather than expanding Phase 5.
