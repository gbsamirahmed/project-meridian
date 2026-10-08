"""Disposable metadata comparison, not an Atlas runtime or publication authority.
Only reads accepted inputs. SQLite files and raw samples stay outside the repository.
"""
from pathlib import Path
import hashlib,json,sqlite3,statistics,time,tracemalloc,sys,os,subprocess
from shapely.geometry import shape,box
R=Path(__file__).resolve().parents[3];H=Path(__file__).parent
OUT=Path('C:/Users/gbsam/Documents/Codex/atlas-local-architecture-decision-v1')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def open_verified(path,seal,fingerprint):
 # A local sealed-view check, not a cryptographic trust service.
 assert digest(path)==seal,'index-integrity'
 db=sqlite3.connect(f'file:{path.as_posix()}?mode=ro',uri=True)
 try:
  assert db.execute('SELECT fingerprint,schemaVersion FROM binding').fetchone()==(fingerprint,1),'index-binding'
 except Exception:
  db.close();raise
 return db
def sample(fn,n=5):
 values=[];result=None
 for _ in range(n):
  t=time.perf_counter();result=fn();values.append((time.perf_counter()-t)*1000)
 return result,{'medianMs':statistics.median(values),'minMs':min(values),'maxMs':max(values),'samplesMs':values}
def body(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def load_population():
 x=read(R/'docs/research/atlas-temporal-integration-results.json');s=Path(x['store']);b=read(R/'docs/research/atlas-temporal-integration-baseline.json');prepared=R.parent/'meridian-data'/b['preparedRootRelative']
 sources={};rows={};members=[];edges=set();geoms={}
 features=read(prepared/'features.json')['features'];sources[str(prepared/'features.json')]=digest(prepared/'features.json')
 for f in features:
  geoms[f['identity']]=shape(f['native']['geometry']);rows['feature:'+f['identity']]={'id':'feature:'+f['identity'],'kind':'feature','feature':f['identity'],'physicalKnown':False,'body':f}
 for g,m in zip(x['history'],x['members']):
  for k in ['temporalKnowledge','riffelhornDerived','tryfanDerived']:
   p=s/'components'/(m[k]+'.json');assert digest(p)==m[k];sources[str(p)]=m[k];v=read(p)['value']
   if k=='temporalKnowledge':
    for r in v['records']:
     rid='temporal:'+r['revision'];rows[rid]={'id':rid,'kind':'temporal','feature':r['feature'],'physicalKnown':r['physical']['extent']['kind']!='unknown','body':r};members.append((g,rid))
   else:
    for rid,r in v['results'].items():
     key='result:'+rid;rows[key]={'id':key,'kind':'result','feature':r['id'],'physicalKnown':False,'body':r}
     for i in r['inputs']:edges.add((i['ref'],key))
    for rid in v['active'].values():members.append((g,'result:'+rid))
 return list(rows.values()),sorted(set(members)),sorted(edges),geoms,x,sources
SCHEMA='''PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL;
CREATE TABLE record(id TEXT PRIMARY KEY,kind TEXT NOT NULL,feature TEXT,physicalKnown INTEGER NOT NULL,body TEXT NOT NULL);
CREATE INDEX by_feature ON record(feature);CREATE INDEX by_kind_time ON record(kind,physicalKnown);
CREATE TABLE member(generation TEXT NOT NULL,id TEXT NOT NULL,PRIMARY KEY(generation,id));
CREATE TABLE edge(upstream TEXT NOT NULL,downstream TEXT NOT NULL,PRIMARY KEY(upstream,downstream));
CREATE TABLE geometry(rowid INTEGER PRIMARY KEY,id TEXT UNIQUE NOT NULL);
CREATE VIRTUAL TABLE bounds USING rtree(rowid,minx,maxx,miny,maxy);
CREATE TABLE binding(fingerprint TEXT NOT NULL,schemaVersion INTEGER NOT NULL);
'''
def build(path,rows,members,edges,geoms,fingerprint):
 db=sqlite3.connect(path);db.executescript(SCHEMA)
 with db:
  db.executemany('INSERT INTO record VALUES(?,?,?,?,?)',[(r['id'],r['kind'],r['feature'],int(r['physicalKnown']),body(r['body'])) for r in rows]);db.executemany('INSERT INTO member VALUES(?,?)',members);db.executemany('INSERT INTO edge VALUES(?,?)',edges)
  for n,(k,g) in enumerate(geoms.items(),1):
   a,b,c,d=g.bounds;db.execute('INSERT INTO geometry VALUES(?,?)',(n,'feature:'+k));db.execute('INSERT INTO bounds VALUES(?,?,?,?,?)',(n,a,c,b,d))
  db.execute('INSERT INTO binding VALUES(?,1)',(fingerprint,))
 assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.close()
def cases(rows,members,edges,geoms,x):
 features=sorted(geoms);point=geoms[features[0]].representative_point();narrow=point.buffer(1).envelope
 return [{'name':'feature','mode':'feature','value':features[0]},{'name':'absent','mode':'feature','value':'absent'}, {'name':'physical-known','mode':'time','value':True},{'name':'physical-unknown','mode':'time','value':False}, *[{'name':'history-'+str(i),'mode':'pin','value':g} for i,g in enumerate(x['history'])],{'name':'reverse-use','mode':'reverse','value':edges[0][0]}, {'name':'narrow','mode':'space','bounds':list(narrow.bounds)}, {'name':'broad','mode':'space','bounds':[2624000,1091000,2626000,1093000]}]
def exact_space(ids,q,geoms):
 region=box(*q['bounds']);return sorted(i for i in ids if geoms[i.removeprefix('feature:')].intersection(region).area>0)
def scan(q,rows,members,edges,geoms):
 mode=q['mode'];value=q.get('value')
 if mode=='feature':ids=[r['id'] for r in rows if r['feature']==value]
 elif mode=='time':ids=[r['id'] for r in rows if r['kind']=='temporal' and r['physicalKnown']==value]
 elif mode=='pin':ids=[i for g,i in members if g==value]
 elif mode=='reverse':ids=[d for u,d in edges if u==value]
 else:ids=exact_space(['feature:'+k for k in geoms],q,geoms)
 return sorted(ids)
def cached(q,lookup,byfeature,bypin,reverse,geoms):
 mode=q['mode'];v=q.get('value')
 if mode=='feature':return sorted(byfeature.get(v,[]))
 if mode=='pin':return sorted(bypin.get(v,[]))
 if mode=='reverse':return sorted(reverse.get(v,[]))
 if mode=='time':return sorted(r['id'] for r in lookup.values() if r['kind']=='temporal' and r['physicalKnown']==v)
 return exact_space(['feature:'+k for k in geoms],q,geoms)
def sql(q,db,geoms):
 mode=q['mode'];v=q.get('value')
 if mode=='feature':query,args='SELECT id FROM record WHERE feature=?',(v,)
 elif mode=='time':query,args='SELECT id FROM record WHERE kind=\'temporal\' AND physicalKnown=?',(int(v),)
 elif mode=='pin':query,args='SELECT id FROM member WHERE generation=?',(v,)
 elif mode=='reverse':query,args='SELECT downstream FROM edge WHERE upstream=?',(v,)
 else:
  a,b,c,d=q['bounds'];ids=[r[0] for r in db.execute('SELECT g.id FROM bounds b JOIN geometry g USING(rowid) WHERE b.minx<=? AND b.maxx>=? AND b.miny<=? AND b.maxy>=?',(c,a,d,b))];return exact_space(ids,q,geoms)
 return sorted(r[0] for r in db.execute(query,args))
def main():
 OUT.mkdir(exist_ok=True);tracemalloc.start();(rows,members,edges,geoms,x,sources),prep=sample(load_population,1)
 fingerprint=hashlib.sha256(body(sources).encode()).hexdigest();population=OUT/'population.json';population.write_text(body({'rows':rows,'members':members,'edges':edges}),encoding='utf-8')
 builds=[];dbpath=None
 for n in range(5):
  dbpath=OUT/f'comparison-{n}-{time.time_ns()}.sqlite';_,m=sample(lambda:build(dbpath,rows,members,edges,geoms,fingerprint),1);builds.append(m['medianMs'])
 byid={r['id']:r for r in rows};byfeature={};bypin={};reverse={}
 t=time.perf_counter()
 for r in rows:byfeature.setdefault(r['feature'],[]).append(r['id'])
 for g,i in members:bypin.setdefault(g,[]).append(i)
 for u,d in edges:reverse.setdefault(u,[]).append(d)
 memory_build=(time.perf_counter()-t)*1000
 db=sqlite3.connect(f'file:{dbpath.as_posix()}?mode=ro',uri=True);answers=[];comparisons=0
 for q in cases(rows,members,edges,geoms,x):
  expected=scan(q,rows,members,edges,geoms)
  def file_scan():
   p=read(population);return scan(q,p['rows'],p['members'],p['edges'],geoms)
  methods={}
  for name,fn in [('files-parse-scan',file_scan),('warm-memory',lambda:cached(q,byid,byfeature,bypin,reverse,geoms)),('warm-sqlite',lambda:sql(q,db,geoms))]:
   result,m=sample(fn);assert result==expected,(q,name);comparisons+=5;methods[name]=m
  returned=[json.loads(r[1]) for i in expected for r in db.execute('SELECT id,body FROM record WHERE id=?',(i,))];assert returned==[byid[i]['body'] for i in expected];comparisons+=1
  if q['mode']=='space':
   a,b,c,d=q['bounds'];candidate_count=db.execute('SELECT count(*) FROM bounds WHERE minx<=? AND maxx>=? AND miny<=? AND maxy>=?',(c,a,d,b)).fetchone()[0]
  else:candidate_count=len(expected)
  answers.append({'query':q,'results':len(expected),'methods':methods,'qualificationBodiesAgree':True,'structural':{'fileBytesRequestedEachRun':population.stat().st_size,'fileRecordsParsedEachRun':len(rows),'sqliteCandidateRows':candidate_count,'exactGeometryEvaluations':candidate_count if q['mode']=='space' else 0,'qualifiedBodyBytesRetrievedForComparison':sum(len(body(byid[i]['body']).encode()) for i in expected),'nativePayloadReads':0,'ancestryTraversals':0,'scope':'logical rows/candidate bodies, not physical SQLite page I/O; geometry resident after setup'}})
 def cold():
  c=open_verified(dbpath,seal,fingerprint)
  result=sql(cases(rows,members,edges,geoms,x)[0],c,geoms);c.close();return result
 seal=digest(dbpath);_,coldtiming=sample(cold)
 # Transaction isolation and rollback on this disposable derived catalogue, not publication protocol implementation.
 rw=sqlite3.connect(dbpath);rw.execute('BEGIN IMMEDIATE');rw.execute('INSERT INTO record VALUES(?,?,?,?,?)',('uncommitted','test','test',0,'{}'));assert db.execute("SELECT count(*) FROM record WHERE id='uncommitted'").fetchone()[0]==0;rw.rollback();rw.close();assert digest(dbpath)==seal
 # Binding mismatch, missing and altered index must fail before candidate reads.
 failures={};corrupt=OUT/('corrupt-'+str(time.time_ns())+'.sqlite');corrupt.write_bytes(b'not-the-sealed-index')
 for name,fn in [('missing-index',lambda:open_verified(OUT/'absent.sqlite',seal,fingerprint)),('wrong-binding',lambda:open_verified(dbpath,seal,'wrong-components')),('altered-index',lambda:open_verified(corrupt,seal,fingerprint))]:
  try:fn();failures[name]=False
  except (AssertionError,sqlite3.OperationalError,FileNotFoundError):failures[name]=True
 assert all(failures.values());peak=tracemalloc.get_traced_memory()[1];db.close()
 cold_code="import hashlib,sqlite3,sys,json;from pathlib import Path;p=Path(sys.argv[1]);assert hashlib.sha256(p.read_bytes()).hexdigest()==sys.argv[2];c=sqlite3.connect('file:'+p.as_posix()+'?mode=ro',uri=True);assert c.execute('SELECT fingerprint FROM binding').fetchone()[0]==sys.argv[3];print(c.execute('SELECT count(*) FROM record').fetchone()[0]);c.close()"
 def fresh():
  process=subprocess.run([sys.executable,'-c',cold_code,str(dbpath),seal,fingerprint],capture_output=True,text=True,check=True);assert int(process.stdout)==len(rows)
 _,fresh_timing=sample(fresh)
 result={'schema':'atlas-local-architecture-comparison/v1','planSha256':digest(H/'plan.json'),'environment':{'python':sys.version.split()[0],'sqlite':sqlite3.sqlite_version,'memory':'Python tracemalloc, includes comparison setup and JSON bodies; excludes native allocations and OS page cache'},'sourceHashes':sources,'population':{'records':len(rows),'features':len(geoms),'temporalRevisions':sum(r['kind']=='temporal' for r in rows),'resultRevisions':sum(r['kind']=='result' for r in rows),'memberships':len(members),'directInputEdges':len(edges),'generations':len(x['history'])},'preparation':prep,'sqliteBuildMs':builds,'memoryIndexBuildMs':memory_build,'footprint':{'projectedJsonBytes':population.stat().st_size,'sqliteBytes':dbpath.stat().st_size,'canonicalInputBytes':sum(Path(p).stat().st_size for p in sources),'sqlitePath':str(dbpath),'sqliteSha256':seal},'queries':answers,'agreement':True,'comparisons':comparisons,'coldReopenWithWholeIndexHash':coldtiming,'freshProcessHashOpenAndCount':fresh_timing,'failures':failures,'rollbackAndReaderIsolation':True,'tracedPeakBytes':peak,'ancestryTraversals':0,'limitations':['metadata projection only; no native payload validation/query speedup claim','file baseline is compact projected JSON not original full components','warm memory spatial path is exact full geometry scan; SQLite uses conservative bounds then exact intersection','tracemalloc changes timing; all candidates measured under same instrumentation','SQLite cold means reopen/hash with warm OS cache, not flushed disk','transaction checks are index-only; accepted publication failure tests provide canonical-root evidence','direct result-input edges, not entire accepted293/294graph; source-to-use graph selection remains canonical']}
 (R/'docs/research/atlas-local-architecture-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['population','footprint','comparisons','coldReopenWithWholeIndexHash','tracedPeakBytes']},indent=2))
def require(ok):assert ok
if __name__=='__main__':main()
