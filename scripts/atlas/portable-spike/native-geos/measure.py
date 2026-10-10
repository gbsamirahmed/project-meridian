"""Desktop binding costs, not mobile predictions or a geometry allocator profile."""
import argparse
import json
from pathlib import Path
import statistics
import sys
import time
from contextlib import nullcontext
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'geometry-crs'))
from resources import memory
from native import NativeGeos

def repeated(call,count):
    values=[]
    for _ in range(count):
        start=time.perf_counter();call();values.append((time.perf_counter()-start)*1000)
    return {'medianMs':statistics.median(values),'minMs':min(values),'maxMs':max(values),'repetitions':count}

def primitive(mode):
    before=memory();start=time.perf_counter()
    if mode=='native':
        ctx=NativeGeos();construct=ctx.box;point=ctx.point;mapping=ctx.mapping
        scope=ctx.arena
    else:
        from shapely.geometry import box,Point,mapping
        construct=box;point=Point;ctx=None;scope=nullcontext
    init=(time.perf_counter()-start)*1000;after=memory()
    g=construct(0,0,4,4);p=point(0,2);second=construct(3,0,5,4)
    def create_destroy():
        with scope():
            v=construct(0,0,4,4);q=point(1,2);v.covers(q)
    rows={'constructDestroy':repeated(create_destroy,1000),'covers':repeated(lambda:g.covers(p),1000),
          'intersection':repeated(lambda:g.intersection(second).area,500),
          'wkbWrite':repeated(lambda:g.wkb,500),'mapping':repeated(lambda:mapping(g),500)}
    if ctx: rows['wkbRead']=repeated(lambda:ctx.from_wkb(g.wkb),500)
    else:
        import shapely
        rows['wkbRead']=repeated(lambda:shapely.from_wkb(g.wkb),500)
    result={'mode':mode,'initialisationMs':init,'before':before,'afterInitialisation':after,
            'afterOperations':memory(),'operations':rows,'identity':ctx.identity if ctx else None,
            'runtimeImports':{name:name in sys.modules for name in ['shapely','numpy','pyproj','rasterio']}}
    if ctx:
        g.close();p.close();second.close();result['remainingOwnedGeometries']=len(ctx.owned);ctx.close()
    result['afterClose']=memory()
    return result

def reader_trial(root,mode,views):
    from adapter import NativeSession
    from window import WindowShared
    m=json.loads((Path(root)/'manifest.json').read_text());aliases={v['alias']:k for k,v in m['pins'].items()}
    pins=[aliases[v] for v in (['after'] if views==1 else ['before','after','legacy'])]
    start=time.perf_counter();factory=NativeSession if mode=='native' else WindowShared
    opened=[]
    with factory(root,m['projectionIdentity']) as owner:
        try:
            opened=[owner.pin(pin) for pin in pins];open_ms=(time.perf_counter()-start)*1000;initial=memory();rows={}
            for view in opened:
                seed=view.records[next(e['from'] for e in view.edges if e['kind']=='consumes-qualified-source')]['identity'] if view.edges else 'glaciers:683'
                queries={'point':{'region':'riffelhorn','point':[2624123.875,1091567.125],'crs':'EPSG:2056'},
                         'area':{'region':'riffelhorn','area':[2624111.125,1091555.125,2624222.625,1091777.375],'crs':'EPSG:2056'},
                         'identity':{'identity':'glaciers:683'},'lineage':{'relatedTo':{'identity':seed,'direction':'dependents','depth':'transitive'}}}
                rows[view.generation]={}
                for name,q in queries.items():
                    view.read(q);rows[view.generation][name]=repeated(lambda:view.read(q),10)
            return {'mode':mode,'views':views,'completeOpenMs':open_ms,'initialMemory':initial,'finalMemory':memory(),
                    'queries':rows,'nativeOwnedGeometries':len(owner.geometry.owned) if mode=='native' else None,
                    'method':'fresh interpreter; retained OS file caches; shared owner and explicit pins; native context and WKB feature copies included'}
        finally:
            for view in opened:view.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['native','reference'],required=True)
    p.add_argument('--workload',choices=['primitive','reader'],required=True);p.add_argument('--projection');p.add_argument('--views',choices=[1,3],type=int,default=3);a=p.parse_args()
    print(json.dumps(primitive(a.mode) if a.workload=='primitive' else reader_trial(a.projection,a.mode,a.views),indent=2))
