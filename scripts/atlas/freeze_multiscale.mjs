import {readFile,writeFile,mkdir,access} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {zoomForScale,igorStrength} from './multiscale_math.mjs';
const data=process.argv[2];if(!data)throw new Error('Supply meridian-data root');
let exists=false;try{await access('docs/atlas/multiscale-representation-plan.json');exists=true;}catch{}
if(exists)throw new Error('This audit plan is already frozen; do not overwrite after inspection.');
const scales=[128,32,8,2,.5,.125],stops=[[5.5,0],[7,.09],[9,.3],[11,.54],[12,.45],[13,.36],[14,.33],[15,.3],[16,.3]];
const sites=[{id:'tryfan',center:[-3.999,53.115],regime:'rugged ridge and gullies',evidence:'tryfan-second-region-proof.md'}, {id:'riffelhorn',center:[7.76121329,45.97910794],regime:'steep Alpine and glacier context',evidence:'swissimage-source-derived-baseline.md'}, {id:'downs',center:[-.766,50.908],regime:'broad rolling terrain',evidence:'native-relief-evaluation.md'}, {id:'cambridge',center:[.12,52.20],regime:'low relief',evidence:'native-relief-evaluation.md'}];
const plan={id:'atlas-multiscale-representation-v1',baseline:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),viewport:{width:1440,height:900},devicePixelRatio:1,scaleBasis:'Local spherical-Mercator tangent map-plane metres per CSS pixel, worldSize=512*2^zoom; not the whole pitched/terrain viewport.',scales,sites,scenes:[],terrainSpectrum:{spacingMetres:2,sideCells:512,wavelengthEdgesMetres:[4,16,64,256,1024],operation:'Read-only native terrain sampling on fixed 1024m squares at retained centres; remove least-squares plane; Hann-windowed FFT band RMS with Parseval closure. No terrain generalisation product, morphology test or causal accuracy attribution.'},productionHashes:{},limitations:['AWS and MapTiler effective information resolution unknown','Common captures are live external-unpinned products; camera reproducibility does not imply identical network pixels','Physical source information is not inferred from delivery levels or spectral energy']};
for(const site of sites){const fine=site.id==='tryfan'||site.id==='riffelhorn';for(const m of fine?scales:[128,8,.5])plan.scenes.push({id:`${site.id}-${m}m`,site:site.id,center:site.center,targetMetresPerCssPixel:m,zoom:zoomForScale(site.center[1],m),pitch:0,bearing:0,igorStrength:igorStrength(zoomForScale(site.center[1],m),stops)});if(fine)for(const m of [8,.5])plan.scenes.push({id:`${site.id}-${m}m-p55`,site:site.id,center:site.center,targetMetresPerCssPixel:m,zoom:zoomForScale(site.center[1],m),pitch:55,bearing:0,igorStrength:igorStrength(zoomForScale(site.center[1],m),stops)});}
const sources=execFileSync('git',['ls-files','src'],{encoding:'utf8'}).trim().split(/\r?\n/);
for(const f of sources)plan.productionHashes[f]=createHash('sha256').update(await readFile(f)).digest('hex');
const out=path.join(data,'experiments/atlas/multiscale-representation-v1');await mkdir(out,{recursive:true});
const file='docs/atlas/multiscale-representation-plan.json';const text=JSON.stringify(plan,null,2)+'\n';await writeFile(file,text);await writeFile(path.join(out,'frozen-plan.json'),text);
console.log(JSON.stringify({file,scenes:plan.scenes.length,productionFiles:sources.length,sha256:createHash('sha256').update(text).digest('hex')}));
