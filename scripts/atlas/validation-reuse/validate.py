"""Validation-reuse regression; preserves accepted pilot, architecture assessment and all non-navigation baseline files."""
from pathlib import Path
import hashlib,json,subprocess,sys,re,os,importlib.util
from urllib.parse import unquote
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
spec=importlib.util.spec_from_file_location('measured_architecture_assess',R/'scripts/atlas/measured-architecture/assess.py');assess=importlib.util.module_from_spec(spec);spec.loader.exec_module(assess)
BASE='38f9ba79822ab2498f6f4acf387e07b5b79f22ba'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/atlas-validation-reuse.md';OUT='docs/research/atlas-validation-reuse-validation.json'
LOG=P.DATA/'experiments/atlas/validation-reuse-validation';LOG.mkdir(parents=True,exist_ok=True)
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
d=read('docs/research/atlas-validation-reuse-decisions.json');next_task=d['nextTask']
plan=read('scripts/atlas/validation-reuse/plan.json');results=read('docs/research/atlas-validation-reuse-results.json');baseline=read('docs/research/atlas-validation-reuse-baseline.json');inventory=read('scripts/atlas/validation-reuse/inventory.json')
check('results and decision agree',results['decision']==d['decision']=='C - PROOF SUCCESS')
check('frozen hypotheses and matrix',len(plan['hypotheses'])==4 and plan['componentsPerFamily']==[4,16,64] and plan['fanouts']==[1,4] and results['planSha256']==digest(R/'scripts/atlas/validation-reuse/plan.json')=='d75f37cfad5da78c34e12891d127331831b49ffb5fa449bc041ca728cb26241b')
check('four architecture classifications',set(x['classification'] for x in d['records'])=={'DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT'})
check('all authoritative inputs unchanged',all(digest(R/p)==h for p,h in plan['authoritativeHashes'].items()))
check('timed implementation hashes',all(digest(R/'scripts/atlas/validation-reuse'/p)==h for p,h in results['codeHashes'].items()))
check('accepted all17 store hashes unchanged',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'/p)==h for p,h in baseline['acceptedStoreHashes'].items()))
check('baseline310 artifacts42MB seven histories',baseline['sources']=={'artifacts':310,'bytes':42473107} and len(baseline['history'])==7)
check('inventory actual guarantees all categories',len(inventory['checks'])==10 and all(x['inputs'] and x['reuseConditions'] and x['existing'] for x in inventory['checks']))
cases=results['cases'];primary=[x for x in cases if not x.get('boundary')];boundary=[x for x in cases if x.get('boundary')]
check('24 primary22 boundary cases',len(primary)==24 and len(boundary)==22)
check('every46 proposal oracle agreement',len(cases)==46 and results['disagreements']==0 and all(x['full']['accepted']==x['incremental']['accepted']==x['expected'] for x in cases))
check('29 valid17 invalid expected verdicts',sum(x['expected'] for x in cases)==29 and sum(not x['expected'] for x in cases)==17)
check('all fixed population/rule records covered',{x['components'] for x in primary}=={12,48,192} and {x['fanout'] for x in primary}=={1,4} and {x['pattern'] for x in primary}==set(plan['changes']))
check('component checks all executed or reused',all(x['incremental']['counter']['localChecks']+x['incremental']['counter']['localReused']==x['components'] for x in primary))
check('all crosschecks executed or reused',all(x['incremental']['counter']['crossChecks']+x['incremental']['counter']['crossReused']==x['n']*x['fanout'] for x in primary))
check('current integrity never skipped',all(x[m]['counter']['componentIntegrity']==x['components'] for x in primary for m in ['full','incremental']))
check('population membership and trust scans reported',all(x['incremental']['counter']['membershipChecks']==x['components'] and x['incremental']['counter']['trustDirectoryEntries']==x['components'] for x in primary))
check('all recordchecks actual localchecks',all(x[m]['counter']['rowsChecked']==64*x[m]['counter']['localChecks'] for x in primary for m in ['full','incremental']))
check('selected relationships not hidden full traversal',all(x['incremental']['counter']['crossChecks']==x['fanout']**2 and x['incremental']['counter']['selectionEdges']==x['fanout'] for x in primary if x['pattern']=='one-local'))
lookup={x['id']:x for x in cases}
check('rule rotation revalidates every component',lookup['stale-rule-evidence']['incremental']['counter']['localReused']==0 and lookup['stale-rule-evidence']['incremental']['counter']['rowsChecked']==3072)
check('invalid trust falls back without altering acceptance',all(lookup[n]['incremental']['counter']['fallbacks']>0 and lookup[n]['incremental']['accepted'] for n in ['forged-receipt','missing-trust-index','unknown-anchor']))
check('invalidity cannot be hidden by trust corruption',all(not lookup[n]['incremental']['accepted'] for n in ['corrupt-receipt-and-invalid-component','corrupt-index-and-stale']))
check('freshness not historical falsehood',lookup['historical-stale-allowed']['expected'] and not lookup['unrecomputed-dependency']['expected'])
check('all raw observations hash pinned',all(digest(Path(x['path']))==x['sha256'] for x in results['rawFiles']))
check('six history pins zero ancestry33 nodes',len(results['history'])==6 and all(x['resolution']['ancestry']==0 and x['resolution']['membershipReads']==33 and x['fresh']['accepted'] for x in results['history']))
check('four abrupt failure points',len([x for x in results['safety'] if 'point' in x])==4 and all(x['exitCode']==79 and x['currentUnchanged'] and x['candidateIneligible'] and x['freshAccepted'] for x in results['safety'] if 'point' in x))
check('two successful retries immutable pinned history',len([x for x in results['safety'] if 'retryPublished' in x])==2 and all(x['previousReadable'] and x['pinnedUnchanged'] for x in results['safety'] if 'retryPublished' in x))
check('fresh processes modes and unavailable RSS honest',len(results['fresh'])==4 and {x['mode'] for x in results['fresh']}=={'full','incremental'} and all(x['rssRange'] is None and x['medianStartupMs']>0 for x in results['fresh']))
check('full preparation and footprint separately measured',len(results['preparations'])==6 and all(x['preparation']['counter']['rowsChecked']==x['n']*3*64 and x['validationEvidenceBytes']>0 for x in results['preparations']))
check('next task not begun',d['nextTaskStatus']=='NOT BEGUN' and 'maintenance and amortization' in next_task)
for name,args in [
 ('validation-reuse-reproduction',[sys.executable,'scripts/atlas/validation-reuse/run.py','--check']),
 ('validation-reuse',[sys.executable,'scripts/atlas/validation-reuse/test_proof.py']),
 ('granularity-reproduction',[sys.executable,'scripts/atlas/component-granularity/run.py','--check']),
 ('granularity',[sys.executable,'scripts/atlas/component-granularity/test_model.py']),
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
allowed={REPORT,OUT,'docs/research/atlas-validation-reuse-results.json','docs/research/atlas-validation-reuse-baseline.json','docs/research/atlas-validation-reuse-decisions.json','docs/research/atlas-validation-reuse.svg'} | {'scripts/atlas/validation-reuse/'+n for n in ['plan.json','inventory.json','README.md','core.py','run.py','worker.py','test_proof.py','validate.py','plot.py']}
check('experiment-only exact allowed paths',all(p in NAV|allowed for p in changed))
check('small artifacts no source payloads',all((R/p).stat().st_size<(500000 if p.endswith('validation-reuse-results.json') else 150000) and not p.endswith(('.tif','.png','.db','.npz','.pyc')) for p in changed if p not in NAV))
text=(R/REPORT).read_text(encoding='utf-8');check('all38 report sections',list(map(int,re.findall(r'^## (\d+)\.',text,re.M)))==list(range(1,39)))
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
receipt=dict(schema='atlas-validation-reuse-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),changedPaths=changed,preservedTrackedFiles=len(preserve),sourceAdmission=prior['sources'],retainedVerification=state['verification'],publishedGeneration=state['generation'],canonicalThreads=42,protectedHashes=113,missingReferences=missing,references=refs,decision=d['decision'],nextTask=next_task,acceptedPilotUnchanged=not errors,experimentHashes={p:digest(R/p) for p in allowed if p!=OUT})
(R/OUT).write_text(assess.encode(receipt),encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors,missing=missing)),flush=True)
if errors:raise SystemExit(1)
