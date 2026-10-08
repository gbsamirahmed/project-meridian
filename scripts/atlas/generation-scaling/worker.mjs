// One fresh process or one twenty-request session. No accepted state is written.
import fs from 'node:fs';
import {join} from 'node:path';
import {install,request,normalize,digest} from './runtime.mjs';
const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url))),[store,variant,query,repetitions='1',selection='current']=process.argv.slice(2);
const started=performance.now(),init=install({variant,expectedHash:plan.authoritativeHashes['pilots/atlas/tryfan/generations.mjs']});
const {G,I}=await init(),{openDelivery}=await import('../../../pilots/atlas/tryfan/delivery.mjs');
const service=await openDelivery({store});let generation;
const pin=await request(async()=>{const p=await service.pin(selection==='current'?undefined:selection);generation=p.generation;return p;});
const startupMilliseconds=performance.now()-started,samples=[];
try{
 for(let i=0;i<+repetitions;i++){
  const r=await request(()=>query==='Q18'?service.provenance(generation,I.sha(I.encode({world:'qualified-lineage'}))):service.query(generation,{property:query==='Q05'?'worldcover-native':'place-evidence',place:{crs:'EPSG:27700',point:[266405,359387]},time:query==='Q05'?'2021':null}));
  if(r.value.generation!==generation)throw Error('Mixed generation');const body=I.encode(r.value);
  samples.push({...r.measurement,responseBytes:Buffer.byteLength(body),answerSha256:digest(body),qualifiedSha256:digest(I.encode(normalize(r.value,generation)))});
 }
 console.log(JSON.stringify({schema:'atlas-generation-scaling-sample/v1',comparisonVersion:2,generation,variant,query,startupMilliseconds,pin:pin.measurement,samples,current:G.currentId(store)}));
}finally{await service.close();}
