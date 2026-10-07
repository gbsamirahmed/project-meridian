// Reuse Contract v1 and retained crosswalk/templates; no second semantic contract.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { contract, build, instantiate } from '../../../scripts/atlas/worldcover-binding-proof/runtime.mjs';
import { ROOT } from './catalogue.mjs';
import { encode, sha, requireThat } from './identity.mjs';
const ref=id=>({id,revision:'1'}),known=value=>({status:'known',value});
export { instantiate };
export async function nativeSemantics(catalogue,metadata) {
  const loaded=await contract(),validate=loaded.validate;
  // Optional TS fixture fields may be undefined; canonical JSON omits them explicitly.
  const fixtures=JSON.parse(JSON.stringify(loaded.fixtures));
  const artifacts=Object.fromEntries(['worldcover','nrw'].map(f=>[f,catalogue.artifacts.find(a=>a.uses.some(u=>u.family===f))]));
  const sources=Object.fromEntries(Object.entries(artifacts).map(([f,a])=>[f==='worldcover'?'tryfan-worldcover.tif':'nrw-vegetation-full-features.json',
    {path:a.aliases[0],sha256:a.sha256,bytes:a.bytes}]));
  // Templates are metadata, not a declaration of operational artifact availability.
  const state=build({status:'available',grid:metadata.families.worldcover.grid??{nativeCodes:[10,20,30,50,60,80,100]},sources,nrw:(metadata.families.nrw.records??[]).filter(f=>['486814','486820','486832'].includes(f.id))},fixtures);
  const n=state.bundle.collections[1],cross=JSON.parse(readFileSync(resolve(ROOT,'docs/atlas/semantic-comparison-results.json'),'utf8'));
  for(const f of metadata.families.nrw.records??[]) {
    const code=f.native.phase1_code,term=ref('nrw:'+code),legend=cross.nrwLegend[code];
    if(!state.bundle.definitions.some(d=>d.id===term.id))state.bundle.definitions.push({...term,kind:'value',
      vocabulary:{id:'Welsh Phase1 / JNCC nomenclature',version:known('retained JNCC2008 Welsh column; historical survey labels')},
      label:legend?.welshName??'Opaque native '+code,
      meaning:legend?JSON.stringify(legend)+'; source inventory meaning, not contemporaneous physical cover.':
        'Opaque retained code '+code+'; record label/attributes preserved; no new habitat definition or physical absence inferred.',
      reference:legend?{href:'docs/atlas/semantic-comparison-results.json',selector:'nrwLegend/'+code}:
        {href:sources['nrw-vegetation-full-features.json'].path,selector:'phase1_code='+code}});
    const prior=n.claims.find(c=>c.id==='claim:nrw-record-'+f.id),support={geometry:{kind:'asset',asset:{href:sources['nrw-vegetation-full-features.json'].path,sha256:artifacts.nrw.sha256,selector:'objectid='+f.id},
      crs:known({name:'EPSG:27700',identifier:'EPSG:27700'}),interpretation:'Exact retained native Voronoi feature; geometry not copied into pilot claims.'},
      meaning:'Original retained feature support, not the query patch or a physical sharp edge',grain:{status:'unknown',reason:'Converted native polygon semantic MMU and local confidence not established.'}};
    const claim=prior??{id:'claim:nrw-record-'+f.id,revision:sha(encode({native:f.native,support,time:n.context.time})),
      native:{property:ref('nrw:habitat'),term,fields:f.native},
      result:legend && code!=='NA'?{kind:'assertion',value:{kind:'category',term}}:{kind:'gap',reason:'unknown',explanation:'Opaque native '+code+'; label/attributes preserved, no new habitat assertion or physical absence.'},
      record:{href:'docs/atlas/semantic-comparison-sources.json',selector:'nrw-vegetation-full-features.json objectid='+f.id},context:{support}};
    const native=cross.nrwCrosswalk.find(m=>m.code===code);
    if(native?.concept) {
      const target=ref('fixture:common-'+native.concept.replace(/[^a-z0-9]+/g,'-'));
      if(!state.bundle.definitions.some(d=>d.id===target.id))state.bundle.definitions.push({...target,kind:'property',
        vocabulary:{id:'Meridian retained crosswalk TEST concepts',version:known('c4da565')},label:native.concept,
        meaning:'Existing small interoperability concept; never replaces native inventory meaning.',valueKinds:['category'],reference:{href:'docs/atlas/semantic-comparison-results.json',selector:'nrwCrosswalk'}});
      const id='mapping:nrw-'+code;
      if(!state.bundle.mappings.some(m=>m.id===id))state.bundle.mappings.push({...ref(id),from:term,target,
        relationship:code==='D.5'?'ambiguous':native.relation==='PARTIAL OVERLAP'?'partial':native.relation.toLowerCase(),
        method:{method:'Retained c4da565 conceptual crosswalk',record:{href:'docs/atlas/semantic-comparison-results.json',selector:'nrwCrosswalk/'+code}},
        loss:[native.loss],qualification:'Native extension relative to common target; historic habitat is not current cover. D.5 Welsh/JNCC wet/dry naming remains unresolved.'});
      if(!prior)claim.interpretation={mapping:ref(id),disposition:code==='D.5'?'unresolved':'qualified'};
    }
    if(!prior)n.claims.push(claim);
  }
  const errors=validate(state.bundle);requireThat(errors.length===0,'invalid-semantic-reference',errors.join('\n'));
  return {state,validate,artifacts};
}
export function qualified(state,claim,collectionId) {
  const collection=state.bundle.collections.find(c=>c.id===collectionId);
  const context={...structuredClone(collection.context),...structuredClone(claim.context??{})};
  const mapping=state.bundle.mappings.find(m=>m.id===claim.interpretation?.mapping.id)??state.bundle.mappings.find(m=>m.from.id===claim.native.term?.id);
  const definitions=state.bundle.definitions.filter(d=>d.id===claim.native.property.id || d.id===claim.native.term?.id || d.id===mapping?.target.id);
  return {claim,context,definitions,...(mapping?{mapping,interpretation:claim.interpretation??{mapping:ref(mapping.id),disposition:'qualified'}}:{commonInterpretation:{kind:'gap',reason:'unsupported',explanation:'No established common mapping for this native value.'}})};
}
