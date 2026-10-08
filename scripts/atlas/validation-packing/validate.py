"""Validation-maintenance regression; preserves accepted pilot, architecture assessment and all non-navigation baseline files."""
from pathlib import Path
import hashlib,json,subprocess,sys,re,os,importlib.util
from urllib.parse import unquote
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
spec=importlib.util.spec_from_file_location('measured_architecture_assess',R/'scripts/atlas/measured-architecture/assess.py');assess=importlib.util.module_from_spec(spec);spec.loader.exec_module(assess)
BASE='a027ec76d1d9f34325a4b4d1023c81ae6ff27a60'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/atlas-validation-packing.md';OUT='docs/research/atlas-validation-packing-validation.json'
LOG=P.DATA/'experiments/atlas/validation-packing-validation';LOG.mkdir(parents=True,exist_ok=True)
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
d=read('docs/research/atlas-validation-packing-decisions.json');next_task=d['nextTask']
plan=read('scripts/atlas/validation-packing/plan.json');results=read('docs/research/atlas-validation-packing-results.json');baseline=read('docs/research/atlas-validation-packing-baseline.json')
check('decision agrees',results['decision']==d['decision']=='C - PROOF SUCCESS')
check('frozen hypotheses and matrix',len(plan['hypotheses'])==5 and len(plan['sequences'])==13 and results['planSha256']==digest(R/'scripts/atlas/validation-packing/plan.json')=='b99e3482d3ade3564d9ec37f9164c3e8f13fec66a042b5c806b5e66d4d494477')
check('all authoritative inputs unchanged',all(digest(R/p)==h for p,h in plan['authoritativeHashes'].items()))
check('all timed source hashes',all(digest(R/'scripts/atlas/validation-packing'/p)==h for p,h in results['codeHashes'].items()))
check('preserved initial orchestration source',digest(R/'scripts/atlas/validation-packing/runner-initial.py')==results['recovery']['previousRunnerSha256'] and digest(Path(results['recovery']['previousRunner']))==results['recovery']['previousRunnerSha256'])
check('each raw timing source known',all(x['runnerSha256'] in [results['recovery']['previousRunnerSha256'],results['codeHashes']['run.py']] for x in results['rawFiles']))
check('only complete original measurements recovered',results['recovery']['preservedCompleteRepetitions']==12)
check('accepted all17 store hashes unchanged',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'/p)==h for p,h in baseline['acceptedStoreHashes'].items()))
check('baseline310 artifacts seven histories',baseline['sources']=={'artifacts':310,'bytes':42473107} and len(baseline['history'])==7)
check('all four classifications',set(x['classification'] for x in d['records'])=={'DECIDE NOW','PROVISIONAL DIRECTION','DEFER PENDING EVIDENCE','REJECT'})
seq=results['sequences'];check('15 sequences three independent repeats',len(seq)==15 and all(len(x['observations'])==3 for x in seq))
check('1488 four-way proposals 4464 comparisons',results['proposals']==1488 and results['oracleComparisons']==4464 and results['disagreements']==0)
check('all45 raw observations pinned',len(results['rawFiles'])==45 and all(digest(Path(x['path']))==x['sha256'] for x in results['rawFiles']))
check('all stores isolated',all(Path(x['path']).resolve().is_relative_to(Path(plan['stateRoot']).resolve()) for x in results['rawFiles']))
raws=[json.loads(Path(x['path']).read_text(encoding='utf-8')) for x in results['rawFiles']];rows=[v for x in raws for v in x['trace']]
check('every verdict agrees',len(rows)==1488 and all(all(c['accepted'] and not c.get('evidenceError') for c in v['candidates'].values()) for v in rows))
check('all current hash and completeness floors retained',all(v['candidates'][m]['validation']['componentIntegrity']>=v['components'] and v['candidates'][m]['validation']['membershipChecks']>=v['components'] for v in rows for m in plan['candidates']))
check('initial evidence included',all(x['trace'][0]['candidates'][m]['maintenance']['receiptsCreated']==x['trace'][0]['components'] for x in raws for m in ['individual','packed','shared']))
check('all accepted anchors retained',all(v['candidates'][m]['anchor'] for v in rows for m in ['individual','packed','shared']))
check('flat and shared directories costed',all(v['candidates']['packed']['maintenance']['directoryEntriesWritten']==v['components'] and 0<v['candidates']['shared']['maintenance']['directoryEntriesWritten']<=v['components'] for v in rows))
check('population bookkeeping disclosed',all(v['candidates'][m]['maintenance']['reverseBookkeepingEntries']==v['components'] for v in rows for m in ['packed','shared']))
check('targeted rule exact family invalidation',all(v['candidates'][m]['validation']['localChecks']==65 and v['candidates'][m]['validation']['localReused']==127 for x in raws if x['id']=='local-rule' for v in x['trace'] if v['step'] and v['step']%8==0 for m in ['individual','packed','shared']))
check('cross rules preserve local eligibility',all(v['candidates'][m]['validation']['crossChecks']==64 and v['candidates'][m]['validation']['localChecks']==2 for x in raws if x['id']=='cross-rule' for v in x['trace'] if v['step'] and v['step']%8==0 for m in ['individual','packed','shared']))
check('context fallback explicit',all(any(v['candidates'][m]['validation']['fallbacks'] for v in x['trace']) for x in raws if x['id']=='context' for m in ['individual','packed','shared']))
check('total equals validation plus maintenance',all(abs(c['totalMs']-c['validationMs']-c['maintenanceMs'])<.00001 for v in rows for c in v['candidates'].values()))
check('cumulative cost adds',all(abs(sum(v['candidates'][m]['totalMs'] for v in x['trace'])-x['summary'][m]['totalMs'])<.0001 for x in raws for m in plan['candidates']))
check('independent candidate stores',all(len(set(x['stores'].values()))==4 for x in raws))
check('analysis footprint excludes scientific components',all(f['evidenceBytes']==sum(v['bytes'] for k,v in f['groups'].items() if k in results['footprintCorrection']['correctEvidenceSchemas']) for x in seq for o in x['observations'] for f in o['footprints'].values()))
check('pre-analysis summary preserved',digest(Path(results['footprintCorrection']['originalSummary']))==results['footprintCorrection']['originalSha256'])
check('structural counts reproducible',all(all(o['summary'][m][k]==x['observations'][0]['summary'][m][k] for o in x['observations'] for m in plan['candidates'] for k in ['counter','validation','maintenance']) for x in seq))
boundary=results['boundary'];check('36 boundary comparisons agree',len(boundary)==36 and all(x['full']==x['candidate']==x['expected'] for x in boundary))
check('invalid and interrupted proposals preserve root',all(x['oldRootPreserved'] for x in boundary))
check('all three interruption retries',sum(x['interruptionRetry'] for x in boundary)==3)
check('corrupt immutable evidence issuance blocked',all(x['evidenceError'] for x in boundary if x['kind']=='pack-corrupt'))
check('fresh12 historical pins direct',len(results['fresh'])==12 and all(x['resolution']['membershipReads']==33 and x['resolution']['ancestry']==0 for x in results['fresh']))
check('memory qualified',len(results['memory'])==4 and all(x['pythonPeakAllocationBytes']>0 and x['rssBytes'] is None for x in results['memory']))
check('stopping rule applied',d['receiptOptimisationClosed']==results['receiptOptimisationClosed'] and bool(results['materialWins'])!=results['receiptOptimisationClosed'])
check('single unstarted next task',d['nextTaskStatus']=='NOT BEGUN' and bool(next_task))
for name,args in [
 ('packing-reproduction',[sys.executable,'scripts/atlas/validation-packing/run.py','--check']),
 ('packing',[sys.executable,'scripts/atlas/validation-packing/test_model.py']),
 ('maintenance-reproduction',[sys.executable,'scripts/atlas/validation-maintenance/run.py','--check']),
 ('maintenance',[sys.executable,'scripts/atlas/validation-maintenance/test_model.py']),
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
check('current generation preserved with310 hashes',state['generation']==b['current'] and state['verification']==b['sources'])
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
allowed={REPORT,OUT,*['docs/research/atlas-validation-packing-'+n for n in ['results.json','baseline.json','decisions.json']],'docs/research/atlas-validation-packing.svg'}|{'scripts/atlas/validation-packing/'+n for n in ['plan.json','README.md','model.py','run.py','worker.py','test_model.py','validate.py','plot.py','report.py','runner-initial.py']}
check('experiment-only exact paths',all(p in NAV|allowed for p in changed))
check('small artifacts no payloads',all((R/p).stat().st_size<(2000000 if p.endswith('packing-results.json') else 150000) and not p.endswith(('.tif','.png','.db','.npz','.pyc')) for p in changed if p not in NAV))
text=(R/REPORT).read_text(encoding='utf-8');check('all37 report sections',list(map(int,re.findall(r'^## (\d+)\.',text,re.M)))==list(range(1,38)))
check('all conclusions classified',all(x['id'] in text and x['classification'] in text for x in d['records']))
for p in NAV:
 s=(R/p).read_text(encoding='utf-8');check('canonical result and next '+p,'C - PROOF SUCCESS' in s and next_task in s)
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
check('references resolve',not missing);run('diff',['git','diff','--check'])
final=P.admission.assess();check('retained sources unchanged after regression',final['sources']==prior['sources']);check('accepted store unchanged after regression',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'/p)==h for p,h in baseline['acceptedStoreHashes'].items()));check('all non-navigation bytes unchanged after regression',intact());check('protected hashes unchanged after regression',protected_ok())
receipt=dict(schema='atlas-validation-packing-validation/v1',startingCheckpoint=BASE,checks=checks,errors=errors,commands=commands,testCount=sum(c['tests'] or 0 for c in commands),changedPaths=changed,preservedTrackedFiles=len(preserve),sourceAdmission=prior['sources'],retainedVerification=state['verification'],publishedGeneration=state['generation'],canonicalThreads=42,protectedHashes=113,missingReferences=missing,references=refs,decision=d['decision'],nextTask=next_task,acceptedPilotUnchanged=not errors,experimentHashes={p:digest(R/p) for p in allowed if p!=OUT})
(R/OUT).write_text(assess.encode(receipt),encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),tests=receipt['testCount'],errors=errors,missing=missing)),flush=True)
if errors:raise SystemExit(1)
