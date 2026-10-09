import { openAtlas } from './index.ts'
import { diagnostic, requireAtlas } from './errors.ts'
import type { Query, QueryAnswer, EvidenceQuery, EvidenceAnswer, RuntimeConfig } from './types.ts'
import { createWorld, stageDerivation, inspectLifecycle, validateStage, publishStage, recoverWorld } from './lifecycle.ts'
import type { Change } from './lifecycle.ts'
import fs from 'node:fs'
import { publicPath } from './authority.ts'
import { inspectEvidence, registerEvidence, planEvidenceUpdate, stageEvidenceUpdate } from './registration.ts'
import type { RegistrationRequest } from './registration.ts'

async function main(): Promise<void> {
  const args = process.argv.slice(2), command = args.shift()
  if (!command || command === '--help') {
    console.log('Atlas local runtime: validate | catalogue build/verify | query | retrieve | derived | world init/recover | derive stage/inspect | stage validate/publish | evidence inspect/register/revise | update plan/validate/publish\nRequired: --data-root PATH --publication-root PATH --catalogue PATH --python PATH\nOptional: --generation SHA256 --json\nquery/retrieve: --query JSON; catalogue: optional --qualified; derived: optional --query JSON\nworld init: --source-publication PATH; derive: optional --change JSON; stage/update validate/publish: --stage SHA256\nevidence inspect/register: --tryfan-root PATH --prepared-root PATH OR --family exe-water; register/revise/update plan: --request PATH\nCanonical writes require a separate owned runtime world. See runtime/atlas/README.md.')
    return
  }
  const actions: Record<string, string[]> = { catalogue: ['build', 'verify'], world: ['init', 'recover'], derive: ['stage', 'inspect'], stage: ['validate', 'publish'], evidence: ['inspect', 'register', 'revise'], update: ['plan', 'validate', 'publish'] }
  const action = actions[command] ? args.shift() : undefined
  requireAtlas(['validate', 'query', 'retrieve', 'derived', ...Object.keys(actions)].includes(command) && (!actions[command] || actions[command].includes(action ?? '')), 'command-invalid', 'Unknown command/action; see --help.')
  const flags: Record<string, string> = {}; let json = false, qualified = false
  while (args.length) {
    const key = args.shift()!
    if (key === '--json') { json = true; continue }
    if (key === '--qualified') { requireAtlas(!qualified && command === 'catalogue', 'argument-invalid', '--qualified applies once to catalogue build/verify only.'); qualified = true; continue }
    requireAtlas(['--data-root', '--publication-root', '--catalogue', '--python', '--generation', '--query', '--change', '--source-publication', '--stage', '--request', '--tryfan-root', '--prepared-root', '--family'].includes(key) && !flags[key], 'argument-invalid', 'Unknown or duplicate flag; see --help.')
    const value = args.shift(); requireAtlas(value && !value.startsWith('--'), 'argument-invalid', 'Flag requires a value; see --help.'); flags[key] = value
  }
  for (const key of ['--data-root', '--publication-root', '--catalogue', '--python']) requireAtlas(flags[key], 'argument-invalid', 'Missing ' + key + '; use explicit public paths.')
  requireAtlas(['query', 'retrieve'].includes(command) ? !!flags['--query'] : command === 'derived' || !flags['--query'], 'argument-invalid', '--query is required for query/retrieve and optional for derived only.')
  const isStage = command === 'stage' || command === 'update' && action !== 'plan', needsRequest = command === 'evidence' && action !== 'inspect' || command === 'update' && action === 'plan'
  requireAtlas((command === 'world' && action === 'init') === !!flags['--source-publication'] && isStage === !!flags['--stage'] && (command === 'derive' || !flags['--change']) && needsRequest === !!flags['--request'], 'argument-invalid', 'Source, stage, request and change flags must match their commands.')
  requireAtlas((!!flags['--tryfan-root'] === !!flags['--prepared-root']) && (command === 'evidence' && action !== 'revise' || !flags['--tryfan-root']), 'argument-invalid', 'Both retained input roots apply only to evidence inspect/register.')
  let query: Query = {}
  if (flags['--query']) {
    try { query = JSON.parse(flags['--query']) as Query } catch { requireAtlas(false, 'query-invalid', 'Query must be valid JSON; see documented examples.') }
  }
  const config: RuntimeConfig = { dataRoot: flags['--data-root'], publicationRoot: flags['--publication-root'], catalogueRoot: flags['--catalogue'], python: flags['--python'], generation: flags['--generation'] }
  if (command === 'evidence' || command === 'update') {
    let request: RegistrationRequest | undefined
    if (needsRequest) {
      try { request = JSON.parse(fs.readFileSync(publicPath(flags['--request']), 'utf8')) as RegistrationRequest } catch { requireAtlas(false, 'registration-request', 'Request must be a readable versioned JSON file; use evidence inspect for a verified template.') }
    }
    requireAtlas(!flags['--family'] || flags['--family'] === 'exe-water' && command === 'evidence' && action !== 'revise' && !flags['--tryfan-root'], 'argument-invalid', 'Only --family exe-water is supported for evidence inspect/register; existing world required.')
    const inputs = flags['--family'] ? { family: 'exe-water' as const } : flags['--tryfan-root'] ? { tryfanRoot: flags['--tryfan-root'], preparedRoot: flags['--prepared-root'] } : undefined
    requireAtlas(!(command === 'evidence' && action === 'register') || inputs, 'argument-invalid', 'Register requires retained input roots or --family exe-water in an existing world.')
    const result = command === 'evidence' ? action === 'inspect' ? await inspectEvidence(config, inputs) : action === 'register' ? await registerEvidence(config, inputs!, request!) : await stageEvidenceUpdate(config, request!) : action === 'plan' ? await planEvidenceUpdate(config, request!) : action === 'validate' ? await validateStage(config, flags['--stage']) : await publishStage(config, flags['--stage'])
    console.log(JSON.stringify(result, null, json ? undefined : 2)); return
  }
  if (['world', 'derive', 'stage'].includes(command)) {
    let change: Change = {}
    try { change = JSON.parse(flags['--change'] ?? '{}') as Change } catch { requireAtlas(false, 'change-invalid', 'Change must be valid bounded JSON.') }
    const result = command === 'world' ? action === 'init' ? await createWorld(config, flags['--source-publication']) : recoverWorld(config) : command === 'derive' ? action === 'stage' ? await stageDerivation(config, change) : await inspectLifecycle(config, change) : action === 'validate' ? await validateStage(config, flags['--stage']) : await publishStage(config, flags['--stage'])
    console.log(JSON.stringify(result, null, json ? undefined : 2)); return
  }
  const context = await openAtlas(config)
  try {
    const result = command === 'validate' ? { generation: context.generation, members: context.members, validation: context.validation, native: context.nativeSetup } : command === 'retrieve' ? await context.retrieve(query as EvidenceQuery) : command === 'derived' ? context.derived(query as never) : command === 'catalogue' ? action === 'build' ? await context.buildCatalogue({ qualified }) : await context.verifyCatalogue({ qualified }) : await context.query(query)
    if (json) console.log(JSON.stringify(result))
    else {
      console.log('Pinned generation: ' + context.generation)
      if (command === 'query' || command === 'retrieve') {
        const answer = result as QueryAnswer | EvidenceAnswer
        console.log('Qualified results: ' + answer.results.length)
        for (const r of answer.results) console.log(r.region + ' ' + r.identity)
        console.log('Use --json to inspect native evidence, support, time, lineage and rights.')
      } else console.log(JSON.stringify(result, null, 2))
    }
  } finally { await context.close() }
}
main().catch(error => { console.error(JSON.stringify(diagnostic(error))); process.exitCode = 1 })
