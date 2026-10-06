// Research-only capture harness. No normal Vite configuration or runtime changes.
import {createServer as vite} from 'vite';
import {createServer} from 'node:http';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import assert from 'node:assert/strict';
import {swissGeometry} from './swissimage_geometry.mjs';
import {tileFootprint} from './terrainProofGateway.mjs';
import {installReliefHook,filterGlsl} from './relief_scale_control.mjs';
const [data,mode,runLabel]=process.argv.slice(2);
assert.ok(!runLabel||/^[A-Za-z0-9_-]+$/.test(runLabel),'Use a simple independent rebuild label');
assert.ok(data&&['aws','tryfan-regional','riffelhorn-regional'].includes(mode));
const planBytes=await readFile('docs/atlas/scale-separated-relief-plan.json'),plan=JSON.parse(planBytes);
const hash=b=>createHash('sha256').update(b).digest('hex');
const safe=url=>{try{const u=new URL(url);return u.origin+u.pathname;}catch{return 'non-URL';}};
const out=path.join(data,'experiments/atlas/scale-separated-relief-v1',runLabel?`captures-${runLabel}`:'captures',mode);
try{await readFile(path.join(out,'capture.json'));throw new Error('Capture record already exists; use an independent run label');}catch(e){if(e.code!=='ENOENT')throw e;}
await mkdir(out,{recursive:true});
const scenes=mode==='aws'?plan.scenes.filter(s=>['downs','cambridge'].includes(s.site)):plan.scenes.filter(s=>s.site===(mode.startsWith('tryfan')?'tryfan':'riffelhorn'));
const report={mode,planSha256:hash(planBytes),viewport:plan.viewport,devicePixelRatio:1,scenes:[],pageErrors:[],httpErrors:[],failures:[],requests:[],identities:[],protectedSourceCount:Object.keys(plan.productionHashes).length};
let geometry,gateway,browser,page,visual;
const loader=await vite({configFile:false,logLevel:'silent',server:{middlewareMode:true}});
if(mode.startsWith('riffelhorn')){geometry=await swissGeometry(loader,data);report.identities=geometry.identities;}
else if(mode==='tryfan-regional'){
 const {createTryfanTerrainProof}=await loader.ssrLoadModule('/src/atlas/terrain/metadata/tryfanTerrainProof.ts');
 const {selectTerrain}=await loader.ssrLoadModule('/src/atlas/terrain/runtime/terrainSelector.ts');
 const {adaptTerrainToMapLibre}=await loader.ssrLoadModule('/src/atlas/map/terrainDeliveryAdapter.ts');
 const root=path.join(data,'derived/atlas/tryfan/tryfan-welsh-regional-v2'),bytes=await readFile(path.join(root,'manifest.json')),manifest=JSON.parse(bytes);
 for(const f of manifest.files){assert.equal(hash(await readFile(path.join(root,f.path))),f.sha256);}
 geometry={registry:createTryfanTerrainProof(),selectTerrain,adaptTerrainToMapLibre,productRoots:{'tryfan-welsh-regional-v2':root}};report.identities=[{product:'tryfan-welsh-regional-v2',revision:manifest.identity,manifestSha256:hash(bytes),verifiedFiles:manifest.files.length}];
}
await loader.close();
if(geometry){
 const selected=geometry.selectTerrain(geometry.registry,{location:{coordinates:scenes[0].center,crs:'OGC:CRS84'},scale:{scheme:geometry.registry.hierarchy.common.levelScheme,requestedLevel:mode.startsWith('tryfan')?'z17':'z18'}});
 const adapted=geometry.adaptTerrainToMapLibre(geometry.registry,selected);
 visual={tileTemplate:'http://127.0.0.1:4188/terrain/{z}/{x}/{y}.png',tileSize:adapted.tileSize,encoding:adapted.encoding,geometryMaxZoom:adapted.maxzoom,reliefMaxZoom:adapted.maxzoom,attribution:'Experimental immutable regional geometry; declared AWS fallback'};
 gateway=createServer(async(req,res)=>{const m=/^\/(terrain|imagery)\/(\d+)\/(\d+)\/(\d+)\.png$/.exec(req.url);if(!m){res.writeHead(404).end();return;}
  const [,kind,...parts]=m,[z,x,y]=parts.map(Number);if(z<0||z>18||x<0||y<0||x>=2**z||y>=2**z){res.writeHead(400).end();return;}
  try{let body,decision;
    decision=geometry.selectTerrain(geometry.registry,{footprint:tileFootprint(z,x,y),scale:{scheme:geometry.registry.hierarchy.common.levelScheme,requestedLevel:`z${z}`},provenanceRequirement:'product-lineage'});
    assert.equal(decision.status,'selected');const delivery=geometry.adaptTerrainToMapLibre(geometry.registry,decision),root=geometry.productRoots[decision.product.id];
    if(root){assert.ok(delivery.maxzoom>=z);body=await readFile(path.join(root,`tiles/${z}/${x}/${y}.png`));}
    else{
     assert.equal(delivery.tiles[0],'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png');
     // Above common ceiling, reuse the retained proof cache's explicit overzoom, never new observations.
     const r=await fetch(z<=15?delivery.tiles[0].replace('{z}',z).replace('{x}',x).replace('{y}',y):`http://127.0.0.1:4187/aws/${z}/${x}/${y}.png`);assert.ok(r.ok);body=Buffer.from(await r.arrayBuffer());
    }
   report.requests.push({kind,z,x,y,decision,status:200,sha256:hash(body)});
   res.writeHead(200,{'content-type':'image/png','access-control-allow-origin':'*','cache-control':'public,max-age=3600'}).end(body);
  }catch(e){report.requests.push({kind,z,x,y,status:502,error:String(e)});res.writeHead(502).end(String(e));}
 });
}
const server=await vite({configFile:false,plugins:[react(),{name:'multiscale-audit-only',enforce:'pre',load(id){if(visual&&id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(visual)};`;},transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port:4173,strictPort:true,forwardConsole:false}});
const save=()=>writeFile(path.join(out,'capture.json'),JSON.stringify(report,null,2)+'\n');
async function settle(){await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving()&&!m.painter.renderToTexture.needsFollowUpFrame;},null,{timeout:90000});await page.waitForTimeout(750);}
async function snapshot(){return page.evaluate(async()=>{
 const m=globalThis.__atlasEvaluationMap,points=[];
 // Central and upper/lower viewport probes avoid most controls. DEM height queries refer to loaded, exaggerated terrain.
 for(const row of [.25,.5,.75]){const pixel=[720,900*row],xyz=([x,y])=>{const p=m.unproject([x,y]);return[p.lng,p.lat,m.queryTerrainElevation(p)];};points.push({row,pixel,origin:xyz(pixel),east:xyz([pixel[0]+2,pixel[1]]),south:xyz([pixel[0],pixel[1]+2])});}
 const actualDEMs=m.terrain?.tileManager.getRenderableTiles().map(t=>({render:t.tileID.canonical,source:m.terrain.tileManager.getSourceTile(t.tileID,true)?.tileID.canonical}));
 const sourceTiles=id=>m.style.tileManagers[id]?.getVisibleCoordinates().map(c=>({z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:m.style.tileManagers[id].getTile(c).state}));
 const geometryBuffers=[];
 const digest=async data=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),v=>v.toString(16).padStart(2,'0')).join('');
 for(const t of m.terrain.tileManager.getRenderableTiles()){
  const d=m.terrain.tileManager.getSourceTile(t.tileID,true),p=d?.dem?.getPixels().data;
  if(p)geometryBuffers.push({render:t.tileID.canonical,source:d.tileID.canonical,sha256:await digest(p)});
 }
 geometryBuffers.sort((a,b)=>JSON.stringify(a.render).localeCompare(JSON.stringify(b.render)));
 const centre=m.getCenter();let derivativeInput;
 for(const c of m.style.tileManagers['terrain-analysis-dem'].getVisibleCoordinates()){
  const z=c.canonical.z,x=(centre.lng+180)/360*2**z,y=(1-Math.asinh(Math.tan(centre.lat*Math.PI/180))/Math.PI)/2*2**z;
  if(c.canonical.x<=x&&x<c.canonical.x+1&&c.canonical.y<=y&&y<c.canonical.y+1){
   const t=m.style.tileManagers['terrain-analysis-dem'].getTile(c),dim=t.dem.dim,lo=Math.floor(dim/2)-48;
   derivativeInput={canonical:c.canonical,overscaledZ:c.overscaledZ,dim,window:[lo,lo,96,96],heights:Array.from({length:96},(_,r)=>Array.from({length:96},(_,col)=>t.dem.get(lo+col,lo+r)))};break;
  }
 }
 return{geometryBuffers,derivativeInput,reliefHook:{patched:globalThis.__researchRelief.patched,draws:globalThis.__researchRelief.draws,enabled:globalThis.__researchRelief.enabled},camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),projection:m.getProjection(),mesh:m.terrain?.meshSize,points,actualDEMs,reliefTiles:sourceTiles('terrain-analysis-dem'),imageryTiles:sourceTiles('swissimage-baseline'),commonImageryTiles:sourceTiles('satellite-imagery-source'),hillshade:m.getLayer('terrain-hillshade').serialize().paint,sources:m.getStyle().sources,satellite:m.getLayer('satellite-imagery-layer')?.serialize().paint};
 });}
try{
 if(gateway)await new Promise(r=>gateway.listen(4188,'127.0.0.1',r));await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();page=await browser.newPage({viewport:plan.viewport,deviceScaleFactor:1});
 await page.addInitScript(installReliefHook,{glsl:filterGlsl});
 page.on('pageerror',e=>report.pageErrors.push(String(e).replace(/\?[^\s]+/g,'?REDACTED')));page.on('requestfailed',r=>report.failures.push({url:safe(r.url()),error:r.failure()?.errorText}));page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:safe(r.url()),status:r.status()});});
 await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Multiscale Atlas-only audit'}));
 await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
 for(const scene of runLabel==='navigation'?[]:scenes){
  await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settle();let control;
  for(const depiction of ['igor','scale-separated']){
   await page.evaluate(v=>{globalThis.__researchRelief.enabled=v;const m=globalThis.__atlasEvaluationMap;for(const t of m.terrain.tileManager.getRenderableTiles())t.releaseRTT(m.painter);m.triggerRepaint();},depiction==='scale-separated');
   await settle();const state=await snapshot();assert.ok(state.reliefHook.patched>0);assert.equal(state.terrain.exaggeration,1.45);
   if(control){assert.deepEqual(state.geometryBuffers,control.geometryBuffers);assert.deepEqual(state.actualDEMs,control.actualDEMs);assert.deepEqual(state.points,control.points);assert.deepEqual(state.camera,control.camera);}
   else control=state;
   for(const source of Object.values(state.sources)){if(source.tiles)source.tiles=source.tiles.map(safe);if(source.url)source.url=safe(source.url);}
   const filename=`${scene.id}--${depiction}.png`,bytes=await page.screenshot({path:path.join(out,filename)});report.scenes.push({scene,depiction,state,filename,sha256:hash(bytes)});console.log('CAPTURE',mode,scene.id,depiction);await save();
  }
 }
 report.navigation=[];
 if(mode!=='aws'){
  const first=scenes.find(s=>s.targetMetresPerCssPixel===8&&s.pitch===0);
  for(let step=0;step<9;step++){
   const scale=8*2**(-step/4),scene={...first,id:`${first.site}-nav-${step}`,zoom:first.zoom+step/4,targetMetresPerCssPixel:scale};delete scene.igorStrength;
   await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settle();let control;
   for(const depiction of ['igor','scale-separated']){
    await page.evaluate(v=>{globalThis.__researchRelief.enabled=v;const m=globalThis.__atlasEvaluationMap;for(const t of m.terrain.tileManager.getRenderableTiles())t.releaseRTT(m.painter);m.triggerRepaint();},depiction==='scale-separated');
    await settle();const state=await snapshot();if(control)assert.deepEqual(state.geometryBuffers,control.geometryBuffers);else control=state;
    for(const source of Object.values(state.sources)){if(source.tiles)source.tiles=source.tiles.map(safe);if(source.url)source.url=safe(source.url);}
    const filename=`${scene.id}--${depiction}.png`,bytes=await page.screenshot({path:path.join(out,filename)});
    report.navigation.push({scene,depiction,state,filename,sha256:hash(bytes)});console.log('NAV',mode,step,depiction);await save();
   }
  }
 }
 report.shaderSourceHashes=await page.evaluate(async()=>Promise.all(globalThis.__researchRelief.shaderSources.map(async s=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))),v=>v.toString(16).padStart(2,'0')).join(''))));
 assert.deepEqual(report.pageErrors,[]);for(const [f,h]of Object.entries(plan.productionHashes))assert.equal(hash(await readFile(f)),h);
}catch(e){report.failure=String(e);throw e;}
finally{await save();if(browser)await browser.close();await server.close();if(gateway)await new Promise(r=>gateway.close(r));}
