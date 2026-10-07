"""Stage-aware S4 acceptance; historical stage receipts remain immutable."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,os
sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'scripts/atlas/regional-pilot-plan'))
import check_plan as P
A=P.admission
BASE='337a3c4c2408ee9e471b37b92b8a23b6e0088b42'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md'}
REPORT='docs/research/tryfan-pilot-s4.md';RESULTS='docs/research/tryfan-pilot-s4-results.json';OUT='docs/research/tryfan-pilot-s4-validation.json'
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
    log=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1/s4-validation';log.mkdir(parents=True,exist_ok=True)
    (log/(re.sub(r'[^a-z0-9]+','-',name.lower())+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n')
    check(name,p.returncode==0);commands.append(dict(check=name,command=args,exitCode=p.returncode))
    if p.returncode:print(p.stdout[-4000:],p.stderr[-4000:])
    return p.stdout+p.stderr

check('expected 337a3c4 ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
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
compat={'pilots/atlas/tryfan/'+p for p in ['generations.mjs','query.mjs','derivations.mjs','world.mjs','adapters/native.py']}
preserve={}
for line in git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research','pilots').splitlines():
    meta,path=line.split('\t',1)
    if path not in NAV|compat:preserve[path]=meta.split()[2]
paths=list(preserve);hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines();bad=[p for p,h in zip(paths,hashes) if h!=preserve[p]]
check('all historical reports scientific/frozen tooling preserved',len(paths)==len(hashes) and not bad)
for name,args,count in [
 ('S4 generation-pinned HTTP tests',['node','--test','pilots/atlas/tryfan/tests/http.test.mjs'],21),
 ('isolated browser interaction and fixed portrayal',['node','pilots/atlas/tryfan/tests/browser-runner.mjs'],None),
 ('S1 S2 S3 regressions',['node','--test','pilots/atlas/tryfan/tests/catalogue.test.mjs','pilots/atlas/tryfan/tests/query.test.mjs','pilots/atlas/tryfan/tests/lifecycle.test.mjs'],84),
 ('native addressing geometry cases',[sys.executable,'pilots/atlas/tryfan/adapters/test_native.py'],9),
 ('planning safeguards',[sys.executable,'scripts/atlas/regional-pilot-plan/test_plan.py'],22),
 ('frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'],64),
 ('retained qualified-query lifecycle',['node','--test','scripts/atlas/test_qualified_query_proof.mjs'],None),
 ('retained persistent lifecycle',['node','--test','scripts/atlas/test_local_persistent_tryfan.mjs'],None)]:
    text=run(name,args)
    if count:check(name+' declared count',(f'tests {count}' if args[0]=='node' else f'Ran {count} tests') in text)
run('frozen semantic TypeScript',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
run('deterministic S4 independent measured rerun',['node','pilots/atlas/tryfan/measure_s4.mjs','--check'])
run('production lint',['npm.cmd','run','lint']);run('production build',['npm.cmd','run','build'])
state=json.loads(subprocess.check_output(['node','pilots/atlas/tryfan/cli.mjs','inspect'],cwd=R,text=True,encoding='utf-8'))
check('310 immutable retained pilot sources',state['counts']==dict(sources=5,products=5,representations=8,families=5,artifacts=310) and state['verification']==dict(artifacts=310,bytes=42473107))
expected=P.read(R/P.OUT)['sourceHashes'];actual={state['locators'][a['id']]:dict(sha256=a['sha256'],bytes=a['bytes']) for a in state['catalogue']['artifacts']};check('exact frozen310source inventory',expected==actual)
results=P.read(R/RESULTS);logical=results['logical']
canonical_hash=subprocess.check_output(['node','--input-type=module','-e',"import {readFileSync} from 'node:fs';import {encode,sha} from './pilots/atlas/tryfan/identity.mjs';const r=JSON.parse(readFileSync('docs/research/tryfan-pilot-s4-results.json','utf8'));console.log(sha(encode(r.logical)));"],cwd=R,text=True,encoding='utf-8').strip()
check('logical receipt integrity using pilot canonical encoder',canonical_hash==results['logicalSha256'])
check('exact currently published generation',logical['generation']==state['generation'] and state['capabilities']==dict(registration=True,queries=True,derivations=True,serving=True,mixedFamilyUpdate=False))
s3=P.read(R/'docs/research/tryfan-pilot-s3-results.json')['logical'];store=P.DATA/'experiments/atlas/tryfan-regional-pilot-v1'
v=P.read(store/'generations'/f"{state['generation']}.json");oldg=P.read(store/'generations'/f"{s3['generation']}.json")
for key in ['catalogue','knowledge','understanding']:check('S3 unchanged scientific '+key,v[key]==oldg[key])
check('common-only stage and four historical results',v['understanding']['stage']=='common' and len(v['understanding']['results'])==4 and v['understanding']['results']==s3['results'])
for a in v['serving']['assets']:
    if a['origin']['kind']=='materialized':check('serving artifact hash '+a['family'],P.digest(store/'artifacts'/(a['id']+('.png' if a['mime']=='image/png' else '.json')))==a['sha256'])
check('exact298 registered native terrain bindings',len(v['serving']['tiles'])==298)
check('five genuinely fresh consumer answers deterministic',len(results['fresh'])==5 and len(set(x['answerSha256'] for x in results['fresh']))==1 and all(x['generation']==state['generation'] for x in results['fresh']))
check('bounded1/4reader measurements no errors',[(r['readers'],r['requests'],r['errors']) for r in results['controlledLoad']]==[(1,100,0),(4,100,0)])
check('single service worker and no byte/query cache',results['service']['delivery']['workerCount']==1 and 'no query or byte cache' in results['runtime']['cache'])
qa=results['qa'];check('real browser four fixed views generation-pinned no errors',qa['allDataGenerationPinned'] and not qa['errors'] and len(qa['views'])==4 and qa['mapDimensions']==[960,720])
for view in qa['views']:check('exact fixed-view PNG '+view['view'],P.digest(store/'s4-qa'/(view['view']+'.png'))==view['sha256'])
for path,record in results['qaFigures'].items():check('compact matched figure '+path,P.digest(R/path)==record['sha256'] and (R/path).stat().st_size==record['bytes']<150000)
# Reproduce original S2/S3 statements under exact historic contexts.
s2=P.read(R/'docs/research/tryfan-pilot-s2-results.json')['logical'];raw=subprocess.check_output(['node','pilots/atlas/tryfan/query-cli.mjs','matrix','--generation',s2['generation']],cwd=R,encoding='utf-8')
check('historical S2 full matrix exact',hashlib.sha256(raw.encode()).hexdigest()==s2['fullMatrixSha256'])
request=json.dumps(dict(property='place-evidence',place=dict(crs='EPSG:27700',point=[266405,359387])))
raw=subprocess.check_output(['node','pilots/atlas/tryfan/lifecycle-cli.mjs','query','--generation',s3['generation'],'--request',request],cwd=R,encoding='utf-8')
check('historical S3 Q21 exact',hashlib.sha256(raw.encode()).hexdigest()==s3['integratedSha256'])
old_native=old('pilots/atlas/tryfan/adapters/native.py');native=body('pilots/atlas/tryfan/adapters/native.py')
check('S2 exact native query geometry unchanged',native.split('    def query(self,q):',1)[1].split('def main()',1)[0]==old_native.split('    def query(self,q):',1)[1].split('def main()',1)[0])
old_der=old('pilots/atlas/tryfan/derivations.mjs');check('S3 scientific lifecycle unchanged',body('pilots/atlas/tryfan/derivations.mjs').replace(' await server.close(); // Loaded frozen functions remain usable; no loader listener retained.\n','')==old_der)
check('S3 coordinator unchanged except read-only assessment forwarding',body('pilots/atlas/tryfan/world.mjs').replace('assess:options=>derived.assess(options),','')==old('pilots/atlas/tryfan/world.mjs'))
current_generation=body('pilots/atlas/tryfan/generations.mjs').split('export function canonicalGeneration',1)[1]
current_generation=current_generation.replace('  if(value.serving)verifyDelivery(store,value.serving);\n','').replace('if(value.serving)verifyDelivery(store,value.serving);','')
check('S1 atomic publication unchanged except serving closure validation',current_generation==old('pilots/atlas/tryfan/generations.mjs').split('export function canonicalGeneration',1)[1])
report=body(REPORT);check('26 durable report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,27)))
next_task='Tryfan pilot scoped and mixed-family publication with interruption - S5 only'
for path in NAV:check('S1 S2 S3 S4 success one next slice '+path,'C - S4 SUCCESS' in body(path) and next_task in body(path) and 'not begun' in body(path))
check('honest bounded report',all(s.lower() in report.lower() for s in ['No S5/S6 implementation','Appearance unresolved/non-blocking','Swiss multiview parked','bad port','stale does not mean false','same-evidence','No scientific applicability update']))
check('prospective matrix/recipe identity',P.digest(R/'pilots/atlas/tryfan/serving-matrix.json')==logical['matrixSha256'] and P.digest(R/'pilots/atlas/tryfan/display-recipe.json')==logical['recipeSha256'] and len(P.read(R/'pilots/atlas/tryfan/serving-matrix.json')['scenarios'])==24)
(R/OUT).write_text('{}\n',encoding='utf-8')
changed=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
allowed={'README-S4.md','delivery.mjs','delivery-schema.mjs','delivery-cli.mjs','server.mjs','display-recipe.json','serving-matrix.json','measure_s4.mjs','validate_s4.py','tests/http.test.mjs','tests/http-worker.mjs','tests/service-process.mjs','tests/visual.mjs','tests/browser-runner.mjs','client/index.html','client/view.mjs','client/http-consumer.mjs','client/session-consumer.mjs'}
check('S4 only changes',all(p in NAV|compat or p.startswith('docs/research/tryfan-pilot-s4') or p.startswith('pilots/atlas/tryfan/') and p[len('pilots/atlas/tryfan/'):] in allowed for p in changed))
check('no source production Weather Traverse changes',not any(p.startswith(('src/','public/','meridian-private')) for p in changed))
check('only lightweight code metadata QA in Git',all((R/p).stat().st_size<200000 for p in changed if p not in NAV) and not any(p.endswith(('.tif','.png','.npz','.db','.sqlite','.pyc')) for p in changed))
check('no S5 onward modules',all(not (R/'pilots/atlas/tryfan'/p).exists() for p in ['updates.mjs','tests/publication.test.mjs','tests/restart.test.mjs','measure.mjs','tests/acceptance.test.mjs']))
for file in ['client/view.mjs','client/http-consumer.mjs','client/session-consumer.mjs']:
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
    if file=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - Tryfan pilot S4'):]
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
receipt=dict(assessment='atlas-tryfan-pilot-s4-validation/v1',startingCheckpoint=BASE,decision='C - S4 SUCCESS',checks=checks,errors=errors,commands=commands,changedPaths=changed,
 retainedSourceVerification=state['verification'],priorAdmissionSourceVerification=prior['sources'],unchangedHistoricalFiles=len(paths),historicalMismatches=bad,canonicalThreads=42,protectedProductionHashes=113,frozenSemanticHashes=7,
 publishedGeneration=state['generation'],parentGeneration=state['parent'],logicalSha256=results['logicalSha256'],matrixSha256=logical['matrixSha256'],missingReferences=missing,localReferences=references,anchors=anchors,nextTask=next_task+'; not begun',
 codeSha256={p:P.digest(R/p) for p in changed if p.startswith('pilots/')},artifactSha256={p:P.digest(R/p) for p in [REPORT,RESULTS]},
 confirmations=dict(noRetainedMutation=True,noNewData=True,noPrivateAccess=True,noProductionChanges=True,noFrozenChanges=True,noS5OrLater=True,S1PublicationUnchanged=True,S2NativeQueryUnchanged=True,S3LifecycleUnchanged=True,appearanceUnresolvedNonBlocking=True,swissMultiviewParked=True))
(R/OUT).write_text(P.encode(receipt),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),errors=errors,retainedFiles=310,protectedHashes=113,refs=references,missing=missing)))
if errors:raise SystemExit(1)
