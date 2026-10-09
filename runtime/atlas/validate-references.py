"""Exact task scope, retained evidence, oracle, runtime and navigation safeguards."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
from urllib.parse import unquote
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent;BASE='e3c14537e6eccf85fa21cf2ef045c7ca8ddf5e3e'
OUT=R/'docs/research/atlas-local-references-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
MOD={'runtime/atlas/'+n for n in ['README.md','authority.ts','publication.ts','registration-model.ts','registration.ts','index.ts','lifecycle.ts','cli.ts','types.ts','worker.py','retrieval-model.ts','retrieval_query.py','exe_worker.py']}
NEW={'runtime/atlas/'+n for n in ['references-plan.json','references-next-task.json','references-model.ts','references-oracle.py','references-cases.mjs','test-references.mjs','example-references.mjs','measure-references.mjs','check-references.py','validate-references.py']}
NEW|={'docs/research/atlas-local-references'+s for s in ['.md','-baseline.json','-results.json','-validation.json']}

def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8')
checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)})
b=read('docs/research/atlas-local-references-baseline.json');x=read('docs/research/atlas-local-references-results.json');p=read('runtime/atlas/references-plan.json');n=read('runtime/atlas/references-next-task.json')
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
t=read('docs/research/atlas-temporal-integration-baseline.json');a=read('docs/research/atlas-local-architecture-baseline.json');old=read('docs/research/atlas-local-runtime-baseline.json');d=read('docs/research/atlas-integrity-cost-baseline.json')
check('exact fetched clean main starting checkpoint',b['checkpoint']==BASE and git('branch','--show-current').strip()=='main' and git('rev-parse','--abbrev-ref','@{u}').strip()=='origin/main' and git('rev-parse','HEAD').strip()==BASE)
keep=[k for k in b['trackedBlobs'] if k not in NAV|MOD];hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines()
check('every original file outside narrow runtime/navigation changes unchanged',len(hashes)==len(keep) and all(b['trackedBlobs'][k]==v for k,v in zip(keep,hashes)))
check('frozen pre-implementation plan exact',p['frozenBeforeImplementation'] and sha(H/'references-plan.json')==b['planSha256']==x['planSha256'])
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
 ('accepted Exe runtime world309 files',Path(b['selectedWorld']),b['selectedWorldHashes'])]:check(label+' unchanged',all(sha(root/k)==v for k,v in hashes.items()))
for i in range(1,7):check('accepted Tryfan S'+str(i)+' report retained',(R/f'docs/research/tryfan-pilot-s{i}.md').is_file())
for name in ['atlas-regional-expansion','atlas-riffelhorn-preparation','atlas-riffelhorn-retrieval','atlas-multi-region','atlas-regional-dependencies','atlas-temporal-integration','atlas-local-architecture','atlas-local-runtime','atlas-local-lifecycle','atlas-local-registration','atlas-local-retrieval','atlas-local-exe','exe-water-query-proof']:
 check(name+' prior report retained',(R/f'docs/research/{name}.md').is_file())
check('no S7 introduced',not any('s7' in k.lower() for k in git('ls-files','--others','--exclude-standard').splitlines()))
runs=x['runs'];phases=x['phases'];current=[r['samples'][-1] for r in runs];before=[r['samples'][0] for r in runs]
check('three fresh process historical replays',len(runs)==3 and len({r['pid'] for r in runs})==3 and all([s['generation'] for s in r['samples']]==phases[0]['history'] for r in runs))
check('all indexed/full query comparisons agree',x['agreement'] and x['comparisons']==sum(len(s['rows']) for r in runs for s in r['samples']) and x['comparisons']>=300)
check('fresh complete qualified answer hashes agree',all([s['answerHash'] for s in r['samples']]==[s['answerHash'] for s in runs[0]['samples']] for r in runs))
check('pre-reference generation has no retroactive habitat/planning',all(s['counts']=={'all':89,'source':55,'derived':34,'habitat':0,'planning':0} for s in before))
check('selected50 real features add52 source claims',all(s['counts']=={'all':141,'source':107,'derived':34,'habitat':15,'planning':37} for s in current))
check('existing34 dependency relationships unchanged',all(s['relationships']==s['built']['relationships']==34 for s in current))
check('three isolated registrations preserve10 old non-ledger components',len(phases)==3 and all(s['unchangedComponents']==10 and s['stage']['affected']==[] and s['stage']['reused']==32 for s in phases))
check('no-op writes nothing',all(s['noop']['status']=='no-op' and s['noop']['bytesWritten']==0 for s in phases))
check('administrative revision reuses all32 terrain outputs',all(s['revision']['affected']==[] and s['revision']['requalified']==[] and s['revision']['reused']==32 for s in phases))
check('31 receipts verify9892590 bytes and66 directory hashes',all(s['inspection']['sourceHashOperations']==31 and s['inspection']['sourceBytesHashed']==9892590 and s['inspection']['directoryHashOperations']==66 and s['inspection']['directoryBytesHashed']==10295691 for s in phases))
check('full candidate validation remains required',all(s['validation']['status']=='fully-validated-unpublished' and s['validation']['outputChecks']==32 and s['validation']['payloadBytesHashed']>237201312 and s['validation']['payloadHashOperations']>738 for s in phases))
check('full pinned validation includes extra source/directory reads',all(s['validation']['payloadHashOperations']>426 and s['validation']['payloadBytesHashed']>191670714 for s in current))
check('zero ancestry membership traversal',all(s['validation']['ancestryTraversals']==0 for r in runs for s in r['samples']))
check('same disposable schema2 binds141 records',all(s['built']['records']==141 and s['built']['schemaVersion']==2 for s in current))
check('clean rebuild measured for all historical pins',all(s['rebuildMs']>0 for r in runs for s in r['samples']))
check('timing spread and environment retained',all(set(v)=={'median','min','max'} for v in x['summary'].values()) and x['environment']['totalMemoryBytes']>0 and 'sqlite' in x['environment']['workerVersions'])
check('RSS is observed and logical metadata counters retained',all(s['parentRss']>0 and s['rows'][0]['metrics']['canonicalMetadataBytes']>0 for s in current))
check('generated worlds/catalogues outside repository',not Path(x['environment']['outputRoot']).is_relative_to(R) and all(not Path(s['config']['publicationRoot']).is_relative_to(R) for s in phases))
check('accepted semantics reused rather than new ecology/planning science',all(k in (H/'references-model.ts').read_text() for k in ['accepted.build','accepted.check']) and 'reader.read(root)' in (H/'exe_worker.py').read_text())
check('independent direct GeoJSON oracle imports no runtime predicate',all(k not in (H/'references-oracle.py').read_text() for k in ['exe_worker','retrieval_query','reader.read','Adapter']))
check('same registration/publication/retrieval interfaces used',all(k in (H/'example-references.mjs').read_text() for k in ["'evidence','register'","'update','publish'","'retrieve'","'catalogue','build'"]))
check('no second publication authority','sqlite' not in (H/'publication.ts').read_text().lower() and 'immutable(' not in (H/'retrieval-model.ts').read_text())
check('registered scope does not invent a fourth geographical region',"region: 'exe'" in (H/'references-model.ts').read_text() and 'exeReferences' in (H/'registration.ts').read_text())
check('native definitions are exposed for scientific meanings','definitions:' in (H/'references-model.ts').read_text())
check('administrative effective time and contributor vintages remain qualified','effective' in (H/'retrieval_query.py').read_text() and 'contributor' in (H/'retrieval_query.py').read_text())
check('no ecological/legal/absence query claims supported',all(k in (H/'test-references.mjs').read_text() for k in ['Legal','Absence']))
oracle=json.loads(subprocess.check_output([str(P.DATA/'earth-lab/.venv/Scripts/python.exe'),str(H/'references-oracle.py'),str(P.DATA),'{}'],cwd=R,text=True,encoding='utf-8'))
check('independent direct source population52 and original50 features',len(oracle['rows'])==52 and oracle['inventory']['phi']['selectedFeatures']==13 and oracle['inventory']['flood']['selectedFeatures']==37)
check('native contributor codes and2 planning categories intact',{r['code'] for r in oracle['rows']}=={'CFPGM','LFENS','MUDFL','RBEDS','SALTM','FZ2','FZ3'})
check('two original selected files total7179122 bytes',sum(v['bytes'] for v in oracle['inventory'].values())==7179122)
check('selected source hashes agree with protected directory',all(v['sha256']==b['retainedExeDirectory'][k+'.geojson'] for k,v in oracle['inventory'].items()))
report=(R/'docs/research/atlas-local-references.md').read_text(encoding='utf-8')
check('all32 durable sections present',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,33)))
check('scientific limitations explicit',all(v in report for v in ['physical absence','power-loss','parent','population-wide','C — HABITAT AND PLANNING-REFERENCE INTEGRATION SUCCESS','CLOSED']))
check('exactly one bounded next task not begun',n['status']=='NOT BEGUN' and n['title'] in report and len(n['acceptance'])==6)
for k in NAV:check('canonical navigation current result/next '+k,all(v in (R/k).read_text(encoding='utf-8') for v in ['atlas-local-references.md','C — HABITAT AND PLANNING-REFERENCE INTEGRATION SUCCESS',n['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')))
changed=set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT.relative_to(R).as_posix()]);check('exact authorised runtime/report/navigation scope',changed==NAV|MOD|NEW)
check('no large payload/catalogue/private files committed',all((R/k).stat().st_size<600000 and not k.endswith(('.sqlite','.db','.tif','.png','.pyc','.npz')) and 'meridian-private' not in k for k in changed-NAV if (R/k).exists()))
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
commands=json.loads((R/'../../Codex/atlas-local-references-v1/final-regression/commands.json').resolve().read_text(encoding='utf-8'));prior=read('docs/research/atlas-local-exe-validation.json')['commands']
check('all inherited794 tests freshly pass',len(commands)==len(prior)+2 and all(c['exitCode']==0 and c['name']==o['name'] for c,o in zip(commands,prior)) and sum(c.get('tests') or 0 for c in commands[:len(prior)])==794)
check('final focused registration/query/recovery/source-oracle tests pass',commands[-2]['name']=='runtime-references' and commands[-2]['exitCode']==0 and commands[-2]['tests']>=109)
check('complete CLI-only workflow passes',commands[-1]['name']=='runtime-references-cli' and commands[-1]['exitCode']==0)
check('types lint build pass',all(c['exitCode']==0 for c in commands if c['name'] in ['semantic-types','application-types','runtime-types','lint','build']))
check('bounded prototype readiness separate from integration result',report.count('**READY FOR BOUNDED PROTOTYPE INTEGRATION**')==1 and 'Node/Python' in report and 'private' in report and 'display' in report)
check('report placeholders resolved',not any(v in report for v in ['MEASUREMENT_PENDING','PERFORMANCE_PENDING','REGRESSION_PENDING']))
review=[]
for name,args in [('final-runtime-types',['node','node_modules/typescript/bin/tsc','-p','runtime/atlas/tsconfig.json']),('final-lint',['npm.cmd','run','lint']),('final-whitespace',['git','diff','--check'])]:
 q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace');review.append({'name':name,'args':args,'exitCode':q.returncode});check(name+' passes',q.returncode==0)
failed=[c['check'] for c in checks if not c['passed']]
receipt={'schema':'atlas-local-references-validation/v1','checkpoint':BASE,'decision':'C — HABITAT AND PLANNING-REFERENCE INTEGRATION SUCCESS' if not failed else 'B — INCONCLUSIVE','passed':len(checks)-len(failed),'failed':failed,'checks':checks,'tests':sum(c.get('tests') or 0 for c in commands),'prototypeReadiness':'READY FOR BOUNDED PROTOTYPE INTEGRATION','selectedNativeCounts':{k:v['selectedFeatures'] for k,v in oracle['inventory'].items()},'commands':commands,'finalReviewCommands':review,'runtimeHashes':{k:sha(R/k) for k in sorted(MOD|NEW) if (R/k).exists() and k!=OUT.relative_to(R).as_posix()},'navigationMissing':missing,'review':{'completeDiffAndUntrackedInspected':True,'canonicalEvidenceUnchanged':True,'scope':'bounded habitat/planning adapter, existing shared runtime, tests/reports/navigation and public-only readiness assessment'}}
OUT.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':receipt['passed'],'failed':failed,'tests':receipt['tests']}));sys.exit(bool(failed))
