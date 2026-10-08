"""Fresh-process verifier; caller supplies a previously trusted anchor explicitly."""
import argparse,json,os
from core import Store,verdict
p=argparse.ArgumentParser();p.add_argument('--store',required=True);p.add_argument('--publication');p.add_argument('--anchor');p.add_argument('--mode',default='incremental');p.add_argument('--rule',default='v1');p.add_argument('--candidate',action='store_true');p.add_argument('--publish',action='store_true');p.add_argument('--fail',choices=['after-validation','before-switch'])
a=p.parse_args();s=Store(a.store)
if a.publish:
    v=s.get(a.publication);s.publish_checked(v,a.mode,a.anchor,a.rule,a.fail)
    if a.fail:os._exit(79)
    print(json.dumps({'current':s.root()['generation']}))
else:
    if a.publication and a.candidate:v=s.get(a.publication)
    else:_,v=s.resolve(a.publication)
    resolution=dict(s.c)
    result=verdict(s,v,a.mode,a.anchor,a.rule)
    result['resolution']=resolution
    try:
        import psutil
        result['rssObserved']=psutil.Process().memory_info().rss
    except ImportError:result['rssObserved']=None
    print(json.dumps(result))
