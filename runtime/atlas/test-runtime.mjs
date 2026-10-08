import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { openAtlas } from './index.ts'
import { resolveAuthoritative } from './authority.ts'
import { sha, encode } from '../../pilots/atlas/tryfan/identity.mjs'

const repository = path.resolve(import.meta.dirname, '../..')
const baseline = JSON.parse(fs.readFileSync(path.join(repository, 'docs/research/atlas-local-runtime-baseline.json')))
const dataRoot = path.resolve(repository, '../meridian-data')
const python = path.join(dataRoot, 'earth-lab/.venv/Scripts/python.exe')
const temp = fs.mkdtempSync(path.resolve(repository, '../../Codex/atlas-local-runtime-v1/test-'))
const config = { dataRoot, python, publicationRoot: baseline.publicationRoot, catalogueRoot: path.join(temp, 'catalogue'), generation: baseline.history[0] }
const matrix = JSON.parse(fs.readFileSync(path.join(repository, 'scripts/atlas/riffelhorn-retrieval/matrix.json'))).cases.filter(c => !Object.hasOwn(c.query, 'associated'))
const prepared = path.join(dataRoot, 'derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1/357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb')
const logical = ({ metrics: _, ...answer }) => answer
function cli(command, extra = [], cfg = config) {
  return spawnSync(process.execPath, [path.join(import.meta.dirname, 'cli.ts'), ...command, '--data-root', cfg.dataRoot, '--publication-root', cfg.publicationRoot, '--catalogue', cfg.catalogueRoot, '--python', python, '--generation', cfg.generation, '--json', ...extra], { encoding: 'utf8', maxBuffer: 100 * 1024 * 1024 })
}
function nativeQuery(q) { return { region: 'riffelhorn', ...q, ...(('point' in q || 'area' in q) ? { crs: q.crs ?? 'EPSG:2056' } : {}) } }
function epoch() { return path.join(config.catalogueRoot, 'epochs', JSON.parse(fs.readFileSync(path.join(config.catalogueRoot, 'current.json'))).epoch) }
function copyStore(name) { const destination = path.join(temp, name); fs.cpSync(config.publicationRoot, destination, { recursive: true }); return destination }

test('retained runtime end-to-end, independent native oracle and recovery', async t => {
  const context = await openAtlas(config)
  try {
    await t.test('full validation and explicit pin without a catalogue', async () => {
      assert.equal(context.generation, baseline.history[0]); assert.equal(context.validation.ancestryTraversals, 0)
      assert.equal(Object.keys(context.members).length, 7); assert(context.validation.payloadBytesHashed > 170_000_000)
      await assert.rejects(context.query({}), /Catalogue/)
    })
    await t.test('build and verify actual 49-record SQLite catalogue', async () => {
      const built = await context.buildCatalogue(); assert.equal(built.records, 49); assert(built.bytes < 150_000)
      assert.equal((await context.verifyCatalogue()).records, 49)
    })
    const oracleProcess = spawnSync(python, [path.join(repository, 'scripts/atlas/multi-region/native-worker.py'), '--root', prepared, '--oracle'], { encoding: 'utf8', maxBuffer: 100 * 1024 * 1024, env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONDONTWRITEBYTECODE: '1', PROJ_NETWORK: 'OFF' } })
    assert.equal(oracleProcess.status, 0, oracleProcess.stderr); const oracle = JSON.parse(oracleProcess.stdout)
    for (const c of matrix) await t.test('indexed/scan/independent native qualifications: ' + c.id, async () => {
      const q = nativeQuery(c.query), answer = await context.query(q), scan = await context.scanReference(q)
      assert.deepEqual(logical(answer), logical(scan)); assert.deepEqual(answer.results.map(r => r.evidence), oracle[c.id].results)
      assert.equal(answer.generation, config.generation); assert(answer.results.every(r => r.componentIdentity === context.members.riffelhornRegistration))
      assert(answer.results.every(r => r.provenance && r.support && r.temporal && r.rights))
    })
    await t.test('Tryfan canonical source product identity and half-open core support', async () => {
      const canonical = resolveAuthoritative(config), families = canonical.native.catalogue.families
      const answer = await context.query({ region: 'tryfan' })
      assert.deepEqual(answer.results.map(r => r.identity).sort(), families.map(f => f.product).sort())
      for (const r of answer.results) {
        const f = families.find(f => f.product === r.identity)
        assert.deepEqual(r.evidence.nativeMetadata, f.nativeMetadata); assert.deepEqual(r.evidence.qualification, f.qualification)
        assert.equal(r.componentIdentity, context.members.tryfanRegistration)
        assert.equal((await context.query({ identity: r.identity })).results.length, 1)
      }
      const [x0,y0,x1,y1] = canonical.native.core.bounds
      assert.equal((await context.query({ region: 'tryfan', point: [x0,y0], crs: 'EPSG:27700' })).results.length, 5)
      assert.equal((await context.query({ region: 'tryfan', point: [x1,y1], crs: 'EPSG:27700' })).results.length, 0)
    })
    await t.test('explicit unknown differs from calendar-year matching; absence is qualified', async () => {
      const known = await context.query({ region: 'tryfan', time: { role: 'evidence-epoch', start: 2021, end: 2021 } })
      assert.equal(known.results.length, 1); assert.equal(known.results[0].evidence.family, 'worldcover')
      const unknown = await context.query({ region: 'tryfan', time: { role: 'evidence-epoch', unknown: true } })
      assert.equal(unknown.results.length, 3)
      assert.equal((await context.query({ feature: 'not-retained' })).gap.physicalAbsenceInferred, false)
    })
    const negatives = [null, { sql: 'SELECT *' }, { point: [0,0] }, { region: 'riffelhorn', point: [0,0], crs: 'unknown' }, { region: 'riffelhorn', area: [1,1,0,0], crs: 'EPSG:2056' }, { time: { role: 'evidence-epoch', instant: '2021-01-01' } }, { time: { role: 'evidence-epoch', start: 2022, end: 2021 } }, { families: ['fabricated'] }, { region: 'unknown' }]
    for (let i = 0; i < negatives.length; i++) await t.test('unsupported predicate rejects ' + i, () => assert.rejects(context.query(negatives[i])))
    const query = { region: 'riffelhorn', feature: 'glaciers:683' }, reference = logical(await context.query(query))
    for (const failAt of ['beforeInstall', 'beforePointer']) await t.test('failed rebuild preserves current catalogue: ' + failAt, async () => {
      const before = fs.readFileSync(path.join(config.catalogueRoot, 'current.json'))
      await assert.rejects(context.buildCatalogue({ failAt }), /interruption/)
      assert.deepEqual(fs.readFileSync(path.join(config.catalogueRoot, 'current.json')), before)
      assert.deepEqual(logical(await context.query(query)), reference)
    })
    await t.test('deleted catalogue fails explicitly and clean rebuild preserves results', async () => {
      fs.unlinkSync(path.join(epoch(), 'index.sqlite')); await assert.rejects(context.query(query), /Catalogue missing/)
      await context.buildCatalogue(); assert.deepEqual(logical(await context.query(query)), reference)
    })
    await t.test('corrupt catalogue rejected and rebuild restores results', async () => {
      fs.appendFileSync(path.join(epoch(), 'index.sqlite'), 'corrupted'); await assert.rejects(context.query(query), /Catalogue altered/)
      await context.buildCatalogue(); assert.deepEqual(logical(await context.query(query)), reference)
    })
    await t.test('incompatible schema and wrong generation rejected', async () => {
      const file = path.join(epoch(), 'seal.json'), original = fs.readFileSync(file), seal = JSON.parse(original)
      fs.writeFileSync(file, JSON.stringify({ ...seal, schemaVersion: 999 })); await assert.rejects(context.verifyCatalogue(), /schema/)
      fs.writeFileSync(file, JSON.stringify({ ...seal, generation: baseline.history[2] })); await assert.rejects(context.query(query), /another generation/)
      fs.writeFileSync(file, original); await context.verifyCatalogue()
    })
    await t.test('resealed malformed selector cannot override canonical qualification', async () => {
      const file = path.join(epoch(), 'index.sqlite'), sealFile = path.join(epoch(), 'seal.json'), original = fs.readFileSync(file), sealBytes = fs.readFileSync(sealFile)
      const mutation = spawnSync(python, ['-c', 'import sqlite3,sys;d=sqlite3.connect(sys.argv[1]);d.execute("UPDATE temporal SET year=9999 WHERE known=1");d.commit();d.close()', file], { encoding: 'utf8' })
      assert.equal(mutation.status, 0, mutation.stderr)
      fs.writeFileSync(sealFile, JSON.stringify({ ...JSON.parse(sealBytes), sha256: sha(fs.readFileSync(file)) }))
      await assert.rejects(context.query(query), /temporal selectors differ/)
      fs.writeFileSync(file, original); fs.writeFileSync(sealFile, sealBytes)
    })
    await t.test('restart through documented CLI reproduces full qualifications', async () => {
      const result = cli(['query'], ['--query', JSON.stringify(query)]); assert.equal(result.status, 0, result.stderr)
      assert.deepEqual(logical(JSON.parse(result.stdout)), reference)
    })
    await t.test('new selected generation detects old catalogue without silent fallback', async () => {
      const newer = await openAtlas({ ...config, generation: baseline.history[2] })
      try { await assert.rejects(newer.query(query), /another generation/); assert.equal(newer.generation, baseline.history[2]) } finally { await newer.close() }
    })
    await t.test('active-root advancement cannot move an existing pin or make its catalogue current', async () => {
      const root = copyStore('advancement'), activeFile = path.join(root, 'current.json'), active = JSON.parse(fs.readFileSync(activeFile))
      fs.writeFileSync(activeFile, encode({ ...active, generation: baseline.history[0] }))
      const cfg = { ...config, publicationRoot: root, catalogueRoot: path.join(temp, 'advancement-catalogue') }; delete cfg.generation
      const pinned = await openAtlas(cfg)
      try {
        await pinned.buildCatalogue(); const before = logical(await pinned.query(query))
        fs.writeFileSync(path.join(root, 'unpublished-revision.json'), '{"status":"staged"}')
        assert.deepEqual(logical(await pinned.query(query)), before)
        fs.writeFileSync(activeFile, encode(active))
        assert.deepEqual(logical(await pinned.query(query)), before)
        const current = await openAtlas(cfg)
        try { assert.equal(current.generation, baseline.history[2]); await assert.rejects(current.query(query), /another generation/) } finally { await current.close() }
      } finally { await pinned.close() }
    })
    await t.test('unpublished exact generation rejected', () => assert.rejects(openAtlas({ ...config, generation: '0'.repeat(64) })))
    for (const mode of ['missing', 'tampered', 'malformed-root', 'incomplete-membership']) await t.test('authoritative failure never repaired: ' + mode, async () => {
      const root = copyStore(mode)
      if (mode === 'missing') fs.unlinkSync(path.join(root, 'components', context.members.catalogue + '.json'))
      if (mode === 'tampered') fs.appendFileSync(path.join(root, 'components', context.members.catalogue + '.json'), ' ')
      if (mode === 'malformed-root') fs.writeFileSync(path.join(root, 'current.json'), '{}')
      if (mode === 'incomplete-membership') { const active = JSON.parse(fs.readFileSync(path.join(root, 'current.json'))); fs.unlinkSync(path.join(root, 'membership', active.membership + '.json')) }
      const before = fs.readFileSync(path.join(root, 'current.json'))
      await assert.rejects(openAtlas({ ...config, publicationRoot: root })); assert.deepEqual(fs.readFileSync(path.join(root, 'current.json')), before)
    })
    await t.test('missing authoritative source payload fails full validation', () => assert.rejects(openAtlas({ ...config, dataRoot: path.join(temp, 'absent-data') })))
    await t.test('catalogue cannot be placed within canonical roots or repository', async () => {
      for (const catalogueRoot of [dataRoot, repository, config.publicationRoot]) await assert.rejects(openAtlas({ ...config, catalogueRoot }), /outside canonical/)
    })
    await t.test('private paths rejected before reads', () => assert.rejects(openAtlas({ ...config, dataRoot: path.join(temp, 'meridian-private') })))
    await t.test('CLI rejects invalid query with nonzero status and safe diagnostic', () => {
      const result = cli(['query'], ['--query', '{invalid']); assert.equal(result.status, 1); assert.match(result.stderr, /query-invalid/); assert(!result.stderr.includes(' at '))
    })
    await t.test('all historical pins replay after fresh process', () => {
      for (const generation of baseline.history) {
        const cfg = { ...config, generation, catalogueRoot: path.join(temp, generation) }
        const build = cli(['catalogue', 'build'], [], cfg); assert.equal(build.status, 0, build.stderr)
        const first = cli(['query'], ['--query', JSON.stringify(query)], cfg), second = cli(['query'], ['--query', JSON.stringify(query)], cfg)
        assert.equal(first.status, 0, first.stderr); assert.equal(second.status, 0, second.stderr)
        const a = JSON.parse(first.stdout); assert.equal(a.generation, generation); assert.deepEqual(logical(a), logical(JSON.parse(second.stdout)))
        assert.deepEqual(a.results.map(r => r.evidence), reference.results.map(r => r.evidence))
      }
    })
    await t.test('accepted selected store files unchanged after runtime and fault tests', () => {
      for (const [file, hash] of Object.entries(baseline.storeHashes)) assert.equal(sha(fs.readFileSync(path.join(config.publicationRoot, file))), hash)
    })
  } finally { await context.close() }
})
