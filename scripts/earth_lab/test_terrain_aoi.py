from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio

from terrain_aoi import (
    Aoi,
    choose_source,
    compare_surfaces,
    output_profile,
    raster_stats,
    run,
)


class TerrainAoiTests(unittest.TestCase):
    def test_aoi_bounds_are_centered_and_one_metre_aligned(self) -> None:
        aoi = Aoi("test", "Test", 266400, 359300, 2000, 2000)
        self.assertEqual(aoi.bounds, (265400, 358300, 267400, 360300))
        profile = output_profile(aoi)
        self.assertEqual((profile["width"], profile["height"]), (2000, 2000))
        self.assertEqual(profile["transform"].a, 1.0)
        self.assertEqual(profile["transform"].e, -1.0)

    def test_source_selection_prefers_resolution_then_newer_date(self) -> None:
        historic = [
            {
                "resolution": 1,
                "date_flown": "Feb---April-2007",
                "dtm_url": "example.test/old-dtm.zip",
                "dsm_url": "example.test/old-dsm.zip",
            }
        ]
        national = [{"date": "02-03-2021", "dtm_link": "present"}]
        self.assertEqual(choose_source(historic, national)["family"], "welsh_government_2020_2023")
        historic[0]["resolution"] = 0.5
        self.assertEqual(choose_source(historic, national)["family"], "nrw_historic")

    def test_nodata_is_preserved_and_surface_difference_uses_shared_valid_cells(self) -> None:
        aoi = Aoi("test", "Test", 2, 2, 4, 4)
        profile = output_profile(aoi)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dtm_path = root / "dtm.tif"
            dsm_path = root / "dsm.tif"
            dtm = np.arange(16, dtype=np.float32).reshape(4, 4)
            dsm = dtm + 3
            dtm[0, 0] = -9999
            dsm[1, 1] = -9999
            for path, values in ((dtm_path, dtm), (dsm_path, dsm)):
                local_profile = {**profile, "tiled": False}
                for key in ("blockxsize", "blockysize"):
                    local_profile.pop(key)
                with rasterio.open(path, "w", **local_profile) as destination:
                    destination.write(values, 1)
            stats = raster_stats(dtm_path)
            self.assertEqual(stats["nodata_cells"], 1)
            comparison = compare_surfaces(dtm_path, dsm_path)
            self.assertEqual(comparison["comparable_cells"], 14)
            self.assertAlmostEqual(comparison["minimum_m"], 3.0)
            self.assertAlmostEqual(comparison["maximum_m"], 3.0)

    def test_generated_data_is_refused_inside_git_worktree(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        with self.assertRaisesRegex(ValueError, "outside the Git worktree"):
            run(Aoi("test", "Test", 2, 2, 4, 4), repository_root / "generated")


if __name__ == "__main__":
    unittest.main()
