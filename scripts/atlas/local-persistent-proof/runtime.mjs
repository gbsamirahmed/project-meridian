// Research-only composition: reuse existing selector, v1 and scientific/lifecycle functions.
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve, relative, isAbsolute } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createServer } from 'vite';
import { StoreError, sha } from './store.mjs';
export const SCHEMA = 'tryfan-local-persistent-world/v1';
const INPUT = 'docs/research/tryfan-qualified-query-inputs.json';
const RESULT = 'docs/research/tryfan-qualified-query-results.json';
const PLAN = 'docs/research/tryfan-qualified-query-plan.json';
const read = p => JSON.parse(readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
export async function runtime(data) {
  const server = await createServer({ configFile: false, appType: 'custom', logLevel: 'silent', server: { middlewareMode: true, hmr: false } });
  try {
    const proof = await server.ssrLoadModule('/scripts/atlas/qualified-query-proof/proof.ts');
    const semantic = await server.ssrLoadModule('/scripts/atlas/semantic-evidence/validate.ts');
    const { registerTerrainHierarchy } = await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainRegistry.ts');
    const { selectTerrain } = await server.ssrLoadModule('/src/atlas/terrain/runtime/terrainSelector.ts');
    const { createTryfanTerrainProof } = await server.ssrLoadModule('/src/atlas/terrain/metadata/tryfanTerrainProof.ts');
    const input = read(INPUT), previous = read(RESULT), plan = read(PLAN);
    const frozen = read('docs/atlas/semantic-evidence-contract-validation.json').code;
    const basis = { inputs: { href: INPUT, sha256: sha(readFileSync(INPUT)) }, result: { href: RESULT, sha256: sha(readFileSync(RESULT)) }, plan: { href: PLAN, sha256: sha(readFileSync(PLAN)) }, methodRevision: previous.methodRevision, methodFiles: previous.methodFiles, implementationFiles: Object.fromEntries(['store.mjs', 'runtime.mjs', 'cli.mjs'].map(f => ['scripts/atlas/local-persistent-proof/' + f, sha(readFileSync('scripts/atlas/local-persistent-proof/' + f))])), semanticFiles: Object.fromEntries(frozen.map(c => [c.href, c.sha256])) };
    const equal = (a, b) => proof.canonical(a) === proof.canonical(b);
    function verifyBasis(actual) {
      if (!equal(actual, basis)) throw new StoreError('basis-mismatch', 'Pinned evidence or method/contract context differs; no silent reinterpretation');
      for (const [p, h] of Object.entries({ ...basis.methodFiles, ...basis.semanticFiles, ...basis.implementationFiles })) if (sha(readFileSync(p)) !== h) throw new StoreError('method-unavailable', 'Pinned method/contract changed: ' + p);
    }
    function metadata(root) { const rest = structuredClone(root); delete rest.heightSamplesM; return rest; }
    function registry(stage) {
      const r = createTryfanTerrainProof();
      if (stage === 'regional') return { hierarchy: r.hierarchy, options: r.options };
      const hierarchy = structuredClone(r.hierarchy);
      hierarchy.id = 'tryfan-proof-common-context'; hierarchy.revision = '1'; hierarchy.regional = []; hierarchy.selection.regionalOrder = [];
      return { hierarchy, options: r.options };
    }
    function hydrate(state) {
      return state.derivations.map(r => {
        const c = state.evidence.collections.find(c => c.claims?.some(q => q.id === r.claim.id && q.revision === r.claim.revision));
        if (!c) throw new StoreError('missing-claim', 'Dependency record has no exact qualified claim');
        const claim = c.claims.find(q => q.id === r.claim.id && q.revision === r.claim.revision);
        return { ...r, claim, context: semantic.resolveContext(c.context, claim) };
      });
    }
    function binding(results) { return results.map(r => ({ question: r.question, probe: r.probe, property: r.property, claim: { id: r.claim.id, revision: r.claim.revision }, receipt: r.receipt })); }
    function validate(state) {
      if (state.schema !== SCHEMA) throw new StoreError('unsupported-schema', 'Unknown local proof schema; no automatic migration');
      verifyBasis(state.basis);
      if (!['common', 'regional'].includes(state.stage) || !equal(state.probes, input.geometry.probes)) throw new StoreError('invalid-context', 'Unknown evidence stage or changed frozen queries');
      registerTerrainHierarchy(state.catalogue.hierarchy, state.catalogue.options);
      if (!equal(state.catalogue, registry(state.stage))) throw new StoreError('invalid-catalogue', 'Declaration differs from registered retained proof');
      const wanted = input.roots.filter(r => state.stage === 'regional' || r.family === 'production-common').map(metadata);
      if (!equal(state.roots, wanted)) throw new StoreError('invalid-roots', 'Exact root revision/support metadata missing or changed');
      const issues = semantic.validateSemanticEvidence(state.evidence);
      const results = hydrate(state);
      issues.push(...proof.validateSlice(results, state.roots));
      if (new Set(results.map(r => r.claim.id + ':' + r.claim.revision)).size !== results.length) issues.push('Duplicate claim revision');
      if (results.length !== (state.stage === 'common' ? 4 : 6)) issues.push('Incomplete accepted proof snapshot');
      for (const r of results) {
        const revision = r.claim.revision, body = structuredClone(r.claim); delete body.id; delete body.revision;
        if (proof.hash({ body, context: r.context }) !== revision || proof.hash(r.claim.result.value.value) !== r.receipt.artifact.sha256) issues.push('Claim content/artifact digest mismatch');
      }
      if (issues.length) throw new StoreError('invalid-evidence', issues.join('; '));
      return results;
    }
    function selections(state) {
      const r = registerTerrainHierarchy(state.catalogue.hierarchy, state.catalogue.options);
      return Object.fromEntries(state.probes.map(p => [p.id, selectTerrain(r, { footprint: p.eligibilityFootprint, scale: plan.selection })]));
    }
    function availableRoots(state) {
      return state.roots.filter(r => r.assets.every(a => {
        const path = resolve(data, a.href.replace('meridian-data://', ''));
        const rel = relative(resolve(data), path);
        if (rel.startsWith('..') || isAbsolute(rel)) throw new StoreError('invalid-asset-path', 'Asset is outside declared retained data');
        return existsSync(path) && sha(readFileSync(path)) === a.sha256;
      }));
    }
    function assess(state, changes = []) {
      const results = validate(state), selected = selections(state), roots = availableRoots(state);
      return results.map(r => ({ probe: r.probe, property: r.property, ref: { id: r.claim.id, revision: r.claim.revision }, current: proof.assess(r, results, roots, selected[r.probe], 'current-applicable-terrain-v1', changes, state.basis.methodRevision), replay: proof.assess(r, results, roots, selected[r.probe], 'fixed-input-replay-v1') }));
    }
    function query(state, probe, property, historicalRevision) {
      const results = validate(state), assessments = assess(state);
      const gapCollection = state.evidence.collections.find(c => c.claims?.some(q => q.result.kind === 'gap' && q.native.property.id === property));
      if (gapCollection) {
        const claim = gapCollection.claims.find(q => q.native.property.id === property), context = semantic.resolveContext(gapCollection.context, claim);
        const point = state.probes.find(p => p.id === probe);
        if (point && equal(context.support.geometry.coordinates, point.centre)) return { status: 'unknown', claim, context };
      }
      const candidates = results.filter(r => r.probe === probe && r.property === property);
      const current = candidates.filter(r => assessments.find(a => a.ref.id === r.claim.id && a.ref.revision === r.claim.revision).current.status === 'fresh');
      const result = historicalRevision ? candidates.find(r => r.claim.revision === historicalRevision) : current.length === 1 ? current[0] : undefined;
      if (!result) return { status: 'unavailable', reason: historicalRevision ? 'Exact historical revision unavailable' : candidates.length ? 'No unique fresh result under this policy' : 'Requested result unavailable', candidates: assessments.filter(a => a.probe === probe && a.property === property) };
      const a = assessments.find(a => a.ref.id === result.claim.id && a.ref.revision === result.claim.revision);
      return { status: historicalRevision ? 'historical' : 'current', result, freshness: historicalRevision ? a.replay : a.current, currentlyPreferred: current.some(r => r.claim.revision === result.claim.revision), currentAssessment: a.current };
    }
    function sample(requests) {
      const p = spawnSync(join(data, 'earth-lab/.venv/Scripts/python.exe'), ['-X', 'utf8', 'scripts/atlas/qualified-query-proof/retained_inputs.py', '--data', data], { input: JSON.stringify(requests), encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
      if (p.status !== 0) throw new StoreError('input-unavailable', p.stderr || p.error?.message || 'Retained pixel adapter failed');
      const sampled = JSON.parse(p.stdout);
      if (!equal(sampled.software, input.software)) throw new StoreError('software-drift', 'Pinned sampler software differs; no silent replay against a changed scientific environment');
      for (const r of sampled.roots) if (!equal(r, input.roots.find(x => x.id === r.id))) throw new StoreError('input-drift', 'Fresh retained sampling differs from pinned root');
      return sampled;
    }
    function initial() {
      verifyBasis(basis);
      const common = registry('common');
      const state = { schema: SCHEMA, basis, probes: input.geometry.probes, catalogue: common, stage: 'common', roots: input.roots.filter(r => r.family === 'production-common').map(metadata), evidence: null, derivations: [], publication: { parent: null, reason: 'retained-common-initialization' } };
      const selected = selections(state);
      const sampled = sample(state.probes.map(p => ({ probe: p.id, family: selected[p.id].family, level: selected[p.id].level })));
      const results = state.probes.flatMap(p => proof.derive(p, sampled.roots.find(r => r.probe === p.id), basis.methodRevision));
      state.evidence = proof.bundle(results, sampled.roots, state.probes[0]); state.derivations = binding(results); validate(state);
      return state;
    }
    function prepareUpdate(old, parent) {
      const oldResults = validate(old);
      if (old.stage !== 'common') throw new StoreError('already-refined', 'Use existing accepted regional snapshot; no duplicate update');
      const state = structuredClone(old); state.stage = 'regional'; state.catalogue = registry('regional'); state.roots = input.roots.map(metadata);
      const selected = selections(state), statuses = oldResults.map(r => ({ probe: r.probe, property: r.property, ref: { id: r.claim.id, revision: r.claim.revision }, assessment: proof.assess(r, oldResults, availableRoots(state), selected[r.probe], 'current-applicable-terrain-v1', [], basis.methodRevision) }));
      // Explicit finite two-stage chain. Outcomes depend on selector/input scopes, not named stale IDs.
      const affected = state.probes.filter(p => statuses.some(a => a.probe === p.id && a.assessment.status === 'stale'));
      const sampled = sample(affected.map(p => ({ probe: p.id, family: selected[p.id].family, level: selected[p.id].level })));
      const added = affected.flatMap(p => proof.derive(p, sampled.roots.find(r => r.probe === p.id), basis.methodRevision));
      const results = [...oldResults, ...added]; state.evidence = proof.bundle(results, input.roots, state.probes[0]); state.derivations = binding(results);
      state.publication = { parent, reason: 'retained-regional-applicability-and-scoped-recompute' }; validate(state);
      return { state, statuses, recomputed: added.map(r => ({ probe: r.probe, property: r.property, ref: { id: r.claim.id, revision: r.claim.revision } })), sampleMeasurement: sampled.measurement };
    }
    function replay(state) {
      const results = validate(state).filter(r => r.receipt.inputs[0].kind === 'resource');
      const sampled = sample(results.map(r => { const u = r.receipt.inputs[0], root = state.roots.find(x => 'retained-input:' + x.id === u.id && x.revision === u.revision); return { probe: root.probe, family: root.family, level: root.level }; }));
      const checks = sampled.roots.flatMap(root => proof.derive(state.probes.find(p => p.id === root.probe), root, basis.methodRevision)).map(r => ({ probe: r.probe, property: r.property, ref: { id: r.claim.id, revision: r.claim.revision }, exact: equal(r, validate(state).find(x => x.claim.id === r.claim.id && x.claim.revision === r.claim.revision)) }));
      if (checks.some(c => !c.exact)) throw new StoreError('replay-mismatch', 'Fresh pixel/method replay differs from stored qualified result');
      return { checks, fromRetainedPixels: true, methodRevision: basis.methodRevision, sampleMeasurement: sampled.measurement };
    }
    function inspect(state) {
      const results = validate(state), reverse = {};
      for (const r of results) for (const use of r.receipt.inputs) (reverse[use.kind + ':' + use.id + ':' + use.revision] ??= []).push({ id: r.claim.id, revision: r.claim.revision });
      const answers = state.probes.flatMap(p => ['slope', 'area-ratio'].map(property => ({ probe: p.id, property, answer: query(state, p.id, property) })));
      function origin(result) {
        const use = result.receipt.inputs[0];
        if (use.kind === 'resource') return state.roots.find(x => 'retained-input:' + x.id === use.id && x.revision === use.revision);
        return origin(results.find(x => x.claim.id === use.id && x.claim.revision === use.revision));
      }
      const historical = results.filter(r => origin(r).family === 'production-common').map(r => query(state, r.probe, r.property, r.claim.revision));
      const r = registerTerrainHierarchy(state.catalogue.hierarchy, state.catalogue.options);
      const nativeGap = state.evidence.collections.at(-1).claims[0];
      const gap = query(state, state.probes[0].id, nativeGap.native.property.id).claim;
      const unavailable = selectTerrain(r, { footprint: state.probes[1].eligibilityFootprint, scale: plan.selection, provenanceRequirement: 'spatial-contributors' });
      return { answers, historical, assessments: assess(state), reverse, unknown: gap, unavailable, selections: selections(state), counts: { claims: state.evidence.collections.reduce((n,c) => n + c.claims.length,0), derivations: results.length, roots: state.roots.length, reverseKeys: Object.keys(reverse).length } };
    }
    return { validate, initial, prepareUpdate, query, replay, inspect, assess, close: () => server.close() };
  } catch (e) { await server.close(); throw e; }
}
