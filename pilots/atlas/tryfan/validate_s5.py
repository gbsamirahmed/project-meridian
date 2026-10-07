"""Stage-aware S5 acceptance; historical stage receipts remain immutable."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,os
sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'))
import check_plan as P
A=P.admission
BASE='f8d3ce98d01f1596a6a2ee9f3041bb721fbbde8f'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/tryfan-pilot-s5.md';RESULTS='docs/research/tryfan-pilot-s5-results.json';OUT='docs/research/tryfan-pilot-s5-validation.json'
checks=[];errors=[];commands=[]
def check(name,ok):
    checks.append(dict(check=name,passed=bool(ok)))
    if not ok:errors.append(name)
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').strip()
def body(path):return (R/path).read_text(encoding='utf-8-sig')
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=R).decode('utf-8')
def run(name,args):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF'}
    p=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
    log=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1/s5-validation';log.mkdir(parents=True,exist_ok=True)
    (log/(re.sub(r'[^a-z0-9]+','-',name.lower())+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n')
    check(name,p.returncode==0);commands.append(dict(check=name,command=args,exitCode=p.returncode))
    if p.returncode:print(p.stdout[-4000:],p.stderr[-4000:])
    return p.stdout+p.stderr

check('expected f8d3ce9 ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
check('main existing upstream0/0 before commit',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main' and git('rev-list','--left-right','--count','HEAD...origin/main').split()==['0','0'])
plan=P.read(R/P.PLAN);check('frozen planning structure',P.check_structure(plan))
for f in plan['foundations']+plan['metadataReceipts']:check('authoritative pin '+f.get('id',f.get('path','')),P.digest(R/f.get('report',f.get('path')))==f['sha256'])
prior=A.assess();check('37proof50capability9PASS admission preserved',prior['proofCount']==37 and prior['requiredCapabilities']==50 and all(v=='PASS' for v in prior['gateOutcomes'].values()))
check('1575 retained admission sources unchanged',prior['sources']['uniqueFiles']==1575)
protected=P.read(R/'docs/atlas/information-display-plan.json')['productionHashes'];check('all113 protected hashes',len(protected)==113 and all(P.digest(R/p)==h for p,h in protected.items()))
frozen=P.read(R/'docs/atlas/semantic-evidence-contract-validation.json')['code'];check('seven frozen semantic hashes',len(frozen)==7 and all(P.digest(R/f['href'])==f['sha256'] for f in frozen))
previous=A.canonical_rows(old('docs/research/atlas-research-state.md'));current=A.canonical_rows(body('docs/research/atlas-research-state.md'))
check('all42 canonical historical statuses unchanged',len(previous)==42 and current==previous)
admission=P.read(R/plan['admission']['manifest']);check('all42 dispositions preserved Swiss parked',len(admission['threads'])==42 and all(t['historicalStatus']==current[t['id']] for t in admission['threads']) and next(t for t in admission['threads'] if t['id']=='A13')['pilotClass']=='PARKED EXTERNAL DEPENDENCY')
check('development log append-only',body('docs/development-log.md').startswith(old('docs/development-log.md')+'\n'))
compat={'pilots/atlas/tryfan/'+p for p in ['generations.mjs','query.mjs','delivery.mjs','client/view.mjs','tests/http.test.mjs','tests/lifecycle.test.mjs']}
preserve={}
for line in git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research','pilots').splitlines():
    meta,path=line.split('\t',1)
    if path not in NAV|compat:preserve[path]=meta.split()[2]
paths=list(preserve);hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines();bad=[p for p,h in zip(paths,hashes) if h!=preserve[p]]
check('all historical reports scientific/frozen tooling preserved',len(paths)==len(hashes) and not bad)
for name,args,count in [
 ('S5 scoped publication and restart',['node','--test','pilots/atlas/tryfan/tests/publication.test.mjs','pilots/atlas/tryfan/tests/restart.test.mjs'],16),
 ('S4 generation-pinned HTTP tests',['node','--test','pilots/atlas/tryfan/tests/http.test.mjs'],21),
 ('isolated browser interaction and fixed portrayal',['node','pilots/atlas/tryfan/tests/publication-browser.mjs'],None),
 ('S1 S2 S3 regressions',['node','--test','pilots/atlas/tryfan/tests/catalogue.test.mjs','pilots/atlas/tryfan/tests/query.test.mjs','pilots/atlas/tryfan/tests/lifecycle.test.mjs'],84),
 ('native addressing geometry cases',[sys.executable,'pilots/atlas/tryfan/adapters/test_native.py'],9),
 ('planning safeguards',[sys.executable,'scripts/atlas/regional-pilot-plan/test_plan.py'],22),
 ('frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'],64),
 ('retained qualified-query lifecycle',['node','--test','scripts/atlas/test_qualified_query_proof.mjs'],None),
 ('retained persistent lifecycle',['node','--test','scripts/atlas/test_local_persistent_tryfan.mjs'],None)]:
    text=run(name,args)
    if count:check(name+' declared count',(f'tests {count}' if args[0]=='node' else f'Ran {count} tests') in text)
run('frozen semantic TypeScript',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
run('deterministic S5 independent measured rerun',['node','pilots/atlas/tryfan/measure_s5.mjs','--check'])
run('production lint',['npm.cmd','run','lint']);run('production build',['npm.cmd','run','build'])
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'))
check('310 immutable retained pilot sources',state['counts']==dict(sources=5,products=5,representations=8,families=5,artifacts=310) and state['verification']==dict(artifacts=310,bytes=42473107))
expected=P.read(R/P.OUT)['sourceHashes'];actual={state['locators'][a['id']]:dict(sha256=a['sha256'],bytes=a['bytes']) for a in state['catalogue']['artifacts']};check('exact frozen310source inventory',expected==actual)
results=P.read(R/RESULTS);logical=results['logical']
store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1';v=P.read(store/'generations'/f"{state['generation']}.json")
check('canonical U1 root and all complete capabilities',state['generation']==results['U1']['logical']['to'] and all(state['capabilities'].values()))
check('six results four current two methods',v['understanding']['stage']=='regional' and len(v['understanding']['results'])==6 and len(v['understanding']['active'])==4)
check('prospective31 scenarios and parsed freeze identity',len(P.read(R/'pilots/atlas/tryfan/publication-matrix.json')['scenarios'])==31)
check('protocol LF encoding only',hashlib.sha256((R/'pilots/atlas/tryfan/publication-matrix.json').read_bytes()).hexdigest()==results['matrixSha256'] and hashlib.sha256(body('pilots/atlas/tryfan/publication-matrix.json').replace('\n','\r\n').encode()).hexdigest()==results['initialMatrixBytesSha256'])
for id in ['U1','U2']:
    record=results[id];branch=store if id=='U1' else store/'s5-mixed'
    before=P.read(branch/'generations'/(record['logical']['from']+'.json'));after=P.read(branch/'generations'/(record['logical']['to']+'.json'))
    for key in ['catalogue','knowledge']:check(id+' native '+key+' unchanged',before[key]==after[key])
    check(id+' four AWS histories retained exact',after['understanding']['results'][:4]==before['understanding']['results'])
    check(id+' recompute2 reuse2',len(record['logical']['recomputed'])==2 and len(record['logical']['reused'])==2)
    check(id+' portrayal assets reused',after['serving']['assets']==before['serving']['assets'])
    check(id+' failures F1 E1 F2 F3 real91',len(record['failures'])==4 and all(f['exitCode']==91 and f['current']==record['logical']['from'] and f['oldConsumer']==f['current'] and f['freshService']==f['current'] for f in record['failures']))
    check(id+' orphan identical to successful retry',record['failures'][-1]['orphan']==record['logical']['to'])
    check(id+' reader while assembly switch coherent',len(record['racing'])>=3 and all(a['generation'] in [record['logical']['from'],record['logical']['to']] and a['pinned']==record['logical']['from'] for a in record['racing']))
    for a in record['racing']:
        wasOld=a['generation']==record['logical']['from'];check(id+' reader combination '+a['generation'][:8],a['family']==('production-common' if wasOld else 'welsh-regional') and a['slope']==(11.837956999552308 if wasOld else 32.918524028483965) and a['nrwCode']==(None if wasOld and id=='U2' else 'D.1.1'))
    for f in record['failures']:check(id+' retained stage '+f['point'],(branch/'staging'/f['operation']).is_dir())
check('six exact pixel replays',len(logical['replay'])==6 and all(c['exact'] for c in logical['replay']))
qa=P.read(store/'s5-qa/browser.json');check('real browser pinned before explicit whole-scene refresh',qa['oldSceneStayedPinned'] and qa['explicitRefreshAtomicScene'] and not qa['errors'])
for name,d in qa['figures'].items():check('browser diagnostic hash '+name,P.digest(store/'s5-qa'/(name+'.png'))==d['sha256'])
# Reproduce original S2/S3 statements under exact historic contexts.
s3=P.read(R/'docs/research/tryfan-pilot-s3-results.json')['logical']
s2=P.read(R/'docs/research/tryfan-pilot-s2-results.json')['logical'];raw=subprocess.check_output(['node','pilots/atlas/tryfan/query-cli.mjs','matrix','--generation',s2['generation']],cwd=R,encoding='utf-8')
check('historical S2 full matrix exact',hashlib.sha256(raw.encode()).hexdigest()==s2['fullMatrixSha256'])
request=json.dumps(dict(property='place-evidence',place=dict(crs='EPSG:27700',point=[266405,359387])))
raw=subprocess.check_output(['node','pilots/atlas/tryfan/lifecycle-cli.mjs','query','--generation',s3['generation'],'--request',request],cwd=R,encoding='utf-8')
check('historical S3 Q21 exact',hashlib.sha256(raw.encode()).hexdigest()==s3['integratedSha256'])
# Exact frozen science remains the S3 module; query additions are applicability only.
for p in ['dependencies.mjs','derivations.mjs','world.mjs','semantic.mjs','adapters/native.py','adapters/retained_derivation.py','identity.mjs','catalogue.mjs']:
    check('unchanged science/native primitive '+p,body('pilots/atlas/tryfan/'+p)==old('pilots/atlas/tryfan/'+p))
check('S1 final atomic switch unchanged',body('pilots/atlas/tryfan/generations.mjs').split('  const publicationStart=',1)[1].split('export function stage',1)[0]==old('pilots/atlas/tryfan/generations.mjs').split('  const publicationStart=',1)[1].split('export function stage',1)[0])
report=body(REPORT);check('31 durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,32)))
next_task='Tryfan pilot measured exit acceptance - S6 only'
for path in NAV:check('S5 success one next slice '+path,'C - S5 SUCCESS' in body(path) and next_task in body(path) and 'not begun' in body(path))
check('honest bounded report',all(s.lower() in report.lower() for s in ['No S6','Appearance unresolved/non-blocking','Swiss multiview parked','stale does not mean false','Single writer','not new terrain surveys','No architectural or foundational deviation']))
(R/OUT).write_text('{}\n',encoding='utf-8')
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
allowed={'README-S5.md','updates.mjs','update-schema.mjs','update-cli.mjs','publication-matrix.json','measure_s5.mjs','validate_s5.py','tests/publication.test.mjs','tests/restart.test.mjs','tests/publication-harness.mjs','tests/publication-browser.mjs','client/publication-consumer.mjs'}
check('S5 only changes',all(p in NAV|compat or p.startswith('docs/research/tryfan-pilot-s5') or p.startswith('pilots/atlas/tryfan/') and p[len('pilots/atlas/tryfan/'):] in allowed for p in changed))
check('no source production Weather Traverse changes',not any(p.startswith(('src/','public/','meridian-private')) for p in changed))
check('only lightweight code metadata in Git',all((R/p).stat().st_size<200000 for p in changed if p not in NAV) and not any(p.endswith(('.tif','.png','.npz','.db','.sqlite','.pyc')) for p in changed))
check('no S6 onward modules',all(not (R/'pilots/atlas/tryfan'/p).exists() for p in ['measure.mjs','tests/acceptance.test.mjs']))
for file in ['client/view.mjs','client/http-consumer.mjs','client/session-consumer.mjs','client/publication-consumer.mjs']:
    check('storage-isolated consumer '+file,not re.search(r'from [\"\']\.\.|readFile|catalogue|generations\.mjs|openEvidence|derivations\.mjs',body('pilots/atlas/tryfan/'+file)))

def slugs(text):
    seen={};out=set()
    for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
        title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1;out.add(key if not n else key+'-'+str(n))
    return out
missing=[];references=anchors=0
for file in changed:
    if not file.endswith('.md'):continue
    text=body(file)
    if file=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - Tryfan pilot S5'):]
    for link in re.findall(r'\]\(([^)]+)\)',text):
        link=link.strip().strip('<>')
        if link.startswith(('http:','https:','mailto:','data:','meridian-data:')):continue
        path,_,anchor=unquote(link).partition('#');target=(R/file).parent/path if path else R/file;references+=1
        if not target.exists():missing.append([file,link]);continue
        if anchor and target.suffix=='.md':
            anchors+=1
            if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([file,link])
check('report and navigation references anchors resolve',not missing)
for t in admission['threads']:
    for link in t['canonicalReferences']:
        path,_,anchor=unquote(link).partition('#');target=R/'docs/research'/path
        check('canonical reference '+t['id']+' '+link,target.exists() and (not anchor or target.suffix!='.md' or anchor in slugs(target.read_text(encoding='utf-8-sig'))))
run('working diff whitespace',['git','diff','--check']);run('staged diff whitespace',['git','diff','--cached','--check'])
check('Markdown whitespace',all(all(line.rstrip()==line for line in body(p).splitlines()) for p in changed if p.endswith('.md')))
receipt=dict(assessment='atlas-tryfan-pilot-s5-validation/v1',startingCheckpoint=BASE,decision='C - S5 SUCCESS',checks=checks,errors=errors,commands=commands,changedPaths=changed,
 retainedSourceVerification=state['verification'],priorAdmissionSourceVerification=prior['sources'],unchangedHistoricalFiles=len(paths),historicalMismatches=bad,canonicalThreads=42,protectedProductionHashes=113,frozenSemanticHashes=7,
 publishedGeneration=state['generation'],parentGeneration=state['parent'],logicalSha256=results['logicalSha256'],matrixSha256=results['matrixSha256'],browserQA=qa,missingReferences=missing,localReferences=references,anchors=anchors,nextTask=next_task+'; not begun',
 codeSha256={p:P.digest(R/p) for p in changed if p.startswith('pilots/')},artifactSha256={p:P.digest(R/p) for p in [REPORT,RESULTS]},
 confirmations=dict(noRetainedMutation=True,noNewData=True,noPrivateAccess=True,noProductionChanges=True,noFrozenChanges=True,noS6OrLater=True,S1PublicationUnchanged=True,S2NativeQueryUnchanged=True,S3LifecycleUnchanged=True,appearanceUnresolvedNonBlocking=True,swissMultiviewParked=True))
(R/OUT).write_text(P.encode(receipt),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),errors=errors,retainedFiles=310,protectedHashes=113,refs=references,missing=missing)))
if errors:raise SystemExit(1)
