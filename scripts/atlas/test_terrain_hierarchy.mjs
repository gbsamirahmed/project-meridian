import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {createServer} from 'vite';
import {hierarchyEvaluationPlugin} from './terrain_hierarchy_evaluation.mjs';
const policy=JSON.parse(readFileSync('docs/atlas/terrain-hierarchy-policy.json','utf8'));
const plan=JSON.parse(readFileSync('docs/atlas/terrain-hierarchy-plan.json','utf8'));
const record=JSON.parse(readFileSync('docs/atlas/terrain-hierarchy-product.json','utf8'));
const {product,checks}=record;
const server=await createServer({configFile:false,appType:'custom',logLevel:'silent',server:{middlewareMode:true}});
const {validateTerrainProduct}=await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataValidation.ts');await server.close();

test('composite keeps both native height references and frozen product lineage',()=>{
  assert.deepEqual(validateTerrainProduct(product),[]);
  assert.equal(product.vertical.kind,'heterogeneous');
  assert.deepEqual(product.vertical.parts.map(p=>p.reference.value.identifier),['EPSG:3855','EPSG:5728']);
  assert.deepEqual(product.lineage.contributors.map(p=>p.revision.value),[plan.products.common,plan.products.swiss]);
  assert.equal(product.lineage.contributorList,'complete');assert.equal(product.lineage.spatialMapping,'mask');
  assert.match(product.lineage.contributionMask.interpretation,/not confidence/);
  assert.equal(product.spatial.transitionSupport.status,'unknown');assert.equal(product.spatial.validSupport.status,'unknown');
  assert.equal(product.revision.value,checks.identity);assert.equal(checks.rebuild.identity,checks.identity);
  assert.equal(checks.rebuild.tilesAndMasksMatched,checks.tiles);
  assert.ok(checks.exactSwissBytes);assert.ok(checks.exactCommonThroughZ13);assert.ok(checks.overzoomQuantizationMaxM<=1/512);
});

test('scale and spatial support stay distinct without fabricating source information',()=>{
  assert.equal(policy.regionalTileGate,14);assert.equal(checks.configuration.gate,14);
  assert.equal(product.delivery.zoom.max.value,18);
  assert.match(product.sourceInformation.informationCeiling.value,/resampled/);
  assert.match(product.delivery.availability,/finite/);
  assert.match(product.spatial.coverage.value.interpretation,/not complete source coverage/);
  assert.notDeepEqual(product.spatial.coverage,product.spatial.protectedInterior);
  assert.match(product.fallback.behavior,/not extension of Swiss coverage/);
});

test('evaluation changes only both visual DEM delivery contracts, not relief paint',()=>{
  const id='/src/atlas/map/terrainLayers.ts';const original=readFileSync('.'+id,'utf8');
  for(const strategy of ['common','H0','H1']){
    const plugin=hierarchyEvaluationPlugin(strategy);const result=plugin.transform(original,id);
    assert.equal((result.match(/minzoom: 8,/g)||[]).length,2);
    assert.equal(result.replace(/\n      minzoom: 8,\n      bounds: \[[^\n]+\],/g,''),original);
    const code=plugin.load('/src/atlas/map/visualTerrainConfig.ts');
    const config=JSON.parse(code.slice('export const VISUAL_TERRAIN_DEM='.length,-1));
    assert.equal(config.geometryMaxZoom,18);assert.equal(config.reliefMaxZoom,18);
    assert.equal(config.encoding,'terrarium');assert.equal(config.tileSize,256);
    assert.match(config.tileTemplate,new RegExp(`/tiles/${strategy}/`));
    assert.equal(plugin.load('/src/atlas/terrain/analyticalElevationConfig.ts'),undefined);
    assert.throws(()=>plugin.transform('',id));
  }
  assert.throws(()=>hierarchyEvaluationPlugin('H2'));
});

test('production policies and startup remain independent of the experiment',()=>{
  for(const file of ['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts']){
    const text=readFileSync(file,'utf8');assert.match(text,/elevation-tiles-prod\/terrarium/);assert.doesNotMatch(text,/terrain_hierarchy|copernicus|metadata\//i);
  }
  assert.match(readFileSync('src/atlas/terrain/analyticalElevationConfig.ts','utf8'),/samplingZoom: 15/);
  assert.match(readFileSync('src/atlas/map/terrainLayers.ts','utf8'),/TERRAIN_EXAGGERATION = 1\.45/);
  assert.doesNotMatch(readFileSync('vite.config.ts','utf8'),/terrain_hierarchy|copernicus_common/);
});
