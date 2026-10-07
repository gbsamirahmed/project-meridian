"""Validate planning artifacts and unchanged Meridian evidence; never create a pilot."""
from pathlib import Path
from urllib.parse import unquote
import json,re,subprocess,sys
import check_plan as P
R=P.ROOT;BASE=P.BASE;A=P.admission
REPORT='docs/research/tryfan-regional-pilot-plan.md'
OUT='docs/research/tryfan-regional-pilot-plan-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
checks=[];errors=[];commands=[]

def check(name,ok):
    checks.append(dict(check=name,passed=bool(ok)))
    if not ok:errors.append(name)

def git(*args):
    return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').strip()

def base_body(path):
    return subprocess.check_output(['git','show',BASE+':'+path],cwd=R).decode('utf-8')

def body(path):return (R/path).read_text(encoding='utf-8-sig')

def run(name,args):
    res=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
    check(name,res.returncode==0);commands.append(dict(check=name,command=args,exitCode=res.returncode))
    if res.returncode:print(res.stdout[-4000:],res.stderr[-4000:])
    return res.stdout+res.stderr

check('expected clean starting checkpoint ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
check('main existing origin/main upstream',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main')
check('fetched pre-commit divergence0/0',git('rev-list','--left-right','--count','HEAD...origin/main').split()==['0','0'])
p=P.read(R/P.PLAN);first=P.assess();second=P.assess()
check('deterministic plan and310retained hashes',first==second and first['uniqueRetainedFiles']==310 and first['retainedBytes']==42473107)
(R/P.OUT).write_text(P.encode(first),encoding='utf-8',newline='\n')
prior=A.assess();check('nine admission gates and original proof coverage reproduced',prior['gateOutcomes']=={'G'+str(i):'PASS' for i in range(1,10)} and prior['requiredCapabilities']==50 and prior['proofCount']==37)
check('1575 admission retained files unchanged',prior['sources']['uniqueFiles']==1575)
check('frozen admission criteria unchanged',A.digest(R/A.GATES)==A.GATES_SHA)
check('plan implementation decision not implementation evidence',first['decision']=='C - IMPLEMENTABLE AS PLANNED' and not first['integratedServingImplemented'] and not first['mixedFamilyPublicationImplemented'] and first['noPilotImplementation'])
check('original exact derivation roots retained',p['scienceBasis']['rootRevisions']=={x['id']:x['revision'] for x in P.read(R/p['scienceBasis']['inputs'])['roots']})
coarse=next(x for x in p['assets'] if x['path'].endswith('5/15/10.png'));receipt=P.read(P.DATA/'cache/atlas/tryfan/second-region-proof/aws/5/15/10.json')
check('coarse common retained receipt matches byte hash',receipt['sha256']==coarse['sha256'])
for f in p['foundations']:
    check('foundation checkpoint '+f['id'],subprocess.run(['git','merge-base','--is-ancestor',f['checkpoint'],BASE],cwd=R,capture_output=True).returncode==0)
old=base_body('docs/research/atlas-research-state.md');state=body('docs/research/atlas-research-state.md')
check('all42 historical status columns unchanged',len(A.canonical_rows(old))==42 and A.canonical_rows(old)==A.canonical_rows(state))
admission=P.read(R/p['admission']['manifest'])
check('all42 admission dispositions unchanged',len(admission['threads'])==42 and all(t['historicalStatus']==A.canonical_rows(state)[t['id']] for t in admission['threads']) and next(t for t in admission['threads'] if t['id']=='A13')['pilotClass']=='PARKED EXTERNAL DEPENDENCY')
check('historical audit details preserved',old[old.index('<details>'):old.index('</details>')+len('</details>')] in state)
check('development log append-only',body('docs/development-log.md').startswith(base_body('docs/development-log.md')+'\n'))
protected=P.read(R/'docs/atlas/information-display-plan.json')['productionHashes'];prod=[path for path,h in protected.items() if P.digest(R/path)!=h]
check('113 protected production hashes unchanged',len(protected)==113 and not prod)
frozen=P.read(R/'docs/atlas/semantic-evidence-contract-validation.json')['code'];bad=[x['href'] for x in frozen if P.digest(R/x['href'])!=x['sha256']]
check('seven frozen semantic contract tooling hashes',len(frozen)==7 and not bad)
check('production Atlas Weather Traverse and frozen domain docs unchanged',not git('diff',BASE,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
preserve={};counts=dict(scripts=0,AtlasEarthLabReports=0,priorResearchAssets=0)
for line in git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research').splitlines():
    meta,path=line.split('\t',1)
    if path.startswith('scripts/'):category='scripts'
    elif path.startswith(('docs/atlas/','docs/earth-lab/')) and path.endswith('.md'):category='AtlasEarthLabReports'
    elif path.startswith('docs/research/') and path not in NAV:category='priorResearchAssets'
    else:continue
    preserve[path]=meta.split()[2];counts[category]+=1
paths=list(preserve)
hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines()
mismatch=[path for path,h in zip(paths,hashes) if h!=preserve[path]]
check('all historical reports research artifacts and scripts unchanged',len(hashes)==len(paths) and not mismatch and counts['AtlasEarthLabReports']==43)
report=body(REPORT)
check('37 required report sections',list(map(int,re.findall(r'^## (\d+)\.',report,re.M)))==list(range(1,38)))
check('eight bounded ADRs present',all('| P'+str(i).zfill(2)+' |' in report for i in range(1,9)))
check('all21queries and16exit tests in report',all('| '+q['id']+' |' in report for q in p['query']['matrix']) and all('| '+a['id']+' |' in report for a in p['acceptance']))
check('controlled cross-family scenario and interrupted publication explicit',all(x in report for x in ['U1','U2','M0','M1','F1','F2','F3','abruptly','generation','not environmental change']))
check('appearance debt and partial results preserved',all(x in report for x in ['1842008','INCONCLUSIVE','e276d81','NOT JUSTIFIED','9dc4445','SCALE-CONDITIONAL','20461af','PARTIAL RETAINED SIGNAL','b85c296','Swiss multiview remains parked']))
check('no next slice begun',p['nextTask'] in report and 'This first implementation task has not begun.' in report and all(not(R/path).exists() for path in p['noImplementationPathsCreated']))
for path in NAV:
    text=body(path)
    check('canonical pilot phase and next task '+path,p['nextTask'] in text and 'C - IMPLEMENTABLE AS PLANNED' in text and ('f16ce63' in text or path.endswith('atlas-research-state.md')) and 'not begun' in text)
(R/OUT).write_text('{}\n',encoding='utf-8',newline='\n')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
check('only planning tooling artifacts and canonical navigation changed',all(path in NAV or path.startswith('docs/research/tryfan-regional-pilot-plan') or path.startswith('scripts/atlas/regional-pilot-plan/') for path in modified))
check('no payload/full transformed imagery/runtime artifacts tracked',all((R/path).stat().st_size<200000 for path in modified if path not in NAV) and all(not path.endswith(('.tif','.png','.npz','.db','.sqlite','.vrt','.pyc')) for path in modified))

def slugs(text):
    seen={};out=set()
    for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
        title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower()
        key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1
        out.add(key if not n else key+'-'+str(n))
    return out
refs=anchors=0;missing=[]
for file in modified:
    if not file.endswith('.md'):continue
    text=body(file)
    if file=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - Bounded retained Tryfan regional-pilot architecture and implementation plan'):]
    for link in re.findall(r'\]\(([^)]+)\)',text):
        link=link.strip().strip('<>')
        if link.startswith(('http:','https:','mailto:','data:','meridian-data:')) or 'meridian-private' in link:continue
        path,_,anchor=unquote(link).partition('#');target=(R/file).parent/path if path else R/file;refs+=1
        if not target.exists():missing.append([file,link]);continue
        if anchor and target.suffix=='.md':
            anchors+=1
            if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([file,link])
check('all report navigation local references and anchors resolve',not missing)
for t in admission['threads']:
    for link in t['canonicalReferences']:
        path,_,anchor=unquote(link).partition('#');target=R/'docs/research'/path
        if not target.exists() or (anchor and target.suffix=='.md' and anchor not in slugs(target.read_text(encoding='utf-8-sig'))):
            raise ValueError('Missing canonical thread evidence '+link)
check('all42 canonical thread reference paths/anchors',True)
for directory in ['docs/research','docs/atlas','docs/earth-lab']:
    for file in (R/directory).glob('*.json'):P.read(file)
check('all research JSON parses',True)
tests=run('22 focused planning safeguards',[sys.executable,'scripts/atlas/regional-pilot-plan/test_plan.py'])
check('22 focused tests counted','Ran 22 tests' in tests)
run('64 frozen domain contract/runtime tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
run('frozen semantic isolated TypeScript check',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
run('working diff whitespace',['git','diff','--check']);run('staged diff whitespace',['git','diff','--cached','--check'])
check('Markdown no trailing whitespace',all(all(line.rstrip()==line for line in body(path).splitlines()) for path in modified if path.endswith('.md')))
receipt={'assessment':'atlas-tryfan-regional-pilot-plan-validation/v1','startingCheckpoint':BASE,'decision':first['decision'],'checks':checks,'errors':errors,'commands':commands,'planReproduces':first==second,'planRequiredSources':dict(files=310,bytes=first['retainedBytes'],inventorySha256=first['retainedInventorySha256']),'priorAdmissionSourceVerification':prior['sources'],'unchangedHistorical':counts,'preservationMismatches':mismatch,'canonicalStatusColumnsUnchanged':A.canonical_rows(old)==A.canonical_rows(state),'canonicalThreadCount':42,'protectedProductionHashChecks':113,'productionMismatches':prod,'frozenSemanticHashChecks':7,'frozenMismatches':bad,'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'artifactSha256':{path:P.digest(R/path) for path in [REPORT,P.PLAN,P.OUT]},'codeSha256':{path:P.digest(R/path) for path in modified if path.startswith('scripts/atlas/regional-pilot-plan/')},'changedPaths':modified,'nextTask':p['nextTask']+'; not begun','confirmations':dict(noPilotImplementation=True,noRetainedWrites=True,noAcquisition=True,noProductionChanges=True,noWeatherTraverseChanges=True,noFrozenChanges=True,swissMultiviewParked=True,appearanceDebtNotClosed=True,noFinalInfrastructureSelected=True)}
(R/OUT).write_text(P.encode(receipt),encoding='utf-8',newline='\n')
print(json.dumps(dict(checks=len(checks),errors=errors,refs=refs,anchors=anchors,historical=counts,sourceFiles=prior['sources']['uniqueFiles'],missing=missing)))
if errors:raise SystemExit(1)
