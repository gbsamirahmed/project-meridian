"""Gated genuine stage worker. Never launched by this implementation milestone."""
import argparse
import json
from pathlib import Path
from worker_bootstrap import lock_worker


def entry():
    lock_worker() # before NumPy/Rasterio/PROJ/ContourPy imports
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--session',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--prior-controller',type=Path)
    args=parser.parse_args()
    from staged_store import Budget,digest
    from staged_continuation import Continuation,Permit
    from riffelhorn_sources import RiffelhornSources
    from supervise_stage import inspect
    profile=json.loads(args.profile.read_text())
    if (profile.get('scope')!='genuine' or profile.get('stage') not in (1,2)
            or not inspect(profile)['readyToAttempt']):
        raise PermissionError('Unapproved or incompatible genuine profile')
    budget=Budget(**profile['budget']);root=args.data_root/'experiments/atlas/source-aware-contours-v1'
    seed=json.loads((args.session/'session-seed.json').read_text())
    controls=[{'path':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':digest(path),'role':'control','vertices':0}
        for path in (args.session/'session-seed.json',args.session/'worker-lock.json',args.session/'worker-lock.json.ack')]
    sources=RiffelhornSources(args.data_root)
    runner=Continuation(sources,budget,range(2000,3201,10))
    permit=Permit('genuine',profile['stage'],profile['approved'],budget.sha256,
        profile.get('checkpointSha256'),profile.get('controllerSha256'))
    external=args.session/'controller-receipt.json'
    if permit.stage==1:
        runner.stage1(permit,root,args.session/'processing',seed['inventory']+controls,seed['charged'],seed['canonical'],
            controller_receipt=external)
    else:
        runner.stage2(permit,root,args.session/'processing',args.checkpoint,prior_controller=args.prior_controller,
            startup_inventory=controls,controller_receipt=external)

if __name__=='__main__':entry()
