/* Bounded offline MVT packaging with installed MapLibre tooling; no contour derivation. */
import { GeoJSONVT } from '@maplibre/geojson-vt';
import { fromGeojsonVt } from '@maplibre/vt-pbf';
import { VectorTile } from '@mapbox/vector-tile';
import { PbfReader } from 'pbf';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';

export const settings = { minZoom: 10, maxZoom: 17, extent: 8192, buffer: 64, tolerance: 0,
  maximumTiles: 2500, maximumTileBytes: 120_000_000, maximumSeconds: 120, maximumRssBytes: 1024 ** 3 };
export const hash = body => createHash('sha256').update(body).digest('hex');
export function tileRange(bounds, z) {
  const count = 2 ** z;
  const x = lon => Math.floor((lon + 180) / 360 * count);
  const y = lat => Math.floor((1 - Math.asinh(Math.tan(lat * Math.PI / 180)) / Math.PI) / 2 * count);
  return [x(bounds[0]), y(bounds[3]), x(bounds[2]), y(bounds[1])];
}
export function encode(tile) {
  return fromGeojsonVt({ contours: tile || { features: [] } }, { version: 2, extent: settings.extent });
}
export function decode(body) {
  // The standard decoder omits zero-feature layers. An empty MVT is valid,
  // not a missing-data response or evidence of a contour in this tile.
  return new VectorTile(new PbfReader(body)).layers.contours || { length: 0, extent: settings.extent, version: 2 };
}
export function tileBounds(z, x, y) {
  const count = 2 ** z, margin = settings.buffer / settings.extent;
  const latitude = row => Math.atan(Math.sinh(Math.PI * (1 - 2 * row / count))) * 180 / Math.PI;
  return [(x - margin) / count * 360 - 180, latitude(y + 1 + margin),
    (x + 1 + margin) / count * 360 - 180, latitude(y - margin)];
}
function encodedTile(features, z, x, y) {
  const box = tileBounds(z, x, y);
  const subset = features.filter(item => item.box[0] <= box[2] && item.box[2] >= box[0]
    && item.box[1] <= box[3] && item.box[3] >= box[1]).map(item => item.feature);
  // A fresh, spatially filtered index per output tile avoids retaining a whole
  // unsimplified multizoom cache. Use public APIs only; never prune private caches.
  const index = new GeoJSONVT({ type: 'FeatureCollection', features: subset },
    { ...settings, indexMaxZoom: 0, indexMaxPoints: 100_000 });
  const tile = index.getTile(z, x, y), body = encode(tile);
  if (hash(body) !== hash(encode(tile))) throw new Error('Nondeterministic tile encoding');
  return body;
}
export function edgeCrossings(layer, axis, value) {
  const crossings = new Map();
  for (let index = 0; index < layer.length; index++) {
    const feature = layer.feature(index), values = [];
    for (const line of feature.loadGeometry()) {
      for (let i = 1; i < line.length; i++) {
        const a = line[i - 1], b = line[i], other = axis === 'x' ? 'y' : 'x';
        if (a[axis] === b[axis]) continue; // Boundary-parallel lines have no unique crossing.
        const t = (value - a[axis]) / (b[axis] - a[axis]);
        if (t >= 0 && t <= 1) values.push(a[other] + t * (b[other] - a[other]));
      }
    }
    if (values.length) crossings.set(feature.id, [...new Set(values)].sort((a, b) => a - b));
  }
  return crossings;
}
export function compareEdges(a, b, axis) {
  const first = edgeCrossings(a, axis, settings.extent), second = edgeCrossings(b, axis, 0);
  let maximum = 0, compared = 0, unmatched = 0;
  for (const id of new Set([...first.keys(), ...second.keys()])) {
    const aa = first.get(id) || [], bb = second.get(id) || [];
    if (aa.length !== bb.length) { unmatched++; continue; }
    for (let index = 0; index < aa.length; index++) {
      maximum = Math.max(maximum, Math.abs(aa[index] - bb[index])); compared++;
    }
  }
  return { maximumUnits: maximum, compared, unmatched };
}

export function packageProduct(root) {
  if (!globalThis.gc) throw new Error('Run packaging with --expose-gc for bounded tile-index retirement');
  const started = performance.now(), metadata = JSON.parse(readFileSync(join(root, 'product.json')));
  if (existsSync(join(root, 'tiles'))) throw new Error('Fresh tile directory required');
  mkdirSync(join(root, 'tiles'));
  let totalBytes = 0, peakRss = 0, decodedFeatures = 0, decodedVertices = 0;
  const inventory = [], products = [];
  for (const product of metadata.products) {
    const raw = readFileSync(join(root, 'inputs', `${product.id}.geojson`));
    if (hash(raw) !== product.geojsonSha256) throw new Error('Prepared source seal mismatch');
    const data = JSON.parse(raw), originals = new Map(data.features.map(feature => [feature.id, feature.properties]));
    const features = data.features.map(feature => {
      const box = [Infinity, Infinity, -Infinity, -Infinity];
      for (const point of feature.geometry.coordinates) {
        box[0] = Math.min(box[0], point[0]); box[1] = Math.min(box[1], point[1]);
        box[2] = Math.max(box[2], point[0]); box[3] = Math.max(box[3], point[1]);
      }
      return { feature, box };
    });
    const entries = [];
    for (let z = settings.minZoom; z <= settings.maxZoom; z++) {
      const range = tileRange(metadata.boundsLonLat, z);
      for (let x = range[0]; x <= range[2]; x++) {
        for (let y = range[1]; y <= range[3]; y++) {
          globalThis.gc();
          const body = encodedTile(features, z, x, y);
          if (inventory.length + 1 > settings.maximumTiles || totalBytes + body.length > settings.maximumTileBytes)
            throw new Error('Tile count/byte reservation refused');
          peakRss = Math.max(peakRss, process.memoryUsage().rss);
          if (peakRss > settings.maximumRssBytes || performance.now() - started > settings.maximumSeconds * 1000)
            throw new Error('Packaging memory/time allowance reached');
          const layer = decode(body);
          if (layer.extent !== settings.extent || layer.version !== 2) throw new Error('MVT schema mismatch');
          for (let i = 0; i < layer.length; i++) {
            const feature = layer.feature(i);
            if (JSON.stringify(feature.properties) !== JSON.stringify(originals.get(feature.id)) || feature.type !== 2)
              throw new Error('Decoded elevation/source properties changed');
            for (const line of feature.loadGeometry()) {
              decodedVertices += line.length;
              for (const point of line) if (!Number.isInteger(point.x) || !Number.isInteger(point.y)
                  || point.x < -settings.buffer || point.y < -settings.buffer
                  || point.x > settings.extent + settings.buffer || point.y > settings.extent + settings.buffer)
                throw new Error('Unexpected clipping/quantisation coordinates');
            }
            decodedFeatures++;
          }
          const relative = `${product.id}/${z}/${x}/${y}.pbf`;
          mkdirSync(join(root, 'tiles', product.id, String(z), String(x)), { recursive: true });
          writeFileSync(join(root, 'tiles', relative), body, { flag: 'wx' });
          const entry = { product: product.id, z, x, y, bytes: body.length, sha256: hash(body), features: layer.length };
          entries.push(entry); inventory.push(entry); totalBytes += body.length;
        }
      }
    }
    // Representative adjacent maximum-zoom pairs, both horizontal and vertical.
    const close = entries.filter(entry => entry.z === settings.maxZoom), pairs = [];
    const keyed = new Map(close.map(entry => [`${entry.x}/${entry.y}`, entry]));
    for (const axis of ['x', 'y']) {
      let sampled = 0;
      for (const a of close) {
        const b = keyed.get(`${a.x + (axis === 'x' ? 1 : 0)}/${a.y + (axis === 'y' ? 1 : 0)}`);
        if (!b || a.features === 0 || b.features === 0) continue;
        const get = entry => decode(readFileSync(join(root, 'tiles', product.id, String(entry.z), String(entry.x), `${entry.y}.pbf`)));
        const result = compareEdges(get(a), get(b), axis);
        if (result.compared === 0) continue;
        pairs.push({ axis, a: [a.x, a.y], b: [b.x, b.y], ...result });
        if (++sampled === 8) break;
      }
    }
    products.push({ id: product.id, tileCount: entries.length, bytes: entries.reduce((sum, entry) => sum + entry.bytes, 0),
      minimumBytes: Math.min(...entries.map(entry => entry.bytes)), maximumBytes: Math.max(...entries.map(entry => entry.bytes)),
      edgeSamples: pairs });
  }
  const receipt = { settings, products, tileCount: inventory.length, tileBytes: totalBytes, peakRssBytes: peakRss,
    elapsedSeconds: (performance.now() - started) / 1000, decodedFeatures, decodedVertices, inventory,
    deterministicEncoding: true, allDecodedPropertiesExact: true, simplification: 'tolerance 0; quantisation can collapse vertices',
    quantisation: 'nearest integer, 8192 extent; half-unit per axis, not horizontal datum accuracy',
    libraries: Object.fromEntries(['@maplibre/geojson-vt', '@maplibre/vt-pbf', '@mapbox/vector-tile', 'pbf'].map(name => {
      const manifest = JSON.parse(readFileSync(new URL(`../../../node_modules/${name}/package.json`, import.meta.url)));
      return [name, { version: manifest.version, licence: manifest.license }];
    })) };
  writeFileSync(join(root, 'tile-receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify({ ...receipt, inventory: undefined, products: products.map(product => ({ ...product, edgeSamples: undefined })) }, null, 2));
  return receipt;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) packageProduct(process.argv[2]);
