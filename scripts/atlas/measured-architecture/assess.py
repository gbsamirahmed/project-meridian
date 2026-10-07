"""Read-only deterministic extraction of accepted receipts; no benchmark or runtime changes."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[3]
OUT=R/'docs/research/atlas-measured-architecture-evidence.json'
BASE='bae7c3e01f03ba91d0d780fedc61593467a022b3'
def read(path):return json.loads((R/path).read_text(encoding='utf-8'))
def encode(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pointer(obj,path):
 for key in path.strip('/').split('/'):
  obj=obj[int(key)] if isinstance(obj,list) else obj[key]
 return obj

def build():
 paths=['docs/research/tryfan-pilot-s6-results.json','docs/research/tryfan-pilot-s6-baseline.json','docs/research/tryfan-pilot-s6-validation.json','docs/research/atlas-storage-requirements-measurements.json','docs/research/tryfan-pilot-s1-results.json','docs/research/tryfan-pilot-s2-results.json','docs/research/tryfan-pilot-s3-results.json']
 r,b,v,old,*_=map(read,paths);rows=[]
 def measured(name,path,qualification='',file=paths[0]):
  rows.append(dict(id=name,classification='MEASURED',value=pointer(read(file),path),evidence=dict(file=file,pointer=path),qualification=qualification))
 measured('registered-inventory','/counts',file=paths[1]);measured('registered-bytes','/sources/bytes',file=paths[1])
 measured('published-generation','/current',file=paths[1]);measured('historical-generations','/history',file=paths[1])
 measured('persistent-classes','/storage','Accepted main store only; source bytes separate; includes unpublished staging diagnostics.')
 measured('acceptance-footprint','/acceptanceStorage','Initial S6 acceptance store only; not a source census, later follow-ups can add files.')
 measured('fresh-process-runs','/fresh','Five runs; warm OS cache, fresh processes, not physically cold disk.')
 measured('machine','/runtime');measured('end-to-end-ms','/endToEndMilliseconds')
 measured('independent-builds','/independentBuilds','Two empty stores, same construction sequence; IDs include administrative parent history.')
 measured('freshness-median-ms','/freshness/median','20 assessments over six retained result revisions.')
 measured('freshness-p95-ms','/freshness/p95')
 measured('replay-ms','/replay/milliseconds','Six exact retained revisions from retained pixels; includes process overhead.')
 measured('pixel-replay','/replay/measurement','Native sampler sub-operation; not full end-to-end replay.')
 measured('historical-query','/independentReproduction/history','Full cold context request versus body read; do not use initial body-only time as latency.')
 measured('independent-reproduction-ms','/independentReproduction/milliseconds','Existing update artifacts can be reused in this second reproduction.')
 measured('node-memory','/independentReproduction/nodeMemory','Observed RSS, not peak or evidence-only memory.')
 measured('python-memory','/independentReproduction/pythonProcessTree','Launcher and actual worker distinct; observed working sets not peak.')
 measured('reader-allocations','/nativeReaderMetrics','Array/bbox/WKB sizes are narrow proxies; process overhead separate.')
 measured('served-assets','/assets','Three explicit responses; no aggregate network/egress claim.')
 measured('delivery-counters','/service/delivery','Only explicit service counters, not total IO.')
 measured('full-query-matrix','/fullWarmMatrix','20 batches, 480 requests, native Q17 missing-file fixture separately tested; raw payload remains external.')
 for key,stats in sorted(r['workload']['warm'].items()):
  for stat in ['median','p95']:
   measured('warm-'+key+'-'+stat,'/workload/warm/'+key+'/'+stat,'20 samples, warm OS cache; no query/byte cache.')
 for i,load in enumerate(r['workload']['controlledLoad']):
  rows.append(dict(id='load-'+str(load['readers']),classification='MEASURED',value={k:x for k,x in load.items() if k!='samples'},evidence=dict(file=paths[0],pointer='/workload/controlledLoad/'+str(i)),qualification='100 TOTAL requests per reader-count workload, one worker; not 100 per individual reader.'))
 for key,u in sorted(r['updates'].items()):
  wanted=['assemblyMilliseconds','validationMilliseconds','publicationMilliseconds','generationBytes','pointerBytes','catalogueBytes','considered','changedArtifacts','reusedArtifacts','retainedBytes','sampling']
  rows.append(dict(id=key+'-publication',classification='MEASURED',value={k:u['metrics'][k] for k in wanted},evidence=dict(file=paths[0],pointer='/updates/'+key+'/metrics'),qualification='Single local observations; applicability updates, zero source bytes revised.'))
  for n in ['recomputed','reused']:
   measured(key+'-'+n,'/updates/'+key+'/logical/'+n)
  rows.append(dict(id=key+'-interruptions',classification='MEASURED',value=[{k:f[k] for k in ['point','exitCode','current','freshService','retainedDiagnostics']} for f in u['failures']],evidence=dict(file=paths[0],pointer='/updates/'+key+'/failures'),qualification='Abrupt subprocess exits, not disk power loss or cloud transaction proof.'))
 measured('larger-retained-payload-counts','/products','Earlier stat/hash-pinned manifest receipt; not new larger-region serving measurements.',paths[3])
 measured('earlier-source-working-sizes','/reportedArchiveAndWorking','Earlier receipt, not additive pilot bytes.',paths[3])
 sample=r['readMeter']['samples'][0];total=sum(x['bytes'] for x in sample['reads'].values())
 assert all(s['reads']==sample['reads'] and s['responseBytes']==sample['responseBytes'] for s in r['readMeter']['samples'])
 rows.append(dict(id='requested-sync-reads',classification='MEASURED',value=dict(reads=sample['reads'],responseBytes=sample['responseBytes'],samples=len(r['readMeter']['samples'])),evidence=dict(file=paths[0],pointer='/readMeter/samples'),qualification=r['readMeter']['limitations']))
 rows.extend([
 dict(id='requested-read-amplification',classification='DERIVED FROM MEASUREMENTS',value=dict(requestedBytes=total,responseBytes=sample['responseBytes'],ratio=total/sample['responseBytes']),inputs=['requested-sync-reads'],formula='sum(read-category bytes) / responseBytes',qualification='Requested synchronous Node bytes only; not disk, total IO, wire traffic, or cost.'),
 dict(id='active-recompute-share',classification='DERIVED FROM MEASUREMENTS',value=len(r['updates']['U1']['logical']['recomputed'])/r['updates']['U1']['metrics']['considered'],inputs=['U1-recomputed','U1-reused'],formula='2 / (2+2)',qualification='Two original chains only; no global fan-out extrapolation.'),
 dict(id='observed-throughput',classification='DERIVED FROM MEASUREMENTS',value=[dict(readers=x['readers'],requestsPerSecond=x['requests']/(x['elapsedMilliseconds']/1000)) for x in r['workload']['controlledLoad']],inputs=['load-1','load-4'],formula='requests / elapsed seconds',qualification='One retained worker/workload, not a production capacity estimate.'),
 dict(id='retained-generation-bytes',classification='DERIVED FROM MEASUREMENTS',value=sum(h['bytes'] for h in b['history']),inputs=['historical-generations'],formula='sum(seven stored generation lengths)',qualification='Metadata only; source/artifact bytes separate.'),
 dict(id='resolution-sensitivity',classification='ESTIMATED',value='Four times native samples when linear spacing halves on an equal fully filled area.',formula='A / r**2',qualification='Illustrative arithmetic only; compression/support/levels/channels and compute excluded.'),
 dict(id='scale-unknowns',classification='UNKNOWN',value=['claim/index growth','multi-region publication','dependency fan-out','many independent revisions','cold physical IO','network RTT and egress','writer concurrency','dynamic cadence','peak scratch','restricted distribution'],qualification='Tryfan did not measure these; no invented throughput, bill or global cardinality.')])
 reports=[f'docs/research/tryfan-pilot-s{i}.md' for i in range(1,7)]+['docs/research/tryfan-regional-pilot-plan.md','docs/research/atlas-regional-pilot-acceptance.md','docs/research/atlas-storage-processing-serving-requirements.md','docs/research/atlas-world-model-architecture-synthesis.md','docs/research/atlas-derived-understanding-lifecycle.md','docs/research/tryfan-local-persistent-proof.md','docs/research/tryfan-qualified-query-proof.md']
 return dict(schema='atlas-measured-architecture-evidence/v1',startingCheckpoint=BASE,scope='Receipt extraction and analysis only; accepted pilot unchanged.',sources={p:digest(R/p) for p in paths+reports},pilotDecision=v['decision'],pilotGates=[dict(name=g['name'],status=g['status']) for g in v['gates']],current=b['current'],baselineCounts=b['counts'],metrics=rows)

def main():
 text=encode(build())
 if '--check' in sys.argv:
  if not OUT.exists() or OUT.read_text(encoding='utf-8')!=text:raise SystemExit('Evidence receipt differs; run explicit extraction.')
  print('deterministic evidence receipt verified')
 else:
  OUT.write_text(text,encoding='utf-8',newline='\n');print('wrote',OUT.name)
if __name__=='__main__':main()
