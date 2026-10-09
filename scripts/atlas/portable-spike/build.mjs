// Generation bridge only. Independent reads never import this module.
import fs from 'node:fs';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import {configuration, flags, assertExternal, referenceSessions, repository, failure, verifyReferenceSources} from '../read-conformance/reference.mjs';
import {hash, encodeFixture, ConformanceError} from '../read-conformance/fixtures.mjs';
import {encode} from '../../../pilots/atlas/tryfan/identity.mjs';
import {resolveAuthoritative} from '../../../runtime/atlas/authority.ts';
import {retrievalView} from '../../../runtime/atlas/retrieval-model.ts';

async function build() {
  const args = flags(process.argv.slice(2), ['config', 'output']);
  if (!args.output) throw new ConformanceError('Required new external --output is missing.');
  const config = configuration(args.config), output = path.resolve(args.output);
  assertExternal(output, config); assertExternal(fs.realpathSync(path.dirname(output)), config);
  if (fs.existsSync(output)) throw new ConformanceError('Output must not exist.');
  const reference = JSON.parse(fs.readFileSync(path.join(repository, 'fixtures/atlas-read/v1/manifest.json')));
  verifyReferenceSources(reference);
  const prepared = path.join(config.dataRoot, 'derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1', reference.prerequisites.preparedRevision);
  const features = fs.readFileSync(path.join(prepared, 'features.json'));
  const rasters = JSON.parse(fs.readFileSync(path.join(prepared, 'raster-bindings.json'))).rasters;
  const inputs = rasters.map(r => ({id: r.id, input: r.input}));
  for (const {input} of inputs) {
    const source = fs.realpathSync(path.join(config.dataRoot, input.path));
    const relative = path.relative(config.dataRoot, source);
    if (relative.startsWith('..') || path.isAbsolute(relative) || hash(fs.readFileSync(source)) !== input.sha256 || fs.statSync(source).size !== input.bytes) throw new ConformanceError('Native raster identity or public root mismatch.');
  }
  const estimated = inputs.reduce((n, r) => n + r.input.bytes, features.length) + 16 * 1024 * 1024;
  if (estimated > 160 * 1024 * 1024) throw new ConformanceError('Native closure exceeds the frozen storage bound.');
  const start = performance.now(), sessions = referenceSessions(config, reference.publications);
  const stage = fs.mkdtempSync(path.join(path.dirname(output), 'atlas-projection-stage-'));
  const files = {}, pins = {}, rasterFiles = {};
  function write(name, bytes) {
    fs.writeFileSync(path.join(stage, name), bytes, {flag: 'wx'});
    files[name] = {bytes: Buffer.byteLength(bytes), sha256: hash(bytes)};
  }
  try {
    write('features.json', features);
    const semantic = JSON.parse(fs.readFileSync(path.join(prepared, 'semantic-evidence.json')));
    write('worldcover.json', encodeFixture(semantic.collections.find(c => c.id.split(':')[0] === 'worldcover')));
    for (const {id, input} of inputs) {
      const name = input.sha256 + '.tif';
      if (!files[name]) write(name, fs.readFileSync(path.join(config.dataRoot, input.path)));
      rasterFiles[id] = name;
    }
    for (const [alias, pin] of Object.entries(reference.publications)) {
      const context = await sessions.get(alias);
      if (sessions.metadata[alias].fingerprint !== pin.fingerprint) throw new ConformanceError('Selected authoritative closure changed.');
      // Unfiltered population, not fixture requests or expected answers.
      const answer = await context.scanEvidence({}); delete answer.metrics;
      const snapshot = resolveAuthoritative({publicationRoot: config[pin.root], generation: pin.generation, dataRoot: config.dataRoot});
      const view = retrievalView(snapshot, config[pin.root]).worker;
      const name = pin.generation + '.json';
      write(name, encodeFixture({schema: 'atlas-read-projection-generation/v1', answer, selectors: view.selectors, knowledge: view.knowledge}));
      pins[pin.generation] = {file: name, fingerprint: pin.fingerprint, alias, records: answer.results.length};
    }
    const manifest = {schema: 'atlas-read-projection-spike/v1', profile: reference.profile, referenceCheckpoint: '5c93074f9773815111af96f89c3a73fcbb3b526a',
      preparedRevision: reference.prerequisites.preparedRevision, core: [2624000,1091000,2626000,1093000], crs: 'EPSG:2056',
      pins, rasterFiles, files, coverage: 'Riffelhorn exact native read profile; whole-publication metadata references retained; not a rendering or mobile package.'};
    manifest.projectionIdentity = hash(encode(manifest));
    write('manifest.json', encodeFixture(manifest));
    const bytes = Object.values(files).reduce((n, v) => n + v.bytes, 0);
    if (bytes > 160 * 1024 * 1024) throw new ConformanceError('Actual projection exceeds bound.');
    fs.renameSync(stage, output);
    console.log(JSON.stringify({bytes, files: Object.keys(files).length, generations: Object.keys(pins).length, projectionIdentity: manifest.projectionIdentity, buildMs: performance.now()-start, nodeRssBytes: process.memoryUsage().rss}));
  } finally {
    await sessions.close();
    // Only the owned new staging directory, never data/publication roots.
    if (fs.existsSync(stage)) fs.rmSync(stage, {recursive: true, force: true});
  }
}
build().catch(failure);
