// Bounded S5 update/recovery measurements, not integrated S6 exit acceptance.
import { readFileSync,writeFileSync } from 'node:fs';
import { join,resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { STORE,load } from './generations.mjs';
import { ROOT,verifyArtifacts,DATA } from './catalogue.mjs';
import { forkBaseline,prepareMixedBaseline } from './updates.mjs';
import { methods } from './derivations.mjs';
import { encode,sha,requireThat } from './identity.mjs';
import { exercise,service,signature } from './tests/publication-harness.mjs';
const output=resolve(ROOT,'docs/research/tryfan-pilot-s5-results.json');
const matrix=join(import.meta.dirname,'publication-matrix.json');
if(process.argv.includes('--check')) {
 const receipt=JSON.parse(readFileSync(output,'utf8')),base=load(STORE,{generation:receipt.U1.logical.from}),u1=load(STORE,{generation:receipt.U1.logical.to}),branch=join(STORE,'s5-mixed'),u2=load(branch,{generation:receipt.U2.logical.to});
 requireThat(sha(encode(receipt.logical))===receipt.logicalSha256 && sha(readFileSync(matrix))===receipt.matrixSha256,'receipt-integrity','Logical/matrix receipt changed');
 const m=await methods();
 try {
  for(const [id,s] of [['U1',u1],['U2',u2]]) {
   const r=receipt[id];requireThat(sha(encode(r.logical))===r.logicalSha256 && sha(encode(s.value.understanding))===r.logical.understandingSha256,'receipt-integrity','Stored logical update differs');
   const statuses=m.assess(base.value.understanding,base.value.catalogue,base.locators,{stage:'regional'});
   requireThat(encode(statuses)===encode(r.logical.statuses),'lifecycle-drift','Fresh independent lifecycle assessment changed');
   const replay=m.replay(s.value.understanding,s.value.catalogue,s.locators);requireThat(replay.checks.length===6 && replay.checks.every(c=>c.exact),'replay-mismatch','Fresh pixel replay failed');
   const serv=await service(id==='U1'?STORE:branch);
   try {const p=spawnSync(process.execPath,[join(import.meta.dirname,'client/http-consumer.mjs'),serv.url,s.generation],{encoding:'utf8',timeout:30000,maxBuffer:2e6});requireThat(p.status===0,'consumer-failed',p.stderr);const answer=JSON.parse(p.stdout);requireThat(encode(signature(answer))===encode(r.logical.after) && sha(encode(answer))===r.responseSha256,'consumer-drift','Fresh boundary reproduction differs');}
   finally{await serv.close();}
  }
 } finally {await m.close();}
 console.log(encode({deterministic:true,fromRetainedPixels:true,logicalSha256:receipt.logicalSha256}));
} else {
 requireThat(!load(STORE).value.update,'already-updated','Measured evaluation begins once at actual S4 baseline; use --check after publication');
 const before=load(STORE),branch=join(STORE,'s5-mixed');forkBaseline(branch);prepareMixedBaseline({store:branch});
 // No mutation of retained sources: reuse exact registration, native knowledge and portrayal.
 const U1=await exercise(STORE,'U1'),U2=await exercise(branch,'U2'),after=load(STORE),m=await methods();let replay;
 try{replay=m.replay(after.value.understanding,after.value.catalogue,after.locators);}finally{await m.close();}
 const logical={startingGeneration:before.generation,U1:U1.logicalSha256,U2:U2.logicalSha256,replay:replay.checks,sourceVerification:verifyArtifacts(after.value.catalogue,after.locators,DATA)};
 const record={assessment:'atlas-tryfan-pilot-s5/v1',startingCheckpoint:'f8d3ce98d01f1596a6a2ee9f3041bb721fbbde8f',matrixSha256:sha(readFileSync(matrix)),decision:'C - S5 SUCCESS',
  U1,U2,logical,logicalSha256:sha(encode(logical)),currentGeneration:after.generation,parent:after.value.parent,
  bytes:{generation:Buffer.byteLength(encode(after.value)),catalogue:Buffer.byteLength(encode(after.value.catalogue)),understanding:Buffer.byteLength(encode(after.value.understanding)),serving:Buffer.byteLength(encode(after.value.serving))},
  provenance:'Applicability only; no new source release, source bytes/native claims unchanged; original method and exact scopes retained.',limitations:['Single writer/local filesystem/process interruption only','Whole-metadata writes despite selective computation','No S6/full pilot acceptance','No production/public/Weather/Traverse integration']};
 writeFileSync(output,encode(record));console.log(encode({decision:record.decision,logicalSha256:record.logicalSha256,currentGeneration:after.generation,failures:8,recomputedPerUpdate:2}));
}
