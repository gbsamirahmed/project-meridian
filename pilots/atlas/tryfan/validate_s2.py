"""Stage-aware S2 acceptance. Prior planning/S1 no-later-slice gates stay historical."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,os
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'))
import check_plan as P
A=P.admission
BASE='b5ac71508776c289ec93a0a894ee6641d62fb879'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/tryfan-pilot-s2.md';RESULTS='docs/research/tryfan-pilot-s2-results.json';OUT='docs/research/tryfan-pilot-s2-validation.json'
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
    check(name,p.returncode==0);commands.append(dict(check=name,command=args,exitCode=p.returncode))
    if p.returncode:print(p.stdout[-4000:],p.stderr[-4000:])
    return p.stdout+p.stderr
check('expected b5ac715 ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
check('main existing upstream0/0 precommit',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main' and git('rev-list','--left-right','--count','HEAD...origin/main').split()==['0','0'])
plan=P.read(R/P.PLAN);check('frozen planning structure',P.check_structure(plan))
for f in plan['foundations']+plan['metadataReceipts']:check('authoritative pin '+f.get('id',f.get('path','')),P.digest(R/f.get('report',f.get('path')))==f['sha256'])
prior=A.assess();check('37proof50capability9PASS admission preserved',prior['proofCount']==37 and prior['requiredCapabilities']==50 and all(v=='PASS' for v in prior['gateOutcomes'].values()))
check('1575 admission sources unchanged',prior['sources']['uniqueFiles']==1575)
protected=P.read(R/'docs/atlas/information-display-plan.json')['productionHashes']
check('all113 protected production hashes',len(protected)==113 and all(P.digest(R/p)==h for p,h in protected.items()))
frozen=P.read(R/'docs/atlas/semantic-evidence-contract-validation.json')['code']
check('seven frozen semantic files',len(frozen)==7 and all(P.digest(R/f['href'])==f['sha256'] for f in frozen))
check('production Atlas Weather Traverse frozen docs packages unchanged',not git('diff',BASE,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
previous=A.canonical_rows(old('docs/research/atlas-research-state.md'));current=A.canonical_rows(body('docs/research/atlas-research-state.md'))
check('all42 research historical status columns unchanged',len(previous)==42 and current==previous)
admission=P.read(R/plan['admission']['manifest'])
check('42 dispositions and Swiss parked preserved',len(admission['threads'])==42 and all(t['historicalStatus']==current[t['id']] for t in admission['threads']) and next(t for t in admission['threads'] if t['id']=='A13')['pilotClass']=='PARKED EXTERNAL DEPENDENCY')
check('development log append-only',body('docs/development-log.md').startswith(old('docs/development-log.md')+'\n'))
preserve={}
for line in git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research','pilots').splitlines():
    meta,path=line.split('\t',1)
    if path not in NAV:preserve[path]=meta.split()[2]
paths=list(preserve);hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines()
bad=[p for p,h in zip(paths,hashes) if h!=preserve[p]]
check('all historical reports assets contracts tooling S1 code unchanged',len(paths)==len(hashes) and not bad)
for name,args,needle in [
 ('33 S2 native query tests',['node','--test','pilots/atlas/tryfan/tests/query.test.mjs'],'tests 33'),
 ('9 labelled native geometry/addressing tests',[sys.executable,'pilots/atlas/tryfan/adapters/test_native.py'],'Ran 9 tests'),
 ('22 S1 tests',['node','--test','pilots/atlas/tryfan/tests/catalogue.test.mjs'],'tests 22'),
 ('22 planning safeguards',[sys.executable,'scripts/atlas/regional-pilot-plan/test_plan.py'],'Ran 22 tests'),
 ('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'],'tests 64')]:
    text=run(name,args);check(name+' count',needle in text)
run('frozen semantic TypeScript',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'))
check('S1 coherent persisted state all310 hashes',state['counts']==dict(sources=5,products=5,representations=8,families=5,artifacts=310) and state['verification']==dict(artifacts=310,bytes=42473107))
check('S1 publication capability and root unchanged',state['generation']==P.read(R/'docs/research/tryfan-pilot-s1-results.json')['logical']['publishedGeneration'] and state['capabilities']==dict(registration=True,queries=False,derivations=False,serving=False,mixedFamilyUpdate=False))
expected=P.read(R/P.OUT)['sourceHashes'];actual={state['locators'][a['id']]:dict(sha256=a['sha256'],bytes=a['bytes']) for a in state['catalogue']['artifacts']}
check('exact frozen310file inventory unchanged',expected==actual)
results=P.read(R/RESULTS);logical=results['logical'];matrix=P.read(R/'pilots/atlas/tryfan/query-matrix.json')
check('15 inherited query definitions unchanged',matrix['queries']==[q for q in plan['query']['matrix'] if q['id'] in ['Q05','Q06','Q07','Q08','Q09','Q10','Q11','Q13','Q14','Q15','Q16','Q17','Q18','Q19','Q20']])
check('matrix pin and real current generation',P.digest(R/'pilots/atlas/tryfan/query-matrix.json')==logical['matrixSha256'] and logical['generation']==state['generation'])
raw=subprocess.check_output(['node','pilots/atlas/tryfan/query-cli.mjs','matrix'],cwd=R,env={**os.environ,'PROJ_NETWORK':'OFF'},encoding='utf-8')
check('independent canonical full matrix hash',hashlib.sha256(raw.encode('utf-8')).hexdigest()==logical['fullMatrixSha256'])
full=json.loads(raw);check('16 deterministic real outputs accounted',len(full['results'])==len(logical['queries'])==16 and [q['id'] for q in full['results']]==[q['id'] for q in logical['queries']])
check('five independent measured outputs same identity',len(results['measurements']['freshProcesses'])==5 and all(p['logicalSha256']==logical['fullMatrixSha256'] for p in results['measurements']['freshProcesses']) and results['measurements']['outsideIdentity'])
check('three30-run query measurements',all(v['runs']==30 for v in results['measurements']['queryMilliseconds'].values()))
check('real parent native claims unchanged not fake scientific revision',logical['historical']['generation']==state['parent'] and logical['historical']['claimSha256']==logical['historical']['currentClaimSha256'] and not logical['historical']['scientificChange'])
check('Q17 unavailable no fallback',logical['unavailableFixture']['answer']['operationalStatus']=='unavailable' and [r['family'] for r in logical['unavailableFixture']['answer']['records']]==['worldcover'])
registered={a['id'] for a in state['catalogue']['artifacts']}
for q in logical['queries']:
    check('generation and qualified source refs '+q['id'],q['answer']['generation']==state['generation'] and all(r['provenance']['generation']==state['generation'] and all(a in registered for a in r['provenance']['artifacts']) and r['provenance']['source']['kind']=='source' and r['provenance']['product']['kind']=='product' for r in q['answer']['records']))
report=body(REPORT);check('32 report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,33)))
next_task='Tryfan pilot retained derivation and lifecycle integration - S3 only'
for path in NAV:check('S1/S2 success and one next slice '+path,'C - S2 SUCCESS' in body(path) and next_task in body(path) and 'not begun' in body(path))
check('S2 reports honest limits and seed capabilities',all(s.lower() in report.lower() for s in ['registration-only','metadata only','S3-S6','Swiss multiview parked','No foundational/technology deviation','not semantic accuracy','not manufactured']))
(R/OUT).write_text('{}\n',encoding='utf-8')
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
code={'semantic.mjs','query.mjs','query-cli.mjs','query-matrix.json','measure_s2.mjs','validate_s2.py','README-S2.md','adapters/native.py','adapters/test_native.py','tests/query.test.mjs'}
check('S2 only changed files',all(p in NAV or p.startswith('docs/research/tryfan-pilot-s2') or p.startswith('pilots/atlas/tryfan/') and p[len('pilots/atlas/tryfan/'):] in code for p in changed))
check('no large/source/runtime payload added',all((R/p).stat().st_size<200000 for p in changed if p not in NAV) and not any(p.endswith(('.tif','.png','.npz','.db','.sqlite','.pyc')) for p in changed))
check('no S3 onward modules',all(not (R/'pilots/atlas/tryfan'/p).exists() for p in ['derivations.mjs','dependencies.mjs','updates.mjs','server.mjs','client']))

def slugs(text):
    seen={};out=set()
    for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
        title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1;out.add(key if not n else key+'-'+str(n))
    return out
missing=[];references=anchors=0
for file in changed:
    if not file.endswith('.md'):continue
    text=body(file)
    if file=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - Tryfan pilot S2'):]
    for link in re.findall(r'\]\(([^)]+)\)',text):
        link=link.strip().strip('<>')
        if link.startswith(('http:','https:','mailto:','data:','meridian-data:')):continue
        path,_,anchor=unquote(link).partition('#');target=(R/file).parent/path if path else R/file;references+=1
        if not target.exists():missing.append([file,link]);continue
        if anchor and target.suffix=='.md':
            anchors+=1
            if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([file,link])
check('all report/navigation/tooling references anchors',not missing)
for t in admission['threads']:
    for link in t['canonicalReferences']:
        path,_,anchor=unquote(link).partition('#');target=R/'docs/research'/path
        check('canonical reference '+t['id']+' '+link,target.exists() and (not anchor or target.suffix!='.md' or anchor in slugs(target.read_text(encoding='utf-8-sig'))))
run('working diff whitespace',['git','diff','--check']);run('staged diff whitespace',['git','diff','--cached','--check'])
check('Markdown whitespace',all(all(line.rstrip()==line for line in body(p).splitlines()) for p in changed if p.endswith('.md')))
receipt=dict(assessment='atlas-tryfan-pilot-s2-validation/v1',startingCheckpoint=BASE,decision='C - S2 SUCCESS',checks=checks,errors=errors,commands=commands,
 changedPaths=changed,retainedSourceVerification=state['verification'],priorAdmissionSourceVerification=prior['sources'],unchangedHistoricalFiles=len(paths),historicalMismatches=bad,
 canonicalThreads=42,protectedProductionHashes=113,frozenSemanticHashes=7,publishedGeneration=state['generation'],parentGeneration=state['parent'],matrixSha256=logical['matrixSha256'],fullMatrixSha256=logical['fullMatrixSha256'],missingReferences=missing,localReferences=references,anchors=anchors,
 nextTask=next_task+'; not begun',codeSha256={p:P.digest(R/p) for p in changed if p.startswith('pilots/')},artifactSha256={p:P.digest(R/p) for p in [REPORT,RESULTS]},
 confirmations=dict(noRetainedMutation=True,noNewData=True,noPrivateAccess=True,noProductionChanges=True,noFrozenChanges=True,noS3OrLater=True,S1PublicationUnchanged=True,appearanceUnresolvedNonBlocking=True,swissMultiviewParked=True))
(R/OUT).write_text(P.encode(receipt),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),errors=errors,retainedFiles=310,protectedHashes=113,refs=references,missing=missing)))
if errors:raise SystemExit(1)
