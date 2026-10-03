import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {riffelhornEvaluationPlugin} from './riffelhorn_evaluation.mjs';

const [provider='aws',phase='inside']=process.argv.slice(2);
assert.ok(['inside','boundary','operations'].includes(phase));
const output='test-results/atlas-riffelhorn';await mkdir(output,{recursive:true});
const report={baseline:'340bf521bc8a042ac34d5a28d95351b9f6fb5077',provider,phase,date:new Date().toISOString(),viewport:{width:1440,height:900},records:[],responses:[],httpErrors:[],failedRequests:[],pageErrors:[]};
const protectedFiles=['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts','src/atlas/map/terrainLayers.ts','src/atlas/map/atlasVisuals.ts','src/atlas/map/AtlasMap.ts','src/atlas/terrain/terrainElevationSampler.ts'];
report.productionHashes=Object.fromEntries(await Promise.all(protectedFiles.map(async p=>[p,createHash('sha256').update(await readFile(p)).digest('hex')])));
const scenes={
  inside:[
    {id:'landscape',center:[7.76121329,45.97910794],zoom:9.4,pitch:45,bearing:0},
    {id:'planning',center:[7.76121329,45.97910794],zoom:11.4,pitch:45,bearing:0},
    {id:'close',center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:0},
    {id:'detail',center:[7.76121329,45.97910794],zoom:16.2,pitch:55,bearing:0},
  ],
  boundary: JSON.parse(await readFile('scripts/atlas/riffelhorn-boundary-cameras.json','utf8')),
  operations:[
    {id:'rotation-90',center:[7.76121329,45.97910794],zoom:15.2,pitch:55,bearing:90},
    {id:'rotation-180',center:[7.76121329,45.97910794],zoom:15.2,pitch:55,bearing:180},
    {id:'outside-control',center:[7.737,45.99],zoom:14.2,pitch:45,bearing:0},
  ],
};
const server=await createServer({configFile:false,plugins:[react(),riffelhornEvaluationPlugin(provider),{
  name:'capture-only-map-access',enforce:'pre',transform(code,id){
    if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(', '    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');
  },
}],server:{host:'127.0.0.1',port:4173,strictPort:true}});
const pending=[];let browser;
async function settled(page){
  await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m?.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});
  await page.evaluate(()=>new Promise((resolve,reject)=>{
    const m=globalThis.__atlasEvaluationMap;const timer=setTimeout(()=>{m.off('idle',done);reject(new Error('No map idle'));},60000);
    function done(){clearTimeout(timer);resolve();}m.once('idle',done);m.triggerRepaint();
  }));await page.waitForTimeout(400);
}
async function snapshot(page){return page.evaluate(()=>{
  const m=globalThis.__atlasEvaluationMap,s=m.getStyle();
  return {camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),projection:m.getProjection()?.type??'mercator',sky:m.getSky(),
    hillshade:m.getLayer('terrain-hillshade').serialize(),elevation:m.getLayer('terrain-elevation-relief').serialize(),meshSize:m.terrain?.meshSize,
    centerVisualElevation:m.queryTerrainElevation(m.getCenter()),sources:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,s.sources[id]])),
    visibleDEMs:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>{const tm=m.style.tileManagers[id];return [id,tm.getVisibleCoordinates().map(c=>{const t=tm.getTile(c);return {z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:t.state,dim:t.dem?.dim};})];}))};
});}
async function capture(page,scene){
  await page.mouse.move(40,40);const start=performance.now();
  await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settled(page);const state=await snapshot(page);
  for(const k of ['zoom','pitch','bearing'])assert.ok(Math.abs(state.camera[k]-scene[k])<1e-8);assert.deepEqual(state.camera.center,scene.center);
  assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(state.meshSize,128);assert.ok(Number.isFinite(state.centerVisualElevation),'No finite terrain at capture center');
  assert.equal(state.hillshade.paint['hillshade-method'],'igor');assert.equal(state.hillshade.paint['hillshade-illumination-direction'],315);
  const filename=`${scene.id}--${provider}.png`;const pixels=await page.screenshot({path:`${output}/${filename}`});
  report.records.push({scene:scene.id,state,filename,settleMs:performance.now()-start,sha256:createHash('sha256').update(pixels).digest('hex')});
  await writeFile(`${output}/${provider}-${phase}.json`,JSON.stringify(report,null,2)+'\n');console.log('CAPTURE',filename);
}
try{
  if(provider==='riffelhorn'){const r=await fetch('http://127.0.0.1:4180/tiles/7/66/45.png');assert.ok(r.ok,'Start isolated product server before regional evaluation');}
  await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
  const page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1,locale:'en-GB',timezoneId:'Europe/London'});
  page.on('pageerror',e=>report.pageErrors.push(String(e)));
  page.on('requestfailed',r=>{const u=new URL(r.url());u.search='';report.failedRequests.push({url:u.href,error:r.failure()?.errorText});});
  page.on('response',r=>{
    const url=r.url();if(r.status()>=400){const u=new URL(url);u.search='';report.httpErrors.push({url:u.href,status:r.status()});}
    if(url.includes('127.0.0.1:4180/tiles/')||url.startsWith('https://s3.amazonaws.com/elevation-tiles-prod/terrarium/'))pending.push((async()=>{
      const row={url,status:r.status(),headers:await r.allHeaders()};try{const body=await r.body();row.bytes=body.length;row.sha256=createHash('sha256').update(body).digest('hex');}catch{row.bodyUnavailable=true;}report.responses.push(row);
    })());
  });
  // No external Weather estate: honest unavailable publication; Weather code untouched.
  await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'No Weather publication in terrain-only evaluation'}));
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});await settled(page);
  for(const scene of scenes[phase])await capture(page,scene);
  if(phase==='operations'){
    const start=performance.now();await page.evaluate(()=>globalThis.__atlasEvaluationMap.easeTo({center:[7.772,45.973],zoom:15.7,bearing:135,duration:700}));await settled(page);
    report.animatedNavigation={settleMs:performance.now()-start,state:await snapshot(page)};
    await page.getByRole('tab',{name:'Journey',exact:true}).click();
    const fixture='<gpx version="1.1" creator="Meridian synthetic terrain-only evaluation"><trk><name>Riffelhorn synthetic test path — not a recommended route</name><trkseg><trkpt lat="45.977" lon="7.756"/><trkpt lat="45.980" lon="7.761"/><trkpt lat="45.984" lon="7.765"/></trkseg></trk></gpx>';
    await page.locator('input[type="file"]').setInputFiles({name:'riffelhorn-synthetic-evaluation.gpx',mimeType:'application/gpx+xml',buffer:Buffer.from(fixture)});
    await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getSource('planned-route-source'),null,{timeout:60000});
    await page.getByRole('button',{name:'Analyse',exact:true}).waitFor({state:'visible',timeout:60000});await page.waitForTimeout(1800);
    await capture(page,{id:'synthetic-route',center:[7.76121329,45.97910794],zoom:14.2,pitch:45,bearing:0});
    report.routeText=await page.locator('body').innerText();
    const satellite=page.getByRole('button',{name:'Satellite basemap',exact:true});report.satelliteConfigured=!(await satellite.isDisabled());
    if(report.satelliteConfigured){
      await satellite.click();
      // Map idle can precede asynchronous TileJSON loading: require real imagery.
      await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m?.getLayer('satellite-imagery-layer')&&m.getLayoutProperty('satellite-imagery-layer','visibility')==='visible'&&m.isSourceLoaded('satellite-imagery-source');},null,{timeout:90000});
      await capture(page,{...scenes.inside[2],id:'satellite'});
      report.satelliteLoaded=true;
      assert.ok(report.records.at(-1).state.hillshade.paint['hillshade-exaggeration'].slice(4).filter((_,i)=>i%2===0).every(v=>v===0));
    }
    for(const zoom of [2.8,5.5,2.8,11.4]){await page.evaluate(z=>globalThis.__atlasEvaluationMap.jumpTo({zoom:z}),zoom);await settled(page);const s=await snapshot(page);assert.equal(s.projection,zoom<5.5?'globe':'mercator');assert.deepEqual(s.terrain,zoom<5.5?null:{source:'terrain-dem',exaggeration:1.45});}
    report.projectionTransitionsPassed=true;
  }
  await Promise.allSettled(pending);assert.deepEqual(report.pageErrors,[]);
  await writeFile(`${output}/${provider}-${phase}.json`,JSON.stringify(report,null,2)+'\n');console.log('COMPLETE',provider,phase,report.httpErrors.length,'HTTP errors');
}catch(e){report.failure=String(e);await writeFile(`${output}/${provider}-${phase}.json`,JSON.stringify(report,null,2)+'\n');throw e;}finally{if(browser)await browser.close();await server.close();}
