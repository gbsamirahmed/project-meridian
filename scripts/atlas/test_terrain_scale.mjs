import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import test from 'node:test';

const read = path => JSON.parse(readFileSync(path,'utf8'));
const plan=read('docs/atlas/terrain-scale-plan.json');
const manifest=read('docs/atlas/terrain-scale-diagnostic.json');
const result=read('docs/atlas/terrain-scale-measurements.json');
const future=read('docs/atlas/riffelhorn-final-reconciliation-experiment.json');
const digest = path => createHash('sha256').update(readFileSync(path,'utf8').replaceAll('\r\n','\n')).digest('hex');

test('record preserves unknown causal attribution and native references',()=>{
  assert.deepEqual(result.products,plan.products);
  assert.match(result.heightPolicy,/no transform/);
  for(const level of Object.values(result.levels)){
    assert.ok(level.closureMaxM < 1e-10);
    for(const row of Object.values(level.strata)){
      assert.ok(Math.abs(row.energy.closure)<1e-9);
      assert.ok(row.components.commonDetail.rms>0);
    }
  }
});

test('diagnostic hashes identify isolated tools without external CI dependency',()=>{
  assert.equal(manifest.protocolSha256,digest('docs/atlas/terrain-scale-plan.json'));
  for(const [name,hash] of Object.entries(manifest.tools)){
    assert.equal(hash,digest(`scripts/atlas/${name}`));
  }
  assert.ok(manifest.files.some(row=>row.path==='profiles.png'));
  for(const file of ['src/atlas/map/visualTerrainConfig.ts','src/atlas/terrain/analyticalElevationConfig.ts','vite.config.ts']){
    assert.doesNotMatch(readFileSync(file,'utf8'),/terrain.scale|reconciliation.experiment/);
  }
});

test('future experiment is one unimplemented protected, explicit synthetic test',()=>{
  assert.equal(future.status,'design-only-not-implemented');
  assert.deepEqual(future.inputs,plan.products);
  assert.equal(future.protectedRadiusM,1500);
  assert.equal(future.sourceEdgeClearanceM,1000);
  assert.ok(future.detailTaperStartRadiusM>future.protectedRadiusM);
  assert.match(future.heightPolicy,/heterogeneous/);
  assert.match(future.provenance,/negative/);
  assert.match(future.terminalRule,/regardless of result/);
});
