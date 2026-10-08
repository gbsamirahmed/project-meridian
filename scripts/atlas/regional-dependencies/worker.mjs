// Finite historical derived-query/replay and publication failure process.
import fs from 'node:fs';import {createInterface} from 'node:readline';
import * as D from './integration.mjs';import {encode} from '../../../pilots/atlas/tryfan/identity.mjs';
const [mode,store,arg,point]=process.argv.slice(2);await D.initialize();
if(mode==='publish')console.log(encode(await D.publish(store,arg,point?{failAt:point}:{})));
else if(mode==='replay'){
 const f=JSON.parse(fs.readFileSync(arg,'utf8')),checks=[],began=performance.now();
 for(const generation of f.history){const p=await D.pin(store,generation);for(const region of ['tryfan','riffelhorn']){const ctx=p.snapshot.value[region+'DependencyState'],state=p.snapshot.value[region+'Derived'],full=await D.M.recompute(ctx,D.M.empty(region),{full:true});if(encode(D.M.currentContent(full.state))!==encode(D.M.currentContent(state)))throw Error('Historical full pixel replay differs');checks.push({generation,region,results:Object.keys(state.active).length,content:D.M.digest(D.M.currentContent(state))});}await p.close();}
 console.log(encode({checks,milliseconds:performance.now()-began,RSS:process.memoryUsage().rss,current:D.current(store).generation}));
}else if(mode==='consumer'){
 const p=await D.pin(store,arg||undefined);console.log(JSON.stringify({ready:true,generation:p.generation}));
 for await(const line of createInterface({input:process.stdin})){try{const q=JSON.parse(line);console.log(JSON.stringify({answer:p.result(q.region,q.question,q.revision)}));}catch(e){console.log(JSON.stringify({error:e.message}));}}await p.close();
}else if(mode==='view'){const p=await D.pin(store);let unpublishedRejected=false;try{await D.pin(store,arg);}catch{unpublishedRejected=true;}console.log(JSON.stringify({generation:p.generation,unpublishedRejected}));}
else throw Error('Unsupported bounded worker mode');
