// Development/evaluation only. No src/ or normal vite.config import.
export const RIFFELHORN_VISUAL = Object.freeze({
  tileTemplate: 'http://127.0.0.1:4180/tiles/{z}/{x}/{y}.png',
  encoding: 'terrarium', tileSize: 256, geometryMaxZoom: 18, reliefMaxZoom: 18,
  attribution: '<a href="https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices" target="_blank" rel="noopener">©swisstopo (regional visual terrain)</a> · <a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">AWS terrain data credits</a>',
});

export function riffelhornEvaluationPlugin(provider) {
  if (!['aws', 'riffelhorn'].includes(provider)) throw new Error(`Unknown regional evaluation source: ${provider}`);
  return {name:'riffelhorn-visual-evaluation-only',enforce:'pre',load(id) {
    if (provider==='riffelhorn' && id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts')) {
      return `export const VISUAL_TERRAIN_DEM = ${JSON.stringify(RIFFELHORN_VISUAL)};`;
    }
  }};
}
