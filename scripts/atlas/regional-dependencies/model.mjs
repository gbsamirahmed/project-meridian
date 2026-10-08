// Finite retained regional dependency/use model. No scheduler or production runtime.
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {join} from 'node:path';
import {createServer} from 'vite';
import {encode,sha,requireThat} from '../../../pilots/atlas/tryfan/identity.mjs';
import {METHOD} from '../../../pilots/atlas/tryfan/dependencies.mjs';
import {DATA,ROOT} from '../../../pilots/atlas/tryfan/catalogue.mjs';
export const H=import.meta.dirname,plan=JSON.parse(fs.readFileSync(join(H,'plan.json'),'utf8'));
export const digest=v=>sha(encode(v));
const clone=structuredClone;
const need=(v,m)=>requireThat(v,'regional-dependency-invalid',m);
export const intersects=(a,b)=>a[0]<b[2]&&b[0]<a[2]&&a[1]<b[3]&&b[1]<a[3];
export function python(payload){const t=performance.now(),p=spawnSync(join(DATA,'earth-lab/.venv/Scripts/python.exe'),[join(H,'sample.py')],{input:JSON.stringify(payload),cwd:ROOT,encoding:'utf8',maxBuffer:32*1024*1024,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONIOENCODING:'utf-8',PROJ_NETWORK:'OFF'}});need(p.status===0,p.stderr||p.error?.message||'Native sampling failed');return {...JSON.parse(p.stdout),processMilliseconds:performance.now()-t};}
let scientific;
export async function methods(){
 if(scientific)return scientific;
 need(sha(fs.readFileSync(join(ROOT,plan.methods.terrainFile)))===plan.methods.terrainFileSha256,'Frozen terrain method changed');
 need(sha(fs.readFileSync(join(ROOT,plan.methods.nativeCountFile)))===plan.methods.nativeCountFileSha256,'Native categorical method changed');
 const server=await createServer({configFile:false,root:ROOT,appType:'custom',logLevel:'silent',server:{middlewareMode:true,hmr:false}});
 try {const m=await server.ssrLoadModule('/scripts/atlas/qualified-query-proof/proof.ts'),s=await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');scientific={horn:m.hornSlope,ratio:m.areaRatio,semantic:s.validateSemanticEvidence};return scientific;}finally{await server.close();}
}
export const revisions={'slope':METHOD,'area-ratio':METHOD,'counts':plan.methods.nativeCountFileSha256};
export const methodNames={'slope':'Horn-3x3-grid-slope','area-ratio':'planar-area-ratio-from-slope','counts':'native-classification-cell-centre-counts'};
export function initialContexts(base,description){
 const input=JSON.parse(fs.readFileSync(join(ROOT,'docs/research/tryfan-qualified-query-inputs.json'),'utf8')),u=base.understanding;
 const active=u.results.filter(r=>r.property==='slope'&&u.active.some(a=>a.id===r.claim.id&&a.revision===r.claim.revision));
 const sources={};const tasks=[];
 for(const r of active){const root=input.roots.find(x=>'retained-input:'+x.id===r.receipt.inputs[0].id),family=root.family==='welsh-regional'?'terrain-regional':'terrain-common',f=base.catalogue.families.find(a=>a.id===family);need(f,'Missing native Tryfan family');
  sources['tryfan:'+root.id]={region:'tryfan',family:'terrain',root:{...root,heightSamplesM:undefined},qualification:{meaning:'Accepted represented heightfield, not verified bare-earth truth',vertical:'unknown native height reference',time:'exact observation epoch unknown',unit:'metre represented height samples / BNG grid metres'},rights:f.nativeMetadata.product.rights};delete sources['tryfan:'+root.id].root.heightSamplesM;
  tasks.push({id:'tryfan-'+r.probe,probe:r.probe,kind:'terrain',region:'tryfan',point:input.geometry.probes.find(p=>p.id===r.probe).centre,source:'tryfan:'+root.id,origin:{acceptedClaim:r.claim.id,acceptedRevision:r.claim.revision,receipt:r.receipt}});
 }
 return {tryfan:{schema:'atlas-regional-dependency-context/v1',region:'tryfan',sources,tasks,notes:[],parameters:{},expectedMethods:clone(revisions),adminRevision:0},riffelhorn:{schema:'atlas-regional-dependency-context/v1',region:'riffelhorn',sources:description.registry,tasks:[...plan.sampling.probes.map(p=>({...p,region:'riffelhorn',kind:'terrain'})),...plan.sampling.areas.map(p=>({...p,region:'riffelhorn',kind:'counts'}))],notes:[],parameters:{},expectedMethods:clone(revisions),adminRevision:0}};
}
export function empty(region){return {schema:'atlas-regional-derived/v1',region,uses:{},results:{},active:{}};}
export function actualIntersection(bounds,use){return use.cells?use.cells.some(c=>intersects(bounds,[c.x-.25,c.y-.25,c.x+.25,c.y+.25])):intersects(bounds,use.scope.bounds);}
export function projection(ctx,use){const source=ctx.sources[use.key];need(source,'Missing upstream evidence identity');return {source:digest(source),scope:use.scope,notes:ctx.notes.filter(n=>n.key===use.key&&n.bounds&&actualIntersection(n.bounds,use))};}
function useNode(ctx,u){const body={...clone(u),qualification:projection(ctx,u)};return {id:digest(body),...body};}
const qid=(task,property)=>task.id+'|'+property;
function makeResult(task,property,value,inputs,uses,ctx,row){
 const roots=uses.map(u=>ctx.sources[u.key]),qualification={sources:roots,notes:uses.flatMap(u=>u.qualification.notes),meaning:property==='counts'?'Counts of classified native cell centres, not fractional physical cover/confidence':property==='slope'?'Local represented-heightfield slope from finite native/accepted stencil, not physical accuracy or traversability':'Local planar represented-surface/map-plane ratio from exact slope, not true rough-surface area',physicalTime:property==='counts'?{kind:'epoch',value:'2021',precision:'year',basis:'nominal2021v200; not exact cell observation date'}:{kind:'unknown',reason:'Exact source stencil observation epoch unknown; product date is not observation'},knowledgeTime:'Publication context, not physical change; scoped notes are explicitly administrative'};
 const body={id:qid(task,property),task:task.id,region:task.region,property,method:methodNames[property],methodRevision:revisions[property],parameters:{stride:row.stride??1,spacingM:row.spacing??null,sampling:task.region==='tryfan'?'accepted bilinear Terrarium 8m analysis grid':property==='counts'?'exact native cell-centre mask':'exact native cell-centre stencil; stride2 is declared subsampling'},inputs,support:task.kind==='counts'?{crs:'EPSG:2056',bounds:task.area,meaning:'qualified query support; counted centres in transformed native polygon'}:{crs:task.region==='tryfan'?'EPSG:27700':'EPSG:2056',point:task.point,meaning:'local derivative; not homogeneous patch'},value,qualification,...(row.origin?{acceptedOrigin:row.origin}:{})};
 return {...body,revision:digest(body)};
}
export async function recompute(ctx,old,{full=false}={}){
 const t=performance.now(),m=await methods();validate(ctx,old,{complete:false});const counters={resultsConsidered:0,relationshipsInspected:0,inputUsesInspected:0,noteRecordsInspected:0};const statuses=assess(ctx,old,{counters}),affected=full?ctx.tasks:ctx.tasks.filter(t=>Object.values(statuses).some(s=>s.task===t.id&&s.status!=='fresh'));
 need(!Object.values(statuses).some(s=>s.status==='indeterminate'),'Indeterminate input scope cannot be recomputed/published');
 const next=clone(old),swiss=affected.filter(t=>t.region==='riffelhorn').map(t=>({id:t.id,kind:t.kind,stride:ctx.parameters[t.id]??1}));let sampled=null,tryfan=null,rows=[];
 if(swiss.length){sampled=python({tasks:swiss});rows.push(...sampled.rows);}
 const local=affected.filter(t=>t.region==='tryfan');if(local.length){const start=performance.now(),p=spawnSync(process.execPath,[join(H,'tryfan-worker.mjs'),JSON.stringify(local.map(t=>t.probe))],{cwd:ROOT,encoding:'utf8',maxBuffer:8*1024*1024});need(p.status===0,p.stderr||'Original Tryfan replay failed');tryfan={...JSON.parse(p.stdout),processMilliseconds:performance.now()-start};rows.push(...tryfan.rows);}
 let numericalComparisons=0;
 for(const task of affected){const row=rows.find(a=>a.id===task.id);need(row,'Required real sampling unavailable');const uses=row.uses.map(u=>useNode(ctx,u));for(const u of uses)next.uses[u.id]=u;
  const add=(property,value,inputs)=>{need(ctx.expectedMethods[property]===revisions[property],'Unsupported prospective method revision');const r=makeResult(task,property,value,inputs,uses,ctx,row);next.results[r.revision]=r;next.active[r.id]=r.revision;return r;};
  if(task.kind==='counts'){need(encode(row.value)===encode(row.oracle),'Independent count disagreement');numericalComparisons++;add('counts',row.value,uses.map(u=>({kind:'use',ref:u.id,role:'native categorical cell-centre selection'})));}
  else {const slope=m.horn(row.samples,row.spacing),ratio=m.ratio(slope);need(Math.abs(slope-row.oracle.slope)<=1e-10&&Math.abs(ratio-row.oracle['area-ratio'])<=1e-12,'Independent numeric oracle disagreement');numericalComparisons+=2;const first=add('slope',slope,uses.map(u=>({kind:'use',ref:u.id,role:'exact consumed source cells including stencil support'})));add('area-ratio',ratio,[{kind:'result',ref:first.revision,role:'exact slope angle'}]);}
 }
 validate(ctx,next);return {state:next,measurement:{milliseconds:performance.now()-t,considered:Object.keys(old.active).length,recomputed:affected.reduce((n,t)=>n+(t.kind==='terrain'?2:1),0),tasksSampled:affected.length,counters,numericalComparisons,sampling:sampled?{...sampled,rows:undefined,registry:undefined}:null,tryfan:tryfan?{processMilliseconds:tryfan.processMilliseconds,checks:tryfan.checks}:null,RSS:process.memoryUsage().rss},statuses};
}
export function assess(ctx,state,{fixed=false,counters=null}={}){
 const memo={},active=new Set(Object.values(state.active));
 function walk(revision,stack=[]){if(memo[revision])return memo[revision];need(!stack.includes(revision),'Dependency cycle');const r=state.results[revision];need(r,'Missing exact derived dependency');if(counters)counters.resultsConsidered++;let status='fresh',reason=fixed?'Exact retained dependencies remain referenceable':'Exact current inputs/method/parameters apply';
  if(!fixed&&(ctx.expectedMethods[r.property]!==r.methodRevision||(ctx.parameters[r.task]??1)!==r.parameters.stride)){status='stale';reason='Method or parameter policy differs';}
  for(const d of r.inputs){if(counters)counters.relationshipsInspected++;if(d.kind==='result'){const a=walk(d.ref,[...stack,revision]);if(a.status==='indeterminate'){status=a.status;reason=a.reason;}else if(!fixed&&(a.status==='stale'||!active.has(d.ref))&&status!=='indeterminate'){status='stale';reason='Transitive exact result dependency changed';}}
   else{const u=state.uses[d.ref];if(counters){counters.inputUsesInspected++;counters.noteRecordsInspected+=ctx.notes.length;}need(u,'Missing exact input-use snapshot');need(ctx.sources[u.key],'Missing upstream evidence');if(!fixed){if(ctx.notes.some(n=>n.key===u.key&&n.bounds===null)){status='indeterminate';reason='Unknown changed scope; no physical absence inferred';}else if(encode(u.qualification)!==encode(projection(ctx,u))&&status!=='indeterminate'){status='stale';reason='Scoped input qualification changed';}}}}
  return memo[revision]={id:r.id,task:r.task,status,reason};
 }
 for(const revision of Object.values(state.active))walk(revision);return memo;
}
export function validate(ctx,state,{complete=true}={}){
 need(ctx.schema==='atlas-regional-dependency-context/v1'&&state.schema==='atlas-regional-derived/v1'&&ctx.region===state.region,'Invalid regional schema');need(['tryfan','riffelhorn'].includes(ctx.region),'Unknown region');
 const expectedTasks=ctx.region==='riffelhorn'?[...plan.sampling.probes.map(p=>p.id),...plan.sampling.areas.map(p=>p.id)]:['tryfan-summit','tryfan-southern-observer'];need(ctx.tasks.length===expectedTasks.length&&ctx.tasks.every(t=>expectedTasks.includes(t.id)&&t.region===ctx.region),'Unsupported task/fusion');
 need(Number.isSafeInteger(ctx.adminRevision)&&ctx.adminRevision>=0&&Object.keys(ctx.parameters).every(id=>ctx.tasks.some(t=>t.id===id&&t.region==='riffelhorn'&&t.kind==='terrain')&&[1,2].includes(ctx.parameters[id])),'Unsupported parameter/context');
 for(const n of ctx.notes)need(ctx.sources[n.key]&&typeof n.description==='string'&&(n.bounds===null||Array.isArray(n.bounds)&&n.bounds.length===4&&n.bounds.every(Number.isFinite)&&n.bounds[0]<n.bounds[2]&&n.bounds[1]<n.bounds[3]),'Invalid or unknown notification scope');
 for(const [id,u]of Object.entries(state.uses)){const {id:_,...body}=u;need(id===u.id&&id===digest(body)&&ctx.sources[u.key],'Invalid input-use identity');need(u.scope.crs===(ctx.region==='tryfan'?'EPSG:27700':'EPSG:2056')&&u.scope.bounds.length===4&&u.scope.bounds.every(Number.isFinite),'Incompatible actual-use support');}
 for(const [rev,r]of Object.entries(state.results)){const {revision,...body}=r;need(rev===revision&&rev===digest(body),'Invalid derived identity');need(revisions[r.property]===r.methodRevision&&r.method===methodNames[r.property]&&[1,2].includes(r.parameters.stride),'Method/parameter mismatch');need(r.region===ctx.region&&ctx.tasks.some(t=>t.id===r.task),'Unsupported cross-source fusion');
  need(r.inputs.length>0&&r.inputs.every(d=>d.kind==='use'?Boolean(state.uses[d.ref]):d.kind==='result'&&Boolean(state.results[d.ref])),'Invalid dependency identity');
  if(r.property==='area-ratio')need(r.inputs.length===1&&r.inputs[0].kind==='result'&&state.results[r.inputs[0].ref].property==='slope'&&state.results[r.inputs[0].ref].task===r.task,'Exact slope dependency required');else need(r.inputs.every(d=>d.kind==='use'),'Source inputs required');
 }
 for(const r of Object.values(state.results))checkNumeric(ctx,state,r);
 // Check every retained version, including non-active history; hash identity cannot conceal cycles.
 const seen=new Set(),walking=new Set();function dfs(id){need(!walking.has(id),'Dependency cycle');if(seen.has(id))return;walking.add(id);for(const d of state.results[id].inputs)if(d.kind==='result')dfs(d.ref);walking.delete(id);seen.add(id);}for(const id of Object.keys(state.results))dfs(id);
 need(Object.entries(state.active).every(([id,rev])=>state.results[rev]?.id===id),'Invalid active result membership');
 if(complete){need(Object.keys(state.active).length===ctx.tasks.reduce((n,t)=>n+(t.kind==='terrain'?2:1),0),'Incomplete recomputation');need(Object.values(assess(ctx,state)).every(s=>s.status==='fresh'),'Stale or indeterminate active publication');}
 return true;
}
export function change(ctx,c){const next=clone(ctx);if(c.kind==='none')return next;if(c.kind==='admin'){next.adminRevision++;return next;}if(c.kind==='parameter'){need(next.tasks.some(t=>t.id===c.probe),'Unknown parameter task');next.parameters[c.probe]=c.stride;return next;}
 const matching=Object.entries(next.sources).filter(([key,s])=>s.family===c.family&&(c.probe?key.endsWith(':'+c.probe):true));need(matching.length,'No real matching evidence');
 for(const [key,s]of matching){let bounds=c.bounds??s.root?.actualUse.bounds;if(c.kind==='scattered'){const t=next.tasks.find(t=>t.kind==='terrain'&&s.native.bounds[0]<=t.point[0]&&t.point[0]<s.native.bounds[2]&&s.native.bounds[1]<=t.point[1]&&t.point[1]<s.native.bounds[3]);bounds=[t.point[0]-.25,t.point[1]-.25,t.point[0]+.25,t.point[1]+.25];}
  next.notes.push({key,bounds:c.kind==='unknown'?null:bounds,description:'Administrative qualification/use-policy notice '+c.id+'; bytes/physical observation unchanged'});}
 return next;}
export function expectedAffected(before,after,state){
 // Independent exhaustive per-result direct-input test plus repeated transitive closure, not assess().
 const affected=new Set();for(const [rev,r]of Object.entries(state.results)){if(!Object.values(state.active).includes(rev))continue;
  if(before.expectedMethods[r.property]!==after.expectedMethods[r.property]||(before.parameters[r.task]??1)!==(after.parameters[r.task]??1))affected.add(r.id);
  for(const d of r.inputs)if(d.kind==='use'){const u=state.uses[d.ref];const hit=n=>u.cells?u.cells.some(c=>n.bounds[0]<c.x+.25&&n.bounds[2]>c.x-.25&&n.bounds[1]<c.y+.25&&n.bounds[3]>c.y-.25):Math.max(n.bounds[0],u.scope.bounds[0])<Math.min(n.bounds[2],u.scope.bounds[2])&&Math.max(n.bounds[1],u.scope.bounds[1])<Math.min(n.bounds[3],u.scope.bounds[3]);const relevant=after.notes.filter(n=>n.key===u.key&&n.bounds!==null&&hit(n));const old=before.notes.filter(n=>n.key===u.key&&n.bounds!==null&&hit(n));if(encode(relevant)!==encode(old))affected.add(r.id);}
 }
 let more=true;while(more){more=false;for(const rev of Object.values(state.active)){const r=state.results[rev];if(r.inputs.some(d=>d.kind==='result'&&affected.has(state.results[d.ref].id))&&!affected.has(r.id)){affected.add(r.id);more=true;}}}
 return [...affected].sort();
}
export function currentContent(state){return Object.fromEntries(Object.entries(state.active).map(([id,rev])=>[id,state.results[rev]]));}
export function density(contexts,states){const nodes=new Map(),edges=[];for(const region of ['tryfan','riffelhorn']){const ctx=contexts[region],st=states[region];for(const key of Object.keys(ctx.sources))nodes.set(key,'source');for(const id of new Set(Object.values(st.active).flatMap(rev=>{const r=st.results[rev];return r.property==='area-ratio'?st.results[r.inputs[0].ref].inputs.map(d=>d.ref):r.inputs.map(d=>d.ref)}))){const u=st.uses[id];nodes.set(id,'qualified-use');edges.push([u.key,id,'source-use']);}for(const rev of Object.values(st.active)){const r=st.results[rev];nodes.set(rev,'derived-'+r.property);for(const d of r.inputs)edges.push([d.ref,rev,d.kind==='use'?'use-result':'result-result']);}}
 const incoming={},outgoing={};for(const id of nodes.keys()){incoming[id]=0;outgoing[id]=0;}for(const [a,b]of edges){incoming[b]++;outgoing[a]++;}const distribution=o=>Object.values(o).reduce((a,n)=>(a[n]=(a[n]??0)+1,a),{});return {nodes:nodes.size,byType:[...nodes.values()].reduce((a,t)=>(a[t]=(a[t]??0)+1,a),{}),edges:edges.length,edgeTypes:edges.reduce((a,e)=>(a[e[2]]=(a[e[2]]??0)+1,a),{}),fanIn:distribution(incoming),fanOut:distribution(outgoing),maximumDepth:Math.max(...[...nodes.keys()].map(function depth(id){const parents=edges.filter(e=>e[1]===id).map(e=>e[0]);return parents.length?1+Math.max(...parents.map(depth)):0;})),crossRegionEdges:0,maximumSourceFanOut:Math.max(...Object.keys(incoming).filter(k=>nodes.get(k)==='source').map(k=>outgoing[k])),edgeList:edges};}

function usesOf(state,r){return r.property==='area-ratio'?usesOf(state,state.results[r.inputs[0].ref]):r.inputs.map(d=>state.uses[d.ref]);}
function checkNumeric(ctx,state,r){
 need(scientific,'Scientific methods not initialized');const task=ctx.tasks.find(t=>t.id===r.task),uses=usesOf(state,r);let value,row={stride:r.parameters.stride,spacing:null,...(task.origin?{origin:task.origin}:{})};
 if(r.property==='counts'){need(uses.length===1&&ctx.sources[uses[0].key].family==='worldcover'&&encode(uses[0].scope.bounds)===encode(task.area),'Invalid categorical support');value=uses[0].counts;}
 else {
  let samples;
  if(ctx.region==='tryfan'){need(uses.length===1&&uses[0].key===task.source,'Incompatible Tryfan input');samples=uses[0].samples;row.spacing=ctx.sources[task.source].root.analysisSpacingM;need(encode(samples)===encode(JSON.parse(fs.readFileSync(join(ROOT,'docs/research/tryfan-qualified-query-inputs.json'),'utf8')).roots.find(a=>'tryfan:'+a.id===task.source).heightSamplesM),'Retained Tryfan samples changed');}
  else {row.spacing=.5*row.stride;const cells=uses.flatMap(u=>u.cells??[]);need(cells.length===9&&uses.every(u=>ctx.sources[u.key].family==='dtm'&&ctx.sources[u.key].unitEvidence.bandUnit==='metre'),'Incomplete/incompatible native stencil');samples=[-1,0,1].map(j=>[-1,0,1].map(i=>{const match=cells.filter(c=>c.x===task.point[0]+i*row.spacing&&c.y===task.point[1]-j*row.spacing);need(match.length===1,'Invalid actual native input cells');return match[0].value;}));}
  const slope=scientific.horn(samples,row.spacing);value=r.property==='slope'?slope:scientific.ratio(state.results[r.inputs[0].ref].value);
 }
 const rebuilt=makeResult(task,r.property,value,r.inputs,uses,ctx,row);need(encode(rebuilt)===encode(r),'Result/method/support/qualification inconsistent');
}
export function semanticBundle(ctx,state){
 const ref=(id,revision,kind='product')=>({id,revision:{status:'known',value:revision},kind});const resources=[],seen=new Set(),definitions=Object.keys(revisions).map(p=>({id:'regional-property:'+p,revision:'1',kind:'property',vocabulary:{id:'Retained regional finite physical quantities',version:{status:'known',value:'1'}},label:methodNames[p],meaning:p==='counts'?'Native categorical cell counts, not area fractions':'Qualified represented-heightfield '+p,reference:{href:'docs/research/atlas-regional-dependencies.md'},valueKinds:[p==='counts'?'descriptor':'quantity']})),collections=[];
 function add(r){const key=digest(r.ref);if(!seen.has(key)){seen.add(key);resources.push(r);}}
 for(const [key,source]of Object.entries(ctx.sources)){const provider=ref('provider:'+ctx.region+':'+source.family,digest(source.rights),'source');add({ref:provider,domain:'terrain',name:'Documented upstream provider/family '+source.family,definition:{href:'docs/research/atlas-regional-dependencies.md',selector:source.family},rights:source.rights,inputs:[]});add({ref:ref(key,digest(source)),domain:source.family==='worldcover'?'semantics':'terrain',name:'Exact retained '+key,definition:{href:'docs/research/atlas-regional-dependencies.md',selector:key},rights:source.rights,inputs:[provider]});}
 for(const u of Object.values(state.uses)){const source=ctx.sources[u.key];add({ref:ref('regional-use:'+u.id,u.id),domain:source.family==='worldcover'?'semantics':'terrain',name:'Exact scoped qualified use',definition:{href:'docs/research/atlas-regional-dependencies.md',selector:u.id},rights:source.rights,inputs:[ref(u.key,digest(source))]});}
 for(const r of Object.values(state.results)){
  const uses=usesOf(state,r),source=ctx.sources[uses[0].key],product=ref('regional-output:'+r.id,r.revision);add({ref:product,domain:'semantics',name:'Retained '+r.property,definition:{href:'docs/research/atlas-regional-dependencies.md',selector:r.revision},rights:source.rights,inputs:uses.map(u=>ref('regional-use:'+u.id,u.id))});
  const crs={name:r.support.crs,identifier:r.support.crs},geometry=r.support.point?{kind:'native-point',crs,coordinates:r.support.point}:{kind:'native-rectangle',crs,bounds:r.support.bounds,axisOrder:'xy'};
  collections.push({id:'regional-collection:'+r.id,revision:r.revision,product,representation:'records',context:{support:{geometry,meaning:r.support.meaning,grain:{status:'known',value:r.parameters.sampling+'; sampling is not accuracy'}},time:[{role:r.property==='counts'?'nominal-epoch':'observation',extent:r.qualification.physicalTime}],evidence:{modes:['derived'],description:r.qualification.meaning,inputs:r.inputs.map(d=>d.kind==='use'?{kind:'resource',ref:ref('regional-use:'+d.ref,d.ref),role:d.role}:{kind:'claim',ref:{id:'regional-claim:'+state.results[d.ref].id,revision:d.ref},role:d.role}),completeness:'complete',limitations:'Complete immediate finite inputs, unknown source uncertainty/observation epochs retained. No datum fusion/physical absence/fraction inference.',processing:[{method:r.method,revision:{status:'known',value:r.methodRevision},parameters:r.parameters,record:{href:'docs/research/atlas-regional-dependencies.md',selector:r.revision}}]}},claims:[{id:'regional-claim:'+r.id,revision:r.revision,native:{property:{id:'regional-property:'+r.property,revision:'1'},fields:{region:r.region,task:r.task,quantity:r.property}},result:{kind:'assertion',value:r.property==='counts'?{kind:'descriptor',text:JSON.stringify(r.value)}:{kind:'quantity',value:r.value,unit:r.property==='slope'?'degree':'m2 represented planar surface / m2 map plane'}},record:{href:'docs/research/atlas-regional-dependencies.md',selector:r.revision}}]});
 }
 return {contract:'atlas-semantic-evidence/v1',resources,definitions,mappings:[],collections};
}
export function validateSemantic(ctx,state){const issues=scientific.semantic(semanticBundle(ctx,state));need(issues.length===0,issues.join('\n'));return true;}
