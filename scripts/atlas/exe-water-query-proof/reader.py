"""Offline retained Exe GIS adapter. No acquisition, geometry repair or state inference."""
from pathlib import Path
import sys,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/atlas'))
import water_compare as W
import numpy as np,rasterio
from pyproj import Transformer
from shapely.geometry import Point,box
from shapely import contains_xy
DATA=ROOT.parent/'meridian-data/derived/atlas/water-check-v1'
MATRIX=Path(__file__).parent/'matrix.json'
MATRIX_SHA='d8afb247c2030367d2a85ae912e42a446cc09e34a49b03b46b4635478d9a304b'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def counts(v):return {str(k):int((v==k).sum()) for k in [0,1,2]}
def read(root=DATA):
 if digest(MATRIX)!=MATRIX_SHA:raise ValueError('Frozen query matrix changed')
 matrix=json.loads(MATRIX.read_text(encoding='utf-8'));pinned=json.loads((ROOT/'docs/atlas/water-check-sources.json').read_text(encoding='utf-8'))
 files={x['file']:x for x in pinned['files'] if x.get('sha256')}
 for n,f in files.items():
  if digest(root/n)!=f['sha256']:raise ValueError('Retained source unavailable or corrupt: '+n)
 vectors={k:W.read_vectors(root,k) for k in ['wfd','phi','flood','rfo']};study=box(*matrix['bounds']);trans=Transformer.from_crs(4326,27700,always_xy=True)
 rasters={};coords=None;grid=None
 for m in ['2024-03','2024-09']:
  with rasterio.open(root/('monthly-'+m+'.tif')) as ds:
   if str(ds.crs)!='EPSG:4326':raise ValueError('Unexpected native CRS')
   a=ds.read(1)
   if not np.isin(a,[0,1,2]).all():raise ValueError('Unknown monthly native code')
   rows,cols=np.indices(a.shape);xx,yy=ds.transform*(cols+.5,rows+.5);x,y=trans.transform(xx,yy)
   g={'shape':list(a.shape),'transform':list(ds.transform)[:6],'bounds':list(ds.bounds),'crs':'EPSG:4326','nominalObservationMetres':30,'nativeDistributedDegrees':list(ds.res),'parentWindow':files['monthly-'+m+'.tif']['subset']['window']}
   if grid is not None and g!=grid:raise ValueError('Monthly grids not identical')
   grid=g;coords=x,y;rasters[m]=a
 facts={};to_geo=Transformer.from_crs(27700,4326,always_xy=True)
 for q in matrix['queries']:
  area=Point(*q['point']) if 'point' in q else box(*q['bounds'])
  if not study.covers(area):facts[q['id']]={'outside':True};continue
  point=area.geom_type=='Point';hits={}
  for k,features in vectors.items():
   hits[k]=[{'id':p['featureId'],'boundaryContact':bool(point and g.boundary.covers(area)),'intersectionAreaM2':None if point else round(g.intersection(area).area,3)} for g,p in features if (g.covers(area) if point else g.intersection(area).area>0)]
  if q['kind']=='feature':
   targets=[(g,p) for g,p in vectors['wfd'] if p.get('water_body_id')==q['feature']]
   if targets:
    area=targets[0][0].intersection(study);hits={k:[{'id':p['featureId'],'intersectionAreaM2':round(g.intersection(area).area,3)} for g,p in fs if g.intersection(area).area>0] for k,fs in vectors.items()}
  cells={};pair=None
  if point:
   lon,lat=to_geo.transform(*q['point']);t=grid['transform'];col=int(np.floor((lon-t[2])/t[0]));row=int(np.floor((lat-t[5])/t[4]));h,w=grid['shape']
   if not (0<=row<h and 0<=col<w):raise ValueError('Study point outside retained raster crop')
   left=t[2]+col*t[0];top=t[5]+row*t[4];bound=[left,top+t[4],left+t[0],top]
   cells={m:{'code':int(a[row,col]),'row':row,'column':col,'parentRow':row+grid['parentWindow'][1],'parentColumn':col+grid['parentWindow'][0],'bounds':bound,'crs':'EPSG:4326'} for m,a in rasters.items()}
  else:
   mask=contains_xy(area,*coords);aa=rasters['2024-03'][mask];bb=rasters['2024-09'][mask];both=(aa!=0)&(bb!=0)
   cells={m:{'counts':counts(a[mask]),'selectedCellCentres':int(mask.sum()),'selection':'native cell centres inside query geometry; not clipped physical fractions'} for m,a in rasters.items()}
   pair={'selectedCellCentres':int(mask.sum()),'bothObserved':int(both.sum()),'anyUnobserved':int((~both).sum()),'marchDetectedSeptemberNotDetected':int(((aa==2)&(bb==1)).sum()),'septemberDetectedMarchNotDetected':int(((aa==1)&(bb==2)).sum()),'pairedCodeCounts':{str(a)+'->'+str(b):int(((aa==a)&(bb==b)).sum()) for a in [1,2] for b in [1,2]}}
  facts[q['id']]={'hits':hits,'cells':cells,**({'pair':pair} if pair else {})}
 records={k:[p for g,p in fs if g.intersection(study).area>0] for k,fs in vectors.items()}
 return {'matrixSha256':digest(MATRIX),'sources':{n:{'path':'meridian-data/derived/atlas/water-check-v1/'+n,'sha256':f['sha256'],'bytes':(root/n).stat().st_size,'retrievedUtc':f.get('retrievedUtc'),**({k:f[k] for k in ['subset','parentListing','url'] if k in f})} for n,f in files.items()},'rights':pinned['familyRights'],'records':records,'grid':grid,'facts':facts,'coordinateOperation':pinned['coordinateOperation'],'directorySha256':{p.name:digest(p) for p in sorted(root.iterdir()) if p.is_file()}}
if __name__=='__main__':print(json.dumps(read(Path(sys.argv[1]) if len(sys.argv)>1 else DATA),sort_keys=True,allow_nan=False))
