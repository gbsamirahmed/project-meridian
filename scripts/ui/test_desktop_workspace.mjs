import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
const [state, journeyModel, profileInteraction, controlOptions, routeCamera, desktopModule, overviewModule, settingsModule, detailsModule, controlsModule, timelineModule, analysisModule] = await Promise.all([
  server.ssrLoadModule("/src/services/desktopWorkspaceState.ts"),
  server.ssrLoadModule("/src/services/journeyModel.ts"),
  server.ssrLoadModule("/src/services/routeProfileInteraction.ts"),
  server.ssrLoadModule("/src/services/desktopControlOptions.ts"),
  server.ssrLoadModule("/src/services/routeCamera.ts"),
  server.ssrLoadModule("/src/components/DesktopWorkspace.tsx"),
  server.ssrLoadModule("/src/components/JourneyOverview.tsx"),
  server.ssrLoadModule("/src/components/JourneySettings.tsx"),
  server.ssrLoadModule("/src/components/ForecastDetails.tsx"),
  server.ssrLoadModule("/src/components/MapControls.tsx"),
  server.ssrLoadModule("/src/components/ForecastTimeline.tsx"),
  server.ssrLoadModule("/src/components/RouteAnalysis.tsx"),
]);
const DesktopWorkspace = desktopModule.default;
const JourneyOverview = overviewModule.default;
const JourneySettings = settingsModule.default;
const ForecastDetails = detailsModule.default;
const MapControls = controlsModule.default;
const ForecastTimeline = timelineModule.default;
const RouteAnalysis = analysisModule.default;
test.after(() => server.close());

const noop = () => {};
const instant = hour => new Date(Date.UTC(2026, 8, 3, hour)).toISOString();
const provenance = (fieldId="temperature_2m") => ({
  fieldId, model: "NOAA GFS", product: "pgrb2.0p25", runTime: instant(0), sourceLevel: "surface",
  units: fieldId === "visibility_surface" ? "m" : fieldId.includes("freezing") || fieldId === "cloud_ceiling" ? "gpm" : "m/s",
  nativeResolutionDegrees: 0.25, requestedTime: instant(2), validTime: instant(2), forecastHour: 2,
  temporalOffsetMinutes: 15, timeSemantics: "instantaneous",
});
const scalar = (value, fieldId="temperature_2m") => ({ state: "available", value, units: provenance(fieldId).units, provenance: provenance(fieldId) });
const missing = () => ({ state: "unavailable", requestedTime: instant(2), reason: "outside-forecast" });
const weather = (partial=false) => ({
  temperature: scalar(8, "temperature_2m"), precipitation: { ...scalar(0.7, "precipitation_surface"), provenance: { ...provenance("precipitation_surface"), timeSemantics: "interval-total", accumulationStart: instant(1), accumulationEnd: instant(2) } },
  cloud: scalar(55, "cloud_cover"), wind: { state: "available", uMs: 3, vMs: 4, speedMs: 5, directionFromDegrees: 220, relative: null, provenance: provenance("wind_10m") },
  gust: scalar(11, "gust_surface"), visibility: partial ? missing() : scalar(8000, "visibility_surface"),
  freezingLevel: scalar(2100, "freezing_level"), highestFreezingLevel: scalar(2500, "highest_freezing_level"), cloudCeiling: scalar(900, "cloud_ceiling"),
});
const samples = [0, 500, 1000].map((distance, index) => ({
  routeSampleIndex: index, coordinate: { longitude: -1 + index * 0.01, latitude: 51 }, cumulativeDistanceM: distance,
  routeProgress: index / 2, routeBearingDegrees: 90, terrain: { elevationM: 100 + index * 20, gradient: index ? 0.08 : 0 },
  journey: { movingElapsedMinutes: index * 30, stoppedElapsedMinutes: 0, elapsedMinutes: index * 30, expectedArrivalTime: instant(1 + index), earliestArrivalTime: instant(1 + index), latestArrivalTime: instant(2 + index) },
  weather: weather(index === 2),
}));
const coverage = Object.fromEntries(Object.keys(samples[0].weather).map(key => [key, { availableSamples: key === "visibility" ? 2 : 3, totalSamples: 3 }]));
const conditions = { routeId: "route", generatedAt: instant(0), samples, coverage, derived: null, summary: {
  temperatureRangeC: [7, 9], precipitationMaximumMm: 0.7, precipitationEncountered: true, cloudRangePercent: [40, 70],
  windMaximumMs: 5, headwindMaximumMs: 2, crosswindMaximumMs: 3, gustMaximumMs: 11, visibilityMinimumM: 8000, freezingLevelRangeGpm: [2000, 2200],
}};
const terrain = { id: "route", name: "South Downs", totalDistanceM: 1000, totalAscentM: 80, totalDescentM: 55, elevationCoverage: "complete", spacingM: 500, sourcePointCount: 3,
  samples: samples.map((sample, index) => ({ index, ...sample.coordinate, cumulativeDistanceM: sample.cumulativeDistanceM, elevationM: sample.terrain.elevationM, smoothedElevationM: sample.terrain.elevationM, gradient: sample.terrain.gradient, cumulativeAscentM: index * 40, cumulativeDescentM: index * 27.5 })) };
const geometry = { id: "route", name: "South Downs", totalDistanceM: 1000, coordinates: samples.map(sample => sample.coordinate), cumulativeDistancesM: samples.map(sample => sample.cumulativeDistanceM), spacingM: 500, sourcePointCount: 3 };
const profile = { activity: "hiking", pace: "normal", party: "solo", load: "light", plannedBreakMinutes: 30 };
const plan = { mode: "profile", departureTime: instant(1), targetDurationMinutes: 180, targetFinishTime: instant(5) };
const schedule = { routeId: "route", departureTime: instant(1), expectedFinishTime: instant(4), movingMinutes: 150, stoppedMinutes: 30, totalMinutes: 180, likelyMinimumMinutes: 160, likelyMaximumMinutes: 210, movementScale: 1, targetComparison: "close-to-baseline", samples: samples.map((sample, index) => ({ routeSampleIndex: index, cumulativeDistanceM: sample.cumulativeDistanceM, movingElapsedMinutes: index * 75, stoppedElapsedMinutes: index ? 15 : 0, elapsedMinutes: index * 90, arrivalTime: instant(1 + index), earliestArrivalTime: instant(1 + index), latestArrivalTime: instant(2 + index) })) };

function overview(extra={}) {
  return renderToStaticMarkup(createElement(JourneyOverview, { routeGeometry: geometry, terrainRoute: terrain, schedule, scheduleError: null, status: "ready", statusMessage: null, profile, plan, routeConditions: conditions, routeConditionStatus: "partial", onImport: noop, onClear: noop, focusedIndex: null, onFocusChange: noop, onOpenSettings: noop, onOpenAnalysis: noop, ...extra }));
}

test("workspace state is presentation-only, explicit, and Map Inspector starts off", () => {
  const routeSentinel = { id: "retained-route" };
  const playbackSentinel = { playing: true, hour: 4 };
  let current = state.INITIAL_DESKTOP_WORKSPACE_STATE;
  assert.equal(current.mapInspectorEnabled, false);
  current = state.desktopWorkspaceReducer(current, { type: "set-workspace", mode: "analysis" });
  current = state.desktopWorkspaceReducer(current, { type: "set-journey-settings", open: true });
  assert.equal(current.workspaceMode, "analysis");
  assert.equal(current.journeySettingsOpen, true);
  assert.deepEqual(routeSentinel, { id: "retained-route" });
  assert.deepEqual(playbackSentinel, { playing: true, hour: 4 });
  current = state.desktopWorkspaceReducer(current, { type: "set-clear-map", active: true });
  assert.equal(current.clearMap, true);
  assert.equal(current.workspaceMode, "analysis");
  current = state.desktopWorkspaceReducer(current, { type: "set-clear-map", active: false });
  assert.equal(current.clearMap, false);
  assert.equal(current.workspaceMode, "analysis");
  current = state.desktopWorkspaceReducer(current, { type: "set-map-inspector", enabled: true });
  assert.equal(current.mapInspectorEnabled, true);
});

test("Analysis is absent without a route and available as the third workspace tab with one", () => {
  const common = { onModeChange: noop, onSettings: noop, onFocusMode: noop };
  const noRoute = renderToStaticMarkup(createElement(DesktopWorkspace, { ...common, mode: "journey", analysisAvailable: false }, createElement("p", null, "journey-state")));
  const analysis = renderToStaticMarkup(createElement(DesktopWorkspace, { ...common, mode: "analysis", analysisAvailable: true }, createElement("p", null, "same-route-state")));
  assert.match(noRoute, /aria-selected="true">Journey/);
  assert.ok(!noRoute.includes(">Analysis<"));
  assert.match(analysis, /aria-selected="true">Analysis/);
  assert.match(analysis, /workspace-tabs-three/);
  assert.match(analysis, /same-route-state/);
});
test("canonical Meridian brand is the sole normal-workspace focus control", () => {
  const html = renderToStaticMarkup(createElement(DesktopWorkspace, {
    mode: "location", analysisAvailable: false, onModeChange: noop, onSettings: noop, onFocusMode: noop,
  }, createElement("p", null, "location-state")));
  assert.match(html, /src="\/favicon\.svg"/);
  assert.match(html, /aria-label="Enter focus mode"/);
  assert.ok(!html.includes("Focus map"));
  assert.ok(!html.includes("Hide workspace"));
});

test("route-fit padding reserves the rendered primary workspace and gutter", () => {
  assert.deepEqual(routeCamera.calculateRouteFitPadding({
    mapLeftPx: 0, workspaceRightPx: 308, workspaceGutterPx: 12,
  }), { top: 48, right: 48, bottom: 48, left: 368 });
  assert.deepEqual(routeCamera.calculateRouteFitPadding({
    mapLeftPx: 0, workspaceRightPx: null, workspaceGutterPx: 12,
  }), { top: 48, right: 48, bottom: 48, left: 48 });
});
test("journey overview separates route facts from derived estimate and uses human coverage wording", () => {
  const html = overview();
  for (const text of ["Route facts", "Journey estimate", "Moving", "Breaks", "Weather overview", "Elevation profile", "Route shape", "Analyse", "Gradient"]) assert.ok(html.includes(text), text);
  for (const removed of ["Measured from route &amp; terrain", "Terrain overview", "Terrain and timing ready", "Open analysis", "View profile", "Environmental details"]) assert.ok(!html.includes(removed), removed);
  for (const mode of ["none", "gradient", "temperature", "precipitation", "wind"]) assert.ok(html.includes("data-analysis-mode=\"" + mode + "\""), mode);
  assert.match(html, /Visibility is unavailable after approximately 0.5 km/);
  assert.ok(!html.includes("All scheduled samples"));
  assert.ok(!html.includes("Route foundation"));
});

test("complete coverage is silent and an empty journey offers a clear import action", () => {
  const complete = structuredClone(conditions); complete.coverage.visibility.availableSamples = 3; complete.samples[2].weather.visibility = scalar(9000, "visibility_surface");
  assert.ok(!overview({ routeConditions: complete, routeConditionStatus: "ready" }).includes("coverage-messages"));
  const html = renderToStaticMarkup(createElement(JourneyOverview, { routeGeometry: null, terrainRoute: null, schedule: null, scheduleError: null, status: "idle", statusMessage: null, profile, plan, routeConditions: null, routeConditionStatus: "idle", onImport: noop, onClear: noop, focusedIndex: null, onFocusChange: noop, onOpenSettings: noop, onOpenAnalysis: noop }));
  for (const text of ["Plan with a route", "Import a GPX to analyse terrain, timing and weather along your journey.", "Import GPX", "Processed locally in your browser."]) assert.ok(html.includes(text), text); assert.match(html, /class="workspace-card journey-empty"/); assert.ok(!html.includes("Route foundation"));
});

test("Journey Tune is an in-panel subview and retains every schedule input", () => {
  const html = renderToStaticMarkup(createElement(JourneySettings, { profile, plan, onProfileChange: noop, onPlanChange: noop, onBack: noop }));
  for (const text of ["Journey settings", "← Journey", "Activity", "Pace", "Party", "Load", "Planned breaks", "Plan from", "Departure"]) assert.ok(html.includes(text), text);
  assert.ok(!html.includes("workspace-popover"));
  assert.ok(!html.includes("These assumptions change"));
  const withoutBreaks = journeyModel.buildJourneySchedule(terrain, { ...profile, plannedBreakMinutes: 0 }, plan);
  const withBreaks = journeyModel.buildJourneySchedule(terrain, { ...profile, plannedBreakMinutes: 60 }, plan);
  assert.equal(withBreaks.stoppedMinutes - withoutBreaks.stoppedMinutes, 60);
});

test("selected point groups model values beneath one shared source block", () => {
  const html = renderToStaticMarkup(createElement(ForecastDetails, { sample: samples[0], derived: null }));
  for (const text of ["Temperature", "Precipitation", "Cloud", "Wind", "Gusts", "Visibility", "Freezing level", "Highest freezing level", "Cloud ceiling", "About this data"]) assert.ok(html.includes(text), text);
  assert.equal((html.match(/shared-source-block/g) ?? []).length, 1);
  assert.equal((html.match(/GFS · 0.25° · run/g) ?? []).length, 1);
});

test("persistent map rail retains every compact layer and has no close or timeline control", () => {
  const html = renderToStaticMarkup(createElement(MapControls, { basemap: "terrain", mapOverlays: { elevation: true, precipitation: false, clouds: false, temperatureContours: false, pressureIsobars: true, windFlow: false }, satelliteAvailable: true, onBasemapChange: noop, onOverlayChange: noop }));
  for (const text of ["Terrain basemap", "Satellite basemap", "Elevation", "Precipitation", "Cloud cover", "Temperature contours", "Pressure isobars", "Wind flow", ">Ter<", ">Sat<", ">Elev<", ">Rain<", ">Cloud<", ">Temp<", ">Pres<", ">Wind<"]) assert.ok(html.includes(text), text);
  assert.ok(!html.includes("Hide map controls"));
  assert.ok(!html.includes("Forecast timeline"));
});

test("forecast timeline remains a compact Location control with playback and data access", () => {
  const statuses = Object.fromEntries(["precipitation","cloud_cover","wind_10m","temperature_2m","gust_surface","visibility_surface","freezing_level","highest_freezing_level","cloud_ceiling"].map(key => [key,"ready"]));
  const html = renderToStaticMarkup(createElement(ForecastTimeline, { mapOverlays: { elevation: false, precipitation: false, clouds: false, temperatureContours: false, pressureIsobars: true, windFlow: false }, forecastHour: 0, forecastTimes: [instant(0), instant(1)], forecastHours: [0,1], activeGlobalValidTime: instant(0), globalPrecipitationSource: null, globalCloudSource: null, globalWindSource: null, globalTemperatureSource: null, globalWeatherStatuses: statuses, globalWeatherCatalog: null, catalogueCheck: { lastSuccessfulCheck: null, lastCheckFailed: false }, journeySchedule: schedule, weatherGridStatus: "ready", onForecastHourChange: noop, isPlaying: true, onPlayingChange: noop }));
  for (const text of ["Forecast timeline", "Pause forecast", "Data", "9 × 9 Open-Meteo sample grid"]) assert.ok(html.includes(text), text);
});

test("Analysis workspace preserves profile focus and condition strip access", () => {
  const html = renderToStaticMarkup(createElement(RouteAnalysis, { route: terrain, schedule, conditions, conditionStatus: "partial", conditionMode: "temperature", focusedIndex: 1, pinnedIndex: 1, onPreviewChange: noop, onPinnedChange: noop, onConditionModeChange: noop }));
  assert.match(html, /role="slider"/); assert.match(html, /aria-valuenow="500"/); assert.match(html, /route-profile-focus-point/); assert.match(html, /route-profile-condition-segment/); assert.match(html, /Selected journey point/);
});

test("presentation actions perform no network work", () => {
  const originalFetch = globalThis.fetch; let calls = 0; globalThis.fetch = () => { calls += 1; throw new Error("unexpected"); };
  try {
    let current = state.INITIAL_DESKTOP_WORKSPACE_STATE;
    for (const action of [{ type: "set-workspace", mode: "analysis" }, { type: "set-clear-map", active: true }, { type: "set-clear-map", active: false }]) current = state.desktopWorkspaceReducer(current, action);
    assert.equal(current.clearMap, false); assert.equal(calls, 0);
  } finally { globalThis.fetch = originalFetch; }
});
test("profile coordinates cover the true drawable width at several container sizes", () => {
  for (const geometry of [
    { boundsLeft: 100, boundsWidth: 1000, viewBoxWidth: 1000, plotLeft: 12, plotRight: 8 },
    { boundsLeft: 20, boundsWidth: 620, viewBoxWidth: 620, plotLeft: 12, plotRight: 8 },
  ]) {
    const drawableStart = geometry.boundsLeft + geometry.boundsWidth * geometry.plotLeft / geometry.viewBoxWidth;
    const drawableWidth = geometry.boundsWidth * (geometry.viewBoxWidth - geometry.plotLeft - geometry.plotRight) / geometry.viewBoxWidth;
    for (const fraction of [0, 0.25, 0.5, 0.75, 1]) {
      const clientX = drawableStart + drawableWidth * fraction;
      assert.ok(Math.abs(profileInteraction.profilePointerFraction(clientX, geometry) - fraction) < 1e-10);
    }
  }
  assert.equal(profileInteraction.nearestRouteSampleForFraction(terrain.samples, terrain.totalDistanceM, 0.5), 1);
});

test("profile pin state moves and toggles off without changing route data", () => {
  assert.equal(profileInteraction.nextPinnedRouteSample(null, 1), 1);
  assert.equal(profileInteraction.nextPinnedRouteSample(1, 2), 2);
  assert.equal(profileInteraction.nextPinnedRouteSample(2, 2), null);
  assert.equal(profileInteraction.activeRouteSampleIndex(1, null), 1);
  assert.equal(profileInteraction.activeRouteSampleIndex(1, 2), 2);
  assert.equal(terrain.id, "route");
});

test("Analysis workspace uses compact mode controls and hides successful status noise", () => {
  const html = renderToStaticMarkup(createElement(RouteAnalysis, { route: { ...terrain, name: "A deliberately very long imported route name that must not displace controls" }, schedule, conditions, conditionStatus: "ready", conditionMode: "none", focusedIndex: null, pinnedIndex: null, onPreviewChange: noop, onPinnedChange: noop, onConditionModeChange: noop }));
  for (const label of ["Elevation analysis", "Temperature analysis", "Rain analysis", "Wind analysis", "Gradient analysis"]) assert.ok(html.includes(label), label);
  assert.ok(!html.includes("Route colour"));
  assert.ok(!html.includes("Conditions ready"));
  assert.match(html, /title="A deliberately very long imported route name/);
});

test("all fields outside the forecast horizon collapse to one clear message", () => {
  const outside = structuredClone(samples[0]);
  outside.weather = Object.fromEntries(Object.keys(outside.weather).map(key => [key, missing()]));
  const html = renderToStaticMarkup(createElement(ForecastDetails, { sample: outside, derived: null }));
  assert.match(html, /outside the available forecast horizon/);
  assert.equal((html.match(/Outside forecast/g) ?? []).length, 0);
});

test("map tool metadata maps every compact control to the existing layer key", () => {
  assert.deepEqual(controlOptions.MAP_OVERLAY_TOOLS.map(tool => tool.key), [
    "elevation", "precipitation", "clouds", "temperatureContours", "pressureIsobars", "windFlow",
  ]);
  assert.deepEqual(controlOptions.ANALYSIS_MODES.map(item => item.mode), [
    "none", "temperature", "precipitation", "wind", "gradient",
  ]);
});

test("loading and degraded route states remain visible", () => {
  assert.match(overview({ status: "loading-elevation", statusMessage: "Loading terrain elevation · 2/4 tiles" }), /Loading terrain elevation · 2\/4 tiles/);
  assert.match(overview({ status: "partial", statusMessage: "Some terrain elevation is unavailable" }), /Some terrain elevation is unavailable/);
});
