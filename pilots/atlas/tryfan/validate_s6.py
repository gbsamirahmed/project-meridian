"""S6 stage-aware integrity and full regression, never modify pilot functionality."""
from pathlib import Path
import json,hashlib,subprocess,sys,re,os
sys.stdout.reconfigure(encoding='utf-8');R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'));import check_plan as P
BASE='fc441c5619e1c8448c057e0796ee334884e4ed02';NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
checks=[];errors=[];commands=[]
def check(name,ok):
 checks.append(dict(check=name,passed=bool(ok)))
 if not ok:errors.append(name)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,args):
 p=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PROJ_NETWORK':'OFF','PYTHONDONTWRITEBYTECODE':'1'});log=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1/s6-validation';log.mkdir(exist_ok=True);(log/(name+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n');check(name,p.returncode==0);commands.append(dict(name=name,args=args,exitCode=p.returncode));print(name,p.returncode,flush=True)
 if p.returncode:print(p.stdout[-3000:]+p.stderr[-3000:],flush=True)
b=read('docs/research/tryfan-pilot-s6-baseline.json');r=read('docs/research/tryfan-pilot-s6-results.json');plan=read('docs/research/tryfan-regional-pilot-plan.json');a=read('docs/research/tryfan-pilot-s6-acceptance.json')
check('baseline expected clean main 0/0',b['commit']==BASE and b['branch']=='main' and b['clean'] and b['divergence'].split()==['0','0']);check('frozen original A-P',b['exitCriteria']==plan['acceptance']);check('all16 exercised',len(r['checks'])==16 and {x['id'] for x in r['checks']}=={x['id'] for x in plan['acceptance']} and all(c['status']=='PASS' for c in r['checks']))
check('nine gates independent exact wording mapping',len(a['gates'])==9 and all(g['status']=='PASS' and g['exitCriterion'] and g['cases'] and g['limitation'] for g in a['gates']))
admission_report=(R/'docs/research/atlas-regional-pilot-acceptance.md').read_text(encoding='utf-8')
original_gates=re.findall(r'^Exit test: (.+)$',admission_report,re.M)
check('exact nine prospective exit criteria',len(original_gates)==9 and [g['exitCriterion'] for g in a['gates']]==original_gates)
check('matrix exact original conditions',all(c['passCondition']==next(v['passCondition'] for v in plan['acceptance'] if v['id']==c['id']) for c in a['criteria']))
check('expected frozen starting ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
for p,h in b['systemSha256'].items():check('frozen system '+p,digest(R/p)==h)
for s,v in b['reports'].items():check('historical '+s,digest(R/v['report'])==v['sha256'])
tracked=git('ls-tree','-r','--name-only',BASE).splitlines();preserve=[p for p in tracked if p not in NAV];hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(preserve)+'\n',text=True).splitlines();tree={line.split('\t')[1]:line.split()[2] for line in git('ls-tree','-r',BASE).splitlines()};bad=[p for p,h in zip(preserve,hashes) if h!=tree[p]];check('all pre-existing files except navigation preserved',not bad and len(preserve)==len(hashes))
prior=P.admission.assess();check('1575 retained admission sources',prior['sources']['uniqueFiles']==1575);check('planning structure',P.check_structure(plan));protected=read('docs/atlas/information-display-plan.json')['productionHashes'];check('113 protected production hashes',len(protected)==113 and all(digest(R/p)==h for p,h in protected.items()))
old=subprocess.check_output(['git','show',BASE+':docs/research/atlas-research-state.md'],cwd=R).decode('utf-8');current=(R/'docs/research/atlas-research-state.md').read_text(encoding='utf-8');check('42 statuses unchanged',len(P.admission.canonical_rows(current))==42 and P.admission.canonical_rows(current)==P.admission.canonical_rows(old));check('development log append-only',(R/'docs/development-log.md').read_text(encoding='utf-8').startswith(subprocess.check_output(['git','show',BASE+':docs/development-log.md'],cwd=R).decode('utf-8')+'\n'))
for name,args in [
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
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'));check('current remains frozen with310 verified assets',state['generation']==b['current'] and state['verification']==b['sources']);check('all historical generations retained',all(digest(P.DATA/'experiments/atlas/tryfan-regional-pilot-v1/generations'/f"{h['generation']}.json")==h['sha256'] for h in b['history']))
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()));allowed={'pilots/atlas/tryfan/'+s for s in ['measure.mjs','rebuild-s6.mjs','validate_s6.py','README-S6.md','tests/read-metrics-s6.mjs','tests/warm-matrix-s6.mjs','tests/acceptance.test.mjs','tests/visual-s6.mjs','tests/browser-s6.mjs']};check('acceptance only allowed paths',all(p in NAV|allowed or p.startswith('docs/research/tryfan-pilot-s6') for p in changed));check('lightweight new artifacts',all((R/p).stat().st_size<200000 for p in changed if p not in NAV));check('no source products',(not any(p.endswith(('.tif','.png','.db','.npz','.pyc')) for p in changed)))
report=(R/'docs/research/tryfan-pilot-s6.md').read_text(encoding='utf-8');check('35 report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,36)));check('nine gate report classifications',all(g['name'] in report and g['status'] in report for g in a['gates']));next_task=a['nextTask']
for p in NAV:check('canonical closure next '+p,'C - PILOT EXIT ACCEPTED' in (R/p).read_text(encoding='utf-8') and next_task in (R/p).read_text(encoding='utf-8'))
# Resolve local links/anchors in the changed reports/navigation (historical log is appended only).
def slugs(text):
 out=set();seen={}
 for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1;out.add(key if not n else key+'-'+str(n))
 return out
from urllib.parse import unquote
missing=[];references=0
for p in changed:
 if not p.endswith('.md'):continue
 text=(R/p).read_text(encoding='utf-8')
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - Tryfan pilot S6'):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if link.startswith(('http:','https:','mailto:','meridian-data:')):continue
  path,_,anchor=unquote(link.strip('<>')).partition('#');target=(R/p).parent/path if path else R/p;references+=1
  if (not target.exists() and target.resolve()!=(R/'docs/research/tryfan-pilot-s6-validation.json').resolve()) or anchor and target.suffix=='.md' and anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([p,link])
check('references anchors',not missing);run('diff',['git','diff','--check'])
final_admission=P.admission.assess()
check('all retained source hashes unchanged after regressions',final_admission['sources']==prior['sources'])
final_hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(preserve)+'\n',text=True).splitlines()
check('all pre-existing tracked content still intact after regressions',len(final_hashes)==len(preserve) and all(h==tree[p] for p,h in zip(preserve,final_hashes)))
check('all113 protected hashes still intact after regressions',all(digest(R/p)==h for p,h in protected.items()))
# Preserve full initial result receipt and hash exact frozen code/acceptance artifacts.
receipt=dict(schema='atlas-tryfan-s6-validation/v1',checks=checks,errors=errors,commands=commands,changedPaths=changed,retainedVerification=state['verification'],protectedHashes=113,canonicalThreads=42,unchangedTrackedFiles=len(preserve),historicalMismatches=bad,missingReferences=missing,references=references,publishedGeneration=b['current'],decision=a['decision'],gates=a['gates'],nextTask=next_task,codeSha256={p:digest(R/p) for p in changed if p.startswith('pilots/')},artifactSha256={p:digest(R/p) for p in changed if p.startswith('docs/research/') and not p.endswith('-validation.json')},sourceAdmission=prior['sources'])
(R/'docs/research/tryfan-pilot-s6-validation.json').write_text(P.encode(receipt),encoding='utf-8',newline='\n');print(json.dumps(dict(checks=len(checks),errors=errors,missing=missing)),flush=True)
if errors:raise SystemExit(1)
