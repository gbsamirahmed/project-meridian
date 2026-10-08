"""Standalone read-only retrieval over the exact prepared Riffelhorn fixture.
No registration, publication, derivation, persistent index or remote service.
"""
from pathlib import Path
import argparse,copy,json,math,sys,time
import numpy as np,pyproj,rasterio,shapely
from rasterio.windows import Window
from shapely.geometry import Point,Polygon,box,shape
from shapely.ops import transform
from shapely.strtree import STRtree
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
sys.path.insert(0,str(R/'scripts/atlas/riffelhorn-fixture'));import prepare as P
pyproj.network.set_network_enabled(False)
PLAN=P.load(H/'plan.json');CORE=box(*P.CORE)
FAMILIES={'dtm','dsm','worldcover','geocover-bedrock','geocover-unconsolidated','glaciers','debris'}

def project(g,source,target):
 if source==target:return g
 return transform(pyproj.Transformer.from_crs(source,target,always_xy=True).transform,g)
def rectangle(bounds):
 x0,y0,x1,y1=bounds;ring=[]
 for a,b in [((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]:
  for n in range(32):ring.append((a[0]+(b[0]-a[0])*n/32,a[1]+(b[1]-a[1])*n/32))
 return Polygon(ring)
def parse(q):
 P.require(isinstance(q,dict) and not set(q)-{'point','area','crs','feature','associated','families','representation','product','time'},'malformed/unsupported query fields')
 crs=q.get('crs','EPSG:2056');P.require(crs in ['EPSG:2056','EPSG:4326','OGC:CRS84'],'unsupported or unknown query CRS')
 crs='EPSG:4326' if crs=='OGC:CRS84' else crs
 P.require(not ('point' in q and 'area' in q),'point and area are exclusive')
 g=None
 for kind,size in [('point',2),('area',4)]:
  if kind not in q:continue
  v=q[kind];P.require(isinstance(v,list) and len(v)==size and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in v),'invalid spatial support')
  if kind=='area':P.require(v[0]<v[2] and v[1]<v[3],'invalid area support');g=rectangle(v)
  else:g=Point(*v)
 if g is not None:
  g=project(g,crs,'EPSG:2056');P.require(g.is_valid and not g.is_empty and all(math.isfinite(x) for x in g.bounds),'invalid transformed support');g=g.intersection(CORE)
  if g.geom_type!='Point' and g.area==0:g=Polygon()
 if 'families' in q:P.require(isinstance(q['families'],list) and bool(q['families']) and all(isinstance(x,str) and x in FAMILIES for x in q['families']),'unsupported evidence family')
 if 'representation' in q:P.require(q['representation'] in ['vector','raster'],'unsupported representation')
 for k in ['feature','product']:
  if k in q:P.require(isinstance(q[k],str) and bool(q[k]),'invalid '+k+' identity')
 if 'associated' in q:P.require(isinstance(q['associated'],bool) and 'feature' in q,'association requires feature identity')
 t=q.get('time')
 if t is not None:
  P.require(isinstance(t,dict) and t.get('role') in ['evidence-epoch','product-reference'],'unsupported temporal qualification')
  if t.get('unknown') is True:P.require(set(t)=={'role','unknown'},'unknown time is not a dated interval')
  else:P.require(set(t)=={'role','start','end'} and all(isinstance(t[k],int) and not isinstance(t[k],bool) and 1<=t[k]<=9999 for k in ['start','end']) and t['start']<=t['end'],'only supported inclusive calendar-year qualification')
 return g

def validate_records(fs,rs,bundle):
 ids=[f['identity'] for f in fs]+[r['id'] for r in rs];P.require(len(ids)==len(set(ids)),'duplicate/conflicting record identity')
 claims={q['id']:q for c in bundle['collections'] for q in c['claims']}
 for f in fs:
  P.require(f['family'] in FAMILIES and f['nativeCrs']=='EPSG:2056','unknown native feature CRS')
  P.require(f['identity'] in claims and bool(claims[f['identity']].get('record',{}).get('href')),'missing provenance reference')
  g=shape(f['native']['geometry']);P.require(g.is_valid and not g.is_empty,'invalid native geometry; no repair')
  P.require(f['parentGlacier'] is None or f['parentGlacier'] in ids,'invalid native association reference')
 for r in rs:P.require(r['family'] in FAMILIES and r['native']['crs'] in ['EPSG:2056','EPSG:4326'] and r['sourceRecord'] and r['rights']['references'],'invalid raster provenance/reference')

class Session:
 def __init__(self,data=None,root=None):
  start=time.perf_counter();self.data=(data or P.resolve_storage_roots(repository_root=R,require_data=True).data).resolve();self.root=(root or self.data/PLAN['preparedRootRelative']).resolve()
  m=P.verify(self.root,self.data);P.require(m['revision']==PLAN['preparedRevision'] and P.sha(self.root/'manifest.json')==PLAN['preparationManifestSha256'],'unsupported prepared fixture identity')
  self.manifest=m;self.input_manifest=P.load(self.root/'input-manifest.json');self.bundle=P.load(self.root/'semantic-evidence.json');self.qual=P.load(self.root/'qualification.json');self.features=P.load(self.root/'features.json')['features'];self.rasters=P.load(self.root/'raster-bindings.json')['rasters'];validate_records(self.features,self.rasters,self.bundle)
  self.definitions={d['id']:d for d in self.bundle['definitions']};self.collections={c['id'].split(':')[0]:c for c in self.bundle['collections']};self.resources={P.digest(P.canonical(r['ref'])):r for r in self.bundle['resources']}
  indexing=time.perf_counter();self.records=[]
  for f in self.features:self.records.append({'id':f['identity'],'family':f['family'],'representation':'vector','product':self.collections[f['family']]['product']['id'],'record':f})
  for r in self.rasters:self.records.append({'id':r['id'],'family':r['family'],'representation':'raster','product':r['sourceRecord']['dataset'],'record':r})
  self.records.sort(key=lambda r:r['id']);self.record_sizes=[len(P.canonical(r['record'])) for r in self.records];self.byid={r['id']:i for i,r in enumerate(self.records)};self.groups={f:[i for i,r in enumerate(self.records) if r['family']==f] for f in FAMILIES};self.parents={}
  for i,r in enumerate(self.records):
   if r['representation']=='vector' and r['record']['parentGlacier']:self.parents.setdefault(r['record']['parentGlacier'],[]).append(i)
  self.vector_indices=[i for i,r in enumerate(self.records) if r['representation']=='vector'];self.geometries=[shape(self.records[i]['record']['native']['geometry']) for i in self.vector_indices];self.geo={i:g for i,g in zip(self.vector_indices,self.geometries)};self.tree=STRtree(self.geometries)
  self.setup={'elapsedSeconds':time.perf_counter()-start,'organisationSeconds':time.perf_counter()-indexing,'loadedRecords':44,'geometryRecordsBuilt':38,'metadataMembersParsed':5,'metadataMemberBytes':sum(a['bytes'] for a in m['artifacts']),'verificationInputHashBytes':120347916,'persistentIndexBytes':0,'physicalIO':'current verification/reconstruction and GDAL/archive reads are additional; member parse bytes and hash bytes are logical, not cold disk traffic'}
 def temporal(self,r):
  family=r['family'];f=r['record']
  if family in ['glaciers','debris']:epoch={'status':'known','year':int(f['native']['properties']['year_acq']),'basis':'native year_acq','role':'survey'};product={'status':'known','year':int(f['native']['properties']['year_rel']),'basis':'native year_rel release'}
  elif family=='worldcover':epoch={'status':'known','year':2021,'basis':'prepared nominal2021v200 context','role':'nominal-epoch'};product={'status':'known','year':2021,'basis':'nominal product2021v200'}
  else:
   epoch={'status':'unknown','reason':self.qual['families']['geocover' if family.startswith('geocover') else family]['time']}
   product={'status':'known','year':2024 if family=='dtm' else 2021,'basis':'documented2024 product' if family=='dtm' else 'documented2021 distribution; exact subrelease unknown'} if family in ['dtm','dsm'] else {'status':'unknown','reason':'GeoCover exact release identity unknown'}
  return {'evidence-epoch':epoch,'product-reference':product}
 def qualification_match(self,r,q,m):
  m['qualificationChecks']+=1
  if 'families' in q and r['family'] not in q['families']:return False
  if 'representation' in q and r['representation']!=q['representation']:return False
  if 'product' in q and r['product']!=q['product']:return False
  if 'feature' in q and not (r['representation']=='vector' and (r['id']==q['feature'] or (q.get('associated') and r['representation']=='vector' and r['record']['parentGlacier']==q['feature']))):return False
  if 'time' in q:
   t=q['time'];value=self.temporal(r)[t['role']]
   if t.get('unknown'):return value['status']=='unknown'
   return value['status']=='known' and t['start']<=value['year']<=t['end']
  return True
 def candidates(self,q,g,mode,m):
  ids=list(range(len(self.records)))
  if mode=='scan':return ids
  if 'families' in q:ids=sorted(set(i for f in q['families'] for i in self.groups[f]));m['directoryLookups']+=len(q['families'])
  if mode=='grouped':return ids
  if 'feature' in q:
   wanted=([self.byid[q['feature']]] if q['feature'] in self.byid and self.records[self.byid[q['feature']]]['representation']=='vector' else [])+(self.parents.get(q['feature'],[]) if q.get('associated') else []);ids=sorted(set(ids)&set(wanted));m['directoryLookups']+=1+int(bool(q.get('associated')))
  if g is not None:
   selected={self.vector_indices[int(n)] for n in self.tree.query(g)};ids=[i for i in ids if self.records[i]['representation']=='raster' or i in selected];m['spatialIndexQueries']+=1
  return ids
 def native_spatial(self,r,g,m):
  m['exactSpatialChecks']+=1
  if r['representation']=='vector':
   source=self.geo[self.byid[r['id']]]
   ok=source.covers(g) if g.geom_type=='Point' else source.intersection(g).area>0
   if not ok:m['spatialFalsePositiveCandidates']+=1
   return ok,None
  a=r['record'];native=project(g,'EPSG:2056',a['native']['crs']);bounds=a['native']['bounds'];aff=rasterio.Affine(*a['native']['transform'][:6]);height,width=a['native']['shape']
  if native.geom_type=='Point':
   col,row=(~aff)*(native.x,native.y);row,col=math.floor(row),math.floor(col)
   return 0<=row<height and 0<=col<width,{'kind':'native-cell','row':row,'column':col,'crs':a['native']['crs'],'point':[native.x,native.y]}
  if box(*bounds).intersection(native).area<=0:return False,None
  x0,y0,x1,y1=native.bounds;c0,r0=(~aff)*(x0,y1);c1,r1=(~aff)*(x1,y0);left=max(0,math.floor(c0));top=max(0,math.floor(r0));right=min(width,math.ceil(c1));bottom=min(height,math.ceil(r1))
  return True,{'kind':'native-window-candidates','window':[left,top,max(0,right-left),max(0,bottom-top)],'crs':a['native']['crs'],'exactQueryPolygon':shapely.geometry.mapping(native),'meaning':'conservative native window; not assertion that every pixel intersects query; height samples not bulk materialized'}
 def payload(self,r,selection,m):
  a=r['record'];path=P.safe(self.data,a['input']['path']);P.require(path.is_file() and path.stat().st_size==a['input']['bytes'],'native payload unavailable or size mismatched');m['payloadAvailabilityChecks']+=1
  if selection['kind']!='native-cell' and r['family']!='worldcover':return {'kind':'support-selection','selection':selection,'value':'not requested; no height aggregation/interpolation'}
  if selection['kind']=='native-cell':window=Window(selection['column'],selection['row'],1,1)
  else:window=Window(*selection['window'])
  with rasterio.open(path) as src:
   P.require(str(src.crs)==a['native']['crs'] and list(src.shape)==a['native']['shape'] and list(src.transform)==a['native']['transform'],'native payload header mismatched')
   values=src.read(1,window=window);m['payloadReadCalls']+=1;m['decodedPayloadBytes']+=int(values.nbytes);m['nativeSamplesRead']+=int(values.size)
   if selection['kind']=='native-cell':
    value=float(values[0,0]);nodata=not math.isfinite(value) or value==src.nodata
    if r['family']=='worldcover':
     code=int(value);collection=self.collections['worldcover'];claim=next((c for c in collection['claims'] if c['native']['fields']['code']==code),None);P.require(claim is not None,'unbound native WorldCover code')
     return {'kind':'gap' if nodata else 'native-category','reason':'no-observation' if nodata else None,'nativeCode':code,'nativeClaim':claim,'selection':selection,'physicalAbsenceInferred':False}
    return {'kind':'gap' if nodata else 'native-height','reason':'no-observation' if nodata else None,'nativeValue':None if nodata else value,'selection':selection,'unit':{'status':'unknown','reason':'unit not explicitly declared in prepared raster binding; provider records remain referenced; do not infer from CRS'},'vertical':self.qual['families'][r['family']]['vertical'],'physicalAccuracy':'not established by grid spacing'}
   aff=src.window_transform(window);rows,cols=np.indices(values.shape);xs=aff.c+(cols+.5)*aff.a;ys=aff.f+(rows+.5)*aff.e;mask=shapely.covers(shape(selection['exactQueryPolygon']),shapely.points(xs,ys));selected=values[mask];codes,counts=np.unique(selected,return_counts=True);m['cellCentrePredicates']+=int(values.size)
   return {'kind':'native-classification-counts','counts':{str(int(k)):int(n) for k,n in zip(codes,counts)},'selectedCellCentres':int(selected.size),'selection':selection,'countMeaning':'sampled native cell centres within qualified query, not physical area fractions or confidence','emptyMeaning':'no sampled cell centre; not physical absence'}
 def envelope(self,r,selection,m):
  f=r['record'];family=r['family'];m['provenanceChecks']+=1
  if r['representation']=='vector':
   col=self.collections[family];claim=next(c for c in col['claims'] if c['id']==r['id']);refs=[col['product']]+[a['namespace'] for a in claim.get('associations',[])];resources=[];seen=set()
   while refs:
    ref=refs.pop();key=P.digest(P.canonical(ref))
    if key in seen:continue
    P.require(key in self.resources,'unresolved source provenance');seen.add(key);res=self.resources[key];resources.append(res);refs.extend(res['inputs']);m['resourceReferencesResolved']+=1
   context={**col['context'],**claim.get('context',{})}
   detail={'nativeFields':f['native']['properties'],'nativeIdentity':f['native']['id'],'geometry':{'type':f['native']['geometry']['type'],'crs':f['nativeCrs'],'bounds':list(self.geo[self.byid[r['id']]].bounds),'asset':'fixture-relative:features.json','selector':r['id'],'sha256':next(a['sha256'] for a in self.manifest['artifacts'] if a['path']=='features.json'),'support':'full retained geometry, never clipped'},'nativeClaim':claim,'definitions':[self.definitions[claim['native']['property']['id']]],'mappingQualifications':[a for a in self.bundle['mappings'] if a['from']['id']==claim['native']['property']['id']],'context':context,'resources':sorted(resources,key=lambda a:a['ref']['id']),'associations':claim.get('associations',[])}
  else:
   detail={'binding':f,'selection':selection,'payload':self.payload(r,selection,m) if selection else {'kind':'support-reference','meaning':'no spatial samples requested'}}
   if family=='worldcover':
    detail['semanticContext']=self.collections['worldcover']['context'];detail['definitions']=[d for d in self.bundle['definitions'] if d['id'].startswith('worldcover:')];detail['mappingQualifications']=[a for a in self.bundle['mappings'] if a['from']['id']=='worldcover:native-property']
  qual='geocover' if family.startswith('geocover') else 'glamos' if family in ['glaciers','debris'] else family
  return {'identity':r['id'],'family':family,'representation':r['representation'],'productSelector':r['product'],'preparationRevision':self.manifest['revision'],'method':self.manifest['method'],'temporal':self.temporal(r),'qualification':self.qual['families'][qual],'evidenceKind':'native evidence, no new derived physical interpretation','detail':detail}
 def query(self,q,mode='selective'):
  start=time.perf_counter();P.require(mode in ['scan','grouped','selective'],'unsupported organisation');g=parse(q);m={k:0 for k in ['recordsConsidered','candidates','qualificationChecks','exactSpatialChecks','spatialFalsePositiveCandidates','directoryLookups','spatialIndexQueries','provenanceChecks','resourceReferencesResolved','payloadAvailabilityChecks','payloadReadCalls','decodedPayloadBytes','nativeSamplesRead','cellCentrePredicates','metadataFileReads','candidateRecordBytesRepresented','ancestryTraversals']}
  results=[]
  if g is None or not g.is_empty:
   ids=self.candidates(q,g,mode,m);m['candidates']=len(ids)
   for i in ids:
    m['recordsConsidered']+=1;m['candidateRecordBytesRepresented']+=self.record_sizes[i];r=self.records[i]
    if not self.qualification_match(r,q,m):continue
    selection=None
    if g is not None:
     ok,selection=self.native_spatial(r,g,m)
     if not ok:continue
    results.append(self.envelope(r,selection,m))
  gap='outside-support' if g is not None and g.is_empty else 'no-matching-retained-evidence' if not results else None
  answer={'schema':'atlas-riffelhorn-standalone-retrieval/v1','preparedRevision':self.manifest['revision'],'query':q,'results':results,'gap':{'reason':gap,'explanation':'fixture/support/predicate result, not physical absence; inventory completeness unknown'} if gap else None,'boundary':'standalone prepared fixture; not an Atlas publication','coordinateQualification':self.qual['coordinateOperation'],'fixtureApplicability':self.qual['core'],'spatialSelectionRule':'spatial queries limited to core; full native feature support retained; vector point covers/area positive intersection; raster point half-open affine; area window is candidate selection, WC counts use centres','rightsBoundary':self.qual['rightsBoundary']}
  m['resultCount']=len(results);m['answerUtf8Bytes']=len(P.canonical(answer));m['elapsedSeconds']=time.perf_counter()-start
  return {'answer':answer,'metrics':m}

def main():
 p=argparse.ArgumentParser();p.add_argument('--query');p.add_argument('--matrix',action='store_true');p.add_argument('--mode',choices=['scan','grouped','selective'],default='selective');a=p.parse_args();s=Session()
 if a.matrix:
  matrix=P.load(H/'matrix.json');print(json.dumps({'setup':s.setup,'answers':{c['id']:P.digest(P.canonical(s.query(c['query'],a.mode)['answer'])) for c in matrix['cases']}}))
 else:print(json.dumps(s.query(json.loads(a.query or '{}'),a.mode),ensure_ascii=False,allow_nan=False))
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8')
 try:main()
 except (ValueError,KeyError,TypeError,FileNotFoundError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
