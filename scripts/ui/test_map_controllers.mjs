import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";

const server = await createServer({
  appType: "custom",
  logLevel: "silent",
  server: { middlewareMode: true },
});
const { WeatherMapController } = await server.ssrLoadModule(
  "/src/weather/map/WeatherMapController.ts"
);
test.after(() => server.close());

function mapHarness() {
  let loaded = false;
  const container = { dataset: {} };
  return {
    setLoaded(value) {
      loaded = value;
    },
    map: {
      isStyleLoaded: () => loaded,
      getStyle: () => ({ layers: [] }),
      getLayer: () => undefined,
      getSource: () => undefined,
      getContainer: () => container,
      removeLayer() {},
      removeSource() {},
      moveLayer() {},
    },
  };
}

function state() {
  return {
    basemap: "terrain",
    overlays: {
      precipitation: false,
      clouds: false,
      temperatureContours: false,
      pressureIsobars: false,
      windFlow: false,
    },
    precipitation: null,
    clouds: null,
    wind: null,
    temperature: null,
    pressure: null,
    validTime: null,
  };
}

test("Weather defers one requested render until Atlas reports a renderable map", () => {
  const harness = mapHarness();
  let renders = 0;
  const controller = new WeatherMapController(
    harness.map,
    () => {
      renders += 1;
    }
  );

  controller.update(state());
  assert.equal(renders, 0);
  harness.setLoaded(true);
  controller.mapBecameRenderable();
  assert.equal(renders, 1);
  controller.mapBecameRenderable();
  assert.equal(renders, 1);

  controller.viewportChanged();
  assert.equal(renders, 2);
  controller.destroy();
});

test("a request made during a later style transition is retained until idle", () => {
  const harness = mapHarness();
  let renders = 0;
  const controller = new WeatherMapController(harness.map, () => {
    renders += 1;
  });
  harness.setLoaded(true);
  controller.update(state());
  assert.equal(renders, 1);

  harness.setLoaded(false);
  controller.styleChanged();
  assert.equal(renders, 1);
  harness.setLoaded(true);
  controller.mapBecameRenderable();
  assert.equal(renders, 2);
  controller.destroy();
});