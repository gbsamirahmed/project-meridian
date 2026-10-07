// Bounded research resolver. GIS and semantic declarations retain separate responsibilities.
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {resolve,join} from 'node:path';
import {contract} from '../worldcover-binding-proof/runtime.mjs';
import {encode,sha,publish,load} from '../local-persistent-proof/store.mjs';
export {contract,encode,sha,publish,load};
export const ROOT=resolve(import.meta.dirname,'../../..');
export const PYTHON=resolve(ROOT,'../meridian-data/earth-lab/.venv/Scripts/python.exe');
export const MATRIX=JSON.parse(readFileSync(join(import.meta.dirname,'matrix.json'),'utf8'));
export const SCHEMA='exe-qualified-water-proof/v1';
const claimRef=c=>({id:c.id,revision:c.revision});
const ref=id=>({id,revision:'1'}),known=value=>({status:'known',value});
const asset=(href,selector)=>({href,...(selector?{selector}:{})});
const receipt='docs/atlas/water-check-sources.json';
const families={wfd:'wfd-exe',phi:'priority-habitat',flood:'ea-flood-zones',rfo:'ea-recorded-floods'};
const props={wfd:'wfd:membership',phi:'phi:habitat',flood:'ea:zone',rfo:'ea:recorded-extent'};
const limitation='Retained source proposition only; no current water, depth, discharge, tide or physical absence inference. Grain/quality and epochs differ.';
const unknownTime=reason=>({kind:'unknown',reason});
const support=(path,selector,meaning,crs='EPSG:27700')=>({geometry:{kind:'asset',asset:asset(path,selector),crs:known({name:crs,identifier:crs}),interpretation:meaning},meaning,grain:known(crs==='EPSG:4326'?'Native0.00025degree cell assignment; nominal Landsat30m; mixed support, not independent homogeneous ground.':'Original native source polygon; simplified/reference/inventory grain is not positional accuracy; local precision unknown.')});
export function reader(){
 const r=spawnSync(PYTHON,[join(import.meta.dirname,'reader.py')],{cwd:ROOT,encoding:'utf8',maxBuffer:12000000,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
 if(r.status!==0)throw new Error('Retained GIS adapter failed: '+r.stderr);
 return JSON.parse(r.stdout);
}
function resource(id,revision,rights,dates=[]){
 const source={kind:'source',id:id+'-source',revision:known('retained-source-2026-10-06')};
 const product={kind:'product',id,revision:known(revision)};
 const terms={licence:known(rights.licence),attribution:[rights.attribution],references:[receipt],limitations:'Retained notices govern reuse; no new clearance or confidence.'};
 return [{ref:source,domain:'semantics',name:id+' source',definition:asset(receipt),rights:terms,inputs:[]},{ref:product,domain:'semantics',name:id+' retained revision',definition:asset(receipt),rights:terms,inputs:[source],dates}];
}
export function build(raw,fixtures){
 const definitions=JSON.parse(encode(fixtures.definitions.filter(d=>/^(wfd|jrc|phi|ea|condition):/.test(d.id)))),resources=[],collections=[];
 const define=(id,kind,label,meaning,valueKinds)=>{
  if(!definitions.some(d=>d.id===id))definitions.push({...ref(id),kind,label,meaning,vocabulary:{id:id.split(':')[0]+' retained native definitions',version:known('Exe retained2026-10-06/proof1')},reference:asset('docs/atlas/water-feature-state-check.md'),...(valueKinds?{valueKinds}:{})});return ref(id);
 };
 for(const [k,id] of Object.entries(families)){
  const source=raw.sources[k+'.geojson'];const right=raw.rights[{wfd:'WFD',phi:'PHI',flood:'Flood Zones',rfo:'RFO'}[k]];
  const dates=[{role:'retrieval',extent:{kind:'instant',value:source.retrievedUtc,precision:'second',basis:'Retained acquisition receipt; not physical observation.'}}];
  if(k==='wfd')dates.push({role:'publication',extent:{kind:'epoch',value:'2025-06-23',precision:'day',basis:'Retained catalogue publication, distinct from classification2019/export2024.'}});
  resources.push(...resource(id,source.sha256,right,dates));const product=resources.at(-1).ref;
  const context={support:support(source.path,'retained feature assignments','Collection support domain; individual native feature selector overrides'),time:[{role:'nominal-epoch',extent:unknownTime('Source release is not claim-local observation or validity.')}],evidence:{modes:k==='flood'?['scenario']:k==='rfo'?['event-record']:['survey-inventory'],description:right.nativeVersion,inputs:[{kind:'resource',ref:product,role:'source-native product'}],completeness:'partial',limitations:limitation,processing:[]}};
  if(k==='wfd')context.conditions=[{definition:ref('condition:MHW'),native:{convention:'Mean High Water-derived mapping'},qualification:'Simplified reference unit, not instantaneous edge. Numeric tide/level/datum details unknown.'}];
  if(k==='flood')context.conditions=[{definition:ref('condition:planning-AEP'),native:{defences:'benefit ignored'},qualification:'Present-day planning convention; source model vintages/physical local levels unknown.'}];
  const claims=[];
  for(const p of raw.records[k]){
   const f={namespace:product,id:String(k==='wfd'?p.water_body_id:k==='phi'?p.uid:k==='rfo'?p.rec_out_id:p.featureId),kind:k==='wfd'?'feature':'inventory-object'};
   const ctx={support:support(source.path,'featureId='+p.featureId,'Original source feature support, not query footprint or current wetted extent')};
   let values;
   if(k==='wfd'){
    values=[{kind:'membership',feature:f}];ctx.time=[{role:'nominal-epoch',extent:{kind:'epoch',value:String(p.classification_year),precision:'year',basis:'WFD classification year; membership reference convention not asserted 2019 survey or current hydraulic state.'}}];
   }else if(k==='phi'){
    const codes=String(p.habcodes).split(',').map(s=>s.trim()).filter(Boolean);
    const years=[...new Set(String(p.primsource).match(/\b(?:19|20)\d{2}\b/g)||[])];
    ctx.time=[{role:'survey',extent:unknownTime('Exact local survey/validity unknown; primsource retains contributor vintages, not contemporaneous pixel labels.')},...years.map(y=>({role:'nominal-epoch',extent:{kind:'epoch',value:y,precision:'year',basis:'Year token in native contributor description; no exact survey/validity or component equivalence inferred.'}}))];
    values=codes.map(code=>({kind:'category',term:define('phi:'+code,'value',code,'Native PHI component; original mainhabs/habcodes/primsource retained, no fractional dominance or current open-water assertion.')}));
   }else if(k==='flood'){
    values=[{kind:'category',term:define('ea:'+p.flood_zone,'value',p.flood_zone,p.flood_zone==='FZ2'?'Annual river0.1-1% /sea0.1-0.5%, planning category under ignored-defence convention.':'Annual river>=1% /sea>=0.5%, planning category under ignored-defence convention.')}];
    ctx.conditions=[{definition:ref('condition:planning-AEP'),native:{flood_zone:p.flood_zone,flood_source:p.flood_source,defences:'benefit ignored'},qualification:'Source annual probability category, not local pixel probability or observed inundation; exact sub-model vintage unknown.'}];
    const modes=['scenario'];if(String(p.origin).includes('modelled'))modes.push('model');if(String(p.origin).includes('recorded'))modes.push('event-record');
    ctx.evidence={...context.evidence,modes,description:'Native Origin='+p.origin+'; mixed provenance retained, not pure observation.'};
   }else{
    values=[{kind:'membership',feature:f}];
    const valid=p.start_date&&p.end_date&&!p.start_date.startsWith('2050')&&!p.end_date.startsWith('2050');
    ctx.time=[{role:'event',extent:valid?{kind:'interval',start:p.start_date.slice(0,10),end:p.end_date.slice(0,10),precision:'day',basis:'Published event interval; raw midnight timestamps retained, exact inundation time at this point unknown.'}:unknownTime('Missing or sentinel event dates; native fields retained.')}];
    if(p.data_qual)ctx.quality=[{kind:'survey',scope:{kind:'claim',description:'Published recorded outline quality, not current flood confidence.'},metric:'Native data_qual',meaning:'Boundary/evidence record qualification',value:{kind:'label',label:p.data_qual},reference:asset(source.path,'rec_out_id='+p.rec_out_id)}];
   }
   for(const [n,value] of values.entries()){
    const effective=structuredClone(ctx);
    if(k==='phi'){
     const code=value.term.id.slice(4);const matched=[...String(p.primsource).matchAll(/\b((?:19|20)\d{2})\s*\(([A-Z, ]+)\)/g)].filter(m=>m[2].split(',').map(s=>s.trim()).includes(code));
     if(matched.length)effective.time=[ctx.time[0],...matched.map(m=>({role:'nominal-epoch',extent:{kind:'epoch',value:m[1],precision:'year',basis:'Published contributor vintage for native '+code+' explicitly associated in primsource; not exact survey or current validity.'}}))];
    }
    claims.push({...ref('claim:'+k+':'+f.id+':'+(k==='phi'?value.term.id.slice(4):n)),revision:source.sha256,native:{property:ref(props[k]),...(value.kind==='category'?{term:value.term}:{}),fields:p},result:{kind:'assertion',value},feature:f,...(k==='rfo'?{associations:[{namespace:product,id:String(p.rec_grp_id),kind:'event'}]}:{}),context:effective,record:asset(source.path,'featureId='+p.featureId)});
   }
  }
  collections.push({...ref('collection:'+k),revision:source.sha256,product,representation:'vector',context,claims});
 }
 for(const month of ['2024-03','2024-09']){
  const source=raw.sources['monthly-'+month+'.tif'];resources.push(...resource('jrc-monthly-'+month,source.sha256,raw.rights.GSW));const product=resources.at(-1).ref;
  const context={support:support(source.path,'native time/code assignment','Template domain, not blanket assertion','EPSG:4326'),time:[{role:'observation',extent:{kind:'interval',start:month+'-01',end:month+(month.endsWith('03')?'-31':'-30'),precision:'day',basis:'Monthly2024 bin, exact supporting Landsat exposure times/tides unknown.'}}],evidence:{modes:['classification','detection'],description:'GSWv1.5 native monthly history codes0/1/2',inputs:[{kind:'resource',ref:product,role:'observation-derived monthly classification'}],completeness:'partial',limitations:'No valid observation is code0; non-detection is not physical absence. Monthly support/acquisitions differ; no depth/tide/current state or local confidence.',processing:[]}};
  const claims=[0,1,2].map(code=>({...ref('template:'+month+':'+code),revision:source.sha256,native:{property:ref('jrc:detection'),fields:{month,code}},result:code===0?{kind:'gap',reason:'no-observation',explanation:'Native0=no observations, not physical absence.'}:{kind:'assertion',value:{kind:'detection',outcome:code===2?'detected':'not-detected',target:'water'}},record:asset(source.path,'native code='+code)}));
  collections.push({...ref('collection:'+month),revision:source.sha256,product,representation:'raster',context,claims,binding:{asset:{href:source.path,sha256:source.sha256},assignment:'Month selects product; native cell code selects template; bind actual cell or selected support without resampling.',codes:claims.map(q=>({code:q.native.fields.code,claim:claimRef(q)}))}});
 }
 define('proof:comparison','property','Observation support comparison','Paired native monthly assignments; no physical change inference.',['descriptor']);
 return {schema:SCHEMA,bundle:{contract:'atlas-semantic-evidence/v1',definitions,resources,collections,mappings:[]},sources:raw.sources,grid:raw.grid,matrixSha256:raw.matrixSha256,method:{id:'exe-property-scoped-resolution',revision:sha(readFileSync(new URL(import.meta.url))),readerRevision:sha(readFileSync(join(import.meta.dirname,'reader.py')))},noCurrentStateInference:true};
}
export function check(state,validate){
 if(state.schema!==SCHEMA)throw new Error('Unknown proof schema');const errors=validate(state.bundle);if(errors.length)throw new Error(errors.join('\n'));
 if(state.matrixSha256!==sha(readFileSync(join(import.meta.dirname,'matrix.json'))))throw new Error('Matrix revision mismatch');
 for(const c of state.bundle.collections)if(c.product.revision.status!=='known')throw new Error('Missing exact product revision');
}
export const gap=(reason,explanation)=>({kind:'gap',reason,explanation});
function use(state,c,q){return {dependency:c.product,role:'source-native '+q.kind+' evidence',actualInputUse:{crs:MATRIX.crs,...(q.point?{point:q.point}:{bounds:q.bounds}),selection:q.kind==='feature'?'Native WFD reference feature intersect study; exact selector in evidence':'Point-containing cell/native polygon or native cell centres inside requested support'},temporalScope:c.context.time,method:state.method};}
export function resolveQuery(state,raw,q){
 const f=raw.facts[q.id];if(!f)throw new Error('No declared GIS facts for query');
 const base={id:q.id,question:q.kind,request:q};
 if(f.outside)return {...base,result:gap('outside-support','Outside frozen retained study; excess returned geometry does not expand proof support.')};
 const collection=k=>state.bundle.collections.find(c=>c.id==='collection:'+k);
 function vector(k){
  const c=collection(k);const hits=new Map(f.hits[k].map(h=>[h.id,h]));let claims=c.claims.filter(c=>hits.has(c.native.fields.featureId));
  if(q.requiredMode){claims=claims.filter(t=>(t.context?.evidence||c.context.evidence).modes.includes(q.requiredMode));}
  if(q.requiredMode&&!claims.length)return {result:gap('unsupported','Requested evidence mode cannot be supplied by this planning product.'),claims:[],rejectedFallback:k};
  if(q.condition&&q.condition!=='planning-AEP')return {result:gap('unsupported','Planning reference is incompatible with requested observed level.'),claims:[]};
  if(q.time)return {result:gap('unknown','Inventory contributor vintages do not establish validity at the requested date.'),claims:[],availableHistoricalClaims:claims.map(claimRef)};
  if(q.interval)claims=claims.filter(c=>c.context.time.some(t=>t.role==='event'&&t.extent.kind==='interval'&&t.extent.start<=q.interval[1]&&t.extent.end>=q.interval[0]));
  return {result:claims.length?{kind:'assertion',value:{kind:'descriptor',text:'Retained native evidence applies; separate source meanings remain.'}}:gap('missing-inventory','No matching retained inventory/event entry; not physical absence or proof no historic flood.'),claims:claims.map(c=>({...claimRef(c),relation:hits.get(c.native.fields.featureId)})),dependencies:[use(state,c,q)]};
 }
 function monthly(month){
  const c=collection(month);
  if(!c)return {result:gap('unsupported','Requested month not retained; no inferred state between periods.'),claims:[]};
  if(q.unavailable?.includes('monthly-'+month))return {availability:'unavailable',reason:'Controlled retained observation access failure; not a physical gap/no-observation code.',rejectedFallbacks:['wfd','phi','flood','rfo'],otherEvidenceExists:Object.values(f.hits).some(a=>a.length>0),claims:[]};
  const cell=f.cells[month];if('code' in cell){
   const template=c.claims.find(t=>t.native.fields.code===cell.code);
   const claim={...structuredClone(template),id:'cell:'+month+':'+cell.parentRow+':'+cell.parentColumn,context:{...c.context,support:{geometry:{kind:'native-rectangle',crs:{name:'EPSG:4326',identifier:'EPSG:4326'},axisOrder:'xy',bounds:cell.bounds},meaning:'Exact native containing-cell assignment; point is not independently observed homogeneous ground.',grain:c.context.support.grain}}};
   return {result:claim.result,claim,cell,dependencies:[{...use(state,c,q),actualInputUse:{crs:'EPSG:4326',row:cell.row,column:cell.column,parentRow:cell.parentRow,parentColumn:cell.parentColumn,bounds:cell.bounds}}]};
  }
  return {result:{kind:'assertion',value:{kind:'descriptor',text:'Composition of selected native raster assignments; no physical area fractions.'}},counts:cell.counts,selectedCellCentres:cell.selectedCellCentres,templates:c.claims.map(claimRef),dependencies:[use(state,c,q)]};
 }
 if(families[q.kind])return {...base,...vector(q.kind)};
 if(q.kind==='detection')return {...base,...monthly(q.month)};
 if(q.kind==='current')return {...base,result:gap('unsupported','Retained historical detection, inventory, event and planning evidence do not establish current underwater state.'),claims:[]};
 if(q.kind==='compare'){
  const cs=q.months.map(collection);const context={support:{geometry:{kind:'native-rectangle',crs:{name:MATRIX.crs,identifier:MATRIX.crs},axisOrder:'xy',bounds:q.bounds},meaning:'Selected native cell-centre population in fixed query rectangle',grain:known('Paired native distributed cells; no continuous temporal interpolation.')},time:cs.flatMap(c=>c.context.time),evidence:{modes:['derived'],description:'Fixed paired nonzero-code comparison, no physical drying inference',inputs:cs.map(c=>({kind:'resource',ref:c.product,role:'compared monthly assignment'})),completeness:'partial',limitations:'Code0 changes observation support. Even paired code transitions cannot identify physical cause or exposure/tide comparability.',processing:[{method:state.method.id,revision:known(state.method.revision),record:asset('scripts/atlas/exe-water-query-proof/runtime.mjs')} ]}};
  const claim={...ref('comparison:'+q.id),revision:sha(encode({method:state.method,products:cs.map(c=>c.product),bounds:q.bounds})),native:{property:ref('proof:comparison'),fields:{physicalChangeSupported:false}},result:{kind:'assertion',value:{kind:'descriptor',text:'Paired classification changes only; physical change interpretation unsupported.'}},context,record:asset('scripts/atlas/exe-water-query-proof/matrix.json','id='+q.id)};
  return {...base,result:claim.result,claim,comparison:f.pair,allSelectedCellsObservedInBothMonths:f.pair.anyUnobserved===0,physicalChangeSupported:false,dependencies:cs.map(c=>use(state,c,q))};
 }
 if(q.kind==='coexist')return {...base,evidence:Object.fromEntries(Object.keys(families).map(k=>[k,vector(k)])),observations:Object.fromEntries(['2024-03','2024-09'].map(m=>[m,monthly(m)])),noUniversalWinner:true};
 if(q.kind==='feature'){
  const c=collection('wfd'),target=c.claims.find(t=>t.feature.id===q.feature);
  if(!target)return {...base,result:gap('not-applicable','Requested source-native feature is not a retained WFD identity; no inferred matching.')};
  return {...base,feature:target.feature,featureClaim:claimRef(target),association:'Spatial intersection within native WFD reference unit AND study, not identity equivalence or water state.',evidence:Object.fromEntries(Object.keys(families).map(k=>[k,vector(k)])),observations:Object.fromEntries(['2024-03','2024-09'].map(m=>[m,monthly(m)]))};
 }
 throw new Error('Unknown bounded query kind');
}
export function evaluate(state,raw){
 for(const [n,s] of Object.entries(state.sources))if(raw.sources[n]?.sha256!==s.sha256)throw new Error('Recovered evidence reference mismatch: '+n);
 return MATRIX.queries.map(q=>resolveQuery(state,raw,q));
}
