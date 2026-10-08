// Isolated regional composition over the unchanged component/publication core.
import fs from 'node:fs';
import {join,resolve,relative} from 'node:path';
import {spawnSync,spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {initialize} from '../component-membership/runtime.mjs';
import * as core from '../component-membership/core.mjs';
import {encode,sha,requireThat,fields} from '../../../pilots/atlas/tryfan/identity.mjs';
import {DATA,ROOT} from '../../../pilots/atlas/tryfan/catalogue.mjs';
export const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url),'utf8'));
export const H=import.meta.dirname,PYTHON=resolve(DATA,'earth-lab/.venv/Scripts/python.exe');
export function python(args){const r=spawnSync(PYTHON,[join(H,'native-worker.py'),...args],{cwd:ROOT,encoding:'utf8',maxBuffer:32*1024*1024,env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1',PROJ_NETWORK:'OFF'}});requireThat(r.status===0,'prepared-evidence-unavailable',r.stderr||'Native bridge failed');return JSON.parse(r.stdout);}
export function reference(mode){const r=spawnSync(process.execPath,[join(H,'reference.mjs'),mode],{cwd:ROOT,encoding:'utf8',maxBuffer:32*1024*1024});requireThat(r.status===0,'reference-unavailable',r.stderr);return JSON.parse(r.stdout);}
let initialized,domain,expectedRiff,checking=false,currentVerification;
export async function initializeProof(){
 if(initialized)return initialized;
 initialized=(async()=>{
  fs.mkdirSync(plan.stateRoot,{recursive:true});core.plan.stateRoot=plan.stateRoot;core.kinds.splice(0,core.kinds.length,...plan.components);
  ({G:domain}=await initialize({hooks:true}));
  expectedRiff=python(['--describe']);
  core.configure({canonicalGeneration});return {expectedRiff};
 })();return initialized;
}
function registration(v,expected){
 fields(v,Object.keys(expected));const {administrative,...content}=v,{administrative:_,...ref}=expected;
 requireThat(encode(content)===encode(ref),'registration-invalid','Region identity/support/native preparation/provenance differs');
 fields(administrative,['revision','notice']);requireThat([0,1].includes(administrative.revision)&&administrative.notice===(administrative.revision===0?'Initial retained regional registration; no new physical observation':'Administrative accountability notice revision; no evidence or physical change'),'registration-invalid','Only frozen administrative revisions');core.count('regionalRelationshipChecks');
}
function tryfanTemplate(native){return {schema:'atlas-regional-evidence-registration/v1',region:'tryfan',acceptedGeneration:plan.regions.tryfan.acceptedGeneration,support:{crs:native.core.crs,bounds:native.core.bounds},catalogueIdentity:sha(encode(native.catalogue)),knowledgeIdentity:sha(encode(native.knowledge)),understandingIdentity:sha(encode(native.understanding)),nativeFamilies:native.catalogue.families.map(f=>f.id),administrative:{revision:0,notice:'Initial retained regional registration; no new physical observation'}};}
function canonicalGeneration(value){
 const {tryfanRegistration,riffelhornRegistration,...tryfan}=value;
 const native=domain.canonicalGeneration(tryfan);requireThat(sha(encode(native))===plan.regions.tryfan.acceptedGeneration,'scientific-drift','Accepted Tryfan scientific state changed');
 registration(tryfanRegistration,tryfanTemplate(native));registration(riffelhornRegistration,expectedRiff);
 requireThat(riffelhornRegistration.preparationRevision===plan.regions.riffelhorn.preparedRevision&&riffelhornRegistration.preparedArtifacts[0].sha256===plan.regions.riffelhorn.manifestSha256,'registration-invalid','Exact prepared identity required');
 if(checking&&!currentVerification){const t=performance.now();currentVerification=python(['--verify']);currentVerification.wallMilliseconds=performance.now()-t;core.count('riffelhornFullVerifications');core.count('riffelhornInputBytesVerified',currentVerification.inputBytesVerified);}
 return {...native,tryfanRegistration,riffelhornRegistration};
}
export function owned(store){const s=resolve(store),rel=relative(resolve(plan.stateRoot),s);requireThat(rel&&!rel.startsWith('..')&&!s.toLowerCase().includes('meridian-private'),'invalid-store','Explicit isolated proof child required');return core.owned(s);}
export async function seed(store){const {expectedRiff}=await initializeProof(),s=reference('seed'),expectedTryfan=tryfanTemplate(s.value);requireThat(s.generation===plan.regions.tryfan.acceptedGeneration,'reference-drift','Accepted Tryfan changed');fs.mkdirSync(store,{recursive:true});owned(store);fs.mkdirSync(join(store,'artifacts'),{recursive:true});
 for(const a of s.value.serving.assets.filter(a=>a.origin.kind==='materialized')){const name=a.id+(a.mime==='image/png'?'.png':'.json'),body=fs.readFileSync(join(DATA,'experiments/atlas/tryfan-regional-pilot-v1/artifacts',name)),file=join(store,'artifacts',name);if(fs.existsSync(file))requireThat(fs.readFileSync(file).equals(body),'immutable-conflict','Existing portrayal differs');else fs.writeFileSync(file,body,{flag:'wx'});}
 return {value:{...s.value,tryfanRegistration:structuredClone(expectedTryfan),riffelhornRegistration:structuredClone(expectedRiff)},locators:s.locators};
}
export function prepare(store,value,locators,options){owned(store);return core.prepare(store,value,locators,options);}
export async function publish(store,id,options={}){checking=true;currentVerification=null;try{const result=await core.measured(()=>core.publish(owned(store),id,options));return {...result,preparedVerification:currentVerification};}finally{checking=false;currentVerification=null;}}
export function revise(value,region){const next=structuredClone(value);requireThat(['tryfan','riffelhorn'].includes(region),'invalid-region','Unknown region');next[region+'Registration'].administrative={revision:1,notice:'Administrative accountability notice revision; no evidence or physical change'};return next;}
export const resolveGeneration=(store,id,options)=>core.resolveGeneration(owned(store),id,options);
export const current=store=>core.root(owned(store));
export const recover=store=>core.recover(owned(store));
export const measured=core.measured;
class RiffelhornSession{
 constructor(){this.pending=[];this.closed=false;this.stderr='';this.child=spawn(PYTHON,[join(H,'native-worker.py')],{cwd:ROOT,stdio:['pipe','pipe','pipe'],env:{...process.env,PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1',PROJ_NETWORK:'OFF'}});this.ready=new Promise((resolve,reject)=>{this.resolveReady=resolve;this.rejectReady=reject;});this.child.stderr.on('data',s=>{this.stderr=(this.stderr+s).slice(-4000);});
 createInterface({input:this.child.stdout}).on('line',line=>{try{const v=JSON.parse(line);if(v.ready){this.resolveReady(v);return;}const p=this.pending.shift();if(!p)return;if(v.error)p.reject(Error(v.error.message));else p.resolve(v.value);}catch(e){this.fail(e);}});this.child.on('error',e=>this.fail(e));this.child.on('exit',code=>this.fail(Error('Read worker exited '+code+': '+this.stderr)));this.child.stdin.on('error',e=>this.fail(e));}
 fail(e){this.closed=true;this.rejectReady(e);for(const p of this.pending.splice(0))p.reject(e);}
 async query(query){await this.ready;requireThat(!this.closed,'worker-unavailable','Closed native worker');return new Promise((resolve,reject)=>{this.pending.push({resolve,reject});this.child.stdin.write(JSON.stringify({query})+'\n');});}
 close(){this.child.stdin.end();}
}
export async function pin(store,id){await initializeProof();const snapshot=resolveGeneration(store,id,{hydrate:true}),generation=snapshot.generation;
 const {openWorld}=await import('../../../pilots/atlas/tryfan/world.mjs');let world,riff;
 async function query(requests){requireThat(Array.isArray(requests)&&requests.length>0&&requests.length<=40,'invalid-request','Bounded explicit regional requests');
 // Revalidate this pin's membership/component integrity; never resolve current as query state.
 resolveGeneration(store,generation,{hydrate:true});const answers=[];
 for(const r of requests){fields(r,['region','query']);requireThat(['tryfan','riffelhorn'].includes(r.region),'invalid-region','Unknown support; no fallback');let native,metrics=null;
 if(r.region==='tryfan'){world??=await openWorld({store,generation});native=await world.query(r.query);requireThat(native.generation===generation,'mixed-generation','Tryfan escaped pin');}
 else{riff??=new RiffelhornSession();const v=await riff.query(r.query);native=v.answer;metrics=v.metrics;requireThat(native.preparedRevision===snapshot.value.riffelhornRegistration.preparationRevision,'mixed-generation','Riffelhorn preparation escaped membership');}
 answers.push({region:r.region,generation,componentIdentity:snapshot.publication.members[r.region+'Registration'],registrationIdentity:sha(encode(snapshot.value[r.region+'Registration'])),registration:snapshot.value[r.region+'Registration'].administrative,native,metrics});}
 return {schema:'atlas-multi-region-qualified-answer/v1',generation,members:snapshot.publication.members,answers};}
 return {generation,snapshot,query,close:async()=>{await world?.close();riff?.close();}};
}
export function normalizeTryfan(answer,publication){function walk(v){if(Array.isArray(v))return v.map(walk);if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,walk(x)]));return v===publication?plan.regions.tryfan.acceptedGeneration:v;}return walk(answer);}
