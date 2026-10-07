// S4 read-only portrayal/provenance projection and generation-pinned service contexts.
import { readFileSync,writeFileSync,mkdirSync,existsSync,statSync,openSync,fsyncSync,closeSync } from 'node:fs';
import { join } from 'node:path';
import { performance } from 'node:perf_hooks';
import { load,register,STORE,storePath } from './generations.mjs';
import { DATA } from './catalogue.mjs';
import { NativeSession,openEvidence } from './query.mjs';
import { openWorld } from './world.mjs';
import { encode,sha,safePath,requireThat } from './identity.mjs';
import { validateDelivery,verifyDelivery,terrainBindings } from './delivery-schema.mjs';
const recipeFile=join(import.meta.dirname,'display-recipe.json');
export const recipe=JSON.parse(readFileSync(recipeFile,'utf8'));
const base=g=>'/pilot/v1/g/'+g;
export async function buildDelivery({store=STORE,dataRoot=DATA}={}) {
 const start=performance.now(),snapshot=load(store,{dataRoot}),session=new NativeSession();let e;
 try {
  requireThat(snapshot.value.understanding,'understanding-unavailable','S3 state required');
  e=await openEvidence({store,dataRoot,generation:snapshot.generation,nativeSession:session});
  const d=await session.call({operation:'display',palette:recipe.worldcover.palette,probes:snapshot.value.understanding.probes});
  const directory=join(storePath(store),'artifacts');mkdirSync(directory,{recursive:true});
  const assets=[];
  function materialize(family,body,mime) {
   const id=sha(body),file=join(directory,id+(mime==='image/png'?'.png':'.json'));
   if(existsSync(file))requireThat(readFileSync(file).equals(body),'immutable-conflict','Materialized artifact changed');
   else writeFileSync(file,body,{flag:'wx'});
   const fd=openSync(file,'r+');try{fsyncSync(fd);}finally{closeSync(fd);} // Durable portrayal closure before S1 root switch.
   assets.push({id,sha256:id,bytes:body.length,mime,family,origin:{kind:'materialized'},rightsRef:sha(encode({rights:family}))});return id;
  }
  const wc=materialize('worldcover',Buffer.from(d.worldcoverPNG,'base64'),'image/png'),nrw=materialize('nrw',Buffer.from(encode(d.nrw)),'application/geo+json');
  const a=snapshot.value.catalogue.artifacts.find(a=>a.uses.some(u=>u.family==='appearance') && a.aliases.some(a=>a.endsWith('/lab010-natural-colour-10m.png')));
  requireThat(a,'required-state-unavailable','Registered Lab010 display absent');
  assets.push({id:a.sha256,sha256:a.sha256,bytes:a.bytes,mime:'image/png',family:'appearance',origin:{kind:'retained',artifact:a.id},rightsRef:sha(encode({rights:'appearance'}))});
  const serving={schema:'atlas-tryfan-delivery/v1',recipeSha256:sha(readFileSync(recipeFile)),assets:assets.sort((a,b)=>a.family.localeCompare(b.family)),
   layers:{appearance:{asset:a.sha256,crs:'EPSG:27700',bounds:recipe.appearance.bounds,width:300,height:300,time:'2026-07-12T11:33:31.024Z',display:'Existing Lab010 fixed display; no correction'},
    worldcover:{asset:wc,grid:e.metadata.families.worldcover.grid,palette:recipe.worldcover.palette,time:'2021 nominal classification epoch; individual observation times unknown',display:recipe.worldcover.sampling},
    nrw:{asset:nrw,featureCount:193,crs:'OGC:CRS84',nativeCRS:'EPSG:27700',time:'Historical inventory; exact native survey/validity times unknown'},
    terrain:{families:['terrain-common','terrain-regional'],availability:'Common z5 context/two z14 samples only; registered Welsh not applicable in G0',encoding:'Exact Terrarium PNG; delivery sampling is not physical accuracy'}},probes:d.probes,tiles:terrainBindings(snapshot.value.catalogue)};
  validateDelivery(serving,snapshot.value.catalogue);verifyDelivery(store,serving);
  const value={...snapshot.value,parent:snapshot.generation,capabilities:{...snapshot.value.capabilities,serving:true},serving};
  return {value,locators:snapshot.locators,metrics:{buildMilliseconds:performance.now()-start,servingManifestBytes:Buffer.byteLength(encode(serving)),materializedBytes:assets.filter(a=>a.origin.kind==='materialized').reduce((n,a)=>n+a.bytes,0)}};
 } finally{e?.close();session.close();}
}
export async function publishDelivery(options={}) {
 const snapshot=load(options.store??STORE,{dataRoot:options.dataRoot??DATA});
 const built=await buildDelivery(options);
 if(snapshot.value.serving && encode(snapshot.value.serving)===encode(built.value.serving))return {generation:snapshot.generation,alreadyPublished:true,buildMetrics:built.metrics};return {...register(options.store??STORE,built.value,built.locators,{dataRoot:options.dataRoot??DATA}),buildMetrics:built.metrics};
}
export async function openDelivery({store=STORE,dataRoot=DATA}={}) {
 const contexts=new Map(),session=new NativeSession(),metrics={pins:0,queries:0,bytesRead:0,assetReads:0,workerCount:1};
 // Accept only current ancestry: a complete pre-switch orphan is not published truth.
 function published(id) {
  let s=load(store,{dataRoot,verify:false});if(!id)return s;
  while(s.generation!==id && s.value.parent)s=load(store,{generation:s.value.parent,dataRoot,verify:false});
  requireThat(s.generation===id,'generation-missing','Generation unknown or unpublished');return s;
 }
 async function pin(id) {
  const snapshot=published(id),g=snapshot.generation;metrics.pins++;
  requireThat(snapshot.value.serving,'serving-unavailable','Requested generation predates serving publication');
  if(!contexts.has(g)) {
   requireThat(contexts.size<16,'worker-unavailable','Finite service context limit16 reached; restart explicitly');
   const promise=(async()=>{const world=await openWorld({store,dataRoot,generation:g,nativeSession:session});return {snapshot,world};})();
   contexts.set(g,promise);try{await promise;}catch(e){contexts.delete(g);throw e;}
  }
  return {generation:g,protocol:'atlas-tryfan-serving/v1',capabilities:snapshot.value.capabilities,core:structuredClone(snapshot.value.core)};
 }
 async function context(id){requireThat(id,'invalid-generation-id','Explicit pinned generation required');await pin(id);return contexts.get(id);}
 function project(value,g) {
  // Native/provenance concepts remain; storage locators and receipt filenames do not.
  const aliases=new Map();for(const a of published(g).value.catalogue.artifacts)for(const alias of a.aliases)aliases.set(alias,{artifact:a.id,sha256:a.sha256});
  function clean(v) {
   if(Array.isArray(v))return v.map(clean);
   if(v && typeof v==='object')return Object.fromEntries(Object.entries(v).filter(([k])=>!['aliases','metadataReceipt','metadataReceipts','methodFiles','receipts','path','storageLocator'].includes(k)).map(([k,x])=>[k,clean(k==='selector' && typeof x==='string'?x.replace(/^[\w-]+\.(json|tif)\s+/,''):x)]));
   if(typeof v==='string') {
    if(aliases.has(v))return base(g)+'/provenance/'+sha(encode(aliases.get(v).artifact));
    if(v.startsWith('meridian-data://')||v.startsWith('docs/')||v.startsWith('scripts/'))return base(g)+'/provenance/'+sha(encode({reference:v}));
   }
   return v;
  }
  return clean(value);
 }
 async function manifest(g) {
  const {snapshot}=await context(g),s=project(snapshot.value.serving,g),c=snapshot.value.catalogue;
  return {protocol:'atlas-tryfan-serving/v1',generation:g,core:structuredClone(snapshot.value.core),capabilities:snapshot.value.capabilities,...s,
   assets:s.assets.map(a=>({...a,url:base(g)+'/assets/'+a.id,rightsURL:base(g)+'/provenance/'+a.rightsRef})),
   families:c.families.map(f=>({id:f.id,source:f.source,product:f.product,representations:f.representations,rightsURL:base(g)+'/provenance/'+sha(encode({rights:f.id})),qualification:project(f.qualification,g)})),
   terrain:terrainBindings(c).map(t=>({...t,url:base(g)+'/terrain/'+t.family+'/'+[t.tile.z,t.tile.x,t.tile.y].join('/')+'.png'}))};
 }
 async function query(g,request) {
  const {world,snapshot}=await context(g);metrics.queries++;
  const {methodRevision,...worldRequest}=request??{};
  requireThat(methodRevision===undefined || typeof methodRevision==='string' && methodRevision.length>0 && methodRevision.length<=128 && ['derived-slope','derived-area-ratio'].includes(worldRequest.property),'invalid-request','Method-relative assessment only for retained derived properties');
  const answer=project(await world.query(methodRevision===undefined?request:worldRequest),g);
  if(methodRevision!==undefined && answer.answers[0]?.result?.claim){
   const ref=answer.answers[0].result.claim;const assessment=world.assess({methodRevision}).find(a=>a.ref.id===ref.id && a.ref.revision===ref.revision).assessment;
   answer.freshness=assessment;answer.answers[0].freshness=assessment;answer.answers[0].status=assessment.status==='stale'?'stale':assessment.status==='fresh'?'available':'unavailable';answer.methodPolicy={revision:methodRevision,qualification:'Read-only policy-relative assessment; no method execution/recomputation or source revision'};
  }
  function attach(v) {
   if(!v || typeof v!=='object')return;
   if(v.selection?.family) {
    const probe=snapshot.value.serving.probes.find(p=>p.pointBNG.every((n,i)=>n===request.place?.point?.[i]) || p.pointCRS84.every((n,i)=>n===request.place?.point?.[i]));
    const family=v.selection.family==='production-common'?'terrain-common':'terrain-regional',tile=probe?.xyz;
    const asset=tile && terrainBindings(snapshot.value.catalogue).find(u=>u.family===family && ['z','x','y'].every(k=>u.tile[k]===tile[k]));
    v.delivery={status:asset?'available':'unavailable',generation:g,family,probe:probe??null,url:asset?base(g)+'/terrain/'+family+'/'+[tile.z,tile.x,tile.y].join('/')+'.png':null,qualification:'Exact retained native Mercator tile; no resampling or cross-CRS corner stretch'};
   }
   for(const child of Object.values(v))if(child!==v.delivery)attach(child);
  }
  attach(answer);
  // Result refs route back through a finite lineage view, never internal manifests.
  answer.provenanceURL=base(g)+'/provenance/'+sha(encode({world:'qualified-lineage'}));
  return answer;
 }
 async function provenance(g,key) {
  const {snapshot}=await context(g),c=snapshot.value.catalogue;
  const family=c.families.find(f=>sha(encode({rights:f.id}))===key);
  if(family)return {generation:g,family:family.id,source:project(c.sources.find(s=>s.id===family.source),g),product:project(c.products.find(p=>p.id===family.product),g),rights:project(family.nativeMetadata.rights??family.nativeMetadata.product?.rights??family.nativeMetadata.resources?.map(r=>r.rights)??{status:'unknown'},g),qualification:project(family.qualification,g)};
  if(key===sha(encode({world:'qualified-lineage'})))return {generation:g,sources:project(c.sources,g),products:project(c.products,g),representations:project(c.representations,g),families:c.families.map(f=>({family:f.id,source:f.source,product:f.product,representations:f.representations,rightsURL:base(g)+'/provenance/'+sha(encode({rights:f.id}))})),derived:project(snapshot.value.understanding.results.map(r=>({claim:r.claim,receipt:r.receipt,probe:r.probe,property:r.property})),g)};
  const refs=new Set();function collect(v){if(typeof v==='string' && (v.startsWith('docs/')||v.startsWith('scripts/')))refs.add(v);else if(v && typeof v==='object')for(const x of Object.values(v))collect(x);}
  collect(c);collect(snapshot.value.knowledge);collect(snapshot.value.understanding);
  const reference=[...refs].find(v=>sha(encode({reference:v}))===key);
  if(reference){const receipt=c.basis.metadataReceipts.find(r=>r.path===reference);return {generation:g,reference:key,sha256:receipt?.sha256??snapshot.value.understanding.basis.receipts?.[reference]??null,qualification:'Retained source/processing proof reference; storage address remains internal'};}
  const entity=[...c.sources,...c.products,...c.representations,...c.artifacts].find(r=>r.id===key || sha(encode(r.id))===key);
  requireThat(entity,'reference-missing','Unknown provenance reference');return {generation:g,record:project(entity,g)};
 }
 async function bytes(g,key,tile) {
  const {snapshot}=await context(g),s=snapshot.value.serving;
  let a,body,mime,family;
  if(tile) {
   const binding=terrainBindings(snapshot.value.catalogue).find(u=>u.family===tile.family && ['z','x','y'].every(k=>u.tile[k]===tile[k]));
   a=binding && snapshot.value.catalogue.artifacts.find(a=>a.id===binding.artifact);
   requireThat(a,'artifact-unavailable','Selected terrain bytes are not retained at requested level/address');family=tile.family;mime='image/png';
  }else {
   const portrayal=s.assets.find(a=>a.id===key);requireThat(portrayal,'asset-missing','Unknown serving asset');mime=portrayal.mime;family=portrayal.family;
   a=portrayal.origin.kind==='retained'?snapshot.value.catalogue.artifacts.find(a=>a.id===portrayal.origin.artifact):portrayal;
  }
  const file=a.origin?.kind==='materialized'?safePath(store,'artifacts/'+a.id+(mime==='image/png'?'.png':'.json')):safePath(dataRoot,snapshot.locators[a.id]);
  requireThat(statSync(file).size<64*1024*1024,'artifact-unavailable','Read exceeds bounded buffer');body=readFileSync(file);
  requireThat(body.length===a.bytes && sha(body)===a.sha256,'hash-mismatch','Registered delivery bytes changed');metrics.assetReads++;metrics.bytesRead+=body.length;
  return {body,mime,sha256:a.sha256,rightsURL:base(g)+'/provenance/'+sha(encode({rights:family}))};
 }
 return {pin,manifest,query,provenance,bytes,project,metrics,close:async()=>{for(const p of contexts.values()){try{await(await p).world.close();}catch{}}session.close();}};
}
