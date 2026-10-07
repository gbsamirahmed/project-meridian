// Tiny operational fixture driver. Never edits retained evidence.
import { readFileSync } from 'node:fs';
import { seed } from '../catalogue.mjs';
import { register, load } from '../generations.mjs';
import { encode } from '../identity.mjs';
const [mode,store,dataRoot,fixture,failAt]=process.argv.slice(2);
const state=JSON.parse(readFileSync(fixture,'utf8'));
if(mode==='write') console.log(encode(register(store,seed(state,state.parent??null),state.locators,{dataRoot,failAt})));
else if(mode==='read') console.log(encode(load(store,{dataRoot})));
else if(mode==='race') {
  const reads=[load(store,{dataRoot}).generation];
  process.stderr.write('READY\n');
  for(let i=1;i<60;i++) {await new Promise(resolve=>setTimeout(resolve,2));reads.push(load(store,{dataRoot}).generation);}
  console.log(encode(reads));
}
