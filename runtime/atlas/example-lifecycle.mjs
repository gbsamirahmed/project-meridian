/** Runnable developer example using public CLI commands, not research harnesses. */
import fs from 'node:fs';import path from 'node:path';import{spawnSync}from'node:child_process';
import{fileURLToPath}from'node:url';
const file=path.resolve(process.argv[2]??'');
if(!process.argv[2]){console.error('Usage: node runtime/atlas/example-lifecycle.mjs PATH-TO-CONFIG.json');process.exit(1)}
const input=JSON.parse(fs.readFileSync(file,'utf8')),dir=path.dirname(file),cli=fileURLToPath(new URL('./cli.ts',import.meta.url));
const keys=['dataRoot','publicationRoot','catalogueRoot','python','sourcePublication'];
if(keys.some(k=>typeof input[k]!=='string')){console.error('Config requires dataRoot, publicationRoot, catalogueRoot, python, sourcePublication.');process.exit(1)}
const c=Object.fromEntries(keys.map(k=>[k,path.resolve(dir,input[k])]));
function run(command,extra=[]){const p=spawnSync(process.execPath,[cli,...command,'--data-root',c.dataRoot,'--publication-root',c.publicationRoot,'--catalogue',c.catalogueRoot,'--python',c.python,'--json',...extra],{encoding:'utf8',maxBuffer:32*1024*1024});if(p.status!==0)throw Error(p.stderr.trim()||'CLI process failed');return JSON.parse(p.stdout)}
try{
 const initialized=run(['world','init'],['--source-publication',c.sourcePublication]);
 const first=run(['derive','stage']);run(['stage','validate'],['--stage',first.generation]);run(['stage','publish'],['--stage',first.generation]);
 const sources=first.policy.sources,key=Object.keys(sources).find(k=>sources[k].native.bounds[0]===2624000&&sources[k].native.bounds[1]===1091000);
 const change=JSON.stringify({notice:{key,bounds:[2624350,1091350,2624350.5,1091350.5],text:'Controlled administrative qualification correction; no physical observation or change'}});
 const inspected=run(['derive','inspect'],['--change',change]),second=run(['derive','stage'],['--change',change]);
 run(['stage','validate'],['--stage',second.generation]);run(['stage','publish'],['--stage',second.generation]);
 const build=run(['catalogue','build']),native=run(['query'],['--query',JSON.stringify({region:'tryfan'})]);
 const latest=run(['derived']),old=run(['derived'],['--generation',first.generation]);
 console.log(JSON.stringify({initialized,initialGeneration:first.generation,currentGeneration:second.generation,affected:inspected.affected,reused:second.reused,catalogue:build,nativeResultCount:native.results.length,currentDerived:latest,previousDerived:old},null,2));
}catch(e){console.error(e.message);process.exitCode=1}
