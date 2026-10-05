import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from 'vite';

const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true } });
const load = path => server.ssrLoadModule(`/src/atlas/${path}.ts`);
const { known, unknown } = await load('terrain/metadata/terrainMetadata');
const { AWS_VISUAL_PRODUCT } = await load('terrain/metadata/terrainMetadataExamples');
const { registerTerrainHierarchy } = await load('terrain/runtime/terrainRegistry');
const { selectTerrain } = await load('terrain/runtime/terrainSelector');
const { adaptTerrainToMapLibre } = await load('map/terrainDeliveryAdapter');
const { productionTerrainRegistry } = await load('terrain/runtime/productionTerrainHierarchy');
const { VISUAL_TERRAIN_DEM } = await load('map/visualTerrainConfig');
const { ANALYTICAL_ELEVATION } = await load('terrain/analyticalElevationConfig');
const { createTerrainHierarchyExamples } = await load('terrain/metadata/terrainHierarchyExamples');
await server.close();

const scheme = 'XYZ Web Mercator zoom (delivery)', record = { href: 'docs/atlas/terrain-runtime-selection.md' };
const rectangle = (bounds, crs = 'OGC:CRS84') => ({ kind: 'native-rectangle', crs: { name: crs, identifier: crs }, axisOrder: 'xy', bounds });
const support = area => known({ area, purpose: 'Synthetic eligibility fixture', basis: 'Owned test geometry only; no measured dataset.' });
const ref = product => ({ kind: 'product', id: product.id, revision: product.revision });
const polygon = { kind: 'geojson', geometry: { type: 'Polygon', coordinates: [
  [[-5, -5], [5, -5], [5, 5], [-5, 5], [-5, -5]],
  [[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]],
] } };
function binding(id, area, sourceFamily) {
  const product = structuredClone(AWS_VISUAL_PRODUCT);
  Object.assign(product, { id, name: `Synthetic ${id}`, revision: known('fixture-1'), version: known('fixture'),
    spatial: { coverage: known(rectangle([-15, -15, 15, 15])), validSupport: support(area) },
    lineage: { contributors: [{ kind: 'source', id: `${id}-upstream`, revision: known('fixture-1') }], contributorList: 'complete', spatialMapping: 'uniform', processing: [{ method: 'Synthetic preparation only' }], limitations: 'No terrain data acquired.' },
    vertical: { kind: 'unknown', reason: 'Fixture has no measured height reference.' },
    delivery: { ...product.delivery, tileTemplate: `https://example.invalid/${id}/{z}/{x}/{y}.png`, zoom: { min: 0, max: known(18) } },
    documentation: [record.href] });
  return { product, origin: { kind: 'source-derived', sourceFamily }, validation: [], limitations: [],
    identity: { kind: 'immutable-prepared', revision: 'fixture-1', preparation: record,
      contentManifest: { sha256: '0'.repeat(64), hashScope: 'canonical-inventory', record } } };
}
function fixture() {
  const common = binding('common-fixture', rectangle([-10, -10, 10, 10]), 'common-evidence');
  const regional = binding('regional-fixture', polygon, 'regional-evidence');
  const family = (id, role, product, orders) => ({ id, role, sourceFamily: `${role}-evidence`, levelScheme: scheme,
    levels: orders.map((order, i) => ({ id: `z${order}`, order,
      representation: { kind: 'raster-dem-heightfield', product: ref(product), context: 'Synthetic fixture' },
      derivation: role === 'regional' && order <= 12 ? 'regional-derived-parent' : 'resampled',
      support: { state: 'complete', validSupport: product.spatial.validSupport, interpretation: 'Synthetic complete support' },
      parent: i ? { family: id, level: `z${orders[i - 1]}` } : undefined,
      parentOperation: known({ method: 'Declared synthetic within-family aggregation' }), sampleSpacing: unknown('Delivery spacing varies with location.') })),
    informationCeiling: unknown('A level does not establish independent observations.'), overzoom: { allowed: false, description: 'No implicit rendering overzoom in this fixture.' }, limitations: [] });
  return { id: 'runtime-fixture', revision: '1', purpose: 'visual-terrain', products: [common, regional],
    common: family('common', 'common', common.product, [0, 10, 12, 14, 16]),
    regional: [{ ...family('regional', 'regional', regional.product, [10, 12, 14, 16]), transitionSupport: unknown('No transition declared.') }],
    transitions: [], compositionPolicies: [], renderOnlyContinuity: [], limitations: [],
    selection: { regionalOrder: ['regional'], eligibility: record, missingFineLevel: 'same-family-parent-then-common', unsupportedRegional: 'common', unavailableTransition: 'common', sourceFamilyHandoff: { state: 'unresolved', policy: record } } };
}
const query = (level = 'z16', coordinates = [0, 0]) => ({ location: { coordinates, crs: 'OGC:CRS84' }, scale: { scheme, requestedLevel: level }, provenanceRequirement: 'product-lineage' });
const select = (h, q = query(), options) => selectTerrain(registerTerrainHierarchy(h, options), q);
const errors = mutate => { const h = fixture(); mutate(h); assert.throws(() => registerTerrainHierarchy(h), /Invalid terrain registration/); };

test('registration snapshots canonical metadata and rejects duplicate identities and broken revisions', () => {
  const h = fixture(), original = JSON.stringify(h), registry = registerTerrainHierarchy(h);
  assert.equal(JSON.stringify(h), original);
  h.regional[0].levels.length = 0;
  assert.equal(selectTerrain(registry, query()).family, 'regional');
  assert.throws(() => { registry.hierarchy.regional.length = 0; }, TypeError);
  errors(h => h.products.push(h.products[0]));
  errors(h => h.regional[0].id = 'common');
  errors(h => h.regional[0].levels[0].representation.product.revision = known('missing'));
});

test('invalid/cyclic parents, level delivery ranges and ambiguous ordering fail at registration', () => {
  errors(h => h.regional[0].levels[1].parent.level = 'missing');
  errors(h => h.regional[0].levels[0].parent = { family: 'regional', level: 'z16' });
  errors(h => h.regional[0].levels[3].order = 19);
  errors(h => h.selection.regionalOrder = ['regional', 'regional']);
  assert.throws(() => registerTerrainHierarchy(fixture(), { scaleLevels: [{ scheme, id: 'z16', order: 17 }] }), /ambiguous scale/);
  errors(h => h.common = undefined);
});

test('immutable identity reuse rejects changed prepared content; a new revision must update references', () => {
  const h = fixture(), previous = registerTerrainHierarchy(h);
  h.products[1].identity.contentManifest.sha256 = 'a'.repeat(64);
  assert.throws(() => registerTerrainHierarchy(h, {}, previous), /immutable revision reused/);
  h.products[1].product.revision = known('fixture-2'); h.products[1].identity.revision = 'fixture-2';
  h.regional[0].levels.forEach(l => { l.representation.product = ref(h.products[1].product); });
  assert.equal(registerTerrainHierarchy(h, {}, previous).hierarchy.products[1].identity.revision, 'fixture-2');
});

test('nonrectangular support with holes is authoritative; coverage alone never grants eligibility', () => {
  const h = fixture();
  assert.equal(select(h).family, 'regional');
  assert.equal(select(h, query('z16', [1.5, 1.5])).family, 'common');
  assert.equal(select(h, query('z16', [7, 0])).family, 'common');
  assert.equal(select(h, query('z16', [11, 0])).status, 'unavailable');
  assert.equal(select(h, { ...query(), footprint: rectangle([-0.9, -0.9, 0.9, 0.9]) }).family, 'regional');
  // All outer corners are inside support, but the requested footprint surrounds an excluded hole.
  assert.equal(select(h, { ...query(), footprint: rectangle([0, 0, 3, 3]) }).family, 'common');
  assert.equal(select(h, { ...query(), footprint: rectangle([-6, -1, 0, 1]) }).family, 'common');
});

test('concave edges and multipolygon gaps cannot be accepted by vertex-only containment', () => {
  const h = fixture();
  const area = { kind: 'geojson', geometry: { type: 'Polygon', coordinates: [
    [[-5,-5],[5,-5],[5,5],[2,5],[2,0],[-2,0],[-2,5],[-5,5],[-5,-5]],
  ] } };
  h.products[1].product.spatial.validSupport = support(area);
  h.regional[0].levels.forEach(l => { l.support.validSupport = support(area); });
  assert.equal(select(h, { ...query(), footprint: rectangle([-4, 1, 4, 2]) }).family, 'common');
  area.geometry = { type: 'MultiPolygon', coordinates: [polygon.geometry.coordinates, [[[-9,-4],[-7,-4],[-7,4],[-9,4],[-9,-4]]]] };
  assert.equal(select(h, query('z16', [-8, 0])).family, 'regional');
  assert.equal(select(h, { ...query(), footprint: rectangle([-8, -1, 0, 1]) }).family, 'common');
});

test('partial, unknown, absent and unresolved asset-backed support decline honestly', () => {
  for (const state of ['partial', 'unknown', 'absent']) {
    const h = fixture();
    h.regional[0].levels.forEach(l => { l.support.state = state; l.support.partition = record; });
    const result = select(h);
    assert.equal(result.family, 'common'); assert.equal(result.reason, 'common-fallback');
    assert.equal(result.refinement, 'source-family-handoff');
    assert.ok(result.trace.some(t => t.outcome.startsWith(state)));
  }
  const h = fixture(), area = { kind: 'asset', asset: record, crs: known({ name: 'CRS84', identifier: 'OGC:CRS84' }), interpretation: 'Frozen test geometry record' };
  h.products[1].product.spatial.validSupport = support(area);
  h.regional[0].levels.forEach(l => { l.support.validSupport = support(area); });
  assert.equal(select(h).family, 'common');
  assert.equal(select(h, query(), { resolvedAreas: [{ asset: record, area: polygon }] }).family, 'regional');
  assert.equal(select(h, { ...query(), location: { coordinates: [0,0], crs: 'EPSG:27700' } }).status, 'unavailable');
});

test('a requested regional child falls through declared eligible parents within its source family', () => {
  const h = fixture(); h.regional[0].levels.at(-1).support.state = 'absent';
  const selected = select(h);
  assert.equal(selected.level, 'z14'); assert.equal(selected.reason, 'regional-parent');
  assert.equal(selected.derivation, 'resampled'); assert.equal(selected.refinement, 'within-family-lod');
  h.regional[0].levels.at(-2).support.state = 'unknown';
  const parent = select(h);
  assert.equal(parent.level, 'z12'); assert.equal(parent.derivation, 'regional-derived-parent');
  assert.equal(parent.product.id, h.products[1].product.id);
  assert.deepEqual(parent.informationCeiling, h.regional[0].informationCeiling);
});

test('omitted levels require a declared scale catalogue; explicit overzoom never claims new information', () => {
  const h = fixture();
  assert.equal(select(h, query('z15')).reason, 'undeclared-requested-level');
  const levels = { scaleLevels: [{ scheme, id: 'z15', order: 15 }, { scheme, id: 'z18', order: 18 }] };
  assert.equal(select(h, query('z15'), levels).level, 'z14');
  h.regional[0].overzoom.allowed = true;
  const result = select(h, query('z18'), levels);
  assert.equal(result.level, 'z16'); assert.equal(result.requestedLevel, 'z18');
  assert.equal(result.overzoom, true); assert.equal(result.reason, 'overzoom');
  assert.equal(result.informationCeiling.status, 'unknown');
});

test('common fallback, missing common and unavailable policies are explicit; no fabricated terrain', () => {
  const h = fixture(); h.regional[0].levels.forEach(l => { l.support.state = 'absent'; });
  assert.equal(select(h).refinement, 'source-family-handoff');
  h.common.levels = [];
  assert.equal(select(h).reason, 'common-unavailable');
  h.selection.unsupportedRegional = 'unavailable';
  assert.equal(select(h).reason, 'declared-fallback-unavailable');
  const missing = fixture(); missing.regional[0].levels.at(-1).support.state = 'absent';
  missing.selection.missingFineLevel = 'unavailable';
  assert.equal(select(missing).status, 'unavailable');
});

test('caller-provided previous selection distinguishes direct, within-family and cross-family decisions', () => {
  const h = fixture();
  assert.equal(select(h).refinement, 'direct');
  assert.equal(select(h, { ...query(), previous: { family: 'regional', level: 'z14' } }).refinement, 'within-family-lod');
  assert.equal(select(h, { ...query(), previous: { family: 'common', level: 'z14' } }).refinement, 'source-family-handoff');
  assert.equal(select(h, { ...query(), previous: { family: 'missing', level: 'z14' } }).status, 'unavailable');
});

test('determinism uses declared ordering rather than object iteration or mutable input', () => {
  const h = fixture(), second = structuredClone(h.regional[0]); second.id = 'another-region';
  second.levels.forEach(l => { if (l.parent) l.parent.family = second.id; });
  h.regional.push(second); h.selection.regionalOrder = ['another-region', 'regional'];
  const q = query(), registry = registerTerrainHierarchy(h), first = selectTerrain(registry, q);
  assert.equal(first.family, 'another-region');
  assert.deepEqual(selectTerrain(registry, q), first);
  h.regional.reverse(); h.products.reverse();
  assert.deepEqual(select(h, q), first);
  h.selection.regionalOrder.reverse();
  assert.equal(select(h, q).family, 'regional');
});

test('all ordered regional candidates are considered before applying unavailable fallback policy', () => {
  const h = fixture(), second = structuredClone(h.regional[0]); second.id = 'second';
  second.levels.forEach(l => { if(l.parent) l.parent.family = second.id; });
  h.regional[0].levels.forEach(l => { l.support.state = 'absent'; });
  h.regional.push(second); h.selection.regionalOrder.push('second');
  h.selection.unsupportedRegional = 'unavailable';
  assert.equal(select(h).family,'second');
  const outside = fixture(); outside.selection.missingFineLevel = 'unavailable';
  assert.equal(select(outside,query('z16',[7,0])).family,'common');
});

test('overzoom prohibition and explicit overzoom levels retain actual delivery ceiling', () => {
  const h = fixture(), options = {scaleLevels:[{scheme,id:'z18',order:18}]};
  assert.equal(select(h,query('z18'),options).status,'unavailable');
  h.regional[0].overzoom.allowed = true;
  h.regional[0].levels.at(-1).derivation = 'overzoom';
  h.products[1].product.delivery.zoom.max = known(14);
  const registry = registerTerrainHierarchy(h), result = selectTerrain(registry,query());
  assert.equal(result.overzoom,true); assert.equal(result.reason,'overzoom'); assert.equal(result.level,'z16');
  assert.equal(adaptTerrainToMapLibre(registry,result).maxzoom,14);
  const forged = {...result,product:ref(h.products[0].product)};
  assert.throws(()=>adaptTerrainToMapLibre(registry,forged),/identity does not match/);
});

test('same-source-family parent aliases remain LOD; cross-source parents are explicit common fallback', () => {
  const h = fixture(), parentFamily = structuredClone(h.regional[0]); parentFamily.id='regional-parents';
  parentFamily.levels=parentFamily.levels.slice(0,2);
  parentFamily.levels.forEach(l=>{if(l.parent) l.parent.family=parentFamily.id;});
  h.regional.push(parentFamily); h.selection.regionalOrder.push(parentFamily.id);
  h.regional[0].levels.at(-1).support.state='absent';
  h.regional[0].levels.at(-1).parent={family:parentFamily.id,level:'z12'};
  const result = select(h);
  assert.equal(result.family,'regional-parents'); assert.equal(result.refinement,'within-family-lod');
  h.regional.splice(1); h.selection.regionalOrder.splice(1);
  h.regional[0].levels.at(-1).parent={family:'common',level:'z14'};
  const common = select(h);
  assert.equal(common.family,'common'); assert.equal(common.refinement,'source-family-handoff');
  assert.equal(select(fixture(),{...query(),previous:{family:'regional',level:'z16'}}).refinement,'direct');
});

test('invalid query geometry and incompatible scale schemes are explicit unavailable outcomes', () => {
  assert.equal(select(fixture(),{...query(),location:undefined}).reason,'invalid-spatial-query');
  assert.equal(select(fixture(),{...query(),footprint:rectangle([2,0,1,1])}).reason,'invalid-spatial-query');
  assert.equal(select(fixture(),{...query(),family:'missing'}).reason,'undeclared-requested-family');
  assert.equal(select(fixture(),{...query(),scale:{scheme:'not-registered',requestedLevel:'z16'}}).reason,'undeclared-requested-level');
});

test('native-CRS fixture requires no Swiss coordinates, heights, radial bands or provider rules', () => {
  const h = fixture(), area = rectangle([100,200,200,300], 'LOCAL:XY');
  for (const b of h.products) b.product.spatial.validSupport = support(area);
  for (const f of [h.common, ...h.regional]) for (const l of f.levels) l.support.validSupport = support(area);
  const q = { ...query(), location: { coordinates: [150,250], crs: 'LOCAL:XY' } };
  assert.equal(select(h,q).family, 'regional');
  for (const path of ['terrainSelector.ts','terrainRegistry.ts','terrainSpatialEligibility.ts']) {
    assert.doesNotMatch(readFileSync(`src/atlas/terrain/runtime/${path}`, 'utf8'), /swiss|riffelhorn|copernicus|LN02/i);
  }
});

test('retained Swiss/Copernicus/transition declarations register without reading external data or enabling a blend', () => {
  const json = path => JSON.parse(readFileSync(`docs/atlas/${path}.json`, 'utf8'));
  const records = createTerrainHierarchyExamples({ aws: AWS_VISUAL_PRODUCT,
    common: json('copernicus-common-metadata').product, regional: json('riffelhorn-support-product').product,
    parents: json('regional-parent-product').product, transition: json('two-band-product').product,
    transitionContentSha256: json('two-band-completion').inventoryIdentity,
    contentManifests: { common: json('copernicus-common-generation').manifestSha256,
      regional: json('riffelhorn-support-reproducibility').manifestSha256,
      parents: json('regional-parent-product').product.spatial.coverage.value.asset.sha256 } });
  const h = records.hierarchy, area = rectangle([-5,-5,5,5]);
  // Explicit synthetic eligibility geometry for model tests, not a claim about real Swiss perimeter cells.
  for (const b of h.products) b.product.spatial.validSupport = support(area);
  for (const f of [h.common,...h.regional,...h.transitions]) for (const l of f.levels) l.support = { state: f.id === 'regional' && l.order < 12 ? 'partial' : 'complete', partition:record, validSupport:support(area), interpretation:'Synthetic selection-only fixture, not validation/adoption.' };
  const normal = select(h, query()); assert.equal(normal.family, 'regional');
  const parents = select(h, query('z12')); assert.equal(parents.derivation, 'regional-derived-parent');
  assert.equal(parents.product.id, h.products[2].product.id);
  assert.equal(select(h, { ...query(), family:'transition' }).family, 'common');
  const derived = select(h, { ...query(), family:'transition', provenanceRequirement:'spatial-contributors' }, {enabledTransitions:['transition']});
  assert.equal(derived.family, 'transition'); assert.equal(derived.compositionPolicy, 'historical-two-band');
  const registry = registerTerrainHierarchy(h, {enabledTransitions:['transition']});
  assert.equal(registry.product(derived.product).product.vertical.kind, 'heterogeneous');
  assert.equal(registry.product(derived.product).validation.find(e=>e.category==='morphology').state,'failed');
  const after = JSON.stringify(h); selectTerrain(registry, query()); assert.equal(JSON.stringify(h),after);
});

test('unsupported future representations and delivery schemes fail at adapter boundary, not by coercion', () => {
  const h = fixture();
  h.regional[0].levels.at(-1).representation = { ...h.regional[0].levels.at(-1).representation, kind:'other', form:'Future mesh', adapterContract:record };
  let registry = registerTerrainHierarchy(h);
  assert.throws(()=>adaptTerrainToMapLibre(registry,selectTerrain(registry,query())),/Unsupported terrain representation/);
  h.regional[0].levels.at(-1).representation.kind = 'raster-dem-heightfield';
  h.products[1].product.delivery.scheme = 'tms'; registry = registerTerrainHierarchy(h);
  assert.throws(()=>adaptTerrainToMapLibre(registry,selectTerrain(registry,query())),/Unsupported MapLibre/);
  assert.throws(()=>adaptTerrainToMapLibre(registry,{status:'unavailable'}),/unavailable/);
  h.products[1].product.delivery.scheme = 'xyz'; h.products[1].product.elevationUnit = known('feet');
  registry = registerTerrainHierarchy(h);
  assert.throws(()=>adaptTerrainToMapLibre(registry,selectTerrain(registry,query())),/Unsupported MapLibre/);
  h.products[1].product.elevationUnit = known('metre'); h.products[1].product.delivery.format = 'GeoTIFF';
  registry = registerTerrainHierarchy(h);
  assert.throws(()=>adaptTerrainToMapLibre(registry,selectTerrain(registry,query())),/Unsupported MapLibre/);
});

test('production AWS has explicit unassessed compatibility and maps to byte-for-byte equivalent configuration', () => {
  const q = { ...query('z14'), location:{coordinates:[0,0],crs:'EPSG:3857'} };
  const selected = selectTerrain(productionTerrainRegistry,q);
  assert.equal(selected.support,'legacy-unassessed'); assert.equal(selected.product.id,'aws-terrarium');
  assert.equal(productionTerrainRegistry.product(selected.product).product.vertical.kind,'unknown');
  assert.equal(selectTerrain(registerTerrainHierarchy(productionTerrainRegistry.hierarchy),q).status,'unavailable');
  const attribution = '<a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">Terrain data credits</a>';
  const url='https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png';
  assert.deepEqual(adaptTerrainToMapLibre(productionTerrainRegistry,selected,attribution),{type:'raster-dem',tiles:[url],tileSize:256,encoding:'terrarium',maxzoom:14,attribution});
  assert.deepEqual(VISUAL_TERRAIN_DEM,{tileTemplate:url,encoding:'terrarium',tileSize:256,geometryMaxZoom:14,reliefMaxZoom:15,attribution});
  assert.deepEqual(ANALYTICAL_ELEVATION,{tileTemplate:url,tileSize:256,samplingZoom:15});
  for(const path of ['terrain/analyticalElevationConfig.ts','terrain/terrainElevationSampler.ts']) assert.doesNotMatch(readFileSync(`src/atlas/${path}`,'utf8'),/runtime\/|terrainSelector|productionTerrainRegistry/);
});
