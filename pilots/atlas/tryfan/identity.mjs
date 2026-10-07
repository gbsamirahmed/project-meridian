// Pilot serialization and integrity, not a new physical/semantic identity model.
import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { resolve, relative, isAbsolute } from 'node:path';
export const FORMAT = 'atlas-tryfan-pilot-store/v1';
export class PilotError extends Error {
  constructor(code, message) { super(message); this.name = 'PilotError'; this.code = code; }
}
export function requireThat(ok, code, message) { if (!ok) throw new PilotError(code, message); }
function ordered(value) {
  if (value === null || ['string','boolean'].includes(typeof value)) return value;
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (Array.isArray(value)) return value.map(ordered);
  requireThat(value && Object.getPrototypeOf(value) === Object.prototype, 'invalid-value', 'Only finite JSON values are permitted');
  return Object.fromEntries(Object.keys(value).sort().map(key => [key, ordered(value[key])]));
}
export const encode = value => JSON.stringify(ordered(value), null, 2) + '\n';
export const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export const refKey = ref => sha(encode(ref));
export const byId = records => [...records].sort((a,b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
export function json(file, code = 'malformed-generation') {
  try { return JSON.parse(readFileSync(file, 'utf8')); }
  catch (error) { throw new PilotError(error.code === 'ENOENT' ? 'missing-file' : code, 'Cannot read JSON: ' + file); }
}
export function safePath(root, locator) {
  requireThat(typeof root==='string' && !root.toLowerCase().includes('meridian-private'),'invalid-locator','Private data roots are excluded');
  requireThat(typeof locator === 'string' && locator.length && !isAbsolute(locator) &&
    !locator.includes('\\') && !locator.includes(':') && !locator.split('/').some(p => p === '..' || p === '' || p.toLowerCase().includes('meridian-private')),
    'invalid-locator', 'Locator must be a safe relative public-data path');
  const target = resolve(root, locator);
  let actual;
  try { actual = realpathSync(target); } catch { throw new PilotError('artifact-unavailable', 'Missing retained artifact: ' + locator); }
  const rel = relative(realpathSync(root), actual);
  requireThat(rel && !rel.startsWith('..') && !isAbsolute(rel) && !actual.toLowerCase().includes('meridian-private'),
    'invalid-locator', 'Locator resolves outside declared public data root');
  return actual;
}
export function fields(object, required, optional = [], code = 'invalid-schema') {
  requireThat(object && !Array.isArray(object) && typeof object === 'object' &&
    required.every(k => Object.hasOwn(object,k)) && Object.keys(object).every(k => [...required,...optional].includes(k)), code, 'Invalid record fields: ' + required.join(','));
}
