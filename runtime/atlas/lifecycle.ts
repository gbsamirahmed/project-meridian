import { openAtlas } from './index.ts'
import { object, resolveAuthoritative, validateNativeFiles, readJson } from './authority.ts'
import type { ObjectJson } from './authority.ts'
import { owned, initializeWorld, immutable, stageObject, commit, recover } from './publication.ts'
import { probes, revise, affected, outputs, digest, validateDerived, readArtifact, projection } from './lifecycle-model.ts'
import type { Policy, DerivedState, Change, TerrainRow } from './lifecycle-model.ts'
import type { RuntimeConfig, Json, DerivationStage } from './types.ts'
import { requireAtlas } from './errors.ts'
import path from 'node:path'

export type { Change, Notice } from './lifecycle-model.ts'
export { recover as recoverWorld }
export async function createWorld(config: RuntimeConfig, source: string): Promise<ObjectJson> {
  const context = await openAtlas({ ...config, publicationRoot: source })
  try {
    const result = initializeWorld(config, source, context.generation), copied = await openAtlas(config)
    try { return { ...result, validation: copied.validation as unknown as Json } } finally { await copied.close() }
  } finally { await context.close() }
}
async function prepare(config: RuntimeConfig, change: Change = {}, full = false, write = true, failAt?: 'afterArtifacts'): Promise<DerivationStage> {
  const start = performance.now(), root = owned(config), base = resolveAuthoritative(config), context = await openAtlas({ ...config, generation: base.generation })
  try {
    const prior = base.values.terrainDerived as unknown as DerivedState | undefined
    const description = await context.terrainSamples([])
    const previousPolicy = base.values.terrainLifecycle as unknown as Policy | undefined
    const policy = revise(previousPolicy ?? { schema: 'atlas-runtime-terrain-policy/v1', sources: description.registry as Policy['sources'], parameters: {}, notes: [] }, change)
    requireAtlas(digest(policy.sources) === digest(description.registry), 'source-invalid', 'Source identities/qualification differ from verified retained inputs.')
    const metadata = { records: 0, bytes: 0 }, closure = affected(root, policy, prior, metadata), tasks = probes.filter(p => full || closure.includes(p.id + '|slope')).map(p => ({ id: p.id, stride: policy.parameters[p.id] ?? 1 }))
    const processingStart = performance.now(), sampled = await context.terrainSamples(tasks), made = await outputs(policy, sampled.rows as unknown as TerrainRow[]), processingMs = performance.now() - processingStart
    const writes = { recordsWritten: 0, bytesWritten: 0, recordsRead: 0, bytesRead: 0, bytesEncoded: 0 }
    const active = { ...(prior?.active ?? {}) }
    for (const [id, body] of Object.entries(made)) active[id] = write ? immutable(root, 'artifacts', body, writes) : digest(body)
    if (failAt === 'afterArtifacts') process.exit(92) // Test-only abrupt stop, never a CLI flag.
    const executions = { ...(prior?.executions ?? {}) }
    if (write && Object.keys(made).length) {
      const method = object(readJson(path.join(import.meta.dirname, 'lifecycle-plan.json')).method)
      const run = immutable(root, 'executions', { schema: 'atlas-runtime-terrain-execution/v1', methodRevision: Object.values(made)[0].methodRevision, worker: sampled.environment, coordinator: { node: process.version, methodSourceSha256: method.sha256 }, tasks, outputs: Object.fromEntries(Object.keys(made).map(id => [id, active[id]])) }, writes)
      for (const id of Object.keys(made)) executions[id] = run
    }
    const state: DerivedState = { schema: 'atlas-runtime-derived-state/v1', active, executions }
    if (write) validateDerived(root, policy, state, metadata)
    const values: Record<string, ObjectJson> = { ...base.values, terrainLifecycle: policy as unknown as ObjectJson, terrainDerived: state as unknown as ObjectJson }
    if (change.unrelated) {
      values.tryfanRegistration = structuredClone(values.tryfanRegistration)
      const admin = object(values.tryfanRegistration.administrative), revision = Number(admin.revision) === 1 ? 0 : 1
      values.tryfanRegistration.administrative = { revision, notice: revision === 0 ? 'Initial retained regional registration; no new physical observation' : 'Administrative accountability notice revision; no evidence or physical change' }
    }
    const unchanged = digest(values) === digest(base.values)
    const generation = write && !unchanged ? stageObject(root, base, values, writes) : base.generation
    return { schema: 'atlas-runtime-lifecycle-stage/v1', generation, predecessor: base.generation, status: unchanged ? 'no-op' : write ? 'staged-unpublished' : 'full-oracle-only', affected: closure, recomputed: Object.keys(made).sort(), reused: 32 - Object.keys(made).length, active, policy, environment: sampled.environment, metrics: { totalMs: performance.now() - start, processingMs, fullValidationMs: context.validation.milliseconds, artifactMetadataReads: metadata.records, artifactMetadataBytes: metadata.bytes, artifactWriteAttempts: write ? Object.keys(made).length : 0, writes, ...object(sampled.metrics) }, validation: context.validation }
  } finally { await context.close() }
}
export const stageDerivation = (config: RuntimeConfig, change: Change = {}, options: { failAt?: 'afterArtifacts' } = {}): Promise<DerivationStage> => prepare(config, change, false, true, options.failAt)
/** Clean all-probe derivation independent of scoped selection, with NumPy arithmetic oracle. No writes. */
export const fullDerivationReference = (config: RuntimeConfig, change: Change = {}): Promise<DerivationStage> => prepare(config, change, true, false)
export async function inspectLifecycle(config: RuntimeConfig, change: Change = {}): Promise<ObjectJson> {
  const root = owned(config), snapshot = resolveAuthoritative(config), context = await openAtlas(config)
  try {
    const description = await context.terrainSamples([]), policy = revise(snapshot.values.terrainLifecycle as unknown as Policy ?? { schema: 'atlas-runtime-terrain-policy/v1', sources: description.registry as Policy['sources'], parameters: {}, notes: [] }, change)
    const state = snapshot.values.terrainDerived as unknown as DerivedState | undefined
    const edges: ObjectJson[] = []
    for (const p of probes) if (state) {
      const slope = readArtifact(root, state.active[p.id + '|slope'])
      for (const use of object(slope.sampling).uses as ObjectJson[]) {
        const identity = digest({ ...use, qualification: projection(snapshot.values.terrainLifecycle as unknown as Policy, use) })
        edges.push({ from: digest(policy.sources[String(use.key)]), to: identity, type: 'source-use' }, { from: identity, to: state.active[p.id + '|slope'], type: 'use-slope' })
      }
      edges.push({ from: state.active[p.id + '|slope'], to: state.active[p.id + '|area-ratio'], type: 'slope-ratio' })
    }
    return { generation: snapshot.generation, affected: affected(root, policy, state), policy: policy as unknown as Json, graph: { registeredSourceNodes: 4, qualifiedUseNodes: edges.filter(e => e.type === 'source-use').length, derivedNodes: state ? 32 : 0, edges, maximumDepth: state ? 3 : 0, crossRegionEdges: 0 }, staleMeaning: 'Changed dependency assumptions, not false historical results.' }
  } finally { await context.close() }
}
export async function validateStage(config: RuntimeConfig, generation: string): Promise<ObjectJson> {
  const start = performance.now(), root = owned(config), candidate = resolveAuthoritative(config, generation, false), active = resolveAuthoritative({ ...config, generation: undefined })
  requireAtlas(candidate.publication.predecessor === active.generation && Number(candidate.publication.ordinal) === Number(active.publication.ordinal) + 1 && candidate.values.terrainLifecycle && candidate.values.terrainDerived, 'stage-invalid', 'Only a complete next-generation lifecycle stage can publish.')
  validateNativeFiles(candidate, config)
  const context = await openAtlas({ ...config, generation: active.generation })
  try {
    requireAtlas(digest(candidate.values.riffelhornRegistration) === digest(active.values.riffelhornRegistration), 'registration-invalid', 'This slice cannot replace regional sources/preparation.')
    const policy = candidate.values.terrainLifecycle as unknown as Policy, state = candidate.values.terrainDerived as unknown as DerivedState
    const metadata = { records: 0, bytes: 0 }, runs = validateDerived(root, policy, state, metadata)
    const sampled = await context.terrainSamples(probes.map(p => ({ id: p.id, stride: policy.parameters[p.id] ?? 1 })))
    requireAtlas(digest(policy.sources) === digest(sampled.registry), 'source-invalid', 'Staged source identity differs from retained evidence.')
    const full = await outputs(policy, sampled.rows as unknown as TerrainRow[])
    const priorActive = active.values.terrainDerived ? object(active.values.terrainDerived.active) : {}
    for (const [id, body] of Object.entries(full)) {
      requireAtlas(digest(body) === state.active[id] && digest(readArtifact(root, state.active[id], metadata)) === digest(body), 'derived-invalid', 'Full authoritative derivation differs; stage remains unpublished.')
      if (priorActive[id] !== state.active[id]) {
        const runId = state.executions[id]
        const run = runs.get(runId)!
        requireAtlas(digest(run.worker) === digest(sampled.environment) && object(run.coordinator).node === process.version, 'execution-invalid', 'New output must record the actual configured worker/coordinator environment.')
      }
    }
    return { generation, status: 'fully-validated-unpublished', outputChecks: 32, metadataRecords: candidate.metrics.metadataRecords + context.validation.metadataRecords + metadata.records, artifactMetadataReads: metadata.records, artifactMetadataBytes: metadata.bytes, payloadBytesHashed: candidate.metrics.payloadBytesHashed + context.validation.payloadBytesHashed, payloadHashOperations: candidate.metrics.payloadHashOperations + context.validation.payloadHashOperations, milliseconds: performance.now() - start, sampling: sampled.metrics }
  } finally { await context.close() }
}
export async function publishStage(config: RuntimeConfig, generation: string, options: { failAt?: 'beforeRoot' | 'crashBeforeRoot' } = {}): Promise<ObjectJson> {
  const start = performance.now()
  const current = readJson(path.join(owned(config), 'current.json')).generation
  if (current === generation) { const context = await openAtlas({ ...config, generation }); try { return { generation, status: 'already-current-validated' } } finally { await context.close() } }
  let validation: ObjectJson | undefined
  const result = await commit(config, generation, async () => { validation = await validateStage(config, generation) }, options.failAt)
  return { ...result, validation: validation!, milliseconds: performance.now() - start }
}
