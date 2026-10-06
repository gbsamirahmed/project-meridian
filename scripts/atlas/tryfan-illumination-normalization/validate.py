"""Bounded stopped-experiment validation. Existing sources/protocol remain read-only."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3]
BASE='96957570b585781995feaec52b1598784b4db3d9'
PREFIX='tryfan-illumination-normalization'
OUT=f'docs/research/{PREFIX}-validation.json'
REPORT=f'docs/research/{PREFIX}.md'
PROTOCOL='scripts/atlas/illumination-assessment/future-evaluation.json'
PROTOCOL_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
NEXT='Retained Riffelhorn imagery-terrain registration and epoch-consistency assessment'
checks=[];errors=[];commands=[]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def read(p):return (ROOT/p).read_text(encoding='utf-8-sig')
def data(p):return json.loads(read(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:errors.append(name)
def run(name,args):
 start=time.perf_counter();r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 commands.append({'check':name,'command':args,'exitCode':r.returncode,'localElapsedSeconds':time.perf_counter()-start});check(name,r.returncode==0)
 if r.returncode:print(r.stdout[-2500:],r.stderr[-2500:])
 return r.stdout+r.stderr
check('checkpoint is ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,capture_output=True).returncode==0)
check('main origin/main',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main')
check('upstream divergence0/0 before commit',git('rev-list','--left-right','--count','main...origin/main').split()==['0','0'])
protected=data('docs/atlas/information-display-plan.json')['productionHashes'];badprod=[p for p,h in protected.items() if sha(p)!=h]
check('113 protected production hashes',len(protected)==113 and not badprod)
frozen=data('docs/atlas/semantic-evidence-contract-validation.json')['code'];badfrozen=[p['href'] for p in frozen if sha(p['href'])!=p['sha256']]
check('seven frozen semantic contract code/fixture hashes',len(frozen)==7 and not badfrozen)
check('production terrain contracts metadata unchanged',not git('diff',BASE,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
entries=git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research').splitlines();preserve={};scripts=[];reports=[];research=[]
for row in entries:
 m,p=row.split('\t',1)
 if p.startswith('scripts/'):scripts.append(p)
 elif p.startswith(('docs/atlas/','docs/earth-lab/')) and p.endswith('.md'):reports.append(p)
 elif p.startswith('docs/research/') and p not in {'docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}:research.append(p)
 else:continue
 preserve[p]=m.split()[2]
paths=list(preserve);hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=ROOT,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines()
badpreserved=[p for p,h in zip(paths,hashes) if preserve[p]!=h]
check('all historical scripts/research and43 Atlas/EarthLab reports',len(hashes)==len(paths) and not badpreserved and len(reports)==43)
old=git('show',BASE+':docs/research/atlas-research-state.md');state=read('docs/research/atlas-research-state.md')
rx=r'^\| ((?:H|T|A|M|S)\d+) — [^|]+\|([^|]+)\|';rows=lambda s:{k:v.strip() for k,v in re.findall(rx,s,re.M)}
check('all42 canonical status columns unchanged',len(rows(state))==42 and rows(state)==rows(old))
historical=old[old.index('<details>'):old.index('</details>')+len('</details>')];check('historical audit gate retained',historical in state)
oldlog=git('show',BASE+':docs/development-log.md');check('append-only development log',read('docs/development-log.md').startswith(oldlog+'\n'))
check('exact frozen criteria unchanged',sha(PROTOCOL)==PROTOCOL_SHA and data(PROTOCOL)['experimentNotStarted'])
check('pre-baseline execution plan stable',sha('scripts/atlas/tryfan-illumination-normalization/execution-plan.json')=='39d2df989e622c42b11b02d9b4a4e7b82ab2b6a2bb68af778d8901cfa7ad7f25')
report=read(REPORT);check('27 report sections',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,28)))
check('explicit D stopped result and next task','**D — INCONCLUSIVE' in report and NEXT in report and 'This next task has not begun.' in report)
check('no mojibake','\u00e2\u20ac' not in report and '\u00c2\u00a7' not in report)
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
artifacts=[f'docs/research/{PREFIX}{s}' for s in ['-baseline.json','-results.json','-baseline.png','-association.png']]
before={p:sha(p) for p in artifacts}
run('deterministic fresh-process experiment stopping diagnostics',[str(python),'scripts/atlas/tryfan-illumination-normalization/experiment.py'])
check('byte-identical JSON and PNG rerun',before=={p:sha(p) for p in artifacts})
b=data(artifacts[0]);r=data(artifacts[1]);meta=b['metadata']
check('exact failed prerequisite',not b['gate']['passed'] and b['gate']['failures']==['SCL5 SE heldout 12<20'])
check('all8 fold counts preserved',len(b['gate']['folds'])==8 and [x['heldoutCells'] for x in b['gate']['folds']]==[1648,2286,2321,2486,271,46,172,12])
check('no alternative observation or altered core',meta['core']==[265900,358800,266900,359800] and meta['sourceSun']==data(PROTOCOL)['sourceSun'])
check('zero correction/models no publication',r['fittedModels']==0 and r['correctedCells']==0 and not r['correctedRepresentationPublished'] and r['decision'].startswith('D - INCONCLUSIVE'))
check('sensitivity and comparison honestly unavailable',r['sensitivity'].startswith('NOT RUN') and r['heldoutNormalizationBenefit']=='NOT EVALUABLE' and r['informationPreservationAfterCorrection']=='NOT EVALUABLE' and r['spectralDamageAfterCorrection']=='NOT EVALUABLE')
check('baseline persisted and referenced',r['baselineSha256']==sha(artifacts[0]) and b['baselineOnly'] and b['noFittingYet'])
check('mask and numeric counts',b['maskCountsOverlapping']=={'nonpositiveOrInvalidRGB':0,'excludedSCL':196,'incidenceBelow0point3':676,'incompleteRay':0,'modelBlockedWithin1km':132,'eligible':9242,'excluded':758} and b['numericCounts']=={'nonfiniteValues':0,'negativeValues':0,'aboveOneValues':0})
check('code plan shared geometry exact references',meta['methodSha256']==sha('scripts/atlas/tryfan-illumination-normalization/experiment.py') and meta['implementationPlanSha256']==sha('scripts/atlas/tryfan-illumination-normalization/execution-plan.json') and meta['sharedGeometryMethodSha256']==sha('scripts/atlas/illumination-assessment/assess.py'))
check('three retained metadata revisions unchanged',all(sha(p)==h for p,h in meta['retainedMetadataSha256'].items()))
source_verified=[]
for name,f in meta['inputs'].items():
 path=ROOT.parent/'meridian-data'/f['path'];ok=hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256'];check('retained source '+name,ok);source_verified.append({'role':name,**f})
f=meta['terrain'];path=ROOT.parent/'meridian-data'/f['path'];check('retained native terrain exact revision',hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']==data(PROTOCOL)['terrainSourceSha256'])
check('native and analysis grain support distinct',all(meta['nativeGrids'][k]['crs']=='EPSG:32630' for k in meta['nativeGrids']) and meta['nativeGrids']['scl']['transform'][0]==20 and f['normalAnalysisGridMetres']==10 and f['rayNativeSamplingMetres']==1 and f['rayRadiusMetres']==1000 and f['actualReadBoundsEPSG27700']==data(PROTOCOL)['retainedFootprintEPSG27700'])
check('reconstructed times not pixel bounds',meta['reconstructedSunAtCore']['notPixelTimeBounds'])
check('baseline texture and ratios not corrections',set(b['baselineTexture'])=={'4','5'} and b['baselineTexture']['4']['edges']==16765 and b['baselineTexture']['5']['edges']==767 and set(b['baselineRatios'])=={'4','5'})
testout=run('16 focused safeguards',[str(python),'scripts/atlas/tryfan-illumination-normalization/test_experiment.py']);check('16 focused tests counted','Ran 16 tests' in testout)
nodeout=run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']);check('64 tests counted',bool(re.search(r'(?:#|ℹ) pass 64',nodeout)))
run('frozen isolated TypeScript declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('current canonical recommendation consistent','**Recommend exactly one next bounded task: “'+NEXT+'.”**' in state and '### Retained Tryfan post-L2A residual normalization experiment — complete at stopping boundary' in state)
for p in ['docs/architecture.md','docs/product-direction.md','docs/research/atlas-research-map.md']:
 check('current navigation '+p,NEXT in read(p) and 'D — INCONCLUSIVE' in read(p))
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated experiment and navigation changed',all(p in nav or p.startswith('docs/research/'+PREFIX) or p.startswith('scripts/atlas/'+PREFIX+'/') for p in modified))
check('bounded artifacts no transient raster/index/store',all((ROOT/p).stat().st_size<250000 for p in modified if p not in nav) and all(not p.endswith(('.tif','.npz','.sqlite','.db','.vrt')) for p in modified))
def slugs(s):
 out=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;out.add(key if n==0 else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for p in modified:
 if not p.endswith('.md'):continue
 text=read(p)
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 — retained Tryfan post-L2A residual normalization experiment'):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  link=link.strip().strip('<>')
  if link.startswith(('http:','https:','data:','mailto:','meridian-data:')) or 'meridian-private' in link:continue
  file,_,anchor=unquote(link).partition('#');target=(ROOT/p).parent/file if file else ROOT/p;refs+=1
  if not target.exists():missing.append([p,link]);continue
  if anchor and target.suffix=='.md':
   anchors+=1
   if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([p,link])
check('all local document links and anchors resolve',not missing)
for d in ['docs/atlas','docs/earth-lab','docs/research']:
 for p in (ROOT/d).glob('*.json'):json.loads(p.read_text(encoding='utf-8-sig'))
check('all research JSON parses',True)
for c in ['9695757','b12dc06','944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');check('checkpoint ancestor '+c,subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'experiment':'tryfan-post-L2A-residual/v1','startingCheckpoint':BASE,'decision':r['decision'],'checks':checks,'errors':errors,'commands':commands,'localElapsedTimesNotPerformancePromises':True,'artifactSha256':before,'codeSha256':{p:sha(p) for p in modified if p.startswith('scripts/atlas/'+PREFIX+'/')},'reportSha256':sha(REPORT),'frozenProtocolSha256':sha(PROTOCOL),'sourceVerification':source_verified,'terrainSha256':f['sha256'],'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'changedPaths':modified,'nextTask':NEXT+'; not started','confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noCorrectionExecuted':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing},ensure_ascii=True))
if errors:raise SystemExit(1)
