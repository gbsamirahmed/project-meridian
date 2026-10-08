// Seed exact retained scientific components; change administrative identity only.
import fs from 'node:fs';import {join} from 'node:path';import {initialize} from './runtime.mjs';
import {encode,sha} from '../../../pilots/atlas/tryfan/identity.mjs';
const {G,core}=await initialize({meter:false}),base=G.load(G.STORE);fs.mkdirSync(core.plan.stateRoot,{recursive:true});
const records=[];
for(const depth of [7,28,112]){
 const store=join(core.plan.stateRoot,'history-'+depth);fs.mkdirSync(store,{recursive:true});core.owned(store);fs.mkdirSync(join(store,'artifacts'),{recursive:true});
 for(const a of base.value.serving.assets.filter(a=>a.origin.kind==='materialized')){const name=a.id+(a.mime==='image/png'?'.png':'.json'),b=fs.readFileSync(join(G.STORE,'artifacts',name)),f=join(store,'artifacts',name);if(fs.existsSync(f)){if(!fs.readFileSync(f).equals(b))throw Error('Portrayal immutable conflict');}else fs.writeFileSync(f,b,{flag:'wx'});}
 const history=[],publication=[];let previous=null;
 for(let n=1;n<=depth;n++){
  const id=core.prepare(store,base.value,base.locators,{ordinal:n,predecessor:previous});history.push(id);
  const exists=fs.existsSync(join(store,'current.json'));
  if(!exists || (n>1 && core.root(store).generation===previous)){const t=performance.now();publication.push({...core.publish(store,id),totalMilliseconds:performance.now()-t});}
  previous=id;
 }
 if(core.root(store).generation!==history.at(-1))throw Error('Unexpected retained fixture publication');
 function sizes(folder){const files=fs.readdirSync(join(store,folder));return {files:files.length,bytes:files.reduce((n,f)=>n+fs.statSync(join(store,folder,f)).size,0)};}
 const manifest=core.resolveGeneration(store,history.at(-1)).publication;
 records.push({depth,store,history,current:history.at(-1),recent:history.at(-2),oldest:history[0],members:manifest.members,publication,footprint:Object.fromEntries(['components','publications','membership','artifacts'].map(f=>[f,sizes(f)])),legacy:base.generation});
}
const file=join(core.plan.stateRoot,'fixtures.json');if(fs.existsSync(file)){const old=JSON.parse(fs.readFileSync(file,'utf8'));for(const r of records)if(!r.publication.length)r.publication=old.records.find(x=>x.depth===r.depth).publication;}
fs.writeFileSync(file,encode({schema:'atlas-component-membership-fixtures/v1',planSha256:sha(fs.readFileSync(new URL('./plan.json',import.meta.url))),records}));
console.log(encode(records.map(r=>({depth:r.depth,footprint:r.footprint}))));
