// Explicit evaluation entry point: normal application startup does not use this.
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {commonEvaluationPlugin} from './copernicus_common_evaluation.mjs';
const provider=process.argv[2]??'common';
const output=process.argv[3]??'test-results/atlas-copernicus-common';await mkdir(output,{recursive:true});
const report={baseline:'9f45d3ae7611f5b4710436d6de5318b0aa31ab29',provider,date:new Date().toISOString(),viewport:{width:1440,height:900},records:[],responses:[],failedRequests:[],pageErrors:[],consoleErrors:[]};
const protectedFiles=['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts','src/atlas/map/terrainLayers.ts','src/atlas/map/atlasVisuals.ts','src/atlas/map/AtlasMap.ts','src/atlas/terrain/terrainElevationSampler.ts'];
report.productionHashes=Object.fromEntries(await Promise.all(protectedFiles.map(async p=>[p,createHash('sha256').update(await readFile(p)).digest('hex')])));
const scenes=[
  {id:'landscape',center:[7.76121329,45.97910794],zoom:9.4,pitch:45,bearing:0},
  {id:'planning',center:[7.76121329,45.97910794],zoom:11.4,pitch:45,bearing:0},
  {id:'close',center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:0},
  {id:'overzoom',center:[7.76121329,45.97910794],zoom:16.2,pitch:55,bearing:0},
  {id:'rotation',center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:180},
  {id:'gentler-control',center:[7.35,46.92],zoom:11.4,pitch:45,bearing:0},
  {id:'parent-join',center:[7.76,46.07323062540835],zoom:10.4,pitch:55,bearing:90},
  {id:'below-level-transition',center:[7.76121329,45.97910794],zoom:11.95,pitch:45,bearing:0},
  {id:'above-level-transition',center:[7.76121329,45.97910794],zoom:12.05,pitch:45,bearing:0},
  {id:'return-planning',center:[7.76121329,45.97910794],zoom:11.4,pitch:45,bearing:0},
  {id:'globe-guard',center:[7.76121329,45.97910794],zoom:4.8,pitch:0,bearing:0},
  {id:'mercator-guard',center:[7.76121329,45.97910794],zoom:5.8,pitch:0,bearing:0},
];
if(provider==='aws')scenes.splice(4); // Only bounded baseline control, no repeated source assessment.
const server=await createServer({configFile:false,plugins:[react(),commonEvaluationPlugin(provider),{name:'private-common-map-access',enforce:'pre',transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port:4173,strictPort:true}});
let browser;const pending=[];
try{
  await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
  const page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1,locale:'en-GB',timezoneId:'Europe/London'});
  page.on('pageerror',e=>report.pageErrors.push(String(e)));
  page.on('requestfailed',request=>report.failedRequests.push({url:request.url(),error:request.failure()?.errorText}));
  page.on('console',message=>{if(message.type()==='error')report.consoleErrors.push(message.text());});
  page.on('response',response=>{if(response.url().includes('127.0.0.1:4182/tiles/'))pending.push((async()=>{
    const row={url:response.url(),status:response.status(),cacheControl:response.headers()['cache-control'],cors:response.headers()['access-control-allow-origin'],etag:response.headers().etag};try{const body=await response.body();row.bytes=body.length;row.sha256=createHash('sha256').update(body).digest('hex');}catch{row.bodyUnavailable=true;}report.responses.push(row);
  })());});
  await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Terrain-only evaluation; no Weather publication'}));
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
  for(const scene of scenes){
    const start=performance.now();const first=report.responses.length;await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);
    await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});
    await page.waitForTimeout(1000);await Promise.allSettled(pending);
    const state=await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;return {camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),projection:m.getProjection()?.type??'mercator',sky:m.getSky(),meshSize:m.terrain?.meshSize,hillshade:m.getLayer('terrain-hillshade').serialize(),elevation:m.getLayer('terrain-elevation-relief').serialize(),centerElevation:m.queryTerrainElevation(m.getCenter()),sources:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.getStyle().sources[id]])),visibleDEMs:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.style.tileManagers[id].getVisibleCoordinates().map(c=>{const t=m.style.tileManagers[id].getTile(c);return {z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:t.state,dim:t.dem?.dim};})]))};});
    if(scene.zoom>=5.5){assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(state.meshSize,128);}else assert.equal(state.terrain,null);
    assert.equal(state.hillshade.paint['hillshade-method'],'igor');assert.equal(state.hillshade.paint['hillshade-illumination-direction'],315);
    scene.center.forEach((v,i)=>assert.ok(Math.abs(state.camera.center[i]-v)<1e-10));for(const key of ['zoom','pitch','bearing'])assert.ok(Math.abs(state.camera[key]-scene[key])<1e-8);
    const filename=`${scene.id}--${provider}.png`;const pixels=await page.screenshot({path:`${output}/${filename}`});
    report.records.push({scene:scene.id,state,filename,settleMs:performance.now()-start,newTileResponses:report.responses.length-first,sha256:createHash('sha256').update(pixels).digest('hex')});console.log('CAPTURE',filename,state.centerElevation);
    await writeFile(`${output}/${provider}.json`,JSON.stringify(report,null,2)+'\n');
  }
  // One continuous zoom/rotation run checks loading without rendering-policy edits.
  await page.evaluate(()=>globalThis.__atlasEvaluationMap.easeTo({center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:180,duration:1800}));
  await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return !m.isMoving()&&m.areTilesLoaded();},null,{timeout:90000});
  await Promise.allSettled(pending);assert.deepEqual(report.pageErrors,[]);await writeFile(`${output}/${provider}.json`,JSON.stringify(report,null,2)+'\n');
}catch(e){report.failure=String(e);await writeFile(`${output}/${provider}.json`,JSON.stringify(report,null,2)+'\n');throw e;}
finally{if(browser)await browser.close();await server.close();}
