"""Isolated metadata model. Native templates stay exact; unit supports are synthetic."""
from pathlib import Path
import json,hashlib,os,time,copy
ROOT=Path(__file__).resolve().parents[3]
PLAN=json.loads((Path(__file__).parent/'plan.json').read_text(encoding='utf-8'))
STATE=Path(PLAN['stateRoot']);STATE.mkdir(exist_ok=True)
def encode(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def owned(path):
 p=Path(path).resolve();assert p.is_relative_to(STATE.resolve()) and p!=STATE.resolve();return p
def overlap(a,b):return a[0]<b[1] and b[0]<a[1]
class Store:
 def __init__(self,path):self.path=owned(path);self.path.mkdir(exist_ok=True,parents=True);self.objects=self.path/'objects';self.objects.mkdir(exist_ok=True);self.reset()
 def reset(self):self.cache={};self.c={'objectReads':0,'metadataBytes':0,'hashChecks':0,'hashedBytes':0,'recordsInspected':0,'directoryEntries':0,'references':0,'ancestry':0,'membershipReads':0,'components':0,'pages':0,'newObjects':0,'newBytes':0,'reusedObjects':0,'reusedBytes':0,'constructionHashOps':0,'constructionHashBytes':0,'reuseReadOps':0,'reuseReadBytes':0,'rootReads':0,'qualifierBytes':0}
 def put(self,v):
  body=encode(v);h=sha(body);p=self.objects/(h+'.json');self.c['constructionHashOps']+=1;self.c['constructionHashBytes']+=len(body)
  if p.exists():assert p.read_bytes()==body;self.c['reusedObjects']+=1;self.c['reusedBytes']+=len(body);self.c['reuseReadOps']+=1;self.c['reuseReadBytes']+=len(body)
  else:
   with p.open('xb') as f:f.write(body);f.flush();os.fsync(f.fileno())
   self.c['newObjects']+=1;self.c['newBytes']+=len(body)
  return h
 def get(self,h):
  assert isinstance(h,str) and len(h)==64 and all(c in '0123456789abcdef' for c in h)
  if h not in self.cache:
   b=(self.objects/(h+'.json')).read_bytes();assert sha(b)==h,'metadata-integrity';v=json.loads(b);assert encode(v)==b
   self.cache[h]=v;self.c['objectReads']+=1;self.c['metadataBytes']+=len(b);self.c['hashChecks']+=1;self.c['hashedBytes']+=len(b)
   if v['schema']=='atlas-publication-membership/v1':self.c['membershipReads']+=1
   if v['schema']=='granularity-leaf/v1':self.c['components']+=1
   if v['schema']=='granularity-index/v1':self.c['pages']+=1
   if v['schema']=='granularity-qualifier/v1':self.c['qualifierBytes']+=len(b)
  return self.cache[h]
 def insert(self,prior,h,depth=0):
  if depth==32:return self.put({'schema':'atlas-publication-membership/v1','depth':depth,'generation':h})
  children=copy.copy(self.get(prior)['children']) if prior else {};k=h[depth*2:depth*2+2];children[k]=self.insert(children.get(k),h,depth+1)
  return self.put({'schema':'atlas-publication-membership/v1','depth':depth,'children':children})
 def root(self):
  b=(self.path/'current.json').read_bytes();self.c['rootReads']+=1;self.c['metadataBytes']+=len(b);v=json.loads(b);assert v['schema']=='atlas-component-root/v1';return v
 def resolve(self,h=None):
  r=self.root();h=h or r['generation'];node=r['membership']
  for depth in range(33):
   v=self.get(node);assert v['depth']==depth
   if depth==32:assert v['generation']==h;break
   assert h[depth*2:depth*2+2] in v['children'],'generation-unpublished';node=v['children'][h[depth*2:depth*2+2]];self.c['references']+=1
  p=self.get(h);assert p['schema']=='granularity-publication/v1';return h,p
 def publish(self,p,fail=False):
  start=time.perf_counter();oldWrites={k:self.c[k] for k in ['newObjects','newBytes']};h=self.put(p);publicationWrite={k:self.c[k]-oldWrites[k] for k in oldWrites};self.reset();audit(self,p);validation=dict(self.c);self.reset();prior=self.root() if (self.path/'current.json').exists() else None
  assert p['predecessor']==(prior['generation'] if prior else None)
  witness=self.insert(prior['membership'] if prior else None,h)
  if fail:return h,validation
  temp=self.path/'current.pending'
  with temp.open('wb') as f:f.write(encode({'schema':'atlas-component-root/v1','generation':h,'membership':witness}));f.flush();os.fsync(f.fileno())
  os.replace(temp,self.path/'current.json');self.lastPublication={'validation':validation,'eligibilityAndPublication':{**self.c,**{k:self.c[k]+publicationWrite[k] for k in publicationWrite}},'milliseconds':(time.perf_counter()-start)*1000};return h,validation

def descriptor(h,rows):return {'id':h,'count':len(rows),'bounds':[min(r['support'][0] for r in rows),max(r['support'][1] for r in rows)],'keys':[min(r['key'] for r in rows),max(r['key'] for r in rows)]}
def branch_descriptor(h,children):return {'id':h,'count':sum(c['count'] for c in children),'bounds':[min(c['bounds'][0] for c in children),max(c['bounds'][1] for c in children)],'keys':[min(c['keys'][0] for c in children),max(c['keys'][1] for c in children)]}
def build(s,rows,strategy,qualifier,family):
 ordered=sorted(rows,key=lambda r:(r['support'][0],r['key'])) if strategy=='moderate' else sorted(rows,key=lambda r:r['key'])
 size=len(rows) if strategy=='coarse' else 1 if strategy=='fine' else 64;members=[]
 for start in range(0,len(rows),size):
  part=ordered[start:start+size];h=s.put({'schema':'granularity-leaf/v1','family':family,'scope':'synthetic-unit-interval; native support unchanged in qualifier','records':part});members.append(descriptor(h,part))
 if strategy=='selective':
  while len(members)>1:
   parent=[]
   for start in range(0,len(members),16):
    children=members[start:start+16];h=s.put({'schema':'granularity-index/v1','children':children});parent.append(branch_descriptor(h,children))
   members=parent
 return {'schema':'granularity-publication/v1','family':family,'strategy':strategy,'qualifier':qualifier,'members':members,'predecessor':None,'ordinal':1,'population':len(rows)}
def audit(s,p):
 s.get(p['qualifier']);found=[]
 def walk(d):
  v=s.get(d['id']);s.c['references']+=1
  if v['schema']=='granularity-leaf/v1':
   rows=v['records'];s.c['recordsInspected']+=len(rows);assert descriptor(d['id'],rows)==d;found.extend(rows)
  else:
   assert branch_descriptor(d['id'],v['children'])==d
   for child in v['children']:walk(child)
 for d in p['members']:walk(d)
 assert len(found)==p['population'] and len({r['key'] for r in found})==len(found)
 keys={r['key'] for r in found};assert all(r.get('upstream') is None or r['upstream'] in keys for r in found)
 return sorted(found,key=lambda r:r['key'])
def records(family,n):
 out=[]
 for i in range(n):
  position=(i*73)%n if family=='inventory' else i//2 if family=='derived' else i
  out.append({'key':i,'support':[position,position+(8 if family=='inventory' else 1)],'inputUse':[position-.25,position+1.25] if family=='derived' else [position,position+1],'upstream':i-1 if family=='derived' and i%2 else None,'nativeTemplate':i%2 if family=='derived' else 0,'syntheticApplicabilityRevision':0})
 return out

def query(s,g,kind):
 _,p=s.resolve(g);n=p['population'];extent=n//2 if p['family']=='derived' else n;c=extent//2
 requested=[0,extent+8] if kind=='broad' else [c,c+32] if kind=='area' else [c,c+1]
 key=n//2+1 if kind=='feature' else None;selected={};looked=set()
 def eligible(d,wanted=None):return d['keys'][0]<=wanted<=d['keys'][1] if wanted is not None else overlap(d['bounds'],requested)
 def walk(d,wanted=None):
  s.c['directoryEntries']+=1
  if not eligible(d,wanted):return
  s.c['references']+=1;v=s.get(d['id'])
  if v['schema']=='granularity-index/v1':
   for child in v['children']:walk(child,wanted)
  elif d['id'] not in looked:
   looked.add(d['id']);s.c['recordsInspected']+=len(v['records'])
   for r in v['records']:
    if (r['key']==wanted if wanted is not None else overlap(r['support'],requested)):selected[r['key']]=r
  else:
   for r in v['records']:
    if r['key']==wanted:selected[r['key']]=r
 for d in p['members']:walk(d,key)
 # Explicit derived-to-derived closure; not scientific recomputation.
 for r in list(selected.values()):
  upstream=r.get('upstream')
  if upstream is not None:
   s.c['references']+=1
   if upstream not in selected:
    for d in p['members']:walk(d,upstream)
 qualifier=s.get(p['qualifier']);out={'family':p['family'],'qualifier':qualifier,'records':[selected[k] for k in sorted(selected)]}
 return out

def templates():
 data=ROOT.parent/'meridian-data/experiments/atlas/tryfan-regional-pilot-v1';b=json.loads((ROOT/'docs/research/atlas-component-granularity-baseline.json').read_text(encoding='utf-8'));v=json.loads((data/'generations'/f"{b['current']}.json").read_text(encoding='utf-8'))
 base={'schema':'granularity-qualifier/v1','scientificGeneration':b['current'],'rightsProvenance':v['catalogue']['sources'],'products':v['catalogue']['products'],'representations':v['catalogue']['representations'],'label':'Exact native metadata retained; model records/supports are synthetic, not physical claims'}
 return {f:{**base,**({'definitions':v['knowledge']['definitions'],'mappings':v['knowledge']['mappings'],'resources':v['knowledge']['resources']} if f in ['worldcover','inventory'] else {'inputRoots':v['understanding']['roots']} if f=='derived' else {}),'family':f,'templates':v['understanding']['results'][:2] if f=='derived' else [v['knowledge']['collections'][1]['claims'][0],{k:x for k,x in v['knowledge']['collections'][1].items() if k!='claims'}] if f=='inventory' else [v['knowledge']['collections'][0]] if f=='worldcover' else [next(a for a in v['catalogue']['artifacts'] if any(u['family']=='terrain-regional' for u in a['uses'])),v['catalogue']['representations']]} for f in PLAN['families']}

def expected(rows,family,kind):
 n=len(rows);extent=n//2 if family=='derived' else n;c=extent//2;support=[0,extent+8] if kind=='broad' else [c,c+32] if kind=='area' else [c,c+1]
 found={r['key']:r for r in rows if r['key']==n//2+1} if kind=='feature' else {r['key']:r for r in rows if overlap(r['support'],support)}
 for r in list(found.values()):
  if r['upstream'] is not None:found[r['upstream']]=rows[r['upstream']]
 return [found[k] for k in sorted(found)]
