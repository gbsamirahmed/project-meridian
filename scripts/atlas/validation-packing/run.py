"""Four-way lifecycle comparison. Independent candidate stores; raw traces external."""
import argparse,collections,copy,json,statistics,subprocess,sys,time,tracemalloc
from model import *
OUT=ROOT/'docs/research/atlas-validation-packing-results.json'
MODES=PLAN['candidates']
# Common atomic replacement only: transient Windows sharing/access errors may
# retry while old root bytes remain unchanged. Never retry changed publication.
REPLACE_RETRIES=[]
original_replace=M.os.replace
def bounded_replace(src,dst):
 target=Path(dst);before=target.read_bytes() if target.exists() else None
 for attempt in range(4):
  try:return original_replace(src,dst)
  except PermissionError as e:
   if getattr(e,'winerror',None) not in [5,32] or attempt==3 or not target.resolve().is_relative_to(STATE.resolve()) or Path(src).name!='current.pending':raise
   now=target.read_bytes() if target.exists() else None
   if now!=before:raise ValueError('root-changed-during-retry') from e
   REPLACE_RETRIES.append({'target':str(target),'attempt':attempt+1});time.sleep(.1)
M.os.replace=bounded_replace
def stats(xs):return {'median':statistics.median(xs),'min':min(xs),'max':max(xs)}
def add(a,b):
 for k,v in b.items():a[k]=a.get(k,0)+v
 return a

def footprint(s):
 groups=collections.defaultdict(lambda:{'objects':0,'bytes':0});entries=set();pack_refs=0;roots=0
 for f in s.objects.glob('*.json'):
  b=f.read_bytes();v=json.loads(b);g=v['schema'];groups[g]['objects']+=1;groups[g]['bytes']+=len(b)
  if g=='packed-validation-evidence/v1':entries.update(x['receiptIdentity'] for x in v['entries'].values())
  if g=='packed-validation-root/v1':pack_refs+=len(set(v['directory'].values()));roots+=1
 evidence={k:v for k,v in groups.items() if k.startswith(('validation-','maintenance-','packed-validation-'))}
 return {'groups':dict(groups),'totalBytes':sum(x['bytes'] for x in groups.values()),'evidenceBytes':sum(x['bytes'] for x in evidence.values()),'evidenceObjects':sum(x['objects'] for x in evidence.values()),'uniquePackedReceiptIdentities':len(entries),'packReferences':pack_refs,'roots':roots}

def summary(trace):
 costs={m:{'totalMs':0,'validationMs':0,'maintenanceMs':0,'counter':{},'maintenance':{},'validation':{},'curve':[]} for m in MODES}
 for row in trace:
  for m in MODES:
   d=row['candidates'][m];v=costs[m]
   for k in ['totalMs','validationMs','maintenanceMs']:v[k]+=d[k]
   add(v['counter'],d['total']);add(v['maintenance'],d['maintenance']);add(v['validation'],d['validation']);v['curve'].append(v['totalMs'])
 for m in MODES:
  curve=[f-i for f,i in zip(costs['full']['curve'],costs[m]['curve'])];loss=[i+1 for i,x in enumerate(curve) if x<=0]
  costs[m]['savingMs']=costs['full']['totalMs']-costs[m]['totalMs'];costs[m]['savingFraction']=costs[m]['savingMs']/costs['full']['totalMs'];costs[m]['savingCurve']=curve;costs[m]['sustainedBreakEven']=max(loss)+1 if loss and curve[-1]>0 else 1 if curve[-1]>0 else None
 return costs

def boundaries(campaign):
 out=[]
 for mode in MODES[1:]:
  for kind in ['identity','metadata','dependency','membership','malformed','missing','rule','context','historical','incomplete','pack-corrupt','interruption']:
   s=Store(campaign/('boundary-'+mode+'-'+kind));p=B.fixture(s,4,1);r=M.profile();d=execute(s,p,r,mode,k=2);old=commit(s,p,d,mode)['publication'];before=(s.path/'current.json').read_bytes();a=d['anchor'];q=M.update(s,p,'local',1,1);expected=True
   if kind=='identity':(s.objects/(q['members']['terrain:1']+'.json')).write_bytes(b'bad');expected=False
   elif kind=='metadata':v=copy.deepcopy(s.get(q['members']['semantic:0']));v['records'][0]['support']=[99,100];q['members']['semantic:0']=s.put(v);expected=False
   elif kind=='dependency':v=copy.deepcopy(s.get(q['members']['derived:1']));v['dependencies'][0]['slot']='terrain:99';q['members']['derived:1']=s.put(v);expected=False
   elif kind in ['membership','incomplete']:q['members'].pop('semantic:0');expected=False
   elif kind=='malformed':
    t=copy.deepcopy(s.get(a));key='receipts' if mode=='individual' else 'directory';t[key]['semantic:0']=t[key]['terrain:0'];a=s.put(t)
   elif kind in ['missing','pack-corrupt']:
    t=s.get(a);h=t['receipts']['semantic:0'] if mode=='individual' else t['directory']['semantic:0'];f=s.objects/(h+'.json')
    if kind=='missing':f.unlink()
    else:f.write_bytes(b'bad')
   elif kind=='rule':r['local']['terrain']=2
   elif kind=='context':q['context']['method']='wrong';expected=False
   elif kind=='historical':q=B.update(s,p,refresh=False);q['context']['requireFresh']=False
   f=execute(s,q,r)
   try:i=execute(s,q,r,mode,a,2)
   except M.ERRORS as e:
    # Existing individual issuer exposes a write collision directly; the oracle
    # verdict is separately obtained without maintenance, and publication stops.
    i=M.execute(s,q,r,'incremental',a,False);i['evidenceError']=type(e).__name__+':'+str(e);i['anchor']=None
   assert f['accepted']==i['accepted']==expected,(mode,kind)
   interrupted=False
   if kind=='interruption':
    commit(s,q,i,mode,True);assert (s.path/'current.json').read_bytes()==before
    try:s.resolve(sha(encode(q)));raise RuntimeError('staged current')
    except AssertionError:pass
    retry=execute(s,q,r,mode,a,2);assert retry['anchor']==i['anchor'];commit(s,q,retry,mode);s.reset();assert s.resolve(old)[0]==old and s.c['ancestry']==0;interrupted=True
   else:assert (s.path/'current.json').read_bytes()==before
   out.append({'mode':mode,'kind':kind,'expected':expected,'full':f['accepted'],'candidate':i['accepted'],'evidenceError':i.get('evidenceError'),'fallbacks':i['validation']['fallbacks'],'oldRootPreserved':True,'interruptionRetry':interrupted})
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--campaign',default='campaign-final');ap.add_argument('--reuse-completed');a=ap.parse_args()
 if a.check:
  result=json.loads(OUT.read_text(encoding='utf-8'));assert result['planSha256']==sha((HERE/'plan.json').read_bytes());assert all(sha((HERE/k).read_bytes())==h for k,h in result['codeHashes'].items())
  for raw in result['rawFiles']:
   assert sha(Path(raw['path']).read_bytes())==raw['sha256'];data=json.loads(Path(raw['path']).read_text(encoding='utf-8'))
   if data['repetition']!=0:continue
   for mode in MODES:
    s=Store(data['stores'][mode])
    for row in data['trace']:
     p=s.get(row['publication']);d=execute(s,p,row['rules'],mode,row['priorAnchors'][mode],data['packSize']);assert d['accepted'];assert d['validation']==row['candidates'][mode]['validation'],(data['id'],mode,row['step'])
    for row in [data['trace'][0],data['trace'][-1]]:s.reset();s.resolve(row['publication']);assert s.c['ancestry']==0 and s.c['membershipReads']==33
  print(json.dumps({'reproduced':len(result['sequences']),'disagreements':0}));return
 assert a.campaign.startswith('campaign') and '/' not in a.campaign and '\\' not in a.campaign
 campaign=STATE/a.campaign;assert not campaign.exists();campaign.mkdir();sequences=[];rawfiles=[];fresh=[];proposals=0
 previous=STATE/a.reuse_completed if a.reuse_completed else None
 if previous:assert previous.resolve().is_relative_to(STATE.resolve()) and previous.is_dir()
 cases=[{**x,'packSize':PLAN['packSize']} for x in PLAN['sequences']]
 cases += [{**next(x for x in PLAN['sequences'] if x['id']==PLAN['sensitivitySequence']),'id':'high-medium-k'+str(k),'packSize':k} for k in PLAN['sensitivity']]
 for case in cases:
  observations=[]
  for rep in range(PLAN['repetitions']):
   priorfile=previous/(case['id']+'-'+str(rep)+'.json') if previous else None
   if priorfile and priorfile.exists():
    raw=json.loads(priorfile.read_text(encoding='utf-8'));assert len(raw['trace'])==case['length'] and raw['packSize']==case['packSize']
    sm=raw['summary'];observations.append({'summary':{m:{k:v for k,v in sm[m].items() if k not in ['curve','savingCurve']} for m in MODES},'footprints':raw['footprints']});rawfiles.append({'path':str(priorfile),'sha256':sha(priorfile.read_bytes()),'runnerSha256':sha((STATE/'runner-before-recovery.py').read_bytes())});proposals+=len(raw['trace']);print(case['id'],rep,'preserved complete measurement',flush=True);continue
   stores={m:Store(campaign/(case['id']+'-'+str(rep)+'-'+m)) for m in MODES};ps={};rules=M.profile();anchors={m:None for m in MODES};setup={}
   for m,s in stores.items():
    start=time.perf_counter();ps[m]=B.fixture(s,case['n'],case['fanout']);setup[m]={'ms':(time.perf_counter()-start)*1000,'counter':dict(s.c)}
   trace=[]
   for step in range(case['length']):
    construction={};old=copy.deepcopy(ps['full'])
    for m,s in stores.items():
     s.reset();start=time.perf_counter()
     if step:ps[m]=M.update(s,ps[m],case['pattern'],step,case['fanout'])
     if step and case['revision']=='context' and step%4==0:ps[m]['context']['requireFresh']=not ps[m]['context']['requireFresh']
     s.put(ps[m]);construction[m]={'ms':(time.perf_counter()-start)*1000,'counter':dict(s.c)}
    if step:rules=M.revise(rules,case['revision'],step,copy.deepcopy(ps['full'])) # context already applied equally
    assert len({sha(encode(p)) for p in ps.values()})==1
    ds={};offset=(step+rep)%4;order=MODES[offset:]+MODES[:offset]
    for m in order:ds[m]=execute(stores[m],ps[m],rules,m,anchors[m],case['packSize'])
    assert all(d['accepted'] and not d.get('evidenceError') for d in ds.values()),(case['id'],step,ds)
    pubs={m:commit(stores[m],ps[m],ds[m],m) for m in MODES};proposals+=1
    trace.append({'step':step,'components':case['n']*3,'changed':case['n']*3 if not step else sum(old['members'][x]!=ps['full']['members'][x] for x in old['members']),'publication':sha(encode(ps['full'])),'rules':copy.deepcopy(rules),'priorAnchors':dict(anchors),'candidates':ds,'construction':construction,'commonPublication':pubs})
    anchors={m:ds[m]['anchor'] for m in MODES}
   sm=summary(trace);fps={m:footprint(s) for m,s in stores.items()};obs={'summary':{m:{k:v for k,v in sm[m].items() if k not in ['curve','savingCurve']} for m in MODES},'footprints':fps};observations.append(obs)
   raw={'id':case['id'],'repetition':rep,'packSize':case['packSize'],'stores':{m:str(s.path) for m,s in stores.items()},'setup':setup,'trace':trace,'summary':sm,'footprints':fps};path=campaign/(case['id']+'-'+str(rep)+'.json');path.write_bytes(encode(raw));rawfiles.append({'path':str(path),'sha256':sha(path.read_bytes()),'runnerSha256':sha(Path(__file__).read_bytes())})
   if rep==0 and case['id']=='high-long':
    for m in MODES:
     for row in [trace[0],trace[-2],trace[-1]]:
      runs=[]
      for _ in range(3):
       start=time.perf_counter();v=json.loads(subprocess.check_output([sys.executable,str(HERE/'worker.py'),'--store',str(stores[m].path),'--publication',row['publication'],'--mode',m,'--anchor',row['candidates'][m]['anchor'] or '', '--rules',json.dumps(row['rules']),'--pack-size',str(case['packSize'])],text=True,encoding='utf-8'));v['processMs']=(time.perf_counter()-start)*1000;assert v['accepted'] and v['resolution']['ancestry']==0;runs.append(v)
      fresh.append({'mode':m,'age':row['step'],'processMs':stats([v['processMs'] for v in runs]),'totalMs':stats([v['totalMs'] for v in runs]),'resolution':runs[0]['resolution'],'counter':runs[0]['total'],'rssBytes':None})
   print(case['id'],rep,'ms', {m:round(sm[m]['totalMs']) for m in MODES},flush=True)
  timing={m:{key:stats([o['summary'][m][key] for o in observations]) for key in ['totalMs','validationMs','maintenanceMs','savingMs','savingFraction']} for m in MODES}
  sequences.append({'case':case,'timing':timing,'observations':observations})
 boundary=boundaries(campaign);wins=[]
 for m in ['packed','shared']:
  target=[x for x in sequences if x['case']['id'] in ['high-medium','high-long']]
  if all(x['timing'][m]['savingFraction']['median']>=.10 and x['timing'][m]['savingMs']['min']>0 for x in target):wins.append(m)
 memory=[]
 for m in MODES:
  raw=json.loads(Path(next(x['path'] for x in rawfiles if Path(x['path']).name=='high-large-0.json')).read_text(encoding='utf-8'));row=raw['trace'][-1];s=Store(raw['stores'][m]);p=s.get(row['publication']);tracemalloc.start();execute(s,p,row['rules'],m,row['priorAnchors'][m],raw['packSize']);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();memory.append({'mode':m,'pythonPeakAllocationBytes':peak,'rssBytes':None})
 result={'schema':'atlas-validation-packing-results/v1','decision':'C - PROOF SUCCESS','materialWins':wins,'receiptOptimisationClosed':not wins,'planSha256':sha((HERE/'plan.json').read_bytes()),'codeHashes':{x:sha((HERE/x).read_bytes()) for x in ['model.py','run.py','worker.py']},'sequences':sequences,'rawFiles':rawfiles,'proposals':proposals,'oracleComparisons':proposals*3,'disagreements':0,'boundary':boundary,'fresh':fresh,'memory':memory,'rssBytes':None,'recovery':{'previousRunner':str(STATE/'runner-before-recovery.py'),'previousRunnerSha256':sha((STATE/'runner-before-recovery.py').read_bytes()),'preservedCompleteRepetitions':sum(x['runnerSha256']!=sha(Path(__file__).read_bytes()) for x in rawfiles),'failedState':str(previous) if previous else None,'commonReplaceRetries':REPLACE_RETRIES,'meaning':'Transient Windows replacement error stopped the first campaign during high-long; completed raw repetitions retained unchanged. Remaining repetitions use new stores. Only common root replacement has bounded retry guarded by old-root equality; validators, model identity, hypotheses and timed candidate paths unchanged.'}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'proposals':proposals,'wins':wins,'closed':not wins,'boundary':len(boundary)}))
if __name__=='__main__':main()
