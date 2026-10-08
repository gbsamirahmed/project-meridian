"""Frozen matrix orchestration; raw samples external, compact summaries retained."""
from pathlib import Path
import json,hashlib,subprocess,time,statistics,sys,os
from supplement import run as supplement
R=Path(__file__).resolve().parents[3];PLAN=Path(__file__).with_name('plan.json');plan=json.loads(PLAN.read_text());STATE=Path(plan['stateRoot']);OUT=R/'docs/research/atlas-generation-scaling-results.json'
def encode(v):return json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+'\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):return dict(median=statistics.median(v),min=min(v),max=max(v),p95=sorted(v)[min(len(v)-1,int(.95*len(v)))])
def worker(store,variant,query,count=1,selection='current'):
 q=subprocess.run(['node','scripts/atlas/generation-scaling/worker.mjs',str(store),variant,query,str(count),selection],cwd=R,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'PYTHONIOENCODING':'utf-8'},timeout=600)
 if q.returncode:raise RuntimeError(q.stderr)
 return json.loads(q.stdout)
def main():
 began=time.perf_counter();fixtures=json.loads((STATE/'fixtures.json').read_text());rawdir=STATE/'measurements';rawdir.mkdir(exist_ok=True);rows=[]
 for case in plan['cases']:
  file=rawdir/(case['id']+'.json');fixture=next(f for f in fixtures['cases'] if f['depth']==case['depth'])
  if file.exists():raw=json.loads(file.read_text());assert raw['planSha256']==sha(PLAN)
  else:
   fresh=[worker(fixture['store'],case['variant'],case['query']) for _ in range(plan['freshProcesses'])];warm=worker(fixture['store'],case['variant'],case['query'],plan['warmRequests']);raw={'planSha256':sha(PLAN),'case':case,'fresh':fresh,'warm':warm};file.write_text(encode(raw),encoding='utf-8',newline='\n')
  warm=raw['warm']['samples'];fresh=raw['fresh'];assert len(warm)==20 and len(fresh)==5
  hashes={s['qualifiedSha256'] for s in warm+[f['samples'][0] for f in fresh]};assert len(hashes)==1
  def structural(s):return {'counters':s['counters'],'reads':s['reads'],'responseBytes':s['responseBytes']}
  assert all(structural(s)==structural(warm[0]) for s in warm)
  rows.append({**case,'generation':fixture['current'],'qualifiedSha256':next(iter(hashes)),'structural':structural(warm[0]),'warmMilliseconds':stats([s['milliseconds'] for s in warm]),'freshFirstQueryMilliseconds':stats([f['samples'][0]['milliseconds'] for f in fresh]),'freshStartupMilliseconds':stats([f['startupMilliseconds'] for f in fresh]),'pin':raw['warm']['pin'],'nodeRSSAfterRange':[min(s['nodeRSSAfter'] for s in warm),max(s['nodeRSSAfter'] for s in warm)],'raw':{'path':str(file),'sha256':sha(file),'bytes':file.stat().st_size}})
  print(case['id'],round(rows[-1]['warmMilliseconds']['median'],2),'ms',flush=True)
 # One explicit historical lookup per depth/variant: canonical served state remains historical.
 historical=[]
 for f in fixtures['cases']:
  for variant in plan['variants']:
   file=rawdir/f"historical-{f['depth']}-{variant}.json"
   if not file.exists():file.write_text(encode(worker(f['store'],variant,'Q05',1,fixtures['acceptedGeneration'])),encoding='utf-8',newline='\n')
   result=json.loads(file.read_text());historical.append({'depth':f['depth'],'variant':variant,'selected':result['generation'],'current':result['current'],'pin':result['pin'],'query':result['samples'][0],'startupMilliseconds':result['startupMilliseconds'],'rawSha256':sha(file)})
   print('historical',f['depth'],variant,round(result['startupMilliseconds'],1),flush=True)
 controls=supplement(plan)
 result={'schema':'atlas-generation-scaling-results/v1','startingCommit':plan['startingCommit'],'planSha256':sha(PLAN),'fixtureSha256':sha(STATE/'fixtures.json'),'fixtures':[{k:v for k,v in f.items() if k not in ['publication','history']}|{'retainedGenerations':len(f['history']),'publication':{'observations':len(f['publication']),'assemblyTotalMilliseconds':stats([x['totalMilliseconds'] for x in f['publication']]) if f['publication'] else None,'validationMilliseconds':stats([x['validationMilliseconds'] for x in f['publication']]) if f['publication'] else None,'switchMilliseconds':stats([x['publicationMilliseconds'] for x in f['publication']]) if f['publication'] else None,'first':f['publication'][0] if f['publication'] else None,'last':f['publication'][-1] if f['publication'] else None}} for f in fixtures['cases']],'rows':rows,'historical':historical,'referenceControls':controls,'runtime':{'node':subprocess.check_output(['node','--version'],text=True).strip(),'platform':sys.platform,'cache':'Fresh processes / warmed OS file cache; no physical cache eviction','timingBoundary':'S4 delivery library operation, not HTTP/network; startup includes Python native initialization','memoryBoundary':'Observed Node RSS, not peak or total process tree'},'elapsedRunMilliseconds':(time.perf_counter()-began)*1000,'decision':'UNJUDGED','limitations':plan['limitations']}
 # Comparison-only correction: generation addresses can also appear in provenanceRefs.
 # Retain original timing receipts byte-for-byte; recheck each case using the narrower
 # equality-to-that-request's-generation replacement, without modifying timed loaders.
 equivalence=[]
 for row in rows:
  file=rawdir/(row['id']+'-equivalence-v2.json')
  if not file.exists():file.write_text(encode(worker(next(f['store'] for f in fixtures['cases'] if f['depth']==row['depth']),row['variant'],row['query'])),encoding='utf-8',newline='\n')
  proof=json.loads(file.read_text());assert proof['comparisonVersion']==2
  row['originalComparisonSha256']=row['qualifiedSha256'];row['qualifiedSha256']=proof['samples'][0]['qualifiedSha256'];equivalence.append({'case':row['id'],'sha256':sha(file),'path':str(file),'qualifiedSha256':row['qualifiedSha256']})
 for query in plan['queries']:assert len({r['qualifiedSha256'] for r in rows if r['query']==query})==1
 result['equivalence']=equivalence
 result['measurementCodeHashes']={p.name:sha(p) for p in Path(__file__).parent.glob('*') if p.is_file() and p.name not in ['validate.py','README.md']}
 result['elapsedRunQualification']='Elapsed orchestration invocation; resumed raw receipts are not retimed. See raw fresh/startup/request measurements for campaign costs.'
 OUT.write_text(encode(result),encoding='utf-8',newline='\n');print('wrote',OUT,flush=True)
def check():
 v=json.loads(OUT.read_text());assert v['planSha256']==sha(PLAN)
 assert v['fixtureSha256']==sha(STATE/'fixtures.json')
 for row in v['rows']:
  assert sha(Path(row['raw']['path']))==row['raw']['sha256'];raw=json.loads(Path(row['raw']['path']).read_text())
  assert len(raw['fresh'])==5 and len(raw['warm']['samples'])==20
  assert all(s['counters']==row['structural']['counters'] and s['reads']==row['structural']['reads'] for s in raw['warm']['samples'])
 for e in v['equivalence']:assert sha(Path(e['path']))==e['sha256']
 for query in plan['queries']:assert len({r['qualifiedSha256'] for r in v['rows'] if r['query']==query})==1
 b=json.loads((R/'docs/research/atlas-generation-scaling-baseline.json').read_text());store=R.parent/'meridian-data/experiments/atlas/tryfan-regional-pilot-v1'
 assert all(sha(store/p)==h for p,h in b['acceptedStoreHashes'].items())
 print(encode({'cases':len(v['rows']),'freshObservations':90,'warmObservations':360,'qualifiedParity':True,'acceptedStoreUnchanged':True}))
if __name__=='__main__':check() if '--check' in sys.argv else main()
