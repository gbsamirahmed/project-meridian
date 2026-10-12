"""Offline accounting/topology controls; no DEMs or scientific generation."""
import tempfile
from pathlib import Path
import unittest
from shapely.geometry import LineString, box
from shapely.ops import unary_union
from accounting import GeometryAccount, AccountingLimit
from topology_generalisation import conservative_simplify, validate_family


class ShortWrite:
    def __init__(self, stream, rollback=True):
        self.stream = stream; self.name = stream.name; self.rollback = rollback
    def __getattr__(self, name): return getattr(self.stream, name)
    def write(self, body): return self.stream.write(body[:2])
    def truncate(self, size):
        if not self.rollback: raise OSError('Injected rollback failure')
        return self.stream.truncate(size)


class AccountingTests(unittest.TestCase):
    def test_final_and_fragments_are_distinct_but_both_charged(self):
        with tempfile.TemporaryDirectory() as tmp:
            account = GeometryAccount(10)
            for name, role, count in [('fragment','intermediate',4), ('master','final',3), ('probe','control',1)]:
                with (Path(tmp)/name).open('xb') as f: account.append(f,b'{}\n',count,role)
            result = account.snapshot()
            self.assertEqual(result['persistentVerticesByRole'], {'final':3,'intermediate':4,'control':1,'diagnostic':0})
            self.assertEqual(result['cumulativeWrittenVertices'],8)
            (Path(tmp)/'probe').unlink(); account.release_deleted(Path(tmp)/'probe')
            self.assertEqual(account.written,8)
            self.assertEqual(account.snapshot()['peakPersistentVertices'],8)

    def test_rejected_fragment_does_not_charge_or_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            account = GeometryAccount(2)
            with (Path(tmp)/'fragment').open('xb') as f:
                with self.assertRaises(AccountingLimit): account.append(f,b'{}\n',3)
                self.assertEqual(f.tell(),0)
            self.assertEqual((account.written,account.attempted,account.rejected),(0,3,3))

    def test_partial_write_rollback_preserves_previous_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            account = GeometryAccount()
            with (Path(tmp)/'fragment').open('xb') as f:
                account.append(f,b'first\n',2)
                with self.assertRaises(OSError): account.append(ShortWrite(f),b'next\n',4)
            self.assertEqual((Path(tmp)/'fragment').read_bytes(),b'first\n')
            self.assertEqual((account.written,account.rolled_back),(2,4))

    def test_unrecoverable_write_poisons_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            account = GeometryAccount()
            with (Path(tmp)/'fragment').open('xb') as f:
                with self.assertRaises(OSError): account.append(ShortWrite(f,False),b'next\n',4)
                with self.assertRaises(AccountingLimit): account.append(f,b'ok\n',1)
            self.assertTrue(account.snapshot()['unreconciledPartialWrite'])

    def test_temporary_geometry_peak_and_release_on_exception(self):
        account = GeometryAccount(temporary_limit=10)
        with self.assertRaises(ValueError):
            with account.temporary(6):
                with account.temporary(4): raise ValueError('probe')
        self.assertEqual((account.workspace,account.workspace_peak),(0,10))
        with account.temporary(9):
            with self.assertRaises(AccountingLimit):
                with account.temporary(2): pass

    def test_release_requires_actual_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'owned'
            account = GeometryAccount()
            with p.open('xb') as f: account.append(f,b'{}\n',2)
            with self.assertRaises(AccountingLimit): account.release_deleted(p)

    def test_stage_counts_do_not_masquerade_as_retained_geometry(self):
        account = GeometryAccount()
        account.processed('extracted',12);account.processed('loaded',12);account.processed('loaded',12)
        self.assertEqual(account.snapshot()['processingVerticesByStage'],{'extracted':12,'loaded':24})
        self.assertEqual(account.written,0)

    def test_stage_gate_and_inherited_counter_are_explicit(self):
        account = GeometryAccount(work_limits={'extracted':3})
        account.written=7
        account.processed('extracted',3)
        with self.assertRaises(AccountingLimit): account.processed('extracted',1)
        self.assertEqual(account.snapshot()['unclassifiedInitialWrittenVertices'],7)
        self.assertEqual(account.processing['extracted'],3)

    def test_seeded_evidence_counts_against_storage_and_cannot_be_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp)/'old';old.write_bytes(b'old\n')
            account = GeometryAccount(persistent_limit=4,final_limit=2)
            account.seed_file(old,3,'intermediate')
            with (Path(tmp)/'new').open('xb') as f:
                with self.assertRaises(AccountingLimit): account.append(f,b'new\n',2,'final')
                self.assertEqual(f.tell(),0)
            with self.assertRaises(AccountingLimit): account.release_deleted(old)
            self.assertEqual(account.snapshot()['peakPersistentVertices'],3)

    def test_final_limit_is_independent_of_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            account = GeometryAccount(final_limit=2)
            with (Path(tmp)/'final').open('xb') as f:
                with self.assertRaises(AccountingLimit): account.append(f,b'{}\n',3,'final')
            self.assertEqual(account.written,0)

    def test_ledger_byte_refusal_records_preflight_vertices(self):
        from windowed import Ledger,LimitsReached
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Ledger(tmp,bytes_limit=1)
            with (Path(tmp)/'rejected').open('xb') as f:
                with self.assertRaises(LimitsReached):ledger.append(f,{'value':1},2)
            self.assertEqual(ledger.resource_counters()['writerPreflightRejectedVertices'],2)
            self.assertEqual(ledger.vertices,0)


class TopologyTests(unittest.TestCase):
    def test_new_crossing_is_rejected_even_when_each_line_is_simple(self):
        lines = [[(-2,0),(0,3),(2,0)],[(0,-.5),(0,.5)]]
        original = [LineString(line) for line in lines]
        bad = [line.simplify(4,preserve_topology=True) for line in original]
        self.assertFalse(validate_family(original,bad,4)[0])
        candidate, result = conservative_simplify(lines)
        self.assertTrue(validate_family(original,[LineString(line) for line in candidate],2)[0])

    def test_collinear_removal_retains_endpoints_and_shared_node(self):
        lines = [[(0,0),(1,0),(2,0)],[(2,0),(2,1),(2,2)]]
        candidate,result = conservative_simplify(lines)
        self.assertEqual(result['candidateVertices'],4)
        self.assertEqual(candidate[0][-1],candidate[1][0])

    def test_closed_nested_rings_deterministic_and_partitioned_once(self):
        import numpy as np
        rings = []
        for radius in (10.,10.5):
            angle = np.linspace(0,2*np.pi,81)
            ring = list(zip(radius*np.cos(angle),radius*np.sin(angle)));ring[-1]=ring[0]
            rings.append(ring)
        a,stats = conservative_simplify(rings)
        b,again = conservative_simplify(rings)
        self.assertEqual((a,stats),(b,again))
        self.assertLess(stats['candidateVertices'],stats['originalVertices'])
        for coords in a:
            line = LineString(coords)
            pieces = [line.intersection(box(x,-20,x+20,20)) for x in (-20,0)]
            combined = unary_union(pieces)
            self.assertLess(line.hausdorff_distance(combined),1e-9)
            self.assertLess(abs(line.length-combined.length),1e-9)

    def test_invalid_self_intersection_is_not_fixed_silently(self):
        with self.assertRaisesRegex(ValueError,'Invalid baseline'):
            conservative_simplify([[(0,0),(2,2),(0,2),(2,0)]])

    def test_ring_collapse_and_moved_endpoint_are_rejected(self):
        originals = [LineString([(0,0),(2,0),(2,2),(0,2),(0,0)])]
        self.assertFalse(validate_family(originals,[LineString([(0,0),(2,0)])],2)[0])
        self.assertFalse(validate_family([LineString([(0,0),(1,1)])],[LineString([(.1,0),(1,1)])],2)[0])

    def test_narrow_valley_and_nearby_contours(self):
        lines = [[(-2,0),(-1,2),(0,.1),(1,2),(2,0)],
                 [(-2,-.1),(-1,1.9),(0,0),(1,1.9),(2,-.1)]]
        candidate,stats = conservative_simplify(lines)
        self.assertTrue(validate_family([LineString(line) for line in lines],
                                       [LineString(line) for line in candidate],2)[0])

    def test_existing_shared_intersection_must_not_move(self):
        originals = [LineString([(0,0),(2,2),(4,0)]),LineString([(1,-1),(1,3)])]
        candidates = [LineString([(0,0),(4,0)]),originals[1]]
        self.assertEqual(originals[0].relate(originals[1]),candidates[0].relate(candidates[1]))
        self.assertEqual(validate_family(originals,candidates,2)[1],'shared intersection moved')


if __name__ == '__main__': unittest.main()
