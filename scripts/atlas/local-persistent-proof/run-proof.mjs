// Real-process acceptance run; generated stores/traces stay outside Git in meridian-data.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import { encode, sha } from './store.mjs';
export function child(command, dir, data, flags = [], expected = 0) {
  const start = performance.now();
  const r = spawnSync(process.execPath, ['scripts/atlas/local-persistent-proof/cli.mjs', command, dir, data, ...flags], { encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  assert.equal(r.status, expected, r.stderr || r.error?.message);
  const output = r.stdout.trim() ? JSON.parse(r.stdout) : undefined;
  return { output, exitCode: r.status, wallMs: performance.now() - start, ...(expected === 1 ? { error: JSON.parse(r.stderr.trim()) } : {}) };
}
export function exercise(base, data) {
  mkdirSync(base, { recursive: true });
  const a = join(base, 'accepted'), b = join(base, 'rebuild');
  const init = child('init', a, data);
  const restartA = child('inspect', a, data);
  assert.notEqual(init.output.process.pid, restartA.output.process.pid);
  assert.equal(encode(init.output.inspection), encode(restartA.output.inspection));
  const pointerA = readFileSync(join(a, 'current.json'), 'utf8');
  const interrupted = child('update', a, data, ['--crash-before-publish'], 73);
  assert.equal(readFileSync(join(a, 'current.json'), 'utf8'), pointerA);
  const afterInterruption = child('inspect', a, data);
  assert.equal(encode(afterInterruption.output.inspection), encode(restartA.output.inspection));
  const update = child('update', a, data);
  const restartB = child('inspect', a, data);
  assert.notEqual(update.output.process.pid, restartB.output.process.pid);
  assert.equal(encode(update.output.inspection), encode(restartB.output.inspection));
  assert.equal(update.output.recomputed.length, 2);
  assert.ok(update.output.recomputed.every(r => r.probe === 'summit'));
  const common = restartA.output.inspection, refined = restartB.output.inspection;
  const summit = update.output.statuses.filter(r => r.probe === 'summit');
  assert.ok(summit.every(r => r.assessment.status === 'stale'));
  assert.ok(update.output.statuses.filter(r => r.probe !== 'summit').every(r => r.assessment.status === 'fresh'));
  assert.equal(refined.counts.derivations, 6);
  const unaffectedA = common.answers.filter(r => r.probe === 'southern-observer').map(r => r.answer.result);
  const unaffectedB = refined.answers.filter(r => r.probe === 'southern-observer').map(r => r.answer.result);
  assert.equal(encode(unaffectedA), encode(unaffectedB));
  for (const old of common.answers) {
    const history = refined.historical.find(h => h.result.claim.id === old.answer.result.claim.id && h.result.claim.revision === old.answer.result.claim.revision);
    assert.equal(encode(history.result), encode(old.answer.result));
    assert.equal(history.freshness.status, 'fresh');
  }
  const replay = child('replay', a, data);
  assert.equal(replay.output.replay.checks.length, 6);
  assert.ok(replay.output.replay.checks.every(r => r.exact));
  const rebuildInit = child('init', b, data), rebuildUpdate = child('update', b, data);
  assert.equal(init.output.publication.snapshot, rebuildInit.output.publication.snapshot);
  assert.equal(update.output.publication.snapshot, rebuildUpdate.output.publication.snapshot);
  const legacy = JSON.parse(readFileSync('docs/research/tryfan-qualified-query-results.json', 'utf8'));
  for (const q of refined.answers) {
    const old = legacy.results.find(r => r.claim.id === q.answer.result.claim.id && r.claim.revision === q.answer.result.claim.revision);
    assert.ok(old); assert.equal(encode(old.value), encode(q.answer.result.claim.result));
  }
  assert.equal(refined.unknown.result.reason, 'unsupported');
  assert.equal(refined.unavailable.status, 'unavailable');
  const allProcesses = [init, restartA, afterInterruption, update, restartB, replay, rebuildInit, rebuildUpdate];
  assert.equal(new Set(allProcesses.map(p => p.output.process.pid)).size, allProcesses.length);
  const files = readdirSync(join(a, 'snapshots')).filter(f => f.endsWith('.json'));
  const snapshots = files.map(f => ({ name: f, bytes: statSync(join(a, 'snapshots', f)).size }));
  const logical = { initial: init.output.publication.snapshot, updated: update.output.publication.snapshot, current: refined.answers.map(q => ({ probe: q.probe, property: q.property, ref: { id: q.answer.result.claim.id, revision: q.answer.result.claim.revision }, value: q.answer.result.claim.result, freshness: q.answer.freshness.status })), history: refined.historical.map(q => ({ id: q.result.claim.id, revision: q.result.claim.revision, replay: q.freshness.status, preferred: q.currentlyPreferred })), unknown: refined.unknown.result, unavailable: refined.unavailable, recomputed: update.output.recomputed };
  for (const [name, c] of Object.entries({ init, restartA, interrupted, afterInterruption, update, restartB, replay, rebuildInit, rebuildUpdate })) writeFileSync(join(base, name + '.json'), encode(c));
  return { logical, logicalSha256: sha(encode(logical)), snapshots, storeBytes: snapshots.reduce((n, r) => n + r.bytes, 0) + statSync(join(a, 'current.json')).size, counts: refined.counts, initialCounts: common.counts, rebuiltEquivalent: true, realProcesses: allProcesses.length + 1, measures: Object.fromEntries(Object.entries({ init, restartA, interrupted, afterInterruption, update, restartB, replay, rebuildInit, rebuildUpdate }).map(([name, c]) => [name, { wallMs: c.wallMs, exitCode: c.exitCode, ...(c.output ? { ...c.output.measurement, loadMs: c.output.loadMs, queryBatchMs: c.output.queryBatchMs, constructedMs: c.output.constructedMs, updateMs: c.output.updateMs, publicationMs: c.output.publicationMs, replayMs: c.output.replayMs } : {}) }])), updateSnapshotBytes: update.output.publication.bytes, retryPublication: update.output.publication, normalRebuildPublication: rebuildUpdate.output.publication, changedDerivations: update.output.recomputed.length, preservedDerivations: unaffectedB.length, proofDirectory: base };
}
if (process.argv[1] && resolve(process.argv[1]) === resolve('scripts/atlas/local-persistent-proof/run-proof.mjs')) {
  const data = resolve(process.argv[2] ?? '../meridian-data');
  const dir = join(data, 'derived/atlas/tryfan/local-persistent-proof-v1/runs', String(Date.now()));
  const result = exercise(dir, data);
  const methods = Object.fromEntries(['store.mjs','runtime.mjs','cli.mjs','run-proof.mjs'].map(f => ['scripts/atlas/local-persistent-proof/' + f, sha(readFileSync('scripts/atlas/local-persistent-proof/' + f))]));
  writeFileSync('docs/research/tryfan-local-persistent-results.json', encode({ proof: 'tryfan-local-persistent-proof/v1', startingCheckpoint: '3c143ebea99ce366a1b00083f64a4ee11149a1e0', decision: 'C — SUCCESS', planSha256: sha(readFileSync('docs/research/tryfan-local-persistent-plan.json')), methods, ...result, machine: { platform: process.platform, arch: process.arch, node: process.version }, limits: 'Local single writer; no power-loss, multi-writer, load or production throughput guarantee. Warm local assets; replay rehashes and samples retained pixels. Snapshot rewrite is full metadata, not incremental record storage.' }));
  console.log(JSON.stringify({ logicalSha256: result.logicalSha256, storeBytes: result.storeBytes, snapshots: result.snapshots, measures: result.measures, proofDirectory: dir }));
}
