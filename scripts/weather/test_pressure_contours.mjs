import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { createServer } from "vite";

const server = await createServer({
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});
const model = await server.ssrLoadModule("/src/services/pressureContourModel.ts");
const weather = await server.ssrLoadModule("/src/services/globalWeatherService.ts");
const pressureLayerSource = readFileSync(
  new URL("../../src/services/pressureLayer.ts", import.meta.url),
  "utf8"
);

test.after(async () => server.close());

test("pressure intervals remain conventional and readable across zooms", () => {
  assert.equal(model.choosePressureContourInterval(2, 40), 8);
  assert.equal(model.choosePressureContourInterval(6, 24), 4);
  assert.equal(model.choosePressureContourInterval(10, 6), 2);
  assert.equal(model.choosePressureContourInterval(10, 20), 4);
  assert.equal(model.choosePressureContourInterval(10, 0.8), null);
});

test("close globe-projection views do not trigger whole-Earth contour work", () => {
  assert.match(pressureLayerSource, /getProjection\(\)\?\.type === "globe" &&\s*map\.getZoom\(\) <= GLOBE_COVERAGE_ZOOM \+ 0\.5/);
  assert.match(pressureLayerSource, /signature: "globe-z2"/);
});

test("pressure manifest enforces the verified PRMSL physical and encoding contract", () => {
  const manifest = {
    schemaVersion: 2, id: "20260905T18Z-pressure-msl", model: "NOAA GFS", product: "pgrb2.0p25",
    runTime: "2026-09-05T18:00:00Z",
    field: { id: "pressure_msl", kind: "scalar", sourceParameter: "PRMSL", sourceLevel: "mean sea level",
      displayName: "Mean sea-level pressure", units: "hPa", verticalReference: "mean-sea-level",
      validRange: [800, 1200], timeSemantics: "instantaneous",
      nativeResolution: { longitudeDegrees: 0.25, latitudeDegrees: 0.25 } },
    coverage: { bounds: [-180, -85.05112878, 180, 85.05112878], worldWrap: true, polarLimit: "Web Mercator" },
    tiles: { format: "png", encoding: "uint16-rg", tileSize: 256, minZoom: 0, maxZoom: 3,
      scale: 0.1, offset: 800, noData: 65535, resampling: "bilinear", overzoom: true },
    timesteps: [{ id: "f001", forecastHour: 1, validTime: "2026-09-05T19:00:00Z", minimum: 980,
      maximum: 1032, tileTemplate: "f001/{z}/{x}/{y}.png" }],
    attribution: { label: "NOAA GFS", url: "https://www.noaa.gov/", source: "NOAA/NCEP GFS" },
    generatedAt: "2026-09-06T01:45:35Z",
  };
  assert.equal(weather.normaliseGlobalWeatherManifest(manifest).field.id, "pressure_msl");
  assert.throws(() => weather.normaliseGlobalWeatherManifest({ ...manifest, field: { ...manifest.field, units: "Pa" } }), /pressure manifest/);
});

test("GFS pressure values generate labelled hPa isobars", () => {
  const matrix = Array.from({ length: 9 }, () =>
    Array.from({ length: 13 }, (_, column) => 992 + column * 2)
  );
  const result = model.buildPressureContourData(
    matrix,
    { west: -6, south: 50, east: 6, north: 58 },
    9
  );
  assert.ok(result.features.length > 0);
  assert.ok(result.features.every((feature) => / hPa$/.test(feature.properties.label)));
  assert.ok(result.features.some((feature) => feature.properties.level === 1000));
  assert.ok(result.features.some((feature) => feature.properties.emphasized === true));
});

test("missing pressure cells make gaps rather than zero-pressure contours", () => {
  const matrix = Array.from({ length: 9 }, () =>
    Array.from({ length: 13 }, (_, column) => 992 + column * 2)
  );
  matrix[4][6] = Number.NaN;
  const result = model.buildPressureContourData(
    matrix,
    { west: -6, south: 50, east: 6, north: 58 },
    9
  );
  assert.ok(result.features.every((feature) =>
    feature.geometry.coordinates.every(([longitude, latitude]) =>
      Number.isFinite(longitude) && Number.isFinite(latitude)
    )
  ));
  assert.equal(result.features.some((feature) => feature.properties.level < 900), false);
});
