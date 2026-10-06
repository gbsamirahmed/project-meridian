// A fresh process reads metadata snapshot and re-reads exact retained raster assignments.
import { performance } from 'node:perf_hooks';
import { contract, readRaster, build, checkState, logicalQueries, STORE, publish, load, encode, sha } from './runtime.mjs';
const action=process.argv[2],dir=process.argv[3]??STORE;
const t=performance.now();const {fixtures,validate}=await contract();const reader=readRaster();
if(reader.status!=='available')throw new Error('Required retained evidence unavailable');
if(action==='build'){
 const state=build(reader,fixtures);const publication=publish(dir,state,s=>checkState(s,validate));
 const qstart=performance.now();const logical=logicalQueries(state,reader);const queryMs=performance.now()-qstart;
 console.log(encode({publication,logical,logicalSha256:sha(encode(logical)),elapsedMs:performance.now()-t,queryMs,readerMs:reader.readTimeMs}));
}else if(action==='query'){
 const recovered=load(dir,s=>checkState(s,validate));
 if(recovered.state.raster.revision!==reader.sources['tryfan-worldcover.tif'].sha256)throw new Error('Retained evidence revision mismatch');
 const qstart=performance.now();const logical=logicalQueries(recovered.state,reader);const queryMs=performance.now()-qstart;
 console.log(encode({snapshot:recovered.snapshot,bytes:recovered.bytes,logical,logicalSha256:sha(encode(logical)),elapsedMs:performance.now()-t,queryMs,readerMs:reader.readTimeMs}));
}else throw new Error('Use build or query');
