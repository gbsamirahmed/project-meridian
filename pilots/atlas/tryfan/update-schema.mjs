// Finite pilot applicability receipts; native Contract v1 stays unchanged.
import { encode,sha,fields,requireThat } from './identity.mjs';
import { ref } from './dependencies.mjs';
const regionalTerrain='1d505b031053dbd3e4f91055c765213d2f61aeb20080cae710f1ad049aee7c71';
export function validateUpdate(value) {
  const u=value.update;
  if(!u)return;
  fields(u,['schema','scenario','phase','from'],['recomputed','reused','changed']);
  requireThat(u.schema==='atlas-tryfan-applicability-update/v1' && ['U1','U2'].includes(u.scenario) && ['withheld','applied'].includes(u.phase) && /^[a-f0-9]{64}$/.test(u.from),'invalid-update','Unknown bounded update/reference');
  requireThat(value.serving && value.understanding,'invalid-update','Complete serving/understanding required');
  const withheld=u.phase==='withheld';
  requireThat(!withheld || u.scenario==='U2','invalid-update','Withheld baseline belongs only to isolated U2');
  requireThat(value.serving.layers.nrw.applicability===(withheld?'withheld':'eligible'),'invalid-update','NRW serving and query applicability must agree');
  if(withheld) {
    requireThat(sha(encode(value.understanding.terrain))==='4ee2af71dbf6978b11b4b8249d25fae83862209d113349a1f66e4a8cd36c4fdd','invalid-hierarchy','Withheld baseline remains original common G0');
    requireThat(!u.recomputed && !u.reused && !u.changed && value.understanding.stage==='common','invalid-update','U2 baseline does not revise/derive evidence');
  } else {
    const results=value.understanding.results;
    // Original S3 order is four AWS records followed by the two Welsh records.
    requireThat(results.length===6 && encode(u.recomputed)===encode(results.slice(4).map(ref)) && encode(u.reused)===encode(results.slice(2,4).map(ref)),'invalid-update','Recomputed/reused receipt differs from exact retained chain');
    requireThat(encode(u.changed)===encode(u.scenario==='U1'?['terrain-applicability','derived-understanding']:['terrain-applicability','nrw-applicability','derived-understanding']),'invalid-update','Unknown family change');
    requireThat(sha(encode(value.understanding.terrain))===regionalTerrain,'invalid-hierarchy','Exact retained Welsh hierarchy required');
  }
}

export function validateTransition(value,previous) {
  if(!value.update)return;
  if(encode(value.update)===encode(previous.update??null))return;
  requireThat(value.update.from===value.parent && previous.understanding?.stage==='common','invalid-update','Bounded update must name the exact common baseline');
  requireThat(encode(value.catalogue)===encode(previous.catalogue) && encode(value.knowledge)===encode(previous.knowledge),'invalid-update','Applicability transactions cannot revise native retained records');
  requireThat(encode(value.serving.assets)===encode(previous.serving.assets),'invalid-update','All portrayal bytes reused');
  requireThat(encode(value.understanding.results.slice(0,4))===encode(previous.understanding.results),'invalid-update','Historical records must be retained exactly');
  if(value.update.phase==='applied')requireThat(value.update.scenario==='U1'?!previous.update:previous.update?.scenario==='U2' && previous.update.phase==='withheld','invalid-update','U1/U2 baseline cannot be substituted');
  else requireThat(!previous.update,'invalid-update','U2 withheld baseline starts only from S4');
}
