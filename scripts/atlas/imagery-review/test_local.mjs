import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { openData } from './local-data.mjs';

test('changed metadata is rejected before any retained data can be served', async () => {
  const temp = await mkdtemp(join(tmpdir(), 'meridian-imagery-test-'));
  try {
    const root = join(temp, 'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1');
    await mkdir(root, { recursive: true }); await writeFile(join(root, 'manifest.json'), '{}');
    await assert.rejects(openData(temp), /Retained evidence changed/);
  } finally { await rm(temp, { recursive: true, force: true }); }
});
test('existing product serving is exact, bounded and separates imagery from contour heights', { skip: !process.env.MERIDIAN_DATA_ROOT }, async () => {
  const local = await openData(process.env.MERIDIAN_DATA_ROOT);
  assert.equal(local.metadata.imageryYear, 2023);
  assert.equal(local.metadata.nominalInformationMetres, 0.25);
  assert.equal(local.metadata.distributedGridMetres, 0.1);
  assert.equal(local.metadata.imageryDelivery.crs, 'EPSG:3857');
  assert.match(local.metadata.contourVerticalReference, /LN02/);
  const png = await local.load('/imagery/12/2136/1457.png');
  assert.equal(png.type, 'image/png'); assert.equal(png.data.length, 58492);
  const tile = await local.load('/contours/swiss-smoothed/17/68366/46646.pbf');
  assert.equal(tile.type, 'application/vnd.mapbox-vector-tile'); assert.equal(tile.data.length, 17);
  for (const path of ['/imagery/../../manifest.json', '/imagery/12/2136/1457.png?x=1', '/fields/12/2136/1457.npz', '/.env.local']) assert.equal(await local.load(path), undefined);
});
