// Boundary-only interactive process used for pinned reader publication tests.
import { createInterface } from 'node:readline';
const url=process.argv[2];if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(url))throw new Error('Loopback required');let generation;
for await(const line of createInterface({input:process.stdin})) {
 try{const request=JSON.parse(line);let path,options;
  if(request.operation==='pin') {if(generation)throw new Error('invalid-context-transition');const r=await fetch(url+'/pilot/v1/current');const v=await r.json();generation=request.generation??v.generation;path='/pilot/v1/g/'+generation+'/manifest';}
  else {if(!generation)throw new Error('context-unpinned');path='/pilot/v1/g/'+generation+'/query';options={method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request.query)};}
  const response=await fetch(url+path,options),value=await response.json();if(!response.ok)throw new Error(value.error?.code??value.status??'unavailable');if(value.generation!==generation)throw new Error('mixed-generation');console.log(JSON.stringify({generation,value}));
 }catch(e){console.log(JSON.stringify({error:e.message}));}
}
