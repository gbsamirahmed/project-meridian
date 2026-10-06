import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs';
import { performance } from 'node:perf_hooks';
import { ROOT, STORE, encode, sha } from './runtime.mjs';
const measures=[];
function child(action){const t=performance.now();const p=spawnSync(process.execPath,['scripts/atlas/worldcover-binding-proof/cli.mjs',action,STORE],{cwd:ROOT,encoding:'utf8'});
 if(p.status!==0)throw new Error(p.stderr);const result=JSON.parse(p.stdout);measures.push({action,wallMs:performance.now()-t,elapsedMs:result.elapsedMs,readerMs:result.readerMs,qualifiedQueryMs:result.queryMs});return result;}
const built=child('build'),restarted=child('query'),rebuilt=child('build');
if(built.logicalSha256!==restarted.logicalSha256 || built.logicalSha256!==rebuilt.logicalSha256 || built.publication.snapshot!==rebuilt.publication.snapshot)throw new Error('Deterministic rebuild/restart mismatch');
const files=['reader.py','runtime.mjs','cli.mjs','run-proof.mjs'];
const methods=Object.fromEntries(files.map(f=>{const p='scripts/atlas/worldcover-binding-proof/'+f;return [p,sha(readFileSync(p))];}));
const storeSnapshots=readdirSync(STORE+'/snapshots').map(name=>({name,bytes:statSync(STORE+'/snapshots/'+name).size}));
const receipt={storeSnapshots,storeBytes:storeSnapshots.reduce((n,s)=>n+s.bytes,0)+built.publication.pointerBytes,decision:'C - SUCCESS',baseline:'691450ff540e0e15ade58cba8464d221e89dc119',store:STORE,methods,
 planSha256:sha(readFileSync('docs/research/tryfan-worldcover-binding-plan.json')),snapshot:built.publication.snapshot,snapshotBytes:built.publication.bytes,pointerBytes:built.publication.pointerBytes,
 logicalSha256:built.logicalSha256,restartEquivalent:true,rebuildEquivalent:true,realProcesses:3,
 measurements:measures,logical:built.logical};
writeFileSync('docs/research/tryfan-worldcover-binding-results.json',encode(receipt));
console.log(encode({decision:receipt.decision,snapshotBytes:receipt.snapshotBytes,logicalSha256:receipt.logicalSha256,measurements:measures}));
