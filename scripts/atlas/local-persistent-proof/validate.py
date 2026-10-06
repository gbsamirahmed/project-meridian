"""Local persistence proof validation; no acquisition, no retained source mutation.
Run before commit/push with retained data environment. Writes only a small receipt.
"""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
BASE='3c143ebea99ce366a1b00083f64a4ee11149a1e0'
REPORT='docs/research/tryfan-local-persistent-proof.md';OUT='docs/research/tryfan-local-persistent-validation.json'
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
 return r.stdout
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
r=data('docs/research/tryfan-local-persistent-results.json');report=read(REPORT)
check('27 report sections present',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,28)))
check('exactly one next native binding task consistent and not begun','**Retained Tryfan WorldCover native-raster binding and qualified semantic-query proof.**' in report and 'Retained Tryfan WorldCover native-raster binding and qualified semantic-query proof' in state and 'This next task has not begun.' in report)
check('bounded success and appearance remains unresolved parked','**C — SUCCESS.**' in report and 'A13 Swiss frame pixels remain **PARKED**' in report and 'Whole-metadata rewrite' in report)
check('measurement wrapper and original plan hashes match',all(sha(p)==h for p,h in r['methods'].items()) and sha('docs/research/tryfan-local-persistent-plan.json')==r['planSha256'])
check('4 initial6 final,2 recomputed2 unaffected and nine real acceptance processes',r['initialCounts']['derivations']==4 and r['counts']['derivations']==6 and r['changedDerivations']==2 and r['preservedDerivations']==2 and r['realProcesses']==9 and r['rebuiltEquivalent'])
check('crash before publication, retry reuse and normal full snapshot write recorded',r['measures']['interrupted']['exitCode']==73 and not r['retryPublication']['snapshotWritten'] and r['normalRebuildPublication']['snapshotWritten'])
external=Path(r['proofDirectory']);external.relative_to((ROOT.parent/'meridian-data'/'derived/atlas/tryfan/local-persistent-proof-v1').resolve())
pointer=json.loads((external/'accepted/current.json').read_text());body=(external/'accepted/snapshots'/(pointer['snapshot']+'.json')).read_bytes();s=json.loads(body)
check('accepted snapshot content hash and counts match receipt',hashlib.sha256(body).hexdigest()==r['logical']['updated']==pointer['snapshot'] and len(s['derivations'])==6 and len(s['roots'])==3)
check('no raster/nine-height/freshness buffers persisted',all('heightSamplesM' not in root for root in s['roots']) and '"freshness"' not in body.decode('utf-8'))
check('accepted store bytes match physical files',sum((external/'accepted/snapshots'/p['name']).stat().st_size for p in r['snapshots'])+(external/'accepted/current.json').stat().st_size==r['storeBytes']==234282)
check('four historical AWS contexts retained and unknown gap not zero',len(r['logical']['history'])==4 and r['logical']['unknown']['kind']=='gap' and r['logical']['unknown']['reason']=='unsupported' and r['logical']['unavailable']['status']=='unavailable')
# Asset/source verification and true fresh-process rebuild/replay occur in these tests.
testout=run('99 tests:18 persistence17 original proof64 frozen contract/domain',['node','--test','scripts/atlas/test_local_persistent_tryfan.mjs','scripts/atlas/test_qualified_query_proof.mjs','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
check('all99 tests counted',bool(re.search(r'(?:#|ℹ) pass 99',testout)))
mjs=['scripts/atlas/local-persistent-proof/'+p for p in ['store.mjs','runtime.mjs','cli.mjs','run-proof.mjs']]+['scripts/atlas/test_local_persistent_tryfan.mjs']
run('focused new JavaScript lint',['npx.cmd','eslint','--no-config-lookup','--rule','no-unused-vars:error','--rule','no-unreachable:error',*mjs])
for p in mjs:run('script syntax '+p,['node','--check',p])
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only new isolated proof and current navigation changed',all(p in nav or p.startswith('docs/research/tryfan-local-persistent-') or p.startswith('scripts/atlas/local-persistent-proof/') or p=='scripts/atlas/test_local_persistent_tryfan.mjs' for p in modified))
check('no store runtime payloads/large files tracked',all((ROOT/p).stat().st_size<100000 for p in modified if p not in nav) and all('/snapshots/' not in p and not p.endswith('current.json') for p in modified))
def slugs(s):
 out=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;out.add(key if n==0 else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for p in modified:
 if not p.endswith('.md'):continue
 text=read(p)
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-06 — local persistent retained Tryfan world-model proof'):]
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
for c in ['3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');ok=subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0;ancestors[c]=full;check('checkpoint ancestor '+c,ok)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('changed Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'proof':'tryfan-local-persistent-proof/v1','date':'2026-10-06','startingCheckpoint':BASE,'branch':'main','upstream':'origin/main','fetchedStartingDivergence':[0,0],'decision':'C — SUCCESS; bounded local proof, not production','checks':checks,'errors':errors,'commands':commands,'resultsSha256':sha('docs/research/tryfan-local-persistent-results.json'),'logicalSha256':r['logicalSha256'],'reportSha256':sha(REPORT),'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,'researchJsonChecked':len(jsonpaths),'checkpointAncestors':ancestors,'changedPaths':modified,'nextTask':'Retained Tryfan WorldCover native-raster binding and qualified semantic-query proof; not started','scopeConfirmations':{'noNewAcquisition':True,'noTerrainPayloadCopy':True,'retainedProductsUnchanged':True,'noPrivateInspection':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noCloudDatabaseServices':True,'noInferenceHydrology':True},'limits':'Single writer, whole metadata snapshot rewrite, no power-loss/multiwriter/load/temporal-state/production throughput guarantee.'}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing,'logicalSha':r['logicalSha256']}))
if errors:raise SystemExit(1)
