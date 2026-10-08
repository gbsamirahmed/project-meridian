"""Five isolated full-validation controls and repeated publication accounting."""
from pathlib import Path
import json,time,sys,copy
from metadata import M,B,measure,install
HERE=Path(__file__).parent;plan=json.loads((HERE/'plan.json').read_text());state=Path(plan['stateRoot'])/'campaign';B.G.STATE=state;mode=sys.argv[1];out=[]
if mode=='meter':install()
for c in plan['metadataCases']:
 s=M.Store(state/('metadata-'+mode+'-'+c['id']));start=time.perf_counter();p=B.fixture(s,c['n'],c['fanout']);setupMs=(time.perf_counter()-start)*1000;samples=[]
 for _ in range(plan['repetitions']):
  if mode=='meter':v=measure(s,p)
  else:
   v=M.execute(s,p,M.profile(),'full');v={'accepted':v['accepted'],'counter':v['validation'],'milliseconds':v['validationMs'],'components':len(p['members'])}
  samples.append(v)
 out.append(dict(kind='population',case=c,setupMs=setupMs,samples=samples))
for c in plan['repeatPublicationCases']:
 repeats=[]
 for rep in range(plan['repetitions']):
  s=M.Store(state/('sequence-'+mode+'-'+c['id']+'-'+str(rep)));start=time.perf_counter();p=B.fixture(s,64,1);setupMs=(time.perf_counter()-start)*1000;rows=[]
  for step in range(c['length']):
   start=time.perf_counter()
   if step:p=B.update(s,p,c['pattern'])
   constructionMs=(time.perf_counter()-start)*1000
   if mode=='meter':v=measure(s,p)
   else:
    v=M.execute(s,p,M.profile(),'full');v={'accepted':v['accepted'],'counter':v['validation'],'milliseconds':v['validationMs'],'components':len(p['members'])}
   decision={'accepted':v['accepted'],'publication':B.sha(B.encode(p))};commit=M.commit(s,p,decision);rows.append(dict(step=step,validation=v,commit=commit,constructionMs=constructionMs))
  s.reset();s.resolve(B.sha(B.encode(p)));current=dict(s.c);r=s.root();old=p
  while old['predecessor'] is not None:old=s.get(old['predecessor'])
  oldest=B.sha(B.encode(old));s.reset();s.resolve(oldest);historical=dict(s.c)
  assert current['ancestry']==historical['ancestry']==0 and current['membershipReads']==historical['membershipReads']==33
  repeats.append(dict(setupMs=setupMs,rows=rows,current=current,historical=historical))
 out.append(dict(kind='sequence',case=c,repeats=repeats))
# Explicit completeness/reference failures of the existing full oracle. No receipts.
s=M.Store(state/('metadata-fail-'+mode));p=B.fixture(s,4,1);d=M.execute(s,p,M.profile());M.commit(s,p,d);root=(s.path/'current.json').read_bytes();failures=[]
for kind in ['incomplete-membership','broken-reference','malformed-component','invalid-scope','historical-corruption']:
 q=copy.deepcopy(p)
 if kind=='incomplete-membership':q['members'].pop('semantic:0')
 elif kind=='broken-reference':
  v=copy.deepcopy(s.get(q['members']['derived:0']));v['dependencies'][0]['slot']='terrain:99';q['members']['derived:0']=s.put(v)
 elif kind=='malformed-component':
  body=b'{malformed';h=B.sha(body);(s.objects/(h+'.json')).write_bytes(body);q['members']['terrain:0']=h
 elif kind=='invalid-scope':
  v=copy.deepcopy(s.get(q['members']['terrain:0']));v['scope']=[0,1];q['members']['terrain:0']=s.put(v)
 else:
  q=B.update(s,p,refresh=False);q['context']['requireFresh']=False;(s.objects/(p['members']['terrain:0']+'.json')).write_bytes(b'corrupt')
 v=M.execute(s,q,M.profile(),'full');assert not v['accepted'];assert (s.path/'current.json').read_bytes()==root;failures.append(dict(kind=kind,error=v['error'],accepted=False,rootPreserved=True))
print(json.dumps(dict(mode=mode,rows=out,failures=failures)))
