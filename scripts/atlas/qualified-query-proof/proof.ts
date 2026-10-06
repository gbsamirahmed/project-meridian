/** Research-only vertical slice; v1 and TerrainHierarchy remain canonical and unchanged. */
import { createHash } from 'node:crypto';
import { known, unknown } from '../../../src/atlas/terrain/metadata/terrainMetadata';
import type { AssetReference, EntityReference } from '../../../src/atlas/terrain/metadata/terrainMetadata';
import { AWS_VISUAL_PRODUCT } from '../../../src/atlas/terrain/metadata/awsVisualTerrainProduct';
import { TRYFAN_PRODUCT, TRYFAN_SOURCE } from '../../../src/atlas/terrain/metadata/tryfanTerrainProof';
import type { TerrainSelection } from '../../../src/atlas/terrain/runtime/terrainSelector';
import type { ClaimContext, SemanticClaim, SemanticDefinition, SemanticEvidenceBundle, SemanticResource, TimeExtent } from '../semantic-evidence/contract';

export type Bounds = readonly [number, number, number, number];
export interface Probe { id: string; centre: readonly [number, number] }
export interface Root {
  id: string; revision: string; probe: string; family: string; level: string;
  heightSamplesM: number[][]; analysisSpacingM: number;
  assets: (AssetReference & {bytes: number})[];
  actualUse: {crs: string; bounds: Bounds; usedPixelCount: number; meaning: string};
  upstream: {product: string; revision: string | {status: 'unknown'; reason: string}};
}
export interface InputUse {
  kind: 'resource' | 'claim'; id: string; revision: string; role: string;
  spatial: {crs: 'EPSG:27700'; bounds: Bounds; meaning: string};
  temporal: TimeExtent;
}
export interface Receipt {
  id: string; method: string; methodRevision: string;
  parameters: {analysisSpacingM: number; horizontalUnits: 'BNG grid metres'};
  inputs: InputUse[]; artifact: {sha256: string; encoding: 'JSON numeric scalar'};
}
export interface Derived {question: string; probe: string; property: 'slope' | 'area-ratio'; claim: SemanticClaim; context: ClaimContext; receipt: Receipt}
export interface Assessment {policy: string; status: 'fresh' | 'stale' | 'indeterminate'; reason: string; result: {id: string; revision: string}; selectedFamily?: string; policyRevision: string; baseline: {hierarchy: {id:string; revision:string}; expectedMethodRevision:string; changesDigest:string}}
export interface Change {inputId: string; bounds?: Bounds; scopeKnown: boolean; description: string}
const report = 'docs/research/tryfan-qualified-query-proof.md';
const record = 'docs/research/tryfan-qualified-query-results.json';
export function canonical(value: unknown): string {
  if (Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
  if (value !== null && typeof value==='object') return '{'+Object.entries(value).sort(([a],[b])=>a.localeCompare(b,'en')).map(([k,v])=>JSON.stringify(k)+':'+canonical(v)).join(',')+'}';
  return JSON.stringify(value);
}
export const hash = (value: unknown): string => createHash('sha256').update(canonical(value)).digest('hex');
export function hornSlope(a: number[][], spacing: number): number {
  if (!(spacing>0) || a.length!==3 || a.some(r=>r.length!==3 || r.some(v=>!Number.isFinite(v)))) throw new Error('Finite 3x3 neighbourhood and positive physical spacing required');
  const dx=((a[0][2]+2*a[1][2]+a[2][2])-(a[0][0]+2*a[1][0]+a[2][0]))/(8*spacing);
  const dy=((a[0][0]+2*a[0][1]+a[0][2])-(a[2][0]+2*a[2][1]+a[2][2]))/(8*spacing);
  return Math.atan(Math.hypot(dx,dy))*180/Math.PI;
}
export function areaRatio(slopeDegrees: number): number {
  if (!Number.isFinite(slopeDegrees) || slopeDegrees<0 || slopeDegrees>=90) throw new Error('Slope must be finite in [0,90)');
  return 1/Math.cos(slopeDegrees*Math.PI/180);
}
export const intersects = (a: Bounds,b: Bounds): boolean => a[0]<=b[2] && b[0]<=a[2] && a[1]<=b[3] && b[1]<=a[3];
const time: TimeExtent={kind:'unknown',reason:'Exact source-cell observation epoch is unknown; Welsh catalogue date is not a mapped per-cell epoch and AWS lineage is unpinned.'};
const crs={name:'OSGB36 / British National Grid',identifier:'EPSG:27700'};
const resourceRef=(r: Root): EntityReference=>({kind:'product',id:'retained-input:'+r.id,revision:known(r.revision)});
const propertyId=(p: Derived['property'])=>'proof-property:represented-heightfield-'+p;
export function derive(probe: Probe, root: Root, methodRevision: string): Derived[] {
  const slope=hornSlope(root.heightSamplesM,root.analysisSpacingM);
  const limitations='Geometric quantity of this represented heightfield, not verified bare-earth slope, accuracy, material, exposure, traversability or true surface area. BNG grid metres approximate horizontal distance. Unknown vertical/epoch/upstream information retained; no source-family fusion.';
  const support={geometry:{kind:'native-point' as const,crs,coordinates:probe.centre},meaning:'Local derivative at fixed query point, sampled 3x3 on the BNG analysis grid; not a homogeneous patch.',grain:known('8m grid spacing; 16m centre-to-centre stencil, plus actual interpolation footprint; not effective source resolution.')};
  const build=(property: Derived['property'],value: number,inputs: InputUse[],upstream?: Derived): Derived=>{
    const method=property==='slope'?'Horn-3x3-grid-slope':'planar-area-ratio-from-slope';
    const receiptBase={method,methodRevision,parameters:{analysisSpacingM:root.analysisSpacingM,horizontalUnits:'BNG grid metres' as const},inputs};
    const receipt: Receipt={...receiptBase,id:'run:'+hash(receiptBase),artifact:{sha256:hash(value),encoding:'JSON numeric scalar'}};
    const context: ClaimContext={support,time:[{role:'observation',extent:time}],evidence:{modes:['derived'],description:property==='slope'?'Horn slope from retained selected Terrarium cells; upstream semantic surface may be unknown.':'Area ratio of locally planar represented surface to map plane, derived from the exact slope claim.',
      inputs:upstream?[{kind:'claim',ref:{id:upstream.claim.id,revision:upstream.claim.revision},role:'local slope angle'}]:[{kind:'resource',ref:resourceRef(root),role:'actual selected z14 pixel neighbourhood'}],completeness:'complete',limitations:'Complete immediate logical inputs/receipt; upstream measurement lineage and uncertainty remain incomplete. '+limitations,
      processing:[{method,revision:known(methodRevision),parameters:{analysisSpacingM:root.analysisSpacingM,horizontalDistance:'BNG grid metres',sampling:'pixel-centre bilinear Terrarium'},record:{href:record,selector:receipt.id}}]}};
    const question=property+'|EPSG:27700|'+probe.centre.join(',')+'|8m|represented-heightfield';
    const body={native:{property:{id:propertyId(property),revision:'1'},fields:{quantity:property,analysisSpacingM:root.analysisSpacingM}},result:{kind:'assertion' as const,value:{kind:'quantity' as const,value,unit:property==='slope'?'degree':'m2 represented planar surface / m2 map plane'}},record:{href:record,selector:receipt.id}};
    const claim: SemanticClaim={id:'claim:'+hash(question),revision:hash({body,context}),...body};
    return {question,probe:probe.id,property,claim,context,receipt};
  };
  const read: InputUse={kind:'resource',id:resourceRef(root).id,revision:root.revision,role:'bilinear pixels consumed by Horn stencil',spatial:{crs:'EPSG:27700',bounds:root.actualUse.bounds,meaning:root.actualUse.meaning},temporal:time};
  const first=build('slope',slope,[read]);
  const next=build('area-ratio',areaRatio(slope),[{kind:'claim',id:first.claim.id,revision:first.claim.revision,role:'slope angle',spatial:{crs:'EPSG:27700',bounds:[probe.centre[0],probe.centre[1],probe.centre[0],probe.centre[1]],meaning:'Exact slope claim at point; transitive terrain read scope remains in upstream receipt.'},temporal:time}],first);
  return [first,next];
}
export function assess(result: Derived, all: Derived[], roots: Root[], selection: TerrainSelection, policy: 'fixed-input-replay-v1'|'current-applicable-terrain-v1',changes: Change[]=[], expectedMethodRevision=result.receipt.methodRevision): Assessment {
  const answer=(status: Assessment['status'],reason: string): Assessment=>({policy,status,reason,result:{id:result.claim.id,revision:result.claim.revision},policyRevision:hash({policy,implementationRevision:expectedMethodRevision}),baseline:{hierarchy:selection.hierarchy,expectedMethodRevision,changesDigest:hash(changes)},...(selection.status==='selected'?{selectedFamily:selection.family}:{})});
  if (result.property==='area-ratio') {
    const use=result.receipt.inputs[0];const upstream=all.find(r=>r.claim.id===use.id && r.claim.revision===use.revision);
    if (!upstream) return answer('indeterminate','Exact upstream slope claim unavailable');
    const a=assess(upstream,all,roots,selection,policy,changes,expectedMethodRevision);
    return answer(a.status,'Transitive slope assessment: '+a.reason);
  }
  const use=result.receipt.inputs[0];const root=roots.find(r=>resourceRef(r).id===use.id && r.revision===use.revision);
  if (!root) return answer('indeterminate','Exact retained input unavailable; do not fabricate physical absence');
  if (policy==='fixed-input-replay-v1') return answer('fresh','Exact local bytes/receipt and method available for historical replay; upstream global revision/time remain unknown');
  if (result.receipt.methodRevision!==expectedMethodRevision) return answer('stale','Explicit current method policy requires a different revision; no automatic scientific superiority');
  if (selection.status!=='selected') return answer('indeterminate','No eligible representation for this request');
  if (selection.family!==root.family || selection.level!==root.level) return answer('stale','Current explicit hierarchy policy selects another applicable representation; stale is not false');
  if (typeof root.upstream.revision==='string' && selection.product.revision.status==='known' && root.upstream.revision!==selection.product.revision.value) return answer('stale','Exact current product revision differs; scoped changed-value evidence needed for reuse');
  for (const change of changes.filter(c=>c.inputId===use.id)) {
    if (!change.scopeKnown || !change.bounds) return answer('indeterminate','Changed use scope unknown; conservative reassessment required');
    if (intersects(change.bounds,use.spatial.bounds)) return answer('stale','Known changed scope intersects actual input use including interpolation halo');
  }
  return answer('fresh','Selected representation still applies; no intersecting relevant input changes');
}
export function bundle(results: Derived[], roots: Root[], probe: Probe): SemanticEvidenceBundle {
  const awsSource: SemanticResource={ref:{kind:'source',id:'aws-hosted-delivery',revision:AWS_VISUAL_PRODUCT.revision},domain:'terrain',name:'Delivered AWS mosaic as available source; original measurement contributors unknown',definition:{href:'src/atlas/terrain/metadata/awsVisualTerrainProduct.ts'},rights:AWS_VISUAL_PRODUCT.rights,inputs:[]};
  const productResources: SemanticResource[]=[{ref:{kind:'product',id:AWS_VISUAL_PRODUCT.id,revision:AWS_VISUAL_PRODUCT.revision},domain:'terrain',name:AWS_VISUAL_PRODUCT.name,definition:{href:'docs/atlas/terrain-runtime-selection.md'},rights:AWS_VISUAL_PRODUCT.rights,inputs:[awsSource.ref]},
    {ref:{kind:'source',id:TRYFAN_SOURCE.id,revision:TRYFAN_SOURCE.revision},domain:'terrain',name:TRYFAN_SOURCE.name,definition:{href:'docs/atlas/tryfan-second-region-proof.md'},rights:TRYFAN_SOURCE.rights,inputs:[]},
    {ref:{kind:'product',id:TRYFAN_PRODUCT.id,revision:TRYFAN_PRODUCT.revision},domain:'terrain',name:TRYFAN_PRODUCT.name,definition:{href:'docs/atlas/tryfan-second-region-proof.md'},rights:TRYFAN_PRODUCT.rights,inputs:[{kind:'source',id:TRYFAN_SOURCE.id,revision:TRYFAN_SOURCE.revision}]}];
  const resources=roots.map(root=>({ref:resourceRef(root),domain:'terrain' as const,name:'Retained exact input subset '+root.id,definition:{href:'docs/research/tryfan-qualified-query-inputs.json',selector:root.id},rights:root.family==='welsh-regional'?TRYFAN_PRODUCT.rights:AWS_VISUAL_PRODUCT.rights,inputs:[productResources[root.family==='welsh-regional'?2:0].ref]}));
  const defs: SemanticDefinition[]=['slope','area-ratio'].map(p=>({id:propertyId(p as Derived['property']),revision:'1',kind:'property',vocabulary:{id:'Research proof physical quantities',version:known('1')},label:'Represented heightfield '+p,meaning:'Qualified ordinary geometric quantity; source surface/epoch limitations remain in the claim.',reference:{href:report},valueKinds:['quantity']}));
  const gapDef: SemanticDefinition={id:'proof-property:current-mineral-exposure-fraction',revision:'1',kind:'property',vocabulary:{id:'Research proof physical quantities',version:known('1')},label:'Current exposed mineral fraction',meaning:'Unsupported by the retained terrain quantities or coarse cover/habitat summary; not inferred in this proof.',reference:{href:'docs/atlas/source-native-semantic-comparison.md'},valueKinds:['fraction']};
  const gapContext: ClaimContext={support:{geometry:{kind:'native-point',crs,coordinates:probe.centre},meaning:'Unanswered physical question at query location, not a fabricated exposure observation.',grain:unknown('No validated fine/current fractional exposure claim')},time:[{role:'asserted-validity',extent:{kind:'unknown',reason:'No dated validated current exposure inference'}}],evidence:{modes:['interpreted-mapping'],description:'Coverage-gap assessment from retained comparison; no exposure classification performed.',inputs:[],completeness:'partial',limitations:'Terrain is shape, broad classification is not fine/current exposure.',processing:[]}};
  const gap: SemanticClaim={id:'claim:unsupported-exposure',revision:'1',native:{property:{id:gapDef.id,revision:'1'},fields:{requested:'current mineral exposure fraction'}},result:{kind:'gap',reason:'unsupported',explanation:'No supported fine/current mineral-exposure fraction. Missing classification does not mean mineral absent.'},record:{href:report}};
  function inputRoot(result: Derived): Root {
    const use=result.receipt.inputs[0];
    if (use.kind==='resource') return roots.find(r=>resourceRef(r).id===use.id && r.revision===use.revision)!;
    return inputRoot(results.find(r=>r.claim.id===use.id && r.claim.revision===use.revision)!);
  }
  const outputResources: SemanticResource[]=results.map(r=>({ref:{kind:'product',id:'derived-product:'+r.claim.id,revision:known(r.claim.revision)},domain:'semantics',name:r.property+' result artifact/evidence collection',definition:{href:record,selector:r.receipt.id},rights:inputRoot(r).family==='welsh-regional'?TRYFAN_PRODUCT.rights:AWS_VISUAL_PRODUCT.rights,inputs:[resourceRef(inputRoot(r))]}));
  return {contract:'atlas-semantic-evidence/v1',resources:[awsSource,...productResources,...resources,...outputResources],definitions:[...defs,gapDef],mappings:[],collections:[...results.map((r,i)=>({id:'collection:'+r.claim.id,revision:r.claim.revision,product:outputResources[i].ref,context:r.context,representation:'records' as const,claims:[r.claim]})),{id:'collection:unsupported-exposure',revision:'1',product:productResources[0].ref,context:gapContext,representation:'records',claims:[gap]}]};
}

/** Finite two-stage receipt checks, not a general DAG validator/workflow engine. */
export function validateSlice(results: Derived[],roots: Root[]): string[] {
  const issues:string[]=[];
  for(const r of results){
    const rec=r.receipt;
    if(!rec.id || !rec.method || !rec.methodRevision || rec.inputs.length!==1)issues.push('Receipt identity/method/single direct input required');
    for(const use of rec.inputs){
      if(!use.id || !use.revision || !use.role)issues.push('Exact input identity/revision/role required');
      if(use.spatial.crs!=='EPSG:27700' || use.spatial.bounds.length!==4 || use.spatial.bounds.some(x=>!Number.isFinite(x)) || use.spatial.bounds[0]>use.spatial.bounds[2] || use.spatial.bounds[1]>use.spatial.bounds[3])issues.push('Invalid actual-use spatial scope');
      if(use.temporal.kind==='unknown' && !use.temporal.reason)issues.push('Unknown temporal scope needs reason');
      if(r.property==='slope'){
        if(use.kind!=='resource' || !roots.some(x=>resourceRef(x).id===use.id && x.revision===use.revision))issues.push('Slope root revision unavailable');
      }else{
        if(use.kind!=='claim' || !results.some(x=>x.property==='slope' && x.claim.id===use.id && x.claim.revision===use.revision && x.probe===r.probe))issues.push('Area ratio must use exact acyclic upstream slope');
      }
    }
  }
  return issues;
}
