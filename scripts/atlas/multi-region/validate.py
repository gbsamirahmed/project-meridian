"""Proof safeguards and established regression coverage. No accepted-state writes."""
from pathlib import Path
import ast,hashlib,json,os,re,subprocess,sys
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
BASE='d208a8627f616bbb9a474cdf23eda72c7bfea588';OUT='docs/research/atlas-multi-region-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
LOG=Path('C:/Users/gbsam/Documents/Codex/atlas-multi-region/regression');LOG.mkdir(parents=True,exist_ok=True)
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
b=read('docs/research/atlas-multi-region-baseline.json');before=b['sourceAdmission'];check('admitted retained source inventory unchanged before regression',P.admission.assess()['sources']==before)
check('all42 canonical research statuses unchanged',len(b['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==b['canonicalRows'])
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
check('accepted17 store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))
x=read('docs/research/atlas-multi-region-results.json');plan=read('scripts/atlas/multi-region/plan.json');matrix=read('scripts/atlas/multi-region/matrix.json');next_task=read('scripts/atlas/multi-region/next-task.json')
prepared=P.DATA/b['preparedRootRelative']
check('accepted6prepared artifacts unchanged before regression',len(b['preparedHashes'])==6 and all(sha(prepared/p)==h for p,h in b['preparedHashes'].items()))
check('exact starting checkpoint',b['commit']==BASE and b['divergence']=='0\t0')
check('exact immutable preparation revision',plan['regions']['riffelhorn']['preparedRevision']==b['preparedRevision'])
check('all38real query cases measured in3publications',len(matrix['cases'])==38 and len(x['observations'])==114 and len(x['history'])==3)
check('all342native comparisons agree',x['agreement'] and x['comparisons']==342 and all(a['agreement'] for a in x['observations']))
check('real two-region population',x['realPopulation']=={'tryfanArtifacts':310,'tryfanFamilies':5,'tryfanResults':6,'riffelhornInputs':12,'riffelhornPreparedArtifacts':6,'riffelhornRecords':44,'riffelhornDeclarations':50,'disconnectedCoreKm2':13})
check('both independent regional changes replace exactlyone component', [a['changed'] for a in x['reuse']]==[['riffelhornRegistration'],['tryfanRegistration']] and all(len(a['reused'])==6 for a in x['reuse']))
check('sevenexplicit memberships eachgeneration',all(set(m)==set(plan['components']) for m in x['members']))
check('unchanged originalTryfan scientific components',all(x['members'][0][k]==m[k] for m in x['members'] for k in ['catalogue','knowledge','understanding','serving','locators']))
check('threefresh complete historical replays agree',len(x['fresh'])==3 and all(a['agreement'] and set(a['answers'])==set(x['history']) and a['current']==x['history'][-1] for a in x['fresh']))
check('pinnedreplay coherent before/during/after',x['pinnedReplayAgreement'])
check('allselected resolution andquery measurements zeroancestry',all(a['measurement']['counters']['ancestryTraversals']==0 for a in x['resolution']+x['observations']))
check('bounded membership33nodes sevencomponentreads',all(a['measurement']['counters']['membershipVisits']==33 and a['measurement']['counters']['componentEdges']==7 for a in x['resolution']))
check('fullRiffverification inside eachpublication',all(a['measurement']['counters']['riffelhornFullVerifications']==1 and a['preparedVerification']['inputBytesVerified']==120347916 for a in x['publication']))
check('all310Tryfan currentbytes verified perpublication',all(a['measurement']['reads']['retained']['calls']==310 and a['measurement']['reads']['retained']['bytes']==42473107 for a in x['publication']))
check('sharedcomponents no copiedsourcepayload',x['footprint']['components']['files']==9 and x['footprint']['artifacts']=={'files':2,'bytes':3057491})
check('isolated store underfrozen proofroot',Path(x['store']).resolve().is_relative_to(Path(plan['stateRoot']).resolve()) and 'meridian-private' not in x['store'].lower())
check('source implementation measured unchanged',sha(R/'scripts/atlas/multi-region/integration.mjs')==x['implementationSha256'])
check('frozen matrix andplan measured',sha(R/'scripts/atlas/multi-region/matrix.json')==x['matrixSha256'] and sha(R/'scripts/atlas/multi-region/plan.json')==x['planSha256']==b['integrationPlanSha256'])
check('one nexttask notbegun',next_task['status']=='NOT BEGUN' and next_task['title']=='Atlas retained regional derivation and scoped dependency-density proof')
check('nexttask completebounded definition',len(next_task['acceptanceCriteria'])==8 and all(k in next_task for k in ['uncertainty','why','prerequisites','permittedWork','deliverable','stopCondition']))
report=(R/'docs/research/atlas-multi-region.md').read_text(encoding='utf-8')
check('all29report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,30)))
check('allfour architectural classifications',all(t in report for t in ['DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT']))
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
run('multi-region-focused',['node','--test',str(H/'test-proof.mjs')])
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
allowed={OUT,*['docs/research/atlas-multi-region'+t for t in ['.md','-baseline.json','-results.json']]}|{'scripts/atlas/multi-region/'+t for t in ['plan.json','next-task.json','matrix.json','integration.mjs','native-worker.py','reference.mjs','worker.mjs','prove.mjs','test-proof.mjs','validate.py','README.md']}
check('proof-only changed-path allowlist',all(p in allowed|NAV for p in changed))
check('no large or source payload files committed',all((R/p).stat().st_size<150000 and not p.endswith(('.png','.tif','.las','.zip','.npz','.db','.pyc')) for p in changed if p not in NAV and p!=OUT))
structured=True
for p in changed:
 if p.endswith('.json') and (R/p).exists():json.loads((R/p).read_text(encoding='utf-8-sig'))
 if p.endswith('.py'):ast.parse((R/p).read_text(encoding='utf-8-sig'))
check('full final structured-file and untracked-path review',structured and len(changed)==20)
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
receipt=dict(schema='atlas-multi-region-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),preservedTrackedFiles=len(keep),changedPaths=changed,canonicalThreads=42,protectedHashes=113,acceptedPilotUnchanged=not errors,sourceAdmission=before,retainedVerification=state['verification'],publishedGeneration=state['generation'],missingReferences=missing,decision=x['decision'],nextTask=next_task['title'],nextTaskStatus='NOT BEGUN',proofHashes={p:sha(R/p) for p in changed if p not in NAV and p!=OUT})
(R/OUT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors)),flush=True)
if errors:raise SystemExit(1)
