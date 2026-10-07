"""Vegetation protocol checks; prior research and source products stay read-only."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3]
BASE='9dc4445d491fd59bab2b8e1b613ef62a4bf486b6'
PREFIX='tryfan-vegetation-protocol'
OUT=f'docs/research/{PREFIX}-validation.json'
REPORT=f'docs/research/{PREFIX}.md'
PROTOCOL='scripts/atlas/illumination-assessment/future-evaluation.json'
PROTOCOL_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
NEXT='Retained Riffelhorn dark-source signal and texture-support assessment'
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

check('original illumination criteria hash unchanged',sha(PROTOCOL)==PROTOCOL_SHA)
report=read(REPORT);check('27 report sections',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,28)))
check('explicit protocol no-go and next','**A - NOT JUSTIFIED' in report and NEXT in report and 'This next task has not begun.' in report)
check('no mojibake','\u00e2\u20ac' not in report and '\u00c2\u00a7' not in report)
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
artifacts=[f'docs/research/{PREFIX}{s}' for s in ['-results.json','-populations.png','-support.png']]
before={p:sha(p) for p in artifacts}
run('fresh process deterministic diagnostics',[str(python),'scripts/atlas/tryfan-vegetation-protocol/assess.py'])
check('byte identical metrics and PNG rerun',before=={p:sha(p) for p in artifacts})
r=data(artifacts[0]);plan=data('scripts/atlas/tryfan-vegetation-protocol/assessment-plan.json');cs=r['candidates']
check('predeclared assessment plan exact hash',plan['recordedBeforeNewPopulationStatistics'] and r['planSha256']=='1754a4cddc32d1b7ed76032f9009e813475c542ab0d2514f1e13596aad32394c' and r['planSha256']==sha('scripts/atlas/tryfan-vegetation-protocol/assessment-plan.json'))
check('isolated method exact revision',r['methodSha256']==sha('scripts/atlas/tryfan-vegetation-protocol/assess.py'))
check('no fitting or corrected arrays',r['noCorrectionModelFitted'] and r['correctedArraysProduced']==0)
check('same fixed study and core',plan['studyEPSG27700']==[264900,357800,267900,360800] and plan['coreEPSG27700']==[265900,358800,266900,359800] and r['metadata']['core']==plan['coreEPSG27700'])
check('three motivated candidates fixed20m boundary and100m holdout guard',[x['id'] for x in plan['candidates']]==['P1','P2','P3'] and plan['boundaryGuardMetres']==20 and plan['spatialDesign']['futureTrainGuardMetres']==100)
check('native SCL nearest lookup equivalence',r['sourceSCLLookupMismatchCells']==0)
check('exact nested population counts',[cs[k]['cells'] for k in cs]==[8053,5370,205] and r['SCL4AfterOriginalGeometry']==8741)
check('native SCL counts not independent10m labels',[cs[k]['nativeSCLCellsUsed'] for k in cs]==[2142,1535,75])
check('all candidate gates fail before fitting',all(not v['feasibility']['passed'] for v in cs.values()) and r['decision'].startswith('A - NOT JUSTIFIED'))
check('P2 central support shortage retained',cs['P2']['feasibility']['folds'][0]['testWithinTrainingP05P95Fraction']<.41 and cs['P2']['feasibility']['folds'][3]['testWithinTrainingP05P95Fraction']<.71)
check('P3 east support absent not zero reflectance',[f['testCells'] for f in cs['P3']['feasibility']['folds']]==[76,0,129,0] and cs['P3']['baselineQuadrants']['NE']['brightness']['pearson'] is None)
check('prior stopped experiment exactly reproduced',r['oldGateReproduced']==data('docs/research/tryfan-illumination-normalization-baseline.json')['gate'] and r['oldGateReproduced']['failures']==['SCL5 SE heldout 12<20'])
check('six retained semantic hashes and bytes',len(r['semanticSources'])==6 and all(hashlib.sha256((ROOT.parent/'meridian-data'/x['path']).read_bytes()).hexdigest()==x['sha256'] and (ROOT.parent/'meridian-data'/x['path']).stat().st_size==x['bytes'] for x in r['semanticSources']))
check('observation and terrain hashes',all(hashlib.sha256((ROOT.parent/'meridian-data'/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in list(r['metadata']['inputs'].values())+[r['metadata']['terrain']]))
check('known mean Sun and qualified reconstruction',r['metadata']['sourceSun']['azimuthDegrees']==160.700929790374 and r['metadata']['sourceSun']['elevationDegrees']==58.062309162853 and r['metadata']['reconstructedSunAtCore']['notPixelTimeBounds'])
check('source native annual class retained',cs['P2']['nativeWCCodeCounts']=={'30':5370} and cs['P3']['NRWCodeIncidenceCounts']=={'D.1.1':205})
check('semantic coexistence without universal truth',sum(cs['P2']['NRWCodeIncidenceCounts'].values())==5370 and cs['P2']['NRWCodeIncidenceCounts']['I.1.2']==75 and cs['P2']['NRWCodeIncidenceCounts']['D.1.1']==3809)
check('no physical area/fraction from assignment counts',all(v['notPhysicalVegetationArea'] for v in cs.values()))
check('retained metadata exact hashes',all(sha(p)==h for p,h in r['metadata']['retainedMetadataSha256'].items()))
source_verified=list(r['metadata']['inputs'].values())+[r['metadata']['terrain']]+r['semanticSources']
testout=run('16 focused mask and support safeguards',[str(python),'scripts/atlas/tryfan-vegetation-protocol/test_assess.py']);check('16 tests counted','Ran 16 tests' in testout)
nodeout=run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']);check('64 tests counted',bool(re.search(r'(?:#|\u2139) pass 64',nodeout)))
run('frozen isolated declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('canonical next assessment explicit', '**Recommend exactly one next bounded task: '+NEXT+'.**' in state and '### Retained Tryfan vegetation-only protocol assessment - complete' in state)
for p in ['docs/architecture.md','docs/product-direction.md','docs/research/atlas-research-map.md']:
 check('current navigation '+p,NEXT in re.sub(r'\s+',' ',read(p)) and 'A - NOT JUSTIFIED' in re.sub(r'\s+',' ',read(p)))
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated assessment and navigation',all(p in nav or p.startswith('docs/research/'+PREFIX) or p.startswith('scripts/atlas/tryfan-vegetation-protocol/') for p in modified))
check('bounded artifacts no warped imagery or scratch store',all((ROOT/p).stat().st_size<(1000000 if p.endswith('.png') else 250000) for p in modified if p not in nav) and all(not p.endswith(('.tif','.npz','.sqlite','.db','.vrt')) for p in modified))
def slugs(s):
 out=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;out.add(key if n==0 else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for p in modified:
 if not p.endswith('.md'):continue
 text=read(p)
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - retained Tryfan vegetation-only residual-normalization protocol assessment'):]
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
for c in ['9dc4445','1842008','9695757','b12dc06','944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');check('checkpoint ancestor '+c,subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))

receipt={'assessment':'tryfan-vegetation-protocol/v1','startingCheckpoint':BASE,'decision':'A - NOT JUSTIFIED','checks':checks,'errors':errors,'commands':commands,'localElapsedTimesNotPerformancePromises':True,'artifactSha256':before,'codeSha256':{p:sha(p) for p in modified if p.startswith('scripts/atlas/tryfan-vegetation-protocol/')},'reportSha256':sha(REPORT),'frozenProtocolSha256':sha(PROTOCOL),'sourceVerification':source_verified,'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'changedPaths':modified,'nextTask':NEXT+'; not started','confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noFittingOrCorrection':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing},ensure_ascii=True))
if errors:raise SystemExit(1)
