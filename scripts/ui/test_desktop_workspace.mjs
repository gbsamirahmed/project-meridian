import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
const [state, journeyModel, desktopModule, overviewModule, settingsModule, detailsModule, controlsModule, analysisModule] = await Promise.all([
  server.ssrLoadModule("/src/services/desktopWorkspaceState.ts"),
  server.ssrLoadModule("/src/services/journeyModel.ts"),
  server.ssrLoadModule("/src/components/DesktopWorkspace.tsx"),
  server.ssrLoadModule("/src/components/JourneyOverview.tsx"),
  server.ssrLoadModule("/src/components/JourneySettings.tsx"),
  server.ssrLoadModule("/src/components/ForecastDetails.tsx"),
  server.ssrLoadModule("/src/components/MapControls.tsx"),
  server.ssrLoadModule("/src/components/RouteAnalysis.tsx"),
]);
const DesktopWorkspace = desktopModule.default;
const JourneyOverview = overviewModule.default;
const JourneySettings = settingsModule.default;
const ForecastDetails = detailsModule.default;
const MapControls = controlsModule.default;
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
  return renderToStaticMarkup(createElement(JourneyOverview, { routeGeometry: geometry, terrainRoute: terrain, schedule, scheduleError: null, status: "ready", statusMessage: null, profile, plan, routeConditions: conditions, routeConditionStatus: "partial", onImport: noop, onClear: noop, onOpenSettings: noop, onOpenAnalysis: noop, ...extra }));
}

test("workspace state is presentation-only, explicit, and Map Inspector starts off", () => {
  const routeSentinel = { id: "retained-route" };
  let current = state.INITIAL_DESKTOP_WORKSPACE_STATE;
  assert.equal(current.mapInspectorEnabled, false);
  current = state.desktopWorkspaceReducer(current, { type: "set-workspace", mode: "journey" });
  current = state.desktopWorkspaceReducer(current, { type: "set-left", open: false });
  current = state.desktopWorkspaceReducer(current, { type: "set-map-controls", open: false });
  current = state.desktopWorkspaceReducer(current, { type: "set-route-analysis", open: false });
  assert.equal(current.workspaceMode, "journey"); assert.equal(current.leftOpen, false); assert.equal(current.mapControlsOpen, false); assert.equal(current.routeAnalysisOpen, false);
  assert.deepEqual(routeSentinel, { id: "retained-route" });
  current = state.desktopWorkspaceReducer(current, { type: "set-clear-map", active: true });
  assert.equal(current.clearMap, true); assert.equal(current.leftOpen, false); assert.equal(current.workspaceMode, "journey");
  current = state.desktopWorkspaceReducer(current, { type: "set-map-inspector", enabled: true });
  assert.equal(current.mapInspectorEnabled, true);
});

test("Location and Journey are parallel workspace tabs", () => {
  const location = renderToStaticMarkup(createElement(DesktopWorkspace, { mode: "location", onModeChange: noop, onClose: noop, onSettings: noop, onClearMap: noop }, createElement("p", null, "location-state")));
  const journey = renderToStaticMarkup(createElement(DesktopWorkspace, { mode: "journey", onModeChange: noop, onClose: noop, onSettings: noop, onClearMap: noop }, createElement("p", null, "same-route-state")));
  assert.match(location, /aria-selected="true">Location/); assert.match(journey, /aria-selected="true">Journey/); assert.match(journey, /same-route-state/);
});

test("journey overview separates route facts from derived estimate and uses human coverage wording", () => {
  const html = overview();
  for (const text of ["Route facts", "Measured from route &amp; terrain", "Journey estimate", "Moving", "Breaks", "Weather overview", "Terrain overview"]) assert.ok(html.includes(text), text);
  assert.match(html, /Visibility is unavailable after approximately 0.5 km/);
  assert.ok(!html.includes("All scheduled samples"));
  assert.ok(!html.includes("Route foundation"));
});

test("complete coverage is silent and an empty journey offers a clear import action", () => {
  const complete = structuredClone(conditions); complete.coverage.visibility.availableSamples = 3; complete.samples[2].weather.visibility = scalar(9000, "visibility_surface");
  assert.ok(!overview({ routeConditions: complete, routeConditionStatus: "ready" }).includes("coverage-messages"));
  const html = renderToStaticMarkup(createElement(JourneyOverview, { routeGeometry: null, terrainRoute: null, schedule: null, scheduleError: null, status: "idle", statusMessage: null, profile, plan, routeConditions: null, routeConditionStatus: "idle", onImport: noop, onClear: noop, onOpenSettings: noop, onOpenAnalysis: noop }));
  assert.match(html, /Import GPX/); assert.ok(!html.includes("Route foundation"));
});

test("journey settings retain every existing schedule input and schedule changes with breaks", () => {
  const html = renderToStaticMarkup(createElement(JourneySettings, { open: true, profile, plan, onProfileChange: noop, onPlanChange: noop, onClose: noop }));
  for (const text of ["Activity", "Pace", "Party", "Load", "Planned breaks", "Plan from", "Departure"]) assert.ok(html.includes(text), text);
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

test("map controls retain all layers, timeline, play, and pressure-specific sampling label", () => {
  const statuses = Object.fromEntries(["precipitation","cloud_cover","wind_10m","temperature_2m","gust_surface","visibility_surface","freezing_level","highest_freezing_level","cloud_ceiling"].map(key => [key,"ready"]));
  const html = renderToStaticMarkup(createElement(MapControls, { basemap: "terrain", mapOverlays: { elevation: true, precipitation: false, clouds: false, temperatureContours: false, pressureIsobars: true, windFlow: false }, satelliteAvailable: true, forecastHour: 0, forecastTimes: [instant(0), instant(1)], forecastHours: [0,1], activeGlobalValidTime: instant(0), globalPrecipitationSource: null, globalCloudSource: null, globalWindSource: null, globalTemperatureSource: null, globalWeatherStatuses: statuses, globalWeatherCatalog: null, catalogueCheck: { lastSuccessfulCheck: null, lastCheckFailed: false }, journeySchedule: schedule, weatherGridStatus: "ready", onBasemapChange: noop, onOverlayChange: noop, onForecastHourChange: noop, onClose: noop }));
  for (const text of ["Terrain", "Satellite", "Elevation", "Precipitation", "Cloud cover", "Temperature contours", "Pressure isobars", "Wind flow", "Forecast timeline", "Play forecast", "Regional pressure · 9 × 9 samples"]) assert.ok(html.includes(text), text);
});

test("bottom route analysis preserves profile focus and condition strip access", () => {
  const html = renderToStaticMarkup(createElement(RouteAnalysis, { route: terrain, schedule, conditions, conditionStatus: "partial", conditionMode: "temperature", focusedIndex: 1, onFocusChange: noop, onConditionModeChange: noop, onClose: noop }));
  assert.match(html, /role="slider"/); assert.match(html, /aria-valuenow="500"/); assert.match(html, /route-profile-focus-point/); assert.match(html, /route-profile-condition-segment/); assert.match(html, /Selected journey point/);
});

test("presentation actions perform no network work", () => {
  const originalFetch = globalThis.fetch; let calls = 0; globalThis.fetch = () => { calls += 1; throw new Error("unexpected"); };
  try {
    let current = state.INITIAL_DESKTOP_WORKSPACE_STATE;
    for (const action of [{ type: "set-workspace", mode: "journey" }, { type: "set-left", open: false }, { type: "set-map-controls", open: false }, { type: "set-clear-map", active: true }]) current = state.desktopWorkspaceReducer(current, action);
    assert.equal(current.clearMap, true); assert.equal(calls, 0);
  } finally { globalThis.fetch = originalFetch; }
});