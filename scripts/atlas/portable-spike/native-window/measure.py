"""Fresh-process baseline/shared ownership comparison; no storage-cold claim."""
from pathlib import Path
import argparse
import json
import sys
import time
from window import WindowShared
from shared import SharedProjection
from benchmark import distribution, peak_bytes


def run():
    p=argparse.ArgumentParser(); p.add_argument('--projection',required=True)
    p.add_argument('--mode',choices=['baseline','window'],required=True)
    p.add_argument('--readers',type=int,choices=[1,3],required=True)
    args=p.parse_args(); root=Path(args.projection)
    m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    pins={v['alias']:k for k,v in m['pins'].items()}
    selected=[pins[k] for k in (['after'] if args.readers==1 else ['before','after','legacy'])]
    owner=None; views=[]; start=time.perf_counter()
    try:
        owner=(WindowShared if args.mode=='window' else SharedProjection)(root,m['projectionIdentity']); views=[owner.pin(pin) for pin in selected]
        opened=(time.perf_counter()-start)*1000; peaks={'afterOpen':peak_bytes()}; times={}
        for view in views:
            source=(view.records[next(e['from'] for e in view.edges if e['kind']=='consumes-qualified-source')]['identity']
                    if view.edges else next(r['identity'] for r in view.records.values() if r['family']=='dtm'))
            queries={
                'nativePoint':{'region':'riffelhorn','point':[2624123.875,1091567.125],'crs':'EPSG:2056'},
                'nativeArea':{'region':'riffelhorn','area':[2624111.125,1091555.125,2624222.625,1091777.375],'crs':'EPSG:2056'},
                'identity':{'identity':'glaciers:683'},
                'lineage':{'relatedTo':{'identity':source,'direction':'dependents','depth':'transitive'}}}
            times[view.generation]={}
            for name,q in queries.items():
                answer=view.read(q); samples=[]
                for _ in range(15):
                    start=time.perf_counter(); view.read(q); samples.append((time.perf_counter()-start)*1000)
                times[view.generation][name]={**distribution(samples), 'resultCount':len(answer['results'])}
        peaks['afterQueries']=peak_bytes()
        print(json.dumps({'mode':args.mode,'readerCount':args.readers,'projectionIdentity':m['projectionIdentity'],
            'projectionBytes':sum(p.stat().st_size for p in root.iterdir()),'completeOpenAndViewsMs':opened,
            'ownerVerificationAndGeometryMs':owner.open_ms if owner else None,
            'queriesMs':times,'peakWorkingSetBytes':peaks,'platform':sys.platform,'python':sys.version.split()[0],
            'warmRepetitionsPerQueryPerPin':15,'cacheState':'fresh process; OS storage caches retained'}))
    finally:
        for view in views: view.close()
        if owner: owner.close()

if __name__=='__main__':run()
