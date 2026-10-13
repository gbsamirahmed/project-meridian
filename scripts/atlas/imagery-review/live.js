import { Map, addProtocol, removeProtocol, setWorkerUrl, setWorkerCount } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import './review.css';
import { createTrial, validateMetadata } from './live-resources.mjs';
const status = document.querySelector('#status');
const trial = createTrial();
const places = [
  ['Riffelhorn', [7.76121, 45.97911]], ['Lauterbrunnen', [7.908, 46.594]],
  ['Cairngorms', [-3.66, 57.09]], ['Stonehaven', [-2.21, 56.96]], ['Edinburgh', [-3.19, 55.95]],
];
let selected = 0, mpp = 3;
const zoom = () => Math.log2(40075016.6856 * Math.cos(places[selected][1][1] * Math.PI / 180) / (512 * mpp));
try {
  if (!__MAPTILER_KEY__) throw Error('Live mode disabled');
  const permit = await fetch('/live-permit', { method: 'POST' });
  if (!permit.ok) throw Error('No additional live document permitted');
  const bytes = await trial.get(`https://api.maptiler.com/tiles/satellite-v2/tiles.json?key=${encodeURIComponent(__MAPTILER_KEY__)}`, 'metadata');
  const metadata = JSON.parse(new TextDecoder().decode(bytes));
  const template = validateMetadata(metadata, __MAPTILER_KEY__);
  const local = await fetch('/metadata').then(r => r.json());
  addProtocol('reviewimage', async (request, controller) => {
    const match = /^reviewimage:\/\/(\d+)\/(\d+)\/(\d+)$/.exec(request.url);
    if (!match) { trial.stop(); throw Error('Unexpected tile path'); }
    const [z, x, y] = match.slice(1).map(Number);
    if (z > 22 || x >= 2 ** z || y >= 2 ** z) { trial.stop(); throw Error('Invalid tile coordinates'); }
    const url = template.replace('{z}', z).replace('{x}', x).replace('{y}', y);
    return { data: await trial.get(url, 'imagery', controller.signal) };
  });
  setWorkerUrl(workerUrl); setWorkerCount(1);
  const map = new Map({ container: 'map', center: places[0][1], zoom: zoom(), pitch: 0, maxPitch: 0,
    minZoom: 12, maxZoom: 19, dragRotate: false, touchPitch: false, fadeDuration: 0,
    style: { version: 8, sources: {
      global: { type: 'raster', tiles: ['reviewimage://{z}/{x}/{y}'], tileSize: 512, minzoom: 0, maxzoom: 22, attribution: metadata.attribution },
      swiss: { type: 'raster', tiles: [`${location.origin}/imagery/{z}/{x}/{y}.png`], tileSize: 512, minzoom: 12, maxzoom: 18, bounds: local.bounds, attribution: '©swisstopo' },
    }, layers: [{ id: 'global', type: 'raster', source: 'global', paint: { 'raster-fade-duration': 0 } },
      { id: 'swiss', type: 'raster', source: 'swiss', layout: { visibility: 'none' }, paint: { 'raster-fade-duration': 0 } }] } });
  map.touchZoomRotate.disableRotation();
  // The official logo stays visible; it is not downloaded into an archive.
  const logo = document.createElement('a'); logo.href = 'https://www.maptiler.com/';
  logo.style.cssText = 'position:fixed;bottom:28px;left:10px;z-index:2;background:white';
  const image = document.createElement('img'); image.src = 'https://api.maptiler.com/resources/logo.svg'; image.alt = 'MapTiler'; image.width = 100;
  logo.append(image); document.body.append(logo);
  const errors = [], observations = [];
  const report = () => { status.textContent = `${places[selected][0]} · ${mpp} m/CSS px · z${map.getZoom().toFixed(2)} · ${trial.stats.imageryAttempts}/100 tiles · ${trial.stats.responseBytes} bytes${trial.stats.stopped ? ' · STOPPED' : ''}`; };
  map.on('idle', report); map.on('error', () => { errors.push('Map/provider failure'); trial.stop(); report(); });
  const move = () => {
    if (trial.stats.stopped) return;
    document.querySelector('#swiss').checked = false; map.setLayoutProperty('swiss', 'visibility', 'none');
    map.jumpTo({ center: places[selected][1], zoom: zoom() }); report();
  };
  for (const [index, [name]] of places.entries()) {
    const button = document.createElement('button'); button.textContent = name;
    button.onclick = () => { selected = index; move(); }; document.querySelector('#places').append(button);
  }
  document.querySelector('#wide').onclick = () => { mpp = 3; move(); };
  document.querySelector('#detail').onclick = () => { mpp = 0.5; move(); };
  document.querySelector('#swiss').onchange = e => {
    if (selected !== 0) { e.target.checked = false; return; }
    map.setLayoutProperty('swiss', 'visibility', e.target.checked ? 'visible' : 'none');
  };
  document.querySelector('#stop').onclick = () => { trial.stop(); report(); };
  window.liveReview = { map, trial, errors, observations, metadata: { minzoom: metadata.minzoom, maxzoom: metadata.maxzoom, attribution: metadata.attribution } };
  window.addEventListener('pagehide', () => { trial.stop(); map.remove(); removeProtocol('reviewimage'); }, { once: true });
} catch { trial.stop(); status.textContent = 'Trial unavailable/refused; stop without reloading. No alternate provider.'; }
