import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from 'vite';
import {readFile} from 'node:fs/promises';
import {tileArea} from './swissimage_geometry.mjs';
import {tileFootprint} from './terrainProofGateway.mjs';

test('connected delivered tile support removes internal row/tile edges',async()=>{
 const loader=await createServer({configFile:false,logLevel:'silent',server:{middlewareMode:true}});
 try{const {containsTerrainQuery}=await loader.ssrLoadModule('/src/atlas/terrain/runtime/terrainSpatialEligibility.ts');
  const files=[{path:'tiles/4/8/5.png'},{path:'tiles/4/9/5.png'},{path:'tiles/4/8/6.png'},{path:'tiles/4/9/6.png'}];
  const area=tileArea(files,4);assert.equal(area.geometry.coordinates.length,1);
  assert.equal(containsTerrainQuery(area,{footprint:tileFootprint(3,4,3)}),'outside');
  for(const f of files){const [,z,x,y]=f.path.match(/tiles\/(\d+)\/(\d+)\/(\d+)/);assert.equal(containsTerrainQuery(area,{footprint:tileFootprint(+z,+x,+y)}),'inside');}
  const q={kind:'geojson',geometry:{type:'Polygon',coordinates:[[[1,25],[40,25],[40,50],[1,50],[1,25]]]}};
  assert.equal(containsTerrainQuery(area,{footprint:q}),'inside');
 }finally{await loader.close();}
});
test('support tracing rejects unclassified corner-touching inventories',()=>{
 assert.throws(()=>tileArea([{path:'tiles/4/8/5.png'},{path:'tiles/4/9/6.png'}],4),/Corner-touching/);
});
test('frozen camera IDs and values remain recoverable without external imagery',async()=>{
 const c=JSON.parse(await readFile('docs/atlas/two-band-cameras.json','utf8'));
 for(const id of ['centre-12.4-b0','centre-14.2-b0','centre-16.2-b0','centre-16.2-b180']){
  const pose=c.central.find(p=>p.id===id);assert.ok(pose);assert.deepEqual(pose.center,[7.76121329,45.97910794]);assert.equal(pose.pitch,55);
 }
});
test('baseline tooling is opt-in and does not introduce correction or production imports',async()=>{
 const runtime=await readFile('src/atlas/map/visualTerrainConfig.ts','utf8');
 assert.ok(!runtime.includes('swissimage'));
 const capture=await readFile('scripts/atlas/capture_swissimage_baseline.mjs','utf8');
 assert.ok(capture.includes('forwardConsole:false'));assert.ok(capture.includes('u.origin+u.pathname'));
 assert.ok(!capture.includes('raster-brightness'));assert.ok(!capture.includes('raster-contrast'));
});
test('retained appearance metadata separates source, product, geometry and display',async()=>{
 const r=JSON.parse(await readFile('docs/atlas/swissimage-source-derived-baseline.json','utf8'));
 assert.equal(r.source.assets.length,4);assert.equal(r.source.sourceBytes,186259028);
 assert.deepEqual(r.source.sourceBounds,[2624000,1091000,2626000,1093000]);
 assert.equal(r.source.nominalUpstreamInformationMetres,.25);assert.equal(r.source.distributedSpacingMetres,.1);
 assert.equal(r.source.acquisition.pixelTimestamp,'UNKNOWN');assert.equal(r.source.acquisition.sun,'UNKNOWN');
 assert.equal(r.product.lineage.radiometricCorrection,'none');assert.equal(r.product.lineage.syntheticFilling,'none');
 assert.match(r.product.origin,/source-derived regional/);assert.equal(r.product.delivery.maxzoom,18);
 assert.equal(r.levels.reduce((n,l)=>n+l.tileCount,0),542);assert.equal(r.capture.visualIndex.length,8);
 assert.equal(r.geometry.length,2);assert.equal(r.productionUnchanged.analyticalElevation,'independent AWS z15');
 assert.ok(r.independentFullRebuildManifestIdentical);assert.equal(r.verification.parentMaxLinearError<3e-8,true);
 for(const f of r.source.assets)assert.match(f.sha256,/^[0-9a-f]{64}$/);
});
