/** Additive qualified inventory/reference admission over accepted Exe semantics. */
import * as accepted from '../../scripts/atlas/exe-water-query-proof/runtime.mjs'
import { object, publicPath } from './authority.ts'
import type { ObjectJson } from './authority.ts'
import type { RuntimeConfig } from './types.ts'
import { NativeWorker } from './worker.ts'
import { digest } from './lifecycle-model.ts'
import { requireAtlas } from './errors.ts'

let definitions: ReturnType<typeof accepted.contract> | undefined
export async function describeReferences(config: RuntimeConfig): Promise<{ native: ObjectJson; metrics: ObjectJson }> {
  const worker = new NativeWorker(publicPath(config.python))
  try {
    const description = object(await worker.call('describe-references', { dataRoot: publicPath(config.dataRoot) }))
    const raw = object(description.raw), contract = await (definitions ??= accepted.contract())
    const state = accepted.build(raw, contract.fixtures); accepted.check(state, contract.validate)
    const bundle = object((state as unknown as ObjectJson).bundle), records: ObjectJson[] = []
    for (const kind of ['phi', 'flood']) {
      const collection = (bundle.collections as ObjectJson[]).find(c => c.id === 'collection:' + kind)!
      const product = object(collection.product), resource = (bundle.resources as ObjectJson[]).find(r => object(r.ref).kind === 'product' && object(r.ref).id === product.id)!
      const supports = object(object(description.supports)[kind]), source = object(raw.sources)[kind + '.geojson']
      for (const claim of collection.claims as ObjectJson[]) {
        const fields = object(object(claim.native).fields), support = supports[String(fields.featureId)]
        if (!support) continue
        const context = { ...object(collection.context), ...object(claim.context) }
        const code = kind === 'phi' ? String(object(object(claim.native).term).id).slice(4) : String(fields.flood_zone)
        const definitionIds = new Set([String(object(object(claim.native).property).id), String(object(object(claim.native).term).id), ...(context.conditions as ObjectJson[] ?? []).map(c => String(object(c.definition).id))])
        const meanings = (bundle.definitions as ObjectJson[]).filter(d => definitionIds.has(String(d.id)))
        records.push({ identity: 'exe:' + claim.id, evidenceClass: 'source', feature: kind + ':' + object(claim.feature).id,
          family: kind === 'phi' ? 'priority-habitat' : 'planning-flood-zone', representation: 'vector', product: product.id,
          nativeClassification: code, evidence: { claim, context, definitions: meanings, scientificRole: kind === 'phi' ? 'mapped ecological inventory' : 'administrative planning scenario reference; not a legal designation', temporalApplicability: { survey: kind === 'phi' ? 'unknown' : 'not-applicable-to-scenario', effective: kind === 'flood' ? 'unknown-reference-validity; no legal effect inferred' : 'not-applicable-to-habitat-inventory' } },
          support, waterTime: [], referenceTime: [...context.time as ObjectJson[], ...(kind === 'flood' ? [{ role: 'effective', extent: { kind: 'unknown', reason: 'No administrative effective or current legal-validity interval is established by retained evidence.' } }] : [])], rights: resource.rights,
          provenance: { source, product, resource, preparation: source, method: (state as unknown as ObjectJson).method,
            parameters: { selection: 'Positive-area intersection with any of six original Exe probe squares; original geometry retained', component: code }, selector: claim.id,
            physicalChangeInferred: false, limitation: 'Source-native inventory/scenario claim; no current habitat, species, legal restriction, physical absence or fusion inference.' } })
      }
    }
    records.sort((a, b) => String(a.identity).localeCompare(String(b.identity)))
    requireAtlas(records.length === 52 && records.filter(r => r.family === 'priority-habitat').length === 15 && new Set(records.map(r => r.identity)).size === 52, 'registration-invalid', 'Frozen 15 habitat/37 planning claim population differs.')
    return { native: { schema: 'atlas-runtime-exe-references/v1', region: 'exe', scope: 'exeReferences', support: { crs: 'EPSG:27700', bounds: accepted.MATRIX.bounds }, records,
      sources: raw.sources, retainedDirectory: raw.directorySha256, rights: raw.rights, method: (state as unknown as ObjectJson).method, physicalChangeInferred: false }, metrics: object(description.metrics) }
  } finally { await worker.close() }
}
export async function verifyReferences(config: RuntimeConfig, native: ObjectJson): Promise<ObjectJson> {
  const verified = await describeReferences(config)
  requireAtlas(digest(verified.native) === digest(native), 'registration-native', 'Habitat/planning source, code, support, dates, rights or lineage differs from accepted retained evidence.')
  return verified.metrics
}
