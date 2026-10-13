// Direct browser requests: no proxy, persistent cache, archive or automatic retry.
export function createTrial(fetcher = fetch, clock = () => Date.now(), wait = ms => new Promise(resolve => setTimeout(resolve, ms))) {
  const stats = { imageryAttempts: 0, metadataAttempts: 0, responseBytes: 0, active: 0, peakActive: 0, stopped: false };
  const queue = [], controllers = new Set();
  let lastStart = -Infinity, pumping = false, reserved = 0;
  function stop() {
    stats.stopped = true;
    for (const controller of controllers) controller.abort();
    for (const job of queue.splice(0)) job.reject(Error('Trial stopped'));
  }
  async function run(job) {
    const cap = job.kind === 'metadata' ? 250_000 : 1_000_000;
    if (stats.stopped || stats.responseBytes + reserved + cap > 30_000_000 ||
        (job.kind === 'metadata' ? stats.metadataAttempts >= 1 : stats.imageryAttempts >= 100)) {
      stop(); job.reject(Error('Trial allowance used')); return;
    }
    reserved += cap; stats.active++; stats.peakActive = Math.max(stats.peakActive, stats.active);
    stats[job.kind === 'metadata' ? 'metadataAttempts' : 'imageryAttempts']++;
    const controller = new AbortController(); controllers.add(controller);
    const abort = () => controller.abort(); job.signal?.addEventListener('abort', abort, { once: true });
    try {
      const response = await fetcher(job.url, { signal: controller.signal, redirect: 'error', credentials: 'omit', cache: 'no-store' });
      const type = response.headers.get('content-type') ?? '';
      if (!response.ok || !(job.kind === 'metadata' ? type.includes('json') : type.startsWith('image/jpeg'))) throw Error('Provider response refused or unexpected');
      const reader = response.body.getReader(), chunks = [];
      let size = 0;
      while (true) {
        const part = await reader.read(); if (part.done) break;
        stats.responseBytes += part.value.byteLength; size += part.value.byteLength;
        if (size > cap || stats.responseBytes > 29_000_000) { await reader.cancel(); throw Error('Response allowance reached'); }
        chunks.push(part.value);
      }
      const data = new Uint8Array(size); let offset = 0;
      for (const chunk of chunks) { data.set(chunk, offset); offset += chunk.length; }
      job.resolve(data.buffer);
    } catch {
      if (!job.signal?.aborted) stop();
      const error = Error(job.signal?.aborted ? 'View request cancelled' : 'Provider/allowance failure; stop without reloading');
      if (job.signal?.aborted) error.name = 'AbortError';
      job.reject(error);
    } finally {
      reserved -= cap; stats.active--; controllers.delete(controller); job.signal?.removeEventListener('abort', abort);
      void pump();
    }
  }
  async function pump() {
    if (pumping || stats.stopped) return;
    pumping = true;
    try {
      while (queue.length && stats.active < 2 && !stats.stopped) {
        await wait(Math.max(0, 550 - (clock() - lastStart)));
        if (stats.stopped) break;
        const job = queue.shift();
        if (job.signal?.aborted) { const error = Error('View request cancelled'); error.name = 'AbortError'; job.reject(error); continue; }
        lastStart = clock(); void run(job);
      }
    } finally { pumping = false; }
  }
  return { stats, stop, get(url, kind, signal) {
    if (stats.stopped) return Promise.reject(Error('Trial stopped'));
    return new Promise((resolve, reject) => { queue.push({ url, kind, signal, resolve, reject }); void pump(); });
  } };
}
export function validateMetadata(metadata, key) {
  if (!Array.isArray(metadata.tiles) || metadata.tiles.length !== 1 || !metadata.attribution ||
      metadata.minzoom !== 0 || metadata.maxzoom !== 22 || (metadata.scheme && metadata.scheme !== 'xyz')) throw Error('Unexpected declaration');
  const template = metadata.tiles[0];
  if (template !== `https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=${encodeURIComponent(key)}`) throw Error('Unapproved resource endpoint');
  return template;
}
