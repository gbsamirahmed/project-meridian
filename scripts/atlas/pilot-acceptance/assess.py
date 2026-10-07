"""Deterministic evidence-accounting assessment; no scientific model or pilot runtime."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT.parent/'meridian-data'
BASE='4acd1916031d868c9a327d09445b770578f01b79'
MANIFEST='docs/research/atlas-regional-pilot-acceptance.json'
OUT='docs/research/atlas-regional-pilot-acceptance-results.json'
GATES='scripts/atlas/pilot-acceptance/gates.json'
GATES_SHA='fc7a4093d2880495ab5a1b0dc6baf4a63654cb20c24a17ab5e4632fc11d386ef'
REQUIRED_NAMES=['Source identity', 'Product identity', 'Representation identity', 'Provenance', 'Rights/licensing metadata', 'Spatial support', 'Scale/resolution semantics', 'CRS/reference semantics', 'Geometry hierarchy', 'Regional/global fallback', 'Source-native semantics', 'Common interpretation without flattening', 'Feature identity', 'Categorical evidence', 'Continuous/quantity evidence', 'Layered/coexisting claims', 'Contradictory versus merely different claims', 'Observation time', 'Survey time', 'Event time', 'Validity/reference periods', 'Reference-conditioned evidence', 'Unknown', 'Non-detection', 'Unavailable', 'Unsupported', 'Derived-result identity', 'Method/revision identity', 'Dependency identity', 'Actual input-use scope', 'Scoped freshness', 'Recomputation', 'Supersession/coexistence', 'Historical replay', 'Persistence/restart', 'Coherent publication', 'Interrupted-publication behaviour', 'Query resolution by physical question', 'Incompatible fallback rejection', 'Evidence coexistence', 'Dense raster evidence', 'Vector evidence', 'Time-qualified observations', 'Event evidence', 'Scenario/model evidence', 'Appearance evidence identity/provenance', 'Uncertainty/qualification', 'Deterministic rebuild/reproduction', 'Source immutability', 'Separation from application concerns']
CLASSES={'PROVEN','PARTIALLY PROVEN','DESIGNED BUT NOT PROVEN','UNRESOLVED','OUTSIDE PILOT SCOPE'}
THREAD_CLASSES={'PILOT BLOCKER','PILOT NON-BLOCKER / RESEARCH DEBT','PARKED EXTERNAL DEPENDENCY','POST-PILOT RESEARCH','CLOSED'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encode(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git_bytes(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
def canonical_rows(s):
 return {c[1].strip().split(' ')[0]:c[2].strip() for line in s.splitlines() if re.match(r'^\| [HTAMS]\d+ —',line) for c in [line.split('|')]}
def decision(gates,prerequisites,blockers):
 if len(gates)!=9 or any(g['status'] not in {'PASS','CONDITIONAL PASS','FAIL'} for g in gates):raise ValueError('Nine declared gate outcomes required')
 if blockers or any(g['status']=='FAIL' for g in gates):return 'A - NOT READY'
 if prerequisites or any(g['status']=='CONDITIONAL PASS' for g in gates):return 'B - CONDITIONALLY READY'
 return 'C - READY FOR BOUNDED REGIONAL PILOT'
def check_structure(m,protocol,old):
 def require(ok,why):
  if not ok:raise ValueError(why)
 require(m['schema']=='atlas-regional-pilot-admission/v1','Unknown acceptance revision')
 require(m['startingCheckpoint']==BASE and protocol['startingCheckpoint']==BASE,'Wrong evidence baseline')
 require(m['gatesSha256']==GATES_SHA and protocol['frozenBeforeFinalDecision'],'Unfrozen gates')
 ids={p['id']:p for p in m['proofs']};require(len(ids)==len(m['proofs']),'Duplicate proof')
 for p in ids.values():require(p['references'] and p['report']==p['references'][0]['path'] and p['checkpoint'] and p['establishes'],'Incomplete proof identity')
 require([c['id'] for c in m['coverage'][:50]]==['C'+str(i).zfill(2) for i in range(1,51)],'Missing or reordered required capability')
 require([c['capability'] for c in m['coverage'][:50]]==REQUIRED_NAMES,'Required capability name changed')
 require(len(set(c['id'] for c in m['coverage']))==len(m['coverage']),'Duplicate capability')
 for c in m['coverage']:
  require(c['classification'] in CLASSES and c['boundedMeaning'],'Invalid/unqualified coverage')
  require(c['proofs'] and all(p in ids for p in c['proofs']),'Missing retained evidence reference')
  if c['classification']=='PROVEN':require(any(ids[p]['evidenceClass'] in {'retained','fixture'} for p in c['proofs']),'Field/design is not empirical proof')
 historical=canonical_rows(old)
 require(len(historical)==42 and len(m['threads'])==42 and {t['id'] for t in m['threads']}==set(historical),'Missing canonical thread')
 for t in m['threads']:
  require(t['historicalStatus']==historical[t['id']] and t['historicalStatusSha256']==hashlib.sha256(t['historicalStatus'].encode()).hexdigest(),'Historical status altered')
  require(t['pilotClass'] in THREAD_CLASSES and t['reason'] and t['canonicalReferences'],'Thread classification unqualified')
 require(next(t for t in m['threads'] if t['id']=='A13')['pilotClass']=='PARKED EXTERNAL DEPENDENCY','Swiss pixels unparked')
 require([g['id'] for g in m['gates']]==[g['id'] for g in protocol['gates']],'Gate ordering/membership changed')
 for g in m['gates']:require(g['proofs'] and all(p in ids for p in g['proofs']) and g['rationale'] and g['admissionOnly'],'Missing gate evidence/scope')
 require(m['decision']==decision(m['gates'],m['prePilotPrerequisites'],m['architecturalBlockers']),'Inconsistent admission decision')
 blockers=[t['id'] for t in m['threads'] if t['pilotClass']=='PILOT BLOCKER'];require(bool(blockers)==bool(m['architecturalBlockers']),'Blocker accounting mismatch')
 require(not m['nextTaskStarted'] and m['nextTask'],'Next task already begun or missing')
 require(m['pilot']['bounds']==[264900,357800,267900,360800] and m['pilot']['crs']=='EPSG:27700' and m['pilot']['areaKm2']==9,'Changed retained pilot footprint')
 return True

def source_checks():
 groups={};seen={}
 def group(name,root,entries,pathkey='path'):
  entries=list(entries);verified=[]
  for e in entries:
   p=(root/e[pathkey]).resolve();h=digest(p)
   if h!=e['sha256']:raise ValueError('Retained hash mismatch: '+str(p))
   if 'bytes' in e and p.stat().st_size!=e['bytes']:raise ValueError('Retained size mismatch: '+str(p))
   verified.append([str(p.relative_to(DATA)).replace(chr(92),'/'),h,p.stat().st_size]);seen[str(p)]=h
  groups[name]={'files':len(verified),'bytes':sum(v[2] for v in verified),'verifiedEntriesSha256':hashlib.sha256(encode(verified).encode()).hexdigest()}
 q=read(ROOT/'docs/research/tryfan-qualified-query-inputs.json')['sourceChecks'];terrainroot=DATA/'derived/atlas/tryfan/tryfan-welsh-regional-v2'
 group('Tryfan source and pinned common samples',DATA,[{'path':'sources/atlas/tryfan/welsh-lidar-1m/rasters/tryfan-004-dtm-1m.tif','sha256':q['welshSourceSha256']},{'path':str((terrainroot/'manifest.json').relative_to(DATA)),'sha256':q['manifestSha256']}]+[{'path':p,'sha256':h} for p,h in q['selectedTileHashes'].items()])
 group('Welsh prepared terrain',terrainroot,read(terrainroot/'manifest.json')['files'])
 sem=DATA/'derived/atlas/semantic-comparison-v1';s=read(ROOT/'docs/atlas/semantic-comparison-sources.json')
 group('Tryfan native semantic crop and habitat',sem,[e for e in s['files'] if e['file'] in ['tryfan-worldcover.tif','nrw-vegetation-full-features.json']], 'file')
 veg=read(ROOT/'docs/research/tryfan-vegetation-protocol-results.json')['metadata'];group('July native post-L2A RGB and SCL',DATA,veg['inputs'].values())
 natural=read(ROOT/'docs/earth-lab/tryfan-010-observed-natural-colour.json');group('Lab010 existing natural-colour preparation',DATA/'experiments/earth-lab/tryfan-010/observed-natural-colour-v1',natural['products'])
 ar=read(ROOT/'docs/research/riffelhorn-appearance-assessment-results.json')['logical'];app=DATA/'derived/atlas/riffelhorn/riffelhorn-swissimage-baseline-v1'
 group('SWISSIMAGE manifest',DATA,[{'path':str((app/'manifest.json').relative_to(DATA)),'sha256':ar['manifestSha256']}]);am=read(app/'manifest.json');group('SWISSIMAGE source',DATA,am['sources']);group('SWISSIMAGE prepared',app,am['files'])
 parked=read(ROOT/'docs/atlas/swiss-multiview-input-manifest.json')
 if not parked['noAerialPixels']:raise ValueError('Parked frame-pixel assumption changed')
 group('Parked Swiss metadata only',DATA/'experiments/atlas/swiss-alpine-multiview-discovery-v1',parked['files'],'file')
 exe=read(ROOT/'docs/research/exe-water-query-results.json');eroot=DATA/'derived/atlas/water-check-v1'
 group('Pinned Exe sources/documents',eroot,[dict(v,path=k) for k,v in exe['sourceHashes'].items()])
 group('Complete retained Exe directory',eroot,[{'path':k,'sha256':v} for k,v in exe['sourceDirectoryHashes'].items()])
 return {'groups':groups,'uniqueFiles':len(seen),'noWritesOrAcquisition':True}

def assess():
 m=read(ROOT/MANIFEST);protocol=read(ROOT/GATES)
 if digest(ROOT/GATES)!=GATES_SHA:raise ValueError('Frozen gate criteria mutated')
 check_structure(m,protocol,git_bytes('docs/research/atlas-research-state.md').decode('utf-8'))
 checked={}
 for p in m['proofs']:
  subprocess.run(['git','merge-base','--is-ancestor',p['checkpoint'],BASE],cwd=ROOT,check=True,capture_output=True)
  for ref in p['references']:
   # Current canonical navigation changes, while the starting register remains evidence.
   body=git_bytes(ref['path']) if p['id']=='AUDIT' else (ROOT/ref['path']).read_bytes()
   if hashlib.sha256(body).hexdigest()!=ref['sha256']:raise ValueError('Proof reference changed: '+ref['path'])
   checked[ref['path']]=ref['sha256']
   if ref['path'].endswith('-validation.json'):
    receipt=json.loads(body)
    if receipt.get('errors'):raise ValueError('Prior evidence receipt reports errors: '+ref['path'])
 return {'assessment':m['schema'],'startingCheckpoint':BASE,'manifestSha256':digest(ROOT/MANIFEST),'gatesSha256':GATES_SHA,'methodSha256':digest(__file__),'decision':decision(m['gates'],m['prePilotPrerequisites'],m['architecturalBlockers']),'proofCount':len(m['proofs']),'proofReferenceCount':len(checked),'proofReferences':checked,'coverageCount':len(m['coverage']),'requiredCapabilities':50,'coverageClasses':dict(sorted(Counter(c['classification'] for c in m['coverage']).items())),'gateOutcomes':{g['id']:g['status'] for g in m['gates']},'canonicalThreadCount':42,'threadClasses':dict(sorted(Counter(t['pilotClass'] for t in m['threads']).items())),'historicalStatusesSha256':hashlib.sha256(encode({t['id']:t['historicalStatus'] for t in m['threads']}).encode()).hexdigest(),'architecturalBlockers':m['architecturalBlockers'],'prePilotPrerequisites':m['prePilotPrerequisites'],'sources':source_checks(),'nextTask':m['nextTask'],'nextTaskStarted':False,'admissionNotImplementedPilot':True}
if __name__=='__main__':
 value=assess();(ROOT/OUT).write_text(encode(value),encoding='utf-8',newline='\n');print(encode({k:value[k] for k in ['decision','proofCount','coverageCount','coverageClasses','threadClasses','sources']}))
