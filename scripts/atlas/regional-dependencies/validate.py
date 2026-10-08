"""Proof safeguards and established regression coverage. No accepted-state writes."""
from pathlib import Path
import ast,hashlib,json,os,re,subprocess,sys
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
BASE='8e0f956b9ca0019a92fcde1c55d1fb0700f8deab';OUT='docs/research/atlas-regional-dependencies-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
LOG=Path('C:/Users/gbsam/Documents/Codex/atlas-regional-dependency-proof-v1/regression');LOG.mkdir(parents=True,exist_ok=True)
checks=[];errors=[];commands=[]
prior=None
if ('--review-only' in sys.argv or '--reuse-unchanged-regression' in sys.argv) and (R/OUT).exists():
 prior=json.loads((R/OUT).read_text(encoding='utf-8'))
 if prior['startingCheckpoint']!=BASE:raise ValueError('regression checkpoint mismatch')
def check(n,ok):
 checks.append(dict(check=n,passed=bool(ok)))
 if not ok:errors.append(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8')
tracked=git('ls-tree','-r','--name-only',BASE).splitlines();keep=[p for p in tracked if p not in NAV];tree={s.split('\t')[1]:s.split()[2] for s in git('ls-tree','-r',BASE).splitlines()}
def intact():
 hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(keep)+'\n',text=True).splitlines();return len(hashes)==len(keep) and all(h==tree[p] for p,h in zip(keep,hashes))
check('all original non-navigation tracked files unchanged before regression',intact())
protected=read('docs/atlas/information-display-plan.json')['productionHashes'];check('all113 production hashes unchanged',len(protected)==113 and all(sha(R/p)==h for p,h in protected.items()))
b=read('docs/research/atlas-regional-dependencies-baseline.json');before=b['sourceAdmission'];check('admitted retained source inventory unchanged before regression',P.admission.assess()['sources']==before)
check('all42 canonical research statuses unchanged',len(b['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==b['canonicalRows'])
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
check('accepted17 store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))
x=read('docs/research/atlas-regional-dependencies-results.json');plan=read('scripts/atlas/regional-dependencies/plan.json');matrix=read('scripts/atlas/regional-dependencies/matrix.json');next_task=read('scripts/atlas/regional-dependencies/next-task.json')
prepared=P.DATA/b['preparedRootRelative']
check('accepted6prepared artifacts unchanged before regression',len(b['preparedHashes'])==6 and all(sha(prepared/p)==h for p,h in b['preparedHashes'].items()))
check('exact starting checkpoint frozen before implementation',b['commit']==BASE and b['divergence']=='0\t0' and b['frozenBeforeImplementation'])
check('exact immutable preparation revision',b['preparedRevision']=='357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb')
check('retained authoritative unit receipts unchanged',all(sha(P.DATA/p)==h for p,h in b['unitEvidence'].items()))
check('accepted multi-region source implementation unchanged',sha(R/'scripts/atlas/multi-region/integration.mjs')==b['acceptedMultiRegionImplementationSha256'])
prior_world=read('docs/research/atlas-multi-region-results.json');prior_root=Path(prior_world['store'])
def old_world_intact():
 return (json.loads((prior_root/'current.json').read_text(encoding='utf-8'))['generation']==prior_world['history'][-1] and all(sha(f)==f.stem for folder in ['components','publications','membership','artifacts'] for f in (prior_root/folder).iterdir() if f.is_file()) and all((prior_root/'publications'/(g+'.json')).is_file() for g in prior_world['history']))
check('accepted multi-region external immutable records and current intact',old_world_intact())
check('real current population and graph',x['density']['nodes']==293 and x['density']['edges']==294 and x['realSourceEvidence']['activeDerived']==184 and x['realSourceEvidence']['SwissTerrainProbes']==88)
check('actual family fan-in and transitive graph depth',x['density']['fanIn']['2']==8 and x['density']['maximumSourceFanOut']==36 and x['density']['maximumDepth']==3 and x['density']['crossRegionEdges']==0)
graph=read('docs/research/atlas-regional-dependencies-graph.json');node_regions={}
for region in ['tryfan','riffelhorn']:
 context=json.loads((Path(x['store'])/'components'/(x['members'][0][region+'DependencyState']+'.json')).read_text(encoding='utf-8'))['value']
 state0=json.loads((Path(x['store'])/'components'/(x['members'][0][region+'Derived']+'.json')).read_text(encoding='utf-8'))['value']
 for node in list(context['sources'])+list(state0['uses'])+list(state0['active'].values()):node_regions[node]=region
check('independent graph regional-edge audit',len(graph['edgeList'])==294 and len(node_regions)==293 and all(node_regions[a]==node_regions[b] for a,b,_ in graph['edgeList']))
check('real regional retained input boundary',x['realSourceEvidence']=={'registeredTryfanArtifacts':310,'registeredSwissInputs':12,'preparedSwissArtifacts':6,'consumedSwissFiles':5,'acceptedTryfanInputRoots':2,'activeDerived':184,'SwissTerrainProbes':88,'SwissCategoricalSupports':4,'TryfanProbes':2})
check('all24paired full/scoped runs agree',len(x['observations'])==24 and x['agreement'] and all(a['agreement'] for a in x['observations']))
expected={'noop':0,'administrative':0,'riff-local':8,'riff-scattered':8,'riff-shared-file':72,'tryfan-local':2,'cover-qualification':4,'parameter':2}
check('all8frozen scenarios repeated3times',set(expected)=={a['case'] for a in x['observations']} and all(sum(a['case']==c for a in x['observations'])==3 for c in expected))
check('exact independent closures and recomputation counts',all(a['changed']==len(a['expectedAffected'])==a['scoped']['recomputed']==expected[a['case']] for a in x['observations']))
check('no-op and admin avoid all payload sampling',all(a['scoped']['sampling'] is None and a['scoped']['tryfan'] is None for a in x['observations'] if a['case'] in ['noop','administrative']))
check('full Swiss numerical oracle coverage',all(a['full']['numericalComparisons']==180 and a['full']['sampling']['metrics']['payloadReadCalls']==796 and a['full']['sampling']['metrics']['oraclePayloadReadCalls']==4 for a in x['observations'] if a['region']=='riffelhorn'))
check('explicit full-population selection disclosed',all(a['scoped']['counters']['resultsConsidered']==(4 if a['region']=='tryfan' else 180) for a in x['observations']))
check('five published contexts',len(x['history'])==len(x['publications'])==len(x['members'])==5)
check('eleven explicit memberships no missing family',all(set(m)==set(['catalogue','knowledge','understanding','serving','locators','tryfanRegistration','riffelhornRegistration','tryfanDependencyState','riffelhornDependencyState','tryfanDerived','riffelhornDerived']) for m in x['members']))
changes=[sorted(k for k in a if a[k]!=b[k]) for a,b in zip(x['members'],x['members'][1:])]
check('regional changes reuse9members and administrative reuses10',changes==[['riffelhornDependencyState','riffelhornDerived'],['tryfanDependencyState','tryfanDerived'],['riffelhornDependencyState','riffelhornDerived'],['riffelhornDependencyState']])
check('all7original scientific/registration components reused',all(x['members'][0][k]==m[k] for m in x['members'] for k in ['catalogue','knowledge','understanding','serving','locators','tryfanRegistration','riffelhornRegistration']))
check('three fresh5context2region replays',len(x['fresh'])==3 and all(len(f['checks'])==10 and f['current']==x['history'][-1] and sum(a['results'] for a in f['checks'])==920 for f in x['fresh']))
check('fresh replay exact content hashes agree',all(f['checks']==x['fresh'][0]['checks'] for f in x['fresh']))
check('36selected queries across current/recent/oldest',len(x['query'])==36 and {q['generation'] for q in x['query']}=={x['history'][0],x['history'][1],x['history'][-1]})
check('selected metadata queries remain ancestry independent',all(q['measurement']['counters']['ancestryTraversals']==0 and q['measurement']['counters']['membershipVisits']==33 and q['measurement']['counters']['componentEdges']==11 for q in x['query']))
check('fullRiffcurrentbyte verification perpublication',all(p['measurement']['counters']['riffelhornFullVerifications']==1 and p['verified']['source']['inputBytesVerified']==120347916 for p in x['publications']))
check('310currentTryfan payloads verified perpublication',all(p['measurement']['reads']['retained']=={'calls':310,'bytes':42473107} for p in x['publications']))
check('full numerical acceptance oracle not hidden from cost',all(sum(v['recomputed'] for v in p['numericalReplay'])==184 and p['totalMilliseconds']>=p['measurement']['milliseconds']+sum(v['milliseconds'] for v in p['numericalReplay']) for p in x['publications']))
check('no copied geography only original two portrayals',x['footprint']['artifacts']=={'files':2,'bytes':3057491} and x['footprint']['components']['files']==18)
check('isolated proof root',Path(x['store']).resolve().is_relative_to(Path(plan['stateRoot']).resolve()) and 'meridian-private' not in x['store'].lower())
check('measured implementation exact',all(sha(H/p)==h for p,h in x['implementationHashes'].items()))
check('frozen plan andmatrix match initial pins',sha(H/'plan.json')==x['planSha256']==b['proofPlanSha256'] and sha(H/'matrix.json')==x['matrixSha256']==b['matrixSha256'])
check('one dated integration nexttask notbegun',next_task['status']=='NOT BEGUN' and next_task['title']=='Atlas dated observation and knowledge-revision integration proof')
check('bounded nexttask definition complete',len(next_task['acceptanceCriteria'])==8 and all(k in next_task for k in ['uncertainty','why','prerequisites','permittedWork','deliverable','stopCondition']))
report=(R/'docs/research/atlas-regional-dependencies.md').read_text(encoding='utf-8')
check('all29durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,30)))
check('four architectural classifications',all(t in report for t in ['DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT']))
for p in NAV:check('result boundary andnexttask in '+p,all(t in (R/p).read_text(encoding='utf-8') for t in ['C - PROOF SUCCESS',next_task['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('append-only development history',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')+'\n'))

def run(n,args):
 old=next((c for c in (prior or {}).get('commands',[]) if c['name']==n and c['args']==args and c['exitCode']==0),None)
 if '--review-only' in sys.argv and old:
  for p,h in prior['proofHashes'].items():
   if p.endswith(('.py','.mjs','.json')):assert sha(R/p)==h,p
  assert intact();check(n,True);commands.append({**old,'reusedPassedCommand':True,'basis':'tested code/fixtures and original baseline unchanged; reporting-only review'});print(n,'passed command reused',flush=True);return
 start=__import__('time').perf_counter();q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'});(LOG/(n+'.log')).write_text(q.stdout+q.stderr,encoding='utf-8',newline='\n');check(n,q.returncode==0);m=re.search(r'^(?:#|\u2139) tests (\d+)',q.stdout,re.M) or re.search(r'Ran (\d+) tests?',q.stderr);commands.append(dict(name=n,args=args,exitCode=q.returncode,tests=int(m[1]) if m else None,elapsedSeconds=__import__('time').perf_counter()-start));print(n,q.returncode,flush=True)
 if q.returncode:print((q.stdout+q.stderr)[-2200:],flush=True)
run('regional-dependencies-focused',['node','--test',str(H/'test-proof.mjs')])
run('accepted-multi-region-focused',['node','--test','scripts/atlas/multi-region/test-proof.mjs'])
run('retrieval-focused',[sys.executable,'scripts/atlas/riffelhorn-retrieval/test_query.py'])
run('preparation-focused',[sys.executable,'scripts/atlas/riffelhorn-fixture/test_prepare.py'])
run('preparation-fresh-verification',[sys.executable,'scripts/atlas/riffelhorn-fixture/prepare.py','verify','--output',str(prepared)])
run('assessment-inventory-reproduction',[sys.executable,'scripts/atlas/regional-expansion/inventory.py','--check'])
selected={'assessment','s6','s1-s5','native','planning','frozen','qualified','persistent','exe','semantic-types','lint','build','diff','application-types'}
for c in read('docs/research/atlas-regional-expansion-validation.json')['commands']:
 if c['name'] in selected:
  old=next((q for q in (prior or {}).get('commands',[]) if q['name']==c['name'] and q['args']==c['args'] and q['exitCode']==0),None)
  if old and intact() and c['name'] not in {'semantic-types','lint','build','diff','application-types'}:
   require_log=LOG/(c['name']+'.log')
   check(c['name'],require_log.is_file());commands.append({**old,'reusedUnchangedRegression':True,'basis':'original non-navigation tracked inputs unchanged; focused preparation/final verification rerun'});print(c['name'],'passed unchanged regression reused',flush=True)
  else:run(c['name'],c['args'])
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT]))
allowed={OUT,*['docs/research/atlas-regional-dependencies'+t for t in ['.md','-baseline.json','-results.json','-graph.json']]}|{'scripts/atlas/regional-dependencies/'+t for t in ['plan.json','next-task.json','matrix.json','model.mjs','integration.mjs','sample.py','tryfan-worker.mjs','worker.mjs','prove.mjs','test-proof.mjs','validate.py','README.md']}
check('proof-only changed-path allowlist',all(p in allowed|NAV for p in changed))
check('no large or source payload files committed',all((R/p).stat().st_size<150000 and not p.endswith(('.png','.tif','.las','.zip','.npz','.db','.pyc')) for p in changed if p not in NAV and p!=OUT))
structured=True
for p in changed:
 if p.endswith('.json') and (R/p).exists():json.loads((R/p).read_text(encoding='utf-8-sig'))
 if p.endswith('.py'):ast.parse((R/p).read_text(encoding='utf-8-sig'))
check('full final structured-file and untracked-path review',structured and len(changed)==22)
missing=[]
for p in changed:
 if not p.endswith('.md'):continue
 text=(R/p).read_text(encoding='utf-8-sig')
 if p=='docs/development-log.md':text=text[len(git('show',BASE+':docs/development-log.md')):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if link.startswith(('http:','https:','mailto:')):continue
  target=unquote(link.strip('<>')).split('#')[0];f=(R/p).parent/target if target else R/p
  if not f.exists() and f.resolve()!=(R/OUT).resolve():missing.append([p,link])
check('report/navigation references resolve',not missing)
check('all original non-navigation tracked files unchanged after regression',intact());check('all admitted source inventory unchanged after regression',P.admission.assess()['sources']==before);check('all113 protected production hashes unchanged after regression',all(sha(R/p)==h for p,h in protected.items()));check('accepted store unchanged after regression',all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()));check('accepted6Riffelhorn artifacts unchanged after regression',all(sha(prepared/p)==h for p,h in b['preparedHashes'].items()))
check('accepted multi-region immutable store remains intact after regression',old_world_intact())
check('unit evidence remains intact after regression',all(sha(P.DATA/p)==h for p,h in b['unitEvidence'].items()))
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'));check('accepted current and310source hashes unchanged',state['generation']==accepted['current'] and state['verification']==accepted['sources'])
receipt=dict(schema='atlas-regional-dependency-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),preservedTrackedFiles=len(keep),changedPaths=changed,canonicalThreads=42,protectedHashes=113,acceptedPilotUnchanged=not errors,sourceAdmission=before,retainedVerification=state['verification'],publishedGeneration=state['generation'],missingReferences=missing,decision=x['decision'],nextTask=next_task['title'],nextTaskStatus='NOT BEGUN',proofHashes={p:sha(R/p) for p in changed if p not in NAV and p!=OUT})
(R/OUT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors)),flush=True)
if errors:raise SystemExit(1)
