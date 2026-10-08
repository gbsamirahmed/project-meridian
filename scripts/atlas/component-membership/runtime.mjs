// Hooks are limited to proof processes; original modules are guarded byte-for-byte.
import fs from 'node:fs';import {registerHooks,syncBuiltinESMExports} from 'node:module';
import * as core from './core.mjs';import {sha} from '../../../pilots/atlas/tryfan/identity.mjs';
const key=Symbol.for('meridian.component-membership-proof');
export async function initialize({hooks=false,meter=true}={}){
 if(meter){const original=fs.readFileSync;fs.readFileSync=function(file,...args){const body=original.call(this,file,...args),s=core.scope.getStore();if(s){const p=String(file).replaceAll('\\','/');const kind=p.includes('/components/')?'components':p.includes('/publications/')?'publications':p.includes('/membership/')?'membership':p.endsWith('/current.json')?'root':p.includes('/artifacts/')?'portrayal':p.includes('meridian-data')?'retained':'runtime';const r=s.reads[kind]??={calls:0,bytes:0};r.calls++;r.bytes+=typeof body==='string'?Buffer.byteLength(body):body.length;}return body;};syncBuiltinESMExports();}
 if(hooks){globalThis[key]=core;registerHooks({load(url,context,next){const r=next(url,context);if(!url.endsWith('/pilots/atlas/tryfan/generations.mjs')&&!url.endsWith('/pilots/atlas/tryfan/delivery.mjs'))return r;let source=String(r.source);
  if(url.endsWith('/pilots/atlas/tryfan/generations.mjs')){
   if(sha(source)!==core.plan.authoritativeHashes['pilots/atlas/tryfan/generations.mjs'])throw Error('Frozen generation module differs');
   const a=source.indexOf('export function currentId('),b=source.indexOf('function withWriter(',a);
   source=source.slice(0,a)+`export function currentId(dir){return globalThis[Symbol.for('meridian.component-membership-proof')].root(dir).generation;}\nexport function load(dir,options={}){return globalThis[Symbol.for('meridian.component-membership-proof')].load(dir,options);}\n`+source.slice(b);
  }
  if(url.endsWith('/pilots/atlas/tryfan/delivery.mjs')){
   if(sha(source)!==core.plan.authoritativeHashes['pilots/atlas/tryfan/delivery.mjs'])throw Error('Frozen delivery module differs');
   const a=source.indexOf(' function published(id)'),b=source.indexOf(' async function pin(id)',a);if(a<0||b<0)throw Error('Guarded serving hook absent');
   source=source.slice(0,a)+' function published(id){return load(store,{generation:id,dataRoot,verify:false});}\n'+source.slice(b);
  }
  return {...r,source};
 }});}
 const G=await import('../../../pilots/atlas/tryfan/generations.mjs');core.configure(G);return {G,core};
}
