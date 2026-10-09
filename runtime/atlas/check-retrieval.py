"""Fresh inherited regressions and the unified runtime CLI. Outputs stay outside the repo."""
from pathlib import Path
import json,os,re,subprocess,sys,time
R=Path(__file__).resolve().parents[2];OUT=(R/'../../Codex/atlas-local-retrieval-v1/regression').resolve();OUT.mkdir(parents=True,exist_ok=True)
prior=json.loads((R/'docs/research/atlas-local-registration-validation.json').read_text(encoding='utf-8'))['commands']
b=json.loads((R/'docs/research/atlas-local-retrieval-baseline.json').read_text(encoding='utf-8'));p=json.loads((R/'runtime/atlas/retrieval-plan.json').read_text(encoding='utf-8'));data=(R/'../meridian-data').resolve()
config={'dataRoot':str(data),'publicationRoot':b['selectedWorld'],'catalogueRoot':str(OUT/('retrieval-cache-'+str(time.time_ns()))),'python':str(data/'earth-lab/.venv/Scripts/python.exe'),'generation':p['publication']['history'][-1],'historicalGeneration':p['publication']['history'][2]}
f=OUT/'retrieval-config.json';f.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8',newline='\n')
commands=prior+[{'name':'runtime-retrieval','args':['node','--test','runtime/atlas/test-retrieval.mjs']},{'name':'runtime-retrieval-cli','args':['node','runtime/atlas/example-retrieval.mjs',str(f)]}];receipts=[]
for c in commands:
 args=c['args']
 if c['name'] in ['runtime-cli-example','runtime-registration-cli']:
  previous=json.loads(Path(args[-1]).read_text(encoding='utf-8'));previous['publicationRoot']=str(OUT/('inherited-world-'+str(time.time_ns())));previous['catalogueRoot']=str(OUT/('inherited-cache-'+str(time.time_ns())));f=OUT/(c['name']+'-config.json');f.write_text(json.dumps(previous),encoding='utf-8');args=[*args[:-1],str(f)]
 start=time.perf_counter();p=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF'});text=p.stdout+p.stderr
 (OUT/(c['name']+'.log')).write_text(text,encoding='utf-8',newline='\n');m=re.search(r'(?:ℹ tests|# tests) (\d+)',text) or re.search(r'Ran (\d+) tests?',text)
 receipts.append({'name':c['name'],'args':args,'exitCode':p.returncode,'tests':int(m[1]) if m else None,'elapsedSeconds':time.perf_counter()-start});(OUT/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(receipts[-1]),flush=True)
sys.exit(any(c['exitCode'] for c in receipts))
