import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync,rmSync,readFileSync,copyFileSync,mkdirSync,writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join,resolve,sep } from 'node:path';
import { spawnSync } from 'node:child_process';
import { buildRetained,seed,ROOT,DATA } from '../catalogue.mjs';
import { register,load,currentId,generationId,STORE } from '../generations.mjs';
import { methods,buildBaseline,openUnderstanding } from '../derivations.mjs';
import { openWorld } from '../world.mjs';
import { METHOD,ref,resultKey,validateDependencies } from '../dependencies.mjs';
import { encode,sha } from '../identity.mjs';
let dir,store,registration,snapshot,m,initial,generation,regional,d,w;
const summit=[266405,359387];
const err=code=>e=>e.code===code;
before(async()=>{
 dir=mkdtempSync(join(tmpdir(),'meridian-s3-'));store=join(dir,'store');registration=await buildRetained();register(store,seed(registration),registration.locators);
 const built=await buildBaseline({store});initial=built.value;generation=register(store,initial,built.locators).generation;snapshot=load(store);
 m=await methods();regional=m.recompute(initial.understanding,registration.catalogue,registration.locators);d=await openUnderstanding({store});w=await openWorld({store});
});
after(async()=>{w&&await w.close();d&&await d.close();m&&await m.close();assert.ok(resolve(dir).startsWith(resolve(tmpdir())+sep));rmSync(dir,{recursive:true,force:true});});
const u=()=>initial.understanding;
const statuses=(options={})=>m.assess(u(),registration.catalogue,registration.locators,options);
const change=(inside=true)=>{const r=u().results.find(r=>r.probe==='summit'&&r.property==='slope'),a=r.receipt.inputs[0].spatial.bounds;
 return {inputId:r.receipt.inputs[0].id,scopeKnown:true,bounds:inside?[a[0],a[1],a[0]+.01,a[1]+.01]:[a[2]+20,a[3]+20,a[2]+21,a[3]+21],description:'Synthetic scope notification only; no retained bytes changed'};};
test('L01 frozen two methods and four exact scientific claim records',()=>{
 assert.equal(u().results.length,4);assert.equal(u().roots.length,2);assert.ok(u().results.every(r=>r.receipt.methodRevision===METHOD));assert.equal(m.validate(u(),registration.catalogue).edges,4);
 assert.deepEqual(u().results.map(r=>r.claim.result.value.value),[11.837956999552308,1.0217304696061646,8.811499729681492,1.011943302930815]);
});
test('L02 repeated fresh sampler construction and shuffled catalogue preserve identity',()=>{
 const other=m.initial(snapshot).understanding;assert.deepEqual(other,u());const reversed=structuredClone(initial);reversed.catalogue.artifacts.reverse();assert.equal(generationId(reversed),generation);
});
test('explicit methods, scopes, graph and source asset linkage survive metadata loading',()=>{
 const inspection=d.inspect();assert.equal(inspection.methods.length,2);assert.equal(inspection.dependencies.edges,4);assert.equal(Object.keys(inspection.dependencies.reverse).length,4);
 assert.deepEqual(u().roots.map(r=>r.actualUse.usedPixelCount),[22,20]);
 assert.ok(u().results[0].receipt.inputs[0].spatial.bounds[0]<summit[0]-8);assert.equal(u().results[1].receipt.inputs[0].kind,'claim');
});
test('L04 unchanged generation is fresh without reading a stored fresh flag',()=>{assert.ok(statuses().every(r=>r.assessment.status==='fresh'));assert.equal(u().freshness,undefined);});
test('L05 unrelated NRW evidence-family notification leaves all fresh',()=>{assert.ok(statuses({changes:[{inputId:'nrw-phase1',scopeKnown:true,bounds:[264900,357800,267900,360800],description:'Administrative inventory applicability only'}]}).every(r=>r.assessment.status==='fresh'));});
test('L06 nonintersecting actual-use change leaves all fresh',()=>{assert.ok(statuses({changes:[change(false)]}).every(r=>r.assessment.status==='fresh'));});
test('L07 relevant interpolation halo, L08 unaffected southern, L09 transitive ratio',()=>{
 const a=statuses({changes:[change()]});assert.deepEqual(a.filter(r=>r.probe==='summit').map(r=>r.assessment.status),['stale','stale']);assert.ok(a.filter(r=>r.probe!=='summit').every(r=>r.assessment.status==='fresh'));assert.ok(a[1].assessment.reason.includes('Transitive'));
});
test('unknown change scope is indeterminate, not blanket fresh or false',()=>{assert.deepEqual(statuses({changes:[{...change(),scopeKnown:false}]}).map(r=>r.assessment.status),['indeterminate','indeterminate','fresh','fresh']);});
test('L10 selective real retained Welsh resampling, L11 southern reuse',()=>{
 assert.equal(regional.considered,4);assert.equal(regional.recomputed.length,2);assert.equal(regional.reused.length,2);assert.ok(regional.reused.every(r=>u().results.find(a=>resultKey(ref(a))===resultKey(r)).probe==='southern-observer'));
 assert.deepEqual(regional.understanding.results.slice(0,4),u().results);const root=regional.understanding.roots.find(r=>r.family==='welsh-regional');assert.equal(regional.measurement.uniqueTileBytes,root.assets.reduce((n,a)=>n+a.bytes,0));
});
test('L12 historical retention six revisions, four current in isolated context only',()=>{assert.equal(regional.understanding.results.length,6);assert.equal(regional.understanding.active.length,4);assert.equal(currentId(store),generation);assert.equal(load(store).value.understanding.stage,'common');});
test('L13 actual pixel historical/current replay exactly reproduces all six',()=>{const r=m.replay(regional.understanding,registration.catalogue,registration.locators);assert.equal(r.checks.length,6);assert.ok(r.checks.every(r=>r.exact));assert.equal(r.fromRetainedPixels,true);});
test('L14 method-relative stale differs from original fixed replay validity',()=>{assert.ok(statuses({methodRevision:'prospective-policy-revision-not-implemented'}).every(r=>r.assessment.status==='stale'));assert.ok(statuses({policy:'fixed-input-replay-v1',methodRevision:'prospective-policy-revision-not-implemented'}).every(r=>r.assessment.status==='fresh'));});
test('L15 unavailable exact registered input never produces false freshness',()=>{
 const locators={...registration.locators};locators['sha256:'+u().roots[0].assets[0].sha256]='missing-operational-fixture';
 assert.deepEqual(m.assess(u(),registration.catalogue,locators).map(r=>r.assessment.status),['indeterminate','indeterminate','fresh','fresh']);assert.throws(()=>m.replay(u(),registration.catalogue,locators),err('artifact-unavailable'));
});
test('missing dependency, invalid scope, unknown method and corrupt result fail visibly',()=>{
 for(const [modify,code] of [[a=>a.results[1].receipt.inputs[0].revision='missing','receipt-integrity'],[a=>a.results[0].receipt.inputs[0].spatial.bounds=[1,2,3,4],'receipt-integrity'],[a=>a.results[0].receipt.methodRevision='new','unsupported-method-revision'],[a=>a.results[0].claim.result.value.value=99,'result-integrity']]){const a=structuredClone(u());modify(a);assert.throws(()=>validateDependencies(a,registration.catalogue),err(code));}
 const a=structuredClone(u());a.active[0].revision='missing';assert.throws(()=>m.validate(a,registration.catalogue),err('invalid-active'));
});
test('S1 seed remains loadable; G0 knowledge closure, hierarchy and capabilities required',()=>{
 const old=load(store,{generation:initial.parent});assert.equal(old.value.understanding,undefined);assert.equal(snapshot.value.knowledge.collections[1].claims.length,193);
 const bad=structuredClone(initial);bad.knowledge.collections[1].claims.pop();assert.throws(()=>generationId(bad),err('required-state-unavailable'));
 const invalid=structuredClone(initial);invalid.understanding.terrain.hierarchy.id='changed';assert.throws(()=>generationId(invalid),err('invalid-hierarchy'));
});
test('S3 cannot publish regional-update candidate, no hidden later slice',()=>{const candidate={...initial,parent:generation,understanding:regional.understanding};assert.throws(()=>register(store,candidate,registration.locators),err('unsupported-capability'));assert.equal(currentId(store),generation);});
test('new generation context alone does not stale exact existing result',()=>{
 const candidate={...initial,parent:generation};const next=register(store,candidate,registration.locators);assert.notEqual(next.generation,generation);assert.ok(m.assess(load(store).value.understanding,registration.catalogue,registration.locators).every(r=>r.assessment.status==='fresh'));
 assert.deepEqual(load(store,{generation}).value.understanding,u());assert.equal(w.generation,generation);
});
test('Q01-Q04 source selection and qualified derived chain pinned to same G0',async()=>{
 for(const property of ['terrain-selection','derived-slope','derived-area-ratio']){const r=await w.query({property,place:{crs:'EPSG:27700',point:summit}});assert.equal(r.generation,generation);assert.equal(r.answers.length,1);}
 const r=await w.query({property:'derived-slope',place:{crs:'EPSG:27700',point:u().probes[1].centre}});assert.equal(r.answers[0].result.claim.result.value.value,8.811499729681492);
});
test('Q12 explicit historical query, exact sampler replay, missing ref rejection',async()=>{
 const r=await w.query({property:'historical-derived',place:{crs:'EPSG:27700',point:summit},resultRef:ref(u().results[0]),policy:'fixed-input-replay-v1'});assert.equal(r.answers[0].status,'historical');assert.equal(r.answers[0].freshness.status,'fresh');assert.equal(w.replay(ref(u().results[0])).checks.length,1);
 await assert.rejects(w.query({property:'historical-derived',place:{crs:'EPSG:27700',point:summit},resultRef:{id:'missing',revision:'missing'}}),err('historical-result-missing'));
});
test('Q21 six separate answers preserve native temporal/support/meaning contexts',async()=>{
 const r=await w.query({property:'place-evidence',place:{crs:'EPSG:27700',point:summit}});assert.equal(r.answers.length,6);assert.ok(r.answers.every(a=>a.response.generation===generation));assert.equal(r.value,undefined);
 const wc=r.answers[3].response.answers[0].records[0],nrw=r.answers[4].response.answers[0].records[0];assert.equal(wc.claim.native.fields.code,30);assert.equal(nrw.claim.native.fields.phase1_code,'D.1.1');assert.notDeepEqual(wc.context.time,nrw.context.time);
 assert.equal(r.answers[5].response.answers[0].records[0].claim,undefined);
});
test('unsupported locations/properties, incompatible families and invalid requests',async()=>{
 const place={crs:'EPSG:27700',point:[266400,360450]};assert.equal((await w.query({property:'derived-slope',place})).result.reason,'unsupported');
 const unsupported=await w.query({property:'geology',place});assert.equal(unsupported.result.reason,'unsupported');
 assert.equal((await w.query({property:'derived-slope',place:{crs:'EPSG:27700',point:summit},evidence:'nrw'})).status,'excluded-by-context');
 await assert.rejects(w.query({property:'derived-slope',place:{crs:'EPSG:4326',point:summit}}),err('invalid-crs'));
 await assert.rejects(w.query({property:'derived-slope',place:{crs:'EPSG:27700',point:summit},policy:'best-truth'}),err('invalid-policy'));
});
test('L03 fresh subprocess inspection, L13 replay, fresh integrated coordinator reproduce',async()=>{
 const base=[join(ROOT,'pilots/atlas/tryfan/lifecycle-cli.mjs')],options=['--store',store,'--generation',generation];
 const run=command=>{const p=spawnSync(process.execPath,[...base,command,...options],{encoding:'utf8',timeout:30000});assert.equal(p.status,0,p.stderr);return JSON.parse(p.stdout);};
 assert.deepEqual(run('inspect').state,u());assert.ok(run('replay').checks.every(c=>c.exact));
 const request={property:'place-evidence',place:{crs:'EPSG:27700',point:summit}};
 const p=spawnSync(process.execPath,[...base,'query',...options,'--request',JSON.stringify(request)],{encoding:'utf8',timeout:30000});assert.equal(p.status,0,p.stderr);assert.deepEqual(JSON.parse(p.stdout),await w.query(request));
});
test('source hashes remain unchanged, actual published pilot not modified by tests',()=>{assert.deepEqual(load(store).verification,{artifacts:310,bytes:42473107});assert.equal(load(STORE).value.understanding?.stage??'common','common');});

test('read-only locator bridge replay survives physical relocation without changing aliases/IDs',()=>{
 const base=join(DATA,'experiments/atlas/tryfan-regional-pilot-v1/staging');mkdirSync(base,{recursive:true});
 const folder=mkdtempSync(join(base,'s3-locator-test-'));const asset=u().roots[0].assets[0],id='sha256:'+asset.sha256,locators={...registration.locators};
 try{copyFileSync(join(DATA,locators[id]),join(folder,'moved.png'));locators[id]=join(folder,'moved.png').slice(DATA.length+1).replaceAll('\\','/');
  const replay=m.replay(u(),registration.catalogue,locators);assert.ok(replay.checks.every(c=>c.exact));assert.deepEqual(m.assess(u(),registration.catalogue,locators).map(a=>a.assessment.status),['fresh','fresh','fresh','fresh']);
 }finally{assert.ok(resolve(folder).startsWith(resolve(base)+sep)&&folder.includes('s3-locator-test-'));rmSync(folder,{recursive:true,force:true});}
});
test('public result/inspection objects cannot mutate persistent in-memory scientific state',()=>{
 const a=d.result('summit','slope');a.provenance.inputs[0].spatial.bounds[0]=0;a.provenance.basis.methodRevision='mutated';const b=d.inspect();b.methods[0].revision='mutated';
 assert.equal(d.result('summit','slope').result.receipt.methodRevision,METHOD);assert.equal(d.inspect().methods[0].revision,METHOD);
});
test('invalid notifications rejected instead of producing false freshness',()=>{
 assert.throws(()=>statuses({changes:[{...change(),bounds:[NaN,0,1,2]}]}),err('invalid-change-scope'));
 assert.throws(()=>statuses({changes:[{...change(),bounds:[4,3,2,1]}]}),err('invalid-change-scope'));
});

test('exact inherited CRS84 probe identifies original physical question; no nearest-point inference',async()=>{
 const a=await w.query({property:'derived-slope',place:{crs:'OGC:CRS84',point:u().probes[0].longitudeLatitude}});assert.equal(a.answers[0].result.claim.id,u().results[0].claim.id);
 const b=await w.query({property:'worldcover-native',place:{crs:'EPSG:27700',point:summit},evidence:'terrain'});assert.equal(b.status,'excluded-by-context');
});
test('unavailable unused terrain tile does not block exact-input replay',()=>{
 const locators={...registration.locators};const used=new Set(u().roots.flatMap(r=>r.assets.map(a=>'sha256:'+a.sha256)));const unused=registration.catalogue.artifacts.find(a=>a.uses.some(x=>x.family==='terrain-regional'&&x.tile)&&!used.has(a.id));
 assert.ok(unused);locators[unused.id]='missing-unused-operational-fixture';assert.ok(m.replay(u(),registration.catalogue,locators).checks.every(c=>c.exact));
});

test('selectively recomputed fixture and historical results persist/replay in a fresh process without publishing',()=>{
 const file=join(dir,'isolated-regional-context.json');writeFileSync(file,encode({generation,understanding:regional.understanding}));
 const p=spawnSync(process.execPath,[join(ROOT,'pilots/atlas/tryfan/tests/lifecycle-worker.mjs'),store,file],{encoding:'utf8',timeout:30000});assert.equal(p.status,0,p.stderr);const result=JSON.parse(p.stdout);
 assert.equal(result.notPublished,true);assert.deepEqual(result.results,regional.understanding.results);assert.equal(result.graph.edges,6);assert.ok(result.checks.every(c=>c.exact));assert.equal(result.assessments.filter(a=>a.assessment.status==='fresh').length,4);
 assert.deepEqual(load(store,{generation}).value.understanding.results,u().results);
});
