// Local research snapshot mechanism. No semantic truth or freshness is stored here.
import { existsSync, mkdirSync, readFileSync, writeFileSync, openSync, fsyncSync, closeSync, renameSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
export const FORMAT = 'tryfan-local-persistent-store/v1';
export class StoreError extends Error {
  constructor(code, message) { super(message); this.name = 'StoreError'; this.code = code; }
}
function ordered(value) {
  if (typeof value === 'number' && !Number.isFinite(value)) throw new StoreError('invalid-value', 'Nonfinite value cannot be serialized');
  if (Array.isArray(value)) return value.map(ordered);
  if (value !== null && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, ordered(value[k])]));
  return value;
}
export const encode = value => JSON.stringify(ordered(value), null, 2) + '\n';
export const sha = body => createHash('sha256').update(body).digest('hex');
function durableWrite(path, body) {
  const fd = openSync(path, 'wx');
  try { writeFileSync(fd, body); fsyncSync(fd); } finally { closeSync(fd); }
}
export function load(dir, validate) {
  const pointer = join(dir, 'current.json');
  if (!existsSync(pointer)) throw new StoreError('store-absent', 'No accepted local proof store; initialize explicitly');
  let pub;
  try { pub = JSON.parse(readFileSync(pointer, 'utf8')); } catch { throw new StoreError('invalid-pointer', 'Publication pointer is invalid'); }
  if (pub.format !== FORMAT || !/^[a-f0-9]{64}$/.test(pub.snapshot ?? '')) throw new StoreError('unsupported-pointer', 'Unknown store format or invalid snapshot address');
  let body;
  try { body = readFileSync(join(dir, 'snapshots', pub.snapshot + '.json')); } catch { throw new StoreError('snapshot-unavailable', 'Accepted snapshot cannot be read'); }
  if (sha(body) !== pub.snapshot) throw new StoreError('checksum-failure', 'Accepted snapshot checksum differs');
  let state;
  try { state = JSON.parse(body); } catch { throw new StoreError('invalid-snapshot', 'Snapshot JSON is invalid'); }
  validate(state);
  return { state, snapshot: pub.snapshot, bytes: body.length, pointerBytes: Buffer.byteLength(encode(pub)) };
}
export function publish(dir, state, validate, { beforePointer } = {}) {
  validate(state); // Invalid state never becomes an accepted revision.
  mkdirSync(join(dir, 'snapshots'), { recursive: true });
  const body = encode(state), snapshot = sha(body), file = join(dir, 'snapshots', snapshot + '.json');
  const existed = existsSync(file);
  if (existed) {
    if (readFileSync(file, 'utf8') !== body) throw new StoreError('collision', 'Snapshot content mismatch');
  } else durableWrite(file, body);
  beforePointer?.(); // Failure injection: completed but unpublished snapshot may remain.
  const temp = join(dir, 'pointer-' + process.pid + '.pending');
  durableWrite(temp, encode({ format: FORMAT, snapshot }));
  renameSync(temp, join(dir, 'current.json')); // Single-writer same-directory publication boundary.
  return { snapshot, bytes: Buffer.byteLength(body), snapshotWritten: !existed, pointerBytes: Buffer.byteLength(encode({ format: FORMAT, snapshot })) };
}
