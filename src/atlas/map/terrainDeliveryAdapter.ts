/** Renderer-specific boundary. This does not define terrain semantics or choose products. */
import type { RasterDEMSourceSpecification } from 'maplibre-gl';
import type { TerrainRegistry } from '../terrain/runtime/terrainRegistry';
import { terrainReferenceKey } from '../terrain/runtime/terrainRegistry';
import type { TerrainSelection } from '../terrain/runtime/terrainSelector';

export function adaptTerrainToMapLibre(registry: TerrainRegistry, selection: TerrainSelection, attribution?: string): RasterDEMSourceSpecification {
  if (selection.status !== 'selected') throw new Error('Cannot adapt unavailable terrain');
  if (selection.hierarchy.id !== registry.hierarchy.id || selection.hierarchy.revision !== registry.hierarchy.revision) throw new Error('Selection belongs to a different hierarchy revision');
  const family = registry.family(selection.family);
  const level = family?.levels.find(l => l.id === selection.level);
  if (!level || level.representation.kind !== 'raster-dem-heightfield') throw new Error('Unsupported terrain representation');
  if (terrainReferenceKey(selection.product) !== terrainReferenceKey(level.representation.product)
    || selection.sourceFamily !== family?.sourceFamily || selection.role !== family.role
    || selection.representation.family !== family.id || selection.representation.level !== level.id
    || selection.representation.kind !== level.representation.kind) throw new Error('Selection identity does not match registered representation');
  const product = registry.product(level.representation.product).product, delivery = product.delivery;
  if (delivery.kind !== 'raster-tiles' || delivery.scheme !== 'xyz' || family?.levelScheme !== 'XYZ Web Mercator zoom (delivery)'
    || delivery.horizontalReference.status !== 'known' || delivery.horizontalReference.value.identifier !== 'EPSG:3857'
    || product.elevationUnit.status !== 'known' || !['metre', 'meter', 'm'].includes(product.elevationUnit.value)
    || !/PNG|WebP/i.test(delivery.format)
    || delivery.tileSize[0] !== delivery.tileSize[1] || !['terrarium', 'mapbox'].includes(delivery.encoding.name.toLowerCase())
    || !Number.isInteger(level.order)) throw new Error('Unsupported MapLibre heightfield delivery');
  const legacy = registry.options.legacyCommon;
  if (selection.support === 'legacy-unassessed' && (!legacy || family.role !== 'common'
    || terrainReferenceKey(legacy.product) !== terrainReferenceKey(selection.product))) throw new Error('Unknown support requires explicit legacy common policy');
  if (selection.support === 'complete' && level.support.state !== 'complete') throw new Error('Incomplete terrain cannot be delivered as complete');
  const maxzoom = delivery.zoom.max.status === 'known' ? Math.min(level.order, delivery.zoom.max.value) : level.order;
  const source: RasterDEMSourceSpecification = { type: 'raster-dem', tiles: [delivery.tileTemplate],
    tileSize: delivery.tileSize[0], encoding: delivery.encoding.name.toLowerCase() as 'terrarium' | 'mapbox', maxzoom };
  if (delivery.zoom.min !== 0) source.minzoom = delivery.zoom.min;
  if (attribution !== undefined) source.attribution = attribution;
  return source;
}
