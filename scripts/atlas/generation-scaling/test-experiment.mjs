import test,{after} from 'node:test';import assert from 'node:assert/strict';
import fs from 'node:fs';import {join} from 'node:path';import {execFileSync} from 'node:child_process';import {randomUUID} from 'node:crypto';
import {digest,normalize} from './runtime.mjs';
const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url))),root=plan.stateRoot,base=join(root,'history-7');
const failures=[];after(()=>{const first=join(root,'failure-matrix.json');fs.writeFileSync(fs.existsSync(first)?join(root,'failure-matrix-repeat.json'):first,JSON.stringify({schema:'atlas-generation-scaling-failures/v1',cases:failures},null,2)+'\n');});
const run=(module,args)=>JSON.parse(execFileSync(process.execPath,['scripts/atlas/generation-scaling/'+module,...args],{encoding:'utf8',timeout:120000,maxBuffer:10*1024*1024}));
test('frozen prospective matrix matches assessment',()=>{assert.deepEqual(plan.historyDepths,[7,28,112]);assert.equal(plan.cases.length,18);assert.equal(plan.freshProcesses,5);assert.equal(plan.warmRequests,20);assert.equal(plan.supplement.cases.length,7);});
test('accepted source hashes guarded',()=>{for(const [file,hash] of Object.entries(plan.authoritativeHashes))assert.equal(digest(fs.readFileSync(file)),hash);});
test('generation identity normalization retains source/result revisions',()=>{const value={generation:'g',ref:{revision:'abc',generation:'historical'},url:'/pilot/v1/g/'+'a'.repeat(64)+'/query'};assert.equal(normalize(value,'g').ref.revision,'abc');assert.equal(normalize(value,'g').ref.generation,'historical');assert.equal(normalize(value,'g').generation,'PINNED_GENERATION');});
for(const query of plan.queries)test('qualified parity and request-local reads '+query,()=>{
 const accepted=run('worker.mjs',[base,'accepted',query,'2']),reuse=run('worker.mjs',[base,'request-reuse',query,'2']);
 assert.equal(accepted.generation,reuse.generation);assert.equal(accepted.samples[0].answerSha256,reuse.samples[0].answerSha256);
 assert.equal(reuse.samples[0].answerSha256,reuse.samples[1].answerSha256);assert.equal(reuse.samples[0].reads.generations.calls,7);
 assert.equal(reuse.samples[0].counters.integrityChecks,7);assert.equal(reuse.samples[1].counters.integrityChecks,7);assert.ok(accepted.samples[0].reads.generations.calls>7);
});
for(const [scenario,code] of [['corrupt-ancestor','generation-integrity'],['missing-artifact','artifact-unavailable'],['orphan','generation-missing'],['between-requests','generation-integrity'],['unknown','generation-missing']])test('failure parity '+scenario,()=>{
 const results=[];
 for(const variant of plan.variants){const fixture=join(root,'failure-fixtures',scenario+'-'+variant+'-'+randomUUID());fs.cpSync(base,fixture,{recursive:true});results.push(run('failure-worker.mjs',[fixture,variant,scenario]));}
 assert.equal(results[0].code,code);assert.equal(results[1].code,code);assert.ok(results.every(r=>r.rootUnchanged));
 failures.push({scenario,expected:code,results});
});
test('request reuse preserves pins across actual administrative publication',()=>{
 for(const variant of plan.variants){
  const fixture=join(root,'transition-'+variant+'-'+randomUUID());fs.cpSync(base,fixture,{recursive:true});
  const script=`import fs from 'node:fs';import assert from 'node:assert/strict';import {install,request,normalize} from './scripts/atlas/generation-scaling/runtime.mjs';
   const p=JSON.parse(fs.readFileSync('scripts/atlas/generation-scaling/plan.json')),init=install({variant:process.argv[2],expectedHash:p.authoritativeHashes['pilots/atlas/tryfan/generations.mjs']}),{G,I}=await init(),{openDelivery}=await import('./pilots/atlas/tryfan/delivery.mjs'),store=process.argv[1],d=await openDelivery({store});
   try{const r=await request(async()=>{const old=await d.pin(),q={property:'place-evidence',place:{crs:'EPSG:27700',point:[266405,359387]}},a=await d.query(old.generation,q),s=G.load(store,{verify:false}),next=G.register(store,{...s.value,parent:s.generation},s.locators),b=await d.query(old.generation,q),newPin=await d.pin(),c=await d.query(newPin.generation,q);
    assert.equal(b.generation,old.generation);assert.equal(newPin.generation,next.generation);assert.notEqual(newPin.generation,old.generation);assert.deepEqual(a,b);assert.deepEqual(normalize(a,old.generation),normalize(c,newPin.generation));return {old:old.generation,new:newPin.generation,passed:true};});console.log(JSON.stringify(r.value));}finally{await d.close();}`;
  const result=JSON.parse(execFileSync(process.execPath,['--input-type=module','-e',script,fixture,variant],{encoding:'utf8',timeout:120000}));assert.ok(result.passed);assert.notEqual(result.old,result.new);
 }
});
test('metadata-only controls preserve complete references and historical identities',()=>{
 const fixture=join(root,'small-control-'+randomUUID());const config={stateRoot:fixture,supplement:{cases:[{id:'small',depth:3,objects:10,reuse:.9,pattern:'localized'}],repetitions:2,modes:plan.supplement.modes}};
 const python='C:/Users/gbsam/Documents/Projects/meridian-data/earth-lab/.venv/Scripts/python.exe';
 const script="import sys,json;sys.path.insert(0,'scripts/atlas/generation-scaling');from supplement import run;print(json.dumps(run(json.loads(sys.stdin.read()))))";
 const small=JSON.parse(execFileSync(python,['-c',script],{input:JSON.stringify(config),encoding:'utf8'}))[0];
 assert.equal(small.actualReused,9);assert.equal(small.changedReferences,1);assert.equal(small.uniqueMetadataObjects,12);assert.equal(small.samples['carry-reference'].logical.hashOperations,0);assert.equal(small.samples['verify-reused-metadata'].logical.verificationOperations,9);
 const resultsFile='docs/research/atlas-generation-scaling-results.json';if(fs.existsSync(resultsFile)){const r=JSON.parse(fs.readFileSync(resultsFile));for(const c of r.referenceControls){assert.equal(c.actualReused+c.changedReferences,c.objects);assert.equal(c.samples['verify-reused-metadata'].logical.verificationOperations,c.actualReused);assert.equal(c.samples['direct-oldest'].logical.historyTraversals,0);}}
});
