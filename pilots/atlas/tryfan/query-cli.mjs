#!/usr/bin/env node
// Developer inspection only; no HTTP listener, generation writer or derivation execution.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import { openEvidence, encode } from './query.mjs';
import { requireThat, sha } from './identity.mjs';
const matrix=JSON.parse(readFileSync(resolve(import.meta.dirname,'query-matrix.json'),'utf8'));
export async function queryMatrix(evidence) {
  const results=[];
  for(const q of matrix.queries) {
    if(q.id==='Q17')continue; // Operational missing-locator fixture exercised separately, never the retained store.
    const point=matrix.probes[q.probe], request={point,crs:'EPSG:27700',property:q.property,time:q.time};
    if(q.property==='worldcover-support')request.support=[point[0]-200,point[1]-200,point[0]+200,point[1]+200];
    results.push({id:q.id,answer:await evidence.query(request)});
    if(q.id==='Q07')results.push({id:'Q07-20m',answer:await evidence.query({...request,support:[point[0]-10,point[1]-10,point[0]+10,point[1]+10]})});
  }
  results.push({id:'core-corner',answer:await evidence.query({point:[264900,357800],property:'coexisting-semantic'})});
  return results;
}
export async function main(args) {
  const command=args.shift(),options={};
  const allowed=['store','generation','data-root','locators','request'];
  while(args.length){const key=args.shift();requireThat(key?.startsWith('--') && allowed.includes(key.slice(2)) && args.length && !Object.hasOwn(options,key.slice(2)),'invalid-command','Explicit bounded options required');options[key.slice(2)]=args.shift();}
  requireThat(['inspect','query','matrix'].includes(command) && (command==='query'?!!options.request:!options.request),'invalid-command','Use inspect, matrix, or query --request finite-JSON');
  requireThat(!options.locators?.toLowerCase().includes('meridian-private'),'invalid-locator','Private locator files excluded before access');
  const start=performance.now(),e=await openEvidence({store:options.store,generation:options.generation,dataRoot:options['data-root'],locators:options.locators?JSON.parse(readFileSync(options.locators,'utf8')):undefined});
  try {
    if(command==='query')return await e.query(JSON.parse(options.request));
    if(command==='matrix')return {generation:e.generation,matrixSha256:sha(readFileSync(resolve(import.meta.dirname,'query-matrix.json'))),results:await queryMatrix(e)};
    return {generation:e.generation,parent:e.parent,publishedCapabilities:e.publishedCapabilities,readerCapabilities:e.capabilities,
      native:{worldcover:e.metadata.families.worldcover,nrw:e.metadata.families.nrw.status==='available'?{status:'available',featureCount:e.metadata.families.nrw.featureCount,codeCount:e.metadata.families.nrw.codeCount,index:e.metadata.families.nrw.index}:e.metadata.families.nrw},
      metrics:{...e.metrics,processMilliseconds:performance.now()-start,rssBytes:process.memoryUsage().rss}};
  } finally {e.close();}
}
if(process.argv[1] && resolve(process.argv[1])===resolve(import.meta.filename)) {
  try {process.stdout.write(encode(await main(process.argv.slice(2))));}
  catch(e){process.stderr.write(encode({error:{code:e.code??'invalid-request',message:e.message}}));process.exitCode=1;}
}
