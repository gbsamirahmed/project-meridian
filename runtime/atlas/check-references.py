"""Fresh inherited regressions plus scoped-reference runtime/CLI workflows."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,os,re,subprocess,sys,time
R=Path(__file__).resolve().parents[2];finish='--finish' in sys.argv;previous=(R/'../../Codex/atlas-local-references-v1/regression').resolve();OUT=previous.parent/'final-regression' if finish else previous;OUT.mkdir(parents=True,exist_ok=True)
commands=json.loads((R/'docs/research/atlas-local-exe-validation.json').read_text(encoding='utf-8'))['commands'];receipts=[None]*len(commands)
for c in commands:
 if c['name'] in ['runtime-cli-example','runtime-registration-cli','runtime-retrieval-cli','runtime-exe-cli']:
  cfg=json.loads(Path(c['args'][-1]).read_text(encoding='utf-8'))
  if c['name']!='runtime-retrieval-cli':cfg['publicationRoot']=str(OUT/('world-'+str(time.time_ns())))
  cfg['catalogueRoot']=str(OUT/('cache-'+str(time.time_ns())));f=OUT/(c['name']+'-config.json');f.write_text(json.dumps(cfg),encoding='utf-8');c['args']=[*c['args'][:-1],str(f)]
def execute(c):
 start=time.perf_counter();p=subprocess.run(c['args'],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF'});output=p.stdout+p.stderr;(OUT/(c['name']+'.log')).write_text(output,encoding='utf-8');m=re.search(r'(?:ℹ tests|# tests) (\d+)',output) or re.search(r'Ran (\d+) tests?',output)
 return {'name':c['name'],'args':c['args'],'exitCode':p.returncode,'tests':int(m[1]) if m else None,'elapsedSeconds':time.perf_counter()-start}
if finish:
 receipts=json.loads((previous/'commands.json').read_text())[:len(commands)]
 assert len(receipts)==32 and all(c and c['exitCode']==0 for c in receipts) and sum(c.get('tests') or 0 for c in receipts)==794
 print('Retain freshly passed inherited794 tests; rerun only final changed reference-family workflows',flush=True)
 (OUT/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
else:
 with ThreadPoolExecutor(max_workers=3) as pool:
  fs={pool.submit(execute,c):i for i,c in enumerate(commands)}
  for f in as_completed(fs):
   i=fs[f];receipts[i]=f.result();print(json.dumps(receipts[i]),flush=True);(OUT/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
if any(c['exitCode'] for c in receipts):sys.exit(1)
data=(R/'../meridian-data').resolve();base=json.loads((R/'docs/research/atlas-local-references-baseline.json').read_text());cfg={'dataRoot':str(data),'publicationRoot':str(OUT/('reference-world-'+str(time.time_ns()))),'catalogueRoot':str(OUT/('reference-cache-'+str(time.time_ns()))),'python':str(data/'earth-lab/.venv/Scripts/python.exe'),'sourcePublication':base['selectedWorld']};f=OUT/'references-config.json';f.write_text(json.dumps(cfg),encoding='utf-8')
for c in [{'name':'runtime-references','args':['node','--test','runtime/atlas/test-references.mjs']},{'name':'runtime-references-cli','args':['node','runtime/atlas/example-references.mjs',str(f)]}]:
 receipts.append(execute(c));print(json.dumps(receipts[-1]),flush=True);(OUT/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
sys.exit(any(c['exitCode'] for c in receipts))
