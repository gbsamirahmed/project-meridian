// Pilot S3: bounded retained derivation, replay and policy-relative lifecycle.
import { readFileSync } from 'node:fs';
import { resolve,join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { createServer } from 'vite';
import { ROOT,DATA,frozenPlan } from './catalogue.mjs';
import { load,STORE,register } from './generations.mjs';
import { openEvidence } from './query.mjs';
import { encode,json,sha,safePath,requireThat } from './identity.mjs';
import { METHOD,basis,ref,resultKey,validateDependencies } from './dependencies.mjs';
const clone=v=>JSON.parse(JSON.stringify(v));
export async function methods({dataRoot=DATA}={}) {
 requireThat(!dataRoot.toLowerCase().includes('meridian-private'),'invalid-locator','Private data excluded before access');frozenPlan();
 const pinned=basis();for(const [p,h] of Object.entries({...pinned.methodFiles,...pinned.receipts}))requireThat(sha(readFileSync(resolve(ROOT,p)))===h,'method-unavailable','Pinned method or receipt changed');
 const server=await createServer({configFile:false,root:ROOT,appType:'custom',logLevel:'silent',server:{middlewareMode:true,hmr:false}});
 try {
 const proof=await server.ssrLoadModule('/scripts/atlas/qualified-query-proof/proof.ts');
 const {registerTerrainHierarchy}=await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainRegistry.ts');
 const {selectTerrain}=await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainSelector.ts');
 const {createTryfanTerrainProof}=await server.ssrLoadModule('/src/atlas/terrain/metadata/tryfanTerrainProof.ts');
 const {validateSemanticEvidence}=await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');
 const input=json(resolve(ROOT,'docs/research/tryfan-qualified-query-inputs.json')),old=json(resolve(ROOT,'docs/research/tryfan-qualified-query-results.json'));
 function terrain(stage) {
  requireThat(['common','regional'].includes(stage),'invalid-context','Unknown applicability stage');const r=createTryfanTerrainProof();const hierarchy=clone(r.hierarchy);
  if(stage==='common'){hierarchy.id='tryfan-proof-common-context';hierarchy.revision='1';hierarchy.regional=[];hierarchy.selection.regionalOrder=[];}
  return clone({hierarchy,options:r.options});
 }
 function selections(u) {
  requireThat(encode(u.terrain)===encode(terrain(u.stage)),'invalid-hierarchy','Terrain declaration differs from frozen selector');
  const registry=registerTerrainHierarchy(u.terrain.hierarchy,u.terrain.options);
  return clone(Object.fromEntries(u.probes.map(p=>[p.id,selectTerrain(registry,{footprint:p.eligibilityFootprint,scale:{scheme:'XYZ Web Mercator zoom (delivery)',requestedLevel:'z14'}})])));
 }
 function available(u,catalogue,locators) {
  return u.roots.filter(r=>r.assets.every(a=>{
   const asset=catalogue.artifacts.find(x=>x.id==='sha256:'+a.sha256 && x.aliases.includes(a.href));if(!asset)return false;
   try{const body=readFileSync(safePath(dataRoot,locators[asset.id]));requireThat(sha(body)===asset.sha256 && body.length===asset.bytes,'artifact-integrity','Registered derivation bytes changed');return true;}
   catch(e){if(e.code==='artifact-unavailable')return false;throw e;}
  }));
 }
 function sample(requests,catalogue,locators) {
  const product=json(resolve(ROOT,'src/atlas/terrain/metadata/tryfanProductRecord.json'));
  const required=new Set(['meridian-data://'+product.source.path,'meridian-data://derived/atlas/tryfan/tryfan-welsh-regional-v2/manifest.json']);
  for(const request of requests){const root=input.roots.find(r=>r.probe===request.probe && r.family===request.family && r.level===request.level);requireThat(root,'input-unavailable','Requested frozen input root unavailable');root.assets.forEach(a=>required.add(a.href));}
  const bindings={};
  for(const a of catalogue.artifacts.filter(a=>a.aliases.some(alias=>required.has(alias))))for(const alias of a.aliases) {
   // The unchanged sampler may read only registered terrain files through this bridge.
   bindings[alias.replace('meridian-data://','')]={path:safePath(dataRoot,locators[a.id]),sha256:a.sha256,bytes:a.bytes};
  }
  const p=spawnSync(join(dataRoot,'earth-lab/.venv/Scripts/python.exe'),['-X','utf8',resolve(ROOT,'pilots/atlas/tryfan/adapters/retained_derivation.py')],
   {input:JSON.stringify({dataRoot,bindings,requests}),encoding:'utf8',maxBuffer:4*1024*1024,timeout:30000,env:{...process.env,PROJ_NETWORK:'OFF',PYTHONDONTWRITEBYTECODE:'1'}});
  requireThat(p.status===0,'input-unavailable',p.stderr||p.error?.message||'Retained sampler failed');const sampled=JSON.parse(p.stdout);
  requireThat(encode(sampled.software)===encode(input.software),'software-drift','Pinned scientific environment differs');
  for(const r of sampled.roots)requireThat(encode(r)===encode(input.roots.find(x=>x.id===r.id)),'input-drift','Fresh registered sampling differs from retained scientific root');
  return sampled;
 }
 function validate(u,catalogue) {
  const graph=validateDependencies(u,catalogue);selections(u);
  requireThat(proof.validateSlice(u.results,u.roots).length===0,'invalid-dependency','Frozen finite receipt validator rejected inputs');
  requireThat(validateSemanticEvidence(proof.bundle(u.results,u.roots,u.probes[0])).length===0,'contract-invalid','Derived evidence fails frozen v1');
  const sel=selections(u);
  const fresh=u.probes.flatMap(p=>u.results.filter(r=>r.probe===p.id && proof.assess(r,u.results,u.roots,sel[r.probe],'current-applicable-terrain-v1',[],METHOD).status==='fresh').map(ref));
  requireThat(encode(fresh)===encode(u.active),'invalid-active','Active references differ from policy-fresh retained results');return graph;
 }
 function initial(snapshot) {
  const terrainState=terrain('common'),u={schema:'atlas-tryfan-understanding/v1',basis:pinned,stage:'common',terrain:terrainState,probes:input.geometry.probes,roots:[],results:[],active:[]};
  const selected=selections(u),sampled=sample(u.probes.map(p=>({probe:p.id,family:selected[p.id].family,level:selected[p.id].level})),snapshot.value.catalogue,snapshot.locators);
  u.roots=sampled.roots.map(r=>{const a=clone(r);delete a.heightSamplesM;return a;});
  u.results=clone(u.probes.flatMap(p=>proof.derive(p,sampled.roots.find(r=>r.probe===p.id),METHOD)));u.active=u.results.map(ref);
  validate(u,snapshot.value.catalogue);return {understanding:u,measurement:sampled.measurement};
 }
 function assess(u,catalogue,locators,{stage=u.stage,changes=[],methodRevision=METHOD,policy='current-applicable-terrain-v1'}={}) {
  requireThat(['fixed-input-replay-v1','current-applicable-terrain-v1'].includes(policy),'invalid-policy','Unknown freshness policy');
  requireThat(typeof methodRevision==='string' && methodRevision.length && Array.isArray(changes),'invalid-context','Explicit method policy/change list required');
  for(const c of changes)requireThat(c && typeof c.inputId==='string' && typeof c.scopeKnown==='boolean' && (!c.scopeKnown || Array.isArray(c.bounds) && c.bounds.length===4 && c.bounds.every(Number.isFinite) && c.bounds[0]<=c.bounds[2] && c.bounds[1]<=c.bounds[3]),'invalid-change-scope','Known notification scope must be finite ordered BNG bounds');
  validate(u,catalogue);
  const context={...u,stage,terrain:terrain(stage)},selected=selections(context),roots=available(u,catalogue,locators);
  return clone(u.results.map(r=>({ref:ref(r),probe:r.probe,property:r.property,assessment:proof.assess(r,u.results,roots,selected[r.probe],policy,changes,methodRevision)})));
 }
 function recompute(u,catalogue,locators,{stage='regional'}={}) {
  // Isolated S3 lifecycle calculation only. Actual applicability-update publication belongs to S5.
  const statuses=assess(u,catalogue,locators,{stage});requireThat(!statuses.some(a=>a.assessment.status==='indeterminate'),'freshness-indeterminate','Cannot recompute without required exact dependencies');
  const affected=u.probes.filter(p=>statuses.some(a=>a.probe===p.id && a.assessment.status==='stale'));
  if(!affected.length)return {understanding:clone(u),considered:u.results.length,recomputed:[],reused:u.active,statuses};
  const next=clone(u);next.stage=stage;next.terrain=terrain(stage);const selected=selections(next);
  const sampled=sample(affected.map(p=>({probe:p.id,family:selected[p.id].family,level:selected[p.id].level})),catalogue,locators);
  next.roots=input.roots.filter(r=>stage==='regional'||r.family==='production-common').map(r=>{const a=clone(r);delete a.heightSamplesM;return a;});
  const added=clone(affected.flatMap(p=>proof.derive(p,sampled.roots.find(r=>r.probe===p.id),METHOD)));
  for(const r of added)if(!next.results.some(x=>resultKey(ref(x))===resultKey(ref(r))))next.results.push(r);
  next.active=next.probes.flatMap(p=>next.results.filter(r=>r.probe===p.id && proof.assess(r,next.results,next.roots,selected[p.id],'current-applicable-terrain-v1',[],METHOD).status==='fresh').map(ref));
  validate(next,catalogue);return {understanding:next,statuses,considered:u.results.length,recomputed:added.map(ref),reused:u.active.filter(a=>!affected.some(p=>u.results.find(r=>resultKey(ref(r))===resultKey(a)).probe===p.id)),measurement:sampled.measurement};
 }
 function replay(u,catalogue,locators,resultRef) {
  validate(u,catalogue);let target=u.results;
  if(resultRef){const wanted=u.results.find(r=>resultKey(ref(r))===resultKey(resultRef));requireThat(wanted,'historical-result-missing','Exact historical result unavailable');target=[wanted];}
  function rootOf(r){const use=r.receipt.inputs[0];return use.kind==='resource'?u.roots.find(x=>'retained-input:'+x.id===use.id && x.revision===use.revision):rootOf(u.results.find(x=>resultKey(ref(x))===resultKey(use)));}
  const roots=[...new Map(target.map(r=>{const root=rootOf(r);return [root.id,root];})).values()];
  const sampled=sample(roots.map(r=>({probe:r.probe,family:r.family,level:r.level})),catalogue,locators);
  const reproduced=clone(sampled.roots.flatMap(r=>proof.derive(u.probes.find(p=>p.id===r.probe),r,METHOD)));
  const checks=target.map(r=>({ref:ref(r),exact:encode(r)===encode(reproduced.find(x=>resultKey(ref(x))===resultKey(ref(r))))}));
  requireThat(checks.every(c=>c.exact),'replay-mismatch','Historical pixel/method replay differs');return {fromRetainedPixels:true,methodRevision:METHOD,checks,measurement:sampled.measurement};
 }
 return {initial,validate,selections,assess,recompute,replay,close:()=>server.close(),methods:[{id:'Horn-3x3-grid-slope',revision:METHOD},{id:'planar-area-ratio-from-slope',revision:METHOD}]};
 }catch(e){await server.close();throw e;}
}
export async function buildBaseline({store=STORE,dataRoot=DATA}={}) {
 const start=performance.now(),snapshot=load(store,{dataRoot});
 requireThat(!snapshot.value.understanding,'already-initialized','Baseline already published; inspect/replay existing generation');
 const m=await methods({dataRoot});let native;
 try {
  native=await openEvidence({store,generation:snapshot.generation,dataRoot});
  const built=m.initial(snapshot),value={...snapshot.value,parent:snapshot.generation,capabilities:{...snapshot.value.capabilities,queries:true,derivations:true},
   understanding:built.understanding,knowledge:clone(native.semantics.bundle)};
  m.validate(value.understanding,value.catalogue);
  return {value,locators:snapshot.locators,metrics:{buildMilliseconds:performance.now()-start,sampling:built.measurement}};
 }finally{native?.close();await m.close();}
}
export async function publishBaseline(options={}) {
 const built=await buildBaseline(options);return {...register(options.store??STORE,built.value,built.locators,{dataRoot:options.dataRoot??DATA}),buildMetrics:built.metrics};
}
export async function openUnderstanding({store=STORE,generation,dataRoot=DATA,locators}={}) {
 const start=performance.now(),snapshot=load(store,{generation,dataRoot,locators,verify:false});
 requireThat(snapshot.value.understanding,'understanding-unavailable','Registration-only generation has no retained derivation state');
 const m=await methods({dataRoot});try{m.validate(snapshot.value.understanding,snapshot.value.catalogue);}catch(e){await m.close();throw e;}
 const u=snapshot.value.understanding,selected=m.selections(u);
 function origin(r){const use=r.receipt.inputs[0];return use.kind==='resource'?u.roots.find(x=>'retained-input:'+x.id===use.id && x.revision===use.revision):origin(u.results.find(x=>resultKey(ref(x))===resultKey(use)));}
 function provenance(r){const root=origin(r),assets=root.assets.map(a=>snapshot.value.catalogue.artifacts.find(x=>x.id==='sha256:'+a.sha256));
 const uses=assets.flatMap(a=>a.uses).filter(a=>a.family===(root.family==='production-common'?'terrain-common':'terrain-regional'));
 const sources=snapshot.value.catalogue.sources.filter(s=>uses.some(u=>u.source===s.id)),products=snapshot.value.catalogue.products.filter(p=>uses.some(u=>u.product===p.id));
 return {generation:snapshot.generation,inputs:r.receipt.inputs,roots:[root],artifacts:assets,sources,products,representations:snapshot.value.catalogue.representations.filter(p=>uses.some(u=>u.representation===p.id)),rights:products.map(p=>snapshot.value.catalogue.families.find(f=>f.product===p.id).nativeMetadata.product.rights),basis:u.basis};}

 return {generation:snapshot.generation,inspect:()=>({methods:clone(m.methods),state:clone(u),dependencies:m.validate(u,snapshot.value.catalogue),selections:clone(selected),assessments:m.assess(u,snapshot.value.catalogue,snapshot.locators)}),
  assess:options=>m.assess(u,snapshot.value.catalogue,snapshot.locators,options),replay:r=>m.replay(u,snapshot.value.catalogue,snapshot.locators,r),
  recomputeFixture:options=>clone(m.recompute(u,snapshot.value.catalogue,snapshot.locators,options)),
  result:(probe,property,resultRef)=>{
   const current=m.assess(u,snapshot.value.catalogue,snapshot.locators),candidates=u.results.filter(r=>r.probe===probe && r.property===property);
   const r=resultRef?candidates.find(r=>resultKey(ref(r))===resultKey(resultRef)):candidates.find(r=>u.active.some(a=>resultKey(a)===resultKey(ref(r))));
   if(!r)return {status:'unsupported',result:{kind:'gap',reason:'unsupported',explanation:'Only frozen two-probe retained methods are available'}};
   const a=current.find(a=>resultKey(a.ref)===resultKey(ref(r))).assessment;
   return clone({status:resultRef?'historical':a.status==='fresh'?'available':a.status==='stale'?'stale':'unavailable',result:clone(r),freshness:a,
    replayAssessment:m.assess(u,snapshot.value.catalogue,snapshot.locators,{policy:'fixed-input-replay-v1'}).find(a=>resultKey(a.ref)===resultKey(ref(r))).assessment,
    provenance:provenance(r)});
  },close:()=>m.close(),metrics:{loadMilliseconds:performance.now()-start}};
}
