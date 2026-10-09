/** Repeatable real-publication queries; no fabricated physical history. */
export const sourceIdentity='dtm:c68c305e4a142da416b46b555a80916ecc52f8fa50bf1efd5cd2c3f24f9cd4bc';
export const slopeIdentity='dtm-cluster-0-0|slope',ratioIdentity='dtm-cluster-0-0|area-ratio';
export const point=[2624350.25,1091350.25];
export function queries(info){
 const rows=[{}, {evidenceClass:'source'},{evidenceClass:'derived'},{region:'tryfan'},{region:'riffelhorn'}];
 for(const identity of ['glaciers:683',sourceIdentity,slopeIdentity,ratioIdentity,'absent'])rows.push({identity});
 for(const feature of ['glaciers:683','absent'])rows.push({region:'riffelhorn',feature});
 for(const family of ['dtm','dsm','worldcover','terrain-slope','planar-area-ratio'])rows.push({families:[family]});
 for(const representation of ['vector','raster','local-scalar','source-product-metadata'])rows.push({representation});
 const spatial={region:'riffelhorn',crs:'EPSG:2056'};
 rows.push({...spatial,point},{...spatial,point,evidenceClass:'derived'},
  {...spatial,point:[2624350.5,1091350.25],evidenceClass:'derived'},
  {...spatial,point,evidenceClass:'derived',spatialSupport:'consumed'},
  {...spatial,point:[2624349.5,1091350.25],evidenceClass:'derived',spatialSupport:'consumed'},
  {...spatial,area:[2624350.25,1091350.25,2624350.75,1091350.75]},
  {...spatial,area:[2624000,1091000,2626000,1093000]}, {...spatial,point:[0,0]});
 for(const role of ['evidence-epoch','product-reference'])for(const time of [{unknown:true},{start:2015,end:2016},{start:2021,end:2021}])rows.push({time:{role,...time}});
 rows.push({evidenceClass:'derived',time:{role:'evidence-epoch',unknown:true}},
  {evidenceClass:'derived',time:{role:'evidence-epoch',start:2024,end:2024}}, {knowledge:{unknown:true}});
 for(const revision of Object.values(info.derivedRevisions||{}).slice(0,2))rows.push({revision});
 if(info.nativeRevision)rows.push({evidenceClass:'source',revision:info.nativeRevision});
 rows.push({revision:'0'.repeat(64)});
 for(const registration of Object.values(info.registrations||{})){
  rows.push({knowledge:{revision:registration.identity}});
  const at=registration.revision?.knowledgeTime?.acceptedAt;
  if(at)rows.push({knowledge:{start:at,end:at}});
 }
 rows.push({...spatial,point,families:['dtm','terrain-slope'],time:{role:'evidence-epoch',unknown:true}});
 for(const [identity,direction,depth] of [[sourceIdentity,'dependents','direct'],[sourceIdentity,'dependents','transitive'],[slopeIdentity,'inputs','direct'],[ratioIdentity,'inputs','transitive'],[slopeIdentity,'dependents','direct'],['glaciers:683','dependents','direct']]){
  // G0 has no derived evidence; a source seed still exists.
  if(identity===slopeIdentity||identity===ratioIdentity){if(!info.derivedCount)continue}
  rows.push({relatedTo:{identity,direction,depth}});
 }
 return rows;
}
export function semantic(answer){const{metrics,...body}=answer;return body}
