"""Controlled non-scientific workloads for job supervision tests only."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['normal','memory','commit','tree','child','failure','override','guard-refusal'])
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    if args.mode!='child':
        from worker_bootstrap import lock_worker
        lock_worker()
    (args.folder/(args.mode+'-worker.json')).write_text(json.dumps({'pid':os.getpid(),
        'numericalThreads':[os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')]}))
    if args.mode == 'normal':
        time.sleep(.2)
    elif args.mode == 'memory':
        allocated = bytearray(32*1024**2)
        for i in range(0,len(allocated),4096): allocated[i] = 1
        (args.folder/'allocated.txt').write_text(str(len(allocated)))
        time.sleep(30)
    elif args.mode == 'commit':
        try:
            bytearray(128*1024**2)
        except MemoryError:
            (args.folder/'commit-refused.txt').write_text('allocation refused')
            return 2
        return 5
    elif args.mode == 'tree':
        subprocess.Popen([sys._base_executable,'-B',__file__,'child',str(args.folder)])
        time.sleep(.3)
        # Root exits while descendant remains. Controller must wait for job empty.
    elif args.mode == 'child':
        time.sleep(30)
    elif args.mode=='override':
        from worker_supervision import api
        kernel,_=api()
        # Deliberately remove the hard flag without raising the configured max.
        kernel.SetProcessWorkingSetSizeEx(kernel.GetCurrentProcess(),1048576,
            int(os.environ['MERIDIAN_GUARD_MEMBER_BYTES']),8)
        time.sleep(30)
    elif args.mode=='guard-refusal':
        from resource_guard import confine_process
        try:confine_process(working_set=512*1024**2)
        except RuntimeError:
            (args.folder/'guard-refused.txt').write_text('override refused before API call')
            return 2
        return 5
    else:
        (args.folder/'partial.ndjson').write_text('{"unfinished":')
        return 3
    return 0

if __name__ == '__main__':
    try:result=main()
    except BaseException as error:
        # Small synthetic-only failure evidence; never a terrain output/log.
        (Path(sys.argv[-1])/'synthetic-error.json').write_text(json.dumps(
            {'type':type(error).__name__,'reason':str(error)}))
        raise
    sys.exit(result)
