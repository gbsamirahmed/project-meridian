// Private Vite/capture entry point. No production import or normal UI controls.
import {createServer} from 'vite';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {RIFFELHORN_VISUAL} from './riffelhorn_evaluation.mjs';

const method=process.argv[2];
assert.ok(['hard','linear250','adaptive3deg'].includes(method));
const output='test-results/atlas-riffelhorn-reconciliation';await mkdir(output,{recursive:true});
const visual={...RIFFELHORN_VISUAL,tileTemplate:`http://127.0.0.1:4180/tiles/${method}/{z}/{x}/{y}.png`};
const report={baseline:'fe8addcbce4b7b7966dc41c93361d69d6c416f49',method,date:new Date().toISOString(),
  viewport:{width:1440,height:900},records:[],pageErrors:[],demErrors:[],responses:[]};
const protectedFiles=['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts',
  'src/atlas/map/terrainLayers.ts','src/atlas/map/atlasVisuals.ts','src/atlas/map/AtlasMap.ts','src/atlas/terrain/terrainElevationSampler.ts'];
report.productionHashes=Object.fromEntries(await Promise.all(protectedFiles.map(async p=>[p,createHash('sha256').update(await readFile(p)).digest('hex')])));
const boundary=JSON.parse(await readFile('scripts/atlas/riffelhorn-boundary-cameras.json','utf8'));
const scenes=[
  {id:'landscape',center:[7.76121329,45.97910794],zoom:9.4,pitch:45,bearing:0},
  {id:'planning',center:[7.76121329,45.97910794],zoom:11.4,pitch:45,bearing:0},
  {id:'close',center:[7.76121329,45.97910794],zoom:13.2,pitch:55,bearing:0},
  {id:'detail',center:[7.76121329,45.97910794],zoom:16.2,pitch:55,bearing:0},
  ...boundary.filter(s=>['boundary-west','boundary-south','boundary-corner'].includes(s.id)),
  {...boundary.find(s=>s.id==='boundary-west'),id:'west-rotated',bearing:180},
];
const server=await createServer({configFile:false,plugins:[react(),{name:'reconciliation-private-capture',enforce:'pre',
  load(id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(visual)};`;},
  transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(',
    '    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');},
}],server:{host:'127.0.0.1',port:4173,strictPort:true}});
let browser;const pending=[];
try{
  await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
  const page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1,locale:'en-GB',timezoneId:'Europe/London'});
  page.on('pageerror',e=>report.pageErrors.push(String(e)));
  page.on('response',r=>{if(r.url().includes('127.0.0.1:4180/tiles/'))pending.push((async()=>{
    const headers=await r.allHeaders();const row={url:r.url(),status:r.status(),identity:headers['x-meridian-analysis']};
    try{row.bytes=(await r.body()).length;}catch{row.bodyUnavailable=true;}
    report.responses.push(row);if(r.status()>=400)report.demErrors.push(row);
  })());});
  await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Terrain-only evaluation: no Weather publication'}));
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
  for(const scene of scenes){
    await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);
    await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});
    await page.evaluate(()=>new Promise((resolve,reject)=>{const m=globalThis.__atlasEvaluationMap;
      const timer=setTimeout(()=>{m.off('idle',done);reject(new Error('Map idle timeout'));},60000);
      function done(){clearTimeout(timer);resolve();}m.once('idle',done);m.triggerRepaint();}));
    await page.waitForTimeout(400);
    const state=await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;return {
      camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},
      terrain:m.getTerrain(),projection:m.getProjection()?.type??'mercator',sky:m.getSky(),meshSize:m.terrain?.meshSize,
      hillshade:m.getLayer('terrain-hillshade').serialize(),elevation:m.getLayer('terrain-elevation-relief').serialize(),
      sources:Object.fromEntries(['terrain-dem','terrain-analysis-dem'].map(id=>[id,m.getStyle().sources[id]]))};});
    assert.deepEqual(state.camera.center,scene.center);
    for(const k of ['zoom','pitch','bearing'])assert.ok(Math.abs(state.camera[k]-scene[k])<1e-8);
    assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(state.meshSize,128);
    assert.equal(state.hillshade.paint['hillshade-method'],'igor');
    assert.equal(state.hillshade.paint['hillshade-illumination-direction'],315);
    const filename=`${scene.id}--${method}.png`;
    const bytes=await page.screenshot({path:`${output}/${filename}`});
    report.records.push({scene:scene.id,state,filename,sha256:createHash('sha256').update(bytes).digest('hex')});
    await writeFile(`${output}/${method}.json`,JSON.stringify(report,null,2)+'\n');console.log('CAPTURE',filename);
  }
  await Promise.allSettled(pending);assert.deepEqual(report.pageErrors,[]);assert.deepEqual(report.demErrors,[]);
  await writeFile(`${output}/${method}.json`,JSON.stringify(report,null,2)+'\n');
  console.log('COMPLETE',method,scenes.length,'captures');
}catch(error){report.failure=String(error);await writeFile(`${output}/${method}.json`,JSON.stringify(report,null,2)+'\n');throw error;}
finally{if(browser)await browser.close();await server.close();}
