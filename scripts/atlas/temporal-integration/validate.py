"""Proof safeguards and established regression coverage. No accepted-state writes."""
from pathlib import Path
import ast,hashlib,json,os,re,subprocess,sys
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
BASE='f98e9c941084fd43e134a727d42de3e086e6e3cc';OUT='docs/research/atlas-temporal-integration-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
LOG=Path('C:/Users/gbsam/Documents/Codex/atlas-temporal-integration-v1/regression');LOG.mkdir(parents=True,exist_ok=True)
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
b=read('docs/research/atlas-temporal-integration-baseline.json');before=b['sourceAdmission'];check('admitted retained source inventory unchanged before regression',P.admission.assess()['sources']==before)
check('all42 canonical research statuses unchanged',len(b['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==b['canonicalRows'])
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
check('accepted17 store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))

x=read('docs/research/atlas-temporal-integration-results.json');plan=read('scripts/atlas/temporal-integration/plan.json');matrix=read('scripts/atlas/temporal-integration/matrix.json');next_task=read('scripts/atlas/temporal-integration/next-task.json')
prepared=P.DATA/b['preparedRootRelative']
check('accepted6prepared artifacts intact',len(b['preparedHashes'])==6 and all(sha(prepared/p)==h for p,h in b['preparedHashes'].items()))
check('authoritative unit receipts intact',all(sha(P.DATA/p)==h for p,h in b['unitEvidence'].items()))
check('frozen exact checkpoint cleanupstream andprefreeze',b['commit']==BASE and b['divergence']=='0\t0' and b['frozenBeforeImplementation'])
check('plan andmatrix frozen beforeimplementation',plan['frozenBeforeImplementation'] and matrix['frozenBeforeImplementation'] and sha(H/'plan.json')==b['proofPlanSha256']==x['planSha256'] and sha(H/'matrix.json')==b['matrixSha256']==x['matrixSha256'])
exe=P.DATA/'derived/atlas/water-check-v1'
def exe_intact():return len(b['retainedExeDirectory'])==66 and all(sha(exe/p)==h for p,h in b['retainedExeDirectory'].items())
check('all66retained Exe files unchanged beforetests',exe_intact())
def proof_store_intact(file):
 a=read(file);s=Path(a['store']);return json.loads((s/'current.json').read_text())['generation']==a['history'][-1] and all(sha(p)==p.stem for d in ['components','publications','membership','artifacts'] for p in (s/d).iterdir() if p.is_file()) and all((s/'publications'/(g+'.json')).is_file() for g in a['history'])
check('accepted multi-region external state unchanged',proof_store_intact('docs/research/atlas-multi-region-results.json'))
check('accepted regional dependency state unchanged',proof_store_intact('docs/research/atlas-regional-dependencies-results.json'))
check('measured engine exactlymatches',all(sha(H/p)==h for p,h in x['implementationHashes'].items()))
check('actual temporal17assignment population',x['retained']['realAssignments']==17 and x['retained']['acceptedRegionalDerived']==184 and x['setup']['verifiedExeFiles']==31 and x['setup']['verifiedExeBytes']==9892590)
check('five frozen knowledge/population stages',len(x['observations'])==5 and [a['current'] for a in x['observations']]==[13,15,15,17,17] and [a['records'] for a in x['observations']]==[13,15,18,20,20])
check('exactly3explicit supersessions',x['observations'][-1]['supersessions']==3)
check('477warm independent qualifiedcomparisons',x['agreement'] and x['queryComparisons']==477 and len(x['query'])==159 and all(q['agreement'] and len(q['milliseconds'])==3 for q in x['query']))
check('raw repeatedmeasurements external/checksummed',Path(x['rawQueries']['path']).is_relative_to(Path(plan['stateRoot'])) and sha(Path(x['rawQueries']['path']))==x['rawQueries']['sha256'])
check('five coherent13member publications',len(x['history'])==len(x['members'])==len(x['roots'])==5 and all(len(m)==13 for m in x['members']))
changes=[sorted(k for k in a if a[k]!=c[k]) for a,c in zip(x['members'],x['members'][1:])]
check('independent temporal/scoped regional/admin memberships',changes==[['temporalDerived','temporalKnowledge'],['riffelhornDependencyState','riffelhornDerived','temporalDerived','temporalKnowledge'],['temporalDerived','temporalKnowledge'],['temporalKnowledge']])
check('all9native/Tryfan component identities unchanged',all(m[k]==x['members'][0][k] for m in x['members'] for k in x['members'][0] if k not in ['temporalKnowledge','temporalDerived','riffelhornDependencyState','riffelhornDerived']))
check('three correction full/scoped equivalences with8exact results',len(x['updates'][1]['runs'])==3 and all(v['regional']['recomputed']==len(v['regional']['expected'])==8 and v['regional']['reuse']==176 and v['regional']['scoped']['numericalComparisons']==8 and v['regional']['full']['numericalComparisons']==180 for v in x['updates'][1]['runs']))
check('correct scoped36native cells144decoded bytes',all(v['regional']['scoped']['sampling']['metrics']['cellsRead']==36 and v['regional']['scoped']['sampling']['metrics']['decodedBytes']==144 for v in x['updates'][1]['runs']))
check('metadata-only zero receipts/regional recompute',all(v['temporal']['recomputed']==v['regional']['recomputed']==0 for v in x['updates'][-1]['runs']) and x['members'][-1]['temporalDerived']==x['members'][-2]['temporalDerived'])
check('three fresh477temporal/2760regional replays',len(x['fresh'])==3 and all(sum(c['queries'] for c in f['checks'])==159 and sum(n['results'] for c in f['checks'] for n in c['numerical'])==920 and f['current']==x['history'][-1] for f in x['fresh']))
check('allfresh qualified/numerical hashes agree',all(f['checks']==x['fresh'][0]['checks'] for f in x['fresh']))
check('historical derivations for15combinedknowledge cases',len(x['derivedKnowledge'])==15 and x['derivedKnowledge'][0]['slots']==[] and len(x['derivedKnowledge'][-1]['slots'])==3)
check('allquery histories zero ancestry/boundedmembership',all(q['measurement']['counters']['ancestryTraversals']==0 and q['measurement']['counters']['membershipVisits']==33 and q['measurement']['counters']['componentEdges']==13 for q in x['query']))
check('fullcurrentTryfan310payload/42473107B eachpub',all(p['measurement']['reads']['retained']=={'calls':310,'bytes':42473107} for p in x['publications']))
check('fullRiff120347916B eachpub',all(p['riffVerification']['verified'] and p['riffVerification']['inputBytesVerified']==120347916 for p in x['publications']))
check('fullExe31sources9892590B eachpub',all(p['exeVerification']['files']==31 and p['exeVerification']['bytes']==9892590 for p in x['publications']))
check('fullnumerical replay disclosed perpub',all(sum(r['recomputed'] for r in p['numericalReplay'])==184 and p['totalMilliseconds']>p['measurement']['milliseconds']+p['exeVerification']['milliseconds']+sum(r['milliseconds'] for r in p['numericalReplay']) for p in x['publications']))
check('unchangedportrayals onlyno scientificpayloadcopies',x['footprint']['artifacts']=={'files':2,'bytes':3057491} and x['footprint']['components']['files']==22 and x['footprint']['publications']['files']==5)
check('single unbegun localimplementation decision nexttask',next_task['status']=='NOT BEGUN' and next_task['title']=='Atlas evidence-based local storage, processing and serving implementation decision' and len(next_task['acceptanceCriteria'])==8)
report=(R/'docs/research/atlas-temporal-integration.md').read_text(encoding='utf-8')
check('all32durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,33)))
check('fourrequired classifications plusbounded scientific/custody limits',all(v in report for v in ['DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT','controlled','single-writer','unknown','not total physical disk traffic']))
for p in NAV:check('resultandunbegun nexttask in '+p,all(v in (R/p).read_text(encoding='utf-8') for v in ['C - PROOF SUCCESS',next_task['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('appendonly developmenthistory',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')+'\n'))

def run(n,args):
 old=next((c for c in (prior or {}).get('commands',[]) if c['name']==n and c['args']==args and c['exitCode']==0),None)
 if ('--review-only' in sys.argv or '--reuse-unchanged-regression' in sys.argv and n!='temporal-focused') and old:
  assert intact()
  for p,h in prior['proofHashes'].items():
   if '--review-only' in sys.argv and p.endswith(('.py','.mjs','.json')) :assert sha(R/p)==h,p
  text=(LOG/(n+'.log')).read_text(encoding='utf-8');m=re.search(r'^(?:#|\u2139) tests (\d+)',text,re.M) or re.search(r'Ran (\d+) tests?',text);old={**old,'tests':int(m[1]) if m else None};check(n,True);commands.append({**old,'reusedPassedCommand':True,'basis':'original accepted inputs unchanged; exact prior successful logs reused; temporal-focused reruns unless reporting-only unchanged proof review'});print(n,'passed command reused',flush=True);return
 start=__import__('time').perf_counter();q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF'});(LOG/(n+'.log')).write_text(q.stdout+q.stderr,encoding='utf-8',newline='\n');check(n,q.returncode==0);m=re.search(r'^(?:#|\u2139) tests (\d+)',q.stdout,re.M) or re.search(r'Ran (\d+) tests?',q.stderr);commands.append(dict(name=n,args=args,exitCode=q.returncode,tests=int(m[1]) if m else None,elapsedSeconds=__import__('time').perf_counter()-start));print(n,q.returncode,flush=True)
 if q.returncode:print((q.stdout+q.stderr)[-2500:],flush=True)
run('temporal-focused',['node','--test',str(H/'test-proof.mjs')])
for c in read('docs/research/atlas-regional-dependencies-validation.json')['commands']:run(c['name'],c['args'])
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()+[OUT]))
allowed={OUT,*['docs/research/atlas-temporal-integration'+s for s in ['.md','-baseline.json','-results.json']]}|{'scripts/atlas/temporal-integration/'+p for p in ['plan.json','matrix.json','next-task.json','evidence.mjs','model.mjs','integration.mjs','oracle.py','worker.mjs','prove.mjs','test-proof.mjs','validate.py','README.md']}
check('proof/reporting onlyexact21path allowlist',set(changed)==allowed|NAV)
check('no unnecessarylargepayloads',all((R/p).stat().st_size<300000 and not p.endswith(('.tif','.png','.zip','.npy','.npz','.db','.pyc')) for p in changed if p not in NAV and p!=OUT))
for p in changed:
 if p.endswith('.json') and (R/p).exists():json.loads((R/p).read_text(encoding='utf-8-sig'))
 if p.endswith('.py'):ast.parse((R/p).read_text(encoding='utf-8-sig'))
check('finalcomplete structured file/untracked review',True)
missing=[]
for p in changed:
 if not p.endswith('.md'):continue
 text=(R/p).read_text(encoding='utf-8-sig')
 if p=='docs/development-log.md':text=text[len(git('show',BASE+':docs/development-log.md')):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if link.startswith(('http:','https:','mailto:')):continue
  target=unquote(link.strip('<>')).split('#')[0];f=(R/p).parent/target if target else R/p
  if not f.exists() and f.resolve()!=(R/OUT).resolve():missing.append([p,link])
check('documentation/navigation references resolve',not missing)
check('all original non-navigation tracked files unchanged aftertests',intact());check('all admitted source inventory unchanged aftertests',P.admission.assess()['sources']==before);check('all113production hashes unchanged aftertests',all(sha(R/p)==h for p,h in protected.items()));check('accepted17store files unchanged aftertests',all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()));check('accepted6prepared files unchanged aftertests',all(sha(prepared/p)==h for p,h in b['preparedHashes'].items()));check('unit receipts unchanged aftertests',all(sha(P.DATA/p)==h for p,h in b['unitEvidence'].items()));check('all66Exe files unchanged aftertests',exe_intact())
for p in ['docs/research/atlas-multi-region-results.json','docs/research/atlas-regional-dependencies-results.json']:check('accepted immutable state unchanged aftertests '+p,proof_store_intact(p))
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'));check('accepted current/310hashverification unchanged',state['generation']==accepted['current'] and state['verification']==accepted['sources'])
size=sum(p.stat().st_size for p in Path(plan['stateRoot']).rglob('*') if p.is_file());check('bounded external proof state below500MB',size<500000000)
receipt=dict(schema='atlas-temporal-integration-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),preservedTrackedFiles=len(keep),changedPaths=changed,canonicalThreads=42,protectedHashes=113,acceptedPilotUnchanged=not errors,retainedVerification=state['verification'],publishedGeneration=state['generation'],sourceAdmission=before,missingReferences=missing,decision=x['decision'],nextTask=next_task['title'],nextTaskStatus='NOT BEGUN',externalProofBytes=size,proofHashes={p:sha(R/p) for p in changed if p not in NAV and p!=OUT})
(R/OUT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors)),flush=True)
if errors:raise SystemExit(1)
