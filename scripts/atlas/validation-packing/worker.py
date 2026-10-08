import argparse,json
from model import *
p=argparse.ArgumentParser();p.add_argument('--store');p.add_argument('--publication');p.add_argument('--mode');p.add_argument('--anchor');p.add_argument('--rules');p.add_argument('--pack-size',type=int);a=p.parse_args()
s=Store(a.store);s.reset();_,q=s.resolve(a.publication);resolution=dict(s.c);d=execute(s,q,json.loads(a.rules),a.mode,a.anchor or None,a.pack_size);d.update(resolution=resolution,rssBytes=None);print(json.dumps(d))
