// Measurements are operational observations, outside source/claim/generation identity.
import { readFileSync,writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { openEvidence,encode } from './query.mjs';
import { queryMatrix } from './query-cli.mjs';
import { ROOT } from './catalogue.mjs';
import { load,STORE } from './generations.mjs';
import { sha } from './identity.mjs';
const start=performance.now(),e=await openEvidence();
const withoutContext=({context,...claim})=>claim;
const summarize=r=>({generation:r.generation,query:r.query,operationalStatus:r.operationalStatus,...(r.result?{result:r.result}:{}),
 records:r.records.map(x=>({family:x.family,...(x.operationalStatus?{operationalStatus:x.operationalStatus}:{}),
 ...(x.claim?{claim:withoutContext(x.claim),context:x.context,...(x.mapping?{mapping:x.mapping}:{})}:{}),
 ...(x.result?{result:x.result}:{}),...(x.membership?{membership:x.membership,feature:x.feature}:{}),...(x.rejectedMapping?{rejectedMapping:x.rejectedMapping}:{}),
 ...(x.assignments?{assignments:{bounds:x.assignments.bounds,cells:x.assignments.cells,counts:x.assignments.counts,meaning:x.assignments.meaning}}:{}),
 ...(x.metadata?{observation:x.metadata.observation,qualification:x.qualification}:{}),
 provenance:{generation:x.provenance.generation,source:x.provenance.source.ref,product:x.provenance.product.ref,representations:x.provenance.representations.map(r=>r.id),
 artifacts:x.provenance.artifacts.map(a=>a.id),rights:x.provenance.rights}}))});
const distribution=values=>{const v=[...values].sort((a,b)=>a-b);return {runs:v.length,min:v[0],median:v[Math.floor(v.length/2)],p95:v[Math.ceil(.95*v.length)-1],max:v.at(-1)};};
try {
 const results=await queryMatrix(e),canonical={generation:e.generation,matrixSha256:sha(readFileSync(resolve(import.meta.dirname,'query-matrix.json'))),results},hash=sha(encode(canonical));
 const timings={};
 for(const property of ['worldcover-native','nrw-native','coexisting-semantic']) {
  const times=[];for(let i=0;i<30;i++){const t=performance.now();await e.query({point:[266405,359387],property});times.push(performance.now()-t);}timings[property]=distribution(times);
 }
 const snapshot=load(STORE,{verify:false}),locators={...snapshot.locators},wc=snapshot.value.catalogue.artifacts.find(a=>a.uses.some(u=>u.family==='worldcover'));
 locators[wc.id]='experiments/atlas/tryfan-regional-pilot-v1/missing-s2-worldcover-fixture.tif';
 const missing=await openEvidence({locators});let q17;try{q17=await missing.query({point:[266405,359387],property:'worldcover-native',time:'2021'});}finally{missing.close();}
 const fresh=[];
 for(let i=0;i<5;i++){
  const t=performance.now(),child=spawnSync(process.execPath,['pilots/atlas/tryfan/query-cli.mjs','matrix'],{cwd:ROOT,encoding:'utf8',maxBuffer:4e6});
  if(child.status!==0)throw Error(child.stderr);const parsed=JSON.parse(child.stdout);const actual=sha(encode(parsed));if(actual!==hash)throw Error('Fresh matrix differs');
  fresh.push({processMilliseconds:performance.now()-t,logicalSha256:actual});
 }
 const historical=await openEvidence({generation:e.parent});let prior;try{prior=await historical.query({point:[266405,359387],property:'coexisting-semantic'});}finally{historical.close();}
 const out={schema:'atlas-tryfan-pilot-s2-results/v1',startingCheckpoint:'b5ac71508776c289ec93a0a894ee6641d62fb879',decision:'C - S2 SUCCESS',
 logical:{generation:e.generation,parent:e.parent,matrixSha256:canonical.matrixSha256,fullMatrixSha256:hash,
   publishedCapabilities:e.publishedCapabilities,readerCapabilities:e.capabilities,counts:{worldcoverCells:185036,templates:8,nrwFeatures:193,nrwNativeCodes:28},
   queries:results.map(r=>({id:r.id,answer:summarize(r.answer)})),unavailableFixture:{id:'Q17',answer:summarize(q17)},
   historical:{generation:prior.generation,claimSha256:sha(encode(prior.records.map(r=>r.claim))),currentClaimSha256:sha(encode(results.find(r=>r.id==='Q09').answer.records.map(r=>r.claim))),scientificChange:false}},
 measurements:{outsideIdentity:true,reader:e.metrics,queryMilliseconds:timings,freshProcesses:fresh,freshMilliseconds:distribution(fresh.map(f=>f.processMilliseconds)),nodeRssBytes:process.memoryUsage().rss,
  caveat:'One Windows developer run; initialized30 request samples each, five independent process matrix executions. Includes Python/Vite runtime overhead; no SLA or physical accuracy metric.'},
 nextTask:'Tryfan pilot retained derivation and lifecycle integration - S3 only; not begun'};
 writeFileSync(resolve(ROOT,'docs/research/tryfan-pilot-s2-results.json'),encode(out));
 console.log(encode({generation:e.generation,hash,queries:results.length,q17:q17.operationalStatus,corner:results.at(-1).answer.records.map(r=>({family:r.family,code:r.claim?.native.fields.phase1_code??r.claim?.native.fields.code,result:r.result??r.claim?.result})),metrics:out.measurements}));
}finally{e.close();}
