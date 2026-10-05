import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from 'vite';

const json = path => JSON.parse(readFileSync(path, 'utf8'));
const commonRecord = json('docs/atlas/copernicus-common-metadata.json');
const regionalRecord = json('docs/atlas/riffelhorn-support-product.json');
const parentRecord = json('docs/atlas/regional-parent-product.json');
const transitionRecord = json('docs/atlas/two-band-product.json');
const completion = json('docs/atlas/two-band-completion.json');
const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true } });
const { known, unknown } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadata.ts');
const { AWS_VISUAL_PRODUCT } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataExamples.ts');
const { createTerrainHierarchyExamples } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainHierarchyExamples.ts');
const { classifyTerrainRefinement } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainHierarchy.ts');
const { validateTerrainHierarchy, validateTerrainIdentityReuse } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainHierarchyValidation.ts');
const { validateTerrainSource } = await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataValidation.ts');
await server.close();

const inputs = { aws: AWS_VISUAL_PRODUCT, common: commonRecord.product, regional: regionalRecord.product,
  parents: parentRecord.product, transition: transitionRecord.product,
  transitionContentSha256: completion.inventoryIdentity,
  contentManifests: { common: json('docs/atlas/copernicus-common-generation.json').manifestSha256,
    regional: json('docs/atlas/riffelhorn-support-reproducibility.json').manifestSha256,
    parents: parentRecord.product.spatial.coverage.value.asset.sha256 } };
const before = JSON.stringify(inputs);
const { hierarchy, aws, secondRegion } = createTerrainHierarchyExamples(inputs);
const errorsFor = mutate => { const copy = structuredClone(hierarchy); mutate(copy); return validateTerrainHierarchy(copy).join('\n'); };

test('five real/synthetic cases use the existing model without external assets or fabricated AWS certainty', () => {
  for (const value of [hierarchy, aws, secondRegion]) assert.deepEqual(validateTerrainHierarchy(value), []);
  assert.equal(aws.products[0].identity.kind, 'external-unpinned');
  assert.equal(aws.products[0].origin.kind, 'unresolved');
  assert.equal(aws.products[0].product.vertical.kind, 'unknown');
  assert.equal(hierarchy.products[0].product.vertical.reference.value.identifier, 'EPSG:3855');
  assert.equal(hierarchy.products[1].product.vertical.reference.value.identifier, 'EPSG:5728');
  assert.equal(hierarchy.products[3].product.vertical.kind, 'heterogeneous');
  assert.equal(secondRegion.products[1].product.vertical.kind, 'unknown');
  assert.equal(JSON.stringify(inputs), before);
});

test('source/product/representation stay distinct and rights remain attached to actual sources/products', () => {
  assert.deepEqual(validateTerrainSource(regionalRecord.source), []);
  assert.deepEqual(validateTerrainSource(commonRecord.source), []);
  const level = hierarchy.regional[0].levels.at(-1);
  assert.equal(level.representation.product.kind, 'product');
  assert.equal(regionalRecord.product.lineage.contributors[0].kind, 'source');
  assert.equal(regionalRecord.source.assets.length, 100);
  assert.ok(regionalRecord.source.rights.attribution.includes('©swisstopo'));
  assert.equal(level.representation.kind, 'raster-dem-heightfield');
  assert.equal('hillshade' in regionalRecord.source, false);
});

test('grid spacing, information ceiling, delivery level and renderer mesh cannot stand in for each other', () => {
  assert.equal(regionalRecord.source.resolution.gridSpacing.x, 0.5);
  assert.equal(regionalRecord.source.resolution.measurementResolution.status, 'unknown');
  assert.equal(hierarchy.regional[0].levels.at(-1).id, 'z18');
  assert.equal(hierarchy.common.levels.at(-1).id, 'z13');
  assert.equal(hierarchy.common.overzoom.allowed, true);
  const copy = structuredClone(hierarchy);
  copy.regional[0].levels.at(-1).sampleSpacing = known('Synthetic delivery at a different latitude; no source mutation.');
  assert.deepEqual(validateTerrainHierarchy(copy), []);
  assert.deepEqual(copy.regional[0].informationCeiling, hierarchy.regional[0].informationCeiling);
  assert.equal('meshResolution' in hierarchy.regional[0], false);
});

test('coverage, protected interior, transition support and partial per-level support remain independent', () => {
  assert.notDeepEqual(regionalRecord.source.coverage.area, regionalRecord.product.spatial.coverage);
  assert.notDeepEqual(regionalRecord.product.spatial.protectedInterior, regionalRecord.product.spatial.validSupport);
  assert.equal(hierarchy.regional[0].transitionSupport.status, 'unknown');
  assert.equal(hierarchy.regional[0].levels[0].support.state, 'partial');
  assert.match(errorsFor(copy => { delete copy.regional[0].levels[0].support.partition; }), /partial support requires/);
  const copy = structuredClone(hierarchy);
  copy.regional[0].levels[0].support = { state: 'absent', validSupport: unknown('No complete terrain at this level.'), interpretation: 'Explicit absence; no zero-height filling.' };
  assert.deepEqual(validateTerrainHierarchy(copy), []);
});

test('same-family parent refinement is classified separately from common-to-derived handoff', () => {
  assert.equal(classifyTerrainRefinement(hierarchy.regional[0], hierarchy.regional[0]), 'within-family-lod');
  assert.equal(classifyTerrainRefinement(hierarchy.common, hierarchy.transitions[0]), 'source-family-handoff');
  assert.equal(hierarchy.transitions[0].levels[0].parent.family, 'common');
  assert.equal(hierarchy.selection.sourceFamilyHandoff.state, 'unresolved');
  assert.match(errorsFor(copy => { copy.regional[0].levels[1].parent.level = 'missing'; }), /parent level must be declared/);
  assert.match(errorsFor(copy => { copy.regional[0].levels[1].parent.level = 'z18'; }), /parent must be coarser/);
  assert.match(errorsFor(copy => { copy.regional[0].levels[1].parentOperation = unknown('No derivation established.'); }), /declared derivation/);
  assert.match(errorsFor(copy => { copy.common.levels[0].parent = { family: 'transition', level: 'z10' }; copy.transitions[0].levels[0].parent = { family: 'common', level: 'z8' }; }), /acyclic/);
  assert.match(errorsFor(copy => { copy.transitions[0].sourceFamily = 'pretend-regional'; }), /silently change source family/);
});

test('fallback is explicit and never expands coverage or asserts safe handoff', () => {
  assert.equal(hierarchy.selection.missingFineLevel, 'same-family-parent-then-common');
  assert.equal(hierarchy.selection.unsupportedRegional, 'common');
  assert.equal(hierarchy.selection.unavailableTransition, 'common');
  const copy = structuredClone(hierarchy);
  copy.selection.unsupportedRegional = 'unavailable';
  assert.deepEqual(validateTerrainHierarchy(copy), []);
  assert.deepEqual(copy.products[1].product.spatial, hierarchy.products[1].product.spatial);
  assert.equal(copy.selection.sourceFamilyHandoff.state, 'unresolved');
});

test('heterogeneous native heights require explicit composition purpose and spatial contributor reconstruction', () => {
  assert.equal(hierarchy.compositionPolicies[0].heightPolicy.permittedUse, 'visual-representation-only');
  assert.equal(hierarchy.compositionPolicies[0].contribution.semantics, 'signed-operator');
  assert.match(hierarchy.compositionPolicies[0].contribution.interpretation, /not confidence/);
  assert.match(errorsFor(copy => { copy.compositionPolicies[0].heightPolicy.kind = 'declared-common-frame'; }), /explicit visual composition permission/);
  assert.match(errorsFor(copy => { delete copy.compositionPolicies[0].contribution.map; }), /requires a contribution map/);
  assert.match(errorsFor(copy => { copy.products[3].origin.compositionPolicy = 'missing'; }), /requires a composition policy/);
  assert.match(errorsFor(copy => { copy.compositionPolicies[0].products[0].revision = known('different'); }), /exact.*revisions/);
  assert.match(errorsFor(copy => { copy.compositionPolicies[0].products = copy.compositionPolicies[0].products.slice(0, -1); }), /cannot omit contributors/);
});

test('immutable revisions pin preparation and frozen content separately; growing inventories need new revisions', () => {
  const transition = hierarchy.products[3];
  assert.notEqual(transition.identity.revision, transition.identity.contentManifest.sha256);
  assert.equal(transition.identity.contentManifest.sha256, completion.inventoryIdentity);
  assert.match(errorsFor(copy => { copy.products[1].identity.revision = 'changed'; }), /must match/);
  assert.match(errorsFor(copy => { copy.products[1].identity.contentManifest.sha256 = 'bad'; }), /SHA-256/);
  const changed = structuredClone(hierarchy);
  changed.products[3].identity.contentManifest.sha256 = 'a'.repeat(64);
  assert.match(validateTerrainIdentityReuse(hierarchy, changed).join('\n'), /immutable revision reused/);
  changed.products[3].product.revision = known('new-product-revision');
  changed.products[3].identity.revision = 'new-product-revision';
  assert.deepEqual(validateTerrainIdentityReuse(hierarchy, changed), []);
  assert.match(validateTerrainHierarchy(changed).join('\n'), /exact registered product revision/);
  const reordered = structuredClone(hierarchy);
  const binding = reordered.products[0];
  binding.product = Object.fromEntries(Object.entries(binding.product).reverse());
  assert.deepEqual(validateTerrainIdentityReuse(hierarchy, reordered), []);
});

test('continuity success does not erase morphology failure or become a terrain-accuracy claim', () => {
  const evidence = hierarchy.products[3].validation;
  assert.equal(evidence.find(item => item.category === 'numerical-continuity').state, 'passed');
  assert.equal(evidence.find(item => item.category === 'morphology').state, 'failed');
  assert.equal(evidence.some(item => item.category === 'terrain-accuracy'), false);
  assert.match(errorsFor(copy => { copy.products[3].validation[0].evidence = []; }), /assessed validation requires evidence/);
});

test('temporal/change semantics preserve heterogeneous or unknown epochs separately from build dates', () => {
  const copy = structuredClone(hierarchy);
  const product = copy.products[3].product;
  product.temporal = { epochs: known({ description: 'Source-family acquisitions differ; individual cell epochs unknown.', heterogeneous: true }),
    change: { mask: { href: 'docs/atlas/support-extent-diagnostic.json' }, classification: 'Historical/recent glacier change proxy',
      basis: 'Retained inventory union, not measured elevation change.', limitations: 'Cross-epoch difference is not automatically source error.' } };
  assert.deepEqual(validateTerrainHierarchy(copy), []);
  assert.equal(product.temporal.epochs.value.heterogeneous, true);
  assert.notDeepEqual(product.temporal.epochs, product.generation.timestamp);
  const source = structuredClone(regionalRecord.source);
  source.verticalReference.value.heightKind = 'national-height-system';
  source.verticalReference.value.geoidModel = unknown('No complete common-frame transform accepted.');
  assert.deepEqual(validateTerrainSource(source), []);
});

test('generic second-region fixture requires no Swiss heights, geography, transition or delivery encoding', () => {
  const product = secondRegion.products[1].product;
  assert.equal(product.spatial.coverage.value.crs.identifier, 'EPSG:27700');
  assert.equal(product.spatial.protectedInterior, undefined);
  assert.equal(product.delivery.kind, 'other');
  assert.equal(secondRegion.transitions.length, 0);
  assert.equal(secondRegion.regional[0].transitionSupport.status, 'unknown');
  assert.equal(JSON.stringify(product).includes('Swiss'), false);
  const copy = structuredClone(secondRegion);
  copy.regional[0].levels[0].representation = { kind: 'other', form: 'Future local mesh',
    product: copy.regional[0].levels[0].representation.product, context: 'Type extension fixture only',
    adapterContract: { href: 'docs/atlas/terrain-hierarchy-contract.md' } };
  assert.deepEqual(validateTerrainHierarchy(copy), []);
});

test('visual compatibility uses the contract while analytical elevation and map lifecycle stay independent', () => {
  const visual = readFileSync('src/atlas/map/visualTerrainConfig.ts', 'utf8');
  const analytical = readFileSync('src/atlas/terrain/analyticalElevationConfig.ts', 'utf8');
  assert.match(visual, /productionTerrainRegistry/);
  assert.match(analytical, /elevation-tiles-prod\/terrarium/);
  assert.match(analytical, /samplingZoom: 15/);
  for (const path of ['src/atlas/map/AtlasMap.ts', 'src/atlas/map/terrainLayers.ts',
    'src/atlas/terrain/terrainElevationSampler.ts', 'src/atlas/terrain/analyticalElevationConfig.ts']) {
    assert.equal(readFileSync(path, 'utf8').includes('terrainHierarchy'), false);
  }
  for (const binding of hierarchy.products) for (const reference of binding.product.documentation) {
    if (!reference.startsWith('https://')) assert.ok(existsSync(reference), reference);
  }
});
