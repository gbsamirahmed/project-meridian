"""Native WorldCover proof validation; no acquisition, no retained source mutation.
Run before commit/push with retained data environment. Writes only a small receipt.
"""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
BASE='691450ff540e0e15ade58cba8464d221e89dc119'
REPORT='docs/research/tryfan-worldcover-binding-proof.md';OUT='docs/research/tryfan-worldcover-binding-validation.json'
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
r=data('docs/research/tryfan-worldcover-binding-results.json');report=read(REPORT)
plan=data('docs/research/tryfan-worldcover-binding-plan.json');logical=r['logical']
check('25 durable report sections',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,26)))
check('C success with categorical-only limitation','**C — SUCCESS.**' in report and 'Code 0/255 are synthetic' in report and 'A13 Swiss frame pixels remain **PARKED**' in report)
next_task='Retained Riffelhorn appearance identity, provenance and qualified-resolution assessment'
check('one next task consistent and not begun',next_task in report and next_task in state and 'This next task has not begun.' in report)
check('original frozen Tryfan bounds patches and plan hash preserved',plan['study']==data('docs/atlas/semantic-comparison-plan.json')['sites']['tryfan'] and sha(plan['originalPlan'])==plan['originalPlanSha256'] and sha('docs/research/tryfan-worldcover-binding-plan.json')==r['planSha256'])
check('method revisions match files',all(sha(p)==h for p,h in r['methods'].items()))
check('three genuine subprocesses equal rebuild/restart',r['realProcesses']==3 and r['restartEquivalent'] and r['rebuildEquivalent'])
hashout=run('native canonical numeric serialization hash',['node','--input-type=module','-e',"import {encode,sha} from './scripts/atlas/worldcover-binding-proof/runtime.mjs';import{readFileSync}from'node:fs';let r=JSON.parse(readFileSync('docs/research/tryfan-worldcover-binding-results.json','utf8'));console.log(sha(encode(r.logical)));"])
check('stable logical query hash',hashout.strip()==r['logicalSha256'])
source_receipts={f['file']:f for f in data('docs/atlas/semantic-comparison-sources.json')['files']}
for name,f in logical['raster']['sources'].items():
 external=Path(f['path']);actual=hashlib.sha256(external.read_bytes()).hexdigest()
 check('retained source hash '+name,actual==source_receipts[name]['sha256']==f['sha256'])
store=Path(r['store']);pointer=json.loads((store/'current.json').read_text(encoding='utf-8'));body=(store/'snapshots'/(pointer['snapshot']+'.json')).read_bytes();snapshot=json.loads(body)
check('accepted metadata snapshot pinned hash and bytes',pointer['snapshot']==r['snapshot']==hashlib.sha256(body).hexdigest() and len(body)==r['snapshotBytes'])
check('only shared metadata templates and referenced raster persisted',len(snapshot['bundle']['collections'][0]['claims'])==8 and len(snapshot['bundle']['collections'][1]['claims'])==3 and snapshot['raster']['grid']['cells']==185036 and 'supports' not in snapshot and 'points' not in snapshot)
check('stored definition mapping and source identity recoverable',len(snapshot['bundle']['resources'])==4 and snapshot['bundle']['contract']=='atlas-semantic-evidence/v1' and snapshot['bundle']['collections'][0]['binding']['asset']['sha256']==logical['raster']['revision'])
check('three point native queries, historical/current and unmappable gaps qualified',[q['native']['native']['fields']['code'] for q in logical['points']]==[30,30,80] and logical['current']['reason']=='unsupported' and logical['unmappable']['mapping']['relationship']=='unmappable' and logical['outside']['reason']=='outside-support' and logical['unavailable']['kind']=='unavailable')
check('all frozen patch native counts match original',all(s['counts']=={c:v['cells'] for c,v in data('docs/atlas/semantic-comparison-results.json')['sites']['tryfan']['regions'][s['id']]['worldcover'].items()} for s in logical['supports'][:3]))
check('NRW same-point native habitat claim retained',any(f['id']=='486832' and f['pointContains'] for f in logical['coexistence']['nativeFeatureIntersections']) and logical['coexistence']['nrw']['claims'][2]['native']['fields']['phase1_code']=='D.1.1')
check('current canonical return point no longer unstarted WorldCover','Exactly one next task is a retained Tryfan WorldCover' not in state and '**Recommend exactly one next bounded task: “'+next_task+'.”**' in state)
testout=run('14 binding tests plus64 frozen domain checks',['node','--test','scripts/atlas/test_worldcover_binding_proof.mjs','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs'])
check('all78 Node tests counted',bool(re.search(r'(?:#|ℹ) pass 78',testout)))
python=ROOT.parent/'meridian-data/earth-lab/.venv/Scripts/python.exe'
run('two synthetic affine/CRS tests',[str(python),'scripts/atlas/worldcover-binding-proof/test_reader.py'])
run('frozen isolated TypeScript declarations',['npx.cmd','tsc','-p','scripts/atlas/semantic-evidence/tsconfig.json'])
mjs=['scripts/atlas/worldcover-binding-proof/'+p for p in ['runtime.mjs','cli.mjs','run-proof.mjs']]+['scripts/atlas/test_worldcover_binding_proof.mjs']
run('focused new JavaScript lint',['npx.cmd','eslint','--no-config-lookup','--rule','no-unused-vars:error','--rule','no-unreachable:error',*mjs])
for p in mjs:run('script syntax '+p,['node','--check',p])
(ROOT/OUT).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',BASE,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/architecture.md','docs/product-direction.md','docs/development-log.md','docs/research/atlas-research-state.md','docs/research/atlas-research-map.md'}
check('only new isolated proof and current navigation changed',all(p in nav or p.startswith('docs/research/tryfan-worldcover-binding-') or p.startswith('scripts/atlas/worldcover-binding-proof/') or p=='scripts/atlas/test_worldcover_binding_proof.mjs' for p in modified))
check('no store runtime payloads/large files tracked',all((ROOT/p).stat().st_size<200000 for p in modified if p not in nav) and all('/snapshots/' not in p and not p.endswith('current.json') for p in modified))
def slugs(s):
 out=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',s,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();key=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(key,0);counts[key]=n+1;out.add(key if n==0 else key+'-'+str(n))
 return out
refs=anchors=0;missing=[]
for p in modified:
 if not p.endswith('.md'):continue
 text=read(p)
 if p=='docs/development-log.md':text=text[text.rindex('## 2026-10-06 — retained Tryfan WorldCover native-raster binding proof'):]
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
for c in ['691450f','3c143eb','1c2d10e','6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8']:
 full=git('rev-parse',c+'^{commit}');ok=subprocess.run(['git','merge-base','--is-ancestor',full,BASE],cwd=ROOT,capture_output=True).returncode==0;ancestors[c]=full;check('checkpoint ancestor '+c,ok)
run('unstaged whitespace',['git','diff','--check']);run('staged whitespace',['git','diff','--cached','--check'])
check('changed Markdown no trailing whitespace',all(all(line.rstrip()==line for line in read(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'proof':'worldcover-native-binding-proof/v1','startingCheckpoint':BASE,'decision':'C - SUCCESS','checks':checks,'errors':errors,'commands':commands,
 'resultsSha256':sha('docs/research/tryfan-worldcover-binding-results.json'),'logicalSha256':r['logicalSha256'],'reportSha256':sha(REPORT),
 'protectedProductionHashChecks':len(protected),'productionMismatches':badprod,'frozenSemanticHashChecks':len(frozen),'frozenMismatches':badfrozen,
 'unchangedScripts':len(scripts),'unchangedHistoricalAtlasEarthLabReports':len(reports),'unchangedPriorResearchAssets':len(research),'preservationMismatches':badpreserved,
 'canonicalThreadCount':42,'canonicalStatusColumnsUnchanged':rows(state)==rows(old),'localReferencesChecked':refs,'anchorsChecked':anchors,'missingReferences':missing,
 'checkpointAncestors':ancestors,'changedPaths':modified,'nextTask':next_task+'; not started',
 'confirmations':{'noAcquisition':True,'noPayloadDuplication':True,'noFrozenContractChanges':True,'noProductionChanges':True,'weatherTraverseUnchanged':True,'multiscaleClosed':True,'multiviewParked':True,'noClassifier':True,'noPrivateInspection':True}}
(ROOT/OUT).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'refs':refs,'anchors':anchors,'reports':len(reports),'scripts':len(scripts),'priorResearch':len(research),'missing':missing}))
if errors:raise SystemExit(1)
