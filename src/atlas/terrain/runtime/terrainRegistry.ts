import type { AssetReference, EntityReference, SpatialArea } from '../metadata/terrainMetadata';
import type { TerrainFamily, TerrainHierarchy, TerrainProductBinding } from '../metadata/terrainHierarchy';
import { validateTerrainHierarchy, validateTerrainIdentityReuse } from '../metadata/terrainHierarchyValidation';
import { validateTerrainSpatialArea } from '../metadata/terrainMetadataValidation';

export const terrainReferenceKey = (ref: EntityReference): string => JSON.stringify([ref.kind, ref.id,
  ref.revision.status === 'known' ? ref.revision.value : null]);
const assetKey = (asset: AssetReference) => JSON.stringify([asset.href, asset.sha256 ?? null, asset.selector ?? null]);
export interface TerrainRegistryOptions {
  /** Explicit scale catalogue supports requests for levels omitted by a family; no parsing of provider names. */
  scaleLevels?: readonly { scheme: string; id: string; order: number }[];
  /** Owned, already-assessed geometry for an asset-backed support record. Never fetched by selection. */
  resolvedAreas?: readonly { asset: AssetReference; area: SpatialArea }[];
  enabledTransitions?: readonly string[];
  /** Retain an existing external common service under an explicit operational policy.
   * Addressing extent is NOT assessed valid terrain support. Regional products cannot opt in. */
  legacyCommon?: { product: EntityReference; addressingExtent: SpatialArea; policy: AssetReference };
}
export interface TerrainRegistry {
  readonly hierarchy: TerrainHierarchy;
  readonly options: TerrainRegistryOptions;
  family(id: string): TerrainFamily | undefined;
  product(ref: EntityReference): TerrainProductBinding;
  levelOrder(scheme: string, id: string): number | undefined;
  area(area: SpatialArea): SpatialArea;
}
function freeze<T>(value: T): T {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
export function registerTerrainHierarchy(input: TerrainHierarchy, options: TerrainRegistryOptions = {}, previous?: TerrainRegistry): TerrainRegistry {
  if (!input.common || !Array.isArray(input.products) || !input.products.length) throw new Error('Invalid terrain registration: a common family and registered products are required');
  const errors = [...validateTerrainHierarchy(input), ...(previous ? validateTerrainIdentityReuse(previous.hierarchy, input) : [])];
  const hierarchy = structuredClone(input), settings = structuredClone(options);
  const families = [hierarchy.common, ...hierarchy.regional, ...hierarchy.transitions];
  const familyMap = new Map(families.map(f => [f.id, f]));
  const products = new Map(hierarchy.products.map(binding => [terrainReferenceKey({ kind: 'product', id: binding.product.id, revision: binding.product.revision }), binding]));
  const orders = new Map<string, number>(), ids = new Map<string, string>();
  const addLevel = (scheme: string, id: string, order: number) => {
    const key = JSON.stringify([scheme, id]), ordinal = JSON.stringify([scheme, order]);
    if (!scheme.trim() || !id.trim() || !Number.isFinite(order)) errors.push('scale catalogue requires identity and finite order');
    if ((orders.has(key) && orders.get(key) !== order) || (ids.has(ordinal) && ids.get(ordinal) !== id)) errors.push('ambiguous scale catalogue identity/order');
    orders.set(key, order); ids.set(ordinal, id);
  };
  settings.scaleLevels?.forEach(l => addLevel(l.scheme, l.id, l.order));
  for (const family of families) for (const level of family.levels) {
    addLevel(family.levelScheme, level.id, level.order);
    if (level.support.validSupport.status === 'known') errors.push(...validateTerrainSpatialArea(level.support.validSupport.value.area));
    const product = products.get(terrainReferenceKey(level.representation.product))?.product;
    if (family.levelScheme === 'XYZ Web Mercator zoom (delivery)' && product?.delivery.kind === 'raster-tiles' && ['complete', 'unknown'].includes(level.support.state)) {
      const zoom = product.delivery.zoom;
      if (!Number.isInteger(level.order) || level.order < zoom.min || (zoom.max.status === 'known' && level.order > zoom.max.value && level.derivation !== 'overzoom')) errors.push('level outside product delivery range');
      if (level.derivation === 'overzoom' && !family.overzoom.allowed) errors.push('overzoom level requires explicit family permission');
    }
  }
  const geometryErrors = validateTerrainSpatialArea;
  const areas = new Map<string, SpatialArea>();
  for (const entry of settings.resolvedAreas ?? []) {
    if (areas.has(assetKey(entry.asset)) || entry.area.kind === 'asset') errors.push('duplicate or unresolved support geometry');
    errors.push(...geometryErrors(entry.area));
    areas.set(assetKey(entry.asset), entry.area);
  }
  for (const id of settings.enabledTransitions ?? []) if (!hierarchy.transitions.some(f => f.id === id)) errors.push('enabled transition family must be registered');
  if (settings.legacyCommon) {
    const legacy = settings.legacyCommon, binding = products.get(terrainReferenceKey(legacy.product));
    if (!binding || binding.identity.kind !== 'external-unpinned' || !legacy.policy.href.trim()
      || legacy.addressingExtent.kind === 'asset' || !hierarchy.common.levels.every(l => terrainReferenceKey(l.representation.product) === terrainReferenceKey(legacy.product))) errors.push('legacy compatibility requires the explicitly registered external common product and operational policy');
    errors.push(...geometryErrors(legacy.addressingExtent));
  }
  if (errors.length) throw new Error(`Invalid terrain registration:\n${errors.join('\n')}`);
  freeze(hierarchy); freeze(settings);
  return Object.freeze({ hierarchy, options: settings,
    family: (id: string) => familyMap.get(id),
    product: (ref: EntityReference) => {
      const binding = products.get(terrainReferenceKey(ref));
      if (!binding) throw new Error('Unregistered terrain product revision');
      return binding;
    },
    levelOrder: (scheme: string, id: string) => orders.get(JSON.stringify([scheme, id])),
    area: (area: SpatialArea) => area.kind === 'asset' ? areas.get(assetKey(area.asset)) ?? area : area,
  });
}
