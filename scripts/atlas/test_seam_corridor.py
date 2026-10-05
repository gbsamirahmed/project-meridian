"""Synthetic topology tests; no external products or production imports."""
import unittest
import numpy as np
from seam_corridor import feasibility, minimum_threshold, boundary_cycle, simple_cycles, encloses


class CorridorTopology(unittest.TestCase):
    def ring(self):
        allowed=np.zeros((9,9),bool)
        allowed[1,1:8]=True;allowed[7,1:8]=True
        allowed[1:8,1]=True;allowed[1:8,7]=True
        return allowed

    def test_closed_ring_separates_entire_interior(self):
        a=self.ring(); d=np.ones(a.shape)
        yes,faces,path=feasibility(a,d,(4,4),1)
        self.assertTrue(yes);self.assertIsNone(path)
        self.assertTrue(faces[2:7,2:7].all())
        cycle=boundary_cycle(faces,(4,4))
        self.assertTrue(encloses(cycle,(4.5,4.5)))
        self.assertEqual(len(cycle)-1,24)
        self.assertEqual(len({tuple(v) for v in cycle[:-1]}),len(cycle)-1)
        self.assertTrue(a[cycle[:,0],cycle[:,1]].all())

    def test_break_in_ring_cannot_escape_constraints_by_diagonal(self):
        a=self.ring();a[1,4]=False
        yes,_,path=feasibility(a,np.ones(a.shape),(4,4))
        self.assertFalse(yes);self.assertGreater(len(path),1)
        self.assertIsNone(minimum_threshold(a,np.ones(a.shape),(4,4)))

    def test_minimax_reports_unavoidable_worst_node_not_mean(self):
        a=self.ring();d=np.ones(a.shape);d[1,4]=10
        self.assertEqual(minimum_threshold(a,d,(4,4)),10)
        self.assertFalse(feasibility(a,d,(4,4),np.nextafter(10.,-np.inf))[0])
        self.assertTrue(feasibility(a,d,(4,4),10)[0])

    def test_favorable_patches_and_wrong_side_cycle_do_not_enclose(self):
        a=np.zeros((15,15),bool);a[1:5,1:5]=True
        self.assertFalse(feasibility(a,np.ones(a.shape),(10,10))[0])

    def test_nonfinite_or_insufficient_support_breaks_route(self):
        a=self.ring();d=np.ones(a.shape);d[1,4]=np.nan
        self.assertFalse(feasibility(a,d,(4,4))[0])

    def test_threshold_feasibility_is_monotone(self):
        a=self.ring();d=np.ones(a.shape);d[1,4]=-4.5
        values=[feasibility(a,d,(4,4),t)[0] for t in [0,1,4,4.5,8]]
        self.assertEqual(values,[False,False,False,True,True])

    def test_boundary_walk_split_does_not_claim_figure_eight_is_simple(self):
        walk=[(0,0),(0,1),(1,1),(1,0),(0,0),(0,-1),(-1,-1),(-1,0),(0,0)]
        cycles=simple_cycles(walk)
        self.assertEqual(len(cycles),2)
        self.assertEqual(sum(encloses(c,(.5,.5)) for c in cycles),1)

    def test_invalid_seed_rejected(self):
        with self.assertRaises(ValueError):
            feasibility(self.ring(),np.ones((9,9)),(20,20))


if __name__=='__main__':
    unittest.main()
