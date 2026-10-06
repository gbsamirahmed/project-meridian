"""Retained appearance assessment validation; no acquisition, no retained source mutation.
Run before commit/push with retained data environment. Writes only a small receipt.
"""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
BASE='944326b6c6fcbe277e3d71a65c463c6fcecd5960'
REPORT='docs/research/riffelhorn-appearance-assessment.md';OUT='docs/research/riffelhorn-appearance-assessment-validation.json'
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
r=data('docs/research/riffelhorn-appearance-assessment-results.json');report=read(REPORT);logical=r['logical']
check('27 durable assessment sections',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,28)))
check('C success separate from B small eligibility and parked science','**C — SUCCESS**' in report and '**Resolution conclusion B:**' in report and 'A13 Swiss frame pixels remain PARKED' in report)
next_task='Retained dated-observation illumination and shadow identifiability assessment'
check('exact next task consistent unstarted',next_task in report and next_task in state and 'This next task has not begun.' in report)
check('finite evaluator method revision',sha('scripts/atlas/appearance-assessment/assess.py')==r['methodSha256'])
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
previous=read('docs/research/riffelhorn-appearance-assessment-results.json')
run('fresh process deterministic retained metadata reevaluation',[str(python),'scripts/atlas/appearance-assessment/assess.py'])
check('byte-equivalent deterministic receipt after fresh process',previous==read('docs/research/riffelhorn-appearance-assessment-results.json'))
check('canonical logical receipt hash',hashlib.sha256(json.dumps(logical,sort_keys=True,separators=(',', ':'),ensure_ascii=True).encode()).hexdigest()==r['logicalSha256'])
check('pinned retained SWISSIMAGE manifest',logical['manifestSha256']=='3c8b50fb9d7721b678abc46b9450495b417ccafff15d4ee8a67d9d6a3fee4934')
check('four original and1084prepared files all exact hashes',logical['sourceVerification']=={'files':4,'bytes':186259028,'allHashesMatch':True} and logical['preparedVerification']=={'files':1084,'bytes':1564233043,'allHashesMatch':True})
check('parked112metadata inputs unchanged no pixels',logical['parkedMetadataVerification']=={'files':112,'bytes':19357606,'allHashesMatch':True} and logical['noAerialPixels'])
check('retained baseline source metadata preserved',logical['sourceMetadata']==data('docs/atlas/swissimage-source-derived-baseline.json')['source'])
check('metadata receipts exact revisions',all(sha(p)==h for p,h in logical['inputMetadataSha256'].items()))
q={k:v['answer'] for k,v in logical['queries'].items()}
check('ordinary steep parent qualified support and delivery sampling',q['A-ordinary']['representation']['zoom']==16 and q['B-steep']['representation']['zoom']==18 and q['regional-parent']['representation']['zoom']==12 and q['A-ordinary']['revision']==q['regional-parent']['revision'])
check('boundary remains partial rather than supported whole',q['boundary']['kind']=='partial-regional' and q['boundary']['support']['supportedIntersection']==[2624000,1091990,2624010,1092010])
check('physical and current state not ordinary RGB substitute',q['D-physical']['kind']=='unsupported' and not q['D-physical']['ordinaryRGBSubstituted'] and q['current-state']['kind']=='unsupported')
check('2023 geometry unknown not borrowed2026',q['E-geometry']['acquisition']['viewGeometry']=='UNKNOWN' and not q['E-geometry']['geometry2026Substituted'])
check('outside no equivalent automatic fallback',q['C-outside-pinned']['kind']=='outside-support' and q['C-outside-display']['kind']=='conditional-display-service' and not q['C-outside-display']['liveAvailabilityVerified'] and not q['C-outside-display']['equivalentRegionalProvenance'])
check('alpha support independent of tile presence visibility confidence',[x['alpha'] for x in logical['deliveryAlphaChecks']]==[1,1,1,1,0] and logical['deliveryAlphaChecks'][-1]['tile']==logical['deliveryAlphaChecks'][-2]['tile'])
check('F conceptual no fused product',logical['scenarioF']['kind']=='conceptual-only' and not logical['scenarioF']['fusedRepresentationExists'])
focused=run('11 focused eligibility support time identity and CRS tests',[str(python),'scripts/atlas/appearance-assessment/test_assess.py'])
check('11 focused tests counted','Ran 11 tests' in focused)
nodeout=run('64 unchanged frozen domain checks',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
check('64domain tests counted',bool(re.search(r'(?:#|ℹ) pass 64',nodeout)))
run('frozen isolated TypeScript declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
check('current navigation completes old appearance recommendation','**Next bounded task:** separately authorized **Retained Riffelhorn' not in state and '**Recommend exactly one next bounded task: “'+next_task+'.”**' in state)
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only isolated assessment and current navigation changed',all(p in nav or p.startswith('docs/research/riffelhorn-appearance-assessment') or p.startswith('scripts/atlas/appearance-assessment/') for p in modified))
check('no payloads stores large artifacts added',all((ROOT/p).stat().st_size<200000 for p in modified if p not in nav) and all(not p.endswith(('.npz','.png','.tif','.sqlite')) for p in modified))
def slugs(s):
 out=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;out.add(key if n==0 else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for p in modified:
 if not p.endswith('.md'):continue
 text=read(p)
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-06 — retained Riffelhorn appearance identity and qualified-resolution assessment'):]
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
for c in ['944326b','691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');ok=subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0;ancestors[c]=full;check('checkpoint ancestor '+c,ok)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('changed Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'assessment':'riffelhorn-appearance-metadata/v1','startingCheckpoint':BASE,'decision':'C - SUCCESS','checks':checks,'errors':errors,'commands':commands,
 'toolSha256':{p:sha(p) for p in ['scripts/atlas/appearance-assessment/assess.py','scripts/atlas/appearance-assessment/test_assess.py','scripts/atlas/appearance-assessment/validate.py']},
 'resultsSha256':sha('docs/research/riffelhorn-appearance-assessment-results.json'),'logicalSha256':r['logicalSha256'],'reportSha256':sha(REPORT),
 'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,
 'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,
 'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,
 'checkpointAncestors':ancestors,'changedPaths':modified,'nextTask':next_task+'; not started',
 'confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noCorrection':True,'noIlluminationNormalization':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing}))
if errors:raise SystemExit(1)
