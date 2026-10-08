import argparse,json
from model import *
p=argparse.ArgumentParser();p.add_argument('--store');p.add_argument('--publication');p.add_argument('--anchor');p.add_argument('--rules');a=p.parse_args()
s=Store(a.store);start=time.perf_counter();s.reset();_,q=s.resolve(a.publication);resolution=dict(s.c)
d=execute(s,q,json.loads(a.rules),'incremental',a.anchor)
d.update(resolution=resolution,startupExcludedMs=(time.perf_counter()-start)*1000,rssBytes=None)
print(json.dumps(d))
