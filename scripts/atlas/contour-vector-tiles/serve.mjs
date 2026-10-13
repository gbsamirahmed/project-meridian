/* Loopback-only disposable static demonstration; no provider proxy or data mutation. */
import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve, relative } from 'node:path';
import { encode, tileRange } from './package.mjs';
const root = resolve(process.argv[2]), port = Number(process.argv[3] || 5180);
const stats = { tileRequests: 0, tileResponseBytes: 0, emptyOutsideProduct: 0 };
const comparison = resolve(root, '../multiscale-contours-hillshade-v1/viewer-final/contours-hillshade.html');
const metadata = JSON.parse(readFileSync(join(root, 'product.json')));
const type = path => path.endsWith('.pbf') ? 'application/vnd.mapbox-vector-tile' : path.endsWith('.png') ? 'image/png'
  : path.endsWith('.js') ? 'text/javascript' : path.endsWith('.css') ? 'text/css' : path.endsWith('.json') ? 'application/json' : 'text/html';
createServer((request, response) => {
  try {
    const path = new URL(request.url, 'http://127.0.0.1').pathname;
    let file;
    if (path === '/stats') {
      response.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      response.end(JSON.stringify(stats)); return;
    }
    if (path === '/') file = join(root, 'demo/index.html');
    else if (path === '/comparison') file = comparison;
    else if (path === '/product.json' || path === '/hillshade-mercator.png') file = join(root, path.slice(1));
    else if (/^\/assets\/[a-zA-Z0-9_.-]+$/.test(path)) file = join(root, 'demo', path.slice(1));
    else if (/^\/tiles\/swiss-(native|2m|smoothed)\/(1[0-7])\/\d+\/\d+\.pbf$/.test(path)) {
      stats.tileRequests++; file = join(root, path.slice(1));
      if (!existsSync(file)) {
        const [z, x, y] = path.split('/').slice(-3).map(value => Number(value.replace('.pbf', '')));
        const range = tileRange(metadata.boundsLonLat, z);
        if (x >= range[0] && x <= range[2] && y >= range[1] && y <= range[3])
          throw new Error('Expected local tile missing; do not fabricate a successful empty response');
        const body = encode(null); stats.emptyOutsideProduct++; stats.tileResponseBytes += body.length;
        response.writeHead(200, { 'Content-Type': 'application/vnd.mapbox-vector-tile', 'Cache-Control': 'no-store' }); response.end(body); return;
      }
    } else { response.writeHead(404); response.end('Unknown local resource'); return; }
    if (file !== comparison && relative(root, file).startsWith('..')) throw new Error('Resource outside product');
    const body = readFileSync(file);
    if (file.endsWith('.pbf')) stats.tileResponseBytes += body.length;
    response.writeHead(200, { 'Content-Type': type(file), 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' }); response.end(body);
  } catch {
    response.writeHead(500); response.end('Local resource unavailable');
  }
}).listen(port, '127.0.0.1', () => console.log(`Offline contour demo: http://127.0.0.1:${port}`));
