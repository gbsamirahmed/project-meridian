"""Windows limits for this process only; no system settings or child processes."""
import ctypes
from ctypes import wintypes
import os


def confine_process(working_set=512*1024**2, private_commit=384*1024**2):
    controller_limit=os.environ.get('MERIDIAN_GUARD_MEMBER_BYTES')
    if controller_limit and working_set>int(controller_limit):
        raise RuntimeError('Cannot override controller-enforced working-set limit')
    if os.name != 'nt':
        raise RuntimeError('The reviewed hard resource guard requires Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    handle_type = wintypes.HANDLE
    size_type = ctypes.c_size_t
    class Basic(ctypes.Structure):
        _fields_ = [('processTime', ctypes.c_longlong), ('jobTime', ctypes.c_longlong),
            ('flags', wintypes.DWORD), ('minimum', size_type), ('maximum', size_type),
            ('active', wintypes.DWORD), ('affinity', size_type),
            ('priority', wintypes.DWORD), ('scheduling', wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in
            ('reads', 'writes', 'other', 'readBytes', 'writeBytes', 'otherBytes')]
    class Extended(ctypes.Structure):
        _fields_ = [('basic', Basic), ('io', IO), ('processMemory', size_type),
            ('jobMemory', size_type), ('peakProcess', size_type), ('peakJob', size_type)]
    kernel.GetCurrentProcess.restype = handle_type
    process = kernel.GetCurrentProcess()
    class Counters(ctypes.Structure):
        _fields_ = [('cb',wintypes.DWORD),('faults',wintypes.DWORD)] + [
            (name,size_type) for name in ('peak','working','pagedPeak','paged',
                'nonpagedPeak','nonpaged','pagefile','pagefilePeak')]
    psapi = ctypes.WinDLL('psapi',use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [handle_type,ctypes.c_void_p,wintypes.DWORD]
    counters = Counters();counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(process,ctypes.byref(counters),counters.cb):
        raise RuntimeError('Cannot inspect baseline private committed memory')
    if counters.pagefile+16*1024**2 > private_commit:
        raise RuntimeError('Existing private commit leaves no guarded headroom; start with one-thread environment before importing NumPy')
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = handle_type
    job = kernel.CreateJobObjectW(None, None)
    kernel.SetInformationJobObject.argtypes = [handle_type, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [handle_type, handle_type]
    info = Extended()
    info.basic.flags = 0x100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY, private committed bytes.
    info.processMemory = private_commit
    if not job or not kernel.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
        raise RuntimeError('Cannot establish private-commit allocation guard')
    if not kernel.AssignProcessToJobObject(job, process):
        raise RuntimeError('Cannot join bounded process job; no unconfined fallback')
    kernel.SetProcessWorkingSetSizeEx.argtypes = [handle_type, size_type, size_type, wintypes.DWORD]
    # Hard maximum constrains resident pages; the tighter job commit cap also limits
    # private allocations. Neither claims battery or total machine-memory isolation.
    if not kernel.SetProcessWorkingSetSizeEx(process, 1*1024**2, working_set, 0x4):
        raise RuntimeError('Cannot establish hard resident working-set maximum')
    kernel.GetProcessWorkingSetSizeEx.argtypes = [handle_type, ctypes.POINTER(size_type),
        ctypes.POINTER(size_type), ctypes.POINTER(wintypes.DWORD)]
    minimum, maximum, flags = size_type(), size_type(), wintypes.DWORD()
    if not kernel.GetProcessWorkingSetSizeEx(process, ctypes.byref(minimum),
            ctypes.byref(maximum), ctypes.byref(flags)):
        raise RuntimeError('Cannot verify working-set maximum')
    if maximum.value != working_set or not flags.value & 0x4:
        raise RuntimeError('Hard working-set maximum not verified')
    # Keep the handle for this process lifetime. No named job or child process exists.
    return {'workingSetMaximum': maximum.value, 'workingSetFlags': flags.value,
            'privateCommitMaximum': private_commit, 'baselinePrivateCommit':counters.pagefile,
            'jobHandle': job}
