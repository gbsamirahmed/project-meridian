// Finite fresh replay/pinned process, not a service or event platform.
import fs from 'node:fs';import {join} from 'node:path';import {spawnSync} from 'node:child_process';import {createInterface} from 'node:readline';
import * as A from './integration.mjs';import {encode} from '../../../pilots/atlas/tryfan/identity.mjs';
const [mode,store,arg,point]=process.argv.slice(2);await A.initialize();
if(mode==='publish')console.log(encode(await A.publish(store,arg,point?{failAt:point}:{})));
else if(mode==='consumer'){const p=await A.pin(store,arg);console.log(JSON.stringify({ready:true,generation:p.generation}));for await(const line of createInterface({input:process.stdin})){try{console.log(JSON.stringify({answer:p.query(JSON.parse(line))}));}catch(e){console.log(JSON.stringify({error:e.message}));}}}
else if(mode==='view'){const p=await A.pin(store);let rejected=false;try{await A.pin(store,arg);}catch{rejected=true;}console.log(JSON.stringify({generation:p.generation,unpublishedRejected:rejected}));}
else if(mode==='replay'){
 const f=JSON.parse(fs.readFileSync(arg,'utf8')),began=performance.now(),checks=[];const e=await A.E.loadEvidence();
 for(const [i,g]of f.history.entries()){const p=await A.pin(store,g),v=p.snapshot.value,queries=f.queryMatrix[i],o=spawnSync(join(A.D.M.plan.dataRoot??'C:/Users/gbsam/Documents/Projects/meridian-data','earth-lab/.venv/Scripts/python.exe'),[join(A.E.H,'oracle.py')],{input:JSON.stringify({ledger:v.temporalKnowledge,queries}),maxBuffer:32*1024*1024,encoding:'utf8',env:{...process.env,PYTHONIOENCODING:'utf-8'}});A.E.need(o.status===0,o.stderr);const answers=queries.map(q=>{const {generation,members,counters,...answer}=p.query(q);return answer;});A.E.need(encode(answers)===encode(JSON.parse(o.stdout)),'Fresh independent temporal oracle mismatch');A.E.need(A.E.digest(answers)===f.answerHashes[i],'Fresh qualified answers changed');
  const numerical=[];for(const region of ['tryfan','riffelhorn']){const full=await A.M.recompute(v[region+'DependencyState'],A.M.empty(region),{full:true});A.E.need(encode(A.M.currentContent(full.state))===encode(A.M.currentContent(v[region+'Derived'])),'Fresh regional pixel replay mismatch');numerical.push({region,results:Object.keys(full.state.active).length,content:A.M.digest(A.M.currentContent(full.state))});}
  const temporal=A.T.recompute(v.temporalKnowledge,A.T.emptyDerived(),e,{full:true});A.E.need(encode(A.T.currentDerived(temporal.state))===encode(A.T.currentDerived(v.temporalDerived)),'Fresh temporal summary replay mismatch');checks.push({generation:g,queries:queries.length,answerHash:f.answerHashes[i],knowledgeRows:v.temporalKnowledge.records.length,temporalResults:Object.keys(v.temporalDerived.current).length,numerical});
 }
 console.log(encode({checks,current:A.current(store).generation,milliseconds:performance.now()-began,RSS:process.memoryUsage().rss,ancestryTraversals:0}));
}else throw Error('Unsupported finite worker mode');
