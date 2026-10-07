// Acceptance-only supplement: twenty batches of the original ordinary Q01-Q21 requests.
// Q17 uses a missing-asset fixture in the existing regression suite, never the real store.
import assert from 'node:assert/strict';
import {fork} from 'node:child_process';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {performance} from 'node:perf_hooks';
import {ROOT} from '../catalogue.mjs';
import {STORE,load} from '../generations.mjs';
import {encode,sha} from '../identity.mjs';
const plan=JSON.parse(readFileSync(join(ROOT,'docs/research/tryfan-regional-pilot-plan.json'))),native=JSON.parse(readFileSync(join(import.meta.dirname,'../query-matrix.json'))),before=load(STORE).generation;
const child=fork(join(import.meta.dirname,'service-process.mjs'),[],{silent:true});
const next=()=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>{child.kill();reject(Error('Service timeout'));},30000);child.once('message',m=>{clearTimeout(timer);resolve(m);});child.once('error',reject);});
const ready=await next(),samples={},start=performance.now();let provenanceURL;
try {
 const requests=plan.query.matrix.filter(q=>q.id!=='Q17').flatMap(q=>q.id==='Q12'?q.context.resultRefs.map(ref=>({...q,sampleId:q.id+'-'+ref.probe+'-'+ref.property,probe:ref.probe,resultRef:{id:ref.id,revision:ref.revision},policy:q.context.policy})):q.id==='Q07'?[{...q,sampleId:'Q07-400m',halfWidth:200},{...q,sampleId:'Q07-20m',halfWidth:10}]:[{...q,sampleId:q.id}]);
 for(let batch=0;batch<20;batch++)for(const q of requests) {
  const point=native.probes[q.probe],place=q.property==='worldcover-support'?{crs:'EPSG:27700',bounds:[point[0]-(q.halfWidth??200),point[1]-(q.halfWidth??200),point[0]+(q.halfWidth??200),point[1]+(q.halfWidth??200)]}:{crs:'EPSG:27700',point};
  const t=performance.now(),root=ready.url+'/pilot/v1/g/'+ready.generation,r=await fetch(q.id==='Q18'?ready.url+provenanceURL:root+'/query',q.id==='Q18'?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({property:q.property,place,time:q.time,...(q.resultRef?{resultRef:q.resultRef,policy:q.policy}:{})})}),bytes=Buffer.from(await r.arrayBuffer());
  assert.equal(r.status,200,q.id);const value=JSON.parse(bytes);assert.equal(value.generation,before,q.id);if(value.provenanceURL)provenanceURL=value.provenanceURL;
  (samples[q.sampleId]??=[]).push({milliseconds:performance.now()-t,bytes:bytes.length,sha256:sha(bytes)});
 }
 const stats=Object.fromEntries(Object.entries(samples).map(([id,rows])=>{const v=rows.map(s=>s.milliseconds).sort((a,b)=>a-b);assert.equal(new Set(rows.map(s=>s.sha256)).size,1,id);return [id,{samples:rows,median:v[10],p95:v[18],min:v[0],max:v[19]}];}));
 const receipt={schema:'atlas-tryfan-s6-full-warm-matrix/v1',generation:before,batches:20,requests:requests.length*20,excluded:{Q17:'Unavailable-file fixture rerun by original S2/S4/S6 regression, no retained locator mutation'},rows:stats,elapsedMilliseconds:performance.now()-start,cache:'Initialized service and warm OS cache; no query/byte cache',errors:0};
 const initial=join(STORE,'s6-acceptance/warm-matrix.json');writeFileSync(existsSync(initial)?join(STORE,'s6-acceptance/warm-matrix-repeat.json'):initial,encode(receipt));console.log(encode({batches:20,requests:requests.length*20,elapsedMilliseconds:receipt.elapsedMilliseconds,rows:Object.keys(stats)}));
} finally {const done=next();child.send('stop');await done;assert.equal(load(STORE).generation,before);}
