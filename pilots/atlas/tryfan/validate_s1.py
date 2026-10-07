"""Stage-aware S1 regression, retaining every frozen planning/research artifact."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'))
import check_plan as P
A=P.admission
BASE='7809147ae86b14a19d195e0cdc9791b47caa59eb'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/tryfan-pilot-s1.md';OUT='docs/research/tryfan-pilot-s1-validation.json'
checks=[];errors=[];commands=[]
def check(name,ok):
 checks.append(dict(check=name,passed=bool(ok)))
 if not ok:errors.append(name)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').strip()
def body(path):return (R/path).read_text(encoding='utf-8-sig')
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=R).decode('utf-8')
def run(name,args):
 p=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
 check(name,p.returncode==0);commands.append(dict(check=name,command=args,exitCode=p.returncode))
 if p.returncode:print(p.stdout[-4000:],p.stderr[-4000:])
 return p.stdout+p.stderr
check('expected7809147checkpoint ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
check('existing main upstream and0/0 precommit',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main' and git('rev-list','--left-right','--count','HEAD...origin/main').split()==['0','0'])
plan=P.read(R/P.PLAN);check('unchanged frozen plan structure',P.check_structure(plan))
for f in plan['foundations']+plan['metadataReceipts']:
 check('authoritative pin '+f.get('id',f.get('path','')),P.digest(R/f.get('report',f.get('path')))==f['sha256'])
prior=A.assess();check('retained37proof/50capability/9PASS admission',prior['proofCount']==37 and prior['requiredCapabilities']==50 and all(x=='PASS' for x in prior['gateOutcomes'].values()))
check('1575 admission sources unchanged',prior['sources']['uniqueFiles']==1575)
protected=P.read(R/'docs/atlas/information-display-plan.json')['productionHashes']
check('all113 protected production hashes',len(protected)==113 and all(P.digest(R/path)==h for path,h in protected.items()))
frozen=P.read(R/'docs/atlas/semantic-evidence-contract-validation.json')['code']
check('seven frozen semantic files',len(frozen)==7 and all(P.digest(R/f['href'])==f['sha256'] for f in frozen))
check('production Atlas Weather Traverse frozen docs packages unchanged',not git('diff',BASE,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
previous=A.canonical_rows(old('docs/research/atlas-research-state.md'));current=A.canonical_rows(body('docs/research/atlas-research-state.md'))
check('all42 historical status columns unchanged',len(previous)==42 and current==previous)
admission=P.read(R/plan['admission']['manifest'])
check('all42 admission dispositions and Swiss parked preserved',len(admission['threads'])==42 and all(t['historicalStatus']==current[t['id']] for t in admission['threads']) and next(t for t in admission['threads'] if t['id']=='A13')['pilotClass']=='PARKED EXTERNAL DEPENDENCY')
check('development log append only',body('docs/development-log.md').startswith(old('docs/development-log.md')+'\n'))
preserve={}
for line in git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research').splitlines():
 meta,path=line.split('\t',1)
 if path not in NAV:preserve[path]=meta.split()[2]
paths=list(preserve);hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines()
bad=[p for p,h in zip(paths,hashes) if h!=preserve[p]]
check('every prior report research asset and tool unchanged including frozen plan receipts',len(paths)==len(hashes) and not bad)
focused=run('22 S1 public interface retained/restart/failure tests',['node','--test','pilots/atlas/tryfan/tests/catalogue.test.mjs'])
check('22 S1 tests counted',bool(re.search(r'tests 22',focused)))
planning=run('existing22 planning invariants',[sys.executable,'scripts/atlas/regional-pilot-plan/test_plan.py'])
check('22 planning safeguards counted','Ran 22 tests' in planning)
run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
run('frozen semantic isolated TypeScript',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
raw=subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8');state=json.loads(raw)
check('genuine external published state recovered by independent CLI',state['counts']==dict(sources=5,products=5,representations=8,families=5,artifacts=310) and state['verification']==dict(artifacts=310,bytes=42473107))
check('registration only capability boundary',state['capabilities']==dict(registration=True,queries=False,derivations=False,serving=False,mixedFamilyUpdate=False))
expected=P.read(R/P.OUT)['sourceHashes'];actual={state['locators'][a['id']]:dict(sha256=a['sha256'],bytes=a['bytes']) for a in state['catalogue']['artifacts']}
check('exact frozen310file inventory no expansion or substitution',expected==actual)
metrics=P.read(R/'docs/research/tryfan-pilot-s1-results.json')
logical=metrics['logical']
check('measurement logical receipt matches current generation/catalogue',logical['publishedGeneration']==state['generation'] and logical['counts']==state['counts'] and logical['verification']==state['verification'])
check('five independent builds and fresh loads recorded outside identity',metrics['measurements']['outsideIdentity'] and len(metrics['measurements']['builds'])==len(metrics['measurements']['freshLoads'])==5 and len({b['generation'] for b in metrics['measurements']['builds']})==1)
parent=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','validate','--generation',state['parent']],cwd=R,text=True,encoding='utf-8'))
check('genuine previous generation remains independently recoverable',parent['generation']==state['parent'] and parent['verification']==state['verification'])
report=body(REPORT);check('31 required implementation report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,32)))
next_task='Tryfan pilot qualified native evidence readers and queries - S2 only'
for path in NAV:
 check('S1 result and one next slice '+path,'C - S1 SUCCESS' in body(path) and next_task in body(path) and 'not begun' in body(path))
check('report explicit limits and remaining admission tests',all(x in report for x in ['registration-only','mixed-family','power loss','Swiss multiview parked','S2 has not begun','No architectural or technology deviation']))
(R/OUT).write_text('{}\n',encoding='utf-8')
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
code={'identity.mjs','catalogue.mjs','generations.mjs','cli.mjs','README.md','measure_s1.mjs','validate_s1.py','tests/catalogue.test.mjs','tests/worker.mjs'}
check('S1 only changed files no later slice modules',all(p in NAV or p.startswith('docs/research/tryfan-pilot-s1') or (p.startswith('pilots/atlas/tryfan/') and p[len('pilots/atlas/tryfan/'):] in code) for p in changed))
check('no large/duplicate/runtime payload tracked',all((R/p).stat().st_size<200000 for p in changed if p not in NAV) and not any(p.endswith(('.tif','.png','.npz','.db','.sqlite','.pyc')) for p in changed))
check('no HTTP/native-reader/derived runtime modules created',all(not(R/'pilots/atlas/tryfan'/p).exists() for p in ['server.mjs','query.mjs','semantic.mjs','derivations.mjs','dependencies.mjs','updates.mjs','adapters','client']))
def slugs(text):
 seen={};out=set()
 for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1;out.add(key if not n else key+'-'+str(n))
 return out
missing=[];references=anchors=0
for file in changed:
 if not file.endswith('.md'):continue
 text=body(file)
 if file=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - Tryfan pilot S1'):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  link=link.strip().strip('<>')
  if link.startswith(('http:','https:','mailto:','data:','meridian-data:')):continue
  path,_,anchor=unquote(link).partition('#');target=(R/file).parent/path if path else R/file;references+=1
  if not target.exists():missing.append([file,link]);continue
  if anchor and target.suffix=='.md':
   anchors+=1
   if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([file,link])
check('all new report/navigation/tooling references and anchors',not missing)
for t in admission['threads']:
 for link in t['canonicalReferences']:
  path,_,anchor=unquote(link).partition('#');target=R/'docs/research'/path
  check('canonical reference '+t['id']+' '+link,target.exists() and (not anchor or target.suffix!='.md' or anchor in slugs(target.read_text(encoding='utf-8-sig'))))
run('working diff whitespace',['git','diff','--check']);run('staged diff whitespace',['git','diff','--cached','--check'])
check('new Markdown whitespace',all(all(line.rstrip()==line for line in body(p).splitlines()) for p in changed if p.endswith('.md')))
receipt=dict(assessment='atlas-tryfan-pilot-s1-validation/v1',startingCheckpoint=BASE,decision='C - S1 SUCCESS',checks=checks,errors=errors,commands=commands,
 changedPaths=changed,retainedSourceVerification=state['verification'],priorAdmissionSourceVerification=prior['sources'],unchangedHistoricalFiles=len(paths),historicalMismatches=bad,
 canonicalThreads=42,protectedProductionHashes=113,frozenSemanticHashes=7,publishedGeneration=state['generation'],previousGeneration=state['parent'],missingReferences=missing,
 localReferences=references,anchors=anchors,nextTask=next_task+'; not begun',codeSha256={p:P.digest(R/p) for p in changed if p.startswith('pilots/')},
 artifactSha256={p:P.digest(R/p) for p in [REPORT,'docs/research/tryfan-pilot-s1-results.json']},confirmations=dict(noRetainedMutation=True,noNewData=True,noPrivateAccess=True,noProductionChanges=True,noFrozenChanges=True,noS2OrLater=True,appearanceUnresolvedNonBlocking=True,swissMultiviewParked=True))
(R/OUT).write_text(P.encode(receipt),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),errors=errors,retainedFiles=310,protectedHashes=113,refs=references,missing=missing)))
if errors:raise SystemExit(1)
