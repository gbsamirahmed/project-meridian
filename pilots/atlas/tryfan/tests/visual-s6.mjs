// Actual isolated browser consumer acceptance; browser reads only HTTP routes.
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdirSync,readFileSync,writeFileSync } from 'node:fs';
import { join,resolve } from 'node:path';
import { sha,encode } from '../identity.mjs';
import { STORE } from '../generations.mjs';
const url=process.argv[2]??'http://127.0.0.1:4191',out=join(STORE,'s6-qa');mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1400,height:1150},deviceScaleFactor:1}),errors=[],requests=[];
page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().startsWith(url))requests.push(new URL(r.url()).pathname);});
try {
 await page.goto(url);await page.getByRole('status').filter({hasText:'Scene pinned'}).waitFor();
 const generation=(await page.locator('#generation').innerText()).split(' ').at(-1),views=[];
 for(const view of ['full','summit','southern','north']) {
  await page.locator('#view').selectOption(view);const file=join(out,view+'.png');await page.locator('#map').screenshot({path:file});views.push({view,width:960,height:720,sha256:sha(readFileSync(file)),bytes:readFileSync(file).length});
 }
 await page.locator('#summit').click();await page.getByRole('status').filter({hasText:'Independent qualified evidence returned'}).waitFor();
 const answer=JSON.parse(await page.locator('#answer').textContent());assert.equal(answer.generation,generation);assert.equal(answer.answers.length,6);assert.ok((await page.locator('#tile').innerText()).includes('exact z14'));
 await page.locator('#trace').click();await page.waitForFunction(()=>document.getElementById('provenance').textContent.includes('sources'));
 await page.locator('#view').selectOption('full');await page.locator('#map').click({position:{x:450,y:340}});await page.getByRole('status').filter({hasText:'Independent qualified evidence returned'}).waitFor();
 assert.equal(JSON.parse(await page.locator('#answer').textContent()).generation,generation);
 await page.mouse.move(350,400);await page.mouse.wheel(0,-100);await page.mouse.down();await page.mouse.move(380,430);await page.mouse.up();
 await page.locator('#nrw').uncheck();await page.locator('#nrw').check();await page.locator('#appearance').uncheck();await page.locator('#appearance').check();
 await page.locator('#refresh').click();await page.getByRole('status').filter({hasText:'Scene pinned'}).waitFor();assert.equal((await page.locator('#generation').innerText()).split(' ').at(-1),generation);assert.ok(!(await page.locator('#cell').innerText()).includes('Native row'));assert.ok((await page.locator('#tile').innerText()).includes('No selected'));
 assert.ok((await page.locator('#rights').innerText()).includes('worldcover'));assert.equal(errors.length,0);
 const dataPaths=requests.filter(p=>p.startsWith('/pilot/')&&!p.endsWith('/current'));assert.ok(dataPaths.every(p=>p.startsWith('/pilot/v1/g/'+generation+'/')));
 const receipt={schema:'atlas-tryfan-s6-browser-qa/v1',generation,viewport:[1400,1150],mapDimensions:[960,720],views,errors,requests:requests.length,allDataGenerationPinned:true,panZoomClickLayersProvenanceRefresh:true,manualInspection:'Pending explicit visual review; this executable verifies functionality only'};
 writeFileSync(join(out,'browser.json'),encode(receipt));console.log(encode(receipt));
 await page.locator('#view').selectOption('summit');await page.locator('#summit').click();await page.getByRole('status').filter({hasText:'Independent qualified evidence returned'}).waitFor();await page.screenshot({path:join(out,'consumer.png')});await page.locator('.inspectors').screenshot({path:join(out,'inspectors.png')});
}finally{await browser.close();}
