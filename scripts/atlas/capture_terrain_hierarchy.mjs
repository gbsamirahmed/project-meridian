// Explicit evaluation entry point: normal application startup does not use this.
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {hierarchyEvaluationPlugin} from './terrain_hierarchy_evaluation.mjs';
const provider=process.argv[2]??'common';
const output=process.argv[3]??'test-results/atlas-copernicus-common';await mkdir(output,{recursive:true});
const report={baseline:'74ea75b1577fbdd7a85af3a1989ac8aee42c54f0',provider,date:new Date().toISOString(),viewport:{width:1440,height:900},records:[],responses:[],failedRequests:[],pageErrors:[],consoleErrors:[]};
const protectedFiles=['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts','src/atlas/map/terrainLayers.ts','src/atlas/map/atlasVisuals.ts','src/atlas/map/AtlasMap.ts','src/atlas/terrain/terrainElevationSampler.ts'];
report.productionHashes=Object.fromEntries(await Promise.all(protectedFiles.map(async p=>[p,createHash('sha256').update(await readFile(p)).digest('hex')])));
const navigationOnly=process.argv[4]==='navigation';
const discovery=process.argv[4]==='discovery';
const scenes=[
  {id:'landscape',center:[7.76121329,45.97910794],zoom:9.4,pitch:45,bearing:0},
  {id:'planning',center:[7.76121329,45.97910794],zoom:11.4,pitch:45,bearing:0},
  {id:'close',center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:0},
  {id:'overzoom',center:[7.76121329,45.97910794],zoom:16.2,pitch:55,bearing:0},
  {id:'rotation',center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:180},
];

if(discovery){scenes.splice(4);for(const zoom of [12.4,14.2,15.2])scenes.push({id:`scale-${zoom}`,center:[7.76121329,45.97910794],zoom,pitch:55,bearing:0});}else{
for(const [id,center] of [['west',[7.69670098884,45.97927397547]],['south',[7.76094881079,45.93413136870]],['east',[7.82572516627,45.97890488993]],['north',[7.76147820742,46.02408475143]],['south-west',[7.6964,45.9343]],['north-east',[7.826,46.024]]])scenes.push({id:`edge-${id}`,center,zoom:15.2,pitch:55,bearing:0});scenes.push({id:'west-rotation',center:[7.69670098884,45.97927397547],zoom:15.2,pitch:55,bearing:180});}
if(navigationOnly)scenes.splice(1);
const server=await createServer({configFile:false,plugins:[react(),hierarchyEvaluationPlugin(provider),{name:'private-hierarchy-map-access',enforce:'pre',transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port:4173,strictPort:true}});
let browser;const pending=[];
try{
  await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
  const page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1,locale:'en-GB',timezoneId:'Europe/London'});
  page.on('pageerror',e=>report.pageErrors.push(String(e)));
  page.on('requestfailed',request=>report.failedRequests.push({url:request.url(),error:request.failure()?.errorText}));
  page.on('console',message=>{if(message.type()==='error')report.consoleErrors.push(message.text());});
  page.on('response',response=>{if(response.url().includes('127.0.0.1:4183/tiles/'))pending.push((async()=>{
    const row={url:response.url(),status:response.status(),cacheControl:response.headers()['cache-control'],cors:response.headers()['access-control-allow-origin'],contributor:response.headers()['x-meridian-contributor'],heightReference:response.headers()['x-meridian-height'],build:response.headers()['x-meridian-build']};try{const body=await response.body();row.bytes=body.length;row.sha256=createHash('sha256').update(body).digest('hex');}catch{row.bodyUnavailable=true;}report.responses.push(row);
  })());});
  await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Terrain-only evaluation; no Weather publication'}));
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
  for(const scene of scenes){
    const start=performance.now();const first=report.responses.length;await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);
    await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});
    await page.waitForTimeout(1000);await Promise.allSettled(pending);
    const state=await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;return {camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),projection:m.getProjection()?.type??'mercator',sky:m.getSky(),meshSize:m.terrain?.meshSize,hillshade:m.getLayer('terrain-hillshade').serialize(),elevation:m.getLayer('terrain-elevation-relief').serialize(),usedDEMs:m.terrain?.tileManager.getRenderableTiles().map(t=>m.terrain.tileManager.getSourceTile(t.tileID,true)?.tileID.canonical).filter(Boolean),bounds:m.getBounds().toArray(),centerElevation:m.queryTerrainElevation(m.getCenter()),sources:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.getStyle().sources[id]])),visibleDEMs:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.style.tileManagers[id].getVisibleCoordinates().map(c=>{const t=m.style.tileManagers[id].getTile(c);return {z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:t.state,dim:t.dem?.dim};})]))};});
    if(scene.zoom>=5.5){assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(state.meshSize,128);}else assert.equal(state.terrain,null);
    assert.equal(state.hillshade.paint['hillshade-method'],'igor');assert.equal(state.hillshade.paint['hillshade-illumination-direction'],315);
    scene.center.forEach((v,i)=>assert.ok(Math.abs(state.camera.center[i]-v)<1e-10));for(const key of ['zoom','pitch','bearing'])assert.ok(Math.abs(state.camera[key]-scene[key])<1e-8);
    const filename=`${scene.id}--${provider}.png`;const pixels=await page.screenshot({path:`${output}/${filename}`});
    report.records.push({scene:scene.id,state,filename,settleMs:performance.now()-start,newTileResponses:report.responses.length-first,sha256:createHash('sha256').update(pixels).digest('hex')});console.log('CAPTURE',filename,state.centerElevation);
    await writeFile(`${output}/${provider}.json`,JSON.stringify(report,null,2)+'\n');
  }
  if(!discovery){
  report.navigation=[];
  for(const [center,zoom,bearing] of [[[7.76121329,45.97910794],9.4,0],[[7.76121329,45.97910794],11.4,0],[[7.76121329,45.97910794],13.2,0],[[7.76121329,45.97910794],16.2,180],[[7.695,45.9793],15.2,180],[[7.681,45.9793],15.2,0],[[7.76121329,45.97910794],11.4,0]]){
    const first=report.responses.length;await page.evaluate(s=>globalThis.__atlasEvaluationMap.easeTo({...s,pitch:55,duration:1800}),{center,zoom,bearing});
    const frames=[];for(let i=0;i<9;i++){await page.waitForTimeout(200);if(i===4)await page.screenshot({path:`${output}/navigation-${report.navigation.length}-moving--${provider}.png`});frames.push(await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;return {zoom:m.getZoom(),center:m.getCenter().toArray(),elevation:m.queryTerrainElevation(m.getCenter()),moving:m.isMoving(),levels:[...new Set(m.style.tileManagers['terrain-dem'].getVisibleCoordinates().map(c=>c.canonical.z))],actualDEMLevels:[...new Set(m.terrain.tileManager.getRenderableTiles().map(t=>m.terrain.tileManager.getSourceTile(t.tileID,true)?.tileID.canonical.z).filter(z=>z!==undefined))]};}));}
    await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return !m.isMoving()&&m.areTilesLoaded();},null,{timeout:90000});await Promise.allSettled(pending);
    const name=`navigation-${report.navigation.length}--${provider}.png`;await page.screenshot({path:`${output}/${name}`});report.navigation.push({center,zoom,bearing,frames,newTileResponses:report.responses.length-first,filename:name});
  }
  }
  // One continuous zoom/rotation run checks loading without rendering-policy edits.
  await page.evaluate(()=>globalThis.__atlasEvaluationMap.easeTo({center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:180,duration:1800}));
  await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return !m.isMoving()&&m.areTilesLoaded();},null,{timeout:90000});
  await Promise.allSettled(pending);assert.deepEqual(report.pageErrors,[]);await writeFile(`${output}/${provider}.json`,JSON.stringify(report,null,2)+'\n');
}catch(e){report.failure=String(e);await writeFile(`${output}/${provider}.json`,JSON.stringify(report,null,2)+'\n');throw e;}
finally{if(browser)await browser.close();await server.close();}
