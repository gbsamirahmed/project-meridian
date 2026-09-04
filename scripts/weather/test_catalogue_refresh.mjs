import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
const refresh = await server.ssrLoadModule("/src/services/weatherCatalogueRefresh.ts");
const weather = await server.ssrLoadModule("/src/services/globalWeatherService.ts");
const freshness = await server.ssrLoadModule("/src/services/weatherFreshness.ts");
const FreshnessComponent = (await server.ssrLoadModule("/src/components/WeatherFreshness.tsx")).default;

const ids = weather.GLOBAL_WEATHER_FIELD_IDS;
const paths = { precipitation: "", cloud_cover: "cloud-cover", wind_10m: "wind-10m", temperature_2m: "temperature-2m", gust_surface: "gust-surface", visibility_surface: "visibility-surface", freezing_level: "freezing-level", highest_freezing_level: "highest-freezing-level", cloud_ceiling: "cloud-ceiling" };
function catalog(run = "2026-01-01T00:00:00Z") {
  const start = Date.parse(run); const runId = run.replaceAll("-", "").slice(0, 11) + "Z";
  return { schemaVersion: 2, model: "NOAA GFS", product: "pgrb2.0p25", generatedAt: new Date(start + 1000).toISOString(), fields: Object.fromEntries(ids.map(id => [id, { runTime: run, firstValidTime: new Date(start + 3600000).toISOString(), lastValidTime: new Date(start + 86400000).toISOString(), timestepCount: 24, manifest: [runId, paths[id], "manifest.json"].filter(Boolean).join("/") }])) };
}
function complete(value) {
  return { catalog: value, sources: Object.fromEntries(ids.map(id => [id, { manifest: { id: `${id}-${value.fields[id].runTime}` } }])) , statuses: Object.fromEntries(ids.map(id => [id, "ready"])) };
}
function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
class Visibility {
  constructor(state = "visible") { this.visibilityState = state; this.listeners = new Set(); }
  addEventListener(_type, listener) { this.listeners.add(listener); }
  removeEventListener(_type, listener) { this.listeners.delete(listener); }
  show() { this.visibilityState = "visible"; for (const listener of this.listeners) listener(); }
}

await test("initial catalogue parsing remains backward-compatible while refresh requires completeness", () => {
  const partial = weather.normaliseGlobalWeatherCatalog({ ...catalog(), fields: { precipitation: catalog().fields.precipitation } });
  assert.deepEqual(Object.keys(partial.fields), ["precipitation"]);
  assert.throws(() => refresh.completeCatalogueRunTime(partial), /all nine fields/);
  assert.equal(refresh.completeCatalogueRunTime(catalog()), Date.parse("2026-01-01T00:00:00Z"));
});

await test("catalogue polling is one cache-busted no-store metadata request", async () => {
  const priorWindow = globalThis.window; const priorFetch = globalThis.fetch; const calls = [];
  globalThis.window = { location: { href: "http://meridian.test/" } };
  globalThis.fetch = async (url, options) => { calls.push({ url: String(url), options }); return new Response(JSON.stringify(catalog()), { status: 200, headers: { "content-type": "application/json" } }); };
  try {
    const controller = new AbortController(); await weather.fetchGlobalWeatherCatalog(controller.signal);
    assert.equal(calls.length, 1); assert.match(calls[0].url, /weather\/gfs\/latest\.json\?checked=\d+/);
    assert.equal(calls[0].options.cache, "no-store"); assert.equal(calls[0].options.signal, controller.signal);
  } finally { globalThis.window = priorWindow; globalThis.fetch = priorFetch; }
});

await test("identical and older pointers stop before immutable manifests are requested", async () => {
  const current = catalog("2026-01-01T06:00:00Z"); let loads = 0;
  for (const [candidate, kind] of [[catalog("2026-01-01T06:00:00Z"), "identical"], [catalog(), "older"]]) {
    const result = await refresh.refreshGlobalWeatherCatalogue(current, new AbortController().signal, { fetchCatalog: async () => candidate, loadSources: async () => { loads++; return complete(candidate); } });
    assert.equal(result.kind, kind);
  }
  assert.equal(loads, 0);
});

await test("newer complete catalogue is adopted only after all manifests load", async () => {
  const current = catalog(); const candidate = catalog("2026-01-01T06:00:00Z"); let loaded = false;
  const result = await refresh.refreshGlobalWeatherCatalogue(current, new AbortController().signal, { fetchCatalog: async () => candidate, loadSources: async () => { loaded = true; return complete(candidate); } });
  assert.equal(loaded, true); assert.equal(result.kind, "adopted"); assert.equal(result.value.catalog, candidate);
});

await test("malformed or failed refresh retains the current value", async () => {
  const current = catalog(); const malformed = { ...catalog("2026-01-01T06:00:00Z"), fields: {} };
  await assert.rejects(refresh.refreshGlobalWeatherCatalogue(current, new AbortController().signal, { fetchCatalog: async () => malformed, loadSources: async () => complete(malformed) }), /all nine/);
  await assert.rejects(refresh.refreshGlobalWeatherCatalogue(current, new AbortController().signal, { fetchCatalog: async () => { throw new Error("offline"); }, loadSources: async value => complete(value) }), /offline/);
  await assert.rejects(refresh.refreshGlobalWeatherCatalogue(current, new AbortController().signal, { fetchCatalog: async () => catalog("2026-01-01T06:00:00Z"), loadSources: async () => { throw new Error("manifest unavailable"); } }), /manifest unavailable/);
  assert.equal(current.fields.precipitation.runTime, "2026-01-01T00:00:00Z");
});

await test("watcher prevents overlap and keeps current visuals while metadata is pending", async () => {
  const current = catalog(); const gate = deferred(); let calls = 0, adoptions = 0;
  const activeSources = { retained: true };
  const watcher = new refresh.GlobalWeatherCatalogueWatcher(current, () => adoptions++, () => {}, { intervalMs: 1e9, timeoutMs: 1e9, dependencies: { fetchCatalog: async () => { calls++; return gate.promise; }, loadSources: async value => complete(value) } });
  watcher.start(); const first = watcher.check(); const second = watcher.check();
  assert.equal(calls, 1); assert.equal(activeSources.retained, true); assert.equal(adoptions, 0);
  gate.resolve(catalog()); await Promise.all([first, second]);
  assert.equal(calls, 1); assert.equal(adoptions, 0); watcher.stop();
});

await test("becoming visible triggers one immediate check", async () => {
  const visible = new Visibility("hidden"); let calls = 0;
  const watcher = new refresh.GlobalWeatherCatalogueWatcher(catalog(), () => {}, () => {}, { visibility: visible, intervalMs: 1e9, timeoutMs: 1e9, dependencies: { fetchCatalog: async () => { calls++; return catalog(); }, loadSources: async value => complete(value) } });
  watcher.start(); assert.equal(calls, 0); visible.show(); await new Promise(resolve => setTimeout(resolve, 0));
  assert.equal(calls, 1); watcher.stop();
});

await test("a stale asynchronous result cannot replace a newer current catalogue", async () => {
  const load = deferred(); const candidate = catalog("2026-01-01T06:00:00Z"); let adoptions = 0;
  const watcher = new refresh.GlobalWeatherCatalogueWatcher(catalog(), () => adoptions++, () => {}, { intervalMs: 1e9, timeoutMs: 1e9, dependencies: { fetchCatalog: async () => candidate, loadSources: async () => load.promise } });
  watcher.start(); const pending = watcher.check(); await Promise.resolve(); watcher.setCurrent(catalog("2026-01-01T12:00:00Z"));
  load.resolve(complete(candidate)); await pending; assert.equal(adoptions, 0); watcher.stop();
});

await test("failed watcher check reports failure without adoption", async () => {
  let adopted = false; const checks = [];
  const watcher = new refresh.GlobalWeatherCatalogueWatcher(catalog(), () => { adopted = true; }, state => checks.push(state), { intervalMs: 1e9, timeoutMs: 1e9, dependencies: { fetchCatalog: async () => { throw new Error("offline"); }, loadSources: async value => complete(value) } });
  watcher.start(); await watcher.check(); assert.equal(adopted, false); assert.equal(checks.at(-1).lastCheckFailed, true); watcher.stop();
});

await test("catalogue swap retains an exact selected time or advances into the new horizon", () => {
  const times = ["2026-01-01T07:00:00Z", "2026-01-01T08:00:00Z", "2026-01-01T09:00:00Z"];
  assert.equal(refresh.catalogueForecastIndex(times, times[1], Date.parse(times[0])), 1);
  assert.equal(refresh.catalogueForecastIndex(times, "2026-01-01T01:00:00Z", Date.parse("2026-01-01T07:30:00Z")), 1);
  assert.equal(refresh.catalogueForecastIndex(times, null, Date.parse("2026-01-01T12:00:00Z")), 2);
});

await test("freshness is based on usable coverage and journey horizon", () => {
  const value = catalog(); const checked = { lastSuccessfulCheck: "2026-01-01T12:34:00Z", lastCheckFailed: false };
  assert.equal(freshness.weatherFreshnessPresentation(value, checked, null, Date.parse("2026-01-01T12:00:00Z")).tone, "current");
  const ending = freshness.weatherFreshnessPresentation(value, checked, null, Date.parse("2026-01-01T22:30:00Z"));
  assert.equal(ending.tone, "ending"); assert.match(ending.detail, /coverage ends in/i);
  const expired = freshness.weatherFreshnessPresentation(value, checked, null, Date.parse("2026-01-02T02:00:00Z"));
  assert.equal(expired.tone, "expired"); assert.match(expired.detail, /coverage ended/i);
  const journey = { departureTime: "2026-01-01T12:00:00Z", expectedFinishTime: "2026-01-02T03:00:00Z" };
  assert.match(freshness.weatherFreshnessPresentation(value, checked, journey, Date.parse("2026-01-01T12:00:00Z")).detail, /Journey extends/);
  const failed = freshness.weatherFreshnessPresentation(value, { ...checked, lastCheckFailed: true }, null, Date.parse("2026-01-01T12:00:00Z"));
  assert.match(failed.detail, /active run was retained/); assert.match(failed.label, /GFS .* 00Z · checked/);
});

await test("compact freshness UI exposes the active run and coverage state", () => {
  const run = new Date(Date.now() - 6 * 60 * 60 * 1000); run.setUTCMinutes(0, 0, 0); run.setUTCHours(Math.floor(run.getUTCHours() / 6) * 6);
  const html = renderToStaticMarkup(React.createElement(FreshnessComponent, { catalog: catalog(run.toISOString().replace(".000Z", "Z")), check: { lastSuccessfulCheck: new Date().toISOString(), lastCheckFailed: false }, journey: null }));
  assert.match(html, /weather-freshness-current/); assert.match(html, /GFS .*Z .* checked/); assert.match(html, /Forecast coverage/);
});

await server.close();
