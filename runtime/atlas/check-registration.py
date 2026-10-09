"""Fresh inherited regression commands plus registration integration and CLI example."""
from pathlib import Path
import json,os,re,subprocess,sys,time
R=Path(__file__).resolve().parents[2];OUT=(R/'../../Codex/atlas-local-registration-v1/regression').resolve();OUT.mkdir(parents=True,exist_ok=True)
prior=json.loads((R/'docs/research/atlas-local-lifecycle-validation.json').read_text(encoding='utf-8'))['commands']
data=(R/'../meridian-data').resolve();config={'dataRoot':str(data),'publicationRoot':str(OUT/('example-world-'+str(time.time_ns()))),'catalogueRoot':str(OUT/('example-cache-'+str(time.time_ns()))),'python':str(data/'earth-lab/.venv/Scripts/python.exe'),'tryfanRoot':str(data/'experiments/atlas/tryfan-regional-pilot-v1'),'preparedRoot':str(data/'derived/atlas/riffelhorn/riffelhorn-qualified-fixture-v1/357b28e705f7c2647cdf2d54467fc9ee851465814d8ed645cae30713ef9187bb')}
(OUT/'example-config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8',newline='\n')
commands=prior+[{'name':'runtime-registration','args':['node','--test','runtime/atlas/test-registration.mjs']},{'name':'runtime-registration-cli','args':['node','runtime/atlas/example-registration.mjs',str(OUT/'example-config.json')]}];receipts=[]
# Historical example configuration is copied to new destinations, never overwritten.
for c in commands:
 args=c['args']
 if c['name']=='runtime-cli-example':
  previous=json.loads(Path(args[-1]).read_text());previous['publicationRoot']=str(OUT/('inherited-world-'+str(time.time_ns())));previous['catalogueRoot']=str(OUT/('inherited-cache-'+str(time.time_ns())));f=OUT/'inherited-config.json';f.write_text(json.dumps(previous));args=[*args[:-1],str(f)]
 start=time.perf_counter();p=subprocess.run(args,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF'});text=p.stdout+p.stderr
 (OUT/(c['name']+'.log')).write_text(text,encoding='utf-8',newline='\n');m=re.search(r'(?:ℹ tests|# tests) (\d+)',text) or re.search(r'Ran (\d+) tests?',text)
 receipts.append({'name':c['name'],'args':args,'exitCode':p.returncode,'tests':int(m[1]) if m else None,'elapsedSeconds':time.perf_counter()-start});(OUT/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(receipts[-1]),flush=True)
sys.exit(any(c['exitCode'] for c in receipts))
