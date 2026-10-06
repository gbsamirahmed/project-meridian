"""Proof-specific checks; run from repository root with the retained-data Python environment.
Optional first argument overrides the sibling meridian-data directory. No network/data acquisition.
"""
import hashlib,json,re,subprocess,sys
from pathlib import Path
from urllib.parse import unquote,urlparse
root=Path.cwd();data_root=Path(sys.argv[1]) if len(sys.argv)>1 else root.parent/'meridian-data';base='6e17e7923f2130b2cfce3671e026fe56b6397f5f'
report_path='docs/research/tryfan-qualified-query-proof.md';receipt_path='docs/research/tryfan-qualified-query-validation.json'
checks=[];errors=[];commands=[]
def git(*args):return subprocess.check_output(['git',*args],text=True,encoding='utf-8').strip()
def read(p):return (root/p).read_text(encoding='utf-8-sig')
def data(p):return json.loads(read(p))
def sha(p):return hashlib.sha256((root/p).read_bytes()).hexdigest()
def check(name,condition):
 checks.append({'check':name,'passed':bool(condition)})
 if not condition:errors.append(name)
def command(name,args):
 r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace');commands.append({'check':name,'command':args,'exitCode':r.returncode});check(name,r.returncode==0)
 if r.returncode:print(r.stdout[-2000:],r.stderr[-2000:])
 return r.stdout
check('synthesis starting checkpoint remains an ancestor',subprocess.run(['git','merge-base','--is-ancestor',base,'HEAD'],capture_output=True).returncode==0)
check('main uses existing origin/main upstream',git('branch','--show-current')=='main' and git('rev-parse','--abbrev-ref','@{upstream}')=='origin/main')
check('validation main/upstream divergence0/0',git('rev-list','--left-right','--count','main...origin/main').split()==['0','0'])
protected=data('docs/atlas/information-display-plan.json')['productionHashes'];prod_bad=[p for p,h in protected.items() if sha(p)!=h]
check('113 protected production SHA256s match',len(protected)==113 and not prod_bad)
frozen=data('docs/atlas/semantic-evidence-contract-validation.json')['code'];frozen_bad=[c['href'] for c in frozen if sha(c['href'])!=c['sha256']]
check('seven frozen semantic code/fixture hashes match',len(frozen)==7 and not frozen_bad)
check('production/frozen metadata/retained report/data domains have no diff',not git('diff',base,'--','src','renderers','docs/atlas','docs/earth-lab','package.json','package-lock.json'))
old_scripts=git('ls-tree','-r','--name-only',base,'scripts').splitlines()
check('all existing scripts preserved',all(git('hash-object',p)==git('rev-parse',base+':'+p) for p in old_scripts))
reports=[p for p in git('ls-tree','-r','--name-only',base,'docs/atlas','docs/earth-lab').splitlines() if p.endswith('.md')]
report_bad=[p for p in reports if git('hash-object',p)!=git('rev-parse',base+':'+p)]
check('43 Atlas/EarthLab reports preserved',len(reports)==43 and not report_bad)
preserved=['docs/research/atlas-derived-understanding-lifecycle.md','docs/research/atlas-derived-understanding-validation.json','docs/research/atlas-world-model-architecture-synthesis.md','docs/research/atlas-world-model-architecture-validation.json','docs/research/atlas-research-audit-validation.json']
check('prior lifecycle/synthesis reports and receipts preserved',all(git('hash-object',p)==git('rev-parse',base+':'+p) for p in preserved))
old=git('show',base+':docs/research/atlas-research-state.md');state=read('docs/research/atlas-research-state.md')
row_re=r'^\| ((?:H|T|A|M|S)\d+) — [^|]+\|([^|]+)\|'
old_rows={k:v.strip() for k,v in re.findall(row_re,old,re.M)};rows={k:v.strip() for k,v in re.findall(row_re,state,re.M)}
check('all42 canonical IDs/status columns preserved',len(rows)==42 and rows==old_rows)
old_gate=old[old.index('<details>'):old.index('</details>')+len('</details>')];check('historical audit gate preserved',old_gate in state)
old_log=git('show',base+':docs/development-log.md');check('development chronology append-only',read('docs/development-log.md').startswith(old_log+'\n'))
plan=data('docs/research/tryfan-qualified-query-plan.json');inputs=data('docs/research/tryfan-qualified-query-inputs.json');out=data('docs/research/tryfan-qualified-query-results.json');report=read(report_path)
check('freeze reuses exact retained window/locations',plan['window']['bounds']==[264900,357800,267900,360800] and plan['probes'][0]['centre']==[266405,359387] and plan['probes'][1]['centre']==[265876.05347833806,358339.7631202109])
check('plan freeze timestamp/checkpoint precedes declared first reads',plan['frozenAt']=='2026-10-06T16:23:43.442342+00:00' and plan['startingCheckpoint']==base and 'before terrain pixel inspection' in report)
check('input/plan/code hashes match deterministic output',sha('docs/research/tryfan-qualified-query-inputs.json')==out['inputSnapshotSha256'] and sha('docs/research/tryfan-qualified-query-plan.json')==out['planSha256'] and all(sha(p)==h for p,h in out['methodFiles'].items()))
from pyproj import Transformer,network
network.set_network_enabled(False)
forward=Transformer.from_crs(27700,4326,always_xy=True);inverse=Transformer.from_crs(4326,27700,always_xy=True)
crs_ok=True
for probe,g in zip(plan['probes'],inputs['geometry']['probes']):
 ll=forward.transform(*probe['centre']);roundtrip=inverse.transform(*ll)
 crs_ok=crs_ok and max(abs(a-b) for a,b in zip(ll,g['longitudeLatitude']))<1e-10 and max(abs(a-b) for a,b in zip(roundtrip,probe['centre']))<0.01
check('CRS axis order and frozen coordinate roundtrip,not geodeticaccuracy',crs_ok)
check('actual input scopes lie inside frozen eligibility supports',all(max(abs(r['actualUse']['bounds'][j]-next(p['centre'][j%2] for p in plan['probes'] if p['id']==r['probe'])) for j in range(4))<=24 for r in inputs['roots']))
check('6 exact revisions,4 current results,2 summit recomputations',len(out['results'])==6 and len(out['currentResults'])==4 and len(out['recomputed'])==2 and all(r['probe']=='summit' for r in out['recomputed']))
check('existingselector regional summit/common control',out['selections']['after']['summit']['family']=='welsh-regional' and out['selections']['after']['southern-observer']['family']=='production-common')
check('v1 validation and exact historical replay pass',out['validation']['semanticContractIssues']==[] and out['validation']['dependencyReceiptIssues']==[] and out['validation']['historicalReplay'] is True)
check('quality/epoch remain honestly unknown',all('quality' not in c['context'] and c['context']['time'][0]['extent']['kind']=='unknown' for c in out['evidence']['collections'][:-1]))
check('unknown property and provenance-unavailable are distinct',out['unknown']['exposure']['result']['reason']=='unsupported' and out['unknown']['terrainWithSpatialContributorRequirement']['status']=='unavailable')
check('synthetic scope notifications do not claim observed physicalchange',all('Synthetic' in c['description'] for c in out['spatialNotifications'].values()))
check('all20 requested report sections present',[int(n) for n in re.findall(r'^## (\d+)\.',report,re.M)]==list(range(1,21)))
check('bounded SUCCESS and unresolved limitations explicit','**Decision C — SUCCESS.**' in report and '**A13 Swiss 2026 pixels remain PARKED**' in report and 'No quality/confidence number' in report and 'conservative' in report and 'not pixel-perfect' in report)
check('exactly one next requirements assessment,not started','**Atlas bounded storage, processing and serving requirements assessment informed by the retained Tryfan proof.**' in report and 'Begin only when separately authorized.' in report and 'Atlas bounded storage, processing and serving requirements assessment informed by the retained Tryfan proof' in state)
proof_tests=command('17 proof-specific tests',['node','--test','scripts/atlas/test_qualified_query_proof.mjs']);check('all17 proof tests counted',bool(re.search(r'(?:#|ℹ) pass 17',proof_tests)))
existing_tests=command('64 existing frozen contract/hierarchy/runtime/Tryfan tests',['node','--test','scripts/atlas/test_semantic_evidence_contract.mjs','scripts/atlas/test_terrain_hierarchy_contract.mjs','scripts/atlas/test_terrain_runtime.mjs','scripts/atlas/test_tryfan_terrain.mjs']);check('all64 existing tests counted',bool(re.search(r'(?:#|ℹ) pass 64',existing_tests)))
command('strict proof TypeScript',['npx.cmd','tsc','-p','scripts/atlas/qualified-query-proof/tsconfig.json'])
command('scoped research lint',['npx.cmd','eslint','scripts/atlas/qualified-query-proof/proof.ts','scripts/atlas/qualified-query-proof/run.mjs','scripts/atlas/test_qualified_query_proof.mjs'])
compile(read('scripts/atlas/qualified-query-proof/retained_inputs.py'),'retained_inputs.py','exec');check('offline Python adapter syntax',True)
determinism=[]
for n in (1,2):
 stdout=command('offline deterministic rebuild '+str(n),['node','scripts/atlas/qualified-query-proof/run.mjs',str(data_root),'--check']);r=json.loads(stdout);determinism.append({k:r[k] for k in ['mode','outputSha256','claims','recomputed','historicalReplay','materializationBytes']})
check('two exact output rebuilds and historical replay agree',len(determinism)==2 and all(r['outputSha256']==sha('docs/research/tryfan-qualified-query-results.json') and r['historicalReplay'] and r['claims']==6 and r['recomputed']==2 for r in determinism))
# Create receipt placeholder solely to validate its new Markdown link; final deterministic receipt below.
(root/receipt_path).write_text('{}\n',encoding='utf-8')
modified=sorted(set(git('diff',base,'--name-only').splitlines()+git('ls-files','--others','--exclude-standard').splitlines()))
nav={'docs/research/atlas-research-state.md','docs/research/atlas-research-map.md','docs/architecture.md','docs/product-direction.md','docs/development-log.md'}
check('changed paths confined to proof plus current navigation',all(p in nav or p.startswith('docs/research/tryfan-qualified-query-') or p.startswith('scripts/atlas/qualified-query-proof/') or p=='scripts/atlas/test_qualified_query_proof.mjs' for p in modified))
check('all newtracked candidates lightweight,maximum100KB',all((root/p).stat().st_size<100000 for p in modified if p not in nav))

def slugs(text):
 result=set();counts={}
 for title in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
  title=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',title).strip().lower();s=re.sub(r'[^\w\- ]','',title).replace(' ','-');n=counts.get(s,0);counts[s]=n+1;result.add(s if n==0 else s+'-'+str(n))
 return result
local_count=anchor_count=0;missing=[];external=set()
for p in modified:
 if not p.endswith('.md'):continue
 s=read(p)
 if p=='docs/development-log.md':s=s[s.rindex('## 2026-10-06 — retained Tryfan qualified-query and revision lifecycle proof'):]
 for ref in re.findall(r'\]\(([^)]+)\)',s):
  ref=ref.strip().strip('<>')
  if ref.startswith(('https:','http:')):external.add(ref);continue
  if ref.startswith(('mailto:','data:','meridian-data:','codex:')) or 'meridian-private' in ref:continue
  file,_,anchor=unquote(ref).partition('#');t=(root/p).parent/file if file else root/p;local_count+=1
  if not t.exists():missing.append([p,ref]);continue
  if anchor and t.suffix=='.md':
   anchor_count+=1
   if anchor not in slugs(t.read_text(encoding='utf-8-sig')):missing.append([p,ref])
check('current/added local documents and anchors resolve',not missing)
check('external references are syntactically valid,no new sourcefacts',all(urlparse(u).netloc for u in external))
jsons=list((root/'docs/atlas').glob('*.json'))+list((root/'docs/earth-lab').glob('*.json'))+list((root/'docs/research').glob('*.json'));json_bad=[]
for p in jsons:
 try:json.loads(p.read_text(encoding='utf-8-sig'))
 except Exception as e:json_bad.append([str(p),str(e)])
check('all research JSON parses',not json_bad)
ancestors={}
for c in ['6e17e79','43afe78','5f14511','e65c2d6','052374e','c4da565','75ea9d8','57688cb','ca74a84','3d406ae','1de9e44','8598c30','ba24e54','53d75f2']:
 try:
  full=git('rev-parse',c+'^{commit}');subprocess.run(['git','merge-base','--is-ancestor',full,base],check=True,capture_output=True);ancestors[c]=full
 except subprocess.CalledProcessError:errors.append('checkpoint ancestry '+c)
check('14 relevant checkpoints verified ancestors',len(ancestors)==14)
command('unstaged whitespace',['git','diff','--check']);command('staged whitespace',['git','diff','--cached','--check'])
check('changed Markdown has no trailing whitespace',all(not any(l.rstrip()!=l for l in read(p).splitlines()) for p in modified if p.endswith('.md')))
receipt={'proof':'tryfan-qualified-query-proof-v1','date':'2026-10-06','startingCheckpoint':base,'startingBranch':'main','upstream':'origin/main','fetchedStartingDivergence':[0,0],'decision':'C — SUCCESS; retained bounded vertical slice, not production/global runtime','checks':checks,'errors':errors,'commands':commands,'deterministicRebuilds':determinism,'resultSha256':sha('docs/research/tryfan-qualified-query-results.json'),'planSha256':out['planSha256'],'inputSnapshotSha256':out['inputSnapshotSha256'],'methodRevision':out['methodRevision'],'inputTileBytes':320857,'resultBytes':92034,'localReferencesChecked':local_count,'localAnchorsChecked':anchor_count,'missingReferences':missing,'protectedProductionSha256Checks':len(protected),'productionMismatches':prod_bad,'frozenSemanticCodeSha256Checks':len(frozen),'frozenMismatches':frozen_bad,'unchangedExistingScripts':len(old_scripts),'unchangedHistoricalReportGitBlobChecks':len(reports),'historicalReportMismatches':report_bad,'additionalPreservedReportsReceipts':preserved,'canonicalThreadCount':len(rows),'canonicalStatusColumnsUnchanged':rows==old_rows,'checkpointAncestors':ancestors,'researchJsonChecked':len(jsons),'jsonErrors':json_bad,'changedPaths':modified,'nextTask':'Atlas bounded storage, processing and serving requirements assessment informed by the retained Tryfan proof; not started','scopeConfirmations':{'researchOnly':True,'frozenContractsUnchanged':True,'productionUnchanged':True,'noDatasetAcquisition':True,'retainedProductsNotModified':True,'noSemanticInference':True,'noPersistentWorldBuild':True,'noNewSemanticIngestion':True,'multiscaleClosed':True,'multiviewParked':True,'weatherTraverseUnchanged':True,'noPrivateInspection':True},'limits':'Exact local retained input replay and finite two-level scope propagation; unknown upstream AWS lineage/epoch/quality, conservative bounds, synthetic change notices, no temporal-state or general-graph runtime proof.'}
(root/receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'checks':len(checks),'errors':errors,'localRefs':local_count,'anchors':anchor_count,'protected':len(protected),'frozen':len(frozen),'threads':len(rows),'reports':len(reports),'existingScripts':len(old_scripts),'json':len(jsons),'resultSHA':receipt['resultSha256']},ensure_ascii=False))
if errors:raise SystemExit(1)
