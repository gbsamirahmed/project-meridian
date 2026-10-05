import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {readFileSync} from 'node:fs';
import {tileFootprint} from './terrainProofGateway.mjs';
const s=await createServer({configFile:false,logLevel:'silent',server:{middlewareMode:true}});
const load=p=>s.ssrLoadModule(`/src/atlas/${p}.ts`);
const {createTryfanTerrainProof,TRYFAN_SOURCE,TRYFAN_PRODUCT}=await load('terrain/metadata/tryfanTerrainProof');
const {selectTerrain}=await load('terrain/runtime/terrainSelector');
const {registerTerrainHierarchy}=await load('terrain/runtime/terrainRegistry');
const {adaptTerrainToMapLibre}=await load('map/terrainDeliveryAdapter');
const {validateTerrainSource,validateTerrainProduct}=await load('terrain/metadata/terrainMetadataValidation');
const {VISUAL_TERRAIN_DEM}=await load('map/visualTerrainConfig');
const {ANALYTICAL_ELEVATION}=await load('terrain/analyticalElevationConfig');
await s.close();
const r=createTryfanTerrainProof(),scheme=r.hierarchy.common.levelScheme;
const query=(z=17,coordinates=[-3.999,53.115])=>({location:{coordinates,crs:'OGC:CRS84'},scale:{scheme,requestedLevel:`z${z}`},provenanceRequirement:'product-lineage'});
const select=(q=query(),reg=r)=>selectTerrain(reg,q);

test('real Welsh source and immutable product validate without external assets; native vertical uncertainty retained',()=>{
  assert.deepEqual(validateTerrainSource(TRYFAN_SOURCE),[]);assert.deepEqual(validateTerrainProduct(TRYFAN_PRODUCT),[]);
  assert.equal(TRYFAN_SOURCE.horizontalReference.value.identifier,'EPSG:27700');assert.equal(TRYFAN_SOURCE.verticalReference.status,'unknown');
  assert.equal(TRYFAN_PRODUCT.vertical.kind,'preserved');assert.equal(TRYFAN_PRODUCT.vertical.reference.status,'unknown');
  const catalog=JSON.parse(readFileSync('docs/atlas/tryfan-data-catalog.json'));const input=catalog.products[0].files.find(f=>f.destination.endsWith('tryfan-004-dtm-1m.tif'));
  assert.equal(TRYFAN_SOURCE.assets[0].sha256,input.sha256);assert.equal(input.raster.width*input.raster.height,9000000);
});
test('Tryfan fine and regional parent selections retain exact product and within-family identity',()=>{
  const fine=select();assert.equal(fine.family,'welsh-regional');assert.equal(fine.level,'z17');assert.equal(fine.product.revision.value,TRYFAN_PRODUCT.revision.value);
  const parent=select({...query(14),previous:{family:fine.family,level:fine.level}});
  assert.equal(parent.derivation,'regional-derived-parent');assert.equal(parent.refinement,'within-family-lod');assert.equal(parent.sourceFamily,fine.sourceFamily);
  assert.deepEqual(select(),fine);
});
test('coarse partial support and real geographic edge select explicit common handoff',()=>{
  for(const q of [query(13),query(17,[-4.03,53.115]),query(17,[-4.0193,53.10])]){
    const d=select({...q,previous:{family:'welsh-regional',level:'z17'}});assert.equal(d.family,r.hierarchy.common.id);assert.equal(d.refinement,'source-family-handoff');assert.equal(d.handoffState,'unresolved');
  }
  const raw=readFileSync('src/atlas/terrain/runtime/terrainSelector.ts','utf8');assert.doesNotMatch(raw,/Tryfan|Wales|Swiss|LN02|LV95|Riffelhorn|Copernicus/);
});
test('requested child unavailable reuses an eligible real Welsh-derived parent; no new information from overzoom',()=>{
  const h=structuredClone(r.hierarchy);
  const child=h.regional[0].levels.find(l=>l.id==='z17');child.support={state:'absent',validSupport:child.support.validSupport,interpretation:'Simulated unavailable child, not a source change.'};
  const absent=registerTerrainHierarchy(h,r.options),d=select(query(17),absent);
  assert.equal(d.level,'z16');assert.equal(d.reason,'regional-parent');assert.equal(d.refinement,'within-family-lod');assert.equal(adaptTerrainToMapLibre(absent,d).maxzoom,16);
  h.regional[0].levels=h.regional[0].levels.filter(l=>l.id!=='z17');h.regional[0].overzoom.allowed=false;
  const reg=registerTerrainHierarchy(h,r.options);
  assert.equal(select(query(17),reg).family,r.hierarchy.common.id);
  const over=select(query(18));assert.equal(over.level,'z17');assert.equal(over.overzoom,true);assert.equal(adaptTerrainToMapLibre(r,over).maxzoom,17);assert.match(over.informationCeiling.value,/1m distributed/);
});
test('whole tile support rather than product rectangle determines eligibility',()=>{
  assert.equal(select({...query(14),location:undefined,footprint:tileFootprint(14,8010,5328)}).family,'welsh-regional');
  assert.equal(select({...query(14),location:undefined,footprint:tileFootprint(14,8009,5328)}).family,r.hierarchy.common.id);
});
test('same adapter handles Welsh and common; production and analytical configurations remain independent',()=>{
  const local=adaptTerrainToMapLibre(r,select());assert.equal(local.encoding,'terrarium');assert.equal(local.tileSize,256);assert.equal(local.minzoom,14);assert.equal(local.maxzoom,17);
  const common=select({...query(15),family:r.hierarchy.common.id});assert.equal(common.family,r.hierarchy.common.id);
  const delivery=adaptTerrainToMapLibre(r,common);assert.equal(delivery.tiles[0],VISUAL_TERRAIN_DEM.tileTemplate);assert.equal(delivery.maxzoom,15);
  assert.equal(ANALYTICAL_ELEVATION.samplingZoom,15);assert.equal(VISUAL_TERRAIN_DEM.geometryMaxZoom,14);assert.equal(VISUAL_TERRAIN_DEM.reliefMaxZoom,15);
});

test('Welsh registration coexists with an explicitly synthetic second region; only declared order breaks overlapping eligibility',()=>{
  const h=structuredClone(r.hierarchy),binding=structuredClone(h.products[1]);
  binding.product.id='synthetic-coexistence-fixture';binding.product.name='Synthetic coexistence control, not another acquired region';
  binding.origin.sourceFamily='synthetic-source-family';binding.product.lineage.contributors[0].id='synthetic-upstream';
  binding.product.vertical={kind:'unknown',reason:'Synthetic fixture has no acquired height datum.'};
  binding.product.revision={status:'known',value:'synthetic-fixture'};binding.identity.revision='synthetic-fixture';binding.identity.contentManifest.sha256='0'.repeat(64);
  binding.product.lineage.processing=[{method:'Synthetic metadata control; no data or measurement'}];
  const family=structuredClone(h.regional[0]);family.id='synthetic-region';family.sourceFamily='synthetic-source-family';
  family.levels.forEach(l=>{l.representation.product.id=binding.product.id;l.representation.product.revision=binding.product.revision;if(l.parent)l.parent.family=family.id;});
  h.products.push(binding);h.regional.push(family);h.selection.regionalOrder.push(family.id);
  assert.equal(select(query(),registerTerrainHierarchy(h,r.options)).family,'welsh-regional');
  h.selection.regionalOrder.reverse();assert.equal(select(query(),registerTerrainHierarchy(h,r.options)).family,'synthetic-region');
  h.selection.regionalOrder=['welsh-regional','welsh-regional'];assert.throws(()=>registerTerrainHierarchy(h,r.options),/Invalid terrain registration/);
});
