import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {createServer} from 'vite';
import {regionalParentEvaluationPlugin} from './regional_parent_evaluation.mjs';

const record=JSON.parse(readFileSync('docs/atlas/regional-parent-product.json','utf8'));
const plan=JSON.parse(readFileSync('docs/atlas/regional-parent-plan.json','utf8'));
const measurements=JSON.parse(readFileSync('docs/atlas/regional-parent-measurements.json','utf8'));
const server=await createServer({configFile:false,appType:'custom',logLevel:'silent',server:{middlewareMode:true}});
const {validateTerrainProduct}=await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataValidation.ts');
await server.close();

test('regional coarse metadata retains LN02, source lineage and unresolved transition',()=>{
  const {product,checks}=record;
  assert.deepEqual(validateTerrainProduct(product),[]);
  assert.equal(product.vertical.kind,'preserved');
  assert.equal(product.vertical.reference.value.identifier,'EPSG:5728');
  assert.deepEqual(product.rights,JSON.parse(readFileSync('docs/atlas/riffelhorn-support-product.json','utf8')).product.rights);
  assert.equal(product.lineage.contributors[0].kind,'source');
  assert.equal(product.lineage.spatialMapping,'uniform');
  assert.equal(product.spatial.transitionSupport.status,'unknown');
  assert.match(product.nodata.value,/partial.*never delivered/);
  assert.match(product.sourceInformation.informationCeiling.value,/Not a regenerated complete fine pyramid/);
  assert.equal(product.revision.value,checks.rebuildIdentity);
  assert.equal(checks.parents.swiss,plan.products.swiss);
  assert.equal(checks.basisTilesByteIdentical,25);
  assert.ok(checks.maxQuantizationM<=1/512);
});

test('support stops delivery without inventing regional parents',()=>{
  const rows=record.checks.levels;
  for(const z of [10,11]){
    const r=rows.find(r=>r.zoom===z);
    assert.equal(r.completeDeliveryTiles,0);
    assert.ok(r.completeCells>0&&r.partialCells>0&&r.unsupportedCells>0);
    assert.equal(r.fullCount,4**(14-z));
  }
  assert.equal(record.product.delivery.zoom.min,12);
  for(const stats of Object.values(measurements.protectedFineModification))assert.equal(stats.rms,0);
  assert.ok(measurements.servedLOD.regional['13-14'].rms<1);
  assert.ok(measurements.servedLOD.regional['11-12'].rms>30);
});

test('evaluation changes visual delivery only; paint and analytical policy untouched',()=>{
  const id='/src/atlas/map/visualTerrainConfig.ts';
  const plug=regionalParentEvaluationPlugin('regional');
  assert.match(plug.load(id),/4184\/tiles\/regional/);
  assert.equal(plug.load('/src/atlas/terrain/analyticalElevationConfig.ts'),undefined);
  const code=readFileSync('src/atlas/map/terrainLayers.ts','utf8');
  const transformed=plug.transform(code,'/src/atlas/map/terrainLayers.ts');
  assert.equal((transformed.match(/minzoom: 8/g)||[]).length,2);
  assert.equal(transformed.replace(/\n      minzoom: 8,\n      bounds: \[[^\]]+\],/g,''),code);
  assert.throws(()=>regionalParentEvaluationPlugin('blend'));
  assert.throws(()=>plug.transform('changed contract','/src/atlas/map/terrainLayers.ts'));
});
