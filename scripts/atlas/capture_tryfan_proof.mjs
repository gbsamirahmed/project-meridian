// Explicit experimental entry point; normal Vite/application startup is untouched.
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {createTerrainProofGateway} from './terrainProofGateway.mjs';

const data=process.argv[2],output=process.argv[3],provider=process.argv[4]??'hierarchy';
if(!data||!output||!['hierarchy','aws'].includes(provider))throw new Error('Usage: node capture_tryfan_proof.mjs DATA OUTPUT [hierarchy|aws]');
await mkdir(output,{recursive:true});
const loader=await createServer({configFile:false,logLevel:'silent',server:{middlewareMode:true}});
const {createTryfanTerrainProof}=await loader.ssrLoadModule('/src/atlas/terrain/metadata/tryfanTerrainProof.ts');
const {selectTerrain}=await loader.ssrLoadModule('/src/atlas/terrain/runtime/terrainSelector.ts');
const {adaptTerrainToMapLibre}=await loader.ssrLoadModule('/src/atlas/map/terrainDeliveryAdapter.ts');
const registry=createTryfanTerrainProof();await loader.close();
const setup=selectTerrain(registry,{location:{coordinates:[-3.999,53.115],crs:'OGC:CRS84'},scale:{scheme:registry.hierarchy.common.levelScheme,requestedLevel:'z17'},provenanceRequirement:'product-lineage',...(provider==='aws'?{family:registry.hierarchy.common.id}:{})});
const adapted=adaptTerrainToMapLibre(registry,setup);
const gateway=createTerrainProofGateway({registry,selectTerrain,adaptTerrainToMapLibre,productRoots:{'tryfan-welsh-regional-v2':path.join(data,'derived/atlas/tryfan/tryfan-welsh-regional-v2')},commonOnly:provider==='aws'});
const visual={tileTemplate:'http://127.0.0.1:4186/terrain/{z}/{x}/{y}.png',tileSize:adapted.tileSize,encoding:adapted.encoding,geometryMaxZoom:provider==='aws'?14:adapted.maxzoom,reliefMaxZoom:provider==='aws'?15:adapted.maxzoom,attribution:'Welsh Government information licensed under OGL v3.0; AWS terrain data credits (experimental hierarchy)'};
const report={baseline:'ba24e54',provider,setup,adapted,viewport:{width:1440,height:900},scenes:[],navigation:[],responses:[],failures:[],pageErrors:[]};
const protectedFiles=['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts','src/atlas/map/terrainLayers.ts','src/atlas/map/AtlasMap.ts','src/atlas/map/atlasVisuals.ts','src/atlas/terrain/terrainElevationSampler.ts'];
report.productionHashes=Object.fromEntries(await Promise.all(protectedFiles.map(async f=>[f,createHash('sha256').update(await readFile(f)).digest('hex')])));
const server=await createServer({configFile:false,plugins:[react(),{name:'second-region-proof-only',enforce:'pre',load(id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(visual)};`;},transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port:4173,strictPort:true}});
const scenes=[
 {id:'landscape',center:[-3.999,53.115],zoom:9.4,pitch:45,bearing:0},
 {id:'planning',center:[-3.999,53.115],zoom:11.4,pitch:45,bearing:0},
 {id:'benchmark-close',center:[-3.999,53.115],zoom:13.2,pitch:55,bearing:0},
 {id:'regional-parent',center:[-3.999,53.115],zoom:15.2,pitch:0,bearing:0},
 {id:'regional-child',center:[-3.999,53.115],zoom:16.2,pitch:35,bearing:0},
 {id:'regional-detail',center:[-3.999,53.115],zoom:17.2,pitch:45,bearing:0},
 {id:'regional-rotation',center:[-3.999,53.115],zoom:16.2,pitch:35,bearing:180},
 {id:'support-edge',center:[-4.018,53.115],zoom:16.2,pitch:35,bearing:0},
 {id:'outside',center:[-4.023,53.115],zoom:16.2,pitch:35,bearing:180},
];
let browser;
try{
 await gateway.listen();await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
 const page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1});
 page.on('pageerror',e=>report.pageErrors.push(String(e)));page.on('requestfailed',r=>report.failures.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.url().includes(':4186/terrain/'))report.responses.push({url:r.url(),status:r.status(),family:r.headers()['x-terrain-family'],level:r.headers()['x-terrain-level']});});
 await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Terrain-only proof; no Weather data publication'}));
 await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
 const settle=()=>page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});
 const snapshot=()=>page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;return{center:m.getCenter().toArray(),zoom:m.getZoom(),terrain:m.getTerrain(),projection:m.getProjection(),elevation:m.queryTerrainElevation(m.getCenter()),mesh:m.terrain?.meshSize,hillshade:m.getLayer('terrain-hillshade').serialize(),sources:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.getStyle().sources[id]])),actualDEMs:m.terrain?.tileManager.getRenderableTiles().map(t=>m.terrain.tileManager.getSourceTile(t.tileID,true)?.tileID.canonical).filter(Boolean)};});
 for(const scene of scenes){
  await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settle();await page.waitForTimeout(750);
  const state=await snapshot();assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(state.mesh,128);assert.equal(state.hillshade.paint['hillshade-method'],'igor');
  const filename=`${scene.id}--${provider}.png`;const pixels=await page.screenshot({path:path.join(output,filename)});report.scenes.push({scene,state,filename,sha256:createHash('sha256').update(pixels).digest('hex')});console.log('CAPTURE',provider,scene.id,state.elevation);
  await writeFile(path.join(output,`${provider}.json`),JSON.stringify(report,null,2)+'\n');
 }
 for(const scene of [scenes[3],scenes[4],scenes[5],scenes[6],scenes[7],scenes[8],scenes[1]]){
  await page.evaluate(s=>globalThis.__atlasEvaluationMap.easeTo({...s,duration:1500}),scene);const frames=[];
  for(let i=0;i<6;i++){await page.waitForTimeout(250);frames.push(await snapshot());if(i===2)await page.screenshot({path:path.join(output,`moving-${report.navigation.length}--${provider}.png`)});}
  await settle();report.navigation.push({target:scene,frames});
 }
 assert.deepEqual(report.pageErrors,[]);
}catch(e){report.failure=String(e);throw e;}
finally{
 report.requests=gateway.records;await writeFile(path.join(output,`${provider}.json`),JSON.stringify(report,null,2)+'\n');
 if(browser)await browser.close();await server.close();await gateway.close();
}
