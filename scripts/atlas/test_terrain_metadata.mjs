import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from 'vite';

const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true } });
const model = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadata.ts');
const cases = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataExamples.ts');
const { validateTerrainSource, validateTerrainProduct } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataValidation.ts');
await server.close();
const { known, unknown } = model;
const { RIFFELHORN_SWISS_SOURCE: swiss, AWS_VISUAL_PRODUCT: aws, RIFFELHORN_REGIONAL_PRODUCT: regional, MAPTERHORN_EVALUATION_PRODUCT: mapterhorn } = cases;
const record = JSON.parse(readFileSync('docs/atlas/riffelhorn-regional-product.json', 'utf8'));

test('four owned cases validate without pretending unknown vertical references are known', () => {
  assert.deepEqual(validateTerrainSource(swiss), []);
  for (const product of [aws, regional, mapterhorn]) assert.deepEqual(validateTerrainProduct(product), []);
  assert.equal(aws.vertical.kind, 'unknown');
  assert.equal(mapterhorn.vertical.kind, 'unknown');
  assert.equal(regional.vertical.kind, 'heterogeneous');
  assert.equal(regional.vertical.parts[0].reference.value.identifier, 'EPSG:5728');
  assert.equal(regional.vertical.parts[1].reference.status, 'unknown');
  const invalid = structuredClone(aws);
  invalid.vertical.reason = '';
  assert.match(validateTerrainProduct(invalid).join('\n'), /unknown requires a reason/);
});

test('distributed grid and delivery zoom are independent; native measurement remains unknown', () => {
  assert.equal(swiss.resolution.gridSpacing.x, 0.5);
  assert.equal(swiss.resolution.measurementResolution.status, 'unknown');
  assert.equal(regional.delivery.zoom.max.value, 18);
  const changed = structuredClone(regional);
  changed.delivery.zoom.max = known(16);
  assert.deepEqual(validateTerrainProduct(changed), []);
  assert.equal(swiss.resolution.gridSpacing.x, 0.5);
  assert.equal(changed.sourceInformation.informationCeiling.status, 'unknown');
});

test('four immutable official inputs and derived identity agree with existing canonical record', () => {
  assert.equal(swiss.assets.length, 4);
  assert.deepEqual(swiss.assets.map(asset => asset.sha256), record.source.inputs.map(input => input.sha256));
  for (const [i, asset] of swiss.assets.entries()) assert.ok(asset.href.endsWith(record.source.inputs[i].path.split('/').at(-1)));
  assert.equal(regional.revision.value, record.identity);
  assert.equal(regional.spatial.coverage.value.asset.sha256, record.manifestSha256);
  assert.equal(regional.delivery.tileSize[0], record.delivery.tileSize);
  assert.equal(regional.delivery.zoom.max.value, record.delivery.maxzoom);
  assert.equal(regional.delivery.encoding.quantizationIncrement.value, record.delivery.quantizationIncrementMetres);
});

test('lineage distinguishes upstream Swiss source, derived AWS product, and input contribution mask', () => {
  assert.deepEqual(regional.lineage.contributors.map(ref => ref.kind), ['source', 'product']);
  assert.equal(regional.lineage.contributorList, 'complete');
  assert.equal(regional.lineage.spatialMapping, 'mask');
  assert.match(regional.lineage.contributionMask.interpretation, /not measurement confidence/);
  const invalid = structuredClone(regional);
  delete invalid.lineage.contributionMask;
  assert.match(validateTerrainProduct(invalid).join('\n'), /requires a mask/);
});

test('coverage, assessed support, protected interior and overlap are independently representable', () => {
  assert.equal(swiss.coverage.scope, 'retained-input-selection');
  assert.equal(swiss.coverage.area.value.kind, 'native-rectangle');
  assert.equal(regional.spatial.coverage.value.kind, 'asset');
  assert.equal(regional.spatial.validSupport.status, 'unknown');
  const example = structuredClone(regional);
  const support = (bounds, purpose) => known({ area: { ...cases.SWISS_SELECTION_AREA, bounds }, purpose, basis: 'Synthetic semantic fixture only; not an accepted Riffelhorn region.' });
  example.spatial.validSupport = support([2624100, 1091100, 2625900, 1092900], 'visual terrain');
  example.spatial.protectedInterior = support([2624500, 1091500, 2625500, 1092500], 'preserve regional information');
  example.spatial.transitionSupport = support([2624000, 1091000, 2626000, 1093000], 'overlap assessment');
  assert.deepEqual(validateTerrainProduct(example), []);
  assert.notDeepEqual(example.spatial.validSupport.value.area, example.spatial.protectedInterior.value.area);
  assert.notDeepEqual(example.spatial.protectedInterior.value.area, example.spatial.transitionSupport.value.area);
});

test('fallback is a relationship, never an expansion of source or product coverage', () => {
  const before = structuredClone(regional.spatial.coverage);
  const withoutFallback = structuredClone(regional);
  delete withoutFallback.fallback;
  assert.deepEqual(validateTerrainProduct(withoutFallback), []);
  assert.deepEqual(withoutFallback.spatial.coverage, before);
  assert.notDeepEqual(swiss.coverage.area, aws.spatial.coverage);
  assert.equal(regional.fallback.product.id, aws.id);
});

test('heterogeneous catalogue and sparse fine zoom are not complete pixel provenance/global coverage', () => {
  assert.equal(mapterhorn.lineage.contributorList, 'partial');
  assert.equal(mapterhorn.lineage.spatialMapping, 'catalogue-only');
  assert.equal(mapterhorn.lineage.contributionMask, undefined);
  assert.equal(mapterhorn.delivery.zoom.max.status, 'unknown');
  assert.match(mapterhorn.delivery.availability, /sparse regional children/);
  assert.equal(mapterhorn.rights.licence.status, 'unknown');
});

test('vertical transformation retains both references, method, accuracy and limitations without applying it', () => {
  const example = structuredClone(regional);
  example.vertical = { kind: 'transformed', transformation: {
    from: { name: 'LN02 height', identifier: 'EPSG:5728' }, to: { name: 'LHN95 height', identifier: 'EPSG:5729' },
    method: 'Synthetic representation fixture; no transformation performed', accuracy: unknown('Fixture has no evaluated accuracy.'), limitations: 'No claim that this transform reconciles AWS.',
  } };
  assert.deepEqual(validateTerrainProduct(example), []);
  example.vertical.transformation.method = '';
  assert.match(validateTerrainProduct(example).join('\n'), /vertical transformation requires/);
});

test('non-tiled output and preserved heights do not require Terrarium, zoom or renderer configuration', () => {
  const example = structuredClone(regional);
  example.delivery = { kind: 'raster-file', horizontalReference: swiss.horizontalReference, format: 'Float32 GeoTIFF', assets: swiss.assets };
  example.vertical = { kind: 'preserved', from: regional.lineage.contributors[0], reference: swiss.verticalReference };
  assert.deepEqual(validateTerrainProduct(example), []);
  assert.equal('zoom' in example.delivery, false);
  assert.equal('hillshade' in swiss, false);
  example.delivery.horizontalReference = unknown('File CRS not established in a hypothetical record.');
  assert.deepEqual(validateTerrainProduct(example), []);
  example.delivery = { kind: 'unknown', reason: 'Delivery contract not established.' };
  assert.deepEqual(validateTerrainProduct(example), []);
});

test('GeoJSON is 2D lon/lat, projected footprints stay explicitly native', () => {
  const example = structuredClone(swiss);
  example.coverage.area = known({ kind: 'geojson', geometry: { type: 'Polygon', coordinates: [[[7, 45], [8, 45], [8, 46], [7, 45]]] } });
  assert.deepEqual(validateTerrainSource(example), []);
  example.coverage.area.value.geometry.coordinates[0][0] = [2624000, 1091000];
  assert.match(validateTerrainSource(example).join('\n'), /longitude\/latitude/);
});

test('invalid tile dimensions, zoom, encoding increments and hashes fail focused validation', () => {
  const example = structuredClone(regional);
  example.delivery.tileSize = [256.5, 0];
  example.delivery.zoom.max = known(3);
  example.delivery.encoding.quantizationIncrement.value = -1;
  example.spatial.coverage.value.asset.sha256 = 'not a checksum';
  const errors = validateTerrainProduct(example).join('\n');
  for (const term of ['tile dimensions', 'zoom range', 'encoding increment', 'SHA-256']) assert.ok(errors.includes(term));
});

test('evidence snapshots retain resolvable repository documentation references', () => {
  for (const entity of [swiss, aws, regional, mapterhorn]) {
    for (const reference of entity.documentation) {
      if (!reference.startsWith('https://')) assert.ok(existsSync(reference), `${entity.id}: ${reference}`);
    }
  }
  assert.ok(regional.generation.buildRecord.href === 'docs/atlas/riffelhorn-regional-product.json');
  assert.equal(regional.generation.buildRecord.selector.includes('source.inputs'), true);
});
