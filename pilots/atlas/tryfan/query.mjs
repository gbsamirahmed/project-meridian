// Read-only S2 query envelope. Publication and domain contracts remain owned by S1/v1.
import { readFileSync, statSync } from 'node:fs';
import { resolve } from 'node:path';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { performance } from 'node:perf_hooks';
import { load, STORE } from './generations.mjs';
import { ROOT, DATA } from './catalogue.mjs';
import { PilotError, requireThat, safePath, sha, encode } from './identity.mjs';
import { nativeSemantics, instantiate, qualified } from './semantic.mjs';
const PYTHON=resolve(DATA,'earth-lab/.venv/Scripts/python.exe');
const PROPERTIES=['worldcover-native','worldcover-common','worldcover-support','nrw-native','coexisting-semantic','appearance','current-cover','physical-appearance','geological-substrate','provenance'];
const gap=(reason,explanation)=>({kind:'gap',reason,explanation});
export class NativeSession {
  constructor() {
    this.pending=[];this.closed=false;this.stderr='';
    this.child=spawn(PYTHON,[resolve(import.meta.dirname,'adapters/native.py')],{cwd:ROOT,stdio:['pipe','pipe','pipe'],
      env:{...process.env,PYTHONIOENCODING:'utf-8',PROJ_NETWORK:'OFF',PYTHONDONTWRITEBYTECODE:'1'}});
    this.child.stderr.on('data',s=>{this.stderr=(this.stderr+s).slice(-4000);});
    createInterface({input:this.child.stdout}).on('line',line=>{
      const p=this.pending.shift();if(!p)return;clearTimeout(p.timer);
      try {const value=JSON.parse(line);if(value.error)p.reject(new PilotError(value.error.code,value.error.message));else p.resolve(value.value);}
      catch(e){p.reject(e);}
    });
    const fail=e=>{this.closed=true;for(const p of this.pending.splice(0)){clearTimeout(p.timer);p.reject(e);}};
    this.child.stdin.on('error',e=>fail(new PilotError('worker-unavailable',e.message)));
    this.child.on('error',e=>fail(new PilotError('worker-unavailable',e.message)));
    this.child.on('exit',code=>fail(new PilotError('worker-unavailable','Worker exited '+code+': '+this.stderr)));
  }
  call(value) {
    requireThat(!this.closed && this.pending.length<32,'worker-unavailable','Closed/overloaded finite worker');
    return new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>{this.child.kill();},30000);this.pending.push({resolve,reject,timer});
      this.child.stdin.write(JSON.stringify(value)+'\n');
    });
  }
  async initialize(value) {
    const identity={...value,artifacts:Object.fromEntries(Object.entries(value.artifacts).map(([family,record])=>[family,Object.fromEntries(Object.entries(record).filter(([k])=>k!=='path'))]))};
    const key=sha(encode(identity));
    if(this.initializing){requireThat(this.key===key,'unsupported-representation','Shared worker requires identical registered native bytes/support');return this.initializing;}
    this.key=key;this.initializing=this.call(value);return this.initializing;
  }
  close(){this.child.stdin.end();}
}
function artifact(catalogue,family) {
  const found=catalogue.artifacts.filter(a=>a.uses.some(u=>u.family===family));
  requireThat(found.length===1,'unsupported-representation','Expected one registered native artifact for '+family);return found[0];
}
function available(a,locators,dataRoot) {
  try {
    const path=safePath(dataRoot,locators[a.id]);
    requireThat(statSync(path).isFile() && statSync(path).size===a.bytes && sha(readFileSync(path))===a.sha256,'hash-mismatch','Registered retained bytes differ: '+a.id);
    return {path,bytes:a.bytes,sha256:a.sha256,status:'available'};
  } catch(e) {if(e.code==='artifact-unavailable')return {status:'unavailable',reason:'artifact-unavailable',artifact:a.id};throw e;}
}
export async function openEvidence({store=STORE,generation,dataRoot=DATA,locators,nativeSession}={}) {
  const start=performance.now();
  // Metadata/root integrity still mandatory; per-family verification permits honest unavailable
  // WC without declaring an otherwise valid NRW artifact absent. Never arbitrary data discovery.
  const snapshot=load(store,{generation,dataRoot,locators,verify:false}),catalogue=snapshot.value.catalogue;
  for(const receipt of catalogue.basis.metadataReceipts)requireThat(sha(readFileSync(safePath(ROOT,receipt.path)))===receipt.sha256,
    'hash-mismatch','Registered semantic/dictionary metadata changed: '+receipt.path);
  const wc=artifact(catalogue,'worldcover'),nrw=artifact(catalogue,'nrw');
  const descriptors={worldcover:available(wc,snapshot.locators,dataRoot),nrw:available(nrw,snapshot.locators,dataRoot)};
  const receipts=JSON.parse(readFileSync(resolve(ROOT,'docs/atlas/semantic-comparison-sources.json'),'utf8'));
  const gridTransform=receipts.files.find(f=>f.file==='tryfan-worldcover.tif').subsetDefinition.windowTransform;
  const worker=nativeSession??new NativeSession();
  const release=()=>{if(!nativeSession)worker.close();};
  try {
    const initialized=await worker.initialize({operation:'init',core:snapshot.value.core.bounds,artifacts:descriptors,gridTransform});
    const semantics=await nativeSemantics(catalogue,initialized.metadata);
    if(snapshot.value.knowledge && initialized.metadata.families.worldcover.status==='available' && initialized.metadata.families.nrw.status==='available')
      requireThat(encode(snapshot.value.knowledge)===encode(semantics.state.bundle),'knowledge-drift','Published native knowledge differs from verified S2 reconstruction');
    const initMilliseconds=performance.now()-start;
    const trace=family=>{
      const f=catalogue.families.find(f=>f.id===family),s=catalogue.sources.find(s=>s.id===f.source),p=catalogue.products.find(p=>p.id===f.product);
      const resources=f.nativeMetadata.resources??[];
      return {generation:snapshot.generation,family,source:s,product:p,representations:catalogue.representations.filter(r=>f.representations.includes(r.id)),
        artifacts:catalogue.artifacts.filter(a=>a.uses.some(u=>u.family===family)).map(a=>({id:a.id,sha256:a.sha256,bytes:a.bytes,aliases:a.aliases,uses:a.uses})),
        resources,rights:family==='appearance'?f.nativeMetadata.rights:resources.map(r=>({ref:r.ref,rights:r.rights})),
        registrationBasis:catalogue.basis,qualification:f.qualification};
    };
    async function query(request) {
      requireThat(request && typeof request==='object' && !Array.isArray(request) && Object.keys(request).every(k=>['point','crs','property','time','family','support'].includes(k)),'invalid-request','Finite S2 request fields required');
      const {point,crs='EPSG:27700',property,time=null,family,support}=request;
      requireThat(Array.isArray(point) && point.length===2 && point.every(Number.isFinite),'invalid-coordinate','Finite xy point required');
      requireThat(['EPSG:27700','OGC:CRS84'].includes(crs),'invalid-crs','Use EPSG:27700 or OGC:CRS84 xy');
      requireThat(crs!=='OGC:CRS84' || Math.abs(point[0])<=180 && Math.abs(point[1])<=90,'invalid-coordinate','CRS84 coordinate out of range');
      requireThat(typeof property==='string' && property.length && (time===null || typeof time==='string') && (family===undefined || ['worldcover','nrw','appearance'].includes(family)),'invalid-request','Invalid property/time/family');
      requireThat(!support || Array.isArray(support) && support.length===4 && support.every(Number.isFinite),'invalid-support','Ordered BNG support required');
      requireThat(property!=='worldcover-support' || support,'invalid-support','Support query requires explicit BNG rectangle');
      const base={schema:'atlas-tryfan-s2-answer/v1',generation:snapshot.generation,query:structuredClone(request),operationalStatus:'available',records:[]};
      for(const [family,a] of [['worldcover',wc],['nrw',nrw]])if(descriptors[family].status==='available')requireThat(available(a,snapshot.locators,dataRoot).status==='available','artifact-unavailable','Registered native evidence disappeared');
      const raw=await worker.call({operation:'query',point,crs,...(support?{support}:{})});
      base.location={pointBNG:raw.pointBNG,pointCRS84:raw.pointCRS84,transform:initialized.metadata.transform};
      if(!raw.insideCore)return {...base,result:gap('outside-support','Outside admitted half-open pilot core; no physical absence asserted.')};
      if(!PROPERTIES.includes(property) || ['current-cover','physical-appearance'].includes(property))return {...base,result:gap('unsupported','No compatible retained S2 evidence; no unrelated historical or RGB fallback.')};
      const wanted=property.startsWith('worldcover') || property==='geological-substrate'?['worldcover']:property==='nrw-native'?['nrw']:property==='appearance'?['appearance']:['worldcover','nrw'];
      if(family && !wanted.includes(family))return {...base,operationalStatus:'excluded-by-context',result:gap('unsupported','Requested family cannot answer this physical/property question; incompatible fallback rejected.')};
      const records=[];
      for(const f of wanted.filter(f=>!family || f===family)) {
        const provenance=trace(f);
        if(f==='appearance') {
          const meta=catalogue.families.find(f=>f.id==='appearance').nativeMetadata;
          if(time && time!=='2026-07-12'){records.push({family:f,result:gap('unsupported','Only retained July12 observation metadata is registered.'),provenance});continue;}
          const assets=provenance.artifacts.map(a=>available(a,snapshot.locators,dataRoot));
          records.push({family:f,operationalStatus:assets.some(a=>a.status==='unavailable')?'unavailable':'available',metadata:meta,provenance,
            qualification:'Metadata only: source/prepared/display distinction. No appearance correction, current physical colour or physical relighting assertion.'});continue;
        }
        if(f==='nrw' && snapshot.value.update?.phase==='withheld') {
          records.push({family:f,operationalStatus:'excluded-by-context',result:gap('unsupported','Controlled U2 applicability withheld; native inventory remains registered, not absent or revised.'),provenance});continue;
        }
        if(descriptors[f].status==='unavailable'){records.push({family:f,operationalStatus:'unavailable',reason:'artifact-unavailable',provenance});continue;}
        if(time && (f==='worldcover'?time!=='2021':true)){records.push({family:f,result:gap('unsupported',f==='worldcover'?'Annual2021 classification cannot answer other/current epoch.':'Exact native feature survey/validity time is unknown; no requested-time assertion.'),provenance});continue;}
        if(f==='worldcover') {
          if(raw.worldcover.gap){records.push({family:f,result:gap(raw.worldcover.gap,'Outside native raster support.'),provenance});continue;}
          const native=instantiate(semantics.state,raw.worldcover);
          requireThat(native.native,'corrupt-native-code','No native code template');
          const record={family:f,operationalStatus:'available',...qualified(semantics.state,native,'collection:worldcover'),cell:raw.worldcover,provenance};
          if(property==='worldcover-support') {
            record.assignments={...raw.worldcoverSupport,templates:Object.keys(raw.worldcoverSupport.counts).map(code=>{
              const c=semantics.state.bundle.collections[0].claims.find(c=>c.native.fields.code===+code);return qualified(semantics.state,c,'collection:worldcover');})};
          }
          if(property==='geological-substrate') {record.result=gap('unsupported','Native cover cannot establish geological substrate.');record.rejectedMapping=semantics.state.bundle.mappings.find(m=>m.id==='mapping:wc-substrate');}
          records.push(record);
        } else {
          if(!raw.nrw.length)records.push({family:f,result:gap('missing-inventory','No retained native polygon covers/intersects requested place within study support; not physical absence.'),provenance});
          for(const member of raw.nrw) {
            const claim=semantics.state.bundle.collections[1].claims.find(c=>c.id==='claim:nrw-record-'+member.id);
            requireThat(claim,'invalid-semantic-reference','Native feature claim missing');
            records.push({family:f,operationalStatus:'available',...qualified(semantics.state,claim,'collection:nrw'),
              feature:{namespace:provenance.product.ref,id:member.id,kind:'inventory-object'},membership:member,provenance});
          }
        }
      }
      return {...base,records,operationalStatus:records.length && records.every(r=>r.operationalStatus==='excluded-by-context')?'excluded-by-context':records.length && records.every(r=>r.operationalStatus==='unavailable')?'unavailable':'available',
        qualification:'Independent qualified evidence; no canonical cover value, ranking, simultaneity or current-state inference.'};
    }
    return {generation:snapshot.generation,parent:snapshot.value.parent,query:async request=>structuredClone(await query(request)),close:release,
      metadata:structuredClone(initialized.metadata),semantics:structuredClone(semantics.state),metrics:{...initialized.metrics,readerInitializationMilliseconds:initMilliseconds},
      capabilities:{nativeQueries:true,derivedUnderstanding:false,serving:false},publishedCapabilities:snapshot.value.capabilities};
  } catch(e){release();throw e;}
}
export { encode };
