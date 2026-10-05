/** Current visual compatibility policy, not adoption of experimental terrain. */
import { AWS_VISUAL_PRODUCT } from '../metadata/awsVisualTerrainProduct';
import { unknown } from '../metadata/terrainMetadata';
import type { TerrainHierarchy } from '../metadata/terrainHierarchy';
import { registerTerrainHierarchy } from './terrainRegistry';

const record = { href: 'docs/atlas/terrain-runtime-selection.md' };
const product = { kind: 'product' as const, id: AWS_VISUAL_PRODUCT.id, revision: AWS_VISUAL_PRODUCT.revision };
export const PRODUCTION_TERRAIN_HIERARCHY: TerrainHierarchy = {
  id: 'production-visual-terrain', revision: 'aws-compatibility-1', purpose: 'visual-terrain',
  products: [{ product: AWS_VISUAL_PRODUCT, identity: { kind: 'external-unpinned', reason: 'Current hosted AWS terrain has no established immutable release.' },
    origin: { kind: 'unresolved', reason: 'Hosted contributor and transformation lineage remains incomplete.' }, validation: [], limitations: ['Operational compatibility is not an accuracy or global validity claim.'] }],
  common: { id: 'production-common', role: 'common', sourceFamily: 'legacy-hosted-terrain', levelScheme: 'XYZ Web Mercator zoom (delivery)',
    levels: Array.from({ length: 16 }, (_, order) => ({ id: `z${order}`, order,
      representation: { kind: 'raster-dem-heightfield' as const, product, context: 'Existing visual terrain delivery ceiling; independent analytical policy.' },
      derivation: 'resampled' as const, support: { state: 'unknown' as const, validSupport: AWS_VISUAL_PRODUCT.spatial.validSupport, interpretation: 'Hosted validity is unassessed; explicit legacy policy retains current visual fallback.' },
      parentOperation: unknown('Hosted parent preparation is not established.'), sampleSpacing: unknown('Consumer level does not establish independent information.') })),
    informationCeiling: AWS_VISUAL_PRODUCT.sourceInformation.informationCeiling,
    overzoom: { allowed: true, description: 'Renderer resampling above the consumed source ceiling adds no information.' }, limitations: ['Hosted content and upstream vertical semantics are unpinned.'] },
  regional: [], transitions: [], compositionPolicies: [],
  selection: { regionalOrder: [], eligibility: record, missingFineLevel: 'same-family-parent-then-common', unsupportedRegional: 'common', unavailableTransition: 'common', sourceFamilyHandoff: { policy: record, state: 'unresolved' } },
  renderOnlyContinuity: [], limitations: ['Retains current production output; no regional hierarchy or reconciliation is enabled.'],
};
if (AWS_VISUAL_PRODUCT.spatial.coverage.status !== 'known') throw new Error('Legacy addressing extent must be declared');
export const productionTerrainRegistry = registerTerrainHierarchy(PRODUCTION_TERRAIN_HIERARCHY, {
  legacyCommon: { product, addressingExtent: AWS_VISUAL_PRODUCT.spatial.coverage.value, policy: record },
});
