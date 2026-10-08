import fs from 'node:fs';import {join,resolve} from 'node:path';import {performance} from 'node:perf_hooks';
import {install,measure,sweep,plan} from './meter.mjs';
const [action,mode,arg]=process.argv.slice(2),instrument=mode==='meter';if(instrument)install();
const I=await import('../../../pilots/atlas/tryfan/identity.mjs'),C=await import('../../../pilots/atlas/tryfan/catalogue.mjs'),G=await import('../../../pilots/atlas/tryfan/generations.mjs'),D=await import('../../../pilots/atlas/tryfan/delivery-schema.mjs');
const base=G.STORE,baseline=JSON.parse(fs.readFileSync(new URL('../../../docs/research/atlas-integrity-cost-baseline.json',import.meta.url),'utf8')),body=JSON.parse(fs.readFileSync(join(base,'generations',baseline.current+'.json'),'utf8')),locators=JSON.parse(fs.readFileSync(join(base,'locators',baseline.current+'.json'),'utf8'));
const out=[];let core,fixtures;
if(action==='history'){({core}=await (await import('../component-membership/runtime.mjs')).initialize({meter:false}));fixtures=JSON.parse(fs.readFileSync(join(core.plan.stateRoot,'fixtures.json'),'utf8'));}
for(let repeat=0;repeat<(process.env.COST_REPS?Number(process.env.COST_REPS):plan.repetitions);repeat++){
 let fn;if(action==='pilot-artifacts')fn=()=>C.verifyArtifacts(body.catalogue,locators,C.DATA);
 else if(action==='pilot-structure')fn=()=>{G.validateGeneration(body);return {generation:I.sha(I.encode(G.canonicalGeneration(body)))};};
 else if(action==='pilot-delivery')fn=()=>{D.verifyDelivery(base,body.serving);return {assets:2};};
 else if(action==='pilot-load')fn=()=>{const v=G.load(base);return {generation:v.generation,verification:v.verification};};
 else if(action==='pilot-register'){
  const dest=resolve(plan.stateRoot,'campaign','register-'+mode+'-'+repeat);if(!dest.startsWith(resolve(plan.stateRoot)+'\\') && !dest.startsWith(resolve(plan.stateRoot)+'/'))throw Error('Isolated path');if(fs.existsSync(dest))throw Error('Existing fixture');fs.mkdirSync(dest,{recursive:true});for(const p of Object.keys(baseline.acceptedStoreHashes)){const target=join(dest,p);fs.mkdirSync(resolve(target,'..'),{recursive:true});fs.copyFileSync(join(base,p),target);}
  const next=structuredClone(body);next.parent=baseline.current;fn=()=>{const v=G.register(dest,next,locators);return {generation:v.generation,verification:v.verification,root:G.currentId(dest)};};
 }else if(action==='payload'){
  const f=JSON.parse(fs.readFileSync(arg,'utf8'));fn=()=>sweep(f.items,f.root,I.sha,I.safePath);
 }else if(action==='history'){
  const c=JSON.parse(arg),f=fixtures.records.find(x=>x.depth===c.depth),id=f[c.selection];fn=()=>{const s=core.load(f.store,{generation:id});return {generation:id,legacy:s.legacyGeneration,verification:s.verification};};
 }else throw Error('Unknown measurement');
 const t=performance.now(),v=instrument?measure(fn):{value:fn()};if(!instrument){v.milliseconds=performance.now()-t;v.RSS=process.memoryUsage().rss;}out.push(v);
}
console.log(JSON.stringify({action,mode,samples:out}));
