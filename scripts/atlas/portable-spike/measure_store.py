"""Serial desktop lifecycle measurements on owned temporary copies, not power-loss proof."""
from pathlib import Path
import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import time
from reader import identity, ReadError
from store import Store
from benchmark import peak_bytes, distribution

p=argparse.ArgumentParser(); p.add_argument('--projection',required=True); a=p.parse_args()
source=Path(a.projection); m=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
projection_id=m['projectionIdentity']; pin=next(k for k,v in m['pins'].items() if v['alias']=='after')
installs=[]; replacements=[]; reopens=[]; restarts=[]; recovery=[]; footprints=[]
for _ in range(3):
    with tempfile.TemporaryDirectory(prefix='atlas-store-measure-') as folder:
        root=Path(folder); store=Store.create(root/'store')
        installs.append(store.install(source,projection_id))
        candidate=root/'candidate'; shutil.copytree(source,candidate)
        revised=copy.deepcopy(m); revised['coverage']+=' Administrative measured packaging variant; scientific records unchanged.'
        revised['projectionIdentity']=identity({k:v for k,v in revised.items() if k!='projectionIdentity'})
        (candidate/'manifest.json').write_text(json.dumps(revised,ensure_ascii=False),encoding='utf-8')
        peak_disk=[0]
        def measure(_): peak_disk[0]=max(peak_disk[0],sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))
        replacements.append(store.install(candidate,revised['projectionIdentity'],measure))
        footprints.append({'additionalScratchPeakBytes':peak_disk[0], 'lastAndSelectedReadyBytes':sum(p.stat().st_size for p in (store.root/'packages').rglob('*') if p.is_file())})
        start=time.perf_counter()
        with Store(store.root).open(pin) as reader: reader.read({'identity':'glaciers:683'})
        reopens.append((time.perf_counter()-start)*1000)
        start=time.perf_counter()
        completed=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('store.py')),'open','--store',str(store.root),'--generation',pin],capture_output=True,text=True)
        if completed.returncode: raise RuntimeError(completed.stdout+completed.stderr)
        restarts.append((time.perf_counter()-start)*1000)
        start=time.perf_counter()
        def fail(name):
            if name.startswith('staged-member:'): raise OSError('Injected staging failure')
        try: store.install(source,projection_id,fail)
        except ReadError: pass
        for stage in list((store.root/'staging').iterdir()): store.discard_stage(stage.name)
        with Store(store.root).open(pin): pass
        recovery.append((time.perf_counter()-start)*1000)
print(json.dumps({'repetitions':3,'installMs':{k:distribution([x[k] for x in installs]) for k in installs[0] if k.endswith('Ms')},
                  'replacementMs':{k:distribution([x[k] for x in replacements]) for k in replacements[0] if k.endswith('Ms')},
                  'reopenAndIdentityMs':distribution(reopens),'freshProcessReopenMs':distribution(restarts),'failedStageCleanupAndReopenMs':distribution(recovery),
                  'footprints':footprints,'peakWorkingSetBytes':peak_bytes(),'platform':sys.platform,'python':sys.version.split()[0]}))
