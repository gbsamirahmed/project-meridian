"""Adversarial synthetic controls; no source DEMs are opened."""
import tempfile
from pathlib import Path
import unittest
import numpy as np
import contourpy
from shapely.geometry import LineString
from shapely.ops import unary_union

from windowed import (Grid, Ledger, LimitsReached, extract, load_level, stitch,
                      simplification_check, make_generator)


class ArrayReader:
    def __init__(self, z, curvilinear=False):
        self.z = z
        self.shape = z.shape
        self.curvilinear = curvilinear

    def read(self, row, r1, col, c1):
        x = np.arange(col, c1, dtype=float)+1000.
        y = np.arange(row, r1, dtype=float)+2000.
        if self.curvilinear:
            x, y = np.meshgrid(x, y)
            x, y = x+.001*y, y+.002*x
        return Grid(x, y, self.z[row:r1, col:c1].copy(), row, col)


def derive(reader, levels):
    with tempfile.TemporaryDirectory() as tmp:
        ledger = Ledger(tmp)
        extract(reader, levels, Path(tmp)/'fragments', ledger)
        return {level: stitch(load_level(Path(tmp)/f'fragments/{level}.ndjson', ledger)) for level in levels}


def whole(reader, level):
    grid = reader.read(0, reader.shape[0], 0, reader.shape[1])
    generator = contourpy.contour_generator(x=grid.x, y=grid.y, z=grid.z,
        name='serial', line_type='Separate', z_interp='Linear',
        corner_mask=False, quad_as_tri=False, thread_count=1)
    return generator.lines(level)


def same_geometry(test, lines, reference):
    a = unary_union([LineString(line) for line in lines])
    b = unary_union([LineString(line) for line in reference])
    test.assertLess(a.hausdorff_distance(b), 1e-6)
    test.assertLess(abs(a.length-b.length), 1e-6)


class WindowControls(unittest.TestCase):
    def test_plane_crosses_four_windows_with_exact_heights(self):
        rows, cols = np.indices((521, 519), dtype=float)
        reader = ArrayReader(2*rows+3*cols)
        for level, lines in derive(reader, [420.5, 1020.5]).items():
            same_geometry(self, lines, whole(reader, level))
            for line in lines:
                p = np.asarray(line)
                np.testing.assert_allclose(2*(p[:, 1]-2000)+3*(p[:, 0]-1000), level, atol=.001)

    def test_closed_contour_spans_four_windows(self):
        rows, cols = np.indices((521, 521), dtype=float)
        reader = ArrayReader((rows-256)**2+(cols-256)**2)
        lines = derive(reader, [20000.5])[20000.5]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0][0], lines[0][-1])
        same_geometry(self, lines, whole(reader, 20000.5))

    def test_nodata_hole_and_missing_window_never_bridge(self):
        rows, cols = np.indices((521, 521), dtype=float)
        z = rows+cols
        z[245:270, 245:270] = np.nan
        z[400:, :80] = np.inf
        reader = ArrayReader(z)
        lines = derive(reader, [513.5])[513.5]
        self.assertGreater(len(lines), 1)
        same_geometry(self, lines, whole(reader, 513.5))

    def test_entire_missing_window_preserves_open_endpoints(self):
        rows,cols = np.indices((521,521),dtype=float)
        z = rows+cols
        z[256:513,256:513] = np.nan
        reader = ArrayReader(z)
        lines = derive(reader,[600.5])[600.5]
        same_geometry(self,lines,whole(reader,600.5))
        self.assertTrue(all(line[0]!=line[-1] for line in lines))

    def test_curvilinear_seams(self):
        rows, cols = np.indices((521, 521), dtype=float)
        reader = ArrayReader(rows*2+cols, curvilinear=True)
        lines = derive(reader, [780.5])[780.5]
        same_geometry(self, lines, whole(reader, 780.5))

    def test_saddle_and_ties_match_monolithic_geometry(self):
        rows, cols = np.indices((521, 521), dtype=float)
        for field, level in ((cols, 256.), ((rows-256)*(cols-256), .25)):
            reader = ArrayReader(field)
            lines = derive(reader, [level])[level]
            same_geometry(self, lines, whole(reader, level))

    def test_repeated_derivation_is_exact(self):
        rows, cols = np.indices((269, 273), dtype=float)
        reader = ArrayReader(rows+cols*.37)
        self.assertEqual(derive(reader, [150.5]), derive(reader, [150.5]))

    def test_partition_quad_ownership(self):
        from windowed import WINDOW_QUADS
        shape = (521, 519)
        ownership = np.zeros((shape[0]-1, shape[1]-1), dtype=np.uint8)
        for row in range(0, shape[0]-1, WINDOW_QUADS):
            for col in range(0, shape[1]-1, WINDOW_QUADS):
                ownership[row:row+WINDOW_QUADS, col:col+WINDOW_QUADS] += 1
        np.testing.assert_array_equal(ownership, 1)

    def test_limits_reject_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args in ({'bytes_limit':5}, {'vertices_limit':1},
                         {'memory_limit':1}, {'seconds_limit':-1}):
                ledger = Ledger(tmp, **args)
                path = Path(tmp)/'out'
                with path.open('wb') as stream:
                    with self.assertRaises(LimitsReached):
                        ledger.append(stream, {'value':1}, 2)
                self.assertEqual(path.stat().st_size, 0)

    def test_ambiguous_junction_and_level_bound_are_rejected(self):
        records = [{'start':['h',0,0], 'end':None, 'coordinates':[[0.,0.],[float(i),1.]]} for i in range(3)]
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            stitch(records)
        with self.assertRaises(LimitsReached):
            stitch(records, max_vertices=1)

    def test_simplification_rejects_new_same_level_crossing(self):
        lines = [[[-2.,0.],[0.,3.],[2.,0.]], [[0.,-.5],[0.,.5]]]
        result = simplification_check(lines, 4.)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['introducedCrossings'], 1)

    def test_simplification_closed_ring_and_displacement(self):
        angle = np.linspace(0, 2*np.pi, 81)
        ring = np.column_stack((30*np.cos(angle),30*np.sin(angle))).tolist()
        ring[-1] = ring[0]
        result = simplification_check([ring], 2.)
        self.assertTrue(result['accepted'])
        self.assertLessEqual(result['maxDisplacement'], 2.)

    def test_oversized_and_folded_windows(self):
        with self.assertRaises(ValueError):
            make_generator(ArrayReader(np.ones((258,258))).read(0,258,0,258))
        x,y = np.meshgrid(np.arange(2.),np.arange(2.))
        with self.assertRaisesRegex(ValueError, 'Folded'):
            make_generator(Grid(-x,y,np.ones((2,2)),0,0))


if __name__ == '__main__':
    unittest.main()
