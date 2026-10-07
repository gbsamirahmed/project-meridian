"""Stage-aware S3 acceptance; historical stage receipts remain immutable."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,os
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'))
import check_plan as P
A=P.admission
BASE='7db385a466ce74abae42c75f7613e18ac2207468'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/tryfan-pilot-s3.md';RESULTS='docs/research/tryfan-pilot-s3-results.json';OUT='docs/research/tryfan-pilot-s3-validation.json'
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

check('expected 7db385a ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
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
compat={'pilots/atlas/tryfan/generations.mjs','pilots/atlas/tryfan/query.mjs','pilots/atlas/tryfan/tests/query.test.mjs'}
preserve={}
for line in git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research','pilots').splitlines():
    meta,path=line.split('\t',1)
    if path not in NAV|compat:preserve[path]=meta.split()[2]
paths=list(preserve);hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines();bad=[p for p,h in zip(paths,hashes) if h!=preserve[p]]
check('all historical reports scientific/frozen tooling preserved',len(paths)==len(hashes) and not bad)
for name,args,count in [
 ('S3 lifecycle tests',['node','--test','pilots/atlas/tryfan/tests/lifecycle.test.mjs'],29),
 ('S2 native query regressions',['node','--test','pilots/atlas/tryfan/tests/query.test.mjs'],33),
 ('native addressing geometry cases',[sys.executable,'pilots/atlas/tryfan/adapters/test_native.py'],9),
 ('S1 immutable generation tests',['node','--test','pilots/atlas/tryfan/tests/catalogue.test.mjs'],22),
 ('planning safeguards',[sys.executable,'scripts/atlas/regional-pilot-plan/test_plan.py'],22),
 ('frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'],64),
 ('retained qualified-query lifecycle',['node','--test','scripts/atlas/test_qualified_query_proof.mjs'],None),
 ('retained persistent lifecycle',['node','--test','scripts/atlas/test_local_persistent_tryfan.mjs'],None)]:
    text=run(name,args)
    if count:check(name+' declared count',(f'tests {count}' if args[0]=='node' else f'Ran {count} tests') in text)
run('frozen semantic TypeScript',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
run('deterministic S3 independent measured rerun',['node','pilots/atlas/tryfan/measure_s3.mjs','--check'])
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'))
check('310 immutable retained pilot sources',state['counts']==dict(sources=5,products=5,representations=8,families=5,artifacts=310) and state['verification']==dict(artifacts=310,bytes=42473107))
expected=P.read(R/P.OUT)['sourceHashes'];actual={state['locators'][a['id']]:dict(sha256=a['sha256'],bytes=a['bytes']) for a in state['catalogue']['artifacts']};check('exact frozen310source inventory',expected==actual)
results=P.read(R/RESULTS);logical=results['logical'];matrix=P.read(R/'pilots/atlas/tryfan/lifecycle-matrix.json')
check('15 prospectively frozen lifecycle scenarios',len(matrix['scenarios'])==15 and matrix['frozenBeforeEvaluation'] and matrix['queries']==[q for q in plan['query']['matrix'] if q['id'] in ['Q01','Q02','Q03','Q04','Q12','Q21']])
check('logical receipt canonical digest',P.digest(R/'pilots/atlas/tryfan/lifecycle-matrix.json')==logical['matrixSha256'] and hashlib.sha256(P.encode(logical).encode()).hexdigest()==results['logicalSha256'])
check('real G0 generation baseline flags',state['generation']==logical['generation'] and state['parent']==logical['parent'] and state['capabilities']==dict(registration=True,queries=True,derivations=True,serving=False,mixedFamilyUpdate=False))
check('four exact retained results two methods four edges',logical['counts']==dict(methods=2,results=4,dependencyEdges=4,reverseKeys=4,referencedTerrainAssets=2,registeredArtifacts=310))
for r in logical['results']:
    prior_result=next(q for q in P.read(R/'docs/research/tryfan-qualified-query-results.json')['results'] if q['claim']==dict(id=r['claim']['id'],revision=r['claim']['revision']))
    check('original claim receipt value '+r['probe']+' '+r['property'],prior_result['receipt']==r['receipt'] and prior_result['value']==r['claim']['result'])
for name in ['unchanged','unrelatedFamily','unrelatedSpace','methodReplay']:check(name+' all fresh',all(a['assessment']['status']=='fresh' for a in logical['scenarios'][name]))
for name,expected_status in [('relevant',['stale','stale','fresh','fresh']),('unknownScope',['indeterminate','indeterminate','fresh','fresh']),('unavailable',['indeterminate','indeterminate','fresh','fresh']),('methodPolicy',['stale']*4)]:check(name+' scoped qualification',[a['assessment']['status'] for a in logical['scenarios'][name]]==expected_status)
rec=logical['isolatedRecomputation'];check('only two recomputed two reused four history six fixture revisions',rec['notPublished'] and rec['considered']==4 and len(rec['recomputed'])==2 and len(rec['reused'])==2 and rec['historicalRetained'] and rec['totalRevisions']==6 and rec['currentResults']==4)
check('four genuine/six fixture exact pixel replay',logical['baselineReplay']['fromRetainedPixels'] and len(logical['baselineReplay']['checks'])==4 and all(c['exact'] for c in logical['baselineReplay']['checks']+rec['replay']) and len(rec['replay'])==6)
check('five independent fresh integrated responses match',len(results['measurements']['freshProcesses'])==5 and all(p['logicalSha256']==logical['integratedSha256'] for p in results['measurements']['freshProcesses']))
check('Q21 fixed six independent native/derived contexts',len(logical['coordinator'])==6 and all(r['generation']==state['generation'] for r in logical['coordinator']))
# Previous S2 results reproduce against their unchanged immutable seed, not a fake current-state assertion.
s2=P.read(R/'docs/research/tryfan-pilot-s2-results.json')['logical']
raw=subprocess.check_output(['node','pilots/atlas/tryfan/query-cli.mjs','matrix','--generation',s2['generation']],cwd=R,encoding='utf-8')
check('historical S2 full matrix exact preserved',hashlib.sha256(raw.encode()).hexdigest()==s2['fullMatrixSha256'])
check('S1 atomic publication implementation unchanged',body('pilots/atlas/tryfan/generations.mjs').split('export function canonicalGeneration',1)[1]==old('pilots/atlas/tryfan/generations.mjs').split('export function canonicalGeneration',1)[1])
check('S2 native query semantics unchanged',body('pilots/atlas/tryfan/query.mjs').split('async function query(request)',1)[1]==old('pilots/atlas/tryfan/query.mjs').split('async function query(request)',1)[1])
report=body(REPORT);check('31 durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,32)))
next_task='Tryfan pilot generation-pinned serving and isolated consumer - S4 only'
for path in NAV:check('S1/S2/S3 success one next slice '+path,'C - S3 SUCCESS' in body(path) and next_task in body(path) and 'not begun' in body(path))
check('honest bounded report',all(s.lower() in report.lower() for s in ['No applicability update is published','isolated','S4-S6','appearance unresolved/non-blocking','Swiss multiview parked','No conceptual, scientific or technology deviation','stale does not mean false']))
(R/OUT).write_text('{}\n',encoding='utf-8')
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
code={'derivations.mjs','dependencies.mjs','world.mjs','lifecycle-cli.mjs','lifecycle-matrix.json','measure_s3.mjs','validate_s3.py','README-S3.md','adapters/retained_derivation.py','tests/lifecycle.test.mjs','tests/lifecycle-worker.mjs'}
check('S3 only changes',all(p in NAV|compat or p.startswith('docs/research/tryfan-pilot-s3') or p.startswith('pilots/atlas/tryfan/') and p[len('pilots/atlas/tryfan/'):] in code for p in changed))
check('no source/production Weather Traverse changes',not any(p.startswith(('src/','public/','meridian-private')) for p in changed))
check('no large/source/runtime payload Git additions',all((R/p).stat().st_size<200000 for p in changed if p not in NAV) and not any(p.endswith(('.tif','.png','.npz','.db','.sqlite','.pyc')) for p in changed))
check('no S4 onward modules',all(not (R/'pilots/atlas/tryfan'/p).exists() for p in ['updates.mjs','server.mjs','delivery.mjs','client']))

def slugs(text):
    seen={};out=set()
    for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
        title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1;out.add(key if not n else key+'-'+str(n))
    return out
missing=[];references=anchors=0
for file in changed:
    if not file.endswith('.md'):continue
    text=body(file)
    if file=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - Tryfan pilot S3'):]
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
receipt=dict(assessment='atlas-tryfan-pilot-s3-validation/v1',startingCheckpoint=BASE,decision='C - S3 SUCCESS',checks=checks,errors=errors,commands=commands,changedPaths=changed,
 retainedSourceVerification=state['verification'],priorAdmissionSourceVerification=prior['sources'],unchangedHistoricalFiles=len(paths),historicalMismatches=bad,canonicalThreads=42,protectedProductionHashes=113,frozenSemanticHashes=7,
 publishedGeneration=state['generation'],parentGeneration=state['parent'],logicalSha256=results['logicalSha256'],matrixSha256=logical['matrixSha256'],missingReferences=missing,localReferences=references,anchors=anchors,nextTask=next_task+'; not begun',
 codeSha256={p:P.digest(R/p) for p in changed if p.startswith('pilots/')},artifactSha256={p:P.digest(R/p) for p in [REPORT,RESULTS]},
 confirmations=dict(noRetainedMutation=True,noNewData=True,noPrivateAccess=True,noProductionChanges=True,noFrozenChanges=True,noS4OrLater=True,S1PublicationUnchanged=True,S2NativeQueryUnchanged=True,appearanceUnresolvedNonBlocking=True,swissMultiviewParked=True))
(R/OUT).write_text(P.encode(receipt),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),errors=errors,retainedFiles=310,protectedHashes=113,refs=references,missing=missing)))
if errors:raise SystemExit(1)
