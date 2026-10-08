"""Run inherited regression commands and focused runtime checks into external logs."""
from pathlib import Path
import json,os,re,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
OUT=(R/'../../Codex/atlas-local-runtime-v1/regression').resolve();OUT.mkdir(parents=True,exist_ok=True)
prior=json.loads((R/'docs/research/atlas-local-architecture-validation.json').read_text(encoding='utf-8'))['commands']
commands=prior+[{'name':'runtime-types','args':['node','node_modules/typescript/bin/tsc','-p','runtime/atlas/tsconfig.json']},{'name':'runtime-focused','args':['node','--test','runtime/atlas/test-runtime.mjs']}]
receipts=[]
for c in commands:
 start=time.perf_counter();p=subprocess.run(c['args'],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PROJ_NETWORK':'OFF'})
 text=p.stdout+p.stderr;(OUT/(c['name']+'.log')).write_text(text,encoding='utf-8',newline='\n')
 m=re.search(r'(?:ℹ tests|# tests) (\d+)',text) or re.search(r'Ran (\d+) tests?',text)
 receipts.append({'name':c['name'],'args':c['args'],'exitCode':p.returncode,'tests':int(m[1]) if m else None,'elapsedSeconds':time.perf_counter()-start})
 (OUT/'commands.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(receipts[-1]),flush=True)
sys.exit(any(c['exitCode'] for c in receipts))
