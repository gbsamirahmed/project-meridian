"""Two serial lazy 4000-square synthetic runs; never opens a scientific input."""
import argparse
import ctypes
import gc
import inspect
import json
import os
from pathlib import Path
import tempfile
import time
import tracemalloc
import unittest

for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
os.environ['PROJ_NETWORK'] = 'OFF'
os.environ['GDAL_PAM_ENABLED'] = 'NO'

from resource_guard import confine_process
from pilot import canonical, digest, memory, block_mean, smooth
from windowed import Grid, Ledger, extract, finish_product
import contourpy
import numpy as np


class SyntheticNative:
    shape = (4000, 4000)
    def read(self, row, r1, col, c1):
        rows = np.arange(row, r1, dtype=float)[:, None]
        cols = np.arange(col, c1, dtype=float)[None, :]
        z = (2180+rows*.02+cols*.015+240*np.exp(-((rows-2000)**2+
            (cols-2000)**2)/1_300_000)+8*np.sin(cols/211)*np.cos(rows/197)).astype(np.float32)
        return Grid(2624000+.25+np.arange(col,c1)*.5,
                    1091000+.25+np.arange(row,r1)*.5,z,row,col)


class CoarseReader:
    """Same aligned block means everywhere; filter halo is not contour overlap."""
    shape = (1000, 1000)
    def __init__(self, native, smoothing=False, diagnostic=False):
        self.native, self.smoothing, self.diagnostic = native, smoothing, diagnostic

    def read(self, row, r1, col, c1):
        halo = 3 if self.smoothing else 0
        a,b,c,d = row-halo,r1+halo,col-halo,c1+halo
        aa,bb,cc,dd = max(a,0),min(b,1000),max(c,0),min(d,1000)
        raw = self.native.read(aa*4,bb*4,cc*4,dd*4).z
        averaged = block_mean(raw)
        if halo:
            padded = np.full((b-a,d-c),np.nan)
            padded[aa-a:bb-a,cc-c:dd-c] = averaged
            values = smooth(padded)[halo:-halo,halo:-halo]
        else:
            values = averaged
        return Grid(2624001+np.arange(col,c1)*2.,1091001+np.arange(row,r1)*2.,values,row,col)


def diagnosis():
    """Scaled allocation-stage measurements, not a replay of the genuine spike."""
    n = 1024
    stages = []
    tracemalloc.start()
    def record(label):
        current,peak = memory()
        heap,heap_peak = tracemalloc.get_traced_memory()
        stages.append({'stage':label,'workingSetBytes':current,'processPeakBytes':peak,
                       'tracedCurrentBytes':heap,'tracedPeakBytes':heap_peak})
    record('baseline')
    z = np.full((n,n),2500.,dtype=np.float32)
    record('float32 input')
    flipped = z[::-1].copy()
    record('orientation copy retained')
    z2 = block_mean(z)
    record('2 m block mean retained')
    masked = np.ma.masked_invalid(flipped)
    record('explicit masked-invalid copy retained')
    generator = contourpy.contour_generator(x=np.arange(n,dtype=float),y=np.arange(n,dtype=float),
        z=masked,name='serial',line_type='Separate',z_interp='Linear',
        corner_mask=False,quad_as_tri=False,thread_count=1)
    record('ContourPy float64 height and full XY meshes')
    valid = np.isfinite(flipped)
    unused_min = flipped[valid].min()
    record('finite mask and advanced-index statistic')
    del generator,valid,masked,z2,flipped,z
    gc.collect()
    record('released Python references')
    tracemalloc.stop()
    source = inspect.getsource(contourpy.contour_generator)+inspect.getsource(contourpy._remove_z_mask)
    return {'syntheticSide':n,'stages':stages,'contourpySourceSha256':
        __import__('hashlib').sha256(source.encode()).hexdigest(),
        'known4000SquareAllocationBytes':{'inputFloat32':64_000_000,'orientationCopyFloat32':64_000_000,
            'convertedHeightFloat64':128_000_000,'twoInternalCoordinateMeshesFloat64':256_000_000,
            'oneBooleanMask':16_000_000,'coarseFloat64Height':8_000_000},
        'qualification':'Scaled current/peak measurements and exact array byte counts; no full-size legacy reproduction or attribution of all C++ caches.'}


def run(output):
    output = Path(output)
    if output.exists():
        raise ValueError('Fresh synthetic output directory required')
    output.mkdir(parents=True)
    ledger = Ledger(output)
    guard = confine_process()
    guard.pop('jobHandle')
    # Fail-fast allocation test: this commit exceeds the stricter 384 MiB job cap.
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.VirtualAlloc.argtypes = [ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong,ctypes.c_ulong]
    kernel.VirtualAlloc.restype = ctypes.c_void_p
    allocation = kernel.VirtualAlloc(None,512*1024**2,0x3000,0x04)
    if allocation:
        kernel.VirtualFree.argtypes = [ctypes.c_void_p,ctypes.c_size_t,ctypes.c_ulong]
        kernel.VirtualFree(allocation,0,0x8000)
        raise RuntimeError('Private allocation guard did not reject over-limit commit')
    guard['overLimitPrivateCommitRejected'] = True
    ledger.json(output/'diagnosis.json',diagnosis())
    temporary = output/'test-temporary'
    temporary.mkdir()
    tempfile.tempdir = str(temporary)
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_windowed.py')
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError('Synthetic correctness controls failed; large runs not permitted')
    ledger.check()
    levels = list(range(2000,3201,10))
    receipts = []
    for index in (1,2):
        folder = output/f'run-{index}'
        folder.mkdir()
        native = SyntheticNative()
        products = {}
        for name,reader in (('native-0.5m',native),('strict-2m',CoarseReader(native)),
                            ('smoothed-2m',CoarseReader(native,smoothing=True))):
            fragments = folder/f'{name}-fragments'
            extraction = extract(reader,levels,fragments,ledger)
            geometry = finish_product(fragments,levels,folder/name,ledger)
            products[name] = {'extraction':extraction,'geometry':geometry,
                'fragmentHashes':{p.name:digest(p) for p in sorted(fragments.glob('*.ndjson'))}}
            print(index,name,'peak',ledger.peak,'stored vertices',ledger.vertices,flush=True)
        receipt = {'synthetic':True,'shape':[4000,4000],'levels':levels,'products':products,
                   'methodHashes':{name:digest(Path(__file__).with_name(name)) for name in
                        ('windowed.py','resource_guard.py','synthetic_recovery.py')}}
        ledger.json(folder/'receipt.json',receipt)
        receipts.append(receipt)
    if canonical(receipts[0]) != canonical(receipts[1]):
        raise RuntimeError('Two synthetic runs are not deterministic')
    ledger.check()
    summary = {'status':'synthetic recovery passed','testsPassed':result.testsRun,
        'twoRunReceiptsIdentical':True,'workingSetPeakBytes':ledger.peak,
        'elapsedSeconds':time.monotonic()-ledger.start,'storedVertices':ledger.vertices,
        'bytesBeforeFinalReceipt':ledger.bytes,'maximumContourWindowSamples':ledger.max_window_samples,
        'windowsMaximumSide':257,'guard':guard,'requests':0,'scientificInputsOpened':0,
        'childProcesses':0,'threads':1,'products':list(receipts[0]['products']),
        'receiptSha256':__import__('hashlib').sha256(canonical(receipts[0])).hexdigest(),
        'limitations':'Synthetic density, not genuine Riffelhorn success or worldwide performance. Real source adapters/transformation/delivery remain gated.'}
    ledger.json(output/'completion.json',summary)
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    run(parser.parse_args().output)
