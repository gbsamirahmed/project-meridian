// Experiment-only instrumentation/read-context adapter. Never imported by Atlas.
import fs from 'node:fs';
import {registerHooks,syncBuiltinESMExports} from 'node:module';
import {AsyncLocalStorage} from 'node:async_hooks';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
const originalRead=fs.readFileSync,scope=new AsyncLocalStorage();
const key=Symbol.for('meridian.generation-scaling');
export const digest=b=>createHash('sha256').update(b).digest('hex');
export function install({variant,expectedHash}) {
  if(!['accepted','request-reuse'].includes(variant))throw Error('Unknown experimental variant');
  let dependencies;
  globalThis[key]={
    count(name){const c=scope.getStore();if(c)c.counters[name]=(c.counters[name]??0)+1;},
    load(dir,options){const c=scope.getStore();if(!c)throw Error('Experimental load requires explicit request scope');return experimentalLoad(c,dependencies,dir,options);},
  };
  fs.readFileSync=function(path,...args){
    const body=originalRead.call(this,path,...args),c=scope.getStore();
    if(c){const p=String(path).replaceAll('\\','/'),kind=p.includes('/generations/')?'generations':p.includes('/locators/')?'locators':p.includes('/artifacts/')?'portrayal':p.includes('meridian-data')?'external':'runtime';
      const r=c.reads[kind]??={calls:0,bytes:0,files:new Set()};r.calls++;r.bytes+=typeof body==='string'?Buffer.byteLength(body):body.length;r.files.add(p);}
    return body;
  };syncBuiltinESMExports();
  registerHooks({load(url,context,next){
    const result=next(url,context);if(!url.endsWith('/pilots/atlas/tryfan/generations.mjs'))return result;
    let source=String(result.source);if(digest(source)!==expectedHash)throw Error('Accepted loader hash differs from frozen plan');
    const counter="globalThis[Symbol.for('meridian.generation-scaling')].count";
    source=source.replace('export function validateGeneration(value) {',`export function validateGeneration(value) { ${counter}('generationValidations');`);
    if(variant==='accepted'){
      source=source.replace('const start=performance.now(), store=storePath(dir),id=generation??currentId(store);',`${counter}('loadCalls');const start=performance.now(), store=storePath(dir),id=generation??currentId(store);`);
      source=source.replace('requireThat(sha(body)===id',`${counter}('integrityChecks');requireThat(sha(body)===id`);
      source=source.replace('requireThat(!seen.has(parent)',`${counter}('referenceTraversals');requireThat(!seen.has(parent)`);
      source=source.replace('requireThat(sha(pbody)===parent',`${counter}('integrityChecks');requireThat(sha(pbody)===parent`);
    }else{
      const a=source.indexOf('export function load(dir,'),b=source.indexOf('function withWriter(',a);
      if(a<0||b<0)throw Error('Guarded experimental substitution unavailable');
      source=source.slice(0,a)+`export function load(dir,options={}) { return globalThis[Symbol.for('meridian.generation-scaling')].load(dir,options); }\n`+source.slice(b);
    }
    return {...result,source};
  }});
  return async function initialize(){
    const G=await import('../../../pilots/atlas/tryfan/generations.mjs'),I=await import('../../../pilots/atlas/tryfan/identity.mjs'),C=await import('../../../pilots/atlas/tryfan/catalogue.mjs'),D=await import('../../../pilots/atlas/tryfan/delivery-schema.mjs');
    dependencies={G,I,C,D};return dependencies;
  };
}
function experimentalLoad(c,{G,I,C,D},dir,{generation,dataRoot=C.DATA,locators,verify=true}={}) {
  const began=performance.now(),store=G.storePath(dir),id=generation??G.currentId(store);
  I.requireThat(typeof id==='string'&&/^[a-f0-9]{64}$/.test(id),'invalid-generation-id','Invalid generation address');
  c.counters.loadCalls++;
  function record(address){
    const file=join(store,'generations',address+'.json'),k=resolve(file);
    if(c.records.has(k))return c.records.get(k);
    I.requireThat(fs.existsSync(file),'generation-missing','Historical/current generation unavailable');
    const body=fs.readFileSync(file,'utf8');c.counters.integrityChecks++;
    I.requireThat(I.sha(body)===address,'generation-integrity','Immutable generation bytes changed');
    let value;try{value=JSON.parse(body);}catch{throw new I.PilotError('malformed-generation','Generation JSON invalid');}
    G.validateGeneration(value);const r={body,value,canonical:false};c.records.set(k,r);return r;
  }
  const r=record(id),closureKey=store+':'+id;
  if(!c.closed.has(closureKey)){
    const seen=new Set();let address=id;
    while(address!==null){
      I.requireThat(!seen.has(address),'invalid-reference','Generation ancestry cycle');seen.add(address);
      const node=record(address);
      if(node.value.parent!==null)c.counters.referenceTraversals++;
      address=node.value.parent;
    }
    // A failed/caught lookup must never leave an incomplete closure marked verified.
    for(const address of seen)c.closed.add(store+':'+address);
  }
  if(!r.canonical){I.requireThat(I.encode(G.canonicalGeneration(r.value))===r.body,'malformed-generation','Generation is not canonical');r.canonical=true;}
  let map=locators;
  if(!map){const file=join(store,'locators',id+'.json');if(!c.locators.has(file)){try{c.locators.set(file,I.json(file,'invalid-locator'));}catch{throw new I.PilotError('required-state-unavailable','Generation locator closure unavailable');}}map=c.locators.get(file);}
  // Preserve required materialized integrity, but perform it once per selected generation/request.
  if(r.value.serving&&!c.deliveries.has(closureKey)){D.verifyDelivery(store,r.value.serving);c.deliveries.add(closureKey);}
  const verification=verify?C.verifyArtifacts(r.value.catalogue,map,dataRoot):{status:'not-verified'};
  return {generation:id,value:r.value,locators:map,verification,metrics:{loadMilliseconds:performance.now()-began,generationBytes:Buffer.byteLength(r.body)}};
}
export async function request(callback){
  const c={reads:{},records:new Map(),closed:new Set(),locators:new Map(),deliveries:new Set(),counters:{loadCalls:0,integrityChecks:0,referenceTraversals:0,generationValidations:0}};
  const before=process.memoryUsage().rss,t=performance.now(),value=await scope.run(c,callback);
  return {value,measurement:{milliseconds:performance.now()-t,nodeRSSBefore:before,nodeRSSAfter:process.memoryUsage().rss,counters:c.counters,reads:Object.fromEntries(Object.entries(c.reads).map(([k,r])=>[k,{calls:r.calls,bytes:r.bytes,distinctFiles:r.files.size}]))}};
}
export function normalize(value,generation){
  if(value===generation)return 'PINNED_GENERATION';
  if(Array.isArray(value))return value.map(v=>normalize(v,generation));
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,k==='generation'&&v===generation?'PINNED_GENERATION':normalize(v,generation)]));
  return typeof value==='string'?value.replaceAll('/pilot/v1/g/'+generation+'/','/pilot/v1/g/PINNED_GENERATION/'):value;
}
