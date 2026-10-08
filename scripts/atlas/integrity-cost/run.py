"""Frozen assessment orchestration; raw state is external and never replaces accepted pilot."""
from pathlib import Path
import json,hashlib,subprocess,time,statistics,os,sys
R=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent;plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'));STATE=Path(plan['stateRoot']);DATA=R.parent/'meridian-data';OUT=R/'docs/research/atlas-integrity-cost-results.json'
def encode(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):return dict(median=statistics.median(v),min=min(v),max=max(v))
def call(args,env=None):
 t=time.perf_counter();p=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8',**(env or {})},timeout=240)
 if p.returncode:raise RuntimeError(p.stderr+'\n'+p.stdout[-1000:])
 return json.loads(p.stdout),(time.perf_counter()-t)*1000

def check():
 x=json.loads(OUT.read_text(encoding='utf-8'));assert x['planSha256']==sha(HERE/'plan.json');assert all(sha(R/p)==h for p,h in plan['authoritativeHashes'].items());assert all(sha(HERE/p)==h for p,h in x['codeHashes'].items());assert all(sha(Path(p['path']))==p['sha256'] for p in x['rawFiles']);assert x['correctness']['plainMeterAgree'];print(encode({'cases':len(x['node']),'rawFiles':len(x['rawFiles']),'authoritativeSourcesUnchanged':True}));return x

def main():
 assert all(sha(R/p)==h for p,h in plan['authoritativeHashes'].items());campaign=STATE/'campaign';assert not campaign.exists(),'Do not overwrite measured state';campaign.mkdir(parents=True);raw=[];node=[]
 def save(name,x):
  p=campaign/(name+'.json');p.write_text(encode(x),encoding='utf-8',newline='\n');raw.append(dict(path=str(p),sha256=sha(p)));return p
 fixtures=[]
 for c in plan['payloadCases']:
  p=DATA/c['manifest'];assert sha(p)==c['manifestSha256'];v=json.loads(p.read_text());items=[a for a in v['files'] if a['path'].split('/')[0] in c['groups']];f=dict(root=str(p.parent),items=items,kind='real-retained',manifest=c['manifest'],manifestSha256=sha(p));path=save('payload-'+c['id'],f);fixtures.append((c['id'],str(path),f))
 for c in plan['syntheticPayloadCases']:
  root=campaign/c['id'];root.mkdir();items=[];start=time.perf_counter()
  for i in range(c['count']):
   size=c['bytes']//c['count'];b=i.to_bytes(4,'little')+bytes(size-4);p=root/(str(i)+'.bin');p.write_bytes(b);items.append(dict(path=p.name,bytes=size,sha256=sha(p)))
  f=dict(root=str(root),items=items,kind='labelled-synthetic-bytes',setupMs=(time.perf_counter()-start)*1000);path=save('payload-'+c['id'],f);fixtures.append((c['id'],str(path),f))
 cases=[(n,n,None,None) for n in ['pilot-artifacts','pilot-structure','pilot-delivery','pilot-load','pilot-register']]+[(i,'payload',arg,f) for i,arg,f in fixtures]+[(f"history-{c['depth']}-{c['selection']}",'history',json.dumps(c),None) for c in plan['historyCases']]
 agree=True
 for index,(id,action,arg,fixture) in enumerate(cases):
  obs={}
  for mode in (['plain','meter'] if index%2==0 else ['meter','plain']):
   v,startup=call(['node',str(HERE/'worker.mjs'),action,mode,*([arg] if arg else [])]);save(id+'-'+mode,v);obs[mode]=v;obs[mode]['processMs']=startup
  values=lambda m:[v['value'] for v in obs[m]['samples']];assert values('plain')==values('meter'),id
  node.append(dict(id=id,action=action,fixture={k:v for k,v in (fixture or {}).items() if k!='items'},artifacts=len(fixture['items']) if fixture else None,payloadBytes=sum(a['bytes'] for a in fixture['items']) if fixture else None,plainMs=stats([v['milliseconds'] for v in obs['plain']['samples']]),meterMs=stats([v['milliseconds'] for v in obs['meter']['samples']]),observations=obs));print(id,round(node[-1]['plainMs']['median'],2),'ms',flush=True)
 metadata={}
 for mode in ['plain','meter']:
  v,_=call([sys.executable,str(HERE/'metadata-worker.py'),mode]);save('metadata-'+mode,v);metadata[mode]=v
 for a,b in zip(metadata['plain']['rows'],metadata['meter']['rows']):
  assert a['case']==b['case']
  av=a['samples'] if a['kind']=='population' else [r['validation'] for rep in a['repeats'] for r in rep['rows']];bv=b['samples'] if b['kind']=='population' else [r['validation'] for rep in b['repeats'] for r in rep['rows']]
  assert all(x['counter']==y['counter'] and x['accepted']==y['accepted'] for x,y in zip(av,bv))
 failures,_=call(['node',str(HERE/'failures.mjs')]);save('failures',failures)
 fresh=[]
 for _ in range(plan['repetitions']):
  v,startup=call(['node',str(HERE/'worker.mjs'),'pilot-load','plain'],{'COST_REPS':'1'});fresh.append(dict(totalProcessMs=startup,sample=v['samples'][0]));assert v['samples'][0]['value']==node[3]['observations']['plain']['samples'][0]['value']
 save('fresh-pilot-load',fresh)
 result=dict(schema='atlas-integrity-cost-results/v1',planSha256=sha(HERE/'plan.json'),codeHashes={p.name:sha(p) for p in HERE.glob('*') if p.suffix in ['.mjs','.py'] and p.name not in ['validate.py','report.py','test_measurement.py']},node=node,metadata=metadata,failures=failures,fresh=fresh,rawFiles=raw,correctness=dict(plainMeterAgree=True,nodeSamples=len(node)*10,metadataValidations=200,failureControls=len(failures)+len(metadata['plain']['failures'])),runtime=dict(node=subprocess.check_output(['node','--version'],text=True).strip(),python=sys.version,OSCache='uncontrolled; fresh process is not cold disk',memory='Observed RSS only, not peak/native aggregate; no memory optimization'),decision='UNJUDGED')
 OUT.write_text(encode(result),encoding='utf-8',newline='\n');print('Measured; judgement remains separate.',flush=True)
if __name__=='__main__':check() if '--check' in sys.argv else main()
