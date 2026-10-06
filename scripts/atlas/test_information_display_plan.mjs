import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const plan=JSON.parse(readFileSync('docs/atlas/information-display-plan.json','utf8'));
const prior=JSON.parse(readFileSync('docs/atlas/multiscale-representation-plan.json','utf8'));
const hash=b=>createHash('sha256').update(b).digest('hex');
test('Frozen camera subset is explicit, unique and bounded',()=>{
 const entries=[];
 for(const task of plan.tasks){
  const old=prior.scenes.find(s=>s.id===task.scene.id)||prior.scenes.find(s=>s.id==='riffelhorn-8m');
  assert.ok(old);const camera=structuredClone(task.scene);
  if(camera.id==='riffelhorn-8m-p35'){camera.id='riffelhorn-8m';camera.pitch=0;}
  assert.deepEqual(camera,old);
  for(const d of task.dprs)for(const a of task.appearances)entries.push([task.mode,task.scene.id,d,a].join('/'));
 }
 assert.equal(entries.length,22);assert.equal(new Set(entries).size,22);
 assert.deepEqual(plan.viewport,{width:1440,height:900});
 assert.equal(hash(readFileSync('docs/atlas/multiscale-representation-plan.json')),plan.priorCameraPlanSha256);
});
test('Production inputs and dependency renderer source remain unchanged',()=>{
 assert.equal(Object.keys(plan.productionHashes).length,113);
 for(const [file,expected]of Object.entries(plan.productionHashes))assert.equal(hash(readFileSync(file)),expected,file);
 for(const [file,expected]of Object.entries(plan.rendererHashes))assert.equal(hash(readFileSync('node_modules/maplibre-gl/src/'+file)),expected,file);
});
