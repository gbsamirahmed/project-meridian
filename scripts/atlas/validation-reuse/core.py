"""Bounded validation-reuse proof. No production imports depend on this model."""
from pathlib import Path
import copy, hashlib, importlib.util, json, os, time
ROOT=Path(__file__).resolve().parents[3]
PLAN=json.loads((Path(__file__).parent/'plan.json').read_text(encoding='utf-8'))
STATE=Path(PLAN['stateRoot']);STATE.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('granularity',ROOT/'scripts/atlas/component-granularity/model.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G);G.STATE=STATE
encode=G.encode;sha=G.sha
IMPLEMENTATION=sha(Path(__file__).read_bytes()+(ROOT/'scripts/atlas/component-granularity/model.py').read_bytes())
METHOD='7fe3f0c3ed6152177dfcb97b7be190dcda8fd45ddb18b27c2a8eb2b2b398f8d9'
FAMILIES=('terrain','semantic','derived')
QUALIFIER={'schema':'validation-native-qualifier/v1','retained':G.templates()}
QUALIFIER_ID=sha(encode(QUALIFIER))

def rule_id(rule):
    if rule not in ('v1','v2'):raise ValueError('unknown-rule')
    return sha(encode({'rule':rule,'implementation':IMPLEMENTATION}))

class Store(G.Store):
    def reset(self):
        super().reset()
        self.c.update({k:0 for k in ['localChecks','localReused','rowsChecked','crossChecks','crossReused','membershipChecks','receiptReads','selectionBuckets','selectionEdges','trustDirectoryEntries','componentIntegrity','fallbacks','componentsParsed','publicationChecks']})
    def raw_component(self,h):
        if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('component-id')
        b=(self.objects/(h+'.json')).read_bytes()
        self.c['objectReads']+=1;self.c['metadataBytes']+=len(b);self.c['hashChecks']+=1;self.c['hashedBytes']+=len(b);self.c['componentIntegrity']+=1
        if sha(b)!=h:raise ValueError('component-integrity')
        return b
    def publish_checked(self,p,mode='full',anchor=None,rule='v1',fail=None):
        decision=verdict(self,p,mode,anchor,rule)
        if not decision['accepted']:raise ValueError('publication-not-accepted: '+str(decision['error']))
        # A verdict authorizes exactly this immutable closure; recheck availability
        # immediately before switch. Sequential writer; concurrent external writes excluded.
        for h in p['members'].values():self.raw_component(h)
        h=self.put(p);prior=self.root() if (self.path/'current.json').exists() else None
        if p['predecessor']!=(prior['generation'] if prior else None):raise ValueError('predecessor')
        if fail=='after-validation':return h
        witness=self.insert(prior['membership'] if prior else None,h)
        if fail=='before-switch':return h
        temp=self.path/'current.pending'
        with temp.open('wb') as f:
            f.write(encode({'schema':'atlas-component-root/v1','generation':h,'membership':witness}));f.flush();os.fsync(f.fileno())
        os.replace(temp,self.path/'current.json');return h


def component(s,f,i,n,fanout,members):
    scope=[i*64,(i+1)*64]
    deps=[{'slot':f'terrain:{(i+j)%n}','identity':members[f'terrain:{(i+j)%n}'],'use':[((i+j)%n)*64,((i+j)%n+1)*64]} for j in range(fanout)] if f=='derived' else []
    return {'schema':'validation-component/v1','family':f,'partition':i,'scope':scope,'method':METHOD if f=='derived' else None,'records':[{'key':f'{f}:{i*64+j}','support':[i*64+j,i*64+j+1],'inputUse':[i*64+j,i*64+j+1] if f=='derived' else None,'revision':0,'nativeTemplate':f} for j in range(64)],'dependencies':deps}


def fixture(s,n,fanout=1):
    members={}
    for f in FAMILIES:
        for i in range(n):members[f'{f}:{i}']=s.put(component(s,f,i,n,fanout,members))
    # Exact retained native qualifications remain separate from synthetic identities.
    q=s.put(QUALIFIER)
    return {'schema':'granularity-publication/v1','members':members,'population':n,'qualifier':q,'predecessor':None,'ordinal':1,'context':{'method':METHOD,'reference':'retained-context','requireFresh':True}}


def local(s,slot,h,b,rule):
    s.c['localChecks']+=1;s.c['componentsParsed']+=1
    v=json.loads(b)
    if encode(v)!=b or set(v)!={'schema','family','partition','scope','method','records','dependencies'}:raise ValueError('component-shape')
    f,i=slot.split(':');i=int(i)
    if v['schema']!='validation-component/v1' or v['family']!=f or v['partition']!=i or v['scope']!=[i*64,(i+1)*64] or len(v['records'])!=64:raise ValueError('component-descriptor')
    for j,r in enumerate(v['records']):
        s.c['rowsChecked']+=1
        if set(r)!={'key','support','inputUse','revision','nativeTemplate'} or r['key']!=f'{f}:{i*64+j}' or r['support']!=[i*64+j,i*64+j+1] or r['nativeTemplate']!=f or type(r['revision'])!=int or r['revision']<0:raise ValueError('record-structure')
        if r['inputUse']!=([i*64+j,i*64+j+1] if f=='derived' else None):raise ValueError('input-use-scope')
    if v['method']!=(METHOD if f=='derived' else None) or f!='derived' and v['dependencies']:raise ValueError('method-or-dependency-kind')
    deps=v['dependencies']
    if not isinstance(deps,list) or len({d['slot'] for d in deps})!=len(deps):raise ValueError('dependency-uniqueness')
    for d in deps:
        if set(d)!={'slot','identity','use'} or not d['slot'].startswith('terrain:') or len(d['identity'])!=64 or len(d['use'])!=2 or not all(type(x)==int for x in d['use']) or d['use'][0]>=d['use'][1]:raise ValueError('dependency-shape')
    if f=='derived' and not deps:raise ValueError('missing-dependency')
    return {'schema':'validation-local-receipt/v1','component':h,'rule':rule_id(rule),'outcome':'valid','guarantee':'component-local-only','summary':{'family':f,'scope':v['scope'],'method':v['method'],'count':64,'dependencyCount':len(deps)},'dependencies':deps}


def publication_checks(s,p):
    s.c['publicationChecks']+=1
    if set(p)!={'schema','members','population','qualifier','predecessor','ordinal','context'} or p['schema']!='granularity-publication/v1' or type(p['population'])!=int or p['population']<1 or type(p['ordinal'])!=int or p['ordinal']<1:raise ValueError('publication-shape')
    n=p['population'];expected={f'{f}:{i}' for f in FAMILIES for i in range(n)}
    if set(p['members'])!=expected or len(set(p['members'].values()))!=len(expected):raise ValueError('publication-completeness')
    context=p['context']
    if set(context)!={'method','reference','requireFresh'} or type(context['requireFresh'])!=bool or not isinstance(context['method'],str) or not context['method'] or not isinstance(context['reference'],str):raise ValueError('context')
    for slot,h in sorted(p['members'].items()):
        s.c['membershipChecks']+=1
        if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('membership-identity')
    if p['predecessor'] is not None and (not isinstance(p['predecessor'],str) or len(p['predecessor'])!=64):raise ValueError('publication-predecessor')
    qualifier=s.get(p['qualifier'])
    if p['qualifier']!=QUALIFIER_ID:raise ValueError('native-qualification')


def cross(s,p,slot,cert,summaries):
    for d in cert['dependencies']:
        s.c['crossChecks']+=1
        if d['slot'] not in summaries or summaries[d['slot']]['family']!='terrain' or d['use']!=summaries[d['slot']]['scope']:raise ValueError('broken-cross-reference')
        # Historical input identity must still exist and remain structurally valid.
        # Current input mismatch is policy-relative staleness, not historical falsity.
        if d['identity']!=p['members'][d['slot']]:
            historical=local(s,d['slot'],d['identity'],s.raw_component(d['identity']),'v1')
            if historical['summary']['scope']!=d['use']:raise ValueError('historical-input')
        fresh=d['identity']==p['members'][d['slot']] and cert['summary']['method']==p['context']['method'] and p['context']['reference']=='retained-context'
        if p['context']['requireFresh'] and not fresh:raise ValueError('policy-stale')


def full(s,p,rule='v1'):
    rule_id(rule);publication_checks(s,p);certs={}
    for slot,h in sorted(p['members'].items()):certs[slot]=local(s,slot,h,s.raw_component(h),rule)
    summaries={k:v['summary'] for k,v in certs.items()}
    for slot,cert in certs.items():cross(s,p,slot,cert,summaries)
    return certs


def prepare(s,p,rule='v1'):
    start=time.perf_counter();certs=full(s,p,rule);s.put(p);reverse={k:[] for k in p['members']};out={};receipts={}
    for slot,c in certs.items():
        # Local receipt excludes contextual edges; edge buckets separately anchored.
        receipts[slot]=s.put({k:v for k,v in c.items() if k!='dependencies'})
        out[slot]=s.put({'schema':'validation-outgoing/v1','dependencies':c['dependencies']})
        for d in c['dependencies']:reverse[d['slot']].append(slot)
    index={k:s.put({'schema':'validation-reverse/v1','sources':sorted(v)}) for k,v in reverse.items()}
    h=s.put({'schema':'validation-trust-root/v1','rule':rule_id(rule),'publication':sha(encode(p)),'context':p['context'],'members':p['members'],'qualifier':p['qualifier'],'receipts':receipts,'outgoing':out,'reverse':index})
    return h,{'milliseconds':(time.perf_counter()-start)*1000,'counter':dict(s.c)}


def incremental(s,p,anchor,rule='v1'):
    rule_id(rule);publication_checks(s,p)
    # Authenticity is supplied by a caller-pinned root from a known successful
    # verifier. A candidate cannot designate its own trusted receipt root.
    try:
        t=s.get(anchor)
        if t['schema']!='validation-trust-root/v1' or t['rule']!=rule_id(rule) or t['qualifier']!=p['qualifier']:raise ValueError('trust-ineligible')
        old=s.get(t['publication']);s.c['trustDirectoryEntries']+=len(t['members'])
        if old['members']!=t['members'] or old['context']!=t['context']:raise ValueError('trust-context')
        certs={};changed=set();summaries={}
        for slot,h in sorted(p['members'].items()):
            b=s.raw_component(h)
            if t['members'].get(slot)==h:
                c=s.get(t['receipts'][slot]);s.c['receiptReads']+=1
                if c.get('component')!=h or c.get('rule')!=rule_id(rule) or c.get('outcome')!='valid' or c.get('guarantee')!='component-local-only':raise ValueError('receipt-ineligible')
                s.c['localReused']+=1
            else:
                c=local(s,slot,h,b,rule);changed.add(slot)
            certs[slot]=c;summaries[slot]=c['summary']
        affected=set(changed)
        context_change=p['context']!=t['context'] or set(p['members'])!=set(t['members'])
        if context_change:affected.update(p['members'])
        else:
            for target in sorted(changed):
                bucket=s.get(t['reverse'][target]);s.c['selectionBuckets']+=1;s.c['selectionEdges']+=len(bucket['sources']);affected.update(bucket['sources'])
        for slot in sorted(affected):
            if slot not in p['members']:continue
            if slot not in changed:
                bucket=s.get(t['outgoing'][slot]);s.c['selectionBuckets']+=1;s.c['selectionEdges']+=len(bucket['dependencies']);certs[slot]={**certs[slot],'dependencies':bucket['dependencies']}
            cross(s,p,slot,certs[slot],summaries)
        # Reused cross checks rely on unchanged endpoints/context AND anchored
        # old acceptance. Still verify historical dependency bytes in the trust
        # closure when context allowed stale inputs, not just current objects.
        if not t['context']['requireFresh']:
            return fallback(s,p,rule)
        s.c['crossReused']=sum(c['summary']['dependencyCount'] for slot,c in certs.items() if slot not in affected)
        return certs
    except (ValueError,KeyError,FileNotFoundError,TypeError,json.JSONDecodeError,AssertionError):
        return fallback(s,p,rule)


def fallback(s,p,rule):
    s.c['fallbacks']+=1;return full(s,p,rule)


def verdict(s,p,mode,anchor=None,rule='v1'):
    s.reset();start=time.perf_counter()
    try:
        if mode=='full':full(s,p,rule)
        elif mode=='incremental':incremental(s,p,anchor,rule)
        else:raise ValueError('mode')
        accepted=True;error=None
    except (ValueError,KeyError,FileNotFoundError,TypeError,json.JSONDecodeError,AssertionError) as e:accepted=False;error=str(e)
    return {'accepted':accepted,'error':error,'publication':sha(encode(p)),'milliseconds':(time.perf_counter()-start)*1000,'counter':dict(s.c)}


def update(s,p,pattern='one-local',refresh=True):
    q=copy.deepcopy(p);n=p['population'];indices=[] if pattern=='none' else [0] if pattern=='one-local' else sorted(set([0,n//3,2*n//3,n-1])) if pattern=='four-scattered' else list(range(max(1,n//4)))
    for i in indices:
        slot=f'terrain:{i}';v=copy.deepcopy(s.get(q['members'][slot]));v['records'][0]['revision']+=1;q['members'][slot]=s.put(v)
    if refresh:
        for slot,h in sorted(q['members'].items()):
            if not slot.startswith('derived:'):continue
            v=copy.deepcopy(s.get(h));changed=False
            for d in v['dependencies']:
                if q['members'][d['slot']]!=d['identity']:d['identity']=q['members'][d['slot']];changed=True
            if changed:v['records'][0]['revision']+=1;q['members'][slot]=s.put(v)
    q['predecessor']=sha(encode(p));q['ordinal']+=1;return q
