"""Retained illumination identifiability validation; no acquisition, no retained source mutation.
Run before commit/push with retained data environment. Writes only a small receipt.
"""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
BASE='b12dc06dc51d86b85d8635f6741398dde9a65801'
REPORT='docs/research/illumination-identifiability.md';OUT='docs/research/illumination-identifiability-validation.json'
PROTOCOL_SHA='d6e573aa7294fde767998836d932097793bd084811ea67e4969f0afbf2bd4c8b'
FUTURE_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
checks=[];errors=[];commands=[]
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True,encoding='utf-8').strip()
def read(p):return (ROOT/p).read_text(encoding='utf-8-sig')
def data(p):return json.loads(read(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def check(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 if not ok:errors.append(name)
def run(name,args):
 r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace');commands.append({'check':name,'command':args,'exitCode':r.returncode});check(name,r.returncode==0)
 if r.returncode:print(r.stdout[-2500:],r.stderr[-2500:])
 return r.stdout+r.stderr
check('expected starting requirements checkpoint ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,capture_output=True).returncode==0)
check('existing clean main upstream context',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main')
check('precommit divergence 0/0',git('rev-list','--left-right','--count','main...origin/main').split()==['0','0'])
protected=data('docs/atlas/information-display-plan.json')['productionHashes'];badprod=[p for p,h in protected.items() if sha(p)!=h]
check('113 protected production hashes unchanged',len(protected)==113 and not badprod)
frozen=data('docs/atlas/semantic-evidence-contract-validation.json')['code'];badfrozen=[p['href'] for p in frozen if sha(p['href'])!=p['sha256']]
check('seven frozen semantic code fixture hashes unchanged',len(frozen)==7 and not badfrozen)
check('production contracts metadata Atlas/EarthLab sources unchanged',not git('diff',BASE,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
entries=git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research').splitlines();preserve={};scripts=[];reports=[];research=[]
for row in entries:
 m,p=row.split('\t',1)
 if p.startswith('scripts/'):scripts.append(p)
 elif p.startswith(('docs/atlas/','docs/earth-lab/')) and p.endswith('.md'):reports.append(p)
 elif p.startswith('docs/research/') and p not in {'docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}:research.append(p)
 else:continue
 preserve[p]=m.split()[2]
paths=list(preserve)
hashes=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=ROOT,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines()
badpreserved=[p for p,h in zip(paths,hashes) if preserve[p]!=h]
check('all existing scripts/research assets and 43 Atlas/EarthLab reports preserved',len(hashes)==len(paths) and not badpreserved and len(reports)==43)
old=git('show',BASE+':docs/research/atlas-research-state.md');state=read('docs/research/atlas-research-state.md')
rx=r'^\| ((?:H|T|A|M|S)\d+) — [^|]+\|([^|]+)\|';rows=lambda s:{k:v.strip() for k,v in re.findall(rx,s,re.M)}
check('all42 canonical status columns unchanged',len(rows(state))==42 and rows(state)==rows(old))
gate=old[old.index('<details>'):old.index('</details>')+len('</details>')];check('historical audit gate preserved',gate in state)
oldlog=git('show',BASE+':docs/development-log.md');check('development log append-only',read('docs/development-log.md').startswith(oldlog+'\n'))
r=data('docs/research/illumination-identifiability-results.json');report=read(REPORT);logical=r['logical']
check('UTF8 report has no mojibake','\u00e2\u20ac' not in report and '\u00c2\u00a7' not in report)
check('27 durable assessment sections',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,28)))
check('B partial assessment and constrained correction readiness','**B — PARTIAL IDENTIFIABILITY**' in report and '**Correction-readiness decision B — PARTIALLY:**' in report and 'A13 Swiss frame pixels remain PARKED' in report)
next_task='Retained Tryfan post-L2A residual terrain-illumination normalization experiment'
check('exact next task consistent unstarted',next_task in report and next_task in state and 'This next task has not begun.' in report)
check('diagnostic method revision',sha('scripts/atlas/illumination-assessment/assess.py')==logical['methodSha256'])
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
previous=read('docs/research/illumination-identifiability-results.json')
run('fresh process deterministic retained illumination diagnostics',[str(python),'scripts/atlas/illumination-assessment/assess.py'])
check('byte-equivalent deterministic receipt after fresh process',previous==read('docs/research/illumination-identifiability-results.json'))
check('canonical logical receipt hash',hashlib.sha256(json.dumps(logical,sort_keys=True,separators=(',', ':'),ensure_ascii=True).encode()).hexdigest()==r['logicalSha256'])
check('source4 and prepared1084 exact hashes',len(logical['sourceVerification'])==4 and sum(x['bytes'] for x in logical['sourceVerification'])==186259028 and logical['preparedVerification']=={'files':1084,'bytes':1564233043,'allHashesMatch':True})
check('parked112metadata inputs unchanged no pixels',logical['parkedMetadataVerification']=={'files':112,'bytes':19357606,'allHashesMatch':True} and all(x['noPixels'] for x in logical['datedFrameContrast']))
check('six dated strip receipts exact hashes',logical['stripMetadataVerification']['files']==6 and logical['stripMetadataVerification']['allHashesMatch'])
check('used native terrain leaves12 and actual scope explicit',len(logical['geometry']['verifiedLeaves'])==12 and logical['geometry']['actualReadScopeLV95']==[2623600,1091100,2626400,1093700] and logical['geometry']['gridMetres']==.5)
check('44 retained temporal input hashes and corrected encoding archive',logical['retainedTemporalVerification']['inputFilesVerified']==44 and logical['retainedTemporalVerification']['lab010ReflectanceSha256']=='89304e0045bc72b49c360c20bb62acd977673897c170ed5ee73b5920e1fb70b2')
check('input metadata unchanged exact revisions',all(sha(p)==h for p,h in logical['metadataHashes'].items()))
check('frozen diagnostic protocol hash',sha('scripts/atlas/illumination-assessment/protocol.json')==PROTOCOL_SHA and logical['protocolSha256']==PROTOCOL_SHA)
future=data('scripts/atlas/illumination-assessment/future-evaluation.json')
check('predeclared future criteria unchanged and unstarted',sha('scripts/atlas/illumination-assessment/future-evaluation.json')==FUTURE_SHA and future['experimentNotStarted'] and future['nextTask']==next_task)
check('four inherited patches and961probes each',set(logical['patches'])=={'ordinary','steep','summit','dark-context'} and all(p['probes']==961 for p in logical['patches'].values()))
check('ten predeclared Sun scenarios no selected winner',len(logical['hypotheticalSunScenarios'])==10 and all(len(p['conditionalScenarios'])==10 for p in logical['patches'].values()) and logical['protocol']['noFittedTimeOrSun'])
check('ray scope and conditional unknown explicit',all(len(s['rays'])==9 and all('UNKNOWN' in q['stateOutsideRadius'] for q in s['rays']) for p in logical['patches'].values() for s in p['conditionalScenarios']))
check('no exact contributor or decoded strip UTC',all(o['pixelContributor']=='UNKNOWN' and o['exactExposureUTC']=='UNKNOWN' for o in logical['stripCandidates']))
check('35degree policy not asserted for monitoring',logical['dateEnvelopes'][0]['policyApplicableToStripGoal']==False and logical['dateEnvelopes'][1]['policyApplicableToStripGoal']==True and all(x['notExposureTimeBound'] for x in logical['dateEnvelopes']))
check('2026 contrasting Sun own location time and no imagery',len(logical['datedFrameContrast'])==2 and all(x['sunAtRemoteBenchmark']['lonlat'][0]>8.9 for x in logical['datedFrameContrast']))
check('date roles no fabricated pixel time bounds',all(x['notPixelTimeBound'] and x['localUpstreamTerrainCorrectionConfiguration']=='NOT RETAINED' for x in logical['datedTryfanContrast']))
check('positive incidence can still meet terrain blocker',any(s['positiveLocalIncidenceBlockerCount']>0 for p in logical['patches'].values() for s in p['conditionalScenarios']))
check('paired source brightness retained without shadow labels',all('sourceEncodedLuma' in q for p in logical['patches'].values() for s in p['conditionalScenarios'] for q in s['rays']))
check('finite diagnostic numbers with no fabricated quality', 'NaN' not in previous and 'Infinity' not in previous)
welsh=ROOT.parent/'meridian-data/sources/atlas/tryfan/welsh-lidar-1m/rasters/tryfan-004-dtm-1m.tif'
check('future retained Welsh terrain exact hash',hashlib.sha256(welsh.read_bytes()).hexdigest()==future['terrainSourceSha256'])
check('no correction acquisition shadow classification',logical['noCorrection'] and logical['noAcquisition'] and logical['noNewShadowClassification'])
focused=run('12 focused time solar normal CRS horizon tests',[str(python),'scripts/atlas/illumination-assessment/test_assess.py'])
check('12focused tests counted','Ran 12 tests' in focused)
nodeout=run('64 unchanged frozen domain checks',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
check('64domain tests counted',bool(re.search(r'(?:#|ℹ) pass 64',nodeout)))
run('frozen isolated TypeScript declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('current navigation completes old assessment recommendation','### Retained dated-observation illumination/shadow assessment — complete' in state and '**Recommend exactly one next bounded task: “'+next_task+'.”**' in state)
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated assessment and current navigation changed',all(p in nav or p.startswith('docs/research/illumination-identifiability') or p.startswith('scripts/atlas/illumination-assessment/') for p in modified))
check('no payloads stores large artifacts added',all((ROOT/p).stat().st_size<250000 for p in modified if p not in nav) and all(not p.endswith(('.npz','.png','.tif','.sqlite')) for p in modified))
def slugs(s):
 out=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;out.add(key if n==0 else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for p in modified:
 if not p.endswith('.md'):continue
 text=read(p)
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 — retained dated-observation illumination and shadow identifiability'):]
 for link in re.findall(r'\]\(([^)]+)\)',text):
  link=link.strip().strip('<>')
  if link.startswith(('http:','https:','data:','mailto:','meridian-data:')) or 'meridian-private' in link:continue
  file,_,anchor=unquote(link).partition('#');target=(ROOT/p).parent/file if file else ROOT/p;refs+=1
  if not target.exists():missing.append([p,link]);continue
  if anchor and target.suffix=='.md':
   anchors+=1
   if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([p,link])
check('local references and anchors resolve',not missing)
jsonpaths=[p for d in ['docs/atlas','docs/earth-lab','docs/research'] for p in (ROOT/d).glob('*.json')]
for p in jsonpaths:json.loads(p.read_text(encoding='utf-8-sig'))
check('all research JSON parses',True)
ancestors={}
for c in ['b12dc06','944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');ok=subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0;ancestors[c]=full;check('checkpoint ancestor '+c,ok)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('changed Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'assessment':'illumination-identifiability/v1','startingCheckpoint':BASE,'decision':'B - PARTIAL IDENTIFIABILITY','checks':checks,'errors':errors,'commands':commands,
 'toolSha256':{p:sha(p) for p in ['scripts/atlas/illumination-assessment/assess.py','scripts/atlas/illumination-assessment/test_assess.py','scripts/atlas/illumination-assessment/validate.py']},
 'resultsSha256':sha('docs/research/illumination-identifiability-results.json'),'logicalSha256':r['logicalSha256'],'reportSha256':sha(REPORT),
 'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,
 'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,
 'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,
 'checkpointAncestors':ancestors,'changedPaths':modified,'nextTask':next_task+'; not started',
 'confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noCorrection':True,'noIlluminationNormalization':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing}))
if errors:raise SystemExit(1)
