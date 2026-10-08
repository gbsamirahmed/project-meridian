// Isolated extension of accepted multi-region composition; original modules unchanged.
import fs from 'node:fs';import {join,relative,resolve} from 'node:path';
import * as I from '../multi-region/integration.mjs';
import * as C from '../component-membership/core.mjs';
import * as M from './model.mjs';
import {encode,sha,requireThat} from '../../../pilots/atlas/tryfan/identity.mjs';
export const extras=['tryfanDependencyState','riffelhornDependencyState','tryfanDerived','riffelhornDerived'];
let initialized,G,expectedRiff,templates,checking=false,verified;
export async function initialize(){if(initialized)return initialized;initialized=(async()=>{
 await I.initializeProof();I.plan.stateRoot=M.plan.stateRoot;await M.methods();fs.mkdirSync(M.plan.stateRoot,{recursive:true});C.plan.stateRoot=M.plan.stateRoot;C.kinds.splice(0,C.kinds.length,...I.plan.components,...extras);G=await import('../../../pilots/atlas/tryfan/generations.mjs');expectedRiff=I.python(['--describe']);C.configure({canonicalGeneration});})();return initialized;}
export function owned(s){const rel=relative(resolve(M.plan.stateRoot),resolve(s));requireThat(rel&&!rel.startsWith('..'),'invalid-store','Isolated new proof child required');return C.owned(s);}
function baseOf(value){const base={...value};for(const k of extras)delete base[k];return base;}
function contexts(value){return {tryfan:value.tryfanDependencyState,riffelhorn:value.riffelhornDependencyState};}
export function states(value){return {tryfan:value.tryfanDerived,riffelhorn:value.riffelhornDerived};}
function canonicalGeneration(value){
 const base=baseOf(value),{tryfanRegistration,riffelhornRegistration,...native}=base;const clean=G.canonicalGeneration(native);requireThat(sha(encode(clean))===I.plan.regions.tryfan.acceptedGeneration,'scientific-drift','Accepted Tryfan remains exact');
 const expectedTryfan={schema:'atlas-regional-evidence-registration/v1',region:'tryfan',acceptedGeneration:I.plan.regions.tryfan.acceptedGeneration,support:{crs:clean.core.crs,bounds:clean.core.bounds},catalogueIdentity:sha(encode(clean.catalogue)),knowledgeIdentity:sha(encode(clean.knowledge)),understandingIdentity:sha(encode(clean.understanding)),nativeFamilies:clean.catalogue.families.map(f=>f.id),administrative:{revision:0,notice:'Initial retained regional registration; no new physical observation'}};
 requireThat(encode(tryfanRegistration)===encode(expectedTryfan)&&encode(riffelhornRegistration)===encode(expectedRiff),'registration-invalid','Exact accepted regional registrations required');
 templates??=M.initialContexts(base,M.python({mode:'describe'}));
 for(const region of ['tryfan','riffelhorn']){const ctx=value[region+'DependencyState'],st=value[region+'Derived'];requireThat(ctx&&st&&encode(ctx.sources)===encode(templates[region].sources)&&encode(ctx.tasks)===encode(templates[region].tasks),'registration-invalid','Native source/task/unit/support identity changed');M.validate(ctx,st);M.validateSemantic(ctx,st);C.count('regionalResultsValidated',Object.keys(st.results).length);C.count('regionalActiveFreshnessChecks',Object.keys(st.active).length);}
 if(checking&&!verified){verified={source:I.python(['--verify'])};C.count('riffelhornFullVerifications');C.count('riffelhornInputBytesVerified',verified.source.inputBytesVerified);}
 return value;
}
export async function seed(store){await initialize();ownedAfterCreate(store);const base=await I.seed(store),description=M.python({mode:'describe'});templates=M.initialContexts(base.value,description);const value={...base.value};for(const region of ['tryfan','riffelhorn']){value[region+'DependencyState']=structuredClone(templates[region]);value[region+'Derived']=(await M.recompute(templates[region],M.empty(region),{full:true})).state;}return {...base,value};}
function ownedAfterCreate(store){fs.mkdirSync(store,{recursive:true});return owned(store);}
export const prepare=(store,value,locators,options)=>C.prepare(owned(store),value,locators,options);
export async function publish(store,id,options={}){
 await initialize();const staged=C.resolveGeneration(owned(store),id,{hydrate:true,published:false});const replay=[];
 for(const region of ['tryfan','riffelhorn']){const full=await M.recompute(staged.value[region+'DependencyState'],M.empty(region),{full:true});requireThat(encode(M.currentContent(full.state))===encode(M.currentContent(staged.value[region+'Derived'])),'replay-mismatch','Fresh full derivation differs from proposed active state');replay.push(full.measurement);}
 checking=true;verified=null;try{const out=await C.measured(()=>C.publish(owned(store),id,options));return {...out,numericalReplay:replay,verified};}finally{checking=false;verified=null;}
}
export const current=store=>C.root(owned(store));export const recover=store=>C.recover(owned(store));export const measured=C.measured;
export const resolveGeneration=(s,id,o)=>C.resolveGeneration(owned(s),id,o);
export async function pin(store,id){await initialize();const snapshot=resolveGeneration(store,id,{hydrate:true}),generation=snapshot.generation;
 return {generation,snapshot,result:(region,question,revision)=>{const fresh=resolveGeneration(store,generation,{hydrate:true}),ctx=fresh.value[region+'DependencyState'],st=fresh.value[region+'Derived'];requireThat(ctx&&st,'invalid-region','Unknown region');const rev=revision??st.active[question],result=st.results[rev];requireThat(result&&result.id===question,'result-unavailable','Exact qualified result unavailable');const a=M.assess(ctx,revision?{...st,active:{[question]:rev}}:st,{fixed:Boolean(revision)});return {generation,component:fresh.publication.members[region+'Derived'],status:revision?'historical':'fresh',result,assessment:a[rev]};},close:async()=>{}};
}
export {M,I,C,contexts};
