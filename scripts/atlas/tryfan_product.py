"""Retained Welsh DTM preparation, no acquisition or reconciliation.

Reuse established Terrarium encoding and recursive unencoded parent means.
Incomplete tiles are recorded but never delivered. Independent of normal app.
"""
import argparse, json, math, sys, time
from pathlib import Path
import numpy as np
import pyproj
import rasterio
from rasterio.transform import from_bounds
from rasterio.windows import Window
from rasterio.warp import reproject, Resampling
from rasterio.features import shapes
from PIL import __version__ as pillow_version
import riffelhorn_terrain as rt
from copernicus_common import mean_parent
from riffelhorn_support import save

VERSION='tryfan-welsh-regional-v2'
SOURCE='sources/atlas/tryfan/welsh-lidar-1m'
PRODUCT='derived/atlas/tryfan/'+VERSION
MIN_Z,MAX_Z,SIZE=13,17,256
SOURCE_HASH='49c131d7de62e0df35f8e02c2f8db3161bfd37f24fea56060fcbb9e6d109b326'
BOUNDS=(264900,357800,267900,360800)

def source_record(data):
    p=data/SOURCE/'rasters/tryfan-004-dtm-1m.tif'
    if rt.digest(p)!=SOURCE_HASH: raise ValueError('Retained source changed')
    with rasterio.open(p) as d:
        if d.crs.to_epsg()!=27700 or tuple(d.bounds)!=BOUNDS or d.res!=(1,1) or d.shape!=(3000,3000) or not np.all(d.read_masks(1)):
            raise ValueError('Source/support contract drift')
    return p

def geometry(z, tiles):
    """Polygonize exact complete-tile union; retain holes and disconnected components."""
    if not tiles:return None
    x0=min(x for x,y in tiles);x1=max(x for x,y in tiles);y0=min(y for x,y in tiles);y1=max(y for x,y in tiles)
    mask=np.zeros((y1-y0+1,x1-x0+1),dtype='uint8')
    for x,y in tiles:mask[y-y0,x-x0]=1
    polygons=[]
    for polygon,value in shapes(mask,mask=mask.astype(bool),connectivity=4):
        def ll(p):return [(p[0]+x0)/2**z*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*(p[1]+y0)/2**z))))]
        polygons.append([[ll(p) for p in ring] for ring in polygon['coordinates']])
    return {'kind':'geojson','geometry':{'type':'MultiPolygon','coordinates':polygons}}

def prepare(data,suffix=''):
    start=time.perf_counter();source=source_record(data);out=data/(PRODUCT+suffix)
    if (out/'manifest.json').exists(): raise ValueError('Immutable product exists; verify or use suffix')
    work=out/'working';work.mkdir(parents=True,exist_ok=True)
    forward=pyproj.Transformer.from_crs(27700,3857,always_xy=True,allow_ballpark=False)
    inverse=pyproj.Transformer.from_crs(3857,27700,always_xy=True,allow_ballpark=False)
    edge=np.linspace(0,1,121);xs=np.r_[264900+3000*edge,np.full(121,267900),267900-3000*edge,np.full(121,264900)];ys=np.r_[np.full(121,357800),357800+3000*edge,np.full(121,360800),360800-3000*edge]
    ex,ny=forward.transform(xs,ys);step=rt.WORLD/2**MIN_Z
    x0=int(math.floor(min(ex)/step+2**(MIN_Z-1)));x1=int(math.floor(max(ex)/step+2**(MIN_Z-1)))
    y0=int(math.floor(2**(MIN_Z-1)-max(ny)/step));y1=int(math.floor(2**(MIN_Z-1)-min(ny)/step))
    bounds=(rt.tile_bounds(MIN_Z,x0,y1)[0],rt.tile_bounds(MIN_Z,x0,y1)[1],rt.tile_bounds(MIN_Z,x1,y0)[2],rt.tile_bounds(MIN_Z,x1,y0)[3])
    def extent(z):
        f=2**(z-MIN_Z);return x0*f,y0*f,(x1-x0+1)*f,(y1-y0+1)*f
    def profile(z):
        _,_,nx,ny=extent(z);return dict(driver='GTiff',width=nx*SIZE,height=ny*SIZE,count=1,dtype='float32',crs='EPSG:3857',transform=from_bounds(*bounds,nx*SIZE,ny*SIZE),nodata=np.nan,tiled=True,blockxsize=256,blockysize=256,compress='deflate',predictor=3,NUM_THREADS='1')
    with rasterio.open(source) as src,rasterio.open(work/f'z{MAX_Z}.tif','w',**profile(MAX_Z)) as dst:
        reproject(rasterio.band(src,1),rasterio.band(dst,1),src_nodata=-9999,dst_nodata=np.nan,resampling=Resampling.bilinear,num_threads=1,ERROR_THRESHOLD=0.0,COORDINATE_OPERATION=forward.get_last_used_operation().definition)
    # Full pixel footprints plus a 2m source interpolation guard, not centre-only validity.
    with rasterio.open(work/f'z{MAX_Z}.tif','r+') as d:
        t=d.transform
        for _,win in d.block_windows(1):
            a=d.read(1,window=win);rr,cc=np.indices(a.shape);rr+=int(win.row_off);cc+=int(win.col_off);valid=np.ones(a.shape,bool)
            for dc,dr in ((0,0),(1,0),(0,1),(1,1)):
                x,y=inverse.transform(t.c+(cc+dc)*t.a,t.f+(rr+dr)*t.e);valid&=(x>=BOUNDS[0]+2)&(x<=BOUNDS[2]-2)&(y>=BOUNDS[1]+2)&(y<=BOUNDS[3]-2)
            a[~valid]=np.nan;d.write(a,1,window=win)
    files=[];levels=[];error=0;lod=[]
    for z in range(MAX_Z,MIN_Z-1,-1):
        sums=[];samples=[]
        if z<MAX_Z:
            with rasterio.open(work/f'z{z+1}.tif') as child,rasterio.open(work/f'z{z}.tif','w',**profile(z)) as parent:
                for _,win in parent.block_windows(1):
                    a=child.read(1,window=Window(win.col_off*2,win.row_off*2,win.width*2,win.height*2));b=mean_parent(a);parent.write(b,1,window=win)
                    good=np.isfinite(b);delta=a.reshape(a.shape[0]//2,2,a.shape[1]//2,2)-b[:,None,:,None];r=delta[np.broadcast_to(good[:,None,:,None],delta.shape)]
                    if r.size:sums.append([len(r),float(np.sum(r.astype('float64')**2)),float(np.max(abs(r)))]);samples.append(r[::max(1,len(r)//1000)])
            lod.append({'parent':z,'child':z+1,'cells':sum(v[0] for v in sums),'rms':math.sqrt(sum(v[1] for v in sums)/sum(v[0] for v in sums)),'max':max(v[2] for v in sums),'sampleAbsP95':float(np.percentile(abs(np.concatenate(samples)),95))})
        tx,ty,nx,ny=extent(z);complete=[];partial=[];absent=0
        with rasterio.open(work/f'z{z}.tif') as d:
            for y in range(ny):
                for x in range(nx):
                    a=d.read(1,window=Window(x*SIZE,y*SIZE,SIZE,SIZE));valid=int(np.isfinite(a).sum())
                    if valid==SIZE*SIZE:
                        body=rt.encode(a);error=max(error,float(np.max(abs(rt.decode(body)-a))));p=out/f'tiles/{z}/{tx+x}/{ty+y}.png';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
                        files.append({'path':p.relative_to(out).as_posix(),'bytes':len(body),'sha256':rt.digest(p)});complete.append([tx+x,ty+y])
                    elif valid:partial.append({'x':tx+x,'y':ty+y,'validCells':valid})
                    else:absent+=1
        levels.append({'zoom':z,'completeTiles':len(complete),'partialTiles':partial,'absentTiles':absent,'completeTileCoordinates':complete,'validSupport':geometry(z,complete),'groundSampleMetresAtBenchmark':rt.WORLD/(256*2**z)*math.cos(math.radians(53.115))})
        print('LEVEL',z,'complete',len(complete),'partial',len(partial),flush=True)
    m={'version':VERSION,'source':{'path':str(source.relative_to(data)).replace('\\','/'),'sha256':SOURCE_HASH,'bytes':source.stat().st_size,'bounds':BOUNDS,'crs':'EPSG:27700','vertical':'Native values preserved; vertical datum not established by checked primary metadata','acquisition':'2021-03-02 delivery 11 catalogue; per-cell epoch not independently mapped'},
       'levels':sorted(levels,key=lambda r:r['zoom']),'files':sorted(files,key=lambda r:r['path']),'lod':sorted(lod,key=lambda r:r['parent']),
       'delivery':{'minzoom':14,'maxzoom':17,'encoding':'Terrarium','tileSize':256,'encodingMaxError':error,'sourceInformation':'1m distributed grid; z17 approximately 0.72m resampling, no new observations','parents':'2x2 unencoded float64 mean stored float32; equal Mercator pixel-area weighting; strict missing support'},
       'processing':{'scriptSha256':rt.repository_text_digest(__file__),'encoderSha256':rt.repository_text_digest(rt.__file__),'parentHelperSha256':rt.repository_text_digest(Path(__file__).with_name('copernicus_common.py')),'python':sys.version.split()[0],'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj.__version__,'proj':pyproj.proj_version_str,'pillow':pillow_version,'horizontalOperation':forward.get_last_used_operation().definition,'horizontalAccuracy':forward.get_last_used_operation().accuracy,'verticalOperation':'none; 2D horizontal warp','sourceFootprintGuardMetres':2,'warp':'bilinear, ERROR_THRESHOLD=0, one thread'},
       'workingHashes':{p.name:rt.digest(p) for p in sorted(work.glob('*.tif'))},'tileBytes':sum(f['bytes'] for f in files),'workingBytes':sum(p.stat().st_size for p in work.glob('*.tif'))}
    m['identity']=rt.stable_id(m);save(out/'manifest.json',m);print('PRODUCT',m['identity'],len(files),m['tileBytes'],'seconds',time.perf_counter()-start,flush=True)

def verify(data,suffix=''):
    source_record(data);out=data/(PRODUCT+suffix);m=json.loads((out/'manifest.json').read_text())
    if rt.stable_id({k:v for k,v in m.items() if k!='identity'})!=m['identity']:raise ValueError('Manifest changed')
    for f in m['files']:
        if rt.digest(out/f['path'])!=f['sha256']:raise ValueError('Tile changed')
    for name,h in m['workingHashes'].items():
        if rt.digest(out/'working'/name)!=h:raise ValueError('Working pyramid changed')
    print('VERIFIED',m['identity'],len(m['files']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','verify']);p.add_argument('--data',type=Path,required=True);p.add_argument('--suffix',default='');a=p.parse_args();globals()[a.action](a.data,a.suffix)
