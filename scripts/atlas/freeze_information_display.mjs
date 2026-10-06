import {readFile,writeFile,mkdir,access} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
const data=process.argv[2];if(!data)throw new Error('Supply meridian-data root');
const file='docs/atlas/information-display-plan.json';
try{await access(file);throw new Error('Plan already frozen; do not overwrite');}catch(e){if(e.code!=='ENOENT')throw e;}
const bytes=await readFile('docs/atlas/multiscale-representation-plan.json'),previous=JSON.parse(bytes);
const hash=b=>createHash('sha256').update(b).digest('hex');
const scene=id=>structuredClone(previous.scenes.find(s=>s.id===id));
const tasks=[];
function add(mode,id,dprs,appearances=['terrain']){tasks.push({mode,scene:scene(id),dprs,appearances});}
add('aws','tryfan-0.125m',[1,2,3]);add('aws','downs-128m',[1]);add('aws','cambridge-8m',[1]);
add('tryfan-regional','tryfan-0.5m',[1,2,3]);
add('riffelhorn-regional','riffelhorn-0.5m',[1,2,3]);add('riffelhorn-regional','riffelhorn-8m',[1]);
const moderate=scene('riffelhorn-8m');moderate.id='riffelhorn-8m-p35';moderate.pitch=35;
tasks.push({mode:'riffelhorn-regional',scene:moderate,dprs:[1],appearances:['terrain']});
add('riffelhorn-regional','riffelhorn-8m-p55',[1]);
add('riffelhorn-appearance','riffelhorn-0.125m',[1,2,3],['common','regional']);
add('riffelhorn-appearance','riffelhorn-8m-p55',[1],['common','regional']);
const rendererFiles=['ui/map.ts','render/terrain.ts','tile/terrain_tile_manager.ts','tile/tile_manager.ts','geo/projection/covering_tiles.ts','webgl/render_to_texture.ts','webgl/draw/draw_raster.ts','webgl/draw/draw_terrain.ts','webgl/texture.ts','shaders/glsl/_prelude.vertex.glsl','shaders/glsl/hillshade_prepare.fragment.glsl'];
const rendererHashes={};for(const f of rendererFiles)rendererHashes[f]=hash(await readFile('node_modules/maplibre-gl/src/'+f));
const plan={id:'atlas-information-display-v1',baseline:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),priorCameraPlanSha256:hash(bytes),viewport:previous.viewport,tasks,expectedCaptures:tasks.reduce((n,t)=>n+t.dprs.length*t.appearances.length,0),productionHashes:previous.productionHashes,rendererHashes,
questions:['Does requested DPR change actual framebuffer, loaded data levels, mesh or RTT size?','How do finite local map/surface Jacobians vary with pitch, orientation and viewport position?','Which ratios are knowable without guessing source information or perceptual thresholds?'],
probes:{xFractions:[.4,.55,.7],yFractions:[.25,.5,.75],centralDifferenceCssPixels:[1,2],normalBasis:'Physical heights divide displayed queries by 1.45; spherical local ENU; keep rendered metric separately',sensitivityFlagRelativePrincipalChange:.25,roundTripFlagCssPixels:2,interpretation:'Flags mark limitations of the approximate diagnostic, not eligibility/quality thresholds'},
controls:{geometry:'Existing AWS or immutable benchmark regional configuration; fixed for each DPR/appearance comparison; observe actual LOD rather than force it',exaggeration:1.45,igor:'Unchanged stock production operator/policy, no relief hook; satellite suppressed',imagery:'Existing satellite-v2 or immutable SWISSIMAGE baseline; no preparation/correction'},
limits:['Only pitch35 is added as a predeclared moderate control to existing pitch0/55; no camera tuning','DPR3 may be clamped by unchanged maxCanvasSize/GPU; measure actual canvas, depth and screenshot dimensions','Finite unproject/query/project diagnostics are not exact mesh derivatives or acquisition footprints; retain sensitivity and round-trip errors','Samples per device pixel are sampling ratios, never confidence, accuracy or human legibility','No learned optical cutoff, no automatic source ranking, no zoom blocking or filtering policy','No interactive performance or visibility/reconstruction test']};
const text=JSON.stringify(plan,null,2)+'\n';const out=path.join(data,'experiments/atlas/information-display-v1');await mkdir(out,{recursive:true});await writeFile(file,text);await writeFile(path.join(out,'frozen-plan.json'),text);console.log(JSON.stringify({captures:plan.expectedCaptures,sha256:hash(text)}));
