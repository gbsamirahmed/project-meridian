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
const [data,mode,runLabel]=process.argv.slice(2);
assert.ok(!runLabel||/^[A-Za-z0-9_-]+$/.test(runLabel),'Use a simple independent rebuild label');
assert.ok(data&&['aws','tryfan-regional','riffelhorn-regional','riffelhorn-appearance'].includes(mode));
const planBytes=await readFile('docs/atlas/information-display-plan.json'),plan=JSON.parse(planBytes);
const hash=b=>createHash('sha256').update(b).digest('hex');
const safe=url=>{try{const u=new URL(url);return u.origin+u.pathname;}catch{return 'non-URL';}};
const out=path.join(data,'experiments/atlas/information-display-v1',runLabel?`captures-${runLabel}`:'captures',mode);
try{await readFile(path.join(out,'capture.json'));throw new Error('Capture record already exists; use an independent run label');}catch(e){if(e.code!=='ENOENT')throw e;}
await mkdir(out,{recursive:true});
const tasks=plan.tasks.filter(t=>t.mode===mode),scenes=tasks.map(t=>t.scene);assert.ok(tasks.length);
const report={mode,planSha256:hash(planBytes),viewport:plan.viewport,requestedDprs:[...new Set(tasks.flatMap(t=>t.dprs))],scenes:[],pageErrors:[],httpErrors:[],failures:[],requests:[],identities:[],protectedSourceCount:Object.keys(plan.productionHashes).length};
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
let imageryRoot,imagery,imageryFiles;
if(mode==='riffelhorn-appearance'){
 imageryRoot=path.join(data,'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1');const bytes=await readFile(path.join(imageryRoot,'manifest.json'));imagery=JSON.parse(bytes);
 assert.equal(imagery.identity,'f6edd630206ed02f255176935d72126cbc6ad7987b12d2986edbe6d05619bc1b');
 imageryFiles=new Map(imagery.files.filter(f=>f.path.startsWith('tiles/')).map(f=>[f.path,f]));report.imageryIdentity={id:imagery.id,revision:imagery.identity,manifestSha256:hash(bytes)};
}
if(geometry){
 const selected=geometry.selectTerrain(geometry.registry,{location:{coordinates:scenes[0].center,crs:'OGC:CRS84'},scale:{scheme:geometry.registry.hierarchy.common.levelScheme,requestedLevel:mode.startsWith('tryfan')?'z17':'z18'}});
 const adapted=geometry.adaptTerrainToMapLibre(geometry.registry,selected);
 visual={tileTemplate:'http://127.0.0.1:4188/terrain/{z}/{x}/{y}.png',tileSize:adapted.tileSize,encoding:adapted.encoding,geometryMaxZoom:adapted.maxzoom,reliefMaxZoom:adapted.maxzoom,attribution:'Experimental immutable regional geometry; declared AWS fallback'};
 gateway=createServer(async(req,res)=>{const m=/^\/(terrain|imagery)\/(\d+)\/(\d+)\/(\d+)\.png$/.exec(req.url);if(!m){res.writeHead(404).end();return;}
  const [,kind,...parts]=m,[z,x,y]=parts.map(Number);if(z<0||z>18||x<0||y<0||x>=2**z||y>=2**z){res.writeHead(400).end();return;}
  try{let body,decision;
   if(kind==='imagery'){const key=`tiles/${z}/${x}/${y}.png`,f=imageryFiles.get(key);body=await readFile(path.join(imageryRoot,f?key:'transparent.png'));if(f)assert.equal(hash(body),f.sha256);decision={product:imagery.id,revision:imagery.identity,support:f?'manifest':'transparent'};}
   else{
    decision=geometry.selectTerrain(geometry.registry,{footprint:tileFootprint(z,x,y),scale:{scheme:geometry.registry.hierarchy.common.levelScheme,requestedLevel:`z${z}`},provenanceRequirement:'product-lineage'});
    assert.equal(decision.status,'selected');const delivery=geometry.adaptTerrainToMapLibre(geometry.registry,decision),root=geometry.productRoots[decision.product.id];
    if(root){assert.ok(delivery.maxzoom>=z);body=await readFile(path.join(root,`tiles/${z}/${x}/${y}.png`));}
    else{
     assert.equal(delivery.tiles[0],'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png');
     // Above common ceiling, reuse the retained proof cache's explicit overzoom, never new observations.
     const r=await fetch(z<=15?delivery.tiles[0].replace('{z}',z).replace('{x}',x).replace('{y}',y):`http://127.0.0.1:4187/aws/${z}/${x}/${y}.png`);assert.ok(r.ok);body=Buffer.from(await r.arrayBuffer());
    }
   }
   report.requests.push({kind,z,x,y,decision,status:200,sha256:hash(body)});
   res.writeHead(200,{'content-type':'image/png','access-control-allow-origin':'*','cache-control':'public,max-age=3600'}).end(body);
  }catch(e){report.requests.push({kind,z,x,y,status:502,error:String(e)});res.writeHead(502).end(String(e));}
 });
}
const server=await vite({configFile:false,plugins:[react(),{name:'multiscale-audit-only',enforce:'pre',load(id){if(visual&&id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(visual)};`;},transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    (globalThis as typeof globalThis & { __atlasEvaluationController?: AtlasMap }).__atlasEvaluationController = this;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port:4173,strictPort:true,forwardConsole:false}});
const save=()=>writeFile(path.join(out,'capture.json'),JSON.stringify(report,null,2)+'\n');
async function settle(){await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving()&&!m.painter.renderToTexture.needsFollowUpFrame;},null,{timeout:90000});await page.waitForTimeout(750);}
async function snapshot(){return page.evaluate(async probes=>{
 const m=globalThis.__atlasEvaluationMap,canvas=m.getCanvas(),gl=m.painter.context.gl;
 const sha=async data=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',data)),v=>v.toString(16).padStart(2,'0')).join('');
 const texture=t=>t?{size:t.size,useMipmap:t.useMipmap,magFilter:t.magFilter,minFilter:t.minFilter}:null;
 const tiles=m.terrain.tileManager.getRenderableTiles();
 const rttTexture=t=>{try{return texture(m.painter.renderToTexture.getTexture(t));}catch{return null;}};
 const geometry=[];
 for(const t of tiles){const d=m.terrain.tileManager.getSourceTile(t.tileID,true);geometry.push({render:t.tileID.canonical,overscaledRender:t.tileID.overscaledZ,source:d?.tileID.canonical,sourceDim:d?.dem?.dim,sha256:d?.dem?await sha(d.dem.getPixels().data):null,demTexture:texture(d?.demTexture),rttTexture:rttTexture(t)});}
 geometry.sort((a,b)=>JSON.stringify(a.render).localeCompare(JSON.stringify(b.render)));
 const sourceTiles=id=>m.style.tileManagers[id]?.getVisibleCoordinates().map(c=>{const t=m.style.tileManagers[id].getTile(c);return{...c.canonical,overscaledZ:c.overscaledZ,state:t.state,demDim:t.dem?.dim,texture:texture(t.texture)}});
 const points=[];
 const at=([x,y])=>{const ll=m.unproject([x,y]);const q=m.project(ll);return{xyz:[ll.lng,ll.lat,m.queryTerrainElevation(ll)],roundTripCssError:Math.hypot(q.x-x,q.y-y)}};
 for(const fy of probes.yFractions)for(const fx of probes.xFractions){const screen=[planWidth()*fx,planHeight()*fy],origin=at(screen),stencils=[];
  for(const step of probes.centralDifferenceCssPixels){stencils.push({step,east:at([screen[0]+step,screen[1]]),west:at([screen[0]-step,screen[1]]),south:at([screen[0],screen[1]+step]),north:at([screen[0],screen[1]-step])});}
  points.push({screen,fraction:[fx,fy],origin,stencils});
 }
 function planWidth(){return m._camera.transform.width;}function planHeight(){return m._camera.transform.height;}
 const t=m._camera.transform,cam=t.getCameraLngLat();
 const sources=m.getStyle().sources;
 return{camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},rendererCamera:{position:[cam.lng,cam.lat,t.getCameraAltitude()],basis:'Published renderer camera transform, rendered height frame'},terrain:m.getTerrain(),projection:m.getProjection(),mesh:m.terrain.meshSize,geometry,points,reliefTiles:sourceTiles('terrain-analysis-dem'),imageryTiles:sourceTiles('swissimage-baseline'),commonImageryTiles:sourceTiles('satellite-imagery-source'),hillshade:m.getLayer('terrain-hillshade').serialize().paint,sources,satellite:m.getLayer('satellite-imagery-layer')?.serialize().paint,
  display:{browserDpr:devicePixelRatio,mapRequestedRatio:m.getPixelRatio(),cssRect:{width:canvas.getBoundingClientRect().width,height:canvas.getBoundingClientRect().height},canvas:[canvas.width,canvas.height],drawingBuffer:[gl.drawingBufferWidth,gl.drawingBufferHeight],transform:[t.width,t.height],maxCanvas:m._maxCanvasSize,maxTexture:gl.getParameter(gl.MAX_TEXTURE_SIZE),depthFramebuffer:m.terrain._fbo?{width:m.terrain._fbo.width,height:m.terrain._fbo.height}:null,rttSize:m.painter.renderToTexture.rttSize,terrainQuality:m.terrain.qualityFactor,anisotropicExtension:!!m.painter.context.extTextureFilterAnisotropic,maxAnisotropy:m.painter.context.extTextureFilterAnisotropicMax,anisotropicPitch:m.getAnisotropicFilterPitch(),browserWebglVersion:gl.getParameter(gl.VERSION)}
 };
 },plan.probes);}

try{
 if(gateway)await new Promise(r=>gateway.listen(4188,'127.0.0.1',r));await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
 for(const dpr of report.requestedDprs){
  page=await browser.newPage({viewport:plan.viewport,deviceScaleFactor:dpr});
  page.on('pageerror',e=>report.pageErrors.push(String(e).replace(/\?[^\s]+/g,'?REDACTED')));page.on('requestfailed',r=>report.failures.push({url:safe(r.url()),error:r.failure()?.errorText}));page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:safe(r.url()),status:r.status()});});
  await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Information sampling characterization only'}));
  // Research synchronization only: retain provider bytes; avoid the existing one-shot style-ready metadata race.
  if(imagery)await page.route('**/tiles/satellite-v2/tiles.json?*',async route=>{const response=await route.fetch();await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.isStyleLoaded(),null,{timeout:90000});const bytes=await response.body();report.metadataSynchronization??=[];report.metadataSynchronization.push({dpr,status:response.status(),sha256:hash(bytes),gate:'existing style ready, response unchanged'});await route.fulfill({response,body:bytes});});
  await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
  if(imagery){await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scenes[0]);await settle();await page.getByRole('button',{name:'Satellite basemap',exact:true}).click();await page.waitForFunction(()=>document.querySelector('button[aria-label=\"Satellite basemap\"]')?.getAttribute('aria-pressed')==='true');await settle();
   const recovered=await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;if(m.getLayer('satellite-imagery-layer'))return false;globalThis.__atlasEvaluationController.setPresentation('terrain',false);return true;});
   if(recovered){await settle();await page.evaluate(()=>globalThis.__atlasEvaluationController.setPresentation('satellite',false));report.activationSynchronization??=[];report.activationSynchronization.push({dpr,gate:'normal public controller presentation after style-ready guard, no source/config override'});}
   await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getLayoutProperty('satellite-imagery-layer','visibility')==='visible',null,{timeout:90000});
   await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap,layers=m.getStyle().layers,i=layers.findIndex(l=>l.id==='satellite-imagery-layer');m.addSource('swissimage-baseline',{type:'raster',tiles:['http://127.0.0.1:4188/imagery/{z}/{x}/{y}.png'],tileSize:512,minzoom:12,maxzoom:18,bounds:[7.748260056402138,45.970074962275305,7.77417077736836,45.988139457488266],attribution:'©swisstopo, retained 2023 source-derived product'});m.addLayer({id:'swissimage-baseline',type:'raster',source:'swissimage-baseline',layout:{visibility:'none'},paint:{'raster-opacity':1,'raster-fade-duration':180,'raster-resampling':'linear'}},layers[i+1]?.id);});
  }
  for(const task of tasks.filter(t=>t.dprs.includes(dpr)))for(const appearance of task.appearances){
   if(imagery)await page.evaluate(a=>globalThis.__atlasEvaluationMap.setLayoutProperty('swissimage-baseline','visibility',a==='regional'?'visible':'none'),appearance);
   const scene=task.scene;await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settle();
   const state=await snapshot();assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(state.mesh,128);assert.equal(state.hillshade['hillshade-method'],'igor');assert.equal(state.display.browserDpr,dpr);
   for(const s of Object.values(state.sources)){if(s.tiles)s.tiles=s.tiles.map(safe);if(s.url)s.url=safe(s.url);}
   const filename=`${scene.id}--${appearance}--dpr${dpr}.png`,bytes=await page.screenshot({path:path.join(out,filename)});report.scenes.push({scene,appearance,dpr,state,filename,sha256:hash(bytes)});console.log('CAPTURE',mode,scene.id,appearance,dpr);await save();
  }
  await page.close();
 }
 assert.deepEqual(report.pageErrors,[]);for(const [f,h]of Object.entries(plan.productionHashes))assert.equal(hash(await readFile(f)),h);
}catch(e){report.failure=String(e);if(page)report.failureState=await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;return{camera:{center:m.getCenter().toArray(),zoom:m.getZoom()},satelliteLayer:m.getLayer('satellite-imagery-layer')?.serialize(),buttons:Array.from(document.querySelectorAll('button')).filter(b=>b.getAttribute('aria-label')==='Satellite basemap').map(b=>({disabled:b.disabled,pressed:b.getAttribute('aria-pressed')}))};}).catch(()=>null);throw e;}
finally{await save();if(browser)await browser.close();await server.close();if(gateway)await new Promise(r=>gateway.close(r));}
