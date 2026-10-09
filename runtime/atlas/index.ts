import fs from 'node:fs'
import path from 'node:path'
import { randomUUID } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { object, publicPath, readJson, resolveAuthoritative, validateNativeFiles } from './authority.ts'
import type { ObjectJson, Snapshot } from './authority.ts'
import { requireAtlas, AtlasError } from './errors.ts'
import { NativeWorker } from './worker.ts'
import { validateDerived, readArtifact, probes } from './lifecycle-model.ts'
import type { Policy, DerivedState } from './lifecycle-model.ts'
import type { Json, Query, QueryAnswer, QualifiedResult, RuntimeConfig, DerivedQuery, DerivedAnswer } from './types.ts'
export type { Query, QueryAnswer, RuntimeConfig, QualifiedResult, DerivationStage, DerivedQuery, DerivedAnswer } from './types.ts'
export { AtlasError } from './errors.ts'
export { createWorld, stageDerivation, inspectLifecycle, validateStage, publishStage, fullDerivationReference, recoverWorld } from './lifecycle.ts'
export type { Change, Notice } from './lifecycle.ts'

const EPOCH = /^[a-f0-9-]{36}$/
function resolvedLocation(p: string): string {
  const absolute = publicPath(p)
  if (fs.existsSync(absolute)) return fs.realpathSync(absolute)
  const parent = path.dirname(absolute)
  requireAtlas(parent !== absolute, 'path-unavailable', 'Configured local volume is unavailable; restore the explicit data path. No generation fallback is permitted.')
  return path.join(resolvedLocation(parent), path.basename(absolute))
}
function inside(child: string, parent: string): boolean {
  const relative = path.relative(parent, child)
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))
}
function safeConfig(input: RuntimeConfig): RuntimeConfig {
  const config = { ...input, dataRoot: resolvedLocation(input.dataRoot), publicationRoot: resolvedLocation(input.publicationRoot), catalogueRoot: resolvedLocation(input.catalogueRoot), python: publicPath(input.python) }
  const repository = fileURLToPath(new URL('../../', import.meta.url))
  for (const protectedRoot of [config.dataRoot, config.publicationRoot, repository]) {
    requireAtlas(!inside(config.catalogueRoot, protectedRoot) && !inside(protectedRoot, config.catalogueRoot), 'catalogue-path', 'Place the disposable catalogue outside canonical data, publication files and the repository.')
  }
  return config
}
function durableJson(file: string, value: Json): void {
  const fd = fs.openSync(file, 'wx')
  try { fs.writeFileSync(fd, JSON.stringify(value) + '\n'); fs.fsyncSync(fd) } finally { fs.closeSync(fd) }
}

/** Read-only authoritative session. Only disposable catalogue directories are written. */
export class AtlasContext {
  readonly generation: string
  readonly members: Readonly<Record<string, string>>
  readonly validation: Snapshot['metrics']
  readonly nativeSetup: ObjectJson
  private epoch?: string
  private config: RuntimeConfig
  private snapshot: Snapshot
  private worker: NativeWorker
  private constructor(config: RuntimeConfig, snapshot: Snapshot, worker: NativeWorker, setup: ObjectJson) {
    this.config = config; this.snapshot = snapshot; this.worker = worker
    this.generation = snapshot.generation; this.members = Object.freeze({ ...snapshot.members })
    this.validation = { ...snapshot.metrics }; this.nativeSetup = setup
  }
  static async open(input: RuntimeConfig): Promise<AtlasContext> {
    const start = performance.now(), config = safeConfig(input), snapshot = resolveAuthoritative(config)
    validateNativeFiles(snapshot, config)
    const worker = new NativeWorker(config.python)
    try {
      const registration = snapshot.values.riffelhornRegistration
      const revision = registration.preparationRevision
      requireAtlas(typeof revision === 'string' && /^[a-f0-9]{64}$/.test(revision), 'registration-invalid', 'Expected immutable prepared revision identity.')
      const setup = object(await worker.call('initialize', { dataRoot: config.dataRoot, preparedRoot: publicPath(path.join(config.dataRoot, 'derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1', revision)), registration, tryfan: { catalogue: snapshot.native.catalogue, core: snapshot.native.core } }))
      snapshot.metrics.payloadHashOperations += Number(setup.inputHashOperations)
      snapshot.metrics.payloadBytesHashed += Number(setup.inputBytesHashed)
      snapshot.metrics.metadataBytes += Number(setup.nativeMetadataBytesParsed)
      snapshot.metrics.milliseconds = performance.now() - start
      snapshot.metrics.parentRssBytes = process.memoryUsage().rss
      if (snapshot.values.terrainLifecycle) {
        const artifactMetrics = { records: 0, bytes: 0 }
        validateDerived(config.publicationRoot, snapshot.values.terrainLifecycle as unknown as Policy, snapshot.values.terrainDerived as unknown as DerivedState, artifactMetrics)
        const samples = object(await worker.call('terrain', { schema: 'atlas-runtime-terrain-request/v1', tasks: probes.map(p => ({ id: p.id, stride: object(snapshot.values.terrainLifecycle.parameters)[p.id] ?? 1 })) }))
        const { outputs, digest } = await import('./lifecycle-model.ts')
        requireAtlas(digest(samples.registry) === digest(snapshot.values.terrainLifecycle.sources), 'source-invalid', 'Lifecycle source qualification differs from verified retained evidence.')
        const full = await outputs(snapshot.values.terrainLifecycle as unknown as Policy, samples.rows as never)
        for (const [id, body] of Object.entries(full)) requireAtlas(digest(body) === object(snapshot.values.terrainDerived.active)[id], 'derived-invalid', 'Full native recomputation disagrees with authoritative derived output.')
        snapshot.metrics.metadataRecords += artifactMetrics.records
        snapshot.metrics.metadataBytes += artifactMetrics.bytes
        snapshot.metrics.milliseconds = performance.now() - start
      }
      return new AtlasContext(config, snapshot, worker, setup)
    } catch (error) { await worker.close(); throw error }
  }
  private checkAuthority(): Snapshot {
    const current = resolveAuthoritative(this.config, this.generation)
    requireAtlas(current.fingerprint === this.snapshot.fingerprint, 'canonical-integrity', 'Pinned canonical closure changed; reopen and fully validate authoritative evidence.')
    return current
  }
  private catalogue(): ObjectJson {
    try {
      if (!this.epoch) {
        const pointer = readJson(path.join(this.config.catalogueRoot, 'current.json'))
        requireAtlas(pointer.schema === 'atlas-local-catalogue-pointer/v1' && typeof pointer.epoch === 'string' && EPOCH.test(pointer.epoch), 'catalogue-invalid', 'Malformed catalogue pointer; rebuild explicitly.')
        this.epoch = pointer.epoch
      }
      const folder = publicPath(path.join(this.config.catalogueRoot, 'epochs', this.epoch)), seal = readJson(publicPath(path.join(folder, 'seal.json')))
      requireAtlas(seal.schema === 'atlas-local-catalogue-seal/v1' && seal.schemaVersion === 1 && seal.records === 49, 'catalogue-schema', 'Incompatible catalogue schema; rebuild explicitly.')
      requireAtlas(seal.generation === this.generation && seal.fingerprint === this.snapshot.fingerprint, 'catalogue-stale', 'Catalogue belongs to another generation/closure; rebuild for the selected generation.')
      requireAtlas(typeof seal.sha256 === 'string' && /^[a-f0-9]{64}$/.test(seal.sha256), 'catalogue-invalid', 'Malformed catalogue seal; rebuild.')
      return { file: publicPath(path.join(folder, 'index.sqlite')), sha256: seal.sha256, generation: this.generation, fingerprint: this.snapshot.fingerprint }
    } catch (error) {
      if (error instanceof AtlasError) throw error
      throw new AtlasError('catalogue-missing', 'Catalogue or its seal is missing/malformed; run catalogue build for this exact generation.')
    }
  }
  /** Build a new disposable epoch, replacing the catalogue pointer only after success.
   * failAt is a bounded fault-injection seam for tests; never a CLI option. */
  async buildCatalogue(options: { failAt?: 'beforeInstall' | 'beforePointer' } = {}): Promise<ObjectJson> {
    const start = performance.now(); this.checkAuthority()
    const epoch = randomUUID(), staging = path.join(this.config.catalogueRoot, 'staging', epoch), destination = path.join(this.config.catalogueRoot, 'epochs', epoch)
    fs.mkdirSync(staging, { recursive: true }); fs.mkdirSync(path.dirname(destination), { recursive: true })
    const file = path.join(staging, 'index.sqlite')
    const built = object(await this.worker.call('build', { file, generation: this.generation, fingerprint: this.snapshot.fingerprint }))
    durableJson(path.join(staging, 'seal.json'), { schema: 'atlas-local-catalogue-seal/v1', schemaVersion: 1, generation: this.generation, fingerprint: this.snapshot.fingerprint, members: this.snapshot.members, records: built.records, sha256: built.sha256 })
    await this.worker.call('verify', { file, sha256: built.sha256, generation: this.generation, fingerprint: this.snapshot.fingerprint })
    this.checkAuthority()
    requireAtlas(options.failAt !== 'beforeInstall', 'build-interrupted', 'Simulated interruption before completed catalogue installation.')
    fs.renameSync(staging, destination)
    requireAtlas(options.failAt !== 'beforePointer', 'build-interrupted', 'Simulated interruption before catalogue pointer replacement.')
    const pointer = path.join(this.config.catalogueRoot, epoch + '.tmp')
    durableJson(pointer, { schema: 'atlas-local-catalogue-pointer/v1', epoch })
    fs.renameSync(pointer, path.join(this.config.catalogueRoot, 'current.json'))
    this.epoch = epoch
    return { ...built, generation: this.generation, milliseconds: performance.now() - start, epoch }
  }
  async verifyCatalogue(): Promise<ObjectJson> {
    this.checkAuthority()
    return object(await this.worker.call('verify', this.catalogue()))
  }
  private async run(query: Query, scan: boolean): Promise<QueryAnswer> {
    const current = this.checkAuthority()
    const answer = object(await this.worker.call('query', { ...(scan ? { scan: true } : this.catalogue()), query: query as Json }))
    const results = (answer.results as ObjectJson[]).map(r => ({ ...r, componentIdentity: this.members[r.region === 'tryfan' ? 'tryfanRegistration' : 'riffelhornRegistration'] })) as unknown as QualifiedResult[]
    return { schema: 'atlas-local-query/v1', generation: this.generation, members: { ...this.members }, results, gap: answer.gap, metrics: { ...(answer.metrics as Record<string, number>), canonicalMetadataReads: current.metrics.metadataRecords, canonicalMetadataBytes: current.metrics.metadataBytes } }
  }
  query(query: Query): Promise<QueryAnswer> { return this.run(query, false) }
  /** Diagnostic full-scan reference, never an automatic catalogue fallback. */
  scanReference(query: Query): Promise<QueryAnswer> { return this.run(query, true) }
  /** Narrow processing contract on fully verified native inputs; no hidden data roots. */
  async terrainSamples(tasks: { id: string; stride: number }[]): Promise<ObjectJson> {
    this.checkAuthority()
    const response = object(await this.worker.call('terrain', { schema: 'atlas-runtime-terrain-request/v1', tasks }))
    requireAtlas(response.schema === 'atlas-runtime-terrain-response/v1' && Array.isArray(response.rows) && response.rows.length === tasks.length && (response.rows as ObjectJson[]).every((r, i) => r.id === tasks[i].id && r.stride === tasks[i].stride), 'processing-invalid', 'Worker response identity/schema differs from the exact requested task set.')
    object(response.environment); return response
  }
  /** Finite canonical scalar lookup, separate from the 49-record native SQLite catalogue. */
  derived(query: DerivedQuery = {}): DerivedAnswer {
    const current = this.checkAuthority()
    requireAtlas(query && typeof query === 'object' && !Array.isArray(query) && Object.keys(query).every(k => ['identity', 'property'].includes(k)) && (query.property === undefined || ['slope', 'area-ratio'].includes(query.property)) && (query.identity === undefined || typeof query.identity === 'string' && query.identity.length > 0), 'query-invalid', 'Only nonempty exact derived identity/property predicates are supported.')
    const regionalRegistration = { componentIdentity: this.members.riffelhornRegistration, evidence: current.values.riffelhornRegistration }
    if (!current.values.terrainDerived) return { generation: this.generation, regionalRegistration, results: [], status: 'no-runtime-derived-state' }
    const artifactMetrics = { records: 0, bytes: 0 }
    validateDerived(this.config.publicationRoot, current.values.terrainLifecycle as unknown as Policy, current.values.terrainDerived as unknown as DerivedState, artifactMetrics)
    const active = object(current.values.terrainDerived.active)
    const executions = object(current.values.terrainDerived.executions), runCache = new Map<string, ObjectJson>()
    const results = Object.entries(active).sort(([a], [b]) => a.localeCompare(b)).filter(([id]) => !query.identity || query.identity === id).map(([id, revision]): ObjectJson => {
      const runId = String(executions[id])
      if (!runCache.has(runId)) runCache.set(runId, readArtifact(this.config.publicationRoot, runId, artifactMetrics, 'executions'))
      return { ...readArtifact(this.config.publicationRoot, String(revision), artifactMetrics), revision, componentIdentity: this.members.terrainDerived, execution: { identity: runId, record: runCache.get(runId)! } }
    }).filter(a => !query.property || a.property === query.property)
    return { generation: this.generation, regionalRegistration, status: 'current-in-pinned-context', results, metrics: { outputMembershipChecks: 32, artifactMetadataReads: artifactMetrics.records, artifactMetadataBytes: artifactMetrics.bytes, canonicalMetadataReads: current.metrics.metadataRecords, canonicalMetadataBytes: current.metrics.metadataBytes, returned: results.length, ancestryTraversals: 0 } }
  }
  close(): Promise<void> { return this.worker.close() }
}
export const openAtlas = AtlasContext.open
