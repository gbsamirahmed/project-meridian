"""Serial owned stores: v1 last-ready, window replacement and recovery costs."""
from pathlib import Path
import argparse
import errno
import json
import subprocess
import sys
import tempfile
import time
from window import WindowShared, WindowStore, ReadError, BASE
from benchmark import distribution, peak_bytes

p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--projection',required=True);a=p.parse_args()
source=Path(a.projection);m=json.loads((source/'manifest.json').read_text(encoding='utf-8'));identifier=m['projectionIdentity'];pins=list(m['pins'])
initial=[];replacement=[];reopens=[];restarts=[];recovery=[];footprints=[]
for _ in range(3):
    with tempfile.TemporaryDirectory(prefix='atlas-window-measure-') as folder:
        store=WindowStore.create(Path(folder)/'store');initial.append(store.install(a.baseline,BASE));replacement.append(store.install(source,identifier))
        start=time.perf_counter()
        with WindowShared.from_store(WindowStore(store.root),identifier) as owner:
            views=[owner.pin(pin) for pin in pins]
            try:
                for view in views:view.read({'identity':'glaciers:683'})
            finally:
                for view in views:view.close()
        reopens.append((time.perf_counter()-start)*1000)
        start=time.perf_counter()
        result=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('local.py')),'query','--store',str(store.root),'--identity',identifier,'--generation',pins[0]],text=True,encoding='utf-8',capture_output=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        restarts.append((time.perf_counter()-start)*1000)
        # Failed replacement in the reverse direction: an explicit valid last-ready
        # window remains selected; no generation fallback and no hidden repair.
        start=time.perf_counter()
        def fail(name):
            if name.startswith('staging-write:'):raise OSError(errno.ENOSPC,'Injected staging write failure')
        try:store.install(a.baseline,BASE,fail)
        except ReadError:pass
        else:raise AssertionError('Injected staging failure was not exercised')
        assert store.selected()==identifier
        footprints.append(sum(p.stat().st_size for p in store.root.rglob('*') if p.is_file()))
        for stage in list((store.root/'staging').iterdir()):store.discard_stage(stage.name)
        with WindowShared.from_store(WindowStore(store.root),identifier) as owner,owner.pin(pins[0]):pass
        recovery.append((time.perf_counter()-start)*1000)
print(json.dumps({'repetitions':3,'baselineInstallMs':{k:distribution([r[k] for r in initial]) for k in initial[0] if k.endswith('Ms')},
    'windowReplacementMs':{k:distribution([r[k] for r in replacement]) for k in replacement[0] if k.endswith('Ms')},
    'sharedThreePinReopenAndIdentityMs':distribution(reopens),'freshWindowProcessReopenMs':distribution(restarts),
    'failedStageCleanupAndWindowReopenMs':distribution(recovery),'observedOwnedBytesAfterFailedStage':footprints,
    'peakWorkingSetBytes':peak_bytes(),'platform':sys.platform,'python':sys.version.split()[0]}))
