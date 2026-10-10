"""Synthetic rejection fixtures are not model evidence; one opt-in real replay."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import field_compatibility as p


class SyntheticGuards(unittest.TestCase):
    def setUp(self):
        self.pin = json.loads(p.PIN.read_text(encoding="utf-8"))
        self.u = deepcopy(self.pin["fields"]["u10"]["expected"])
        self.v = deepcopy(self.pin["fields"]["v10"]["expected"])
        self.grid = self.pin["section3_sha256"]

    def concept(self, m, evidence="new_independent_numerical"):
        return p.identity(m, self.grid, "a"*64, evidence)

    def rejected(self, mutations, source=None, function=None):
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                m = deepcopy(self.u if source is None else source); m[key] = value
                with self.assertRaises(p.Error): (function or self.concept)(m)

    def test_wrong_unit(self): self.rejected([("units", "K"), ("units", None)])
    def test_wrong_level(self): self.rejected([("level", 2), ("typeOfFirstFixedSurface", 100)])
    def test_unknown_parameter(self): self.rejected([("parameterNumber", 99)])
    def test_invalid_valid_time(self): self.rejected([("validityDate", 20250117), ("validityTime", 100)])
    def test_wrong_step(self): self.rejected([("endStep", 23), ("startStep", 1), ("forecastTime", 0)])
    def test_unsupported_time_unit(self): self.rejected([("indicatorOfUnitOfTimeRange", 255), ("indicatorOfUnitOfTimeRange", 3)])
    def test_unknown_support(self): self.rejected([("productDefinitionTemplateNumber", 11), ("stepType", "avg")])
    def test_ensemble_not_member_zero(self): self.rejected([("typeOfProcessedData", 4), ("productDefinitionTemplateNumber", 1)])
    def test_unknown_evidence(self):
        with self.assertRaises(p.Error): self.concept(self.u, "forecast_skill_validated")
    def test_missing_provenance(self):
        for seal in ("", "x"*64, None):
            with self.subTest(seal=seal), self.assertRaises(p.Error): p.identity(self.u, seal, "a"*64, "metadata_only")
    def test_grid_scan_longitude_rejection(self):
        self.rejected([("scanningMode", 128), ("longitudeOfFirstGridPointInDegrees", -180), ("Ni", 1441), ("gridType", "rotated_ll")])
    def test_matching_pair(self):
        self.assertEqual(p.vector_pair(self.concept(self.u), self.concept(self.v), self.u, self.v)["status"], "aligned numerical component pair")
    def test_pair_support_mismatches(self):
        a, b = self.concept(self.u), self.concept(self.v)
        for key, value in [("grid_section3_sha256", "b"*64), ("native_unit", "K"), ("vertical", {"level": 2}), ("temporal", {"kind": "accumulation"}), ("ensemble", {"member": 1}), ("product", {"centre": 1})]:
            with self.subTest(key=key):
                c = deepcopy(b); c[key] = value
                with self.assertRaises(p.Error): p.vector_pair(a, c, self.u, self.v)
    def test_pair_basis(self):
        for key, value in [("uvRelativeToGrid", 1), ("resolutionAndComponentFlags", 56)]:
            with self.subTest(key=key):
                m = dict(self.v); m[key] = value
                with self.assertRaises(p.Error): p.vector_pair(self.concept(self.u), self.concept(self.v), self.u, m)
    def test_pair_order(self):
        with self.assertRaises(p.Error): p.vector_pair(self.concept(self.v), self.concept(self.u), self.v, self.u)
    def test_metadata_only_pair(self):
        with self.assertRaises(p.Error): p.vector_pair(self.concept(self.u, "metadata_only"), self.concept(self.v), self.u, self.v)
    def test_interval_not_instant(self):
        m = json.loads((p.HERE.parent/"wr009/input-pins.json").read_text())["expected"]
        a, b = self.concept(self.u), self.concept(m); check = p.compatibility(a, b)
        self.assertTrue(check["same_valid_endpoint"]); self.assertFalse(check["same_temporal_support"])
        self.assertEqual(b["temporal"]["interval_duration_seconds"], 21600)
    def test_missing_contradictory_accumulation(self):
        m = json.loads((p.HERE.parent/"wr009/input-pins.json").read_text())["expected"]
        self.rejected([("lengthOfTimeRange", 0), ("lengthOfTimeRange", 24), ("numberOfTimeRange", 2), ("typeOfStatisticalProcessing", 0), ("yearOfEndOfOverallTimeInterval", None)], m, p.temporal)
        del m["lengthOfTimeRange"]
        with self.assertRaises(p.Error): p.temporal(m)
    def test_numerical_nonfinite_and_masks(self):
        for bad in (np.nan, np.inf):
            with self.subTest(bad=bad), self.assertRaises(p.Error): p.numeric_compare(np.array([bad]), np.array([0.]), np.array([False]), np.array([False]), self.u)
        with self.assertRaises(p.Error): p.numeric_compare(np.array([0.]), np.array([0.]), np.array([True]), np.array([False]), self.u)
        with self.assertRaises(p.Error): p.numeric_compare(np.array([0.]), np.array([0.]), np.array([True]), np.array([True]), self.u)
    def test_decoder_disagreement(self):
        m = dict(self.u); m["referenceValue"] = 0
        with self.assertRaises(p.Error): p.numeric_compare(np.array([1.]), np.array([2.]), np.array([False]), np.array([False]), m)
    def test_unsupported_packing(self):
        m = dict(self.u); m["dataRepresentationTemplateNumber"] = 40
        with self.assertRaises(p.Error): p.numeric_compare(np.array([0.]), np.array([0.]), np.array([False]), np.array([False]), m)
    def test_framing_truncated(self):
        with self.assertRaises(p.Error): p.field.validate_framing(b"GRIB")
    def test_receipt_serialisation(self):
        self.assertEqual(p.field.canonical({"b": 2, "a": 1}), p.field.canonical({"a": 1, "b": 2}))
        with self.assertRaises(ValueError): p.field.canonical({"value": float("nan")})
    def test_spatial_missing_invalid_and_polar(self):
        m = dict(self.u); m.update(Ni=4, Nj=5, numberOfPoints=20, iDirectionIncrementInDegrees=90, jDirectionIncrementInDegrees=45, longitudeOfLastGridPointInDegrees=270)
        a = np.ones((5, 4)); mask = np.zeros(a.shape, dtype=bool); mask[1, 0] = True
        sampler = p.spatial.Sampler(a, mask, m)
        q = {"latitude": 45., "longitude": 0., "method": "BILINEAR"}
        self.assertEqual(sampler.query(q)["status"], "MISSING_CONTRIBUTING_NODE")
        for latitude, expected in [(91, "LATITUDE_OUT_OF_RANGE"), (90, "UNSUPPORTED_POLAR_CAP_BILINEAR"), (float("nan"), "NONFINITE_COORDINATE")]:
            q["latitude"] = latitude; self.assertEqual(sampler.query(q)["status"], expected)
        mask[:] = False; a[1, 0] = np.nan; q["latitude"] = 45
        self.assertEqual(sampler.query(q)["status"], "UNINTERPRETABLE_NODE")


class RealReplay(unittest.TestCase):
    @unittest.skipUnless(all(os.environ.get(n) for n in ["MERIDIAN_WR010_INPUTS", "MERIDIAN_WR007_INPUT", "MERIDIAN_WR009_INPUT", "MERIDIAN_WR007_GDAL_PYTHON"]), "Pinned external science/independent interpreter opt-in required")
    def test_actual_three_field_receipt_replay(self):
        root = Path(os.environ["MERIDIAN_WR010_INPUTS"])
        borrowed = {"temperature": Path(os.environ["MERIDIAN_WR007_INPUT"]), "precipitation": Path(os.environ["MERIDIAN_WR009_INPUT"])}
        with tempfile.TemporaryDirectory(prefix="wr010-test-", dir=root) as directory:
            paths = [Path(directory)/name for name in ("a.json", "b.json")]
            for out in paths: p.run(root, os.environ["MERIDIAN_WR007_GDAL_PYTHON"], out, borrowed)
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            expected = json.loads((p.HERE/"integrity-receipt.json").read_text(encoding="utf-8"))["scientific_receipt"]
            self.assertEqual(json.loads(paths[0].read_text(encoding="utf-8")), expected)


if __name__ == "__main__": unittest.main()
