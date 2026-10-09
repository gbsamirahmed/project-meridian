/** Reproducible workflow using only supported runtime CLI commands. */
import fs from 'node:fs';import path from 'node:path';import {spawnSync} from 'node:child_process';import {fileURLToPath} from 'node:url';
if(!process.argv[2]){console.error('Usage: node runtime/atlas/example-exe.mjs CONFIG.json');process.exit(1)}
else try{
 const input=JSON.parse(fs.readFileSync(path.resolve(process.argv[2]),'utf8')),R=fileURLToPath(new URL('../../',import.meta.url));
 const flags=Object.entries({'--data-root':input.dataRoot,'--publication-root':input.publicationRoot,'--catalogue':input.catalogueRoot,'--python':input.python}).flat();
 function run(command,extra=[]){const p=spawnSync(process.execPath,[path.join(R,'runtime/atlas/cli.ts'),...command,...flags,...extra,'--json'],{cwd:R,encoding:'utf8',maxBuffer:32*1024*1024});if(p.status!==0)throw Error(p.stderr.trim()||'Runtime CLI failed');return JSON.parse(p.stdout)}
 if(input.sourcePublication)run(['world','init'],['--source-publication',input.sourcePublication]);
 const before=run(['validate']),inspection=run(['evidence','inspect'],['--family','exe-water']),file=path.join(path.dirname(input.publicationRoot),'exe-request.json');
 fs.writeFileSync(file,JSON.stringify(inspection.templates.exe,null,2));
 const plan=run(['update','plan'],['--request',file]),stage=run(['evidence','register'],['--family','exe-water','--request',file]);
 if(stage.status!=='no-op'){run(['update','validate'],['--stage',stage.generation]);run(['update','publish'],['--stage',stage.generation])}
 const built=run(['catalogue','build'],['--qualified']);run(['catalogue','verify'],['--qualified']);
 const selected=run(['retrieve'],['--query',JSON.stringify({region:'exe',area:[296600,86550,296800,86750],crs:'EPSG:27700',waterTime:{role:'observation',start:'2024-03-01',end:'2024-03-31'}})]);
 const related=run(['retrieve'],['--query',JSON.stringify({relatedTo:{identity:'exe:2024-03:support',direction:'inputs',depth:'direct'}})]);
 const all=run(['retrieve'],['--query','{}']);
 run(['catalogue','build'],['--qualified','--generation',before.generation]);
 const old=run(['retrieve'],['--generation',before.generation,'--query','{"region":"exe"}']);
 const latest=run(['evidence','inspect']),revision={...inspection.templates.exe,operation:'knowledge',expectedGeneration:all.generation,expectedRevision:latest.registrations.exe.identity,explanation:'Administrative retained-source accountability clarification; no physical observation or classification change.'};
 fs.writeFileSync(file,JSON.stringify(revision,null,2));const revised=run(['evidence','revise'],['--request',file]);run(['update','publish'],['--stage',revised.generation]);
 fs.unlinkSync(path.join(input.catalogueRoot,'current.json'));const rebuilt=run(['catalogue','build'],['--qualified']);const current=run(['retrieve'],['--query','{"region":"exe"}']);
 console.log(JSON.stringify({before:before.generation,registered:all.generation,revised:current.generation,plan,built,rebuilt,selected:selected.results.map(r=>r.identity),inputs:related.results.map(r=>r.identity),historicalExe:old.results.length,currentExe:current.results.length,regions:Object.keys(all.regions)},null,2));
}catch(error){console.error(error.message);process.exitCode=1}
