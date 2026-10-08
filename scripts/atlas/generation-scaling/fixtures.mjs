// Administrative history only. Exact accepted source/knowledge/results stay unchanged.
import fs from 'node:fs';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {STORE,load,register} from '../../../pilots/atlas/tryfan/generations.mjs';
import {encode,sha} from '../../../pilots/atlas/tryfan/identity.mjs';
const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url))),root=resolve(plan.stateRoot);
export function build(){
 fs.mkdirSync(root,{recursive:true});const original=load(STORE),baseline=JSON.parse(fs.readFileSync(new URL('../../../docs/research/tryfan-pilot-s6-baseline.json',import.meta.url)));
 if(original.generation!==baseline.current)throw Error('Accepted current differs from frozen checkpoint');
 const cases=[];
 for(const depth of plan.historyDepths){
  const store=join(root,'history-'+depth);fs.mkdirSync(store,{recursive:true});
  for(const folder of ['generations','locators','artifacts']){
   fs.mkdirSync(join(store,folder),{recursive:true});
   const files=folder==='artifacts'?fs.readdirSync(join(STORE,folder)):baseline.history.map(g=>g.generation+'.json');
   for(const f of files){const dest=join(store,folder,f),body=fs.readFileSync(join(STORE,folder,f));if(fs.existsSync(dest)){if(!fs.readFileSync(dest).equals(body))throw Error('Fixture existing immutable conflict');}else fs.writeFileSync(dest,body,{flag:'wx'});}
  }
  const pointer=join(store,'current.json');if(!fs.existsSync(pointer))fs.writeFileSync(pointer,fs.readFileSync(join(STORE,'current.json')),{flag:'wx'});
  let snapshot=load(store),history=[];let parent=snapshot.generation;
  while(parent){history.push(parent);parent=JSON.parse(fs.readFileSync(join(store,'generations',parent+'.json'))).parent;}
  const publication=[];
  for(let n=history.length;n<depth;n++){
   const next={...snapshot.value,parent:snapshot.generation},t=performance.now();const r=register(store,next,snapshot.locators);publication.push({depth:n+1,...r.metrics,totalMilliseconds:performance.now()-t});snapshot=load(store,{generation:r.generation,verify:false});
  }
  history=[];parent=snapshot.generation;while(parent){history.push(parent);parent=JSON.parse(fs.readFileSync(join(store,'generations',parent+'.json'))).parent;}
  if(history.length!==depth)throw Error('Fixture depth drift');
  cases.push({depth,store,current:snapshot.generation,history,publication,metadataBytes:history.reduce((s,id)=>s+fs.statSync(join(store,'generations',id+'.json')).size,0),currentBytes:fs.statSync(join(store,'generations',snapshot.generation+'.json')).size,objects:310,reusedArtifacts:310,changedScientificArtifacts:0,componentHashes:Object.fromEntries(['catalogue','knowledge','understanding','serving'].map(k=>[k,sha(encode(snapshot.value[k]))]))});
 }
 const receipt={schema:'atlas-generation-scaling-fixtures/v1',planSha256:sha(fs.readFileSync(new URL('./plan.json',import.meta.url))),acceptedGeneration:original.generation,acceptedBytes:original.verification,baselineHistory:baseline.history,cases};
 const file=join(root,'fixtures.json');if(fs.existsSync(file)){const previous=JSON.parse(fs.readFileSync(file));for(const c of receipt.cases)c.publication=previous.cases.find(p=>p.depth===c.depth)?.publication??c.publication;}
 fs.writeFileSync(file,encode(receipt));return receipt;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){const r=build();console.log(encode({accepted:r.acceptedGeneration,cases:r.cases.map(c=>({depth:c.depth,generation:c.current,metadataBytes:c.metadataBytes}))}));}
