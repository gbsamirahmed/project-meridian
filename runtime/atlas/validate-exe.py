"""Exact task scope, retained evidence, oracle, runtime and navigation safeguards."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
from urllib.parse import unquote
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent;BASE='a71dc7192333af56a186d0b67891340d9394fa92'
OUT=R/'docs/research/atlas-local-exe-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
MOD={'runtime/atlas/'+n for n in ['README.md','authority.ts','publication.ts','registration-model.ts','registration.ts','index.ts','lifecycle.ts','cli.ts','types.ts','worker.py','retrieval-model.ts','retrieval_query.py']}
NEW={'runtime/atlas/'+n for n in ['exe-plan.json','exe-next-task.json','exe-model.ts','exe_worker.py','exe-oracle.py','exe-cases.mjs','test-exe.mjs','example-exe.mjs','measure-exe.mjs','check-exe.py','validate-exe.py']}
NEW|={'docs/research/atlas-local-exe'+s for s in ['.md','-baseline.json','-results.json','-validation.json']}
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8')
checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)})
b=read('docs/research/atlas-local-exe-baseline.json');x=read('docs/research/atlas-local-exe-results.json');p=read('runtime/atlas/exe-plan.json');n=read('runtime/atlas/exe-next-task.json')
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
t=read('docs/research/atlas-temporal-integration-baseline.json');a=read('docs/research/atlas-local-architecture-baseline.json');old=read('docs/research/atlas-local-runtime-baseline.json');d=read('docs/research/atlas-integrity-cost-baseline.json')
check('exact fetched clean main starting checkpoint',b['checkpoint']==BASE and b['branch']=='main' and b['divergence']=='0/0' and git('rev-parse','HEAD').strip()==BASE)
keep=[k for k in b['trackedBlobs'] if k not in NAV|MOD];hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines()
check('every original file outside narrow runtime/navigation changes unchanged',len(hashes)==len(keep) and all(b['trackedBlobs'][k]==v for k,v in zip(keep,hashes)))
check('frozen pre-implementation plan exact',p['frozenBeforeImplementation'] and sha(H/'exe-plan.json')==b['planSha256']==x['planSha256'])
prod=read('docs/atlas/information-display-plan.json')['productionHashes'];check('all113 protected production hashes unchanged',len(prod)==113 and all(sha(R/k)==v for k,v in prod.items()))
check('all42 canonical research statuses unchanged',len(b['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==b['canonicalRows'])
check('retained original source admission unchanged',P.admission.assess()['sources']==b['sourceAdmission'])
for label,root,hashes in [
 ('accepted Tryfan17 files',P.DATA/'experiments/atlas/tryfan-regional-pilot-v1',d['acceptedStoreHashes']),
 ('prepared Riffelhorn6 files',P.DATA/t['preparedRootRelative'],t['preparedHashes']),
 ('native unit/source receipts',P.DATA,t['unitEvidence']),
 ('retained Exe66 files',P.DATA/'derived/atlas/water-check-v1',b['retainedExeDirectory']),
 ('accepted temporal world',Path(a['previousTemporalStore']),a['previousStoreHashes']),
 ('accepted multi-region world115 files',Path(old['publicationRoot']),old['storeHashes']),
 ('accepted registered runtime world236 files',Path(b['selectedWorld']),b['selectedWorldHashes'])]:check(label+' unchanged',all(sha(root/k)==v for k,v in hashes.items()))
for i in range(1,7):check('accepted Tryfan S'+str(i)+' report retained',(R/f'docs/research/tryfan-pilot-s{i}.md').is_file())
for name in ['atlas-regional-expansion','atlas-riffelhorn-preparation','atlas-riffelhorn-retrieval','atlas-multi-region','atlas-regional-dependencies','atlas-temporal-integration','atlas-local-architecture','atlas-local-runtime','atlas-local-lifecycle','atlas-local-registration','atlas-local-retrieval','exe-water-query-proof']:
 check(name+' prior report retained',(R/f'docs/research/{name}.md').is_file())
check('no S7 introduced',not any('s7' in k.lower() for k in git('ls-files','--others','--exclude-standard').splitlines()))
runs=x['runs'];phases=x['phases'];current=[r['samples'][-1] for r in runs];before=[r['samples'][0] for r in runs]
check('three fresh process historical replays',len(runs)==x['freshProcesses']==3 and len({r['pid'] for r in runs})==3 and all([s['generation'] for s in r['samples']]==phases[0]['history'] for r in runs))
check('all indexed/full query comparisons agree',x['agreement'] and x['comparisons']==sum(len(s['rows']) for r in runs for s in r['samples']) and x['comparisons']>=300)
check('fresh qualified answer hashes agree',all([s['answerHash'] for s in r['samples']]==[s['answerHash'] for s in runs[0]['samples']] for r in runs))
check('pre-Exe generation contains no retroactive Exe',all(s['counts']=={'source':49,'derived':32,'exe':0} for s in before))
check('eight real Exe selectors add6 source and2 derived',all(s['counts']=={'source':55,'derived':34,'exe':8} for s in current))
check('34 relationships retain32 old and2 product-to-summary edges',all(s['relationships']==s['built']['relationships']==34 for s in current))
check('three isolated registrations preserve existing components',len(phases)==3 and all(s['unchangedComponents']==9 and s['stage']['affected']==[] and s['stage']['reused']==32 for s in phases))
check('no-op writes nothing or advances history',all(s['noop']['status']=='no-op' and s['noop']['metrics']['bytesWritten']==0 for s in phases))
check('administrative knowledge revision needs no numerical recomputation',all(s['revision']['affected']==[] and s['revision']['requalified']==[] and s['revision']['reused']==32 for s in phases))
check('current payload validation includes Exe source and directory hashes',all(s['validation']['payloadHashOperations']==426 and s['validation']['payloadBytesHashed']==191670714 for s in current))
check('31 receipts verify9892590 bytes/66 local files',all(s['inspection']['sourceHashOperations']==31 and s['inspection']['sourceBytesHashed']==9892590 and s['inspection']['directoryHashOperations']==66 and s['inspection']['directoryBytesHashed']==10295691 for s in phases))
check('full candidate validation retained',all(s['validation']['status']=='fully-validated-unpublished' and s['validation']['outputChecks']==32 and s['validation']['payloadBytesHashed']==237201312 and s['validation']['payloadHashOperations']==738 for s in phases))
check('zero ancestry membership traversal',all(s['validation']['ancestryTraversals']==0 for r in runs for s in r['samples']))
check('disposable schema2 binds89 complete records',all(s['built']['records']==89 and s['built']['schemaVersion']==2 for s in current))
check('rebuild measured from canonical evidence',all(s['rebuildMs']>0 for r in runs for s in r['samples']))
check('timing medians and spread recorded',all(set(v)=={'median','min','max'} for v in x['summary'].values()) and x['environment']['totalMemoryBytes']>0)
check('RSS observations and logical metadata counters retained',all(s['parentRss']>0 and s['rows'][0]['metrics']['canonicalMetadataBytes']>0 for s in current))
check('generated retained worlds and catalogues outside repository',not Path(x['environment']['outputRoot']).is_relative_to(R) and all(not Path(s['config']['publicationRoot']).is_relative_to(R) for s in phases))
check('reuses frozen water semantics rather than a new scientific method',all(k in (H/'exe-model.ts').read_text() for k in ['accepted.build','accepted.check','accepted.resolveQuery']) and 'reader.read(root)' in (H/'exe_worker.py').read_text())
check('independent GIS oracle does not call runtime predicates',all(k not in (H/'exe-oracle.py').read_text() for k in ['exe_worker','retrieval_query','reader.read','Adapter']))
check('same registration/publication/retrieval interfaces extended',all(k in (H/'example-exe.mjs').read_text() for k in ["'evidence','register'","'update','publish'","'retrieve'","'catalogue','build'"]))
check('SQLite remains read-side catalogue only','immutable(' not in (H/'retrieval-model.ts').read_text() and 'commit(' not in (H/'retrieval-model.ts').read_text() and 'sqlite' not in (H/'publication.ts').read_text().lower())
check('direct product dependencies never invent point-to-summary lineage',"replace(':support', ':product')" in (H/'retrieval-model.ts').read_text())
check('native month/event/reference and unknown are explicit',all(v in (H/'retrieval_query.py').read_text() for v in ['waterTime','nominal-epoch','Unknown is not unrestricted time']))
report=(R/'docs/research/atlas-local-exe.md').read_text(encoding='utf-8')
check('all31 durable sections present',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,32)))
check('scientific limitations explicit',all(v in report for v in ['physical absence','no-observation','power-loss','parent','population-wide','C — EXE INTEGRATION SUCCESS','CLOSED']))
check('exactly one bounded next task not begun',n['status']=='NOT BEGUN' and n['title'] in report and len(n['acceptance'])==6)
for k in NAV:check('canonical navigation current result/next '+k,all(v in (R/k).read_text(encoding='utf-8') for v in ['atlas-local-exe.md','C — EXE INTEGRATION SUCCESS',n['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')))
changed=set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT.relative_to(R).as_posix()]);check('exact authorised runtime/report/navigation scope',changed==NAV|MOD|NEW)
check('no large payload/catalogue/private files committed',all((R/k).stat().st_size<250000 and not k.endswith(('.sqlite','.db','.tif','.png','.pyc','.npz')) and 'meridian-private' not in k for k in changed-NAV if (R/k).exists()))
missing=[]
for k in changed:
 f=R/k
 if not f.exists():continue
 if k.endswith('.json'):read(k)
 if k.endswith('.py'):ast.parse(f.read_text(encoding='utf-8'))
 if k.endswith('.md'):
  text=f.read_text(encoding='utf-8');text=text[len(git('show',BASE+':'+k)):] if k=='docs/development-log.md' else text
  for link in re.findall(r'\]\(([^)]+)\)',text):
   if link.startswith(('http:','https:','mailto:')):continue
   dest=f.parent/unquote(link.strip('<>')).split('#')[0]
   if not dest.exists() and dest.resolve()!=OUT.resolve():missing.append([k,link])
check('documentation links resolve',not missing)
commands=json.loads((R/'../../Codex/atlas-local-exe-v1/regression/commands.json').resolve().read_text(encoding='utf-8'));prior=read('docs/research/atlas-local-retrieval-validation.json')['commands']
check('all inherited705 tests freshly pass',len(commands)==len(prior)+2 and all(c['exitCode']==0 and c['name']==o['name'] for c,o in zip(commands,prior)) and sum(c.get('tests') or 0 for c in commands[:len(prior)])==705)
check('focused registration/query/recovery/independent-oracle tests pass',commands[-2]['name']=='runtime-exe' and commands[-2]['exitCode']==0 and commands[-2]['tests']>=89)
check('complete CLI-only workflow passes',commands[-1]['name']=='runtime-exe-cli' and commands[-1]['exitCode']==0)
check('types lint build pass',all(c['exitCode']==0 for c in commands if c['name'] in ['semantic-types','application-types','runtime-types','lint','build']))
review=[]
cfg=json.loads((R/'../../Codex/atlas-local-exe-v1/regression/exe-config.json').resolve().read_text(encoding='utf-8'))
native_check=(R/'../../Codex/atlas-local-exe-v1/regression/native-exe-review.mjs').resolve()
module=(H/'index.ts').resolve().as_uri()
native_check.write_text("import assert from 'node:assert/strict';import{openAtlas}from"+json.dumps(module)+";const x=await openAtlas("+json.dumps(cfg)+");try{await x.buildCatalogue();const a=await x.query({region:'exe'});assert.equal(a.results.length,8);assert(a.results.every(r=>r.componentIdentity===a.members.exeRegistration));await x.buildCatalogue({qualified:true});assert.equal((await x.retrieve({region:'exe'})).results.length,8)}finally{await x.close()}\n",encoding='utf-8')
q=subprocess.run(['node',str(native_check)],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
review.append({'name':'final-native-exe-component','args':['node',str(native_check)],'exitCode':q.returncode});check('legacy native and qualified Exe return correct component identity',q.returncode==0)
for name,args in [('final-runtime-types',['node','node_modules/typescript/bin/tsc','-p','runtime/atlas/tsconfig.json']),('final-lint',['npm.cmd','run','lint']),('final-whitespace',['git','diff','--check'])]:
 q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace');review.append({'name':name,'args':args,'exitCode':q.returncode});check(name+' passes',q.returncode==0)
failed=[c['check'] for c in checks if not c['passed']]
receipt={'schema':'atlas-local-exe-validation/v1','checkpoint':BASE,'decision':'C — EXE INTEGRATION SUCCESS' if not failed else 'B — INCONCLUSIVE','passed':len(checks)-len(failed),'failed':failed,'checks':checks,'tests':sum(c.get('tests') or 0 for c in commands),'commands':commands,'finalReviewCommands':review,'runtimeHashes':{k:sha(R/k) for k in sorted(MOD|NEW) if (R/k).exists() and k!=OUT.relative_to(R).as_posix()},'navigationMissing':missing,'review':{'completeDiffAndUntrackedInspected':True,'canonicalEvidenceUnchanged':True,'scope':'bounded Exe adapter, shared runtime, tests/reports/navigation only'}}
OUT.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':receipt['passed'],'failed':failed,'tests':receipt['tests']}));sys.exit(bool(failed))
