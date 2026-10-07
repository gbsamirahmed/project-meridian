// Fresh process boundary. No query facts are stored as durable world knowledge.
import {writeFileSync} from 'node:fs';
import {contract,reader,build,check,evaluate,publish,load,encode} from './runtime.mjs';
const [action,dir,out]=process.argv.slice(2);const {fixtures,validate}=await contract();
const raw=reader();let loaded;
if(action==='init'){
 const state=build(raw,fixtures);const publication=publish(dir,state,s=>check(s,validate));
 loaded={state,...publication};
}else if(action==='recover')loaded=load(dir,s=>check(s,validate));
else throw new Error('Use init|recover store-directory output-json');
const answers=evaluate(loaded.state,raw);
// Validate the dynamically bound cell/comparison claims as well as the durable templates.
const dynamic=[];
function visit(x){if(!x||typeof x!=='object')return;if(x.claim)dynamic.push(x.claim);for(const v of Object.values(x))if(v!==x.claim)visit(v);}
visit(answers);const unique=[...new Map(dynamic.map(c=>[c.id+':'+c.revision,c])).values()];
const bundle=structuredClone(loaded.state.bundle);
bundle.collections.push({id:'collection:dynamic-query-validation',revision:'1',product:bundle.collections.at(-1).product,representation:'records',context:bundle.collections.at(-1).context,claims:unique});
const errors=validate(bundle);if(errors.length)throw new Error(errors.join('\n'));
const result={schema:loaded.state.schema,snapshot:loaded.snapshot,storeBytes:loaded.bytes,answers,sourceDirectoryHashes:raw.directorySha256,sourceHashes:loaded.state.sources,counts:loaded.state.bundle.collections.map(c=>({id:c.id,claims:c.claims.length})),dynamicClaimCount:unique.length,method:loaded.state.method};
writeFileSync(out,encode(result));console.log(loaded.snapshot);
