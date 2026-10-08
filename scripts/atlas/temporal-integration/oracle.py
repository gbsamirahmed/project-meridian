"""Independent full-scan temporal oracle, standard datetime; no implementation imports."""
import sys,json,datetime,calendar
sys.stdout.reconfigure(encoding='utf-8')
def parse(v):
 if 'T' in v:return datetime.datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()
 y=int(v[:4]);m=int(v[5:7]) if len(v)>4 else 1;d=int(v[8:10]) if len(v)>7 else 1
 return datetime.datetime(y,m,d,tzinfo=datetime.timezone.utc).timestamp()
def upper(v):
 if 'T' in v:return parse(v)
 y=int(v[:4]);m=int(v[5:7]) if len(v)>4 else 1
 if len(v)==4:return parse(str(y+1))
 if len(v)==7:return parse(f'{y+1}-01' if m==12 else f'{y}-{m+1:02}')
 return parse(v)+86400
def bounds(t):
 if t['kind']=='unknown':return None
 return (parse(t['start']),upper(t['end'])) if t['kind']=='interval' else (parse(t['value']),upper(t['value']))
def query(l,q):
 cutoff=q.get('knowledge',l['ordinal']);selected={}
 for r in sorted(l['records'],key=lambda r:r['knowledge']['ordinal']):
  if r['knowledge']['ordinal']<=cutoff:selected[r['assignment']]=r
 yes=[];unknown=[]
 for key,r in sorted(selected.items()):
  if any(q.get(k) and q[k]!=r[k] for k in ['region','assignment','feature']):continue
  if q.get('unknown'):
   axis=r['physical']['extent'] if q['unknown']=='physical' else r['sourceTime']
   if axis['kind']!='unknown':continue
  ok=True;ind=False
  if 'physical' in q:
   b=bounds(r['physical']['extent']);p=q['physical'];a=(parse(p['start']),upper(p['end']))
   if b is None:ind=True
   elif q.get('mode')=='valid-throughout':ind=True
   elif r['physical']['role']!=p['role']:ok=False
   elif b[0]==b[1]:ok=a[0]<=b[0]<a[1] or b[0]==a[0]==a[1]
   elif a[0]==a[1]:ok=b[0]<=a[0]<b[1]
   else:ok=b[0]<a[1] and a[0]<b[1]
  if 'sourcePeriod' in q:
   b=bounds(r['sourceTime']);a=(parse(q['sourcePeriod'][0]),upper(q['sourcePeriod'][1]))
   if b is None:ind=True
   elif b[0]==b[1]:ok=ok and (a[0]<=b[0]<a[1] or b[0]==a[0]==a[1])
   elif a[0]==a[1]:ok=ok and b[0]<=a[0]<b[1]
   else:ok=ok and b[0]<a[1] and a[0]<b[1]
  if ok:(unknown if ind else yes).append(r)
 return {'schema':'atlas-qualified-temporal-answer/v1','knowledgeCutoff':cutoff,'matches':yes,'indeterminate':unknown,'limitations':'No match is not physical absence. Overlap describes source time support, never continuous physical validity or physical change.'}
request=json.load(sys.stdin);print(json.dumps([query(request['ledger'],q) for q in request['queries']],ensure_ascii=False,allow_nan=False))
