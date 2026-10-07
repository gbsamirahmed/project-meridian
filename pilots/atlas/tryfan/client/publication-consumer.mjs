// Test consumer of HTTP only; reads independently while a writer assembles/publishes.
const url=process.argv[2];if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(url))throw new Error('Loopback required');
let done=false;process.on('message',m=>{if(m==='finish')done=true;});
const query={property:'place-evidence',place:{crs:'EPSG:27700',point:[266405,359387]}},observations=[];
async function read(g){const r=await fetch(url+'/pilot/v1/g/'+g+'/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(query)});if(!r.ok)throw new Error('query-unavailable');const v=await r.json();if(v.generation!==g || !v.answers.every(a=>a.response.generation===g))throw new Error('mixed-generation');return v;}
const g1=(await(await fetch(url+'/pilot/v1/current')).json()).generation;
async function sample(){const g=(await(await fetch(url+'/pilot/v1/current')).json()).generation,v=await read(g),old=await read(g1);if(old.generation!==g1)throw new Error('pin-changed');const find=p=>v.answers.find(a=>a.property===p).response;observations.push({generation:g,pinned:g1,family:find('terrain-selection').answers[0].selection.family,slope:find('derived-slope').answers[0].result.claim.result.value.value,nrwStatus:find('nrw-native').status,nrwCode:find('nrw-native').answers[0]?.records[0]?.claim?.native.fields.phase1_code??null});}
await sample();process.send({ready:true,generation:g1});
for(let i=0;!done && i<100;i++)await sample();
// Finite bounded race; a finish signal requires a final new-current read.
if(!done)throw new Error('publication-race-timeout');await sample();process.send({observations});process.disconnect();
