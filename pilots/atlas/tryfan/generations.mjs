// Local single-writer publication. No server, scheduler, domain resolver or GC.
import { mkdirSync, readFileSync, openSync, closeSync, writeFileSync, fsyncSync, renameSync, unlinkSync, existsSync, realpathSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { validateDependencies } from './dependencies.mjs';
import { FORMAT, PilotError, requireThat, fields, encode, sha, json } from './identity.mjs';
import { canonicalCatalogue, validateCatalogue, verifyArtifacts, DATA, ROOT } from './catalogue.mjs';
export const STORE = resolve(DATA,'experiments/atlas/tryfan-regional-pilot-v1');
const hashPattern=/^[a-f0-9]{64}$/;
export function storePath(dir) {
  const requested=resolve(dir);
  requireThat(!requested.toLowerCase().includes('meridian-private'),'invalid-store','Private paths are excluded before filesystem inspection');
  const path=existsSync(requested)?realpathSync(requested):requested,lower=path.toLowerCase().replaceAll('\\','/');
  const data=DATA.toLowerCase().replaceAll('\\','/'),repo=ROOT.toLowerCase().replaceAll('\\','/'),runtime=data+'/experiments/atlas/tryfan-regional-pilot-v1';
  requireThat(!lower.includes('meridian-private') && !lower.startsWith(repo+'/') && lower!==repo && lower!==data &&
    !repo.startsWith(lower+'/') && !data.startsWith(lower+'/') &&
    (!lower.startsWith(data+'/') || lower===runtime || lower.startsWith(runtime+'/')),
    'invalid-store','Store must be isolated from retained evidence/production/private data');
  return path;
}
function writeDurable(file,body) {
  const fd=openSync(file,'wx');
  try { writeFileSync(fd,body);fsyncSync(fd); } finally { closeSync(fd); }
}
function writeImmutable(file,body) {
  if (existsSync(file)) requireThat(readFileSync(file,'utf8')===body,'immutable-conflict','Existing immutable object differs: '+file);
  else writeDurable(file,body);
}
function idCheck(id) {requireThat(typeof id==='string' && hashPattern.test(id),'invalid-generation-id','Invalid generation address');}
function opCheck(id) {requireThat(typeof id==='string' && /^[a-f0-9-]{36}$/.test(id),'invalid-operation','Invalid operation address');}
export function validateGeneration(value) {
  fields(value,['format','semanticContract','capabilities','core','parent','catalogue'],['understanding','knowledge']);
  requireThat(value.format===FORMAT,'unknown-generation-schema','Unsupported generation schema');
  requireThat(value.semanticContract==='atlas-semantic-evidence/v1','contract-invalid','Unexpected frozen contract version');
  fields(value.capabilities,['registration','queries','derivations','serving','mixedFamilyUpdate']);
  requireThat(value.capabilities.registration===true && value.capabilities.serving===false && value.capabilities.mixedFamilyUpdate===false &&
    value.capabilities.queries===!!value.understanding && value.capabilities.derivations===!!value.understanding, 'unsupported-capability','Only registration or complete S3 baseline capabilities');
  validateCatalogue(value.catalogue);
  if(value.understanding) {
    requireThat(value.understanding.stage==='common','unsupported-capability','S3 publishes baseline only; live applicability updates remain deferred');
    validateDependencies(value.understanding,value.catalogue);
    requireThat(value.knowledge?.contract==='atlas-semantic-evidence/v1' && sha(encode(value.knowledge))==='9bbaa0c10db1a1f03810ef3a4e708eca09e25a94c9a8474f07ab944e162438a5','required-state-unavailable','Exact retained native knowledge closure required');
    requireThat(sha(encode(value.understanding.terrain))==='4ee2af71dbf6978b11b4b8249d25fae83862209d113349a1f66e4a8cd36c4fdd','invalid-hierarchy','Exact common G0 applicability required');
  } else requireThat(!value.knowledge,'unsupported-capability','Registration seed cannot advertise incomplete knowledge');
  fields(value.core,['crs','bounds','boundary']);
  requireThat(value.core.crs==='EPSG:27700' && encode(value.core.bounds)===encode([264900,357800,267900,360800]) &&
    typeof value.core.boundary==='string' && value.core.boundary.length,'invalid-scope','Core support differs from bounded pilot');
  requireThat(value.parent===null || (typeof value.parent==='string' && hashPattern.test(value.parent)),'invalid-reference','Invalid parent generation');
  return value;
}
export function canonicalGeneration(value) {
  validateGeneration(value);
  return {...value,catalogue:canonicalCatalogue(value.catalogue)};
}
export function generationId(value) {return sha(encode(canonicalGeneration(value)));}
export function currentId(dir) {
  const file=join(storePath(dir),'current.json');
  requireThat(existsSync(file),'store-absent','No published generation; register explicitly');
  let root;try {root=json(file,'invalid-published-root');} catch {throw new PilotError('invalid-published-root','Cannot decode published root');}
  fields(root,['format','generation'],[],'invalid-published-root');
  requireThat(root.format===FORMAT && typeof root.generation==='string' && hashPattern.test(root.generation),'invalid-published-root','Unknown root schema/address');
  return root.generation;
}
export function load(dir,{generation,dataRoot=DATA,locators,verify=true}={}) {
  const start=performance.now(), store=storePath(dir),id=generation??currentId(store);idCheck(id);
  const file=join(store,'generations',id+'.json');
  requireThat(existsSync(file),'generation-missing','Generation is not retained: '+id);
  let body;try {body=readFileSync(file,'utf8');} catch {throw new PilotError('generation-unavailable','Generation cannot be read');}
  requireThat(sha(body)===id,'generation-integrity','Immutable generation bytes changed');
  let value;try {value=JSON.parse(body);} catch {throw new PilotError('malformed-generation','Generation JSON invalid');}
  validateGeneration(value);
  requireThat(encode(canonicalGeneration(value))===body,'malformed-generation','Generation is not canonical');
  // Verify ancestry closure without deriving knowledge or requiring the parent to be current.
  const seen=new Set([id]);let parent=value.parent;
  while(parent!==null) {
    requireThat(!seen.has(parent),'invalid-reference','Generation ancestry cycle');seen.add(parent);
    const pfile=join(store,'generations',parent+'.json');requireThat(existsSync(pfile),'generation-missing','Historical parent unavailable');
    const pbody=readFileSync(pfile,'utf8');requireThat(sha(pbody)===parent,'generation-integrity','Historical parent changed');
    const pvalue=json(pfile);validateGeneration(pvalue);parent=pvalue.parent;
  }
  let map=locators;
  if(!map) {try {map=json(join(store,'locators',id+'.json'),'invalid-locator');} catch {throw new PilotError('required-state-unavailable','Generation locator closure unavailable');}}
  const verification=verify?verifyArtifacts(value.catalogue,map,dataRoot):{status:'not-verified'};
  return {generation:id,value,locators:map,verification,metrics:{loadMilliseconds:performance.now()-start,generationBytes:Buffer.byteLength(body)}};
}
function withWriter(dir,callback) {
  const store=storePath(dir);mkdirSync(store,{recursive:true});
  const operation=randomUUID(),lock=join(store,'writer.lock');
  try {writeDurable(lock,encode({pid:process.pid,operation}));}
  catch(error) {if(error.code==='EEXIST')throw new PilotError('writer-locked','One writer already owns this store; explicit dead-owner recovery required');throw error;}
  try {return callback(store,operation);}
  finally {if(existsSync(lock)) {const owner=json(lock);requireThat(owner.operation===operation,'lock-conflict','Writer ownership changed');unlinkSync(lock);}}
}
export function recoverLock(dir,operation) {
  const lock=join(storePath(dir),'writer.lock'),owner=json(lock,'invalid-lock');opCheck(operation);
  requireThat(owner.operation===operation && Number.isSafeInteger(owner.pid) && owner.pid>0,'lock-conflict','Operation/owner differs');
  let dead=false;
  try {process.kill(owner.pid,0);} catch(error) {dead=error.code==='ESRCH';}
  requireThat(dead,'writer-alive-or-unknown','Owner PID is alive or cannot be proven dead; never reclaim by age');
  unlinkSync(lock);return {recoveredOperation:operation};
}
function staged(store,operation,value,locators) {
  const path=join(store,'staging',operation);mkdirSync(path,{recursive:true});
  // Staged state is not accepted state, even if it parses or has a valid hash.
  writeDurable(join(path,'candidate.json'),encode(canonicalGeneration(value)));
  writeDurable(join(path,'locators.json'),encode(locators));
  return path;
}
function interrupt(point,options) { if(options.failAt===point) process.exit(91); }
function publishCandidate(store,path,{dataRoot=DATA,...options}={}) {
  const validationStart=performance.now(),value=json(join(path,'candidate.json')),locators=json(join(path,'locators.json'));
  validateGeneration(value);const verification=verifyArtifacts(value.catalogue,locators,dataRoot);
  const existing=existsSync(join(store,'current.json'))?currentId(store):null;
  requireThat(value.parent===existing,'publication-conflict','Candidate parent is not the currently published generation');
  if(existing) load(store,{generation:existing,dataRoot});
  const validationMilliseconds=performance.now()-validationStart;
  interrupt('after-validation',options);
  const body=encode(canonicalGeneration(value)),id=sha(body);
  for(const folder of ['generations','locators'])mkdirSync(join(store,folder),{recursive:true});
  writeImmutable(join(store,'locators',id+'.json'),encode(locators));
  writeImmutable(join(store,'generations',id+'.json'),body);
  // Complete generation and locator closure exists before publishing; never scan/adopt orphans.
  interrupt('before-switch',options);
  const publicationStart=performance.now(),pointer=encode({format:FORMAT,generation:id}),temp=join(store,'current-'+randomUUID()+'.pending');
  writeDurable(temp,pointer);renameSync(temp,join(store,'current.json'));
  return {generation:id,verification,metrics:{catalogueBytes:Buffer.byteLength(encode(value.catalogue)),generationBytes:Buffer.byteLength(body),
    pointerBytes:Buffer.byteLength(pointer),validationMilliseconds,publicationMilliseconds:performance.now()-publicationStart}};
}
export function stage(dir,value,locators,{dataRoot=DATA,...options}={}) {
  return withWriter(dir,(store,operation)=>{
    const path=staged(store,operation,value,locators);interrupt('after-staging',options);
    validateGeneration(value);verifyArtifacts(value.catalogue,locators,dataRoot);
    return {operation,generation:generationId(value),published:false};
  });
}
export function publish(dir,operation,options={}) {
  opCheck(operation);
  return withWriter(dir,store=>publishCandidate(store,join(store,'staging',operation),options));
}
export function register(dir,value,locators,{dataRoot=DATA,...options}={}) {
  return withWriter(dir,(store,operation)=>{
    const path=staged(store,operation,value,locators);interrupt('after-staging',options);
    return {operation,...publishCandidate(store,path,{dataRoot,...options})};
  });
}
export function rollback(dir,generation,{dataRoot=DATA}={}) {
  idCheck(generation);
  return withWriter(dir,store=>{
    load(store,{generation,dataRoot});
    const temp=join(store,'current-'+randomUUID()+'.pending');writeDurable(temp,encode({format:FORMAT,generation}));renameSync(temp,join(store,'current.json'));
    return {generation,rollback:true};
  });
}
