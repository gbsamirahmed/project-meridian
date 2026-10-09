"""Standalone process proof with authority/source opens and network/process calls denied."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time

p=argparse.ArgumentParser(); p.add_argument('--projection',required=True); p.add_argument('--config',required=True); p.add_argument('--fixtures',required=True)
a=p.parse_args(); config=json.loads(Path(a.config).read_text(encoding='utf-8'))
repo=Path(__file__).resolve().parents[3]
forbidden=[str(repo),config['registrationWorld'],config['legacyWorld']]+[str(Path(config['dataRoot'])/name) for name in ['sources','derived','experiments']]
with tempfile.TemporaryDirectory(prefix='atlas-independent-process-') as folder:
    root=Path(folder)
    for name in ['reader.py','verification.py','conformance.py']: shutil.copyfile(Path(__file__).parent/name,root/name)
    shutil.copytree(a.fixtures,root/'fixtures')
    bootstrap='''import sys,os
forbidden=[os.path.normcase(os.path.realpath(p)) for p in FORBIDDEN]
def guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen','os.system'):
        raise RuntimeError('Forbidden network or authority dispatch')
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=os.path.normcase(os.path.realpath(args[0]))
        if any(path==p or path.startswith(p+os.sep) for p in forbidden):
            raise RuntimeError('Forbidden authority or original source access')
sys.addaudithook(guard)
import conformance
sys.argv=['conformance.py','--projection',PROJECTION,'--fixtures','fixtures']
sys.exit(conformance.run())
'''.replace('FORBIDDEN',repr(forbidden)).replace('PROJECTION',repr(str(Path(a.projection).resolve())))
    start=time.perf_counter()
    completed=subprocess.run([sys.executable,'-B','-c',bootstrap],cwd=root,text=True,encoding='utf-8',capture_output=True)
    print(completed.stdout,end='')
    if completed.stderr: print(completed.stderr,file=sys.stderr,end='')
    print(json.dumps({'isolation':{'returnCode':completed.returncode,'freshProcessMs':(time.perf_counter()-start)*1000,'authorityAndSourceOpens':'denied','networkAndChildProcesses':'denied'}}))
    sys.exit(completed.returncode)
