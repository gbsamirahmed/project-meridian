import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtempSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,dirname,resolve,basename} from 'node:path';
import {ROOT,encode,sha,contract,load,check} from './runtime.mjs';
const dir=mkdtempSync(join(tmpdir(),'meridian-exe-proof-'));
try{
 const commands=[['init','storeA','initial.json'],['recover','storeA','restartA.json'],['init','storeB','rebuild.json'],['recover','storeA','restartB.json']];
 for(const [action,store,out] of commands){
  const p=spawnSync(process.execPath,['scripts/atlas/exe-water-query-proof/cli.mjs',action,join(dir,store),join(dir,out)],{cwd:ROOT,encoding:'utf8'});
  if(p.status!==0)throw new Error(p.stderr);
 }
 const initial=readFileSync(join(dir,'initial.json'),'utf8');
 for(const p of ['restartA.json','rebuild.json','restartB.json'])assert.equal(readFileSync(join(dir,p),'utf8'),initial);
 const logical=JSON.parse(initial);const {validate}=await contract();const recovered=load(join(dir,'storeA'),s=>check(s,validate));
 const ids=new Set();
 function visit(x){if(!x||typeof x!=='object')return;if(Array.isArray(x.claims))for(const c of x.claims)ids.add(c.id);if(x.featureClaim)ids.add(x.featureClaim.id);if(x.availableHistoricalClaims)for(const c of x.availableHistoricalClaims)ids.add(c.id);for(const v of Object.values(x))visit(v);}
 visit(logical.answers);
 // Preserve shared collection context once, rather than duplicating it in every claim.
 for(const c of recovered.state.bundle.collections.filter(c=>c.binding))for(const q of c.claims)ids.add(q.id);
 const collections=recovered.state.bundle.collections.map(col=>({...col,claims:col.claims.filter(c=>ids.has(c.id))}));
 const evidence=collections.flatMap(c=>c.claims);
 const output={...logical,collections,resources:recovered.state.bundle.resources,definitions:recovered.state.bundle.definitions.filter(d=>['wfd:membership','jrc:detection','phi:habitat','ea:zone','ea:recorded-extent','condition:MHW','condition:planning-AEP','proof:comparison'].includes(d.id)||evidence.some(c=>c.native.term?.id===d.id)),restart:{freshProcesses:4,initialRecoveryExact:true,secondRecoveryExact:true,independentBuildExact:true,logicalResultsSha256:sha(initial)},matrixSha256:sha(readFileSync(join(ROOT,'scripts/atlas/exe-water-query-proof/matrix.json'))),codeSha256:Object.fromEntries(['reader.py','runtime.mjs','cli.mjs','run-proof.mjs'].map(p=>[p,sha(readFileSync(join(ROOT,'scripts/atlas/exe-water-query-proof',p)))]))};
 const outputBody=JSON.stringify(JSON.parse(encode(output)))+'\n';
 writeFileSync(join(ROOT,'docs/research/exe-water-query-results.json'),outputBody);
 console.log(JSON.stringify({queries:logical.answers.length,selectedClaims:evidence.length,storeBytes:logical.storeBytes,outputBytes:Buffer.byteLength(outputBody),restart:output.restart}));
}finally{assert.equal(dirname(resolve(dir)),resolve(tmpdir()));assert.ok(basename(dir).startsWith('meridian-exe-proof-'));rmSync(dir,{recursive:true,force:true});}
