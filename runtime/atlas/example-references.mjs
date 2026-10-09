/** Complete CLI-only workflow; no manual research runner required. */
import fs from 'node:fs';import path from 'node:path';import {spawnSync} from 'node:child_process';
try{
 if(!process.argv[2])throw Error('Usage: node runtime/atlas/example-references.mjs CONFIG.json');
 const c=JSON.parse(fs.readFileSync(path.resolve(process.argv[2]),'utf8')),R=path.resolve(import.meta.dirname,'../..');
 const flags=Object.entries({'--data-root':c.dataRoot,'--publication-root':c.publicationRoot,'--catalogue':c.catalogueRoot,'--python':c.python}).flat();
 const run=(args,extra=[])=>{const p=spawnSync(process.execPath,[path.join(R,'runtime/atlas/cli.ts'),...args,...flags,...extra,'--json'],{cwd:R,encoding:'utf8',maxBuffer:16e6});if(p.status!==0)throw Error(p.stderr.trim());return JSON.parse(p.stdout)};
 if(c.sourcePublication)run(['world','init'],['--source-publication',c.sourcePublication]);
 const before=run(['validate']),inspection=run(['evidence','inspect'],['--family','exe-references']),request=path.join(path.dirname(c.publicationRoot),'references-request.json');
 fs.writeFileSync(request,JSON.stringify(inspection.templates.exeReferences));run(['update','plan'],['--request',request]);const stage=run(['evidence','register'],['--family','exe-references','--request',request]);
 if(stage.status!=='no-op'){run(['update','validate'],['--stage',stage.generation]);run(['update','publish'],['--stage',stage.generation])}
 const b=run(['catalogue','build'],['--qualified']);run(['catalogue','verify'],['--qualified']);
 const all=run(['retrieve'],['--query','{}']),selected=run(['retrieve'],['--query',JSON.stringify({region:'exe',area:[296600,86550,296800,86750],crs:'EPSG:27700'})]);
 const habitat=run(['retrieve'],['--query',JSON.stringify({families:['priority-habitat'],referenceTime:{role:'survey',unknown:true}})]);
 const planning=run(['retrieve'],['--query',JSON.stringify({nativeClassification:'FZ2',referenceTime:{role:'effective',unknown:true}})]);
 run(['catalogue','build'],['--qualified','--generation',before.generation]);const historical=run(['retrieve'],['--generation',before.generation,'--query','{}']);
 const info=run(['evidence','inspect']),revision={...inspection.templates.exeReferences,operation:'knowledge',expectedGeneration:all.generation,expectedRevision:info.registrations.exeReferences.identity,explanation:'Administrative accountability only; no ecological, legal or physical change.'};
 fs.writeFileSync(request,JSON.stringify(revision));const updated=run(['evidence','revise'],['--request',request]);run(['update','publish'],['--stage',updated.generation]);fs.unlinkSync(path.join(c.catalogueRoot,'current.json'));
 const rebuilt=run(['catalogue','build'],['--qualified']),current=run(['retrieve'],['--query','{}']);
 console.log(JSON.stringify({before:before.generation,current:current.generation,records:all.results.length,priorRecords:historical.results.length,habitat:habitat.results.length,fz2:planning.results.length,pointFamilies:[...new Set(selected.results.map(r=>r.family))],catalogue:b,rebuilt},null,2));
}catch(error){console.error(error.message);process.exitCode=1}
