// Frozen scenes/navigation; no application source edits or parameter search.
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {twoBandEvaluationPlugin} from './two_band_evaluation.mjs';

const provider=process.argv[2]??'transition';
const output=process.argv[3];
const phase=process.argv[4]??'central';
const port=Number(process.argv[5]??4173);
assert.ok(Number.isInteger(port)&&port>=1024&&port<=65535);
const sequenceControl=process.argv[6];
assert.ok(!sequenceControl || (provider!=='transition' && ['centre','west','south'].includes(sequenceControl)));
assert.ok(output);assert.ok(['central','edges','navigation','satellite','controls'].includes(phase));
await mkdir(output,{recursive:true});
const cameras=JSON.parse(await readFile('docs/atlas/two-band-cameras.json','utf8'));
const spec=JSON.parse(await readFile('docs/atlas/riffelhorn-final-reconciliation-experiment.json','utf8'));
const report={provider,phase,baseline:'53b9efbc9e1e2d9393291a1b3fe90abcfcf3f7d0',date:new Date().toISOString(),records:[],navigation:[],responses:[],failedRequests:[],pageErrors:[],consoleErrors:[]};
const protectedFiles=['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts','src/atlas/map/terrainLayers.ts','src/atlas/map/atlasVisuals.ts','src/atlas/map/AtlasMap.ts','src/atlas/terrain/terrainElevationSampler.ts'];
report.productionHashes=Object.fromEntries(await Promise.all(protectedFiles.map(async p=>[p,createHash('sha256').update(await readFile(p)).digest('hex')])));
const server=await createServer({configFile:false,plugins:[react(),twoBandEvaluationPlugin(provider),{name:'private-two-band-map-access',enforce:'pre',transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port,strictPort:true}});
let browser;const pending=[];let page;
async function state(){return page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;return {camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),projection:m.getProjection()?.type,sky:m.getSky(),meshSize:m.terrain?.meshSize,hillshade:m.getLayer('terrain-hillshade').serialize(),usedDEMs:m.terrain?.tileManager.getRenderableTiles().map(t=>m.terrain.tileManager.getSourceTile(t.tileID,true)?.tileID.canonical).filter(Boolean),bounds:m.getBounds().toArray(),centerElevation:m.queryTerrainElevation(m.getCenter()),sources:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.getStyle().sources[id]])),visibleDEMs:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.style.tileManagers[id].getVisibleCoordinates().map(c=>({z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:m.style.tileManagers[id].getTile(c).state}))]))};});}
async function settle(){await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});await page.waitForTimeout(400);await Promise.allSettled(pending);}
async function save(){await writeFile(`${output}/${provider}-${phase}.json`,JSON.stringify(report,null,2)+'\n');}
async function capture(scene){
  const first=report.responses.length;await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settle();
  const current=await state();assert.deepEqual(current.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(current.meshSize,128);
  assert.equal(current.hillshade.paint['hillshade-method'],'igor');assert.equal(current.hillshade.paint['hillshade-illumination-direction'],315);
  assert.equal(current.hillshade.paint['hillshade-illumination-anchor'],'map');
  const filename=`${scene.id}--${provider}.png`;const body=await page.screenshot({path:`${output}/${filename}`});
  report.records.push({scene:scene.id,state:current,filename,sha256:createHash('sha256').update(body).digest('hex'),newResponses:report.responses.length-first});
  console.log('CAPTURE',filename,current.centerElevation);await save();
}
async function startPage(){
  page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1,locale:'en-GB',timezoneId:'Europe/London'});
  page.on('pageerror',e=>report.pageErrors.push(String(e)));page.on('requestfailed',request=>report.failedRequests.push({url:request.url(),error:request.failure()?.errorText}));
  page.on('console',m=>{if(m.type()==='error')report.consoleErrors.push(m.text());});
  page.on('response',response=>{if(response.url().includes('127.0.0.1:4185/tiles/'))pending.push((async()=>{const row={url:response.url(),status:response.status(),cacheControl:response.headers()['cache-control'],cors:response.headers()['access-control-allow-origin'],height:response.headers()['x-meridian-height'],build:response.headers()['x-meridian-build']};try{const body=await response.body();row.bytes=body.length;row.sha256=createHash('sha256').update(body).digest('hex');}catch{row.bodyUnavailable=true;}report.responses.push(row);})());});
  await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Terrain-only evaluation; no Weather publication'}));
  await page.goto(`http://127.0.0.1:${port}/`,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
}
try {
  await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();await startPage();
  if(phase==='central')for(const scene of cameras.central)await capture(scene);
  if(phase==='edges')for(const scene of cameras.edges)await capture(scene);
  if(phase==='controls')for(const scene of cameras.controls)await capture(scene);
  if(phase==='satellite'){
    await settle();
    const button=page.getByRole('button',{name:'Satellite basemap',exact:true});report.satelliteConfigured=!(await button.isDisabled());
    if(report.satelliteConfigured){await button.click();await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.getLayer('satellite-imagery-layer')&&m.getLayoutProperty('satellite-imagery-layer','visibility')==='visible';},null,{timeout:90000});for(const scene of cameras.satellite)await capture(scene);}
  }
  if(phase==='navigation'){
    for(const cache of ['cold','warm'])for(const [sequence,scenes] of Object.entries(cameras.navigation)){
      if(sequenceControl && sequence!==sequenceControl)continue;
      if(cache==='cold'){await page.close();await startPage();}
      await capture({...scenes[0],id:`${sequence}-${cache}-start`});
      for(let j=1;j<scenes.length;j++){
        const scene=scenes[j];const frames=[];const first=report.responses.length;
        await page.evaluate(s=>globalThis.__atlasEvaluationMap.easeTo({...s,duration:1800}),scene);
        for(let i=0;i<9;i++){await page.waitForTimeout(200);frames.push(await state());if([3,6].includes(i))await page.screenshot({path:`${output}/${sequence}-${cache}-${j}-moving-${i}.png`});}
        await settle();const filename=`${sequence}-${cache}-${j}-settled.png`;await page.screenshot({path:`${output}/${filename}`});
        report.navigation.push({sequence,cache,scene,frames,filename,newResponses:report.responses.length-first});await save();
      }
    }
  }
  assert.deepEqual(report.pageErrors,[]);await save();
  for(const file of protectedFiles)assert.equal(createHash('sha256').update(await readFile(file)).digest('hex'),report.productionHashes[file]);
  assert.equal(spec.outerRadiusM,4000);
}catch(e){report.failure=String(e);await save();throw e;}
finally{if(browser)await browser.close();await server.close();}
