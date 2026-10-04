"""Bounded frozen Copernicus product; no Swiss/AWS composition or app imports."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.windows import Window
from rasterio.warp import reproject, Resampling
import pyproj
from PIL import __version__ as pillow_version
import riffelhorn_terrain as rt
from riffelhorn_support import save

REPO = Path(__file__).resolve().parents[2]
VERSION = 'riffelhorn-copernicus-common-v1'
SOURCE = 'sources/atlas/riffelhorn/copernicus-common-2021-v1'
PRODUCT = 'derived/atlas/riffelhorn/'+VERSION
EXPERIMENT = 'experiments/atlas/'+VERSION
MIN_Z, MAX_Z, SIZE = 8, 13, 256
ROOT_X, ROOT_Y = 133, 90
BOUNDS = (rt.tile_bounds(8,133,91)[0], rt.tile_bounds(8,133,91)[1], rt.tile_bounds(8,133,90)[2], rt.tile_bounds(8,133,90)[3])
GEOGRAPHIC = (7.03125,45.089035564831015,8.4375,47.040182144806664)


def mean_parent(a):
    """Unencoded 2x2 mean, float64 accumulation/float32 storage.

    Missing support propagates: never average around a hole to invent support.
    Uniform weights represent Web Mercator pixel area, not ground-area mass.
    """
    if a.ndim != 2 or any(n % 2 for n in a.shape):
        raise ValueError('Aligned even raster dimensions required')
    return a.astype('float64').reshape(a.shape[0]//2,2,a.shape[1]//2,2).mean(axis=(1,3)).astype('float32')


def extent(z):
    factor = 2**(z-MIN_Z)
    return ROOT_X*factor, ROOT_Y*factor, factor, 2*factor


def acquire(data):
    previous = json.loads((REPO/'docs/atlas/global-reference-acquisition.json').read_text(encoding='utf8'))
    plan_hash = rt.repository_text_digest(REPO/'docs/atlas/copernicus-common-product-plan.json')
    base = data/SOURCE
    if (base/'acquisition.json').exists():
        return source_record(data)
    def asset(coordinate):
        north, east = coordinate
        name = f'Copernicus_DSM_COG_10_N{north:02}_00_E{east:03}_00_DEM'
        if east == 7 and north in [45,46]:
            old = previous['assets'][f'cop{north}']
            p = data/old['path']
            if rt.digest(p) != old['sha256']: raise ValueError('Assessed asset changed')
            row = {**old, 'reused': True}
        else:
            p = base/'originals'/(name+'.tif')
            receipt = base/'metadata'/(name+'.json')
            if not p.exists():
                p.parent.mkdir(parents=True,exist_ok=True)
                url = 'https://copernicus-dem-30m.s3.amazonaws.com/'+name+'/'+name+'.tif'
                part = p.with_suffix('.part')
                with urlopen(Request(url,headers={'User-Agent':'Meridian-bounded-common-terrain-product'}),timeout=90) as response:
                    headers = dict(response.headers)
                    with part.open('wb') as output:
                        while body := response.read(1024*1024): output.write(body)
                etag = headers.get('ETag','').strip('"')
                if len(etag) != 32 or hashlib.md5(part.read_bytes()).hexdigest() != etag:
                    raise ValueError('Expected complete COG provider ETag verification')
                part.replace(p)
                save(receipt, {'url':url,'path':p.relative_to(data).as_posix(),'sha256':rt.digest(p),'bytes':p.stat().st_size,'acquiredAt':datetime.now(timezone.utc).isoformat(),'headers':headers,'reused':False})
            row = json.loads(receipt.read_text(encoding='utf8'))
            if rt.digest(p) != row['sha256']: raise ValueError('Frozen additional asset changed')
        with rasterio.open(p) as ds:
            expected = (east-.5/3600,1/3600,0,north+1+.5/3600,0,-1/3600)
            if ds.shape != (3600,3600) or ds.crs.to_epsg() != 4326 or ds.dtypes != ('float32',) or ds.nodata is not None or ds.tags().get('AREA_OR_POINT') != 'Point':
                raise ValueError('Unexpected 2021 COG contract')
            if not np.allclose(ds.transform.to_gdal(),expected,rtol=0,atol=1e-10): raise ValueError('Posting alignment differs')
            row.update({'latitude':north,'longitude':east,'raster':{'shape':list(ds.shape),'crs':str(ds.crs),'transform':list(ds.transform)[:6],'nodata':ds.nodata,'tags':ds.tags()}})
        print('SOURCE',north,east,row['bytes'],'reused',row['reused'],flush=True)
        return row
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(asset,[(n,e) for n in [45,46,47] for e in [7,8]]))
    record = {'version':VERSION,'release':'Public COG distribution documenting 2021 release; exact sub-release unknown','planSha256':plan_hash,'previousAssessmentInputIdentity':previous['identity'],'assets':rows,'height':'EGM2008 metres, unchanged','totalSourceBytes':sum(r['bytes'] for r in rows)}
    record['identity'] = rt.stable_id(record)
    save(base/'acquisition.json',record)
    save(REPO/'docs/atlas/copernicus-common-acquisition.json',record)
    return record


def source_record(data):
    record = json.loads((data/SOURCE/'acquisition.json').read_text(encoding='utf8'))
    if rt.stable_id({k:v for k,v in record.items() if k != 'identity'}) != record['identity'] or record['planSha256'] != rt.repository_text_digest(REPO/'docs/atlas/copernicus-common-product-plan.json'):
        raise ValueError('Source/plan identity mismatch')
    for row in record['assets']:
        if rt.digest(data/row['path']) != row['sha256']: raise ValueError('Source bytes changed')
    return record


def build_vrt(data,out,record):
    parts = ['<VRTDataset rasterXSize="7200" rasterYSize="10800"><SRS>EPSG:4326</SRS><GeoTransform>6.9998611111111115,0.0002777777777777778,0,48.00013888888889,0,-0.0002777777777777778</GeoTransform><VRTRasterBand dataType="Float32" band="1"><NoDataValue>nan</NoDataValue><UnitType>m</UnitType>']
    for row in record['assets']:
        relative = escape(os.path.relpath(data/row['path'],out).replace('\\','/'))
        parts.append(f'<SimpleSource><SourceFilename relativeToVRT="1">{relative}</SourceFilename><SourceBand>1</SourceBand><SrcRect xOff="0" yOff="0" xSize="3600" ySize="3600"/><DstRect xOff="{(row["longitude"]-7)*3600}" yOff="{(47-row["latitude"])*3600}" xSize="3600" ySize="3600"/></SimpleSource>')
    parts.append('</VRTRasterBand></VRTDataset>')
    (out/'source-mosaic.vrt').write_text(''.join(parts)+'\n',encoding='utf8')


def raster_profile(z):
    _,_,nx,ny = extent(z)
    return {'driver':'GTiff','width':nx*SIZE,'height':ny*SIZE,'count':1,'dtype':'float32','crs':'EPSG:3857','transform':from_bounds(*BOUNDS,nx*SIZE,ny*SIZE),'nodata':np.nan,'tiled':True,'blockxsize':256,'blockysize':256,'compress':'deflate','predictor':3,'NUM_THREADS':'1'}


def prepare(data,suffix=''):
    start = time.perf_counter(); record = source_record(data); out = data/(PRODUCT+suffix)
    if (out/'manifest.json').exists(): raise ValueError('Existing immutable build; verify or use --suffix')
    out.mkdir(parents=True,exist_ok=True); build_vrt(data,out,record)
    operation = pyproj.Transformer.from_crs(4326,3857,always_xy=True,allow_ballpark=False)
    operation.transform(7.76,45.98)
    working = out/'working'; working.mkdir(exist_ok=True)
    with rasterio.Env(GDAL_CACHEMAX=256*1024*1024), rasterio.open(out/'source-mosaic.vrt') as source, rasterio.open(working/f'z{MAX_Z}.tif','w',**raster_profile(MAX_Z)) as destination:
        # GDAL handles EPSG latitude/longitude axis mapping. A pyproj always_xy
        # pipeline passed directly as COORDINATE_OPERATION is not equivalent.
        reproject(rasterio.band(source,1),rasterio.band(destination,1),src_transform=source.transform,src_crs=source.crs,src_nodata=np.nan,dst_transform=destination.transform,dst_crs=destination.crs,dst_nodata=np.nan,resampling=Resampling.bilinear,num_threads=1,ERROR_THRESHOLD=0.0)
    with rasterio.open(working/f'z{MAX_Z}.tif') as check:
        if not all(np.all(np.isfinite(check.read(1,window=w))) for _,w in check.block_windows(1)):
            raise ValueError('Selected complete land support was not transferred; no product accepted')
    files = []; levels = []; max_error = 0
    for z in range(MAX_Z,MIN_Z-1,-1):
        if z != MAX_Z:
            with rasterio.open(working/f'z{z+1}.tif') as children, rasterio.open(working/f'z{z}.tif','w',**raster_profile(z)) as parent:
                for _,window in parent.block_windows(1):
                    block = children.read(1,window=Window(window.col_off*2,window.row_off*2,window.width*2,window.height*2))
                    parent.write(mean_parent(block),1,window=window)
        x0,y0,nx,ny = extent(z); count = 0; omitted = 0
        with rasterio.open(working/f'z{z}.tif') as ds:
            for y in range(ny):
                for x in range(nx):
                    values = ds.read(1,window=Window(x*SIZE,y*SIZE,SIZE,SIZE))
                    if not np.all(np.isfinite(values)): omitted += 1; continue
                    body = rt.encode(values)
                    max_error = max(max_error,float(np.max(np.abs(rt.decode(body)-values))))
                    p = out/f'tiles/{z}/{x0+x}/{y0+y}.png'; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(body)
                    files.append({'path':p.relative_to(out).as_posix(),'bytes':len(body),'sha256':rt.digest(p)}); count += 1
        levels.append({'zoom':z,'tiles':count,'omittedUnsupported':omitted})
        print('PREPARED',z,count,omitted,flush=True)
    manifest = {'version':VERSION,'sourceIdentity':record['identity'],'sourceBytes':record['totalSourceBytes'],'coverageMercator':list(BOUNDS),'coverageGeographic':list(GEOGRAPHIC),
        'delivery':{'crs':'EPSG:3857','scheme':'xyz','tileSize':SIZE,'format':'RGB PNG','encoding':'terrarium','minzoom':MIN_Z,'maxzoom':MAX_Z,'quantizationIncrementMetres':1/256,'maxEncodingErrorMetres':max_error,'height':'EGM2008 preserved','finest':'bilinear source-post reprojection','parents':'2x2 mean unencoded float32 heights; float64 accumulation; uniform Web Mercator pixel area','nodata':'strict support propagation, omit any incomplete tile; no zero/alpha/AWS padding','overzoom':'renderer above z13; no new source information'},
        'processing':{'scriptSha256':rt.repository_text_digest(__file__),'helperSha256':rt.repository_text_digest(rt.__file__),'python':sys.version.split()[0],'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__,'proj':pyproj.proj_version_str,'pillow':pillow_version,'horizontalOperation':operation.definition,'verticalTransformation':'none','threads':1,'warpErrorThreshold':0},
        'levels':sorted(levels,key=lambda row:row['zoom']),'files':sorted(files,key=lambda row:row['path']),'tileStorageBytes':sum(row['bytes'] for row in files),'workingRasterBytes':sum(p.stat().st_size for p in working.glob('*.tif')),'workingHashes':{p.name:rt.digest(p) for p in sorted(working.glob('*.tif'))},'sourceVrtSha256':rt.repository_text_digest(out/'source-mosaic.vrt'),
        'rightsReference':'https://s3.waw3-1.cloudferro.com/swift/v1/portal_uploads_prod/CSCDA_ESA_Mission-specific_Annex_31_Oct_22_latest.pdf'}
    manifest['identity'] = rt.stable_id(manifest); save(out/'manifest.json',manifest)
    summary = {k:v for k,v in manifest.items() if k != 'files'}
    summary.update({'manifestSha256':rt.digest(out/'manifest.json'),'tileCount':len(files),'generationSeconds':time.perf_counter()-start,'generatedAt':datetime.now(timezone.utc).isoformat()})
    save(data/EXPERIMENT/('generation'+suffix+'.json'),summary)
    if not suffix: save(REPO/'docs/atlas/copernicus-common-generation.json',summary)
    print('PRODUCT',manifest['identity'],len(files),manifest['tileStorageBytes'],'seconds',time.perf_counter()-start,flush=True)


def verify(data,suffix=''):
    record = source_record(data); out = data/(PRODUCT+suffix); manifest = json.loads((out/'manifest.json').read_text(encoding='utf8'))
    if rt.stable_id({k:v for k,v in manifest.items() if k != 'identity'}) != manifest['identity'] or manifest['sourceIdentity'] != record['identity'] or manifest['processing']['scriptSha256'] != rt.repository_text_digest(__file__) or manifest['processing']['helperSha256'] != rt.repository_text_digest(rt.__file__):
        raise ValueError('Build identity drift')
    for row in manifest['files']:
        p = out/row['path']
        if rt.digest(p) != row['sha256'] or not np.all(np.isfinite(rt.decode(p.read_bytes()))): raise ValueError('Tile integrity failure')
    for name,checksum in manifest['workingHashes'].items():
        if rt.digest(out/'working'/name) != checksum: raise ValueError('Unencoded pyramid changed')
    print('VERIFIED',manifest['identity'],len(manifest['files']),flush=True)
    return manifest


def serve(data,port):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    manifest = verify(data); out = data/PRODUCT
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            match = re.fullmatch(r'/tiles/(\d+)/(\d+)/(\d+)\.png',self.path)
            path = out/f'tiles/{match[1]}/{match[2]}/{match[3]}.png' if match else None
            if path is None or not path.exists():
                self.send_response(404); self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Cache-Control','no-store'); self.end_headers(); return
            body = path.read_bytes(); etag = '"'+rt.digest(path)+'"'
            self.send_response(304 if self.headers.get('If-None-Match') == etag else 200)
            self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Cache-Control','public,max-age=3600'); self.send_header('ETag',etag); self.send_header('X-Meridian-Product',manifest['identity']); self.send_header('Content-Type','image/png'); self.end_headers()
            if self.headers.get('If-None-Match') != etag:
                try: self.wfile.write(body)
                except (BrokenPipeError,ConnectionResetError): pass
        def log_message(self,*args): pass
    print('SERVING',port,flush=True); ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('command',choices=['acquire','prepare','verify','serve']); parser.add_argument('--suffix',default=''); parser.add_argument('--port',type=int,default=4182); args = parser.parse_args()
    if args.suffix and not re.fullmatch(r'-[a-z0-9-]+',args.suffix): raise ValueError('Simple named sibling rebuild only')
    data = rt.resolve_storage_roots(require_data=True).data
    if args.command == 'acquire': acquire(data)
    elif args.command == 'prepare': prepare(data,args.suffix)
    elif args.command == 'verify': verify(data,args.suffix)
    else: serve(data,args.port)
