"""Frozen controlled matrix; measurements outside Git, summaries committed."""
from pathlib import Path
import sys,json,subprocess,time,statistics,hashlib,copy
from model import Store,STATE,ROOT,PLAN,records,templates,build,query,expected,encode,sha,audit
OUT=ROOT/'docs/research/atlas-component-granularity-results.json'
def digest(p):return sha(Path(p).read_bytes())
def stats(v):return {'median':statistics.median(v),'min':min(v),'max':max(v)}
def rss():
 import ctypes
 class M(ctypes.Structure):
  _fields_=[("cb",ctypes.c_ulong),("faults",ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ["peak","working","peakPaged","paged","peakNonPaged","nonPaged","pagefile","peakPagefile"]]
 m=M();m.cb=ctypes.sizeof(m);ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p;ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong]
 return m.working if ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(m),m.cb) else None
def worker(path,g,kind):
 s=Store(path);samples=[];begin=time.perf_counter()
 for _ in range(PLAN['repetitions']):
  s.reset();t=time.perf_counter();answer=query(s,g,kind);elapsed=(time.perf_counter()-t)*1000
  samples.append({'rss':rss(),'ms':elapsed,'counter':s.c.copy(),'answer':sha(encode(answer)),'required':len(answer['records'])})
 assert all(x['counter']==samples[0]['counter'] and x['answer']==samples[0]['answer'] for x in samples)
 return {'samples':samples,'workerMilliseconds':(time.perf_counter()-begin)*1000}
def fresh(path,g,kind):
 start=time.perf_counter();v=json.loads(subprocess.check_output([sys.executable,__file__,'--worker',str(path),g,kind],cwd=ROOT,text=True,encoding='utf-8'));v['processMilliseconds']=(time.perf_counter()-start)*1000;return v
def save_raw(id,value):
 p=STATE/'measurements'/f'{id}.json';p.parent.mkdir(exist_ok=True);p.write_bytes(encode(value));return {'path':str(p),'sha256':digest(p)}
def main():
 qualifiers=templates();result={'schema':'atlas-component-granularity-results/v1','planSha256':digest(Path(__file__).parent/'plan.json'),'decision':'UNJUDGED','rows':[],'updates':[],'history':[],'fixtures':[],'runtime':{'python':sys.version,'fresh':'Fresh process, OS cache not flushed','memory':'Observed Windows working set through standard ctypes, not peak/leak/live heap','payloadReads':0},'codeHashes':{p.name:digest(p) for p in Path(__file__).parent.glob('*.py') if p.name not in ['validate.py','test_model.py','report.py']}}
 def measure(id,s,g,kind,rows,family,n,strategy):
  runs=[fresh(s.path,g,kind) for _ in range(3 if n==2048 and kind in ['narrow','broad'] else 1)]
  sample=runs[0]['samples'][0];s.reset();_,pub=s.resolve(g);qualifier=s.get(pub['qualifier']);wanted={'family':family,'qualifier':qualifier,'records':expected(rows,family,kind)};assert sha(encode(wanted))==sample['answer']
  assert all(x['counter']==sample['counter'] and x['answer']==sample['answer'] for r in runs for x in r['samples'])
  value={'id':id,'family':family,'population':n,'strategy':strategy,'query':kind,'required':sample['required'],'counter':sample['counter'],'answer':sample['answer'],'ms':stats([x['ms'] for r in runs for x in r['samples']]),'freshProcessMs':stats([r['processMilliseconds'] for r in runs]),'rssObserved':max(x['rss'] or 0 for r in runs for x in r['samples']),'raw':save_raw(id,runs)};result['rows'].append(value);print(id,sample['counter']['recordsInspected'],sample['counter']['metadataBytes'],flush=True)
 for family in PLAN['families']:
  for n in PLAN['populations']:
   rows=records(family,n)
   for strategy in PLAN['strategies']:
    path=STATE/f'{family}-{n}-{strategy}';assert not path.exists(),'Use a new deliberately frozen campaign, never overwrite measured fixtures';s=Store(path);q=s.put(qualifiers[family]);p=build(s,rows,strategy,q,family);construction=s.c.copy();g,_=s.publish(p)
    result['fixtures'].append({'family':family,'population':n,'strategy':strategy,'store':str(path),'generation':g,'members':len(p['members']),'qualifier':q,'construction':construction,'publication':s.lastPublication,'initialObjectBytes':sum(f.stat().st_size for f in s.objects.glob('*.json')),'initialObjects':len(list(s.objects.glob('*.json')))})
    for kind in PLAN['queries']:measure(f'{family}-{n}-{strategy}-{kind}',s,g,kind,rows,family,n,strategy)
    if family=='inventory' and n==2048:measure(f'{family}-{n}-{strategy}-feature',s,g,'feature',rows,family,n,strategy)
    if n!=2048:continue
    previous=g;current=copy.deepcopy(rows)
    for label,count in zip(PLAN['updates']['patterns'],PLAN['updates']['counts']):
     indices=list(range(n//2,n//2+count)) if label=='local' else sorted({(i*73)%n for i in range(count)}) if label=='scattered' else list(range(count))
     changed=copy.deepcopy(current)
     for i in indices:changed[i]['syntheticApplicabilityRevision']+=1
     s.reset();t=time.perf_counter();new=build(s,changed,strategy,q,family);new.update(predecessor=previous,ordinal=p['ordinal']+1);construction={**s.c,'recordPopulationVisited':n,'milliseconds':(time.perf_counter()-t)*1000};nextg,_=s.publish(new)
     s.reset();historical=audit(s,s.resolve(previous)[1]);assert historical==current
     s.reset();assert audit(s,s.resolve(nextg)[1])==changed
     # Record replacement and dependency notification are separate; no physical values are recomputed.
     affected=set(indices)
     for r in current:
      if r['upstream'] in affected:affected.add(r['key'])
     result['updates'].append({'family':family,'strategy':strategy,'pattern':label,'changedRecords':len(indices),'changedKeys':indices,'derivedAffected':len(affected) if family=='derived' else 0,'derivedPhysicalRecomputed':0,'old':previous,'new':nextg,'oldMemberCount':len(p['members']),'newMemberCount':len(new['members']),'reusedMembers':len({m['id'] for m in p['members']}&{m['id'] for m in new['members']}),'construction':construction,'publication':s.lastPublication});p=new;previous=nextg;current=changed
 # Separate controlled high-reuse histories; no accepted or previous-proof fixture altered.
 for strategy in PLAN['strategies']:
  for depth in PLAN['history']['depths']:
   s=Store(STATE/f'history-{depth}-{strategy}');rows=records('terrain',512);q=s.put(qualifiers['terrain']);previous=None;ids=[];states=[];pubs=[]
   for index in range(depth):
    if index in [depth//4,depth//2,3*depth//4]:rows=copy.deepcopy(rows);rows[256]['syntheticApplicabilityRevision']+=1
    p=build(s,rows,strategy,q,'terrain');p.update(predecessor=previous,ordinal=index+1);previous,_=s.publish(p);ids.append(previous);states.append(copy.deepcopy(rows));pubs.append(s.lastPublication)
   for label,index in [('current',depth-1),('recent',depth-2),('oldest',0)]:
    id=f'history-{depth}-{strategy}-{label}';r=fresh(s.path,ids[index],'narrow');s.reset();expectedHash=sha(encode({'family':'terrain','qualifier':s.get(q),'records':expected(states[index],'terrain','narrow')}));assert r['samples'][0]['answer']==expectedHash
    result['history'].append({'id':id,'depth':depth,'strategy':strategy,'selection':label,'counter':r['samples'][0]['counter'],'answer':expectedHash,'ms':stats([x['ms'] for x in r['samples']]),'raw':save_raw(id,r),'members':len(p['members']),'store':str(s.path),'publication':pubs[-1],'footprint':{'objects':len(list(s.objects.glob('*.json'))),'bytes':sum(f.stat().st_size for f in s.objects.glob('*.json'))}})
 result['rawSetupReceipt']=save_raw('setup',{'fixtures':result['fixtures'],'updates':result['updates'],'history':result['history']})
 for update in result['updates']:del update['changedKeys']
 # Compact machine-readable summaries; full raw observations remain external and SHA pinned.
 OUT.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
 print({'rows':len(result['rows']),'updates':len(result['updates']),'history':len(result['history']),'bytes':OUT.stat().st_size},flush=True)
def check():
 v=json.loads(OUT.read_text(encoding='utf-8'));assert v['planSha256']==digest(Path(__file__).parent/'plan.json');assert len(v['rows'])==148 and len(v['updates'])==48 and len(v['history'])==24
 for r in v['rows']+v['history']:assert digest(r['raw']['path'])==r['raw']['sha256'] and r['counter']['membershipReads']==33 and r['counter']['ancestry']==0
 b=json.loads((ROOT/'docs/research/atlas-component-granularity-baseline.json').read_text(encoding='utf-8'));store=ROOT.parent/'meridian-data/experiments/atlas/tryfan-regional-pilot-v1';assert all(digest(store/p)==h for p,h in b['acceptedStoreHashes'].items());print('220 observations; source/pilot unchanged')
if __name__=='__main__':
 if '--worker' in sys.argv:print(json.dumps(worker(Path(sys.argv[2]),sys.argv[3],sys.argv[4])))
 elif '--check' in sys.argv:check()
 else:main()
