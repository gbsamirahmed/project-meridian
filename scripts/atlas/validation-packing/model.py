"""Isolated packed evidence adapter over the unchanged maintenance oracle."""
from pathlib import Path
import copy, importlib.util, json, time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PLAN=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('maintenance_model',ROOT/'scripts/atlas/validation-maintenance/model.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
B=M.B;encode=M.encode;sha=M.sha
STATE=Path(PLAN['stateRoot']);STATE.mkdir(exist_ok=True);B.G.STATE=STATE
IMPLEMENTATION=sha(Path(__file__).read_bytes()+M.IMPLEMENTATION.encode())
EXTRA=['packLookups','packRecordsDecoded','receiptDigestChecks','directoryEntriesRead','directoryEntriesWritten','packsCreated','packsReused','packEntriesWritten','evidenceEncodingOps','reverseBookkeepingEntries']
class Store(M.Store):
 def reset(self):
  super().reset();self.c.update({k:0 for k in EXTRA})
 def get(self,h):
  cached=h in self.cache if hasattr(self,'cache') else False
  v=super().get(h)
  if v.get('schema')=='packed-validation-evidence/v1' and not cached:self.c['packRecordsDecoded']+=len(v['entries'])
  return v

def group(slot,k):
 f,i=slot.split(':');return f+':'+str(int(i)//k)
def root(s,a,p,mode,k):
 t=s.get(a);s.c['evidenceLookup']+=1
 if t['schema']!='packed-validation-root/v1' or t['implementation']!=IMPLEMENTATION or t['mode']!=mode or t['packSize']!=k or t['qualifier']!=p['qualifier']:raise ValueError('root-ineligible')
 M.validate_profile(t['profile']);old=s.get(t['publication'])
 if t['context']!=old['context'] or t['qualifier']!=old['qualifier']:raise ValueError('root-context')
 expected=set(old['members']) if mode=='packed' else {group(x,k) for x in old['members']}
 if set(t['directory'])!=expected or mode=='packed' and t['members']!=old['members']:raise ValueError('directory-membership')
 s.c['directoryEntriesRead']+=len(t['directory']);s.c['trustDirectoryEntries']+=len(old['members'])
 return t,old

def entry(s,t,old,slot):
 k=t['packSize'];g=group(slot,k);key=slot if t['mode']=='packed' else g
 h=t['directory'][key];s.c['packLookups']+=1;v=s.get(h)
 if v['schema']!='packed-validation-evidence/v1' or v['implementation']!=IMPLEMENTATION or v['group']!=g or v['packSize']!=k:raise ValueError('pack-identity')
 # Do not rediscover groups by scanning membership per lookup. The expected
 # group is derived arithmetically from family/population, including last page.
 f=slot.split(':')[0];start=int(g.split(':')[1])*k
 expected={f+':'+str(i) for i in range(start,min(start+k,old['population']))}
 if set(v['entries'])!=expected:raise ValueError('pack-membership')
 e=v['entries'][slot];c=e['receipt'];s.c['receiptDigestChecks']+=1;s.c['evidenceEncodingOps']+=1
 if set(e)!={'receipt','receiptIdentity','dependencies','sources'} or sha(encode(c))!=e['receiptIdentity']:raise ValueError('entry-integrity')
 if c.get('component')!=old['members'][slot] or c.get('rule')!=M.rid('local:'+f,t['profile']['local'][f]) or c.get('schema')!='validation-local-receipt/v1' or c.get('outcome')!='valid' or c.get('guarantee')!='component-local-only':raise ValueError('receipt-ineligible')
 return e

def incremental(s,p,r,a,mode,k):
 M.validate_profile(r);B.publication_checks(s,p)
 try:
  t,old=root(s,a,p,mode,k);cs={};changed=set();summaries={}
  for slot,h in sorted(p['members'].items()):
   b=s.raw_component(h);s.c['eligibility']+=1;f=slot.split(':')[0]
   if old['members'].get(slot)==h and t['profile']['local'][f]==r['local'][f]:
    c=entry(s,t,old,slot)['receipt'];s.c['localReused']+=1;s.c['receiptReads']+=1
   else:c=M.local(s,slot,h,b,r);s.c['invalidations']+=1
   if old['members'].get(slot)!=h:changed.add(slot)
   cs[slot]=c;summaries[slot]=c['summary']
  affected=set(changed)
  if p['context']!=old['context'] or set(p['members'])!=set(old['members']) or r['cross']!=t['profile']['cross']:affected.update(p['members'])
  else:
   for target in sorted(changed):
    sources=entry(s,t,old,target)['sources'];s.c['selectionBuckets']+=1;s.c['selectionEdges']+=len(sources);affected.update(sources)
  for slot in sorted(affected):
   if 'dependencies' not in cs[slot]:
    deps=entry(s,t,old,slot)['dependencies'];s.c['selectionBuckets']+=1;s.c['selectionEdges']+=len(deps);cs[slot]={**cs[slot],'dependencies':deps}
   B.cross(s,p,slot,cs[slot],summaries)
  if not old['context']['requireFresh']:raise ValueError('historical-availability-fallback')
  s.c['crossReused']=sum(c['summary']['dependencyCount'] for x,c in cs.items() if x not in affected)
  return cs,(t,old)
 except M.ERRORS:
  s.c['fallbacks']+=1;cs,_=M.full(s,p,r);return cs,None

def issue(s,p,r,cs,prior,mode,k):
 t,old=prior if prior else (None,None);entries={};reverse_changes={};groups={}
 for slot,c in sorted(cs.items()):
  prev=entry(s,t,old,slot) if t else None;changed=t is None or old['members'].get(slot)!=p['members'][slot]
  rulechange=t is None or t['profile']['local'][slot.split(':')[0]]!=r['local'][slot.split(':')[0]]
  if changed or rulechange:
   receipt={x:v for x,v in c.items() if x!='dependencies'};s.c['evidenceEncodingOps']+=1;rid=sha(encode(receipt));s.c['receiptsCreated']+=1
   if prev and rid!=prev['receiptIdentity']:s.c['supersessions']+=1
  else:receipt=prev['receipt'];rid=prev['receiptIdentity'];s.c['receiptsShared']+=1
  deps=c['dependencies'] if changed else prev['dependencies']
  entries[slot]={'receipt':receipt,'receiptIdentity':rid,'dependencies':deps,'sources':list(prev['sources']) if prev else []}
  if changed:
   s.c['outgoingChanged']+=1
   for d in prev['dependencies'] if prev else []:reverse_changes.setdefault(d['slot'],[set(),set()])[0].add(slot);s.c['maintenanceEdges']+=1
   for d in deps:reverse_changes.setdefault(d['slot'],[set(),set()])[1].add(slot);s.c['maintenanceEdges']+=1
  groups.setdefault(group(slot,k),[]).append(slot);s.c['reverseBookkeepingEntries']+=1
 for target,(remove,add) in sorted(reverse_changes.items()):
  sources=set(entries[target]['sources']);sources.difference_update(remove);sources.update(add);entries[target]['sources']=sorted(sources);s.c['reverseChanged']+=1
 directory={}
 for g,slots in sorted(groups.items()):
  new={x:entries[x] for x in slots};key=slots[0] if mode=='packed' else g
  oldid=t['directory'][key] if t else None
  if oldid and s.get(oldid)['entries']==new:
   h=oldid;s.c['packsReused']+=1
  else:
   h=s.put({'schema':'packed-validation-evidence/v1','implementation':IMPLEMENTATION,'group':g,'packSize':k,'entries':new});s.c['packsCreated']+=1;s.c['packEntriesWritten']+=len(new)
  if mode=='packed':directory.update({x:h for x in slots})
  else:directory[g]=h
 s.put(p);s.c['directoryEntriesWritten']+=len(directory)
 v={'schema':'packed-validation-root/v1','implementation':IMPLEMENTATION,'mode':mode,'packSize':k,'publication':sha(encode(p)),'context':p['context'],'qualifier':p['qualifier'],'profile':r,'directory':directory}
 if mode=='packed':v['members']=p['members']
 return s.put(v)

def execute(s,p,r,mode='full',anchor=None,k=16):
 if mode in ['full','individual']:return M.execute(s,p,r,'full' if mode=='full' else 'incremental',anchor,mode=='individual')
 if mode not in ['packed','shared'] or type(k)!=int or k<1:raise ValueError('candidate')
 s.reset();start=time.perf_counter();a=None
 try:
  cs,prior=(M.full(s,p,r)[0],None) if anchor is None else incremental(s,p,r,anchor,mode,k)
  accepted=True;error=None
 except M.ERRORS as e:accepted=False;error=str(e)
 validation_ms=(time.perf_counter()-start)*1000;validation=dict(s.c);before=dict(s.c)
 evidence_error=None
 if accepted:
  try:a=issue(s,p,r,cs,prior,mode,k)
  except M.ERRORS as e:evidence_error=type(e).__name__+':'+str(e)
 total=(time.perf_counter()-start)*1000
 return {'accepted':accepted,'evidenceError':evidence_error,'error':error,'publication':sha(encode(p)),'anchor':a,'validationMs':validation_ms,'maintenanceMs':total-validation_ms,'totalMs':total,'validation':validation,'maintenance':{x:v-before[x] for x,v in s.c.items()},'total':dict(s.c)}

def commit(s,p,d,mode,fail=False):
 if mode!='full' and (not d.get('anchor') or d.get('evidenceError')):raise ValueError('evidence-not-issued')
 return M.commit(s,p,d,fail)
