// Separate process for every phase/query. Never imported by production.
import { performance } from 'node:perf_hooks';
import { resolve, join } from 'node:path';
import { existsSync, writeFileSync } from 'node:fs';
import { runtime } from './runtime.mjs';
import { load, publish, StoreError } from './store.mjs';
const [command, dirArg, dataArg, ...flags] = process.argv.slice(2);
if (!command || !dirArg || !dataArg) throw new Error('Usage: cli.mjs init|inspect|update|replay STORE DATA [--crash-before-publish]');
const dir = resolve(dirArg), data = resolve(dataArg), start = performance.now();
let r;
try {
  r = await runtime(data); const startupMs = performance.now() - start;
  let output;
  if (command === 'init') {
    if (existsSync(join(dir, 'current.json'))) throw new StoreError('already-initialized', 'Refuse overwrite; use a new empty proof store');
    const t = performance.now(), state = r.initial(), constructedMs = performance.now() - t;
    const p = performance.now(), publication = publish(dir, state, r.validate), publicationMs = performance.now() - p;
    output = { publication, constructedMs, publicationMs, inspection: r.inspect(state) };
  } else {
    const t = performance.now(), saved = load(dir, r.validate), loadMs = performance.now() - t;
    if (command === 'inspect') {
      const q = performance.now(), inspection = r.inspect(saved.state), queryBatchMs = performance.now() - q;
      output = { snapshot: saved.snapshot, bytes: saved.bytes, loadMs, queryBatchMs, inspection };
    } else if (command === 'replay') {
      const p = performance.now(), replay = r.replay(saved.state), replayMs = performance.now() - p;
      output = { snapshot: saved.snapshot, loadMs, replayMs, replay };
    } else if (command === 'update') {
      const u = performance.now(), update = r.prepareUpdate(saved.state, saved.snapshot), updateMs = performance.now() - u;
      if (flags.includes('--crash-before-publish')) {
        publish(dir, update.state, r.validate, { beforePointer: () => {
          writeFileSync(join(dir, 'interruption.json'), JSON.stringify({ oldSnapshot: saved.snapshot, completedUnpublished: true, pid: process.pid }));
          process.exit(73); // Genuine abrupt process exit after snapshot close, before pointer write.
        } });
      }
      const p = performance.now(), publication = publish(dir, update.state, r.validate), publicationMs = performance.now() - p;
      output = { oldSnapshot: saved.snapshot, publication, loadMs, updateMs, publicationMs, statuses: update.statuses, recomputed: update.recomputed, sampleMeasurement: update.sampleMeasurement, inspection: r.inspect(update.state) };
    } else throw new StoreError('unknown-command', 'Unsupported bounded proof command');
  }
  console.log(JSON.stringify({ ...output, process: { pid: process.pid }, measurement: { startupMs, totalMs: performance.now() - start } }));
} catch (e) {
  console.error(JSON.stringify({ status: 'infrastructure-error', code: e.code ?? 'runtime-error', reason: e.message, physicalClaim: false })); process.exitCode = 1;
} finally { await r?.close(); }
