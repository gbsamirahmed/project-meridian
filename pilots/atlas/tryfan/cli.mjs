#!/usr/bin/env node
// Finite developer commands; no network listener or world-model query surface.
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { performance } from 'node:perf_hooks';
import { PilotError, encode, json, requireThat } from './identity.mjs';
import { buildRetained, seed, DATA } from './catalogue.mjs';
import { STORE, storePath, currentId, load, stage, publish, register, recoverLock, rollback } from './generations.mjs';
const args=process.argv.slice(2),command=args.shift(),options={};
try {
  const allowed=new Set(['store','data-root','generation','operation','locators','fail-at']);
  while(args.length) {const key=args.shift();requireThat(key?.startsWith('--') && allowed.has(key.slice(2)) && args.length && !Object.hasOwn(options,key.slice(2)),
    'invalid-command','Use one explicit value per documented option');options[key.slice(2)]=args.shift();}
  const permitted={register:['store','data-root','fail-at'],stage:['store','data-root','fail-at'],publish:['store','data-root','operation','fail-at'],
    inspect:['store','data-root','generation','locators'],validate:['store','data-root','generation','locators'],
    'recover-lock':['store','operation'],rollback:['store','data-root','generation']}[command];
  requireThat(permitted && Object.keys(options).every(key=>permitted.includes(key)),'invalid-command','Option is not valid for this command');
  const store=storePath(options.store??STORE),dataRoot=options['data-root']??DATA;
  requireThat(!options['fail-at'] || ['after-staging','after-validation','before-switch'].includes(options['fail-at']),'invalid-command','Unknown failure point');
  const reachable={register:['after-staging','after-validation','before-switch'],stage:['after-staging'],publish:['after-validation','before-switch']};
  requireThat(!options['fail-at'] || reachable[command]?.includes(options['fail-at']),'invalid-command','Failure point is not reachable by this command');
  const start=performance.now();let result;
  if(command==='register' || command==='stage') {
    const built=await buildRetained(dataRoot),buildMilliseconds=performance.now()-start;
    const parent=existsSync(join(store,'current.json'))?currentId(store):null;
    const value=seed(built,parent);
    result=(command==='stage'?stage:register)(store,value,built.locators,{dataRoot,failAt:options['fail-at']});
    result.metrics={...result.metrics,buildMilliseconds};
  } else if(command==='publish') result=publish(store,options.operation,{dataRoot,failAt:options['fail-at']});
  else if(command==='recover-lock') result=recoverLock(store,options.operation);
  else if(command==='rollback') result=rollback(store,options.generation,{dataRoot});
  else if(command==='inspect' || command==='validate') {
    const state=load(store,{dataRoot,generation:options.generation,locators:options.locators?json(options.locators,'invalid-locator'):undefined});
    result={generation:state.generation,parent:state.value.parent,format:state.value.format,capabilities:state.value.capabilities,
      counts:{sources:state.value.catalogue.sources.length,products:state.value.catalogue.products.length,representations:state.value.catalogue.representations.length,
        families:state.value.catalogue.families.length,artifacts:state.value.catalogue.artifacts.length},verification:state.verification,metrics:state.metrics};
    if(command==='inspect') {result.catalogue=state.value.catalogue;result.locators=state.locators;}
  } else throw new PilotError('invalid-command','Commands: register, stage, publish, inspect, validate, recover-lock, rollback');
  result.metrics={...result.metrics,processMilliseconds:performance.now()-start,rssBytes:process.memoryUsage().rss};
  process.stdout.write(encode(result));
} catch(error) {
  process.stderr.write(encode({error:{code:error.code??'internal-error',message:error.message}}));process.exitCode=1;
}
