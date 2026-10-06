"""Read-only native raster adapter. No acquisition, categorical resampling or inference."""
import argparse, hashlib, json, math, time
from pathlib import Path
import numpy as np
import rasterio
from pyproj import Transformer
from shapely.geometry import box, shape
from shapely import contains_xy
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT.parent/'meridian-data/derived/atlas/semantic-comparison-v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def cell_index(transform,x,y,width,height):
 c,r=~transform*(x,y)
 # Native half-open row/column intervals: west/north included, east/south excluded.
 return (math.floor(r),math.floor(c)) if 0<=r<height and 0<=c<width else None

def inspect(root=DATA):
 start=time.perf_counter();receipts=read(ROOT/'docs/atlas/semantic-comparison-sources.json')
 files={x['file']:x for x in receipts['files']}
 for name in ['tryfan-worldcover.tif','nrw-vegetation-full-features.json']:
  p=root/name
  if not p.exists():return {'status':'unavailable','reason':'retained-data-unavailable','asset':name}
  if sha(p)!=files[name]['sha256']:raise ValueError('Retained checksum mismatch: '+name)
 plan=read(ROOT/'docs/atlas/semantic-comparison-plan.json')['sites']['tryfan']
 with rasterio.open(root/'tryfan-worldcover.tif') as ds:
  values=ds.read(1);t=ds.transform
  if ds.crs.to_string()!='EPSG:4326' or list(values.shape)!=[334,554]:raise ValueError('Unexpected retained grid')
  if list(t)!=files['tryfan-worldcover.tif']['subsetDefinition']['windowTransform']:raise ValueError('Grid transform differs from receipt')
  forward=Transformer.from_crs(27700,4326,always_xy=True)
  inverse=Transformer.from_crs(4326,27700,always_xy=True)
  # Exact native centres transformed, never a reprojected class grid.
  rr,cc=np.indices(values.shape);lon=t.c+(cc+0.5)*t.a;lat=t.f+(rr+0.5)*t.e
  east,north=inverse.transform(lon,lat)
  points=[];supports=[]
  for patch in plan['patches']:
   x,y=patch['centre'];lng,lt=forward.transform(x,y);idx=cell_index(t,lng,lt,ds.width,ds.height)
   if idx is None:raise ValueError('Frozen probe outside retained grid')
   r,c=idx;left,top=t*(c,r);right,bottom=t*(c+1,r+1)
   point={'id':patch['id'],'queryCrs':'EPSG:27700','query':patch['centre'],'nativeQuery':[lng,lt],
    'row':r,'column':c,'parentRow':r+10464,'parentColumn':c+23753,'code':int(values[r,c]),
    'cellBounds':[left,bottom,right,top]}
   points.append(point)
   half=patch['side']/2;b=[x-half,y-half,x+half,y+half]
   mask=(east>=b[0])&(east<b[2])&(north>=b[1])&(north<b[3]);codes,counts=np.unique(values[mask],return_counts=True)
   supports.append({'id':patch['id'],'bounds':b,'crs':'EPSG:27700','selection':'native cell centres inside half-open BNG rectangle',
    'cells':int(mask.sum()),'counts':{str(int(k)):int(v) for k,v in zip(codes,counts)},
    'meaning':'Raster-class assignment counts, not physical surface fractions; edge-intersecting cells without centres are excluded.'})
  # One tiny 20m support centred on the pre-existing summit, not selected after classes.
  x,y=plan['patches'][0]['centre'];m=(east>=x-10)&(east<x+10)&(north>=y-10)&(north<y+10)
  co,cn=np.unique(values[m],return_counts=True)
  supports.append({'id':'summit-20m','bounds':[x-10,y-10,x+10,y+10],'crs':'EPSG:27700','cells':int(m.sum()),
   'counts':{str(int(k)):int(v) for k,v in zip(co,cn)},'selection':'native cell centres inside half-open BNG rectangle',
   'meaning':'Raster-class assignment counts only; does not assert homogeneous physical support.'})
  # A real geographic miss, not a fabricated missing row.
  ox,oy=264800,357700;olng,olat=forward.transform(ox,oy)
  outside={'id':'outside','queryCrs':'EPSG:27700','query':[ox,oy],'nativeQuery':[olng,olat],
   'kind':'gap','reason':'outside-support'}
  if cell_index(t,olng,olat,ds.width,ds.height) is not None:raise ValueError('Outside probe unexpectedly intersects retained raster')
  nrw=read(root/'nrw-vegetation-full-features.json');nrw_claims=[]
  summit=box(*supports[0]['bounds'])
  for f in nrw['features']:
   p=f['properties']
   if p['phase1_code']=='D.1.1' and shape(f['geometry']).intersects(summit):
    nrw_claims.append({'id':str(p['objectid']),'native':p,'geometry':f['geometry'],
     'pointContains':bool(contains_xy(shape(f['geometry']),*plan['patches'][0]['centre'])),
     'summitOverlapM2':round(shape(f['geometry']).intersection(summit).area,6)})
  if not nrw_claims:raise ValueError('Retained summit coexistence evidence missing')
  overview={'shape':[ds.height,ds.width],'cells':int(values.size),'crs':ds.crs.to_string(),'transform':list(t),
   'bounds':list(ds.bounds),'nodata':ds.nodata,'dtype':str(values.dtype),'nativeCodes':[int(x) for x in np.unique(values)],
   'transformOperation':inverse.get_last_used_operation().description,'transformAccuracyM':inverse.get_last_used_operation().accuracy,
   'sampling':'native angular classification grid; nominal10m, not local accuracy or homogeneous ground'}
 # No geometry payload duplication: native records reference exact retained feature IDs.
 for q in nrw_claims:del q['geometry']
 return {'status':'available','grid':overview,'points':points,'supports':supports,'outside':outside,'nrw':nrw_claims,
  'sources':{n:{'sha256':files[n]['sha256'],'bytes':files[n]['bytes'],'path':str(root/n)} for n in ['tryfan-worldcover.tif','nrw-vegetation-full-features.json']},
  'readTimeMs':round((time.perf_counter()-start)*1000,3)}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--data',type=Path,default=DATA);args=parser.parse_args()
 print(json.dumps(inspect(args.data),sort_keys=True,ensure_ascii=False))
