import {loadFixtures, unpackOutcome, difference, ConformanceError} from './fixtures.mjs';
import {flags, configuration, referenceSessions, invoke, verifyReferenceSources, failure} from './reference.mjs';

async function run() {
  const args = flags(process.argv.slice(2), ['config', 'case']);
  const config = configuration(args.config), fixtures = loadFixtures();
  verifyReferenceSources(fixtures.manifest);
  const cases = fixtures.cases.filter(c => !args.case || c.id === args.case);
  if (!cases.length) throw new ConformanceError('Requested fixture case does not exist.');
  const sessions = referenceSessions(config, fixtures.manifest.publications);
  let passed = 0, failed = 0, expectedErrors = 0, comparisons = 0;
  try {
    for (const c of cases) {
      const context = await sessions.get(c.publication), metadata = sessions.metadata[c.publication];
      if (metadata.fingerprint !== fixtures.manifest.publications[c.publication].fingerprint) throw new ConformanceError(`Authoritative closure differs for pin: ${c.publication}`);
      const expected = unpackOutcome(fixtures.expected[c.id], fixtures.documents), mismatches = [];
      for (const method of ['retrieve', 'scanEvidence']) {
        const actual = await invoke(context, c.query, method), at = difference(expected, actual);
        comparisons++;
        if (at) mismatches.push({method, at, actualOutcome: actual.kind, actualCode: actual.code ?? null});
      }
      if (mismatches.length) failed++; else passed++;
      if (expected.kind === 'error') expectedErrors++;
      console.log(JSON.stringify({case: c.id, generation: context.generation, status: mismatches.length ? 'FAIL' : 'PASS',
        expectedOutcome: expected.kind, expectedCode: expected.code ?? null, unsupportedRequest: c.tags.includes('unsupported'), mismatches}));
    }
    console.log(JSON.stringify({summary: {selected: cases.length, passed, failed, skipped: 0, expectedErrors, comparisons},
      publications: Object.fromEntries(Object.entries(sessions.metadata).map(([k,v]) => [k,{generation: v.generation, records: v.catalogue.records,
        fullValidationMs: v.validation.milliseconds, catalogueBuildMs: v.catalogue.milliseconds ?? null}]))}));
    if (failed) process.exitCode = 1;
  } finally { await sessions.close(); }
}
run().catch(failure);
