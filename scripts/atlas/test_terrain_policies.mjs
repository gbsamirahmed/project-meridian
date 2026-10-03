import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { createServer } from "vite";

const AWS_TERRARIUM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png";
const CREDITS = '<a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">Terrain data credits</a>';

async function modules(context, visualOverride) {
  const server = await createServer({
    configFile: false,
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
    plugins: visualOverride ? [{
      name: "test-visual-terrain-policy",
      enforce: "pre",
      load(id) {
        if (id.replaceAll("\\", "/").endsWith("/src/atlas/map/visualTerrainConfig.ts")) {
          return `export const VISUAL_TERRAIN_DEM = ${JSON.stringify(visualOverride)};`;
        }
      },
    }] : [],
  });
  context.after(() => server.close());
  return {
    visual: await server.ssrLoadModule("/src/atlas/map/visualTerrainConfig.ts"),
    layers: await server.ssrLoadModule("/src/atlas/map/terrainLayers.ts"),
    analytical: await server.ssrLoadModule("/src/atlas/terrain/analyticalElevationConfig.ts"),
    sampler: await server.ssrLoadModule("/src/atlas/terrain/terrainElevationSampler.ts"),
  };
}

function mapHarness(zoom = 11.4) {
  const sources = new Map();
  const layers = new Map();
  let terrain = null;
  let projection = "mercator";
  return {
    sources, layers,
    getContainer: () => ({ style: {} }),
    setSky(sky) { this.sky = structuredClone(sky); },
    getSource: (id) => sources.get(id),
    addSource: (id, source) => sources.set(id, structuredClone(source)),
    getLayer: (id) => layers.get(id),
    addLayer: (layer) => layers.set(layer.id, structuredClone(layer)),
    getStyle: () => ({ layers: [...layers.values()] }),
    moveLayer() {},
    setPaintProperty(id, key, value) { layers.get(id).paint[key] = structuredClone(value); },
    getZoom: () => zoom,
    setZoom(value) { zoom = value; },
    getTerrain: () => terrain,
    setTerrain(value) { terrain = value; },
    getProjection: () => ({ type: projection }),
    setProjection(value) { projection = value.type; },
  };
}

function replaceGlobal(context, name, value) {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, name);
  Object.defineProperty(globalThis, name, { configurable: true, writable: true, value });
  context.after(() => {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else delete globalThis[name];
  });
}

function mockTiles(context, heightForUrl) {
  const requests = [];
  let closed = 0;
  replaceGlobal(context, "fetch", async (url, options) => {
    requests.push({ url, signal: options.signal });
    return { ok: true, blob: async () => ({ url }) };
  });
  replaceGlobal(context, "createImageBitmap", async ({ url }) => {
    const height = heightForUrl(url);
    const encoded = Math.round((height + 32768) * 256);
    const pixels = new Uint8ClampedArray(256 * 256 * 4);
    for (let offset = 0; offset < pixels.length; offset += 4) {
      pixels[offset] = Math.floor(encoded / 65536);
      pixels[offset + 1] = Math.floor(encoded / 256) % 256;
      pixels[offset + 2] = encoded % 256;
      pixels[offset + 3] = 255;
    }
    return { width: 256, height: 256, pixels, close() { closed += 1; } };
  });
  replaceGlobal(context, "document", {
    createElement(name) {
      assert.equal(name, "canvas");
      let bitmap;
      return { getContext() { return {
        drawImage(image) { bitmap = image; },
        getImageData: () => ({ data: bitmap.pixels }),
      }; } };
    },
  });
  return { requests, closed: () => closed };
}

// Coordinates for a four-tile intersection adjacent to the equator/prime meridian.
const crossTilePoint = {
  longitude: -0.5 / (256 * 2 ** 15) * 360,
  latitude: Math.atan(Math.sinh(Math.PI / (256 * 2 ** 15))) * 180 / Math.PI,
};

function assertNear(actual, expected) {
  assert.ok(Math.abs(actual - expected) < 1e-8, `${actual} != ${expected}`);
}

test("visual policy retains both DEM sources, credits and rendering settings", async (context) => {
  const { visual, layers } = await modules(context);
  assert.equal(visual.VISUAL_TERRAIN_DEM.tileTemplate, AWS_TERRARIUM);
  const map = mapHarness();
  layers.configurePlanetAndTerrain(map);
  assert.deepEqual(map.sources.get("terrain-dem"), {
    type: "raster-dem", tiles: [AWS_TERRARIUM], tileSize: 256,
    encoding: "terrarium", maxzoom: 14, attribution: CREDITS,
  });
  assert.deepEqual(map.sources.get("terrain-analysis-dem"), {
    type: "raster-dem", tiles: [AWS_TERRARIUM], tileSize: 256,
    encoding: "terrarium", maxzoom: 15,
  });
  assert.deepEqual(map.getTerrain(), { source: "terrain-dem", exaggeration: 1.45 });
  assert.equal(map.layers.get("terrain-hillshade").paint["hillshade-method"], "igor");
  assert.deepEqual(map.layers.get("terrain-hillshade").paint["hillshade-exaggeration"],
    ["interpolate", ["linear"], ["zoom"], 5.5, 0, 7, 0.06, 9, 0.2, 11, 0.36, 12, 0.3, 13, 0.24, 14, 0.22, 15, 0.2, 16, 0.2]);
  layers.applyTerrainLayerState(map, "terrain", true);
  assert.equal(map.layers.get("terrain-elevation-relief").paint["color-relief-opacity"], 0.7);
  layers.applyTerrainLayerState(map, "satellite", false);
  assert.equal(map.layers.get("terrain-elevation-relief").paint["color-relief-opacity"], 0);
  const strength = map.layers.get("terrain-hillshade").paint["hillshade-exaggeration"];
  assert.ok(strength.slice(4).filter((_, index) => index % 2 === 0).every((value) => value === 0));
  map.setZoom(5.49);
  layers.updateTerrainActivation(map);
  assert.equal(map.getTerrain(), null);
  assert.equal(map.getProjection().type, "globe");
  map.setZoom(5.5);
  layers.updateTerrainActivation(map);
  assert.equal(map.getProjection().type, "mercator");
  assert.deepEqual(map.getTerrain(), { source: "terrain-dem", exaggeration: 1.45 });
});

test("analytical policy remains AWS Terrarium at z15 with 256-pixel addressing", async (context) => {
  const { analytical } = await modules(context);
  assert.deepEqual(analytical.ANALYTICAL_ELEVATION, {
    tileTemplate: AWS_TERRARIUM, tileSize: 256, samplingZoom: 15,
  });
});

test("substituting visual DEM settings leaves analytical requests and values unchanged", async (context) => {
  const override = {
    tileTemplate: "https://visual.example/{z}/{x}/{y}.png", tileSize: 512,
    encoding: "mapbox", geometryMaxZoom: 12, reliefMaxZoom: 13,
    attribution: "Visual test source",
  };
  const { layers, sampler, analytical } = await modules(context, override);
  const map = mapHarness();
  layers.configurePlanetAndTerrain(map);
  assert.deepEqual(map.sources.get("terrain-dem").tiles, [override.tileTemplate]);
  assert.equal(map.sources.get("terrain-dem").tileSize, 512);
  assert.equal(map.sources.get("terrain-dem").maxzoom, 12);
  assert.equal(map.sources.get("terrain-analysis-dem").maxzoom, 13);
  assert.equal(analytical.ANALYTICAL_ELEVATION.tileTemplate, AWS_TERRARIUM);
  const tiles = mockTiles(context, () => 123.25);
  const signal = new AbortController().signal;
  const values = await sampler.sampleTerrainElevations([{ latitude: 0, longitude: 0 }], signal);
  assert.deepEqual(values, [123.25]);
  assert.deepEqual(tiles.requests.map(({ url }) => url), [
    "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/15/16384/16384.png",
  ]);
  assert.equal(tiles.requests[0].signal, signal);
});

test("Terrarium values interpolate across four tiles, wrap longitude and reuse decoded tiles", async (context) => {
  const { sampler } = await modules(context);
  const heights = new Map([
    ["16383/16383", -12.5], ["16384/16383", 10.25],
    ["16383/16384", 100.75], ["16384/16384", 201.5],
  ]);
  const tiles = mockTiles(context, (url) => {
    const match = /\/15\/(\d+\/\d+)\.png$/.exec(url);
    assert.ok(match, url);
    assert.ok(heights.has(match[1]), url);
    return heights.get(match[1]);
  });
  const progress = [];
  const signal = new AbortController().signal;
  const values = await sampler.sampleTerrainElevations([crossTilePoint], signal,
    (completed, total) => progress.push([completed, total]));
  assertNear(values[0], 75);
  assert.equal(tiles.requests.length, 4);
  assert.equal(tiles.closed(), 4);
  assert.deepEqual(progress, [[1, 4], [2, 4], [3, 4], [4, 4]]);
  const repeated = await sampler.sampleTerrainElevations([
    crossTilePoint, { ...crossTilePoint, longitude: crossTilePoint.longitude + 360 },
    { latitude: 90, longitude: 0 }, { latitude: -90, longitude: 0 },
  ], signal);
  assertNear(repeated[0], 75);
  assertNear(repeated[1], 75);
  assert.deepEqual(repeated.slice(2), [null, null]);
  assert.equal(tiles.requests.length, 4);
});

test("tile failure stays unavailable and cancellation still rejects", async (context) => {
  const { sampler } = await modules(context);
  const controller = new AbortController();
  let cancel = false;
  replaceGlobal(context, "fetch", async (_url, { signal }) => {
    if (!cancel) return { ok: false, status: 404 };
    assert.equal(signal, controller.signal);
    controller.abort();
    throw new DOMException("Aborted", "AbortError");
  });
  assert.deepEqual(await sampler.sampleTerrainElevations([crossTilePoint], new AbortController().signal), [null]);
  cancel = true;
  await assert.rejects(sampler.sampleTerrainElevations([crossTilePoint], controller.signal), { name: "AbortError" });
});

test("route preparation continues to request numeric elevation through the analytical sampler", () => {
  const app = readFileSync(new URL("../../src/app/App.tsx", import.meta.url), "utf8");
  assert.match(app, /import \{ sampleTerrainElevations \} from "\.\.\/atlas\/terrain\/terrainElevationSampler"/);
  assert.match(app, /await sampleTerrainElevations\(\s*resampled\.coordinates,\s*controller\.signal/);
});
