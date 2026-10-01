import json
from pathlib import Path
import unittest

import numpy as np
import rasterio

from observed_surface_height import BOUNDS, components, difference, sha256, window_fields
from meridian_paths import resolve_storage_roots


class SurfaceHeightTests(unittest.TestCase):
    def test_signed_subtraction_and_missing_data(self):
        dtm = np.array([[3,7,np.nan]],np.float32)
        dsm = np.array([[2,9,5]],np.float32)
        actual = difference(dtm,dsm)
        np.testing.assert_equal(actual,np.array([[-1,2,np.nan]],np.float32))

    def test_four_neighbour_components_and_run_merging(self):
        np.testing.assert_array_equal(components(np.array([[1,0],[0,1]],bool)),[[1,0],[0,2]])
        labels=components(np.array([[1,0,1],[1,1,1],[0,0,1]],bool))
        self.assertEqual(int(labels.max()),1)
        self.assertEqual(int(np.sum(labels==1)),6)

    def test_components_against_independent_flood_fill(self):
        # Exhaust all 3x3 masks, checking connectivity rather than label numbering.
        for bits in range(512):
            mask=np.array([(bits >> i)&1 for i in range(9)],bool).reshape(3,3)
            pending=set(zip(*np.nonzero(mask)))
            expected=[]
            while pending:
                start=pending.pop()
                group={start}; stack=[start]
                while stack:
                    r,c=stack.pop()
                    for point in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                        if point in pending:
                            pending.remove(point); group.add(point); stack.append(point)
                expected.append(frozenset(group))
            labels=components(mask)
            actual=[frozenset(zip(*np.nonzero(labels==i))) for i in range(1,int(labels.max())+1)]
            self.assertEqual(set(actual),set(expected))

    def test_windows_match_independent_direct_calculation(self):
        a=np.arange(42,dtype=np.float64).reshape(6,7)
        for size in (1,3,4):
            result=window_fields(a,size)
            start=(size-1)//2
            for r in range(6-size+1):
                for c in range(7-size+1):
                    patch=a[r:r+size,c:c+size]
                    for key,expected in (("mean",patch.mean()),("std",patch.std()),("range",np.ptp(patch)),("max",patch.max())):
                        self.assertAlmostEqual(float(result[key][r+start,c+start]),float(expected),places=5)
            self.assertEqual(int(np.isfinite(result["mean"]).sum()),(6-size+1)*(7-size+1))

    def test_local_departure_is_zero_on_planar_slope(self):
        y,x=np.mgrid[:12,:13]
        plane=(500+3*x-7*y).astype(np.float32)
        f=window_fields(plane,5)
        np.testing.assert_equal((plane-f["mean"])[2:-2,2:-2],0)

    def test_real_grid_hashes_subtraction_and_orientation(self):
        repo=Path(__file__).resolve().parents[2]
        root=resolve_storage_roots(repository_root=repo,require_data=True).data
        out=root/"experiments/earth-lab/tryfan-011/observed-surface-height-v1"
        manifest=json.loads((out/"lab011-manifest.json").read_text(encoding="utf-8"))
        for item in manifest["sources"]:
            self.assertEqual(sha256(root/item["path"].split("${MERIDIAN_DATA_ROOT}/",1)[1]),item["sha256"])
        for item in manifest["products"]:
            self.assertEqual(sha256(out/item["path"]),item["sha256"])
        source=root/"sources/atlas/tryfan/welsh-lidar-1m/rasters"
        with rasterio.open(source/"tryfan-004-dtm-1m.tif") as dtm, rasterio.open(source/"tryfan-004-dsm-1m.tif") as dsm, rasterio.open(out/"lab011-signed-residual-1m.tif") as residual:
            self.assertEqual(dtm.transform,dsm.transform)
            self.assertEqual(dtm.transform,residual.transform)
            self.assertEqual(str(residual.crs),"EPSG:27700")
            self.assertEqual(tuple(residual.bounds),BOUNDS)
            self.assertEqual(residual.shape,(3000,3000))
            self.assertEqual(residual.xy(0,0),(264900.5,360799.5))
            self.assertEqual(residual.xy(2999,2999),(267899.5,357800.5))
            for item in manifest["independent_sample_coordinates"]:
                r,c=item["row"],item["column"]
                xy=residual.xy(r,c)
                expected=float(next(dsm.sample([xy]))[0])-float(next(dtm.sample([xy]))[0])
                self.assertEqual(float(next(residual.sample([xy]))[0]),expected)
            self.assertEqual(int(np.sum(~np.isfinite(residual.read(1)))),0)


if __name__ == "__main__":
    unittest.main()
