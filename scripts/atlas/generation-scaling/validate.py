"""Scaling-stage regression; preserves accepted pilot, architecture assessment and all non-navigation baseline files."""
from pathlib import Path
import hashlib,json,subprocess,sys,re,os,importlib.util
from urllib.parse import unquote
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
spec=importlib.util.spec_from_file_location('measured_architecture_assess',R/'scripts/atlas/measured-architecture/assess.py');assess=importlib.util.module_from_spec(spec);spec.loader.exec_module(assess)
BASE='c4f50a40369c2e43c48cebb53c1de13b4c2bb4f3'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/atlas-generation-scaling.md';OUT='docs/research/atlas-generation-scaling-validation.json'
LOG=P.DATA/'experiments/atlas/generation-scaling-validation';LOG.mkdir(parents=True,exist_ok=True)
checks=[];errors=[];commands=[]
def check(name,ok):
 checks.append(dict(check=name,passed=bool(ok)))
 if not ok:errors.append(name)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def run(name,args):
 q=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
 (LOG/(name+'.log')).write_text(q.stdout+q.stderr,encoding='utf-8',newline='\n');check(name,q.returncode==0)
 n=re.search(r'^(?:#|\u2139) tests (\d+)',q.stdout,re.M) or re.search(r'Ran (\d+) tests?',q.stderr)
 commands.append(dict(name=name,args=args,exitCode=q.returncode,tests=int(n[1]) if n else None));print(name,q.returncode,flush=True)
 if q.returncode:print((q.stdout+q.stderr)[-3000:],flush=True)
check('starting baseline ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
tracked=git('ls-tree','-r','--name-only',BASE).splitlines();preserve=[p for p in tracked if p not in NAV]
tree={line.split('\t')[1]:line.split()[2] for line in git('ls-tree','-r',BASE).splitlines()}
def intact():
 hs=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(preserve)+'\n',text=True).splitlines()
 return len(hs)==len(preserve) and all(h==tree[p] for p,h in zip(preserve,hs))
check('all accepted pilot and non-navigation history unchanged',intact())
b=read('docs/research/tryfan-pilot-s6-baseline.json');old=git('show',BASE+':docs/research/atlas-research-state.md');cur=(R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8')
check('all42 research statuses unchanged',len(P.admission.canonical_rows(cur))==42 and P.admission.canonical_rows(cur)==P.admission.canonical_rows(old))
protected=read('docs/atlas/information-display-plan.json')['productionHashes']
def protected_ok():return len(protected)==113 and all(digest(R/p)==h for p,h in protected.items())
check('all113 protected production hashes',protected_ok())
check('all seven historical generations unchanged',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1/generations'/f"{h['generation']}.json")==h['sha256'] for h in b['history']))
prior=P.admission.assess();check('1575 retained sources verified',prior['sources']['uniqueFiles']==1575)
check('planning structure preserved',P.check_structure(read('docs/research/tryfan-regional-pilot-plan.json')))
check('receipt reproduces',assess.encode(assess.build())==(R/assess.OUT).read_text(encoding='utf-8'))
d=read('docs/research/atlas-generation-scaling-decisions.json');next_task=d['nextTask']
plan=read('scripts/atlas/generation-scaling/plan.json');results=read('docs/research/atlas-generation-scaling-results.json');baseline=read('docs/research/atlas-generation-scaling-baseline.json')
check('results and decision agree',results['decision']==d['decision'])
check('failure evidence hash pinned',digest(Path(results['failureEvidence']['path']))==results['failureEvidence']['sha256'])
check('measurement code hashes',all(digest(R/'scripts/atlas/generation-scaling'/p)==h for p,h in results['measurementCodeHashes'].items()))
check('four decision levels',set(x['classification'] for x in d['records'])=={'DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT'})
check('frozen experiment matrix and hashes',plan['historyDepths']==[7,28,112] and len(plan['cases'])==18 and results['planSha256']==digest(R/'scripts/atlas/generation-scaling/plan.json'))
check('accepted store unchanged',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'/p)==h for p,h in baseline['acceptedStoreHashes'].items()))
check('authoritative frozen hashes',all(digest(R/p)==h for p,h in plan['authoritativeHashes'].items()))
check('same scientific components at every depth',all(f['componentHashes']==results['fixtures'][0]['componentHashes'] for f in results['fixtures']))
check('all18 measured cases',len(results['rows'])==18 and {x['id'] for x in results['rows']}=={x['id'] for x in plan['cases']})
check('per query qualified equivalence',all(len({x['qualifiedSha256'] for x in results['rows'] if x['query']==q})==1 for q in plan['queries']))
check('once per distinct generation each request',all(x['structural']['reads']['generations']['calls']==x['depth'] and x['structural']['counters']['integrityChecks']==x['depth'] for x in results['rows'] if x['variant']=='request-reuse'))
check('raw observations hash pinned',all(digest(Path(x['raw']['path']))==x['raw']['sha256'] for x in results['rows']))
check('fresh/warm repeat counts',all(len(json.loads(Path(x['raw']['path']).read_text(encoding='utf-8'))['fresh'])==5 and len(json.loads(Path(x['raw']['path']).read_text(encoding='utf-8'))['warm']['samples'])==20 for x in results['rows']))
check('six historical observations explicit',len(results['historical'])==6 and all(x['selected']==baseline['current'] for x in results['historical']))
check('seven metadata-only controls',len(results['referenceControls'])==7 and all(x['actualReused']+x['changedReferences']==x['objects'] for x in results['referenceControls']))
check('four architecture levels explicit',set(x['classification'] for x in d['records'])=={'DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT'})

for name,args in [
 ('scaling-reproduction',[sys.executable,'scripts/atlas/generation-scaling/run.py','--check']),
 ('scaling',['node','--test','scripts/atlas/generation-scaling/test-experiment.mjs']),
 ('assessment',[sys.executable,'scripts/atlas/measured-architecture/test_assess.py']),
 ('s6',['node','--test','pilots/atlas/tryfan/tests/acceptance.test.mjs']),
 ('s1-s5',['node','--test',*[f'pilots/atlas/tryfan/tests/{n}.test.mjs' for n in ['catalogue','query','lifecycle','http','publication','restart']]]),
 ('s6-browser',['node','pilots/atlas/tryfan/tests/browser-s6.mjs']),
 ('s5-browser',['node','pilots/atlas/tryfan/tests/publication-browser.mjs']),
 ('native',[sys.executable,'pilots/atlas/tryfan/adapters/test_native.py']),
 ('planning',[sys.executable,'scripts/atlas/regional-pilot-plan/test_plan.py']),
 ('frozen',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']),
 ('qualified',['node','--test','scripts/atlas/test_qualified_query_proof.mjs']),
 ('persistent',['node','--test','scripts/atlas/test_local_persistent_tryfan.mjs']),
 ('exe',['node','--test','scripts/atlas/exe-water-query-proof/test-proof.mjs']),
 ('s5-reproduction',['node','pilots/atlas/tryfan/measure_s5.mjs','--check']),
 ('semantic-types',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json']),
 ('lint',['npm.cmd','run','lint']),('build',['npm.cmd','run','build'])]:run(name,args)
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'))
check('current published generation preserved with310 asset hashes',state['generation']==b['current'] and state['verification']==b['sources'])
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
allowed={REPORT,OUT,'docs/research/atlas-generation-scaling-results.json','docs/research/atlas-generation-scaling-baseline.json','docs/research/atlas-generation-scaling-decisions.json'} | {'scripts/atlas/generation-scaling/'+n for n in ['plan.json','README.md','runtime.mjs','fixtures.mjs','worker.mjs','failure-worker.mjs','run.py','supplement.py','test-experiment.mjs','validate.py','plot.py']} | {'docs/research/atlas-generation-scaling.svg'}
check('experiment-only exact allowed paths',all(p in NAV|allowed for p in changed))
check('small artifacts no source payloads',all((R/p).stat().st_size<150000 and not p.endswith(('.tif','.png','.db','.npz','.pyc')) for p in changed if p not in NAV))
text=(R/REPORT).read_text(encoding='utf-8');check('all39 report sections',list(map(int,re.findall(r'^## (\d+)\.',text,re.M)))==list(range(1,40)))
check('all conclusions explicitly classified',all(x['id'] in text and x['classification'] in text for x in d['records']))
for p in NAV:
 s=(R/p).read_text(encoding='utf-8');check('canonical experiment and one next '+p,'C - EXPERIMENT RESOLVED' in s and next_task in s)
check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(git('show',BASE+':docs/development-log.md')+'\n'))
def slugs(text):
 out=set();seen={}
 for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1;out.add(key if not n else key+'-'+str(n))
 return out
missing=[];refs=0
for p in changed:
 if not p.endswith('.md'):continue
 text=(R/p).read_text(encoding='utf-8')
 if p=='docs/development-log.md':text=text[len(git('show',BASE+':docs/development-log.md')):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if link.startswith(('http:','https:','mailto:','meridian-data:')):continue
  path,_,anchor=unquote(link.strip('<>')).partition('#');target=(R/p).parent/path if path else R/p;refs+=1
  if (not target.exists() and target.resolve()!=(R/OUT).resolve()) or anchor and target.suffix=='.md' and anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([p,link])
check('references and anchors resolve',not missing);run('diff',['git','diff','--check'])
final=P.admission.assess();check('retained sources unchanged after regression',final['sources']==prior['sources']);check('accepted persistent store unchanged after regression',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'/p)==h for p,h in baseline['acceptedStoreHashes'].items()));check('all non-navigation bytes unchanged after regression',intact());check('protected hashes unchanged after regression',protected_ok())
receipt=dict(schema='atlas-generation-scaling-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),changedPaths=changed,preservedTrackedFiles=len(preserve),sourceAdmission=prior['sources'],retainedVerification=state['verification'],publishedGeneration=state['generation'],canonicalThreads=42,protectedHashes=113,missingReferences=missing,references=refs,decision=d['decision'],nextTask=next_task,acceptedPilotUnchanged=not errors,experimentHashes={p:digest(R/p) for p in allowed if p!=OUT})
(R/OUT).write_text(assess.encode(receipt),encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors,missing=missing)),flush=True)
if errors:raise SystemExit(1)
