import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, copyFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, basename, sep } from 'node:path';
import { spawnSync, spawn } from 'node:child_process';
import { buildRetained, seed, validateCatalogue, verifyArtifacts, ROOT, DATA } from '../catalogue.mjs';
import { encode, sha, refKey, safePath } from '../identity.mjs';
import { register, stage, publish, load, generationId, recoverLock, currentId, rollback } from '../generations.mjs';
let retained,workspace;
before(async()=>{retained=await buildRetained();workspace=mkdtempSync(join(tmpdir(),'meridian-s1-tests-'));});
after(()=>{
  assert.ok(resolve(workspace).startsWith(resolve(tmpdir())+sep) && basename(workspace).startsWith('meridian-s1-tests-'));
  rmSync(workspace,{recursive:true,force:true});
});
function fixture(name='case') {
  const base=mkdtempSync(join(workspace,name)),root=join(base,'data'),store=join(base,'store');mkdirSync(root);
  const bytes=Buffer.from('Labelled operational fixture. Not new terrain or source release.\n');
  writeFileSync(join(root,'fixture.txt'),bytes);
  const artifact={id:'sha256:'+sha(bytes),sha256:sha(bytes),bytes:bytes.length,kind:'txt',aliases:['meridian-data://operational-fixture'],
    uses:[{family:'terrain-common',source:retained.catalogue.families.find(f=>f.id==='terrain-common').source,
      product:retained.catalogue.families.find(f=>f.id==='terrain-common').product,representation:'representation:terrain-common',role:'Labelled operational test only'}]};
  const registration={...structuredClone(retained),catalogue:{...structuredClone(retained.catalogue),artifacts:[artifact]},locators:{[artifact.id]:'fixture.txt'}};
  const path=join(base,'fixture.json');writeFileSync(path,encode(registration));
  return {base,root,store,registration,path};
}
function err(code) {return e=>e.code===code;}
const worker=join(ROOT,'pilots/atlas/tryfan/tests/worker.mjs');
function child(f,mode,point) {return spawnSync(process.execPath,[worker,mode,f.store,f.root,f.path,...(point?[point]:[])],{encoding:'utf8'});}
function first(f) {return register(f.store,seed(f.registration),f.registration.locators,{dataRoot:f.root});}
function candidate(f,parent) {return seed(f.registration,parent);}

test('all five frozen families/310 files, bytes, identities and rights retained',()=>{
  assert.equal(retained.catalogue.families.length,5);assert.equal(retained.catalogue.artifacts.length,310);
  assert.deepEqual(verifyArtifacts(retained.catalogue,retained.locators,DATA),{artifacts:310,bytes:42473107});
  assert.equal(retained.catalogue.families.find(f=>f.id==='appearance').qualification.observationUTC,'2026-07-12T11:33:31.024Z');
  assert.equal(retained.catalogue.families.find(f=>f.id==='terrain-common').nativeMetadata.product.rights.licence.status,'unknown');
  assert.equal(retained.catalogue.families.find(f=>f.id==='worldcover').nativeMetadata.resources[1].rights.licence.value,'CC-BY-4.0');
});
test('actual retained evidence reproduced by a separately constructed process',()=>{
  const store=join(workspace,'actual');const registered=register(store,seed(retained),retained.locators);
  const fresh=spawnSync(process.execPath,[join(ROOT,'pilots/atlas/tryfan/cli.mjs'),'validate','--store',store],{encoding:'utf8'});
  assert.equal(fresh.status,0,fresh.stderr);const value=JSON.parse(fresh.stdout);
  assert.equal(value.generation,registered.generation);assert.equal(value.verification.artifacts,310);assert.equal(value.capabilities.queries,false);
});
test('registration order/object order never changes logical identity',()=>{
  const original=seed(retained),shuffled=structuredClone(original);
  for(const key of ['sources','products','families','representations','artifacts'])shuffled.catalogue[key].reverse();
  shuffled.catalogue.basis.metadataReceipts.reverse();
  assert.equal(generationId(shuffled),generationId(original));
});
test('relocation/rebuild in another data root preserves identity',()=>{
  const f=fixture(),g=first(f),other=join(f.base,'relocated');mkdirSync(other);copyFileSync(join(f.root,'fixture.txt'),join(other,'moved.txt'));
  const map={[f.registration.catalogue.artifacts[0].id]:'moved.txt'};
  assert.equal(load(f.store,{dataRoot:other,locators:map}).generation,g.generation);
  assert.equal(generationId(seed({...f.registration,locators:map})),g.generation);
});
test('missing and mismatched required artifacts fail explicitly without publication',()=>{
  const f=fixture();const id=f.registration.catalogue.artifacts[0].id;
  assert.throws(()=>verifyArtifacts(f.registration.catalogue,{[id]:'missing'},f.root),err('artifact-unavailable'));
  writeFileSync(join(f.root,'fixture.txt'),'Corrupt ONLY operational fixture');
  assert.throws(()=>first(f),err('hash-mismatch'));assert.equal(existsSync(join(f.store,'current.json')),false);
});
test('duplicate source or conflicting artifact identity is rejected',()=>{
  const c=structuredClone(retained.catalogue);c.sources.push(c.sources[0]);assert.throws(()=>validateCatalogue(c),err('duplicate-identity'));
  const d=structuredClone(retained.catalogue);d.artifacts[0].id='sha256:'+'0'.repeat(64);assert.throws(()=>validateCatalogue(d),err('invalid-artifact'));
});
test('dangling product, representation, family and metadata references fail',()=>{
  const c=structuredClone(retained.catalogue);c.representations[0].metadataReceipt='absent';assert.throws(()=>validateCatalogue(c),err('invalid-reference'));
  for(const field of ['source','product','representation','family']) {
    const c=structuredClone(retained.catalogue);c.artifacts[0].uses[0][field]='missing';assert.throws(()=>validateCatalogue(c),err('invalid-reference'));
  }
});
test('unknown schema, capability, nonfinite value and unsafe locator fail',()=>{
  const f=fixture(),value=seed(f.registration);value.catalogue.schema='future';assert.throws(()=>generationId(value),err('unknown-catalogue-schema'));
  const v=seed(f.registration);v.format='future';assert.throws(()=>generationId(v),err('unknown-generation-schema'));
  const parent=seed(f.registration);parent.parent=['0'.repeat(64)];assert.throws(()=>generationId(parent),err('invalid-reference'));
  const cap=seed(f.registration);cap.capabilities.serving=true;assert.throws(()=>generationId(cap),err('unsupported-capability'));
  const n=seed(f.registration);n.catalogue.artifacts[0].bytes=NaN;assert.throws(()=>generationId(n));
  for(const path of ['../fixture.txt','C:/private','meridian-private/file'])assert.throws(()=>safePath(f.root,path),err('invalid-locator'));
});
test('first root and immutable generation are inspectable; loader detects mutation',()=>{
  const f=fixture(),g=first(f),path=join(f.store,'generations',g.generation+'.json');
  const body=readFileSync(path);assert.equal(sha(body),g.generation);assert.equal(currentId(f.store),g.generation);
  // A direct external write is outside the supported API; checksum must catch it.
  writeFileSync(path,'{}');assert.throws(()=>load(f.store,{dataRoot:f.root}),err('generation-integrity'));
});
test('new administrative generation preserves byte-identical historical generation',()=>{
  const f=fixture(),g0=first(f),old=readFileSync(join(f.store,'generations',g0.generation+'.json'),'utf8');
  const g1=register(f.store,candidate(f,g0.generation),f.registration.locators,{dataRoot:f.root});
  assert.notEqual(g1.generation,g0.generation);assert.equal(load(f.store,{generation:g0.generation,dataRoot:f.root}).value.parent,null);
  assert.equal(readFileSync(join(f.store,'generations',g0.generation+'.json'),'utf8'),old);
  rollback(f.store,g0.generation,{dataRoot:f.root});assert.equal(currentId(f.store),g0.generation);
});
test('staging is not publication; explicit publish validates ancestry',()=>{
  const f=fixture(),g0=first(f),s=stage(f.store,candidate(f,g0.generation),f.registration.locators,{dataRoot:f.root});
  assert.equal(currentId(f.store),g0.generation);assert.equal(s.published,false);
  const g1=publish(f.store,s.operation,{dataRoot:f.root});assert.equal(currentId(f.store),g1.generation);
  assert.throws(()=>publish(f.store,s.operation,{dataRoot:f.root}),err('publication-conflict'));
});
for(const point of ['after-staging','after-validation','before-switch'])test('abrupt writer exit '+point+' preserves old root and requires explicit recovery',()=>{
  const f=fixture(),g0=first(f);f.registration.parent=g0.generation;writeFileSync(f.path,encode(f.registration));
  const failed=child(f,'write',point);assert.equal(failed.status,91,failed.stderr);
  const recovered=child(f,'read');assert.equal(recovered.status,0,recovered.stderr);assert.equal(JSON.parse(recovered.stdout).generation,g0.generation);
  const lock=JSON.parse(readFileSync(join(f.store,'writer.lock'),'utf8'));
  assert.throws(()=>register(f.store,candidate(f,g0.generation),f.registration.locators,{dataRoot:f.root}),err('writer-locked'));
  assert.throws(()=>recoverLock(f.store,'00000000-0000-0000-0000-000000000000'),err('lock-conflict'));
  recoverLock(f.store,lock.operation);const retry=publish(f.store,lock.operation,{dataRoot:f.root});
  assert.notEqual(retry.generation,g0.generation);assert.equal(load(f.store,{generation:g0.generation,dataRoot:f.root}).generation,g0.generation);
});
test('live/unknown writer PID cannot be reclaimed',()=>{
  const f=fixture();mkdirSync(f.store);const operation='00000000-0000-0000-0000-000000000000';
  writeFileSync(join(f.store,'writer.lock'),encode({operation,pid:process.pid}));assert.throws(()=>recoverLock(f.store,operation),err('writer-alive-or-unknown'));
});
test('real reader during root switch sees complete old or complete new generation',async()=>{
  const f=fixture(),g0=first(f);
  const reader=spawn(process.execPath,[worker,'race',f.store,f.root,f.path],{stdio:['ignore','pipe','pipe']});
  let out='',error='',readyResolve;const ready=new Promise(resolve=>readyResolve=resolve);
  reader.stdout.on('data',d=>out+=d);reader.stderr.on('data',d=>{error+=d;if(error.includes('READY'))readyResolve();});
  const done=new Promise(resolve=>reader.on('exit',resolve));
  await ready;
  const g1=register(f.store,candidate(f,g0.generation),f.registration.locators,{dataRoot:f.root});
  assert.equal(await done,0,error);const values=JSON.parse(out);assert.equal(values.length,60);
  assert.ok(values.every(id=>[g0.generation,g1.generation].includes(id)));
  assert.ok(values.includes(g0.generation) && values.includes(g1.generation));
});
test('absent root, malformed root, missing generation, malformed content reject safely',()=>{
  const f=fixture();assert.throws(()=>load(f.store,{dataRoot:f.root}),err('store-absent'));first(f);
  writeFileSync(join(f.store,'current.json'),'broken');assert.throws(()=>load(f.store,{dataRoot:f.root}),err('invalid-published-root'));
  assert.throws(()=>load(f.store,{generation:'0'.repeat(64),dataRoot:f.root}),err('generation-missing'));
  const body='{not json',id=sha(body);writeFileSync(join(f.store,'generations',id+'.json'),body);
  assert.throws(()=>load(f.store,{generation:id,dataRoot:f.root}),err('malformed-generation'));
});
test('write-once object conflict cannot replace a generation or switch current',()=>{
  const f=fixture(),g0=first(f),v=candidate(f,g0.generation),id=generationId(v);
  writeFileSync(join(f.store,'generations',id+'.json'),'corrupt operational fixture');
  assert.throws(()=>register(f.store,v,f.registration.locators,{dataRoot:f.root}),err('immutable-conflict'));assert.equal(currentId(f.store),g0.generation);
});
test('retained source hashes still match after all fixture operations',()=>{
  assert.equal(verifyArtifacts(retained.catalogue,retained.locators,DATA).bytes,42473107);
});

test('fresh independent retained construction yields the same generation identity',()=>{
  const rebuilt=spawnSync(process.execPath,[join(ROOT,'pilots/atlas/tryfan/cli.mjs'),'register','--store',join(workspace,'independent-rebuild')],{encoding:'utf8'});
  assert.equal(rebuilt.status,0,rebuilt.stderr);assert.equal(JSON.parse(rebuilt.stdout).generation,generationId(seed(retained)));
});
test('required locator closure and parent integrity are validated on restart',()=>{
  const f=fixture(),g0=first(f),g1=register(f.store,candidate(f,g0.generation),f.registration.locators,{dataRoot:f.root});
  assert.throws(()=>load(f.store,{dataRoot:f.root,locators:{}}),err('invalid-locator'));
  writeFileSync(join(f.store,'generations',g0.generation+'.json'),'broken historical fixture');
  assert.throws(()=>load(f.store,{generation:g1.generation,dataRoot:f.root}),err('generation-integrity'));
});

test('store paths cannot target retained inputs, repository production or private data',()=>{
  for(const store of [ROOT,join(ROOT,'src'),DATA,join(DATA,'sources/atlas'),join(DATA,'meridian-private')])
    assert.throws(()=>currentId(store),err('invalid-store'));
});
