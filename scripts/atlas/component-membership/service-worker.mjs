// Actual existing S4 server, only storage read hooks vary in this proof process.
import {initialize} from './runtime.mjs';
await initialize({hooks:true});
const {startServer}=await import('../../../pilots/atlas/tryfan/server.mjs');
const server=await startServer({port:0,store:process.argv[2]});process.send({url:server.url,generation:server.initialGeneration});
process.on('message',async message=>{if(message==='stop'){await server.close();process.disconnect();}});
