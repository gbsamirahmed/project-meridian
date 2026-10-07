// Bounded S1 observations only. Logical receipt is deterministic; timings are not.
import { spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, basename, sep } from 'node:path';
import { performance } from 'node:perf_hooks';
import { ROOT } from './catalogue.mjs';
import { encode, sha } from './identity.mjs';
const scratch=mkdtempSync(join(tmpdir(),'meridian-s1-measure-'));
function command(args) {
  const start=performance.now();const p=spawnSync(process.execPath,[join(ROOT,'pilots/atlas/tryfan/cli.mjs'),...args],{encoding:'utf8'});
  if(p.status!==0)throw new Error(p.stderr);
  return {...JSON.parse(p.stdout),spawnWallMilliseconds:performance.now()-start};
}
try {
  const builds=Array.from({length:5},(_,i)=>command(['register','--store',join(scratch,'build-'+i)]));
  if(new Set(builds.map(b=>b.generation)).size!==1)throw new Error('Independent builds differ');
  const reads=Array.from({length:5},()=>command(['validate']));
  if(new Set(reads.map(b=>b.generation)).size!==1)throw new Error('Published root changed during measurement');
  const inspected=command(['inspect']);
  const report={assessment:'atlas-tryfan-pilot-s1-results/v1',startingCheckpoint:'7809147ae86b14a19d195e0cdc9791b47caa59eb',decision:'C - S1 SUCCESS',
    logical:{publishedGeneration:inspected.generation,parent:inspected.parent,independentSeedGeneration:builds[0].generation,
      format:inspected.format,capabilities:inspected.capabilities,counts:inspected.counts,verification:inspected.verification,
      catalogueSha256:sha(encode(inspected.catalogue)),locatorMapSha256:sha(encode(inspected.locators)),
      catalogueBytes:Buffer.byteLength(encode(inspected.catalogue)),generationBytes:inspected.metrics.generationBytes,pointerBytes:130,
      planSha256:inspected.catalogue.basis.sha256,sourceInventorySha256:sha(encode(inspected.catalogue.artifacts.map(a=>({id:a.id,sha256:a.sha256,bytes:a.bytes})))),
      historicalPreserved:inspected.parent!==null,nextTask:'Tryfan pilot qualified native evidence readers and queries - S2 only'},
    measurements:{outsideIdentity:true,conditions:{node:process.version,platform:process.platform,architecture:process.arch,warmFilesystemCache:true,
      builds:'Five fresh Node processes and independent empty runtime stores; retained OS file cache not cleared',
      loads:'Five fresh Node processes against published generation with full310asset hash verification and parent metadata integrity',
      memory:'End-of-command process RSS, not peak RSS; Vite loader used only by construction'},
      builds:builds.map(b=>({generation:b.generation,...b.metrics,spawnWallMilliseconds:b.spawnWallMilliseconds})),
      freshLoads:reads.map(b=>({...b.metrics,spawnWallMilliseconds:b.spawnWallMilliseconds}))}};
  for(const section of ['builds','freshLoads']) {
    const keys=Object.keys(report.measurements[section][0]).filter(k=>typeof report.measurements[section][0][k]==='number');
    report.measurements[section+'Summary']=Object.fromEntries(keys.map(k=>{const a=report.measurements[section].map(x=>x[k]).sort((x,y)=>x-y);return [k,{min:a[0],median:a[2],max:a[4]}];}));
  }
  const out=resolve(ROOT,'docs/research/tryfan-pilot-s1-results.json');writeFileSync(out,encode(report));
  console.log(encode({logical:report.logical,summary:{build:report.measurements.buildsSummary,load:report.measurements.freshLoadsSummary}}));
} finally {
  if(!resolve(scratch).startsWith(resolve(tmpdir())+sep) || !basename(scratch).startsWith('meridian-s1-measure-')) throw new Error('Unsafe measurement cleanup');
  rmSync(scratch,{recursive:true,force:true});
}
