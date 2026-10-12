"""Synthetic adapter/halo controls, with mocked raster reads only."""
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import tempfile
import json

from readers import SwissNativeReader, SwissCoarseReader
from synthetic_recovery import SyntheticNative,CoarseReader
from pilot import block_mean,smooth


class ReaderControls(unittest.TestCase):
    def test_all_level_pairs_reject_introduced_crossing(self):
        from rerun import global_simplification
        from windowed import Ledger
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for level,line in ((0,[[-1.,0.],[0.,1.5],[1.,0.]]),(10,[[0.,-.25],[0.,.25]])):
                (folder/f'{level}.ndjson').write_text(json.dumps({'coordinates':line})+'\n')
            result = global_simplification(folder,[0,10],False,Ledger(folder))
            self.assertTrue(result['allPairsTested'])
            self.assertEqual(result['levelPairsTested'],1)
            self.assertFalse(result['accepted'])
            self.assertEqual(result['introducedCrossings'],1)

    def test_filtered_halos_share_identical_samples(self):
        native = SyntheticNative()
        for filtering in (False,True):
            reader = SwissCoarseReader(native,smoothing=filtering)
            a = reader.read(250,507,0,257)
            b = reader.read(250,507,256,513)
            np.testing.assert_array_equal(a.z[:,-1],b.z[:,0])
            self.assertEqual(a.x[-1],b.x[0])
            reference = CoarseReader(native,smoothing=filtering).read(250,507,0,257)
            np.testing.assert_array_equal(a.z,reference.z)

    def test_filter_matches_whole_patch_and_masks_unavailable_halo(self):
        native = SyntheticNative()
        reader = SwissCoarseReader(native,smoothing=True)
        actual = reader.read(20,40,20,40).z
        expected = smooth(block_mean(native.read(17*4,43*4,17*4,43*4).z))[3:-3,3:-3]
        np.testing.assert_array_equal(actual,expected)
        edge = reader.read(0,20,0,20).z
        self.assertTrue(np.isnan(edge[:3]).all())
        self.assertTrue(np.isnan(edge[:,:3]).all())

    def test_mocked_native_tile_join_preserves_post_centres(self):
        class Fake:
            crs = SimpleNamespace(to_epsg=lambda:2056)
            shape,res,nodata = (2000,2000),(.5,.5),-9999
            def __init__(self,row,col):
                self.row,self.col = row,col
                self.bounds = SimpleNamespace(left=2624000+col*.5,bottom=1091000+row*.5)
            def __enter__(self):return self
            def __exit__(self,*args):return None
            def read(self,band,window,masked):
                rows = self.row+2000-1-(window.row_off+np.arange(window.height))
                cols = self.col+window.col_off+np.arange(window.width)
                return (rows[:,None]*4000+cols[None,:]).astype(np.float32)
        tiles = [Fake(r,c) for r in (0,2000) for c in (0,2000)]
        with patch('readers.rasterio.open',side_effect=tiles):
            reader = SwissNativeReader(Path('not-opened'),{'inputs':[{'path':str(i)} for i in range(4)]})
            try:
                grid = reader.read(1998,2003,1998,2003)
                expected = np.arange(1998,2003)[:,None]*4000+np.arange(1998,2003)[None,:]
                np.testing.assert_array_equal(grid.z,expected)
                self.assertEqual(grid.x[0],2624999.25)
                self.assertEqual(grid.y[0],1091999.25)
                with self.assertRaises(ValueError):reader.read(0,2000,0,2000)
            finally:reader.close()


if __name__ == '__main__':
    unittest.main()
