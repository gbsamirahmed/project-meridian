"""Independent retained GIS checks, not a runtime/index implementation."""
from pathlib import Path
import json,sys
import numpy as np,rasterio
from pyproj import Transformer
from shapely.geometry import shape,Point,box
R=Path(__file__).resolve().parents[2]
root=Path(sys.argv[1])/'derived/atlas/water-check-v1';outputs={};tr=Transformer.from_crs(4326,27700,always_xy=True);back=Transformer.from_crs(27700,4326,always_xy=True)
for month in ['2024-03','2024-09']:
 with rasterio.open(root/('monthly-'+month+'.tif')) as d:
  if str(d.crs)!='EPSG:4326' or (d.width,d.height)!=(202,112):raise ValueError('Native raster support differs')
  v=d.read(1);rr,cc=np.indices(v.shape);xs=d.transform.c+(cc+.5)*d.transform.a;ys=d.transform.f+(rr+.5)*d.transform.e;x,y=tr.transform(xs,ys)
  mask=(x>296600)&(x<296800)&(y>86550)&(y<86750)
  counts={str(c):int((v[mask]==c).sum()) for c in [0,1,2]};row,col=d.index(*back.transform(296700,86650));code=int(v[row,col]);expected={'0':0,'1':0,'2':77} if month=='2024-03' else {'0':76,'1':1,'2':0}
  if counts!=expected or code!=(2 if month=='2024-03' else 0):raise ValueError('Accepted native assignment mismatch')
  outputs[month]={'counts':counts,'pointCode':code,'row':row,'column':col,'centres':list(map(list,zip(map(float,x[mask]),map(float,y[mask]))))}
polygons={}
for family,key,value in [('wfd','water_body_id','GB510804505600'),('rfo','rec_out_id','31383')]:
 doc=json.loads((root/(family+'.geojson')).read_text());matches=[f for f in doc['features'] if str(f['properties'].get(key))==value]
 if len(matches)!=1:raise ValueError('Ambiguous native feature')
 f=matches[0];g=shape(f['geometry']);polygons[family]={'valid':g.is_valid,'bounds':list(g.bounds),'pointP1':g.covers(Point(296700,86650)),'areaP1':g.intersection(box(296600,86550,296800,86750)).area,'nativeProperties':f['properties']}
print(json.dumps({'monthly':outputs,'polygons':polygons}))
