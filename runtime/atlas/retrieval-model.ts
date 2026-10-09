/** Canonical identity/qualification projection, not a spatial query engine. */
import { object } from './authority.ts'
import type { ObjectJson, Snapshot } from './authority.ts'
import { digest, readArtifact, projection, validateDerived } from './lifecycle-model.ts'
import type { Policy, DerivedState } from './lifecycle-model.ts'
import { validateRegistrations } from './registration-model.ts'
import { requireAtlas } from './errors.ts'
import type { EvidenceAnswer, EvidenceRecord, EvidenceRelationship, Json } from './types.ts'

export function retrievalView(snapshot: Snapshot, root: string) {
  const metrics = { records: 0, bytes: 0 }, registrations = validateRegistrations(snapshot, root, metrics)
  const regions = ['tryfan', 'riffelhorn', ...(snapshot.values.exeRegistration ? ['exe'] : [])]
  const knowledge = Object.fromEntries(regions.map(region => [region, registrations[region] ? { revision: registrations[region].identity, acceptedAt: object(object(registrations[region].revision).knowledgeTime).acceptedAt } : null]))
  const nativeRevisions = { tryfan: snapshot.values.tryfanRegistration.acceptedGeneration, riffelhorn: snapshot.values.riffelhornRegistration.preparationRevision, ...(snapshot.values.exeRegistration ? { exe: digest(snapshot.values.exeRegistration) } : {}) }
  const bodies: Record<string, ObjectJson> = {}, executions: Record<string, ObjectJson> = {}, selectors: ObjectJson[] = [], relationships: EvidenceRelationship[] = []
  const policy = snapshot.values.terrainLifecycle as unknown as Policy | undefined, state = snapshot.values.terrainDerived as unknown as DerivedState | undefined
  if (policy && state) {
    const runs = validateDerived(root, policy, state, metrics)
    for (const [id, revision] of Object.entries(state.active)) {
      const body = readArtifact(root, revision, metrics), run = runs.get(state.executions[id])!
      bodies[id] = body; executions[id] = run
    }
    const nativeIds = new Set((snapshot.values.riffelhornRegistration.records as ObjectJson[]).map(r => r.identity))
    for (const [id, body] of Object.entries(bodies)) {
      const slope = body.property === 'slope' ? body : bodies[id.replace('|area-ratio', '|slope')]
      const uses = object(slope.sampling).uses as ObjectJson[], cells = uses.flatMap(u => (u.cells as ObjectJson[]).map(c => [c.x, c.y]))
      selectors.push({ key: 'derived:' + id, identity: id, revision: state.active[id], region: 'riffelhorn', family: body.property === 'slope' ? 'terrain-slope' : 'planar-area-ratio', representation: 'local-scalar', product: body.methodRevision, point: object(body.support).point, cells })
      if (body.property === 'slope') {
        for (const use of uses) {
          const key = String(use.key), source = policy.sources[key]
          requireAtlas(source && nativeIds.has(key), 'relationship-invalid', 'Exact consumed source is absent from registered native evidence.')
          const edge = { from: 'riffelhorn:' + key, to: 'derived:' + id, kind: 'consumes-qualified-source' as const, fromRevision: String(object(source.artifact).sha256), toRevision: state.active[id], via: { identity: digest({ ...use, qualification: projection(policy, use) }), scope: use.scope, sourceArtifact: source.artifact, preparedRevision: nativeRevisions.riffelhorn, underlyingEdges: ['source-to-qualified-use', 'qualified-use-to-slope'] } }
          requireAtlas((body.inputs as ObjectJson[]).some(i => i.kind === 'qualified-input-use' && i.identity === edge.via.identity), 'relationship-invalid', 'Source relationship must retain the exact canonical qualified-use input.')
          relationships.push({ identity: digest(edge), ...edge } as EvidenceRelationship)
        }
      } else {
        const parent = String(slope.id), edge = { from: 'derived:' + parent, to: 'derived:' + id, kind: 'derived-input' as const, fromRevision: state.active[parent], toRevision: state.active[id], via: null }
        requireAtlas((body.inputs as ObjectJson[]).some(i => i.identity === edge.fromRevision), 'relationship-invalid', 'Derived dependency must reference the exact slope revision.')
        relationships.push({ identity: digest(edge), ...edge })
      }
    }
  }
  selectors.sort((a, b) => String(a.key).localeCompare(String(b.key))); relationships.sort((a, b) => a.identity.localeCompare(b.identity))
  if (snapshot.values.exeRegistration) for (const row of snapshot.values.exeRegistration.records as ObjectJson[]) if (row.evidenceClass === 'derived') {
    const source = 'exe:' + String(row.identity).replace(':support', ':product'), target = 'exe:' + row.identity
    const edge = { from: source, to: target, kind: 'consumes-qualified-source' as const, fromRevision: String(nativeRevisions.exe), toRevision: String(nativeRevisions.exe), via: object(row.provenance) }
    relationships.push({ identity: digest(edge), ...edge })
  }
  relationships.sort((a, b) => a.identity.localeCompare(b.identity))
  const worker = { selectors, relationships, knowledge, nativeRevisions }
  return { worker, bodies, executions, registrations, policy, metrics }
}
export function evidenceAnswer(snapshot: Snapshot, view: ReturnType<typeof retrievalView>, selected: ObjectJson, relatedTo?: import('./types.ts').EvidenceQuery['relatedTo']): EvidenceAnswer {
  const documents: Record<string, Json> = {}, put = (value: Json): string => { const id = digest(value); documents[id] = value; return id }
  const regions = Object.fromEntries(['tryfan', 'riffelhorn', ...(snapshot.values.exeRegistration ? ['exe'] : [])].map(region => {
    const value = view.registrations[region], nativeRef = put(snapshot.values[region + 'Registration'])
    const revision = value ? Object.fromEntries(Object.entries(object(value.revision)).filter(([k]) => k !== 'native')) : null
    return [region, { nativeRef, knowledgeRef: revision ? put({ identity: value.identity, ...revision, nativeRef }) : null }]
  }))
  const results: EvidenceRecord[] = (selected.results as ObjectJson[]).map(row => {
    const derived = row.evidenceClass === 'derived' && row.region !== 'exe', id = String(row.identity), body = derived ? view.bodies[id] : object(row.evidence), region = String(row.region), key = String(row.key)
    const qualification = derived ? body.qualification : { native: body.qualification ?? body.nativeMetadata ?? (row.region === 'exe' ? body.context : null) ?? null, sourceNotices: view.policy?.notes.filter(n => n.key === id) ?? [], physicalChangeInferred: false }
    const provenance = derived ? { inputs: body.inputs, method: body.method, methodRevision: body.methodRevision, parameters: body.parameters, executionRef: put(view.executions[id]), regionalNativeRef: regions[region].nativeRef } : row.provenance
    return { key, identity: id, revision: String(row.revision), evidenceClass: row.evidenceClass as 'source' | 'derived', region, family: String(row.family), representation: String(row.representation), componentIdentity: snapshot.members[derived ? 'terrainDerived' : region + 'Registration'], evidenceRef: put(body), qualificationRef: put(qualification as Json), provenanceRef: put(provenance as Json), rightsRef: put((derived ? object(body.qualification).rights : row.rights) as Json), support: (derived ? body.support : row.support) as Json, temporal: row.temporal as Json, knowledgeRef: regions[region].knowledgeRef, relationshipRefs: view.worker.relationships.filter(e => e.from === key || e.to === key).map(e => e.identity) }
  })
  const wanted = new Set(results.flatMap(r => r.relationshipRefs).concat(selected.traversed as string[]))
  return { schema: 'atlas-qualified-retrieval/v1', generation: snapshot.generation, members: { ...snapshot.members }, results, relationships: view.worker.relationships.filter(e => wanted.has(e.identity)), documents, regions, traversal: relatedTo ? { selection: relatedTo, relationshipRefs: selected.traversed as string[] } : null, gap: results.length ? null : { reason: 'no-matching-qualified-evidence', physicalAbsenceInferred: false }, metrics: { ...(selected.metrics as Record<string, number>), artifactMetadataReads: view.metrics.records, artifactMetadataBytes: view.metrics.bytes, canonicalMetadataReads: snapshot.metrics.metadataRecords, canonicalMetadataBytes: snapshot.metrics.metadataBytes } }
}
