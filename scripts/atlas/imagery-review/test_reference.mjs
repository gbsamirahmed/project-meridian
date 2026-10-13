import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
const source = await readFile(new URL('../../../src/atlas/map/satelliteLayer.ts', import.meta.url), 'utf8');
const script = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
function fixture(fetcher) {
  const exports = {};
  runInNewContext(script, { exports, fetch: fetcher, console: { warn() {} }, require: name => {
    if (name === './satelliteProvider') return { SATELLITE_PROVIDER: { tileJsonUrl: 'synthetic-metadata', tileSize: 512 } };
    if (name === './terrainLayers') return { ELEVATION_RELIEF_LAYER_ID: 'relief', HILLSHADE_LAYER_ID: 'shade' };
    throw Error('Unexpected dependency');
  } });
  const base = () => [{ id: 'background', type: 'background' }, { id: 'land', type: 'fill' },
    { id: 'road', type: 'line', layout: { visibility: 'none' } }, { id: 'label', type: 'symbol' }];
  const map = { layers: base(), sources: {}, isStyleLoaded: () => true,
    getStyle() { return { layers: this.layers }; }, getLayer(id) { return this.layers.find(l => l.id === id); },
    getSource(id) { return this.sources[id]; }, addSource(id, value) { this.sources[id] = value; },
    addLayer(value) { this.layers.push(value); }, setLayoutProperty(id, key, value) { const l = this.getLayer(id); (l.layout ??= {})[key] = value; } };
  return { api: exports, map, base };
}
const metadata = { tiles: ['https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg'], attribution: 'Synthetic provider credit', minzoom: 0, maxzoom: 22 };
test('reference satellite deduplicates metadata, preserves original visibility and restores after style reload', async () => {
  let calls = 0;
  const { api, map, base } = fixture(async () => { calls++; return { ok: true, json: async () => metadata }; });
  api.captureSatelliteBasemapLayers(map);
  await Promise.all([api.ensureSatelliteLayer(map), api.ensureSatelliteLayer(map)]);
  assert.equal(calls, 1); assert.equal(map.sources[api.SATELLITE_SOURCE_ID].tileSize, 512);
  api.applySatelliteLayerState(map, true);
  assert.equal(map.getLayer('land').layout.visibility, 'none'); assert.equal(map.getLayer('label').layout, undefined);
  api.applySatelliteLayerState(map, false);
  assert.equal(map.getLayer('land').layout.visibility, 'visible'); assert.equal(map.getLayer('road').layout.visibility, 'none');
  map.layers = base(); map.sources = {}; api.captureSatelliteBasemapLayers(map);
  assert.equal(await api.ensureSatelliteLayer(map), 'ready'); assert.equal(calls, 1);
});
test('reference metadata failure is session-sticky and leaves the conventional basemap usable', async () => {
  let calls = 0;
  const { api, map } = fixture(async () => { calls++; return { ok: false, status: 403 }; });
  api.captureSatelliteBasemapLayers(map);
  assert.equal(await api.ensureSatelliteLayer(map), 'error'); assert.equal(await api.ensureSatelliteLayer(map), 'error');
  assert.equal(calls, 1); api.applySatelliteLayerState(map, true);
  assert.equal(map.getLayer('land').layout.visibility, 'visible'); assert.equal(map.getSource(api.SATELLITE_SOURCE_ID), undefined);
});
test('reference parser has no endpoint allowlist: a non-empty unreviewed URL is accepted without fetching it', async () => {
  const { api, map } = fixture(async () => ({ ok: true, json: async () => ({ ...metadata, tiles: ['https://unreviewed.example/{z}/{x}/{y}.jpg'] }) }));
  assert.equal(await api.ensureSatelliteLayer(map), 'ready');
  assert.equal(map.sources[api.SATELLITE_SOURCE_ID].tiles[0], 'https://unreviewed.example/{z}/{x}/{y}.jpg');
});
