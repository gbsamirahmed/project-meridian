// Opt-in development plugin only. Never referenced by normal Vite configuration.
export const COMMON_VISUAL=Object.freeze({tileTemplate:'http://127.0.0.1:4182/tiles/{z}/{x}/{y}.png',encoding:'terrarium',tileSize:256,geometryMaxZoom:13,reliefMaxZoom:13,attribution:'Copernicus DEM, modified by Meridian (evaluation); <a href="https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf">source licence and obligations</a>'});
export const COMMON_BOUNDS=Object.freeze([7.03125,45.089035564831015,8.4375,47.040182144806664]);
export function commonEvaluationPlugin(provider){
  if(!['aws','common'].includes(provider))throw new Error(`Unknown common evaluation: ${provider}`);
  return {name:'copernicus-common-evaluation-only',enforce:'pre',load(id){
    if(provider==='common'&&id.replaceAll('\\','/').endsWith('/src/atlas/map/visualTerrainConfig.ts'))return `export const VISUAL_TERRAIN_DEM=${JSON.stringify(COMMON_VISUAL)};`;
  },transform(code,id){
    if(provider!=='common'||!id.replaceAll('\\','/').endsWith('/src/atlas/map/terrainLayers.ts'))return;
    let count=0;
    const result=code.replace(/maxzoom: VISUAL_TERRAIN_DEM\.(geometryMaxZoom|reliefMaxZoom),/g,match=>{count++;return `${match}\n      minzoom: 8,\n      bounds: ${JSON.stringify(COMMON_BOUNDS)},`;});
    if(count!==2)throw new Error('Expected both visual DEM sources; evaluation aborted');
    return result;
  }};
}
