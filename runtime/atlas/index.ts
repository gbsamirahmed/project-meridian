import fs from 'node:fs'
import path from 'node:path'
import { randomUUID } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { object, publicPath, readJson, resolveAuthoritative, validateNativeFiles } from './authority.ts'
import type { ObjectJson, Snapshot } from './authority.ts'
import { requireAtlas, AtlasError } from './errors.ts'
import { NativeWorker } from './worker.ts'
import type { Json, Query, QueryAnswer, QualifiedResult, RuntimeConfig } from './types.ts'
export type { Query, QueryAnswer, RuntimeConfig, QualifiedResult } from './types.ts'
export { AtlasError } from './errors.ts'

const EPOCH = /^[a-f0-9-]{36}$/
function resolvedLocation(p: string): string {
  const absolute = publicPath(p)
  if (fs.existsSync(absolute)) return fs.realpathSync(absolute)
  return path.join(resolvedLocation(path.dirname(absolute)), path.basename(absolute))
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
  close(): Promise<void> { return this.worker.close() }
}
export const openAtlas = AtlasContext.open
