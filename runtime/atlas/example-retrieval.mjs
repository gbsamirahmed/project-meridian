/** Real workflow through the public CLI, with explicit retained pins and disposable caches. */
import fs from 'node:fs';import path from 'node:path';import {spawnSync} from 'node:child_process';import {fileURLToPath} from 'node:url';
if(!process.argv[2]){console.error('Usage: node runtime/atlas/example-retrieval.mjs CONFIG.json');process.exit(1)}
try{
 const f=path.resolve(process.argv[2]),input=JSON.parse(fs.readFileSync(f,'utf8')),keys=['dataRoot','publicationRoot','catalogueRoot','python'];
 if(keys.some(k=>typeof input[k]!=='string'||!input[k]))throw Error('Four explicit paths required; see runtime/atlas/README.md');
 const c=Object.fromEntries(keys.map(k=>[k,path.resolve(path.dirname(f),input[k])])),cli=fileURLToPath(new URL('./cli.ts',import.meta.url));
 function run(command,extra=[],generation=input.generation){const p=spawnSync(process.execPath,[cli,...command,'--data-root',c.dataRoot,'--publication-root',c.publicationRoot,'--catalogue',c.catalogueRoot,'--python',c.python,'--json',...(generation?['--generation',generation]:[]),...extra],{encoding:'utf8',maxBuffer:32*1024*1024});if(p.status!==0)throw Error(p.stderr.trim()||'CLI failed');return JSON.parse(p.stdout)}
 const validated=run(['validate']),built=run(['catalogue','build'],['--qualified']);run(['catalogue','verify'],['--qualified']);
 const answers=[];
 for(const query of [{},{evidenceClass:'source'},{evidenceClass:'derived'},{region:'riffelhorn',feature:'glaciers:683'},{region:'riffelhorn',point:[2624350.25,1091350.25],crs:'EPSG:2056'},{evidenceClass:'derived',time:{role:'evidence-epoch',unknown:true}}])answers.push({query,answer:run(['retrieve'],['--query',JSON.stringify(query)])});
 const first=answers[2].answer.results.find(r=>r.family==='planar-area-ratio');
 if(first)answers.push({query:'inspect derived identity',answer:run(['retrieve'],['--query',JSON.stringify({identity:first.identity})])},{query:'exact transitive lineage',answer:run(['retrieve'],['--query',JSON.stringify({relatedTo:{identity:first.identity,direction:'inputs',depth:'transitive'}})])});
 let historical=null;
 if(input.historicalGeneration){run(['catalogue','build'],['--qualified'],input.historicalGeneration);historical=run(['retrieve'],['--query','{}'],input.historicalGeneration);run(['catalogue','build'],['--qualified'])}
 console.log(JSON.stringify({validated,built,answers,historical},null,2));
}catch(e){console.error(e.message);process.exitCode=1}
