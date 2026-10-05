import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {createServer} from 'vite';
import {COMMON_VISUAL,COMMON_BOUNDS,commonEvaluationPlugin} from './copernicus_common_evaluation.mjs';
const metadata=JSON.parse(readFileSync('docs/atlas/copernicus-common-metadata.json','utf8'));
const acq=JSON.parse(readFileSync('docs/atlas/copernicus-common-acquisition.json','utf8'));
const generation=JSON.parse(readFileSync('docs/atlas/copernicus-common-generation.json','utf8'));
const server=await createServer({configFile:false,appType:'custom',logLevel:'silent',server:{middlewareMode:true}});
const {validateTerrainSource,validateTerrainProduct}=await server.ssrLoadModule('/src/atlas/terrain/metadata/terrainMetadataValidation.ts');await server.close();
test('frozen source selection and delivery product fit existing model',()=>{
  assert.deepEqual(validateTerrainSource(metadata.source),[]);assert.deepEqual(validateTerrainProduct(metadata.product),[]);
  assert.equal(metadata.source.assets.length,6);assert.equal(acq.assets.filter(a=>a.reused).length,2);
  assert.equal(metadata.source.revision.value,acq.identity);assert.equal(metadata.product.revision.value,generation.identity);
  assert.equal(metadata.product.lineage.contributors[0].revision.value,acq.identity);
});
test('preserved EGM2008 and source information are independent of delivery zoom',()=>{
  const {source,product}=metadata;assert.equal(source.resolution.gridSpacing.unit,'arcsecond');assert.equal(source.resolution.measurementResolution.status,'unknown');
  assert.equal(product.vertical.kind,'preserved');assert.equal(product.vertical.reference.value.identifier,'EPSG:3855');
  assert.equal(product.delivery.zoom.max.value,13);assert.match(product.sourceInformation.informationCeiling.value,/adds no observations/);
  assert.equal(product.spatial.protectedInterior,undefined);assert.equal(product.fallback,undefined);assert.equal(product.spatial.transitionSupport.status,'unknown');
  assert.notDeepEqual(source.coverage.area.value.bounds,product.spatial.coverage.value.bounds);
});
test('evaluation changes both visual source contracts and preserves presentation',()=>{
  const id='/src/atlas/map/terrainLayers.ts';const original=readFileSync('.'+id,'utf8');const plugin=commonEvaluationPlugin('common');
  const result=plugin.transform(original,id);assert.equal((result.match(/minzoom: 8,/g)||[]).length,2);assert.equal((result.match(/bounds:/g)||[]).length,2);
  assert.equal(result.replace(/\n      minzoom: 8,\n      bounds: \[[^\n]+\],/g,''),original);
  assert.equal(plugin.load('/src/atlas/terrain/analyticalElevationConfig.ts'),undefined);assert.equal(commonEvaluationPlugin('aws').transform(original,id),undefined);
  assert.equal(COMMON_VISUAL.geometryMaxZoom,13);assert.equal(COMMON_VISUAL.tileSize,256);assert.equal(COMMON_VISUAL.encoding,'terrarium');assert.deepEqual(COMMON_BOUNDS,metadata.product.spatial.coverage.value.bounds);
  assert.throws(()=>plugin.transform('',id));assert.throws(()=>commonEvaluationPlugin('swiss'));
});
test('production visual and analytical AWS policies remain independent and untouched',()=>{
  for(const p of ['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts']){
    const source=readFileSync(p,'utf8');assert.match(source,p.includes('visualTerrainConfig')?/productionTerrainRegistry/:/elevation-tiles-prod\/terrarium/);assert.doesNotMatch(source,/copernicus|metadata\//i);
  }
  assert.match(readFileSync('src/atlas/terrain/analyticalElevationConfig.ts','utf8'),/samplingZoom: 15/);
  assert.doesNotMatch(readFileSync('vite.config.ts','utf8'),/copernicus_common/);
});
