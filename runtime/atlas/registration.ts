/** Bounded native registration/update coordination through the local runtime. */
import fs from 'node:fs'
import path from 'node:path'
import { randomUUID } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { canonicalGeneration } from '../../pilots/atlas/tryfan/generations.mjs'
import { verifyArtifacts } from '../../pilots/atlas/tryfan/catalogue.mjs'
import { verifyDelivery } from '../../pilots/atlas/tryfan/delivery-schema.mjs'
import { encode, sha } from '../../pilots/atlas/tryfan/identity.mjs'
import { openAtlas } from './index.ts'
import { NativeWorker } from './worker.ts'
import { object, publicPath, readJson, resolveAuthoritative } from './authority.ts'
import type { ObjectJson } from './authority.ts'
import { digest, readArtifact, revise, affected, requalifyOutputs, validateDerived } from './lifecycle-model.ts'
import type { Policy, DerivedState } from './lifecycle-model.ts'
import { validateRequest, validateRegistrations, nativeFor } from './registration-model.ts'
import type { RegistrationRequest } from './registration-model.ts'
import { immutable, durable, member, stageObject, owned, real, inside } from './publication.ts'
import { requireAtlas } from './errors.ts'
import type { RuntimeConfig } from './types.ts'
export type { RegistrationRequest } from './registration-model.ts'

export interface RegistrationInputs { tryfanRoot: string; preparedRoot: string }
const TRYFAN = '5f2c1b1f25c45ddea7e640f8c286a6caec5dc61aa55e8f678062bdc5704fca06'
async function inputs(config: RuntimeConfig, input: RegistrationInputs) {
  const start = performance.now(), data = real(config.dataRoot), tryfan = real(input.tryfanRoot), prepared = real(input.preparedRoot)
  requireAtlas(inside(tryfan, data) && inside(prepared, data), 'registration-path', 'Selected retained reference and prepared artifacts must be within the explicit public data root.')
  const bytes = fs.readFileSync(path.join(tryfan, 'generations', TRYFAN + '.json')), native = object(canonicalGeneration(JSON.parse(bytes.toString('utf8'))))
  requireAtlas(sha(bytes) === TRYFAN && encode(native) === bytes.toString('utf8'), 'registration-native', 'Exact accepted Tryfan canonical reference required; no scientific state replacement.')
  const locators = readJson(path.join(tryfan, 'locators', TRYFAN + '.json')), verified = verifyArtifacts(native.catalogue, locators, data)
  verifyDelivery(tryfan, native.serving)
  const worker = new NativeWorker(publicPath(config.python))
  try {
    const description = object(await worker.call('describe', { dataRoot: data, preparedRoot: prepared })), riff = object(description.native)
    const tr = { schema: 'atlas-regional-evidence-registration/v1', region: 'tryfan', acceptedGeneration: TRYFAN, support: { crs: object(native.core).crs, bounds: object(native.core).bounds }, catalogueIdentity: digest(native.catalogue), knowledgeIdentity: digest(native.knowledge), understandingIdentity: digest(native.understanding), nativeFamilies: (object(native.catalogue).families as ObjectJson[]).map(f => f.id), administrative: { revision: 0, notice: 'Initial retained regional registration; no new physical observation' } }
    requireAtlas(prepared === real(path.join(data, 'derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1', String(riff.preparationRevision))), 'registration-path', 'Use the exact verified retained preparation directory, not an unaccountable copy.')
    return { native, locators, tryfan, registrations: { riffelhorn: riff, tryfan: tr as unknown as ObjectJson }, metrics: { milliseconds: performance.now() - start, payloadBytesHashed: verified.bytes + Number(object(description.setup).inputBytesHashed) + (object(native.serving).assets as ObjectJson[]).filter(a => object(a.origin).kind === 'materialized').reduce((n, a) => n + Number(a.bytes), 0), payloadHashOperations: verified.artifacts + Number(object(description.setup).inputHashOperations) + 2, nativeSetup: description.setup } }
  } finally { await worker.close() }
}
function revision(request: RegistrationRequest, previous?: ObjectJson, supersedes?: string): ObjectJson {
  const acceptedAt = new Date().toISOString()
  requireAtlas(!previous || acceptedAt > String(object(previous.knowledgeTime).acceptedAt), 'registration-time', 'Acceptance clock has not advanced beyond the previous revision; retry with a correct local clock.')
  return { schema: 'atlas-runtime-registration-revision/v1', operation: request.operation, region: request.region, native: request.native, nativeIdentity: digest(request.native), sequence: previous ? Number(previous.sequence) + 1 : 0, supersedes: supersedes ?? null, knowledgeTime: { acceptedAt, basis: 'runtime acceptance clock; not physical observation or source publication' }, physicalChangeInferred: false, explanation: request.explanation, sourceNotice: request.sourceNotice as unknown as ObjectJson ?? null }
}
function template(native: ObjectJson, region: RegistrationRequest['region'], generation: string | null, id: string | null): RegistrationRequest {
  return { schema: 'atlas-runtime-registration-request/v1', operation: 'register', region, expectedGeneration: generation, expectedRevision: id, native, explanation: 'Register retained qualified evidence; no new physical observation' }
}
export async function inspectEvidence(config: RuntimeConfig, selected?: RegistrationInputs): Promise<ObjectJson> {
  if (selected) {
    const verified = await inputs(config, selected)
    const snapshot = fs.existsSync(path.join(config.publicationRoot, 'current.json')) ? resolveAuthoritative(config) : undefined
    if (snapshot) { const context = await openAtlas(config); try { verified.metrics.payloadBytesHashed += context.validation.payloadBytesHashed; verified.metrics.payloadHashOperations += context.validation.payloadHashOperations } finally { await context.close() } }
    const registrations = snapshot ? validateRegistrations(snapshot, config.publicationRoot) : {}
    return { verified: true, templates: Object.fromEntries(Object.entries(verified.registrations).map(([region, native]) => [region, template(snapshot ? nativeFor(snapshot, region) : native, region as RegistrationRequest['region'], snapshot?.generation ?? null, registrations[region] ? String(registrations[region].identity) : null)])) as unknown as ObjectJson, metrics: verified.metrics }
  }
  const context = await openAtlas(config)
  try { const snapshot = resolveAuthoritative(config); return { generation: context.generation, registrations: validateRegistrations(snapshot, config.publicationRoot), native: { tryfan: snapshot.values.tryfanRegistration, riffelhorn: snapshot.values.riffelhornRegistration }, validation: context.validation as unknown as ObjectJson } }
  finally { await context.close() }
}
/** Assemble from canonical pilot/reference and preparation manifests, never copy a research world. */
export async function registerEvidence(config: RuntimeConfig, selected: RegistrationInputs, request: RegistrationRequest, options: { failAt?: 'beforeInstall' } = {}): Promise<ObjectJson> {
  validateRequest(request)
  if (fs.existsSync(config.publicationRoot)) return stageEvidenceUpdate(config, request)
  requireAtlas(config.generation === undefined, 'registration-request', 'Initial registration creates a new generation; a historical generation selector is not an input observation identity.')
  requireAtlas(request.operation === 'register' && request.region === 'riffelhorn' && request.expectedGeneration === null && request.expectedRevision === null, 'registration-request', 'Initial registration needs a Riffelhorn register request with no existing generation/revision.')
  const verified = await inputs(config, selected)
  requireAtlas(digest(request.native) === digest(verified.registrations.riffelhorn), 'registration-native', 'Requested source/preparation/rights/support/time differs from verified retained evidence.')
  const target = real(config.publicationRoot), data = real(config.dataRoot), repo = fileURLToPath(new URL('../../', import.meta.url)), cache = real(config.catalogueRoot)
  requireAtlas(![data, repo, cache].some(p => inside(target, p) || inside(p, target)), 'world-path', 'Use a new owned world outside public inputs, repository and disposable catalogue.')
  fs.mkdirSync(path.dirname(target), { recursive: true }); const staging = target + '.registering-' + randomUUID(); fs.mkdirSync(staging)
  const writes = { recordsWritten: 0, bytesWritten: 0, recordsRead: 0, bytesRead: 0, bytesEncoded: 0 }
  const active: ObjectJson = {}
  for (const region of ['riffelhorn', 'tryfan'] as const) active[region] = immutable(staging, 'registrations', revision(region === 'riffelhorn' ? request : template(verified.registrations.tryfan, 'tryfan', null, null)), writes)
  const values: Record<string, ObjectJson> = { catalogue: object(verified.native.catalogue), knowledge: object(verified.native.knowledge), understanding: object(verified.native.understanding), serving: object(verified.native.serving), locators: verified.locators, tryfanRegistration: verified.registrations.tryfan, riffelhornRegistration: verified.registrations.riffelhorn, registrationLedger: { schema: 'atlas-runtime-registration-ledger/v1', active } }
  const header = Object.fromEntries(Object.entries(verified.native).filter(([k]) => !['catalogue', 'knowledge', 'understanding', 'serving'].includes(k)))
  const members = Object.fromEntries(Object.entries(values).map(([kind, value]) => [kind, immutable(staging, 'components', { schema: 'atlas-retained-component/v1', kind, value }, writes)]))
  const generation = immutable(staging, 'publications', { schema: 'atlas-component-publication/v1', ordinal: 1, predecessor: null, header, members, legacyGeneration: digest({ ...verified.native, tryfanRegistration: values.tryfanRegistration, riffelhornRegistration: values.riffelhornRegistration, registrationLedger: values.registrationLedger }) }, writes)
  for (const asset of object(verified.native.serving).assets as ObjectJson[]) if (object(asset.origin).kind === 'materialized') {
    const name = String(asset.id) + (asset.mime === 'image/png' ? '.png' : '.json'), dest = path.join(staging, 'artifacts', name)
    fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.copyFileSync(path.join(verified.tryfan, 'artifacts', name), dest)
    writes.recordsWritten++; writes.bytesWritten += Number(asset.bytes)
  }
  durable(path.join(staging, 'current.json'), encode({ schema: 'atlas-component-root/v1', generation, membership: member(staging, null, generation, 0, writes) }))
  durable(path.join(staging, 'owned-world.json'), JSON.stringify({ schema: 'atlas-local-owned-world/v1', originGeneration: generation }) + '\n')
  const context = await openAtlas({ ...config, publicationRoot: staging, generation })
  try {
    if (options.failAt === 'beforeInstall') process.exit(93) // Tests only; final destination remains absent.
    requireAtlas(!fs.existsSync(target), 'publication-conflict', 'Registration destination appeared; never overwrite it.')
    fs.renameSync(staging, target)
    return { generation, status: 'registered-published', registrations: validateRegistrations(resolveAuthoritative(config), target), validation: context.validation as unknown as ObjectJson, preparationVerification: verified.metrics, writes }
  } finally { await context.close() }
}
async function update(config: RuntimeConfig, request: RegistrationRequest, write: boolean, options: { failAt?: 'afterArtifacts' } = {}): Promise<ObjectJson> {
  validateRequest(request); const start = performance.now(), root = owned(config), context = await openAtlas(config)
  try {
    const base = resolveAuthoritative({ ...config, generation: undefined }), registrationReads = { records: 0, bytes: 0 }, prior = validateRegistrations(base, root, registrationReads), current = prior[request.region]
    requireAtlas(context.generation === base.generation, 'registration-conflict', 'Publication changed during opening; inspect and restage explicitly.')
    requireAtlas(request.expectedGeneration === base.generation && digest(request.native) === digest(nativeFor(base, request.region)), 'registration-conflict', 'Expected generation or exact verified native registration differs; inspect and restage explicitly.')
    const oldId = current ? String(current.identity) : null, old = current ? object(current.revision) : undefined
    requireAtlas(request.operation !== 'register' || request.expectedRevision === null || request.expectedRevision === oldId, 'registration-conflict', 'Repeated registration must identify the current exact revision or explicitly request identity-based idempotence.')
    if (request.operation === 'register' && current) return { generation: base.generation, status: 'no-op', affected: [], recomputed: [], requalified: [], reused: base.values.terrainDerived ? 32 : 0, registration: current, metrics: { milliseconds: performance.now() - start, validation: context.validation as unknown as ObjectJson, bytesWritten: 0 } }
    requireAtlas(request.expectedRevision === oldId && (request.operation === 'register' || !!old), 'registration-conflict', 'Expected exact registration revision differs; supersession cannot be guessed.')
    const policy = base.values.terrainLifecycle as unknown as Policy | undefined, state = base.values.terrainDerived as unknown as DerivedState | undefined
    requireAtlas(!request.sourceNotice || policy && state, 'derivation-required', 'Source-scoped revision needs the existing qualified derivation context.')
    const nextPolicy = policy ? revise(policy, request.sourceNotice ? { notice: request.sourceNotice } : {}) : undefined
    if (request.sourceNotice?.bounds && nextPolicy) {
      const native = object(nextPolicy.sources[request.sourceNotice.key].native), bounds = native.bounds as number[], scoped = request.sourceNotice.bounds
      requireAtlas(scoped[0] >= bounds[0] && scoped[1] >= bounds[1] && scoped[2] <= bounds[2] && scoped[3] <= bounds[3], 'registration-support', 'Source notice bounds use EPSG:2056 and must lie within that exact retained DTM support.')
    }
    const metadata = { records: 0, bytes: 0 }, closure = nextPolicy && state ? affected(root, nextPolicy, state, metadata) : []
    const result: ObjectJson = { generation: base.generation, status: write ? 'staged-unpublished' : 'dry-run', affected: closure, recomputed: [], requalified: closure, reused: state ? 32 - closure.length : 0, reason: request.sourceNotice ? 'Source bytes/method/parameters unchanged: reuse verified samples/numerical values; requalify exact claims and downstream identities.' : 'Informational knowledge accountability only; no numerical/scientific input qualification change.', metrics: { milliseconds: performance.now() - start, validation: context.validation as unknown as ObjectJson, closureArtifactReads: metadata.records, artifactMetadataReads: metadata.records, artifactMetadataBytes: metadata.bytes, registrationReads: registrationReads as unknown as ObjectJson, baseMetadataReads: base.metrics.metadataRecords, baseMetadataBytes: base.metrics.metadataBytes, processingCellsRead: 0 } }
    if (!write) return result
    const writes = { recordsWritten: 0, bytesWritten: 0, recordsRead: 0, bytesRead: 0, bytesEncoded: 0 }
    const active = base.values.registrationLedger ? { ...object(base.values.registrationLedger.active) } : {}
    // Existing accepted worlds may adopt the ledger from their independently verified native contexts.
    for (const region of ['riffelhorn', 'tryfan'] as const) if (!active[region]) active[region] = immutable(root, 'registrations', revision(region === request.region && request.operation === 'register' ? request : template(nativeFor(base, region), region, base.generation, null)), writes)
    active[request.region] = request.operation === 'register' ? active[request.region] : immutable(root, 'registrations', revision(request, old, oldId ?? undefined), writes)
    const values = { ...base.values, registrationLedger: { schema: 'atlas-runtime-registration-ledger/v1', active } } as Record<string, ObjectJson>
    if (request.sourceNotice && nextPolicy) values.terrainLifecycle = nextPolicy as unknown as ObjectJson
    if (closure.length && state && nextPolicy) {
      const pairs = closure.filter(id => id.endsWith('|slope')).map(id => ({ slope: readArtifact(root, state.active[id], metadata), ratio: readArtifact(root, state.active[id.replace('|slope', '|area-ratio')], metadata) }))
      const processingStart = performance.now(), made = requalifyOutputs(nextPolicy, pairs), nextState = structuredClone(state), description = await context.terrainSamples([])
      for (const [id, body] of Object.entries(made)) nextState.active[id] = immutable(root, 'artifacts', body, writes)
      const execution = immutable(root, 'executions', { schema: 'atlas-runtime-terrain-requalification/v1', methodRevision: Object.values(made)[0].methodRevision, worker: description.environment, coordinator: { node: process.version, methodSourceSha256: object(readJson(path.join(import.meta.dirname, 'lifecycle-plan.json')).method).sha256 }, tasks: pairs.map(p => ({ id: p.slope.task, stride: object(p.slope.parameters).stride })), outputs: Object.fromEntries(Object.keys(made).map(id => [id, nextState.active[id]])), reusedInputs: Object.fromEntries(Object.keys(made).map(id => [id, state.active[id]])) }, writes)
      for (const id of Object.keys(made)) nextState.executions[id] = execution
      validateDerived(root, nextPolicy, nextState, metadata)
      values.terrainLifecycle = nextPolicy as unknown as ObjectJson; values.terrainDerived = nextState as unknown as ObjectJson
      object(result.metrics).requalificationMs = performance.now() - processingStart
    }
    if (options.failAt === 'afterArtifacts') process.exit(94)
    result.generation = stageObject(root, base, values, writes); result.registrationRevision = active[request.region]
    object(result.metrics).artifactMetadataReads = metadata.records; object(result.metrics).artifactMetadataBytes = metadata.bytes
    object(result.metrics).writes = writes as unknown as ObjectJson; object(result.metrics).milliseconds = performance.now() - start
    return result
  } finally { await context.close() }
}
export const planEvidenceUpdate = (config: RuntimeConfig, request: RegistrationRequest): Promise<ObjectJson> => update(config, request, false)
export const stageEvidenceUpdate = (config: RuntimeConfig, request: RegistrationRequest, options: { failAt?: 'afterArtifacts' } = {}): Promise<ObjectJson> => update(config, request, true, options)
