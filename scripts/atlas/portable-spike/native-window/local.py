"""Thin explicit experimental store commands; lifecycle code remains in Store."""
import argparse
import json
import sys
from window import WindowStore,WindowShared,ReadError

p=argparse.ArgumentParser();p.add_argument('operation',choices=['init','install','query','delete'])
p.add_argument('--store',required=True);p.add_argument('--projection');p.add_argument('--identity');p.add_argument('--generation');p.add_argument('--query',default='{"identity":"glaciers:683"}')
a=p.parse_args()
try:
    if a.operation=='init':WindowStore.create(a.store);result={'kind':'initialised'}
    else:
        store=WindowStore(a.store)
        if a.operation=='install':result=store.install(a.projection,a.identity)
        elif a.operation=='delete':store.delete(a.identity);result={'kind':'deleted'}
        else:
            with WindowShared.from_store(store,a.identity) as owner,owner.pin(a.generation) as view:result=view.outcome(json.loads(a.query))
    print(json.dumps(result,ensure_ascii=False,allow_nan=False));sys.exit(1 if result.get('kind')=='error' else 0)
except (ReadError,OSError,ValueError,TypeError) as e:
    print(json.dumps({'kind':'error','code':e.code if isinstance(e,ReadError) else 'experiment-request','message':str(e) if isinstance(e,ReadError) else 'Check explicit paths, identity, generation and request.'}));sys.exit(1)
