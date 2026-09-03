import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
const [numeric, route, globalWeather, atmospheric, format, routePanelModule] = await Promise.all([
  server.ssrLoadModule("/src/services/numericTileCache.ts"),
  server.ssrLoadModule("/src/services/routeConditions.ts"),
  server.ssrLoadModule("/src/services/globalWeatherService.ts"),
  server.ssrLoadModule("/src/services/atmosphericFields.ts"),
  server.ssrLoadModule("/src/services/atmosphericFormatting.ts"),
  server.ssrLoadModule("/src/components/RoutePlannerPanel.tsx"),
]);
const { ATMOSPHERIC_FIELDS, validateAtmosphericManifest } = atmospheric;
const RoutePlannerPanel = routePanelModule.default;
test.after(() => server.close());

const keys = { gust: "gust_surface", visibility: "visibility_surface", freezingLevel: "freezing_level", highestFreezingLevel: "highest_freezing_level", cloudCeiling: "cloud_ceiling" };
const encodings = { gust_surface: [0.1, 0, 200], visibility_surface: [10, 0, 100000], freezing_level: [5, -1000, 30000], highest_freezing_level: [5, -1000, 30000], cloud_ceiling: [5, -1000, 20001] };
const instant = hour => new Date(Date.UTC(2026, 0, 1, hour)).toISOString();
const sources = () => Object.fromEntries(Object.entries(keys).map(([key, id]) => {
  const [scale, offset, maximum] = encodings[id];
  return [key, {
    baseUrl: `https://example.test/${id}/`, manifestUrl: `https://example.test/${id}/manifest.json`,
    manifest: {
      schemaVersion: 2, id, model: "NOAA GFS", product: "pgrb2.0p25", runTime: instant(0),
      field: { id, kind: "scalar", ...ATMOSPHERIC_FIELDS[id], displayName: id, validRange: [offset, maximum],
        noDataMeaning: id === "cloud_ceiling" ? "missing-or-no-diagnosed-ceiling" : "missing",
        timeSemantics: "instantaneous", nativeResolution: { longitudeDegrees: 0.25, latitudeDegrees: 0.25 } },
      tiles: { format: "png", encoding: "uint16-rg", tileSize: 4, minZoom: 0, maxZoom: 0, scale, offset, noData: 65535, resampling: "bilinear", overzoom: true },
      coverage: { bounds: [-180, -85.05112878, 180, 85.05112878], worldWrap: true },
      timesteps: [1, 2, 3].map(hour => ({ id: `f00${hour}`, forecastHour: hour, validTime: instant(hour), minimum: 0, maximum, tileTemplate: `f00${hour}/{z}/{x}/{y}.png` })),
    },
  }];
}));

async function runtime(fn, pixel = () => 0, fail = () => false, delay = 0) {
  numeric.clearNumericTileCache();
  const originals = { fetch: globalThis.fetch, document: globalThis.document, createImageBitmap: globalThis.createImageBitmap };
  const requests = [];
  globalThis.fetch = async input => {
    const url = String(input); requests.push(url);
    if (delay) await new Promise(resolve => setTimeout(resolve, delay));
    if (fail(url)) throw new Error("Synthetic unavailable tile");
    return { ok: true, blob: async () => ({ url }) };
  };
  globalThis.createImageBitmap = async blob => ({ url: blob.url, close() {} });
  globalThis.document = { createElement: () => {
    let url;
    return { getContext: () => ({ drawImage(bitmap) { url = bitmap.url; }, getImageData() {
      const data = new Uint8ClampedArray(4 * 4 * 4);
      const id = new URL(url).pathname.split("/")[1];
      const [scale, offset] = encodings[id];
      for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
        const value = pixel(id, x, y, url);
        const code = value === null ? 65535 : Math.round((value - offset) / scale);
        const i = (y * 4 + x) * 4;
        data[i] = code >> 8; data[i + 1] = code & 255; data[i + 3] = 255;
      }
      return { data };
    } }) };
  } };
  try { await fn(requests); } finally { Object.assign(globalThis, originals); numeric.clearNumericTileCache(); }
}

function journey(times) {
  const terrain = { id: "synthetic", totalDistanceM: 100 * (times.length - 1), samples: times.map((_, index) => ({ index, longitude: 0, latitude: 0, cumulativeDistanceM: 100 * index, smoothedElevationM: 500, gradient: 0.1 })) };
  const schedule = { routeId: "synthetic", samples: times.map((arrivalTime, index) => ({ routeSampleIndex: index, arrivalTime, earliestArrivalTime: arrivalTime, latestArrivalTime: arrivalTime, movingElapsedMinutes: index, stoppedElapsedMinutes: 0, elapsedMinutes: index })) };
  return [terrain, schedule];
}
const routeSources = () => ({ temperature: null, precipitation: null, cloud: null, wind: null, ...sources() });

test("all five fields decode, bilinearly sample, wrap and retain zero independently", async () => {
  await runtime(async requests => {
    for (const source of Object.values(sources())) {
      validateAtmosphericManifest(source.manifest);
      const step = source.manifest.timesteps[0];
      await numeric.prepareScalarFieldCoordinates(source, step, [{ longitude: 0, latitude: 0 }, { longitude: 180, latitude: 0 }]);
      for (const longitude of [0, -180, 180, 540]) assert.equal(numeric.sampleCachedScalarField(source, step, 0, longitude, 0), 0);
      for (const latitude of [-85.05112878, 85.05112878]) assert.equal(numeric.sampleCachedScalarField(source, step, 0, 0, latitude), 0);
      assert.equal(numeric.sampleCachedScalarField(source, step, 0, 0, 90), null);
      assert.equal(await numeric.sampleScalarField(source, step, 0, 0), 0);
    }
    assert.equal(requests.length, 5);
    assert.equal(numeric.getNumericTileCacheStats().pendingCount, 0);
  });
  await runtime(async () => {
    for (const source of Object.values(sources())) {
      const step = source.manifest.timesteps[0];
      await numeric.prepareScalarFieldCoordinates(source, step, [{ longitude: 0, latitude: 0 }]);
      assert.ok(Math.abs(numeric.sampleCachedScalarField(source, step, 0, 0, 0) - 75) < 1e-8);
    }
  }, (_, x, y) => (x + y * 4) * 10);
});

test("raw no-data does not become a value or invalidate other fields", async () => {
  await runtime(async () => {
    const conditions = await route.buildRouteConditions(...journey([instant(1), instant(2)]), routeSources());
    for (const sample of conditions.samples) {
      assert.equal(sample.weather.cloudCeiling.reason, "no-data");
      assert.equal(sample.weather.gust.value, 0);
      assert.equal(sample.weather.visibility.units, "m");
      assert.equal(sample.weather.freezingLevel.units, "gpm");
      assert.equal(sample.weather.wind.state, "unavailable");
    }
    assert.equal(conditions.summary.gustMaximumMs, 0);
    assert.equal(conditions.summary.visibilityMinimumM, 0);
    assert.equal(conditions.coverage.cloudCeiling.availableSamples, 0);
  }, id => id === "cloud_ceiling" ? null : 0);
});

test("short in-horizon route, earlier ties, distinct freezing levels and grouped cache reuse", async () => {
  await runtime(async requests => {
    const args = journey([instant(1), "2026-01-01T01:30:00Z", instant(2)]);
    const result = await route.buildRouteConditions(...args, routeSources());
    for (const key of Object.keys(keys)) assert.equal(result.coverage[key].availableSamples, 3);
    assert.equal(result.samples[1].weather.gust.provenance.validTime, instant(1));
    assert.equal(result.samples[0].weather.freezingLevel.value, 1000);
    assert.equal(result.samples[0].weather.highestFreezingLevel.value, 2000);
    assert.equal(result.samples[0].weather.cloudCeiling.provenance.sourceLevel, "cloud ceiling");
    assert.equal(result.samples[0].weather.cloudCeiling.provenance.verticalReference, "model-surface");
    const count = requests.length;
    await route.buildRouteConditions(...args, routeSources());
    assert.equal(requests.length, count);
    assert.equal(count, 10); // five fields x two steps, not five x route points
  }, id => id === "freezing_level" ? 1000 : id === "highest_freezing_level" ? 2000 : 0);
});

test("partial horizon, missing timestep tile, departure changes and all-outside route", async () => {
  await runtime(async () => {
    const result = await route.buildRouteConditions(...journey([instant(1), instant(2), instant(3), instant(4)]), routeSources());
    assert.equal(result.samples[0].weather.visibility.state, "available");
    assert.equal(result.samples[1].weather.visibility.reason, "tile-unavailable");
    assert.equal(result.samples[2].weather.visibility.state, "available");
    assert.equal(result.samples[3].weather.gust.reason, "outside-forecast");
    assert.equal(result.coverage.visibility.availableSamples, 2);
    assert.equal(result.coverage.gust.availableSamples, 3);
    assert.equal(result.summary.visibilityMinimumM, 0);
    const outside = await route.buildRouteConditions(...journey([instant(0), instant(4)]), routeSources());
    for (const key of Object.keys(keys)) assert.equal(outside.coverage[key].availableSamples, 0);
    const later = await route.buildRouteConditions(...journey([instant(3)]), routeSources());
    assert.equal(later.samples[0].weather.gust.provenance.validTime, instant(3));
    assert.equal(numeric.getNumericTileCacheStats().pendingCount, 0);
  }, () => 0, url => url.includes("visibility_surface/f002"));
});

test("aborting an old route leaves shared fetches available to the new route", async () => {
  await runtime(async () => {
    const controller = new AbortController();
    const old = route.buildRouteConditions(...journey([instant(1)]), routeSources(), controller.signal);
    const rejected = assert.rejects(old, { name: "AbortError" });
    controller.abort();
    const current = await route.buildRouteConditions(...journey([instant(2)]), routeSources());
    await rejected;
    assert.equal(current.samples[0].weather.gust.provenance.validTime, instant(2));
    assert.equal(current.samples[0].weather.gust.state, "available");
    assert.equal(numeric.getNumericTileCacheStats().pendingCount, 0);
  }, () => 0, () => false, 5);
});

test("catalogue loads new fields independently; rejects wrong units/reference and malformed entries", async () => {
  const originals = { fetch: globalThis.fetch, window: globalThis.window };
  const set = sources();
  const fields = Object.fromEntries(Object.values(set).map(source => [source.manifest.field.id, { runTime: instant(0), firstValidTime: instant(1), lastValidTime: instant(3), timestepCount: 3, manifest: source.manifestUrl }]));
  const catalog = { schemaVersion: 2, model: "NOAA GFS", product: "pgrb2.0p25", generatedAt: instant(0), fields };
  globalThis.window = { location: { href: "https://example.test/" } };
  globalThis.fetch = async url => ({ ok: true, json: async () => String(url).endsWith("latest.json") ? catalog : Object.values(set).find(s => s.manifestUrl === url).manifest });
  try {
    const loaded = await globalWeather.loadGlobalWeatherSources();
    assert.equal(Object.keys(loaded.sources).length, 5);
    set.cloudCeiling.manifest.field.verticalReference = "mean-sea-level";
    set.visibility.manifest.field.units = "km";
    catalog.fields.highest_freezing_level = { bad: true };
    const partial = await globalWeather.loadGlobalWeatherSources();
    assert.equal(partial.statuses.gust_surface, "ready");
    assert.equal(partial.statuses.freezing_level, "ready");
    assert.equal(partial.statuses.cloud_ceiling, "error");
    assert.equal(partial.statuses.visibility_surface, "error");
    assert.equal(partial.statuses.highest_freezing_level, "unavailable");
  } finally { Object.assign(globalThis, originals); }
});

test("restrained formatting preserves zero, units and incomplete sample coverage", () => {
  assert.equal(format.gustLabel(10), "~36 km/h");
  assert.equal(format.gustLabel(0), "~0 km/h");
  assert.equal(format.visibilityLabel(0), "~0 m");
  assert.equal(format.visibilityLabel(120), "~120 m");
  assert.equal(format.visibilityLabel(2437), "~2.4 km");
  assert.equal(format.visibilityLabel(24135), "~24 km");
  assert.equal(format.atmosphericHeightLabel(1047), "~1050 m");
  assert.equal(format.atmosphericHeightLabel(713), "~700 m");
  assert.equal(format.atmosphericHeightLabel(0), "~0 m");
  assert.equal(format.fieldCoverageLabel({ availableSamples: 5, totalSamples: 5 }), "");
  assert.equal(format.fieldCoverageLabel({ availableSamples: 3, totalSamples: 5 }), "Partial forecast coverage");
});

test("atmospheric manifests reject fabricated times and incompatible encodings", () => {
  for (const change of [
    source => { source.manifest.timesteps[0].validTime = instant(2); },
    source => { source.manifest.tiles.scale = 0; },
    source => { source.manifest.tiles.offset = 1; },
    source => { source.manifest.timesteps[0].maximum = Infinity; },
    source => { source.manifest.field.timeSemantics = "interval-total"; },
  ]) {
    const source = sources().gust;
    change(source);
    assert.throws(() => validateAtmosphericManifest(source.manifest));
  }
});

test("inspector renders approximate raw atmospheric values without cloud-base or hazard claims", async () => {
  await runtime(async () => {
    const conditions = await route.buildRouteConditions(...journey([instant(1)]), routeSources());
    const noop = () => {};
    const html = renderToStaticMarkup(createElement(RoutePlannerPanel, {
      routeGeometry: { id: "synthetic", name: "Synthetic route", totalDistanceM: 1000 }, terrainRoute: null,
      schedule: null, scheduleError: null, status: "ready", statusMessage: null,
      profile: { activity: "walking", pace: "normal", party: "solo", load: "light", plannedBreakMinutes: 0 },
      plan: { mode: "profile", departureTime: instant(1) }, focusedIndex: 0,
      routeConditions: conditions, routeConditionStatus: "partial", routeConditionMode: "none",
      onImport: noop, onClear: noop, onProfileChange: noop, onPlanChange: noop,
      onFocusChange: noop, onRouteConditionModeChange: noop,
    }));
    for (const text of ["Gusts", "~0 km/h", "Model visibility", "~2.4 km", "0°C level", "~1050 m", "Cloud ceiling", "~700 m", "Highest tropospheric freezing level", "above the model surface", "GFS 0.25°"]) assert.ok(html.includes(text), text);
    assert.ok(!html.includes("Cloud base"));
    assert.ok(!html.includes("2437"));
    assert.ok(!html.includes("713 m"));
  }, id => id === "visibility_surface" ? 2430 : id === "freezing_level" ? 1045 : id === "cloud_ceiling" ? 715 : 0);
});
