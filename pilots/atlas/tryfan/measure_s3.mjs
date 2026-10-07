// Deterministic logical receipt; operational measurements remain outside generation identity.
import { readFileSync,writeFileSync } from 'node:fs';
import { resolve,join } from 'node:path';
import { performance } from 'node:perf_hooks';
import { spawnSync } from 'node:child_process';
import { load,STORE } from './generations.mjs';
import { methods,openUnderstanding } from './derivations.mjs';
import { openWorld } from './world.mjs';
import { ROOT } from './catalogue.mjs';
import { encode,sha,requireThat } from './identity.mjs';
import { ref } from './dependencies.mjs';
const OUT=resolve(ROOT,'docs/research/tryfan-pilot-s3-results.json'),matrix=JSON.parse(readFileSync(resolve(import.meta.dirname,'lifecycle-matrix.json'),'utf8'));
const snapshot=load(STORE),m=await methods(),d=await openUnderstanding(),w=await openWorld();
function runs(count,fn){const samples=[];for(let i=0;i<count;i++){const t=performance.now();fn();samples.push(performance.now()-t);}const sorted=[...samples].sort((a,b)=>a-b);return {runs:count,median:sorted[Math.floor(sorted.length/2)],minimum:sorted[0],maximum:sorted.at(-1),samples};}
try {
 const u=snapshot.value.understanding,c=snapshot.value.catalogue,l=snapshot.locators;
 const baseline=runs(5,()=>requireThat(encode(m.initial(snapshot).understanding)===encode(u),'baseline-drift','Fresh derivation differs'));
 const freshness=runs(30,()=>requireThat(d.assess().every(r=>r.assessment.status==='fresh'),'freshness-drift','Unexpected baseline freshness'));
 const recompute=runs(5,()=>m.recompute(u,c,l));const regional=m.recompute(u,c,l);
 const slope=u.results[0],a=slope.receipt.inputs[0].spatial.bounds;
 const relevant={inputId:slope.receipt.inputs[0].id,scopeKnown:true,bounds:[a[0],a[1],a[0]+.01,a[1]+.01],description:'Synthetic interpolation-halo notification, no evidence mutation'};
 const outside={...relevant,bounds:[a[2]+20,a[3]+20,a[2]+21,a[3]+21],description:'Synthetic nonintersecting notification'};
 const scenario={unchanged:d.assess(),unrelatedFamily:d.assess({changes:[{inputId:'nrw-phase1',scopeKnown:true,bounds:[264900,357800,267900,360800],description:'Administrative only'}]}),
 unrelatedSpace:d.assess({changes:[outside]}),relevant:d.assess({changes:[relevant]}),unknownScope:d.assess({changes:[{...relevant,scopeKnown:false}]}),
 methodPolicy:d.assess({methodRevision:'prospective-policy-revision-not-implemented'}),methodReplay:d.assess({policy:'fixed-input-replay-v1',methodRevision:'prospective-policy-revision-not-implemented'})};
 const missing={...l};missing['sha256:'+u.roots[0].assets[0].sha256]='missing-operational-fixture';scenario.unavailable=m.assess(u,c,missing);
 const q=[];for(const row of matrix.queries){const p=u.probes.find(p=>p.id===row.probe);const request={property:row.property,place:{crs:'EPSG:27700',point:p.centre}};
  if(row.property==='historical-derived'){for(const r of u.results) {const rq={...request,place:{crs:'EPSG:27700',point:u.probes.find(p=>p.id===r.probe).centre},resultRef:ref(r),policy:'fixed-input-replay-v1'},answer=await w.query(rq);q.push({id:row.id,request:rq,answerSha256:sha(encode(answer)),status:answer.status,ref:ref(r),freshness:answer.answers[0].freshness.status});}}
  else {const answer=await w.query(request);q.push({id:row.id,request,answerSha256:sha(encode(answer)),status:answer.status,answerCount:answer.answers.length});}
 }
 const req={property:'place-evidence',place:{crs:'EPSG:27700',point:u.probes[0].centre}},integrated=await w.query(req),fresh=[];
 for(let i=0;i<5;i++){const t=performance.now(),p=spawnSync(process.execPath,[join(ROOT,'pilots/atlas/tryfan/lifecycle-cli.mjs'),'query','--request',JSON.stringify(req)],{encoding:'utf8',timeout:30000});requireThat(p.status===0,'fresh-process-failure',p.stderr);
  requireThat(sha(p.stdout)===sha(encode(integrated)),'fresh-process-drift','Q21 differs after restart');fresh.push({milliseconds:performance.now()-t,logicalSha256:sha(p.stdout)});}
 const replay=d.replay(),fixtureReplay=m.replay(regional.understanding,c,l),inspection=d.inspect();
 const logical={schema:'atlas-tryfan-s3-results/v1',generation:snapshot.generation,parent:snapshot.value.parent,capabilities:snapshot.value.capabilities,
 matrixSha256:sha(readFileSync(resolve(import.meta.dirname,'lifecycle-matrix.json'))),basis:u.basis,methods:inspection.methods,results:u.results,active:u.active,dependencies:inspection.dependencies,
 roots:u.roots,selections:inspection.selections,scenarios:scenario,queries:q,integratedSha256:sha(encode(integrated)),coordinator:integrated.answers.map(a=>({property:a.property,generation:a.response.generation,status:a.response.status})),
 baselineReplay:{fromRetainedPixels:replay.fromRetainedPixels,checks:replay.checks},
 isolatedRecomputation:{notPublished:true,considered:regional.considered,recomputed:regional.recomputed,reused:regional.reused,totalRevisions:regional.understanding.results.length,currentResults:regional.understanding.active.length,historicalRetained:encode(regional.understanding.results.slice(0,4))===encode(u.results),replay:fixtureReplay.checks},
 counts:{methods:2,results:4,dependencyEdges:4,reverseKeys:Object.keys(inspection.dependencies.reverse).length,referencedTerrainAssets:new Set(u.roots.flatMap(r=>r.assets.map(a=>a.sha256))).size,registeredArtifacts:c.artifacts.length},verification:snapshot.verification};
 const publication={buildMilliseconds:2253.0614,validationMilliseconds:458.79359999999997,rootSwitchMilliseconds:4.3221999999996115,source:'First real S3 initialize observation; not rerun/production SLA'};
 const output={logical,logicalSha256:sha(encode(logical)),measurements:{outsideIdentity:true,baselineDerivationMilliseconds:baseline,freshnessMilliseconds:freshness,selectiveRecomputeMilliseconds:recompute,
 freshProcesses:fresh,metadataBytes:{catalogue:Buffer.byteLength(encode(c)),knowledge:Buffer.byteLength(encode(snapshot.value.knowledge)),understanding:Buffer.byteLength(encode(u)),generation:snapshot.metrics.generationBytes},startup:d.metrics,publication,rssBytes:process.memoryUsage().rss,memoryQualification:'Node process aggregate including Vite/reused contexts; not isolated dependency memory or production capacity'}};
 if(process.argv.includes('--check')){const previous=JSON.parse(readFileSync(OUT,'utf8'));requireThat(previous.logicalSha256===output.logicalSha256 && encode(previous.logical)===encode(logical),'logical-drift','Persisted deterministic S3 logical evidence differs');}
 else writeFileSync(OUT,encode(output));
 console.log(encode({logicalSha256:output.logicalSha256,generation:logical.generation,counts:logical.counts,metrics:output.measurements}));
}finally{await w.close();await d.close();await m.close();}
