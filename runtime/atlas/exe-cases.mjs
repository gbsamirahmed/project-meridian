/** Finite real-population queries and independent expected selections. */
export const point=[296700,86650],area=[296600,86550,296800,86750];
export const queries=[{}, {region:'exe'}, {region:'tryfan'}, {region:'riffelhorn'},
 ...['source','derived'].map(evidenceClass=>({region:'exe',evidenceClass})),
 ...['water-reference','water-event','water-monthly'].map(family=>({families:[family]})),
 ...['exe:wfd','exe:rfo','exe:2024-03:point','exe:2024-03:product','exe:2024-03:support','exe:2024-09:point','exe:2024-09:product','exe:2024-09:support','absent'].map(identity=>({identity})),
 ...['wfd:GB510804505600','rfo:31383','absent'].map(feature=>({region:'exe',feature})),
 {region:'exe',point,crs:'EPSG:27700'}, {region:'exe',area,crs:'EPSG:27700'},
 {region:'exe',point:[294999,86000],crs:'EPSG:27700'},
 {region:'exe',point:[298500,89000],crs:'EPSG:27700'},
 {region:'exe',area:[296800,86550,296801,86750],crs:'EPSG:27700'},
 ...['2024-03','2024-09'].map(month=>({region:'exe',waterTime:{role:'observation',start:month+'-01',end:month+(month.endsWith('03')?'-31':'-30')}})),
 {region:'exe',waterTime:{role:'observation',start:'2024-04-01',end:'2024-04-30'}},
 {region:'exe',waterTime:{role:'observation',unknown:true}},
 {region:'exe',waterTime:{role:'reference',start:'2019',end:'2019'}},
 {region:'exe',waterTime:{role:'reference',start:'2024',end:'2024'}},
 {region:'exe',waterTime:{role:'event',start:'1960-01-01',end:'2024-12-31'}},
 {region:'exe',time:{role:'evidence-epoch',unknown:true}},
 {region:'exe',time:{role:'evidence-epoch',start:2024,end:2024}},
 {region:'exe',area,crs:'EPSG:27700',evidenceClass:'derived',waterTime:{role:'observation',start:'2024-09-01',end:'2024-09-30'}},
 {families:['water-reference','terrain-slope']},
 ...['direct','transitive'].map(depth=>({relatedTo:{identity:'exe:2024-03:product',direction:'dependents',depth}})),
 {relatedTo:{identity:'exe:2024-09:support',direction:'inputs',depth:'direct'}}];
export const semantic=a=>{const {metrics,...v}=a;return v};
export const ids=a=>a.results.map(r=>r.identity).sort();
export function literal(q,records){
 // Independent interval/identity oracle over immutable descriptors. Geometry is
 // separately checked against source GIS rather than against another SQL path.
 return records.filter(r=>{
  if(q.region&&q.region!=='exe')return false;
  if(q.identity&&q.identity!==r.identity)return false;
  if(q.feature&&q.feature!==r.feature)return false;
  if(q.evidenceClass&&q.evidenceClass!==r.evidenceClass)return false;
  if(q.families&&!q.families.includes(r.family))return false;
  if(q.waterTime){const t=q.waterTime,role=t.role==='reference'?'nominal-epoch':t.role,extents=r.waterTime.filter(x=>x.role===role).map(x=>x.extent);if(t.unknown)return !extents.length||extents.every(x=>x.kind==='unknown');return extents.some(x=>x.kind==='interval'?x.start<=t.end&&x.end>=t.start:x.kind==='epoch'&&t.start<=x.value&&x.value<=t.end)}
  return true;
 }).map(r=>r.identity).sort();
}
