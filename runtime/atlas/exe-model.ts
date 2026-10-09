/** Admission adapter over frozen Exe scientific definitions; no water inference. */
import * as accepted from '../../scripts/atlas/exe-water-query-proof/runtime.mjs'
import { object, publicPath } from './authority.ts'
import type { ObjectJson } from './authority.ts'
import type { RuntimeConfig, Json } from './types.ts'
import { NativeWorker } from './worker.ts'
import { digest } from './lifecycle-model.ts'
import { requireAtlas } from './errors.ts'

let definitions: ReturnType<typeof accepted.contract> | undefined
export async function exeNative(description: ObjectJson): Promise<ObjectJson> {
  const raw = object(description.raw), contract = await (definitions ??= accepted.contract())
  const state = accepted.build(raw, contract.fixtures)
  accepted.check(state, contract.validate)
  const native = state as unknown as ObjectJson, bundle = object(native.bundle)
  const collections = bundle.collections as ObjectJson[], resources = bundle.resources as ObjectJson[]
  const geometry = object(description.supports), records: ObjectJson[] = []
  const add = (identity: string, collection: ObjectJson, evidence: Json, evidenceClass: string, feature: string | null, temporal: Json, representation: string) => {
    const product = object(collection.product), resource = resources.find(r => object(r.ref).kind === 'product' && object(r.ref).id === product.id)!
    const support = object(geometry[identity])
    const source = object(raw.sources)[identity === 'exe:wfd' ? 'wfd.geojson' : identity === 'exe:rfo' ? 'rfo.geojson' : 'monthly-' + identity.split(':')[1] + '.tif']
    records.push({ identity, evidenceClass, feature, family: identity === 'exe:wfd' ? 'water-reference' : identity === 'exe:rfo' ? 'water-event' : 'water-monthly', representation, product: product.id, evidence,
      support, waterTime: temporal, rights: resource.rights,
      provenance: { source, product, resource, preparation: source, method: native.method, parameters: object(evidence).request ?? { selection: 'Native source/product selector; no raster resampling or geometry repair' }, selector: identity, physicalChangeInferred: false, limitation: 'Selected source-native evidence; no current water, depth, flow, tide or physical absence inference.' } })
  }
  for (const [identity, cid, claimId, feature] of [['exe:wfd', 'collection:wfd', 'claim:wfd:GB510804505600:0', 'wfd:GB510804505600'], ['exe:rfo', 'collection:rfo', 'claim:rfo:31383:0', 'rfo:31383']]) {
    const c = collections.find(c => c.id === cid)!, claim = (c.claims as ObjectJson[]).find(c => c.id === claimId)!
    requireAtlas(claim, 'registration-invalid', 'Accepted Exe feature is unavailable.')
    const context = { ...object(c.context), ...object(claim.context) }
    add(identity, c, { claim, context }, 'source', feature, context.time, 'vector')
  }
  for (const month of ['2024-03', '2024-09']) {
    const c = collections.find(c => c.id === 'collection:' + month)!, context = object(c.context)
    add('exe:' + month + ':product', c, { binding: c.binding, context, templates: c.claims }, 'source', null, context.time, 'raster')
    for (const kind of ['point', 'support']) {
      const q = accepted.MATRIX.queries.find((q: { id: string }) => q.id === 'P1-' + kind + '-' + month)!
      const answer = accepted.resolveQuery(state, raw, q) as unknown as ObjectJson
      add('exe:' + month + ':' + kind, c, { ...answer, context, interpretation: kind === 'support' ? 'Derived composition of selected native cell codes; not fractional cover or a homogeneous physical observation.' : 'Source-native containing-cell classification; not independent ground truth.' }, kind === 'support' ? 'derived' : 'source', null, context.time, kind === 'support' ? 'native-cell-summary' : 'raster')
    }
  }
  records.sort((a, b) => String(a.identity).localeCompare(String(b.identity)))
  return { schema: 'atlas-runtime-exe-native/v1', region: 'exe', support: { crs: 'EPSG:27700', bounds: accepted.MATRIX.bounds }, records,
    sources: raw.sources, rights: raw.rights, grid: raw.grid, coordinateOperation: raw.coordinateOperation, matrixSha256: raw.matrixSha256,
    retainedDirectory: raw.directorySha256, method: native.method, physicalChangeInferred: false }
}
export async function describeExe(config: RuntimeConfig): Promise<{ native: ObjectJson; metrics: ObjectJson }> {
  const worker = new NativeWorker(publicPath(config.python))
  try {
    const description = object(await worker.call('describe-exe', { dataRoot: publicPath(config.dataRoot) }))
    return { native: await exeNative(description), metrics: object(description.metrics) }
  } finally { await worker.close() }
}
export async function verifyExe(config: RuntimeConfig, native: ObjectJson): Promise<ObjectJson> {
  const verified = await describeExe(config)
  requireAtlas(digest(verified.native) === digest(native), 'registration-native', 'Exe source, classification, support, time, rights or lineage differs from verified retained evidence.')
  return verified.metrics
}
