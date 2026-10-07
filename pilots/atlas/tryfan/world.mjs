// S3 finite generation-pinned coordinator, not a universal query language or service.
import { openEvidence } from './query.mjs';
import { openUnderstanding } from './derivations.mjs';
import { load,STORE } from './generations.mjs';
import { DATA } from './catalogue.mjs';
import { requireThat } from './identity.mjs';
const questions=['terrain-selection','derived-slope','derived-area-ratio','worldcover-native','nrw-native','appearance'];
const gap=(reason,explanation)=>({kind:'gap',reason,explanation});
export async function openWorld(options={}) {
 const snapshot=load(options.store??STORE,{generation:options.generation,dataRoot:options.dataRoot??DATA,locators:options.locators,verify:false});
 const pinned={...options,generation:snapshot.generation},native=await openEvidence(pinned);let derived;
 try{derived=await openUnderstanding(pinned);}catch(e){native.close();throw e;}
 const state=derived.inspect().state;
 async function query(request) {
  requireThat(request && typeof request==='object' && !Array.isArray(request) && Object.keys(request).every(k=>['property','place','time','policy','evidence','resultRef'].includes(k)),'invalid-request','Finite pilot envelope required');
  const {property,place,time=null,policy='current-applicable-terrain-v1',evidence,resultRef}=request;
  requireThat(place && !Array.isArray(place) && Object.keys(place).every(k=>['crs','point','bounds'].includes(k)) && typeof property==='string' && property.length && (time===null||typeof time==='string'),'invalid-request','Explicit place/property/time required');
  requireThat(['EPSG:27700','OGC:CRS84'].includes(place.crs),'invalid-crs','Explicit EPSG:27700 or CRS84 xy required');
  requireThat(['current-applicable-terrain-v1','fixed-input-replay-v1'].includes(policy),'invalid-policy','Unknown policy');
  requireThat(!evidence||['terrain','worldcover','nrw','appearance'].includes(evidence),'invalid-request','Unknown evidence restriction');
  if(resultRef)requireThat(Object.keys(resultRef).sort().join(',')==='id,revision' && typeof resultRef.id==='string' && typeof resultRef.revision==='string' && property==='historical-derived','invalid-reference','Exact ref only applies to historical-derived');
  requireThat(!place.bounds||Array.isArray(place.bounds)&&place.bounds.length===4&&place.bounds.every(Number.isFinite),'invalid-support','Finite rectangular support required');
  requireThat(!(place.bounds && place.point) && (!place.bounds||place.crs==='EPSG:27700'),'invalid-support','One point or BNG rectangle only');
  const point=place.point??(place.bounds?[(place.bounds[0]+place.bounds[2])/2,(place.bounds[1]+place.bounds[3])/2]:undefined);
  const location=await native.query({point,crs:place.crs,property:'s3-location-context',...(place.bounds?{support:place.bounds}:{})});
  const base={protocol:'atlas-tryfan-query/v1',generation:snapshot.generation,request:structuredClone(request),status:'available',answers:[],provenanceRefs:[],limitations:['Separate retained evidence contexts, not a canonical/current world state.']};
  if(location.result?.reason==='outside-support')return {...base,result:location.result};
  const probe=state.probes.find(p=>p.centre.every((v,i)=>v===location.location.pointBNG[i]) || place.crs==='OGC:CRS84' && p.longitudeLatitude.every((v,i)=>v===point[i]));
  if(evidence==='terrain' && !['place-evidence','terrain-selection','derived-slope','derived-area-ratio','historical-derived'].includes(property))return {...base,status:'excluded-by-context',result:gap('unsupported','Terrain evidence cannot substitute for a native semantic property.')};
  if(property==='place-evidence') {
   requireThat(!resultRef && !evidence && !place.bounds && time===null,'invalid-request','Fixed coordinator has separate native time/evidence contexts');
   const answers=[];for(const p of questions)answers.push({property:p,response:await query({property:p,place,policy})});
   return {...base,answers,provenanceRefs:[snapshot.generation],limitations:[...base.limitations,'Fixed six-question coordinator; no merged value, source winner or inferred simultaneity.']};
  }
  if(['terrain-selection','derived-slope','derived-area-ratio','historical-derived'].includes(property)) {
   if(evidence && evidence!=='terrain')return {...base,status:'excluded-by-context',result:gap('unsupported','Incompatible evidence cannot substitute for terrain-derived understanding.')};
   if(!probe||place.bounds||time!==null)return {...base,result:gap('unsupported','Only the two frozen point probes and native unknown terrain epoch are supported.')};
   if(property==='terrain-selection')return {...base,answers:[{selection:derived.inspect().selections[probe.id],scope:{selector:probe.eligibilityFootprint,scale:{scheme:'XYZ Web Mercator zoom (delivery)',requestedLevel:'z14'},eligibilityHalfWidthM:24}}],provenanceRefs:[snapshot.generation]};
   if(property==='historical-derived')requireThat(resultRef,'invalid-reference','Historical query requires exact result reference');
   const historical=resultRef?state.results.find(r=>r.claim.id===resultRef.id && r.claim.revision===resultRef.revision):null;
   if(resultRef)requireThat(historical && historical.probe===probe.id,'historical-result-missing','Exact historical result/probe unavailable');
   const answer=derived.result(probe.id,historical?.property??(property==='derived-slope'?'slope':'area-ratio'),resultRef);
   if(policy==='fixed-input-replay-v1')answer.freshness=answer.replayAssessment;
   return {...base,status:answer.status==='unavailable'?'unavailable':'available',freshness:answer.freshness,answers:[answer],provenanceRefs:[snapshot.generation,...answer.result?.receipt.inputs.map(r=>({kind:r.kind,id:r.id,revision:r.revision}))??[]]};
  }
  const response=await native.query({point,crs:place.crs,property,time,...(evidence?{family:evidence}:{}) ,...(place.bounds?{support:place.bounds}:{})});
  return {...base,status:response.operationalStatus,answers:[response],provenanceRefs:response.records.map(r=>r.provenance),...(response.result?{result:response.result}:{})};
 }
 return {generation:snapshot.generation,query:async r=>structuredClone(await query(r)),inspect:()=>derived.inspect(),replay:r=>derived.replay(r),close:async()=>{native.close();await derived.close();},metrics:{...derived.metrics,nativeInitializationMilliseconds:native.metrics.readerInitializationMilliseconds}};
}
