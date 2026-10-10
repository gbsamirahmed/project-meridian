"""Synthetic guards; the opt-in real-field test is explicitly separate."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
import gfs_field_pilot as pilot


class SyntheticGuards(unittest.TestCase):
    def setUp(self):
        self.pin = json.loads(pilot.PIN.read_text(encoding="utf-8"))
        self.metadata = copy.deepcopy(self.pin["expected"])

    def rejection(self, key, wrong):
        self.metadata[key] = wrong
        with self.assertRaises(pilot.IntegrityError):
            pilot.validate_metadata(self.metadata, self.pin)

    def test_parameter_number(self): self.rejection("parameterNumber", 6)
    def test_parameter_category(self): self.rejection("parameterCategory", 1)
    def test_wrong_height(self): self.rejection("level", 1.5)
    def test_wrong_height_type(self): self.rejection("typeOfFirstFixedSurface", 1)
    def test_wrong_lead(self): self.rejection("forecastTime", 0)
    def test_wrong_initialisation(self): self.rejection("dataDate", 20250101)
    def test_wrong_initialisation_hour(self): self.rejection("dataTime", 600)
    def test_wrong_valid_time(self): self.rejection("validityDate", 20250115)
    def test_wrong_units(self): self.rejection("units", "C")
    def test_statistical_not_instantaneous(self): self.rejection("stepType", "avg")
    def test_analysis_not_forecast(self): self.rejection("typeOfProcessedData", 0)
    def test_orientation(self): self.rejection("scanningMode", 64)
    def test_unsupported_grid(self): self.rejection("gridType", "reduced_gg")
    def test_unsupported_packing(self): self.rejection("dataRepresentationTemplateNumber", 40)
    def test_unsupported_bitmap(self): self.rejection("bitmapPresent", 1)
    def test_unsupported_internal_missing(self): self.rejection("missingValueManagementUsed", 1)
    def test_missing_metadata(self):
        del self.metadata["units"]
        with self.assertRaises(pilot.IntegrityError): pilot.validate_metadata(self.metadata, self.pin)

    def test_longitude_wrap_is_reversible(self):
        for original, expected in [(0, 0), (179.75, 179.75), (180, -180), (359.75, -0.25)]:
            wrapped = pilot.wrap_longitude(original)
            self.assertEqual(wrapped, expected)
            self.assertEqual(wrapped % 360, original)
        with self.assertRaises(pilot.IntegrityError): pilot.wrap_longitude(360)

    def test_malformed_truncated_and_multiple_messages(self):
        body = b"GRIB\0\0\0\2" + (20).to_bytes(8, "big") + b"7777"
        pilot.validate_framing(body)  # Framing only, explicitly not valid meteorological content.
        for bad in [b"", b"HTML" + body[4:], body[:-1], body + body, body[:7] + b"\1" + body[8:]]:
            with self.subTest(size=len(bad)), self.assertRaises(pilot.IntegrityError):
                pilot.validate_framing(bad)

    def test_source_inside_repository_rejected(self):
        with self.assertRaises(pilot.IntegrityError):
            pilot.pinned_input(pilot.REPOSITORY / "synthetic.grib2", self.pin)

    def test_output_inside_repository_rejected(self):
        with self.assertRaises(pilot.IntegrityError):
            pilot.require_external(pilot.REPOSITORY / "generated.json")

    def arrays(self):
        integers = np.array([[0, 100, 1000]], dtype=np.float64)
        reference = self.metadata["referenceValue"]
        a = (integers + reference) * .01
        b = ((integers.astype(np.float32) + np.float32(reference)) * np.float32(.01)).astype(np.float64)
        mask = np.zeros(a.shape, dtype=bool)
        return a, b, mask

    def test_documented_rounding_profile(self):
        a, b, mask = self.arrays()
        result = pilot.compare_arrays(a, b, mask, mask, self.metadata)
        self.assertEqual(result["g2clib_rounding_profile_exact_cells"], 3)

    def test_decoder_disagreement(self):
        a, b, mask = self.arrays()
        b[0, 0] += .001
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.metadata)

    def test_mask_disagreement(self):
        a, b, mask = self.arrays()
        other = mask.copy(); other[0, 0] = True
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, other, self.metadata)

    def test_explicit_mask_not_a_guessed_sentinel(self):
        a, b, mask = self.arrays()
        mask[0, 0] = True; a[0, 0] = np.nan; b[0, 0] = -9999
        result = pilot.compare_arrays(a, b, mask, mask, self.metadata)
        self.assertEqual(result["compared_cells"], 2)

    def test_non_finite_unmasked(self):
        a, b, mask = self.arrays(); a[0, 0] = np.nan
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.metadata)

    def test_transposed_secondary(self):
        a, b, mask = self.arrays()
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b.T, mask, mask, self.metadata)

    def test_not_on_integer_lattice(self):
        a, b, mask = self.arrays(); a[0, 0] += .001
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.metadata)

    def test_checksum_and_input_immutability(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "synthetic.grib2"
            path.write_bytes(b"GRIB\0\0\0\2" + (20).to_bytes(8, "big") + b"7777")
            pin = {"input": {"bytes": 20, "sha256": pilot.digest(path)}}
            self.assertEqual(pilot.pinned_input(path, pin), path.read_bytes())
            path.write_bytes(path.read_bytes()[:-4] + b"7778")
            with self.assertRaises(pilot.IntegrityError): pilot.pinned_input(path, pin)


@unittest.skipUnless(os.environ.get("MERIDIAN_WR007_INPUT") and os.environ.get("MERIDIAN_WR007_GDAL_PYTHON"),
                     "Optional pinned external field and separate GDAL interpreter required")
class RealFieldReproducibility(unittest.TestCase):
    def test_real_receipt_reproducibility_and_immutability(self):
        source = Path(os.environ["MERIDIAN_WR007_INPUT"])
        pin = json.loads(pilot.PIN.read_text(encoding="utf-8"))
        initial = pilot.digest(source)
        with tempfile.TemporaryDirectory() as name:
            outputs = [Path(name) / f"receipt-{i}.json" for i in range(2)]
            for output in outputs:
                result = pilot.run(source, os.environ["MERIDIAN_WR007_GDAL_PYTHON"], output, pin)
                self.assertEqual(result["independent_comparison"]["compared_cells"], 1038240)
                self.assertEqual(result["statistics_K"]["missing_cells"], 0)
                accepted = json.loads(pilot.PIN.with_name("integrity-receipt.json").read_text(encoding="utf-8"))
                self.assertEqual(pilot.digest(output), accepted["full_local_receipt"]["sha256"])
                with self.assertRaises(pilot.IntegrityError):
                    pilot.run(source, os.environ["MERIDIAN_WR007_GDAL_PYTHON"], output, pin)
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
        self.assertEqual(pilot.digest(source), initial)


if __name__ == "__main__": unittest.main()
