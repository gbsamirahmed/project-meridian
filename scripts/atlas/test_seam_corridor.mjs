import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const read = name => JSON.parse(readFileSync(`docs/atlas/${name}.json`, 'utf8'));
const plan = read('seam-corridor-plan');
const results = read('seam-corridor-measurements');
const record = read('seam-corridor-diagnostic');

test('corridor diagnostic retains exact independent product identities and native heights', () => {
  assert.deepEqual(results.products, plan.products);
  assert.deepEqual(record.inputs.products, plan.products);
  assert.deepEqual(plan.levels, [12, 13]);
  assert.equal(record.heightsUnmodified, true);
  assert.equal(record.noVerticalTransformation, true);
  assert.equal(record.noTerrainOutput, true);
  assert.match(results.heightPolicy, /LN02.*EGM2008/);
  assert.deepEqual(results.verification.sourceAssetsVerified, {common: 6, swiss: 100});
  assert.equal(results.verification.regionalFilesVerified, 35);
});

test('infeasibility is not rescued by compatibility scores or relaxed change masks', () => {
  for (const row of Object.values(results.levels)) {
    for (const name of ['primary', 'edge100', 'edge500', 'ice100', 'ice500', 'strictStable', 'glacierOnlyAttribution', 'snowOnlyAttribution']) {
      assert.equal(row.scenarios[name].closedCycleAtUnlimitedDisagreement, false);
      assert.equal(row.scenarios[name].minimumThresholdMetres, null);
    }
    assert.ok(row.thresholds.every(t => t.closedCycle === false));
    const control = row.scenarios.noChangeExclusionControl;
    assert.equal(control.closedCycleAtUnlimitedDisagreement, true);
    assert.equal(control.belowMinimumFeasible, false);
    assert.ok(control.route.glacier250Fraction > .75);
    assert.ok(control.route.stableVertexFraction < .03);
    assert.equal(row.scenarios.primary.obstruction.fullySupportedOutsideProtected.glacier250EndpointFraction, 1);
    assert.ok(row.scenarios.primary.obstruction.fullySupportedOutsideProtected.edges > 100);
  }
});

test('sensitivity domains remain nested and protected/source edge constraints explicit', () => {
  assert.equal(plan.protectedInterior.radiusMetres, 1500);
  assert.deepEqual(plan.protectedInterior.centreLV95, [2625000, 1092000]);
  for (const row of Object.values(results.levels)) {
    assert.ok(row.scenarios.edge100.domainNodes >= row.domainNodes);
    assert.ok(row.scenarios.edge500.domainNodes <= row.domainNodes);
    assert.ok(row.scenarios.ice100.domainNodes >= row.domainNodes);
    assert.ok(row.scenarios.ice500.domainNodes <= row.domainNodes);
    assert.equal(row.corners.SE.permittedNodes, 0);
    assert.ok(row.rectangleControl.changeExcludedFraction > .6);
    const route = row.scenarios.noChangeExclusionControl.route;
    assert.ok(route.minimumSourceEdgeMetres >= 200);
    assert.ok(route.minimumProtectedClearanceMetres > 0);
  }
});

test('diagnostic outputs are hashes and evidence fields; no runtime source hook', () => {
  for (const file of record.files) {
    assert.match(file.sha256, /^[0-9a-f]{64}$/);
    assert.ok(file.bytes > 0);
    assert.doesNotMatch(file.path, /tiles\//);
  }
  const source = readFileSync('scripts/atlas/seam_corridor.py', 'utf8');
  assert.doesNotMatch(source, /createServer|ThreadingHTTPServer|urlopen|vgridshift/);
  assert.doesNotMatch(readFileSync('src/atlas/map/visualTerrainConfig.ts', 'utf8'), /seam.corridor/);
  assert.doesNotMatch(readFileSync('vite.config.ts', 'utf8'), /seam.corridor/);
});
