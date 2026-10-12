"""Watch the single pilot process; stop at the approved process/time ceilings."""
import ctypes
import subprocess
import sys
import time
from pathlib import Path

class Counters(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
        (name, ctypes.c_size_t) for name in ("peak", "working", "pagedPeak", "paged",
            "nonpagedPeak", "nonpaged", "pagefile", "pagefilePeak")]

if __name__ == "__main__":
    start = time.monotonic()
    process = subprocess.Popen([sys.executable, "-B", str(Path(__file__).with_name("pilot.py")), *sys.argv[1:]])
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.restype = ctypes.c_void_p
    handle = kernel.OpenProcess(0x0410, False, process.pid)
    if not handle:
        process.terminate()
        raise RuntimeError("Cannot supervise the approved resource ceiling")
    reason = None
    peak = 0
    try:
        while process.poll() is None:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
            if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                reason = "Resource monitor unavailable"
                break
            peak = max(peak, counters.peak)
            if peak > 512*1024**2 or time.monotonic()-start > 1195:
                reason = "Working-set/time ceiling reached"
                break
            time.sleep(.1)
        if reason:
            process.terminate()
        result = process.wait()
    finally:
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle(handle)
    print({"supervisedPeakWorkingSetBytes": peak, "elapsedSeconds": time.monotonic()-start,
           "exitCode": result, "stopReason": reason}, flush=True)
    sys.exit(result if not reason else 2)
