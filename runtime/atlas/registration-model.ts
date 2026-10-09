/** Immutable knowledge registrations over independently verified native evidence. */
import { object, address } from './authority.ts'
import type { ObjectJson, Snapshot } from './authority.ts'
import { digest, readArtifact } from './lifecycle-model.ts'
import type { Notice, ArtifactMetrics } from './lifecycle-model.ts'
import { requireAtlas } from './errors.ts'

export interface RegistrationRequest {
  schema: 'atlas-runtime-registration-request/v1'
  operation: 'register' | 'knowledge' | 'source-qualification'
  region: 'tryfan' | 'riffelhorn' | 'exe'
  scope?: 'exeReferences'
  expectedGeneration: string | null
  expectedRevision: string | null
  native: ObjectJson
  explanation: string
  sourceNotice?: Notice
}
export function validateRequest(input: RegistrationRequest): void {
  requireAtlas(input && typeof input === 'object' && !Array.isArray(input) && Object.keys(input).every(k => ['schema', 'operation', 'region', 'scope', 'expectedGeneration', 'expectedRevision', 'native', 'explanation', 'sourceNotice'].includes(k)), 'registration-request', 'Use the documented versioned registration request; scientific overrides are unsupported.')
  requireAtlas(input.scope === undefined || input.scope === 'exeReferences' && input.region === 'exe' && input.operation !== 'source-qualification', 'registration-request', 'Only the additive Exe reference scope is supported; actual region remains Exe.')
  requireAtlas(input.schema === 'atlas-runtime-registration-request/v1' && ['register', 'knowledge', 'source-qualification'].includes(input.operation) && ['tryfan', 'riffelhorn', 'exe'].includes(input.region), 'registration-request', 'Unsupported operation/region; new observations, product replacement and method changes need separate qualified admission.')
  object(input.native)
  for (const k of ['expectedGeneration', 'expectedRevision'] as const) if (input[k] !== null) address(input[k])
  requireAtlas(typeof input.explanation === 'string' && input.explanation.trim().length > 0 && input.explanation.length <= 1000, 'registration-request', 'An explicit accountability explanation is required.')
  requireAtlas((input.operation === 'source-qualification') === (input.sourceNotice !== undefined) && (input.operation !== 'source-qualification' || input.region === 'riffelhorn'), 'registration-request', 'Only a declared Riffelhorn source qualification may affect the Swiss derivation.')
}
export function nativeFor(snapshot: Snapshot, region: string): ObjectJson {
  return snapshot.values[region + 'Registration']
}
export function validateRegistrations(snapshot: Snapshot, root: string, metrics?: ArtifactMetrics): Record<string, ObjectJson> {
  const ledger = snapshot.values.registrationLedger
  if (!ledger) return {}
  const expected = ['riffelhorn', 'tryfan', ...(snapshot.values.exeRegistration ? ['exe'] : []), ...(snapshot.values.exeReferencesRegistration ? ['exeReferences'] : [])].sort().join(',')
  requireAtlas(ledger.schema === 'atlas-runtime-registration-ledger/v1' && Object.keys(ledger).sort().join(',') === 'active,schema' && Object.keys(object(ledger.active)).sort().join(',') === expected, 'registration-invalid', 'Exact regional/scoped registration references for every admitted population are required.')
  const current: Record<string, ObjectJson> = {}
  for (const [region, ref] of Object.entries(object(ledger.active))) {
    let id = String(ref), child: ObjectJson | undefined
    const seen = new Set<string>()
    while (id) {
      requireAtlas(!seen.has(id), 'registration-cycle', 'Registration supersession cycle is invalid.'); seen.add(id)
      const v = readArtifact(root, id, metrics, 'registrations')
      const scoped = region === 'exeReferences'
      requireAtlas(Object.keys(v).sort().join(',') === (scoped ? 'explanation,knowledgeTime,native,nativeIdentity,operation,physicalChangeInferred,region,schema,scope,sequence,sourceNotice,supersedes' : 'explanation,knowledgeTime,native,nativeIdentity,operation,physicalChangeInferred,region,schema,sequence,sourceNotice,supersedes') && v.schema === 'atlas-runtime-registration-revision/v1' && v.region === (scoped ? 'exe' : region) && (!scoped || v.scope === region) && v.physicalChangeInferred === false && Number.isSafeInteger(v.sequence) && Number(v.sequence) >= 0, 'registration-invalid', 'Malformed immutable registration revision.')
      validateRequest({ schema: 'atlas-runtime-registration-request/v1', operation: v.operation as RegistrationRequest['operation'], region: (scoped ? 'exe' : region) as RegistrationRequest['region'], ...(scoped ? { scope: 'exeReferences' as const } : {}), expectedGeneration: null, expectedRevision: null, native: object(v.native), explanation: String(v.explanation), ...(v.sourceNotice === null ? {} : { sourceNotice: v.sourceNotice as unknown as Notice }) })
      const time = object(v.knowledgeTime)
      requireAtlas(Object.keys(time).sort().join(',') === 'acceptedAt,basis' && time.basis === 'runtime acceptance clock; not physical observation or source publication' && typeof time.acceptedAt === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(time.acceptedAt) && new Date(time.acceptedAt).toISOString() === time.acceptedAt, 'registration-time', 'Invalid knowledge acceptance clock; native physical time must remain separate.')
      requireAtlas(v.nativeIdentity === digest(v.native) && digest(v.native) === digest(nativeFor(snapshot, region)), 'registration-native', 'Registration cannot alter source/native support, time, provenance, rights or prepared identities.')
      if (child) requireAtlas(Number(child.sequence) === Number(v.sequence) + 1 && String(object(child.knowledgeTime).acceptedAt) > String(time.acceptedAt), 'registration-order', 'Supersession and knowledge acceptance ordering differ.')
      else current[region] = { identity: id, revision: v }
      if (v.sourceNotice !== null) {
        const policy = object(snapshot.values.terrainLifecycle), notes = policy.notes as unknown[]
        requireAtlas(Array.isArray(notes) && notes.some(n => digest(n) === digest(v.sourceNotice)), 'registration-stale', 'Source qualification is not propagated into current derived context.')
      }
      requireAtlas(v.sequence === 0 ? v.operation === 'register' && v.supersedes === null : v.operation !== 'register' && typeof v.supersedes === 'string', 'registration-order', 'Initial registration and subsequent revisions have distinct identities.')
      child = v; id = v.supersedes === null ? '' : String(v.supersedes)
    }
  }
  return current
}
export function validateRegistrationTransition(before: Snapshot, after: Snapshot, root: string, metrics?: ArtifactMetrics): void {
  requireAtlas(!before.values.registrationLedger || after.values.registrationLedger, 'registration-incomplete', 'Publication cannot discard accepted registration history.')
  const prior = validateRegistrations(before, root, metrics), next = validateRegistrations(after, root, metrics)
  requireAtlas(Object.keys(prior).every(region => next[region]), 'registration-incomplete', 'Publication cannot discard a retained regional registration.')
  for (const [region, value] of Object.entries(next)) {
    if (prior[region]?.identity === value.identity) continue
    const revision = object(value.revision)
    requireAtlas(prior[region] ? revision.supersedes === prior[region].identity && Number(revision.sequence) === Number(object(prior[region].revision).sequence) + 1 : revision.supersedes === null && revision.sequence === 0, 'registration-conflict', 'A publication must directly supersede its exact current registration, not fork or rewrite knowledge.')
  }
}
