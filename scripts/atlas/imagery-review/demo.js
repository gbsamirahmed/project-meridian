import { Map, setWorkerUrl, setWorkerCount } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import './review.css';
import { opacity, policy, sourceWeight, intervalWeight } from '../contour-vector-tiles/rules.mjs';
setWorkerUrl(workerUrl); setWorkerCount(1);
const metadata = await fetch('/metadata').then(r => { if (!r.ok) throw Error('Metadata unavailable'); return r.json(); });
const sources = { orthophoto: { type: 'raster', tiles: [`${location.origin}/imagery/{z}/{x}/{y}.png`],
  tileSize: 512, minzoom: 12, maxzoom: 18, bounds: metadata.bounds, attribution: '©swisstopo / Swiss OGD' },
  shade: { type: 'image', url: '/hillshade.png', coordinates: metadata.hillshadeCoordinates } };
const layers = [{ id: 'background', type: 'background', paint: { 'background-color': '#eeeae2' } },
  { id: 'photo', type: 'raster', source: 'orthophoto', paint: { 'raster-opacity': 1, 'raster-fade-duration': 0 } },
  { id: 'shade', type: 'raster', source: 'shade', layout: { visibility: 'none' }, paint: { 'raster-opacity': 0.18, 'raster-fade-duration': 0 } }];
const products = ['swiss-smoothed', 'swiss-2m', 'swiss-native'];
for (const id of products) {
  sources[id] = { type: 'vector', tiles: [`${location.origin}/contours/${id}/{z}/{x}/{y}.pbf`], minzoom: 10, maxzoom: 17, bounds: metadata.bounds };
  layers.push({ id, type: 'line', source: id, 'source-layer': 'contours',
    minzoom: id === 'swiss-smoothed' ? policy.first : id === 'swiss-2m' ? policy.strictStart : policy.nativeStart,
    maxzoom: id === 'swiss-smoothed' ? policy.strictEnd : id === 'swiss-2m' ? policy.nativeEnd : 24,
    layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: {
      'line-color': ['case', ['get', 'index100'], '#68533b', '#93795a'],
      'line-width': ['case', ['get', 'index100'], 1.3, 0.6], 'line-opacity': opacity(id) } });
}
const map = new Map({ container: 'map', style: { version: 8, sources, layers }, center: metadata.centre,
  zoom: 14, minZoom: 12, maxZoom: 19, pitch: 0, minPitch: 0, maxPitch: 0, dragRotate: false, touchPitch: false });
map.touchZoomRotate.disableRotation();
const status = document.querySelector('#status'), picked = document.querySelector('#picked'), errors = [];
map.on('idle', () => { if (!errors.length) status.textContent = `Zoom ${map.getZoom().toFixed(2)} · flat geometry · imagery dates per pixel unknown`; });
map.on('error', e => { errors.push(e.error.message); status.textContent = 'Local evidence unavailable; stop rather than reload.'; });
map.on('click', e => {
  const features = map.queryRenderedFeatures([[e.point.x - 8, e.point.y - 8], [e.point.x + 8, e.point.y + 8]], { layers: products });
  const feature = features.find(f => intervalWeight(f.properties.elevation_m, map.getZoom()) * sourceWeight(f.layer.id, map.getZoom()) > 0.05);
  picked.textContent = feature ? `${feature.properties.elevation_m} m LN02 · ${feature.properties.source_product} · contour line, not point height` : '';
});
map.on('movestart', () => { picked.textContent = ''; });
document.querySelector('#contours').addEventListener('change', e => { for (const id of products) map.setLayoutProperty(id, 'visibility', e.target.checked ? 'visible' : 'none'); });
document.querySelector('#photo').addEventListener('change', e => map.setLayoutProperty('photo', 'visibility', e.target.checked ? 'visible' : 'none'));
document.querySelector('#shade').addEventListener('change', e => map.setLayoutProperty('shade', 'visibility', e.target.checked ? 'visible' : 'none'));
document.querySelector('#overview').addEventListener('click', () => map.jumpTo({ center: metadata.centre, zoom: 14 }));
document.querySelector('#close').addEventListener('click', () => map.jumpTo({ center: metadata.centre, zoom: 18 }));
window.imageryReview = { map, metadata, errors };
window.addEventListener('pagehide', () => map.remove(), { once: true });
