import type { EntityReference } from '../../../src/atlas/terrain/metadata/terrainMetadata';
import { validateTerrainSpatialArea } from '../../../src/atlas/terrain/metadata/terrainMetadataValidation';
import type { ClaimContext, ClaimSupport, DefinitionRef, FeatureRef, SemanticClaim,
  SemanticEvidenceBundle, SemanticValue, TimeExtent } from './contract';

export const definitionKey = (ref: DefinitionRef): string => JSON.stringify([ref.id, ref.revision]);
export const resourceKey = (ref: EntityReference): string => JSON.stringify([
  ref.kind, ref.id, ref.revision.status === 'known' ? ref.revision.value : null,
]);
export function resolveContext(shared: ClaimContext, claim: SemanticClaim): ClaimContext {
  return { ...shared, ...claim.context };
}
/** Focused validation of OWNED typed declarations. Not an untrusted JSON parser,
 * GIS topology validator, rights clearance, ontology reasoner or truth adjudicator. */
export function validateSemanticEvidence(bundle: SemanticEvidenceBundle): string[] {
  const errors: string[] = [];
  const require = (ok: boolean, message: string) => { if (!ok) errors.push(message); };
  const nonempty = (value: string, path: string) => require(typeof value === 'string' && !!value.trim(), `${path}: required text`);
  const identity = (ref: DefinitionRef, path: string) => { nonempty(ref.id, path); nonempty(ref.revision, `${path} revision`); };
  require(bundle.contract === 'atlas-semantic-evidence/v1', 'unsupported contract');
  const resources = new Map(bundle.resources.map(r => [resourceKey(r.ref), r]));
  const definitions = new Map(bundle.definitions.map(d => [definitionKey(d), d]));
  const mappings = new Map(bundle.mappings.map(m => [definitionKey(m), m]));
  const claims = new Map(bundle.collections.flatMap(c => c.claims.map(q => [definitionKey(q), q] as const)));
  require(resources.size === bundle.resources.length, 'duplicate resource identity/revision');
  require(definitions.size === bundle.definitions.length, 'duplicate definition identity/revision');
  require(mappings.size === bundle.mappings.length, 'duplicate mapping identity/revision');
  require(claims.size === bundle.collections.reduce((n, c) => n + c.claims.length, 0), 'duplicate claim identity/revision');
  require(new Set(bundle.collections.map(definitionKey)).size === bundle.collections.length, 'duplicate collection identity/revision');
  function resource(ref: EntityReference, path: string): void {
    nonempty(ref.id, path);
    require(resources.has(resourceKey(ref)), `${path}: unresolved resource revision`);
  }
  function definition(ref: DefinitionRef, path: string, kind?: string): void {
    identity(ref, path);
    const d = definitions.get(definitionKey(ref));
    require(!!d, `${path}: unresolved definition revision`);
    if (d && kind) require(d.kind === kind, `${path}: definition kind must be ${kind}`);
  }
  function feature(ref: FeatureRef, path: string): void { nonempty(ref.id, path); resource(ref.namespace, path); }
  function support(s: ClaimSupport, path: string): void {
    nonempty(s.meaning, `${path} meaning`);
    const g = s.geometry;
    if (g.kind === 'native-point' || g.kind === 'native-line') {
      nonempty(g.crs.name, `${path} CRS`);
      const points = g.kind === 'native-point' ? [g.coordinates] : g.coordinates;
      require(points.length >= (g.kind === 'native-line' ? 2 : 1), `${path}: insufficient positions`);
      require(points.every(p => p.length === 2 && p.every(Number.isFinite)), `${path}: invalid coordinates`);
    } else errors.push(...validateTerrainSpatialArea(g).map(e => `${path}: ${e}`));
  }
  function time(t: TimeExtent, path: string): void {
    if (t.kind === 'unknown') { nonempty(t.reason, `${path} unknown reason`); return; }
    nonempty(t.basis, `${path} basis`);
    const precision = t.precision;
    function date(value: string): boolean {
      const patterns = { year: /^\d{4}$/, month: /^\d{4}-\d{2}$/,
        day: /^\d{4}-\d{2}-\d{2}$/,
        second: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/ };
      if (!patterns[precision].test(value)) return false;
      const [y, m, d] = value.slice(0, 10).split('-').map(Number);
      if (!y || (m !== undefined && (m < 1 || m > 12))) return false;
      if (d !== undefined && (d < 1 || d > new Date(Date.UTC(y, m, 0)).getUTCDate())) return false;
      return precision !== 'second' || Number.isFinite(Date.parse(value));
    }
    if (t.kind === 'interval') {
      require(date(t.start) && date(t.end), `${path}: invalid interval precision/calendar`);
      const ordered = t.precision === 'second' ? Date.parse(t.start) <= Date.parse(t.end) : t.start <= t.end;
      require(ordered, `${path}: reversed interval`);
    } else require(date(t.value), `${path}: invalid time precision/calendar`);
  }
  function unitRatio(value: number, path: string): void {
    require(Number.isFinite(value) && value >= 0 && value <= 1, `${path}: proportion outside [0,1]`);
  }
  function value(v: SemanticValue, path: string): void {
    if (v.kind === 'category') definition(v.term, path, 'value');
    if (v.kind === 'descriptor') nonempty(v.text, path);
    if (v.kind === 'quantity') { require(Number.isFinite(v.value), `${path}: nonfinite quantity`); nonempty(v.unit, path); }
    if (v.kind === 'fraction') { unitRatio(v.value, path); nonempty(v.denominator, path); support(v.support, path); }
    if (v.kind === 'probability') { unitRatio(v.value, path); nonempty(v.event, path); nonempty(v.basis, path); }
    if (v.kind === 'occurrence') { unitRatio(v.value, path); nonempty(v.denominator, path); time(v.period, path); }
    if (v.kind === 'detection') nonempty(v.target, path);
    if (v.kind === 'membership') feature(v.feature, path);
    if (v.kind === 'composition') {
      nonempty(v.denominator, path); support(v.support, path);
      require(v.components.length > 0, `${path}: empty composition`);
      for (const c of v.components) {
        unitRatio(c.fraction, path);
        if (c.term.status === 'known') definition(c.term.value, path, 'value');
      }
      require(v.components.reduce((n, c) => n + c.fraction, 0) <= 1.000001, `${path}: composition exceeds its declared denominator`);
      // No global sum-to-one rule for overlapping layers or independent property fractions.
    }
  }
  function context(c: ClaimContext, path: string): void {
    support(c.support, path);
    require(c.time.length > 0, `${path}: time must be declared (unknown is valid)`);
    for (const t of c.time) time(t.extent, path);
    const e = c.evidence;
    require(e.modes.length > 0 && new Set(e.modes).size === e.modes.length, `${path}: evidence modes empty or duplicated`);
    nonempty(e.description, path); nonempty(e.limitations, path);
    for (const input of e.inputs) {
      nonempty(input.role, path);
      if (input.kind === 'resource') resource(input.ref, path);
      else require(claims.has(definitionKey(input.ref)), `${path}: unresolved input claim revision`);
    }
    if (e.modes.includes('derived')) {
      require(e.inputs.length > 0 && e.processing.length > 0, `${path}: derived claim requires inputs and processing lineage`);
    }
    for (const step of e.processing) {
      nonempty(step.method, `${path} processing method`);
      require(!!step.revision, `${path}: processing revision knowledge required`);
    }
    if (e.modes.includes('scenario')) require(!!c.conditions?.length, `${path}: scenario requires reference condition`);
    for (const condition of c.conditions ?? []) {
      definition(condition.definition, path, 'condition'); nonempty(condition.qualification, path);
    }
    for (const q of c.quality ?? []) {
      nonempty(q.scope.description, `${path} quality scope`); nonempty(q.metric, path); nonempty(q.meaning, path);
      if (q.kind === 'confidence') require(q.scope.kind === 'claim' || q.scope.kind === 'spatial', `${path}: confidence cannot borrow product/class validation scope`);
      if (q.value?.kind === 'numeric') {
        require(Number.isFinite(q.value.value), `${path}: nonfinite quality`); nonempty(q.value.unit, path);
        if (q.value.unit === 'proportion') unitRatio(q.value.value, path);
        if (q.value.unit === 'percent') require(q.value.value >= 0 && q.value.value <= 100, `${path}: invalid quality percentage`);
      }
      if (q.value?.kind === 'label') nonempty(q.value.label, path);
    }
  }
  for (const r of bundle.resources) {
    nonempty(r.ref.id, 'resource'); nonempty(r.name, 'resource');
    for (const input of r.inputs) resource(input, r.ref.id);
    if (r.ref.kind === 'product') require(r.inputs.length > 0, `${r.ref.id}: product requires source/input reference`);
    if (r.coverage?.status === 'known') errors.push(...validateTerrainSpatialArea(r.coverage.value));
    for (const t of r.dates ?? []) time(t.extent, r.ref.id);
  }
  for (const d of bundle.definitions) {
    identity(d, 'definition'); nonempty(d.vocabulary.id, d.id); nonempty(d.meaning, d.id); nonempty(d.label, d.id);
    for (const condition of d.requiredConditions ?? []) definition(condition, d.id, 'condition');
    if (d.kind === 'property') require(!!d.valueKinds?.length, `${d.id}: property needs allowed value kinds`);
  }
  for (const m of bundle.mappings) {
    identity(m, 'mapping'); definition(m.from, m.id); definition(m.target, m.id);
    nonempty(m.method.method, m.id); nonempty(m.qualification, m.id);
    for (const loss of m.loss) nonempty(loss, `${m.id} loss`);
  }
  for (const c of bundle.collections) {
    identity(c, 'collection'); resource(c.product, c.id);
    require(c.product.kind === 'product', `${c.id}: collection must reference a product`);
    context(c.context, c.id);
    for (const q of c.claims) {
      identity(q, 'claim'); definition(q.native.property, q.id, 'property');
      if (q.native.term) definition(q.native.term, q.id, 'value');
      const effective = resolveContext(c.context, q); context(effective, q.id);
      const property = definitions.get(definitionKey(q.native.property));
      if (q.result.kind === 'assertion') {
        for (const mode of property?.requiredModes ?? []) require(effective.evidence.modes.includes(mode), `${q.id}: native property requires evidence mode ${mode}`);
        for (const condition of property?.requiredConditions ?? []) require(!!effective.conditions?.some(c => definitionKey(c.definition) === definitionKey(condition)), `${q.id}: native property requires reference condition`);
      }
      if (q.feature) feature(q.feature, q.id);
      for (const f of q.associations ?? []) feature(f, q.id);
      if (q.result.kind === 'assertion') {
        value(q.result.value, q.id);
        const p = definitions.get(definitionKey(q.native.property));
        if (p) require(!!p.valueKinds?.includes(q.result.value.kind), `${q.id}: value kind violates property definition`);
        if (q.result.value.kind === 'detection') require(effective.evidence.modes.some(m => ['observation', 'detection', 'classification'].includes(m)), `${q.id}: detection requires observation-based evidence mode`);
        if (q.native.term && q.result.value.kind === 'category') require(definitionKey(q.native.term) === definitionKey(q.result.value.term), `${q.id}: native category overwritten`);
      } else nonempty(q.result.explanation, `${q.id} gap explanation`);
      if (q.interpretation) {
        const m = mappings.get(definitionKey(q.interpretation.mapping));
        require(!!m, `${q.id}: unresolved mapping revision`);
        if (m) {
          require([definitionKey(q.native.property), ...(q.native.term ? [definitionKey(q.native.term)] : [])].includes(definitionKey(m.from)), `${q.id}: mapping does not concern native meaning`);
          const disposition = m.relationship === 'ambiguous' ? 'unresolved'
            : ['incompatible', 'unmappable'].includes(m.relationship) ? 'rejected' : 'qualified';
          require(q.interpretation.disposition === disposition, `${q.id}: mapping disposition misrepresents relationship`);
          require(q.result.kind === 'assertion' || disposition !== 'qualified', `${q.id}: evidence gap cannot assert a common interpretation`);
        }
      }
    }
    if (c.binding) {
      nonempty(c.binding.assignment, `${c.id} binding`);
      require(new Set(c.binding.codes.map(b => JSON.stringify(b.code))).size === c.binding.codes.length, `${c.id}: duplicate native code binding`);
      for (const b of c.binding.codes) require(c.claims.some(q => definitionKey(q) === definitionKey(b.claim)), `${c.id}: binding must reference local claim revision`);
    }
  }
  function visit(v: unknown, path: string): void {
    if (!v || typeof v !== 'object') return;
    const o = v as Record<string, unknown>;
    if (o.status === 'unknown' || o.kind === 'unknown') require(typeof o.reason === 'string' && !!o.reason.trim(), `${path}: unknown requires reason`);
    if (o.status === 'known' && typeof o.value === 'string') nonempty(o.value, path);
    if ('href' in o) require(typeof o.href === 'string' && !!o.href.trim(), `${path}: asset requires href`);
    if ('sha256' in o) require(typeof o.sha256 === 'string' && /^[a-f0-9]{64}$/.test(o.sha256), `${path}: invalid SHA256`);
    for (const [key, child] of Object.entries(o)) visit(child, `${path}.${key}`);
  }
  visit(bundle, 'bundle');
  return [...new Set(errors)];
}
