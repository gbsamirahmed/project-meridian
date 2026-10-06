"""Focused documentation/integrity validation. No acquisition or payload writes.
Run from repository root before committing/pushing; records a lightweight receipt.
"""
from pathlib import Path
from urllib.parse import unquote,urlparse
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
BASE='1c2d10e522f54e60f83bae2e416008bd1a241eb1'
REPORT='docs/research/atlas-storage-processing-serving-requirements.md'
OUT='docs/research/atlas-storage-requirements-validation.json'
CHECKS=[];ERRORS=[];COMMANDS=[]
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def read(p):return (ROOT/p).read_text(encoding='utf-8-sig')
def data(p):return json.loads(read(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def check(label,ok):
 CHECKS.append({'check':label,'passed':bool(ok)})
 if not ok:ERRORS.append(label)
def run(label,args):
 r=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
 COMMANDS.append({'check':label,'command':args,'exitCode':r.returncode});check(label,r.returncode==0)
 if r.returncode:print(r.stdout[-2000:],r.stderr[-2000:])
 return r.stdout
check('expected starting proof checkpoint ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=ROOT,capture_output=True).returncode==0)
check('existing main/origin-main upstream',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main')
check('precommit divergence 0/0',git('rev-list','--left-right','--count','main...origin/main').split()==['0','0'])
protected=data('docs/atlas/information-display-plan.json')['productionHashes'];badprod=[p for p,h in protected.items() if sha(p)!=h]
check('113 protected production hashes unchanged',len(protected)==113 and not badprod)
frozen=data('docs/atlas/semantic-evidence-contract-validation.json')['code'];badfrozen=[r['href'] for r in frozen if sha(r['href'])!=r['sha256']]
check('seven frozen semantic code fixture hashes unchanged',len(frozen)==7 and not badfrozen)
check('production metadata contracts and Atlas-EarthLab evidence domains unchanged',not git('diff',BASE,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
# Git blob checks use one batched hash command, not hundreds of shell processes.
entries=git('ls-tree','-r',BASE,'scripts','docs/atlas','docs/earth-lab','docs/research').splitlines()
preserved={};scripts=[];reports=[];research=[]
for row in entries:
 meta,p=row.split('\t',1);blob=meta.split()[2]
 if p.startswith('scripts/'):scripts.append(p)
 elif p.startswith(('docs/atlas/','docs/earth-lab/')) and p.endswith('.md'):reports.append(p)
 elif p.startswith('docs/research/') and p not in {'docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}:research.append(p)
 else:continue
 preserved[p]=blob
paths=list(preserved)
hashed=subprocess.check_output(['git','hash-object','--stdin-paths'],cwd=ROOT,input='\n'.join(paths)+'\n',text=True,encoding='utf-8').splitlines()
badpreserved=[p for p,h in zip(paths,hashed) if h!=preserved[p]]
check('all existing scripts and historical research assets preserved',len(hashed)==len(paths) and not badpreserved)
check('43 Atlas/EarthLab reports preserved',len(reports)==43)
old=git('show',BASE+':docs/research/atlas-research-state.md');state=read('docs/research/atlas-research-state.md')
regex=r'^\| ((?:H|T|A|M|S)\d+) — [^|]+\|([^|]+)\|'
rows=lambda s:{k:v.strip() for k,v in re.findall(regex,s,re.M)}
check('42 canonical status columns unchanged',len(rows(state))==42 and rows(state)==rows(old))
gate=old[old.index('<details>'):old.index('</details>')+len('</details>')]
check('historical audit gate preserved',gate in state)
oldlog=git('show',BASE+':docs/development-log.md')
check('development log append-only',read('docs/development-log.md').startswith(oldlog+'\n'))
report=read(REPORT)
check('30 required sections present',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,31)))
check('decision C not production architecture selected','**Decision C:' in report and '**D is not supported:**' in report and 'not selected products or deployments' in report)
check('measured estimated hypothetical distinguished',all(x in report for x in ['**measured**','**estimated**','**hypothetical**','not wire traffic','not resident RAM','not a complete total']))
check('appearance and Swiss parked work explicit','A13 Swiss 2026 provisioning remains **PARKED**' in report and 'remain unresolved/partial' in report)
nexttask='implement and evaluate one local persistent retained Tryfan regional world-model proof'
check('one next task consistent and not begun',nexttask.lower() in report.lower() and nexttask.lower() in state.lower() and 'it has not begun' in report.lower())
check('12 persistent proof requirements present',re.findall(r'^\| R(\d+) ',report,re.M)==[str(i) for i in range(1,13)])
for p in ('measure.py','test_measure.py','validate.py'):
 compile(read('scripts/atlas/storage_requirements/'+p),p,'exec')
check('new Python syntax passes',True)
run('six focused inventory mathematical tests',[sys.executable,'scripts/atlas/storage_requirements/test_measure.py'])
rebuilds=[]
for i in range(2):
 s=run('deterministic read-only inventory check '+str(i+1),[sys.executable,'scripts/atlas/storage_requirements/measure.py','--check'])
 try:rebuilds.append(json.loads(s))
 except json.JSONDecodeError:ERRORS.append('inventory response decode')
check('two exact deterministic measurements agree',len(rebuilds)==2 and rebuilds[0]==rebuilds[1] and rebuilds[0]['sha256']==sha('docs/research/atlas-storage-requirements-measurements.json'))
checks=run('64 frozen semantic/hierarchy/runtime/Tryfan tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
check('64 contract domain tests counted',bool(re.search(r'(?:#|ℹ) pass 64',checks)))
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/research/atlas-research-state.md','docs/research/atlas-research-map.md','docs/architecture.md','docs/product-direction.md','docs/development-log.md'}
allowed=nav|{REPORT,OUT,'docs/research/atlas-storage-requirements-measurements.json'}
check('only assessment analysis and current navigation changed',all(p in allowed or p.startswith('scripts/atlas/storage_requirements/') for p in modified))
check('new outputs lightweight maximum 100KB',all((ROOT/p).stat().st_size<100000 for p in modified if p not in nav))
def slugs(s):
 result=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower()
  key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;result.add(key if n==0 else key+'-'+str(n))
 return result
refs=anchors=0;missing=[];external=set()
for p in modified:
 if not p.endswith('.md'):continue
 s=read(p)
 if p=='docs/development-log.md':s=s[s.rindex('## 2026-10-06 — Atlas storage, processing and serving requirements assessment'):]
 for link in re.findall(r'\]\(([^)]+)\)',s):
  link=link.strip().strip('<>')
  if link.startswith(('http:','https:')):external.add(link);continue
  if link.startswith(('mailto:','data:','meridian-data:','codex:')) or 'meridian-private' in link:continue
  name,_,anchor=unquote(link).partition('#');target=(ROOT/p).parent/name if name else ROOT/p;refs+=1
  if not target.exists():missing.append([p,link]);continue
  if anchor and target.suffix=='.md':
   anchors+=1
   if anchor not in slugs(target.read_text(encoding='utf-8-sig')):missing.append([p,link])
check('all added/current local references and anchors resolve',not missing)
check('external documentation links syntactically valid',all(urlparse(u).netloc for u in external))
jsonpaths=[p for d in ('docs/atlas','docs/earth-lab','docs/research') for p in (ROOT/d).glob('*.json')]
for p in jsonpaths:json.loads(p.read_text(encoding='utf-8-sig'))
check('all research JSON parses',True)
ancestors={}
for c in ['1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8','57688cb','ca74a84','3d406ae']:
 full=git('rev-parse',c+'^{commit}');ok=subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0;check('checkpoint ancestor '+c,ok);ancestors[c]=full
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('changed Markdown no trailing whitespace',all(all(l.rstrip()==l for l in read(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'assessment':'atlas-storage-processing-serving-requirements','date':'2026-10-06','startingCheckpoint':BASE,'startingBranch':'main','upstream':'origin/main','fetchedStartingDivergence':[0,0],'decision':'C; bounded local persistent proof can be designed; production stack not selected','checks':CHECKS,'errors':ERRORS,'commands':COMMANDS,'measurementSha256':sha('docs/research/atlas-storage-requirements-measurements.json'),'measurementRechecks':rebuilds,'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'canonicalThreadCount':len(rows(state)),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'externalDocumentationLinks':sorted(external),'researchJsonChecked':len(jsonpaths),'checkpointAncestors':ancestors,'changedPaths':modified,'nextTask':nexttask+'; not started','scopeConfirmations':{'noAcquisition':True,'retainedPayloadsReadOnly':True,'noPrivateInspection':True,'noStorageDatabaseCloudServices':True,'noTechnologySelection':True,'noFrozenContractChanges':True,'noProductionChanges':True,'multiscaleClosed':True,'multiviewParked':True,'weatherTraverseUnchanged':True},'measurementLimits':'Manifest hashes verified and listed payload sizes checked; no fresh payload content rehash, preparation/network/RSS/load benchmark; historical timings and source receipts remain qualified.'}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(CHECKS),'errors':ERRORS,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'researchAssets':len(research),'missing':missing}))
if ERRORS:raise SystemExit(1)
