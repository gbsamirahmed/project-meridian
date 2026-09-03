"""Synthetic atmospheric GRIB/PNG/publication regressions (no live NOAA calls)."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from PIL import Image

import gfs_atmospheric as atmosphere
import gfs_weather_builder as core


RUN = datetime(2026, 1, 1, tzinfo=timezone.utc)


def metadata(field, hour=1):
    valid = RUN + timedelta(hours=hour)
    return dict(shortName=field.short_name, units=field.source_units,
                typeOfLevel=field.level_type, level=0, discipline=0,
                parameterCategory=field.category, parameterNumber=field.number,
                productDefinitionTemplateNumber=0, stepType="instant", startStep=hour,
                endStep=hour, forecastTime=hour, Ni=1440, Nj=721, gridType="regular_ll",
                scanningMode=0, jScansPositively=0, iScansNegatively=0,
                jPointsAreConsecutive=0, alternativeRowScanning=0,
                iDirectionIncrementInDegrees=0.25, jDirectionIncrementInDegrees=0.25,
                latitudeOfFirstGridPointInDegrees=90, longitudeOfFirstGridPointInDegrees=0,
                latitudeOfLastGridPointInDegrees=-90, longitudeOfLastGridPointInDegrees=359.75,
                dataDate=20260101, dataTime=0, validityDate=int(valid.strftime("%Y%m%d")),
                validityTime=int(valid.strftime("%H%M")), numberOfMissing=0, missingValue=9999)


class AtmosphericTests(unittest.TestCase):
    def test_exact_selection_all_fields_and_hours(self):
        for field in atmosphere.FIELDS:
            for hour in (1, 6, 12, 24):
                with self.subTest(field=field.id, hour=hour):
                    good = f"1:0:d=2026010100:{field.parameter}:{field.level}:{hour} hour fcst:"
                    average = f"2:100:d=2026010100:{field.parameter}:{field.level}:0-{hour} hour ave fcst:"
                    end = "3:200:d=2026010100:TMP:surface:1 hour fcst:"
                    self.assertEqual(atmosphere.select_record("\n".join((good, average, end)), hour, field).offset, 0)
                    with self.assertRaises(ValueError):
                        atmosphere.select_record("\n".join((average, end)), hour, field)
                    with self.assertRaises(ValueError):
                        atmosphere.select_record("\n".join((good.replace(field.level, "500 mb"), end)), hour, field)
                    with self.assertRaises(ValueError):
                        atmosphere.select_record("\n".join((good, good.replace("1:0:", "2:100:"), end)), hour, field)
                    atmosphere.validate_metadata(metadata(field, hour), RUN, hour, field)

    def test_reject_wrong_metadata_independently(self):
        for field in atmosphere.FIELDS:
            for key, bad in {"units": "wrong", "typeOfLevel": "wrong", "shortName": "wrong",
                             "parameterNumber": 99, "Ni": 720, "Nj": 360,
                             "scanningMode": 64, "jPointsAreConsecutive": 1,
                             "startStep": 0, "validityTime": 200, "dataDate": 20260102,
                             "stepType": "max", "typeOfStatisticalProcessing": 1}.items():
                with self.subTest(field=field.id, key=key), self.assertRaises(ValueError):
                    atmosphere.validate_metadata({**metadata(field), key: bad}, RUN, 1, field)

    def test_missing_is_not_valid_9999_or_zero(self):
        values = np.array([[0, 9999, 9998.95]], dtype=np.float32)
        result = atmosphere.normalise_missing(values, {"numberOfMissing": 0, "missingValue": 9999})
        np.testing.assert_equal(result, values)
        result = atmosphere.normalise_missing(values, {"numberOfMissing": 1, "missingValue": 9999})
        self.assertTrue(np.isnan(result[0, 1]))
        self.assertTrue(np.isfinite(result[0, 2]))
        with self.assertRaises(ValueError):
            atmosphere.normalise_missing(values, {"numberOfMissing": 2, "missingValue": 9999})

    def test_ceiling_sentinel_masked_before_interpolation_and_zero_retained(self):
        field = atmosphere.FIELDS[-1]
        result, count = atmosphere.validated_values(np.array([[0, 700, 19999.7, 20000.15, np.nan]]), field)
        self.assertEqual(count, 2)
        np.testing.assert_equal(result, [[0, 700, np.nan, np.nan, np.nan]])
        grid = np.full((721, 1440), 700.0)
        grid[:, 0] = np.nan
        self.assertTrue(np.isnan(core.sample_gfs_grid(grid, np.array([0.125]), np.array([0]))[0, 0]))

    def test_ranges_encoding_exact_bytes_and_quantisation(self):
        with tempfile.TemporaryDirectory() as directory:
            for field in atmosphere.FIELDS:
                scale, offset, bounds = atmosphere.encoding(field)
                values = np.array([[0, scale, bounds[0], bounds[1]], [scale * 12.49, scale * 12.51, np.nan, 150]])
                path = Path(directory) / (field.id + ".png")
                atmosphere.encode_png(values, path, field)
                decoded = atmosphere.decode_png(path, field)
                np.testing.assert_allclose(decoded, np.where(np.isnan(values), np.nan,
                                           np.rint((values - offset) / scale) * scale + offset), equal_nan=True)
                self.assertEqual(decoded[0, 0], 0)
                rgba = np.asarray(Image.open(path))
                self.assertEqual(tuple(rgba[1, 2]), (255, 255, 0, 255))
                self.assertTrue(np.all(rgba[:, :, 2] == 0))
                self.assertTrue(np.all(rgba[:, :, 3] == 255))
                for bad in (bounds[0] - 1, bounds[1] + 1, np.inf):
                    with self.assertRaises(ValueError):
                        atmosphere.validated_values(np.array([[bad]]), field)
                    with self.assertRaises(ValueError):
                        atmosphere.encode_png(np.array([[bad]]), path, field)

    def test_canonical_orientation_wrap_and_export_tolerance(self):
        grid = np.repeat(np.arange(721)[:, None], 1440, axis=1).astype(float)
        north = core.sample_gfs_grid(grid, np.array([-180, 180]), np.array([60, -60]))
        np.testing.assert_equal(north, [[120, 120], [600, 600]])
        for field in atmosphere.FIELDS:
            manifest = atmosphere.field_manifest(field, SimpleNamespace(run_time=RUN), [])
            self.assertEqual(manifest["field"]["sourceLevel"], field.level)
            self.assertEqual(manifest["field"]["timeSemantics"], "instantaneous")
            self.assertNotIn("accumulationHours", manifest["field"])
            self.assertEqual(manifest["tiles"]["noData"], 65535)

    def test_independent_publication_and_failure_retains_catalogue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = atmosphere.field_manifest(atmosphere.FIELDS[0], SimpleNamespace(run_time=RUN), [
                {"forecastHour": 1, "validTime": "2026-01-01T01:00:00Z"}])
            core.publish_catalog_field(root, "precipitation", old, "prior/manifest.json")
            core.publish_catalog_field(root, "gust_surface", old, "prior/gust.json")
            before = (root / "latest.json").read_bytes()
            resolution = SimpleNamespace(run_time=RUN, checked_candidates=())
            args = SimpleNamespace(output_root=root)
            with patch.object(atmosphere, "load_field", side_effect=ValueError("invalid units")):
                with self.assertRaises(ValueError):
                    atmosphere.build_field(args, resolution, [1], root / "20260101T00Z", "20260101T00Z", atmosphere.FIELDS[0])
            self.assertEqual((root / "latest.json").read_bytes(), before)
            calls = []
            def build(*args):
                calls.append(args[-1].id)
                if args[-1].id == "gust_surface":
                    raise ValueError("unavailable")
            with patch.object(atmosphere, "build_field", side_effect=build), self.assertRaises(RuntimeError):
                atmosphere.build_atmospheric_datasets(args, resolution, [1], root, "run")
            self.assertEqual(calls, [field.id for field in atmosphere.FIELDS])

    def test_bounded_range_rejects_full_object_before_reading(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers = {}
        with patch.object(core.urllib.request, "urlopen", return_value=response), self.assertRaises(ValueError):
            core.fetch_bytes("https://example.test/data", (100, 199))
        response.read.assert_not_called()

    def test_inspection_cache_does_not_preempt_immutable_run_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = atmosphere.source_cache(SimpleNamespace(output_root=root), SimpleNamespace(run_time=RUN))
            cache.mkdir(parents=True)
            self.assertFalse((root / "20260101T00Z").exists())
            self.assertEqual(cache.parent, root)
            self.assertTrue(cache.name.endswith("-building"))


if __name__ == "__main__":
    unittest.main()
