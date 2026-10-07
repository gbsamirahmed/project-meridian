// Isolated lifecycle-fixture restart only; never publishes or scans unaccepted states.
import { readFileSync } from 'node:fs';
import { methods } from '../derivations.mjs';
import { load } from '../generations.mjs';
import { encode,requireThat } from '../identity.mjs';
const [store,file]=process.argv.slice(2);
requireThat(file && !file.toLowerCase().includes('meridian-private'),'invalid-fixture','Private fixture paths excluded before I/O');
const fixture=JSON.parse(readFileSync(file,'utf8')),snapshot=load(store,{generation:fixture.generation}),m=await methods();
try{const graph=m.validate(fixture.understanding,snapshot.value.catalogue),replay=m.replay(fixture.understanding,snapshot.value.catalogue,snapshot.locators),assessments=m.assess(fixture.understanding,snapshot.value.catalogue,snapshot.locators);
 process.stdout.write(encode({publishedGeneration:snapshot.generation,notPublished:true,results:fixture.understanding.results,graph,checks:replay.checks,assessments}));
}finally{await m.close();}
