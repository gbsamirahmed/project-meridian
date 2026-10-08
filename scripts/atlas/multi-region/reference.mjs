// Independent accepted pilot path: never installs component storage hooks.
import fs from 'node:fs';
import {load,STORE} from '../../../pilots/atlas/tryfan/generations.mjs';
import {openWorld} from '../../../pilots/atlas/tryfan/world.mjs';
import {encode} from '../../../pilots/atlas/tryfan/identity.mjs';
const snapshot=load(STORE);
if(process.argv[2]==='seed'){console.log(encode(snapshot));}
else {const matrix=JSON.parse(fs.readFileSync(new URL('./matrix.json',import.meta.url))),world=await openWorld({generation:snapshot.generation});
 try{const answers={};for(const c of matrix.cases.filter(c=>c.region==='tryfan'))answers[c.id]=await world.query(c.query);console.log(encode({generation:snapshot.generation,answers}));}finally{await world.close();}}
