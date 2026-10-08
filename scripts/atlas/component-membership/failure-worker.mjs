// Deliberate damage only to newly owned proof fixture copies.
import fs from 'node:fs';import {join} from 'node:path';import {initialize} from './runtime.mjs';
const [store,scenario]=process.argv.slice(2),{core}=await initialize();core.owned(store);
const before=fs.readFileSync(join(store,'current.json')),g=core.root(store).generation,pub=core.resolveGeneration(store,g).publication;
try{
 if(scenario==='unpublished-complete-orphan'){const s=core.resolveGeneration(store,g,{hydrate:true}),id=core.prepare(store,s.value,s.locators,{ordinal:1000,predecessor:g});await core.measured(()=>core.resolveGeneration(store,id,{hydrate:true}));}
 else if(scenario==='unknown-generation')await core.measured(()=>core.resolveGeneration(store,'0'.repeat(64)));
 else if(scenario==='corrupt-unselected-history-detected-by-historical-read'){
  const fixture=JSON.parse(fs.readFileSync(join(core.plan.stateRoot,'fixtures.json'),'utf8')).records[0],old=fixture.oldest;
  fs.appendFileSync(join(store,'publications',old+'.json'),' ');await core.measured(()=>core.resolveGeneration(store,g,{hydrate:true}));
  await core.measured(()=>core.resolveGeneration(store,old,{hydrate:true}));
 }else if(scenario==='corrupt-membership-node'){
  fs.appendFileSync(join(store,'membership',core.root(store).membership+'.json'),' ');await core.measured(()=>core.resolveGeneration(store,g));
 }else{
  const file=join(store,'components',pub.members.understanding+'.json');
  if(scenario==='between-request-mutation')await core.measured(()=>core.resolveGeneration(store,g,{hydrate:true}));
  if(scenario==='missing-selected-component')fs.unlinkSync(file);else fs.appendFileSync(file,' ');
  await core.measured(()=>core.resolveGeneration(store,g,{hydrate:true}));
 }
 throw Error('Required failure undetected');
}catch(e){if(!e.code)throw e;console.log(JSON.stringify({scenario,code:e.code,rootUnchanged:fs.readFileSync(join(store,'current.json')).equals(before)}));}
