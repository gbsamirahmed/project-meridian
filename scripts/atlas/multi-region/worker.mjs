// Bounded isolated publication/replay/consumer process; no public service.
import fs from 'node:fs';import {createInterface} from 'node:readline';
import * as I from './integration.mjs';import {encode,sha} from '../../../pilots/atlas/tryfan/identity.mjs';
const [mode,store,id,point]=process.argv.slice(2);await I.initializeProof();
function semantic(v){const c=structuredClone(v);for(const a of c.answers)delete a.metrics;return c;}
if(mode==='publish'){console.log(encode(await I.publish(store,id,{...(point?{failAt:point}:{})})));}
else if(mode==='replay'){
 const input=JSON.parse(fs.readFileSync(id,'utf8')),matrix=JSON.parse(fs.readFileSync(new URL('./matrix.json',import.meta.url),'utf8')),answers={};const started=performance.now();
 for(const g of input.history){const p=await I.pin(store,g);try{const response=await p.query(matrix.cases.map(({region,query})=>({region,query})));answers[g]=sha(encode(semantic(response)));}finally{await p.close();}}
 console.log(encode({current:I.current(store).generation,answers,milliseconds:performance.now()-started,RSS:process.memoryUsage().rss}));
}else if(mode==='recover-view'){
 const p=await I.pin(store);try{const matrix=JSON.parse(fs.readFileSync(new URL('./matrix.json',import.meta.url),'utf8'));const q=await p.query(matrix.cases.slice(0,1).concat(matrix.cases.slice(9,10)).map(({region,query})=>({region,query})));let unpublishedRejected=false;try{await I.pin(store,id);}catch{unpublishedRejected=true;}console.log(encode({generation:q.generation,hash:sha(encode(semantic(q))),unpublishedRejected}));}finally{await p.close();}
}else if(mode==='consumer'){
 const p=await I.pin(store,id||undefined);console.log(JSON.stringify({ready:true,generation:p.generation}));
 for await(const line of createInterface({input:process.stdin})){try{console.log(JSON.stringify({value:await p.query(JSON.parse(line).requests)}));}catch(e){console.log(JSON.stringify({error:{code:e.code,message:e.message}}));}}
 await p.close();
}else throw Error('Unknown bounded worker command');
