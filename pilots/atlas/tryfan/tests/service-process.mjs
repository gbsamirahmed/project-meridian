import { startServer } from '../server.mjs';
const service=await startServer({port:0,...JSON.parse(process.argv[2]??'{}')});
process.send({url:service.url,generation:service.initialGeneration,startup:service.metrics.startupMilliseconds});
process.on('message',async message=>{if(message==='stop'){await service.close();process.send({metrics:service.metrics,delivery:service.delivery.metrics,memory:process.memoryUsage()});process.disconnect();}});
