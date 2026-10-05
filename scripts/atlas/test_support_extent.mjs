import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import test from 'node:test';
const read = name => JSON.parse(readFileSync(`docs/atlas/${name}.json`, 'utf8'));
const result = read('support-extent-measurements');
const plan = read('support-extent-plan');
const manifest = read('support-extent-diagnostic');

test('support extent retains protected geometry, buffer sensitivity and no elevation access', () => {
  assert.deepEqual(plan.protectedCentreLV95, [2625000, 1092000]);
  assert.equal(plan.protectedRadiusMetres, 1500);
  assert.deepEqual(plan.glacierBuffersMetres, [100, 250, 500]);
  assert.equal(result.heightArraysRead, false);
  assert.equal(result.elevationAssetsAcquired, false);
  assert.ok(result.catalogueChecks.every(row => row.assetNotDownloaded));
  assert.equal(manifest.noElevationAccess, true);
});

test('censored geography cannot become a fabricated minimum or acquisition recommendation', () => {
  for (const row of Object.values(result.steps)) {
    assert.equal(row.epochBorderChecks.recent2023.connectedToUnknownTerritory, true);
    for (const item of Object.values(row.cases)) {
      assert.equal(item.touchesStudyEdge, true);
      assert.equal(item.minimumExtent, null);
      assert.equal(item.robustExtent, null);
      assert.equal(item.connectedToUnknownTerritory, true);
      const box = item.candidates.observedWindow;
      assert.equal(box.tiles, 468);
      assert.equal(box.reuse, 100);
      assert.equal(box.new, 368);
      assert.ok(Object.values(box.tests).every(test => !test.enclosingCycle));
      assert.equal(box.sourceBytesAreaEstimate, Math.round(1667166026 * 4.68));
    }
  }
  assert.equal(result.steps['25'].retained250MaskReproduced, true);
  assert.equal(manifest.noAcquisitionRecommendationAccepted, true);
});

test('record hashes identify isolated diagnostic code; no new startup source', () => {
  const sha = value => createHash('sha256').update(value).digest('hex');
  const tool = readFileSync('scripts/atlas/support_extent.py', 'utf8').replaceAll('\r\n', '\n');
  assert.equal(sha(tool), manifest.toolSha256);
  assert.equal(sha(readFileSync('docs/atlas/support-extent-plan.json', 'utf8').replaceAll('\r\n', '\n')), manifest.planSha256);
  assert.doesNotMatch(tool, /urlopen|WarpedVRT|read\(1/);
  for (const file of ['src/atlas/map/visualTerrainConfig.ts', 'src/atlas/terrain/analyticalElevationConfig.ts', 'vite.config.ts']) {
    assert.doesNotMatch(readFileSync(file, 'utf8'), /support.extent/);
  }
});
