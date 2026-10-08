"""Proof safeguards and established regression coverage. No accepted-state writes."""
from pathlib import Path
import ast,hashlib,json,os,re,subprocess,sys
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
BASE='d55584feec520c0a550dc8a4b40f973bd4eee95e';OUT='docs/research/atlas-riffelhorn-retrieval-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
LOG=Path('C:/Users/gbsam/Documents/Codex/atlas-riffelhorn-retrieval/regression');LOG.mkdir(parents=True,exist_ok=True)
checks=[];errors=[];commands=[]
prior=None
if '--reuse-unchanged-regression' in sys.argv and (R/OUT).exists():
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
b=read('docs/research/atlas-riffelhorn-retrieval-baseline.json');before=b['sourceAdmission'];check('admitted retained source inventory unchanged before regression',P.admission.assess()['sources']==before)
check('all42 canonical research statuses unchanged',len(b['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==b['canonicalRows'])
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
check('accepted17 store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))
x=read('docs/research/atlas-riffelhorn-retrieval-results.json');plan=read('scripts/atlas/riffelhorn-retrieval/plan.json');matrix=read('scripts/atlas/riffelhorn-retrieval/matrix.json')
prepared=P.DATA/b['preparedRootRelative']
check('accepted6prepared artifacts unchanged before regression',len(b['preparedHashes'])==6 and all(sha(prepared/p)==h for p,h in b['preparedHashes'].items()))
check('exact starting checkpoint',b['commit']==BASE and b['divergence']=='0\t0')
check('exact immutable fixture revision',x['preparedRevision']==plan['preparedRevision']==b['preparedRevision'])
check('actual population44not synthetic',x['realPopulation']['metadataRecords']==44 and x['realPopulation']['features']==38 and x['realPopulation']['rasterSupports']==6 and not x['syntheticPopulationExpansion'])
check('three distinct candidate organisations',x['organisations']==['scan','grouped','selective'])
check('all29real matrix cases measured',x['matrixCases']==len(matrix['cases'])==29 and len(x['observations'])==87)
check('all435repeated full-envelope comparisons agree',x['agreement'] and x['comparableRepeatedQueries']==435 and all(a['agreement'] for a in x['observations']))
check('case hashes agree across organisations',all(len({a['answerSha256'] for a in x['observations'] if a['case']==c['id']})==1 for c in matrix['cases']))
check('all3fresh processes agree',len(x['freshProcessRuns'])==3 and all(a['answerHashesAgree'] for a in x['freshProcessRuns']))
check('no ancestry/persistent index',x['persistentIndexBytes']==0 and all(a['metrics']['ancestryTraversals']==0 for a in x['observations']))
check('full startup hydration explicitly accounted',x['setup']['loadedRecords']==44 and x['setup']['metadataMembersParsed']==5 and x['setup']['metadataMemberBytes']==5603919)
check('actualyearqualifications not fabricated',x['realPopulation']['evidenceEpochDistribution']=={'2015-survey':1,'2016-survey':6,'2021-nominal':1,'unknown-exact-epoch':36})
check('source implementation measured unchanged',sha(R/'scripts/atlas/riffelhorn-retrieval/query.py')==x['sourceImplementationSha256'])
check('frozen matrix and plan measured',sha(R/'scripts/atlas/riffelhorn-retrieval/matrix.json')==x['matrixSha256'] and sha(R/'scripts/atlas/riffelhorn-retrieval/plan.json')==x['planSha256'])
check('exactlyone next task not begun',x['nextTask']['status']=='NOT BEGUN' and x['nextTask']['title']=='Atlas retained Tryfan and Riffelhorn coherent multi-region world-model integration proof')
check('next task complete bounded definition',len(x['nextTask']['acceptanceCriteria'])==8 and all(k in x['nextTask'] for k in ['uncertainty','why','prerequisites','permittedWork','deliverable','stopCondition']))
report=(R/'docs/research/atlas-riffelhorn-retrieval.md').read_text(encoding='utf-8-sig')
check('all30report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,31)))
check('all four decision classes',all(t in report for t in ['DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT']))
for p in NAV:check('result boundary and next task in '+p,all(t in (R/p).read_text(encoding='utf-8') for t in ['C - PROOF SUCCESS',x['nextTask']['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('append-only development history',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')+'\n'))
def run(n,args):
 start=__import__('time').perf_counter();q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'});(LOG/(n+'.log')).write_text(q.stdout+q.stderr,encoding='utf-8',newline='\n');check(n,q.returncode==0);m=re.search(r'^(?:#|\u2139) tests (\d+)',q.stdout,re.M) or re.search(r'Ran (\d+) tests?',q.stderr);commands.append(dict(name=n,args=args,exitCode=q.returncode,tests=int(m[1]) if m else None,elapsedSeconds=__import__('time').perf_counter()-start));print(n,q.returncode,flush=True)
 if q.returncode:print((q.stdout+q.stderr)[-2200:],flush=True)
run('retrieval-focused',[sys.executable,str(H/'test_query.py')])
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
allowed={OUT,*['docs/research/atlas-riffelhorn-retrieval'+t for t in ['.md','-baseline.json','-population.json','-results.json']]}|{'scripts/atlas/riffelhorn-retrieval/'+t for t in ['plan.json','next-task.json','matrix.json','query.py','test_query.py','measure.py','validate.py','README.md']}
check('proof-only changed-path allowlist',all(p in allowed|NAV for p in changed))
check('no large or source payload files committed',all((R/p).stat().st_size<150000 and not p.endswith(('.png','.tif','.las','.zip','.npz','.db','.pyc')) for p in changed if p not in NAV and p!=OUT))
structured=True
for p in changed:
 if p.endswith('.json') and (R/p).exists():json.loads((R/p).read_text(encoding='utf-8-sig'))
 if p.endswith('.py'):ast.parse((R/p).read_text(encoding='utf-8-sig'))
check('full final structured-file and untracked-path review',structured and len(changed)==18)
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
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'));check('accepted current and310source hashes unchanged',state['generation']==accepted['current'] and state['verification']==accepted['sources'])
receipt=dict(schema='atlas-riffelhorn-retrieval-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),preservedTrackedFiles=len(keep),changedPaths=changed,canonicalThreads=42,protectedHashes=113,acceptedPilotUnchanged=not errors,sourceAdmission=before,retainedVerification=state['verification'],publishedGeneration=state['generation'],missingReferences=missing,decision=x['decision'],nextTask=x['nextTask']['title'],nextTaskStatus='NOT BEGUN',proofHashes={p:sha(R/p) for p in changed if p not in NAV and p!=OUT})
(R/OUT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors)),flush=True)
if errors:raise SystemExit(1)
