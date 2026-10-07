import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { resolve,join,sep } from 'node:path';
import { mkdtempSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { forkBaseline,publishUpdate } from '../updates.mjs';
import { load,currentId } from '../generations.mjs';
import { service,signature } from './publication-harness.mjs';
test('new CLI and service reproduce persisted current without construction globals',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'meridian-s5-restart-')),store=join(dir,'store');let server;
 try {
  forkBaseline(store);const published=await publishUpdate({store});
  const inspect=spawnSync(process.execPath,[resolve(import.meta.dirname,'../cli.mjs'),'validate','--store',store],{encoding:'utf8',timeout:30000});assert.equal(inspect.status,0,inspect.stderr);assert.equal(JSON.parse(inspect.stdout).generation,published.generation);
  server=await service(store);const consumer=spawnSync(process.execPath,[resolve(import.meta.dirname,'../client/http-consumer.mjs'),server.url],{encoding:'utf8',timeout:30000,maxBuffer:2e6});assert.equal(consumer.status,0,consumer.stderr);
  const value=JSON.parse(consumer.stdout);assert.equal(value.generation,currentId(store));assert.equal(signature(value).slope,32.918524028483965);assert.equal(load(store).value.understanding.results.length,6);
 } finally {await server?.close();assert.ok(resolve(dir).startsWith(resolve(tmpdir())+sep));rmSync(dir,{recursive:true,force:true});}
});
