import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, readFileSync, writeFileSync, copyFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { exercise, child } from './local-persistent-proof/run-proof.mjs';
import { runtime } from './local-persistent-proof/runtime.mjs';
import { load, publish, encode, sha } from './local-persistent-proof/store.mjs';
const data = resolve(process.env.MERIDIAN_DATA_ROOT ?? '../meridian-data');
const dir = join(data, 'derived/atlas/tryfan/local-persistent-proof-v1/tests', String(Date.now()));
const run = exercise(dir, data);
const r = await runtime(data);
after(() => r.close());
const saved = load(join(dir,'accepted'),r.validate), initial = load(join(dir,'rebuild'),r.validate);
function broken(name, alter) {
  const state = structuredClone(saved.state); alter(state);
  const target = join(dir, name); publish(target, state, () => {}); // Deliberately create an invalid NEW test store.
  return child('inspect', target, data, [], 1).error;
}

test('restart A and B use distinct terminated processes with equivalent qualified answers', () => {
  assert.equal(run.realProcesses,9);assert.equal(run.rebuiltEquivalent,true);
  assert.equal(run.counts.derivations,6);assert.equal(run.initialCounts.derivations,4);
});
test('identities retain exact earlier fixture values/revisions and coexist historically', () => {
  const previous=JSON.parse(readFileSync('docs/research/tryfan-qualified-query-results.json','utf8'));
  for(const q of run.logical.current){const old=previous.results.find(x=>x.claim.id===q.ref.id&&x.claim.revision===q.ref.revision);assert.ok(old);assert.deepEqual(old.value,q.value);}
  assert.equal(run.logical.history.length,4);assert.equal(run.logical.history.filter(h=>!h.preferred).length,2);
});
test('v1 roundtrip and order-independent artifact identity do not define physical claim identity', () => {
  assert.equal(encode(JSON.parse(encode(saved.state))),encode(saved.state));
  assert.equal(sha(encode({a:1,b:{x:2,y:3}})),sha(encode({b:{y:3,x:2},a:1})));
  assert.notEqual(saved.snapshot,saved.state.derivations[0].claim.revision);
  assert.equal(saved.snapshot,initial.snapshot);
});
test('freshness is assessed after startup, not a durable flag or preferred mutable claim', () => {
  assert.ok(!encode(saved.state).includes('"freshness"'));
  const a=r.assess(saved.state);assert.equal(a.filter(x=>x.current.status==='stale').length,2);
  assert.ok(a.every(x=>x.replay.status==='fresh'));
});
test('scope notifications outside read halo do not invalidate, inside halo propagates', () => {
  const notice=JSON.parse(readFileSync('docs/research/tryfan-qualified-query-results.json','utf8')).spatialNotifications;
  const outside=r.assess(saved.state,[notice.outside]);
  assert.equal(outside.filter(x=>x.current.status==='stale').length,2); // Already historical summit only.
  const halo=r.assess(saved.state,[notice.halo]);
  assert.equal(halo.filter(x=>x.current.status==='stale').length,4);
  assert.ok(halo.filter(x=>x.probe==='southern-observer').every(x=>x.current.status==='fresh'));
  assert.equal(r.assess(saved.state,[{...notice.halo,scopeKnown:false}]).filter(x=>x.current.status==='indeterminate').length,2);
});
test('derived-on-derived exact references reconstruct reverse lookup without persistent cache', () => {
  const i=r.inspect(saved.state);assert.equal(i.counts.reverseKeys,6);
  const ratio=saved.state.derivations.find(x=>x.property==='area-ratio');
  assert.equal(ratio.receipt.inputs[0].kind,'claim');assert.ok(Object.values(i.reverse).some(v=>v.some(x=>x.id===ratio.claim.id&&x.revision===ratio.claim.revision)));
  assert.equal(run.changedDerivations,2);assert.equal(run.preservedDerivations,2);
});
test('stored roots contain references/scopes but no raster payload or nine-height buffer', () => {
  assert.ok(saved.state.roots.every(x=>!('heightSamplesM' in x)&&x.assets.every(a=>a.href.startsWith('meridian-data://')&&a.sha256)));
  assert.ok(saved.state.roots.every(x=>x.actualUse.bounds.length===4));
});
test('historical replay rehashes and samples real retained pixels, not serialized numbers', () => {
  const replay=r.replay(saved.state);assert.equal(replay.fromRetainedPixels,true);
  assert.equal(replay.checks.length,6);assert.ok(replay.checks.every(c=>c.exact));
});
test('unsupported semantic gap and unavailable provenance remain distinct after restart', () => {
  const i=r.inspect(saved.state);assert.equal(i.unknown.result.reason,'unsupported');assert.equal(i.unavailable.status,'unavailable');
  assert.equal(i.unknown.result.kind,'gap');assert.ok(!('value' in i.unknown.result));
  assert.equal(r.query(saved.state,'summit',i.unknown.native.property.id).status,'unknown');
  assert.equal(r.query(saved.state,'summit','slope','missing').reason,'Exact historical revision unavailable');
});
test('missing external asset is infrastructure unavailable, not a physical unknown or zero', () => {
  const response=child('inspect',join(dir,'accepted'),join(dir,'empty-external-context')).output.inspection;
  assert.ok(response.answers.every(q=>q.answer.status==='unavailable'));
  assert.equal(response.unknown.result.reason,'unsupported');assert.ok(response.assessments.every(a=>a.replay.status==='indeterminate'));
});
test('absent first-run store has explicit safe error', () => {
  const e=child('inspect',join(dir,'absent'),data,[],1).error;assert.equal(e.code,'store-absent');assert.equal(e.physicalClaim,false);
});
test('incompatible local proof schema is rejected independently of frozen v1', () => {
  const e=broken('unknown-schema',s=>{s.schema='future/v2';});assert.equal(e.code,'unsupported-schema');assert.equal(e.physicalClaim,false);
});
test('invalid native v1 record cannot be accepted or recovered as zero', () => {
  const e=broken('invalid-native',s=>{s.evidence.collections[0].claims[0].native.property.id='';});assert.equal(e.code,'invalid-evidence');
});
test('missing exact upstream dependency is rejected', () => {
  const e=broken('missing-dependency',s=>{s.derivations.find(d=>d.property==='area-ratio').receipt.inputs[0].revision='missing';});assert.equal(e.code,'invalid-evidence');
});
test('checksum damage fails visibly and preserves history rather than overwriting input', () => {
  const target=join(dir,'corrupt');mkdirSync(join(target,'snapshots'),{recursive:true});
  copyFileSync(join(dir,'accepted/current.json'),join(target,'current.json'));
  const body=readFileSync(join(dir,'accepted/snapshots',saved.snapshot+'.json'));
  writeFileSync(join(target,'snapshots',saved.snapshot+'.json'),Buffer.concat([body,Buffer.from('x')]));
  const e=child('inspect',target,data,[],1).error;assert.equal(e.code,'checksum-failure');assert.equal(e.physicalClaim,false);
  assert.equal(load(join(dir,'accepted'),r.validate).snapshot,saved.snapshot);
});
test('incomplete update cannot publish; abrupt exit before pointer replacement leaves coherent prior state', () => {
  const target=join(dir,'reject-publication');publish(target,saved.state,r.validate);
  const bad=structuredClone(saved.state);bad.derivations.pop();
  assert.throws(()=>publish(target,bad,r.validate));assert.equal(load(target,r.validate).snapshot,saved.snapshot);
  assert.equal(run.measures.interrupted.exitCode,73);
  assert.equal(run.retryPublication.snapshotWritten,false);assert.equal(run.normalRebuildPublication.snapshotWritten,true);
});
test('logical rebuild is exact and full metadata rewrite remains a disclosed limitation', () => {
  assert.equal(run.logical.updated,saved.snapshot);assert.ok(run.updateSnapshotBytes>0);
  assert.equal(run.snapshots.length,2);assert.ok(run.storeBytes>run.updateSnapshotBytes);
  assert.equal(run.logicalSha256,sha(encode(run.logical)));
  assert.equal(run.logicalSha256,JSON.parse(readFileSync('docs/research/tryfan-local-persistent-results.json','utf8')).logicalSha256);
});
test('nonfinite values and unknown pointer format cannot silently serialize or load', () => {
  assert.throws(()=>encode({value:NaN}));
  const target=join(dir,'bad-pointer');mkdirSync(target,{recursive:true});writeFileSync(join(target,'current.json'),'{}');
  const e=child('inspect',target,data,[],1).error;assert.equal(e.code,'unsupported-pointer');
});
