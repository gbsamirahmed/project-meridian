import assert from 'node:assert/strict';
import { test } from 'node:test';
import { GeoJSONVT } from '@maplibre/geojson-vt';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { settings, encode, decode, compareEdges, hash, tileRange, tileBounds } from './package.mjs';
import { sourceWeight, intervalWeight, opacity, indexOpacity, indexStops } from './rules.mjs';
const lonlat = (x, y) => [x * 360 - 180, Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180 / Math.PI];
const makeIndex = coordinates => new GeoJSONVT({ type: 'FeatureCollection', features: [{ type: 'Feature', id: 7,
  properties: { elevation_m: 2500, index100: true, vertical_ref: 'LN02', units: 'm' },
  geometry: { type: 'LineString', coordinates: coordinates.map(point => lonlat(...point)) } }] },
  { ...settings, indexMaxZoom: 0 });
test('standard MVT v2 round-trip retains source-local identity and attributes', () => {
  const tile = makeIndex([[0.49, 0.55], [0.51, 0.65]]).getTile(1, 0, 1), body = encode(tile), layer = decode(body);
  assert.equal(layer.version, 2); assert.equal(layer.extent, 8192); assert.equal(layer.feature(0).id, 7);
  assert.equal(layer.feature(0).properties.elevation_m, 2500); assert.equal(layer.feature(0).properties.vertical_ref, 'LN02');
  assert.equal(layer.feature(0).properties.index100, true); assert.equal(hash(body), hash(encode(tile)));
});
test('buffered adjacent synthetic tiles preserve crossings and integer bounds', () => {
  const index = makeIndex([[0.49, 0.55], [0.51, 0.65]]);
  const a = decode(encode(index.getTile(1, 0, 1))), b = decode(encode(index.getTile(1, 1, 1)));
  const result = compareEdges(a, b, 'x');
  assert.equal(result.unmatched, 0); assert.equal(result.compared, 1); assert.ok(result.maximumUnits <= 1);
  for (const layer of [a, b]) for (const point of layer.feature(0).loadGeometry()[0]) {
    assert.ok(Number.isInteger(point.x)); assert.ok(point.x >= -64 && point.x <= 8256);
  }
});
test('closed synthetic ring is retained across four tile corners', () => {
  const index = makeIndex([[0.49, 0.49], [0.51, 0.49], [0.51, 0.51], [0.49, 0.51], [0.49, 0.49]]);
  for (const x of [0, 1]) for (const y of [0, 1]) assert.equal(decode(encode(index.getTile(1, x, y))).length, 1);
});
test('valid empty MVT is distinguishable from contour evidence', () => assert.equal(decode(encode(null)).length, 0));
test('tile ranges and padded coordinates use a standard north-up Mercator grid', () => {
  assert.deepEqual(tileRange([-1, -1, 1, 1], 1), [0, 0, 1, 1]);
  const box = tileBounds(1, 0, 1); assert.ok(box[0] < -180 && box[2] > 0 && box[3] > 0);
});
test('provisional intervals hide remotely and add detail without altering heights', () => {
  assert.equal(intervalWeight(2500, 10), 0); assert.equal(intervalWeight(2500, 14), 1);
  assert.equal(intervalWeight(2550, 12.25), 1); assert.equal(intervalWeight(2550, 13.75), 0);
  assert.equal(intervalWeight(2520, 13.75), 1); assert.equal(intervalWeight(2510, 15.75), 1);
  for (const z of [10, 14.9, 15.1, 17.5, 20]) {
    const sum = ['swiss-native', 'swiss-2m', 'swiss-smoothed'].reduce((sum, product) => sum + sourceWeight(product, z), 0);
    assert.ok(Math.abs(sum - 1) < 1e-12);
  }
  assert.equal(opacity('swiss-native', 'swiss-2m', 50), 0);
});
test('automatic indices fade gently, peak at fourteen and recede without changing manual opacity', () => {
  assert.equal(indexOpacity(10.99), 0); assert.equal(indexOpacity(11), 0);
  assert.ok(Math.abs(indexOpacity(11.05) - 0.008) < 1e-12);
  assert.equal(indexOpacity(11.25), 0.04);
  for (const [zoom, value] of indexStops) assert.ok(Math.abs(indexOpacity(zoom) - value) < 1e-12);
  assert.ok(indexOpacity(13.9) < 1); assert.ok(indexOpacity(14.1) < 1);
  assert.ok(indexOpacity(18.5) < indexOpacity(16));
  for (let zoom = 11.01; zoom <= 14; zoom += 0.01) assert.ok(indexOpacity(zoom) >= indexOpacity(zoom - 0.01));
  for (let zoom = 14.01; zoom <= 21; zoom += 0.01) assert.ok(indexOpacity(zoom) <= indexOpacity(zoom - 0.01));
  const manual = opacity('swiss-native', 'swiss-native', 20);
  assert.equal(manual.at(-2), 1); assert.equal(manual.at(-1), 0);
  // Each new index reference is present in the compiled MapLibre expression.
  const expression = opacity('swiss-smoothed');
  for (const [zoom] of indexStops) assert.ok(expression.includes(zoom));
});

test('genuine product seals, representative seams and close-scale vertex displacement', () => {
  assert.ok(process.env.MERIDIAN_TILE_ROOT, 'Explicit prepared product required; no skipped genuine tile check');
  const root = process.env.MERIDIAN_TILE_ROOT, metadata = JSON.parse(readFileSync(join(root, 'product.json')));
  const receipt = JSON.parse(readFileSync(join(root, 'tile-receipt.json')));
  let maxDistance = 0, sampled = 0, missing = 0, missingLines = 0;
  const perZoom = {};
  for (const entry of receipt.inventory) {
    const file = join(root, 'tiles', entry.product, String(entry.z), String(entry.x), `${entry.y}.pbf`);
    const body = readFileSync(file); assert.equal(hash(body), entry.sha256);
    perZoom[entry.z] = (perZoom[entry.z] || 0) + entry.bytes;
  }
  for (const product of metadata.products) {
    const source = JSON.parse(readFileSync(join(root, 'inputs', `${product.id}.geojson`)));
    const tiles = new Map(), present = new Set();
    for (const entry of receipt.inventory.filter(entry => entry.product === product.id && entry.z === 17)) {
      const layer = decode(readFileSync(join(root, 'tiles', entry.product, '17', String(entry.x), `${entry.y}.pbf`)));
      tiles.set(`${entry.x}/${entry.y}`, layer);
      for (let i = 0; i < layer.length; i++) present.add(layer.feature(i).id);
    }
    missingLines += source.features.filter(feature => !present.has(feature.id)).length;
    for (const feature of source.features.filter((_, index) => index % 11 === 0)) {
      const points = feature.geometry.coordinates;
      for (const point of [points[0], points[Math.floor(points.length / 2)], points[points.length - 1]]) {
        const count = 2 ** 17, x = (point[0] + 180) / 360 * count;
        const y = (1 - Math.asinh(Math.tan(point[1] * Math.PI / 180)) / Math.PI) / 2 * count;
        const tx = Math.floor(x), ty = Math.floor(y), px = (x - tx) * settings.extent, py = (y - ty) * settings.extent;
        const layer = tiles.get(`${tx}/${ty}`);
        const match = Array.from({ length: layer?.length || 0 }, (_, index) => layer.feature(index)).find(candidate => candidate.id === feature.id);
        if (!match) { missing++; continue; }
        let distance = Infinity;
        for (const line of match.loadGeometry()) for (let i = 1; i < line.length; i++) {
          const a = line[i - 1], b = line[i], dx = b.x - a.x, dy = b.y - a.y, denominator = dx * dx + dy * dy;
          const t = denominator ? Math.max(0, Math.min(1, ((px - a.x) * dx + (py - a.y) * dy) / denominator)) : 0;
          distance = Math.min(distance, Math.hypot(px - a.x - t * dx, py - a.y - t * dy));
        }
        assert.ok(distance <= Math.SQRT1_2 + 1e-5, `Quantisation exceeded half-unit per axis: ${distance}`);
        maxDistance = Math.max(maxDistance, distance); sampled++;
      }
    }
  }
  const edges = receipt.products.flatMap(product => product.edgeSamples);
  assert.equal(missing, 0); assert.equal(missingLines, 0);
  assert.ok(edges.length >= 24); assert.equal(edges.reduce((sum, edge) => sum + edge.unmatched, 0), 0);
  const seamMaximum = Math.max(...edges.map(edge => edge.maximumUnits)); assert.ok(seamMaximum <= 2);
  const record = { sampledVertices: sampled, missingSamples: missing, missingMasterLinesAtZ17: missingLines,
    maximumVertexDisplacementTileUnits: maxDistance,
    approximateMaximumGroundDisplacementMetres: maxDistance * 40075016.68557849 / (2 ** 17 * 8192) * Math.cos(metadata.centre[1] * Math.PI / 180),
    edgePairs: edges.length, edgeCrossings: edges.reduce((sum, edge) => sum + edge.compared, 0),
    maximumSeamDisplacementTileUnits: seamMaximum, unmatchedEdgeGroups: 0, tileBytesPerZoom: perZoom };
  const evidence = join(root, 'geometry-validation.json');
  if (existsSync(evidence)) assert.deepEqual(JSON.parse(readFileSync(evidence)), record);
  else writeFileSync(evidence, JSON.stringify(record, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(record));
});
