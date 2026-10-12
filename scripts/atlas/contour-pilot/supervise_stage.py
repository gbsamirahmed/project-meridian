"""Dormant genuine controller entry point; proposal inspection is read-only.

An approval file records a trusted operator decision, never grants permission by
itself. The supplied proposal is explicitly unapproved and cannot launch a stage.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from staged_store import Budget,digest,encode
from staged_continuation import historical_inventory,check_shape_capacity


def inspect(profile):
    budget=Budget(**profile['budget']);memory=profile['memory'];issues=[]
    if not profile.get('approved'):issues.append('No explicit owner stage approval')
    try:check_shape_capacity((1000,1000),budget)
    except ValueError as error:issues.append(str(error))
    if memory['memberBytes']<139104256 and not profile.get('memberRiskExplicitlyAccepted',False):
        issues.append('Member cap below prior genuine peak; compatibility/risk decision outstanding')
    if (memory['controllerBytes']!=128*1024**2 or memory['memberBytes']*memory['maxProcesses']>384*1024**2
            or memory['jobCommitBytes']>384*1024**2):
        issues.append('Controller/member allocation exceeds reviewed 512 MiB layout')
    return {'profileSha256':budget.sha256,'approved':bool(profile.get('approved')),
            'readyToAttempt':not issues,'blockers':issues,'effectiveMemory':memory}


def launch(args):
    started=time.monotonic()
    profile=json.loads(args.profile.read_text())
    decision=inspect(profile)
    if not decision['readyToAttempt']:raise PermissionError('; '.join(decision['blockers']))
    if profile.get('scope')!='genuine' or profile.get('stage')!=args.stage:
        raise PermissionError('Approval does not match this stage')
    if not re.fullmatch(r'execution-[0-9]+-stage[12](-[a-z0-9-]+)?',args.session):
        raise ValueError('Explicit fresh session name required')
    root=args.data_root/'experiments/atlas/source-aware-contours-v1'
    session=root/args.session
    if session.exists():raise ValueError('Cannot overwrite a previous session')
    budget=Budget(**profile['budget']);elapsed=0.
    if args.stage==1:
        old=json.loads(Path(__file__).with_name('genuine-rerun-receipt.json').read_text())
        entries=historical_inventory(root,root/'execution-3/inventory.json',old['inventorySha256'],
            {'files':867,'bytes':64250005,'stored':1992909,'final':953147})
        seed={'inventory':entries,'charged':1999871,
              'canonical':{n:f'execution-3/processing/run-1/{n}' for n in old['completedProducts']}}
    else:
        if not args.checkpoint or not args.prior_controller:raise ValueError('Stage 2 needs both sealed closures')
        if digest(args.checkpoint)!=profile.get('checkpointSha256') or digest(args.prior_controller)!=profile.get('controllerSha256'):
            raise PermissionError('Owner approval does not bind the reviewed closures')
        closure=json.loads(args.prior_controller.read_text())
        if not closure['success']:raise ValueError('Stage 1 controller failed')
        elapsed=closure['totalActiveSeconds'];seed={}
    remaining=budget.seconds-elapsed-(time.monotonic()-started)
    if remaining<=0:raise ValueError('No shared active-time headroom')
    # Reserve the whole 64 KiB for controller/worker failure evidence before any
    # session write, including immutable existing storage in the owning root.
    body=encode(seed)
    existing=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if existing+len(body)+budget.receipt_reserve>budget.scratch:raise ValueError('No session scratch headroom')
    session.mkdir();seed_path=session/'session-seed.json';seed_path.write_bytes(body)
    # The scientific interpreter's base executable is already installed. Reuse
    # its exact venv site-packages to avoid supervising another controller launcher.
    base=subprocess.check_output([str(args.python),'-B','-c','import sys; print(sys._base_executable)'],text=True).strip()
    packages=args.python.parent.parent/'Lib/site-packages'
    bootstrap='import site,runpy,sys; site.addsitedir(sys.argv.pop(1)); runpy.run_path(sys.argv[0],run_name="__main__")'
    command=[base,'-B','-c',bootstrap,str(packages),str(Path(__file__).with_name('stage_worker.py')),
        '--profile',str(args.profile.resolve()),'--data-root',str(args.data_root.resolve()),'--session',str(session.resolve())]
    if args.checkpoint:command+=['--checkpoint',str(args.checkpoint.resolve())]
    if args.prior_controller:command+=['--prior-controller',str(args.prior_controller.resolve())]
    from worker_supervision import supervise
    memory=profile['memory'];target=session/'controller-receipt.json'
    remaining=budget.seconds-elapsed-(time.monotonic()-started)
    if remaining<=0:raise ValueError('No active-time headroom after controller preparation')
    result=supervise(command,target,seconds=remaining,sampled_limit=budget.working,member_limit=memory['memberBytes'],
        commit_limit=memory['jobCommitBytes'],max_processes=memory['maxProcesses'],
        handshake_path=session/'worker-lock.json',receipt_byte_limit=budget.receipt_reserve//4,
        storage_root=root,storage_limit=budget.scratch)
    result['totalActiveSeconds']=elapsed+time.monotonic()-started
    if result['totalActiveSeconds']>=budget.seconds:
        result['success']=False
        result['stopReason']='Shared active-time ceiling reached before controller closure'
    result['profileSha256']=budget.sha256;result['stage']=args.stage
    final=encode(result)
    if len(final)>budget.receipt_reserve//4:raise ValueError('Controller closure exceeds reserved transaction size')
    temporary=target.with_name(target.name+'.pending')
    if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+len(final)>budget.scratch:
        raise ValueError('Final controller receipt cannot fit scratch ceiling')
    with temporary.open('xb') as stream:
        if stream.write(final)!=len(final):raise OSError('Short controller closure write')
        stream.flush();os.fsync(stream.fileno())
    temporary.replace(target)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--stage',type=int,choices=(1,2))
    parser.add_argument('--data-root',type=Path)
    parser.add_argument('--python',type=Path)
    parser.add_argument('--session')
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--prior-controller',type=Path)
    args=parser.parse_args()
    if args.inspect:print(json.dumps(inspect(json.loads(args.profile.read_text())),indent=2))
    elif not all((args.stage,args.data_root,args.python,args.session)):
        parser.error('Explicit stage, source root, installed Python and fresh session required')
    else:print(json.dumps(launch(args),indent=2))
