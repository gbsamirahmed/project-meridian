"""Disposable synthetic stage histories. Never loads a genuine raster/input."""
from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from staged_store import Budget,StageStore,digest,encode
from staged_continuation import Continuation,Permit,MISSING,SWISS,check_shape_capacity
from accounting import AccountingLimit
from windowed import Ledger,extract,finish_product
from test_windowed import ArrayReader


class SyntheticSources:
    scope='synthetic-test'
    memory_reader=None
    def __init__(self):self.calls=[];self.changed=None
    def preflight(self,budget):check_shape_capacity((33,33),budget)
    @contextmanager
    def reader(self,name):
        self.calls.append(name)
        rows,cols=np.indices((33,33),dtype=float)
        yield ArrayReader(rows+cols+(1 if self.changed==name else 0))
    def metadata(self,name):
        return {'scope':self.scope,'core':[1000,2000,1032,2032],'geographic':False,
            'syntheticSource':name,'units':'m','verticalReference':'synthetic only'}
    def height_diagnostic(self,store):return {'scope':self.scope,'notScientificEvidence':True}


class RingSources(SyntheticSources):
    def preflight(self,budget):check_shape_capacity((521,521),budget)
    @contextmanager
    def reader(self,name):
        self.calls.append(name)
        rows,cols=np.indices((521,521),dtype=float)
        yield ArrayReader((rows-256)**2+(cols-256)**2)
    def metadata(self,name):
        result=super().metadata(name);result['core']=[1000,2000,1520,2520]
        return result


def fixtures(root,sources=None,levels=(20,30)):
    sources=sources or SyntheticSources();old=root/'history';old.mkdir()
    canonical={};inventory=[]
    ledger=Ledger(root)
    for name in SWISS:
        with sources.reader(name) as reader:
            extract(reader,levels,old/(name+'-fragments'),ledger)
        stats=finish_product(old/(name+'-fragments'),levels,old/name,ledger)
        (old/name/'manifest.json').write_bytes(encode({'id':name,'meaning':sources.metadata(name),'geometry':stats}))
        canonical[name]=str((old/name).relative_to(root))
    for path in root.rglob('*'):
        if not path.is_file():continue
        vertices=0
        if path.suffix=='.ndjson':vertices=sum(len(json.loads(body)['coordinates']) for body in path.open('rb'))
        role='final' if path.parent.name in SWISS and vertices else ('intermediate' if vertices else 'control')
        inventory.append({'path':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':digest(path),
                          'vertices':vertices,'role':role})
    sources.calls.clear()
    budget=Budget(10000,30000,50000,20000,50000,20000,20000,2_000_000,512*1024**2,60,8192)
    charged=sum(e['vertices'] for e in inventory)+7
    return sources,levels,canonical,inventory,budget,charged


class StageTests(unittest.TestCase):
    def test_two_gated_stages_seven_new_derivations_and_immutable_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,levels,canonical,inventory,budget,charged=fixtures(root)
            runner=Continuation(s,budget,levels)
            first=runner.stage1(Permit(s.scope,1,True,budget.sha256),root,root/'stage1',inventory,charged,canonical)
            self.assertEqual(s.calls,list(MISSING))
            with self.assertRaises(PermissionError):runner.stage2(Permit(s.scope,1,True,budget.sha256),root,root/'stage2',first)
            final=runner.stage2(Permit(s.scope,2,True,budget.sha256,digest(first)),root,root/'stage2',first)
            self.assertEqual(s.calls,list(MISSING)+list(MISSING)+list(SWISS))
            result=json.loads(final.read_text());self.assertEqual(result['state'],'complete-replay-comparisons')
            self.assertFalse(list((root/'stage2').rglob('*.ndjson')))
            self.assertGreater(result['resources']['geometry']['cumulativeWrittenVertices'],charged)
            for e in inventory:self.assertEqual(digest(root/e['path']),e['sha256'])
            self.assertLess(result['resources']['geometry']['peakTemporaryVertices'],budget.temporary)

    def test_no_approval_cannot_call_source_or_create_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,l,c,i,b,w=fixtures(root)
            with self.assertRaises(PermissionError):Continuation(s,b,l).stage1(Permit(s.scope,1,False,b.sha256),root,root/'refused',i,w,c)
            self.assertEqual(s.calls,[]);self.assertFalse((root/'refused').exists())

    def test_profile_or_checkpoint_change_cannot_reset_shared_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,l,c,i,b,w=fixtures(root);runner=Continuation(s,b,l)
            first=runner.stage1(Permit(s.scope,1,True,b.sha256),root,root/'first',i,w,c)
            with self.assertRaises(PermissionError):runner.stage2(Permit(s.scope,2,True,b.sha256,'bad'),root,root/'second',first)
            larger=replace(b,written=b.written+1)
            with self.assertRaises(PermissionError):Continuation(s,larger,l).stage2(Permit(s.scope,2,True,b.sha256,digest(first)),root,root/'second',first)

    def test_mismatch_keeps_fresh_evidence_and_marks_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,l,c,i,b,w=fixtures(root);runner=Continuation(s,b,l)
            first=runner.stage1(Permit(s.scope,1,True,b.sha256),root,root/'first',i,w,c)
            s.changed=MISSING[0]
            with self.assertRaisesRegex(ValueError,'Fresh geometry differs'):
                runner.stage2(Permit(s.scope,2,True,b.sha256,digest(first)),root,root/'second',first)
            self.assertTrue(list((root/'second').rglob('*.ndjson')))
            self.assertEqual(json.loads((root/'second/incomplete.json').read_text())['state'],'incomplete')
            self.assertFalse((root/'second/completion.json').exists())

    def test_rejected_simplification_is_never_called(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,l,c,i,b,w=fixtures(root)
            with (patch('rerun.global_simplification',side_effect=AssertionError('forbidden')),
                  patch('windowed.simplification_check',side_effect=AssertionError('forbidden'))):
                Continuation(s,b,l).stage1(Permit(s.scope,1,True,b.sha256),root,root/'first',i,w,c)

    def test_native_allocation_preflight_refuses_200k_profile_without_data(self):
        with self.assertRaisesRegex(ValueError,'262144'):
            check_shape_capacity((1000,1000),Budget(1,1,1,1,1,1,200000,100000,512*1024**2,1200,1000))

    def test_genuine_binding_refuses_proposal_before_any_raster_import(self):
        from riffelhorn_sources import RiffelhornSources
        from supervise_stage import inspect
        profile=json.loads(Path(__file__).with_name('staged-profile-proposal.json').read_text())
        self.assertFalse(inspect(profile)['readyToAttempt'])
        with patch.dict('os.environ',{'MERIDIAN_GUARD_MEMBER_BYTES':str(128*1024**2)}):
            with self.assertRaisesRegex(ValueError,'262144'):
                RiffelhornSources(Path('nonexistent-synthetic-source-root')).preflight(Budget(**profile['budget']))

    def test_worker_cap_change_refused_before_stage2_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,l,c,i,b,w=fixtures(root);runner=Continuation(s,b,l)
            first=runner.stage1(Permit(s.scope,1,True,b.sha256),root,root/'one',i,w,c)
            with patch.dict('os.environ',{'MERIDIAN_GUARD_MEMBER_BYTES':str(128*1024**2)}):
                with self.assertRaisesRegex(PermissionError,'memory allocation changed'):
                    runner.stage2(Permit(s.scope,2,True,b.sha256,digest(first)),root,root/'two',first)
            self.assertFalse((root/'two').exists())

    def test_closed_contours_cross_extraction_and_delivery_partitions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,l,c,i,b,w=fixtures(root,RingSources(),(5000,10000))
            # Explicit synthetic-only capacity to exercise the conservative
            # preflight. This does not change the proposed 200k genuine ceiling.
            b=replace(b,temporary=300000,scratch=8_000_000,seconds=120)
            runner=Continuation(s,b,l)
            first=runner.stage1(Permit(s.scope,1,True,b.sha256),root,root/'one',i,w,c)
            final=runner.stage2(Permit(s.scope,2,True,b.sha256,digest(first)),root,root/'two',first)
            for product in json.loads(final.read_text())['results'].values():
                self.assertGreater(product['geometry']['closedLines'],0)
                self.assertGreater(product['extraction']['windows'],1)

    def test_same_source_replay_hashes_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s,l,c,i,b,w=fixtures(root);runner=Continuation(s,b,l)
            first=runner.stage1(Permit(s.scope,1,True,b.sha256),root,root/'one',i,w,c)
            original=json.loads(first.read_text())
            final=runner.stage2(Permit(s.scope,2,True,b.sha256,digest(first)),root,root/'two',first)
            replay=json.loads(final.read_text())
            for name in MISSING:
                self.assertEqual(original['products'][name]['geometry']['levels'],replay['results'][name]['geometry']['levels'])


class StoreTests(unittest.TestCase):
    def store(self,root,**change):
        old=root/'old.ndjson';old.write_bytes(encode({'coordinates':[[0,0],[1,1]]}))
        budget=Budget(100,100,100,100,100,100,100,100000,512*1024**2,60,1000)
        budget=replace(budget,**change)
        entry={'path':'old.ndjson','bytes':old.stat().st_size,'sha256':digest(old),'vertices':2,'role':'final'}
        return StageStore(root,root/'new',budget,[entry],written=9)

    def test_seed_counts_and_refusals_before_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root,stored=3)
            self.assertEqual(store.geometry.written,9)
            self.assertEqual(store.geometry.snapshot()['persistentVerticesByRole']['final'],2)
            with store.open_geometry(store.execution/'candidate','diagnostic',True) as stream:
                with self.assertRaises(AccountingLimit):store.append(stream,{'coordinates':[[0,0],[1,1]]},2)
            self.assertEqual((store.execution/'candidate').stat().st_size,0)

    def test_retirement_reconciles_bytes_without_refunding_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root)
            path=store.execution/'candidate'
            with store.open_geometry(path,'diagnostic',True) as stream:store.append(stream,{'coordinates':[[0,0],[1,1]]},2)
            charged=store.geometry.written;size=path.stat().st_size
            store.retire(path,expected_hash=digest(path),receipt=store.execution/'verified.json')
            self.assertEqual(store.geometry.written,charged)
            self.assertFalse(path.exists());self.assertEqual(store.bytes,sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))
            self.assertEqual(json.loads((store.execution/'verified.json').read_text())['state'],'retired')

    def test_immutable_and_outside_paths_cannot_be_retired(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root)
            with self.assertRaises(ValueError):store.retire(root/'old.ndjson',expected_hash=digest(root/'old.ndjson'),receipt=store.execution/'receipt')
            with self.assertRaises(ValueError):store.open_geometry(root.parent/'outside')

    def test_failed_atomic_update_preserves_previous_receipt_and_geometry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root);receipt=store.execution/'receipt.json'
            store.atomic_json(receipt,{'state':'incomplete'})
            path=store.execution/'candidate'
            with store.open_geometry(path,'diagnostic',True) as stream:store.append(stream,{'coordinates':[[0,0],[1,1]]},2)
            with patch('staged_store.os.replace',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):store.retire(path,expected_hash=digest(path),receipt=receipt)
            self.assertTrue(path.exists());self.assertEqual(json.loads(receipt.read_text())['state'],'incomplete')
            self.assertTrue(receipt.with_name(receipt.name+'.pending').exists())

    def test_changed_or_unregistered_file_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root)
            (store.execution/'unexpected').write_text('x')
            with self.assertRaises(AccountingLimit):store.check()
            self.assertTrue(store.poisoned)

    def test_temporary_stage_and_cumulative_limits_are_shared(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root,written=10,loaded=1,temporary=2)
            with store.workspace(2):
                with self.assertRaises(AccountingLimit):
                    with store.workspace(1):pass
            with self.assertRaises(AccountingLimit):store.geometry.processed('loaded',2)
            with store.open_geometry(store.execution/'refused') as stream:
                with self.assertRaises(AccountingLimit):store.append(stream,{'coordinates':[[0,0],[1,1]]},2)
            self.assertEqual(store.geometry.written,9)

    def test_receipt_space_is_reserved_before_geometry_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root,scratch=1050)
            with store.open_geometry(store.execution/'refused') as stream:
                with self.assertRaises(AccountingLimit):store.append(stream,{'coordinates':[[0,0],[1,1],[2,2]]},3)
            self.assertEqual((store.execution/'refused').stat().st_size,0)

    def test_shared_clock_and_memory_reservations_refuse_before_allocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root)
            store.prior_elapsed=store.budget.seconds
            with self.assertRaisesRegex(AccountingLimit,'time limit'):store.check()
            store.prior_elapsed=0
            store.memory_reader=lambda:(store.worker_ceiling-10,store.worker_ceiling-10)
            with self.assertRaisesRegex(AccountingLimit,'memory/preflight'):
                with store.workspace(1):pass

    def test_seed_hash_mismatch_does_not_create_new_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);store=self.store(root)
            entry=store.sealed_inventory()[0];(root/entry['path']).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Immutable evidence changed'):
                StageStore(root,root/'refused',store.budget,[entry],written=9)
            self.assertFalse((root/'refused').exists())
