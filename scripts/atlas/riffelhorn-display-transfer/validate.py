"""Display-transfer diagnostics checks; prior research and source products stay read-only."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3]
BASE='20461af84b0619abc8b7b218aac9ef1e53de1fae'
PREFIX='riffelhorn-display-transfer'
OUT=f'docs/research/{PREFIX}-validation.json'
REPORT=f'docs/research/{PREFIX}.md'
PROTOCOL='scripts/atlas/illumination-assessment/future-evaluation.json'
PROTOCOL_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
NEXT='Retained Exe time-qualified water-observation and feature-query proof'
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
report=read(REPORT);check('28 report sections',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,29)))
check('explicit partial signal and next','**B - PARTIAL' in report and NEXT in report and 'This next task has not begun.' in report)
check('no mojibake','\u00e2\u20ac' not in report and '\u00c2\u00a7' not in report)
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
artifacts=[f'docs/research/{PREFIX}{x}' for x in ['-results.json','-views.png','-insets.png','-curves.png']]
before={p:sha(p) for p in artifacts}
run('fresh process deterministic experiment',[str(python),'scripts/atlas/riffelhorn-display-transfer/experiment.py'])
check('byte identical metrics and three PNG rerun',before=={p:sha(p) for p in artifacts})
r=data(artifacts[0]);plan=data('scripts/atlas/riffelhorn-display-transfer/protocol.json')
planpath='scripts/atlas/riffelhorn-display-transfer/protocol.json'
check('predeclared protocol exact revision',plan['frozenBeforeCandidateOutputs'] and r['protocolSha256']==sha(planpath)=='90f4d2e00d7e11a02e2eff12a38b39e93f0d5bf378b08bb67ee9462d97b81de8')
check('exact method revision',r['methodSha256']==sha('scripts/atlas/riffelhorn-display-transfer/experiment.py'))
check('prior metrics untouched',r['priorMetricsSha256']==sha('docs/research/riffelhorn-dark-source-signal-results.json'))
check('display only no source/product writes',r['displayOnly'] and r['noSourceOrProductWrites'])
check('four frozen patches and unchanged strata',plan['patches']==data('scripts/atlas/riffelhorn-dark-source/assessment-plan.json')['patches'] and plan['binsDN']==[0,5,10,20,40,80,128,256])
check('four source hashes and bytes',len(r['sources'])==4 and all(hashlib.sha256((ROOT.parent/'meridian-data'/x['path']).read_bytes()).hexdigest()==x['sha256'] and (ROOT.parent/'meridian-data'/x['path']).stat().st_size==x['bytes'] for x in r['sources']))
check('source bytes fixed',sum(x['bytes'] for x in r['sources'])==186259028)
check('prepared product exact identity',r['prepared']['identity']=='f6edd630206ed02f255176935d72126cbc6ad7987b12d2986edbe6d05619bc1b' and r['prepared']['manifestSha256']=='3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934')
check('prepared1084 verified and14 patch tiles',r['prepared']['payloadsVerified']==1084 and len(r['prepared']['tiles'])==14 and r['prepared']['alphaUnchanged'] and r['prepared']['operatorAfterPNGDecode'])
check('production display hashes exact',all(sha(p)==h for p,h in r['productionDisplayCodeSha256'].items()))
check('historical decisions and source qualifications retained',all(x in report for x in ['INCONCLUSIVE','NOT JUSTIFIED','PARTIAL RETAINED SIGNAL','SCALE-CONDITIONAL','6.1923','PARKED']))
ps=r['patches'];oldr=data('docs/research/riffelhorn-dark-source-signal-results.json')
check('source windows and baseline quantiles exact',all(v['sourceWindow']==oldr['patches'][k]['sourceWindow'] and all(c['pixels']['sourceIntensityQuantiles']==oldr['patches'][k]['intensityP05P50P95'] for c in v['candidates'].values()) for k,v in ps.items()))
check('fixed block counts including unsupported deepest bin',all(sum(b['blocks'] for b in v['baseline'].values())==oldr['patches'][k]['blocks5m'] and v['baseline']['0-5']['blocks']==0 for k,v in ps.items()))
check('toe4 all numerical gates pass',all(r['numericalCriteria']['toe4'][k] for k in ['curveMonotonic','darkNumericalPass','codecNumericalPass','preservationPass']))
check('toe8 codec failure preserved',not r['numericalCriteria']['toe8']['codecNumericalPass'] and r['numericalCriteria']['toe8']['darkNumericalPass'] and r['numericalCriteria']['toe8']['preservationPass'])
check('quantization occupied and merged levels preserved',[(r['numericalCriteria'][k]['greyOccupiedOutputLevels'],r['numericalCriteria'][k]['greyMergedAdjacentPairs'],r['numericalCriteria'][k]['greyMaxStep']) for k in ['toe4','toe8']]==[(252,4,2),(248,8,2)])
check('visual judgement required independently',all(c['visualAssessmentRequired'] for c in r['numericalCriteria'].values()))
for label,groups in [('native',{k:{n:c['pixels'] for n,c in v['candidates'].items()} for k,v in ps.items()}),('prepared',{k:v['candidates'] for k,v in r['prepared']['patches'].items()})]:
 check(label+' anchors clipping colour order and exact output identities',all(c['weakIdentity'] and c['brightIdentity'] and c['allRGBZero']==0 and c['anyChannel255']==0 and c['channelOrderInversions']==0 and c['rawRatioMaxError']<=1e-12 and c['hueErrorDegreesP05P50P95'][2]<=5 and c['saturationAbsErrorP05P50P95'][2]<=.05 and len(c['outputRGB8Sha256'])==64 for g in groups.values() for c in g.values()))
check('current report research only not physical correction','Research-only; no production display prototype' in report and 'no candidate' in report.lower())
source_verified=r['sources']

testout=run('13 focused display safeguards',[str(python),'scripts/atlas/riffelhorn-display-transfer/test_experiment.py']);check('13 tests counted','Ran 13 tests' in testout)
nodeout=run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']);check('64 tests counted',bool(re.search(r'(?:#|\u2139) pass 64',nodeout)))
run('frozen isolated declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('canonical next assessment explicit', '**Recommend exactly one next bounded task: '+NEXT+'.**' in state and '### Retained Riffelhorn dark-detail display-transfer experiment - complete' in state)
for p in ['docs/architecture.md','docs/product-direction.md','docs/research/atlas-research-map.md']:
 check('current navigation '+p,NEXT in re.sub(r'\s+',' ',read(p)) and 'B - PARTIAL' in re.sub(r'\s+',' ',read(p)))
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated assessment and navigation',all(p in nav or p.startswith('docs/research/'+PREFIX) or p.startswith('scripts/atlas/riffelhorn-display-transfer/') for p in modified))
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
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - retained Riffelhorn dark-detail display-transfer experiment'):]
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
for c in ['20461af','e276d81','9dc4445','1842008','9695757','b12dc06','944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');check('checkpoint ancestor '+c,subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))

receipt={'assessment':'riffelhorn-display-transfer/v1','startingCheckpoint':BASE,'decision':'B - PARTIAL','checks':checks,'errors':errors,'commands':commands,'localElapsedTimesNotPerformancePromises':True,'artifactSha256':before,'codeSha256':{p:sha(p) for p in modified if p.startswith('scripts/atlas/riffelhorn-display-transfer/')},'reportSha256':sha(REPORT),'frozenProtocolSha256':sha(planpath),'originalIlluminationCriteriaSha256':sha(PROTOCOL),'sourceVerification':source_verified,'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'changedPaths':modified,'nextTask':NEXT+'; not started','confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noFittingOrCorrection':True,'diagnosticLiftOnly':True,'noPhysicalSNR':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing},ensure_ascii=True))
if errors:raise SystemExit(1)
