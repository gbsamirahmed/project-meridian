// Optional external-evidence summarizer. CI imports only the lightweight metadata fixture.
import {readFile,writeFile,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createServer} from 'vite';
import path from 'node:path';
import assert from 'node:assert/strict';
const data=process.argv[2];if(!data)throw new Error('Provide meridian-data root');
const root=path.join(data,'experiments/atlas/tryfan-second-region-proof'),json=async p=>JSON.parse(await readFile(p,'utf8'));
const a=await json(path.join(data,'derived/atlas/tryfan/tryfan-welsh-regional-v2/manifest.json'));
const b=await json(path.join(data,'derived/atlas/tryfan/tryfan-welsh-regional-v2-rebuild/manifest.json'));assert.deepEqual(a,b);
const captures={};
for(const provider of ['hierarchy','aws']){
 const r=await json(path.join(root,'captures',provider+'.json'));
 assert.deepEqual(r.pageErrors,[]);assert.equal(r.failure,undefined);assert.ok(r.requests.every(row=>row.status===200));
 const counts={};for(const request of r.requests){const key=`${request.decision.family}/${request.z}`;counts[key]=(counts[key]??0)+1;}
 captures[provider]={requests:r.requests.length,responses:r.responses.length,requestCounts:counts,failures:r.failures,productionHashes:r.productionHashes,
   scenes:r.scenes.map(s=>({camera:s.scene,filename:s.filename,sha256:s.sha256,elevationIncludesExaggeration:s.state.elevation,actualDEMLevels:[...new Set(s.state.actualDEMs.map(d=>d.z))].sort((x,y)=>x-y)})),navigationSequences:r.navigation.length,
   movingCaptures:await Promise.all((await readdir(path.join(root,'captures'))).filter(f=>f.endsWith(`--${provider}.png`)&&f.startsWith('moving-')).map(async f=>({path:f,sha256:createHash('sha256').update(await readFile(path.join(root,'captures',f))).digest('hex')})))};
}
assert.deepEqual(captures.hierarchy.productionHashes,captures.aws.productionHashes);
const s=await createServer({configFile:false,logLevel:'silent',server:{middlewareMode:true}});
const load=p=>s.ssrLoadModule(`/src/atlas/${p}.ts`);
const {createTryfanTerrainProof}=await load('terrain/metadata/tryfanTerrainProof');const {selectTerrain}=await load('terrain/runtime/terrainSelector');const {registerTerrainHierarchy}=await load('terrain/runtime/terrainRegistry');const {adaptTerrainToMapLibre}=await load('map/terrainDeliveryAdapter');
const r=createTryfanTerrainProof(),q=(z=17,coordinates=[-3.999,53.115])=>({location:{coordinates,crs:'OGC:CRS84'},scale:{scheme:r.hierarchy.common.levelScheme,requestedLevel:`z${z}`},provenanceRequirement:'product-lineage'});
const requests={fine:q(),parent:{...q(14),previous:{family:'welsh-regional',level:'z17'}},outside:{...q(17,[-4.023,53.115]),previous:{family:'welsh-regional',level:'z17'}},coarse:q(13),commonOnly:{...q(15),family:r.hierarchy.common.id},overzoom:q(18)};
const decisions=Object.fromEntries(Object.entries(requests).map(([id,request])=>{const selected=selectTerrain(r,request);return[id,{request,selected,delivery:adaptTerrainToMapLibre(r,selected)}];}));
const h=structuredClone(r.hierarchy),fine=h.regional[0].levels.find(l=>l.id==='z17');fine.support={state:'absent',validSupport:fine.support.validSupport,interpretation:'Simulated missing child; retained source/product unchanged.'};
const absent=registerTerrainHierarchy(h,r.options),selected=selectTerrain(absent,q());decisions.missingFine={request:q(),selected,delivery:adaptTerrainToMapLibre(absent,selected)};
await s.close();
const checks=await json(path.join(root,'numerical-checks.json'));
const result={baseline:'ba24e54',classification:'SUCCESS',generationDate:'2026-10-05',productIdentity:a.identity,tileCount:a.files.length,tileBytes:a.tileBytes,workingBytes:a.workingBytes,source:a.source,sourceAccess:await json(path.join(root,'source-evidence/current-access.json')),deterministicRebuild:'All manifest, tile, working and support hashes identical',numerical:checks,decisions,captures};
await writeFile('docs/atlas/tryfan-second-region-proof.json',JSON.stringify(result,null,2)+'\n');
console.log('RECORDED',result.classification,result.tileCount);
