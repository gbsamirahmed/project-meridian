// Evaluation-only configuration: never imported by src/ or the production Vite config.
// Verified 2026-10-03; not a production source registry or a promise of regional coverage.
export const MAPTERHORN_EVALUATION = Object.freeze({
  tileTemplate: 'https://tiles.mapterhorn.com/{z}/{x}/{y}.webp',
  encoding: 'terrarium', tileSize: 512, geometryMaxZoom: 14, reliefMaxZoom: 15,
  attribution: '<a href="https://mapterhorn.com/attribution/" target="_blank" rel="noopener">© Mapterhorn / terrain sources</a> · © Welsh Government and NRW · Contains Environment Agency information © Environment Agency and database right · ©swisstopo · Dati estratti dal Modello Digitale del Terreno (DTM) della Regione Autonoma Valle d\'Aosta · © Istituto Nazionale di Geofisica e Vulcanologia (INGV) · produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved',
});

export function visualEvaluationPlugin(provider) {
  if (!['aws', 'mapterhorn', 'mapterhorn-extended'].includes(provider)) {
    throw new Error(`Unknown evaluation source: ${provider}`);
  }
  return {
    name: 'atlas-visual-source-evaluation-only', enforce: 'pre',
    load(id) {
      if (provider === 'aws' || !id.replaceAll('\\', '/').endsWith('/src/atlas/map/visualTerrainConfig.ts')) return;
      const policy = provider === 'mapterhorn-extended'
        ? {...MAPTERHORN_EVALUATION, geometryMaxZoom: 17, reliefMaxZoom: 17}
        : MAPTERHORN_EVALUATION;
      return `export const VISUAL_TERRAIN_DEM = ${JSON.stringify(policy)};`;
    },
  };
}
