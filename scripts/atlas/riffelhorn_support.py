"""One bounded official 2024 Swiss selection; pure LN02 support product.
No datum adjustment, AWS fill, blending or production hook.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.transform import from_bounds
from rasterio.windows import Window
from rasterio.warp import transform_bounds
from pyproj import Transformer
from PIL import Image
import riffelhorn_terrain as rt

VERSION='riffelhorn-swiss-support-v1'
SOURCE='sources/atlas/riffelhorn/swissalti3d-2024-support-v1'
PRODUCT='derived/atlas/riffelhorn/'+VERSION
EXPERIMENT='experiments/atlas/'+VERSION
BOUNDS=(2620000,1087000,2630000,1097000)
CENTRE=(2625000,1092000)
RADIUS=1500
MIN_Z,MAX_Z=12,18
SIZE=256
REPO=Path(__file__).resolve().parents[2]

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf8')

def acquire(data,plan_path):
    plan=json.loads(Path(plan_path).read_text(encoding='utf8'))
    if tuple(plan['bounds'])!=BOUNDS or len(plan['selection'])!=100: raise ValueError('Selection contract mismatch')
    old=json.loads((REPO/'docs/atlas/riffelhorn-regional-product.json').read_text(encoding='utf8'))['source']['inputs']
    reused={Path(row['path']).name:row for row in old}
    base=data/SOURCE;base.mkdir(parents=True,exist_ok=True)
    save(base/'metadata/selection-plan.json',plan)
    def asset(row):
        name=row['assetName'];is_reused=name in reused
        p=data/reused[name]['path'] if is_reused else base/'originals'/name
        receipt=base/'metadata'/(name+'.receipt.json')
        if is_reused:
            if rt.digest(p)!=reused[name]['sha256']:raise ValueError('Retained input changed')
        elif not p.exists():
            p.parent.mkdir(parents=True,exist_ok=True)
            part=p.with_suffix('.part')
            with urlopen(Request(row['url'],headers={'User-Agent':'Meridian-bounded-Swiss-support-product'}),timeout=90) as response:
                headers=dict(response.headers)
                with part.open('wb')as out:
                    while body:=response.read(1024*1024):out.write(body)
            with rasterio.open(part)as ds:
                if ds.crs.to_epsg()!=2056 or ds.res!=(.5,.5) or ds.shape!=(2000,2000)or tuple(ds.bounds)!=tuple(row['bounds']):raise ValueError('Official asset contract mismatch')
            part.replace(p)
            save(receipt,{'url':row['url'],'sha256':rt.digest(p),'headers':headers,'downloadedAt':datetime.now(timezone.utc).isoformat()})
        if not is_reused:
            frozen=json.loads(receipt.read_text(encoding='utf8'))
            if rt.digest(p)!=frozen['sha256']:raise ValueError('Acquired asset drift')
        with rasterio.open(p)as ds:
            if ds.crs.to_epsg()!=2056 or ds.res!=(.5,.5)or ds.shape!=(2000,2000)or ds.dtypes!=('float32',)or ds.nodata!=-9999 or tuple(ds.bounds)!=tuple(row['bounds']):raise ValueError('Source grid contract mismatch')
            nodata=int(np.ma.getmaskarray(ds.read(1,masked=True)).sum())
        result={'path':p.relative_to(data).as_posix(),'url':row['url'],'sha256':rt.digest(p),'bytes':p.stat().st_size,'reused':is_reused,'bounds':row['bounds'],'nodataCells':nodata,'officialItem':row['id'],'officialProperties':row['officialMetadata']['properties']}
        print('ACQUIRED',name,'reused'if is_reused else 'new',result['bytes'],flush=True)
        return result
    with ThreadPoolExecutor(max_workers=2)as pool: rows=list(pool.map(asset,plan['selection']))
    record={'version':VERSION,'bounds':list(BOUNDS),'protectedCentre':list(CENTRE),'protectedRadiusMetres':RADIUS,'minimumSourceSupportMetres':3500,'priorMaximumDiagnosticWidthMetres':2500,'release':'2024 / 2024-2 Valais','basis':'2021/2022 LiDAR, 2023 photogrammetric updates; per-cell lineage unknown','horizontalCRS':'EPSG:2056','verticalReference':'LN02 / EPSG:5728','gridSpacingMetres':.5,'nodata':-9999,'geographicEnvelope':plan['geographicEnvelope'],'assets':rows,'officialMetadataAccessDate':plan['accessDate']}
    record['identity']=rt.stable_id(record);save(base/'acquisition.json',record)
    save(REPO/'docs/atlas/riffelhorn-support-acquisition.json',record)
    print('SOURCE',record['identity'],sum(r['bytes']for r in rows),flush=True)

def source_record(data):
    record=json.loads((data/SOURCE/'acquisition.json').read_text(encoding='utf8'))
    if rt.stable_id({k:v for k,v in record.items()if k!='identity'})!=record['identity']:raise ValueError('Acquisition identity mismatch')
    for row in record['assets']:
        if rt.digest(data/row['path'])!=row['sha256']:raise ValueError('Source bytes changed')
    return record

def build_vrt(data,out,record):
    width=int((BOUNDS[2]-BOUNDS[0])/.5);height=int((BOUNDS[3]-BOUNDS[1])/.5)
    parts=[f'<VRTDataset rasterXSize="{width}" rasterYSize="{height}"><SRS>EPSG:2056</SRS><GeoTransform>{BOUNDS[0]},0.5,0,{BOUNDS[3]},0,-0.5</GeoTransform><VRTRasterBand dataType="Float32" band="1"><NoDataValue>-9999</NoDataValue>']
    for row in record['assets']:
        b=row['bounds'];x=int((b[0]-BOUNDS[0])/.5);y=int((BOUNDS[3]-b[3])/.5)
        path=escape(os.path.relpath(data/row['path'],out).replace('\\','/'))
        parts.append(f'<ComplexSource><SourceFilename relativeToVRT="1">{path}</SourceFilename><SourceBand>1</SourceBand><SrcRect xOff="0" yOff="0" xSize="2000" ySize="2000"/><DstRect xOff="{x}" yOff="{y}" xSize="2000" ySize="2000"/><NODATA>-9999</NODATA></ComplexSource>')
    parts.append('</VRTRasterBand></VRTDataset>');(out/'source-mosaic.vrt').write_text(''.join(parts)+'\n',encoding='utf8')

def hierarchy(z):
    bounds=transform_bounds(2056,3857,*BOUNDS,densify_pts=41);span=rt.WORLD/2**z
    x0=math.floor((bounds[0]+rt.WORLD/2)/span);x1=math.floor((bounds[2]+rt.WORLD/2)/span)
    y0=math.floor((rt.WORLD/2-bounds[3])/span);y1=math.floor((rt.WORLD/2-bounds[1])/span)
    shape=((y1-y0+1)*SIZE,(x1-x0+1)*SIZE)
    extent=(rt.tile_bounds(z,x0,y1)[0],rt.tile_bounds(z,x0,y1)[1],rt.tile_bounds(z,x1,y0)[2],rt.tile_bounds(z,x1,y0)[3])
    return x0,x1,y0,y1,shape,extent

def tile_supported(z,x,y,inverse):
    b=rt.tile_bounds(z,x,y)
    # Entire support of area cells, not just centre-in-AOI. Sample curved perimeter.
    edge=np.linspace(0,1,33);e=np.r_[b[0]+edge*(b[2]-b[0]),b[0]+edge*(b[2]-b[0]),np.full(33,b[0]),np.full(33,b[2])]
    n=np.r_[np.full(33,b[1]),np.full(33,b[3]),b[1]+edge*(b[3]-b[1]),b[1]+edge*(b[3]-b[1])]
    se,sn=inverse.transform(e,n)
    # One source cell guard for bilinear/average edge support.
    return bool(np.all((se>=BOUNDS[0]+.5)&(se<=BOUNDS[2]-.5)&(sn>=BOUNDS[1]+.5)&(sn<=BOUNDS[3]-.5)))

def warped(ds,z,forward):
    x0,x1,y0,y1,shape,extent=hierarchy(z)
    vrt=WarpedVRT(ds,crs='EPSG:3857',transform=from_bounds(*extent,shape[1],shape[0]),width=shape[1],height=shape[0],src_nodata=-9999,nodata=np.nan,dtype='float32',resampling=Resampling.bilinear if z==18 else Resampling.average,tolerance=1e-9,warp_extras={'COORDINATE_OPERATION':forward.definition,'NUM_THREADS':'1'})
    return vrt,(x0,x1,y0,y1)

def prepare(data,suffix=''):
    start=time.perf_counter();record=source_record(data);out=data/(PRODUCT+suffix)
    if (out/'manifest.json').exists():raise ValueError('Existing product; use verify or a separate rebuild directory')
    out.mkdir(parents=True,exist_ok=True);build_vrt(data,out,record)
    forward=Transformer.from_crs(2056,3857,always_xy=True,allow_ballpark=False);forward.transform(*CENTRE)
    inverse=Transformer.from_crs(3857,2056,always_xy=True,allow_ballpark=False)
    files=[];zoom_stats=[];max_error=0.
    with rasterio.Env(GDAL_CACHEMAX=256*1024*1024),rasterio.open(out/'source-mosaic.vrt')as ds:
        for z in range(MIN_Z,MAX_Z+1):
            zvrt,(x0,x1,y0,y1)=warped(ds,z,forward);count=0;omitted=0
            with zvrt:
                for y in range(y0,y1+1):
                    for x in range(x0,x1+1):
                        if not tile_supported(z,x,y,inverse):omitted+=1;continue
                        h=zvrt.read(1,window=Window((x-x0)*SIZE,(y-y0)*SIZE,SIZE,SIZE))
                        if not np.all(np.isfinite(h)):omitted+=1;continue
                        body=rt.encode(h);max_error=max(max_error,float(np.max(np.abs(rt.decode(body)-h))))
                        p=out/f'tiles/{z}/{x}/{y}.png';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
                        files.append({'path':p.relative_to(out).as_posix(),'bytes':len(body),'sha256':rt.digest(p)});count+=1
            zoom_stats.append({'zoom':z,'tiles':count,'omittedPartialOrNodataTiles':omitted});print('PREPARED',z,count,flush=True)
    manifest={'version':VERSION,'sourceIdentity':record['identity'],'bounds':list(BOUNDS),'sourceGridSpacingMetres':.5,'protectedInterior':{'centreLV95':list(CENTRE),'radiusMetres':RADIUS,'polygonSides':64},'minimumSourceSupportMetres':3500,'verticalReference':'LN02 preserved; no AWS pixels or vertical transformation','delivery':{'crs':'EPSG:3857','scheme':'xyz','tileSize':SIZE,'encoding':'terrarium','format':'lossless RGB PNG','minzoom':MIN_Z,'maxzoom':MAX_Z,'resampling':'GDAL average z12-17, bilinear z18','nodata':'omit any partial/nodata tile; no alpha/zero/AWS fill','coverage':'per-level fully supported tile inventory; full source support retained through source-mosaic.vrt','quantizationIncrementMetres':1/256,'maxEncodingErrorMetres':max_error},'processing':{'scriptSha256':rt.repository_text_digest(__file__),'python':sys.version.split()[0],'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':__import__('pyproj').__version__,'numpy':np.__version__,'horizontalOperation':forward.definition,'operationStatedAccuracyMetres':forward.accuracy,'warpTolerancePixels':1e-9,'threads':1,'verticalTransform':'none'},'zooms':zoom_stats,'files':files,'storageBytes':sum(f['bytes']for f in files),'attribution':'©swisstopo'}
    manifest['identity']=rt.stable_id(manifest);save(out/'manifest.json',manifest)
    save(data/EXPERIMENT/('generation-metrics'+suffix+'.json'),{'seconds':time.perf_counter()-start,'generatedAt':datetime.now(timezone.utc).isoformat(),'productIdentity':manifest['identity'],'tiles':len(files),'bytes':manifest['storageBytes']})
    print('PRODUCT',manifest['identity'],len(files),manifest['storageBytes'],'seconds',time.perf_counter()-start,flush=True)

def verify(data,suffix=''):
    record=source_record(data);out=data/(PRODUCT+suffix);m=json.loads((out/'manifest.json').read_text(encoding='utf8'))
    if rt.stable_id({k:v for k,v in m.items()if k!='identity'})!=m['identity']or m['sourceIdentity']!=record['identity']or m['processing']['scriptSha256']!=rt.repository_text_digest(__file__):raise ValueError('Product lineage drift')
    for f in m['files']:
        p=out/f['path']
        if rt.digest(p)!=f['sha256']:raise ValueError('Tile changed')
        rt.decode(p.read_bytes())
    print('VERIFIED',m['identity'],len(m['files']),flush=True);return m

def serve(data,port):
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import re
    m=verify(data);out=data/PRODUCT
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            match=re.fullmatch(r'/tiles/(\d+)/(\d+)/(\d+)\.png',self.path)
            if not match:self.send_error(404);return
            z,x,y=map(int,match.groups());p=out/f'tiles/{z}/{x}/{y}.png'
            if not p.exists():self.send_error(404,'Outside supported regional tile inventory');return
            body=p.read_bytes();self.send_response(200);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','public,max-age=3600');self.send_header('X-Meridian-Product',m['identity']);self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def log_message(self,*args):pass
    print('SERVING',port,flush=True);ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['acquire','prepare','verify','serve']);p.add_argument('--plan');p.add_argument('--suffix',default='');p.add_argument('--port',type=int,default=4181);args=p.parse_args()
    data=rt.resolve_storage_roots(require_data=True).data
    if args.command=='acquire':acquire(data,args.plan)
    elif args.command=='prepare':prepare(data,args.suffix)
    elif args.command=='verify':verify(data,args.suffix)
    else:serve(data,args.port)
