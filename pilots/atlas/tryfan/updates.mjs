// S5 finite U1/U2 writer. No source revision, scheduler or serving write endpoint.
import { readFileSync,writeFileSync,mkdirSync,existsSync } from 'node:fs';
import { join } from 'node:path';
import { performance } from 'node:perf_hooks';
import { load,STORE,storePath,register,assembleAndRegister } from './generations.mjs';
import { DATA } from './catalogue.mjs';
import { methods } from './derivations.mjs';
import { encode,requireThat } from './identity.mjs';
const clone=structuredClone;

export function inheritedS4(store=STORE) {
  let s=load(store);
  while(s.value.update) s=load(store,{generation:s.value.parent});
  requireThat(s.value.serving && s.value.understanding.stage==='common','invalid-update','S4 common serving baseline required');
  return s;
}
// Explicit isolated U2/test fork, never discovers a newer scientific source release.
export function forkBaseline(target,{source=STORE,generation}={}) {
  const dir=storePath(target),from=storePath(source);
  requireThat(dir!==from && !existsSync(join(dir,'current.json')),'invalid-store','Fork requires an independent empty root');
  for(const f of ['generations','locators','artifacts'])mkdirSync(join(dir,f),{recursive:true});
  let s=generation?load(source,{generation}):inheritedS4(source);const selected=s.generation;
  for(;;) {
    writeFileSync(join(dir,'generations',s.generation+'.json'),encode(s.value),{flag:'wx'});
    writeFileSync(join(dir,'locators',s.generation+'.json'),encode(s.locators),{flag:'wx'});
    if(!s.value.parent)break;s=load(source,{generation:s.value.parent});
  }
  // Only the already declared rebuildable portrayal files are copied, never retained payloads.
  const selectedState=load(source,{generation:selected});
  for(const a of selectedState.value.serving.assets.filter(a=>a.origin.kind==='materialized')) {
    const name=a.id+(a.mime==='image/png'?'.png':'.json');writeFileSync(join(dir,'artifacts',name),readFileSync(join(from,'artifacts',name)),{flag:'wx'});
  }
  writeFileSync(join(dir,'current.json'),encode({format:'atlas-tryfan-pilot-store/v1',generation:selected}),{flag:'wx'});
  return {generation:selected,isolated:true};
}
export function prepareMixedBaseline({store,dataRoot=DATA}={}) {
  requireThat(store && storePath(store)!==storePath(STORE),'invalid-store','U2 requires an explicitly isolated store');
  const s=load(store,{dataRoot});
  if(s.value.update?.scenario==='U2' && s.value.update.phase==='withheld')return {generation:s.generation,alreadyPublished:true};
  requireThat(!s.value.update && s.value.understanding?.stage==='common' && s.value.serving,'invalid-update','U2 starts from retained S4 common baseline');
  const value=clone(s.value);value.parent=s.generation;
  value.update={schema:'atlas-tryfan-applicability-update/v1',scenario:'U2',phase:'withheld',from:s.generation};
  value.serving.layers.nrw.applicability='withheld';
  return register(store,value,s.locators,{dataRoot});
}
export function publishUpdate({store=STORE,dataRoot=DATA,scenario='U1',failAt}={}) {
  requireThat(['U1','U2'].includes(scenario),'invalid-update','Only frozen U1 and U2 supported');
  requireThat(failAt===undefined || ['after-artifacts','after-evidence','after-recompute','after-validation','before-switch'].includes(failAt),'invalid-operation','Unknown failure checkpoint');
  return assembleAndRegister(store,async(s,checkpoint)=>{
    const start=performance.now();
    if(s.value.update?.scenario===scenario && s.value.update.phase==='applied')return {generation:s.generation,alreadyPublished:true};
    requireThat(s.value.serving && s.value.understanding?.stage==='common' && (scenario==='U1'?!s.value.update:s.value.update?.scenario==='U2' && s.value.update.phase==='withheld'),'invalid-update','Frozen source applicability context required');
    checkpoint('after-artifacts',{scenario,baseline:s.generation,catalogue:s.value.catalogue,locators:s.locators,qualification:'Diagnostic staging only, never current state'});
    const m=await methods({dataRoot});
    try {
      const statuses=m.assess(s.value.understanding,s.value.catalogue,s.locators,{stage:'regional'});
      checkpoint('after-evidence',{scenario,baseline:s.generation,statuses,nrwApplicability:'eligible',qualification:'No completed derived state, not publishable'});
      const computed=m.recompute(s.value.understanding,s.value.catalogue,s.locators,{stage:'regional'});
      checkpoint('after-recompute',{scenario,baseline:s.generation,understanding:computed.understanding,qualification:'Pre-validation diagnostic state, never current'});
      const value=clone(s.value);value.parent=s.generation;value.capabilities.mixedFamilyUpdate=true;
      value.understanding=computed.understanding;
      value.update={schema:'atlas-tryfan-applicability-update/v1',scenario,phase:'applied',from:s.generation,
        recomputed:computed.recomputed,reused:computed.reused,changed:scenario==='U1'?['terrain-applicability','derived-understanding']:['terrain-applicability','nrw-applicability','derived-understanding']};
      value.serving.layers.nrw.applicability='eligible';
      value.serving.layers.terrain.availability='Retained Welsh applicability via original z14 selector; summit regional, southern common. Missing levels remain explicit.';
      m.validate(value.understanding,value.catalogue);
      requireThat(computed.recomputed.length===2 && computed.reused.length===2,'invalid-update','Only summit pair may be recomputed');
      return {value,locators:s.locators,metrics:{assemblyMilliseconds:performance.now()-start,considered:computed.considered,recomputed:computed.recomputed,reused:computed.reused,statuses,
        changedArtifacts:0,reusedArtifacts:s.value.catalogue.artifacts.length,retainedBytes:s.verification.bytes,sampling:computed.measurement}};
    } finally {await m.close();}
  },{dataRoot,failAt});
}
export function recoverInterrupted(store) {
  // Inspection only; recovery requires S1's exact nonce plus dead PID proof.
  const path=join(storePath(store),'writer.lock');return existsSync(path)?JSON.parse(readFileSync(path,'utf8')):null;
}
