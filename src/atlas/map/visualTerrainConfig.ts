/** Visual compatibility policy. Analytical elevation owns its separate AWS z15 policy. */
import { productionTerrainRegistry } from '../terrain/runtime/productionTerrainHierarchy';
import { selectTerrain } from '../terrain/runtime/terrainSelector';
import { adaptTerrainToMapLibre } from './terrainDeliveryAdapter';

const attribution = '<a href="https://github.com/tilezen/joerd/blob/master/docs/attribution.md" target="_blank" rel="noopener">Terrain data credits</a>';
function sourceAt(level: string) {
  // Resolve the sole nominal global service at setup; this is not camera/viewport source switching.
  const selection = selectTerrain(productionTerrainRegistry, {
    location: { coordinates: [0, 0], crs: 'EPSG:3857' },
    scale: { scheme: 'XYZ Web Mercator zoom (delivery)', requestedLevel: level }, provenanceRequirement: 'product-lineage',
  });
  return adaptTerrainToMapLibre(productionTerrainRegistry, selection, attribution);
}
const geometry = sourceAt('z14'), relief = sourceAt('z15');
export const VISUAL_TERRAIN_DEM = {
  tileTemplate: geometry.tiles![0], encoding: geometry.encoding!, tileSize: geometry.tileSize!,
  geometryMaxZoom: geometry.maxzoom!, reliefMaxZoom: relief.maxzoom!, attribution,
} as const;
