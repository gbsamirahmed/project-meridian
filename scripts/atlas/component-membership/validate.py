"""Component-proof regression; preserves accepted pilot, architecture assessment and all non-navigation baseline files."""
from pathlib import Path
import hashlib,json,subprocess,sys,re,os,importlib.util
from urllib.parse import unquote
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
spec=importlib.util.spec_from_file_location('measured_architecture_assess',R/'scripts/atlas/measured-architecture/assess.py');assess=importlib.util.module_from_spec(spec);spec.loader.exec_module(assess)
BASE='e88b575f51dc294806752a05bbbaee3a5d04efc8'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/atlas-component-membership.md';OUT='docs/research/atlas-component-membership-validation.json'
LOG=P.DATA/'experiments/atlas/component-membership-validation';LOG.mkdir(parents=True,exist_ok=True)
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
d=read('docs/research/atlas-component-membership-decisions.json');next_task=d['nextTask']
plan=read('scripts/atlas/component-membership/plan.json');results=read('docs/research/atlas-component-membership-results.json');baseline=read('docs/research/atlas-component-membership-baseline.json')
check('results and decision agree',results['decision']==d['decision']=='C - PROOF SUCCESS')
check('four decision levels',set(x['classification'] for x in d['records'])=={'DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT'})
check('prospective plan SHA',results['planSha256']==digest(R/'scripts/atlas/component-membership/plan.json')=='11c41e38c762526e116c9b05e8b0769f2ba66887445df0bf82c107f54f4f9f88')
check('measurement code hashes',all(digest(R/'scripts/atlas/component-membership'/p)==h for p,h in results['codeHashes'].items()))
check('measured source unchanged except LF packaging',all(digest(Path(v['path']))==v['sha256'] and Path(v['path']).read_bytes().replace(b'\r\n',b'\n')==(R/'scripts/atlas/component-membership'/p).read_bytes() for p,v in results['measurementCodePackaging']['files'].items()))
check('all authoritative contracts modules reports unchanged',all(digest(R/p)==h for p,h in plan['authoritativeHashes'].items()))
check('accepted store unchanged',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'/p)==h for p,h in baseline['acceptedStoreHashes'].items()))
check('previous scaling receipt preserved',results['baselineComparison']['sourceResultsSha256']==digest(R/'docs/research/atlas-generation-scaling-results.json'))
check('fixture receipt pinned',digest(Path(plan['stateRoot'])/'fixtures.json')==results['fixtureSha256'])
fixtures=json.loads((Path(plan['stateRoot'])/'fixtures.json').read_text(encoding='utf-8'))['records']
check('7 28 112 explicit immutable histories',len(fixtures)==3 and [f['depth'] for f in fixtures]==[7,28,112] and all(len(set(f['history']))==f['depth'] for f in fixtures))
check('five direct components shared across all depths',all(f['members']==fixtures[0]['members'] and f['legacy']==fixtures[0]['legacy'] and f['footprint']['components']=={'files':5,'bytes':1287421} for f in fixtures))
check('bounded index footprint explicit',all(f['footprint']['membership']['files']==33*f['depth'] and f['footprint']['publications']['files']==f['depth'] for f in fixtures))
expected={c['id']+'-'+m for c in plan['cases'] for m in plan['modes']}|{f"G{c['depth']}-{c['query']}" for c in plan['servingCases']}
check('all27 prospective primary cells',len(results['rows'])==27 and {r['id'] for r in results['rows']}==expected)
check('bounded membership selected lookup',all(r['reads']['membership']['calls']==33 and r['reads']['publications']['calls']==1 and r['counters']['ancestryTraversals']==0 for r in results['rows']))
check('five components integrity per hydrated request',all(r['reads']['components']=={'calls':5,'bytes':1287421} and r['counters']['integrityChecks']==39 for r in results['rows'] if r['mode']!='membership'))
check('membership only34 identity checks',all(r['counters']['integrityChecks']==34 and 'components' not in r['reads'] for r in results['rows'] if r['mode']=='membership'))
check('raw observations hash pinned',all(digest(Path(r['raw']['path']))==r['raw']['sha256'] for r in results['rows']))
raw=[(r,json.loads(Path(r['raw']['path']).read_text(encoding='utf-8'))) for r in results['rows']]
check('fresh warm repeats and counter parity',all(len(v['fresh'])==r['fresh'] and len(v['warm']['samples'])==r['warm'] and all(x['reads']==r['reads'] and x['counters']==r['counters'] and x['answerSha256']==r['answerSha256'] for x in v['warm']['samples']+[y['samples'][0] for y in v['fresh']]) for r,v in raw))
oldResults=read('docs/research/atlas-generation-scaling-results.json');oldHashes={r['query']:r['qualifiedSha256'] for r in oldResults['rows']}
check('WorldCover composed provenance exact qualified parity',all(r['qualifiedSha256']==oldHashes[r['mode']] for r in results['rows'] if r['mode'].startswith('Q')))
check('three supplementary historical raw receipts',len(results['historicalServed'])==3 and all(digest(Path(r['raw']['path']))==r['raw']['sha256'] and r['samples'][0]['qualifiedSha256']==oldHashes[r['query']] and r['samples'][0]['reads']['membership']['calls']==33 for r in results['historicalServed']))
l=results['lifecycle'];check('retained U1 first receipt pinned',digest(Path(l['path']))==l['sha256'] and json.loads(Path(l['path']).read_text(encoding='utf-8'))==l['receipt']);l=l['receipt']
check('retained scientific U1 exact',l['exactAcceptedU1'] and len(l['recomputed'])==2 and len(l['reusedResults'])==2)
check('actual relevant versus unrelated freshness',sum(x['assessment']['status']=='stale' for x in l['freshnessBefore'])==2 and sum(x['assessment']['status']=='fresh' for x in l['freshnessBefore'])==2)
check('three components reused two replaced',len(l['reusedComponents'])==3 and l['changedComponents']==['serving','understanding'] and len(l['components'])==7)
check('four original plus six historical current replays',len(l['replayBefore']['checks'])==4 and len(l['replayAfter']['checks'])==6 and all(x['exact'] for x in l['replayBefore']['checks']+l['replayAfter']['checks']))
check('method policy comparison explicit stale',all(x['assessment']['status']=='stale' for x in l['methodRelative']))
check('two interruptions coherent fresh historical consumers',len(l['failures'])==2 and all(x['exitCode']==91 and x['current']==l['g1'] and x['orphanRejected'] and x['freshServiceRecovered'] and x['pinnedConsumerUnchanged'] for x in l['failures']) and l['pinnedAcrossPublication'] and l['freshConsumer'])
check('required source hashing preserved',l['sourceVerification']=={'artifacts':310,'bytes':42473107})
f=results['failures'];check('seven failure receipt pinned',digest(Path(f['path']))==f['sha256'] and len(f['cases'])==7 and {x['scenario'] for x in f['cases']}==set(plan['failureCases']) and all(x['rootUnchanged'] for x in f['cases']))

for name,args in [
 ('proof-reproduction',[sys.executable,'scripts/atlas/component-membership/run.py','--check']),
 ('proof',['node','--test','scripts/atlas/component-membership/test-proof.mjs']),
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
allowed={REPORT,OUT,'docs/research/atlas-component-membership-results.json','docs/research/atlas-component-membership-baseline.json','docs/research/atlas-component-membership-decisions.json','docs/research/atlas-component-membership.svg'} | {'scripts/atlas/component-membership/'+n for n in ['plan.json','README.md','core.mjs','runtime.mjs','fixtures.mjs','worker.mjs','service-worker.mjs','interruption-worker.mjs','lifecycle-worker.mjs','failure-worker.mjs','run.py','test-proof.mjs','validate.py','plot.py']}
check('experiment-only exact allowed paths',all(p in NAV|allowed for p in changed))
check('small artifacts no source payloads',all((R/p).stat().st_size<150000 and not p.endswith(('.tif','.png','.db','.npz','.pyc')) for p in changed if p not in NAV))
text=(R/REPORT).read_text(encoding='utf-8');check('all40 report sections',list(map(int,re.findall(r'^## (\d+)\.',text,re.M)))==list(range(1,41)))
check('all conclusions explicitly classified',all(x['id'] in text and x['classification'] in text for x in d['records']))
for p in NAV:
 s=(R/p).read_text(encoding='utf-8');check('canonical experiment and one next '+p,'C - PROOF SUCCESS' in s and next_task in s)
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
receipt=dict(schema='atlas-component-membership-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),changedPaths=changed,preservedTrackedFiles=len(preserve),sourceAdmission=prior['sources'],retainedVerification=state['verification'],publishedGeneration=state['generation'],canonicalThreads=42,protectedHashes=113,missingReferences=missing,references=refs,decision=d['decision'],nextTask=next_task,acceptedPilotUnchanged=not errors,experimentHashes={p:digest(R/p) for p in allowed if p!=OUT})
(R/OUT).write_text(assess.encode(receipt),encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors,missing=missing)),flush=True)
if errors:raise SystemExit(1)
