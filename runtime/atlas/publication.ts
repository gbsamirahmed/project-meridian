/** Owned local canonical writer. Filesystem root is the only publication authority. */
import fs from 'node:fs'
import path from 'node:path'
import { randomUUID } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { encode, sha } from '../../pilots/atlas/tryfan/identity.mjs'
import { object, publicPath, readJson, address } from './authority.ts'
import type { ObjectJson, Snapshot } from './authority.ts'
import { requireAtlas } from './errors.ts'
import type { RuntimeConfig } from './types.ts'
const marker = 'atlas-local-owned-world/v1'
export function real(p: string): string {
  const a = publicPath(p); if (fs.existsSync(a)) return fs.realpathSync(a)
  const parent = path.dirname(a)
  requireAtlas(parent !== a, 'path-unavailable', 'Configured local volume is unavailable; restore the explicit path.')
  return path.join(real(parent), path.basename(a))
}
export function inside(a: string, b: string): boolean { const r = path.relative(b, a); return !r || !r.startsWith('..') && !path.isAbsolute(r) }
export function owned(config: RuntimeConfig): string {
  const root = real(config.publicationRoot), data = real(config.dataRoot), repo = fileURLToPath(new URL('../../', import.meta.url))
  requireAtlas(!inside(root, data) && !inside(data, root) && !inside(root, repo) && !inside(repo, root), 'world-path', 'Writable proof world must be separate from retained public inputs and the repository.')
  requireAtlas(readJson(path.join(root, 'owned-world.json')).schema === marker, 'world-unowned', 'Initialize a separate runtime world; accepted publication stores are read-only.')
  return root
}
export function durable(file: string, bytes: string): void { const fd = fs.openSync(file, 'wx'); try { fs.writeFileSync(fd, bytes); fs.fsyncSync(fd) } finally { fs.closeSync(fd) } }
export interface WriteMetrics { recordsWritten: number; bytesWritten: number; recordsRead: number; bytesRead: number; bytesEncoded: number }
export function immutable(root: string, folder: string, value: unknown, metrics?: WriteMetrics): string {
  const bytes = encode(value), id = sha(bytes), dir = path.join(root, folder), file = path.join(dir, id + '.json'); fs.mkdirSync(dir, { recursive: true })
  if (metrics) metrics.bytesEncoded += Buffer.byteLength(bytes)
  if (fs.existsSync(file)) {
    const existing = fs.readFileSync(file, 'utf8')
    if (metrics) { metrics.recordsRead++; metrics.bytesRead += Buffer.byteLength(existing) }
    requireAtlas(existing === bytes, 'canonical-integrity', 'Immutable object identity collision/corruption.')
  }
  else {
    const pending = path.join(dir, randomUUID() + '.tmp'); durable(pending, bytes)
    if (metrics) { metrics.recordsWritten++; metrics.bytesWritten += Buffer.byteLength(bytes) }
    // Atomic no-overwrite installation on one local volume; crash debris is unreferenced.
    try { fs.linkSync(pending, file) } catch (e) {
      requireAtlas((e as NodeJS.ErrnoException).code === 'EEXIST' && fs.readFileSync(file, 'utf8') === bytes, 'canonical-integrity', 'Cannot install immutable object safely.')
    } finally { fs.unlinkSync(pending) }
  }
  return id
}
export function initializeWorld(config: RuntimeConfig, source: string, selected: string): ObjectJson {
  const target = real(config.publicationRoot), origin = real(source), data = real(config.dataRoot), repo = fileURLToPath(new URL('../../', import.meta.url))
  const catalogue = real(config.catalogueRoot)
  requireAtlas(!fs.existsSync(target) && ![origin, data, repo, catalogue].some(p => inside(target, p) || inside(p, target)), 'world-path', 'Use a new separate destination; existing worlds and retained sources are never overwritten. Keep the catalogue separate.')
  const staging = target + '.initializing-' + randomUUID(); fs.mkdirSync(path.dirname(target), { recursive: true })
  {
    fs.cpSync(origin, staging, { recursive: true, dereference: false, filter: p => {
      requireAtlas(!fs.lstatSync(p).isSymbolicLink(), 'world-path', 'Canonical source must not contain symlinks.')
      return !['writer.lock', 'owned-world.json'].includes(path.basename(p)) && !path.basename(p).endsWith('.tmp')
    } })
    const original = readJson(path.join(origin, 'current.json')); address(selected)
    fs.writeFileSync(path.join(staging, 'current.json'), encode({ ...original, generation: selected }))
    durable(path.join(staging, 'owned-world.json'), JSON.stringify({ schema: marker, originGeneration: selected }) + '\n')
    fs.renameSync(staging, target)
  } // Incomplete initialization remains separate and never current.
  return { root: target, generation: readJson(path.join(target, 'current.json')).generation }
}
export function stageObject(root: string, base: Snapshot, values: Record<string, ObjectJson>, metrics?: WriteMetrics): string {
  const members = Object.fromEntries(Object.entries(values).sort(([a], [b]) => a.localeCompare(b)).map(([kind, value]) => [kind, immutable(root, 'components', { schema: 'atlas-retained-component/v1', kind, value }, metrics)]))
  const reconstructed = { ...base.native, tryfanRegistration: values.tryfanRegistration, riffelhornRegistration: values.riffelhornRegistration, ...(values.terrainLifecycle ? { terrainLifecycle: values.terrainLifecycle, terrainDerived: values.terrainDerived } : {}), ...(values.registrationLedger ? { registrationLedger: values.registrationLedger } : {}), ...(values.exeRegistration ? { exeRegistration: values.exeRegistration } : {}) }
  return immutable(root, 'publications', { schema: 'atlas-component-publication/v1', ordinal: Number(base.publication.ordinal) + 1, predecessor: base.generation, legacyGeneration: sha(encode(reconstructed)), header: base.publication.header, members }, metrics)
}
export function member(root: string, previous: string | null, generation: string, depth = 0, metrics?: WriteMetrics): string {
  if (depth === 32) return immutable(root, 'membership', { schema: 'atlas-publication-membership/v1', depth, generation }, metrics)
  let children: ObjectJson = {}
  if (previous) {
    address(previous); const bytes = fs.readFileSync(path.join(root, 'membership', previous + '.json'))
    if (metrics) { metrics.recordsRead++; metrics.bytesRead += bytes.length }
    const node = object(JSON.parse(bytes.toString('utf8')))
    requireAtlas(sha(bytes) === previous && encode(node) === bytes.toString('utf8') && node.schema === 'atlas-publication-membership/v1' && node.depth === depth && Object.keys(node).sort().join(',') === 'children,depth,schema', 'membership-invalid', 'Cannot extend invalid committed membership.')
    children = { ...object(node.children) }
    requireAtlas(Object.entries(children).every(([k, v]) => /^[a-f0-9]{2}$/.test(k) && typeof v === 'string' && /^[a-f0-9]{64}$/.test(v)), 'membership-invalid', 'Invalid historical membership reference.')
  }
  const selector = generation.slice(depth * 2, depth * 2 + 2), old = children[selector]
  children[selector] = member(root, typeof old === 'string' ? old : null, generation, depth + 1, metrics)
  return immutable(root, 'membership', { schema: 'atlas-publication-membership/v1', depth, children }, metrics)
}
/** Tests may stop beforeRoot, leaving validated immutable objects uncommitted. */
export async function commit(config: RuntimeConfig, generation: string, validate: () => Promise<unknown>, failAt?: 'beforeRoot' | 'crashBeforeRoot'): Promise<ObjectJson> {
  const root = owned(config); address(generation); const lock = path.join(root, 'writer.lock')
  requireAtlas(!fs.existsSync(lock), 'writer-busy', 'Writer lock exists; inspect/recover after confirming its owner exited.')
  durable(lock, JSON.stringify({ pid: process.pid, operation: randomUUID() }) + '\n')
  try {
    const before = fs.readFileSync(path.join(root, 'current.json'), 'utf8'), active = object(JSON.parse(before)), candidate = readJson(path.join(root, 'publications', generation + '.json'))
    requireAtlas(candidate.predecessor === active.generation, 'publication-conflict', 'Stage is based on a different current generation; restage explicitly.')
    await validate()
    requireAtlas(fs.readFileSync(path.join(root, 'current.json'), 'utf8') === before, 'publication-conflict', 'Authoritative root changed during validation.')
    const writes: WriteMetrics = { recordsWritten: 0, bytesWritten: 0, recordsRead: 0, bytesRead: 0, bytesEncoded: 0 }
    const membership = member(root, String(active.membership), generation, 0, writes), pending = path.join(root, randomUUID() + '.tmp')
    durable(pending, encode({ schema: 'atlas-component-root/v1', generation, membership }))
    if (failAt === 'crashBeforeRoot') process.exit(91)
    requireAtlas(failAt !== 'beforeRoot', 'publication-interrupted', 'Interruption before root switch; prior generation remains current.')
    fs.renameSync(pending, path.join(root, 'current.json'))
    return { generation, membership, authority: 'filesystem-root', writes: { ...writes, rootBytesWritten: fs.statSync(path.join(root, 'current.json')).size } }
  } finally { fs.unlinkSync(lock) }
}
export function recover(config: RuntimeConfig): ObjectJson {
  const root = owned(config), lock = path.join(root, 'writer.lock')
  if (fs.existsSync(lock)) {
    const v = readJson(lock); requireAtlas(Number.isSafeInteger(v.pid) && Number(v.pid) > 0, 'recovery-invalid', 'Malformed lock requires explicit inspection.')
    let dead = false; try { process.kill(Number(v.pid), 0) } catch (e) { dead = (e as NodeJS.ErrnoException).code === 'ESRCH' }
    requireAtlas(dead, 'writer-busy', 'Lock owner is live or cannot be proven dead; recovery cannot steal it.')
    fs.unlinkSync(lock)
  }
  return { generation: readJson(path.join(root, 'current.json')).generation, status: 'root-unchanged; unreferenced staged objects retained' }
}
