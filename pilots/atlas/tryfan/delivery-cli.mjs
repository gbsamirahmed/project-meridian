import { publishDelivery } from './delivery.mjs';
import { encode,requireThat } from './identity.mjs';
const args=process.argv.slice(2);requireThat(args.shift()==='initialize','invalid-request','Only S4 portrayal initialization; no update command');const options={};
for(let i=0;i<args.length;i+=2){requireThat(['--store','--data-root'].includes(args[i]) && args[i+1],'invalid-request','Explicit store/data-root option');options[args[i]==='--store'?'store':'dataRoot']=args[i+1];}
console.log(encode(await publishDelivery(options)));
