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
import {surfaceMetric} from './multiscale_math.mjs';
const [data,mode,runLabel]=process.argv.slice(2);
assert.ok(!runLabel||/^[A-Za-z0-9_-]+$/.test(runLabel),'Use a simple independent rebuild label');
assert.ok(data&&['aws','tryfan-regional','riffelhorn-regional','riffelhorn-appearance'].includes(mode));
const planBytes=await readFile('docs/atlas/multiscale-representation-plan.json'),plan=JSON.parse(planBytes);
const hash=b=>createHash('sha256').update(b).digest('hex');
const safe=url=>{try{const u=new URL(url);return u.origin+u.pathname;}catch{return 'non-URL';}};
const out=path.join(data,'experiments/atlas/multiscale-representation-v1',runLabel?`captures-${runLabel}`:'captures',mode);
try{await readFile(path.join(out,'capture.json'));throw new Error('Capture record already exists; use an independent run label');}catch(e){if(e.code!=='ENOENT')throw e;}
await mkdir(out,{recursive:true});
const scenes=mode==='aws'?plan.scenes:plan.scenes.filter(s=>s.site===(mode.startsWith('tryfan')?'tryfan':'riffelhorn'));
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
const server=await vite({configFile:false,plugins:[react(),{name:'multiscale-audit-only',enforce:'pre',load(id){if(visual&&id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(visual)};`;},transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port:4173,strictPort:true,forwardConsole:false}});
const save=()=>writeFile(path.join(out,'capture.json'),JSON.stringify(report,null,2)+'\n');
async function settle(){await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});await page.waitForTimeout(750);}
async function snapshot(){return page.evaluate(()=>{
 const m=globalThis.__atlasEvaluationMap,points=[];
 // Central and upper/lower viewport probes avoid most controls. DEM height queries refer to loaded, exaggerated terrain.
 for(const row of [.25,.5,.75]){const pixel=[720,900*row],xyz=([x,y])=>{const p=m.unproject([x,y]);return[p.lng,p.lat,m.queryTerrainElevation(p)];};points.push({row,pixel,origin:xyz(pixel),east:xyz([pixel[0]+2,pixel[1]]),south:xyz([pixel[0],pixel[1]+2])});}
 const actualDEMs=m.terrain?.tileManager.getRenderableTiles().map(t=>({render:t.tileID.canonical,source:m.terrain.tileManager.getSourceTile(t.tileID,true)?.tileID.canonical}));
 const sourceTiles=id=>m.style.tileManagers[id]?.getVisibleCoordinates().map(c=>({z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:m.style.tileManagers[id].getTile(c).state}));
 return{camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),projection:m.getProjection(),mesh:m.terrain?.meshSize,points,actualDEMs,reliefTiles:sourceTiles('terrain-analysis-dem'),imageryTiles:sourceTiles('swissimage-baseline'),commonImageryTiles:sourceTiles('satellite-imagery-source'),hillshade:m.getLayer('terrain-hillshade').serialize().paint,sources:m.getStyle().sources,satellite:m.getLayer('satellite-imagery-layer')?.serialize().paint};
 });}
try{
 if(gateway)await new Promise(r=>gateway.listen(4188,'127.0.0.1',r));await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();page=await browser.newPage({viewport:plan.viewport,deviceScaleFactor:1});
 page.on('pageerror',e=>report.pageErrors.push(String(e).replace(/\?[^\s]+/g,'?REDACTED')));page.on('requestfailed',r=>report.failures.push({url:safe(r.url()),error:r.failure()?.errorText}));page.on('response',r=>{if(r.status()>=400)report.httpErrors.push({url:safe(r.url()),status:r.status()});});
 await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Multiscale Atlas-only audit'}));
 await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
 const appearances=imagery?['common','regional']:['terrain'];
 if(imagery){await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scenes[0]);await settle();await page.getByRole('button',{name:'Satellite basemap',exact:true}).click();await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getLayoutProperty('satellite-imagery-layer','visibility')==='visible',null,{timeout:90000});
  await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap,layers=m.getStyle().layers,i=layers.findIndex(l=>l.id==='satellite-imagery-layer');m.addSource('swissimage-baseline',{type:'raster',tiles:['http://127.0.0.1:4188/imagery/{z}/{x}/{y}.png'],tileSize:512,minzoom:12,maxzoom:18,bounds:[7.748260056402138,45.970074962275305,7.77417077736836,45.988139457488266],attribution:'©swisstopo, retained 2023 source-derived product'});m.addLayer({id:'swissimage-baseline',type:'raster',source:'swissimage-baseline',layout:{visibility:'none'},paint:{'raster-opacity':1,'raster-fade-duration':180,'raster-resampling':'linear'}},layers[i+1]?.id);});
 }
 for(const appearance of appearances){if(imagery)await page.evaluate(a=>globalThis.__atlasEvaluationMap.setLayoutProperty('swissimage-baseline','visibility',a==='regional'?'visible':'none'),appearance);
  for(const scene of scenes){await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settle();const state=await snapshot();assert.deepEqual(state.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(state.mesh,128);assert.equal(state.hillshade['hillshade-method'],'igor');
   // Remove secret-bearing tile URLs from saved source declarations.
   for(const s of Object.values(state.sources)){if(s.tiles)s.tiles=s.tiles.map(safe);if(s.url)s.url=safe(s.url);}
   for(const p of state.points){p.renderedMetric=surfaceMetric(p.origin,p.east,p.south);p.physicalMetric=surfaceMetric(...[p.origin,p.east,p.south].map(v=>[v[0],v[1],v[2]/1.45]));}
   const filename=`${scene.id}--${appearance}.png`,bytes=await page.screenshot({path:path.join(out,filename)});report.scenes.push({scene,appearance,state,filename,sha256:hash(bytes)});console.log('CAPTURE',mode,scene.id,appearance);await save();
  }
 }
 assert.deepEqual(report.pageErrors,[]);for(const [f,h]of Object.entries(plan.productionHashes))assert.equal(hash(await readFile(f)),h);
}catch(e){report.failure=String(e);throw e;}
finally{await save();if(browser)await browser.close();await server.close();if(gateway)await new Promise(r=>gateway.close(r));}
