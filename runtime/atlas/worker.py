"""Native accepted predicates and disposable SQLite selectors, never publication writes."""
from pathlib import Path
import hashlib,json,math,os,sqlite3,sys,time
from retrieval_query import Qualified
from exe_worker import describe as describe_exe,describe_references
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'scripts/atlas/riffelhorn-retrieval'))
import query as Q
from importlib.util import spec_from_file_location,module_from_spec
terrain_spec=spec_from_file_location('runtime_terrain',Path(__file__).parent/'terrain-worker.py')
terrain=module_from_spec(terrain_spec);terrain_spec.loader.exec_module(terrain)
sys.path.insert(0,str(R/'scripts/atlas/multi-region'))
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('accepted_native',R/'scripts/atlas/multi-region/native-worker.py')
accepted=module_from_spec(spec);spec.loader.exec_module(accepted)

class Failure(Exception):
 def __init__(self,code,message):super().__init__(message);self.code=code
def need(ok,code,message):
 if not ok:raise Failure(code,message)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def normalized(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def valid_query(q,families):
 need(isinstance(q,dict) and not set(q)-{'region','identity','feature','families','representation','product','point','area','crs','time'},'query-invalid','Unsupported query fields; use the documented finite predicates.')
 need(q.get('region') in [None,'tryfan','riffelhorn','exe'],'query-invalid','Unknown region; no fallback.')
 for k in ['identity','feature','product']:
  if k in q:need(isinstance(q[k],str) and bool(q[k]),'query-invalid','Expected a nonempty '+k+' identity.')
 if 'families' in q:need(isinstance(q['families'],list) and bool(q['families']) and all(f in families for f in q['families']),'query-invalid','Unsupported evidence family.')
 if 'representation' in q:need(q['representation'] in ['vector','raster','source-product-metadata','native-cell-summary'],'query-invalid','Unsupported representation.')
 need(not ('point' in q and 'area' in q),'query-invalid','Point and area are exclusive.')
 if 'point' in q or 'area' in q:
  need(q.get('region') is not None,'query-invalid','Spatial queries require an explicit region and native query CRS.')
  for key,n in [('point',2),('area',4)]:
   if key in q:
    v=q[key];need(isinstance(v,list) and len(v)==n and all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in v),'query-invalid','Invalid finite spatial support.')
    if key=='area':need(v[0]<v[2] and v[1]<v[3],'query-invalid','Area bounds must be ordered.')
  allowed=['EPSG:2056','EPSG:4326','OGC:CRS84'] if q['region']=='riffelhorn' else ['EPSG:27700','EPSG:4326','OGC:CRS84']
  need(q.get('crs') in allowed,'query-invalid','Explicit supported query CRS required; no inferred CRS.')
 elif 'crs' in q:need(False,'query-invalid','CRS requires point or area.')
 if 'time' in q:
  t=q['time'];need(isinstance(t,dict) and t.get('role') in ['evidence-epoch','product-reference'],'query-invalid','Unsupported time role.')
  if t.get('unknown') is True:need(set(t)=={'role','unknown'},'query-invalid','Unknown is distinct from a dated interval.')
  else:need(set(t)=={'role','start','end'} and all(isinstance(t[k],int) and not isinstance(t[k],bool) and 1<=t[k]<=9999 for k in ['start','end']) and t['start']<=t['end'],'query-invalid','Only inclusive calendar-year qualification is supported in this adapter.')

class Adapter:
 def validate(self,q):valid_query(q,{r['family'] for r in self.records})
 def __init__(self,a):
  start=time.perf_counter();self.s=Q.Session(data=Path(a['dataRoot']),root=Path(a['preparedRoot']))
  expected=accepted.describe(self.s);actual=a['registration'];expected.pop('administrative');actual={k:v for k,v in actual.items() if k!='administrative'}
  need(expected==actual,'registration-invalid','Prepared registration differs from the selected authoritative publication.')
  self.tryfan=a['tryfan'];self.records=[];self.bykey={}
  for i,r in enumerate(self.s.records):
   bounds=list(self.s.geo[i].bounds) if r['representation']=='vector' else None
   self.records.append({'key':'riffelhorn:'+r['id'],'identity':r['id'],'region':'riffelhorn','feature':r['id'] if r['representation']=='vector' else None,'family':r['family'],'representation':r['representation'],'product':r['product'],'bounds':bounds,'temporal':self.s.temporal(r),'record':r})
  for f in self.tryfan['catalogue']['families']:
   temporal={role:{'status':'unknown','reason':'No supported calendar-year qualification recovered here; exact accepted native fields remain attached.'} for role in ['evidence-epoch','product-reference']}
   if f['id']=='appearance':
    value=f['nativeMetadata']['observation']['acquisition_time_utc'];temporal['evidence-epoch']={'status':'known','year':int(value[:4]),'role':'observation','nativeInstant':value,'basis':'Exact accepted appearance acquisition timestamp; query uses its calendar year only.'}
   elif f['id']=='worldcover':
    temporal['evidence-epoch']={'status':'known','year':2021,'role':'nominal-epoch','basis':'Accepted native WorldCover2021 context; not continuous physical validity.'}
   self.records.append({'key':'tryfan:'+f['product'],'identity':f['product'],'region':'tryfan','feature':None,'family':f['id'],'representation':'source-product-metadata','product':f['product'],'bounds':self.tryfan['core']['bounds'],'temporal':temporal,'record':f})
  self.exe=a.get('exe')
  if self.exe:
   from shapely.geometry import shape
   for r in self.exe['records']+(a.get('references',{}).get('records',[])):
    g=shape(r['support']['geometry']);crs=r['support']['crs'];bng=Q.project(g,crs,'EPSG:27700');epoch={'status':'unknown','reason':'Reference classification is not physical observation; native water-time roles remain separate.'}
    times=r['waterTime'];event=next((x['extent'] for x in times if x['role'] in ['observation','event'] and x['extent']['kind']=='interval'),None)
    if event and event['start'][:4]==event['end'][:4]:epoch={'status':'known','year':int(event['start'][:4]),'basis':'Native monthly/event interval calendar-year projection only; exact interval remains attached.'}
    reference={'status':'known','year':2019,'basis':'WFD classification reference2019, not observation or publication.'} if r['identity']=='exe:wfd' else {'status':'unknown','reason':'No product-reference year admitted as an observation timestamp.'}
    self.records.append({'key':'exe:'+r['identity'],'identity':r['identity'],'region':'exe','feature':r['feature'],'family':r['family'],'representation':r['representation'],'product':r['product'],'bounds':list(bng.intersection(Q.box(*self.exe['support']['bounds'])).bounds),'temporal':{'evidence-epoch':epoch,'product-reference':reference},'record':r,'geometry':bng,'evidenceClass':r['evidenceClass'],**({'scope':'exeReferences','nativeClassification':r['nativeClassification']} if 'referenceTime' in r else {})})
  self.bykey={r['key']:r for r in self.records};need(len(self.bykey)==49+(8 if self.exe else 0)+(52 if a.get('references') else 0),'registration-invalid','Unexpected retained population.')
  self.setup={**self.s.setup,'milliseconds':(time.perf_counter()-start)*1000,'records':len(self.records),'nativeMetadataBytesParsed':self.s.setup['metadataMemberBytes'],'inputHashOperations':len(self.s.input_manifest['inputs'])+len(self.s.manifest['artifacts']),'inputBytesHashed':sum(i['bytes'] for i in self.s.input_manifest['inputs'])+sum(i['bytes'] for i in self.s.manifest['artifacts'])}
 def build(self,a):
  start=time.perf_counter();p=Path(a['file']);db=sqlite3.connect(p)
  try:
   db.executescript('''PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL;
CREATE TABLE binding(schemaVersion INTEGER NOT NULL,generation TEXT NOT NULL,fingerprint TEXT NOT NULL);
CREATE TABLE record(rowid INTEGER PRIMARY KEY,key TEXT UNIQUE NOT NULL,identity TEXT NOT NULL,region TEXT NOT NULL,feature TEXT,family TEXT NOT NULL,representation TEXT NOT NULL,product TEXT NOT NULL);
CREATE INDEX identity_lookup ON record(identity); CREATE INDEX feature_lookup ON record(feature);CREATE INDEX family_lookup ON record(region,family);
CREATE TABLE temporal(key TEXT NOT NULL,role TEXT NOT NULL,known INTEGER NOT NULL,year INTEGER,PRIMARY KEY(key,role));
CREATE INDEX time_lookup ON temporal(role,known,year);
CREATE VIRTUAL TABLE bounds USING rtree(rowid,minx,maxx,miny,maxy);''')
   with db:
    db.execute('INSERT INTO binding VALUES(1,?,?)',(a['generation'],a['fingerprint']))
    for i,r in enumerate(self.records,1):
     db.execute('INSERT INTO record VALUES(?,?,?,?,?,?,?,?)',(i,r['key'],r['identity'],r['region'],r['feature'],r['family'],r['representation'],r['product']))
     for role,t in r['temporal'].items():db.execute('INSERT INTO temporal VALUES(?,?,?,?)',(r['key'],role,int(t['status']=='known'),t.get('year')))
     if r['bounds']:
      x0,y0,x1,y1=r['bounds'];db.execute('INSERT INTO bounds VALUES(?,?,?,?,?)',(i,x0,x1,y0,y1))
   need(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','catalogue-invalid','Catalogue integrity check failed.')
   need(sorted(r[0] for r in db.execute('SELECT key FROM record'))==sorted(self.bykey),'catalogue-invalid','Catalogue population incomplete.')
  finally:db.close()
  return {'milliseconds':(time.perf_counter()-start)*1000,'records':len(self.records),'bytes':p.stat().st_size,'sha256':sha(p),'schemaVersion':1}
 def verify(self,a):
  p=Path(a['file'])
  need(p.is_file(),'catalogue-missing','Catalogue missing; run catalogue build for this exact generation.')
  need(sha(p)==a['sha256'],'catalogue-integrity','Catalogue altered; rebuild from canonical files.')
  db=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True)
  try:
   rows=list(db.execute('SELECT schemaVersion,generation,fingerprint FROM binding'))
   need(rows==[(2 if a.get('qualified') else 1,a['generation'],a['fingerprint'])],'catalogue-stale','Catalogue schema/generation/closure differs; rebuild explicitly.')
   need(db.execute('PRAGMA quick_check').fetchone()[0]=='ok','catalogue-integrity','Catalogue check failed; rebuild.')
   need(sorted(r[0] for r in db.execute('SELECT key FROM record'))==sorted(self.bykey),'catalogue-integrity','Catalogue incomplete; rebuild.')
   expected=[(i,r['key'],r['identity'],r['region'],r['feature'],r['family'],r['representation'],r['product']) for i,r in enumerate(self.records,1)]
   need(list(db.execute('SELECT rowid,key,identity,region,feature,family,representation,product FROM record ORDER BY rowid'))==expected,'catalogue-integrity','Catalogue selectors differ from canonical evidence; rebuild.')
   times=sorted((r['key'],role,int(t['status']=='known'),t.get('year')) for r in self.records for role,t in r['temporal'].items())
   need(sorted(db.execute('SELECT key,role,known,year FROM temporal'))==times,'catalogue-integrity','Catalogue temporal selectors differ; rebuild.')
   boxes={row[0]:row[1:] for row in db.execute('SELECT rowid,minx,maxx,miny,maxy FROM bounds')}
   expected_boxes={i:r['bounds'] for i,r in enumerate(self.records,1) if r['bounds']}
   need(set(boxes)==set(expected_boxes),'catalogue-integrity','Catalogue spatial population differs; rebuild.')
   for i,b in expected_boxes.items():
    x0,x1,y0,y1=boxes[i];need(x0<=b[0] and x1>=b[2] and y0<=b[1] and y1>=b[3],'catalogue-integrity','Catalogue bounds could omit canonical support; rebuild.')
  finally:db.close()
  return {'records':len(self.records),'bytes':p.stat().st_size,'schemaVersion':1}
 def geometry(self,q,region):
  if 'point' not in q and 'area' not in q:return None
  if q['region']!=region:return None
  if region=='riffelhorn':return Q.parse({k:v for k,v in q.items() if k in ['point','area','crs','time']})
  crs='EPSG:4326' if q['crs']=='OGC:CRS84' else q['crs'];g=Q.Point(*q['point']) if 'point' in q else Q.rectangle(q['area'])
  g=Q.project(g,crs,'EPSG:27700');need(g.is_valid and not g.is_empty and all(math.isfinite(x) for x in g.bounds),'query-invalid','Invalid transformed spatial support.');return g
 def selected(self,q,keys):
  m={k:0 for k in ['recordsConsidered','qualificationChecks','exactSpatialChecks','spatialFalsePositiveCandidates','provenanceChecks','resourceReferencesResolved','payloadAvailabilityChecks','payloadReadCalls','decodedPayloadBytes','nativeSamplesRead','cellCentrePredicates']};out=[]
  gs={region:self.geometry(q,region) for region in ['tryfan','riffelhorn','exe']}
  for key in sorted(keys):
   r=self.bykey[key];m['recordsConsidered']+=1
   if q.get('region') and q['region']!=r['region']:continue
   if q.get('identity') and q['identity']!=r['identity']:continue
   if q.get('feature') and q['feature']!=r['feature']:continue
   if q.get('families') and r['family'] not in q['families']:continue
   if q.get('representation') and q['representation']!=r['representation']:continue
   if q.get('product') and q['product']!=r['product']:continue
   m['qualificationChecks']+=1
   if 'time' in q:
    t=q['time'];v=r['temporal'][t['role']]
    if t.get('unknown'):
     if v['status']!='unknown':continue
    elif v['status']!='known' or not t['start']<=v['year']<=t['end']:continue
   g=gs[r['region']];selection=None
   if r['region']=='riffelhorn':
    if g is not None:
     if g.is_empty:continue
     ok,selection=self.s.native_spatial(r['record'],g,m)
     if not ok:continue
    evidence=self.s.envelope(r['record'],selection,m);native=r['record']['record'];support=evidence['detail'].get('geometry',native.get('native'));rights=evidence['detail'].get('resources',native.get('rights'))
    provenance={'preparationRevision':self.s.manifest['revision'],'preparationMethod':self.s.manifest['method'],'inputs':self.s.input_manifest['inputs'],'preparedArtifacts':self.s.manifest['artifacts'],'selector':r['identity'],'rightsBoundary':self.s.qual['rightsBoundary']}
   elif r['region']=='exe':
    rec=r['record'];support=rec['support'];rights=rec['rights'];provenance=rec['provenance'];evidence=rec['evidence']
    if g is not None:
     m['exactSpatialChecks']+=1
     study=Q.box(*self.exe['support']['bounds']);bounded=g.intersection(study)
     if bounded.is_empty:continue
     geometry=r['geometry']
     if g.geom_type=='Point':
      b=self.exe['support']['bounds']
      if not(b[0]<=g.x<b[2] and b[1]<=g.y<b[3] and geometry.covers(g)):continue
     elif geometry.geom_type=='MultiPoint':
      if not any(bounded.contains(p) for p in geometry.geoms):continue
     elif geometry.intersection(bounded).area<=0:continue
   else:
    if g is not None:
     m['exactSpatialChecks']+=1;core=Q.box(*self.tryfan['core']['bounds'])
     b=self.tryfan['core']['bounds']
     if not (b[0]<=g.x<b[2] and b[1]<=g.y<b[3] if g.geom_type=='Point' else core.intersection(g).area>0):continue
    f=r['record'];cat=self.tryfan['catalogue'];evidence={'identity':r['identity'],'family':f['id'],'representation':r['representation'],'evidenceKind':'qualified source-product metadata, not physical measurement at query point','nativeMetadata':f['nativeMetadata'],'qualification':f['qualification'],'source':next(s for s in cat['sources'] if s['id']==f['source']),'product':next(p for p in cat['products'] if p['id']==f['product']),'representations':[v for v in cat['representations'] if v['id'] in f['representations']]}
    support={'registryApplicability':self.tryfan['core'],'meaning':'Registered core eligibility for metadata inspection; full native source support remains in original records, not inferred equivalent.'};rights={'nativeMetadata':f['nativeMetadata'],'source':evidence['source'],'product':evidence['product']};provenance={'catalogueSelector':f['id'],'source':f['source'],'product':f['product'],'basis':cat['basis']}
   out.append({'identity':r['identity'],'region':r['region'],**({'scope':r['scope']} if r.get('scope') else {}),'evidence':evidence,'support':support,'temporal':{**r['temporal'],'native':r['record'].get('referenceTime',r['record']['waterTime']),'retention':r['record']['provenance']['source'],'sourceRecordDates':r['record']['provenance']['resource'].get('dates',[]),'preparationTime':{'status':'unknown','reason':'Exact preparation completion clock not independently established; subset acquisition receipt remains distinct.'}} if r['region']=='exe' else r['temporal'],'provenance':provenance,'rights':rights})
  return {'results':out,'metrics':m,'gap':None if out else {'reason':'no-matching-retained-evidence','physicalAbsenceInferred':False}}
 def query(self,a,verified=False,allowed_keys=None):
  q=a['query'];valid_query(q,{r['family'] for r in self.records});start=time.perf_counter()
  if a.get('scan'):keys=list(self.bykey)
  else:
   if not verified:self.verify(a)
   db=sqlite3.connect(Path(a['file']).resolve().as_uri()+'?mode=ro',uri=True)
   try:
    clauses=[];params=[]
    if allowed_keys is not None:
     clauses.append('r.key IN ('+','.join('?' for _ in allowed_keys)+')');params.extend(allowed_keys)
    for k in ['region','identity','feature','representation','product']:
     if k in q:clauses.append('r.'+k+'=?');params.append(q[k])
    if 'families' in q:clauses.append('r.family IN ('+','.join('?' for _ in q['families'])+')');params.extend(q['families'])
    if 'time' in q:
     t=q['time'];clauses.append('EXISTS(SELECT 1 FROM temporal t WHERE t.key=r.key AND t.role=? AND t.known=?)');params.extend([t['role'],0 if t.get('unknown') else 1])
     if not t.get('unknown'):clauses.append('EXISTS(SELECT 1 FROM temporal t WHERE t.key=r.key AND t.role=? AND t.year BETWEEN ? AND ?)');params.extend([t['role'],t['start'],t['end']])
    if 'point' in q or 'area' in q:
     g=self.geometry(q,q['region'])
     if g.is_empty:keys=[]
     else:
      x0,y0,x1,y1=g.bounds;clauses.append("(r.representation='raster' OR r.rowid IN (SELECT rowid FROM bounds WHERE minx<=? AND maxx>=? AND miny<=? AND maxy>=?))");params.extend([x1,x0,y1,y0]);keys=[row[0] for row in db.execute('SELECT r.key FROM record r'+(' WHERE '+' AND '.join(clauses) if clauses else ''),params)]
    else:keys=[row[0] for row in db.execute('SELECT r.key FROM record r'+(' WHERE '+' AND '.join(clauses) if clauses else ''),params)]
   finally:db.close()
  result=self.selected(q,keys);result['metrics'].update({'candidates':len(keys),'availableRecords':len(self.records),'milliseconds':(time.perf_counter()-start)*1000,'ancestryTraversals':0,'catalogueSelectorAuditRecords':0 if a.get('scan') else len(self.records),'catalogueBytesHashed':0 if a.get('scan') else Path(a['file']).stat().st_size})
  return result

def main():
 adapter=None;qualified=None
 for line in sys.stdin:
  req=json.loads(line)
  try:
   op=req['operation'];a=req['args']
   if op=='describe-exe':result=describe_exe(a['dataRoot'])
   elif op=='describe-references':result=describe_references(a['dataRoot'])
   elif op=='describe':
    s=Q.Session(data=Path(a['dataRoot']),root=Path(a['preparedRoot']));result={'native':accepted.describe(s),'setup':{**s.setup,'inputHashOperations':len(s.input_manifest['inputs'])+len(s.manifest['artifacts']),'inputBytesHashed':sum(i['bytes'] for i in s.input_manifest['inputs'])+sum(i['bytes'] for i in s.manifest['artifacts'])}}
   elif op=='initialize':adapter=Adapter(a);result=adapter.setup
   else:
    need(adapter is not None,'worker-unavailable','Initialize the pinned adapter first.')
    if op=='qualify':qualified=Qualified(adapter,a,need);result={'records':len(adapter.records)+len(qualified.rows)}
    elif op=='build':
     result=adapter.build(a)
     if a.get('qualified'):
      need(qualified is not None,'query-invalid','Initialize qualified selectors.');result=qualified.build(a,result)
    elif op=='verify':result=qualified.verify(a) if a.get('qualified') else adapter.verify(a)
    elif op=='retrieve':
     need(qualified is not None,'query-invalid','Initialize qualified selectors.');result=qualified.query(a)
    elif op=='query':result=adapter.query(a)
    elif op=='terrain':result=terrain.sample(adapter.s,a)
    else:raise Failure('query-invalid','Unsupported worker operation.')
   print(json.dumps({'id':req['id'],'result':result},ensure_ascii=False,allow_nan=False),flush=True)
  except Failure as e:print(json.dumps({'id':req['id'],'error':{'code':e.code,'message':str(e)}}),flush=True)
  except (ValueError,KeyError,TypeError,OSError,sqlite3.Error):print(json.dumps({'id':req['id'],'error':{'code':'authoritative-invalid' if req['operation']=='initialize' else 'registration-invalid' if req['operation']=='describe' else 'processing-invalid' if req['operation']=='terrain' else 'catalogue-or-query-invalid','message':'Required retained metadata/payload, processing request or catalogue is missing, malformed or incompatible. Validate explicit identities and parameters; rebuild only disposable catalogues.'}}),flush=True)
if __name__=='__main__':
 sys.stdout.reconfigure(encoding='utf-8');main()
