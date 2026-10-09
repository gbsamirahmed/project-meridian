export const families=['priority-habitat','planning-flood-zone'];
export const probes=[[296700,86650],[296850,87100],[297150,87350],[297650,87600],[295800,87150],[296850,88350]];
export const areas=probes.map(([x,y])=>[x-100,y-100,x+100,y+100]);
export const semantic=a=>Object.fromEntries(Object.entries(a).filter(([k])=>k!=='metrics'));
export const ids=a=>a.results.map(r=>r.identity).sort();
export const queries=[{}, {region:'exe'},...families.map(f=>({families:[f]})),{families:['water-reference',...families]}, {families:['terrain-slope',...families]}, {evidenceClass:'source'},{evidenceClass:'derived'},
 ...['MUDFL','CFPGM','LFENS','RBEDS','SALTM','FZ2','FZ3'].map(nativeClassification=>({nativeClassification})),
 ...probes.map(point=>({region:'exe',point,crs:'EPSG:27700'})),...areas.map(area=>({region:'exe',area,crs:'EPSG:27700'})),
 {region:'exe',point:[295000,86000],crs:'EPSG:27700'},{region:'exe',point:[298500,89000],crs:'EPSG:27700'},
 {region:'exe',area:[294999,85999,295000,86000],crs:'EPSG:27700'},
 ...['survey','effective','publication','contributor'].map(role=>({referenceTime:{role,unknown:true}})),
 {referenceTime:{role:'survey',start:'2024-01-01',end:'2024-12-31'}}, {referenceTime:{role:'effective',start:'2026-01-01',end:'2026-12-31'}},
 {referenceTime:{role:'contributor',start:'2019',end:'2026'}},
 {referenceTime:{role:'survey',unknown:true},nativeClassification:'SALTM'},
 {region:'exe',feature:'phi:absent'}, {identity:'absent'}, {region:'tryfan'}, {region:'riffelhorn'},
 {waterTime:{role:'observation',unknown:true}}, {referenceTime:{role:'survey',unknown:true},knowledge:{revision:'0'.repeat(64)}}];
