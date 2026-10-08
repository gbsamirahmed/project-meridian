"""Assessment instrumentation around the unchanged full oracle; no receipt path."""
import importlib.util,time,json
from pathlib import Path
HERE=Path(__file__).parent;R=HERE.resolve().parents[2]
spec=importlib.util.spec_from_file_location('integrity_original',R/'scripts/atlas/validation-maintenance/model.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);B=M.B
active=None

def wrap(name,fn):
 def measured(*a,**kw):
  if active is None:return fn(*a,**kw)
  start=time.perf_counter();frame=[0];active['stack'].append(frame);result=None
  try:result=fn(*a,**kw);return result
  finally:
   ms=(time.perf_counter()-start)*1000;active['stack'].pop()
   if active['stack']:active['stack'][-1][0]+=ms
   v=active['ops'].setdefault(name,dict(calls=0,inclusiveMs=0,exclusiveMs=0,bytes=0));v['calls']+=1;v['inclusiveMs']+=ms;v['exclusiveMs']+=ms-frame[0]
   if name in ('sha','parse'):v['bytes']+=len(a[0]) if isinstance(a[0],(bytes,str)) else 0
   if name=='read' and result is not None:v['bytes']+=len(result)
 return measured

installed=False
def install():
 global installed
 if installed:return
 installed=True
 original_sha=B.sha;original_encode=B.encode
 for obj in [M,B,B.G]:obj.sha=wrap('sha',original_sha);obj.encode=wrap('encode',original_encode)
 json.loads=wrap('parse',json.loads);Path.read_bytes=wrap('read',Path.read_bytes)
 for obj,name in [(B,'local'),(M,'local'),(B,'cross'),(B,'publication_checks'),(M,'full')]:setattr(obj,name,wrap(('base-' if obj is B else '')+name,getattr(obj,name)))
 B.Store.raw_component=wrap('componentIntegrity',B.Store.raw_component)

def measure(s,p):
 global active
 s.reset();active={'ops':{},'stack':[]};start=time.perf_counter()
 try:
  certs,_=M.full(s,p,M.profile());return dict(milliseconds=(time.perf_counter()-start)*1000,ops=active['ops'],counter=dict(s.c),accepted=True,components=len(certs))
 finally:active=None
