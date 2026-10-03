import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from '@playwright/test';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import path from 'node:path';
import { visualEvaluationPlugin } from './terrain_foundation_evaluation.mjs';

// Normal bounded browser traffic, real terrain/basemap/imagery; only rain is synthetic.
// Source substitution exists only in this private Vite server. No product UI or src edits.
const [provider = 'aws', phase = 'core'] = process.argv.slice(2);
assert.ok(['core','extended','operations','controls'].includes(phase));
const root = process.cwd();
const output = path.join(root,'test-results','atlas-terrain-foundation');
await mkdir(output,{recursive:true});
const scenes = [
  {id:'tryfan-landscape',center:[-3.999,53.115],zoom:9.4,pitch:45,bearing:0},
  {id:'tryfan-planning',center:[-3.999,53.115],zoom:11.4,pitch:45,bearing:0},
  {id:'tryfan-close',center:[-3.999,53.115],zoom:13.2,pitch:55,bearing:0},
  {id:'riffelhorn-landscape',center:[7.76121329,45.97910794],zoom:9.4,pitch:45,bearing:0},
  {id:'riffelhorn-planning',center:[7.76121329,45.97910794],zoom:11.4,pitch:45,bearing:0},
  {id:'riffelhorn-close',center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:0},
  {id:'downs-rolling',center:[-.766,50.908],zoom:11.4,pitch:45,bearing:0},
  {id:'cambridge-flat',center:[.12,52.20],zoom:11.4,pitch:0,bearing:0},
];
const diagnostics={pageErrors:[],errors:[],failedRequests:[],httpErrors:[],demResponses:[]};
const report={baselineCheckpoint:'d05f054c96249754cc712044a82d6af1f24d628b',provider,phase,accessTime:new Date().toISOString(),viewport:{width:1440,height:900},scenes,records:[],diagnostics,weather:'Synthetic 1 mm interval-total via unchanged production renderer, not a forecast'};
const terrainUrl=u=>u.startsWith('https://tiles.mapterhorn.com/')||u.startsWith('https://s3.amazonaws.com/elevation-tiles-prod/terrarium/');
const cleanUrl=u=>{try{const v=new URL(u);v.search='';return v.href;}catch{return u;}};
const server=await createServer({configFile:false,root,plugins:[react(),visualEvaluationPlugin(provider),{
  name:'atlas-capture-only',enforce:'pre',transform(code,id){
    if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(', '    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');
  },
}],server:{host:'127.0.0.1',port:4173,strictPort:true}});
let browser;
const pending=[];
const manifestPath=path.join(output,`${provider}-${phase}-manifest.json`);
const frozenFiles=['src/atlas/map/terrainLayers.ts','src/atlas/map/atlasVisuals.ts','src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts','src/atlas/terrain/terrainElevationSampler.ts','src/atlas/map/AtlasMap.ts'];
report.productionFileHashes=Object.fromEntries(await Promise.all(frozenFiles.map(async f=>[f,createHash('sha256').update(await readFile(path.join(root,f))).digest('hex')])));
async function fixtureRoutes(page) {
  const png = await page.evaluate(() => {
    const canvas = document.createElement('canvas'); canvas.width=canvas.height=256;
    const context=canvas.getContext('2d'); const image=context.createImageData(256,256);
    for(let i=0;i<image.data.length;i+=4) { image.data[i]=0;image.data[i+1]=100;image.data[i+3]=255; }
    context.putImageData(image,0,0);return canvas.toDataURL('image/png').split(',')[1];
  });
  const runTime=new Date(new Date().setUTCHours(0,0,0,0)).toISOString();
  report.fixtureRunTime=runTime;
  const timesteps=Array.from({length:24},(_,i)=>({id:`f${String(i+1).padStart(3,'0')}`,forecastHour:i+1,validTime:new Date(Date.parse(runTime)+(i+1)*3600000).toISOString(),minimum:1,maximum:1,tileTemplate:`f${i+1}/{z}/{x}/{y}.png`,accumulationStart:new Date(Date.parse(runTime)+i*3600000).toISOString(),accumulationEnd:new Date(Date.parse(runTime)+(i+1)*3600000).toISOString(),accumulationHours:1}));
  const manifest={schemaVersion:2,id:'atlas-relief-synthetic-rain',model:'GFS',product:'relief-compatibility-fixture',runTime,generatedAt:runTime,
    field:{id:'precipitation',kind:'scalar',sourceParameter:'APCP',sourceLevel:'surface',displayName:'Synthetic precipitation',units:'mm',validRange:[0,655.34],timeSemantics:'interval-total',nativeResolution:{longitudeDegrees:.25,latitudeDegrees:.25}},
    coverage:{bounds:[-180,-85.05112878,180,85.05112878],worldWrap:true,polarLimit:'Web Mercator'},
    tiles:{format:'png',encoding:'uint16-rg',tileSize:256,minZoom:0,maxZoom:2,scale:.01,offset:0,noData:65535,resampling:'bilinear',overzoom:true},timesteps,
    attribution:{label:'Synthetic relief evaluation fixture',url:'https://example.invalid/relief-fixture',source:'Not observed weather'},
  };
  const catalog={schemaVersion:2,model:manifest.model,product:manifest.product,generatedAt:runTime,fields:{precipitation:{runTime,firstValidTime:timesteps[0].validTime,lastValidTime:timesteps.at(-1).validTime,timestepCount:24,manifest:'evaluation/precipitation/manifest.json'}}};
  await page.route('**/weather/gfs/**',route=>{
    const url=route.request().url();
    if(url.includes('latest.json')) return route.fulfill({json:catalog});
    if(url.endsWith('/manifest.json')) return route.fulfill({json:manifest});
    if(url.endsWith('.png')) return route.fulfill({contentType:'image/png',body:Buffer.from(png,'base64')});
    return route.fulfill({status:404,body:'Unknown evaluation fixture'});
  });
}
async function settled(page) {
  await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m&&m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:60000});
  // loaded tiles alone do not establish that terrain RTT refresh/fades have finished.
  await page.evaluate(()=>new Promise((resolve,reject)=>{
    const map=globalThis.__atlasEvaluationMap;
    const timeout=setTimeout(()=>{map.off('idle',done);reject(new Error('Map did not become idle'));},60000);
    function done(){clearTimeout(timeout);resolve();}
    map.once('idle',done);map.triggerRepaint();
  }));
  await page.waitForTimeout(400);
}
async function snapshot(page) {
  return page.evaluate(()=>{
    const m=globalThis.__atlasEvaluationMap,s=m.getStyle();
    const ids=['terrain-dem','terrain-analysis-dem'];
    // Read-only version-specific diagnostics, never used to select or mutate tiles.
    const managers=Object.fromEntries(ids.map(id=>{const tm=m.style.tileManagers[id];
      return [id,tm.getVisibleCoordinates().map(c=>{const t=tm.getTile(c);return {z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:t?.state,demSize:t?.dem?.dim};})];}));
    return {camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),dem:Object.fromEntries(ids.map(id=>[id,s.sources[id]])),managers,
      hillshade:m.getLayer('terrain-hillshade').serialize(),elevation:m.getLayer('terrain-elevation-relief').serialize(),sky:m.getSky(),projection:m.getProjection()?.type ?? "mercator",
      centerElevation:m.queryTerrainElevation(m.getCenter()),meshSize:m.terrain?.meshSize,
      rainVisible:document.querySelector('[aria-label="Precipitation"]')?.getAttribute('aria-pressed'),satellite:document.querySelector('[aria-label="Satellite basemap"]')?.getAttribute('aria-pressed')};
  });
}
async function capture(page,scene) {
  await page.mouse.move(40,40);
  const start=performance.now(),before=diagnostics.demResponses.length;
  await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);
  await settled(page);
  const state=await snapshot(page);
  assert.deepEqual(state.camera.center,scene.center);
  for(const key of ['zoom','pitch','bearing'])assert.ok(Math.abs(state.camera[key]-scene[key])<1e-8,`Camera drift: ${key}`);
  assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});
  assert.equal(state.hillshade.paint['hillshade-method'],'igor');
  assert.equal(state.hillshade.paint['hillshade-illumination-direction'],315);
  assert.equal(state.hillshade.paint['hillshade-illumination-anchor'],'map');
  assert.equal(state.meshSize,128);
  const filename=`${scene.id}--${provider}.png`;
  const pixels=await page.screenshot({path:path.join(output,filename)});
  const performanceEntries=await page.evaluate(()=>performance.getEntriesByType('resource').filter(r=>r.name.includes('tiles.mapterhorn.com/')||r.name.includes('elevation-tiles-prod/terrarium/')).map(r=>({url:r.name,duration:r.duration,transferSize:r.transferSize,encodedBodySize:r.encodedBodySize})));
  report.records.push({scene:scene.id,filename,state,settleMs:performance.now()-start,responsesSinceStart:diagnostics.demResponses.length-before,performanceEntries,sha256:createHash('sha256').update(pixels).digest('hex')});
  await writeFile(manifestPath,JSON.stringify(report,null,2)+'\n');console.log('CAPTURE',filename);
}
try {
  await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
  const page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1,locale:'en-GB',timezoneId:'Europe/London'});
  page.on('pageerror',e=>diagnostics.pageErrors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')diagnostics.errors.push(m.text().replace(/key=[^&\s"]+/g,'key=REDACTED'));});
  page.on('requestfailed',r=>diagnostics.failedRequests.push({url:cleanUrl(r.url()),error:r.failure()?.errorText}));
  page.on('response',r=>{
    if(r.status()>=400)diagnostics.httpErrors.push({url:cleanUrl(r.url()),status:r.status()});
    if(terrainUrl(r.url()))pending.push((async()=>{const row={url:r.url(),status:r.status(),headers:await r.allHeaders()};
      try{const b=await r.body();row.bytes=b.length;row.sha256=createHash('sha256').update(b).digest('hex');}catch{row.bodyUnavailable=true;}
      diagnostics.demResponses.push(row);
    })());
  });
  await fixtureRoutes(page);
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});await settled(page);
  report.loadedProduction=await snapshot(page);
  report.mapLibreVersion=JSON.parse(await readFile(path.join(root,'node_modules/maplibre-gl/package.json'),'utf8')).version;
  if(phase==='core')for(const scene of scenes)await capture(page,scene);
  if(phase==='extended')for(const i of [2,5])await capture(page,{...scenes[i],id:scenes[i].id+'-detail',zoom:16.2});
  if(phase==='controls'){
    await capture(page,{id:'menai-coast',center:[-4.105,53.252],zoom:13.2,pitch:45,bearing:0});
    await capture(page,{id:'global-fallback-nepal-planning',center:[86.86,27.98],zoom:11.4,pitch:45,bearing:0});
    await page.getByRole('button',{name:'Elevation',exact:true}).click();
    await capture(page,{...scenes[1],id:'tryfan-elevation-colors'});
  }
  if(phase==='operations'){
    await capture(page,{...scenes[2],id:'tryfan-rotation-90',bearing:90});
    await capture(page,{...scenes[2],id:'tryfan-rotation-180',bearing:180});
    const navigationStart=performance.now();
    await page.evaluate(()=>globalThis.__atlasEvaluationMap.easeTo({center:[-3.994,53.112],zoom:13.7,bearing:135,duration:600}));await settled(page);
    report.animatedNavigation={settleMs:performance.now()-navigationStart,state:await snapshot(page)};
    await capture(page,{id:'source-boundary',center:[7.6965,45.94],zoom:14.2,pitch:45,bearing:0});
    await capture(page,{id:'anglesey-coast',center:[-4.08,53.34],zoom:13.2,pitch:45,bearing:0});
    await capture(page,{id:'global-fallback-nepal',center:[86.86,27.98],zoom:15.2,pitch:45,bearing:0});
    await page.getByRole('tab',{name:'Journey',exact:true}).click();
    await page.locator('input[type="file"]').setInputFiles(path.join(root,'scripts/route/fixtures/snowdonia-smoke.gpx'));
    await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getSource('planned-route-source'),null,{timeout:60000});
    await page.getByRole('button',{name:'Analyse',exact:true}).waitFor({state:'visible',timeout:60000});await page.waitForTimeout(1800);
    const scene={id:'snowdonia-route-rain',center:[-4.073,53.102],zoom:11.4,pitch:45,bearing:0};
    await page.getByRole('button',{name:'Precipitation',exact:true}).click();
    await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getLayer('global-precipitation-layer-a')||globalThis.__atlasEvaluationMap.getLayer('global-precipitation-layer-b'),null,{timeout:20000});
    await capture(page,scene);
    await page.getByRole('button',{name:'Precipitation',exact:true}).click();
    await page.getByRole('button',{name:'Terrain basemap',exact:true}).waitFor({state:'visible'});
    const sat=page.getByRole('button',{name:'Satellite basemap',exact:true});report.satelliteConfigured=!(await sat.isDisabled());
    if(report.satelliteConfigured){await sat.click();await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getSource('satellite-imagery-source'),null,{timeout:30000});await capture(page,{...scenes[5],id:'riffelhorn-satellite'});}
    for(const zoom of [2.8,5.5,2.8,11.4]){
      await page.evaluate(z=>globalThis.__atlasEvaluationMap.jumpTo({zoom:z}),zoom);await settled(page);
      const s=await snapshot(page);assert.equal(s.projection,zoom<5.5?'globe':'mercator');assert.deepEqual(s.terrain,zoom<5.5?null:{source:'terrain-dem',exaggeration:1.45});
    }
    report.projectionTransitionsPassed=true;
  }
  await Promise.allSettled(pending);assert.deepEqual(diagnostics.pageErrors,[]);
  await writeFile(manifestPath,JSON.stringify(report,null,2)+'\n');console.log(`COMPLETE ${provider} ${phase}: ${report.records.length} captures; ${diagnostics.httpErrors.length} HTTP errors; ${diagnostics.failedRequests.length} cancelled/failed requests`);
} catch(e){report.failure=String(e);await writeFile(manifestPath,JSON.stringify(report,null,2)+'\n');throw e;} finally{if(browser)await browser.close();await server.close();}
