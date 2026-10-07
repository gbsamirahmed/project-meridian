// Independent service + actual browser consumer; no running developer server required.
import { fork,spawn } from 'node:child_process';
import { join } from 'node:path';
const service=fork(join(import.meta.dirname,'service-process.mjs'),['{}'],{silent:true});service.stderr.on('data',v=>process.stderr.write(v));
const message=()=>new Promise((r,j)=>{const timer=setTimeout(()=>j(new Error('Service process timeout')),30000);service.once('message',v=>{clearTimeout(timer);r(v);});service.once('error',j);});
try{const ready=await message(),browser=spawn(process.execPath,[join(import.meta.dirname,'visual-s6.mjs'),ready.url],{stdio:'inherit'});const code=await new Promise((r,j)=>{browser.once('exit',r);browser.once('error',j);});const stopped=message();service.send('stop');await stopped;if(code)process.exitCode=code;}
catch(e){service.kill();throw e;}
