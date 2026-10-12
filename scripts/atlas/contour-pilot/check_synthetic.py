"""Repeat focused controls with measured, owned temporary storage; no DEM inputs."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[name] = '1'
import argparse
import json
from pathlib import Path
import tempfile
import time
import unittest

from resource_guard import confine_process
from windowed import Ledger
from pilot import memory
from staged_store import StageStore


def check(output):
    if output.exists():raise ValueError('Fresh synthetic check directory required')
    output.mkdir()
    temporary = output/'temporary';temporary.mkdir()
    assert temporary.resolve().is_relative_to(output.resolve())
    tempfile.tempdir = str(temporary)
    controls = output/'worker-controls';controls.mkdir()
    os.environ['MERIDIAN_RECOVERY_CONTROLS'] = str(controls)
    os.environ['MERIDIAN_TEST_PYTHON'] = __import__('sys').executable
    guard = confine_process();guard.pop('jobHandle')
    original = Ledger.append
    original_reconcile=StageStore.reconcile
    record = {'maxTemporaryFileBytes':0,'storedVertexWritesDuringChecks':0}
    def measured(self,stream,value,vertices=0):
        result = original(self,stream,value,vertices)
        size = sum(p.stat().st_size for p in temporary.rglob('*') if p.is_file())
        record['maxTemporaryFileBytes'] = max(record['maxTemporaryFileBytes'],size)
        record['storedVertexWritesDuringChecks'] += vertices
        return result
    Ledger.append = measured
    def measured_reconcile(self):
        value=original_reconcile(self)
        record['adapterPeakOwnedRootBytes']=max(record.get('adapterPeakOwnedRootBytes',0),value)
        record['adapterPeakReservedCoordinates']=max(record.get('adapterPeakReservedCoordinates',0),self.geometry.workspace_peak)
        record['adapterObservedGeneratedCoordinates']=max(record.get('adapterObservedGeneratedCoordinates',0),self.observed_generated_peak)
        size=sum(p.stat().st_size for p in temporary.rglob('*') if p.is_file())
        record['maxTemporaryFileBytes']=max(record['maxTemporaryFileBytes'],size)
        return value
    StageStore.reconcile=measured_reconcile
    started = time.monotonic()
    try:
        result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover(
            str(Path(__file__).parent),pattern='test_*.py'))
    finally:
        Ledger.append = original
        StageStore.reconcile=original_reconcile
    record.update(tests=result.testsRun,passed=result.wasSuccessful(),elapsedSeconds=time.monotonic()-started,
        peakWorkingSetBytes=memory()[1],guard=guard,scientificInputsOpened=0,requests=0,
        childProcesses='contained synthetic workers; see worker-controls receipts')
    record['retainedControlBytes'] = sum(p.stat().st_size for p in controls.rglob('*') if p.is_file())
    with (output/'receipt.json').open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record),flush=True)
    if not result.wasSuccessful():raise RuntimeError('Synthetic controls failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    check(parser.parse_args().output)
