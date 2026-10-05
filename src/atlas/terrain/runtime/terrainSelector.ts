import type { EntityReference, Knowledge } from '../metadata/terrainMetadata';
import type { TerrainFamily, TerrainHierarchyLevel, TerrainLevelReference, TerrainSelectionContext } from '../metadata/terrainHierarchy';
import { classifyTerrainRefinement } from '../metadata/terrainHierarchy';
import type { TerrainRegistry } from './terrainRegistry';
import { terrainReferenceKey } from './terrainRegistry';
import { containsTerrainQuery } from './terrainSpatialEligibility';
import { validateTerrainSpatialArea } from '../metadata/terrainMetadataValidation';

export interface TerrainSelectionRequest extends TerrainSelectionContext {
  /** Explicit opt-in only; transitions are never automatically ranked above regional terrain. */
  family?: string;
  /** Caller-provided previous identity; no hidden navigation state in the selector. */
  previous?: TerrainLevelReference;
}
export interface TerrainSelectionTrace { family: string; level?: string; outcome: string }
export type TerrainSelection = {
  status: 'selected'; hierarchy: { id: string; revision: string };
  family: string; sourceFamily: string; role: TerrainFamily['role']; product: EntityReference;
  representation: { family: string; level: string; kind: TerrainHierarchyLevel['representation']['kind'] };
  level: string; requestedLevel: string; derivation: TerrainHierarchyLevel['derivation'];
  informationCeiling: Knowledge<string>; sampleSpacing: Knowledge<string>; overzoom: boolean;
  support: 'complete' | 'legacy-unassessed';
  reason: 'direct' | 'regional-parent' | 'same-family-parent' | 'common-fallback' | 'overzoom';
  refinement: 'direct' | 'within-family-lod' | 'source-family-handoff';
  handoffState: 'unresolved' | 'declared';
  compositionPolicy?: string;
  trace: readonly TerrainSelectionTrace[];
} | { status: 'unavailable'; hierarchy: { id: string; revision: string }; reason: string; trace: readonly TerrainSelectionTrace[] };

export function selectTerrain(registry: TerrainRegistry, request: TerrainSelectionRequest): TerrainSelection {
  const hierarchy = registry.hierarchy, identity = { id: hierarchy.id, revision: hierarchy.revision };
  const trace: TerrainSelectionTrace[] = [];
  const unavailable = (reason: string): TerrainSelection => ({ status: 'unavailable', hierarchy: identity, reason, trace });
  const order = registry.levelOrder(request.scale.scheme, request.scale.requestedLevel);
  if (order === undefined) return unavailable('undeclared-requested-level');
  if ((!request.location && !request.footprint) || request.location?.coordinates.some(n => !Number.isFinite(n))
    || (request.footprint && validateTerrainSpatialArea(request.footprint).length)) return unavailable('invalid-spatial-query');
  if (request.previous && !registry.family(request.previous.family)?.levels.some(l => l.id === request.previous!.level)) return unavailable('undeclared-previous-selection');
  if (request.family && !registry.family(request.family)) return unavailable('undeclared-requested-family');

  const eligibility = (family: TerrainFamily, level: TerrainHierarchyLevel): 'complete' | 'legacy-unassessed' | undefined => {
    const binding = registry.product(level.representation.product), product = binding.product;
    const reject = (outcome: string) => { trace.push({ family: family.id, level: level.id, outcome }); return undefined; };
    if (request.provenanceRequirement === 'spatial-contributors' && product.lineage.spatialMapping !== 'uniform' && product.lineage.spatialMapping !== 'mask') return reject('spatial-contributors-unavailable');
    if (level.support.state === 'absent') return reject('absent-support');
    if (level.support.state === 'partial') return reject('partial-support-partition-not-evaluated');
    if (level.support.state === 'unknown' || level.support.validSupport.status === 'unknown' || product.spatial.validSupport.status === 'unknown') {
      const legacy = registry.options.legacyCommon;
      if (family.role === 'common' && legacy && terrainReferenceKey(legacy.product) === terrainReferenceKey(level.representation.product)
        && containsTerrainQuery(legacy.addressingExtent, request) === 'inside') {
        trace.push({ family: family.id, level: level.id, outcome: 'legacy-external-common-policy; valid-support-remains-unknown' });
        return 'legacy-unassessed';
      }
      return reject('unknown-valid-support');
    }
    for (const area of [product.spatial.validSupport.value.area, level.support.validSupport.value.area]) {
      const state = containsTerrainQuery(registry.area(area), request);
      if (state !== 'inside') return reject(`${state}-valid-support`);
    }
    trace.push({ family: family.id, level: level.id, outcome: 'eligible-complete-support' });
    return 'complete';
  };

  let attempted: TerrainFamily | undefined;
  const tryFamily = (family: TerrainFamily, fallback: boolean): TerrainSelection | undefined => {
    if (family.levelScheme !== request.scale.scheme) { trace.push({ family: family.id, outcome: 'incompatible-level-scheme' }); return; }
    if (family.role === 'transition' && !registry.options.enabledTransitions?.includes(family.id)) { trace.push({ family: family.id, outcome: 'transition-not-enabled' }); return; }
    const exact = family.levels.find(l => l.id === request.scale.requestedLevel);
    const finest = [...family.levels].sort((a, b) => b.order - a.order)[0];
    const overzoom = !exact && finest && order > finest.order && family.overzoom.allowed;
    if (!exact && finest && order > finest.order && !family.overzoom.allowed) {
      trace.push({ family: family.id, outcome: 'overzoom-not-permitted' }); return;
    }
    let level = exact ?? (overzoom ? finest : undefined);
    let selectedFamily = family;
    // An omitted request level can use the finest declared coarser entry, then its explicit parent chain.
    if (!level && hierarchy.selection.missingFineLevel === 'same-family-parent-then-common') level = [...family.levels].filter(l => l.order < order).sort((a, b) => b.order - a.order)[0];
    while (level) {
      const support = eligibility(selectedFamily, level);
      if (support) {
        const binding = registry.product(level.representation.product);
        const parentFallback = level.id !== request.scale.requestedLevel && !overzoom;
        const from = request.previous ? registry.family(request.previous.family) : fallback ? attempted : parentFallback ? family : undefined;
        const unchanged = request.previous?.family === selectedFamily.id && request.previous.level === level.id;
        return { status: 'selected', hierarchy: identity, family: selectedFamily.id, sourceFamily: selectedFamily.sourceFamily, role: selectedFamily.role,
          product: level.representation.product, representation: { family: selectedFamily.id, level: level.id, kind: level.representation.kind },
          level: level.id, requestedLevel: request.scale.requestedLevel, derivation: level.derivation,
          informationCeiling: selectedFamily.informationCeiling, sampleSpacing: level.sampleSpacing, overzoom: Boolean(overzoom) || level.derivation === 'overzoom', support,
          reason: fallback ? 'common-fallback' : overzoom || level.derivation === 'overzoom' ? 'overzoom' : parentFallback ? selectedFamily.role === 'regional' ? 'regional-parent' : 'same-family-parent' : 'direct',
          refinement: from && !unchanged ? classifyTerrainRefinement(from, selectedFamily) : 'direct',
          handoffState: hierarchy.selection.sourceFamilyHandoff.state,
          ...(binding.origin.kind === 'derived-transition' ? { compositionPolicy: binding.origin.compositionPolicy } : {}), trace };
      }
      if (hierarchy.selection.missingFineLevel !== 'same-family-parent-then-common' || !level.parent) break;
      const parentFamily = registry.family(level.parent.family)!;
      // Cross-family parents are handoffs, not ordinary regional fallback. Resolve common explicitly below.
      if (parentFamily.sourceFamily !== family.sourceFamily || parentFamily.levelScheme !== family.levelScheme) break;
      const parentId = level.parent.level;
      selectedFamily = parentFamily;
      level = parentFamily.levels.find(l => l.id === parentId);
    }
    if (!exact) trace.push({ family: family.id, outcome: 'requested-level-unavailable' });
    return;
  };
  const candidates = request.family ? [registry.family(request.family)!] : hierarchy.selection.regionalOrder.map(id => registry.family(id)!);
  let commonFallbackPermitted = true;
  for (const family of candidates) {
    const result = tryFamily(family, false);
    if (result) return result;
    attempted = family;
    const policy = family.role === 'transition' ? hierarchy.selection.unavailableTransition : hierarchy.selection.unsupportedRegional;
    const withinProductSupport = family.levels.some(l => {
      const support = registry.product(l.representation.product).product.spatial.validSupport;
      return support.status === 'known' && containsTerrainQuery(registry.area(support.value.area), request) === 'inside';
    });
    if (policy === 'unavailable' || (withinProductSupport && hierarchy.selection.missingFineLevel === 'unavailable')) commonFallbackPermitted = false;
  }
  if (request.family === hierarchy.common.id) return unavailable('common-unavailable');
  if (!commonFallbackPermitted) return unavailable('declared-fallback-unavailable');
  return tryFamily(hierarchy.common, Boolean(attempted)) ?? unavailable('common-unavailable');
}
