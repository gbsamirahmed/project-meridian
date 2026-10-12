"""Actual worker/tree termination controls, never genuine processing."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from worker_supervision import supervise, api


class SupervisionTests(unittest.TestCase):
    def run_worker(self, mode, **limits):
        base = Path(os.environ['MERIDIAN_RECOVERY_CONTROLS'])
        folder = base/mode; folder.mkdir(exist_ok=False)
        command = [os.environ.get('MERIDIAN_TEST_PYTHON',sys.executable),'-B',
                   str(Path(__file__).with_name('synthetic_worker.py')),mode,str(folder)]
        receipt = supervise(command, folder/'supervision.json',handshake_path=folder/'lock.json', **limits)
        self.assertTrue(receipt['terminationVerified'], receipt)
        self.assertTrue(receipt['allProcessHandlesSignalled'],receipt)
        self.assertTrue(receipt['allAssignedProcessesObserved'],receipt)
        self.assertLess(receipt['elapsedSeconds'],8)
        for pid, code in receipt['exitCodes'].items():
            self.assertNotEqual(code,259)
        return folder,receipt

    def test_venv_actual_worker_is_observed_and_finishes(self):
        folder,r = self.run_worker('normal',seconds=5)
        worker = json.loads((folder/'normal-worker.json').read_text())
        self.assertTrue(r['success'],r)
        self.assertIn(str(worker['pid']),r['memberPeaksBytes'])
        self.assertEqual(worker['numericalThreads'],['1','1','1'])
        # The configured venv launcher and actual worker are deliberately different.
        self.assertNotEqual(worker['pid'],r['rootPid'])

    def test_memory_exceedance_terminates_actual_worker(self):
        kernel,memory = api()
        threshold = memory(kernel.GetCurrentProcess()).peak + 35*1024**2
        folder,r = self.run_worker('memory',seconds=5,sampled_limit=threshold)
        self.assertFalse(r['success'])
        self.assertIn('working-set limit',r['stopReason'])
        worker = json.loads((folder/'memory-worker.json').read_text())
        self.assertIn(str(worker['pid']),r['exitCodes'])

    def test_timeout_kills_descendant_after_launcher_and_root_exit(self):
        folder,r = self.run_worker('tree',seconds=1,member_limit=96*1024**2,max_processes=4)
        self.assertEqual(r['stopReason'],'elapsed-time limit')
        child = json.loads((folder/'child-worker.json').read_text())
        self.assertIn(str(child['pid']),r['exitCodes'])
        self.assertGreaterEqual(r['maxJobProcesses'],2)

    def test_job_allocation_refusal_is_failure_not_success(self):
        folder,r = self.run_worker('commit',seconds=5,commit_limit=48*1024**2)
        self.assertFalse(r['success'])
        self.assertTrue((folder/'commit-refused.txt').exists())

    def test_worker_failure_preserves_partial_output(self):
        folder,r = self.run_worker('failure',seconds=5)
        self.assertFalse(r['success'])
        self.assertEqual((folder/'partial.ndjson').read_text(),'{"unfinished":')

    def test_failed_termination_signal_is_not_reported_as_verified(self):
        kernel,memory = api()
        class FailedTermination:
            def __getattr__(self,name): return getattr(kernel,name)
            def TerminateJobObject(self,job,code):
                kernel.TerminateJobObject(job,code)
                return False
        base = Path(os.environ['MERIDIAN_RECOVERY_CONTROLS'])/'failed-termination'
        base.mkdir()
        command = [os.environ['MERIDIAN_TEST_PYTHON'],'-B',
                   str(Path(__file__).with_name('synthetic_worker.py')),'normal',str(base)]
        with patch('worker_supervision.api',return_value=(FailedTermination(),memory)):
            result = supervise(command,base/'supervision.json',seconds=.15,handshake_path=base/'lock.json')
        self.assertFalse(result['terminationVerified'])
        self.assertFalse(result['success'])
        self.assertTrue(result['allProcessHandlesSignalled'])

    def test_resident_reset_after_lock_terminates_worker(self):
        folder,result=self.run_worker('override',seconds=5)
        self.assertTrue(result['residentOverrideDetected'])
        self.assertFalse(result['success'])
        self.assertTrue(result['workerHandshakeVerified'])

    def test_worker_guard_cannot_raise_controller_ceiling(self):
        folder,result=self.run_worker('guard-refusal',seconds=5)
        self.assertTrue((folder/'guard-refused.txt').exists())
        self.assertFalse(result['success'])
        self.assertEqual(result['memberWorkingSetLimitBytes'],128*1024**2)

    def test_receipt_refusal_happens_after_worker_cleanup(self):
        base=Path(os.environ['MERIDIAN_RECOVERY_CONTROLS'])/'receipt-refusal';base.mkdir()
        command=[os.environ['MERIDIAN_TEST_PYTHON'],'-B',
                 str(Path(__file__).with_name('synthetic_worker.py')),'normal',str(base)]
        with self.assertRaisesRegex(RuntimeError,'receipt reservation'):
            supervise(command,base/'supervision.json',seconds=5,handshake_path=base/'lock.json',receipt_byte_limit=1)
        worker=json.loads((base/'normal-worker.json').read_text())
        kernel,_=api();handle=kernel.OpenProcess(0x100000,False,worker['pid'])
        if handle:
            try:self.assertEqual(kernel.WaitForSingleObject(handle,0),0)
            finally:kernel.CloseHandle(handle)
        self.assertFalse((base/'supervision.json').exists())

