/** Semantic checks for owned typed declarations, not an external JSON parser,
 * spatial eligibility engine, licence clearance or scientific validation. */
import type { EntityReference } from './terrainMetadata';
import { validateTerrainProduct } from './terrainMetadataValidation';
import type { TerrainFamily, TerrainHierarchy, TerrainHierarchyLevel, TerrainLevelReference, TerrainValidationEvidence } from './terrainHierarchy';

const refKey = (ref: EntityReference) => JSON.stringify([ref.kind, ref.id,
  ref.revision.status === 'known' ? ['known', ref.revision.value] : ['unknown']]);
const levelKey = (ref: TerrainLevelReference) => JSON.stringify([ref.family, ref.level]);
const canonical = (value: unknown): string => {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.entries(value).sort(([a], [b]) => a.localeCompare(b))
      .map(([key, item]) => `${JSON.stringify(key)}:${canonical(item)}`).join(',')}}`;
  }
  return JSON.stringify(value) ?? 'undefined';
};

export function validateTerrainHierarchy(hierarchy: TerrainHierarchy): string[] {
  const errors: string[] = [];
  const check = (condition: boolean, message: string) => { if (!condition) errors.push(message); };
  const evidence = (records: readonly TerrainValidationEvidence[]) => {
    for (const item of records) {
      check(Boolean(item.scope.trim()), 'validation evidence requires a scope');
      check(item.state === 'not-assessed' || item.evidence.length > 0,
        'assessed validation requires evidence, not a continuity boolean');
    }
  };
  check(Boolean(hierarchy.id.trim() && hierarchy.revision.trim()), 'hierarchy requires identity/revision');
  check(hierarchy.purpose === 'visual-terrain', 'hierarchy does not replace analytical elevation');
  const families = [hierarchy.common, ...hierarchy.regional, ...hierarchy.transitions];
  const familyMap = new Map(families.map(family => [family.id, family]));
  check(familyMap.size === families.length, 'duplicate family identity');
  const products = new Map(hierarchy.products.map(binding => [refKey({
    kind: 'product', id: binding.product.id, revision: binding.product.revision,
  }), binding]));
  check(products.size === hierarchy.products.length, 'duplicate product revision binding');
  const policies = new Map(hierarchy.compositionPolicies.map(policy => [policy.id, policy]));
  check(policies.size === hierarchy.compositionPolicies.length, 'duplicate composition policy');
  for (const binding of hierarchy.products) {
    errors.push(...validateTerrainProduct(binding.product).map(error => `${binding.product.id}: ${error}`));
    if (binding.identity.kind === 'immutable-prepared') {
      check(binding.product.revision.status === 'known'
        && binding.product.revision.value === binding.identity.revision,
      'immutable revision must match the product revision');
      check(Boolean(binding.identity.revision.trim() && binding.identity.preparation.href.trim()),
        'immutable prepared product requires a revision and preparation record');
      check(/^[a-f0-9]{64}$/i.test(binding.identity.contentManifest.sha256)
        && Boolean(binding.identity.contentManifest.record.href.trim()), 'immutable content requires SHA-256 manifest');
    } else {
      check(Boolean(binding.identity.reason.trim()), 'external unpinned identity requires a reason');
    }
    if (binding.origin.kind === 'derived-transition') {
      check(Boolean(binding.origin.sourceFamily.trim()), 'derived product requires coherent family identity');
      check(policies.has(binding.origin.compositionPolicy), 'derived product requires a composition policy');
      const policy = policies.get(binding.origin.compositionPolicy);
      if (policy) {
        check(policy.products.length > 0 && policy.products.every(ref =>
          binding.product.lineage.contributors.some(contributor => refKey(contributor) === refKey(ref))),
        'composition contributors must match exact product lineage revisions');
        check(binding.product.lineage.contributorList !== 'complete'
          || policy.products.length === binding.product.lineage.contributors.length,
        'complete composition lineage cannot omit contributors');
        if (binding.product.vertical.kind === 'heterogeneous') {
          check(policy.heightPolicy.kind === 'preserve-native-heterogeneous'
            && policy.heightPolicy.permittedUse === 'visual-representation-only',
          'heterogeneous heights need explicit visual composition permission');
        }
      }
    } else if (binding.origin.kind === 'source-derived') {
      check(Boolean(binding.origin.sourceFamily.trim()), 'source-derived product requires family identity');
    } else check(Boolean(binding.origin.reason.trim()), 'unresolved origin requires a reason');
    evidence(binding.validation);
  }
  const levelMap = new Map<string, { family: TerrainFamily; level: TerrainHierarchyLevel }>(families.flatMap(family => family.levels.map(level =>
    [levelKey({ family: family.id, level: level.id }), { family, level }] as const)));
  for (const family of families) {
    check(Boolean(family.id.trim() && family.sourceFamily.trim() && family.levelScheme.trim()), 'family requires identity and level scheme');
    check(new Set(family.levels.map(level => level.id)).size === family.levels.length, 'duplicate level identity');
    check(new Set(family.levels.map(level => level.order)).size === family.levels.length, 'duplicate level order');
    for (const level of family.levels) {
      check(Boolean(level.id.trim()) && Number.isFinite(level.order), 'level requires identity and finite order');
      const binding = products.get(refKey(level.representation.product));
      check(Boolean(binding), 'representation must reference an exact registered product revision');
      if (binding && binding.origin.kind !== 'unresolved') check(binding.origin.sourceFamily === family.sourceFamily,
        'level cannot silently change source family');
      check(level.support.state !== 'partial' || Boolean(level.support.partition?.href), 'partial support requires a partition map');
      check(!['complete', 'partial'].includes(level.support.state) || level.support.validSupport.status === 'known',
        'usable level support requires an assessed footprint');
      if (level.parent) {
        const parent = levelMap.get(levelKey(level.parent));
        check(Boolean(parent), 'parent level must be declared, including cross-family handoffs');
        if (parent?.family.sourceFamily === family.sourceFamily) {
          check(parent.family.levelScheme !== family.levelScheme || parent.level.order < level.order,
            'within-family parent must be coarser (cycles prohibited)');
          check(level.parentOperation.status === 'known', 'within-family parent requires a declared derivation operation');
        }
      }
    }
  }
  for (const [key] of levelMap) {
    const seen = new Set<string>();
    let cursor: string | undefined = key;
    while (cursor) {
      if (seen.has(cursor)) { errors.push('parent graph must be acyclic, including source-family handoffs'); break; }
      seen.add(cursor);
      const parent: TerrainLevelReference | undefined = levelMap.get(cursor)?.level.parent;
      cursor = parent ? levelKey(parent) : undefined;
    }
  }
  check(hierarchy.common.role === 'common' && hierarchy.regional.every(family => family.role === 'regional')
    && hierarchy.transitions.every(family => family.role === 'transition'), 'hierarchy family roles must match their slots');
  check(new Set(hierarchy.selection.regionalOrder).size === hierarchy.regional.length
    && hierarchy.selection.regionalOrder.length === hierarchy.regional.length
    && hierarchy.selection.regionalOrder.every(id => hierarchy.regional.some(family => family.id === id)),
    'regional selection order must contain each regional family exactly once');
  check(Boolean(hierarchy.selection.eligibility.href.trim()
    && hierarchy.selection.sourceFamilyHandoff.policy.href.trim()), 'selection and handoff require explicit policy records');
  for (const policy of hierarchy.compositionPolicies) {
    check(Boolean(policy.id.trim() && policy.heightPolicy.rationale.trim()), 'composition needs identity and height rationale');
    check(policy.products.every(ref => products.has(refKey(ref))), 'composition requires exact registered input product revisions');
    check(policy.operations.length > 0 && policy.operations.every(operation => operation.method.trim()),
      'composition requires declared operations');
    check(new Set(policy.products.map(refKey)).size === policy.products.length, 'duplicate composition contributor');
    check(!policy.contribution.spatiallyVarying || (policy.contribution.mapping === 'spatial-map'
      && Boolean(policy.contribution.map?.href)), 'spatially varying composition requires a contribution map');
    check(Boolean(policy.contribution.reconstruction.href.trim() && policy.contribution.interpretation.trim()),
      'contribution requires reconstruction and weight interpretation');
    evidence(policy.validation);
  }
  return errors;
}

/** Compare frozen declarations across revisions. A recipe alone does not pin a growing inventory. */
export function validateTerrainIdentityReuse(previous: TerrainHierarchy, next: TerrainHierarchy): string[] {
  const errors: string[] = [];
  for (const old of previous.products) {
    if (old.identity.kind !== 'immutable-prepared') continue;
    const revision = old.identity.revision;
    const current = next.products.find(binding => binding.product.id === old.product.id
      && binding.product.revision.status === 'known' && binding.product.revision.value === revision);
    if (current && canonical([current.product, current.identity, current.origin])
      !== canonical([old.product, old.identity, old.origin])) {
      errors.push(`${old.product.id}: immutable revision reused for changed declaration/content; create a new revision`);
    }
  }
  return errors;
}
