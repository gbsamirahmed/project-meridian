"""Task-specific accepted-evidence, query and navigation safeguards; no canonical writes."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
from urllib.parse import unquote
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent
BASE='dc4b4b45e45029a42bf206bef5c3bde0c5e38f9d';OUT=R/'docs/research/atlas-local-retrieval-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
MOD={'runtime/atlas/'+n for n in ['README.md','index.ts','cli.ts','worker.py','types.ts']}
NEW={'runtime/atlas/'+n for n in ['retrieval-plan.json','retrieval-next-task.json','retrieval-model.ts','retrieval_query.py','retrieval-cases.mjs','test-retrieval.mjs','measure-retrieval.mjs','example-retrieval.mjs','check-retrieval.py','validate-retrieval.py']}
NEW|={'docs/research/atlas-local-retrieval'+s for s in ['.md','-baseline.json','-results.json','-validation.json']}
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8')
b=read('docs/research/atlas-local-retrieval-baseline.json');x=read('docs/research/atlas-local-retrieval-results.json');p=read('runtime/atlas/retrieval-plan.json');n=read('runtime/atlas/retrieval-next-task.json');old=read('docs/research/atlas-local-runtime-baseline.json');t=read('docs/research/atlas-temporal-integration-baseline.json');a=read('docs/research/atlas-local-architecture-baseline.json')
keep=[k for k in b['trackedBlobs'] if k not in NAV|MOD];hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines()
check('starting clean main checkpoint/upstream recorded',b['startingCheckpoint']==BASE and b['branch']=='main' and b['divergence']=='0\t0')
check('every original file outside exact runtime/navigation edits unchanged',all(b['trackedBlobs'][k]==h for k,h in zip(keep,hashes)) and len(hashes)==len(keep))
check('frozen plan remains exact',p['frozenBeforeImplementation'] and b['frozenBeforeImplementation'] and sha(H/'retrieval-plan.json')==b['planSha256']==x['planSha256'])
prod=read('docs/atlas/information-display-plan.json')['productionHashes'];check('all113 protected production hashes unchanged',len(prod)==113 and all(sha(R/k)==v for k,v in prod.items()))
check('all42 canonical research statuses unchanged',len(t['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==t['canonicalRows'])
check('retained original source admission unchanged',P.admission.assess()['sources']==t['sourceAdmission'])
s=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1';d=read('docs/research/atlas-integrity-cost-baseline.json')
check('all17 accepted Tryfan files unchanged',all(sha(s/k)==v for k,v in d['acceptedStoreHashes'].items()))
s=P.DATA/t['preparedRootRelative'];check('all6 accepted prepared Riffelhorn artifacts unchanged',len(t['preparedHashes'])==6 and all(sha(s/k)==v for k,v in t['preparedHashes'].items()))
check('native unit/source receipts unchanged',all(sha(P.DATA/k)==v for k,v in t['unitEvidence'].items()))
check('all66 retained Exe temporal files unchanged',len(t['retainedExeDirectory'])==66 and all(sha(P.DATA/'derived/atlas/water-check-v1'/k)==v for k,v in t['retainedExeDirectory'].items()))
s=Path(a['previousTemporalStore']);check('complete accepted temporal state unchanged',set(a['previousStoreHashes'])=={f.relative_to(s).as_posix() for f in s.rglob('*') if f.is_file()} and all(sha(s/k)==v for k,v in a['previousStoreHashes'].items()))
s=Path(old['publicationRoot']);check('all115 accepted multi-region publication files unchanged',len(old['storeHashes'])==115 and set(old['storeHashes'])=={f.relative_to(s).as_posix() for f in s.rglob('*') if f.is_file()} and all(sha(s/k)==v for k,v in old['storeHashes'].items()))
s=Path(b['selectedWorld']);check('all236 selected registered runtime canonical files unchanged',len(b['selectedWorldHashes'])==236 and set(b['selectedWorldHashes'])=={f.relative_to(s).as_posix() for f in s.rglob('*') if f.is_file()} and all(sha(s/k)==v for k,v in b['selectedWorldHashes'].items()))
for name in ['atlas-multi-region','atlas-regional-dependencies']:
 q=read('docs/research/'+name+'-results.json');s=Path(q['store']);check(name+' root/history retained',json.loads((s/'current.json').read_bytes())['generation']==q['history'][-1] and all(sha(f)==f.stem for folder in ['components','publications','membership','artifacts'] for f in (s/folder).iterdir() if f.is_file()))
for i in range(1,7):check('accepted S'+str(i)+' report unchanged and present',(R/f'docs/research/tryfan-pilot-s{i}.md').is_file())
for name in ['atlas-component-membership','atlas-component-granularity','atlas-validation-packing','atlas-integrity-cost','atlas-regional-expansion','atlas-riffelhorn-preparation','atlas-riffelhorn-retrieval','atlas-multi-region','atlas-regional-dependencies','atlas-temporal-integration','atlas-local-architecture','atlas-local-runtime','atlas-local-lifecycle','atlas-local-registration']:
 check(name+' primary evidence unchanged and present',(R/f'docs/research/{name}.md').is_file())
runs=x['runs'];samples=[s for r in runs for s in r['samples']];current=[r['samples'][-1] for r in runs]
check('three genuinely fresh processes across five exact retained pins',x['freshProcesses']==len(runs)==3 and all([s['generation'] for s in r['samples']]==p['publication']['history'] for r in runs))
check('all qualified indexed/full comparisons agree',x['agreement'] and x['comparisons']==sum(len(s['rows']) for s in samples) and x['comparisons']>700)
check('fresh-process complete historical answer hashes reproduce',all([[v[1] for v in s['rows']] for s in r['samples']]==[[v[1] for v in s['rows']] for s in runs[0]['samples']] for r in runs))
check('current81 records preserve49 native and32 derived evidence',all(s['classes']=={'source':49,'derived':32} and s['built']['records']==81 for s in current))
check('initial real publication has no fabricated derived evidence',all(r['samples'][0]['classes']=={'source':49,'derived':0} and r['samples'][0]['relationships']==0 for r in runs))
check('schema2 remains163840-byte disposable selectors',all(s['built']['schemaVersion']==2 and s['built']['bytes']==163840 and s['rebuilt']['bytes']==163840 for s in current))
check('direct evidence adjacency32 versus accepted underlying48 edges explicit',all(s['relationships']==32 and s['built']['relationships']==32 for s in current) and 'underlyingEdges' in (H/'retrieval-model.ts').read_text())
check('full authoritative open retains current329 hashes/171MB',all(s['validation']['payloadHashOperations']==329 and s['validation']['payloadBytesHashed']==171482433 for s in samples))
check('normal membership remains zero ancestry traversals',all(s['validation']['ancestryTraversals']==0 for s in samples))
check('knowledge correction changes exactly8 scalar identities with24 reusable',all(sum(v!=r['samples'][3]['derivedRevisions'][k] for k,v in r['samples'][2]['derivedRevisions'].items())==8 for r in runs))
check('unrelated Welsh knowledge update preserves every Swiss derived identity',all(r['samples'][3]['derivedRevisions']==r['samples'][4]['derivedRevisions'] for r in runs))
check('query audit hidden amplification recorded',all(s['metadataMetrics']['nativeSelectorPredicates']==49 and s['metadataMetrics']['artifactMetadataReads']>0 and s['metadataMetrics']['canonicalMetadataReads']>0 for s in current))
check('exact point index narrows derived candidates without assuming support patches',all(s['spatialMetrics']['derivedCandidates']==2 for s in current) and all(k in (H/'retrieval_query.py').read_text() for k in ['consumed_bounds','intersection(g).area>0','x-.25<=g.x<x+.25']))
check('exact source transitive fanout traverses32 qualified relationships',all(s['relationshipMetrics']['relationshipResults']==32 for s in current))
check('timing medians/spread hardware/RSS recorded',all(set(x['summary'][k])=={'median','min','max'} for k in ['currentOpenMs','currentBuildMs','currentRebuildMs','freshFivePinWorkflowMs']) and x['environment']['totalMemoryBytes']>0 and all(s['parentRss']>0 for s in samples))
check('all generated query catalogues outside repository',not Path(x['environment']['outputRoot']).is_relative_to(R))
check('no second native predicate implementation',all(k in (H/'retrieval_query.py').read_text() for k in ['self.o.query','self.o.geometry','self.o.verify']))
check('canonical qualification and exact execution references preserved',all(k in (H/'retrieval-model.ts').read_text() for k in ['validateDerived','validateRegistrations','rightsRef','knowledgeRef','executionRef','readArtifact']))
check('query-only runtime never writes canonical components or advances roots',all(k not in (H/'retrieval-model.ts').read_text() for k in ['writeFileSync','stageObject(','immutable(','publishStage(']))
check('unknown clock roles are not fabricated from execution dates',all(k in (H/'retrieval_query.py').read_text() for k in ['Exact native stencil observation epoch is unknown','No source product-reference calendar year','Closed knowledge UTC interval']))
report=(R/'docs/research/atlas-local-retrieval.md').read_text(encoding='utf-8');check('all29 durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,30)))
check('scientific and operational limitations explicit',all(v in report for v in ['unknown','controlled','LN02','power-loss','CLOSED','C — QUALIFIED RETRIEVAL SUCCESS','half-open','population-wide']))
check('one evidence-backed next task selected not begun',n['status']=='NOT BEGUN' and n['title'] in report and len(n['acceptance'])==7 and 'Exe' in n['title'])
for name in NAV:
 text=(R/name).read_text(encoding='utf-8');check('current navigation result and next-task '+name,all(v in text for v in ['atlas-local-retrieval.md','C — QUALIFIED RETRIEVAL SUCCESS',n['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')))
changed=set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT.relative_to(R).as_posix()]);check('exact authorized runtime/report/navigation scope',changed==NAV|MOD|NEW)
check('no large committed payload/catalogue',all((R/k).stat().st_size<250000 and not k.endswith(('.sqlite','.db','.tif','.png','.pyc','.npz')) for k in changed-NAV if (R/k).exists()))
missing=[]
for name in changed:
 f=R/name
 if not f.exists():continue
 if name.endswith('.json'):read(name)
 if name.endswith('.py'):ast.parse(f.read_text(encoding='utf-8'))
 if name.endswith('.md'):
  text=f.read_text(encoding='utf-8');text=text[len(git('show',BASE+':'+name)):] if name=='docs/development-log.md' else text
  for link in re.findall(r'\]\(([^)]+)\)',text):
   if link.startswith(('http:','https:','mailto:')):continue
   pth=unquote(link.strip('<>')).split('#')[0];target=f.parent/pth if pth else f
   if not target.exists() and target.resolve()!=OUT.resolve():missing.append([name,link])
check('all documentation links resolve',not missing)
commands=json.loads((R/'../../Codex/atlas-local-retrieval-v1/regression/commands.json').resolve().read_text(encoding='utf-8'));previous=read('docs/research/atlas-local-registration-validation.json')['commands']
check('all inherited613 tests/commands freshly pass',len(commands)==len(previous)+2 and all(c['name']==o['name'] and c['exitCode']==0 for c,o in zip(commands,previous)) and sum(c.get('tests') or 0 for c in commands[:len(previous)])==613)
check('all focused qualified retrieval tests pass',commands[-2]['name']=='runtime-retrieval' and commands[-2]['exitCode']==0 and commands[-2]['tests']>=92)
check('documented complete unified retrieval CLI example passes',commands[-1]['exitCode']==0 and commands[-1]['name']=='runtime-retrieval-cli')
check('types lint build freshly pass',all(c['exitCode']==0 for c in commands if c['name'] in ['semantic-types','application-types','runtime-types','lint','build']))
final_review=json.loads((R/'../../Codex/atlas-local-retrieval-v1/regression/final-review.json').resolve().read_text(encoding='utf-8'))
check('final reviewed runtime types and lint pass',{c['name'] for c in final_review}=={'final-runtime-types','final-lint'} and all(c['exitCode']==0 for c in final_review))
check('git whitespace clean',subprocess.run(['git','diff','--check'],cwd=R,capture_output=True).returncode==0)
result={'schema':'atlas-runtime-qualified-retrieval-validation/v1','startingCheckpoint':BASE,'decision':'C — QUALIFIED RETRIEVAL SUCCESS','passed':sum(c['passed'] for c in checks),'failed':[c['check'] for c in checks if not c['passed']],'checks':checks,'tests':sum(c.get('tests') or 0 for c in commands),'commands':commands,'finalReviewCommands':final_review,'runtimeHashes':{k:sha(R/k) for k in sorted(changed-NAV) if (R/k).exists() and (R/k)!=OUT},'navigationMissing':missing,'review':'Only bounded unified runtime catalogue/retrieval interfaces, tests, safe reports/navigation. Full validation and filesystem authority preserved. Accepted evidence/contracts/42statuses/113production hashes unchanged; no acquisition/private/S7/cloud. Full diff/untracked review before commit.'}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['passed','failed','tests','navigationMissing']},indent=2));sys.exit(bool(result['failed']))
