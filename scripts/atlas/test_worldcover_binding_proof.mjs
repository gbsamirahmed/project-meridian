import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { contract,readRaster,build,checkState,instantiate,answer,logicalQueries,encode,sha,ROOT } from './worldcover-binding-proof/runtime.mjs';
const {fixtures,validate}=await contract();const reader=readRaster();const state=build(reader,fixtures);
const col=state.bundle.collections[0];
test('exact retained SHA grid and seven codes preserved',()=>{
 assert.equal(reader.sources['tryfan-worldcover.tif'].sha256,'9a0ad7162b1fb5fdc276a90c219c8d1d1daa0e83650ccd22d1dfbb51cbe98f6d');
 assert.equal(reader.grid.cells,185036);assert.equal(reader.grid.crs,'EPSG:4326');assert.deepEqual(reader.grid.nativeCodes,[10,20,30,50,60,80,100]);
});
test('shared native templates, not185036 heavyweight objects, validate frozen v1',()=>{
 assert.equal(col.claims.length,8);assert.equal(col.binding.codes.length,8);checkState(state,validate);assert.deepEqual(validate(state.bundle),[]);
});
test('all real point instances retain native category and exact cell support',()=>{
 for(const p of reader.points){const q=instantiate(state,p);assert.equal(q.native.fields.code,p.code);assert.equal(q.result.value.term.id,'wc:'+p.code);
  assert.deepEqual(q.context.support.geometry.bounds,p.cellBounds);const b=structuredClone(state.bundle);b.collections[0]={...col,claims:[q]};delete b.collections[0].binding;assert.deepEqual(validate(b),[]);}
});
test('frozen three patch class counts reproduce earlier native comparison',()=>{
 const old=JSON.parse(readFileSync(join(ROOT,'docs/atlas/semantic-comparison-results.json'),'utf8')).sites.tryfan.regions;
 for(const s of reader.supports.slice(0,3))assert.deepEqual(s.counts,Object.fromEntries(Object.entries(old[s.id].worldcover).map(([c,v])=>[c,v.cells])));
});
test('20m support has ten class30 assignments; larger summit has mixed native classes',()=>{
 assert.deepEqual(reader.supports[3].counts,{'30':10});assert.equal(reader.supports[0].counts['60'],28);
 assert.match(reader.supports[0].meaning,/not physical surface fractions/);assert.equal('fraction' in reader.supports[0],false);
});
test('qualified narrower/compatible mapping preserves direction, revision, loss and native claim',()=>{
 const a=answer(state,reader,'summit',{property:'common'});assert.equal(a.mapping.relationship,'narrower');assert.equal(a.native.native.fields.code,30);assert.ok(a.mapping.loss.length);
 const m=state.bundle.mappings.find(m=>m.id==='mapping:wc60');assert.equal(m.relationship,'compatible');assert.match(m.loss[0],/Soil\/sand\/rock/);
});
test('unmappable substrate preserves known native assertion without target assertion',()=>{
 const a=answer(state,reader,'summit',{property:'substrate'});assert.equal(a.kind,'unresolved');assert.equal(a.mapping.relationship,'unmappable');assert.equal(a.native.result.kind,'assertion');assert.equal(a.interpretation.disposition,'rejected');
});
test('2026 current state unavailable as a claim, while historical native2021 remains recoverable',()=>{
 const a=answer(state,reader,'summit',{time:'2026'});assert.equal(a.kind,'gap');assert.equal(a.reason,'unsupported');assert.equal(a.native.context.time[0].extent.value,'2021');assert.equal(a.native.context.time[1].extent.kind,'unknown');
 assert.equal(state.bundle.resources.find(r=>r.ref.id==='worldcover').dates[0].extent.value,'2022');
});
test('classification and scoped product validation never become observation/local confidence',()=>{
 const a=answer(state,reader,'summit');assert.deepEqual(a.native.context.evidence.modes,['classification']);
 assert.equal(a.native.context.quality[0].scope.kind,'product');assert.equal(a.native.context.quality[0].kind,'validation');assert.equal(a.native.context.quality[0].value.value,76.7);
});
test('geographic support miss vs unavailable raster vs native nodata stay distinct',()=>{
 assert.equal(answer(state,reader,'outside').reason,'outside-support');assert.deepEqual(answer(state,reader,'outside').query,[264800,357700]);
 const absent=readRaster(join(tmpdir(),'meridian-explicitly-nonexistent-retained-source'));assert.equal(answer(state,absent,'summit').kind,'unavailable');
 const p={...reader.points[0],code:0};const q=instantiate(state,p);assert.equal(q.native.fields.code,0);assert.equal(q.result.reason,'not-classified');
 assert.equal(reader.grid.nativeCodes.includes(0),false); // No real code0 encountered: adapter test only.
});
test('unknown probe names and unbound synthetic values do not fabricate categories',()=>{
 assert.equal(answer(state,reader,'unregistered').reason,'unsupported');assert.equal(instantiate(state,{...reader.points[0],code:255}).reason,'not-classified');
});
test('real overlapping NRW habitat and WorldCover persist independently with different support/time',()=>{
 const q=logicalQueries(state,reader);assert.equal(q.coexistence.worldcover.native.native.fields.code,30);
 const nrw=q.coexistence.nrw;assert.equal(nrw.claims.length,3);assert.equal(nrw.context.time[0].extent.kind,'unknown');
 assert.equal(q.coexistence.nativeFeatureIntersections.find(f=>f.id==='486832').pointContains,true);
 assert.equal(nrw.claims[2].native.fields.phase1_code,'D.1.1');assert.deepEqual(nrw.context.evidence.modes,['survey-inventory','classification']);
});
test('invalid native binding/mapping/quality declarations rejected without changing contract',()=>{
 const b=structuredClone(state);b.bundle.collections[0].binding.codes[0].claim.id='missing';assert.throws(()=>checkState(b,validate),/binding/);
 const c=structuredClone(state);c.bundle.mappings[0].relationship='unmappable';assert.throws(()=>checkState(c,validate),/mapping disposition/);
 const d=structuredClone(state);d.bundle.collections[0].context.quality[0].kind='confidence';assert.throws(()=>checkState(d,validate),/confidence cannot borrow/);
});
test('real subprocess restart and deterministic reconstruction preserve logical queries and native codes',()=>{
 const dir=mkdtempSync(join(tmpdir(),'meridian-wc-binding-'));
 try {
  const call=action=>{const p=spawnSync(process.execPath,['scripts/atlas/worldcover-binding-proof/cli.mjs',action,dir],{cwd:ROOT,encoding:'utf8'});assert.equal(p.status,0,p.stderr);return JSON.parse(p.stdout);};
  const a=call('build'),b=call('query'),c=call('build');assert.equal(a.publication.snapshot,b.snapshot);assert.equal(a.publication.snapshot,c.publication.snapshot);
  assert.deepEqual(a.logical,b.logical);assert.equal(a.logicalSha256,sha(encode(b.logical)));assert.equal(a.publication.bytes,Buffer.byteLength(encode(state)));
 }finally{rmSync(dir,{recursive:true,force:true});}
});
