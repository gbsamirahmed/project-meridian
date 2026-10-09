import fs from 'node:fs';
import {encode, sha} from '../../../pilots/atlas/tryfan/identity.mjs';
import {semantic} from '../../../runtime/atlas/retrieval-cases.mjs';

export class ConformanceError extends Error {}

export const fixtureRoot = new URL('../../../fixtures/atlas-read/v1/', import.meta.url);
export const encodeFixture = value => JSON.stringify(JSON.parse(encode(value))) + '\n';
export const hash = sha;

/** Only operational metrics are excluded, matching existing runtime comparisons. */
export function semanticOutcome(answer) {
  return {kind: 'answer', value: semantic(answer)};
}

export function packOutcome(outcome, documents) {
  if (outcome.kind === 'error') return outcome;
  const {documents: shared, ...value} = outcome.value;
  for (const [id, body] of Object.entries(shared)) {
    if (hash(encode(body)) !== id) throw new ConformanceError(`Document identity mismatch: ${id}`);
    if (documents[id] && encode(documents[id]) !== encode(body)) throw new ConformanceError(`Conflicting document: ${id}`);
    documents[id] = body;
  }
  return {kind: 'answer', value, documentRefs: Object.keys(shared).sort()};
}

export function unpackOutcome(outcome, documents) {
  if (outcome.kind === 'error') return outcome;
  return {kind: 'answer', value: {...outcome.value, documents: Object.fromEntries(outcome.documentRefs.map(id => {
    if (!Object.hasOwn(documents, id)) throw new ConformanceError(`Missing expected document: ${id}`);
    return [id, documents[id]];
  }))}};
}

export function loadFixtures(root = fixtureRoot) {
  const read = name => fs.readFileSync(new URL(name, root));
  const manifest = JSON.parse(read('manifest.json'));
  if (manifest.schema !== 'meridian-atlas-read-fixtures/v1') throw new ConformanceError('Unsupported fixture schema.');
  const values = {};
  for (const name of ['requests.json', 'expected.json', 'documents.json']) {
    const bytes = read(name), seal = manifest.files[name];
    if (bytes.length !== seal.bytes || hash(bytes) !== seal.sha256) throw new ConformanceError(`Fixture integrity failure: ${name}`);
    values[name] = JSON.parse(bytes);
  }
  const {cases} = values['requests.json'], expected = values['expected.json'].cases, documents = values['documents.json'].documents;
  if (values['requests.json'].schema !== 'meridian-atlas-read-requests/v1' || values['expected.json'].schema !== 'meridian-atlas-read-expected/v1' || values['documents.json'].schema !== 'meridian-atlas-read-documents/v1') throw new ConformanceError('Unsupported fixture member schema.');
  if (cases.length !== manifest.caseCount || new Set(cases.map(c => c.id)).size !== cases.length || Object.keys(expected).length !== cases.length) throw new ConformanceError('Fixture case membership differs.');
  for (const [id, body] of Object.entries(documents)) if (hash(encode(body)) !== id) throw new ConformanceError(`Document integrity failure: ${id}`);
  for (const c of cases) {
    if (!expected[c.id] || c.operation !== 'retrieve' || !manifest.publications[c.publication]) throw new ConformanceError(`Unsupported fixture operation or pin: ${c.id}`);
    const outcome = unpackOutcome(expected[c.id], documents);
    if (outcome.kind === 'answer' && outcome.value.generation !== manifest.publications[c.publication].generation) throw new ConformanceError(`Expected pin differs: ${c.id}`);
    if (!['answer', 'error'].includes(outcome.kind)) throw new ConformanceError(`Unsupported outcome: ${c.id}`);
  }
  return {manifest, cases, expected, documents};
}

/** Deterministic first semantic difference; avoids dumping entire evidence bodies. */
export function difference(expected, actual, location = '$') {
  if (Object.is(expected, actual)) return null;
  if (expected === null || actual === null || typeof expected !== 'object' || typeof actual !== 'object') return location;
  if (Array.isArray(expected) !== Array.isArray(actual)) return location;
  const a = Object.keys(expected).sort(), b = Object.keys(actual).sort();
  if (encode(a) !== encode(b)) return `${location} [keys]`;
  for (const key of a) {
    const found = difference(expected[key], actual[key], `${location}/${key}`);
    if (found) return found;
  }
  return null;
}
