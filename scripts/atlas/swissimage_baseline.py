"""Frozen four-tile source-derived appearance preparation, never application startup.

Linear-light premultiplied RGBA area resampling; no radiometric correction.
The assumed sRGB transfer is a resampling convention, not source calibration.
"""
import argparse, hashlib, json, math, platform, time
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_bounds
from PIL import Image, __version__ as pillow_version
from pyproj import Transformer, __version__ as pyproj_version

VERSION = 'riffelhorn-swissimage-baseline-v1'
BOUNDS = (2624000, 1091000, 2626000, 1093000)
TILES = {'2624-1091', '2624-1092', '2625-1091', '2625-1092'}
SIZE, MIN_Z, MAX_Z = 512, 12, 18
WORLD = 40075016.68557849
PATCHES = {'ordinary': (2625240,1092530,60), 'steep': (2624805,1092330,60),
           'summit': (2624810,1092252,150), 'dark-context': (2624740,1092318,150)}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n', encoding='utf8')

def linear(a):
    a=np.asarray(a,dtype=np.float32)/255
    return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)

def encoded(a):
    a=np.clip(a,0,1)
    return np.rint(255*np.where(a<=.0031308,12.92*a,1.055*a**(1/2.4)-.055)).astype('uint8')

def rgba(field):
    alpha=np.clip(field[3],0,1)
    rgb=np.divide(field[:3],alpha[None],out=np.zeros_like(field[:3]),where=alpha[None]>0)
    return np.dstack([encoded(rgb).transpose(1,2,0),np.rint(alpha*255).astype('uint8')])

def parent(children):
    """Equal Mercator-area means of unencoded, premultiplied child samples."""
    n=children[0].shape[1]; a=np.zeros((4,2*n,2*n),dtype='float32')
    for k,c in enumerate(children): a[:,(k//2)*n:(k//2+1)*n,(k%2)*n:(k%2+1)*n]=c
    return a.reshape(4,n,2,n,2).mean(axis=(2,4),dtype='float64').astype('float32')

def tile_transform(z,x,y):
    step=WORLD/(2**z*SIZE)
    return from_origin(-WORLD/2+x*SIZE*step,WORLD/2-y*SIZE*step,step,step)

def entries(repo):
    c=json.loads((repo/'docs/atlas/riffelhorn-data-catalog.json').read_text(encoding='utf8'))
    rows=[a for a in c['assets'] if a['product']=='swissimage-dop10' and a['tile'] in TILES]
    assert len(rows)==4 and {r['tile'] for r in rows}==TILES
    return c['external_root_relative'],sorted(rows,key=lambda a:a['tile'])

def verify_sources(repo,data):
    root,rows=entries(repo); result=[]
    for r in rows:
        p=data/root/r['path']; assert digest(p)==r['sha256'],str(p)
        with rasterio.open(p) as s:
            assert s.crs.to_epsg()==2056 and s.count==3 and s.width==s.height==10000
            assert s.dtypes==('uint8',)*3 and abs(s.res[0]-.1)<1e-9
            result.append({'tile':r['tile'],'path':p.relative_to(data).as_posix(), 'sha256':r['sha256'],
                           'bytes':p.stat().st_size,'bounds':list(s.bounds),'nodata':s.nodata,
                           'colourInterpretation':[v.name for v in s.colorinterp]})
    return result

class Sources:
    def __init__(self,data,rows): self.datasets=[rasterio.open(data/r['path']) for r in rows]
    def close(self):
        for s in self.datasets:s.close()
    def window(self,bounds):
        # Snap a bounded read onto the existing native 0.1m mosaic grid. No new source extent.
        w,s,e,n=bounds
        w=max(BOUNDS[0],math.floor((w-BOUNDS[0])/.1)*.1+BOUNDS[0])
        e=min(BOUNDS[2],math.ceil((e-BOUNDS[0])/.1)*.1+BOUNDS[0])
        s=max(BOUNDS[1],math.floor((s-BOUNDS[1])/.1)*.1+BOUNDS[1])
        n=min(BOUNDS[3],math.ceil((n-BOUNDS[1])/.1)*.1+BOUNDS[1])
        if w>=e or s>=n:return None,None
        width=round((e-w)/.1);height=round((n-s)/.1)
        a=np.zeros((4,height,width),dtype='float32')
        for ds in self.datasets:
            l,b,r,t=ds.bounds; il=max(l,w);ir=min(r,e);ib=max(b,s);it=min(t,n)
            if il>=ir or ib>=it:continue
            cw=round((ir-il)/.1);ch=round((it-ib)/.1)
            win=Window(round((il-l)/.1),round((t-it)/.1),cw,ch)
            rgb=ds.read(window=win); mask=(ds.dataset_mask(window=win)>0).astype('float32')
            yy=round((n-it)/.1);xx=round((il-w)/.1)
            a[:3,yy:yy+ch,xx:xx+cw]=linear(rgb)*mask
            a[3,yy:yy+ch,xx:xx+cw]=mask
        return a,from_origin(w,n,.1,.1)
    def finest(self,z,x,y):
        transform=tile_transform(z,x,y);step=transform.a
        bounds=(transform.c,transform.f-SIZE*step,transform.c+SIZE*step,transform.f)
        w,s,e,n=transform_bounds('EPSG:3857','EPSG:2056',*bounds,densify_pts=21)
        a,tr=self.window((w-.3,s-.3,e+.3,n+.3)); out=np.zeros((4,SIZE,SIZE),dtype='float32')
        if a is not None:
            reproject(a,out,src_transform=tr,src_crs='EPSG:2056',dst_transform=transform,
                      dst_crs='EPSG:3857',resampling=Resampling.average,num_threads=1,
                      init_dest_nodata=True,dst_nodata=0)
        return out

def write_field(out,z,x,y,a,files):
    f=out/f'fields/{z}/{x}/{y}.npz'; f.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(f,rgba=a)
    p=out/f'tiles/{z}/{x}/{y}.png';p.parent.mkdir(parents=True,exist_ok=True)
    Image.fromarray(rgba(a)).save(p,compress_level=6)
    for path in (f,p):files.append({'path':path.relative_to(out).as_posix(),'bytes':path.stat().st_size,'sha256':digest(path)})

def read_field(out,z,x,y):
    p=out/f'fields/{z}/{x}/{y}.npz'
    return np.load(p)['rgba'] if p.exists() else np.zeros((4,SIZE,SIZE),dtype='float32')

def build(repo,data,out):
    if (out/'manifest.json').exists():raise ValueError('Immutable product exists; use a named rebuild sibling')
    start=time.perf_counter();rows=verify_sources(repo,data); sources=Sources(data,rows)
    try:
        w,s,e,n=transform_bounds('EPSG:2056','EPSG:3857',*BOUNDS,densify_pts=21)
        span=WORLD/2**MAX_Z
        coords={(x,y) for x in range(math.floor((w+WORLD/2)/span),math.floor((e+WORLD/2)/span)+1)
                        for y in range(math.floor((WORLD/2-n)/span),math.floor((WORLD/2-s)/span)+1)}
        files=[];levels=[]
        for z in range(MAX_Z,MIN_Z-1,-1):
            delivered=[];partials=0;valid=0.
            for x,y in sorted(coords):
                a=sources.finest(z,x,y) if z==MAX_Z else parent([read_field(out,z+1,2*x+dx,2*y+dy) for dy in (0,1) for dx in (0,1)])
                if not np.any(a[3]):continue
                write_field(out,z,x,y,a,files);delivered.append([x,y]);partials+=int(np.any(a[3]<.999999));valid+=float(a[3].sum())
            levels.append({'zoom':z,'tiles':delivered,'partialTiles':partials,'supportedSampleArea':valid,
                           'groundSampleMetresAtRiffelhorn':WORLD*math.cos(math.radians(45.97910794))/(SIZE*2**z)})
            print('LEVEL',z,len(delivered),flush=True)
            coords={(x//2,y//2) for x,y in delivered}
        manifest={'id':VERSION,'revision':'v1','origin':'source-derived regional appearance; processed orthophoto, not raw observation',
          'sources':rows,'nativeCRS':'EPSG:2056','sourceBounds':list(BOUNDS),'distributedGridMetres':.1,'nominalSourceInformationMetres':.25,
          'acquisition':{'mosaicYear':2023,'pixelTimestamp':'UNKNOWN','sensor':'UNKNOWN','sun':'UNKNOWN','viewGeometry':'UNKNOWN'},
          'delivery':{'scheme':'xyz','crs':'EPSG:3857','tileSize':SIZE,'minzoom':MIN_Z,'maxzoom':MAX_Z,'format':'lossless RGBA PNG',
            'finest':'GDAL area average of assumed-sRGB decoded linear-light premultiplied RGB and validity; one thread',
            'parents':'recursive 2x2 equal Mercator-area means of unencoded premultiplied linear RGB/alpha; independently encoded',
            'colour':'Assumed sRGB RGB8, no colour profile calibration or exposure modification',
            'alpha':'area support fraction, not quality/shadow mask; valid black pixels retained; absent children transparent',
            'informationCeiling':'25cm nominal upstream information; 10cm distributed grid and z18 ~0.207m are resampling, not new observations'},
          'lineage':{'radiometricCorrection':'none','syntheticFilling':'none','reprojection':'EPSG:2056 to EPSG:3857, horizontal only',
                     'geometryUsedForPreparation':'none; upstream orthorectification geometry exact revision UNKNOWN'},
          'rights':{'attribution':'©swisstopo','licence':'swisstopo custom OGD terms',
                    'reference':'https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices'},
          'software':{'python':platform.python_version(),'numpy':np.__version__,'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__,'pyproj':pyproj_version,'pillow':pillow_version},
          'recipeSha256':digest(__file__),'levels':sorted(levels,key=lambda r:r['zoom']),'files':sorted(files,key=lambda r:r['path'])}
        manifest['identity']=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        save(out/'manifest.json',manifest)
        save(out/'generation.json',{'seconds':time.perf_counter()-start,'identity':manifest['identity'],'sourceBytes':sum(r['bytes'] for r in rows),
                                   'tileBytes':sum(r['bytes'] for r in files if r['path'].startswith('tiles/')),'fieldBytes':sum(r['bytes'] for r in files if r['path'].startswith('fields/'))})
    finally:sources.close()

def verify(repo,data,out):
    m=json.loads((out/'manifest.json').read_text(encoding='utf8'));copy={k:v for k,v in m.items() if k!='identity'}
    assert m['identity']==hashlib.sha256(json.dumps(copy,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert m['recipeSha256']==digest(__file__) and m['sources']==verify_sources(repo,data)
    max_parent_error=0.;colour_rounding=0.;partial=0
    for r in m['files']:assert digest(out/r['path'])==r['sha256'],r['path']
    for l in m['levels']:
        z=l['zoom']
        for x,y in l['tiles']:
            a=read_field(out,z,x,y);assert np.all(np.isfinite(a)) and a.min()>=0 and a.max()<=1.000001
            img=np.asarray(Image.open(out/f'tiles/{z}/{x}/{y}.png'))
            assert np.array_equal(img,rgba(a));partial+=int(np.any(a[3]<.999999))
            if z<MAX_Z:
                # Independent direct four-child reduction, avoiding the parent's mosaic helper.
                expect=np.zeros_like(a,dtype='float64')
                for dy in (0,1):
                    for dx in (0,1):
                        c=read_field(out,z+1,2*x+dx,2*y+dy)
                        q=(c[:,::2,::2].astype('float64')+c[:,1::2,::2]+c[:,::2,1::2]+c[:,1::2,1::2])/4
                        expect[:,dy*SIZE//2:(dy+1)*SIZE//2,dx*SIZE//2:(dx+1)*SIZE//2]=q
                max_parent_error=max(max_parent_error,float(np.max(abs(a-expect))))
            valid=a[3]>.999999
            if valid.any():colour_rounding=max(colour_rounding,float(np.max(abs(linear(img[:,:,:3].transpose(2,0,1))[:,valid]-a[:3,valid]))))
    result={'identity':m['identity'],'manifestSha256':digest(out/'manifest.json'),'verifiedFiles':len(m['files']),
            'parentMaxLinearError':max_parent_error,'maxLinearEncodingDifference':colour_rounding,'partialTiles':partial,
            'noCorrection':True,'sourceHashesUnchanged':True}
    save(out/'verification.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','verify']);p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();repo=Path(__file__).resolve().parents[2]
    (build if args.command=='build' else verify)(repo,args.data,args.out)
