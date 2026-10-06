// Research mathematics only; no production imports or selection policy.
export const WORLD = 2 * Math.PI * 6378137;
export function metresPerPixel(latitude, zoom, tileSize = 512) {
  if (!Number.isFinite(latitude) || Math.abs(latitude) > 85.0511287798066 || !Number.isFinite(zoom) || !Number.isFinite(tileSize) || tileSize <= 0) throw new Error('Invalid Mercator scale');
  return WORLD * Math.cos(latitude * Math.PI / 180) / (tileSize * 2 ** zoom);
}
export function zoomForScale(latitude, metres) {
  if (!(metres > 0)) throw new Error('Invalid display scale');
  return Math.log2(metresPerPixel(latitude, 0) / metres);
}
export function localVector(a, b) {
  const latitude = (a[1] + b[1]) / 2 * Math.PI / 180;
  return [(b[0] - a[0]) * Math.PI / 180 * 6378137 * Math.cos(latitude), (b[1] - a[1]) * Math.PI / 180 * 6378137, b[2] - a[2]];
}
export function surfaceMetric(origin, east, south, pixels = 2) {
  if (!(pixels > 0) || [origin,east,south].flat().some(v=>!Number.isFinite(v))) throw new Error('Invalid surface probes');
  const a=localVector(origin,east).map(v=>v/pixels), b=localVector(origin,south).map(v=>v/pixels);
  const dot=(u,v)=>u.reduce((s,x,i)=>s+x*v[i],0), aa=dot(a,a), bb=dot(b,b), ab=dot(a,b);
  const delta=Math.hypot(aa-bb,2*ab), major=Math.sqrt(Math.max(0,(aa+bb+delta)/2)), minor=Math.sqrt(Math.max(0,(aa+bb-delta)/2));
  return {horizontalX:Math.hypot(...a.slice(0,2)),horizontalY:Math.hypot(...b.slice(0,2)),surfaceX:Math.sqrt(aa),surfaceY:Math.sqrt(bb),principalMajor:major,principalMinor:minor,surfaceAreaPerPixel:Math.sqrt(Math.max(0,aa*bb-ab*ab)),anisotropy:minor>0?major/minor:null};
}
export function igorStrength(zoom, stops) {
  if (zoom<=stops[0][0]) return stops[0][1];
  for(let i=1;i<stops.length;i++)if(zoom<=stops[i][0]){const a=stops[i-1],b=stops[i];return a[1]+(b[1]-a[1])*(zoom-a[0])/(b[0]-a[0]);}
  return stops.at(-1)[1];
}
