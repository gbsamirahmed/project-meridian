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
const numericTiles = await server.ssrLoadModule("/src/services/numericTileCache.ts");

test.after(async () => server.close());

function scalarSource(fieldId = "temperature_2m", timeSemantics = "instantaneous") {
  const isTemperature = fieldId === "temperature_2m";
  const isCloud = fieldId === "cloud_cover";
  return {
    manifestUrl: `https://example.test/run/${fieldId}/manifest.json`,
    baseUrl: `https://example.test/run/${fieldId}/`,
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
        sourceParameter: isTemperature ? "TMP" : isCloud ? "TCDC" : "APCP",
        sourceLevel: isTemperature
          ? "2 m above ground"
          : isCloud
            ? "entire atmosphere"
            : "surface",
        displayName: fieldId,
        units: isTemperature ? "celsius" : isCloud ? "percent" : "mm",
        validRange: isTemperature ? [-150, 100] : isCloud ? [0, 100] : [0, 655.34],
        timeSemantics,
        nativeResolution: { longitudeDegrees: 0.25, latitudeDegrees: 0.25 },
      },
      tiles: {
        format: "png",
        encoding: isCloud ? "uint8-r" : "uint16-rg",
        tileSize: 256,
        minZoom: 0,
        maxZoom: 3,
        scale: isTemperature ? 0.1 : isCloud ? 1 : 0.01,
        offset: isTemperature ? -150 : 0,
        noData: isCloud ? 255 : 65535,
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

function sourceSet(scope = "default") {
  const temperature = scalarSource("temperature_2m", "instantaneous");
  temperature.manifest.timesteps = [scalarStep(8), scalarStep(9)];
  const precipitation = scalarSource("precipitation", "interval-total");
  precipitation.manifest.timesteps = [
    scalarStep(8, {
      accumulationStart: "2026-09-02T07:00:00Z",
      accumulationEnd: "2026-09-02T08:00:00Z",
      accumulationHours: 1,
    }),
    scalarStep(9, {
      accumulationStart: "2026-09-02T08:00:00Z",
      accumulationEnd: "2026-09-02T09:00:00Z",
      accumulationHours: 1,
    }),
  ];
  const cloud = scalarSource("cloud_cover", "instantaneous");
  cloud.manifest.timesteps = [scalarStep(8), scalarStep(9)];
  const wind = vectorSource();
  wind.manifest.timesteps = [vectorStep(8), vectorStep(9)];
  const sources = { temperature, precipitation, cloud, wind };
  for (const [field, source] of Object.entries(sources)) {
    source.baseUrl = `https://example.test/${scope}/${field}/`;
    source.manifestUrl = `${source.baseUrl}manifest.json`;
  }
  return sources;
}

function syntheticRoute(sampleCount) {
  const samples = Array.from({ length: sampleCount }, (_, index) => ({
    index,
    longitude: -0.17 + index * 0.001,
    latitude: 51.5075,
    cumulativeDistanceM: index * 100,
    elevationM: 25,
    smoothedElevationM: 25,
    gradient: index === 0 ? 0 : 0.01,
    cumulativeAscentM: index,
    cumulativeDescentM: 0,
  }));
  return {
    id: "synthetic-route",
    name: "Synthetic route",
    samples,
    totalDistanceM: Math.max(0, (sampleCount - 1) * 100),
    totalAscentM: Math.max(0, sampleCount - 1),
    totalDescentM: 0,
    minimumElevationM: 25,
    maximumElevationM: 25,
    elevationCoverage: "complete",
  };
}

function syntheticSchedule(times) {
  const start = Date.parse(times[0]);
  return {
    routeId: "synthetic-route",
    departureTime: times[0],
    expectedFinishTime: times.at(-1),
    movingMinutes: (Date.parse(times.at(-1)) - start) / 60000,
    stoppedMinutes: 0,
    totalMinutes: (Date.parse(times.at(-1)) - start) / 60000,
    likelyMinimumMinutes: 0,
    likelyMaximumMinutes: 0,
    movementScale: 1,
    targetComparison: "close-to-baseline",
    samples: times.map((time, index) => ({
      routeSampleIndex: index,
      movingElapsedMinutes: (Date.parse(time) - start) / 60000,
      stoppedElapsedMinutes: 0,
      elapsedMinutes: (Date.parse(time) - start) / 60000,
      arrivalTime: time,
      earliestArrivalTime: time,
      latestArrivalTime: time,
    })),
  };
}

function constantPixels(url) {
  let red = 0;
  let green = 0;
  let blue = 0;
  if (url.includes("/temperature/")) {
    red = 5;
    green = 220; // (0 °C - -150 °C) / 0.1 = 1500
  } else if (url.includes("wind")) {
    red = 127;
    green = 223;
    blue = 240; // U and V both encode the zero-wind bias code 511.
  }
  const pixels = new Uint8ClampedArray(256 * 256 * 4);
  for (let offset = 0; offset < pixels.length; offset += 4) {
    pixels[offset] = red;
    pixels[offset + 1] = green;
    pixels[offset + 2] = blue;
    pixels[offset + 3] = 255;
  }
  return pixels;
}

async function withSyntheticNumericRuntime(run, options = {}) {
  const previousFetch = globalThis.fetch;
  const previousCreateImageBitmap = globalThis.createImageBitmap;
  const previousDocument = globalThis.document;
  const failingFragments = new Set(options.failingFragments ?? []);
  globalThis.fetch = async (input) => {
    const url = String(input);
    if ([...failingFragments].some((fragment) => url.includes(fragment))) {
      throw new Error("Synthetic tile failure");
    }
    if (options.delayMs) {
      await new Promise((resolve) => setTimeout(resolve, options.delayMs));
    }
    return {
      ok: true,
      status: 200,
      blob: async () => ({ url }),
    };
  };
  globalThis.createImageBitmap = async (blob) => ({
    url: blob.url,
    close() {},
  });
  globalThis.document = {
    createElement() {
      let activeUrl = "";
      return {
        width: 0,
        height: 0,
        getContext() {
          return {
            drawImage(bitmap) {
              activeUrl = bitmap.url;
            },
            getImageData() {
              return { data: constantPixels(activeUrl) };
            },
          };
        },
      };
    },
  };
  try {
    return await run({ failingFragments });
  } finally {
    globalThis.fetch = previousFetch;
    globalThis.createImageBitmap = previousCreateImageBitmap;
    globalThis.document = previousDocument;
  }
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
  sample.weather.precipitation = available(0.001, "mm");
  assert.equal(conditions.buildRouteConditionSummary([sample]).precipitationEncountered, true);
});

test("direct global source preparation and sampling preserves valid zero values", async () => {
  await withSyntheticNumericRuntime(async () => {
    const sources = sourceSet("direct-source");
    const coordinate = { longitude: -0.17, latitude: 51.5075 };
    const temperatureStep = sources.temperature.manifest.timesteps[0];
    const precipitationStep = sources.precipitation.manifest.timesteps[0];
    const cloudStep = sources.cloud.manifest.timesteps[0];
    const windStep = sources.wind.manifest.timesteps[0];

    await numericTiles.prepareScalarFieldCoordinates(
      sources.temperature,
      temperatureStep,
      [coordinate]
    );
    await numericTiles.prepareScalarFieldCoordinates(
      sources.precipitation,
      precipitationStep,
      [coordinate]
    );
    await numericTiles.prepareScalarFieldCoordinates(
      sources.cloud,
      cloudStep,
      [coordinate]
    );
    await numericTiles.prepareVectorFieldCoordinates(
      sources.wind,
      windStep,
      [coordinate]
    );

    assert.equal(
      numericTiles.sampleCachedScalarField(
        sources.temperature,
        temperatureStep,
        3,
        coordinate.longitude,
        coordinate.latitude
      ),
      0
    );
    assert.equal(
      numericTiles.sampleCachedScalarField(
        sources.precipitation,
        precipitationStep,
        3,
        coordinate.longitude,
        coordinate.latitude
      ),
      0
    );
    assert.equal(
      numericTiles.sampleCachedScalarField(
        sources.cloud,
        cloudStep,
        3,
        coordinate.longitude,
        coordinate.latitude
      ),
      0
    );
    assert.deepEqual(
      numericTiles.sampleCachedVectorField(
        sources.wind,
        windStep,
        3,
        coordinate.longitude,
        coordinate.latitude
      ),
      { u: 0, v: 0 }
    );
  });
});

test("a short in-horizon route resolves every field and expected-arrival provenance", async () => {
  await withSyntheticNumericRuntime(async () => {
    const times = [
      "2026-09-02T08:00:00Z",
      "2026-09-02T08:30:00Z",
      "2026-09-02T09:00:00Z",
    ];
    const result = await conditions.buildRouteConditions(
      syntheticRoute(times.length),
      syntheticSchedule(times),
      sourceSet("short-route")
    );
    for (const sample of result.samples) {
      assert.equal(sample.weather.temperature.state, "available");
      assert.equal(sample.weather.precipitation.state, "available");
      assert.equal(sample.weather.cloud.state, "available");
      assert.equal(sample.weather.wind.state, "available");
      assert.equal(sample.weather.temperature.value, 0);
      assert.equal(sample.weather.precipitation.value, 0);
      assert.equal(sample.weather.cloud.value, 0);
      assert.equal(sample.weather.wind.speedMs, 0);
      assert.equal(sample.weather.wind.relative.alongRouteMs, 0);
      assert.equal(sample.weather.wind.relative.crossRouteMs, 0);
      assert.equal(
        sample.weather.temperature.provenance.requestedTime,
        sample.journey.expectedArrivalTime
      );
    }
    assert.equal(result.coverage.temperature.availableSamples, times.length);
    assert.equal(result.coverage.precipitation.availableSamples, times.length);
    assert.deepEqual(result.summary.temperatureRangeC, [0, 0]);
    assert.equal(result.summary.precipitationEncountered, false);
    assert.equal(result.summary.windMaximumMs, 0);
  });
});

test("partial and entirely out-of-horizon routes retain sample-level availability", async () => {
  await withSyntheticNumericRuntime(async () => {
    const partialTimes = [
      "2026-09-02T08:00:00Z",
      "2026-09-02T08:30:00Z",
      "2026-09-02T10:00:00Z",
    ];
    const partial = await conditions.buildRouteConditions(
      syntheticRoute(partialTimes.length),
      syntheticSchedule(partialTimes),
      sourceSet("partial-route")
    );
    assert.equal(partial.samples[0].weather.temperature.state, "available");
    assert.equal(partial.samples[1].weather.temperature.state, "available");
    assert.equal(partial.samples[2].weather.temperature.state, "unavailable");
    assert.equal(
      partial.samples[2].weather.temperature.reason,
      "outside-forecast"
    );
    assert.equal(partial.coverage.temperature.availableSamples, 2);
    assert.notEqual(
      styles.routeConditionColour(partial.samples[0], "temperature"),
      "#7b8581"
    );
    assert.equal(
      styles.routeConditionColour(partial.samples[2], "temperature"),
      "#7b8581"
    );

    const outsideTimes = [
      "2026-09-02T10:00:00Z",
      "2026-09-02T11:00:00Z",
    ];
    const outside = await conditions.buildRouteConditions(
      syntheticRoute(outsideTimes.length),
      syntheticSchedule(outsideTimes),
      sourceSet("outside-route")
    );
    assert.equal(outside.coverage.temperature.availableSamples, 0);
    assert.equal(outside.coverage.precipitation.availableSamples, 0);
    assert.equal(outside.coverage.cloud.availableSamples, 0);
    assert.equal(outside.coverage.wind.availableSamples, 0);
  });
});

test("a missing precipitation interval and one unavailable field do not invalidate neighbours", async () => {
  await withSyntheticNumericRuntime(async () => {
    const sources = sourceSet("missing-step");
    sources.precipitation.manifest.timesteps = [
      scalarStep(8, {
        accumulationStart: "2026-09-02T07:00:00Z",
        accumulationEnd: "2026-09-02T08:00:00Z",
        accumulationHours: 1,
      }),
      scalarStep(10, {
        accumulationStart: "2026-09-02T09:00:00Z",
        accumulationEnd: "2026-09-02T10:00:00Z",
        accumulationHours: 1,
      }),
    ];
    const times = [
      "2026-09-02T07:30:00Z",
      "2026-09-02T08:30:00Z",
      "2026-09-02T09:30:00Z",
    ];
    const result = await conditions.buildRouteConditions(
      syntheticRoute(times.length),
      syntheticSchedule(times),
      { ...sources, cloud: null }
    );
    assert.equal(result.samples[0].weather.precipitation.state, "available");
    assert.equal(result.samples[1].weather.precipitation.state, "unavailable");
    assert.equal(result.samples[1].weather.precipitation.reason, "outside-forecast");
    assert.equal(result.samples[2].weather.precipitation.state, "available");
    assert.equal(result.coverage.precipitation.availableSamples, 2);
    assert.equal(result.coverage.cloud.availableSamples, 0);
  });
});

test("a failed field tile settles unavailable, preserves other fields, and can retry", async () => {
  const sources = sourceSet("failed-field");
  const route = syntheticRoute(1);
  const schedule = syntheticSchedule(["2026-09-02T08:00:00Z"]);
  await withSyntheticNumericRuntime(
    async () => {
      const failed = await conditions.buildRouteConditions(route, schedule, sources);
      assert.equal(failed.samples[0].weather.cloud.state, "unavailable");
      assert.equal(failed.samples[0].weather.cloud.reason, "tile-unavailable");
      assert.equal(failed.samples[0].weather.temperature.state, "available");
      assert.equal(failed.samples[0].weather.precipitation.state, "available");
      assert.equal(failed.samples[0].weather.wind.state, "available");
    },
    { failingFragments: ["/cloud/"] }
  );
  await withSyntheticNumericRuntime(async () => {
    const retried = await conditions.buildRouteConditions(route, schedule, sources);
    assert.equal(retried.samples[0].weather.cloud.state, "available");
    assert.equal(retried.samples[0].weather.cloud.value, 0);
  });
});

test("an aborted obsolete build cannot complete after a newer departure", async () => {
  const obsoleteSources = sourceSet("obsolete-build");
  const currentSources = sourceSet("current-build");
  const route = syntheticRoute(1);
  const obsoleteSchedule = syntheticSchedule(["2026-09-02T08:00:00Z"]);
  const currentSchedule = syntheticSchedule(["2026-09-02T09:00:00Z"]);
  await withSyntheticNumericRuntime(
    async () => {
      const controller = new AbortController();
      const obsolete = conditions.buildRouteConditions(
        route,
        obsoleteSchedule,
        obsoleteSources,
        controller.signal
      );
      controller.abort();
      await assert.rejects(obsolete, { name: "AbortError" });
    },
    { delayMs: 5 }
  );
  await withSyntheticNumericRuntime(async () => {
    const current = await conditions.buildRouteConditions(
      route,
      currentSchedule,
      currentSources
    );
    assert.equal(
      current.samples[0].weather.temperature.provenance.validTime,
      "2026-09-02T09:00:00Z"
    );
  });
});
