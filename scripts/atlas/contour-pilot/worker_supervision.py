"""Windows job-tree supervision, including Windows venv redirector descendants.

No shell, network or terrain entry point. The command is supplied by an operator;
using this controller does not authorise a scientific rerun.
"""
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import subprocess
import time

SIZE = c.c_size_t
HANDLE = w.HANDLE


class Basic(c.Structure):
    _fields_ = [('processTime', c.c_longlong), ('jobTime', c.c_longlong),
               ('flags', w.DWORD), ('minimum', SIZE), ('maximum', SIZE),
               ('active', w.DWORD), ('affinity', SIZE),
               ('priority', w.DWORD), ('scheduling', w.DWORD)]


class IO(c.Structure):
    _fields_ = [(name, c.c_ulonglong) for name in
               ('reads', 'writes', 'other', 'readBytes', 'writeBytes', 'otherBytes')]


class Extended(c.Structure):
    _fields_ = [('basic', Basic), ('io', IO), ('processMemory', SIZE),
               ('jobMemory', SIZE), ('peakProcess', SIZE), ('peakJob', SIZE)]


class Start(c.Structure):
    _fields_ = [('cb', w.DWORD), ('reserved', w.LPWSTR), ('desktop', w.LPWSTR),
               ('title', w.LPWSTR)] + [(name, w.DWORD) for name in
               ('x', 'y', 'xSize', 'ySize', 'xCount', 'yCount', 'fill', 'flags')] + [
               ('show', w.WORD), ('reservedSize', w.WORD), ('reservedBytes', c.c_void_p),
               ('stdin', HANDLE), ('stdout', HANDLE), ('stderr', HANDLE)]


class Process(c.Structure):
    _fields_ = [('process', HANDLE), ('thread', HANDLE), ('pid', w.DWORD), ('tid', w.DWORD)]


class Memory(c.Structure):
    _fields_ = [('cb', w.DWORD), ('faults', w.DWORD)] + [(name, SIZE) for name in
               ('peak', 'working', 'pagedPeak', 'paged', 'nonpagedPeak', 'nonpaged',
                'pagefile', 'pagefilePeak')]


class JobAccounting(c.Structure):
    _fields_ = [(name, c.c_longlong) for name in ('user','kernel','periodUser','periodKernel')] + [
        (name,w.DWORD) for name in ('faults','totalProcesses','activeProcesses','terminatedProcesses')]


def api():
    if os.name != 'nt':
        raise RuntimeError('Reviewed controller requires Windows')
    kernel = c.WinDLL('kernel32', use_last_error=True)
    declarations = {
        'CreateJobObjectW': ([c.c_void_p, w.LPCWSTR], HANDLE),
        'SetInformationJobObject': ([HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL),
        'QueryInformationJobObject': ([HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p], w.BOOL),
        'AssignProcessToJobObject': ([HANDLE, HANDLE], w.BOOL),
        'TerminateJobObject': ([HANDLE, w.UINT], w.BOOL),
        'CloseHandle': ([HANDLE], w.BOOL),
        'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], HANDLE),
        'ResumeThread': ([HANDLE], w.DWORD),
        'WaitForSingleObject': ([HANDLE, w.DWORD], w.DWORD),
        'GetExitCodeProcess': ([HANDLE, c.POINTER(w.DWORD)], w.BOOL),
        'SetProcessWorkingSetSizeEx': ([HANDLE, SIZE, SIZE, w.DWORD], w.BOOL),
        'GetProcessWorkingSetSizeEx': ([HANDLE,c.POINTER(SIZE),c.POINTER(SIZE),c.POINTER(w.DWORD)],w.BOOL),
        'GetCurrentProcess': ([], HANDLE),
        'TerminateProcess': ([HANDLE, w.UINT], w.BOOL),
        'CreateProcessW': ([w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p, w.BOOL,
                            w.DWORD, c.c_void_p, w.LPCWSTR, c.POINTER(Start), c.POINTER(Process)], w.BOOL),
    }
    for name, (args, result) in declarations.items():
        fn = getattr(kernel, name)
        fn.argtypes, fn.restype = args, result
    psapi = c.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [HANDLE, c.POINTER(Memory), w.DWORD]
    def memory(handle):
        value = Memory(); value.cb = c.sizeof(value)
        if not psapi.GetProcessMemoryInfo(handle, c.byref(value), value.cb):
            raise c.WinError(c.get_last_error())
        return value
    return kernel, memory


def supervise(command, receipt_path, *, seconds=1200, sampled_limit=512*1024**2,
              member_limit=128*1024**2, commit_limit=384*1024**2, max_processes=3,
              handshake_path=None, receipt_byte_limit=65536, storage_root=None, storage_limit=None):
    """Keep all inherited children in a kill-on-close job before execution starts.

    Samples/individual lifetime peaks include the controller. A sum of independent
    peaks is a conservative upper bound, not an observed simultaneous maximum.
    OS job commit/working-set limits supplement sampling; refusal never means pass.
    """
    receipt_path = Path(receipt_path)
    if receipt_path.exists():
        raise ValueError('Fresh receipt required')
    if (seconds <= 0 or not 1 <= max_processes <= 4 or member_limit <= 0
            or max_processes*member_limit > 384*1024**2 or receipt_byte_limit <= 0):
        raise ValueError('Unsupported resource profile')
    if (storage_root is None) != (storage_limit is None):
        raise ValueError('Storage root and ceiling must be supplied together')
    kernel, memory = api()
    def confine(handle, maximum):
        if not kernel.SetProcessWorkingSetSizeEx(handle, 1024**2, maximum, 4):
            raise c.WinError(c.get_last_error())
        minimum, actual, flags = SIZE(), SIZE(), w.DWORD()
        if not kernel.GetProcessWorkingSetSizeEx(handle,c.byref(minimum),c.byref(actual),c.byref(flags)):
            raise c.WinError(c.get_last_error())
        if actual.value != maximum or not flags.value & 4:
            raise RuntimeError('Per-process hard working-set maximum not verified')
    controller = kernel.GetCurrentProcess()
    confine(controller,128*1024**2)
    if memory(controller).peak > 128*1024**2:
        raise RuntimeError('Controller already exceeded its allowance')
    job = kernel.CreateJobObjectW(None, None)
    process = Process()
    handles = {}
    peaks = {}
    previous_environment = {key:os.environ.get(key) for key in
                            ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','MERIDIAN_GUARD_MEMBER_BYTES',
                             'MERIDIAN_WORKER_LOCK_FILE')}
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
    os.environ['MERIDIAN_GUARD_MEMBER_BYTES']=str(member_limit)
    if handshake_path:os.environ['MERIDIAN_WORKER_LOCK_FILE']=str(handshake_path)
    started = time.monotonic()
    result = {'stopReason': None, 'terminationVerified': False, 'maxJobProcesses': 0,
              'sampledAggregatePeakBytes': 0, 'requests': 0, 'processingThreads': 1,
              'jobCommitLimitBytes': commit_limit, 'memberWorkingSetLimitBytes': member_limit,
              'aggregateWorkingSetCeilingBytes':sampled_limit,
              'controllerWorkingSetLimitBytes': 128*1024**2,
              'activeProcessLimit': max_processes, 'deadlineSeconds': seconds,
              'allProcessHandlesSignalled': True, 'allAssignedProcessesObserved': False,
              'memberHardLimitsVerified': True, 'finalMemoryCountersComplete': True,
              'jobProcessCommitLimitBytes':member_limit,'residentOverrideDetected':False,
              'startupSettingsReasserted':0,'workerHandshakeVerified':False,
              'memoryProfile':'explicit conservative member allocation; not genuine-performance qualification'}
    def members():
        # A job process list inspects only this workload, never unrelated processes.
        buf = c.create_string_buffer(8 + 8*32)
        if not kernel.QueryInformationJobObject(job, 3, buf, len(buf), None):
            raise c.WinError(c.get_last_error())
        count = w.DWORD.from_buffer(buf, 4).value
        return list((SIZE*count).from_buffer(buf, 8))
    try:
        info = Extended()
        # ACTIVE_PROCESS | JOB_MEMORY | KILL_ON_JOB_CLOSE. No breakaway.
        # Job-wide WORKINGSET requires an unavailable quota privilege on this
        # laptop. Apply per-process hard maxima through existing handle rights.
        info.basic.flags = 0x8 | 0x100 | 0x200 | 0x2000
        info.basic.active, info.jobMemory,info.processMemory = max_processes, commit_limit,member_limit
        if not job or not kernel.SetInformationJobObject(job, 9, c.byref(info), c.sizeof(info)):
            raise c.WinError(c.get_last_error())
        verified = Extended()
        if not kernel.QueryInformationJobObject(job, 9, c.byref(verified), c.sizeof(verified), None):
            raise c.WinError(c.get_last_error())
        if (verified.basic.flags != info.basic.flags or verified.jobMemory != commit_limit
                or verified.basic.active != max_processes or verified.processMemory!=member_limit):
            raise RuntimeError('Job configuration mismatch')
        startup = Start(); startup.cb = c.sizeof(startup)
        cmd = c.create_unicode_buffer(subprocess.list2cmdline([str(v) for v in command]))
        if not kernel.CreateProcessW(None, cmd, None, None, False, 0x4 | 0x08000000,
                                     None, None, c.byref(startup), c.byref(process)):
            raise c.WinError(c.get_last_error())
        handles[process.pid] = process.process
        if not kernel.AssignProcessToJobObject(job, process.process):
            raise c.WinError(c.get_last_error())
        confine(process.process,member_limit)
        if kernel.ResumeThread(process.thread) == 0xffffffff:
            raise c.WinError(c.get_last_error())
        while True:
            ids = members()
            accounting = JobAccounting()
            if not kernel.QueryInformationJobObject(job, 1, c.byref(accounting), c.sizeof(accounting), None):
                raise c.WinError(c.get_last_error())
            result['maxJobProcesses'] = max(result['maxJobProcesses'], accounting.activeProcesses)
            current = memory(controller).working
            protected=None
            if handshake_path and Path(handshake_path).exists():
                hello=json.loads(Path(handshake_path).read_text())
                protected=hello['pid']
                if protected not in ids and protected not in handles:raise RuntimeError('Handshake process is outside job')
            for pid in ids:
                if pid not in handles:
                    handle = kernel.OpenProcess(0x100510, False, pid)
                    if not handle:
                        # A short-lived child may exit before OpenProcess. Its
                        # unobserved peak prevents accepting the resource claim.
                        raise RuntimeError('Job member exited before memory handle capture')
                    handles[pid] = handle
                    confine(handle,member_limit)
                if kernel.WaitForSingleObject(handles[pid],0)!=0:
                    minimum,maximum,flags=SIZE(),SIZE(),w.DWORD()
                    if not kernel.GetProcessWorkingSetSizeEx(handles[pid],c.byref(minimum),c.byref(maximum),c.byref(flags)):
                        raise c.WinError(c.get_last_error())
                    if maximum.value!=member_limit or not flags.value&4:
                        if protected==pid and result['workerHandshakeVerified']:
                            result['residentOverrideDetected']=True
                            result['residentMismatch']={'expectedMaximum':member_limit,'actualMaximum':maximum.value,'flags':flags.value}
                            raise RuntimeError('Worker attempted to override the controller resident limit')
                        # Native venv startup may reset inherited flags. No
                        # scientific execution is permitted before the handshake.
                        confine(handles[pid],member_limit)
                        result['startupSettingsReasserted']+=1
                counters = memory(handles[pid])
                current += counters.working
                peaks[pid] = max(peaks.get(pid, 0), counters.peak)
            if protected and not result['workerHandshakeVerified']:
                result['workerHandshakeVerified']=True
                acknowledgement=Path(str(handshake_path)+'.ack')
                temporary=Path(str(acknowledgement)+'.pending')
                with temporary.open('x') as stream:
                    json.dump({'pid':protected,'memberBytes':member_limit},stream)
                    stream.flush();os.fsync(stream.fileno())
                os.replace(temporary,acknowledgement)
            controller_peak = memory(controller).peak
            bound = controller_peak + sum(peaks.values())
            result['sampledAggregatePeakBytes'] = max(result['sampledAggregatePeakBytes'], current)
            result['sumOfIndividualPeaksBytes'] = bound
            if bound > sampled_limit:
                result['stopReason'] = 'working-set limit'
            elif time.monotonic() - started >= seconds and ids:
                result['stopReason'] = 'elapsed-time limit'
            if not ids or result['stopReason']:
                break
            time.sleep(.01)
    except BaseException as error:
        if 'working-set maximum' in str(error): result['memberHardLimitsVerified'] = False
        result['stopReason'] = 'controller failure: ' + str(error)
    finally:
        # Kill the entire tree even if root exited while its worker stayed alive.
        if job:
            terminated = bool(kernel.TerminateJobObject(job, 124))
            deadline = time.monotonic() + 5
            try:
                while members() and time.monotonic() < deadline:
                    time.sleep(.01)
                result['terminationVerified'] = terminated and not members()
            except OSError:
                result['terminationVerified'] = False
        if process.process:
            # Also catches failure before the suspended root was assigned to job.
            if kernel.WaitForSingleObject(process.process, 0) != 0:
                kernel.TerminateProcess(process.process, 125)
                if kernel.WaitForSingleObject(process.process, 5000) != 0:
                    result['terminationVerified'] = False
        exits = {}
        if job:
            accounting = JobAccounting()
            if kernel.QueryInformationJobObject(job, 1, c.byref(accounting), c.sizeof(accounting), None):
                result['assignedProcesses'] = accounting.totalProcesses
                result['allAssignedProcessesObserved'] = accounting.totalProcesses == len(handles)
                if not result['allAssignedProcessesObserved']:
                    result['stopReason'] = 'Unobserved job member; memory claim incomplete'
        for pid, handle in handles.items():
            # Exit codes can become available before the process handle is signalled.
            # Keep each identity handle until termination is conclusively complete.
            if kernel.WaitForSingleObject(handle, 5000) != 0:
                result['allProcessHandlesSignalled'] = False
                result['terminationVerified'] = False
            try:
                counters = memory(handle)
                peaks[pid] = max(peaks.get(pid, 0), counters.peak)
            except OSError:
                result['finalMemoryCountersComplete'] = False
            value = w.DWORD()
            if not kernel.GetExitCodeProcess(handle, c.byref(value)):
                result['terminationVerified'] = False
            exits[str(pid)] = value.value
            if value.value == 259:
                result['terminationVerified'] = False
            kernel.CloseHandle(handle)
        result['rootPid'] = process.pid
        result['exitCodes'] = exits
        result['memberPeaksBytes'] = {str(k): v for k, v in peaks.items()}
        result['sumOfIndividualPeaksBytes'] = memory(controller).peak + sum(peaks.values())
        if result['sumOfIndividualPeaksBytes'] > sampled_limit and not result['stopReason']:
            result['stopReason'] = 'working-set limit (final peak counters)'
        if process.thread: kernel.CloseHandle(process.thread)
        if job: kernel.CloseHandle(job)
        result['elapsedSeconds'] = time.monotonic() - started
        if result['elapsedSeconds']>seconds and not result['stopReason']:
            result['stopReason']='elapsed-time limit including cleanup'
        result['success'] = (result['terminationVerified'] and not result['stopReason']
                             and result['allAssignedProcessesObserved']
                             and result['finalMemoryCountersComplete']
                             and bool(exits) and all(code == 0 for code in exits.values()))
        for key, value in previous_environment.items():
            if value is None: os.environ.pop(key,None)
            else: os.environ[key] = value
        # All job handles are closed and the environment restored before this
        # failure-safe publication. A refused receipt must never leave a worker.
        body=(json.dumps(result, indent=2)+'\n').encode('utf-8')
        if len(body)>receipt_byte_limit:raise RuntimeError('Controller receipt reservation exceeded')
        if storage_root is not None:
            size=sum(p.stat().st_size for p in Path(storage_root).rglob('*') if p.is_file())
            if size+len(body)>storage_limit:raise RuntimeError('Controller receipt scratch reservation exceeded')
        temporary=receipt_path.with_name(receipt_path.name+'.pending')
        with temporary.open('xb') as stream:
            if stream.write(body)!=len(body):raise OSError('Short controller receipt write')
            stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,receipt_path)
    return result
