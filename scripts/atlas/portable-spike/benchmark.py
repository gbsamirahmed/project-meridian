"""Desktop cold-open/warm-query distributions, not phone or full offline validation."""
from pathlib import Path
import argparse
import ctypes
import json
import statistics
import sys
import time
from reader import Reader

def peak_bytes():
    if sys.platform=='win32':
        class Counters(ctypes.Structure):
            _fields_=[('cb',ctypes.c_ulong),('faults',ctypes.c_ulong)]+[(k,ctypes.c_size_t) for k in ['peak','working','peakPaged','paged','peakNonpaged','nonpaged','pagefile','peakPagefile']]
        data=Counters(); data.cb=ctypes.sizeof(data)
        ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
        handle=ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong]
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(data),data.cb): return data.peak
        return None
    return None

def distribution(values):
    ordered=sorted(values)
    return {'min':ordered[0],'median':statistics.median(ordered),'p95':ordered[min(len(ordered)-1,int(.95*len(ordered)))],'max':ordered[-1]}

def run():
    p=argparse.ArgumentParser(); p.add_argument('--projection',required=True); a=p.parse_args()
    m=json.loads((Path(a.projection)/'manifest.json').read_text(encoding='utf-8')); result={}
    for generation,pin in m['pins'].items():
        opens=[]
        for _ in range(3):
            if _ > 0: reader.close()
            reader=Reader(a.projection,generation,m['projectionIdentity']); opens.append(reader.startup_ms)
        queries={'nativePoint':{'region':'riffelhorn','point':[2624123.875,1091567.125],'crs':'EPSG:2056'},
                 'nativeArea':{'region':'riffelhorn','area':[2624111.125,1091555.125,2624222.625,1091777.375],'crs':'EPSG:2056'},
                 'identity':{'identity':'glaciers:683'},
                 'lineage':{'relatedTo':{'identity':reader.records[next(e['from'] for e in reader.edges if e['kind']=='consumes-qualified-source')]['identity'] if reader.edges else next(r['identity'] for r in reader.records.values() if r['family']=='dtm'),'direction':'dependents','depth':'transitive'}}}
        times={}
        for name,q in queries.items():
            reader.read(q); values=[]
            for _ in range(30):
                start=time.perf_counter(); reader.read(q); values.append((time.perf_counter()-start)*1000)
            times[name]=distribution(values)
        result[pin['alias']]={'openMs':distribution(opens),'queriesMs':times}
        reader.close()
    print(json.dumps({'platform':sys.platform,'python':sys.version.split()[0],'repeats':{'open':3,'warmQuery':30},'measurements':result,'peakWorkingSetBytes':peak_bytes()},sort_keys=True))

if __name__ == '__main__': run()
