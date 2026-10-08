// Fresh-process measurement over a fixed publication pin; no cross-request verification cache.
import fs from 'node:fs';import {initialize} from './runtime.mjs';
import {encode,sha} from '../../../pilots/atlas/tryfan/identity.mjs';
import {normalize} from '../generation-scaling/runtime.mjs';
const [store,selection,mode,repeat='1']=process.argv.slice(2),began=performance.now();
const {core}=await initialize({hooks:mode.startsWith('Q')});let delivery;
if(mode.startsWith('Q')){const {openDelivery}=await import('../../../pilots/atlas/tryfan/delivery.mjs');delivery=await openDelivery({store});}
const picked=selection==='current'?core.root(store).generation:selection;
const pin=await core.measured(()=>delivery?delivery.pin(picked):core.resolveGeneration(store,picked));const startupMilliseconds=performance.now()-began,samples=[];
try{
 for(let i=0;i<+repeat;i++){
  const r=await core.measured(()=>!delivery?core.resolveGeneration(store,picked,{hydrate:mode==='hydrate'}):mode==='Q18'?delivery.provenance(picked,sha(encode({world:'qualified-lineage'}))):delivery.query(picked,{property:mode==='Q05'?'worldcover-native':'place-evidence',place:{crs:'EPSG:27700',point:[266405,359387]},time:mode==='Q05'?'2021':null}));
  const body=encode(r.value),qualified=normalize(r.value,picked);
  samples.push({...r.measurement,responseBytes:Buffer.byteLength(body),answerSha256:sha(body),qualifiedSha256:sha(encode(qualified))});
 }
 console.log(encode({generation:picked,mode,startupMilliseconds,pin:pin.measurement,samples,current:core.root(store).generation}));
}finally{await delivery?.close();}
