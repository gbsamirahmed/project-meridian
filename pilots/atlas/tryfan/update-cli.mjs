import { publishUpdate,prepareMixedBaseline,forkBaseline } from './updates.mjs';
import { recoverLock,STORE } from './generations.mjs';
import { encode,requireThat } from './identity.mjs';
const [command,...args]=process.argv.slice(2),o={};
try {
 for(let i=0;i<args.length;i+=2){requireThat(['--store','--scenario','--fail-at','--operation','--source'].includes(args[i]) && args[i+1],'invalid-command','Explicit bounded options required');o[args[i].slice(2)]=args[i+1];}
 let r;
 if(command==='apply')r=await publishUpdate({store:o.store??STORE,scenario:o.scenario??'U1',failAt:o['fail-at']});
 else if(command==='fork')r=forkBaseline(o.store,{source:o.source??STORE});
 else if(command==='withhold-nrw')r=prepareMixedBaseline({store:o.store});
 else if(command==='recover-lock')r=recoverLock(o.store??STORE,o.operation);
 else requireThat(false,'invalid-command','Commands: apply, fork, withhold-nrw, recover-lock');
 process.stdout.write(encode(r));
} catch(e){console.error(encode({error:{code:e.code??'update-failed',message:e.message}}));process.exitCode=1;}
