"""Package verified existing contour masters for local display; no DEM decoding."""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import time

PRODUCTS=('swiss-native','swiss-2m','swiss-smoothed')
LABELS=('Native 0.5 m','Strict 2 m aggregation','Smoothed 2 m')
EXPECTED=((662196,1596,332486,762),(150389,356,75518,176),(140562,203,70484,101))
BOUNDS=(2624000,1091000,2626000,1093000)

class BoundedWriter:
    def __init__(self,stream,limit=50_000_000):self.stream=stream;self.limit=limit;self.bytes=0
    def write(self,body):
        if self.bytes+len(body)>self.limit:raise ValueError('Viewer output reservation exceeded')
        if self.stream.write(body)!=len(body):raise OSError('Short viewer write')
        self.bytes+=len(body)

def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for body in iter(lambda:stream.read(1048576),b''):value.update(body)
    return value.hexdigest()

def verify_history(root,seal):
    inventory=root/'execution-3/inventory.json'
    if digest(inventory)!=seal['inventorySha256']:raise ValueError('Historical inventory seal changed')
    entries=json.loads(inventory.read_text())['inventory']
    paths={str((root/e['path']).resolve()) for e in entries}|{str(inventory.resolve())}
    if paths!={str(p.resolve()) for p in root.rglob('*') if p.is_file()}:
        raise ValueError('Historical inventory membership changed')
    for entry in entries:
        path=root/entry['path']
        if path.stat().st_size!=entry['bytes'] or digest(path)!=entry['sha256']:
            raise ValueError('Historical evidence changed: '+entry['path'])
    if len(paths)!=867 or sum(Path(p).stat().st_size for p in paths)!=64250005:
        raise ValueError('Historical resource totals changed')
    return entries

def validate_record(record,level):
    if set(record)!={'level','index','twentyMetreSubset','line','coordinates'}:
        raise ValueError('Unexpected geometry record fields')
    if record['level']!=level or record['index']!=(level%100==0) or record['twentyMetreSubset']!=(level%20==0):
        raise ValueError('Contour elevation/classification mismatch')
    points=record['coordinates']
    if len(points)<2:raise ValueError('Invalid contour line')
    for point in points:
        if len(point)!=2 or not all(isinstance(v,(float,int)) and math.isfinite(v) for v in point):
            raise ValueError('Non-finite/projected coordinate mismatch')
        if not BOUNDS[0]<=point[0]<=BOUNDS[2] or not BOUNDS[1]<=point[1]<=BOUNDS[3]:
            raise ValueError('Geometry outside declared study footprint')
    return len(points)

def package_products(stream,products):
    """Copy each source NDJSON record verbatim into one JSON array; no rounding."""
    summaries=[]
    stream.write(b'{"bounds":'+json.dumps(BOUNDS).encode()+b',"variants":[')
    for variant_index,(name,label,expected) in enumerate(zip(PRODUCTS,LABELS,EXPECTED)):
        source=products/name;manifest=json.loads((source/'manifest.json').read_text())
        for key,value in {'id':name,'horizontalReference':'EPSG:2056','verticalReference':'LN02',
                          'surface':'DTM','units':'m','interval':10,'subsetInterval':20}.items():
            if manifest.get(key)!=value:raise ValueError('Scientific meaning mismatch: '+key)
        metadata={key:manifest[key] for key in ('id','sourceRevision','rights','processingRevision','limitations')}
        metadata.update(label=label,horizontalReference='EPSG:2056',verticalReference='LN02 / EPSG:5728',
                        surface='DTM',units='m',geometry='unsimplified source-specific lines')
        if variant_index:stream.write(b',')
        stream.write(json.dumps(metadata,ensure_ascii=True,separators=(',',':')).encode()[:-1]+b',"lines":[')
        counts=[0,0,0,0];first=True;payloads={};source_bytes=0
        for level in range(2000,3201,10):
            path=source/f'{level}.ndjson';seal=manifest['geometry']['levels'][str(level)]
            if digest(path)!=seal['sha256']:raise ValueError('Canonical payload seal changed')
            payloads[str(level)]=seal['sha256'];source_bytes+=path.stat().st_size
            vertices=lines=closed=0;seen=set()
            with path.open('rb') as records:
                for raw in records:
                    record=json.loads(raw);count=validate_record(record,level)
                    if record['line'] in seen:raise ValueError('Duplicate source line identifier')
                    seen.add(record['line']);vertices+=count;lines+=1
                    closed+=record['coordinates'][0]==record['coordinates'][-1]
                    if b'<' in raw:raise ValueError('Unsafe embedded source record')
                    if not first:stream.write(b',')
                    stream.write(raw.rstrip(b'\r\n'));first=False
            if (vertices,lines,closed)!=(seal['vertices'],seal['lines'],seal['closed']):
                raise ValueError('Canonical geometry count changed')
            counts[0]+=vertices;counts[1]+=lines
            if level%20==0:counts[2]+=vertices;counts[3]+=lines
        if tuple(counts)!=expected:raise ValueError('Verified product totals changed')
        stream.write(b'],"counts":'+json.dumps({'10':{'vertices':counts[0],'lines':counts[1]},
             '20':{'vertices':counts[2],'lines':counts[3]}}).encode()+b'}')
        summaries.append({'id':name,'counts10m':counts[:2],'counts20m':counts[2:],
            'sourcePayloadBytes':source_bytes,'manifestSha256':digest(source/'manifest.json'),
            'payloadSha256':payloads})
    stream.write(b']}')
    return summaries

def build(data_root,output):
    started=time.monotonic()
    if output.exists():raise ValueError('Fresh external viewer directory required')
    root=data_root/'experiments/atlas/source-aware-contours-v1'
    pilot=Path(__file__).resolve().parent.parent/'contour-pilot'
    seal=json.loads((pilot/'genuine-rerun-receipt.json').read_text())
    verify_history(root,seal)
    output.mkdir(parents=True)
    source=Path(__file__).parent;code=(source/'viewer.js').read_bytes()
    code_hash=base64.b64encode(hashlib.sha256(code).digest()).decode()
    template=(source/'viewer.html').read_text(encoding='utf-8')
    prefix,suffix=template.replace('CODE_HASH',code_hash).split('DATA_PAYLOAD')
    target=output/'contours.html';partial=target.with_suffix('.partial')
    with partial.open('xb') as raw_stream:
        stream=BoundedWriter(raw_stream)
        stream.write(prefix.encode())
        summaries=package_products(stream,root/'execution-3/processing/run-1')
        stream.write(suffix.replace('VIEWER_CODE',code.decode()).encode())
    if partial.stat().st_size>50_000_000:raise ValueError('Viewer exceeds bounded 50 MB output allowance')
    verify_history(root,seal)
    partial.rename(target)
    receipt={'scope':'offline display of existing Swiss master lines only','genuineContoursGenerated':0,
        'background':'neutral; no qualified offline shaded image selected','requests':0,
        'coordinateDisplay':'EPSG:2056 local translation, uniform scale and north-up Y inversion; no reprojection',
        'elevationDisplay':'unchanged metre LN02 values; no vertical transformation',
        'sourceInventorySha256':seal['inventorySha256'],'products':summaries,
        'outputBytes':target.stat().st_size,'outputSha256':digest(target),'elapsedSeconds':time.monotonic()-started,
        'implementationSha256':{p.name:digest(p) for p in (source/'build.py',source/'viewer.js',source/'viewer.html')}}
    (output/'bundle-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=build(args.data_root,args.output)
    print(json.dumps({k:v for k,v in result.items() if k!='products'},indent=2))
