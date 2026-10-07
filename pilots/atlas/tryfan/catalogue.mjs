// S1 registration only: no pixel reader, claim resolver, derivation or selection.
import { readFileSync, statSync } from 'node:fs';
import { resolve, extname } from 'node:path';
import { createServer } from 'vite';
import { FORMAT, encode, sha, refKey, byId, json, safePath, fields, requireThat } from './identity.mjs';
export const ROOT = resolve(import.meta.dirname, '../../..');
export const DATA = resolve(ROOT, '../meridian-data');
export const PLAN = 'docs/research/tryfan-regional-pilot-plan.json';
const PLAN_SHA = 'd9b9c99cb5d0277998439bc51c28990643e6c0feb9c2361b0258ba46ca5ebf46';
const CAPS = { registration: true, queries: false, derivations: false, serving: false, mixedFamilyUpdate: false };
export function frozenPlan() {
  requireThat(sha(readFileSync(resolve(ROOT,PLAN))) === PLAN_SHA, 'plan-drift', 'Frozen pilot plan changed');
  return json(resolve(ROOT,PLAN));
}
async function nativeMetadata(plan) {
  for (const receipt of plan.metadataReceipts) requireThat(sha(readFileSync(resolve(ROOT,receipt.path))) === receipt.sha256,
    'metadata-drift', 'Metadata receipt changed: ' + receipt.path);
  const server = await createServer({ configFile:false, appType:'custom', logLevel:'silent', root:ROOT, server:{middlewareMode:true} });
  try {
    const regional = await server.ssrLoadModule('/src/atlas/terrain/metadata/tryfanTerrainProof.ts');
    // Validate the established hierarchy registration, but do not run selection.
    regional.createTryfanTerrainProof();
    const common = await server.ssrLoadModule('/src/atlas/terrain/metadata/awsVisualTerrainProduct.ts');
    const fixtures = (await server.ssrLoadModule('/scripts/atlas/semantic-evidence/fixtures.ts')).SEMANTIC_EVIDENCE_FIXTURES;
    const errors = (await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts')).validateSemanticEvidence(fixtures);
    requireThat(errors.length === 0, 'contract-invalid', errors.join('; '));
    const semantic = id => ({ resources: fixtures.resources.filter(x => [id,id+'-source'].includes(x.ref.id)),
      exampleClaimContext: fixtures.collections.find(x => x.product.id === id).context,
      contextQualification:'Example-specific retained fixture context; not blanket coverage/time for every registered cell or feature' });
    const lab = json(resolve(ROOT,'docs/earth-lab/tryfan-010-observed-natural-colour.json'));
    const observation = { ...lab.selected_observation }; delete observation.candidate_aoi_scl;
    return JSON.parse(JSON.stringify({
      'terrain-common': { product:common.AWS_VISUAL_PRODUCT },
      'terrain-regional': { source:regional.TRYFAN_SOURCE, product:regional.TRYFAN_PRODUCT,
        levels:json(resolve(ROOT,'src/atlas/terrain/metadata/tryfanProductRecord.json')).levels },
      worldcover:semantic('worldcover'), nrw:semantic('nrw-phase1'),
      appearance:{ observation, aoi:lab.aoi, processing:lab.processing, rights:lab.licence,
        semantics:lab.semantics, visualAcceptance:lab.visual_acceptance }
    }));
  } finally { await server.close(); }
}
function familyFor(path) {
  if (path.includes('aws/')) return 'terrain-common';
  if (path.includes('welsh')) return 'terrain-regional';
  if (path.includes('worldcover')) return 'worldcover';
  if (path.includes('nrw-')) return 'nrw';
  return 'appearance';
}
export async function buildRetained(dataRoot = DATA) {
  const plan = frozenPlan(), metadata = await nativeMetadata(plan);
  const sources=[], products=[], representations=[], families=[], files=[...plan.assets], locators={};
  for (const set of plan.assetSets) {
    const manifestFile = safePath(dataRoot,set.manifest);
    requireThat(sha(readFileSync(manifestFile)) === set.sha256, 'hash-mismatch', 'Welsh manifest changed');
    const entries = json(manifestFile)[set.entries];
    requireThat(entries.length === set.count && entries.reduce((s,e)=>s+e.bytes,0) === set.bytes, 'inventory-mismatch', 'Welsh inventory differs');
    files.push(...entries.map(e => ({ ...e, path:set.base+'/'+e.path, role:'Welsh complete terrain tile' })));
  }
  for (const binding of plan.registrationBindings) {
    const sourceRef = { kind:'source', ...binding.source }, productRef = { kind:'product', ...binding.product };
    const source=refKey(sourceRef), product=refKey(productRef), representation='representation:'+binding.family;
    sources.push({id:source,ref:sourceRef}); products.push({id:product,ref:productRef,source});
    const defs = [{id:representation,description:binding.representation}];
    if(binding.family==='terrain-regional') defs.unshift({id:'representation:welsh-native-dtm',description:'Original 1m EPSG:27700 source DTM; unknown vertical reference, not Terrarium delivery'});
    if(binding.family==='appearance') defs.unshift(
      {id:'representation:sentinel-july-native-rgb',description:'Exact retained B02/B03/B04 405x405 10m EPSG:32630 DN windows; no prepared display transfer'},
      {id:'representation:sentinel-july-native-scl',description:'Exact retained SCL 203x203 20m EPSG:32630 categorical mask; independent sampling from RGB'});
    if(binding.family==='appearance') defs[defs.length-1].id='lab010-observed-natural-colour-v1@'+plan.families.find(f=>f.id==='appearance').preparedIdentity;
    if(binding.family==='worldcover') defs[0].id='worldcover-v200-2021-N51W006-native-window';
    for(const d of defs) representations.push({...d,product,metadataReceipt:binding.metadata});
    families.push({id:binding.family,source,product,representations:defs.map(d=>d.id),
      qualification:plan.families.find(x=>x.id===binding.family),nativeMetadata:metadata[binding.family]});
  }
  const artifacts = new Map();
  for (const file of files) {
    const family=familyFor(file.path), descriptor=families.find(x=>x.id===family), id='sha256:'+file.sha256;
    let representation=descriptor.representations.at(-1);
    if(file.role==='Welsh source') representation='representation:welsh-native-dtm';
    if(file.role==='Native July RGB/SCL') representation=file.path.includes('SCL_')?'representation:sentinel-july-native-scl':'representation:sentinel-july-native-rgb';
    const use={family,source:descriptor.source,product:descriptor.product,representation,role:file.role};
    const tile=/tiles\/(\d+)\/(\d+)\/(\d+)\.png$/.exec(file.path);
    if (tile) use.tile = { scheme:'xyz',crs:'EPSG:3857',z:+tile[1],x:+tile[2],y:+tile[3] };
    const alias='meridian-data://'+file.path;
    const artifact=artifacts.get(id) ?? {id,sha256:file.sha256,bytes:file.bytes,kind:extname(file.path).slice(1),aliases:[],uses:[]};
    artifact.aliases.push(alias);artifact.uses.push(use);artifacts.set(id,artifact);locators[id] ??= file.path;
  }
  const catalogue={ schema:'atlas-tryfan-retained-catalogue/v1',basis:{plan:PLAN,sha256:PLAN_SHA,metadataReceipts:plan.metadataReceipts},
    sources:byId(sources),products:byId(products),representations:byId(representations),families:byId(families),
    artifacts:byId([...artifacts.values()].map(a=>({...a,aliases:a.aliases.sort(),uses:a.uses.sort((x,y)=>encode(x).localeCompare(encode(y)))}))) };
  validateCatalogue(catalogue);verifyArtifacts(catalogue,locators,dataRoot);
  return { catalogue,locators,core:{ crs:plan.scope.crs,bounds:plan.scope.bounds,boundary:plan.scope.boundary },capabilities:CAPS };
}
function collection(records, name) {
  requireThat(Array.isArray(records) && records.length>0, 'invalid-schema', name+' must be a nonempty collection');
  const map=new Map();
  for (const record of records) {
    requireThat(typeof record.id==='string' && record.id.length && !map.has(record.id), 'duplicate-identity', name+' duplicate/missing identity');
    map.set(record.id,record);
  }
  return map;
}
function entity(ref, kind) {
  fields(ref,['kind','id','revision']);fields(ref.revision,['status'],['value','reason']);
  requireThat(ref.kind===kind && typeof ref.id==='string' && ref.id &&
    ((ref.revision.status==='known' && typeof ref.revision.value==='string' && ref.revision.value && !Object.hasOwn(ref.revision,'reason')) ||
     (ref.revision.status==='unknown' && typeof ref.revision.reason==='string' && ref.revision.reason && !Object.hasOwn(ref.revision,'value'))), 'invalid-reference', 'Invalid native entity reference');
}
export function validateCatalogue(c) {
  fields(c,['schema','basis','sources','products','representations','families','artifacts']);
  requireThat(c.schema==='atlas-tryfan-retained-catalogue/v1', 'unknown-catalogue-schema', 'Unsupported catalogue schema');
  encode(c); // Reject undefined/nonfinite/non-JSON state before hashing.
  fields(c.basis,['plan','sha256','metadataReceipts']);
  requireThat(/^[a-f0-9]{64}$/.test(c.basis.sha256) && Array.isArray(c.basis.metadataReceipts), 'invalid-schema', 'Invalid registration basis');
  const receiptPaths=new Set();
  for(const receipt of c.basis.metadataReceipts) {fields(receipt,['path','sha256']);requireThat(typeof receipt.path==='string' &&
    !receipt.path.includes('..') && !receipt.path.includes('meridian-private') && /^[a-f0-9]{64}$/.test(receipt.sha256) && !receiptPaths.has(receipt.path),
    'invalid-reference','Invalid/duplicate metadata receipt');receiptPaths.add(receipt.path);}
  const sources=collection(c.sources,'sources'),products=collection(c.products,'products'),reps=collection(c.representations,'representations'),families=collection(c.families,'families');
  const ref=(map,id)=>requireThat(map.has(id),'invalid-reference','Dangling reference: '+id);
  for (const s of sources.values()) { fields(s,['id','ref']);entity(s.ref,'source');requireThat(s.id===refKey(s.ref),'invalid-reference','Source key differs'); }
  for (const p of products.values()) { fields(p,['id','ref','source']);entity(p.ref,'product');ref(sources,p.source);requireThat(p.id===refKey(p.ref),'invalid-reference','Product key differs'); }
  for (const r of reps.values()) { fields(r,['id','product','description','metadataReceipt']);ref(products,r.product);requireThat(typeof r.description==='string' && r.description,'invalid-schema','Representation meaning missing');ref(receiptPaths,r.metadataReceipt); }
  for (const f of families.values()) {
    fields(f,['id','source','product','representations','qualification','nativeMetadata']);ref(sources,f.source);ref(products,f.product);
    requireThat(products.get(f.product).source===f.source && Array.isArray(f.representations) && f.representations.length &&
      f.nativeMetadata && Object.keys(f.nativeMetadata).length && f.qualification.id===f.id,'invalid-reference','Incomplete family registration');
    for (const r of f.representations) { ref(reps,r);requireThat(reps.get(r).product===f.product,'invalid-reference','Family representation/product mismatch'); }
  }
  const aliases=new Set();
  for (const a of collection(c.artifacts,'artifacts').values()) {
    fields(a,['id','sha256','bytes','kind','aliases','uses']);
    requireThat(/^[a-f0-9]{64}$/.test(a.sha256) && a.id==='sha256:'+a.sha256 && Number.isSafeInteger(a.bytes) && a.bytes>0,
      'invalid-artifact','Invalid immutable materialization');
    requireThat(typeof a.kind==='string' && a.kind.length,'invalid-artifact','Materialization kind missing');
    requireThat(Array.isArray(a.aliases) && a.aliases.length && Array.isArray(a.uses) && a.uses.length,'invalid-artifact','Missing materialization relations');
    for (const alias of a.aliases) { requireThat(typeof alias==='string' && alias.startsWith('meridian-data://') && !aliases.has(alias),'duplicate-identity','Duplicate/invalid logical alias');aliases.add(alias); }
    for (const use of a.uses) {
      fields(use,['family','source','product','representation','role'],['tile']);ref(families,use.family);ref(sources,use.source);ref(products,use.product);ref(reps,use.representation);
      const f=families.get(use.family);
      requireThat(f.source===use.source && f.product===use.product && f.representations.includes(use.representation) && typeof use.role==='string' && use.role,
        'invalid-reference','Artifact relation mismatch');
      if(use.tile) {fields(use.tile,['scheme','crs','z','x','y']);requireThat(use.tile.scheme==='xyz' && use.tile.crs==='EPSG:3857' &&
        ['z','x','y'].every(k=>Number.isSafeInteger(use.tile[k]) && use.tile[k]>=0),'invalid-artifact','Invalid tile partition');}
    }
  }
  return c;
}
export function canonicalCatalogue(c) {
  validateCatalogue(c);
  const clone=structuredClone(c);
  for (const key of ['sources','products','representations','families','artifacts']) clone[key]=byId(clone[key]);
  for (const f of clone.families) f.representations.sort();
  clone.basis.metadataReceipts.sort((a,b)=>a.path<b.path?-1:a.path>b.path?1:0);
  for (const a of clone.artifacts) { a.aliases.sort();a.uses.sort((x,y)=>encode(x)<encode(y)?-1:encode(x)>encode(y)?1:0); }
  return clone;
}
export function verifyArtifacts(c, locators, root) {
  validateCatalogue(c);requireThat(locators && typeof locators==='object','invalid-locator','Missing locator map');
  let bytes=0;
  for (const a of c.artifacts) {
    const path=safePath(root,locators[a.id]);
    requireThat(statSync(path).isFile() && statSync(path).size===a.bytes && sha(readFileSync(path))===a.sha256,
      'hash-mismatch','Retained bytes differ: '+a.id);
    bytes+=a.bytes;
  }
  return {artifacts:c.artifacts.length,bytes};
}
export function seed(registration, parent=null) {
  return {format:FORMAT,semanticContract:'atlas-semantic-evidence/v1',capabilities:{...CAPS},core:registration.core,
    parent,catalogue:canonicalCatalogue(registration.catalogue)};
}
