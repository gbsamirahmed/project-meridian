import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
const d = await server.ssrLoadModule("/src/services/derivedRouteConditions.ts");
const f = await server.ssrLoadModule("/src/services/derivedConditionFormatting.ts");
const route = await server.ssrLoadModule("/src/services/routeConditions.ts");
const Profile = (await server.ssrLoadModule("/src/components/RouteProfile.tsx")).default;
const Context = (await server.ssrLoadModule("/src/components/DerivedConditionContext.tsx")).default;
test.after(() => server.close());
const time = "2026-01-01T01:00:00Z";
const missing = () => ({ state: "unavailable", reason: "outside-forecast", requestedTime: time });
const scalar = (value, units = "gpm", reference = "mean-sea-level") => ({
  state: "available", value, units,
  provenance: { model: "NOAA GFS", product: "pgrb2.0p25", runTime: "2026-01-01T00:00:00Z", validTime: time,
    requestedTime: time, sourceLevel: "synthetic", units, verticalReference: reference, nativeResolutionDegrees: 0.25, forecastHour: 1, temporalOffsetMinutes: 0, timeSemantics: "instantaneous" },
});
function sample(separation = 0, index = 0) {
  const stamp = new Date(Date.parse(time) + index * 60000).toISOString();
  return { routeSampleIndex: index, cumulativeDistanceM: index * 40, routeProgress: index / 10,
    coordinate: { longitude: 0, latitude: 0 }, routeBearingDegrees: 0,
    terrain: { elevationM: d.geopotentialToAltitudeM(1000) + separation, gradient: 0 },
    journey: { expectedArrivalTime: stamp, earliestArrivalTime: stamp, latestArrivalTime: stamp, elapsedMinutes: index },
    weather: { freezingLevel: scalar(1000), highestFreezingLevel: scalar(1000), gust: scalar(10, "m/s", "surface"),
      visibility: scalar(900, "m", "surface"), cloudCeiling: scalar(500, "gpm", "model-surface"),
      cloud: scalar(80, "percent", "surface"), temperature: scalar(0, "celsius", "surface"), precipitation: scalar(0, "mm", "surface"),
      wind: { state: "available", speedMs: 5, uMs: 0, vMs: 5, directionFromDegrees: 180,
        relative: route.deriveRouteRelativeWind(0, 5, 0), provenance: scalar(0).provenance } },
  };
}
const build = raw => d.buildDerivedRouteConditions("synthetic", raw);
const crossings = raw => build(raw).events.filter(e => e.kind === "freezing-crossing");

test("geopotential conversion is explicit, bounded and zero preserving", () => {
  assert.equal(d.geopotentialToAltitudeM(0), 0);
  assert.ok(Math.abs(d.geopotentialToAltitudeM(1000) - 1000.157) < 0.001);
  assert.ok(d.geopotentialToAltitudeM(7600) - 7600 < 10);
  assert.ok(d.geopotentialToAltitudeM(-100) < 0);
  assert.ok(Number.isNaN(d.geopotentialToAltitudeM(Infinity)));
  assert.ok(Number.isNaN(d.geopotentialToAltitudeM(40000)));
});
test("below, above and inclusive near band retain signed separation", () => {
  for (const [height, expected] of [[-250,"below"],[-100,"near"],[0,"near"],[100,"near"],[150,"above"]]) {
    const result = d.deriveFreezing(sample(height));
    assert.equal(result.position, expected);
    assert.ok(Math.abs(result.separationM - height) < 1e-9);
  }
  assert.equal(f.freezingContextLabel(d.deriveFreezing(sample(-250))), "~250 m below forecast 0°C level");
});
test("unavailable or incompatible heights never become sea-level zero", () => {
  const s = sample(); s.weather.freezingLevel = missing();
  assert.equal(d.deriveFreezing(s).state, "unavailable");
  s.weather.freezingLevel = scalar(1000, "gpm", "model-surface");
  assert.equal(d.deriveFreezing(s).reason, "incompatible-reference");
  s.weather.freezingLevel = scalar(0); s.weather.highestFreezingLevel = scalar(0); s.terrain.elevationM = 0;
  assert.equal(d.deriveFreezing(s).position, "near");
  assert.equal(d.deriveFreezing(s).altitudeM, 0);
  s.terrain.elevationM = null;
  assert.equal(d.deriveFreezing(s).state, "unavailable");
});
test("separate highest level and inconsistent/time-mismatched evidence remain explicit", () => {
  const s = sample(); s.weather.highestFreezingLevel = scalar(1400);
  const result = d.deriveFreezing(s);
  assert.equal(result.structure, "multiple-levels-indicated");
  assert.ok(result.highestAltitudeM > result.altitudeM + 399);
  assert.equal(s.weather.highestFreezingLevel.value, 1400);
  s.weather.highestFreezingLevel = scalar(900);
  assert.equal(d.deriveFreezing(s).structure, "inconsistent-levels");
  s.weather.highestFreezingLevel = scalar(1400);
  s.weather.highestFreezingLevel.provenance.validTime = "2026-01-01T02:00:00Z";
  assert.equal(d.deriveFreezing(s).structure, "unknown");
  s.weather.highestFreezingLevel = missing();
  assert.equal(d.deriveFreezing(s).state, "available");
  assert.equal(d.deriveFreezing(s).highestAltitudeM, null);
});
test("freezing structure threshold boundaries are physical, not code equality", () => {
  const s = sample(); s.weather.freezingLevel = scalar(0); s.weather.highestFreezingLevel = scalar(99);
  assert.equal(d.deriveFreezing(s).structure, "no-separated-levels-indicated");
  s.weather.highestFreezingLevel = scalar(100);
  assert.equal(d.deriveFreezing(s).structure, "multiple-levels-indicated"); // spherical correction puts it just beyond 100 m
});
test("exact zero crossing uses that sample, and noise inside the near band is suppressed", () => {
  let raw = [-200, 0, 200].map(sample);
  assert.equal(crossings(raw).length, 1);
  assert.equal(crossings(raw)[0].approximateDistanceM, 40);
  assert.equal(crossings(raw)[0].direction, "above");
  raw = [-200, -5, 5, -8, 10, 200, 4, -4, 5, -10, -200].map(sample);
  assert.deepEqual(crossings(raw).map(e => e.direction), ["above", "below"]);
  assert.equal(crossings([-50, 50, -40, 30].map(sample)).length, 0);
});
test("crossings do not bridge gaps or ambiguous freezing structures", () => {
  const raw = [-200, 0, 200].map(sample);
  raw[1].weather.freezingLevel = missing();
  assert.equal(crossings(raw).length, 0);
  raw[1] = sample(0, 1); raw[1].weather.highestFreezingLevel = scalar(2000);
  assert.equal(crossings(raw).length, 0);
  raw[1].weather.highestFreezingLevel = missing();
  assert.equal(crossings(raw).length, 0);
});
test("crossing at a forecast step change is bracketed, never interpolated weather", () => {
  const raw = [-200, 200].map(sample);
  raw[1].weather.freezingLevel.provenance.validTime = "2026-01-01T02:00:00Z";
  raw[1].weather.highestFreezingLevel.provenance.validTime = "2026-01-01T02:00:00Z";
  const event = crossings(raw)[0];
  assert.equal(event.fromSampleIndex, 0); assert.equal(event.toSampleIndex, 1);
  assert.equal(event.approximateDistanceM, 20);
  assert.ok(f.crossingLabel(event).includes("around"));
});
test("wind signs preserve head/tail and crosswind FROM left/right", () => {
  for (const [u, v, expected] of [[0,-5,"headwind"],[0,5,"tailwind"],[5,0,"crosswind-left"],[-5,0,"crosswind-right"],[5,5,"mixed"]]) {
    const s = sample(); s.weather.wind.relative = route.deriveRouteRelativeWind(u,v,0); s.weather.wind.speedMs = Math.hypot(u,v);
    assert.equal(d.deriveConditionSample(s).wind.orientation, expected);
  }
  const bearing = route.routeBearingDegrees([{ longitude: 179.9, latitude: 0 }, { longitude: -179.9, latitude: 0 }], 0);
  assert.ok(Math.abs(bearing - 90) < 1e-8);
  assert.ok(route.deriveRouteRelativeWind(5,0,bearing).tailwindMs > 4.99);
});
test("calm/light thresholds and unknown route bearing avoid false dominance", () => {
  const s = sample();
  for (const [speed, expected] of [[0,"calm"],[d.DERIVED_THRESHOLDS.calmMs - 1e-6,"calm"],[d.DERIVED_THRESHOLDS.calmMs,"light"],[1,"light"]]) {
    s.weather.wind.speedMs = speed; assert.equal(d.deriveConditionSample(s).wind.orientation, expected);
  }
  s.weather.wind.speedMs = 5; s.weather.wind.relative = null;
  assert.equal(d.deriveConditionSample(s).wind.orientation, "unknown");
});
test("gust excess is separate, signed, zero preserving and has no invented direction or ratio", () => {
  const s = sample();
  for (const [gust, excess] of [[10,5],[5,0],[0,-5]]) {
    s.weather.gust = scalar(gust, "m/s");
    const derived = d.deriveConditionSample(s).gust;
    assert.equal(derived.state, "available"); assert.equal(derived.excessMs, excess);
    assert.deepEqual(Object.keys(derived).sort(), ["excessMs","state"]);
  }
  s.weather.gust = missing(); assert.equal(d.deriveConditionSample(s).wind.state, "available");
  assert.equal(d.deriveConditionSample(s).gust.state, "unavailable");
  s.weather.gust = scalar(5, "m/s"); s.weather.wind = missing();
  assert.equal(d.deriveConditionSample(s).gust.state, "available"); assert.equal(d.deriveConditionSample(s).gust.excessMs, null);
});
test("gust excess is unavailable across different forecasts", () => {
  const s = sample(); s.weather.gust.provenance.validTime = "2026-01-01T02:00:00Z";
  assert.equal(d.deriveConditionSample(s).gust.excessMs, null);
});
test("Met Office visibility bands preserve raw zero, exact boundaries and saturated high values", () => {
  for (const [m, category] of [[0,"very-poor"],[999.9,"very-poor"],[1000,"poor"],[3703.9,"poor"],[3704,"moderate"],[9259,"moderate"],[9260,"good"],[24135,"good"]]) {
    assert.equal(d.visibilityCategory(m).category, category);
    assert.match(f.visibilityContextLabel(d.visibilityCategory(m)), /model visibility/);
  }
  assert.equal(d.visibilityCategory(NaN).state, "unavailable");
  assert.equal(d.visibilityCategory(-1).state, "unavailable");
});
test("ceiling is raw model-surface context; no-data does not disable visibility", () => {
  const s = sample(); s.weather.cloudCeiling = missing();
  assert.equal(d.deriveConditionSample(s).visibilityCloud.visibility.state, "available");
  assert.equal(d.deriveConditionSample(s).visibilityCloud.ceiling.state, "unavailable");
  s.weather.cloudCeiling = scalar(20000,"gpm","model-surface");
  assert.equal(d.deriveConditionSample(s).visibilityCloud.ceiling.state, "unavailable");
  s.weather.cloudCeiling = scalar(0,"gpm","model-surface");
  assert.deepEqual(d.deriveConditionSample(s).visibilityCloud.ceiling, { state: "available", reference: "model-surface", interpretation: "raw-only" });
  s.weather.cloudCeiling = scalar(500,"gpm","mean-sea-level");
  assert.equal(d.deriveConditionSample(s).visibilityCloud.ceiling.reason, "incompatible-reference");
});
test("visibility sections cluster contiguous samples, splitting at unavailable evidence", () => {
  const raw = Array.from({length:7}, (_,i) => sample(0,i));
  raw[2].weather.visibility = missing(); raw[5].weather.visibility = scalar(10000,"m");
  const events = build(raw).events.filter(e => e.kind === "poor-visibility-section");
  assert.deepEqual(events.map(e=>[e.fromSampleIndex,e.toSampleIndex]), [[0,1],[3,4],[6,6]]);
});
test("extrema and summaries use available evidence with explicit partial coverage", () => {
  const raw = [-200, 200, 300].map(sample);
  raw[0].weather.gust = scalar(0,"m/s"); raw[1].weather.gust = scalar(20,"m/s"); raw[2].weather.gust = missing();
  raw[0].weather.visibility = scalar(0,"m"); raw[2].weather.visibility = missing(); raw[2].weather.freezingLevel = missing();
  raw[1].weather.wind.relative = route.deriveRouteRelativeWind(12,-6,0);
  const result = build(raw);
  assert.equal(result.events.find(e=>e.kind === "peak-gust").fromSampleIndex,1);
  assert.equal(result.events.find(e=>e.kind === "strongest-crosswind").value,12);
  assert.equal(result.events.find(e=>e.kind === "strongest-headwind").value,6);
  assert.equal(result.events.find(e=>e.kind === "minimum-visibility").value,0);
  assert.deepEqual(result.coverage.freezing,{availableSamples:2,totalSamples:3});
  assert.equal(result.summary.aboveFreezingSamples,1);
  assert.match(f.freezingSummaryLabel(result), /2\/3 scheduled samples assessed/);
});
test("all-outside forecast is unavailable, not zero; other families fail independently", () => {
  const s = sample(); for(const key of Object.keys(s.weather)) s.weather[key] = missing();
  const result = build([s]);
  assert.equal(result.events.length,0);
  for (const coverage of Object.values(result.coverage)) assert.equal(coverage.availableSamples,0);
  assert.equal(f.freezingSummaryLabel(result),"Freezing context unavailable");
  s.weather.visibility = scalar(0,"m");
  assert.equal(build([s]).coverage.visibility.availableSamples,1);
  assert.equal(build([s]).coverage.freezing.availableSamples,0);
});
test("pure derivation does not mutate raw weather/schedule or request data", () => {
  const raw = [-300,0,300].map(sample); const copy = structuredClone(raw);
  const originalFetch = globalThis.fetch; globalThis.fetch = () => { throw new Error("No network allowed"); };
  try { assert.deepEqual(build(raw),build(raw)); } finally { globalThis.fetch = originalFetch; }
  assert.deepEqual(raw,copy);
  assert.deepEqual(build(raw).samples.map(s=>s.routeSampleIndex),[0,1,2]);
});
test("profile series retains sample indexes and unavailable holes", () => {
  const raw = [-300,0,300].map(sample); raw[1].weather.freezingLevel = missing();
  const result = build(raw); const series = d.freezingProfileSeries(raw,result);
  assert.deepEqual(series.map(s=>s.routeSampleIndex),[0,1,2]);
  assert.equal(series[1].altitudeM,null);
  result.samples[0].routeSampleIndex = 99;
  assert.equal(d.freezingProfileSeries(raw,result)[0].altitudeM,null);
});
test("SVG profile does not bridge unavailable forecast and preserves shared keyboard/touch focus", () => {
  const raw = [-300,0,300].map(sample); raw[1].weather.freezingLevel = missing();
  const terrain = { id:"synthetic",totalDistanceM:80,samples:raw.map(s=>({index:s.routeSampleIndex,cumulativeDistanceM:s.cumulativeDistanceM,smoothedElevationM:s.terrain.elevationM})) };
  const html = renderToStaticMarkup(createElement(Profile,{route:terrain,schedule:null,conditions:{routeId:"synthetic",samples:raw,derived:build(raw)},conditionMode:"none",focusedIndex:2,onFocusChange(){}}));
  const freezingPath = html.match(/<path d="([^"]*)" class="route-profile-freezing-line"/)[1];
  assert.equal((freezingPath.match(/M/g)||[]).length,2); assert.ok(!freezingPath.includes("L"));
  assert.ok(html.includes('role="slider"')); assert.ok(html.includes('tabindex="0"')); assert.ok(html.includes('aria-valuenow="80"'));
  assert.ok(html.includes("route-profile-focus-point")); assert.ok(html.includes("GFS 0.25°"));
});
test("derived inspector states evidence without false ice, snow, cloud-base or immersion claims", () => {
  const s=sample(150); s.weather.highestFreezingLevel=scalar(2000);
  const html=renderToStaticMarkup(createElement(Context,{raw:s,context:d.deriveConditionSample(s)}));
  assert.match(html,/150 m above forecast 0°C level/); assert.match(html,/Multiple freezing levels indicated/);
  assert.match(html,/Very poor model visibility/); assert.match(html,/Sustained/); assert.match(html,/gusts/);
  assert.ok(!/Cloud base|Expect ice|Icy|Expect snow|definitely in cloud|safe route/i.test(html));
});
