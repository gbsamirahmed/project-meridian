// S4 publication closure for rebuildable portrayal, not semantic evidence.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { requireThat,fields,encode,sha,safePath } from './identity.mjs';
// Explicit retained sample addressing, independently of movable storage locators.
export function terrainBindings(c) {
 const common={
  'cb81fc13e12e530cbdb5bdb899a665f70e2f740430102498c0a276d99d1b0ef9':[14,8010,5328],
  '56728a2c278801c3aea6cf9d1e7c513c829636404696472819640c4581e70a12':[14,8009,5329],
  '9b661bb849997f0e07d9a0cb865d13487080922c80196cc59f1d434cfa889e5c':[5,15,10]};
 return c.artifacts.flatMap(a=>a.uses.flatMap(u=>{
  const xyz=common[a.sha256],tile=u.tile??(u.family==='terrain-common' && xyz?{crs:'EPSG:3857',scheme:'xyz',z:xyz[0],x:xyz[1],y:xyz[2]}:null);
  return tile?[{artifact:a.id,sha256:a.sha256,bytes:a.bytes,family:u.family,tile}]:[];
 })).sort((a,b)=>encode(a).localeCompare(encode(b),'en'));
}
export function validateDelivery(s,c) {
 fields(s,['schema','recipeSha256','assets','layers','probes'],['tiles']);
 requireThat(s.schema==='atlas-tryfan-delivery/v1' && /^[a-f0-9]{64}$/.test(s.recipeSha256),'invalid-serving-state','Unknown serving schema/recipe');
 requireThat(Array.isArray(s.assets) && s.assets.length===3 && new Set(s.assets.map(a=>a.id)).size===3,'invalid-serving-state','Exactly three distinct portrayal assets required');
 for(const a of s.assets) {
  fields(a,['id','sha256','bytes','mime','family','origin','rightsRef']);
  requireThat(a.id===a.sha256 && /^[a-f0-9]{64}$/.test(a.id) && Number.isSafeInteger(a.bytes) && a.bytes>0 && a.bytes<64*1024*1024 && ['image/png','application/geo+json'].includes(a.mime),'invalid-serving-state','Invalid immutable portrayal artifact');
  requireThat(['appearance','worldcover','nrw'].includes(a.family) && a.rightsRef===sha(encode({rights:a.family})),'invalid-serving-state','Required source rights link');
  requireThat(a.origin.kind==='materialized' || a.origin.kind==='retained' && c.artifacts.some(x=>x.id===a.origin.artifact && x.sha256===a.sha256 && x.bytes===a.bytes && x.uses.some(u=>u.family===a.family)),'invalid-serving-state','Invalid source/materialization reference');
 }
 requireThat(s.assets.filter(a=>a.origin.kind==='retained').length===1 && s.assets.find(a=>a.family==='appearance').origin.kind==='retained','invalid-serving-state','Appearance remains exact retained bytes');
 for(const a of s.assets)requireThat(a.mime===(a.family==='nrw'?'application/geo+json':'image/png'),'invalid-serving-state','Family portrayal MIME changed');
 for(const f of ['appearance','worldcover','nrw'])requireThat(s.layers[f]?.asset===s.assets.find(a=>a.family===f).id,'invalid-serving-state','Layer/asset closure');
 requireThat(s.layers.worldcover.grid.shape.join(',')==='334,554' && s.layers.nrw.featureCount===193 && s.probes.length===2,'invalid-serving-state','Native portrayal support changed');
 const recipe=JSON.parse(readFileSync(join(import.meta.dirname,'display-recipe.json'),'utf8'));
 requireThat(encode(s.layers.appearance.bounds)===encode(recipe.appearance.bounds) && s.layers.appearance.crs==='EPSG:27700' && s.layers.appearance.width===300 && s.layers.appearance.height===300 && s.layers.appearance.time==='2026-07-12T11:33:31.024Z','invalid-serving-state','Retained appearance footprint/date changed');
 requireThat(s.layers.worldcover.grid.cells===185036 && s.layers.worldcover.grid.crs==='EPSG:4326' && s.layers.worldcover.grid.nodata===0 && s.layers.worldcover.grid.dtype==='uint8' && encode(s.layers.worldcover.palette)===encode(recipe.worldcover.palette) && s.layers.nrw.crs==='OGC:CRS84' && s.layers.nrw.nativeCRS==='EPSG:27700','invalid-serving-state','Native display encoding/support changed');
 if(s.tiles)requireThat(encode(s.tiles)===encode(terrainBindings(c)),'invalid-serving-state','Exact registered native XYZ bindings required');
 return s;
}
export function verifyDelivery(store,s) {
 for(const a of s.assets.filter(a=>a.origin.kind==='materialized')) {
  const file=safePath(store,'artifacts/'+a.id+(a.mime==='image/png'?'.png':'.json')),body=readFileSync(file);
  requireThat(body.length===a.bytes && sha(body)===a.sha256,'serving-integrity','Serving artifact changed');
 }
 const body=readFileSync(join(import.meta.dirname,'display-recipe.json'));
 requireThat(sha(body)===s.recipeSha256,'serving-integrity','Serving recipe revision unavailable');
}
