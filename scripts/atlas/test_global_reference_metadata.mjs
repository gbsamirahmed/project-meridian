import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from 'vite';

const fixture = JSON.parse(readFileSync('docs/atlas/global-reference-metadata.json', 'utf8'));
const acquisition = JSON.parse(readFileSync('docs/atlas/global-reference-acquisition.json', 'utf8'));
const measurements = JSON.parse(readFileSync('docs/atlas/global-reference-measurements.json', 'utf8'));
const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true } });
const { validateTerrainSource, validateTerrainProduct } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataValidation.ts');
await server.close();

test('retained source, COG derivative and height diagnostic fit existing metadata model', () => {
  assert.deepEqual(validateTerrainSource(fixture.source), []);
  assert.deepEqual(validateTerrainProduct(fixture.product), []);
  assert.deepEqual(validateTerrainProduct(fixture.heightDiagnostic), []);
});

test('COG selection preserves known EGM2008 and source revision without implying global selected coverage', () => {
  assert.equal(fixture.source.coverage.scope, 'retained-input-selection');
  assert.equal(fixture.source.assets.length, 2);
  assert.deepEqual(fixture.source.assets.map(a => a.sha256), ['cop45', 'cop46'].map(k => acquisition.assets[k].sha256));
  assert.equal(fixture.product.vertical.kind, 'preserved');
  assert.equal(fixture.product.vertical.reference.value.identifier, 'EPSG:3855');
  assert.equal(fixture.product.lineage.contributors[0].revision.value, fixture.source.revision.value);
});

test('source grid spacing, diagnostic spacing and delivery remain different concepts', () => {
  assert.equal(fixture.source.resolution.gridSpacing.unit, 'arcsecond');
  assert.equal(fixture.source.resolution.measurementResolution.status, 'unknown');
  assert.equal(fixture.product.delivery.kind, 'raster-file');
  assert.equal(fixture.product.delivery.zoom, undefined);
  assert.equal(measurements.grid.spacing, 25);
  assert.equal(fixture.heightDiagnostic.delivery.kind, 'other');
});

test('height transformation is explicit, with unknown accuracy and independent stable support', () => {
  const diagnostic = fixture.heightDiagnostic;
  assert.equal(diagnostic.vertical.kind, 'transformed');
  assert.equal(diagnostic.vertical.transformation.from.identifier, 'EPSG:5728');
  assert.equal(diagnostic.vertical.transformation.to.identifier, 'EPSG:3855');
  assert.equal(diagnostic.vertical.transformation.accuracy.status, 'unknown');
  assert.equal(diagnostic.vertical.transformation.method, measurements.heightDiagnostic.pipeline);
  assert.equal(diagnostic.spatial.validSupport.value.area.asset.selector, 'primaryMask');
  assert.equal(diagnostic.spatial.transitionSupport.status, 'unknown');
});

test('predeclared protocol remains frozen and production has no experimental reference dependency', () => {
  const hash = createHash('sha256').update(readFileSync('docs/atlas/global-reference-protocol.json')).digest('hex');
  assert.equal(hash, acquisition.protocolSha256);
  for (const path of ['src/atlas/map/visualTerrainConfig.ts', 'src/atlas/terrain/analyticalElevationConfig.ts']) {
    const source = readFileSync(path, 'utf8');
    if (path.includes('analytical')) assert.match(source, /elevation-tiles-prod\/terrarium/);
    else assert.match(source, /productionTerrainRegistry/);
    assert.doesNotMatch(source, /global-reference|metadata\//);
  }
});
