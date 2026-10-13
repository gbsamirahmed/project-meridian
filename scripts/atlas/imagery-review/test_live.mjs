import test from 'node:test';
import assert from 'node:assert/strict';
import { createTrial, validateMetadata } from './live-resources.mjs';
test('direct requests share spacing, concurrency and counters across camera changes', async () => {
  let time = 0, active = 0, peak = 0;
  const starts = [];
  const trial = createTrial(async () => {
    starts.push(time); active++; peak = Math.max(peak, active);
    await new Promise(resolve => setTimeout(resolve, 1)); active--;
    return new Response(new Uint8Array(10), { headers: { 'content-type': 'image/jpeg' } });
  }, () => time, async ms => { time += ms; });
  await Promise.all(Array.from({ length: 5 }, () => trial.get('synthetic', 'imagery')));
  assert.equal(trial.stats.imageryAttempts, 5); assert.equal(trial.stats.responseBytes, 50);
  assert.ok(peak <= 2); assert.ok(starts.slice(1).every((value, index) => value - starts[index] >= 550));
});
test('refusals and oversized responses stop without retries', async () => {
  for (const response of [new Response('', { status: 429 }), new Response(new Uint8Array(1_000_001), { headers: { 'content-type': 'image/jpeg' } })]) {
    let calls = 0;
    const trial = createTrial(async () => { calls++; return response; }, () => 0, async () => {});
    await assert.rejects(trial.get('synthetic', 'imagery')); await assert.rejects(trial.get('synthetic', 'imagery'));
    assert.equal(calls, 1); assert.equal(trial.stats.stopped, true); assert.equal(trial.stats.active, 0);
  }
});
test('attempt cap and metadata endpoint validation are fail-closed', async () => {
  const trial = createTrial(async () => new Response('', { headers: { 'content-type': 'image/jpeg' } }), () => 0, async () => {});
  for (let i = 0; i < 100; i++) await trial.get('synthetic', 'imagery');
  await assert.rejects(trial.get('synthetic', 'imagery')); assert.equal(trial.stats.imageryAttempts, 100);
  const metadata = { tiles: ['https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=synthetic'], minzoom: 0, maxzoom: 22, attribution: 'credit' };
  assert.equal(validateMetadata(metadata, 'synthetic'), metadata.tiles[0]);
  assert.throws(() => validateMetadata({ ...metadata, tiles: ['https://unexpected.invalid/tile'] }, 'synthetic'));
});
test('stopping during the start-spacing wait retires queued work without a request', async () => {
  let release, calls = 0;
  const trial = createTrial(async () => { calls++; }, () => 0, () => new Promise(resolve => { release = resolve; }));
  const result = assert.rejects(trial.get('synthetic', 'imagery'));
  trial.stop(); release(); await result;
  assert.equal(calls, 0); assert.equal(trial.stats.active, 0); assert.equal(trial.stats.imageryAttempts, 0);
});
test('camera cancellation releases an actual request without stopping the trial', async () => {
  let started;
  const ready = new Promise(resolve => { started = resolve; });
  const trial = createTrial(async (_, options) => new Promise((resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(Error('synthetic cancellation')), { once: true }); started();
  }), () => 0, async () => {});
  const controller = new AbortController();
  const result = assert.rejects(trial.get('synthetic', 'imagery', controller.signal), { name: 'AbortError' });
  await ready; controller.abort(); await result;
  assert.equal(trial.stats.active, 0); assert.equal(trial.stats.stopped, false); assert.equal(trial.stats.imageryAttempts, 1);
});
