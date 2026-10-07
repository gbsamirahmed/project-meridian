// Finite retained slope -> planar-ratio graph; no workflow engine.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { ROOT } from './catalogue.mjs';
import { encode,sha,requireThat,fields,json } from './identity.mjs';
export const METHOD='7fe3f0c3ed6152177dfcb97b7be190dcda8fd45ddb18b27c2a8eb2b2b398f8d9';
export const scientificCanonical=v=>Array.isArray(v)?'['+v.map(scientificCanonical).join(',')+']':v!==null && typeof v==='object'?'{'+Object.entries(v).sort(([a],[b])=>a.localeCompare(b,'en')).map(([k,x])=>JSON.stringify(k)+':'+scientificCanonical(x)).join(',')+'}':JSON.stringify(v);
export const scientificHash=v=>sha(scientificCanonical(v));
export const resultKey=r=>r.id+'@'+r.revision;
export const ref=r=>({id:r.claim.id,revision:r.claim.revision});
export function basis() {
 const pins={'inputs':'ab2062b81b7e84b749700cae13c499e837e0705de96c22192ef9ad2f6d13a9a7','results':'871be961f6df0ff479c4ec935980eb35070e5a9363bcddc5fe73bfd6051fc3f2','plan':'06097cb52471721c7aefe7e25886c51bf0a2249ea306feff42695a17ff06d67e'};
 for(const [n,h] of Object.entries(pins))requireThat(sha(readFileSync(resolve(ROOT,'docs/research/tryfan-qualified-query-'+n+'.json')))===h,'method-unavailable','Authoritative scientific receipt changed');
 const previous=json(resolve(ROOT,'docs/research/tryfan-qualified-query-results.json'));
 return {methodRevision:METHOD,methodFiles:previous.methodFiles,software:json(resolve(ROOT,'docs/research/tryfan-qualified-query-inputs.json')).software,
 receipts:Object.fromEntries(['inputs','results','plan'].map(n=>{const p='docs/research/tryfan-qualified-query-'+n+'.json';return [p,sha(readFileSync(resolve(ROOT,p)))];}))};
}
export function validateDependencies(u,catalogue) {
 fields(u,['schema','basis','probes','terrain','stage','roots','results','active']);
 requireThat(u.schema==='atlas-tryfan-understanding/v1','unsupported-understanding','Unknown pilot understanding schema');
 requireThat(encode(u.basis)===encode(basis()) && u.basis.methodRevision===METHOD,'method-unavailable','Pinned scientific basis differs');
 const input=json(resolve(ROOT,'docs/research/tryfan-qualified-query-inputs.json'));
 requireThat(['common','regional'].includes(u.stage) && encode(u.probes)===encode(input.geometry.probes),'invalid-context','Unknown terrain applicability or probe');
 requireThat(u.results.length===(u.stage==='common'?4:6),'invalid-results','Incomplete finite retained result set');
 const expected=input.roots.filter(r=>u.stage==='regional'||r.family==='production-common').map(r=>{const a=structuredClone(r);delete a.heightSamplesM;return a;});
 requireThat(encode(u.roots)===encode(expected),'invalid-roots','Changed exact retained dependency metadata');
 const references=new Map(),forward={},reverse={};
 for(const r of u.results) {
  requireThat(['slope','area-ratio'].includes(r.property) && u.probes.some(p=>p.id===r.probe),'unknown-method','Only frozen two-probe methods are supported');
  const key=resultKey(ref(r));requireThat(!references.has(key),'conflicting-result','Duplicate result revision');references.set(key,r);
  const body=structuredClone(r.claim);delete body.id;delete body.revision;
  requireThat(scientificHash({body,context:r.context})===r.claim.revision && scientificHash(r.claim.result.value.value)===r.receipt.artifact.sha256,'result-integrity','Qualified result or scalar digest differs');
  requireThat(r.receipt.methodRevision===METHOD && r.receipt.method===(r.property==='slope'?'Horn-3x3-grid-slope':'planar-area-ratio-from-slope'),'unsupported-method-revision','Unknown scientific method revision');
  const b=structuredClone(r.receipt);delete b.id;delete b.artifact;
  requireThat(r.receipt.id==='run:'+scientificHash(b),'receipt-integrity','Invocation digest differs');
  requireThat(r.receipt.inputs.length===1,'invalid-dependency','Finite method requires one immediate input');
  forward[key]=[];
 }
 for(const r of u.results) for(const use of r.receipt.inputs) {
  const a=use.spatial?.bounds;
  requireThat(use.id && use.revision && use.role && use.spatial?.crs==='EPSG:27700' && Array.isArray(a) && a.length===4 && a.every(Number.isFinite) && a[0]<=a[2] && a[1]<=a[3],'invalid-input-use','Exact identity and valid actual use required');
  const key=resultKey(ref(r)),inputKey=use.kind+':'+resultKey(use);
  (reverse[inputKey]??=[]).push(ref(r));
  if(use.kind==='claim') {
   const parent=references.get(resultKey(use));requireThat(parent && parent.property==='slope' && r.property==='area-ratio' && parent.probe===r.probe,'dependency-missing','Exact upstream slope required');forward[key].push(resultKey(use));
  } else {
   const root=u.roots.find(x=>'retained-input:'+x.id===use.id && x.revision===use.revision);
   requireThat(r.property==='slope' && use.kind==='resource' && root,'dependency-missing','Exact retained resource required');
   requireThat(encode(a)===encode(root.actualUse.bounds),'invalid-input-use','Scope differs from actual sampled cells');
  }
 }
 const visited=new Set(),visiting=new Set();
 function visit(k){requireThat(!visiting.has(k),'cyclic-dependency','Cyclic retained dependency');if(visited.has(k))return;visiting.add(k);forward[k].forEach(visit);visiting.delete(k);visited.add(k);}
 Object.keys(forward).forEach(visit);
 requireThat(u.active.length===4 && new Set(u.active.map(resultKey)).size===4 && u.active.every(a=>references.has(resultKey(a))),'invalid-active','Four exact current result refs required');
 const previous=json(resolve(ROOT,'docs/research/tryfan-qualified-query-results.json'));
 const current=u.stage==='common'?u.results.map(ref):previous.currentResults.map(r=>r.result);
 requireThat(encode(u.active)===encode(current),'invalid-active','Current references differ from frozen lifecycle context');
 for(const r of u.results){const c=previous.evidence.collections.find(c=>c.claims?.some(q=>q.id===r.claim.id && q.revision===r.claim.revision));const original=previous.results.find(q=>q.claim.id===r.claim.id && q.claim.revision===r.claim.revision);
  requireThat(c && original && encode(r.claim)===encode(c.claims[0]) && encode(r.context)===encode(c.context) && encode(r.receipt)===encode(original.receipt) && r.question===original.question,'scientific-drift','Result differs from authoritative retained proof');}
 for(const root of u.roots)for(const a of root.assets)requireThat(catalogue.artifacts.some(x=>x.id==='sha256:'+a.sha256 && x.bytes===a.bytes && x.aliases.includes(a.href)),'unregistered-dependency','Input has no S1 catalogue artifact');
 return {forward,reverse,edges:u.results.length};
}
