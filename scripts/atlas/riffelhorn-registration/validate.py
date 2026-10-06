"""Registration assessment checks; prior research and source products stay read-only."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3]
BASE='1842008ea4996d941226a428aa20aba7dec8fd5e'
PREFIX='riffelhorn-registration-epoch'
OUT=f'docs/research/{PREFIX}-validation.json'
REPORT=f'docs/research/{PREFIX}.md'
PROTOCOL='scripts/atlas/illumination-assessment/future-evaluation.json'
PROTOCOL_SHA='0e1b884bd64c94effffeb1cb024f01c6f385d87eda73f20fa134f0a2add5ca28'
NEXT='Retained Tryfan vegetation-only residual-normalization protocol assessment'
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
check('explicit scale conditional decision and next','**B - SCALE-CONDITIONAL CONSISTENCY' in report and NEXT in report and 'This next task has not begun.' in report)
check('no mojibake','\u00e2\u20ac' not in report and '\u00c2\u00a7' not in report)
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
artifacts=[f'docs/research/{PREFIX}{s}' for s in ['-results.json','-patches.png','-search.png']]
before={p:sha(p) for p in artifacts}
run('fresh process deterministic diagnostics',[str(python),'scripts/atlas/riffelhorn-registration/assess.py'])
check('byte identical metrics and PNG rerun',before=={p:sha(p) for p in artifacts})
r=data(artifacts[0]);audit=r['coordinateAudit'];plan=data('scripts/atlas/riffelhorn-registration/plan.json');initial=data('scripts/atlas/riffelhorn-registration/initial-plan.json')
check('diagnostic plan scope and explicit numerical correction',initial['beforeResults'] and not plan['beforeResults'] and plan['fixedScopeBeforeResults'] and initial['haloMetres']==6 and plan['haloMetres']==10 and plan['implementationCorrection']['previousPlanSha256']==sha('scripts/atlas/riffelhorn-registration/initial-plan.json') and plan['patches']==initial['patches'])
check('method and plan exact reference',r['methodSha256']==sha('scripts/atlas/riffelhorn-registration/assess.py') and r['planSha256']==sha('scripts/atlas/riffelhorn-registration/plan.json'))
check('four inherited patches',[r['patches'][k]['centreEPSG2056']+ [r['patches'][k]['sizeMetres']] for k in plan['patches']]==list(plan['patches'].values()))
check('all central cells retained',sum(p['cells'] for p in r['patches'].values())==208800)
check('actual read scopes preserved',all(p['actualReadBoundsEPSG2056']==[p['centreEPSG2056'][0]-p['sizeMetres']/2-10,p['centreEPSG2056'][1]-p['sizeMetres']/2-10,p['centreEPSG2056'][0]+p['sizeMetres']/2+10,p['centreEPSG2056'][1]+p['sizeMetres']/2+10] for p in r['patches'].values()))
check('native area pixels and local terrain grids',len(audit['sourceGrids'])==4 and len(audit['nativeLocalTerrainGrids'])==4 and all(g['crs']=='EPSG:2056' and g['areaOrPoint']=='Area' for g in audit['sourceGrids']+audit['nativeLocalTerrainGrids']))
check('native pixel sizes and expected centres',all(g['transform'][0]==.1 for g in audit['sourceGrids']) and all(g['transform'][0]==.5 for g in audit['nativeLocalTerrainGrids']) and audit['nativeCellCentreDifferenceMetres']==[.2,-.2])
check('centred coordinate checks below1cm not source accuracy',audit['maxCRSRoundtripMetres']<.01 and audit['coordinateRampMaxNativeMetres']<.01 and audit['maxIndependentXYZCentreErrorMercatorMetres']<1e-7 and audit['operationStatedAccuracyMetres']==1)
check('all four imagery fields exactly regenerated',len(audit['z18FieldRegeneration'])==4 and all(x['maxAbsoluteFieldDifference']==0 for x in audit['z18FieldRegeneration']))
check('native terrain sample equivalence to quantized delivery',len(audit['terrainZ18NativeBilinearChecks'])==4 and all(x['samples']==81 and x['maxAbsoluteHeightDifferenceMetres']<.003 and x['notHorizontalRegistrationAccuracy'] for x in audit['terrainZ18NativeBilinearChecks']))
check('forty scoped diagnostic searches not physical shifts',sum(len(v) for p in r['patches'].values() for v in p['proxies'].values())==40 and all(v['notGeospatialShift'] for p in r['patches'].values() for rows in p['proxies'].values() for v in rows.values()))
check('coarse method precise provenance',r['terrainProductRevision']['status']=='known' and r['terrainProductRevision']['value']=='1a44a0644de1bde73a3ba84d1b761dc0aa17d48cc971e5f6b5d2c14fb329d7ea' and r['imageryProductIdentity']=='f6edd630206ed02f255176935d72126cbc6ad7987b12d2986edbe6d05619bc1b')
check('no accepted shift or source-state inference',r['noTrueLocalShiftEstimated'] and r['noWarpOrCorrection'] and r['pixelEpochsAndOriginalOrthoRevisionUnknown'] and not audit['verticalTransformationPerformed'])
check('retained metadata unchanged',all(sha(p)==h for p,h in r['readOnlyMetadataSha256'].items()))
source_verified=r['inputVerification'];sources=[x for x in source_verified if x['role'].startswith('source-')]
check('four image and100 terrain sources verified',len(sources)==104 and sum(x['bytes'] for x in sources if x['role']=='source-image')==186259028 and sum(x['bytes'] for x in sources if x['role']=='source-terrain')==1667166026)
check('1084 imagery and11429 terrain payloads verified',[x['files'] for x in source_verified if x['role'].startswith('prepared-')]==[1084,11429])
check('retained official documents verified',len([x for x in source_verified if x['role']=='retained-document'])==2)
check('height coupling explicitly hypothetical',len(r['heightHorizontalCouplingHypothetical'])==9 and r['heightHorizontalCouplingHypothetical'][0]['heightDifferenceMetres']==.3)
testout=run('18 focused numerical safeguards',[str(python),'scripts/atlas/riffelhorn-registration/test_assess.py']);check('18 tests counted','Ran 18 tests' in testout)
nodeout=run('64 frozen domain tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']);check('64 tests counted',bool(re.search(r'(?:#|\u2139) pass 64',nodeout)))
run('frozen isolated declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('canonical next assessment explicit', '**Recommend exactly one next bounded task: '+NEXT+'.**' in state and '### Retained Riffelhorn registration and epoch assessment - complete' in state)
for p in ['docs/architecture.md','docs/product-direction.md','docs/research/atlas-research-map.md']:
 check('current navigation '+p,NEXT in re.sub(r'\s+',' ',read(p)) and 'B - SCALE-CONDITIONAL CONSISTENCY' in re.sub(r'\s+',' ',read(p)))
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated assessment and navigation',all(p in nav or p.startswith('docs/research/'+PREFIX) or p.startswith('scripts/atlas/riffelhorn-registration/') for p in modified))
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
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-07 - retained Riffelhorn imagery-terrain registration and epoch consistency'):]
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
for c in ['1842008','9695757','b12dc06','944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');check('checkpoint ancestor '+c,subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))

receipt={'assessment':'riffelhorn-registration-epoch/v2','startingCheckpoint':BASE,'decision':'B - SCALE-CONDITIONAL CONSISTENCY','checks':checks,'errors':errors,'commands':commands,'localElapsedTimesNotPerformancePromises':True,'artifactSha256':before,'codeSha256':{p:sha(p) for p in modified if p.startswith('scripts/atlas/riffelhorn-registration/')},'reportSha256':sha(REPORT),'frozenProtocolSha256':sha(PROTOCOL),'sourceVerification':source_verified,'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'changedPaths':modified,'nextTask':NEXT+'; not started','confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noWarpOrCorrection':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing},ensure_ascii=True))
if errors:raise SystemExit(1)
