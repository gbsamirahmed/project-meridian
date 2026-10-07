"""Dark-source diagnostics checks; prior research and source products stay read-only."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3]
BASE='e276d814942b5e94adfa2353a95a10e78536b028'
PREFIX='riffelhorn-dark-source-signal'
OUT=f'docs/research/{PREFIX}-validation.json'
REPORT=f'docs/research/{PREFIX}.md'
PROTOCOL='scripts/atlas/illumination-assessment/future-evaluation.json'
PROTOCOL_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
NEXT='Retained Riffelhorn dark-detail display-transfer experiment'
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
check('explicit partial signal and next','**B - PARTIAL RETAINED SIGNAL' in report and NEXT in report and 'This next task has not begun.' in report)
check('no mojibake','\u00e2\u20ac' not in report and '\u00c2\u00a7' not in report)
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
artifacts=[f'docs/research/{PREFIX}{s}' for s in ['-results.json','-views.png','-support.png']]
before={p:sha(p) for p in artifacts}
run('fresh process deterministic diagnostics',[str(python),'scripts/atlas/riffelhorn-dark-source/assess.py'])
check('byte identical metrics and PNG rerun',before=={p:sha(p) for p in artifacts})
r=data(artifacts[0]);plan=data('scripts/atlas/riffelhorn-dark-source/assessment-plan.json')
check('predeclared plan exact revision',plan['recordedBeforeStatistics'] and r['planSha256']=='3d586fd3fd9bfefb19f5d979797b4371670a7f394776e4b7a15b99fb48654e32' and r['planSha256']==sha('scripts/atlas/riffelhorn-dark-source/assessment-plan.json'))
check('exact method revision',r['methodSha256']==sha('scripts/atlas/riffelhorn-dark-source/assess.py'))
check('no correction or fitting',r['noCorrection'] and r['noFitting'] and plan['noCorrection'] and plan['noFitting'])
check('four frozen patches',plan['patches']==data('scripts/atlas/riffelhorn-registration/plan.json')['patches'])
check('four source hashes and bytes',len(r['sources'])==4 and all(hashlib.sha256((ROOT.parent/'meridian-data'/x['path']).read_bytes()).hexdigest()==x['sha256'] and (ROOT.parent/'meridian-data'/x['path']).stat().st_size==x['bytes'] for x in r['sources']))
check('source metadata preserved',all(x['dtype']==['uint8']*3 and x['crs']==2056 and x['res']==[.1,.1] and x['imageStructure']['COMPRESSION']=='YCbCr JPEG' and x['imageStructure']['JPEG_QUALITY']=='95' for x in r['encoding']))
check('source bytes fixed',r['sourceBytes']==186259028)
check('prepared product exact identity',r['prepared']['identity']=='f6edd630206ed02f255176935d72126cbc6ad7987b12d2986edbe6d05619bc1b' and r['prepared']['manifestSha256']=='3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934')
check('prepared1084 verified and14 regenerated',r['prepared']['payloadsVerified']==1084 and len(r['prepared']['tilesRegenerated'])==14 and all(v['fieldExact'] and v['PNGExactDeclaredEncoding'] for v in r['prepared']['tilesRegenerated']))
check('all42 statuses and old source qualification independent',len(rows(state))==42 and 'INCONCLUSIVE' in report and '6.1923' in report and 'PARKED' in report)
ps=r['patches']
check('native counts',ps['ordinary']['nativeCells']==ps['steep']['nativeCells']==360000 and ps['summit']['nativeCells']==ps['dark-context']['nativeCells']==2250000)
check('blocks mean-stratified all accounted',all(sum(b['blocks'] for b in v['blockStrata'].values())==v['blocks5m'] for v in ps.values()))
check('native strata all accounted',all(sum(b['cells'] for b in v['nativeStrata'].values())==v['nativeCells'] for v in ps.values()))
check('no allRGBblack or255 support collapse',all(v['allRGBZeroCells']==0 and v['anyChannel255Cells']==0 for v in ps.values()))
check('below5 no complete block not absent pixels',all(v['blockStrata']['0-5']['blocks']==0 and v['nativeStrata']['0-5']['cells']>0 and v['blockStrata']['0-5']['adjacency05m'] is None for v in ps.values()))
check('darkest green occupancy7',all(ps[k]['nativeStrata']['0-5']['channelOccupiedLevels'][1]==7 for k in ['steep','summit','dark-context']))
check('dark block support fixed',ps['steep']['blockStrata']['5-10']['blocks']==10 and ps['dark-context']['blockStrata']['5-10']['blocks']==19 and ps['steep']['blockStrata']['10-20']['blocks']==123 and ps['dark-context']['blockStrata']['10-20']['blocks']==586)
check('dark multiscale recorded adjacency',all(ps[k]['blockStrata']['10-20']['adjacency05m'][1]>.39 and ps[k]['blockStrata']['10-20']['adjacency1m'][1]>.22 and abs(ps[k]['blockStrata']['10-20']['shuffleAdjacency05m'][1])<.02 for k in ['steep','summit','dark-context']))
check('tensor comparator limitation retained',all(ps[k]['blockStrata']['10-20']['coherence05m'][1]<ps[k]['blockStrata']['10-20']['shuffleCoherence05m'][1] for k in ['steep','summit','dark-context']))
check('same-field encoding error bound andnozero',all(v.get('maxIntensityRoundingErrorDN',0)<=.500001 and v.get('encodedAllRGBZero',0)==0 for pop in r['prepared']['encodingStrata'].values() for v in pop.values()))
check('retained metadata exact',all(sha(p)==h for p,h in r['retainedMetadataSha256'].items()))
source_verified=r['sources']

testout=run('13 focused signal and support safeguards',[str(python),'scripts/atlas/riffelhorn-dark-source/test_assess.py']);check('13 tests counted','Ran 13 tests' in testout)
nodeout=run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']);check('64 tests counted',bool(re.search(r'(?:#|\u2139) pass 64',nodeout)))
run('frozen isolated declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('canonical next assessment explicit', '**Recommend exactly one next bounded task: '+NEXT+'.**' in state and '### Retained Riffelhorn dark-source signal assessment - complete' in state)
for p in ['docs/architecture.md','docs/product-direction.md','docs/research/atlas-research-map.md']:
 check('current navigation '+p,NEXT in re.sub(r'\s+',' ',read(p)) and 'B - PARTIAL RETAINED SIGNAL' in re.sub(r'\s+',' ',read(p)))
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated assessment and navigation',all(p in nav or p.startswith('docs/research/'+PREFIX) or p.startswith('scripts/atlas/riffelhorn-dark-source/') for p in modified))
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
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - retained Riffelhorn dark-source signal and texture-support assessment'):]
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
for c in ['e276d81','9dc4445','1842008','9695757','b12dc06','944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');check('checkpoint ancestor '+c,subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))

receipt={'assessment':'riffelhorn-dark-source/v1','startingCheckpoint':BASE,'decision':'B - PARTIAL RETAINED SIGNAL','checks':checks,'errors':errors,'commands':commands,'localElapsedTimesNotPerformancePromises':True,'artifactSha256':before,'codeSha256':{p:sha(p) for p in modified if p.startswith('scripts/atlas/riffelhorn-dark-source/')},'reportSha256':sha(REPORT),'frozenProtocolSha256':sha(PROTOCOL),'sourceVerification':source_verified,'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'changedPaths':modified,'nextTask':NEXT+'; not started','confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noFittingOrCorrection':True,'diagnosticLiftOnly':True,'noPhysicalSNR':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing},ensure_ascii=True))
if errors:raise SystemExit(1)
