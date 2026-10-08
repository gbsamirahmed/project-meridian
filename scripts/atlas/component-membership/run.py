"""Prospectively frozen matrix; raw measurements remain in isolated proof state."""
from pathlib import Path
import json,subprocess,hashlib,time,statistics,sys,os
R=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'));STATE=Path(plan['stateRoot']);OUT=R/'docs/research/atlas-component-membership-results.json'

def encode(v):return json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+'\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(a):return dict(median=statistics.median(a),min=min(a),max=max(a))
def call(store,selection,mode,n):
 p=subprocess.run(['node',str(HERE/'worker.mjs'),store,selection,mode,str(n)],cwd=R,capture_output=True,text=True,encoding='utf-8',timeout=120)
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout)
def main():
 fixtures=json.loads((STATE/'fixtures.json').read_text(encoding='utf-8'));rawdir=STATE/'measurements';rawdir.mkdir(exist_ok=True);rows=[]
 cases=[dict(id=c['id']+'-'+m,depth=c['generations'],selection=c['selection'],mode=m,fresh=5,warm=20) for c in plan['cases'] for m in plan['modes']]
 cases +=[dict(id=f"G{c['depth']}-{c['query']}",depth=c['depth'],selection='current',mode=c['query'],fresh=3,warm=10) for c in plan['servingCases']]
 previous=json.loads((R/'docs/research/atlas-generation-scaling-results.json').read_text(encoding='utf-8'))
 for c in cases:
  fixture=next(f for f in fixtures['records'] if f['depth']==c['depth']);selection=fixture[c['selection']];file=rawdir/(c['id']+'.json')
  if file.exists():raw=json.loads(file.read_text(encoding='utf-8'));assert raw['planSha256']==sha(HERE/'plan.json')
  else:
   raw={'planSha256':sha(HERE/'plan.json'),'case':c,'fresh':[call(fixture['store'],selection,c['mode'],1) for _ in range(c['fresh'])],'warm':call(fixture['store'],selection,c['mode'],c['warm'])};file.write_text(encode(raw),encoding='utf-8',newline='\n')
  warm=raw['warm']['samples'];sample=warm[0];assert all(s['reads']==sample['reads'] and s['counters']==sample['counters'] and s['answerSha256']==sample['answerSha256'] for s in warm)
  assert all(s['counters']['ancestryTraversals']==0 for s in warm)
  assert sample['reads']['membership']['calls']==33
  if c['mode'].startswith('Q'):
   expected=next(x['qualifiedSha256'] for x in previous['rows'] if x['query']==c['mode']);assert sample['qualifiedSha256']==expected
  row={**c,'generation':selection,'counters':sample['counters'],'reads':sample['reads'],'answerSha256':sample['answerSha256'],'qualifiedSha256':sample['qualifiedSha256'],'responseBytes':sample['responseBytes'],'warmMilliseconds':stats([s['milliseconds'] for s in warm]),'freshQueryMilliseconds':stats([f['samples'][0]['milliseconds'] for f in raw['fresh']]),'freshStartupMilliseconds':stats([f['startupMilliseconds'] for f in raw['fresh']]),'warmRSSAfter':stats([s['RSSAfter'] for s in warm]),'raw':{'path':str(file),'sha256':sha(file)}};rows.append(row)
  print(c['id'],round(row['warmMilliseconds']['median'],3),row['reads'].get('components',{}),flush=True)
 result={'schema':'atlas-component-membership-results/v1','planSha256':sha(HERE/'plan.json'),'fixtureSha256':sha(STATE/'fixtures.json'),'fixtures':fixtures['records'],'rows':rows,'decision':'UNJUDGED','runtime':{'node':subprocess.check_output(['node','--version'],text=True).strip(),'platform':sys.platform,'timing':'Library boundaries, not HTTP/network. Fresh process, warm OS cache; no physical cold-disk claim.','memory':'Observed Node RSS, not peak/live heap or total Python tree'},'baselineComparison':{'commit':'e88b575','sourceResultsSha256':sha(R/'docs/research/atlas-generation-scaling-results.json'),'historical112':next(x for x in previous['historical'] if x['depth']==112 and x['variant']=='request-reuse')},'codeHashes':{p.name:sha(p) for p in HERE.glob('*') if p.is_file() and p.name not in ['validate.py','README.md']}}
 OUT.write_text(encode(result),encoding='utf-8',newline='\n')
def check():
 v=json.loads(OUT.read_text(encoding='utf-8'));assert v['planSha256']==sha(HERE/'plan.json') and v['fixtureSha256']==sha(STATE/'fixtures.json');assert len(v['rows'])==27
 for r in v['rows']:
  raw=json.loads(Path(r['raw']['path']).read_text(encoding='utf-8'));assert sha(Path(r['raw']['path']))==r['raw']['sha256'];assert len(raw['fresh'])==r['fresh'] and len(raw['warm']['samples'])==r['warm'];assert r['counters']['ancestryTraversals']==0 and r['reads']['membership']['calls']==33
 b=json.loads((R/'docs/research/atlas-component-membership-baseline.json').read_text(encoding='utf-8'));store=R.parent/'meridian-data/experiments/atlas/tryfan-regional-pilot-v1';assert all(sha(store/p)==h for p,h in b['acceptedStoreHashes'].items())
 print(encode({'rows':27,'acceptedStoreUnchanged':True,'ancestryTraversals':0}))
if __name__=='__main__':check() if '--check' in sys.argv else main()
