import { openAtlas } from './index.ts'
import { diagnostic, requireAtlas } from './errors.ts'
import type { Query, QueryAnswer, RuntimeConfig } from './types.ts'
import { createWorld, stageDerivation, inspectLifecycle, validateStage, publishStage, recoverWorld } from './lifecycle.ts'
import type { Change } from './lifecycle.ts'

async function main(): Promise<void> {
  const args = process.argv.slice(2), command = args.shift()
  if (!command || command === '--help') {
    console.log('Atlas local runtime: validate | catalogue build/verify | query | derived | world init/recover | derive stage/inspect | stage validate/publish\nRequired: --data-root PATH --publication-root PATH --catalogue PATH --python PATH\nOptional: --generation SHA256 --json\nquery: --query JSON; derived: optional --query JSON\nworld init: --source-publication PATH; derive: optional --change JSON; stage: --stage SHA256\nCanonical writes require a separate initialized runtime world. See runtime/atlas/README.md.')
    return
  }
  const actions: Record<string, string[]> = { catalogue: ['build', 'verify'], world: ['init', 'recover'], derive: ['stage', 'inspect'], stage: ['validate', 'publish'] }
  const action = actions[command] ? args.shift() : undefined
  requireAtlas(['validate', 'query', 'derived', ...Object.keys(actions)].includes(command) && (!actions[command] || actions[command].includes(action ?? '')), 'command-invalid', 'Unknown command/action; see --help.')
  const flags: Record<string, string> = {}; let json = false
  while (args.length) {
    const key = args.shift()!
    if (key === '--json') { json = true; continue }
    requireAtlas(['--data-root', '--publication-root', '--catalogue', '--python', '--generation', '--query', '--change', '--source-publication', '--stage'].includes(key) && !flags[key], 'argument-invalid', 'Unknown or duplicate flag; see --help.')
    const value = args.shift(); requireAtlas(value && !value.startsWith('--'), 'argument-invalid', 'Flag requires a value; see --help.'); flags[key] = value
  }
  for (const key of ['--data-root', '--publication-root', '--catalogue', '--python']) requireAtlas(flags[key], 'argument-invalid', 'Missing ' + key + '; use explicit public paths.')
  requireAtlas(command === 'query' ? !!flags['--query'] : command === 'derived' || !flags['--query'], 'argument-invalid', '--query is required for query and optional for derived only.')
  requireAtlas((command === 'world' && action === 'init') === !!flags['--source-publication'] && (command === 'stage') === !!flags['--stage'] && (command === 'derive' || !flags['--change']), 'argument-invalid', 'Source, stage and change flags must match their commands.')
  let query: Query = {}
  if (flags['--query']) {
    try { query = JSON.parse(flags['--query']) as Query } catch { requireAtlas(false, 'query-invalid', 'Query must be valid JSON; see documented examples.') }
  }
  const config: RuntimeConfig = { dataRoot: flags['--data-root'], publicationRoot: flags['--publication-root'], catalogueRoot: flags['--catalogue'], python: flags['--python'], generation: flags['--generation'] }
  if (['world', 'derive', 'stage'].includes(command)) {
    let change: Change = {}
    try { change = JSON.parse(flags['--change'] ?? '{}') as Change } catch { requireAtlas(false, 'change-invalid', 'Change must be valid bounded JSON.') }
    const result = command === 'world' ? action === 'init' ? await createWorld(config, flags['--source-publication']) : recoverWorld(config) : command === 'derive' ? action === 'stage' ? await stageDerivation(config, change) : await inspectLifecycle(config, change) : action === 'validate' ? await validateStage(config, flags['--stage']) : await publishStage(config, flags['--stage'])
    console.log(JSON.stringify(result, null, json ? undefined : 2)); return
  }
  const context = await openAtlas(config)
  try {
    const result = command === 'validate' ? { generation: context.generation, members: context.members, validation: context.validation, native: context.nativeSetup } : command === 'derived' ? context.derived(query as never) : command === 'catalogue' ? action === 'build' ? await context.buildCatalogue() : await context.verifyCatalogue() : await context.query(query)
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
