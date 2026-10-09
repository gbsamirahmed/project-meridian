import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {openAtlas, AtlasError} from '../../../runtime/atlas/index.ts';
import {resolveAuthoritative} from '../../../runtime/atlas/authority.ts';
import {semanticOutcome, hash, ConformanceError} from './fixtures.mjs';

export const repository = path.resolve(import.meta.dirname, '../../..');
export function flags(argv, allowed) {
  const out = {};
  for (let i = 0; i < argv.length; i += 2) {
    const name = argv[i].replace(/^--/, '');
    if (!argv[i].startsWith('--') || !allowed.includes(name) || !argv[i + 1] || Object.hasOwn(out, name)) throw new ConformanceError('Use documented explicit flags; no unknown or duplicate options.');
    out[name] = argv[i + 1];
  }
  if (!out.config) throw new ConformanceError('Required --config LOCAL_CONFIGURATION_JSON is missing.');
  return out;
}

export function configuration(file) {
  const absolute = path.resolve(file), raw = JSON.parse(fs.readFileSync(absolute, 'utf8'));
  const keys = ['dataRoot', 'python', 'registrationWorld', 'legacyWorld'];
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) || Object.keys(raw).some(k => !keys.includes(k))) throw new ConformanceError('Configuration accepts only public data, Python and publication locators.');
  for (const k of ['dataRoot', 'python']) if (typeof raw[k] !== 'string' || !raw[k]) throw new ConformanceError(`Missing configuration field: ${k}`);
  const config = {};
  for (const [k, v] of Object.entries(raw)) {
    if (typeof v !== 'string' || !v || v.toLowerCase().includes('meridian-private')) throw new ConformanceError(`Invalid public locator: ${k}`);
    config[k] = fs.realpathSync(path.resolve(path.dirname(absolute), v));
    if (config[k].toLowerCase().includes('meridian-private')) throw new ConformanceError('Private path targets are forbidden.');
  }
  return config;
}

export function inside(child, parent) {
  const relative = path.relative(parent, child);
  return !relative || (!path.isAbsolute(relative) && relative !== '..' && !relative.startsWith('..' + path.sep));
}

export function assertExternal(destination, config) {
  const target = path.resolve(destination);
  for (const root of [repository, config.dataRoot, config.registrationWorld, config.legacyWorld].filter(Boolean)) {
    if (inside(target, root) || inside(root, target)) throw new ConformanceError('Output/scratch must be outside the repository and canonical data/publications.');
  }
  if (target.toLowerCase().includes('meridian-private')) throw new ConformanceError('Private output paths are forbidden.');
}

export function referenceSessions(config, publications) {
  assertExternal(os.tmpdir(), config);
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'meridian-atlas-read-'));
  const sessions = new Map(), metadata = {};
  return {
    metadata,
    async get(alias) {
      if (sessions.has(alias)) return sessions.get(alias);
      const pin = publications[alias], root = pin && config[pin.root];
      if (!root) throw new ConformanceError(`Missing explicit publication locator for pin: ${alias}`);
      const settings = {dataRoot: config.dataRoot, python: config.python, publicationRoot: root,
        generation: pin.generation, catalogueRoot: path.join(scratch, alias)};
      const context = await openAtlas(settings);
      sessions.set(alias, context);
      const built = await context.buildCatalogue({qualified: true});
      const snapshot = resolveAuthoritative(settings);
      metadata[alias] = {root: pin.root, generation: context.generation, fingerprint: snapshot.fingerprint,
        members: context.members, validation: context.validation, catalogue: built};
      return context;
    },
    async close() {
      // scratch is exactly this invocation's newly created directory, never a configured root.
      try { for (const session of sessions.values()) await session.close(); }
      finally { fs.rmSync(scratch, {recursive: true, force: true}); }
    },
  };
}

export async function invoke(context, query, method) {
  try { return semanticOutcome(await context[method](query)); }
  catch (error) {
    if (!(error instanceof AtlasError)) throw error;
    return {kind: 'error', code: error.code, message: error.message};
  }
}

export function verifyReferenceSources(manifest) {
  for (const [file, expected] of Object.entries(manifest.referenceSources)) {
    if (hash(fs.readFileSync(path.join(repository, file))) !== expected) throw new ConformanceError(`Reference source changed: ${file}; review/version fixtures, never rewrite expectations silently.`);
  }
}

export function failure(error) {
  // Configuration/open failures are blockers, never skipped or generated scientific answers.
  console.error(JSON.stringify({status: 'blocked', code: error instanceof AtlasError ? error.code : 'reference-prerequisite-or-fixture-invalid',
    message: error instanceof AtlasError || error instanceof ConformanceError ? error.message : 'Check the explicit public configuration, retained inputs, fixture integrity and documented command.'}));
  process.exitCode = 1;
}
