"""Frozen workload orchestration; compact outputs, isolated immutable fixtures."""
from pathlib import Path
import argparse,copy,json,statistics,subprocess,sys,time
from core import Store,STATE,PLAN,ROOT,fixture,prepare,update,verdict,encode,sha
HERE=Path(__file__).parent;OUT=ROOT/'docs/research/atlas-validation-reuse-results.json'

def measure(s,p,mode,anchor,rule='v1'):
    runs=[verdict(s,p,mode,anchor,rule) for _ in range(PLAN['repetitions'])]
    assert all(x['accepted']==runs[0]['accepted'] and x['counter']==runs[0]['counter'] for x in runs)
    times=[x['milliseconds'] for x in runs]
    return {k:v for k,v in runs[0].items() if k!='milliseconds'}|{'timingMs':{'median':statistics.median(times),'min':min(times),'max':max(times)}}

def worker(s,h,anchor,mode='incremental',candidate=True):
    start=time.perf_counter();cmd=[sys.executable,str(HERE/'worker.py'),'--store',str(s.path),'--publication',h,'--anchor',anchor,'--mode',mode]
    if candidate:cmd+=['--candidate']
    q=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8');assert q.returncode==0,q.stderr
    v=json.loads(q.stdout);v['startupAndValidationMs']=(time.perf_counter()-start)*1000;return v

def files(s):return {p.name:len(p.read_bytes()) for p in s.objects.glob('*.json')}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--campaign',default='campaign-final');a=p.parse_args()
    if a.check:
        r=json.loads(OUT.read_text(encoding='utf-8'));assert r['planSha256']==sha((HERE/'plan.json').read_bytes())
        assert all(sha((HERE/n).read_bytes())==h for n,h in r['codeHashes'].items())
        assert all(sha(Path(x['path']).read_bytes())==x['sha256'] for x in r['rawFiles'])
        for row in r['cases']:
            s=Store(row['store']);v=s.get(row['publication']);anchor=row['anchor'];rule=row.get('rule','v1')
            full=verdict(s,v,'full',rule=rule);inc=verdict(s,v,'incremental',anchor,rule)
            assert full['accepted']==inc['accepted']==row['expected'],row['id']
            assert full['counter']==row['full']['counter'] and inc['counter']==row['incremental']['counter'],row['id']
        for row in r['history']:
            s=Store(row['store']);s.resolve(row['publication']);assert s.c['membershipReads']==33 and s.c['ancestry']==0
            v=worker(s,row['publication'],row['anchor'],candidate=False);assert v['accepted'] and v['resolution']['membershipReads']==33
        print(json.dumps({'reproducedCases':len(r['cases']),'history':len(r['history']),'zeroDisagreements':True}));return
    assert a.campaign.startswith('campaign') and '/' not in a.campaign and '\\' not in a.campaign
    campaign=STATE/a.campaign;assert not campaign.exists(),'Use a separately frozen campaign, do not overwrite measured fixtures'
    campaign.mkdir();cases=[];raw=[];preparations=[];fresh=[]
    def record(s,q,anchor,id,expected=True,rule='v1',labels=None):
        h=s.put(q);full=measure(s,q,'full',anchor,rule);inc=measure(s,q,'incremental',anchor,rule)
        assert full['accepted']==inc['accepted']==expected,{'id':id,'full':full,'incremental':inc}
        row={'id':id,'store':str(s.path),'publication':h,'anchor':anchor,'rule':rule,'expected':expected,'full':full,'incremental':inc,**(labels or {})};cases.append(row);return row
    for n in PLAN['componentsPerFamily']:
        for fan in PLAN['fanouts']:
            s=Store(campaign/f'n{n}-fan{fan}');start=time.perf_counter();p=fixture(s,n,fan);fixtureMs=(time.perf_counter()-start)*1000
            before=files(s);s.reset();anchor,prep=prepare(s,p);after=files(s)
            preparations.append({'n':n,'fanout':fan,'fixtureMs':fixtureMs,'validationEvidenceBytes':sum(v for k,v in after.items() if k not in before),'evidenceObjects':len(after)-len(before),'preparation':prep,'fixtureBytes':sum(before.values())})
            for pattern in PLAN['changes']:
                s.reset();start=time.perf_counter();q=update(s,p,pattern);construction={'milliseconds':(time.perf_counter()-start)*1000,'counter':dict(s.c)}
                row=record(s,q,anchor,f'n{n}-f{fan}-{pattern}',labels={'n':n,'components':n*3,'records':n*3*64,'fanout':fan,'pattern':pattern,'changedComponents':sum(q['members'][k]!=p['members'][k] for k in p['members']),'construction':construction})
                if n==64 and pattern=='one-local':
                    for mode in ['full','incremental']:
                        runs=[worker(s,row['publication'],anchor,mode) for _ in range(5)]
                        fresh.append({'case':row['id'],'mode':mode,'medianStartupMs':statistics.median(x['startupAndValidationMs'] for x in runs),'rangeStartupMs':[min(x['startupAndValidationMs'] for x in runs),max(x['startupAndValidationMs'] for x in runs)],'medianValidationMs':statistics.median(x['milliseconds'] for x in runs),'rssRange':([min(x['rssObserved'] for x in runs),max(x['rssObserved'] for x in runs)] if all(x['rssObserved'] is not None for x in runs) else None)})
    # Independent boundary stores keep corruption local and replayable.
    mutations={
      'content-hash':('bytes',None,False),'missing-component':('missing',None,False),
      'malformed-metadata':('semantic:0',lambda v:v.update(schema='wrong'),False),
      'invalid-scope':('derived:0',lambda v:v['records'][0].update(inputUse=[9,1]),False),
      'duplicate-key':('semantic:0',lambda v:v['records'][1].update(key=v['records'][0]['key']),False),
      'missing-dependency':('derived:0',lambda v:v.update(dependencies=[]),False),
      'broken-cross-reference':('derived:0',lambda v:v['dependencies'][0].update(slot='terrain:999'),False),
      'changed-dependency-identity':('derived:0',lambda v:v['dependencies'][0].update(identity='0'*64),False),
      'cross-support':('derived:0',lambda v:v['dependencies'][0].update(use=[64,128]),False),
      'incompatible-membership':('membership',None,False),'incomplete-publication':('incomplete',None,False),
      'stale-rule-evidence':('rule',None,True),'unknown-rule':('unknown-rule',None,False),
      'changed-method-policy':('method',None,False),'changed-reference-context':('reference',None,False),
      'historical-stale-allowed':('historical',None,True),'unrecomputed-dependency':('stale',None,False),
      'forged-receipt':('receipt',None,True),'corrupt-receipt-and-invalid-component':('receipt-invalid',None,False),
      'missing-trust-index':('index',None,True),'corrupt-index-and-stale':('index-stale',None,False),'unknown-anchor':('anchor',None,True)}
    for name,(kind,fn,expected) in mutations.items():
        s=Store(campaign/name);p=fixture(s,16,1);anchor,_=prepare(s,p);q=update(s,p);rule='v1'
        if fn:
            v=copy.deepcopy(s.get(q['members'][kind]));fn(v);q['members'][kind]=s.put(v)
        elif kind=='bytes':(s.objects/(q['members']['semantic:0']+'.json')).write_bytes(b'altered')
        elif kind=='missing':(s.objects/(q['members']['semantic:0']+'.json')).unlink()
        elif kind=='membership':q['members']['semantic:0']=q['members']['terrain:0']
        elif kind=='incomplete':q['members'].pop('semantic:0')
        elif kind=='rule':rule='v2'
        elif kind=='unknown-rule':rule='unknown'
        elif kind=='method':q['context']['method']='changed-policy'
        elif kind=='reference':q['context']['reference']='changed-reference'
        elif kind in ['historical','stale','index-stale']:
            q=update(s,p,refresh=False)
            if kind=='historical':q['context']['requireFresh']=False
            if kind=='index-stale':t=s.get(anchor);(s.objects/(t['reverse']['terrain:0']+'.json')).write_bytes(encode({'schema':'validation-reverse/v1','sources':[]}))
        elif kind in ['receipt','receipt-invalid']:
            t=s.get(anchor);(s.objects/(t['receipts']['semantic:0']+'.json')).write_bytes(encode({'schema':'validation-local-receipt/v1','outcome':'valid'}))
            if kind=='receipt-invalid':v=copy.deepcopy(s.get(q['members']['derived:0']));v['dependencies']=[];q['members']['derived:0']=s.put(v)
        elif kind=='index':t=s.get(anchor);(s.objects/(t['reverse']['terrain:0']+'.json')).unlink()
        elif kind=='anchor':anchor='0'*64
        record(s,q,anchor,name,expected,rule,{'n':16,'components':48,'boundary':True})
    history=[];safety=[]
    for depth in PLAN['history']:
        s=Store(campaign/f'history{depth}');p=fixture(s,16,1);anchor,_=prepare(s,p);ids=[];anchors=[]
        for i in range(depth):
            if i:p=update(s,p,'one-local' if i%16==0 else 'none')
            h=s.publish_checked(p,'incremental',anchor);ids.append(h)
            if i%16==0:s.reset();anchor,_=prepare(s,p)
            anchors.append(anchor)
        for label,index in [('oldest',0),('recent',depth-2),('current',depth-1)]:
            s.reset();h=ids[index];s.resolve(h);resolution=dict(s.c);v=worker(s,h,anchors[index],candidate=False)
            history.append({'store':str(s.path),'depth':depth,'selection':label,'publication':h,'anchor':anchors[index],'resolution':resolution,'fresh':v})
        q=update(s,p);candidate=s.put(q);rootBefore=(s.path/'current.json').read_bytes()
        for point in ['after-validation','before-switch']:
            cmd=[sys.executable,str(HERE/'worker.py'),'--store',str(s.path),'--publication',candidate,'--anchor',anchor,'--publish','--fail',point]
            r=subprocess.run(cmd,capture_output=True);assert r.returncode==79,r.stderr
            assert (s.path/'current.json').read_bytes()==rootBefore
            old=worker(s,ids[-1],anchor,candidate=False);assert old['accepted']
            try:s.reset();s.resolve(candidate);raise ValueError('incomplete unexpectedly visible')
            except AssertionError:pass
            safety.append({'depth':depth,'point':point,'exitCode':r.returncode,'currentUnchanged':True,'candidateIneligible':True,'freshAccepted':old['accepted']})
        start=time.perf_counter();new=s.publish_checked(q,'incremental',anchor);publicationMs=(time.perf_counter()-start)*1000
        assert s.resolve(ids[-1])[0]==ids[-1] and s.resolve()[0]==new
        safety.append({'depth':depth,'retryPublished':new,'previousReadable':True,'pinnedUnchanged':True,'publicationMs':publicationMs})
    result={'schema':'atlas-validation-reuse-results/v1','decision':'C - PROOF SUCCESS','planSha256':sha((HERE/'plan.json').read_bytes()),'codeHashes':{n:sha((HERE/n).read_bytes()) for n in ['core.py','run.py','worker.py']},'cases':cases,'preparations':preparations,'fresh':fresh,'history':history,'safety':safety,'disagreements':0,'limitations':['Trusted local verifier and externally pinned anchor; no hostile root/verifier','All current component integrity and membership still population-wide','Synthetic metadata controls; retained qualifiers unchanged; no new physical methods','No OS cache eviction, no remote or concurrent external writes']}
    rawpath=campaign/'observations.json';rawpath.write_bytes(encode(result));result['rawFiles']=[{'path':str(rawpath),'sha256':sha(rawpath.read_bytes())}]
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'cases':len(cases),'history':len(history),'safety':len(safety),'disagreements':0}))

if __name__=='__main__':main()
