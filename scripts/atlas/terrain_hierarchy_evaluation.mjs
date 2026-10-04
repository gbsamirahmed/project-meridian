// Opt-in development plugin only. Never referenced by normal Vite configuration.
const HIERARCHY_VISUAL=Object.freeze({tileTemplate:'http://127.0.0.1:4183/tiles/STRATEGY/{z}/{x}/{y}.png',encoding:'terrarium',tileSize:256,geometryMaxZoom:18,reliefMaxZoom:18,attribution:'Copernicus DEM + swissALTI3D (c) swisstopo, modified by Meridian (evaluation; native EGM2008/LN02); <a href="https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf">source licence and obligations</a>'});
export const COMMON_BOUNDS=Object.freeze([7.03125,45.089035564831015,8.4375,47.040182144806664]);
export function hierarchyEvaluationPlugin(provider){
  if(!['common','H0','H1'].includes(provider))throw new Error(`Unknown hierarchy evaluation: ${provider}`);
  return {name:'terrain-hierarchy-evaluation-only',enforce:'pre',load(id){
    if(id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify({...HIERARCHY_VISUAL,tileTemplate:HIERARCHY_VISUAL.tileTemplate.replace('STRATEGY',provider)})};`;
  },transform(code,id){
    if(!id.replaceAll('\\','/').endsWith('/src/atlas/map/terrainLayers.ts'))return;
    let count=0;
    const result=code.replace(/maxzoom: VISUAL_TERRAIN_DEM\.(geometryMaxZoom|reliefMaxZoom),/g,match=>{count++;return `${match}\n      minzoom: 8,\n      bounds: ${JSON.stringify(COMMON_BOUNDS)},`;});
    if(count!==2)throw new Error('Expected both visual DEM sources; evaluation aborted');
    return result;
  }};
}
