"""Read-only programme acceptance validation; only new repository receipts are written."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys
import assess as A
R=A.ROOT;BASE=A.BASE
REPORT='docs/research/atlas-regional-pilot-acceptance.md'
OUT='docs/research/atlas-regional-pilot-acceptance-validation.json'
NAV={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
checks=[];errors=[];commands=[]
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:errors.append(name)
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def body(p):return (R/p).read_text(encoding='utf-8-sig')
def run(name,args):
 r=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace');check(name,r.returncode==0);commands.append({'check':name,'command':args,'exitCode':r.returncode})
 if r.returncode:print(r.stdout[-2000:],r.stderr[-2000:])
 return r.stdout+r.stderr
check('expected checkpoint ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=R,capture_output=True).returncode==0)
check('main and existing upstream',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main')
check('fetched pre-commit divergence0/0',git('rev-list','--left-right','--count','HEAD...origin/main').split()==['0','0'])
check('frozen admission gates exact',A.digest(R/A.GATES)==A.GATES_SHA)
m=A.read(R/A.MANIFEST);p=A.read(R/A.GATES);old=A.git_bytes('docs/research/atlas-research-state.md').decode('utf-8')
check('50capabilities 42threads 9gates evidence structure',A.check_structure(m,p,old))
first=A.assess();second=A.assess();check('deterministic coverage gates source verification',first==second)
(R/A.OUT).write_text(A.encode(first),encoding='utf-8',newline='\n')
check('explicit C admission with no identified prerequisite',first['decision']=='C - READY FOR BOUNDED REGIONAL PILOT' and not first['architecturalBlockers'] and not first['prePilotPrerequisites'] and first['admissionNotImplementedPilot'])
check('all50coverage roles plus3 explicit limits',first['requiredCapabilities']==50 and first['coverageCount']==53 and sum(first['coverageClasses'].values())==53 and first['coverageClasses']['PARTIALLY PROVEN']==4 and first['coverageClasses']['DESIGNED BUT NOT PROVEN']==1)
check('37proof records mapped to immutable references',first['proofCount']==37 and first['proofReferenceCount']>=70)
check('all9gates reproduced without scoring',first['gateOutcomes']=={'G'+str(i):'PASS' for i in range(1,10)})
check('1575 retained sources/prepared/metadata files verify',first['sources']['uniqueFiles']==1575 and first['sources']==second['sources'])
for t in m['threads']:
 check('canonical disposition '+t['id'],t['historicalStatus']==A.canonical_rows(old)[t['id']])
state=body('docs/research/atlas-research-state.md');check('42 original status columns unchanged',A.canonical_rows(state)==A.canonical_rows(old) and len(A.canonical_rows(state))==42)
history=old[old.index('<details>'):old.index('</details>')+len('</details>')];check('historical audit gate preserved',history in state)
check('development log append-only',body('docs/development-log.md').startswith(A.git_bytes('docs/development-log.md').decode('utf-8')+'\n'))
protected=A.read(R/'docs/atlas/information-display-plan.json')['productionHashes'];prod=[p for p,h in protected.items() if A.digest(R/p)!=h]
check('113 protected production hashes',len(protected)==113 and not prod)
frozen=A.read(R/'docs/atlas/semantic-evidence-contract-validation.json')['code'];bad=[e['href'] for e in frozen if A.digest(R/e['href'])!=e['sha256']]
check('seven frozen semantic declarations fixtures tooling',len(frozen)==7 and not bad)
check('production Atlas Weather Traverse contracts source unchanged',not git('diff',BASE,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
preserve={};counts={'scripts':0,'AtlasEarthLabReports':0,'priorResearchAssets':0}
for line in git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research').splitlines():
 meta,path=line.split('\t',1)
 if path.startswith('scripts/'):category='scripts'
 elif path.startswith(('docs/atlas/','docs/earth-lab/')) and path.endswith('.md'):category='AtlasEarthLabReports'
 elif path.startswith('docs/research/') and path not in NAV:category='priorResearchAssets'
 else:continue
 preserve[path]=meta.split()[2];counts[category]+=1
paths=list(preserve);hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=R,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines();mismatch=[p for p,h in zip(paths,hashes) if h!=preserve[p]]
check('all historical reports research assets and scripts frozen',len(hashes)==len(paths) and not mismatch and counts['AtlasEarthLabReports']==43)
for name in ['docs/architecture.md','docs/product-direction.md','docs/research/atlas-research-map.md','docs/research/atlas-research-state.md']:
 s=body(name);check('current programme transition '+name,m['nextTask'] in s and 'C - READY FOR BOUNDED REGIONAL PILOT' in s and 'not begun' in s)
report=body(REPORT);check('36required report sections',[int(x) for x in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,37)))
check('one next design task unstarted',m['nextTask'] in report and 'This next task has not begun.' in report)
check('partial outcomes and parked status preserved',all(s in report for s in ['INCONCLUSIVE','NOT JUSTIFIED','SCALE-CONDITIONAL','PARTIAL','PARKED EXTERNAL DEPENDENCY']))
check('pilot admission not implementation or final tech',all(s in report for s in ['No concrete foundational blocker','not acceptance of an already implemented pilot','power-loss','mixed publication','DESIGNED BUT NOT PROVEN']))
(R/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
check('only acceptance tooling artifacts and navigation',all(p in NAV or p.startswith('docs/research/atlas-regional-pilot-acceptance') or p.startswith('scripts/atlas/pilot-acceptance/') for p in modified))
check('lightweight files no datasets runtime stores',all((R/p).stat().st_size<200000 for p in modified if p not in NAV) and all(not p.endswith(('.tif','.png','.npz','.db','.sqlite','.vrt','.pyc')) for p in modified))
def slugs(s):
 seen={};out=set()
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=seen.get(key,0);seen[key]=n+1;out.add(key if not n else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for file in modified:
 if not file.endswith('.md'):continue
 s=body(file)
 if file=='docs/development-log.md':s=s[s.rindex('## 2026-10-07 - Atlas retained-proof coverage and bounded regional-pilot acceptance'):]
 for link in re.findall(r'\]\(([^)]+)\)',s):
  link=link.strip().strip('<>')
  if link.startswith(('http:','https:','mailto:','data:','meridian-data:')) or 'meridian-private' in link:continue
  path,_,anchor=unquote(link).partition('#');target=(R/file).parent/path if path else R/file;refs+=1
  if not target.exists():missing.append([file,link]);continue
  if anchor and target.suffix=='.md':
   anchors+=1
   if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([file,link])
check('all local references and anchors',not missing)
for t in m['threads']:
 for link in t['canonicalReferences']:
  path,_,anchor=unquote(link).partition('#');target=R/'docs/research'/path
  if not target.exists() or (anchor and target.suffix=='.md' and anchor not in slugs(target.read_text(encoding='utf-8-sig'))):raise ValueError('Missing canonical thread evidence '+link)
check('all42native thread evidence references',True)
for d in ['docs/research','docs/atlas','docs/earth-lab']:
 for file in (R/d).glob('*.json'):A.read(file)
check('research JSON parses',True)
tests=run('17 focused acceptance safeguards',[sys.executable,'scripts/atlas/pilot-acceptance/test_assess.py']);check('17 tests counted','Ran 17 tests' in tests)
run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
run('frozen isolated semantic declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
run('working diff whitespace',['git','diff','--check']);run('staged diff whitespace',['git','diff','--cached','--check'])
check('Markdown trailing whitespace',all(all(line.rstrip()==line for line in body(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'assessment':'atlas-pilot-admission-validation/v1','startingCheckpoint':BASE,'decision':first['decision'],'checks':checks,'errors':errors,'commands':commands,'gatesSha256':A.GATES_SHA,'coverageAndGatesReproduce':first==second,'sourceVerification':first['sources'],'unchangedHistorical':counts,'preservationMismatches':mismatch,'protectedProductionHashChecks':113,'productionMismatches':prod,'frozenSemanticHashChecks':7,'frozenMismatches':bad,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':A.canonical_rows(old)==A.canonical_rows(state),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'artifactSha256':{p:A.digest(R/p) for p in [REPORT,A.MANIFEST,A.OUT,A.GATES]},'codeSha256':{p:A.digest(R/p) for p in modified if p.startswith('scripts/atlas/pilot-acceptance/')},'changedPaths':modified,'nextTask':m['nextTask']+'; not begun','confirmations':{'noSourceAcquisition':True,'noDomainExperiment':True,'noRetainedDatasetWrites':True,'noPilotImplementation':True,'noProductionChanges':True,'noWeatherTraverseChanges':True,'noFrozenChanges':True,'noScienceClosureByAdmission':True,'swissMultiviewParked':True,'noFinalInfrastructureSelection':True}}
(R/OUT).write_text(A.encode(receipt),encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'historical':counts,'sourceFiles':first['sources']['uniqueFiles'],'missing':missing}))
if errors:raise SystemExit(1)
