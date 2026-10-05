// Explicit isolated baseline entry point. No production module or normal Vite config changes.
import {createServer as vite} from 'vite';
import {createServer} from 'node:http';
import react from '@vitejs/plugin-react';
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {swissGeometry} from './swissimage_geometry.mjs';
import {tileFootprint} from './terrainProofGateway.mjs';
const [data,out]=process.argv.slice(2);assert.ok(data&&out);
const product=path.join(data,'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1');
const imagery=JSON.parse(await readFile(path.join(product,'manifest.json'),'utf8'));
const probes=JSON.parse(await readFile(path.join(product,'probe-locations.json'),'utf8'));
const cameraFile=JSON.parse(await readFile('docs/atlas/two-band-cameras.json','utf8'));
const ids=['centre-12.4-b0','centre-14.2-b0','centre-16.2-b0','centre-16.2-b180'];
const cameras=ids.map(id=>{const c=cameraFile.central.find(c=>c.id===id);assert.ok(c);return c;});
const hash=b=>createHash('sha256').update(b).digest('hex');
// Strip query credentials before retaining any network diagnostics.
const safe=url=>{try{const u=new URL(url);return u.origin+u.pathname;}catch{return 'non-URL';}};
const report={baseline:'6f2eb02',imageryIdentity:imagery.identity,viewport:{width:1920,height:1080},devicePixelRatio:1,scenes:[],navigation:[],requests:[],failures:[],pageErrors:[],geometry:[]};
const protectedFiles=['src/atlas/map/visualTerrainConfig.ts','src/atlas/map/satelliteProvider.ts','src/atlas/map/satelliteLayer.ts','src/atlas/terrain/analyticalElevationConfig.ts','src/atlas/map/terrainLayers.ts','src/atlas/map/AtlasMap.ts','src/atlas/map/atlasVisuals.ts','src/atlas/terrain/terrainElevationSampler.ts'];
report.productionHashes=Object.fromEntries(await Promise.all(protectedFiles.map(async f=>[f,hash(await readFile(f))])));
const loader=await vite({configFile:false,logLevel:'silent',server:{middlewareMode:true}});
const geometry=await swissGeometry(loader,data);await loader.close();report.geometry=geometry.identities;
const selected=geometry.selectTerrain(geometry.registry,{location:{coordinates:cameras[0].center,crs:'OGC:CRS84'},scale:{scheme:geometry.registry.hierarchy.common.levelScheme,requestedLevel:'z18'}});
const adapted=geometry.adaptTerrainToMapLibre(geometry.registry,selected);report.geometrySetup=selected;report.geometryAdapter=adapted;
const imageryFiles=new Map(imagery.files.filter(f=>f.path.startsWith('tiles/')).map(f=>[f.path,f]));
let page,browser;
const gateway=createServer(async(req,res)=>{
 const m=/^\/(imagery|terrain)\/(\d+)\/(\d+)\/(\d+)\.png$/.exec(req.url);
 if(!m){res.writeHead(404).end();return;}
 const [,kind,...parts]=m,[z,x,y]=parts.map(Number);
 if(z<0||z>18||x<0||y<0||x>=2**z||y>=2**z){res.writeHead(400).end();return;}
 try{let body;
  if(kind==='imagery'){
   const key=`tiles/${z}/${x}/${y}.png`,f=imageryFiles.get(key);
   body=await readFile(path.join(product,f?key:'transparent.png'));
   // Missing regional support is transparent; common imagery remains visible below.
   if(f)assert.equal(hash(body),f.sha256);

   report.requests.push({kind,z,x,y,product:imagery.id,support:f?'manifest':'absent-transparent',status:200});
  }else{
   const decision=geometry.selectTerrain(geometry.registry,{footprint:tileFootprint(z,x,y),scale:{scheme:geometry.registry.hierarchy.common.levelScheme,requestedLevel:`z${z}`},provenanceRequirement:'product-lineage'});
   assert.equal(decision.status,'selected');const delivery=geometry.adaptTerrainToMapLibre(geometry.registry,decision);
   const root=geometry.productRoots[decision.product.id];
   if(root){assert.ok(delivery.maxzoom>=z);body=await readFile(path.join(root,`tiles/${z}/${x}/${y}.png`));}
   else{assert.equal(delivery.tiles[0],'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png');const r=await fetch(`http://127.0.0.1:4187/aws/${z}/${x}/${y}.png`);assert.ok(r.ok);body=Buffer.from(await r.arrayBuffer());}
   report.requests.push({kind,z,x,y,decision,status:200});
  }
  res.writeHead(200,{'content-type':'image/png','content-length':body.length,'access-control-allow-origin':'*','cache-control':'public,max-age=3600'}).end(body);
 }catch(e){report.requests.push({kind,z,x,y,error:String(e),status:502});res.writeHead(502).end(String(e));}
});
const visual={tileTemplate:'http://127.0.0.1:4188/terrain/{z}/{x}/{y}.png',encoding:adapted.encoding,tileSize:adapted.tileSize,geometryMaxZoom:18,reliefMaxZoom:18,attribution:'©swisstopo (fixed experimental geometry); AWS fallback outside complete support'};
const server=await vite({configFile:false,plugins:[react(),{name:'appearance-baseline-only',enforce:'pre',load(id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(visual)};`;},transform(code,id){if(id.replaceAll('\\','/').endsWith('/src/atlas/map/AtlasMap.ts'))return code.replace('    this.map.addControl(','    (globalThis as typeof globalThis & { __atlasEvaluationMap?: maplibregl.Map }).__atlasEvaluationMap = this.map;\n    this.map.addControl(');}}],server:{host:'127.0.0.1',port:4173,strictPort:true,forwardConsole:false}});
await mkdir(out,{recursive:true});
const save=()=>writeFile(path.join(out,'capture.json'),JSON.stringify(report,null,2)+'\n');
async function settle(){await page.waitForFunction(()=>{const m=globalThis.__atlasEvaluationMap;return m.isStyleLoaded()&&m.areTilesLoaded()&&!m.isMoving();},null,{timeout:90000});await page.waitForTimeout(500);}
async function state(){return page.evaluate(probes=>{
 const m=globalThis.__atlasEvaluationMap;
 const projection=probes.map(p=>{const q=m.project(p.lonlat),hit=m.unproject(q);return{id:p.id,patch:p.patch,lonlat:p.lonlat,screen:[q.x,q.y],visibleScreen:q.x>=0&&q.x<1920&&q.y>=0&&q.y<1080,firstSurface:hit.toArray(),roundtripDegreeError:Math.hypot(hit.lng-p.lonlat[0],hit.lat-p.lonlat[1]),elevation:m.queryTerrainElevation(p.lonlat)};});
 return {camera:{center:m.getCenter().toArray(),zoom:m.getZoom(),pitch:m.getPitch(),bearing:m.getBearing()},terrain:m.getTerrain(),projection:m.getProjection(),mesh:m.terrain?.meshSize,hillshade:m.getLayer('terrain-hillshade').serialize().paint,satellite:m.getLayer('satellite-imagery-layer').serialize().paint,regional:m.getLayer('swissimage-baseline')?.serialize().paint,probes:projection,usedImagery:m.style.tileManagers['swissimage-baseline']?.getVisibleCoordinates().map(c=>({z:c.canonical.z,x:c.canonical.x,y:c.canonical.y,state:m.style.tileManagers['swissimage-baseline'].getTile(c).state})),usedDEMs:m.terrain?.tileManager.getRenderableTiles().map(t=>m.terrain.tileManager.getSourceTile(t.tileID,true)?.tileID.canonical).filter(Boolean)};
},probes);}
try{
 await new Promise(resolve=>gateway.listen(4188,'127.0.0.1',resolve));await server.listen();browser=await chromium.launch({headless:true});report.browserVersion=browser.version();
 page=await browser.newPage({viewport:report.viewport,deviceScaleFactor:1});
 page.on('pageerror',e=>report.pageErrors.push(String(e).replace(/\?[^\s]+/g,'?REDACTED')));
 page.on('response',r=>{if(r.url().includes('api.maptiler.com'))report.requests.push({kind:'maptiler',url:safe(r.url()),status:r.status()});});
 page.on('requestfailed',r=>report.failures.push({url:safe(r.url()),error:r.failure()?.errorText}));
 await page.route('**/weather/gfs/**',r=>r.fulfill({status:503,body:'Appearance-only evaluation; no Weather publication'}));
 await page.goto('http://127.0.0.1:4173/',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>globalThis.__atlasEvaluationMap?.getLayer('terrain-hillshade'),null,{timeout:60000});
 await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),cameras[0]); await settle(); await page.getByRole('button',{name:'Satellite basemap',exact:true}).click(); await save();
 await page.waitForFunction(()=>globalThis.__atlasEvaluationMap.getLayer('satellite-imagery-layer')&&globalThis.__atlasEvaluationMap.getLayoutProperty('satellite-imagery-layer','visibility')==='visible',null,{timeout:90000});
 await page.evaluate(()=>{const m=globalThis.__atlasEvaluationMap;m.addSource('swissimage-baseline',{type:'raster',tiles:['http://127.0.0.1:4188/imagery/{z}/{x}/{y}.png'],tileSize:512,minzoom:12,maxzoom:18,bounds:[7.748260056402138,45.970074962275305,7.77417077736836,45.988139457488266],attribution:'©swisstopo (2023 source-derived experimental appearance)'});
 const layers=m.getStyle().layers;const i=layers.findIndex(l=>l.id==='satellite-imagery-layer');
 m.addLayer({id:'swissimage-baseline',type:'raster',source:'swissimage-baseline',layout:{visibility:'none'},paint:{'raster-opacity':1,'raster-fade-duration':180,'raster-resampling':'linear'}},layers[i+1]?.id);
 });
 for(const mode of ['common','regional']){
  await page.evaluate(mode=>globalThis.__atlasEvaluationMap.setLayoutProperty('swissimage-baseline','visibility',mode==='regional'?'visible':'none'),mode);
  for(const scene of cameras){await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),scene);await settle();const s=await state();
   assert.deepEqual(s.terrain,{source:'terrain-dem',exaggeration:1.45});assert.equal(s.mesh,128);assert.equal(s.satellite['raster-opacity'],1);assert.equal(s.hillshade['hillshade-method'],'igor');assert.ok(s.hillshade['hillshade-exaggeration'].filter((_,i)=>i>=4&&i%2===0).every(v=>v===0));
   const filename=`${scene.id}--${mode}.png`;const bytes=await page.screenshot({path:path.join(out,filename)});
   report.scenes.push({mode,scene,filename,sha256:hash(bytes),state:s});console.log('CAPTURE',mode,scene.id);await save();
  }
  await page.evaluate(s=>globalThis.__atlasEvaluationMap.jumpTo(s),cameras[0]);await settle();
  for(const scene of [cameras[1],cameras[2],cameras[1]]){
   await page.evaluate(s=>globalThis.__atlasEvaluationMap.easeTo({...s,duration:1500}),scene);const frames=[];
   for(let i=0;i<6;i++){await page.waitForTimeout(250);const s=await state();delete s.probes;frames.push(s);}
   await settle();report.navigation.push({mode,target:scene,frames});await save();
  }
 }
 assert.deepEqual(report.pageErrors,[]);
 for(const f of protectedFiles)assert.equal(hash(await readFile(f)),report.productionHashes[f]);
}catch(e){report.failure=String(e);throw e;}
finally{await save();if(browser)await browser.close();await server.close();await new Promise(resolve=>gateway.close(resolve));}
