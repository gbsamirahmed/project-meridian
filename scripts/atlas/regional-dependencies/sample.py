"""Read-only native sampling and independently expressed arithmetic/count oracle."""
import json,math,sys,time
from pathlib import Path
import numpy as np,rasterio
from rasterio.windows import Window
from shapely.geometry import Point,shape
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.path.insert(0,str(R/'scripts/atlas/riffelhorn-retrieval'));import query as Q
PLAN=json.loads((H/'plan.json').read_bytes())
def need(ok,msg):
 if not ok:raise ValueError(msg)
def oracle(a,spacing):
 v=np.asarray(a,dtype=np.float64).reshape(9)
 dx=np.dot(v,[-1,0,1,-2,0,2,-1,0,1])/(8*spacing);dy=np.dot(v,[1,2,1,0,0,0,-1,-2,-1])/(8*spacing)
 angle=float(np.arctan(np.sqrt(dx*dx+dy*dy))*180/np.pi)
 return {'slope':angle,'area-ratio':float(1/np.cos(angle*np.pi/180))}
def main():
 request=json.load(sys.stdin);start=time.perf_counter();s=Q.Session();setup=time.perf_counter()-start
 rasters=[r for r in s.rasters if r['family'] in ['dtm','worldcover']]
 registry={r['id']:{'region':'riffelhorn','family':r['family'],'artifact':r['input'],'native':r['native'],'source':r['sourceRecord'],'rights':r['rights'],'qualification':s.qual['families'][r['family']]} for r in rasters}
 for r in rasters:
  if r['family']=='dtm':
   with rasterio.open(Q.P.safe(s.data,r['input']['path'])) as src:
    need(src.units==('metre',) and src.crs.linear_units=='metre','Incompatible native height/horizontal units')
    registry[r['id']]['unitEvidence']={'bandUnit':src.units[0],'gridUnit':src.crs.linear_units,'verticalRecord':'sources/atlas/riffelhorn/swisstopo-2021-2024/metadata/spatial-validation.json','vertical':'LN02 / EPSG:5728, no transformation'}
 if request.get('mode')=='describe':return {'registry':registry,'setup':s.setup,'unitProvenance':'retained spatial-validation.json + native raster band units (not inferred from CRS)'}
 metrics={'payloadReadCalls':0,'decodedBytes':0,'cellsRead':0,'headerChecks':0,'inputFilesOpened':0,'oraclePayloadReadCalls':0,'oracleDecodedBytes':0,'oracleCellCentrePredicates':0};handles={};rows=[];began=time.perf_counter()
 def opened(r):
  key=r['id']
  if key not in handles:
   p=Q.P.safe(s.data,r['input']['path']);need(p.is_file() and p.stat().st_size==r['input']['bytes'],'Missing/mismatched upstream')
   a=rasterio.open(p);need(str(a.crs)==r['native']['crs'] and list(a.transform)==r['native']['transform'],'Header identity mismatch')
   if r['family']=='dtm':need(a.units==('metre',) and str(a.crs)=='EPSG:2056' and a.transform.a==.5 and a.transform.e==-.5,'Incompatible native units/grid')
   handles[key]=a;metrics['headerChecks']+=1;metrics['inputFilesOpened']+=1
  return handles[key]
 try:
  for t in request.get('tasks',[]):
   if t['kind']=='terrain':
    need(t['stride'] in [1,2],'Unsupported parameter');p=next((p for p in PLAN['sampling']['probes'] if p['id']==t['id']),None);need(p,'Unknown real probe')
    x,y=p['point'];stride=t['stride'];a=[];groups={}
    for j in [-1,0,1]:
     line=[]
     for i in [-1,0,1]:
      xx,yy=x+i*.5*stride,y-j*.5*stride
      match=[r for r in rasters if r['family']=='dtm' and r['native']['bounds'][0]<=xx<r['native']['bounds'][2] and r['native']['bounds'][1]<yy<=r['native']['bounds'][3]];need(len(match)==1,'Missing native stencil support')
      r=match[0];src=opened(r);col,row=(~src.transform)*(xx,yy);row,col=math.floor(row),math.floor(col);cx,cy=src.xy(row,col)
      need(abs(cx-xx)<1e-8 and abs(cy-yy)<1e-8,'Not exact native cell centre')
      v=src.read(1,window=Window(col,row,1,1));value=float(v[0,0]);need(math.isfinite(value) and value!=src.nodata,'Unsupported nodata stencil')
      metrics['payloadReadCalls']+=1;metrics['decodedBytes']+=v.nbytes;metrics['cellsRead']+=1;line.append(value)
      groups.setdefault(r['id'],[]).append({'row':row,'column':col,'x':xx,'y':yy,'value':value})
     a.append(line)
    uses=[{'key':key,'scope':{'crs':'EPSG:2056','bounds':[min(c['x'] for c in cells)-.25,min(c['y'] for c in cells)-.25,max(c['x'] for c in cells)+.25,max(c['y'] for c in cells)+.25],'meaning':'Exact consumed native cell footprints; no interpolation'},'cells':cells} for key,cells in sorted(groups.items())]
    rows.append({'id':t['id'],'region':'riffelhorn','kind':'terrain','point':p['point'],'stride':stride,'spacing':.5*stride,'samples':a,'uses':uses,'oracle':oracle(a,.5*stride)})
   elif t['kind']=='counts':
    p=next((p for p in PLAN['sampling']['areas'] if p['id']==t['id']),None);need(p,'Unknown categorical support');out=s.query({'area':p['area'],'families':['worldcover']},'selective');rec=out['answer']['results'][0];v=rec['detail']['payload'];need(v['kind']=='native-classification-counts','Unsupported count request');r=next(r for r in rasters if r['family']=='worldcover');src=opened(r);window=Window(*v['selection']['window']);a=src.read(1,window=window);metrics['oraclePayloadReadCalls']+=1;metrics['oracleDecodedBytes']+=int(a.nbytes);metrics['oracleCellCentrePredicates']+=int(a.size);aff=src.window_transform(window);g=shape(v['selection']['exactQueryPolygon']);counts={}
    for row in range(a.shape[0]):
     for col in range(a.shape[1]):
      x,y=aff*(col+.5,row+.5)
      if g.covers(Point(x,y)):
       code=str(int(a[row,col]));counts[code]=counts.get(code,0)+1
    need(counts==v['counts'],'Independent categorical oracle disagrees');m=out['metrics'];metrics['payloadReadCalls']+=m['payloadReadCalls'];metrics['decodedBytes']+=m['decodedPayloadBytes'];metrics['cellsRead']+=m['nativeSamplesRead']
    rows.append({'id':t['id'],'region':'riffelhorn','kind':'counts','area':p['area'],'value':v['counts'],'selection':v['selection'],'uses':[{'key':r['id'],'scope':{'crs':'EPSG:2056','bounds':p['area'],'meaning':v['countMeaning']},'selection':v['selection'],'counts':v['counts']}],'oracle':counts})
   else:need(False,'Unsupported derivation/fusion')
 finally:
  for src in handles.values():src.close()
 return {'rows':rows,'registry':registry,'setupSeconds':setup,'samplingSeconds':time.perf_counter()-began,'metrics':metrics,'setup':s.setup,'independentCountOracleIncludesExtraRead':True,'physicalIO':'decoded requested cells only, not compressed block traffic; full verification/setup additional'}
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8')
 try:print(json.dumps(main(),sort_keys=True,allow_nan=False))
 except Exception as e:print(str(e),file=sys.stderr);raise SystemExit(1)
