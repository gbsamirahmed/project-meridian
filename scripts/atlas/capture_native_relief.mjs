import { createServer } from 'vite';
import react from '@vitejs/plugin-react';
import { chromium } from '@playwright/test';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import path from 'node:path';

// Bounded production-relief reproducer. DEM/basemap/imagery requests stay real.
// Only Weather uses an explicit synthetic compatibility fixture; no external data roots.
const root = process.cwd();
const output = path.join(root, 'test-results', 'atlas-relief');
await mkdir(output, { recursive: true });
const modes = process.argv.slice(2);
const phase = modes[0] ?? 'core';
assert.ok(['core','rotation','overlays','satellite','verify'].includes(phase), 'Unknown capture phase');
const stops = [[5.5,0],[7,.06],[9,.2],[11,.36],[12,.3],[13,.24],[14,.22],[15,.2],[16,.2]];
const variants = [
  { id: 'baseline', method: 'igor', directions: 315, altitude: 42, scale: 1 },
  { id: 'igor-strong', method: 'igor', directions: 315, altitude: 42, scale: 1.5 },
  { id: 'multi', method: 'multidirectional', directions: [225,270,315,0], altitude: 30, scale: 1, alpha: .35 },
  { id: 'basic', method: 'basic', directions: 315, altitude: 30, scale: 1, alpha: .35 },
];
const scenes = [
  { id:'tryfan-landscape', center:[-3.999,53.115], zoom:9.4, pitch:45, bearing:0 },
  { id:'tryfan-planning', center:[-3.999,53.115], zoom:11.4, pitch:45, bearing:0 },
  { id:'tryfan-close', center:[-3.999,53.115], zoom:13.2, pitch:55, bearing:0 },
  { id:'downs-rolling', center:[-.766,50.908], zoom:11.4, pitch:45, bearing:0 },
  { id:'cambridge-flat', center:[.12,52.20], zoom:11.4, pitch:0, bearing:0 },
];
const diagnostics = { pageErrors:[], errors:[], failedRequests:[], httpErrors:[], demTiles:{} };
const cleanUrl = url => { try { const value = new URL(url); value.search = ''; return value.href; } catch { return url; } };
const server = await createServer({
  configFile:false, root, plugins:[react(), {
    name:'atlas-relief-capture-only', enforce:'pre',
    transform(code,id) {
      if (id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts')) {
        return code.replace('    this.map.addControl(', '    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');
      }
    },
  }], server:{host:'127.0.0.1',port:4173,strictPort:true},
});
let browser;
const report = { baselineCheckpoint:'669fbd09239ce5cf16935e33c92749de693ea32c', mapLibreVersion:JSON.parse(await readPackage()).version, phase, viewport:{width:1440,height:900}, variants, scenes, records:[], diagnostics, weather:'Synthetic uniform 1 mm interval-total through unchanged production Weather renderer; not a forecast' };
async function readPackage() { return readFile(path.join(root,'node_modules','maplibre-gl','package.json'),'utf8'); }
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
    const dem=Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,s.sources[id]]));
    return {camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),dem,
      hillshade:m.getLayer('terrain-hillshade').serialize(),sky:m.getSky(),centerElevation:m.queryTerrainElevation(m.getCenter()),
      elevation:m.getPaintProperty('terrain-elevation-relief','color-relief-opacity'),rainVisible:document.querySelector('[aria-label="Precipitation"]')?.getAttribute('aria-pressed'),
      satellite:document.querySelector('[aria-label="Satellite basemap"]')?.getAttribute('aria-pressed')};
  });
}
async function capture(page,scene,variant) {
  const invariant=await snapshot(page);
  if(!variant.production) {
    // Public visibility cycle refreshes native terrain RTT caches before each comparison.
    await page.evaluate(()=>globalThis.__atlasEvaluationMap.setLayoutProperty('terrain-hillshade','visibility','none'));
    await settled(page);
    await page.evaluate(({variant,stops})=>{
      const m=globalThis.__atlasEvaluationMap,id='terrain-hillshade';
      m.setPaintProperty(id,'hillshade-exaggeration-transition',{duration:0,delay:0});
      m.setPaintProperty(id,'hillshade-shadow-color',variant.alpha ? `rgba(23,33,31,${variant.alpha})` : '#17211f');
      m.setPaintProperty(id,'hillshade-highlight-color',variant.alpha ? `rgba(244,239,224,${variant.alpha})` : '#f4efe0');
      m.setPaintProperty(id,'hillshade-method',variant.method);
      m.setPaintProperty(id,'hillshade-illumination-direction',variant.directions);
      m.setPaintProperty(id,'hillshade-illumination-altitude',variant.altitude);
      m.setPaintProperty(id,'hillshade-illumination-anchor','map');
      m.setPaintProperty(id,'hillshade-exaggeration',['interpolate',['linear'],['zoom'],...stops.flatMap(([z,s])=>[z,s*variant.scale])]);
    },{variant,stops});
    await page.evaluate(()=>globalThis.__atlasEvaluationMap.setLayoutProperty('terrain-hillshade','visibility','visible'));
  }
  await settled(page);
  const state=await snapshot(page);
  assert.equal(state.hillshade.paint['hillshade-method'],variant.method);
  assert.equal(state.hillshade.paint['hillshade-illumination-anchor'],'map');
  assert.deepEqual(state.hillshade.paint['hillshade-illumination-direction'],variant.directions);
  const expected=['interpolate',['linear'],['zoom'],...stops.flatMap(([z,strength])=>[z,strength*variant.scale])];
  const actual=state.hillshade.paint['hillshade-exaggeration'];
  assert.equal(actual.length,expected.length);
  assert.deepEqual(actual.slice(0,3),expected.slice(0,3));
  for(let i=3;i<expected.length;i++)assert.ok(Math.abs(actual[i]-expected[i])<1e-12);
  assert.deepEqual(state.dem,invariant.dem); assert.deepEqual(state.terrain,invariant.terrain);
  assert.deepEqual(state.camera,invariant.camera);assert.equal(state.centerElevation,invariant.centerElevation);
  const filename=`${scene.id}--${variant.id}.png`;
  const pixels=await page.screenshot({path:path.join(output,filename)});
  report.records.push({scene:scene.id,variant:variant.id,filename,sha256:createHash('sha256').update(pixels).digest('hex'),state});
  await writeFile(path.join(output,`${phase}-manifest.json`),JSON.stringify(report,null,2)+'\n');
  console.log(`CAPTURE ${filename}`);
}
async function compare(page,scene,choices=variants.slice(0,3)) {
  await page.evaluate(scene=>globalThis.__atlasEvaluationMap.jumpTo(scene),scene);
  await settled(page);
  for(const variant of choices) await capture(page,scene,variant);
}
try {
  await server.listen();
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1,locale:'en-GB',timezoneId:'Europe/London'});
  page.on('pageerror',error=>diagnostics.pageErrors.push(String(error)));
  page.on('console',message=>{if(message.type()==='error')diagnostics.errors.push(message.text().replace(/key=[^&\s"]+/g,'key=REDACTED'));});
  page.on('requestfailed',request=>diagnostics.failedRequests.push({url:cleanUrl(request.url()),error:request.failure()?.errorText}));
  const pending=[];
  page.on('response',response=>{
    if(response.status()>=400)diagnostics.httpErrors.push({url:cleanUrl(response.url()),status:response.status()});
    if(response.url().startsWith('https://s3.amazonaws.com/elevation-tiles-prod/terrarium/')&&response.ok()) {
      pending.push(response.body().then(body=>{diagnostics.demTiles[response.url()]=createHash('sha256').update(body).digest('hex');}).catch(()=>{}));
    }
  });
  await fixtureRoutes(page);
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
  await settled(page);
  report.loadedProduction=await snapshot(page);
  report.browserVersion=browser.version();
  report.satelliteConfigured=!(await page.getByRole('button',{name:'Satellite basemap',exact:true}).isDisabled());
  if(phase==='verify') {
    const selected={...variants[1],id:'production-selected',production:true};
    for(const scene of scenes.slice(0,3))await compare(page,scene,[selected]);
    for(const zoom of [2.8,5.5,2.8,11.4]) {
      await page.evaluate(zoom=>globalThis.__atlasEvaluationMap.jumpTo({zoom}),zoom);await settled(page);
      const state=await snapshot(page);
      assert.deepEqual(state.terrain,zoom<5.5?null:{source:'terrain-dem',exaggeration:1.45});
      const projection=await page.evaluate(()=>globalThis.__atlasEvaluationMap.getProjection().type);
      assert.equal(projection,zoom<5.5?'globe':'mercator');
    }
    report.projectionTransitionsPassed=true;
  } else if(phase==='core') {
    for(const scene of scenes) await compare(page,scene);
    await compare(page,scenes[1],[variants[3]]);
    await compare(page,scenes[3],[variants[3]]);
  } else if(phase==='rotation') {
    for(const bearing of [90,180])await compare(page,{...scenes[1],id:`tryfan-bearing-${bearing}`,bearing});
    await page.getByRole('button',{name:'Elevation',exact:true}).click();
    await compare(page,{...scenes[1],id:'tryfan-elevation'});
  } else if(phase==='overlays') {
    await page.getByRole('tab',{name:'Journey',exact:true}).click();
    await page.locator('input[type="file"]').setInputFiles(path.join(root,'scripts','route','fixtures','snowdonia-smoke.gpx'));
    await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getSource('planned-route-source'),null,{timeout:60000});
    await page.getByRole('button',{name:'Analyse',exact:true}).waitFor({state:'visible',timeout:60000});
    await page.waitForTimeout(1800);
    const scene={id:'snowdonia-route',center:[-4.073,53.102],zoom:11.4,pitch:45,bearing:0};
    await compare(page,scene);
    await page.getByRole('button',{name:'Precipitation',exact:true}).click();
    await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getLayer('global-precipitation-layer-a')||globalThis.__atlasEvaluationMap.getLayer('global-precipitation-layer-b'),null,{timeout:20000});
    await compare(page,{...scene,id:'snowdonia-route-rain'});
  } else if(phase==='satellite') {
    if(report.satelliteConfigured) {
      await page.getByRole('button',{name:'Satellite basemap',exact:true}).click();
      await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getSource('satellite-imagery-source'),null,{timeout:30000});
      await settled(page);
      for(const scene of [scenes[1],scenes[2]])await compare(page,{...scene,id:scene.id+'-satellite'},[
        {...variants[0],id:'satellite-off',scale:0}, {...variants[0],id:'satellite-igor',scale:.2}, {...variants[2],id:'satellite-multi',scale:.2},
      ]);
    } else console.log('SATELLITE NOT CONFIGURED: no real imagery comparison; retain suppression');
  }
  await Promise.allSettled(pending);
  assert.deepEqual(diagnostics.pageErrors,[]);
  await writeFile(path.join(output,`${phase}-manifest.json`),JSON.stringify(report,null,2)+'\n');
  console.log(`COMPLETE ${phase}: ${report.records.length} captures, ${Object.keys(diagnostics.demTiles).length} real DEM response hashes; ${diagnostics.httpErrors.length} HTTP errors`);
} catch(error) {report.failure=String(error);await writeFile(path.join(output,`${phase}-manifest.json`),JSON.stringify(report,null,2)+'\n');throw error;} finally { if(browser)await browser.close();await server.close(); }
