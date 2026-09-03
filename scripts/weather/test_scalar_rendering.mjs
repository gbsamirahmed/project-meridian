import assert from "node:assert/strict";
import test from "node:test";
import { createServer } from "vite";

const server = await createServer({ appType: "custom", logLevel: "silent", server: { middlewareMode: true } });
const raster = await server.ssrLoadModule("/src/services/scalarRaster.ts");
const style = await server.ssrLoadModule("/src/services/precipitationStyle.ts");
const labels = await server.ssrLoadModule("/src/services/weatherTimeLabel.ts");
const numeric = await server.ssrLoadModule("/src/services/numericTileCache.ts");
test.after(() => server.close());

test("trace precipitation stays visible and joins the unchanged 0.1 mm palette continuously", () => {
  assert.equal(style.precipitationColor(0).a, 0);
  assert.equal(style.precipitationColor(NaN).a, 0);
  for (const value of [0.01, 0.05, 0.08, 0.09]) assert.ok(style.precipitationColor(value).a > 0);
  assert.deepEqual(style.precipitationColor(0.1), { r: 88, g: 191, b: 211, a: 117 });
  assert.deepEqual(style.precipitationColor(0.5), { r: 36, g: 151, b: 200, a: 158 });
  assert.equal(style.precipitationColor(0.09999).a, style.precipitationColor(0.1).a);
  assert.equal(style.precipitationAmountLabel(0), "Dry");
  assert.equal(style.precipitationAmountLabel(0.001), "<0.01 mm / 1 h");
  assert.equal(style.precipitationAmountLabel(0.09), "0.09 mm / 1 h");
});

test("adjacent scalar display tiles share identical edges, including the 0.09/0.10 mm control", () => {
  const size = 16;
  const field = (x, y) => (x < size ? 0.1 : 0.09) + y * 0.0001;
  const west = raster.scalarRasterPixels(size, field, style.precipitationColor);
  const east = raster.scalarRasterPixels(size, (x, y) => field(x + size, y), style.precipitationColor);
  for (let row = 0; row < size; row++) {
    const a = (row * size + size - 1) * 4;
    const b = row * size * 4;
    assert.deepEqual(west.slice(a, a + 4), east.slice(b, b + 4));
    assert.ok(east[b + 3] > 0);
  }
  const south = raster.scalarRasterPixels(size, (x, y) => field(x, y + size), style.precipitationColor);
  for (let column = 0; column < size; column++) {
    const a = ((size - 1) * size + column) * 4;
    const b = column * 4;
    assert.deepEqual(west.slice(a, a + 4), south.slice(b, b + 4));
  }
});

test("no-data remains transparent and is never colourised as an encoded high precipitation value", () => {
  let called = false;
  const empty = raster.scalarRasterPixels(4, () => null, () => { called = true; return { r: 255, g: 0, b: 0, a: 255 }; });
  assert.equal(called, false);
  assert.ok(empty.every(value => value === 0));
  const hole = raster.scalarRasterPixels(4, (x, y) => x === 1 && y === 1 ? null : 0.1, style.precipitationColor);
  assert.equal(hole[(1 * 4 + 1) * 4 + 3], 0);
  assert.ok(hole[3] > 0);
});

async function numericRuntime(code, fn) {
  const originals = { fetch: globalThis.fetch, document: globalThis.document, createImageBitmap: globalThis.createImageBitmap };
  const requests = [];
  globalThis.fetch = async url => { requests.push(url); return { ok: true, blob: async () => ({}) }; };
  globalThis.createImageBitmap = async () => ({ close() {} });
  globalThis.document = { createElement: () => ({ getContext: () => ({
    drawImage() {}, getImageData() {
      const data = new Uint8ClampedArray(4 * 4 * 4);
      for (let i = 0; i < data.length; i += 4) { data[i] = code >> 8; data[i + 1] = code & 255; data[i + 3] = 255; }
      return { data };
    },
  }) }) };
  try { await fn(requests); } finally { Object.assign(globalThis, originals); }
}

test("renderer and point sampler share decoded values/no-data, cache and wrapped low-zoom requests", async () => {
  for (const code of [0, 9, 65535]) {
    const source = {
      baseUrl: `https://example.test/scalar-${code}/`,
      manifest: { coverage: { bounds: [-180, -85, 180, 85] }, tiles: {
        tileSize: 4, minZoom: 0, maxZoom: 0, encoding: "uint16-rg", noData: 65535, scale: 0.01, offset: 0,
      } },
    };
    const step = { tileTemplate: "f011/{z}/{x}/{y}.png" };
    await numericRuntime(code, async requests => {
      const pixels = await raster.loadScalarRasterPixels(source, step, 0, 0, 0, style.precipitationColor);
      const sample = await numeric.sampleScalarField(source, step, 0, 0);
      assert.equal(requests.length, 1); // all nine neighbours wrap/clip to one tile
      assert.equal(sample, code === 65535 ? null : code * 0.01);
      assert.equal(pixels[3], code === 65535 || code === 0 ? 0 : style.precipitationColor(code * 0.01).a);
    });
  }
});

test("interval labels use local accumulation bounds, never a future-valid-time offset", () => {
  const provenance = {
    timeSemantics: "interval-total", validTime: "2026-09-03T05:00:00Z",
    accumulationStart: "2026-09-03T04:00:00Z", accumulationEnd: "2026-09-03T05:00:00Z",
    temporalOffsetMinutes: 55,
  };
  const label = labels.routeConditionTimeLabel(provenance, "Europe/London");
  assert.match(label, /Interval.*05:00.*06:00.*BST/);
  assert.doesNotMatch(label, /after|before|Valid/);
  const instant = labels.routeConditionTimeLabel({ ...provenance, timeSemantics: "instantaneous", validTime: "2026-09-03T04:00:00Z", temporalOffsetMinutes: -5 }, "Europe/London");
  assert.match(instant, /Valid.*05:00.*BST.*5 min before arrival/);
  const midnight = labels.accumulationIntervalLabel({ accumulationStart: "2026-09-02T22:30:00Z", accumulationEnd: "2026-09-02T23:30:00Z" }, "Europe/London");
  assert.match(midnight, /Wed.*23:30.*Thu.*00:30/);
});
