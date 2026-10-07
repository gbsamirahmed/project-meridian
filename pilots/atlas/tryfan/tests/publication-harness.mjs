// Test/measurement driver only: separate service, consumer and writer processes.
import assert from 'node:assert/strict';
import { fork,spawn,spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline';
import { readFileSync,existsSync } from 'node:fs';
import { join,resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import { currentId,load,recoverLock } from '../generations.mjs';
import { generationId } from '../generations.mjs';
import { encode,sha } from '../identity.mjs';
import { recoverInterrupted } from '../updates.mjs';
const cli=resolve(import.meta.dirname,'../update-cli.mjs'),summit=[266405,359387];
function lines(file,args) {
 const child=spawn(process.execPath,[file,...args],{stdio:['pipe','pipe','pipe']}),queued=[],waiting=[];let stderr='';
 child.stderr.on('data',v=>stderr+=v);
 createInterface({input:child.stdout}).on('line',l=>{if(waiting.length)waiting.shift()(l);else queued.push(l);});
 const next=()=>queued.length?Promise.resolve(queued.shift()):new Promise((r,j)=>{const t=setTimeout(()=>j(new Error('Consumer timeout: '+stderr)),30000);waiting.push(l=>{clearTimeout(t);r(l);});});
 return {child,call:async r=>{child.stdin.write(JSON.stringify(r)+'\n');return JSON.parse(await next());}};
}
export async function service(store) {
 const p=fork(resolve(import.meta.dirname,'service-process.mjs'),[JSON.stringify({store})],{stdio:['ignore','ignore','pipe','ipc']});let stderr='';p.stderr.on('data',s=>stderr+=s);
 const address=await new Promise((r,j)=>{const t=setTimeout(()=>j(new Error('Service timeout '+stderr)),30000);p.once('message',v=>{clearTimeout(t);r(v);});p.once('exit',()=>{clearTimeout(t);j(new Error(stderr));});});
 return {...address,close:()=>new Promise((r,j)=>{const t=setTimeout(()=>{p.kill();j(new Error('Service close timeout'));},30000);p.once('exit',()=>{clearTimeout(t);r();});p.send('stop');})};
}
function fresh(url,generation) {
 const start=performance.now(),p=spawnSync(process.execPath,[resolve(import.meta.dirname,'../client/http-consumer.mjs'),url,...(generation?[generation]:[])],{encoding:'utf8',timeout:30000,maxBuffer:2e6});
 assert.equal(p.status,0,p.stderr);return {value:JSON.parse(p.stdout),milliseconds:performance.now()-start};
}
export function signature(v) {
 const a=v.answer??v.value,q=a.answers,find=k=>q.find(x=>x.property===k).response;
 const slope=find('derived-slope'),ratio=find('derived-area-ratio'),nrw=find('nrw-native'),wc=find('worldcover-native');
 assert.ok(q.every(x=>x.response.generation===a.generation),'Every combined answer must use one pinned generation');
 return {generation:a.generation,family:find('terrain-selection').answers[0].selection.family,slope:slope.answers[0].result.claim.result.value.value,
  ratio:ratio.answers[0].result.claim.result.value.value,nrwStatus:nrw.status,nrwCode:nrw.answers[0]?.records[0]?.claim?.native.fields.phase1_code??null,
  worldcover:wc.answers[0].records[0].cell.code,appearanceBytes:v.assetBytes??null};
}
export async function exercise(store,scenario) {
 const first=load(store),g1=first.generation,root=readFileSync(join(store,'current.json')),history=readFileSync(join(store,'generations',g1+'.json'));
 const s=await service(store),old=lines(resolve(import.meta.dirname,'../client/session-consumer.mjs'),[s.url]);let g2;
 const query={property:'place-evidence',place:{crs:'EPSG:27700',point:summit}},failures=[];
 try {
  const pinned=await old.call({operation:'pin'});assert.equal(pinned.generation,g1);
  const before=fresh(s.url),baseline=signature(before.value);
  assert.equal(baseline.family,'production-common');assert.equal(baseline.slope,11.837956999552308);assert.equal(baseline.nrwCode,scenario==='U2'?null:'D.1.1');
  for(const point of ['after-artifacts','after-evidence','after-recompute','before-switch']) {
   const started=performance.now(),p=spawnSync(process.execPath,[cli,'apply','--store',store,'--scenario',scenario,'--fail-at',point],{encoding:'utf8',timeout:60000,maxBuffer:2e6});
   assert.equal(p.status,91,p.stderr);assert.deepEqual(readFileSync(join(store,'current.json')),root);
   const lock=recoverInterrupted(store);assert.ok(lock);const diagnostic=join(store,'staging',lock.operation);
   if(point!=='before-switch')assert.equal(existsSync(join(diagnostic,'candidate.json')),false);
   let orphan=null;
   if(point==='before-switch') {
    const candidate=JSON.parse(readFileSync(join(diagnostic,'candidate.json'),'utf8'));orphan=generationId(candidate);assert.ok(existsSync(join(store,'generations',orphan+'.json')));
    const unavailable=await fetch(s.url+'/pilot/v1/g/'+orphan+'/manifest');assert.equal(unavailable.status,404,'Closed pre-switch orphan is not published');
   }
   const previous=await old.call({query});assert.equal(previous.generation,g1);assert.deepEqual(signature(previous),{...baseline,appearanceBytes:null});
   // New independent service and consumer reconstruct only the old published root.
   const restart=await service(store);let recovered;
   try{recovered=fresh(restart.url);assert.deepEqual(signature(recovered.value),baseline);}finally{await restart.close();}
   recoverLock(store,lock.operation);
   failures.push({point,exitCode:p.status,current:g1,oldConsumer:g1,freshService:g1,orphan,operation:lock.operation,retainedDiagnostics:true,
    milliseconds:performance.now()-started,freshConsumerMilliseconds:recovered.milliseconds});
  }
  const race=fork(resolve(import.meta.dirname,'../client/publication-consumer.mjs'),[s.url],{stdio:['ignore','ignore','pipe','ipc']});let raceError='';race.stderr.on('data',v=>raceError+=v);
  const raceMessage=()=>new Promise((r,j)=>{const t=setTimeout(()=>{race.kill();j(new Error('Race timeout '+raceError));},30000);race.once('message',v=>{clearTimeout(t);r(v);});race.once('exit',code=>{if(code){clearTimeout(t);j(new Error(raceError));}});});
  const ready=await raceMessage();assert.equal(ready.generation,g1);
  const start=performance.now(),p=spawnSync(process.execPath,[cli,'apply','--store',store,'--scenario',scenario],{encoding:'utf8',timeout:60000,maxBuffer:2e6});assert.equal(p.status,0,p.stderr);
  const publicationProcessMilliseconds=performance.now()-start;const publication=JSON.parse(p.stdout);g2=publication.generation;assert.notEqual(g2,g1);assert.equal(currentId(store),g2);
  const raceFinished=raceMessage();race.send('finish');const racing=(await raceFinished).observations;
  assert.ok(racing.length>=3);assert.equal(racing.at(-1).generation,g2);
  for(const row of racing){assert.equal(row.pinned,g1);assert.ok([g1,g2].includes(row.generation));const isOld=row.generation===g1;assert.equal(row.family,isOld?'production-common':'welsh-regional');assert.equal(row.slope,isOld?11.837956999552308:32.918524028483965);assert.equal(row.nrwCode,isOld && scenario==='U2'?null:'D.1.1');}
  assert.equal(g2,failures.at(-1).orphan,'Retry reuses byte-identical closed generation');
  const oldAnswer=await old.call({query});assert.deepEqual(signature(oldAnswer),{...baseline,appearanceBytes:null});
  const after=fresh(s.url),newSignature=signature(after.value);assert.equal(newSignature.generation,g2);assert.equal(newSignature.family,'welsh-regional');assert.equal(newSignature.slope,32.918524028483965);assert.equal(newSignature.ratio,1.191264396968292);assert.equal(newSignature.nrwCode,'D.1.1');
  const historical=fresh(s.url,g1);assert.deepEqual(signature(historical.value),baseline);assert.deepEqual(readFileSync(join(store,'generations',g1+'.json')),history);
  const next=load(store);for(const key of ['catalogue','knowledge'])assert.deepEqual(next.value[key],first.value[key]);
  assert.deepEqual(next.value.understanding.results.slice(0,4),first.value.understanding.results);assert.equal(next.value.understanding.results.length,6);
  assert.equal(publication.buildMetrics.recomputed.length,2);assert.equal(publication.buildMetrics.reused.length,2);
  assert.deepEqual(next.value.serving.assets,first.value.serving.assets);
  const idempotent=spawnSync(process.execPath,[cli,'apply','--store',store,'--scenario',scenario],{encoding:'utf8',timeout:60000});assert.equal(idempotent.status,0,idempotent.stderr);assert.equal(JSON.parse(idempotent.stdout).alreadyPublished,true);assert.equal(currentId(store),g2);
  const restarted=await service(store);let recovered;try{recovered=fresh(restarted.url);assert.deepEqual(signature(recovered.value),newSignature);}finally{await restarted.close();}
  const logical={scenario,from:g1,to:g2,before:baseline,after:newSignature,recomputed:next.value.update.recomputed,reused:next.value.update.reused,
    catalogueSha256:sha(encode(next.value.catalogue)),knowledgeSha256:sha(encode(next.value.knowledge)),understandingSha256:sha(encode(next.value.understanding)),historicalSha256:sha(history),
    statuses:publication.buildMetrics.statuses,registeredArtifacts:310,changedArtifactBytes:0,retainedHistoricalResults:4,totalResults:6};
  return {logical,logicalSha256:sha(encode(logical)),failures,racing,metrics:{...publication.metrics,...publication.buildMetrics,publicationProcessMilliseconds,publicationAndConsumerVerificationMilliseconds:performance.now()-start,
    oldServiceStartup:s.startup,beforeConsumer:before.milliseconds,afterConsumer:after.milliseconds,restartedConsumer:recovered.milliseconds},responseSha256:sha(encode(after.value)),responseBytes:Buffer.byteLength(encode(after.value))};
 } finally {old.child.stdin.end();await s.close();}
}
