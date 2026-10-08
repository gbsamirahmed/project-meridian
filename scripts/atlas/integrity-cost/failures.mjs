// Only labelled payload fixtures inside the assessment root are ever changed.
import fs from 'node:fs';import {join,resolve,dirname} from 'node:path';import {spawnSync} from 'node:child_process';import assert from 'node:assert/strict';
import {plan} from './meter.mjs';import * as G from '../../../pilots/atlas/tryfan/generations.mjs';import * as C from '../../../pilots/atlas/tryfan/catalogue.mjs';import {sha,encode} from '../../../pilots/atlas/tryfan/identity.mjs';
if(process.argv[2]==='interrupt'){const [store,root,file]=process.argv.slice(3),v=JSON.parse(fs.readFileSync(file));G.register(store,v.value,v.locators,{dataRoot:root,failAt:'before-switch'});throw Error('Expected abrupt exit');}
const base=JSON.parse(fs.readFileSync(join(G.STORE,'generations',G.currentId(G.STORE)+'.json'),'utf8')),out=[];
for(const kind of ['missing-payload','same-size-corruption','wrong-size','wrong-hash','malformed-metadata','invalid-reference','invalid-closure','historical-payload-unavailable','pre-switch-interruption']){
 const dir=resolve(plan.stateRoot,'campaign','failure-'+kind);assert.ok(dir.startsWith(resolve(plan.stateRoot)));assert.ok(!fs.existsSync(dir));const root=join(dir,'data'),store=join(dir,'store');fs.mkdirSync(root,{recursive:true});const b=Buffer.from('Assessment fixture; not an observation.\n'),file=join(root,'fixture.bin');fs.writeFileSync(file,b);const artifact={...structuredClone(base.catalogue.artifacts.find(a=>a.uses.some(u=>u.family==='terrain-common'))),id:'sha256:'+sha(b),sha256:sha(b),bytes:b.length,aliases:['meridian-data://labelled-integrity-fixture']};
 const c={...structuredClone(base.catalogue),artifacts:[artifact]},locators={[artifact.id]:'fixture.bin'},value=C.seed({core:base.core,catalogue:c,locators}),initial=G.register(store,value,locators,{dataRoot:root}),before=fs.readFileSync(join(store,'current.json'));let q=structuredClone(value);q.parent=initial.generation;let code=null,exit=null;
 if(kind==='missing-payload'||kind==='historical-payload-unavailable')fs.unlinkSync(file);
 if(kind==='same-size-corruption')fs.writeFileSync(file,Buffer.alloc(b.length,33));
 if(kind==='wrong-size')fs.writeFileSync(file,Buffer.concat([b,b]));
 if(kind==='wrong-hash'){q.catalogue.artifacts[0].sha256='0'.repeat(64);q.catalogue.artifacts[0].id='sha256:'+'0'.repeat(64);locators[q.catalogue.artifacts[0].id]='fixture.bin';}
 if(kind==='invalid-reference')q.catalogue.artifacts[0].uses[0].product={id:'missing',revision:'missing'};
 if(kind==='invalid-closure')q.capabilities.serving=true;
 try{
  if(kind==='malformed-metadata'){fs.writeFileSync(join(store,'generations',initial.generation+'.json'),'{malformed');G.load(store,{dataRoot:root});}
  else if(kind==='historical-payload-unavailable')G.load(store,{generation:initial.generation,dataRoot:root});
  else if(kind==='pre-switch-interruption'){const f=join(dir,'candidate.json');fs.writeFileSync(f,encode({value:q,locators}));const p=spawnSync(process.execPath,[resolve(import.meta.dirname,'failures.mjs'),'interrupt',store,root,f],{encoding:'utf8'});exit=p.status;assert.equal(exit,91,p.stderr);code='interrupted-before-switch';}
  else G.register(store,q,locators,{dataRoot:root});
  if(!code)throw Error('Missed rejection '+kind);
 }catch(e){if(!e.code)throw e;code=e.code;}
 assert.ok(fs.readFileSync(join(store,'current.json')).equals(before));out.push({kind,code,exit,rootPreserved:true,historicalAvailabilityIsPrecondition:kind==='historical-payload-unavailable'});
}
console.log(JSON.stringify(out));
