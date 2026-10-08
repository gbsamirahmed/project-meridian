"""Labelled metadata-only cardinality/reuse control; not a scientific generation store."""
from pathlib import Path
import json,hashlib,time,statistics

def encode(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def measured(callback):
 t=time.perf_counter();value=callback();return dict(value=value,milliseconds=(time.perf_counter()-t)*1000)
def run(plan):
 root=Path(plan['stateRoot'])/'reference-controls';root.mkdir(parents=True,exist_ok=True);rows=[]
 for case in plan['supplement']['cases']:
  folder=root/case['id'];folder.mkdir(exist_ok=True);objects=folder/'objects';objects.mkdir(exist_ok=True)
  refs=[];footprint=0;history=[];changed=round(case['objects']*(1-case['reuse']))
  for generation in range(case['depth']):
   previous=list(refs)
   indices=set(range(changed)) if case['pattern']=='localized' else {i*case['objects']//changed for i in range(changed)}
   for index in range(case['objects']):
    if not generation or index in indices:
     value={'kind':'SYNTHETIC_METADATA_ONLY','source':'synthetic:source','product':'synthetic:product','object':index,'revision':generation,'support':{'cell':index},'qualification':'No scientific evidence or payload; fixed source/result distinction','provenance':{'method':'deterministic-reuse-control/v1','generation':generation}}
     body=encode(value);address=sha(body);file=objects/(address+'.json')
     if file.exists():assert file.read_bytes()==body,'Immutable control object differs'
     else:file.write_bytes(body)
     record={'identity':'synthetic:item:'+str(index),'revision':generation,'metadataSha256':address}
     if generation:refs[index]=record
     else:refs.append(record)
   manifest={'schema':'atlas-generation-scaling-control/v1','synthetic':True,'parent':history[-1] if history else None,'references':refs,'changed':changed if generation else len(refs),'reused':len(refs)-changed if generation else 0}
   body=encode(manifest);address=sha(body);file=folder/(address+'.json')
   if file.exists():assert file.read_bytes()==body,'Immutable control manifest differs'
   else:file.write_bytes(body)
   history.append(address);footprint+=len(body)
  reused=[a for a,b in zip(previous,refs) if a==b]
  def resolve(address):
   body=(folder/(address+'.json')).read_bytes();assert sha(body)==address;manifest=json.loads(body)
   # Full manifest/reference structural inspection; one chosen identity lookup, not ancestry.
   assert all(set(r)=={'identity','revision','metadataSha256'} for r in manifest['references'])
   wanted=manifest['references'][-1];payload=(objects/(wanted['metadataSha256']+'.json')).read_bytes();assert sha(payload)==wanted['metadataSha256']
   return {'manifestReads':1,'recordsInspected':len(manifest['references']),'objectReads':1,'verificationOperations':2,'metadataBytes':len(body)+len(payload),'historyTraversals':0}
  def verify():
   size=0
   for record in reused:
    body=(objects/(record['metadataSha256']+'.json')).read_bytes();assert sha(body)==record['metadataSha256'];size+=len(body)
   return {'reusedRecords':len(reused),'verificationOperations':len(reused),'objectReads':len(reused),'metadataBytes':size,'historyTraversals':0}
  def carry():
   carried=list(refs)
   return {'carriedReferences':len(carried),'hashOperations':0,'historyTraversals':0}
  samples={}
  for mode in plan['supplement']['modes']:
   callback=(lambda:resolve(history[-1])) if mode=='direct-current' else (lambda:resolve(history[0])) if mode=='direct-oldest' else verify if mode=='verify-reused-metadata' else carry if mode=='carry-reference' else (lambda:{'serializedBytes':len(encode(manifest)),'identityHash':sha(encode(manifest)),'entriesInspected':len(refs),'historyTraversals':0})
   values=[measured(callback) for _ in range(plan['supplement']['repetitions'])];samples[mode]={'logical':values[0]['value'],'medianMilliseconds':statistics.median(x['milliseconds'] for x in values),'minMilliseconds':min(x['milliseconds'] for x in values),'maxMilliseconds':max(x['milliseconds'] for x in values)}
  (folder/'current.json').write_bytes(encode({'schema':'atlas-generation-scaling-control-root/v1','generation':history[-1]}))
  rows.append({**case,'currentManifest':history[-1],'oldestManifest':history[0],'actualReused':len(reused),'changedReferences':changed,'manifestBytes':len(encode(manifest)),'retainedManifestBytes':footprint,'uniqueMetadataObjects':len(list(objects.glob('*.json'))),'metadataObjectBytes':sum(p.stat().st_size for p in objects.glob('*.json')),'samples':samples})
 return rows
