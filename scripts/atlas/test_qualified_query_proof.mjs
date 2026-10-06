import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createServer } from 'vite';
const json=p=>JSON.parse(readFileSync(p,'utf8'));
const input=json('docs/research/tryfan-qualified-query-inputs.json');
const output=json('docs/research/tryfan-qualified-query-results.json');
const server=await createServer({configFile:false,appType:'custom',logLevel:'silent',server:{middlewareMode:true}});
const p=await server.ssrLoadModule('/scripts/atlas/qualified-query-proof/proof.ts');
const {validateSemanticEvidence,resolveContext}=await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');
const {createTryfanTerrainProof}=await server.ssrLoadModule('/src/atlas/terrain/metadata/tryfanTerrainProof.ts');
const {registerTerrainHierarchy}=await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainRegistry.ts');
const {selectTerrain}=await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainSelector.ts');
await server.close();
const roots=input.roots;
const results=output.results.map(r=>{const c=output.evidence.collections.find(c=>c.claims.some(q=>q.id===r.claim.id&&q.revision===r.claim.revision));return {...r,claim:c.claims[0],context:resolveContext(c.context,c.claims[0])};});
const slope=results.find(r=>r.probe==='summit'&&r.property==='slope'&&r.receipt.inputs[0].id.includes('welsh'));
const area=results.find(r=>r.probe==='summit'&&r.property==='area-ratio'&&r.receipt.inputs[0].revision===slope.claim.revision);
const older=results.find(r=>r.probe==='summit'&&r.property==='slope'&&r.receipt.inputs[0].id.includes('production-common'));
const assess=(r,policy='current-applicable-terrain-v1',changes=[],all=results,available=roots,method=output.methodRevision)=>p.assess(r,all,available,output.selections.after[r.probe],policy,changes,method);

test('Horn synthetic planes use physical spacing, constant offsets do not change slope',()=>{
 const plane=[[12,14,16],[8,10,12],[4,6,8]];
 assert.ok(Math.abs(p.hornSlope(plane,2)-Math.atan(Math.sqrt(5))*180/Math.PI)<1e-12);
 assert.equal(p.hornSlope(plane.map(r=>r.map(x=>x+1000)),2),p.hornSlope(plane,2));
 assert.equal(p.hornSlope([[1,1,1],[1,1,1],[1,1,1]],8),0);
});
test('missing/nonfinite neighbourhood and invalid spacing are rejected, never zero-filled',()=>{
 assert.throws(()=>p.hornSlope([[1]],8));assert.throws(()=>p.hornSlope([[1,1,1],[1,NaN,1],[1,1,1]],8));assert.throws(()=>p.hornSlope([[1,1,1],[1,1,1],[1,1,1]],0));
});
test('area ratio is an ordinary geometric ratio, not fraction or probability',()=>{
 assert.equal(p.areaRatio(0),1);assert.ok(Math.abs(p.areaRatio(60)-2)<1e-12);assert.throws(()=>p.areaRatio(90));assert.throws(()=>p.areaRatio(-1));
 assert.equal(area.claim.result.value.kind,'quantity');assert.ok(area.claim.result.value.value>=1);
});
test('all real fixture claims and dependency receipts validate unchanged v1',()=>{
 assert.deepEqual(validateSemanticEvidence(output.evidence),[]);assert.deepEqual(p.validateSlice(results,roots),[]);
 assert.equal(output.validation.historicalReplay,true);assert.equal(results.length,6);
});
test('freshness consumes exact existing TerrainHierarchy selection, including fallback',()=>{
 const registry=createTryfanTerrainProof();
 for(const probe of input.geometry.probes){const selection=selectTerrain(registry,{footprint:probe.eligibilityFootprint,scale:{scheme:'XYZ Web Mercator zoom (delivery)',requestedLevel:'z14'}});assert.deepEqual(selection,output.selections.after[probe.id]);}
 assert.equal(output.selections.after.summit.family,'welsh-regional');assert.equal(output.selections.after['southern-observer'].family,'production-common');
 const decl=structuredClone(registry.hierarchy);decl.regional=[];decl.selection.regionalOrder=[];decl.id='tryfan-proof-common-context';decl.revision='1';
 const common=registerTerrainHierarchy(decl,registry.options);
 assert.equal(selectTerrain(common,{footprint:input.geometry.probes[0].eligibilityFootprint,scale:{scheme:decl.common.levelScheme,requestedLevel:'z14'}}).family,'production-common');
});
test('same physical question/id coexists with distinct evidence/process/claim revisions',()=>{
 assert.equal(older.question,slope.question);assert.equal(older.claim.id,slope.claim.id);assert.notEqual(older.claim.revision,slope.claim.revision);assert.notEqual(older.receipt.id,slope.receipt.id);
 assert.notEqual(older.receipt.inputs[0].revision,slope.receipt.inputs[0].revision);
});
test('historical exact-input replay stays fresh while current applicable policy is stale',()=>{
 assert.equal(assess(older,'fixed-input-replay-v1').status,'fresh');assert.equal(assess(older).status,'stale');assert.equal(assess(slope).status,'fresh');
 assert.match(assess(older).reason,/stale is not false/);assert.ok(assess(slope).policyRevision);assert.ok(assess(slope).baseline.expectedMethodRevision);
});
test('only affected summit two-level chain recomputes; southern results remain preferred',()=>{
 assert.equal(output.recomputed.length,2);assert.ok(output.recomputed.every(r=>r.probe==='summit'));
 assert.equal(output.currentResults.length,4);assert.ok(results.filter(r=>r.probe==='southern-observer').every(r=>assess(r).status==='fresh'));
});
test('derived-on-derived uses exact upstream revision and propagates stale transitively',()=>{
 assert.equal(area.receipt.inputs[0].kind,'claim');assert.equal(area.receipt.inputs[0].revision,slope.claim.revision);
 const oldArea=results.find(r=>r.property==='area-ratio'&&r.receipt.inputs[0].revision===older.claim.revision);
 assert.equal(assess(oldArea).status,'stale');assert.equal(assess(oldArea,'fixed-input-replay-v1').status,'fresh');
 assert.equal(assess(area).status,'fresh');
});
test('outside read scope has no impact, interpolation halo matters outside output point',()=>{
 assert.equal(assess(slope,undefined,[output.spatialNotifications.outside]).status,'fresh');
 assert.equal(assess(slope,undefined,[output.spatialNotifications.halo]).status,'stale');
 assert.equal(assess(area,undefined,[output.spatialNotifications.halo]).status,'stale');
 for(const r of results.filter(r=>r.probe==='southern-observer'))assert.equal(assess(r,undefined,[output.spatialNotifications.halo]).status,'fresh');
});
test('unknown change scope produces indeterminate assessment rather than fake minimal impact',()=>{
 const change={...output.spatialNotifications.halo,scopeKnown:false};assert.equal(assess(slope,undefined,[change]).status,'indeterminate');assert.equal(assess(area,undefined,[change]).status,'indeterminate');
});
test('missing exact input or upstream claim cannot become absent terrain or a fabricated scalar',()=>{
 assert.equal(assess(older,'fixed-input-replay-v1',[],results,[]).status,'indeterminate');assert.equal(assess(area,undefined,[],[area]).status,'indeterminate');
});
test('method policy change is explicit; older method remains reproducible, no newest-wins',()=>{
 assert.equal(assess(slope,undefined,[],results,roots,'hypothetical-method-v2').status,'stale');
 assert.equal(assess(slope,'fixed-input-replay-v1',[],results,roots,'hypothetical-method-v2').status,'fresh');
 const root=roots.find(r=>r.family==='welsh-regional');const changed=p.derive(input.geometry.probes[0],root,'hypothetical-method-v2');
 assert.equal(changed[0].claim.id,slope.claim.id);assert.notEqual(changed[0].claim.revision,slope.claim.revision);assert.equal(changed[0].claim.result.value.value,slope.claim.result.value.value);
 assert.deepEqual(validateSemanticEvidence(p.bundle([...results,...changed],roots,input.geometry.probes[0])),[]);
});
test('unknown exposure differs from non-detection; stricter provenance request returns unavailable',()=>{
 assert.equal(output.unknown.exposure.result.kind,'gap');assert.equal(output.unknown.exposure.result.reason,'unsupported');assert.equal(output.unknown.terrainWithSpatialContributorRequirement.status,'unavailable');
 assert.ok(output.unknown.terrainWithSpatialContributorRequirement.trace.some(t=>t.outcome==='spatial-contributors-unavailable'));
 assert.ok(results.every(r=>r.context.quality===undefined));assert.ok(results.every(r=>r.context.time[0].extent.kind==='unknown'));
});
test('materialization/reload and historical recomputation preserve qualified identities',()=>{
 assert.deepEqual(JSON.parse(JSON.stringify(output)),output);
 for(const r of results){const slopeInput=r.property==='slope'?r:results.find(u=>u.claim.id===r.receipt.inputs[0].id&&u.claim.revision===r.receipt.inputs[0].revision);const root=roots.find(x=>'retained-input:'+x.id===slopeInput.receipt.inputs[0].id);const replay=p.derive(input.geometry.probes.find(x=>x.id===r.probe),root,r.receipt.methodRevision)[r.property==='slope'?0:1];assert.deepEqual(replay.claim,r.claim);assert.deepEqual(replay.receipt,r.receipt);}
 assert.notEqual(slope.question,slope.receipt.artifact.sha256);
});
test('bad exact references, malformed scope and same-result cycles are rejected in finite chain',()=>{
 const a=structuredClone(area);a.receipt.inputs[0].revision='missing';assert.match(p.validateSlice([slope,a],roots).join(';'),/exact acyclic upstream/);
 const b=structuredClone(slope);b.receipt.inputs[0].spatial.bounds=[2,2,1,1];assert.match(p.validateSlice([b],roots).join(';'),/Invalid actual-use/);
 const c=structuredClone(area);c.receipt.inputs[0].id=c.claim.id;c.receipt.inputs[0].revision=c.claim.revision;assert.match(p.validateSlice([c],roots).join(';'),/exact acyclic upstream/);
});
test('source/code snapshots and synthetic change labels remain explicit',()=>{
 for(const [file,h] of Object.entries(output.methodFiles))assert.equal(createHash('sha256').update(readFileSync(file)).digest('hex'),h);
 assert.equal(createHash('sha256').update(readFileSync('docs/research/tryfan-qualified-query-inputs.json')).digest('hex'),output.inputSnapshotSha256);
 assert.match(roots.find(r=>r.family==='production-common').upstream.revision.reason,/unknown/);
 assert.match(output.spatialNotifications.halo.description,/Synthetic/);assert.match(output.retainedNativeContext.qualification,/not.*exposure fractions/);
});
