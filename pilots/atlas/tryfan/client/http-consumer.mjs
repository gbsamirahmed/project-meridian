// Separate-process consumer: only built-in fetch and versioned serving URLs.
// No Atlas imports, file reads, locators, native adapters or derivation stores.
const [url,generation]=process.argv.slice(2);
if(!/^http:\/\/127\.0\.0\.1:\d+$/.test(url))throw new Error('Loopback service required');
async function read(path,body){const r=await fetch(url+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});const value=await r.json();if(!r.ok)throw new Error(value.error?.code??value.status??'unavailable');return value;}
const current=await read('/pilot/v1/current'),g=generation??current.generation,root='/pilot/v1/g/'+g;
const manifest=await read(root+'/manifest');const answer=await read(root+'/query',{property:'place-evidence',place:{crs:'EPSG:27700',point:[266405,359387]}});
if(answer.generation!==g || manifest.generation!==g)throw new Error('Mixed generation');
const artifact=await fetch(url+manifest.assets.find(a=>a.family==='appearance').url);
if(!artifact.ok||artifact.headers.get('X-Atlas-Generation')!==g)throw new Error('Unpinned artifact');
console.log(JSON.stringify({generation:g,manifest,answer,assetBytes:(await artifact.arrayBuffer()).byteLength}));
