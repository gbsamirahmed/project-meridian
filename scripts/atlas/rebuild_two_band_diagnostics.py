"""Reproduce measured fields/figures, excluding the evolving sparse inventory."""
import argparse
from pathlib import Path
import two_band_transition as tb
from analyze_two_band import run
from finish_two_band import main,hierarchy

p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);data=p.parse_args().data
folder=data/tb.EXPERIMENT
files=[*sorted(folder.glob('*.npy')),*[folder/name for name in ['measurements.json','independent-checks.json','collar-lod.json','coarse-handoff.json','numerical-fields.png','radial-profiles.png','extrema-patch-profiles.png']]]
before={f.name:tb.rt.digest(f) for f in files}
run(data);main(data);hierarchy(data)
after={f.name:tb.rt.digest(f) for f in files}
assert before==after, {k:(before[k],after[k]) for k in before if before[k]!=after[k]}
tb.sp.save(folder/'diagnostic-rebuild.json',{'identical':True,'files':after,'count':len(after)})
print('IDENTICAL DIAGNOSTICS',len(after))
