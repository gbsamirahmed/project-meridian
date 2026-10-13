import * as maplibre from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import './demo.css';
import { opacity, policy, sourceWeight, intervalWeight } from './rules.mjs';

maplibre.setWorkerUrl(workerUrl); maplibre.setWorkerCount(1);
const status = document.getElementById('status'), mode = document.getElementById('mode'), interval = document.getElementById('interval');
const started = performance.now(), metadata = await fetch('/product.json').then(response => {
  if (!response.ok) throw new Error('Local product manifest unavailable'); return response.json();
}).catch(error => { status.textContent = error.message; throw error; });
const metrics = { firstIdleMs: null, errors: [], pitch: 0, terrain: false };
const sources = { shading: { type: 'image', url: '/hillshade-mercator.png', coordinates: metadata.background.imageCoordinates } };
const layers = [{ id: 'background', type: 'background', paint: { 'background-color': '#f4f1e8' } },
  { id: 'shading', type: 'raster', source: 'shading', paint: { 'raster-opacity': 0.5, 'raster-fade-duration': 0 } }];
for (const product of metadata.products) {
  sources[product.id] = { type: 'vector', tiles: [`${location.origin}/tiles/${product.id}/{z}/{x}/{y}.pbf`],
    minzoom: 10, maxzoom: 17, bounds: metadata.boundsLonLat, attribution: '©swisstopo / Swiss OGD' };
  const minzoom = product.id === 'swiss-smoothed' ? policy.first : product.id === 'swiss-2m' ? policy.strictStart : policy.nativeStart;
  const maxzoom = product.id === 'swiss-smoothed' ? policy.strictEnd : product.id === 'swiss-2m' ? policy.nativeEnd : 24;
  layers.push({ id: product.id, type: 'line', source: product.id, 'source-layer': 'contours', minzoom, maxzoom,
    layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: {
      'line-color': ['case', ['get', 'index100'], '#68533b', '#93795a'],
      'line-width': ['case', ['get', 'index100'], 1.3, 0.6], 'line-opacity': opacity(product.id) } });
}
const map = new maplibre.Map({ container: 'map', style: { version: 8, sources, layers },
  center: metadata.centre, zoom: 14, minZoom: 8, maxZoom: 21, pitch: 0, minPitch: 0, maxPitch: 0,
  bearing: 0, dragRotate: false, pitchWithRotate: false, touchPitch: false,
  canvasContextAttributes: { preserveDrawingBuffer: true } });
map.touchZoomRotate.disableRotation(); map.keyboard.disableRotation();
map.addControl(new maplibre.NavigationControl({ showCompass: false }), 'top-right');
let popup;
function clearPick() {
  popup?.remove(); popup = null;
  document.getElementById('picked').textContent = 'Click a line to inspect its retained elevation.';
}
map.on('movestart', clearPick);
map.on('error', event => { metrics.errors.push(String(event.error.message)); status.textContent = `Local map error: ${event.error.message}`; });
function summary() {
  if (metrics.errors.length) return;
  const zoom = map.getZoom();
  const bands = zoom < policy.first ? 'contours hidden' : zoom < policy.first + policy.fade ? 'hidden→100 m'
    : zoom < policy.fifty ? '100 m' : zoom < policy.fifty + policy.fade ? '100→50 m'
      : zoom < policy.twenty ? '50 m' : zoom < policy.twenty + policy.fade ? '50→20 m'
        : zoom < policy.ten ? '20 m' : zoom < policy.ten + policy.fade ? '20→10 m' : '10 m';
  const products = mode.value === 'auto' ? metadata.products.filter(product => sourceWeight(product.id, zoom) > 0)
    .map(product => `${product.id} ${Math.round(sourceWeight(product.id, zoom) * 100)}%`).join(' / ') : mode.value;
  status.textContent = `Zoom ${zoom.toFixed(2)} · ${mode.value === 'auto' ? bands : `${interval.value} m manual`} · ${products} · LN02`;
}
map.on('move', summary);
map.once('idle', () => { metrics.firstIdleMs = performance.now() - started; summary(); });
map.on('load', () => {
  for (const id of metadata.products.map(product => product.id)) map.on('click', id, event => {
    // MapLibre queries can include feature-dependent zero-opacity lines.
    const feature = event.features.find(feature => mode.value === 'auto'
      ? intervalWeight(feature.properties.elevation_m, map.getZoom()) * sourceWeight(id, map.getZoom()) > 0.05
      : mode.value === id && feature.properties.elevation_m % Number(interval.value) === 0);
    if (!feature) return;
    const p = feature.properties, text = `${p.elevation_m} m ${p.vertical_ref} · ${p.source_product} · source line ${p.source_line}`;
    const element = document.createElement('div'); element.textContent = text;
    popup?.remove(); popup = new maplibre.Popup().setLngLat(event.lngLat).setDOMContent(element).addTo(map);
    document.getElementById('picked').textContent = text;
  });
});
const update = () => {
  clearPick();
  interval.disabled = mode.value === 'auto';
  for (const product of metadata.products) {
    const automatic = mode.value === 'auto';
    const min = automatic ? product.id === 'swiss-smoothed' ? policy.first : product.id === 'swiss-2m' ? policy.strictStart : policy.nativeStart : 10;
    const max = automatic ? product.id === 'swiss-smoothed' ? policy.strictEnd : product.id === 'swiss-2m' ? policy.nativeEnd : 24 : 24;
    map.setLayerZoomRange(product.id, min, max);
    map.setLayoutProperty(product.id, 'visibility', automatic || mode.value === product.id ? 'visible' : 'none');
    map.setPaintProperty(product.id, 'line-opacity', opacity(product.id, mode.value, Number(interval.value)));
  }
  summary();
};
mode.addEventListener('change', update); interval.addEventListener('change', update);
document.getElementById('fit').addEventListener('click', () => map.jumpTo({ center: metadata.centre, zoom: 14, pitch: 0, bearing: 0 }));
document.getElementById('regional').addEventListener('click', () => map.jumpTo({ center: metadata.centre, zoom: 9.5, pitch: 0, bearing: 0 }));
document.getElementById('shading').addEventListener('change', event => map.setPaintProperty('shading', 'raster-opacity', event.target.checked ? 0.5 : 0));
window.meridianTiles = { map, metadata, metrics, policy };
window.addEventListener('pagehide', () => map.remove(), { once: true });
