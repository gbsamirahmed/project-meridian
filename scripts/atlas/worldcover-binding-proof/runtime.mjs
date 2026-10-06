import { readFileSync } from 'node:fs';
import { createServer } from 'vite';
import { spawnSync } from 'node:child_process';
import { join, resolve } from 'node:path';
import { encode, sha, publish, load } from '../local-persistent-proof/store.mjs';
export const ROOT = resolve(import.meta.dirname, '../../..');
export const PYTHON = resolve(ROOT, '../meridian-data/earth-lab/.venv/Scripts/python.exe');
export const STORE = resolve(ROOT, '../meridian-data/derived/atlas/worldcover-binding-proof-v1/store');
export const SCHEMA = 'worldcover-native-binding-proof/v1';
const json = path => JSON.parse(readFileSync(join(ROOT,path),'utf8'));
const ref = id => ({id,revision:'1'});
const known = value => ({status:'known',value});
const asset = (href, selector) => ({href, ...(selector ? {selector} : {})});
const receipt = 'docs/atlas/semantic-comparison-sources.json';
export async function contract() {
 const server=await createServer({configFile:false,appType:'custom',logLevel:'silent',root:ROOT,server:{middlewareMode:true}});
 try {return {fixtures:structuredClone((await server.ssrLoadModule('/scripts/atlas/semantic-evidence/fixtures.ts')).SEMANTIC_EVIDENCE_FIXTURES),
  validate:(await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts')).validateSemanticEvidence};}
 finally {await server.close();}
}
export function readRaster(data) {
 const r=spawnSync(PYTHON,[join(ROOT,'scripts/atlas/worldcover-binding-proof/reader.py'),...(data?['--data',data]:[])],{encoding:'utf8',cwd:ROOT,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
 if(r.status!==0)throw new Error('Retained raster adapter failed: '+r.stderr);
 return JSON.parse(r.stdout);
}
const meanings={
 10:'Tree-dominated cover, at least10% tree cover; native class can include vegetation/other cover beneath canopy.',
 20:'Woody perennial vegetation below5m, at least10% shrub cover; native annual classification.',
 30:'Herbaceous vegetation below5m and at least10% grass cover; not a specific habitat identity.',
 50:'Buildings, roads and other human-made structures; native exclusions/thresholds in PUM table3; not land use.',
 60:'Exposed soil, sand or rocks, never exceeding10% vegetation during the year; does not distinguish bedrock, scree or soil.',
 80:'Water-covered areas for more than9 months of the year; not instantaneous water edge or depth.',
 100:'Moss and lichen cover; source taxonomy/thresholds in PUM table3; not generic habitat truth.'};
export function build(reader, fixtures) {
 if(reader.status!=='available')throw new Error('Cannot publish binding without verified retained evidence');
 const wc=structuredClone(fixtures.collections.find(c=>c.id==='collection:worldcover'));
 const nrw=fixtures.collections.find(c=>c.id==='collection:nrw');
 const base=fixtures.definitions.filter(d=>['wc:cover','nrw:habitat','nrw:D.1.1'].includes(d.id));
 const definitions=structuredClone(base),mappings=[],claims=[];
 definitions.find(d=>d.id==='wc:cover').requiredModes=['classification'];
 const cross=json('docs/atlas/semantic-comparison-results.json').worldcoverCrosswalk;
 for(const code of [0,...reader.grid.nativeCodes]){
  const id='wc:'+code, term=ref(id), native=cross[code];
  definitions.push({...term,kind:'value',vocabulary:{id:'ESA WorldCover nomenclature',version:known('v200/2021 PUM2.0')},
   label:native.native,meaning:code===0?'Native no-data code; not evidence of physical absence.':meanings[code],reference:asset(receipt,'worldcover-manual.pdf PUMv2 table3')});
  const q={...ref('template:wc'+code),native:{property:ref('wc:cover'),term,fields:{code,label:native.native}},
   result:code===0?{kind:'gap',reason:'not-classified',explanation:'Source-native code0 no data; no physical absence inferred.'}:{kind:'assertion',value:{kind:'category',term}},record:asset(receipt,'tryfan-worldcover.tif native code='+code)};
  if(native.concept){
   const target=ref('fixture:common-'+native.concept.replace(/[^a-z0-9]+/g,'-'));
   if(!definitions.some(d=>d.id===target.id))definitions.push({...target,kind:'property',vocabulary:{id:'Meridian retained crosswalk TEST concepts',version:known('c4da565')},
    label:native.concept,meaning:'Small retained common interpretation, not a production ontology or per-cell physical truth.',valueKinds:['category'],reference:asset('docs/atlas/source-native-semantic-comparison.md','Small test vocabulary')});
   const m={...ref('mapping:wc'+code),from:term,target,relationship:native.relation.toLowerCase(),
    method:{method:'Retained c4da565 conceptual crosswalk',record:asset('docs/atlas/semantic-comparison-results.json','worldcoverCrosswalk/'+code)},
    loss:[code===60?'Soil/sand/rock and loose/solid distinction, actual vegetation fraction and material identity remain unknown.':
     code===80?'Annual persistence criterion and water feature identity/instantaneous state are not preserved by a broad concept.':
     'Native growth form, source thresholds, mixture and specific source class meaning are lost in the broader concept.'],
    qualification:'Native extension relative to target; compatible is qualified usability, not equivalence, accuracy or homogeneous ground.'};
   mappings.push(m);q.interpretation={mapping:ref(m.id),disposition:'qualified'};
  }
  claims.push(q);
 }
 const material=ref('fixture:substrate');
 definitions.push({...material,kind:'property',vocabulary:{id:'Meridian TEST unsupported property',version:known('1')},label:'Geological substrate',
  meaning:'Material beneath the current cover; annual cover classification cannot establish it.',valueKinds:['category'],reference:asset('docs/atlas/physical-surface-semantics.md')});
 mappings.push({...ref('mapping:wc-substrate'),from:ref('wc:cover'),target:material,relationship:'unmappable',
  method:{method:'Retained cover versus substrate distinction c4da565'},loss:['Source cover cannot establish geological substrate.'],qualification:'Reject target assertion; retain native cover evidence.'});
 wc.claims=claims;
 wc.context.time.push({role:'observation',extent:{kind:'unknown',reason:'Sentinel1/2 annual2021 source observations; exact acquisition times supporting this cell are not retained.'}});
 wc.context.evidence.description='Annual WorldCover2021 v200 classification derived from Sentinel1/2; binding reads the retained native categorical raster without inference.';
 wc.context.evidence.limitations='Per-cell acquisition lineage, local confidence, semantic MMU and exact physical composition are unavailable. Source agreement is not ground truth.';
 wc.context.support={geometry:{kind:'asset',asset:asset(receipt,'tryfan-worldcover.tif native grid assignment'),crs:known({name:'EPSG:4326',identifier:'EPSG:4326'}),interpretation:'Lazy class template; support substituted only when a native cell is assigned.'},
  meaning:'Template domain, not blanket claim over crop',grain:known('Native1/12000 degree classification grid; nominal10m; semantic MMU and local confidence unknown.')};
 wc.binding={asset:{href:reader.sources['tryfan-worldcover.tif'].path,sha256:reader.sources['tryfan-worldcover.tif'].sha256},
  assignment:'Native code selects one template; cell instance uses exact native bounds and parent grid row/column. No resampling or whole-crop assertion.',codes:claims.map(q=>({code:q.native.fields.code,claim:ref(q.id)}))};
 const n=structuredClone(nrw);n.claims=[];
 for(const f of reader.nrw){
  n.claims.push({...ref('claim:nrw-record-'+f.id),native:{property:ref('nrw:habitat'),term:ref('nrw:D.1.1'),fields:f.native},
   result:{kind:'assertion',value:{kind:'category',term:ref('nrw:D.1.1')}},record:asset(receipt,'nrw-vegetation-full-features.json objectid='+f.id),
   context:{support:{geometry:{kind:'asset',asset:asset(reader.sources['nrw-vegetation-full-features.json'].path,'objectid='+f.id),crs:known({name:'EPSG:27700',identifier:'EPSG:27700'}),interpretation:'Exact retained native Voronoi feature; geometry not copied into proof.'},
    meaning:'Original retained feature support, not the query patch or a physical sharp edge',grain:{status:'unknown',reason:'Converted native polygon semantic MMU and local confidence not established.'}}}});
 }
 n.context.time=[{role:'survey',extent:{kind:'unknown',reason:'Historic survey lineage; exact feature observation epoch not established by these retained properties.'}}];
 const bundle={contract:'atlas-semantic-evidence/v1',resources:fixtures.resources.filter(r=>['worldcover','worldcover-source','nrw-phase1','nrw-phase1-source'].includes(r.ref.id)),definitions,mappings,collections:[wc,n]};
 bundle.resources.find(r=>r.ref.id==='worldcover').dates=[{role:'publication',extent:{kind:'epoch',value:'2022',precision:'year',basis:'v200 publication year retained in source-native comparison; not observation year.'}}];
 return {schema:SCHEMA,revision:'1',bundle,raster:{representationId:'worldcover-v200-2021-N51W006-native-window',revision:reader.sources['tryfan-worldcover.tif'].sha256,
  parentWindow:[23753,10464,554,334],grid:reader.grid,sources:reader.sources},bindingRevision:'native-code-cell/v1',mappingRevision:'retained-crosswalk/c4da565-plus-qualified-binding-v1'};
}
export function checkState(state,validate){
 if(state.schema!==SCHEMA)throw new Error('Unsupported proof schema');
 const errors=validate(state.bundle);if(errors.length)throw new Error(errors.join('\n'));
 const wc=state.bundle.collections[0];
 if(wc.binding.asset.sha256!==state.raster.revision || wc.claims.some(q=>q.context))throw new Error('Invalid shared template binding');
 for(const b of wc.binding.codes){const q=wc.claims.find(q=>q.id===b.claim.id);if(q?.native.fields.code!==b.code)throw new Error('Native code binding mismatch');}
}
export function instantiate(state,point){
 const wc=state.bundle.collections[0];const b=wc.binding.codes.find(b=>b.code===point.code);
 if(!b)return {kind:'gap',reason:'not-classified',explanation:'Unbound native code; never substituted with another category.'};
 const template=wc.claims.find(q=>q.id===b.claim.id);return {...structuredClone(template),id:`claim:wc2021v200-N51W006-parent-r${point.parentRow}-c${point.parentColumn}`,
  revision:state.bindingRevision+'@'+state.raster.revision,context:{...structuredClone(wc.context),support:{
   geometry:{kind:'native-rectangle',crs:{name:'EPSG:4326',identifier:'EPSG:4326'},bounds:point.cellBounds,axisOrder:'xy'},
   meaning:'Whole native classified cell assignment, not independently observed homogeneous ground',grain:wc.context.support.grain}}};
}
export function answer(state,reader,probe,{property='native',time='2021'}={}){
 if(reader.status!=='available')return {kind:'unavailable',reason:reader.reason,explanation:'Infrastructure availability, not a physical evidence gap.'};
 if(probe==='outside')return {...reader.outside,explanation:'Geographic query falls outside retained raster support; no physical absence asserted.'};
 const point=reader.points.find(p=>p.id===probe);
 if(!point)return {kind:'gap',reason:'unsupported',explanation:'This bounded harness does not register the requested probe; this is not a physical absence claim.'};
 const claim=instantiate(state,point);
 const result={query:{probe,property,time},native:claim,template:ref('template:wc'+point.code),raster:{representationId:state.raster.representationId,revision:state.raster.revision,bindingRevision:state.bindingRevision,product:state.bundle.collections[0].product},
  limitation:'Historical annual classification; no local confidence or homogeneous physical cover claim.'};
 if(time!=='2021')return {...result,kind:'gap',reason:'unsupported',explanation:'2021 annual classification cannot answer current or other-year surface state.'};
 if(property==='substrate')return {...result,kind:'unresolved',interpretation:{mapping:ref('mapping:wc-substrate'),disposition:'rejected'},
  mapping:state.bundle.mappings.find(m=>m.id==='mapping:wc-substrate'),reason:'unsupported-property'};
 if(property==='common'){
  const mapping=state.bundle.mappings.find(m=>m.id===claim.interpretation?.mapping.id);
  return {...result,kind:mapping?'qualified-interpretation':'unresolved',...(mapping?{mapping}:{reason:'no-defensible-common-mapping'})};
 }
 return {...result,kind:claim.result.kind};
}
export function logicalQueries(state,reader){
 return {raster:state.raster,resources:state.bundle.resources,definitions:state.bundle.definitions,points:reader.points.map(p=>answer(state,reader,p.id)),common:reader.points.map(p=>answer(state,reader,p.id,{property:'common'})),
  supports:reader.supports.map(s=>({...s,collection:ref('collection:worldcover'),bindingRevision:state.bindingRevision,
   rasterRevision:state.raster.revision,time:state.bundle.collections[0].context.time,evidence:state.bundle.collections[0].context.evidence,
   quality:state.bundle.collections[0].context.quality,assignments:Object.entries(s.counts).map(([code,count])=>{
    const template=state.bundle.collections[0].claims.find(q=>q.native.fields.code===Number(code));
    return {code:Number(code),count,native:template.native,result:template.result,interpretation:template.interpretation,
     mapping:state.bundle.mappings.find(m=>m.id===template.interpretation?.mapping.id)};})})),coexistence:{worldcover:answer(state,reader,'summit'),nrw:state.bundle.collections[1],
   nativeFeatureIntersections:reader.nrw.map(f=>({id:f.id,pointContains:f.pointContains,summitOverlapM2:f.summitOverlapM2})),decision:'Multiple native claims; no truth winner or simultaneity asserted.'},
  current:answer(state,reader,'summit',{time:'2026'}),unmappable:answer(state,reader,'summit',{property:'substrate'}),
  outside:answer(state,reader,'outside'),unavailable:answer(state,{status:'unavailable',reason:'retained-data-unavailable'},'summit')};
}
export { encode, sha, publish, load };
