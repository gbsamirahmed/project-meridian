// Isolated proof storage. This module is never imported by pilot or production code.
import fs from 'node:fs';
import {join,resolve,relative} from 'node:path';
import {randomUUID} from 'node:crypto';
import {AsyncLocalStorage} from 'node:async_hooks';
import {encode,sha,fields,requireThat,json} from '../../../pilots/atlas/tryfan/identity.mjs';
import {verifyArtifacts,DATA} from '../../../pilots/atlas/tryfan/catalogue.mjs';
import {verifyDelivery} from '../../../pilots/atlas/tryfan/delivery-schema.mjs';
import {validateTransition} from '../../../pilots/atlas/tryfan/update-schema.mjs';
export const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url),'utf8'));
export const scope=new AsyncLocalStorage();
export const kinds=plan.components;
const HEX=/^[a-f0-9]{64}$/;
let domain;
export function configure(value){domain=value;}
export function owned(dir){
 const root=fs.realpathSync(plan.stateRoot),path=fs.existsSync(dir)?fs.realpathSync(dir):resolve(dir),r=relative(root,path);
 requireThat(r && !r.startsWith('..') && !resolve(path).toLowerCase().includes('meridian-private'),'invalid-store','Proof state must be inside its isolated root');return path;
}
export function count(key,n=1){const s=scope.getStore();if(s)s.counters[key]=(s.counters[key]??0)+n;}
function address(id){requireThat(typeof id==='string'&&HEX.test(id),'invalid-generation-id','Expected SHA256 identity');}
function readObject(dir,kind,id){
 address(id);const file=join(owned(dir),kind,id+'.json'),s=scope.getStore();if(s?.cache.has(file))return s.cache.get(file);
 requireThat(fs.existsSync(file),kind==='components'?'component-unavailable':'membership-unavailable','Required immutable proof record unavailable');
 const body=fs.readFileSync(file,'utf8');count('integrityChecks');requireThat(sha(body)===id,'metadata-integrity','Immutable proof bytes changed');
 let v;try{v=JSON.parse(body);}catch{requireThat(false,'malformed-state','Invalid immutable JSON');}
 requireThat(encode(v)===body,'malformed-state','Non-canonical immutable record');s?.cache.set(file,v);return v;
}
export function root(dir){
 const file=join(owned(dir),'current.json');requireThat(fs.existsSync(file),'store-absent','No proof publication');
 const value=json(file,'invalid-published-root');fields(value,['schema','generation','membership']);
 requireThat(value.schema==='atlas-component-root/v1','invalid-published-root','Unknown proof root');address(value.generation);address(value.membership);return value;
}
export function membership(dir,registry,id){
 address(id);let next=registry;
 for(let depth=0;depth<=32;depth++){
  const node=readObject(dir,'membership',next);count('membershipVisits');
  requireThat(node.schema==='atlas-publication-membership/v1'&&node.depth===depth,'membership-integrity','Invalid bounded membership level');
  if(depth===32){fields(node,['schema','depth','generation']);requireThat(node.generation===id,'generation-unpublished','Not a committed publication');return true;}
  fields(node,['schema','depth','children']);requireThat(node.children && !Array.isArray(node.children) && Object.keys(node.children).every(k=>/^[a-f0-9]{2}$/.test(k)) && Object.values(node.children).every(x=>HEX.test(x)),'membership-integrity','Invalid direct keyed membership');
  next=node.children[id.slice(depth*2,depth*2+2)];requireThat(next,'generation-unpublished','Unknown or pre-switch publication');count('membershipEdges');
 }
}
function publication(dir,id){
 const p=readObject(dir,'publications',id);fields(p,['schema','ordinal','predecessor','legacyGeneration','header','members']);
 requireThat(p.schema==='atlas-component-publication/v1' && Number.isSafeInteger(p.ordinal)&&p.ordinal>=1,'malformed-publication','Unknown publication schema');
 requireThat(p.predecessor===null||HEX.test(p.predecessor),'invalid-reference','Invalid lineage reference');address(p.legacyGeneration);
 requireThat(Object.keys(p.members).sort().join(',')===[...kinds].sort().join(',') && Object.values(p.members).every(v=>HEX.test(v)),'invalid-reference','Exact explicit membership required');
 return p;
}
export function resolveGeneration(dir,id,{hydrate=false,published=true}={}){
 const store=owned(dir),pointer=published?root(store):null,g=id??pointer?.generation;address(g);
 if(published)membership(store,pointer.membership,g);
 const p=publication(store,g);if(!hydrate)return {generation:g,publication:p};
 const s=scope.getStore(),key=store+':'+g;if(s?.hydrated.has(key))return s.hydrated.get(key);
 const values={};for(const kind of kinds){count('componentEdges');const c=readObject(store,'components',p.members[kind]);fields(c,['schema','kind','value']);requireThat(c.schema==='atlas-retained-component/v1'&&c.kind===kind,'component-integrity','Wrong component kind');values[kind]=c.value;}
 const {locators,...science}=values,value={...p.header,...science};
 count('generationValidations');const body=encode(domain.canonicalGeneration(value));requireThat(sha(body)===p.legacyGeneration,'scientific-drift','Exact legacy reconstruction differs');
 const snapshot={generation:g,value,locators,legacyGeneration:p.legacyGeneration,publication:p};s?.hydrated.set(key,snapshot);return snapshot;
}
// S1-compatible load result for the existing S2/S3/S4 read interfaces.
export function load(dir,{generation,dataRoot=DATA,locators,verify=true}={}){
 const t=performance.now(),snapshot=resolveGeneration(dir,generation,{hydrate:true}),s=scope.getStore(),key=owned(dir)+':'+snapshot.generation;
 if(!s?.portrayals.has(key)){verifyDelivery(dir,snapshot.value.serving);s?.portrayals.add(key);}
 const map=locators??snapshot.locators,verification=verify?verifyArtifacts(snapshot.value.catalogue,map,dataRoot):{status:'not-verified'};
 return {...snapshot,locators:map,verification,metrics:{loadMilliseconds:performance.now()-t,generationBytes:Buffer.byteLength(encode(snapshot.publication))}};
}
function durable(file,body){const fd=fs.openSync(file,'wx');try{fs.writeFileSync(fd,body);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
function immutable(dir,kind,value){const store=owned(dir),body=encode(value),id=sha(body),folder=join(store,kind);fs.mkdirSync(folder,{recursive:true});const file=join(folder,id+'.json');
 if(fs.existsSync(file))requireThat(fs.readFileSync(file,'utf8')===body,'immutable-conflict','Existing immutable object differs');else durable(file,body);return id;}
function insert(dir,previous,id,depth=0){
 if(depth===32)return immutable(dir,'membership',{schema:'atlas-publication-membership/v1',depth,generation:id});
 const children=previous?structuredClone(readObject(dir,'membership',previous).children):{},key=id.slice(depth*2,depth*2+2);
 children[key]=insert(dir,children[key],id,depth+1);return immutable(dir,'membership',{schema:'atlas-publication-membership/v1',depth,children});
}
export function prepare(dir,value,locators,{ordinal,predecessor=null}={}){
 const store=owned(dir),body=encode(domain.canonicalGeneration(value)),members={};
 for(const kind of kinds)members[kind]=immutable(store,'components',{schema:'atlas-retained-component/v1',kind,value:kind==='locators'?locators:value[kind]});
 const header=structuredClone(value);for(const kind of kinds)delete header[kind];
 return immutable(store,'publications',{schema:'atlas-component-publication/v1',ordinal,predecessor,legacyGeneration:sha(body),header,members});
}
export function publish(dir,id,{failAt,dataRoot=DATA}={}){
 const store=owned(dir);fs.mkdirSync(store,{recursive:true});const lock=join(store,'writer.lock'),operation=randomUUID();
 try{durable(lock,encode({pid:process.pid,operation}));}catch(e){requireThat(e.code!=='EEXIST','writer-locked','Single proof writer owns root');throw e;}
 try{
  const prior=fs.existsSync(join(store,'current.json'))?root(store):null,snapshot=resolveGeneration(store,id,{hydrate:true,published:false});
  requireThat(snapshot.publication.predecessor===(prior?.generation??null),'publication-conflict','Candidate predecessor is not current');
  if(prior)validateTransition(snapshot.value,resolveGeneration(store,prior.generation,{hydrate:true}).value);
  const start=performance.now();verifyArtifacts(snapshot.value.catalogue,snapshot.locators,dataRoot);verifyDelivery(store,snapshot.value.serving);
  const validationMilliseconds=performance.now()-start;
  if(failAt==='after-components')process.exit(91);
  const membershipRoot=insert(store,prior?.membership,id);
  if(failAt==='before-switch')process.exit(91);
  const began=performance.now(),temp=join(store,'current-'+operation+'.pending');durable(temp,encode({schema:'atlas-component-root/v1',generation:id,membership:membershipRoot}));fs.renameSync(temp,join(store,'current.json'));
  return {generation:id,validationMilliseconds,switchMilliseconds:performance.now()-began};
 }finally{fs.unlinkSync(lock);}
}
export function recover(dir){const file=join(owned(dir),'writer.lock'),v=json(file);let dead=false;try{process.kill(v.pid,0);}catch(e){dead=e.code==='ESRCH';}requireThat(dead,'writer-alive-or-unknown','Only demonstrably dead lock owner can be recovered');fs.unlinkSync(file);return v.operation;}
export async function measured(callback){const s={cache:new Map(),hydrated:new Map(),portrayals:new Set(),reads:{},counters:{ancestryTraversals:0,integrityChecks:0,membershipVisits:0,membershipEdges:0,componentEdges:0,generationValidations:0}},before=process.memoryUsage().rss,t=performance.now();const value=await scope.run(s,callback);
 return {value,measurement:{milliseconds:performance.now()-t,RSSBefore:before,RSSAfter:process.memoryUsage().rss,reads:s.reads,counters:s.counters}};}
