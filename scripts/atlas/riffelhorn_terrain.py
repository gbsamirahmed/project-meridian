"""Bounded visual-only Riffelhorn product. Never imported by the application.

prepare: verifies four retained official TIFFs, writes a composed XYZ pyramid.
serve: loopback-only evaluation endpoint; AWS outside prepared regional tiles.
verify: local byte/encoding/provenance checks; no downloads.
No datum adjustment, seam blend, terrain reconstruction or analytical sampling.
"""
from __future__ import annotations
import argparse
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image, __version__ as pillow_version
import pyproj
from pyproj import Transformer
import rasterio
from rasterio.merge import merge
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling, transform_bounds

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts'))
from meridian_paths import resolve_storage_roots

VERSION = 'riffelhorn-regional-terrain-v1'
SOURCE = 'sources/atlas/riffelhorn/swisstopo-2021-2024'
PRODUCT = 'derived/atlas/riffelhorn/' + VERSION
CACHE = 'cache/atlas/riffelhorn/' + VERSION + '/aws'
BOUNDS = (2624000, 1091000, 2626000, 1093000)
SIZE = 256
MIN_Z, MAX_Z = 5, 18
WORLD = 40075016.68557849
AWS = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repository_text_digest(path):
    # Match Git's LF text contract, regardless of working-copy line endings.
    return hashlib.sha256(Path(path).read_text(encoding='utf-8').encode('utf-8')).hexdigest()


def stable_id(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':')).encode()).hexdigest()


def encode(heights):
    if not np.all(np.isfinite(heights)) or np.any(heights < -32768) or np.any(heights >= 32768):
        raise ValueError('Invalid/out-of-range Terrarium elevation; never silently encode nodata')
    q = np.rint((heights.astype(np.float64)+32768)*256).astype(np.uint32)
    if np.any(q > 0xffffff): raise ValueError('Terrarium overflow')
    rgb = np.stack((q >> 16, (q >> 8) & 255, q & 255), axis=-1).astype('uint8')
    out=BytesIO();Image.fromarray(rgb).save(out,format='PNG',compress_level=6)
    return out.getvalue()


def decode(body):
    image=Image.open(BytesIO(body))
    if image.size != (SIZE,SIZE) or image.mode not in ('RGB','RGBA'):
        raise ValueError('Unexpected DEM dimensions/encoding image mode')
    a=np.asarray(image.convert('RGB'),dtype=np.float64)
    return a[...,0]*256+a[...,1]+a[...,2]/256-32768


def pixel_xy(e,n,z):
    scale=SIZE*2**z
    return (np.asarray(e)/WORLD+.5)*scale-.5, (.5-np.asarray(n)/WORLD)*scale-.5


def tile_bounds(z,x,y):
    span=WORLD/2**z
    return (-WORLD/2+x*span, WORLD/2-(y+1)*span,
            -WORLD/2+(x+1)*span, WORLD/2-y*span)


class AwsCache:
    def __init__(self, root):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.arrays={};self.records={}

    def tile(self,z,x,y):
        x%=2**z
        if not 0 <= y < 2**z: raise ValueError('Polar sample outside XYZ grid')
        key=(z,x,y)
        with self.lock:
            if key in self.arrays: return self.arrays[key]
            p=self.root/f'{z}/{x}/{y}.png';meta=p.with_suffix('.json')
            if not p.exists():
                url=AWS.format(z=z,x=x,y=y)
                with urlopen(Request(url,headers={'User-Agent':'Meridian-Riffelhorn-visual-prototype'}),timeout=30) as r:
                    body=r.read();headers=dict(r.headers)
                decode(body) # validate before persisting
                p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
                meta.write_text(json.dumps({'url':url,'headers':headers,'sha256':digest(p)},sort_keys=True)+'\n',encoding='utf-8')
            record=json.loads(meta.read_text(encoding='utf-8'))
            if digest(p)!=record['sha256']: raise ValueError('Cached AWS input changed: '+str(p))
            self.records['/'.join(map(str,key))]={**record,'cachePath':str(p.relative_to(self.root)).replace('\\','/')}
            self.arrays[key]=decode(p.read_bytes());return self.arrays[key]

    def sample_pixels(self,z,x,y):
        x,y=np.broadcast_arrays(x,y);x0=np.floor(x).astype('int64');y0=np.floor(y).astype('int64')
        def pixels(xx,yy):
            out=np.empty(xx.shape,dtype='float64')
            pairs=np.stack((xx//SIZE,yy//SIZE),axis=-1)
            for tx,ty in np.unique(pairs.reshape(-1,2),axis=0):
                mask=(pairs[...,0]==tx)&(pairs[...,1]==ty)
                out[mask]=self.tile(z,int(tx),int(ty))[yy[mask]%SIZE,xx[mask]%SIZE]
            return out
        fx=x-x0;fy=y-y0
        return (pixels(x0,y0)*(1-fx)+pixels(x0+1,y0)*fx)*(1-fy)+(pixels(x0,y0+1)*(1-fx)+pixels(x0+1,y0+1)*fx)*fy

    def at_mercator(self,e,n,z=15):
        return self.sample_pixels(z,*pixel_xy(e,n,z))

    def at_tile(self,z,x,y):
        if z<=15: return self.tile(z,x,y)
        f=2**(z-15)
        xx=(x*SIZE+np.arange(SIZE)+.5)/f-.5
        yy=(y*SIZE+np.arange(SIZE)+.5)/f-.5
        return self.sample_pixels(15,xx[None,:],yy[:,None])


def inspect_sources(data):
    catalog=REPO/'docs/atlas/riffelhorn-data-catalog.json'
    c=json.loads(catalog.read_text(encoding='utf-8'))
    rows=sorted([v for v in c['assets'] if v['path'].startswith('originals/swissalti3d/')],key=lambda v:v['path'])
    if len(rows)!=4: raise ValueError('Expected exactly four frozen swissALTI3D inputs')
    paths=[];records=[]
    for v in rows:
        p=data/SOURCE/v['path']
        if digest(p)!=v['sha256']: raise ValueError('Swiss source checksum mismatch: '+str(p))
        receipt=data/SOURCE/'metadata'/(p.name+'.receipt.json')
        if json.loads(receipt.read_text(encoding='utf-8'))['sha256']!=v['sha256']:raise ValueError('Receipt mismatch')
        with rasterio.open(p) as t:
            if t.crs.to_epsg()!=2056 or t.res!=(.5,.5) or (t.width,t.height)!=(2000,2000) or t.dtypes!=('float32',):raise ValueError('Swiss grid contract changed')
            a=t.read(1,masked=True)
            if np.any(np.ma.getmaskarray(a)):raise ValueError('Unexpected Swiss source nodata')
            records.append({'path':SOURCE+'/'+v['path'],'sha256':v['sha256'],'bytes':p.stat().st_size,
                'url':json.loads(receipt.read_text(encoding='utf-8'))['url'],'bounds':list(t.bounds),'nodata':t.nodata,'crs':str(t.crs),
                'shape':[t.height,t.width],'gridSpacingMetres':.5,'dtype':t.dtypes[0],
                'verticalReference':v['vertical_reference'],'receiptSha256':digest(receipt)})
        paths.append(p)
    datasets=[rasterio.open(p)for p in paths]
    try: a,affine=merge(datasets,bounds=BOUNDS)
    finally:
        for t in datasets:t.close()
    return a[0],affine,records,repository_text_digest(catalog)


def prepare(data):
    source,affine,records,catalog_hash=inspect_sources(data)
    out=data/PRODUCT
    if (out/'manifest.json').exists():raise ValueError('Product already exists; use verify, or explicitly choose a new version')
    out.mkdir(parents=True,exist_ok=True)
    aws=AwsCache(data/CACHE)
    forward=Transformer.from_crs(2056,3857,always_xy=True,allow_ballpark=False)
    forward.transform(2625000,1092000)
    inverse=Transformer.from_crs(3857,2056,always_xy=True,allow_ballpark=False)
    bounds=transform_bounds(2056,3857,*BOUNDS,densify_pts=21)
    files=[];errors=[];zoom_stats=[]
    for z in range(MIN_Z,MAX_Z+1):
        span=WORLD/2**z
        x0=math.floor((bounds[0]+WORLD/2)/span);x1=math.floor((bounds[2]+WORLD/2)/span)
        y0=math.floor((WORLD/2-bounds[3])/span);y1=math.floor((WORLD/2-bounds[1])/span)
        shape=((y1-y0+1)*SIZE,(x1-x0+1)*SIZE)
        extent=(tile_bounds(z,x0,y1)[0],tile_bounds(z,x0,y1)[1],tile_bounds(z,x1,y0)[2],tile_bounds(z,x1,y0)[3])
        transform=from_bounds(*extent,shape[1],shape[0]);warped=np.full(shape,np.nan,dtype='float32')
        reproject(source,warped,src_transform=affine,src_crs='EPSG:2056',src_nodata=-9999,
            dst_transform=transform,dst_crs='EPSG:3857',dst_nodata=np.nan,
            resampling=Resampling.bilinear if z==18 else Resampling.average,
            num_threads=1,ERROR_THRESHOLD=0.0,COORDINATE_OPERATION=forward.definition)
        columns=extent[0]+(np.arange(shape[1])+.5)*span/SIZE
        northings=extent[3]-(np.arange(shape[0])+.5)*span/SIZE
        xx,yy=np.meshgrid(columns,northings);se,sn=inverse.transform(xx,yy)
        valid=np.isfinite(warped)&(se>=BOUNDS[0])&(se<BOUNDS[2])&(sn>=BOUNDS[1])&(sn<BOUNDS[3])
        tiles=0
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                sl=(slice((y-y0)*SIZE,(y-y0+1)*SIZE),slice((x-x0)*SIZE,(x-x0+1)*SIZE))
                mask=valid[sl]
                if not mask.any():continue
                swiss=warped[sl];baseline=aws.at_tile(z,x,y);heights=np.where(mask,swiss,baseline)
                body=encode(heights);decoded=decode(body)
                errors.append(float(np.max(np.abs(decoded-heights))))
                p=out/f'tiles/{z}/{x}/{y}.png';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
                m=out/f'masks/{z}/{x}/{y}.png';m.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(mask.astype('uint8')*255).save(m)
                for f in [p,m]:files.append({'path':f.relative_to(out).as_posix(),'bytes':f.stat().st_size,'sha256':digest(f)})
                tiles+=1
        zoom_stats.append({'zoom':z,'tiles':tiles,'swissPixels':int(valid.sum())});print('PREPARED',z,tiles,flush=True)
    manifest={'schemaVersion':1,'productVersion':VERSION,'status':'experimental visual terrain only',
        'source':{'dataset':'swissALTI3D','authority':'swisstopo','release':'2024 / 2024-2 Valais','gridSpacingMetres':.5,
            'measurementResolutionMetres':None,'horizontalCRS':'EPSG:2056','verticalReference':'LN02 / EPSG:5728','units':'metres',
            'nativeBounds':list(BOUNDS),'inputs':records,'catalogSha256':catalog_hash,'catalogHashContract':'UTF-8, canonical LF line endings',
            'basis':'2021/2022 LiDAR with 2023 photogrammetric updates; per-cell update lineage unavailable'},
        'delivery':{'crs':'EPSG:3857','scheme':'xyz','tileSize':SIZE,'encoding':'terrarium','format':'lossless RGB PNG',
            'minzoom':MIN_Z,'maxzoom':MAX_Z,'mercatorBounds':list(bounds),'resampling':'average z5-17; bilinear z18',
            'pixelRegistration':'area cells, sample at pixel centres','nodata':'AWS fill; never encode Swiss -9999 or transparent DEM',
            'boundary':'hard centre-in-AOI substitution, no datum shift or seam blend',
            'verticalReference':'LN02 for Swiss mask=255; AWS reference not independently established for mask=0',
            'quantizationIncrementMetres':1/256,'maxEncodingErrorMetres':max(errors),
            'fallback':'AWS original tiles through z15, cross-tile bilinear z15 overzoom above; no new information'},
        'processing':{'scriptSha256':repository_text_digest(__file__),'scriptHashContract':'UTF-8, canonical LF line endings','python':sys.version.split()[0],'numpy':np.__version__,'pillow':pillow_version,
            'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__,
            'horizontalOperation':forward.definition,'operationStatedAccuracyMetres':forward.accuracy,
            'verticalTransform':'none; only two-dimensional horizontal coordinates transformed'},
        'attribution':'©swisstopo; AWS terrain sources: https://github.com/tilezen/joerd/blob/master/docs/attribution.md',
        'rights':'swisstopo custom OGD terms, https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices',
        'awsInputs':aws.records,'zooms':zoom_stats,'files':files,'storageBytes':sum(f['bytes']for f in files)}
    manifest['identity']=stable_id(manifest)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('PRODUCT',manifest['identity'],manifest['storageBytes'],flush=True)


def verify(data):
    out=data/PRODUCT;m=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    payload={k:v for k,v in m.items()if k!='identity'}
    if stable_id(payload)!=m['identity'] or repository_text_digest(__file__)!=m['processing']['scriptSha256']:raise ValueError('Product manifest/code identity changed')
    _,_,inputs,catalog_hash=inspect_sources(data)
    if inputs!=m['source']['inputs'] or catalog_hash!=m['source']['catalogSha256']:
        raise ValueError('Frozen source provenance changed; prepare an explicitly versioned product')
    for f in m['files']:
        if digest(out/f['path'])!=f['sha256']:raise ValueError('Product file changed: '+f['path'])
        if f['path'].startswith('tiles/'):decode((out/f['path']).read_bytes())
    for f in m['awsInputs'].values():
        if digest(data/CACHE/f['cachePath'])!=f['sha256']:raise ValueError('Frozen AWS input changed')
    print('VERIFIED',m['identity'],len(m['files']),m['storageBytes']);return m


def serve(data,port):
    m=verify(data);out=data/PRODUCT;aws=AwsCache(data/CACHE)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            match=re.fullmatch(r'/tiles/(\d+)/(\d+)/(\d+)\.png',self.path)
            if not match:self.send_error(404);return
            z,x,y=map(int,match.groups())
            if not 0<=z<=MAX_Z or not 0<=x<2**z or not 0<=y<2**z:self.send_error(400);return
            p=out/f'tiles/{z}/{x}/{y}.png'
            try:
                if p.exists():body=p.read_bytes();role='regional-composite'
                elif z<=15:
                    self.send_response(302);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Location',AWS.format(z=z,x=x,y=y));self.end_headers();return
                else:body=encode(aws.at_tile(z,x,y));role='aws-overzoom'
                self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Access-Control-Allow-Origin','*')
                self.send_header('Cache-Control','public, max-age=3600');self.send_header('Content-Length',str(len(body)))
                self.send_header('X-Meridian-Product',m['identity']);self.send_header('X-Meridian-Terrain-Role',role)
                self.end_headers();self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
            except Exception as e:
                print('TILE ERROR',self.path,str(e),flush=True);self.send_error(502,'Terrain unavailable')
        def log_message(self,*args):pass
    print('SERVING loopback',port,PRODUCT,flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','serve']);parser.add_argument('--port',type=int,default=4180)
    args=parser.parse_args();data=resolve_storage_roots(require_data=True).data
    if args.command=='prepare':prepare(data)
    elif args.command=='verify':verify(data)
    else:serve(data,args.port)
