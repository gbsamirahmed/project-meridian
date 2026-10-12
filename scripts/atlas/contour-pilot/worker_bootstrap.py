"""Cooperative startup lock, before scientific imports; no system configuration."""
import json
import os
from pathlib import Path
import time


def lock_worker():
    path=os.environ.get('MERIDIAN_WORKER_LOCK_FILE')
    if not path:raise RuntimeError('Controller handshake is required')
    ceiling=int(os.environ['MERIDIAN_GUARD_MEMBER_BYTES'])
    # The controller already owns the allocation job. Do not create an inner
    # worker-owned job whose lifetime could obscure descendant supervision.
    import ctypes
    from worker_supervision import api,SIZE
    from ctypes import wintypes
    kernel,_=api();process=kernel.GetCurrentProcess()
    if not kernel.SetProcessWorkingSetSizeEx(process,1048576,ceiling,4):raise ctypes.WinError(ctypes.get_last_error())
    minimum,maximum,flags=SIZE(),SIZE(),wintypes.DWORD()
    if not kernel.GetProcessWorkingSetSizeEx(process,ctypes.byref(minimum),ctypes.byref(maximum),ctypes.byref(flags)):
        raise ctypes.WinError(ctypes.get_last_error())
    if maximum.value!=ceiling or not flags.value&4:raise RuntimeError('Worker resident lock not verified')
    guard={'workingSetMaximum':maximum.value,'workingSetFlags':flags.value,
           'allocationGuard':'controller-owned, non-inherited job handle'}
    path=Path(path)
    temporary=path.with_name(path.name+'.pending')
    with temporary.open('x') as stream:
        json.dump({'pid':os.getpid(),'guard':guard},stream);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
    acknowledgement=Path(str(path)+'.ack');deadline=time.monotonic()+5
    while not acknowledgement.exists():
        if time.monotonic()>deadline:raise RuntimeError('Controller did not acknowledge the worker lock')
        time.sleep(.01)
    actual=json.loads(acknowledgement.read_text())
    if actual!={'pid':os.getpid(),'memberBytes':ceiling}:raise RuntimeError('Wrong worker acknowledgement')
    return guard
