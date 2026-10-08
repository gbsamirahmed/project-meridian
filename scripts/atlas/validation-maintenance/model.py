"""Isolated receipt lifecycle adapter; no production imports or acceptance shortcuts."""
from pathlib import Path
import copy, importlib.util, json, os, time
HERE=Path(__file__).parent;ROOT=HERE.resolve().parents[2]
PLAN=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('reuse_core',ROOT/'scripts/atlas/validation-reuse/core.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
STATE=Path(PLAN['stateRoot']);STATE.mkdir(exist_ok=True);B.G.STATE=STATE
encode=B.encode;sha=B.sha
IMPLEMENTATION=sha(Path(__file__).read_bytes()+(ROOT/'scripts/atlas/validation-reuse/core.py').read_bytes()+(ROOT/'scripts/atlas/component-granularity/model.py').read_bytes())
ERRORS=(ValueError,KeyError,FileNotFoundError,TypeError,json.JSONDecodeError,AssertionError)
EXTRA=['evidenceLookup','eligibility','invalidations','receiptsCreated','receiptsShared','supersessions','outgoingChanged','reverseChanged','directoryWritten','relationshipInvalidations','maintenanceEdges']
class Store(B.Store):
    def reset(self):
        super().reset();self.c.update({k:0 for k in EXTRA})

def profile():return {'local':{f:1 for f in B.FAMILIES},'cross':1,'publication':1}
def validate_profile(r):
    if set(r)!={'local','cross','publication'} or set(r['local'])!=set(B.FAMILIES) or not all(type(x)==int and x>0 for x in [*r['local'].values(),r['cross'],r['publication']]):raise ValueError('rule-profile')
def rid(kind,revision):return sha(encode({'implementation':IMPLEMENTATION,'kind':kind,'revision':revision}))
def local(s,slot,h,b,r):
    c=B.local(s,slot,h,b,'v1');c['rule']=rid('local:'+slot.split(':')[0],r['local'][slot.split(':')[0]]);return c

def full(s,p,r):
    validate_profile(r);B.publication_checks(s,p)
    cs={slot:local(s,slot,h,s.raw_component(h),r) for slot,h in sorted(p['members'].items())}
    sums={k:v['summary'] for k,v in cs.items()}
    for slot,c in cs.items():B.cross(s,p,slot,c,sums)
    return cs, None

def incremental(s,p,r,anchor):
    validate_profile(r);B.publication_checks(s,p)
    try:
        t=s.get(anchor);s.c['evidenceLookup']+=1
        if t['schema']!='maintenance-trust-root/v1' or t['implementation']!=IMPLEMENTATION or t['qualifier']!=p['qualifier']:raise ValueError('trust')
        old=s.get(t['publication'])
        if old['members']!=t['members'] or old['context']!=t['context']:raise ValueError('trust-context')
        s.c['trustDirectoryEntries']+=len(t['members']);cs={};content_changed=set();sums={}
        for slot,h in sorted(p['members'].items()):
            b=s.raw_component(h);s.c['eligibility']+=1
            eligible=t['members'].get(slot)==h and t['profile']['local'][slot.split(':')[0]]==r['local'][slot.split(':')[0]]
            if eligible:
                c=s.get(t['receipts'][slot]);s.c['evidenceLookup']+=1;s.c['receiptReads']+=1
                if c.get('schema')!='validation-local-receipt/v1' or c.get('component')!=h or c.get('rule')!=rid('local:'+slot.split(':')[0],r['local'][slot.split(':')[0]]) or c.get('outcome')!='valid' or c.get('guarantee')!='component-local-only':raise ValueError('receipt-ineligible')
                s.c['localReused']+=1
            else:
                c=local(s,slot,h,b,r);s.c['invalidations']+=1
            if t['members'].get(slot)!=h:content_changed.add(slot)
            cs[slot]=c;sums[slot]=c['summary']
        affected=set(content_changed)
        if p['context']!=t['context'] or set(p['members'])!=set(t['members']) or r['cross']!=t['profile']['cross']:
            affected.update(p['members']);s.c['relationshipInvalidations']+=sum(c['summary']['dependencyCount'] for c in cs.values())
        else:
            for target in sorted(content_changed):
                b=s.get(t['reverse'][target]);s.c['selectionBuckets']+=1;s.c['selectionEdges']+=len(b['sources']);affected.update(b['sources'])
        for slot in sorted(affected):
            if 'dependencies' not in cs[slot]:
                b=s.get(t['outgoing'][slot]);s.c['selectionBuckets']+=1;s.c['selectionEdges']+=len(b['dependencies']);cs[slot]={**cs[slot],'dependencies':b['dependencies']}
            B.cross(s,p,slot,cs[slot],sums)
        if not t['context']['requireFresh']:raise ValueError('historical-availability-fallback')
        s.c['crossReused']=sum(c['summary']['dependencyCount'] for slot,c in cs.items() if slot not in affected)
        return cs,t
    except ERRORS:
        s.c['fallbacks']+=1
        return full(s,p,r)

def issue(s,p,r,cs,t):
    # Called only by execute after its own successful validator dispatch. Carry
    # forward prior authenticated maps; update precisely changed adjacency buckets.
    receipts=dict(t['receipts']) if t else {};out=dict(t['outgoing']) if t else {};reverse=dict(t['reverse']) if t else {};changes={}
    for slot,c in sorted(cs.items()):
        changed=t is None or t['members'].get(slot)!=p['members'][slot]
        rule_changed=t is None or t['profile']['local'][slot.split(':')[0]]!=r['local'][slot.split(':')[0]]
        if changed or rule_changed:
            h=s.put({k:v for k,v in c.items() if k!='dependencies'});s.c['receiptsCreated']+=1
            if t and h!=receipts.get(slot):s.c['supersessions']+=1
            receipts[slot]=h
        else:s.c['receiptsShared']+=1
        if changed:
            deps=c['dependencies'];old=s.get(t['outgoing'][slot])['dependencies'] if t else []
            out[slot]=s.put({'schema':'validation-outgoing/v1','dependencies':deps});s.c['outgoingChanged']+=1
            for d in old:changes.setdefault(d['slot'],[set(),set()])[0].add(slot);s.c['maintenanceEdges']+=1
            for d in deps:changes.setdefault(d['slot'],[set(),set()])[1].add(slot);s.c['maintenanceEdges']+=1
    for target in sorted(p['members']):
        if not t or target in changes:
            sources=set(s.get(t['reverse'][target])['sources']) if t else set()
            remove,add=changes.get(target,(set(),set()));sources.difference_update(remove);sources.update(add)
            reverse[target]=s.put({'schema':'validation-reverse/v1','sources':sorted(sources)});s.c['reverseChanged']+=1
    s.put(p);s.c['directoryWritten']+=len(p['members'])*4
    return s.put({'schema':'maintenance-trust-root/v1','implementation':IMPLEMENTATION,'profile':r,'publication':sha(encode(p)),'context':p['context'],'members':p['members'],'qualifier':p['qualifier'],'receipts':receipts,'outgoing':out,'reverse':reverse})

def execute(s,p,r,mode='full',anchor=None,maintain=False):
    s.reset();start=time.perf_counter();new_anchor=None
    try:
        cs,t=full(s,p,r) if mode=='full' or anchor is None else incremental(s,p,r,anchor)
        accepted=True;error=None
    except ERRORS as e:accepted=False;error=str(e)
    validate_ms=(time.perf_counter()-start)*1000;validation=dict(s.c);before=dict(s.c)
    if accepted and maintain:new_anchor=issue(s,p,r,cs,t)
    total_ms=(time.perf_counter()-start)*1000
    return {'accepted':accepted,'error':error,'publication':sha(encode(p)),'anchor':new_anchor,'validationMs':validate_ms,'maintenanceMs':total_ms-validate_ms,'totalMs':total_ms,'validation':validation,'maintenance':{k:v-before[k] for k,v in s.c.items()},'total':dict(s.c)}

def commit(s,p,decision,fail=False):
    # Private experiment sequence calls with execute's just-created acceptance;
    # normal external callers use publish() to validate internally.
    if not decision['accepted'] or decision['publication']!=sha(encode(p)):raise ValueError('not-accepted')
    s.reset();start=time.perf_counter()
    for h in p['members'].values():s.raw_component(h)
    h=s.put(p);old=s.root() if (s.path/'current.json').exists() else None
    if p['predecessor']!=(old['generation'] if old else None):raise ValueError('predecessor')
    witness=s.insert(old['membership'] if old else None,h)
    if not fail:
        temp=s.path/'current.pending'
        with temp.open('wb') as f:f.write(encode({'schema':'atlas-component-root/v1','generation':h,'membership':witness}));f.flush();os.fsync(f.fileno())
        os.replace(temp,s.path/'current.json')
    return {'publication':h,'milliseconds':(time.perf_counter()-start)*1000,'counter':dict(s.c),'committed':not fail}

def publish(s,p,r,anchor=None,fail=False):
    d=execute(s,p,r,'incremental',anchor,True)
    if not d['accepted']:raise ValueError(d['error'])
    return d,commit(s,p,d,fail)

def update(s,p,pattern,step,fanout):
    q=copy.deepcopy(p);n=p['population']
    indices=[] if pattern=='none' else [step%n] if pattern=='local' else sorted({step%n,(step+n//3)%n,(step+2*n//3)%n,(step+n-1)%n}) if pattern=='scattered' else list(range(n//2)) if pattern=='half' else list(range(n))
    for i in indices:
        slot=f'terrain:{i}';v=copy.deepcopy(s.get(q['members'][slot]));v['records'][0]['revision']+=1;q['members'][slot]=s.put(v)
    for slot,h in sorted(q['members'].items()):
        if not slot.startswith('derived:'):continue
        v=copy.deepcopy(s.get(h));changed=False
        for d in v['dependencies']:
            if d['identity']!=q['members'][d['slot']]:d['identity']=q['members'][d['slot']];changed=True
        if changed:v['records'][0]['revision']+=1;q['members'][slot]=s.put(v)
    q['predecessor']=sha(encode(p));q['ordinal']+=1;return q

def revise(r,kind,step,p):
    r=copy.deepcopy(r)
    if step%PLAN['ruleInterval']==0:
        if kind in ['terrain','all']:
            for f in (B.FAMILIES if kind=='all' else ['terrain']):r['local'][f]+=1
        if kind in ['cross','all']:r['cross']+=1
        if kind in ['publication','all']:r['publication']+=1
    if kind=='context' and step%4==0:p['context']['requireFresh']=not p['context']['requireFresh']
    return r
