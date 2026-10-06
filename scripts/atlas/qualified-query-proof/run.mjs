// Offline research runner. Vite SSR loads the existing contracts/selector without app startup.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { createServer } from 'vite';

const args=process.argv.slice(2);const data=resolve(args[0]??'');
if (!args[0]) throw new Error('Usage: node scripts/atlas/qualified-query-proof/run.mjs DATA [--freeze-inputs] [--check]');
const freeze=args.includes('--freeze-inputs'),checkOnly=args.includes('--check');
if (freeze && checkOnly) throw new Error('Freeze and check are separate actions');
const read=p=>JSON.parse(readFileSync(p,'utf8'));
const sha=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const dump=o=>JSON.stringify(o,null,2)+'\n';
const planPath='docs/research/tryfan-qualified-query-plan.json';const plan=read(planPath);
const python=join(data,'earth-lab/.venv/Scripts/python.exe');
function adapter(flags,input){
 const p=spawnSync(python,['-X','utf8','scripts/atlas/qualified-query-proof/retained_inputs.py',...flags],{input:input?JSON.stringify(input):undefined,encoding:'utf8',maxBuffer:4*1024*1024});
 if(p.status!==0) throw new Error(p.stderr||p.error?.message||'Retained adapter failed');
 return JSON.parse(p.stdout);
}
const start=performance.now();const geometry=adapter(['--geometry']);
const server=await createServer({configFile:false,appType:'custom',logLevel:'silent',server:{middlewareMode:true}});
try {
 const {createTryfanTerrainProof}=await server.ssrLoadModule('/src/atlas/terrain/metadata/tryfanTerrainProof.ts');
 const {registerTerrainHierarchy}=await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainRegistry.ts');
 const {selectTerrain}=await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainSelector.ts');
 const {validateSemanticEvidence}=await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');
 const proof=await server.ssrLoadModule('/scripts/atlas/qualified-query-proof/proof.ts');
 const regional=createTryfanTerrainProof();const commonDeclaration=structuredClone(regional.hierarchy);
 commonDeclaration.id='tryfan-proof-common-context';commonDeclaration.revision='1';commonDeclaration.regional=[];commonDeclaration.selection.regionalOrder=[];
 const common=registerTerrainHierarchy(commonDeclaration,regional.options);
 const request=p=>({footprint:p.eligibilityFootprint,scale:{scheme:plan.selection.scheme,requestedLevel:plan.selection.requestedLevel}});
 const selections={before:{},after:{}};const needed=new Map();
 for (const p of geometry.probes) for (const [stage,registry] of [['before',common],['after',regional]]) {
   const q=selectTerrain(registry,request(p));selections[stage][p.id]=q;
   if(q.status!=='selected') throw new Error('Frozen supported probe unavailable: '+p.id+' '+stage+' '+q.reason);
   const r={probe:p.id,family:q.family,level:q.level};needed.set(q.family+':'+p.id,r);
 }
 const sampled=adapter(['--data',data],[...needed.values()]);
 const stableInputs={geometry,roots:sampled.roots,sourceChecks:sampled.sourceChecks,software:sampled.software};
 const inputPath='docs/research/tryfan-qualified-query-inputs.json';
 if(freeze){if(existsSync(inputPath)) throw new Error('Input snapshot exists; refuse silent refreeze');writeFileSync(inputPath,dump(stableInputs));}
 else if(!existsSync(inputPath)||proof.canonical(read(inputPath))!==proof.canonical(stableInputs)) throw new Error('Retained input/geometry/software differs from pinned snapshot; no silent reacquisition/refreeze');
 const codeFiles=['scripts/atlas/qualified-query-proof/proof.ts','scripts/atlas/qualified-query-proof/retained_inputs.py','scripts/atlas/qualified-query-proof/run.mjs'];
 const methodFiles=Object.fromEntries(codeFiles.map(f=>[f,sha(f)]));
 const methodRevision=proof.hash({methodFiles,planSha256:geometry.planSha256,software:sampled.software});
 const roots=stableInputs.roots;const results=[];const assessments=[];const before=[];
 for(const p of geometry.probes){
   const selected=selections.before[p.id];const root=roots.find(r=>r.probe===p.id&&r.family===selected.family);
   const pair=proof.derive(p,root,methodRevision);results.push(...pair);before.push(...pair);
 }
 // This finite two-level chain is explicit; no generic graph scheduler or global rebuild.
 const recomputed=[];
 for(const p of geometry.probes){
   const old=before.filter(r=>r.probe===p.id);const selected=selections.after[p.id];
   for(const r of old){const replay=proof.assess(r,results,roots,selected,'fixed-input-replay-v1');const current=proof.assess(r,results,roots,selected,'current-applicable-terrain-v1',[],methodRevision);assessments.push({probe:p.id,property:r.property,historical:{id:r.claim.id,revision:r.claim.revision}, replay,current});}
   if(proof.assess(old[0],results,roots,selected,'current-applicable-terrain-v1',[],methodRevision).status==='stale'){
     const root=roots.find(r=>r.probe===p.id&&r.family===selected.family);const pair=proof.derive(p,root,methodRevision);results.push(...pair);recomputed.push(...pair.map(r=>({probe:r.probe,property:r.property,claim:{id:r.claim.id,revision:r.claim.revision}})));
   }
 }
 const currentResults=geometry.probes.flatMap(p=>results.filter(r=>r.probe===p.id&&proof.assess(r,results,roots,selections.after[p.id],'current-applicable-terrain-v1',[],methodRevision).status==='fresh').map(r=>({question:r.question,result:{id:r.claim.id,revision:r.claim.revision},value:r.claim.result,preferredUnder:'current-applicable-terrain-v1'})));
 const welshSlope=results.find(r=>r.property==='slope'&&r.probe==='summit'&&r.receipt.inputs[0].id.includes('welsh-regional'));
 const bounds=welshSlope.receipt.inputs[0].spatial.bounds;
 const outside={inputId:welshSlope.receipt.inputs[0].id,bounds:[bounds[2]+20,bounds[3]+20,bounds[2]+21,bounds[3]+21],scopeKnown:true,description:'Synthetic change notification outside actual used neighbourhood; retained terrain not changed'};
 const halo={inputId:outside.inputId,bounds:[bounds[0],bounds[1],bounds[0]+.01,bounds[1]+.01],scopeKnown:true,description:'Synthetic notification inside actual read footprint, outside output point; no physical change asserted'};
 const spatialAssessments=results.filter(r=>proof.assess(r,results,roots,selections.after[r.probe],'current-applicable-terrain-v1',[],methodRevision).status==='fresh').map(r=>({result:{id:r.claim.id,revision:r.claim.revision},probe:r.probe,property:r.property,outside:proof.assess(r,results,roots,selections.after[r.probe],'current-applicable-terrain-v1',[outside],methodRevision),halo:proof.assess(r,results,roots,selections.after[r.probe],'current-applicable-terrain-v1',[halo],methodRevision)}));
 const sliceIssues=proof.validateSlice(results,roots);if(sliceIssues.length)throw new Error('Dependency receipt validation: '+sliceIssues.join('; '));
 const evidence=proof.bundle(results,roots,geometry.probes[0]);const issues=validateSemanticEvidence(evidence);
 if(issues.length) throw new Error('Contract v1 validation: '+issues.join('; '));
 const unavailable=selectTerrain(regional,{...request(geometry.probes[1]),provenanceRequirement:'spatial-contributors'});
 const semanticPath='docs/atlas/semantic-comparison-results.json';const semantic=read(semanticPath);
 const output={proof:plan.id,startingCheckpoint:plan.startingCheckpoint,planSha256:sha(planPath),inputSnapshotSha256:sha(inputPath),methodRevision,methodFiles,selections,results:results.map(r=>({question:r.question,probe:r.probe,property:r.property,claim:{id:r.claim.id,revision:r.claim.revision},value:r.claim.result,receipt:r.receipt})),assessments,currentResults,recomputed,spatialNotifications:{outside,halo},spatialAssessments,evidence,
   unknown:{exposure:evidence.collections.at(-1).claims[0],terrainWithSpatialContributorRequirement:unavailable},
   retainedNativeContext:{source:{href:semanticPath,sha256:sha(semanticPath)},patch:'summit',bounds:semantic.sites.tryfan.regions.summit.bounds,worldcoverNativeCellCounts:semantic.sites.tryfan.regions.summit.worldcover,qualification:'Retained 2021 classification counts over original400m patch, not source-derived exposure fractions or labels at the derivative point.'},
   validation:{dependencyReceiptIssues:sliceIssues,semanticContractIssues:issues,historicalReplay:before.every(r=>{const root=roots.find(x=>x.probe===r.probe&&x.family===selections.before[r.probe].family);return proof.canonical(proof.derive(geometry.probes.find(p=>p.id===r.probe),root,methodRevision)[r.property==='slope'?0:1])===proof.canonical(r);}),identityContinuity:results.filter(r=>r.probe==='summit'&&r.property==='slope').map(r=>({question:r.question,id:r.claim.id,revision:r.claim.revision,artifact:r.receipt.artifact.sha256}))}};
 const outPath='docs/research/tryfan-qualified-query-results.json';const bytes=dump(output);
 if(checkOnly){if(!existsSync(outPath)||readFileSync(outPath,'utf8')!==bytes)throw new Error('Deterministic proof output drift');}
 else writeFileSync(outPath,bytes);
 const external=join(data,'derived/atlas/tryfan/qualified-query-proof-v1');mkdirSync(external,{recursive:true});
 const materialized=join(external,'result-'+sha(outPath)+'.json');
 if(!existsSync(materialized))writeFileSync(materialized,bytes);else if(readFileSync(materialized,'utf8')!==bytes)throw new Error('Content-addressed artifact collision');
 if(proof.canonical(read(materialized))!==proof.canonical(output))throw new Error('Serialization/reload changed qualified answers');
 console.log(JSON.stringify({mode:checkOnly?'deterministic-check':'run',outputSha256:sha(outPath),claims:results.length,recomputed:recomputed.length,selected:selections.after,historicalReplay:output.validation.historicalReplay,semanticIssues:issues,materializationBytes:Buffer.byteLength(bytes),measurement:{...sampled.measurement,totalSeconds:(performance.now()-start)/1000}},null,2));
} finally {await server.close();}
