// Evaluation-only: pure regional source, no AWS composition/fallback or UI selector.
export const SUPPORT_VISUAL=Object.freeze({tileTemplate:'http://127.0.0.1:4181/tiles/{z}/{x}/{y}.png',encoding:'terrarium',tileSize:256,geometryMaxZoom:18,reliefMaxZoom:18,attribution:'©swisstopo (experimental regional visual terrain)'});
export function supportEvaluationPlugin(provider){
  if(!['aws','support'].includes(provider))throw new Error(`Unknown support evaluation: ${provider}`);
  return {name:'riffelhorn-support-evaluation-only',enforce:'pre',load(id){
    if(provider==='support'&&id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(SUPPORT_VISUAL)};`;
  },transform(code,id){
    if(provider!=='support'||!id.replaceAll('\\','/').endsWith('/src/atlas/map/terrainLayers.ts'))return;
    // Native source delivery limits only, never presentation or production files.
    let count=0;
    const result=code.replace(/maxzoom: VISUAL_TERRAIN_DEM\.(geometryMaxZoom|reliefMaxZoom),/g,match=>{count++;return `${match}\n      minzoom: 12,\n      bounds: [7.696489552439658,45.933928484248874,7.826043211954982,46.024250922603905],`;});
    if(count!==2)throw new Error('DEM-source evaluation insertion no longer matches both sources');
    return result;
  }};
}
