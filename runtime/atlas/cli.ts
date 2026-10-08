import { openAtlas } from './index.ts'
import { diagnostic, requireAtlas } from './errors.ts'
import type { Query, QueryAnswer, RuntimeConfig } from './types.ts'

async function main(): Promise<void> {
  const args = process.argv.slice(2), command = args.shift()
  if (!command || command === '--help') {
    console.log('Atlas local runtime: validate | catalogue build | catalogue verify | query\nRequired: --data-root PATH --publication-root PATH --catalogue PATH --python PATH\nOptional: --generation SHA256 --json\nQuery: --query JSON (documented finite predicates; no arbitrary SQL)')
    return
  }
  const action = command === 'catalogue' ? args.shift() : undefined
  requireAtlas(['validate', 'catalogue', 'query'].includes(command) && (command !== 'catalogue' || ['build', 'verify'].includes(action ?? '')), 'command-invalid', 'Use validate, catalogue build, catalogue verify or query; see --help.')
  const flags: Record<string, string> = {}; let json = false
  while (args.length) {
    const key = args.shift()!
    if (key === '--json') { json = true; continue }
    requireAtlas(['--data-root', '--publication-root', '--catalogue', '--python', '--generation', '--query'].includes(key) && !flags[key], 'argument-invalid', 'Unknown or duplicate flag; see --help.')
    const value = args.shift(); requireAtlas(value && !value.startsWith('--'), 'argument-invalid', 'Flag requires a value; see --help.'); flags[key] = value
  }
  for (const key of ['--data-root', '--publication-root', '--catalogue', '--python']) requireAtlas(flags[key], 'argument-invalid', 'Missing ' + key + '; use explicit public paths.')
  requireAtlas(command === 'query' ? !!flags['--query'] : !flags['--query'], 'argument-invalid', '--query JSON is required only for query.')
  let query: Query = {}
  if (command === 'query') {
    try { query = JSON.parse(flags['--query']) as Query } catch { requireAtlas(false, 'query-invalid', 'Query must be valid JSON; see documented examples.') }
  }
  const config: RuntimeConfig = { dataRoot: flags['--data-root'], publicationRoot: flags['--publication-root'], catalogueRoot: flags['--catalogue'], python: flags['--python'], generation: flags['--generation'] }
  const context = await openAtlas(config)
  try {
    const result = command === 'validate' ? { generation: context.generation, members: context.members, validation: context.validation, native: context.nativeSetup } : command === 'catalogue' ? action === 'build' ? await context.buildCatalogue() : await context.verifyCatalogue() : await context.query(query)
    if (json) console.log(JSON.stringify(result))
    else {
      console.log('Pinned generation: ' + context.generation)
      if (command === 'query') {
        const answer = result as QueryAnswer
        console.log('Qualified results: ' + answer.results.length)
        for (const r of answer.results) console.log(r.region + ' ' + r.identity)
        console.log('Use --json to inspect native evidence, support, time, lineage and rights.')
      } else console.log(JSON.stringify(result, null, 2))
    }
  } finally { await context.close() }
}
main().catch(error => { console.error(JSON.stringify(diagnostic(error))); process.exitCode = 1 })
