import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";

const server = await createServer({
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});
const conditions = await server.ssrLoadModule("/src/services/routeConditions.ts");
const styles = await server.ssrLoadModule("/src/services/routeConditionStyle.ts");

test.after(async () => server.close());

function scalarSource(fieldId = "temperature_2m", timeSemantics = "instantaneous") {
  return {
    manifestUrl: "https://example.test/manifest.json",
    baseUrl: "https://example.test/run/temperature/",
    manifest: {
      schemaVersion: 2,
      id: `gfs-${fieldId}`,
      model: "GFS",
      product: "pgrb2.0p25",
      runTime: "2026-09-02T00:00:00Z",
      coverage: {
        bounds: [-180, -85.05112878, 180, 85.05112878],
        worldWrap: true,
        polarLimit: "Web Mercator",
      },
      attribution: { label: "NOAA GFS", url: "https://example.test", source: "NOAA" },
      generatedAt: "2026-09-02T01:00:00Z",
      field: {
        id: fieldId,
        kind: "scalar",
        sourceParameter: fieldId === "temperature_2m" ? "TMP" : "APCP",
        sourceLevel: fieldId === "temperature_2m" ? "2 m above ground" : "surface",
        displayName: fieldId,
        units: fieldId === "temperature_2m" ? "celsius" : "mm",
        validRange: fieldId === "temperature_2m" ? [-150, 100] : [0, 655.34],
        timeSemantics,
        nativeResolution: { longitudeDegrees: 0.25, latitudeDegrees: 0.25 },
      },
      tiles: {
        format: "png",
        encoding: "uint16-rg",
        tileSize: 256,
        minZoom: 0,
        maxZoom: 3,
        scale: 0.1,
        offset: -150,
        noData: 65535,
        resampling: "bilinear",
        overzoom: true,
      },
      timesteps: [],
    },
  };
}

function vectorSource() {
  return {
    manifestUrl: "https://example.test/wind/manifest.json",
    baseUrl: "https://example.test/run/wind/",
    manifest: {
      schemaVersion: 2,
      id: "gfs-wind",
      model: "GFS",
      product: "pgrb2.0p25",
      runTime: "2026-09-02T00:00:00Z",
      coverage: {
        bounds: [-180, -85.05112878, 180, 85.05112878],
        worldWrap: true,
        polarLimit: "Web Mercator",
      },
      attribution: { label: "NOAA GFS", url: "https://example.test", source: "NOAA" },
      generatedAt: "2026-09-02T01:00:00Z",
      field: {
        id: "wind_10m",
        kind: "vector",
        sourceLevel: "10 m above ground",
        displayName: "Wind",
        units: "m/s",
        timeSemantics: "instantaneous",
        vectorConvention: "earth-relative-eastward-northward",
        nativeResolution: { longitudeDegrees: 0.25, latitudeDegrees: 0.25 },
        components: [
          { id: "u", sourceParameter: "UGRD", role: "eastward" },
          { id: "v", sourceParameter: "VGRD", role: "northward" },
        ],
      },
      tiles: {
        format: "png",
        encoding: "packed-uv10-rgb",
        tileSize: 256,
        minZoom: 0,
        maxZoom: 3,
        componentScale: 0.2,
        componentBias: 511,
        componentBits: 10,
        noDataCode: 0,
        noDataRgb: [0, 0, 0],
        resampling: "bilinear",
        overzoom: true,
      },
      timesteps: [],
    },
  };
}

function scalarStep(hour, extra = {}) {
  const validTime = `2026-09-02T${String(hour).padStart(2, "0")}:00:00Z`;
  return {
    id: `f${String(hour).padStart(3, "0")}`,
    forecastHour: hour,
    validTime,
    minimum: 0,
    maximum: 10,
    tileTemplate: `f${hour}/{z}/{x}/{y}.png`,
    ...extra,
  };
}

function vectorStep(hour) {
  return {
    id: `f${String(hour).padStart(3, "0")}`,
    forecastHour: hour,
    validTime: `2026-09-02T${String(hour).padStart(2, "0")}:00:00Z`,
    minimumU: -10,
    maximumU: 10,
    minimumV: -10,
    maximumV: 10,
    minimumSpeed: 0,
    maximumSpeed: 15,
    tileTemplate: `f${hour}/{z}/{x}/{y}.png`,
  };
}

test("instantaneous selection is exact, nearest with earlier tie, and bounded", () => {
  const steps = [scalarStep(1), scalarStep(3), scalarStep(4)];
  assert.equal(
    conditions.selectInstantaneousTimestep(steps, "2026-09-02T03:00:00Z").id,
    "f003"
  );
  assert.equal(
    conditions.selectInstantaneousTimestep(steps, "2026-09-02T02:00:00Z").id,
    "f001"
  );
  assert.equal(
    conditions.selectInstantaneousTimestep(steps, "2026-09-02T03:40:00Z").id,
    "f004"
  );
  assert.equal(
    conditions.selectInstantaneousTimestep(steps, "2026-09-01T23:00:00Z"),
    null
  );
  assert.equal(
    conditions.selectInstantaneousTimestep(steps, "2026-09-02T05:00:00Z"),
    null
  );
});

test("precipitation selects the containing accumulation interval without interpolation", () => {
  const steps = [
    scalarStep(1, {
      accumulationStart: "2026-09-02T00:00:00Z",
      accumulationEnd: "2026-09-02T01:00:00Z",
      accumulationHours: 1,
    }),
    scalarStep(2, {
      accumulationStart: "2026-09-02T01:00:00Z",
      accumulationEnd: "2026-09-02T02:00:00Z",
      accumulationHours: 1,
    }),
    scalarStep(4, {
      accumulationStart: "2026-09-02T03:00:00Z",
      accumulationEnd: "2026-09-02T04:00:00Z",
      accumulationHours: 1,
    }),
  ];
  assert.equal(
    conditions.selectPrecipitationTimestep(steps, "2026-09-02T01:00:00Z").id,
    "f001"
  );
  assert.equal(
    conditions.selectPrecipitationTimestep(steps, "2026-09-02T01:30:00Z").id,
    "f002"
  );
  assert.equal(
    conditions.selectPrecipitationTimestep(steps, "2026-09-02T02:30:00Z"),
    null
  );
  assert.equal(
    conditions.selectPrecipitationTimestep(steps, "2026-09-02T00:00:00Z"),
    null
  );
});

test("route bearings are stable at starts, ends, cardinal directions and antimeridian", () => {
  const north = [
    { latitude: 50, longitude: 0 },
    { latitude: 50.01, longitude: 0 },
    { latitude: 50.02, longitude: 0 },
  ];
  assert.ok(Math.abs(conditions.routeBearingDegrees(north, 0)) < 0.01);
  assert.ok(Math.abs(conditions.routeBearingDegrees(north, 2)) < 0.01);
  const east = [
    { latitude: 0, longitude: 0 },
    { latitude: 0, longitude: 0.01 },
  ];
  assert.ok(Math.abs(conditions.routeBearingDegrees(east, 0) - 90) < 0.01);
  const west = [...east].reverse();
  assert.ok(Math.abs(conditions.routeBearingDegrees(west, 1) - 270) < 0.01);
  const crossing = [
    { latitude: 0, longitude: 179.99 },
    { latitude: 0, longitude: -179.99 },
  ];
  assert.ok(Math.abs(conditions.routeBearingDegrees(crossing, 0) - 90) < 0.01);
});

test("route-relative wind preserves U/V and uses positive along-route as tailwind", () => {
  const headwind = conditions.deriveRouteRelativeWind(0, -5, 0);
  assert.equal(headwind.headwindMs, 5);
  assert.equal(headwind.tailwindMs, 0);
  const tailwind = conditions.deriveRouteRelativeWind(0, 6, 0);
  assert.equal(tailwind.alongRouteMs, 6);
  assert.equal(tailwind.tailwindMs, 6);
  const fromLeft = conditions.deriveRouteRelativeWind(4, 0, 0);
  assert.equal(fromLeft.crosswindMs, 4);
  assert.equal(fromLeft.crosswindFrom, "left");
  const fromRight = conditions.deriveRouteRelativeWind(-4, 0, 0);
  assert.equal(fromRight.crosswindFrom, "right");
  const calm = conditions.deriveRouteRelativeWind(0.01, 0.01, 0);
  assert.equal(calm.crosswindFrom, "calm");
  assert.equal(conditions.deriveRouteRelativeWind(2, 2, null), null);
});

test("condition resolution preserves valid zero, missing states and actual valid time", () => {
  const source = scalarSource();
  const step = scalarStep(2);
  const requested = "2026-09-02T01:40:00Z";
  const zero = conditions.resolvedScalarCondition(source, step, requested, 0);
  assert.equal(zero.state, "available");
  assert.equal(zero.value, 0);
  assert.equal(zero.provenance.validTime, step.validTime);
  assert.equal(zero.provenance.requestedTime, requested);
  assert.equal(zero.provenance.temporalOffsetMinutes, 20);
  assert.equal(
    conditions.resolvedScalarCondition(source, step, requested, null).reason,
    "no-data"
  );
  assert.equal(
    conditions.resolvedScalarCondition(source, step, requested, undefined).reason,
    "tile-unavailable"
  );
  assert.equal(
    conditions.resolvedScalarCondition(null, null, requested, undefined).reason,
    "source-unavailable"
  );
  assert.equal(
    conditions.resolvedScalarCondition(source, null, requested, undefined).reason,
    "outside-forecast"
  );
});

test("wind resolution preserves calm zero vector and provenance", () => {
  const source = vectorSource();
  const step = vectorStep(3);
  const result = conditions.resolvedWindCondition(
    source,
    step,
    "2026-09-02T02:45:00Z",
    { u: 0, v: 0 },
    90
  );
  assert.equal(result.state, "available");
  assert.equal(result.speedMs, 0);
  assert.equal(result.directionFromDegrees, null);
  assert.equal(result.relative.tailwindMs, 0);
  assert.equal(result.provenance.temporalOffsetMinutes, 15);
});

test("summary and presentation retain partial availability and gradient without weather", () => {
  const available = (value, units = "celsius") => ({
    state: "available",
    value,
    units,
    provenance: {
      fieldId: "temperature_2m",
      model: "GFS",
      product: "pgrb2.0p25",
      runTime: "2026-09-02T00:00:00Z",
      sourceLevel: "2 m above ground",
      requestedTime: "2026-09-02T01:00:00Z",
      validTime: "2026-09-02T01:00:00Z",
      forecastHour: 1,
      temporalOffsetMinutes: 0,
      timeSemantics: "instantaneous",
    },
  });
  const missing = {
    state: "unavailable",
    requestedTime: "2026-09-02T01:00:00Z",
    reason: "no-data",
  };
  const sample = {
    routeSampleIndex: 0,
    coordinate: { latitude: 0, longitude: 0 },
    cumulativeDistanceM: 0,
    routeProgress: 0,
    routeBearingDegrees: 0,
    terrain: { elevationM: 100, gradient: 0.12 },
    journey: {
      movingElapsedMinutes: 0,
      stoppedElapsedMinutes: 0,
      elapsedMinutes: 0,
      expectedArrivalTime: "2026-09-02T01:00:00Z",
      earliestArrivalTime: "2026-09-02T01:00:00Z",
      latestArrivalTime: "2026-09-02T01:00:00Z",
    },
    weather: {
      temperature: available(0),
      precipitation: available(0, "mm"),
      cloud: missing,
      wind: missing,
    },
  };
  const summary = conditions.buildRouteConditionSummary([sample]);
  assert.deepEqual(summary.temperatureRangeC, [0, 0]);
  assert.equal(summary.precipitationMaximumMm, 0);
  assert.equal(summary.precipitationEncountered, false);
  assert.equal(summary.windMaximumMs, null);
  assert.notEqual(styles.routeConditionColour(sample, "gradient"), "#7b8581");
  assert.equal(styles.routeConditionColour(sample, "wind"), "#7b8581");
});
