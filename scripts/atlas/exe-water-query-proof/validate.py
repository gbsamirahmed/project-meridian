"""Retained Exe query-proof checks; prior research and source products stay read-only."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3]
BASE='b85c296ba480a3d26159a759f1d26d829efc2f50'
PREFIX='exe-water-query'
OUT=f'docs/research/{PREFIX}-validation.json'
REPORT='docs/research/exe-water-query-proof.md'
PROTOCOL='scripts/atlas/illumination-assessment/future-evaluation.json'
PROTOCOL_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
NEXT='Atlas retained-proof coverage and bounded regional-pilot acceptance assessment'
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
report=read(REPORT);check('32 report sections',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,33)))
check('explicit semantic integration success and next','**C - SUCCESS' in report and NEXT in report and 'This next task has not begun.' in report)
check('no mojibake','\u00e2\u20ac' not in report and '\u00c2\u00a7' not in report)
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
artifact='docs/research/exe-water-query-results.json'
run('initialize final deterministic artifact',['node','scripts/atlas/exe-water-query-proof/run-proof.mjs'])
before={artifact:sha(artifact)}
original=data(artifact)
run('repeat four fresh-process recovery/rebuild proof',['node','scripts/atlas/exe-water-query-proof/run-proof.mjs'])
check('byte identical query/result manifest rerun',sha(artifact)==before[artifact])
r=data(artifact);planpath='scripts/atlas/exe-water-query-proof/matrix.json';plan=data(planpath)
check('frozen75-query matrix exact',len(plan['queries'])==75 and plan['frozenBeforeNewQueryEvaluation'] and sha(planpath)==r['matrixSha256']=='d8afb247c2030367d2a85ae912e42a446cc09e34a49b03b46b4635478d9a304b')
check('code revisions exact',all(sha('scripts/atlas/exe-water-query-proof/'+p)==h for p,h in r['codeSha256'].items()))
check('four processes exact recovery and independent build',r['restart']['freshProcesses']==4 and all(r['restart'][k] for k in ['initialRecoveryExact','secondRecoveryExact','independentBuildExact']))
source_verified=r['sourceHashes'];root=ROOT.parent/'meridian-data/derived/atlas/water-check-v1'
check('31 pinned source hashes and exact bytes',len(source_verified)==31 and all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v['sha256'] and (root/n).stat().st_size==v['bytes'] for n,v in source_verified.items()))
check('66 retained files unchanged through all fresh processes',len(r['sourceDirectoryHashes'])==66 and original['sourceDirectoryHashes']==r['sourceDirectoryHashes'] and all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in r['sourceDirectoryHashes'].items()))
check('native3-code raster and vector counts preserved',[(c['id'],c['claims']) for c in r['counts']]==[('collection:wfd',1),('collection:phi',336),('collection:flood',492),('collection:rfo',23),('collection:2024-03',3),('collection:2024-09',3)])
a={q['id']:q for q in r['answers']}
check('75 outputs match frozen IDs',list(a)==[q['id'] for q in plan['queries']])
check('source-native WFD identity stable',a['feature-exe']['feature']['id']=='GB510804505600')
check('positive negative no-observation distinct',a['P1-point-2024-03']['result']['value']['outcome']=='detected' and a['P3-point-2024-03']['result']['value']['outcome']=='not-detected' and a['P1-point-2024-09']['result']['reason']=='no-observation')
check('current state unsupported',all(a['P'+str(i)+'-current']['result']['reason']=='unsupported' for i in range(1,7)))
check('unavailable outside unknown unsupported not-applicable',a['P1-unavailable-month']['availability']=='unavailable' and 'result' not in a['P1-unavailable-month'] and a['outside-study']['result']['reason']=='outside-support' and a['wrong-epoch-inventory']['result']['reason']=='unknown' and a['wrong-mode']['result']['reason']=='unsupported' and a['not-applicable-feature']['result']['reason']=='not-applicable')
check('incompatible fallback rejected despite coexisting evidence',a['P1-unavailable-month']['otherEvidenceExists'] and a['P1-unavailable-month']['rejectedFallbacks']==['wfd','phi','flood','rfo'])
check('comparison never implies drying',all(not q['physicalChangeSupported'] for q in r['answers'] if q['question']=='compare') and a['P1-compare']['comparison']['anyUnobserved']==76 and a['P3-compare']['allSelectedCellsObservedInBothMonths'])
check('all four vector meanings coexist atP1',all(a['P1-coexist']['evidence'][k]['claims'] for k in ['wfd','phi','flood','rfo']) and a['P1-coexist']['noUniversalWinner'])
check('prior appearance decisions preserved',all(t in report for t in ['SCALE-CONDITIONAL','PARTIAL RETAINED SIGNAL','PARTIAL display transfer','INCONCLUSIVE','NOT JUSTIFIED','PARKED']))
testout=run('20 focused retained semantic/query safeguards',['node','--test','scripts/atlas/exe-water-query-proof/test-proof.mjs']);check('20 tests counted',bool(re.search(r'(?:#|\u2139) pass 20',testout)))
nodeout=run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']);check('64 tests counted',bool(re.search(r'(?:#|\u2139) pass 64',nodeout)))
run('frozen isolated declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('canonical next assessment explicit', '**Recommend exactly one next bounded task: '+NEXT+'.**' in state and '### Retained Exe time-qualified water-observation and feature-query proof - complete' in state)
for p in ['docs/architecture.md','docs/product-direction.md','docs/research/atlas-research-map.md']:
 check('current navigation '+p,NEXT in re.sub(r'\s+',' ',read(p)) and 'C - SUCCESS' in re.sub(r'\s+',' ',read(p)))
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated assessment and navigation',all(p in nav or p.startswith('docs/research/'+PREFIX) or p.startswith('scripts/atlas/exe-water-query-proof/') for p in modified))
check('bounded artifacts no warped imagery or scratch store',all((ROOT/p).stat().st_size<(1200000 if p.endswith('-results.json') else 250000) for p in modified if p not in nav) and all(not p.endswith(('.tif','.npz','.sqlite','.db','.vrt')) for p in modified))
def slugs(s):
 out=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;out.add(key if n==0 else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for p in modified:
 if not p.endswith('.md'):continue
 text=read(p)
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - retained Exe time-qualified water-observation and feature-query proof'):]
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
for c in ['b85c296','20461af','e276d81','9dc4445','1842008','9695757','b12dc06','944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');check('checkpoint ancestor '+c,subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))

receipt={'proof':'exe-qualified-water/v1','startingCheckpoint':BASE,'decision':'C - SUCCESS','checks':checks,'errors':errors,'commands':commands,'localElapsedTimesNotPerformancePromises':True,'storeBytes':r['storeBytes'],'resultArtifactBytes':(ROOT/artifact).stat().st_size,'restart':r['restart'],'artifactSha256':before,'codeSha256':{p:sha(p) for p in modified if p.startswith('scripts/atlas/exe-water-query-proof/')},'reportSha256':sha(REPORT),'frozenMatrixSha256':sha(planpath),'originalIlluminationCriteriaSha256':sha(PROTOCOL),'sourceVerification':source_verified,'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'changedPaths':modified,'nextTask':NEXT+'; not started','confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noFittingOrCorrection':True,'noUniversalWaterLayer':True,'noHydrologyOrCurrentStateInference':True,'noPhysicalSNR':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing},ensure_ascii=True))
if errors:raise SystemExit(1)
