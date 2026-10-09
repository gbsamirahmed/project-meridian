"""Frozen-case adapter only; the reader never receives case IDs or expected data."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time
from reader import Reader, ReadError

def first_difference(a,b,where='$'):
    if type(a) != type(b) and not (type(a) in (int,float) and type(b) in (int,float)): return where+' [type]'
    if isinstance(a,dict):
        if set(a)!=set(b): return where+' [keys]'
        for key in sorted(a):
            found=first_difference(a[key],b[key],where+'/'+key)
            if found: return found
    elif isinstance(a,list):
        if len(a)!=len(b): return where+' [length]'
        for i,(x,y) in enumerate(zip(a,b)):
            found=first_difference(x,y,where+'/'+str(i))
            if found: return found
    elif a!=b: return where
    return None

def run():
    parser=argparse.ArgumentParser(); parser.add_argument('--projection',required=True); parser.add_argument('--fixtures',required=True)
    args=parser.parse_args(); root=Path(args.fixtures)
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    for name,seal in manifest['files'].items():
        raw=(root/name).read_bytes()
        if len(raw)!=seal['bytes'] or hashlib.sha256(raw).hexdigest()!=seal['sha256']: raise ValueError('Frozen fixture seal differs.')
    requests=json.loads((root/'requests.json').read_text(encoding='utf-8'))['cases']; expected=json.loads((root/'expected.json').read_text(encoding='utf-8'))['cases']; docs=json.loads((root/'documents.json').read_text(encoding='utf-8'))['documents']
    readers={}; passed=0; failed=0; errors=0; times=[]
    for case in requests:
        pin=manifest['publications'][case['publication']]['generation']
        if pin not in readers: readers[pin]=Reader(args.projection,pin)
        start=time.perf_counter(); actual=readers[pin].outcome(case['query']); times.append((time.perf_counter()-start)*1000)
        wanted=expected[case['id']]
        if wanted['kind']=='answer': wanted={'kind':'answer','value':{**wanted['value'],'documents':{ref:docs[ref] for ref in wanted['documentRefs']}}}
        else: errors+=1
        difference=first_difference(wanted,actual)
        if difference: failed+=1
        else: passed+=1
        print(json.dumps({'case':case['id'],'status':'FAIL' if difference else 'PASS','difference':difference,'actualCode':actual.get('code')},separators=(',',':')))
    print(json.dumps({'summary':{'selected':len(requests),'passed':passed,'failed':failed,'skipped':0,'expectedErrors':errors},
                      'coldOpenMs':{k:r.startup_ms for k,r in readers.items()},'queryMs':{'min':min(times),'median':sorted(times)[len(times)//2],'max':max(times)}}))
    for reader in readers.values(): reader.close()
    return 1 if failed else 0

if __name__=='__main__':
    try: sys.exit(run())
    except (ReadError,OSError,ValueError,KeyError) as e:
        print(json.dumps({'status':'BLOCKED','code':e.code if isinstance(e,ReadError) else 'fixture-prerequisite','message':str(e) if isinstance(e,ReadError) else 'Check the explicit fixture and projection prerequisites.'})); sys.exit(1)
