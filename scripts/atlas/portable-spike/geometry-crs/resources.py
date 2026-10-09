"""Small desktop inventory/import/resource driver; no mobile or allocation claims."""
from pathlib import Path
import argparse
from contextlib import nullcontext
import ctypes as C
import hashlib
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import platform
import shutil
import statistics
import sys
import time


def memory():
    if sys.platform != 'win32': return {'current':None,'peak':None}
    class Counters(C.Structure):
        _fields_=[('cb',C.c_ulong),('faults',C.c_ulong)]+[(k,C.c_size_t) for k in
                 ['peak','working','peakPaged','paged','peakNonpaged','nonpaged','pagefile','peakPagefile']]
    data=Counters(); data.cb=C.sizeof(data)
    C.windll.kernel32.GetCurrentProcess.restype=C.c_void_p
    C.windll.psapi.GetProcessMemoryInfo.argtypes=[C.c_void_p,C.c_void_p,C.c_ulong]
    if not C.windll.psapi.GetProcessMemoryInfo(C.windll.kernel32.GetCurrentProcess(),C.byref(data),data.cb):
        raise RuntimeError('Process memory observation failed.')
    return {'current':data.working,'peak':data.peak}


def inventory():
    result={'python':platform.python_version(),'os':platform.platform(),'packages':{},'tools':{},'localCandidates':{}}
    for name in ['numpy','shapely','pyproj','rasterio']:
        module=importlib.import_module(name); root=Path(module.__file__).parent
        dll=root.parent/(name+'.libs')
        members=[p for folder in [root,dll] if folder.exists() for p in folder.rglob('*') if p.is_file()]
        licence_files=[p for p in metadata.distribution(name).files or [] if 'license' in str(p).lower() or 'copying' in str(p).lower()]
        result['packages'][name]={'version':module.__version__,'installedBytes':sum(p.stat().st_size for p in members),
            'packageBytes':sum(p.stat().st_size for p in root.rglob('*') if p.is_file()),
            'companionBytes':sum(p.stat().st_size for p in dll.rglob('*') if p.is_file()) if dll.exists() else 0,
            'nativeVersion':getattr(module,'__gdal_version__',getattr(module,'geos_version_string',getattr(module,'proj_version_str',None))),
            'licenceFiles':[str(p) for p in licence_files],
            'dlls':[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in members if p.suffix=='.dll']}
    import pyproj
    database=Path(pyproj.datadir.get_data_dir())/'proj.db'
    result['projDatabase']={'bytes':database.stat().st_size,'sha256':hashlib.sha256(database.read_bytes()).hexdigest()}
    from pyproj.transformer import TransformerGroup
    result['operations']=[{'pipeline':t.definition,'accuracyMetres':t.accuracy} for t in TransformerGroup(2056,4326,always_xy=True).transformers]
    # Presence on PATH is not an exhaustive device/build-access inventory.
    for name in ['node','java','javac','gradle','cmake','clang','gcc','adb','dotnet','emcc','xcodebuild']:
        result['tools'][name]=shutil.which(name) is not None
    result['localCandidates']['osgeoPython']=importlib.util.find_spec('osgeo') is not None
    repo=Path(__file__).resolve().parents[4]
    for name in ['jsts','proj4','geos-wasm','gdal3.js']:
        result['localCandidates'][name]=(repo/'node_modules'/name/'package.json').is_file()
    return result


def imports(mode):
    rows=[{'stage':'standardLibrary','memory':memory()}]
    if mode=='native':
        from native_proj import NativeProj
        start=time.perf_counter()
        with NativeProj() as binding:
            binding.xy([2625000],[1092000],'EPSG:2056','EPSG:4326')
            rows.append({'stage':'ctypesPROJDatabaseTransform','ms':(time.perf_counter()-start)*1000,'memory':memory(),'identity':binding.identity})
            if 'pyproj' in sys.modules or 'numpy' in sys.modules or 'shapely' in sys.modules or 'rasterio' in sys.modules:
                raise AssertionError('Direct XY unexpectedly imported Python GIS bindings.')
    else:
        for name in ['numpy','shapely','pyproj','rasterio']:
            start=time.perf_counter(); importlib.import_module(name)
            if name=='pyproj':
                import pyproj
                pyproj.network.set_network_enabled(False)
                pyproj.Transformer.from_crs(2056,4326,always_xy=True).transform(2625000,1092000)
            rows.append({'stage':name,'ms':(time.perf_counter()-start)*1000,'memory':memory()})
    return {'mode':mode,'stages':rows,'method':'sequential imports; current/peak working set, not allocation attribution'}


def reader_trial(projection,mode,count):
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'native-window'))
    from window import WindowShared
    from native_proj import NativeProj, comparison_binding
    root=Path(projection);m=json.loads((root/'manifest.json').read_text())
    aliases={v['alias']:k for k,v in m['pins'].items()}
    pins=[aliases[a] for a in (['after'] if count==1 else ['before','after','legacy'])]
    start=time.perf_counter();views=[]
    with WindowShared(root,m['projectionIdentity']) as owner:
        try:
            views=[owner.pin(pin) for pin in pins]; opened=(time.perf_counter()-start)*1000
            before=memory(); samples={}
            with (NativeProj() if mode=='native' else nullcontext()) as binding:
                with (comparison_binding(binding) if binding else nullcontext()):
                    for view in views:
                        seed=view.records[next(e['from'] for e in view.edges if e['kind']=='consumes-qualified-source')]['identity'] if view.edges else 'glaciers:683'
                        queries={'point':{'region':'riffelhorn','point':[2624123.875,1091567.125],'crs':'EPSG:2056'},
                                 'area':{'region':'riffelhorn','area':[2624111.125,1091555.125,2624222.625,1091777.375],'crs':'EPSG:2056'},
                                 'identity':{'identity':'glaciers:683'},
                                 'lineage':{'relatedTo':{'identity':seed,'direction':'dependents','depth':'transitive'}}}
                        samples[view.generation]={}
                        for name,q in queries.items():
                            view.read(q);times=[]
                            for _ in range(15):
                                t=time.perf_counter();view.read(q);times.append((time.perf_counter()-t)*1000)
                            samples[view.generation][name]={'medianMs':statistics.median(times),'minMs':min(times),'maxMs':max(times)}
            geometry={'features':len(owner._features),'vertices':int(sum(importlib.import_module('shapely').get_num_coordinates(g) for g in owner._features.values())),
                      'wkbBytes':sum(len(g.wkb) for g in owner._features.values()),'validFeatures':sum(g.is_valid for g in owner._features.values())}
            return {'mode':mode,'viewCount':count,'openMs':opened,'openMemory':before,'queryMemory':memory(),
                    'geometry':geometry,'queries':samples,'projectionBytes':sum(p.stat().st_size for p in root.iterdir()),
                    'cacheState':'fresh process; OS storage caches retained; owned verified snapshot'}
        finally:
            for view in views:view.close()


def batch():
    import pyproj
    from native_proj import NativeProj
    xy=([2624000+n for n in range(2000)],[1091000+n for n in range(2000)])
    ref=pyproj.Transformer.from_crs(2056,4326,always_xy=True)
    with NativeProj() as native:
        expected=tuple(tuple(v) for v in ref.transform(*xy));actual=native.xy(*xy,'EPSG:2056','EPSG:4326')
        if expected!=actual:raise AssertionError('Batch semantics differ.')
        rows={}
        for mode,call in [('reference',lambda:ref.transform(*xy)),('native',lambda:native.xy(*xy,'EPSG:2056','EPSG:4326'))]:
            times=[]
            for _ in range(30):
                t=time.perf_counter();call();times.append((time.perf_counter()-t)*1000)
            rows[mode]={'medianMs':statistics.median(times),'minMs':min(times),'maxMs':max(times)}
    return {'coordinatePairs':2000,'exactAgreement':True,'repetitions':30,'cachedBatchMs':rows,'memory':memory()}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['inventory','imports','native','reader','batch'],required=True)
    p.add_argument('--projection');p.add_argument('--binding',choices=['native','reference'],default='reference')
    p.add_argument('--views',type=int,choices=[1,3],default=3);a=p.parse_args()
    value=inventory() if a.mode=='inventory' else imports(a.mode) if a.mode in ['imports','native'] else batch() if a.mode=='batch' else reader_trial(a.projection,a.binding,a.views)
    print(json.dumps(value,indent=2))
