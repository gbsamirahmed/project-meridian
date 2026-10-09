import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {publications, referenceCases} from './cases.mjs';
import {encodeFixture, hash, packOutcome, difference, ConformanceError} from './fixtures.mjs';
import {flags, configuration, assertExternal, referenceSessions, invoke, repository, failure} from './reference.mjs';

async function generate() {
  const args = flags(process.argv.slice(2), ['config', 'output']), config = configuration(args.config);
  if (!args.output) throw new ConformanceError('Required new external --output directory is missing.');
  const output = path.resolve(args.output);
  assertExternal(fs.realpathSync(path.dirname(output)), config);
  assertExternal(output, config);
  if (fs.existsSync(output)) throw new ConformanceError('Output must not exist; published fixtures are never overwritten.');
  const requests = referenceCases(), expected = {}, documents = {}, sessions = referenceSessions(config, publications);
  try {
    for (const c of requests.cases) {
      const x = await sessions.get(c.publication);
      const scan = await invoke(x, c.query, 'scanEvidence'), indexed = await invoke(x, c.query, 'retrieve');
      const mismatch = difference(scan, indexed);
      if (mismatch) throw new ConformanceError(`Reference disagreement: ${c.id} at ${mismatch}`);
      expected[c.id] = packOutcome(scan, documents);
    }
    const files = {
      'requests.json': requests,
      'expected.json': {schema: 'meridian-atlas-read-expected/v1', cases: expected},
      'documents.json': {schema: 'meridian-atlas-read-documents/v1', documents},
    };
    const referenceFiles = ['runtime/atlas/index.ts', 'runtime/atlas/types.ts', 'runtime/atlas/worker.py',
      'runtime/atlas/retrieval-model.ts', 'runtime/atlas/retrieval_query.py', 'runtime/atlas/retrieval-cases.mjs',
      'scripts/atlas/riffelhorn-retrieval/query.py', 'scripts/atlas/riffelhorn-retrieval/matrix.json',
      'scripts/atlas/riffelhorn-fixture/prepare.py', 'docs/research/atlas-regional-expansion-fixture.json'];
    const versions = spawnSync(config.python, ['-c', 'import sys,json,sqlite3,numpy,rasterio,shapely,pyproj;print(json.dumps(dict(python=sys.version.split()[0],sqlite=sqlite3.sqlite_version,numpy=numpy.__version__,rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__,shapely=shapely.__version__,pyproj=pyproj.__version__,proj=pyproj.proj_version_str)))'],
      {encoding: 'utf8', env: {...process.env, PYTHONDONTWRITEBYTECODE: '1'}});
    if (versions.status !== 0) throw new ConformanceError('Cannot record the required GIS tool versions.');
    const prepared = JSON.parse(fs.readFileSync(path.join(config.dataRoot, 'derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1/357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb/input-manifest.json'), 'utf8'));
    const manifest = {
      schema: 'meridian-atlas-read-fixtures/v1', profile: 'meridian-atlas-read-contract/v1',
      referenceCheckpoint: '984e7d2b8ebe3b3fe5a358ba7087af5a19d5f282', caseCount: requests.cases.length,
      referenceOperation: 'AtlasContext.scanEvidence; AtlasContext.retrieve cross-check',
      command: 'node scripts/atlas/read-conformance/generate.mjs --config LOCAL_CONFIG_JSON --output NEW_EXTERNAL_DIRECTORY',
      tools: {node: process.version, platform: process.platform, ...JSON.parse(versions.stdout)},
      publications: Object.fromEntries(Object.entries(sessions.metadata).map(([alias, m]) => [alias,
        {root: m.root, generation: m.generation, fingerprint: m.fingerprint, members: m.members}])),
      prerequisites: {sourceInputs: prepared.inputs, preparedRevision: '357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb',
        preparedHashes: JSON.parse(fs.readFileSync(path.join(repository, 'docs/research/atlas-temporal-integration-baseline.json'), 'utf8')).preparedHashes,
        registrationLocatorReceipt: 'docs/research/atlas-local-retrieval-baseline.json#selectedWorld',
        legacyLocatorReceipt: 'docs/research/atlas-local-runtime-baseline.json#publicationRoot'},
      referenceSources: Object.fromEntries(referenceFiles.map(file => [file, hash(fs.readFileSync(path.join(repository, file)))])),
      exclusions: ['top-level operational metrics only'],
      files: Object.fromEntries(Object.entries(files).map(([name, value]) => {
        const bytes = encodeFixture(value); return [name, {bytes: Buffer.byteLength(bytes), sha256: hash(bytes)}];
      })),
    };
    files['manifest.json'] = manifest;
    const encoded = Object.fromEntries(Object.entries(files).map(([name, value]) => [name, encodeFixture(value)]));
    const bytes = Object.values(encoded).reduce((n, s) => n + Buffer.byteLength(s), 0);
    if (bytes > 2 * 1024 * 1024) throw new ConformanceError(`Fixture exceeds the bounded 2 MiB metadata budget: ${bytes} bytes; ${Object.keys(documents).length} documents.`);
    for (const text of Object.values(encoded)) if (text.includes('C:\\') || text.includes('C:/') || /\/Users\/|\/home\/|meridian-private/i.test(text)) throw new ConformanceError('Fixture contains a forbidden physical/private locator.');
    fs.mkdirSync(output);
    for (const [name, text] of Object.entries(encoded)) fs.writeFileSync(path.join(output, name), text, {flag: 'wx'});
    console.log(JSON.stringify({cases: requests.cases.length, expectedErrors: Object.values(expected).filter(e => e.kind === 'error').length,
      documents: Object.keys(documents).length, bytes, publications: Object.keys(manifest.publications).length}));
  } finally { await sessions.close(); }
}
generate().catch(failure);
