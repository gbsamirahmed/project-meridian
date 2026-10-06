"""Focused metadata eligibility tests; no image processing or public query API."""
import copy, unittest
from assess import assess, level, support, read, PRODUCT

class EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = read(PRODUCT/'manifest.json')
    def test_inside_identity_provenance(self):
        r=assess(self.m, {'purpose':'source-derived','point':[2625240,1092530],'deliveryBudgetMetres':1})
        self.assertEqual(r['revision'], self.m['identity'])
        self.assertEqual(r['lineage'],self.m['lineage'])
        self.assertEqual(r['rights'],self.m['rights'])
        self.assertEqual(r['representation']['zoom'],16)
        self.assertEqual(r['acquisition']['pixelTimestamp'],'UNKNOWN')
    def test_partial_boundary_is_not_full_support(self):
        s=support(self.m['sourceBounds'],area=[2623990,1091990,2624010,1092010])
        self.assertEqual(s['relation'],'partial')
        self.assertEqual(s['supportedIntersection'],[2624000,1091990,2624010,1092010])
    def test_outside_not_equivalent_fallback(self):
        q={'purpose':'map-display','point':[2623900,1092000]}
        r=assess(self.m,q)
        self.assertEqual(r['kind'],'conditional-display-service')
        self.assertFalse(r['liveAvailabilityVerified'])
        self.assertFalse(r['equivalentRegionalProvenance'])
        self.assertEqual(assess(self.m,{**q,'pinnedRegional':True})['kind'],'outside-support')
    def test_physical_request_cannot_return_rgb(self):
        for purpose in ['illumination-independent','corrected-appearance']:
            r=assess(self.m,{'purpose':purpose,'point':[2624805,1092330]})
            self.assertEqual(r['kind'],'unsupported')
            self.assertFalse(r['ordinaryRGBSubstituted'])
    def test_geometry_not_borrowed(self):
        r=assess(self.m,{'purpose':'acquisition-geometry','point':[2624805,1092330]})
        self.assertEqual(r['acquisition']['viewGeometry'],'UNKNOWN')
        self.assertFalse(r['geometry2026Substituted'])
    def test_2023_not_current(self):
        r=assess(self.m,{'purpose':'source-derived','point':[2625240,1092530],'requireCurrentState':True})
        self.assertEqual(r['kind'],'unsupported')
    def test_delivery_never_new_information(self):
        r=assess(self.m,{'purpose':'source-derived','point':[2624805,1092330],'deliveryBudgetMetres':.1})
        self.assertEqual(r['representation']['zoom'],18)
        self.assertEqual(r['scale']['nominalSourceInformationMetres'],.25)
        self.assertFalse(r['scale']['newInformationFromResampling'])
    def test_parent_same_product(self):
        r=assess(self.m,{'purpose':'map-display','point':[2625240,1092530],'deliveryBudgetMetres':14})
        self.assertEqual(r['representation']['zoom'],12)
        self.assertEqual(r['product'],self.m['id'])
    def test_serialization_order_not_identity(self):
        m=dict(reversed(list(copy.deepcopy(self.m).items())))
        q={'purpose':'source-derived','point':[2625240,1092530],'deliveryBudgetMetres':1}
        self.assertEqual(assess(m,q),assess(self.m,q))
    def test_native_delivery_crs_roundtrip(self):
        from pyproj import Transformer
        p=[2625240,1092530]
        q=Transformer.from_crs(2056,3857,always_xy=True).transform(*p)
        r=Transformer.from_crs(3857,2056,always_xy=True).transform(*q)
        self.assertLess(max(abs(a-b) for a,b in zip(p,r)),.01)
    def test_invalid_metadata_query_fails_not_physical_absence(self):
        with self.assertRaises(ValueError):support(self.m['sourceBounds'])
        with self.assertRaises(ValueError):support(self.m['sourceBounds'],point=[float('nan'),1])
        with self.assertRaises(ValueError):support(self.m['sourceBounds'],area=[1,2,1,3])
        with self.assertRaises(ValueError):level(self.m['levels'],float('nan'))
        with self.assertRaises(ValueError):assess(self.m,{'purpose':'unknown','point':[2625240,1092530]})

if __name__=='__main__': unittest.main()
