// Deliberate corruption only in owned fixture copies, never retained evidence.
import fs from 'node:fs';import {join,resolve} from 'node:path';
import {install,request,digest} from './runtime.mjs';
const plan=JSON.parse(fs.readFileSync(new URL('./plan.json',import.meta.url))),[store,variant,scenario]=process.argv.slice(2);
if(!resolve(store).startsWith(resolve(plan.stateRoot)+'/')&&!resolve(store).startsWith(resolve(plan.stateRoot)+'\\'))throw Error('Failure fixture outside isolated experiment');
const init=install({variant,expectedHash:plan.authoritativeHashes['pilots/atlas/tryfan/generations.mjs']}),{G,I}=await init(),{openDelivery}=await import('../../../pilots/atlas/tryfan/delivery.mjs');
const current=G.currentId(store),body=JSON.parse(fs.readFileSync(join(store,'generations',current+'.json')));let oldest=current;
while(true){const value=JSON.parse(fs.readFileSync(join(store,'generations',oldest+'.json')));if(!value.parent)break;oldest=value.parent;}
let selected,service;
if(scenario==='corrupt-ancestor')fs.appendFileSync(join(store,'generations',oldest+'.json'),' ');
if(scenario==='missing-artifact'){const asset=body.serving.assets.find(a=>a.origin.kind==='materialized');const file=join(store,'artifacts',asset.id+(asset.mime==='image/png'?'.png':'.json'));fs.unlinkSync(file);}
if(scenario==='orphan'){
 const value={...body,parent:current},bytes=I.encode(G.canonicalGeneration(value));selected=I.sha(bytes);
 fs.writeFileSync(join(store,'generations',selected+'.json'),bytes,{flag:'wx'});fs.copyFileSync(join(store,'locators',current+'.json'),join(store,'locators',selected+'.json'));
}
if(scenario==='unknown')selected='0'.repeat(64);
try{
 service=await openDelivery({store});await request(()=>service.pin());
 if(scenario==='between-requests'){
  await request(()=>service.query(current,{property:'worldcover-native',place:{crs:'EPSG:27700',point:[266405,359387]}}));
  fs.appendFileSync(join(store,'generations',oldest+'.json'),' ');
 }
 await request(()=>selected?service.pin(selected):service.query(current,{property:'worldcover-native',place:{crs:'EPSG:27700',point:[266405,359387]}}));
 throw Error('Required failure was not detected');
}catch(error){
 if(!error.code)throw error;
 console.log(JSON.stringify({scenario,variant,code:error.code,current:G.currentId(store),expectedCurrent:current,rootUnchanged:G.currentId(store)===current,fixture:resolve(store),loaderHash:plan.authoritativeHashes['pilots/atlas/tryfan/generations.mjs'],diagnosticSha:digest(Buffer.from(error.code))}));
}finally{await service?.close();}
