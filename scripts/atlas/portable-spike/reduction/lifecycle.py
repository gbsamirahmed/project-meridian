"""Unchanged installer with shared views: serial owned-copy lifecycle measurement."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile
import time
from shared import SharedProjection
from reader import ReadError
from store import Store
from benchmark import distribution,peak_bytes

p=argparse.ArgumentParser(); p.add_argument('--projection',required=True); a=p.parse_args()
source=Path(a.projection); m=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
identifier=m['projectionIdentity']; pins=list(m['pins']); installs=[]; reopens=[]; restarts=[]; recovery=[]; footprints=[]
for _ in range(3):
    with tempfile.TemporaryDirectory(prefix='atlas-shared-lifecycle-') as folder:
        store=Store.create(Path(folder)/'store'); installs.append(store.install(source,identifier))
        start=time.perf_counter()
        with SharedProjection.from_store(Store(store.root)) as owner:
            views=[owner.pin(pin) for pin in pins]
            try:
                for view in views:view.read({'identity':'glaciers:683'})
            finally:
                for view in views:view.close()
        reopens.append((time.perf_counter()-start)*1000)
        start=time.perf_counter()
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('shared.py')),'--store',str(store.root),'--generation',pins[0]],text=True,encoding='utf-8',capture_output=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        restarts.append((time.perf_counter()-start)*1000)
        start=time.perf_counter()
        def fail(name):
            if name.startswith('staged-member:'):raise OSError('Injected staging failure')
        try:store.install(source,identifier,fail)
        except ReadError:pass
        footprints.append(sum(p.stat().st_size for p in store.root.rglob('*') if p.is_file()))
        for stage in list((store.root/'staging').iterdir()):store.discard_stage(stage.name)
        with SharedProjection.from_store(Store(store.root)) as owner,owner.pin(pins[0]):pass
        recovery.append((time.perf_counter()-start)*1000)
print(json.dumps({'repetitions':3,'unchangedInstallMs':{k:distribution([r[k] for r in installs]) for k in installs[0] if k.endswith('Ms')},
    'sharedThreePinReopenAndIdentityMs':distribution(reopens),'freshSharedProcessReopenMs':distribution(restarts),
    'failedStageCleanupAndSharedReopenMs':distribution(recovery),'observedOwnedBytesAfterFailedStage':footprints,
    'peakWorkingSetBytes':peak_bytes(),'platform':sys.platform,'python':sys.version.split()[0]}))
