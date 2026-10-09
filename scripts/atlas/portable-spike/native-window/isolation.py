"""Fresh isolated shared-reader replay; source/authority/network opens are denied."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time

p=argparse.ArgumentParser(); p.add_argument('--projection',required=True); p.add_argument('--config',required=True); p.add_argument('--fixtures',required=True); p.add_argument('--baseline',required=True)
a=p.parse_args(); here=Path(__file__).resolve().parent; repo=here.parents[3]
config=json.loads(Path(a.config).read_text(encoding='utf-8'))
forbidden=[str(repo),str(Path(a.baseline).resolve()),config['registrationWorld'],config['legacyWorld']]+[str(Path(config['dataRoot'])/name) for name in ['sources','derived','experiments']]
with tempfile.TemporaryDirectory(prefix='atlas-shared-isolation-') as folder:
    root=Path(folder)
    for name in ['reader.py','verification.py','conformance.py','store.py']: shutil.copyfile(here.parent/name,root/name)
    shutil.copyfile(here.parent/'reduction'/'shared.py',root/'shared.py')
    for name in ['window.py','closure.py','replay.py']: shutil.copyfile(here/name,root/name)
    shutil.copytree(a.fixtures,root/'fixtures')
    code='''import sys,os
forbidden=[os.path.normcase(os.path.realpath(p)) for p in FORBIDDEN]
def guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo','subprocess.Popen','os.system'):
        raise RuntimeError('Forbidden network or authority dispatch')
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=os.path.normcase(os.path.realpath(args[0]))
        if any(path==p or path.startswith(p+os.sep) for p in forbidden):
            raise RuntimeError('Forbidden authority or original source access')
sys.addaudithook(guard)
import replay
sys.argv=['replay.py','--projection',PROJECTION,'--fixtures','fixtures']
sys.exit(replay.run())
'''.replace('FORBIDDEN',repr(forbidden)).replace('PROJECTION',repr(str(Path(a.projection).resolve())))
    start=time.perf_counter()
    completed=subprocess.run([sys.executable,'-B','-c',code],cwd=root,text=True,encoding='utf-8',capture_output=True)
    print(completed.stdout,end='')
    if completed.stderr:print(completed.stderr,file=sys.stderr,end='')
    print(json.dumps({'isolation':{'returnCode':completed.returncode,'freshProcessMs':(time.perf_counter()-start)*1000,'authorityAndSourceOpens':'denied','networkAndChildProcesses':'denied'}}))
    sys.exit(completed.returncode)
