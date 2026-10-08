// Unhooked accepted Tryfan pixel-replay control, not a new source/method.
import fs from 'node:fs';
import {openUnderstanding} from '../../../pilots/atlas/tryfan/derivations.mjs';
import {encode} from '../../../pilots/atlas/tryfan/identity.mjs';
const wanted=JSON.parse(process.argv[2]),d=await openUnderstanding();
try {
 const s=d.inspect().state,input=JSON.parse(fs.readFileSync('docs/research/tryfan-qualified-query-inputs.json','utf8')),rows=[],checks=[];
 for(const id of wanted){
  const r=s.results.find(r=>r.probe===id&&r.property==='slope'&&s.active.some(a=>a.id===r.claim.id&&a.revision===r.claim.revision));
  if(!r)throw Error('Unknown current Tryfan probe');checks.push(d.replay({id:r.claim.id,revision:r.claim.revision}));
  const root=input.roots.find(x=>'retained-input:'+x.id===r.receipt.inputs[0].id);
  rows.push({id:'tryfan-'+id,region:'tryfan',kind:'terrain',stride:1,point:input.geometry.probes.find(p=>p.id===id).centre,spacing:root.analysisSpacingM,samples:root.heightSamplesM,uses:[{key:'tryfan:'+root.id,scope:root.actualUse,samples:root.heightSamplesM}],oracle:{slope:r.claim.result.value.value,'area-ratio':s.results.find(x=>x.probe===id&&x.property==='area-ratio'&&s.active.some(a=>a.id===x.claim.id&&a.revision===x.claim.revision)).claim.result.value.value},origin:{acceptedClaim:r.claim.id,acceptedRevision:r.claim.revision,receipt:r.receipt}});
 }
 console.log(encode({rows,checks}));
}finally{await d.close();}
