"""Schema2 selectors extend the existing native catalogue and exact predicate adapter."""
from pathlib import Path
import datetime,hashlib,json,sqlite3,time
class Qualified:
 def __init__(self,owner,view,need):
  self.o=owner;self.v=view;self.need=need;self.rows={r['key']:r for r in view['selectors']};self.edges=view['relationships'];self.native={r['key']:r for r in owner.records};self.allkeys=set(self.rows)|set(self.native)
  need(len(self.rows)==len(view['selectors']) and all(e['from'] in self.allkeys and e['to'] in self.allkeys for e in self.edges),'relationship-invalid','Exact dependency reference missing.')
  self.families={r['family'] for r in owner.records}|{'terrain-slope','planar-area-ratio'}
 def build(self,a,result):
  db=sqlite3.connect(a['file'])
  try:
   with db:
    db.executescript('CREATE TABLE derived(key TEXT PRIMARY KEY,identity TEXT NOT NULL,revision TEXT NOT NULL,region TEXT NOT NULL,family TEXT NOT NULL,representation TEXT NOT NULL,product TEXT NOT NULL); CREATE INDEX derived_identity ON derived(identity,revision); CREATE INDEX derived_family ON derived(region,family); CREATE TABLE knowledge(region TEXT PRIMARY KEY,revision TEXT,acceptedAt TEXT,nativeRevision TEXT NOT NULL); CREATE TABLE relationship(identity TEXT PRIMARY KEY,source TEXT NOT NULL,target TEXT NOT NULL,kind TEXT NOT NULL); CREATE INDEX downstream ON relationship(source); CREATE INDEX upstream ON relationship(target); CREATE VIRTUAL TABLE derived_bounds USING rtree(rowid,minx,maxx,miny,maxy); CREATE VIRTUAL TABLE consumed_bounds USING rtree(rowid,minx,maxx,miny,maxy);')
    db.execute('UPDATE binding SET schemaVersion=2')
    for i,r in enumerate(self.rows.values(),1):
     db.execute('INSERT INTO derived(rowid,key,identity,revision,region,family,representation,product) VALUES(?,?,?,?,?,?,?,?)',(i,*[r[k] for k in ['key','identity','revision','region','family','representation','product']]))
     x,y=r['point'];db.execute('INSERT INTO derived_bounds VALUES(?,?,?,?,?)',(i,x,x,y,y));xs=[c[0] for c in r['cells']];ys=[c[1] for c in r['cells']];db.execute('INSERT INTO consumed_bounds VALUES(?,?,?,?,?)',(i,min(xs)-.25,max(xs)+.25,min(ys)-.25,max(ys)+.25))
    for region,rev in self.v['nativeRevisions'].items():
     k=self.v['knowledge'][region];db.execute('INSERT INTO knowledge VALUES(?,?,?,?)',(region,k['revision'] if k else None,k['acceptedAt'] if k else None,rev))
    db.executemany('INSERT INTO relationship VALUES(?,?,?,?)',[(e['identity'],e['from'],e['to'],e['kind']) for e in self.edges])
  finally:db.close()
  return {**result,'records':len(self.native)+len(self.rows),'nativeRecords':len(self.native),'derivedRecords':len(self.rows)+sum(r.get('evidenceClass')=='derived' for r in self.native.values()),'relationships':len(self.edges),'schemaVersion':2,'bytes':Path(a['file']).stat().st_size,'sha256':hashlib.sha256(Path(a['file']).read_bytes()).hexdigest()}
 def verify(self,a):
  result=self.o.verify(a);db=sqlite3.connect(Path(a['file']).resolve().as_uri()+'?mode=ro',uri=True)
  try:
   expected=[(i,*[r[k] for k in ['key','identity','revision','region','family','representation','product']]) for i,r in enumerate(self.rows.values(),1)]
   self.need(list(db.execute('SELECT rowid,key,identity,revision,region,family,representation,product FROM derived ORDER BY rowid'))==expected,'catalogue-integrity','Derived selectors differ from canonical metadata; rebuild.')
   wanted=sorted((region,k['revision'] if k else None,k['acceptedAt'] if k else None,self.v['nativeRevisions'][region]) for region,k in self.v['knowledge'].items())
   self.need(sorted(db.execute('SELECT * FROM knowledge'))==wanted and sorted(db.execute('SELECT * FROM relationship'))==sorted((e['identity'],e['from'],e['to'],e['kind']) for e in self.edges),'catalogue-integrity','Knowledge/dependency selectors differ; rebuild.')
   for table in ['derived_bounds','consumed_bounds']:
    actual={r[0]:r[1:] for r in db.execute('SELECT * FROM '+table)};self.need(len(actual)==len(self.rows),'catalogue-integrity','Derived spatial selector missing.')
    for i,r in enumerate(self.rows.values(),1):
     b=[r['point'][0],r['point'][1],r['point'][0],r['point'][1]] if table=='derived_bounds' else [min(c[0] for c in r['cells'])-.25,min(c[1] for c in r['cells'])-.25,max(c[0] for c in r['cells'])+.25,max(c[1] for c in r['cells'])+.25]
     x0,x1,y0,y1=actual[i];self.need(x0<=b[0] and x1>=b[2] and y0<=b[1] and y1>=b[3],'catalogue-integrity','Derived bounds could omit exact support.')
  finally:db.close()
  return {**result,'records':len(self.native)+len(self.rows),'derivedRecords':len(self.rows)+sum(r.get('evidenceClass')=='derived' for r in self.native.values()),'relationships':len(self.edges),'schemaVersion':2}
 def validate(self,q):
  self.need(isinstance(q,dict),'query-invalid','Query must be a structured object.')
  base={k:v for k,v in q.items() if k in ['region','identity','feature','product','point','area','crs','time']};self.o.validate(base)
  self.need(isinstance(q,dict) and not set(q)-set(base)-{'families','representation','evidenceClass','revision','spatialSupport','knowledge','relatedTo','waterTime'},'query-invalid','Unsupported qualified predicates.')
  self.need(q.get('evidenceClass') in [None,'source','derived'] and q.get('representation') in [None,'vector','raster','source-product-metadata','local-scalar','native-cell-summary'],'query-invalid','Unsupported evidence class/representation.')
  if 'families' in q:self.need(isinstance(q['families'],list) and bool(q['families']) and all(isinstance(f,str) and f in self.families for f in q['families']),'query-invalid','Unsupported family.')
  if 'revision' in q:self.need(isinstance(q['revision'],str) and len(q['revision'])==64 and all(c in '0123456789abcdef' for c in q['revision']),'query-invalid','Revision must be an exact SHA256.')
  self.need(q.get('spatialSupport') in [None,'location','consumed'] and ('spatialSupport' not in q or ('point' in q or 'area' in q)) and (q.get('spatialSupport')!='consumed' or q.get('evidenceClass')=='derived'),'query-invalid','Consumed support requires a derived spatial query; scalar location is not a patch.')
  if 'waterTime' in q:
   t=q['waterTime'];self.need(isinstance(t,dict) and t.get('role') in ['observation','event','reference'],'query-invalid','Use native observation/event/reference role.')
   if t.get('unknown') is True:self.need(set(t)=={'role','unknown'},'query-invalid','Unknown is not unrestricted time.')
   else:
    self.need(set(t)=={'role','start','end'},'query-invalid','Closed native interval required.')
    for v in [t['start'],t['end']]:
     try:valid=isinstance(v,str) and (len(v)==4 and v.isdigit() and 1<=int(v)<=9999 if t['role']=='reference' else datetime.date.fromisoformat(v).isoformat()==v)
     except (ValueError,TypeError):valid=False
     self.need(valid,'query-invalid','Use native year precision for reference, ISO day for observation/event; no exposure precision inference.')
    self.need(t['start']<=t['end'],'query-invalid','Interval ordering invalid.')
  if 'knowledge' in q:
   k=q['knowledge'];self.need(isinstance(k,dict),'query-invalid','Invalid knowledge qualification.')
   if set(k)=={'unknown'}:self.need(k['unknown'] is True,'query-invalid','Unknown must be explicit.')
   elif set(k)=={'revision'}:self.need(isinstance(k['revision'],str) and len(k['revision'])==64 and all(c in '0123456789abcdef' for c in k['revision']),'query-invalid','Exact active registration revision required.')
   else:
    self.need(set(k)=={'start','end'},'query-invalid','Closed knowledge UTC interval required; open/ambiguous intervals unsupported.')
    for v in k.values():
     self.need(isinstance(v,str),'query-invalid','Invalid knowledge timestamp.')
     try:d=datetime.datetime.strptime(v,'%Y-%m-%dT%H:%M:%S.%fZ');valid=d.isoformat(timespec='milliseconds')+'Z'==v
     except ValueError:valid=False
     self.need(valid,'query-invalid','Use exact UTC millisecond knowledge timestamps, not physical dates.')
    self.need(k['start']<=k['end'],'query-invalid','Knowledge interval unordered.')
  if 'relatedTo' in q:
   t=q['relatedTo'];self.need(isinstance(t,dict) and set(t)=={'identity','direction','depth'} and t['direction'] in ['inputs','dependents'] and t['depth'] in ['direct','transitive'],'query-invalid','Invalid relationship traversal.')
   self.need(any(r['identity']==t['identity'] for r in list(self.native.values())+list(self.rows.values())),'relationship-missing','Selected relationship identity is absent from this pin.')
 def allowed(self,q,r,cls):
  if q.get('evidenceClass') and q['evidenceClass']!=cls:return False
  for k in ['region','identity','representation','product']:
   if k in q and q[k]!=r[k]:return False
  if 'families' in q and r['family'] not in q['families']:return False
  revision=r['revision'] if cls=='derived' and r['region']!='exe' else self.v['nativeRevisions'][r['region']]
  if 'revision' in q and q['revision']!=revision:return False
  if 'feature' in q and (cls=='derived' or r['feature']!=q['feature']):return False
  if 'waterTime' in q:
   if r['region']!='exe':return False
   t=q['waterTime'];wanted='nominal-epoch' if t['role']=='reference' else t['role'];times=[x['extent'] for x in r['record']['waterTime'] if x['role']==wanted]
   if t.get('unknown'):
    if times and not all(x['kind']=='unknown' for x in times):return False
   elif not any((t['start']<=x['end'] and t['end']>=x['start']) if x['kind']=='interval' else (t['start']<=x['value']<=t['end'] if x['kind']=='epoch' else False) for x in times):return False
  if 'knowledge' in q:
   k=q['knowledge'];v=self.v['knowledge'][r['region']]
   if k.get('unknown'):return v is None
   if v is None:return False
   if 'revision' in k:return v['revision']==k['revision']
   return k['start']<=v['acceptedAt']<=k['end']
  return True
 def traversal(self,q,db):
  if 'relatedTo' not in q:return None,[]
  t=q['relatedTo'];seeds=[k for k,r in {**self.native,**self.rows}.items() if r['identity']==t['identity']];forward=t['direction']=='dependents';a,b=('source','target') if forward else ('target','source')
  if db:
   marks=','.join('?' for _ in seeds)
   if t['depth']=='direct':wanted={r[0] for r in db.execute(f'SELECT {b} FROM relationship WHERE {a} IN ({marks})',seeds)}
   else:wanted={r[0] for r in db.execute(f'WITH RECURSIVE reach(key) AS (SELECT {b} FROM relationship WHERE {a} IN ({marks}) UNION SELECT e.{b} FROM relationship e JOIN reach r ON e.{a}=r.key) SELECT key FROM reach',seeds)}
  else:
   wanted=set();front=set(seeds)
   while front:
    nxt={e['to' if forward else 'from'] for e in self.edges if e['from' if forward else 'to'] in front}-wanted;wanted|=nxt
    if t['depth']=='direct':break
    front=nxt
  wanted-=set(seeds);traversed=[e['identity'] for e in self.edges if e['from' if forward else 'to'] in set(seeds)|wanted and e['to' if forward else 'from'] in wanted]
  return wanted,traversed
 def query(self,a):
  q=a['query'];self.validate(q);start=time.perf_counter();scan=a.get('scan',False);db=None
  if not scan:self.verify(a);db=sqlite3.connect(Path(a['file']).resolve().as_uri()+'?mode=ro',uri=True)
  try:
   reachable,traversed=self.traversal(q,db);nativekeys=[k for k,r in self.native.items() if self.allowed(q,r,r.get('evidenceClass','source')) and (reachable is None or k in reachable)]
   nq={k:v for k,v in q.items() if k in ['region','identity','feature','product','point','area','crs','time']}
   if 'families' in q:nq['families']=[f for f in q['families'] if f in {r['family'] for r in self.native.values()}]
   if q.get('representation') and q['representation']!='local-scalar':nq['representation']=q['representation']
   # Canonical extra qualifiers select native keys; native SQL and exact predicates remain shared.
   native=self.o.query({**a,'query':nq},verified=True,allowed_keys=None if scan else nativekeys) if nativekeys else {'results':[],'metrics':{'candidates':0,'recordsConsidered':0,'exactSpatialChecks':0}}
   out=[]
   for r in native['results']:
    key=r['region']+':'+r['identity']
    if key in nativekeys:out.append({**r,'key':key,'revision':self.v['nativeRevisions'][r['region']],'evidenceClass':self.native[key].get('evidenceClass','source'),'family':self.native[key]['family'],'representation':self.native[key]['representation']})
   candidates=list(self.rows)
   if db:
    clauses=['0'] if q.get('evidenceClass')=='source' or 'feature' in q else [];args=[]
    for k in ['region','identity','revision','representation','product']:
     if k in q:clauses.append('d.'+k+'=?');args.append(q[k])
    if reachable is not None:
     clauses.append('d.key IN ('+','.join('?' for _ in reachable)+')' if reachable else '0');args+=list(reachable)
    if 'families' in q:clauses.append('d.family IN ('+','.join('?' for _ in q['families'])+')');args+=q['families']
    if 'point' in q or 'area' in q:
     g=self.o.geometry(q,'riffelhorn')
     if g is not None and not g.is_empty:
      x0,y0,x1,y1=g.bounds;table='consumed_bounds' if q.get('spatialSupport')=='consumed' else 'derived_bounds';clauses.append(f'd.rowid IN(SELECT rowid FROM {table} WHERE minx<=? AND maxx>=? AND miny<=? AND maxy>=?)');args += [x1,x0,y1,y0]
     else:clauses.append('0')
    candidates=[r[0] for r in db.execute('SELECT d.key FROM derived d'+(' WHERE '+' AND '.join(clauses) if clauses else ''),args)]
   considered=0;exact=0
   for key in candidates:
    r=self.rows[key];considered+=1
    if not self.allowed(q,r,'derived') or (reachable is not None and key not in reachable):continue
    if 'time' in q and not q['time'].get('unknown'):continue
    if 'point' in q or 'area' in q:
     g=self.o.geometry(q,'riffelhorn');exact+=1
     if g is None or g.is_empty:continue
     if q.get('spatialSupport')=='consumed':
      from shapely.geometry import box
      if not any((x-.25<=g.x<x+.25 and y-.25<=g.y<y+.25) if g.geom_type=='Point' else box(x-.25,y-.25,x+.25,y+.25).intersection(g).area>0 for x,y in r['cells']):continue
     else:
      from shapely.geometry import Point
      x,y=r['point']
      if not (g.x==x and g.y==y if g.geom_type=='Point' else g.contains(Point(x,y)) or (g.covers(Point(x,y)) and x<g.bounds[2] and y<g.bounds[3])):continue
    out.append({**r,'evidenceClass':'derived','temporal':{'evidence-epoch':{'status':'unknown','reason':'Exact native stencil observation epoch is unknown.'},'product-reference':{'status':'unknown','reason':'No source product-reference calendar year is declared for this derived quantity; method identity and execution time remain separate.'}}})
   out.sort(key=lambda r:r['key']);return {'results':out,'traversed':traversed,'metrics':{**native['metrics'],'nativeSelectorPredicates':len(self.native),'derivedCandidates':len(candidates),'derivedPredicates':considered,'derivedSpatialPredicates':exact,'availableRecords':len(self.native)+len(self.rows),'relationshipRowsAudited':len(self.edges),'relationshipResults':len(traversed),'milliseconds':(time.perf_counter()-start)*1000,'catalogueBytesHashed':0 if scan else Path(a['file']).stat().st_size}}
  finally:
   if db:db.close()
