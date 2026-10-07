"""Mutation tests for bounded planning invariants, not pilot implementation tests."""
import copy, tempfile, unittest
from pathlib import Path
import check_plan as P

class PlanSafeguards(unittest.TestCase):
    def setUp(self):
        self.plan = P.read(P.ROOT/P.PLAN)

    def reject(self, mutate):
        candidate=copy.deepcopy(self.plan);mutate(candidate)
        with self.assertRaises(ValueError):
            P.check_structure(candidate)

    def test_authoritative_plan(self):
        self.assertTrue(P.check_structure(self.plan))

    def test_expanded_region(self):
        self.reject(lambda p:p['scope']['bounds'].__setitem__(2,268900))

    def test_substituted_observation(self):
        self.reject(lambda p:p['families'][4].__setitem__('identity','newer-scene'))

    def test_lost_vector_identity_support(self):
        self.reject(lambda p:p['families'][3].__setitem__('records',3))

    def test_mutable_source(self):
        self.reject(lambda p:p['assets'][0].__setitem__('immutable',False))

    def test_locator_traversal(self):
        self.reject(lambda p:p['assets'][0].__setitem__('path','../meridian-private/data'))

    def test_locator_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'root';root.mkdir()
            with self.assertRaises(ValueError):
                P.safe_asset(root,'../outside')

    def test_recomputed_unaffected_chain(self):
        self.reject(lambda p:p['updates'][0].__setitem__('recompute',4))

    def test_lost_historical_revisions(self):
        self.reject(lambda p:p['scienceBasis']['counts'].__setitem__('historicalAWS',0))

    def test_mutable_generation(self):
        self.reject(lambda p:p['publication'].__setitem__('mutableGeneration',True))

    def test_root_before_validation(self):
        self.reject(lambda p:p['publication']['steps'].reverse())

    def test_unpinned_asset_read(self):
        self.reject(lambda p:p['serving']['routes'][4].__setitem__('generationRequired',False))

    def test_http_writer(self):
        self.reject(lambda p:p['serving']['routes'][4].__setitem__('method','PUT'))

    def test_no_independent_mixed_family(self):
        self.reject(lambda p:p['updates'][1].__setitem__('familiesChanged',['terrain','derived-understanding']))

    def test_unordered_slice(self):
        self.reject(lambda p:p['slices'][0].__setitem__('dependsOn',['S5']))

    def test_shared_production_module(self):
        self.reject(lambda p:p['slices'][0]['modules'].append('src/atlas/pilot.ts'))

    def test_acceptance_missing_serving(self):
        self.reject(lambda p:p['admission'].__setitem__('outstandingAcceptance',['mixed-family-coherent-publication']))

    def test_unfrozen_acceptance(self):
        self.reject(lambda p:p.__setitem__('acceptanceFrozen',False))

    def test_metrics_in_identity(self):
        self.reject(lambda p:p['instrumentation'].__setitem__('outsideIdentity',False))

    def test_implementation_started(self):
        self.reject(lambda p:p.__setitem__('nextTaskStarted',True))

    def test_final_database_decided_now(self):
        self.reject(lambda p:p['decideNow'].append('productiondatabase'))

    def test_unknown_schema(self):
        self.reject(lambda p:p.__setitem__('schema','atlas-tryfan-regional-pilot-plan/v2'))

if __name__=='__main__':
    unittest.main()
