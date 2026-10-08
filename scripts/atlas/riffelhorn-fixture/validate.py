"""Proof safeguards and established regression coverage. No accepted-state writes."""
from pathlib import Path
import ast,hashlib,json,os,re,subprocess,sys
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.stdout.reconfigure(encoding='utf-8');sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
BASE='c53c478babbedd7aac609cf091503a8fd7fbe287';OUT='docs/research/atlas-riffelhorn-preparation-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
LOG=Path('C:/Users/gbsam/Documents/Codex/atlas-riffelhorn-preparation/regression');LOG.mkdir(parents=True,exist_ok=True)
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
b=read('docs/research/atlas-riffelhorn-preparation-baseline.json');before=b['sourceAdmission'];check('admitted retained source inventory unchanged before regression',P.admission.assess()['sources']==before)
check('all42 canonical research statuses unchanged',len(b['canonicalRows'])==42 and P.admission.canonical_rows((R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8'))==b['canonicalRows'])
accepted=read('docs/research/atlas-integrity-cost-baseline.json');store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
check('accepted17 store files unchanged',len(accepted['acceptedStoreHashes'])==17 and all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()))
x=read('docs/research/atlas-riffelhorn-preparation-results.json');s=read('docs/research/atlas-regional-expansion-fixture.json');plan=read('scripts/atlas/riffelhorn-fixture/plan.json')
check('expected clean starting checkpoint',b['commit']==BASE and b['branch']=='main' and b['divergence']=='0\t0')
check('specification still frozen',sha(R/plan['specification'])==plan['specificationSha256'])
check('all12 selected sources unchanged',len(s['inputs'])==12 and all(sha(P.DATA/a['path'])==a['sha256'] for a in s['inputs']))
check('exact input byte count',sum(a['bytes'] for a in s['inputs'])==x['inputBytes']==120347916)
check('three independent byte-identical empty builds',x['byteIdenticalEmptyRebuilds'] and len(x['independentEmptyRuns'])==3 and len({a['revision'] for a in x['independentEmptyRuns']})==1)
check('three matching fresh-process verifications',len(x['freshProcessRuns'])==3 and all(a['complete'] and a['revision']==x['revision'] for a in x['freshProcessRuns']))
check('metadata only no raster payload copy',x['rasterPayloadCopies']==0 and x['nativeFeatures']==38 and x['claims']==50)
check('five semantic collections ten resources',x['semanticCounts']['collections']==5 and x['semanticCounts']['resources']==10)
check('exact immutable preparation membership',len(x['manifest']['artifacts'])==5 and x['manifest']['revision']==x['revision'])
check('prepared payload outside code and accepted pilot',x['externalRootRelative'].startswith('derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1/'))
check('implementation hashes agree',all(sha(R/p)==h for p,h in x['sourceImplementationHashes'].items()))
root=P.DATA/x['externalRootRelative'];q=json.loads((root/'qualification.json').read_text(encoding='utf-8'))
check('not registered queried derived published or served',q['integration']['prepared'] and all(not v for k,v in q['integration'].items() if k!='prepared'))
check('full geometry originalZIP selection documented',q['glamosSelection']['counts']=={'glaciers':1,'debris':6} and not q['glamosSelection']['geometryClipping'] and not q['glamosSelection']['geometryRepair'])
check('optional references unchanged conditional',q['optionalReferences']==s['optionalReferencePreparations'])
check('scientific exclusions preserved',q['excludedClaims']==s['excludedClaims'] and q['unknowns']==s['nonBlockingUnknowns'])
check('rights boundary preserved',q['rightsBoundary']==s['rightsBoundary'] and q['rightsReferences']==s['rightsReferences'])
check('2D eligibility distinct support',q['core']['bounds']==s['supports'][0]['bounds'] and q['coordinateOperation']['verticalOperation']=='none')
check('exact one bounded next task not begun',x['nextTask']['status']=='NOT BEGUN' and x['nextTask']['title']=='Atlas prepared Riffelhorn qualified spatial, feature and temporal retrieval proof')
check('next task has complete acceptance boundary',len(x['nextTask']['acceptanceCriteria'])==8 and all(k in x['nextTask'] for k in ['uncertainty','why','prerequisites','permittedWork','deliverable','stopCondition']))
report=(R/'docs/research/atlas-riffelhorn-preparation.md').read_text(encoding='utf-8-sig')
check('all29 durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,30)))
check('all four classification sections',all('## '+str(i)+'. '+t in report for i,t in [(22,'DECIDE NOW'),(23,'PROVISIONAL DIRECTION'),(24,'DEFER PENDING EVIDENCE'),(25,'REJECT')]))
for p in NAV:check('result next task and boundary in '+p,all(t in (R/p).read_text(encoding='utf-8') for t in ['C - PROOF SUCCESS',x['nextTask']['title'],'Tryfan remains CLOSED / ACCEPTED']))
check('append-only development history',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')+'\n'))
def run(n,args):
 start=__import__('time').perf_counter();q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'});(LOG/(n+'.log')).write_text(q.stdout+q.stderr,encoding='utf-8',newline='\n');check(n,q.returncode==0);m=re.search(r'^(?:#|\u2139) tests (\d+)',q.stdout,re.M) or re.search(r'Ran (\d+) tests?',q.stderr);commands.append(dict(name=n,args=args,exitCode=q.returncode,tests=int(m[1]) if m else None,elapsedSeconds=__import__('time').perf_counter()-start));print(n,q.returncode,flush=True)
 if q.returncode:print((q.stdout+q.stderr)[-2200:],flush=True)
run('preparation-focused',[sys.executable,str(H/'test_prepare.py')])
run('preparation-fresh-verification',[sys.executable,str(H/'prepare.py'),'verify','--output',str(root)])
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
allowed={OUT,*['docs/research/atlas-riffelhorn-preparation'+t for t in ['.md','-baseline.json','-results.json']]}|{'scripts/atlas/riffelhorn-fixture/'+t for t in ['plan.json','next-task.json','prepare.py','test_prepare.py','measure.py','validate.py','verify_semantic.mjs','README.md']}
check('proof-only changed-path allowlist',all(p in allowed|NAV for p in changed))
check('no large or source payload files committed',all((R/p).stat().st_size<150000 and not p.endswith(('.png','.tif','.las','.zip','.npz','.db','.pyc')) for p in changed if p not in NAV and p!=OUT))
structured=True
for p in changed:
 if p.endswith('.json') and (R/p).exists():json.loads((R/p).read_text(encoding='utf-8-sig'))
 if p.endswith('.py'):ast.parse((R/p).read_text(encoding='utf-8-sig'))
check('full final structured-file and untracked-path review',structured and len(changed)==17)
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
check('all original non-navigation tracked files unchanged after regression',intact());check('all admitted source inventory unchanged after regression',P.admission.assess()['sources']==before);check('all113 protected production hashes unchanged after regression',all(sha(R/p)==h for p,h in protected.items()));check('accepted store unchanged after regression',all(sha(store/p)==h for p,h in accepted['acceptedStoreHashes'].items()));check('all12 native input hashes unchanged after regression',all(sha(P.DATA/a['path'])==a['sha256'] for a in s['inputs']))
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'));check('accepted current and310source hashes unchanged',state['generation']==accepted['current'] and state['verification']==accepted['sources'])
receipt=dict(schema='atlas-riffelhorn-preparation-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),preservedTrackedFiles=len(keep),changedPaths=changed,canonicalThreads=42,protectedHashes=113,acceptedPilotUnchanged=not errors,sourceAdmission=before,retainedVerification=state['verification'],publishedGeneration=state['generation'],missingReferences=missing,decision=x['decision'],nextTask=x['nextTask']['title'],nextTaskStatus='NOT BEGUN',proofHashes={p:sha(R/p) for p in changed if p not in NAV and p!=OUT})
(R/OUT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors)),flush=True)
if errors:raise SystemExit(1)
