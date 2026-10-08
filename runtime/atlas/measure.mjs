// Bounded real-publication measurement; all generated catalogues stay external.
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { openAtlas } from './index.ts'
import { encode, sha } from '../../pilots/atlas/tryfan/identity.mjs'
const repo = path.resolve(import.meta.dirname, '../..')
const b = JSON.parse(fs.readFileSync(path.join(repo, 'docs/research/atlas-local-runtime-baseline.json')))
const dataRoot = path.resolve(repo, '../meridian-data'), python = path.join(dataRoot, 'earth-lab/.venv/Scripts/python.exe')
const outputRoot = path.resolve(repo, '../../Codex/atlas-local-runtime-v1')
const matrix = JSON.parse(fs.readFileSync(path.join(repo, 'scripts/atlas/riffelhorn-retrieval/matrix.json'))).cases.filter(c => !('associated' in c.query))
const samples = [], queries = [], replay = []; let comparisons = 0
const logical = ({ metrics: _, ...answer }) => answer
for (let repeat = 0; repeat < 3; repeat++) {
  const config = { dataRoot, python, publicationRoot: b.publicationRoot, catalogueRoot: path.join(outputRoot, 'measured-' + repeat), generation: b.history[0] }
  const start = performance.now(), ctx = await openAtlas(config), openMs = performance.now() - start
  try {
    const built = await ctx.buildCatalogue(), rebuilt = await ctx.buildCatalogue()
    for (const c of matrix) {
      const q = { region: 'riffelhorn', ...c.query, ...(('point' in c.query || 'area' in c.query) ? { crs: c.query.crs ?? 'EPSG:2056' } : {}) }
      const begin = performance.now(), a = await ctx.query(q), indexedMs = performance.now() - begin
      const scanStart = performance.now(), s = await ctx.scanReference(q), scanMs = performance.now() - scanStart
      if (encode(logical(a)) !== encode(logical(s))) throw Error('Oracle disagreement: ' + c.id)
      comparisons++; queries.push({ repeat, case: c.id, resultCount: a.results.length, indexedMs, scanMs, indexed: a.metrics, scan: s.metrics })
    }
    const q = { region: 'riffelhorn', feature: 'glaciers:683' }, answer = logical(await ctx.query(q))
    const freshStart = performance.now(), fresh = spawnSync(process.execPath, [path.join(import.meta.dirname, 'cli.ts'), 'query', '--data-root', dataRoot, '--publication-root', b.publicationRoot, '--catalogue', config.catalogueRoot, '--python', python, '--generation', config.generation, '--query', JSON.stringify(q), '--json'], { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 })
    if (fresh.status !== 0 || encode(answer) !== encode(logical(JSON.parse(fresh.stdout)))) throw Error('Fresh process replay disagreement')
    samples.push({ repeat, openMs, validation: ctx.validation, native: ctx.nativeSetup, built, rebuilt, freshProcessFullOpenAndQueryMs: performance.now() - freshStart, parentRssBytes: process.memoryUsage().rss })
  } finally { await ctx.close() }
}
for (const generation of b.history) {
  const config = { dataRoot, python, publicationRoot: b.publicationRoot, catalogueRoot: path.join(outputRoot, 'history-' + generation), generation }, start = performance.now(), ctx = await openAtlas(config)
  try {
    await ctx.buildCatalogue(); const answer = await ctx.query({ region: 'riffelhorn', feature: 'glaciers:683' })
    replay.push({ generation, elapsedMs: performance.now() - start, component: answer.results[0].componentIdentity, evidenceSha256: sha(encode(answer.results[0].evidence)), ancestryTraversals: answer.metrics.ancestryTraversals })
  } finally { await ctx.close() }
}
function spread(values) { const a = [...values].sort((a,b) => a-b); return { median: a[Math.floor(a.length/2)], min: a[0], max: a.at(-1), samples: values } }
const results = { schema: 'atlas-local-runtime-results/v1', startingCheckpoint: b.startingCheckpoint, planSha256: b.planSha256, environment: { node: process.version, platform: process.platform, python, dataRoot, outputRoot, warmFilesystem: true, physicalIO: 'Logical counters only; filesystem cache not flushed; Python/native peak RSS not isolated.' }, comparisons, agreement: true, population: { records: 49, riffelhorn: 44, tryfanSourceProductDescriptors: 5, components: 7, generations: 3 }, samples, queries, replay, summary: { openMs: spread(samples.map(s => s.openMs)), catalogueBuildMs: spread(samples.map(s => s.built.milliseconds)), catalogueRebuildMs: spread(samples.map(s => s.rebuilt.milliseconds)), freshProcessFullOpenAndQueryMs: spread(samples.map(s => s.freshProcessFullOpenAndQueryMs)), catalogueBytes: samples[0].built.bytes, parentRssBytes: spread(samples.map(s => s.parentRssBytes)) }, boundary: 'Actual retained native bodies and current hash validation, not synthetic/global scale; runtime scan shares accepted predicates, test-runtime additionally compares the independent accepted native scan.' }
fs.writeFileSync(path.join(repo, 'docs/research/atlas-local-runtime-results.json'), JSON.stringify(results, null, 2) + '\n')
console.log(JSON.stringify({ comparisons, summary: results.summary, replay }, null, 2))
