import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync,writeFileSync,mkdtempSync,rmSync,existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join,resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { openEvidence,encode } from '../query.mjs';
import { load,STORE,currentId } from '../generations.mjs';
import { DATA,ROOT,verifyArtifacts } from '../catalogue.mjs';
import { sha } from '../identity.mjs';
import { instantiate } from '../semantic.mjs';
import { queryMatrix } from '../query-cli.mjs';
let e,snapshot,initialRoot;
const summit=[266405,359387],query=(property,extra={})=>e.query({point:summit,property,...extra});
before(async()=>{initialRoot=currentId(STORE);snapshot=load(STORE,{verify:false});e=await openEvidence();});
after(()=>e.close());
test('published S1 state pinned, read capabilities do not mislabel registration-only seed',()=>{
 assert.equal(e.generation,initialRoot);assert.equal(e.publishedCapabilities.queries,false);assert.equal(e.capabilities.nativeQueries,true);
});
test('retained native grid and finite vector inventory sizes',()=>{
 assert.equal(e.metadata.families.worldcover.grid.cells,185036);assert.equal(e.metadata.families.nrw.featureCount,193);assert.equal(e.metadata.families.nrw.codeCount,28);
 assert.equal(e.semantics.bundle.collections[0].claims.length,8);assert.equal(e.semantics.bundle.collections[1].claims.length,193);
});
test('WorldCover native30 exact parent cell and definition',async()=>{
 const r=(await query('worldcover-native',{time:'2021'})).records[0];assert.equal(r.claim.native.fields.code,30);assert.equal(r.claim.native.fields.label,'Grassland');
 assert.equal(r.claim.id,`claim:wc2021v200-N51W006-parent-r${r.cell.parentRow}-c${r.cell.parentColumn}`);assert.equal(r.context.support.geometry.kind,'native-rectangle');
 assert.equal(r.context.support.geometry.crs.identifier,'EPSG:4326');assert.equal(r.claim.result.value.kind,'category');
});
test('coordinate-to-cell deterministic and CRS84 equivalent',async()=>{
 const a=await query('worldcover-native');const b=await e.query({property:'worldcover-native',point:a.location.pointCRS84,crs:'OGC:CRS84'});
 assert.deepEqual(a.records[0].cell,b.records[0].cell);assert.equal(a.records[0].claim.id,b.records[0].claim.id);assert.equal(a.location.transform.axisOrder,'xy');
});
test('labelled code0 fixture remains not-classified, not detection or absence',()=>{
 const c=instantiate(e.semantics,{code:0,parentRow:0,parentColumn:0,cellBounds:[0,0,1,1]});
 assert.equal(c.result.reason,'not-classified');assert.equal(c.native.fields.code,0);assert.ok(!e.metadata.families.worldcover.grid.nativeCodes.includes(0));
});
test('unknown native code is not silently mapped',()=>{assert.equal(instantiate(e.semantics,{code:255}).reason,'not-classified');});
test('NRW native feature486832 fields and whole polygon support',async()=>{
 const r=(await query('nrw-native')).records.find(r=>r.feature.id==='486832');assert.ok(r);assert.equal(r.claim.native.fields.phase1_code,'D.1.1');
 assert.equal(r.claim.revision,'1');assert.equal(r.feature.namespace.id,'nrw-phase1');assert.equal(r.context.support.geometry.kind,'asset');assert.equal(r.membership.onBoundary,false);
 assert.equal(r.context.support.geometry.asset.selector,'objectid=486832');assert.equal(r.claim.native.fields.objectid,486832);
});
test('previous three NRW claim identities/bodies retained, only relocatable asset href changed',()=>{
 const old=JSON.parse(readFileSync(resolve(ROOT,'docs/research/tryfan-worldcover-binding-results.json'),'utf8')).logical.coexistence.nrw.claims;
 for(const c of old){const actual=e.semantics.bundle.collections[1].claims.find(n=>n.id===c.id);const expected=structuredClone(c);
 expected.context.support.geometry.asset.href=actual.context.support.geometry.asset.href;
 assert.deepEqual(actual,expected);}
});
test('all native NRW records have independent source terms; NA/mosaic remain unknown',()=>{
 const n=e.semantics.bundle.collections[1];assert.equal(new Set(n.claims.map(c=>c.native.term.id)).size,28);
 for(const c of n.claims.filter(c=>['NA','mosaic'].includes(c.native.fields.phase1_code))) {assert.equal(c.result.reason,'unknown');assert.equal(c.interpretation,undefined);assert.ok(c.native.fields.label);}
});
test('coexistence preserves Grassland and historical dry acid heath without winner',async()=>{
 const a=await query('coexisting-semantic');assert.deepEqual(a.records.map(r=>r.family),['worldcover','nrw']);
 assert.equal(a.records[0].claim.native.fields.code,30);assert.equal(a.records[1].claim.native.fields.phase1_code,'D.1.1');assert.equal(a.value,undefined);
});
test('common mapping direction loss and native category remain inspectable',async()=>{
 const r=(await query('worldcover-common')).records[0];assert.equal(r.claim.native.fields.code,30);assert.ok(r.mapping.loss.length);assert.equal(r.claim.interpretation.disposition,'qualified');
 assert.ok(['narrower','compatible','partial','broader'].includes(r.mapping.relationship));assert.ok(r.definitions.some(d=>d.id===r.mapping.target.id));
});
test('D5 Welsh/JNCC ambiguity survives existing crosswalk',()=>{
 const claim=e.semantics.bundle.collections[1].claims.find(c=>c.native.fields.phase1_code==='D.5');assert.equal(claim.interpretation.disposition,'unresolved');
 assert.equal(e.semantics.bundle.mappings.find(m=>m.id===claim.interpretation.mapping.id).relationship,'ambiguous');
});
test('distinct nominal epoch and survey times, not retrieval as observation',async()=>{
 const rs=(await query('coexisting-semantic')).records;assert.ok(rs[0].context.time.some(t=>t.role==='nominal-epoch' && t.extent.value==='2021'));
 assert.ok(rs[0].context.time.some(t=>t.role==='observation' && t.extent.kind==='unknown'));
 assert.deepEqual(rs[1].context.time.map(t=>[t.role,t.extent.kind]),[['survey','unknown']]);
});
test('unsupported current/physical/other properties never fall back',async()=>{
 for(const property of ['current-cover','physical-appearance','geology','derived-slope']) {const r=await query(property);assert.equal(r.result.reason,'unsupported');assert.deepEqual(r.records,[]);}
});
test('geological substrate rejected while native cover remains',async()=>{
 const r=(await query('geological-substrate')).records[0];assert.equal(r.result.reason,'unsupported');assert.equal(r.rejectedMapping.relationship,'unmappable');assert.equal(r.claim.native.fields.code,30);
});
test('incompatible evidence-family restriction explicitly rejected',async()=>{
 const r=await query('worldcover-native',{family:'nrw'});assert.equal(r.operationalStatus,'excluded-by-context');assert.equal(r.result.reason,'unsupported');assert.deepEqual(r.records,[]);
});
test('out of core and half-open east/north limits remain outside support',async()=>{
 for(const point of [[264800,357700],[267900,359000],[266000,360800]]) {const r=await e.query({property:'worldcover-native',point});assert.equal(r.result.reason,'outside-support');assert.deepEqual(r.records,[]);}
});
test('NRW rectangle support exact membership and source supports remain distinct',async()=>{
 const r=await query('nrw-native',{support:[266205,359187,266605,359587]});assert.ok(r.records.every(r=>r.membership.intersectionM2>=0));assert.ok(r.records.every(r=>r.context.support.geometry.asset.selector.startsWith('objectid=')));
});
test('native assignment counts reproduce old frozen proof, no physical fractions',async()=>{
 const old=JSON.parse(readFileSync(resolve(ROOT,'docs/research/tryfan-worldcover-binding-results.json'),'utf8'));
 const matrix=await queryMatrix(e);
 for(const id of ['Q07','Q07-20m','Q19','Q20']) {const row=matrix.find(q=>q.id===id).answer.records[0].assignments;assert.equal(Object.values(row.counts).reduce((a,b)=>a+b,0),row.cells);assert.ok(row.meaning.includes('not physical fractions'));}
 // Existing retained proof has its own schema; exact expected counts stored by native reader receipt.
 const names={'Q07':'summit','Q07-20m':'summit-20m','Q19':'southern-observer','Q20':'northern-context'};
 for(const [id,name] of Object.entries(names)){const a=matrix.find(q=>q.id===id).answer.records[0].assignments,b=old.logical.supports.find(s=>s.id===name);assert.deepEqual(a.counts,b.counts);assert.equal(a.cells,b.cells);}
});
test('provenance traces through generation, native artifact and product/source refs',async()=>{
 const rs=(await query('provenance')).records;
 for(const r of rs){assert.equal(r.provenance.generation,initialRoot);assert.equal(r.provenance.product.source,r.provenance.source.id);
 assert.ok(r.provenance.artifacts.some(a=>a.id==='sha256:'+a.sha256));assert.ok(r.provenance.representations.length);assert.ok(r.provenance.resources.length);}
});
test('rights remain linked not inferred',async()=>{
 const rs=(await query('coexisting-semantic')).records;for(const r of rs)assert.ok(r.provenance.rights.length);
 assert.ok(encode(rs[0].provenance.rights).includes('CC-BY'));assert.ok(encode(rs[1].provenance.rights).includes('OGL'));
});
test('dated appearance metadata retains source/prepared distinction without pixel query',async()=>{
 const r=(await query('appearance',{time:'2026-07-12'})).records[0];assert.equal(r.family,'appearance');assert.ok(r.metadata.observation);assert.equal(r.provenance.artifacts.length,7);
 assert.ok(r.qualification.includes('Metadata only'));assert.equal(r.claim,undefined);
});
test('requested other epoch does not imply current WorldCover or NRW inventory',async()=>{
 for(const property of ['worldcover-native','nrw-native']){const r=await query(property,{time:'2026'});assert.equal(r.records[0].result.reason,'unsupported');}
});
test('malformed request CRS coordinate support fails visibly',async()=>{
 for(const [request,code] of [[{point:summit,property:'nrw-native',crs:'EPSG:4326'},'invalid-crs'],[{point:[NaN,0],property:'nrw-native'},'invalid-coordinate'],[{point:[999,99],crs:'OGC:CRS84',property:'nrw-native'},'invalid-coordinate'],[{point:summit,property:'worldcover-support'},'invalid-support'],[{point:summit,property:'nrw-native',support:[1,2,3,4]},'invalid-support'],[{point:summit,property:'nrw-native',extra:true},'invalid-request']])
 await assert.rejects(()=>e.query(request),err=>err.code===code);
});
test('missing registered WC is unavailable and never substituted with NRW (Q17)',async()=>{
 const locators={...snapshot.locators};const a=snapshot.value.catalogue.artifacts.find(a=>a.uses.some(u=>u.family==='worldcover'));
 locators[a.id]='experiments/atlas/tryfan-regional-pilot-v1/missing-s2-worldcover-fixture.tif';assert.ok(!existsSync(resolve(DATA,locators[a.id])));
 const other=await openEvidence({locators});try {const r=await other.query({point:summit,property:'worldcover-native',time:'2021'});
 assert.equal(r.operationalStatus,'unavailable');assert.equal(r.records.length,1);assert.equal(r.records[0].family,'worldcover');assert.equal(r.records[0].claim,undefined);
 assert.ok((await other.query({point:summit,property:'nrw-native'})).records[0].claim);
 }finally{other.close();}
});
test('developer CLI reports missing NRW distinctly while WC stays available',()=>{
 const locators={...snapshot.locators},a=snapshot.value.catalogue.artifacts.find(a=>a.uses.some(u=>u.family==='nrw'));
 locators[a.id]='experiments/atlas/tryfan-regional-pilot-v1/missing-s2-nrw-fixture.json';assert.ok(!existsSync(resolve(DATA,locators[a.id])));
 const dir=mkdtempSync(join(tmpdir(),'meridian-s2-inspect-'));
 try {const path=join(dir,'locators.json');writeFileSync(path,encode(locators));
 const p=spawnSync(process.execPath,['pilots/atlas/tryfan/query-cli.mjs','inspect','--locators',path],{cwd:ROOT,encoding:'utf8',maxBuffer:1e6});
 assert.equal(p.status,0,p.stderr);const r=JSON.parse(p.stdout);assert.equal(r.native.nrw.status,'unavailable');assert.equal(r.native.worldcover.status,'available');
 }finally{assert.ok(resolve(dir).startsWith(resolve(tmpdir(),'meridian-s2-inspect-')));rmSync(dir,{recursive:true});}
});
test('safe temporary corruption rejected; retained file never altered',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'meridian-s2-corruption-'));
 try {writeFileSync(join(dir,'wrong.tif'),'not retained bytes');const locators={...snapshot.locators};const a=snapshot.value.catalogue.artifacts.find(a=>a.uses.some(u=>u.family==='worldcover'));locators[a.id]='wrong.tif';
 await assert.rejects(()=>openEvidence({dataRoot:dir,locators}),err=>err.code==='hash-mismatch');}
 finally {assert.equal(resolve(dir).startsWith(resolve(tmpdir(),'meridian-s2-corruption-')),true);rmSync(dir,{recursive:true});}
});
test('unknown generation and private path rejected before evidence access',async()=>{
 await assert.rejects(()=>openEvidence({generation:'0'.repeat(64)}),err=>['missing-file','generation-missing'].includes(err.code));
 await assert.rejects(()=>openEvidence({dataRoot:'meridian-private'}),err=>err.code==='invalid-locator');
});
test('repeated canonical results deterministic without query cache',async()=>{assert.equal(encode(await query('coexisting-semantic')),encode(await query('coexisting-semantic')));});
test('inspection/result mutation cannot alter next native answer',async()=>{
 const r=await query('coexisting-semantic');r.records[0].claim.native.fields.code=255;r.records[0].provenance.product.ref.id='wrong';
 const templates=structuredClone(e.semantics);e.semantics.bundle.collections[0].claims[1].native.fields.code=255;
 const next=await query('coexisting-semantic');assert.equal(next.records[0].claim.native.fields.code,30);assert.equal(next.records[0].provenance.product.ref.id,'worldcover');
 e.semantics=templates;
});
test('fresh independent process reproduces complete frozen matrix',async()=>{
 const expected={generation:e.generation,matrixSha256:sha(readFileSync(resolve(ROOT,'pilots/atlas/tryfan/query-matrix.json'))),results:await queryMatrix(e)};
 const child=spawnSync(process.execPath,['pilots/atlas/tryfan/query-cli.mjs','matrix'],{cwd:ROOT,encoding:'utf8',maxBuffer:4e6});assert.equal(child.status,0,child.stderr);
 assert.equal(encode(JSON.parse(child.stdout)),encode(expected));
});
test('genuine S1 historical generation resolves same unchanged native evidence',async()=>{
 const old=await openEvidence({generation:e.parent});try{const a=await query('coexisting-semantic'),b=await old.query({point:summit,property:'coexisting-semantic'});
 assert.notEqual(b.generation,a.generation);assert.deepEqual(b.records.map(r=>r.claim),a.records.map(r=>r.claim));}finally{old.close();}
});
test('all310 registered artifacts immutable and published root unchanged',()=>{
 assert.deepEqual(verifyArtifacts(snapshot.value.catalogue,snapshot.locators,DATA),{artifacts:310,bytes:42473107});assert.equal(currentId(STORE),initialRoot);
});
