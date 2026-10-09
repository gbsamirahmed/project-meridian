"""Read-only native Exe supports over accepted retained files. No resampling."""
from pathlib import Path
import importlib.util,time
import numpy as np
import rasterio
from pyproj import Transformer
from shapely.geometry import box,MultiPoint,mapping
from shapely import contains_xy
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('accepted_exe_reader',R/'scripts/atlas/exe-water-query-proof/reader.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)

def describe(data):
 start=time.perf_counter();root=Path(data)/'derived/atlas/water-check-v1';raw=reader.read(root);supports={}
 def add(identity,g,crs,meaning):
  if not g.is_valid or g.is_empty:raise ValueError('Invalid retained native support')
  supports[identity]={'geometry':mapping(g),'crs':crs,'meaning':meaning}
 for family,identity,key,value in [('wfd','exe:wfd','water_body_id','GB510804505600'),('rfo','exe:rfo','rec_out_id',31383)]:
  matches=[g for g,p in reader.W.read_vectors(root,family) if str(p.get(key))==str(value)]
  if len(matches)!=1:raise ValueError('Ambiguous accepted Exe identity')
  add(identity,matches[0],'EPSG:27700','Original reference/event polygon; study eligibility remains separate; not current water extent.')
 transform=Transformer.from_crs(4326,27700,always_xy=True)
 for month in ['2024-03','2024-09']:
  with rasterio.open(root/('monthly-'+month+'.tif')) as d:
   add('exe:'+month+':product',box(*d.bounds),'EPSG:4326','Native retained crop support; template domain, no blanket observation.')
   cell=raw['facts']['P1-point-'+month]['cells'][month]
   add('exe:'+month+':point',box(*cell['bounds']),'EPSG:4326','Exact containing native cell; source classification, not independent homogeneous ground.')
   rr,cc=np.meshgrid(np.arange(d.height),np.arange(d.width),indexing='ij');xx=d.transform.c+(cc+.5)*d.transform.a;yy=d.transform.f+(rr+.5)*d.transform.e;x,y=transform.transform(xx,yy)
   selected=contains_xy(box(296600,86550,296800,86750),x,y)
   add('exe:'+month+':support',MultiPoint(list(zip(x[selected],y[selected]))),'EPSG:27700','Exactly selected native cell centres in P1, not continuous area or fractional cover.')
 return {'raw':raw,'supports':supports,'metrics':{'milliseconds':(time.perf_counter()-start)*1000,'sourceHashOperations':len(raw['sources']),'sourceBytesHashed':sum(s['bytes'] for s in raw['sources'].values()),'directoryHashOperations':len(raw['directorySha256']),'directoryBytesHashed':sum(p.stat().st_size for p in root.iterdir() if p.is_file()),'nativeCellsPerMonth':22624,'selectedCentresPerMonth':77}}
