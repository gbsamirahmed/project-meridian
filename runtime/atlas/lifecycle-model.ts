import fs from 'node:fs'
import path from 'node:path'
import { encode, sha } from '../../pilots/atlas/tryfan/identity.mjs'
import { METHOD } from '../../pilots/atlas/tryfan/dependencies.mjs'
import { methods } from '../../scripts/atlas/regional-dependencies/model.mjs'
import { object, address } from './authority.ts'
import type { ObjectJson } from './authority.ts'
import type { Json } from './types.ts'
import { requireAtlas } from './errors.ts'

export const digest = (v: unknown): string => sha(encode(v))
const plan = JSON.parse(fs.readFileSync(new URL('./lifecycle-plan.json', import.meta.url), 'utf8'))
export const probes: { id: string; point: number[] }[] = plan.population.probes
export type Notice = { key: string; bounds: number[] | null; text: string }
export interface Policy { schema: string; sources: Record<string, ObjectJson>; parameters: Record<string, number>; notes: Notice[] }
export interface DerivedState { schema: string; active: Record<string, string>; executions: Record<string, string> }
export interface Change { parameters?: Record<string, number>; notice?: Notice; unrelated?: boolean }
export interface TerrainRow { id: string; point: number[]; stride: number; spacing: number; samples: number[][]; uses: ObjectJson[]; oracle: { slope: number; 'area-ratio': number } }
export const key = (id: string, property: string): string => id + '|' + property
export interface ArtifactMetrics { records: number; bytes: number }
export function readArtifact(root: string, id: string, metrics?: ArtifactMetrics, folder = 'artifacts'): ObjectJson {
  address(id); const bytes = fs.readFileSync(path.join(root, folder, id + '.json'))
  if (metrics) { metrics.records++; metrics.bytes += bytes.length }
  requireAtlas(sha(bytes) === id, 'derived-integrity', 'Derived artifact is missing or altered; restore canonical evidence.')
  const v = object(JSON.parse(bytes.toString('utf8')))
  requireAtlas(encode(v) === bytes.toString('utf8'), 'derived-integrity', 'Derived encoding differs.')
  return v
}
export function validatePolicy(policy: Policy): void {
  requireAtlas(policy.schema === 'atlas-runtime-terrain-policy/v1' && Object.keys(policy).sort().join(',') === 'notes,parameters,schema,sources', 'lifecycle-invalid', 'Invalid lifecycle policy.')
  requireAtlas(Object.keys(policy.sources).length === 4 && Object.values(policy.sources).every(s => s.family === 'dtm' && s.region === 'riffelhorn'), 'lifecycle-invalid', 'Four exact native DTM sources required; no fusion.')
  requireAtlas(Object.entries(policy.parameters).every(([id, n]) => probes.some(p => p.id === id) && [1, 2].includes(n)), 'parameter-invalid', 'Only declared native stride1/2 parameters are supported.')
  requireAtlas(Array.isArray(policy.notes) && policy.notes.every(n => Object.keys(n).sort().join(',') === 'bounds,key,text' && typeof n.key === 'string' && Object.hasOwn(policy.sources, n.key) && typeof n.text === 'string' && n.text.length > 0 && n.text.length <= 1000 && (n.bounds === null || Array.isArray(n.bounds) && n.bounds.length === 4 && n.bounds.every(Number.isFinite) && n.bounds[0] < n.bounds[2] && n.bounds[1] < n.bounds[3])), 'qualification-invalid', 'Notices need an exact source identity and bounded or explicitly whole-source administrative support.')
  requireAtlas(new Set(policy.notes.map(digest)).size === policy.notes.length, 'qualification-invalid', 'Duplicate notice identity.')
}
export function revise(policy: Policy, change: Change): Policy {
  requireAtlas(change && typeof change === 'object' && !Array.isArray(change) && (change.parameters === undefined || change.parameters && typeof change.parameters === 'object' && !Array.isArray(change.parameters) && Object.entries(change.parameters).every(([id, stride]) => probes.some(p => p.id === id) && [1, 2].includes(stride))) && (change.notice === undefined || change.notice && typeof change.notice === 'object' && !Array.isArray(change.notice)), 'change-invalid', 'Change must be a structured object with declared probe parameters and/or an exact source notice.')
  requireAtlas(Object.keys(change).every(k => ['parameters', 'notice', 'unrelated'].includes(k)) && (change.unrelated === undefined || typeof change.unrelated === 'boolean'), 'change-invalid', 'Unsupported lifecycle change; no physical observation is fabricated.')
  const next = structuredClone(policy)
  if (change.parameters) Object.assign(next.parameters, change.parameters)
  if (change.notice && !next.notes.some(n => digest(n) === digest(change.notice))) next.notes.push(structuredClone(change.notice))
  next.notes.sort((a, b) => digest(a).localeCompare(digest(b))); validatePolicy(next); return next
}
export function projection(policy: Policy, use: ObjectJson): ObjectJson {
  const source = policy.sources[String(use.key)]; requireAtlas(source, 'dependency-missing', 'Unknown exact source dependency.')
  const notes = policy.notes.filter(n => n.key === use.key && (n.bounds === null || (use.cells as ObjectJson[]).some(c => Number(c.x) - .25 < n.bounds![2] && n.bounds![0] < Number(c.x) + .25 && Number(c.y) - .25 < n.bounds![3] && n.bounds![1] < Number(c.y) + .25)))
  return { sourceIdentity: digest(source), scope: use.scope, notes: notes as unknown as Json }
}
export function affected(root: string, policy: Policy, state?: DerivedState, metrics?: ArtifactMetrics): string[] {
  validatePolicy(policy); const stale: string[] = []
  for (const p of probes) {
    const slopeKey = key(p.id, 'slope'), ratioKey = key(p.id, 'area-ratio'), ref = state?.active[slopeKey]
    let changed = !ref
    if (ref) {
      const a = readArtifact(root, ref, metrics)
      const row = object(a.sampling), uses = row.uses as ObjectJson[]
      changed = a.methodRevision !== METHOD || object(a.parameters).stride !== (policy.parameters[p.id] ?? 1) || encode(a.inputs) !== encode(uses.map(u => ({ kind: 'qualified-input-use', identity: digest({ ...u, qualification: projection(policy, u) }) })))
    }
    if (changed) stale.push(slopeKey, ratioKey)
    else if (!state?.active[ratioKey]) stale.push(ratioKey)
  }
  return stale.sort()
}
function qualificationFor(policy: Policy, uses: ObjectJson[]) {
  return { sources: uses.map(u => policy.sources[String(u.key)]), notes: uses.flatMap(u => projection(policy, u).notes as Json[]), physicalTime: { kind: 'unknown', reason: 'Stencil observation epoch unknown; product edition is not observation.' }, knowledge: 'Administrative qualification revisions are not physical changes.', rights: uses.map(u => policy.sources[String(u.key)].rights), vertical: 'LN02 / EPSG:5728, source documented; no vertical transformation', uncertainty: 'Native represented DTM, not a guarantee of physical accuracy; no source fusion.' }
}
/** Metadata-only qualification revision: never invoke a scientific method or read new cells. */
export function requalifyOutputs(policy: Policy, pairs: { slope: ObjectJson; ratio: ObjectJson }[]): Record<string, ObjectJson> {
  validatePolicy(policy); const made: Record<string, ObjectJson> = {}
  for (const { slope, ratio } of pairs) {
    const sampling = object(slope.sampling), uses = sampling.uses as ObjectJson[]
    requireAtlas(slope.methodRevision === METHOD && ratio.methodRevision === METHOD && object(slope.parameters).stride === (policy.parameters[String(slope.task)] ?? 1), 'requalification-invalid', 'Changed methods/parameters require numerical recomputation, not requalification.')
    const next = { ...slope, qualification: qualificationFor(policy, uses), inputs: uses.map(u => ({ kind: 'qualified-input-use', identity: digest({ ...u, qualification: projection(policy, u) }) })) }
    made[String(slope.id)] = next as unknown as ObjectJson
    made[String(ratio.id)] = { ...ratio, qualification: next.qualification, inputs: [{ kind: 'derived', identity: digest(next) }] } as unknown as ObjectJson
  }
  return made
}
export async function outputs(policy: Policy, rows: TerrainRow[]): Promise<Record<string, ObjectJson>> {
  validatePolicy(policy); const accepted = await methods(), artifacts: Record<string, ObjectJson> = {}
  for (const row of rows) {
    requireAtlas(probes.some(p => p.id === row.id && encode(p.point) === encode(row.point)) && row.stride === (policy.parameters[row.id] ?? 1) && row.spacing === .5 * row.stride, 'processing-invalid', 'Native task/support/parameters differ.')
    const slope = accepted.horn(row.samples, row.spacing), ratio = accepted.ratio(slope)
    requireAtlas(Number.isFinite(slope) && Number.isFinite(ratio) && Math.abs(slope - row.oracle.slope) <= 1e-10 && Math.abs(ratio - row.oracle['area-ratio']) <= 1e-12, 'oracle-disagreement', 'Frozen method disagrees with independent native arithmetic; output remains unpublished.')
    const qualifiedUses = row.uses.map(u => ({ ...u, qualification: projection(policy, u) }))
    const qualification = qualificationFor(policy, row.uses)
    const sampling = { id: row.id, point: row.point, stride: row.stride, spacing: row.spacing, samples: row.samples, uses: row.uses }
    const common = { schema: 'atlas-runtime-derived-artifact/v1', region: 'riffelhorn', task: row.id, methodRevision: METHOD, parameters: { stride: row.stride, spacingM: row.spacing, sampling: 'exact native cell centres; stride2 is declared subsampling' }, support: { crs: 'EPSG:2056', point: row.point, meaning: 'Local derivative, not a homogeneous patch', consumed: row.uses.map(u => u.scope) }, qualification }
    const a = { ...common, id: key(row.id, 'slope'), property: 'slope', method: 'Horn-3x3-grid-slope', value: slope, unit: 'degree', inputs: qualifiedUses.map(u => ({ kind: 'qualified-input-use', identity: digest(u) })), sampling, meaning: 'Local represented-heightfield slope; not accuracy, traversability or independent observation.' }
    const b = { ...common, id: key(row.id, 'area-ratio'), property: 'area-ratio', method: 'planar-area-ratio-from-slope', value: ratio, unit: 'dimensionless', inputs: [{ kind: 'derived', identity: digest(a) }], sampling: null, meaning: 'Local planar represented-surface/map-plane ratio; not true rough-surface area.' }
    artifacts[a.id] = a as unknown as ObjectJson; artifacts[b.id] = b as unknown as ObjectJson
  }
  return artifacts
}
export function validateDerived(root: string, policy: Policy, state: DerivedState, metrics?: ArtifactMetrics): ReadonlyMap<string, ObjectJson> {
  validatePolicy(policy)
  const expected = probes.flatMap(p => [key(p.id, 'slope'), key(p.id, 'area-ratio')]).sort()
  requireAtlas(state.schema === 'atlas-runtime-derived-state/v1' && Object.keys(state).sort().join(',') === 'active,executions,schema' && encode(Object.keys(state.active).sort()) === encode(expected) && encode(Object.keys(state.executions).sort()) === encode(expected), 'derived-incomplete', 'Complete finite output and execution membership required.')
  requireAtlas(affected(root, policy, state, metrics).length === 0, 'derived-stale', 'Stale derived state cannot be published as current.')
  const artifacts = new Map<string, ObjectJson>()
  for (const p of probes) {
    const a = readArtifact(root, state.active[key(p.id, 'slope')], metrics), b = readArtifact(root, state.active[key(p.id, 'area-ratio')], metrics)
    requireAtlas(a.id === key(p.id, 'slope') && b.id === key(p.id, 'area-ratio') && a.methodRevision === METHOD && b.methodRevision === METHOD && encode(b.inputs) === encode([{ kind: 'derived', identity: state.active[String(a.id)] }]) && encode(a.qualification) === encode(b.qualification) && encode(a.parameters) === encode(b.parameters), 'dependency-invalid', 'Exact typed acyclic slope-to-ratio relationship required.')
    requireAtlas(a.schema === 'atlas-runtime-derived-artifact/v1' && b.schema === a.schema && a.region === 'riffelhorn' && b.region === a.region, 'derived-invalid', 'Invalid derived artifact contract.')
    artifacts.set(String(a.id), a); artifacts.set(String(b.id), b)
  }
  const runs = new Map<string, ObjectJson>()
  for (const id of expected) {
    const runId = state.executions[id]; address(runId)
    if (!runs.has(runId)) runs.set(runId, readArtifact(root, runId, metrics, 'executions'))
    const run = runs.get(runId)!, worker = object(run.worker), coordinator = object(run.coordinator)
    const tasks = run.tasks as ObjectJson[]
    const requalified = run.schema === 'atlas-runtime-terrain-requalification/v1'
    requireAtlas(Object.keys(run).sort().join(',') === (requalified ? 'coordinator,methodRevision,outputs,reusedInputs,schema,tasks,worker' : 'coordinator,methodRevision,outputs,schema,tasks,worker') && Array.isArray(tasks) && tasks.length > 0 && tasks.length <= 16 && new Set(tasks.map(t => t.id)).size === tasks.length && tasks.every(t => Object.keys(t).sort().join(',') === 'id,stride' && probes.some(p => p.id === t.id) && [1, 2].includes(Number(t.stride))) && encode(Object.keys(object(run.outputs)).sort()) === encode(tasks.flatMap(t => [key(String(t.id), 'slope'), key(String(t.id), 'area-ratio')]).sort()), 'execution-invalid', 'Incomplete or malformed execution task/output provenance.')
    requireAtlas(tasks.some(t => t.id === artifacts.get(id)!.task && t.stride === object(artifacts.get(id)!.parameters).stride), 'execution-invalid', 'Recorded execution parameters differ from the actual result.')
    requireAtlas((requalified || run.schema === 'atlas-runtime-terrain-execution/v1') && run.methodRevision === METHOD && object(run.outputs)[id] === state.active[id] && coordinator.methodSourceSha256 === plan.method.sha256 && typeof coordinator.node === 'string' && ['python', 'numpy', 'rasterio', 'pyproj'].every(k => typeof worker[k] === 'string' && String(worker[k]).length > 0), 'execution-invalid', 'Missing or mismatched immutable processing provenance.')
    if (requalified) {
      requireAtlas(encode(Object.keys(object(run.reusedInputs)).sort()) === encode(Object.keys(object(run.outputs)).sort()), 'execution-invalid', 'Requalification must identify every reused numerical input.')
      const previous = readArtifact(root, String(object(run.reusedInputs)[id]), metrics), next = artifacts.get(id)!
      requireAtlas(['id', 'value', 'property', 'method', 'methodRevision', 'parameters', 'sampling', 'support'].every(k => encode(previous[k]) === encode(next[k])), 'execution-invalid', 'Requalification cannot silently change numerical values, samples, method, parameters or support.')
    }
    address(worker.samplingWorkerSha256)
    requireAtlas(worker.oracleSha256 === '9a2c914c272b8f010ee92293bd82fd056af922da9c74966d2eb2d6f4462f6bbb', 'execution-invalid', 'Unknown independent oracle identity.')
  }
  return runs
}
