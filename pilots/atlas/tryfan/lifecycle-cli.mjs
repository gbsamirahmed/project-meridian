#!/usr/bin/env node
// Developer S3 commands only. No server or applicability-update publisher.
import { resolve } from 'node:path';
import { readFileSync } from 'node:fs';
import { publishBaseline,openUnderstanding } from './derivations.mjs';
import { openWorld } from './world.mjs';
import { encode,requireThat } from './identity.mjs';
export async function main(args) {
 const command=args.shift(),o={};while(args.length){const k=args.shift();requireThat(['--store','--generation','--data-root','--request','--assessment'].includes(k)&&args.length&&!Object.hasOwn(o,k),'invalid-command','Finite S3 command options required');o[k]=args.shift();}
 const options={store:o['--store'],generation:o['--generation'],dataRoot:o['--data-root']};
 requireThat(['initialize','inspect','assess','replay','query'].includes(command),'invalid-command','Use initialize, inspect, assess, replay, query');
 if(command==='initialize'){requireThat(!options.generation&&!o['--request']&&!o['--assessment'],'invalid-command','Initialize published seed once');return await publishBaseline(options);}
 if(command==='query'){requireThat(o['--request']&&!o['--assessment'],'invalid-command','Query needs request JSON');const w=await openWorld(options);try{return await w.query(JSON.parse(o['--request']));}finally{await w.close();}}
 requireThat(!o['--request'] && (command==='assess'||!o['--assessment']),'invalid-command','Option incompatible with command');
 const d=await openUnderstanding(options);try {
  if(command==='inspect')return {generation:d.generation,...d.inspect()};
  if(command==='assess')return {generation:d.generation,assessments:d.assess(o['--assessment']?JSON.parse(o['--assessment']):{})};
  return {generation:d.generation,...d.replay()};
 }finally{await d.close();}
}
if(process.argv[1] && resolve(process.argv[1])===resolve(import.meta.filename))try{process.stdout.write(encode(await main(process.argv.slice(2))));}catch(e){process.stderr.write(encode({error:{code:e.code??'invalid-request',message:e.message}}));process.exitCode=1;}
