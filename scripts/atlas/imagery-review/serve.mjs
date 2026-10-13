import { createServer, loadEnv } from 'vite';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { openData } from './local-data.mjs';
const root = process.env.MERIDIAN_DATA_ROOT;
if (!root) throw Error('Set MERIDIAN_DATA_ROOT to the existing external workspace');
const local = await openData(root);
const stats = { requests: 0, responseBytes: 0, stopped: false };
// Explicit owner approval is required separately; the switch is not permission.
const live = process.argv.includes('--approved-maptiler');
const repository = resolve(fileURLToPath(new URL('../../..', import.meta.url)));
const key = live ? loadEnv('development', repository, 'VITE_MAPTILER_KEY').VITE_MAPTILER_KEY?.trim() : '';
if (live && !key) throw Error('Approved comparison requires the existing MapTiler key');
let claimed = false;
const server = await createServer({ configFile: false, publicDir: false, root: fileURLToPath(new URL('.', import.meta.url)),
  // Only this existing client-visible key is exposed, and only in explicit live mode.
  envDir: false, define: { __MAPTILER_KEY__: JSON.stringify(key || '') }, server: { host: '127.0.0.1', port: 5182, strictPort: true, cors: false, hmr: false,
    fs: { allow: [resolve(fileURLToPath(new URL('../../..', import.meta.url)))] } },
  plugins: [{ name: 'retained-imagery-only', configureServer(server) {
    server.middlewares.use(async (req, res, next) => {
      const url = req.url ?? '';
      if (url === '/live-permit') {
        res.setHeader('Cache-Control', 'no-store');
        if (!live || claimed || req.method !== 'POST') { res.statusCode = 403; res.end('No fresh live document allowed'); return; }
        claimed = true; res.end('One approved document; no reloads'); return;
      }
      if (url === '/metadata' || url === '/stats') {
        res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(url === '/metadata' ? local.metadata : stats)); return;
      }
      if (!['/imagery/', '/contours/', '/hillshade.png'].some(prefix => url.startsWith(prefix))) return next();
      res.setHeader('Cache-Control', 'no-store');
      try {
        if (req.method !== 'GET' || stats.stopped) { res.statusCode = 429; res.end('Local experiment stopped'); return; }
        if (++stats.requests > 120) { stats.stopped = true; throw Error('Local request allowance used'); }
        const result = await local.load(url);
        if (!result) { res.statusCode = 404; res.end('Outside retained inventory'); return; }
        if (stats.responseBytes + result.data.length > 40_000_000) { stats.stopped = true; throw Error('Local byte allowance used'); }
        stats.responseBytes += result.data.length;
        res.setHeader('Content-Type', result.type); res.end(result.data);
      } catch { res.statusCode = 503; res.end('Local product unavailable, changed or allowance used'); }
    });
  } }] });
await server.listen();
console.log('Offline Swiss imagery review: http://127.0.0.1:5182/ (120 local attempts / 40 MB per server session)');
