import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {loadFixtures, fixtureRoot, packOutcome, unpackOutcome, semanticOutcome, difference, encodeFixture, hash} from './fixtures.mjs';
import {referenceCases} from './cases.mjs';
import {point, sourceIdentity, slopeIdentity, ratioIdentity} from '../../../runtime/atlas/retrieval-cases.mjs';

const fixtures = loadFixtures();
const outcome = id => unpackOutcome(fixtures.expected[id], fixtures.documents);
const answer = id => outcome(id).value;
const ids = id => answer(id).results.map(r => r.identity).sort();
function alteredFixture(change) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'meridian-read-fixture-test-'));
  try {
    fs.cpSync(fileURLToPath(fixtureRoot), dir, {recursive: true});
    change(dir);
    return loadFixtures(pathToFileURL(dir + path.sep));
  } finally { fs.rmSync(dir, {recursive: true, force: true}); }
}
function reseal(dir, name, value) {
  const bytes = encodeFixture(value);
  fs.writeFileSync(path.join(dir, name), bytes);
  const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json')));
  manifest.files[name] = {bytes: Buffer.byteLength(bytes), sha256: hash(bytes)};
  fs.writeFileSync(path.join(dir, 'manifest.json'), encodeFixture(manifest));
}

test('fixed requests reuse accepted cases and three exact published pins', () => {
  assert.equal(fixtures.cases.length, 60);
  assert.deepEqual(referenceCases().cases, fixtures.cases);
  assert.equal(Object.keys(fixtures.manifest.publications).length, 3);
  assert.equal(fixtures.manifest.prerequisites.sourceInputs.length, 12);
});
test('document deduplication reconstructs every complete semantic envelope', () => {
  for (const c of fixtures.cases) {
    const expected = fixtures.expected[c.id], shared = {};
    const hydrated = unpackOutcome(expected, fixtures.documents);
    assert.deepEqual(packOutcome(hydrated, shared), expected);
    if (hydrated.kind === 'answer') assert(!Object.hasOwn(hydrated.value, 'metrics'));
  }
});
test('presentation handling preserves arrays, numbers, false, null and unknown qualifications', () => {
  const original = {generation: 'pin', metrics: {milliseconds: 1}, documents: {}, results: [{value: 1.2345678901234567, temporal: {status: 'unknown'}, physicalAbsenceInferred: false, values: [2, 1], missing: null}]};
  assert.equal(difference(semanticOutcome(original), semanticOutcome({...original, metrics: {milliseconds: 999}})), null);
  const changed = structuredClone(semanticOutcome(original));
  changed.value.results[0].values.reverse();
  assert.equal(difference(semanticOutcome(original), changed), '$/value/results/0/values/0');
  assert.equal(JSON.parse(encodeFixture(original)).results[0].value, original.results[0].value);
});
test('independent native raster seam and outer half-open boundaries', () => {
  assert.equal(answer('native-tile-seam').results.length, 1);
  assert.deepEqual(ids('native-outer-x-edge'), []);
  assert.deepEqual(ids('native-outer-y-edge'), []);
  assert.deepEqual(answer('native-outer-x-edge').gap, {reason: 'no-matching-qualified-evidence', physicalAbsenceInferred: false});
});
test('independent scalar location is discrete, consumed support separate', () => {
  assert.deepEqual(ids('derived-anchor'), [ratioIdentity, slopeIdentity].sort());
  assert.deepEqual(ids('derived-adjacent-absent'), []);
  assert.deepEqual(ids('derived-feature-absent'), []);
  for (const r of answer('derived-anchor').results) assert.deepEqual(r.support.point, point);
});
test('survey, release and unknown units/times remain native qualifications', () => {
  const glacier = answer('native-epoch-2015').results.find(r => r.identity === 'glaciers:683');
  assert.equal(glacier.temporal['evidence-epoch'].year, 2015);
  assert.equal(glacier.temporal['product-reference'].year, 2020);
  const dtm = answer('native-tile-seam'), body = dtm.documents[dtm.results[0].evidenceRef];
  assert.equal(body.detail.payload.unit.status, 'unknown');
  assert.equal(body.detail.payload.kind, 'native-height');
  assert.equal(answer('derived-unknown-epoch').results[0].temporal['evidence-epoch'].status, 'unknown');
  assert.deepEqual(ids('derived-finite-epoch-absent'), []);
});
test('known qualification correction preserves value, historical identity and supersession', () => {
  const old = answer('slope-before-requalification'), now = answer('derived-slope');
  const a = old.results[0], b = now.results[0];
  assert.notEqual(a.revision, b.revision);
  assert.equal(old.documents[a.evidenceRef].value, now.documents[b.evidenceRef].value);
  const sourceBefore = answer('source-before-qualification'), sourceAfter = answer('source-exact');
  assert.equal(sourceBefore.results[0].identity, sourceIdentity);
  assert.equal(sourceBefore.documents[sourceBefore.results[0].qualificationRef].sourceNotices.length, 0);
  assert.equal(sourceAfter.documents[sourceAfter.results[0].qualificationRef].sourceNotices.length, 1);
  const k = sourceAfter.documents[sourceAfter.results[0].knowledgeRef];
  assert.equal(k.physicalChangeInferred, false);
  assert.equal(k.supersedes, sourceBefore.documents[sourceBefore.results[0].knowledgeRef].identity);
});
test('legacy unknown knowledge is not unrestricted known acceptance', () => {
  assert.deepEqual(ids('legacy-unknown-knowledge'), ['glaciers:683']);
  assert.deepEqual(ids('legacy-known-knowledge-absent'), []);
  assert.deepEqual(ids('legacy-no-derived-state'), []);
  assert.equal(answer('legacy-unknown-knowledge').results[0].knowledgeRef, null);
});
test('explicit transitive lineage is preserved rather than inferred', () => {
  assert.deepEqual(ids('ratio-inputs-transitive'), [sourceIdentity, slopeIdentity].sort());
  const a = answer('ratio-inputs-transitive');
  assert.equal(a.traversal.relationshipRefs.length, 2);
  assert(a.relationships.some(r => r.kind === 'derived-input'));
  assert(a.relationships.some(r => r.kind === 'consumes-qualified-source' && r.via.preparedRevision === fixtures.manifest.prerequisites.preparedRevision));
});
test('nine unsupported/invalid requests retain exact runtime errors, not empty results', () => {
  const errors = fixtures.cases.filter(c => fixtures.expected[c.id].kind === 'error');
  assert.equal(errors.length, 9);
  for (const c of errors) {
    assert(c.tags.includes('unsupported'));
    assert.equal(typeof fixtures.expected[c.id].message, 'string');
    assert(!Object.hasOwn(fixtures.expected[c.id], 'value'));
  }
  assert.equal(outcome('unsupported-missing-relationship').code, 'relationship-missing');
});
test('modified member bytes and missing expected documents are rejected', () => {
  assert.throws(() => alteredFixture(dir => fs.appendFileSync(path.join(dir, 'requests.json'), ' ')), /integrity/);
  assert.throws(() => alteredFixture(dir => {
    const value = JSON.parse(fs.readFileSync(path.join(dir, 'documents.json')));
    delete value.documents[answer('source-exact').results[0].evidenceRef];
    reseal(dir, 'documents.json', value);
  }), /Missing expected document/);
});
test('resealed altered scientific document and wrong pin cannot pass fixture integrity', () => {
  assert.throws(() => alteredFixture(dir => {
    const value = JSON.parse(fs.readFileSync(path.join(dir, 'documents.json')));
    value.documents[answer('source-exact').results[0].evidenceRef].evidenceKind = 'invented';
    reseal(dir, 'documents.json', value);
  }), /Document integrity/);
  assert.throws(() => alteredFixture(dir => {
    const value = JSON.parse(fs.readFileSync(path.join(dir, 'expected.json')));
    value.cases['source-exact'].value.generation = '0'.repeat(64);
    reseal(dir, 'expected.json', value);
  }), /Expected pin differs/);
});
