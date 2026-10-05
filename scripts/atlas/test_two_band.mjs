import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {createServer} from 'vite';
import {twoBandEvaluationPlugin} from './two_band_evaluation.mjs';

const spec=JSON.parse(readFileSync('docs/atlas/riffelhorn-final-reconciliation-experiment.json','utf8'));
const cameras=JSON.parse(readFileSync('docs/atlas/two-band-cameras.json','utf8'));

test('isolated transition adapter retains production paint and analytical policy',()=>{
  const plugin=twoBandEvaluationPlugin('transition');
  assert.match(plugin.load('/src/atlas/map/visualTerrainConfig.ts'),/4185\/tiles\/transition/);
  assert.equal(plugin.load('/src/atlas/terrain/analyticalElevationConfig.ts'),undefined);
  const paint=readFileSync('src/atlas/map/terrainLayers.ts','utf8');
  const changed=plugin.transform(paint,'/src/atlas/map/terrainLayers.ts');
  assert.equal(changed.replace(/\n      minzoom: 8,\n      bounds: \[[^\]]+\],/g,''),paint);
  assert.throws(()=>twoBandEvaluationPlugin('tuned'));
  for(const path of ['vite.config.ts','src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts'])
    assert.doesNotMatch(readFileSync(path,'utf8'),/two.band|4185/);
});

test('frozen bands and camera matrix include every sector and rotation',()=>{
  assert.deepEqual([spec.protectedRadiusM,spec.detailTaperStartRadiusM,spec.outerRadiusM],[1500,3000,4000]);
  assert.equal(cameras.central.length,24);assert.equal(cameras.edges.length,128);
  assert.deepEqual([...new Set(cameras.edges.map(s=>s.bearing))].sort((a,b)=>a-b),[0,90,180,270]);
  assert.equal(cameras.controls.length,18);assert.equal(cameras.satellite.length,3);
  assert.equal(Object.keys(cameras.navigation).length,3);
  assert.match(spec.heightPolicy,/heterogeneous/);assert.match(spec.provenance,/negative/);
  assert.match(spec.terminalRule,/regardless of result/);
});

test('derived product preserves heterogeneous heights and signed contributor lineage',async()=>{
  const server=await createServer({configFile:false,appType:'custom',logLevel:'silent',server:{middlewareMode:true}});
  try {
    const {validateTerrainProduct}=await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataValidation.ts');
    const record=JSON.parse(readFileSync('docs/atlas/two-band-product.json','utf8'));
    assert.deepEqual(validateTerrainProduct(record.product),[]);
    assert.deepEqual(record.sourceProductIdentities,spec.inputs);
    assert.equal(record.product.vertical.kind,'heterogeneous');
    assert.equal(record.product.lineage.contributors.length,3);
    assert.equal(record.product.lineage.spatialMapping,'mask');
    assert.match(record.product.lineage.contributionMask.interpretation,/not confidence/);
    assert.match(record.product.vertical.description,/never analytical/);
    assert.match(record.product.delivery.availability,/Sparse/);
    assert.equal(record.product.revision.value,record.build.identity);
  } finally {await server.close();}
});
