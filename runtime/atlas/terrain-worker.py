"""Explicit-root native sampling adapter; frozen accepted arithmetic is the oracle."""
import importlib.util,math,platform,time,hashlib
from pathlib import Path
import numpy as np,rasterio,pyproj
from rasterio.windows import Window
R=Path(__file__).resolve().parents[2]
if hashlib.sha256((R/'scripts/atlas/regional-dependencies/sample.py').read_bytes()).hexdigest()!='9a2c914c272b8f010ee92293bd82fd056af922da9c74966d2eb2d6f4462f6bbb':
 raise ValueError('Frozen accepted sampling/oracle implementation changed')
spec=importlib.util.spec_from_file_location('terrain_reference',R/'scripts/atlas/regional-dependencies/sample.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)

def sample(session,request):
 if set(request)!={'schema','tasks'} or request['schema']!='atlas-runtime-terrain-request/v1':raise ValueError('Unsupported terrain request')
 probes={p['id']:p for p in reference.PLAN['sampling']['probes'] if 'cluster' in p['id']}
 rasters=[r for r in session.rasters if r['family']=='dtm'];handles={};rows=[];start=time.perf_counter()
 registry={r['id']:{'region':'riffelhorn','family':'dtm','artifact':r['input'],'native':r['native'],'source':r['sourceRecord'],'rights':r['rights'],'qualification':session.qual['families']['dtm'],'vertical':'LN02 / EPSG:5728; no transformation; retained spatial-validation record'} for r in rasters}
 try:
  if not isinstance(request['tasks'],list) or len(request['tasks'])>16:raise ValueError('Bounded tasks required')
  seen=set()
  for task in request['tasks']:
   if set(task)!={'id','stride'} or task['id'] not in probes or type(task['stride']) is not int or task['stride'] not in [1,2] or task['id'] in seen:raise ValueError('Unsupported task/parameter')
   seen.add(task['id']);x,y=probes[task['id']]['point'];spacing=.5*task['stride'];a=[];groups={}
   for j in [-1,0,1]:
    line=[]
    for i in [-1,0,1]:
     xx,yy=x+i*spacing,y-j*spacing
     found=[r for r in rasters if r['native']['bounds'][0]<=xx<r['native']['bounds'][2] and r['native']['bounds'][1]<yy<=r['native']['bounds'][3]]
     if len(found)!=1:raise ValueError('Missing native stencil support')
     r=found[0];key=r['id']
     if key not in handles:
      src=rasterio.open(reference.Q.P.safe(session.data,r['input']['path']))
      if src.units!=('metre',) or str(src.crs)!='EPSG:2056' or list(src.transform)!=r['native']['transform'] or src.transform.a!=.5 or src.transform.e!=-.5:
       src.close();raise ValueError('Incompatible native units/CRS/grid')
      handles[key]=src
     src=handles[key];col,row=(~src.transform)*(xx,yy);row,col=math.floor(row),math.floor(col);cx,cy=src.xy(row,col)
     if abs(cx-xx)>1e-8 or abs(cy-yy)>1e-8:raise ValueError('Not an exact native cell centre')
     value=float(src.read(1,window=Window(col,row,1,1))[0,0])
     if not math.isfinite(value) or value==src.nodata:raise ValueError('Unsupported nodata stencil')
     line.append(value);groups.setdefault(key,[]).append({'row':row,'column':col,'x':xx,'y':yy,'value':value})
    a.append(line)
   uses=[{'key':key,'scope':{'crs':'EPSG:2056','bounds':[min(c['x'] for c in cells)-.25,min(c['y'] for c in cells)-.25,max(c['x'] for c in cells)+.25,max(c['y'] for c in cells)+.25],'meaning':'Exact consumed native cell footprints; no interpolation'},'cells':cells} for key,cells in sorted(groups.items())]
   rows.append({'id':task['id'],'point':[x,y],'stride':task['stride'],'spacing':spacing,'samples':a,'uses':uses,'oracle':reference.oracle(a,spacing)})
 finally:
  for src in handles.values():src.close()
 return {'schema':'atlas-runtime-terrain-response/v1','rows':rows,'registry':registry,'environment':{'python':platform.python_version(),'numpy':np.__version__,'rasterio':rasterio.__version__,'pyproj':pyproj.__version__,'samplingWorkerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'oracleSha256':'9a2c914c272b8f010ee92293bd82fd056af922da9c74966d2eb2d6f4462f6bbb'},'metrics':{'milliseconds':(time.perf_counter()-start)*1000,'cellsRead':len(rows)*9,'decodedBytes':len(rows)*36,'filesOpened':len(handles),'physicalIO':'Decoded requested cells; compressed block traffic and full input verification are additional'}}
