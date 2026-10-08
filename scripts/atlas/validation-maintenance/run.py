"""Paired cumulative lifecycle campaign. Raw traces/state remain outside Git."""
import argparse,collections,copy,json,statistics,subprocess,sys,time
from model import *
OUT=ROOT/'docs/research/atlas-validation-maintenance-results.json'
def add(a,b):
 for k,v in b.items():a[k]=a.get(k,0)+v
 return a
def stats(v):return {'median':statistics.median(v),'min':min(v),'max':max(v)}
def footprint(s,anchors):
 groups=collections.defaultdict(lambda:{'objects':0,'bytes':0});ids=set();receipt_ids=set();active=set()
 for f in s.objects.glob('*.json'):
  b=f.read_bytes();v=json.loads(b);g=v['schema'];groups[g]['objects']+=1;groups[g]['bytes']+=len(b)
  if g=='validation-local-receipt/v1':receipt_ids.add(f.stem)
 for a in anchors:
  t=s.get(a);ids.update(t['receipts'].values())
 t=s.get(anchors[-1]);active.update(t['receipts'].values())
 evidence_schemas=['validation-local-receipt/v1','validation-outgoing/v1','validation-reverse/v1','maintenance-trust-root/v1']
 return {'groups':dict(groups),'totalBytes':sum(v['bytes'] for v in groups.values()),'evidenceBytes':sum(groups[k]['bytes'] for k in evidence_schemas),'localReceipts':len(receipt_ids),'currentlyReferencedReceipts':len(active),'historicalOnlyReceipts':len(ids-active),'unreferencedLocalReceipts':len(receipt_ids-ids),'sharedReferences':sum(len(s.get(a)['receipts']) for a in anchors)-len(ids),'retirement':'Historical-only receipts cannot retire while all corresponding accepted roots remain retained; unreferenced staging evidence merely a candidate after pin/audit/retry obligations. No deletion.'}
def summary(trace):
 full={};inc={};maint={};construct={};pub={};cumf=cumi=0;curve=[]
 for x in trace:
  add(full,x['full']['total']);add(inc,x['incremental']['total']);add(maint,x['incremental']['maintenance']);add(construct,x['construction']['counter']);add(pub,x['publicationCost']['counter'])
  cumf+=x['full']['totalMs'];cumi+=x['incremental']['totalMs'];curve.append({'publication':x['step']+1,'fullMs':cumf,'incrementalMs':cumi,'savingMs':cumf-cumi})
 positive=[x['publication'] for x in curve if x['savingMs']>0];loss=[x['publication'] for x in curve if x['savingMs']<=0]
 return {'full':full,'incremental':inc,'maintenance':maint,'construction':construct,'commonPublication':pub,'fullMs':cumf,'incrementalMs':cumi,'maintenanceMs':sum(x['incremental']['maintenanceMs'] for x in trace),'commonPublicationMs':sum(x['publicationCost']['milliseconds'] for x in trace),'constructionMs':sum(x['construction']['milliseconds'] for x in trace),'initialFullMs':trace[0]['full']['totalMs'],'initialIncrementalMs':trace[0]['incremental']['totalMs'],'netSavingMs':cumf-cumi,'firstBreakEven':positive[0] if positive else None,'sustainedBreakEvenWithinRange':max(loss)+1 if positive and curve[-1]['savingMs']>0 else None,'curve':curve,'changedComponents':sum(x['changed'] for x in trace),'reusedComponents':sum(x['components']-x['changed'] for x in trace[1:])}
def failures(campaign):
 out=[]
 for kind in PLAN['failures']:
  s=Store(campaign/('boundary-'+kind));p=B.fixture(s,4,1);r=profile();d,initial=publish(s,p,r);a=d['anchor'];q=update(s,p,'local',1,1);old=(s.path/'current.json').read_bytes();expected=True
  if kind=='broken-identity':(s.objects/(q['members']['terrain:1']+'.json')).write_bytes(b'corrupt');expected=False
  elif kind=='broken-relationship':
   v=copy.deepcopy(s.get(q['members']['derived:1']));v['dependencies'][0]['slot']='terrain:99';q['members']['derived:1']=s.put(v);expected=False
  elif kind=='incomplete-membership':q['members'].pop('semantic:0');expected=False
  elif kind=='mismatched-receipt':
   t=copy.deepcopy(s.get(a));t['receipts']['semantic:0']=t['receipts']['terrain:0'];a=s.put(t)
  elif kind=='missing-receipt':(s.objects/(s.get(a)['receipts']['semantic:0']+'.json')).unlink()
  elif kind=='unknown-anchor':a='0'*64
  elif kind=='context-policy':q['context']['method']='wrong';expected=False
  elif kind=='stale-rule':r['local']['terrain']=2
  elif kind=='historical-stale':q=B.update(s,p,refresh=False);q['context']['requireFresh']=False
  f=execute(s,q,r);i=execute(s,q,r,'incremental',a,True);assert f['accepted']==i['accepted']==expected,kind
  if kind=='interrupted-before-switch':
   c=commit(s,q,i,True);assert old==(s.path/'current.json').read_bytes()
   try:s.resolve(c['publication']);raise RuntimeError('staged generation visible')
   except AssertionError:pass
   retry=execute(s,q,r,'incremental',a,True);assert retry['anchor']==i['anchor'];commit(s,q,retry)
   s.reset();s.resolve(initial['publication']);assert s.c['ancestry']==0
   out.append({'id':kind,'accepted':True,'rootPreservedBeforeRetry':True,'unpublishedRejected':True,'retryEvidenceNewBytes':retry['maintenance']['newBytes'],'oldPinReadable':True});continue
  assert old==(s.path/'current.json').read_bytes()
  out.append({'id':kind,'expected':expected,'full':f,'incremental':i,'rootPreserved':True})
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--campaign',default='campaign-final');a=ap.parse_args()
 if a.check:
  r=json.loads(OUT.read_text(encoding='utf-8'));assert r['planSha256']==sha((HERE/'plan.json').read_bytes());assert all(sha((HERE/k).read_bytes())==h for k,h in r['codeHashes'].items())
  for raw in r['rawFiles']:
   assert sha(Path(raw['path']).read_bytes())==raw['sha256'];data=json.loads(Path(raw['path']).read_text(encoding='utf-8'))
   if data['repetition']!=0:continue
   s=Store(data['store'])
   for row in data['trace']:
    p=s.get(row['publication']);f=execute(s,p,row['rules']);i=execute(s,p,row['rules'],'incremental',row['priorAnchor'])
    assert f['accepted']==i['accepted']==True
    assert f['validation']==row['full']['validation'] and i['validation']==row['incremental']['validation'],(data['id'],row['step'])
   for h in [data['trace'][0]['publication'],data['trace'][-1]['publication']]:s.reset();s.resolve(h);assert s.c['ancestry']==0 and s.c['membershipReads']==33
  print(json.dumps({'sequences':len(r['sequences']),'zeroDisagreements':True,'immutableRawFiles':len(r['rawFiles'])}));return
 assert a.campaign.startswith('campaign') and '/' not in a.campaign and '\\' not in a.campaign
 campaign=STATE/a.campaign;assert not campaign.exists(),'Do not overwrite a measured campaign';campaign.mkdir()
 rawfiles=[];sequences=[];fresh=[];totalprops=0
 for case in PLAN['sequences']:
  observations=[];fps=[]
  for rep in range(PLAN['repetitions']):
   s=Store(campaign/(case['id']+'-'+str(rep)));s.reset();begin=time.perf_counter();p=B.fixture(s,case['n'],case['fanout']);setup={'milliseconds':(time.perf_counter()-begin)*1000,'counter':dict(s.c)};anchor=None;rules=profile();trace=[];anchors=[]
   for step in range(case['length']):
    previous=copy.deepcopy(p);s.reset();start=time.perf_counter()
    if step:p=update(s,p,case['pattern'],step,case['fanout']);rules=revise(rules,case['revision'],step,p)
    s.put(p) # staged manifest is shared construction, not receipt-only cost
    construction={'milliseconds':(time.perf_counter()-start)*1000,'counter':dict(s.c)}
    if (step+rep)%2:
     i=execute(s,p,rules,'incremental',anchor,True);f=execute(s,p,rules)
    else:
     f=execute(s,p,rules);i=execute(s,p,rules,'incremental',anchor,True)
    assert f['accepted']==i['accepted']==True,(case['id'],step,f['error'],i['error']);totalprops+=1
    pub=commit(s,p,i);trace.append({'step':step,'components':case['n']*3,'changed':case['n']*3 if step==0 else sum(p['members'][k]!=previous['members'][k] for k in p['members']),'publication':pub['publication'],'rules':copy.deepcopy(rules),'priorAnchor':anchor,'full':f,'incremental':i,'construction':construction,'publicationCost':pub});anchor=i['anchor'];anchors.append(anchor)
   fp=footprint(s,anchors);fps.append(fp);sm=summary(trace);observations.append({k:v for k,v in sm.items() if k!='curve'})
   raw={'id':case['id'],'repetition':rep,'store':str(s.path),'setup':setup,'trace':trace,'summary':sm,'footprint':fp};path=campaign/(case['id']+'-'+str(rep)+'.json');path.write_bytes(encode(raw));rawfiles.append({'path':str(path),'sha256':sha(path.read_bytes())})
   if rep==0 and case['id'] in ['high-long','high-large']:
    for row in [trace[0],trace[-2],trace[-1]]:
     runs=[]
     for _ in range(3):
      start=time.perf_counter();out=subprocess.check_output([sys.executable,str(HERE/'worker.py'),'--store',str(s.path),'--publication',row['publication'],'--anchor',row['incremental']['anchor'],'--rules',json.dumps(row['rules'])],text=True,encoding='utf-8');v=json.loads(out);v['processMs']=(time.perf_counter()-start)*1000;assert v['accepted'] and v['resolution']['ancestry']==0;runs.append(v)
     fresh.append({'sequence':case['id'],'age':row['step'],'publication':row['publication'],'processMs':stats([v['processMs'] for v in runs]),'validationMs':stats([v['validationMs'] for v in runs]),'resolution':runs[0]['resolution'],'validation':runs[0]['validation'],'rssBytes':None})
   print(case['id'],rep,'full/inc ms',round(sm['fullMs']),round(sm['incrementalMs']),'break-even',sm['firstBreakEven'],flush=True)
  vals={key:stats([o[key] for o in observations]) for key in ['fullMs','incrementalMs','netSavingMs','maintenanceMs','initialFullMs','initialIncrementalMs','commonPublicationMs','constructionMs']}
  sequences.append({'case':case,'observations':observations,'timing':vals,'footprints':fps,'breakEvenPublications':[o['firstBreakEven'] for o in observations],'sustainedBreakEvenPublications':[o['sustainedBreakEvenWithinRange'] for o in observations]})
 boundary=failures(campaign)
 r={'schema':'atlas-validation-maintenance-results/v1','decision':'C - EXPERIMENT RESOLVED','planSha256':sha((HERE/'plan.json').read_bytes()),'codeHashes':{p:sha((HERE/p).read_bytes()) for p in ['model.py','run.py','worker.py']},'sequences':sequences,'rawFiles':rawfiles,'proposals':totalprops,'boundary':boundary,'fresh':fresh,'disagreements':0,'repetitions':3,'rssBytes':None}
 OUT.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'proposals':totalprops,'sequences':len(sequences),'boundaries':len(boundary)}))
if __name__=='__main__':main()
