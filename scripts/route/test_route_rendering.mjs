import assert from "node:assert/strict";
import test from "node:test";
import { GeoJSONVT } from "@maplibre/geojson-vt";
import { createServer } from "vite";

const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
const layer = await server.ssrLoadModule("/src/services/routeLayer.ts");
test.after(() => server.close());

function mockMap() {
  const sources = new Map();
  const layers = new Map();
  return {
    sources, layers,
    isStyleLoaded: () => true,
    getStyle: () => ({ layers: [...layers.values()] }),
    getSource: (id) => sources.get(id),
    getLayer: (id) => layers.get(id),
    addSource(id, source) { sources.set(id, { ...source, setData(data) { this.data = data; } }); },
    addLayer(spec) { layers.set(spec.id, structuredClone(spec)); },
    setLayoutProperty(id, key, value) { layers.get(id).layout[key] = value; },
    moveLayer() {},
  };
}

const coordinates = Array.from({ length: 101 }, (_, i) => ({
  longitude: -0.17 + i * 40 / (111195 * Math.cos(51.5 * Math.PI / 180)),
  latitude: 51.5,
}));
const conditions = { samples: coordinates.map((_, i) => ({
  terrain: { gradient: i % 2 ? -0.1 : 0.1 },
  weather: Object.fromEntries(["temperature", "precipitation", "cloud", "wind"].map(field =>
    [field, i < 50 ? { state: "available", value: field === "precipitation" ? 0.09 : 10, speedMs: 5 } : { state: "unavailable" }]
  )),
})) };

function tileFeatures(source, zoom, tolerance = source.tolerance) {
  // Same pixel-to-tile conversion as MapLibre's GeoJSONSource (512 px tiles).
  const index = new GeoJSONVT(source.data, { extent: 8192, tolerance: tolerance * 16, maxZoom: 18 });
  const x = Math.floor((coordinates[0].longitude + 180) / 360 * 2 ** zoom);
  const y = Math.floor((1 - Math.asinh(Math.tan(51.5 * Math.PI / 180)) / Math.PI) / 2 * 2 ** zoom);
  return index.getTile(zoom, x, y)?.features ?? [];
}

function width(expression, zoom) {
  const [, , , z0, w0, z1, w1] = expression;
  return w0 + (w1 - w0) * Math.max(0, Math.min(1, (zoom - z0) / (z1 - z0)));
}

test("short condition segments survive actual overview tiling; default simplification reproduces the bug", () => {
  for (const mode of ["gradient", "temperature", "precipitation", "wind"]) {
    const map = mockMap();
    layer.updateRouteLayer(map, coordinates, 10, conditions, mode);
    const source = map.getSource(layer.ROUTE_SOURCE_ID);
    assert.equal(source.tolerance, 0);
    for (const zoom of [6, 8, 10, 12]) {
      assert.equal(tileFeatures(source, zoom).filter(f => f.tags.kind === "condition-segment").length, 100);
    }
    assert.equal(tileFeatures(source, 6, 0.375).filter(f => f.tags.kind === "condition-segment").length, 0);
    assert.equal(tileFeatures(source, 6, 0.375).filter(f => f.tags.kind === "route").length, 1);
  }
});

test("Normal paint remains unchanged and condition width/opacity are prominent relative to casing", () => {
  const map = mockMap();
  layer.updateRouteLayer(map, coordinates, null, conditions, "none");
  const normal = map.getLayer(layer.ROUTE_LINE_LAYER_ID);
  assert.deepEqual(normal.paint, {
    "line-color": "#ff7652", "line-opacity": 0.96,
    "line-width": ["interpolate", ["linear"], ["zoom"], 3, 1.5, 10, 3.8],
  });
  assert.equal(normal.layout.visibility, "visible");
  const coloured = map.getLayer(layer.ROUTE_CONDITION_LAYER_ID).paint;
  const casing = map.getLayer(layer.ROUTE_CASING_LAYER_ID).paint;
  for (const zoom of [6, 8, 10, 12]) {
    assert.ok(width(coloured["line-width"], zoom) > width(normal.paint["line-width"], zoom));
    assert.ok(width(coloured["line-width"], zoom) / width(casing["line-width"], zoom) > 0.6);
    assert.equal(coloured["line-opacity"], 0.98);
  }
});

test("Gradient is independent of weather and partial weather colours stay per segment", () => {
  const map = mockMap();
  layer.updateRouteLayer(map, coordinates, null, conditions, "gradient");
  let segments = map.getSource(layer.ROUTE_SOURCE_ID).data.features.filter(f => f.properties.kind === "condition-segment");
  assert.ok(segments.every(f => f.properties.colour !== "#7b8581"));
  for (const mode of ["temperature", "precipitation", "wind"]) {
    layer.updateRouteLayer(map, coordinates, null, conditions, mode);
    segments = map.getSource(layer.ROUTE_SOURCE_ID).data.features.filter(f => f.properties.kind === "condition-segment");
    assert.ok(segments.slice(0, 50).every(f => f.properties.colour !== "#7b8581"));
    assert.ok(segments.slice(50).every(f => f.properties.colour === "#7b8581"));
  }
});
