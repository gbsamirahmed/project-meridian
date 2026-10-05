/** Contract fixtures only. No production registry, selection or provider dependency. */
import { known, unknown } from './terrainMetadata';
import type { EntityReference, TerrainProduct } from './terrainMetadata';
import type {
  RegionalTerrainPyramid, TerrainFamily, TerrainHierarchy,
  TerrainHierarchyLevel, TerrainProductBinding,
} from './terrainHierarchy';

const record = 'docs/atlas/terrain-hierarchy-contract.md';
const ref = (product: TerrainProduct): EntityReference => ({ kind: 'product', id: product.id, revision: product.revision });

export function createTerrainHierarchyExamples(inputs: {
  aws: TerrainProduct; common: TerrainProduct; regional: TerrainProduct;
  parents: TerrainProduct; transition: TerrainProduct;
  /** Final retained output inventory hash, distinct from the transition recipe revision. */
  transitionContentSha256: string;
  contentManifests: { common: string; regional: string; parents: string };
}): { hierarchy: TerrainHierarchy; aws: TerrainHierarchy; secondRegion: TerrainHierarchy } {
  const bind = (product: TerrainProduct, sourceFamily: string, documentation: string): TerrainProductBinding => ({
    product,
    identity: product.revision.status === 'known' ? {
      kind: 'immutable-prepared', revision: product.revision.value,
      preparation: { href: documentation },
      contentManifest: { record: { href: documentation, selector: 'manifestSha256 / recorded output manifest' },
        hashScope: 'manifest-bytes', sha256: product.revision.value },
    } : { kind: 'external-unpinned', reason: 'Hosted content is not pinned by a URL or consumer zoom ceiling.' },
    origin: { kind: 'source-derived', sourceFamily }, validation: [], limitations: [],
  });
  const common = bind(inputs.common, 'common-evidence', 'docs/atlas/copernicus-common-generation.json');
  const swiss = bind(inputs.regional, 'regional-evidence', 'docs/atlas/riffelhorn-support-reproducibility.json');
  const parents = bind(inputs.parents, 'regional-evidence', 'docs/atlas/regional-parent-product.json');
  for (const [binding, hash] of [[common, inputs.contentManifests.common], [swiss, inputs.contentManifests.regional],
    [parents, inputs.contentManifests.parents]] as const) {
    if (binding.identity.kind === 'immutable-prepared') binding.identity.contentManifest.sha256 = hash;
  }
  const transition = bind(inputs.transition, 'derived-evidence', 'docs/atlas/two-band-product.json');
  transition.identity = { kind: 'immutable-prepared', revision: inputs.transition.revision.status === 'known'
    ? inputs.transition.revision.value : 'invalid-unpinned-transition',
  preparation: { href: 'docs/atlas/two-band-product.json' },
  contentManifest: { record: { href: 'docs/atlas/two-band-completion.json', selector: 'inventoryIdentity: canonical tile/mask inventory hash, not completion-file bytes' },
    hashScope: 'canonical-inventory', sha256: inputs.transitionContentSha256 } };
  transition.origin = { kind: 'derived-transition', sourceFamily: 'derived-evidence', compositionPolicy: 'historical-two-band' };
  transition.validation = [
    { category: 'morphology', state: 'failed', scope: 'Two retained glacier/change-proxy patches',
      evidence: [{ href: 'docs/atlas/protected-priority-two-band-transition.md' }],
      limitations: 'Synthetic closed depressions approximately 3.19 m and 1.35 m; not a validated reconciliation algorithm.' },
    { category: 'numerical-continuity', state: 'passed', scope: 'Frozen radial band endpoints only',
      evidence: [{ href: 'docs/atlas/two-band-completion.json' }],
      limitations: 'Does not establish morphology, terrain accuracy or the lower source-family handoff.' },
  ];

  const supportPartition = (product: TerrainProduct, n: number) => {
    const support = product.spatial.validSupport;
    if (support.status === 'known' && support.value.area.kind === 'asset') {
      return { ...support.value.area.asset, selector: `Level z${n}: complete/partial/absent counts or delivered-tile support entries; ${support.value.area.interpretation}` };
    }
    return { href: product.documentation[0], selector: `Level z${n} support/complete-tile records referenced by this product document` };
  };
  const level = (product: TerrainProduct, n: number, derivation: TerrainHierarchyLevel['derivation']): TerrainHierarchyLevel => ({
    id: `z${n}`, order: n, representation: { kind: 'raster-dem-heightfield', product: ref(product), context: 'Contract example; no runtime adoption.' },
    derivation,
    support: { state: 'partial', validSupport: product.spatial.validSupport,
      partition: supportPartition(product, n),
      interpretation: 'Support varies over the level envelope; complete cells/tiles, partial and absent are distinguished in the referenced record.' },
    parentOperation: known({ method: 'Declared source-family averaging/resampling; exact parameters remain in the product lineage.' }),
    sampleSpacing: unknown('Location-dependent delivery spacing is distinct from native observation resolution.'),
  });
  const family = (id: string, sourceFamily: string, product: TerrainProduct, from: number, to: number): TerrainFamily => ({
    id, sourceFamily, role: 'common', levelScheme: 'XYZ Web Mercator zoom (delivery)',
    levels: Array.from({ length: to - from + 1 }, (_, i) => level(product, from + i, 'source-sampled')),
    informationCeiling: product.sourceInformation.informationCeiling,
    overzoom: { allowed: true, description: 'Resampling only; no new observations.' }, limitations: [],
  });
  const commonFamily = { ...family('common', 'common-evidence', inputs.common, 8, 13), role: 'common' as const };
  for (const item of commonFamily.levels) {
    item.derivation = item.order === 13 ? 'resampled' : 'generalized-parent';
    item.support = { state: 'complete', validSupport: inputs.common.spatial.validSupport,
      interpretation: 'Complete coverage inside the two retained roots only; no global/ocean/polar claim.' };
  }
  const regional: RegionalTerrainPyramid = {
    ...family('regional', 'regional-evidence', inputs.regional, 12, 18), role: 'regional',
    levels: [...[10, 11, 12, 13].map(n => level(inputs.parents, n, 'regional-derived-parent')),
      ...[14, 15, 16, 17, 18].map(n => level(inputs.regional, n, 'resampled'))],
    protectedInterior: inputs.regional.spatial.protectedInterior,
    transitionSupport: inputs.regional.spatial.transitionSupport ?? unknown('No validated transition support.'),
  };
  for (const f of [commonFamily, regional]) for (let i = 1; i < f.levels.length; i++) {
    f.levels[i].parent = { family: f.id, level: f.levels[i - 1].id };
  }
  const derived = { ...family('transition', 'derived-evidence', inputs.transition, 10, 18), role: 'transition' as const };
  for (const item of derived.levels) item.derivation = item.order < 12 ? 'generalized-parent' : 'resampled';
  derived.levels[0].parent = { family: 'common', level: 'z9' };
  for (let i = 1; i < derived.levels.length; i++) derived.levels[i].parent = { family: 'transition', level: derived.levels[i - 1].id };
  derived.limitations = ['Common z9 -> derived z10: 41.84 m RMS at the retained 705 points; unresolved source-family handoff.'];
  const hierarchy: TerrainHierarchy = {
    id: 'retained-terrain-contract-example', revision: '1', purpose: 'visual-terrain',
    products: [common, swiss, parents, transition], common: commonFamily, regional: [regional], transitions: [derived],
    compositionPolicies: [{
      id: 'historical-two-band', products: inputs.transition.lineage.contributors,
      operations: inputs.transition.lineage.processing,
      heightPolicy: { kind: 'preserve-native-heterogeneous', rationale: 'Explicit synthetic visual experiment; neither native vertical reference was transformed.', permittedUse: 'visual-representation-only' },
      contribution: { mapping: 'spatial-map', spatiallyVarying: true,
        map: inputs.transition.lineage.contributionMask?.asset,
        semantics: 'signed-operator', reconstruction: { href: 'docs/atlas/two-band-product.json' },
        interpretation: 'Categorical labels plus signed band operator/parent records; not confidence, probability or convex source fractions.' },
      support: inputs.transition.spatial.validSupport,
      protectedInterior: inputs.transition.spatial.protectedInterior,
      validation: transition.validation, limitations: transition.validation.map(item => item.limitations),
    }],
    selection: { regionalOrder: ['regional'], eligibility: { href: record },
      missingFineLevel: 'same-family-parent-then-common', unsupportedRegional: 'common', unavailableTransition: 'common',
      sourceFamilyHandoff: { state: 'unresolved', policy: { href: record } } },
    renderOnlyContinuity: [], limitations: ['Declaration demonstrates expressibility, not accepted product eligibility or safe renderer adoption.'],
  };
  const awsBinding = bind(inputs.aws, 'legacy-hosted-evidence', record);
  awsBinding.origin = { kind: 'unresolved', reason: 'Hosted heterogeneous derivative has incomplete upstream processing/contributor lineage.' };
  const awsFamily = { ...family('legacy-common', 'legacy-hosted-evidence', inputs.aws, 0, 15), role: 'common' as const };
  for (const item of awsFamily.levels) item.support = { state: 'unknown', validSupport: inputs.aws.spatial.validSupport,
    interpretation: 'Consumer ceiling is not proof of complete hosted support or information.' };
  const aws: TerrainHierarchy = { ...hierarchy, id: 'current-visual-policy-example', products: [awsBinding],
    common: awsFamily, regional: [], transitions: [], compositionPolicies: [],
    selection: { ...hierarchy.selection, regionalOrder: [] } };

  // Intentionally synthetic second region: no claim of a processed Welsh asset or licence.
  const secondProduct = structuredClone(inputs.regional);
  secondProduct.id = 'second-region-fixture'; secondProduct.name = 'Generic second regional DTM fixture';
  secondProduct.version = known('fixture-1');
  secondProduct.surface = { kind: 'dtm', description: 'Hypothetical second-region bare-earth representation; no real dataset claim.' };
  secondProduct.producer = known('Synthetic contract fixture');
  secondProduct.vertical = { kind: 'unknown', reason: 'Actual second-region height system must be verified before preparation.' };
  secondProduct.spatial = { coverage: known({ kind: 'native-rectangle', crs: { name: 'British National Grid', identifier: 'EPSG:27700' },
    bounds: [265000, 358000, 267000, 360000], axisOrder: 'xy' }),
  validSupport: known({ area: { kind: 'native-rectangle', crs: { name: 'British National Grid', identifier: 'EPSG:27700' },
    bounds: [265100, 358100, 266900, 359900], axisOrder: 'xy' }, purpose: 'Synthetic visual fixture', basis: 'Fixture only; no Welsh terrain acquired.' }) };
  secondProduct.revision = known('fixture-1');
  secondProduct.delivery = { kind: 'other', description: 'Synthetic heightfield delivery fixture; no network endpoint or generated data.', assets: [] };
  secondProduct.sourceInformation = { description: 'Synthetic second-region family; actual grid/measurement information not yet established.', informationCeiling: unknown('Fixture contains no measured information.') };
  secondProduct.generation = { timestamp: unknown('No second-region product generated.') };
  secondProduct.nodata = unknown('Fixture only.');
  secondProduct.documentation = [record];
  secondProduct.temporal = { epochs: unknown('No verified acquisition epoch for the synthetic second-region fixture.') };
  secondProduct.lineage = { contributors: [{ kind: 'source', id: 'second-region-source-fixture', revision: known('fixture-1') }],
    contributorList: 'complete', spatialMapping: 'uniform', processing: [{ method: 'Synthetic declared preparation only' }], limitations: 'No measured Welsh terrain or actual rights represented.' };
  secondProduct.rights = { licence: unknown('Real Welsh source terms must be verified separately.'), references: [], attribution: [] };
  const secondBinding = bind(secondProduct, 'second-region-evidence', record);
  secondBinding.identity = { kind: 'immutable-prepared', revision: 'fixture-1', preparation: { href: record },
    contentManifest: { record: { href: record, selector: 'Synthetic fixture only' },
      hashScope: 'canonical-inventory', sha256: '0'.repeat(64) } }; // Synthetic token, never a verified external hash.
  const secondFamily: RegionalTerrainPyramid = {
    ...family('second-region', 'second-region-evidence', secondProduct, 12, 16), role: 'regional',
    transitionSupport: unknown('No prepared transition in this synthetic example.'),
  };
  for (let i = 1; i < secondFamily.levels.length; i++) secondFamily.levels[i].parent = { family: 'second-region', level: secondFamily.levels[i - 1].id };
  const secondRegion: TerrainHierarchy = { ...hierarchy, id: 'second-region-contract-fixture',
    products: [common, secondBinding], regional: [secondFamily], transitions: [], compositionPolicies: [],
    selection: { ...hierarchy.selection, regionalOrder: ['second-region'] } };
  return { hierarchy, aws, secondRegion };
}
