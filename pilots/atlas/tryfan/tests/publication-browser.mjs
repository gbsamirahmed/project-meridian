// Independent browser scene pin/refresh across real isolated U2 publication.
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdirSync,writeFileSync,mkdtempSync,rmSync,readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join,resolve,sep } from 'node:path';
import { forkBaseline,prepareMixedBaseline,publishUpdate } from '../updates.mjs';
import { STORE } from '../generations.mjs';
import { service } from './publication-harness.mjs';
import { encode,sha } from '../identity.mjs';
const dir=mkdtempSync(join(tmpdir(),'meridian-s5-browser-')),store=join(dir,'store'),out=join(STORE,'s5-qa');mkdirSync(out,{recursive:true});
let s,browser;try {
 forkBaseline(store);const old=prepareMixedBaseline({store});s=await service(store);browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1400,height:1150},deviceScaleFactor:1}),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().startsWith(s.url))requests.push(new URL(r.url()).pathname);});
 await page.goto(s.url);await page.locator('#status').filter({hasText:'Scene pinned'}).waitFor();
 await page.locator('#view').selectOption('summit');await page.locator('#summit').click();await page.locator('#status').filter({hasText:'Independent qualified evidence returned'}).waitFor();
 let answer=JSON.parse(await page.locator('#answer').textContent());assert.equal(answer.generation,old.generation);assert.equal(answer.answers.find(x=>x.property==='nrw-native').response.status,'excluded-by-context');assert.ok((await page.locator('#summary').innerText()).includes('excluded by controlled applicability'));assert.equal(await page.locator('#nrw').isDisabled(),true);
 await page.screenshot({path:join(out,'before.png')});
 const published=await publishUpdate({store,scenario:'U2'});
 await page.locator('#summit').click();await page.locator('#status').filter({hasText:'Independent qualified evidence returned'}).waitFor();answer=JSON.parse(await page.locator('#answer').textContent());assert.equal(answer.generation,old.generation);
 const split=requests.length;await page.locator('#refresh').click();await page.locator('#status').filter({hasText:'Scene pinned'}).waitFor();assert.equal((await page.locator('#generation').innerText()).split(' ').at(-1),published.generation);
 await page.locator('#summit').click();await page.locator('#status').filter({hasText:'Independent qualified evidence returned'}).waitFor();answer=JSON.parse(await page.locator('#answer').textContent());assert.equal(answer.generation,published.generation);assert.equal(await page.locator('#nrw').isDisabled(),false);assert.equal(answer.answers.find(x=>x.property==='derived-slope').response.answers[0].result.claim.result.value.value,32.918524028483965);assert.equal(answer.answers.find(x=>x.property==='nrw-native').response.answers[0].records[0].claim.native.fields.phase1_code,'D.1.1');
 await page.locator('#trace').click();await page.waitForFunction(()=>document.getElementById('provenance').textContent.includes('sources'));assert.equal(errors.length,0);assert.ok(!(await page.locator('body').innerText()).includes('Â·'),'UTF-8 display punctuation must remain intact');
 assert.ok(requests.slice(0,split).filter(p=>p.startsWith('/pilot/v1/g/')).every(p=>p.startsWith('/pilot/v1/g/'+old.generation+'/')));assert.ok(requests.slice(split).filter(p=>p.startsWith('/pilot/v1/g/')).every(p=>p.startsWith('/pilot/v1/g/'+published.generation+'/')));
 await page.screenshot({path:join(out,'after.png')});
 const receipt={schema:'atlas-tryfan-s5-browser/v1',before:old.generation,after:published.generation,oldSceneStayedPinned:true,explicitRefreshAtomicScene:true,errors,requests:requests.length,
  figures:Object.fromEntries(['before','after'].map(n=>[n,{sha256:sha(readFileSync(join(out,n+'.png'))),bytes:readFileSync(join(out,n+'.png')).length}])),manualInspection:'Executable checks only; separate visual inspection required'};
 writeFileSync(join(out,'browser.json'),encode(receipt));console.log(encode(receipt));
} finally {await browser?.close();await s?.close();assert.ok(resolve(dir).startsWith(resolve(tmpdir())+sep));rmSync(dir,{recursive:true,force:true});}
