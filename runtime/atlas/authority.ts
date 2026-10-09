import fs from 'node:fs'
import path from 'node:path'
import { encode, sha } from '../../pilots/atlas/tryfan/identity.mjs'
import { canonicalGeneration } from '../../pilots/atlas/tryfan/generations.mjs'
import { verifyArtifacts } from '../../pilots/atlas/tryfan/catalogue.mjs'
import { verifyDelivery } from '../../pilots/atlas/tryfan/delivery-schema.mjs'
import { requireAtlas } from './errors.ts'
import type { Json, RuntimeConfig, ValidationMetrics } from './types.ts'

export type ObjectJson = { [key: string]: Json }
const HEX = /^[a-f0-9]{64}$/
export const KINDS = ['catalogue', 'knowledge', 'locators', 'riffelhornRegistration', 'serving', 'tryfanRegistration', 'understanding']
export const LIFECYCLE_KINDS = [...KINDS, 'terrainLifecycle', 'terrainDerived'].sort()
export const REGISTRATION_KINDS = [KINDS, LIFECYCLE_KINDS].map(k => [...k, 'registrationLedger'].sort().join(','))
export function object(v: unknown): ObjectJson {
  requireAtlas(v && typeof v === 'object' && !Array.isArray(v), 'canonical-malformed', 'Expected structured canonical metadata.')
  return v as ObjectJson
}
export function address(v: unknown): asserts v is string {
  requireAtlas(typeof v === 'string' && HEX.test(v), 'canonical-identity', 'Expected an exact SHA256 identity, not a locator.')
}
export function publicPath(p: string): string {
  requireAtlas(typeof p === 'string' && p.length && !p.toLowerCase().includes('meridian-private'), 'path-invalid', 'Explicit public data paths are required; private paths are excluded.')
  const absolute = path.resolve(p)
  if (fs.existsSync(absolute)) requireAtlas(!fs.realpathSync(absolute).toLowerCase().includes('meridian-private'), 'path-invalid', 'Private path targets are excluded.')
  return absolute
}
export function readJson(file: string): ObjectJson { return object(JSON.parse(fs.readFileSync(file, 'utf8'))) }
export interface Snapshot {
  generation: string
  publication: ObjectJson
  members: Record<string, string>
  values: Record<string, ObjectJson>
  native: ObjectJson
  fingerprint: string
  metrics: ValidationMetrics
}
/** Read-only closure adapter: accepted base plus the finite runtime lifecycle extension.
 * committed=false is stage inspection only; serving always uses committed eligibility. */
export function resolveAuthoritative(config: RuntimeConfig, generation?: string, committed = true): Snapshot {
  const start = performance.now(), root = publicPath(config.publicationRoot)
  let metadataRecords = 0, metadataBytes = 0
  function readObject(folder: string, id: string): ObjectJson {
    address(id)
    const bytes = fs.readFileSync(path.join(root, folder, id + '.json'))
    metadataRecords++; metadataBytes += bytes.length
    requireAtlas(sha(bytes) === id, 'canonical-integrity', 'Canonical object missing or altered; restore authoritative evidence, not the catalogue.')
    const v = object(JSON.parse(bytes.toString('utf8')))
    requireAtlas(encode(v) === bytes.toString('utf8'), 'canonical-malformed', 'Canonical object encoding differs.')
    return v
  }
  const active = readJson(path.join(root, 'current.json'))
  requireAtlas(Object.keys(active).sort().join(',') === 'generation,membership,schema' && active.schema === 'atlas-component-root/v1', 'root-invalid', 'Invalid authoritative publication root.')
  address(active.generation); address(active.membership)
  const selected = generation ?? config.generation ?? active.generation
  address(selected)
  let nodeId = active.membership
  for (let depth = 0; committed && depth <= 32; depth++) {
    const node = readObject('membership', nodeId)
    requireAtlas(node.schema === 'atlas-publication-membership/v1' && node.depth === depth, 'closure-invalid', 'Invalid committed membership path.')
    if (depth === 32) {
      requireAtlas(Object.keys(node).sort().join(',') === 'depth,generation,schema' && node.generation === selected, 'generation-unpublished', 'Requested generation is not committed. Never fall back to current.')
    } else {
      requireAtlas(Object.keys(node).sort().join(',') === 'children,depth,schema', 'closure-invalid', 'Invalid membership fields.')
      const children = object(node.children)
      requireAtlas(Object.entries(children).every(([k, v]) => /^[a-f0-9]{2}$/.test(k) && typeof v === 'string' && HEX.test(v)), 'closure-invalid', 'Invalid membership references.')
      const next = children[selected.slice(depth * 2, depth * 2 + 2)]
      requireAtlas(next, 'generation-unpublished', 'Requested generation is not committed. Never fall back to current.')
      address(next); nodeId = next
    }
  }
  const publication = readObject('publications', selected), members = object(publication.members)
  requireAtlas(publication.schema === 'atlas-component-publication/v1' && Object.keys(publication).sort().join(',') === 'header,legacyGeneration,members,ordinal,predecessor,schema', 'publication-format', 'Unsupported publication format; use a complete accepted or runtime lifecycle world.')
  const kinds = Object.keys(members).sort()
  requireAtlas(Number.isSafeInteger(publication.ordinal) && Number(publication.ordinal) > 0 && [KINDS.join(','), LIFECYCLE_KINDS.join(','), ...REGISTRATION_KINDS, ...REGISTRATION_KINDS.map(k => [...k.split(','), 'exeRegistration'].sort().join(','))].includes(kinds.join(',')), 'closure-invalid', 'Complete accepted or runtime registration/lifecycle membership required.')
  address(publication.legacyGeneration)
  if (publication.predecessor !== null) address(publication.predecessor)
  const values: Record<string, ObjectJson> = {}, refs: Record<string, string> = {}
  for (const kind of kinds) {
    const id = members[kind]; address(id); refs[kind] = id
    const component = readObject('components', id)
    requireAtlas(component.schema === 'atlas-retained-component/v1' && component.kind === kind && Object.keys(component).sort().join(',') === 'kind,schema,value', 'closure-invalid', 'Component kind/schema mismatch.')
    values[kind] = object(component.value)
  }
  const { tryfanRegistration, riffelhornRegistration } = values
  const science = Object.fromEntries(Object.entries(values).filter(([kind]) => KINDS.includes(kind) && !['locators', 'tryfanRegistration', 'riffelhornRegistration'].includes(kind)))
  const native = object(canonicalGeneration({ ...object(publication.header), ...science }))
  requireAtlas(sha(encode(native)) === '5f2c1b1f25c45ddea7e640f8c286a6caec5dc61aa55e8f678062bdc5704fca06', 'registration-invalid', 'This adapter requires the unchanged accepted Tryfan scientific state.')
  const reconstructed = { ...native, tryfanRegistration, riffelhornRegistration, ...(values.terrainLifecycle ? { terrainLifecycle: values.terrainLifecycle, terrainDerived: values.terrainDerived } : {}), ...(values.registrationLedger ? { registrationLedger: values.registrationLedger } : {}), ...(values.exeRegistration ? { exeRegistration: values.exeRegistration } : {}) }
  requireAtlas(sha(encode(reconstructed)) === publication.legacyGeneration, 'closure-invalid', 'Exact publication closure reconstruction differs.')
  const expectedTry = { schema: 'atlas-regional-evidence-registration/v1', region: 'tryfan', acceptedGeneration: sha(encode(native)), support: { crs: object(native.core).crs, bounds: object(native.core).bounds }, catalogueIdentity: sha(encode(native.catalogue)), knowledgeIdentity: sha(encode(native.knowledge)), understandingIdentity: sha(encode(native.understanding)), nativeFamilies: (object(native.catalogue).families as ObjectJson[]).map(f => f.id), administrative: tryfanRegistration.administrative }
  requireAtlas(encode(expectedTry) === encode(tryfanRegistration), 'registration-invalid', 'Tryfan registration/source identity differs.')
  for (const reg of [tryfanRegistration, riffelhornRegistration]) {
    const admin = object(reg.administrative)
    requireAtlas(Object.keys(admin).sort().join(',') === 'notice,revision', 'registration-invalid', 'Invalid administrative revision fields.')
    const notice = admin.revision === 0 ? 'Initial retained regional registration; no new physical observation' : 'Administrative accountability notice revision; no evidence or physical change'
    requireAtlas(typeof admin.revision === 'number' && [0, 1].includes(admin.revision) && admin.notice === notice, 'registration-invalid', 'Unsupported administrative revision.')
  }
  return { generation: selected, publication, members: refs, values, native, fingerprint: sha(encode({ schema: 'atlas-local-catalogue/v1', generation: selected, members: refs })), metrics: { milliseconds: performance.now() - start, metadataRecords, metadataBytes, payloadHashOperations: 0, payloadBytesHashed: 0, ancestryTraversals: 0, parentRssBytes: process.memoryUsage().rss } }
}
export function validateNativeFiles(snapshot: Snapshot, config: RuntimeConfig): void {
  const start = performance.now()
  const verified = verifyArtifacts(snapshot.native.catalogue, snapshot.values.locators, publicPath(config.dataRoot))
  verifyDelivery(publicPath(config.publicationRoot), snapshot.native.serving)
  const assets = (object(snapshot.native.serving).assets as ObjectJson[]).filter(a => object(a.origin).kind === 'materialized')
  snapshot.metrics.payloadHashOperations += verified.artifacts + assets.length
  snapshot.metrics.payloadBytesHashed += verified.bytes + assets.reduce((n, a) => n + Number(a.bytes), 0)
  snapshot.metrics.milliseconds += performance.now() - start
}
