"""Explicitly synthetic guards, plus one opt-in real historical-field replay."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import gfs_precipitation_pilot as pilot


class SyntheticMetadataAndNumerics(unittest.TestCase):
    """Copies of the finite metadata profile are synthetic mutations, not forecasts."""
    def setUp(self):
        self.pin = json.loads(pilot.PIN.read_text(encoding="utf-8"))
        self.m = copy.deepcopy(self.pin["expected"])

    def rejects(self, **changes):
        self.m.update(changes)
        with self.assertRaises(pilot.IntegrityError): pilot.interval(self.m)

    def test_utc_interval_crosses_midnight(self):
        v = pilot.interval(self.m)
        self.assertEqual(v["interval_start"], "2025-01-15T18:00:00Z")
        self.assertEqual(v["interval_end"], "2025-01-16T00:00:00Z")

    def test_lead_is_not_duration(self):
        v = pilot.interval(self.m)
        self.assertEqual(v["forecast_lead_to_end_seconds"], 86400)
        self.assertEqual(v["interval_duration_seconds"], 21600)

    def test_documented_fixed_time_units(self):
        self.assertEqual([pilot.seconds(2, k) for k in [0, 1, 2, 10, 11, 12, 13]],
                         [120, 7200, 172800, 21600, 43200, 86400, 2])

    def test_equivalent_duration_in_minutes(self):
        self.m.update(lengthOfTimeRange=360, indicatorOfUnitForTimeRange=0)
        self.assertEqual(pilot.interval(self.m)["interval_duration_seconds"], 21600)

    def test_calendar_unit_unsupported(self): self.rejects(indicatorOfUnitForTimeRange=3)
    def test_missing_time_unit_unsupported(self): self.rejects(indicatorOfUnitForTimeRange=255)
    def test_float_time_not_silently_truncated(self): self.rejects(forecastTime=18.1)
    def test_boolean_time_rejected(self): self.rejects(timeIncrement=False)
    def test_negative_time_rejected(self): self.rejects(lengthOfTimeRange=-6)
    def test_zero_duration_rejected(self): self.rejects(lengthOfTimeRange=0)
    def test_average_not_accumulation(self): self.rejects(typeOfStatisticalProcessing=0)
    def test_instantaneous_template_rejected(self): self.rejects(productDefinitionTemplateNumber=0)
    def test_multiple_time_ranges_unsupported(self): self.rejects(numberOfTimeRange=2)
    def test_missing_statistical_inputs_rejected(self): self.rejects(numberOfMissingInStatisticalProcess=1)
    def test_floating_subinterval_unsupported(self): self.rejects(typeOfTimeIncrement=5)
    def test_discrete_increment_unsupported(self): self.rejects(timeIncrement=1)
    def test_unknown_step_type_rejected(self): self.rejects(stepType="instant")
    def test_interval_end_conflict_rejected(self): self.rejects(hourOfEndOfOverallTimeInterval=1)
    def test_valid_time_conflict_rejected(self): self.rejects(validityTime=100)
    def test_start_alias_conflict_rejected(self): self.rejects(startStep=0)
    def test_end_alias_conflict_rejected(self): self.rejects(endStep=18)
    def test_invalid_calendar_date_rejected(self): self.rejects(dayOfEndOfOverallTimeInterval=32)

    def test_missing_metadata_rejected(self):
        del self.m["lengthOfTimeRange"]
        with self.assertRaises(pilot.IntegrityError): pilot.interval(self.m)

    def test_water_equivalent_conversion_labelled(self):
        self.assertEqual(pilot.water_equivalent_mm(12.5, "kg m**-2"), 12.5)

    def test_rate_not_mass_amount(self):
        with self.assertRaises(pilot.IntegrityError): pilot.water_equivalent_mm(1, "kg m**-2 s**-1")

    def test_nonfinite_conversion_rejected(self):
        with self.assertRaises(pilot.IntegrityError): pilot.water_equivalent_mm(float("nan"), "kg m**-2")

    def arrays(self):
        a = np.array([[0, .0625], [2.5, 100.]])
        return a, a.copy(), np.zeros(a.shape, dtype=bool)

    def test_exact_binary_scaling_agreement(self):
        a, b, mask = self.arrays()
        self.assertEqual(pilot.compare_arrays(a, b, mask, mask, self.m)["compared_cells"], 4)

    def test_decoder_difference_not_hidden(self):
        a, b, mask = self.arrays(); b[1, 1] = np.nextafter(b[1, 1], float("inf"))
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.m)

    def test_unmasked_nonfinite_rejected(self):
        a, b, mask = self.arrays(); a[1, 1] = float("nan")
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.m)

    def test_mask_disagreement_rejected(self):
        a, b, mask = self.arrays(); other = mask.copy(); other[1, 1] = True
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, other, self.m)

    def test_explicit_mask_not_guessed_sentinel(self):
        a, b, mask = self.arrays(); mask[1, 1] = True; a[1, 1] = float("nan"); b[1, 1] = -9999
        self.assertEqual(pilot.compare_arrays(a, b, mask, mask, self.m)["compared_cells"], 3)

    def test_wrong_dimensions_rejected(self):
        a, b, mask = self.arrays()
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b[:, :1], mask, mask, self.m)

    def test_unsupported_scale_rejected(self):
        a, b, mask = self.arrays(); self.m["decimalScaleFactor"] = 1
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.m)

    def test_fractional_lattice_rejected(self):
        a, b, mask = self.arrays(); a[0, 0] = .001
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.m)

    def test_negative_not_clamped(self):
        a, b, mask = self.arrays(); a[0, 0] = -.0625
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.m)

    def test_integer_beyond_binary32_proof_rejected(self):
        a, b, mask = self.arrays(); a[0, 0] = 2**24 / 16
        with self.assertRaises(pilot.IntegrityError): pilot.compare_arrays(a, b, mask, mask, self.m)

    def synthetic_message(self):
        # Framing and documented PDT bytes only; no real numerical GRIB payload.
        chunks = {i: bytearray(5) for i in [1, 3, 4, 5, 6, 7]}; chunks[4] = bytearray(58)
        for i, chunk in chunks.items(): chunk[:4] = len(chunk).to_bytes(4, "big"); chunk[4] = i
        chunks[4][7:9] = (8).to_bytes(2, "big")
        b = b"GRIB\0\0\0\2" + (20+sum(len(c) for c in chunks.values())).to_bytes(8, "big")
        return b+b"".join(chunks.values())+b"7777"

    def test_truncated_message_rejected(self):
        with self.assertRaises(pilot.IntegrityError): pilot.sections(self.synthetic_message()[:-1])

    def test_concatenated_message_rejected(self):
        with self.assertRaises(pilot.IntegrityError): pilot.sections(self.synthetic_message()*2)

    def test_raw_template_conflict_rejected(self):
        raw = pilot.sections(self.synthetic_message())[4]
        with self.assertRaises(pilot.IntegrityError): pilot.check_section4(raw, self.m)

    def test_grid_coercion_rejected(self):
        self.m["Ni"] = 1439
        with self.assertRaises(pilot.IntegrityError): pilot.grid_compatibility(self.m, self.pin, b"synthetic")

    def test_receipt_serialisation_is_deterministic(self):
        self.assertEqual(pilot.canonical({"a": 1, "b": pilot.interval(self.m)}),
                         pilot.canonical({"b": pilot.interval(self.m), "a": 1}))

    def test_checksum_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as n:
            p = Path(n)/"synthetic.grib2"; p.write_bytes(self.synthetic_message())
            pin = {"input": {"bytes": p.stat().st_size, "sha256": "0"*64}}
            with self.assertRaises(pilot.IntegrityError): pilot.field.pinned_input(p, pin)

    def test_repository_output_rejected(self):
        with self.assertRaises(pilot.IntegrityError): pilot.field.require_external(pilot.HERE/"scratch.json")

    def test_wrong_parameter_identity_rejected(self):
        self.m["parameterNumber"] = 7
        with self.assertRaises(pilot.IntegrityError): pilot.field.validate_metadata(self.m, self.pin)

    def test_wrong_vertical_level_rejected(self):
        self.m["typeOfFirstFixedSurface"] = 103
        with self.assertRaises(pilot.IntegrityError): pilot.field.validate_metadata(self.m, self.pin)

    def test_wrong_reference_cycle_rejected(self):
        self.m["dataTime"] = 600
        with self.assertRaises(pilot.IntegrityError): pilot.field.validate_metadata(self.m, self.pin)

    def test_wrong_units_rejected(self):
        self.m["units"] = "mm/h"
        with self.assertRaises(pilot.IntegrityError): pilot.field.validate_metadata(self.m, self.pin)

    def test_scratch_ceiling_fails_closed(self):
        with tempfile.TemporaryDirectory() as n:
            with patch.object(Path, "rglob", return_value=[Path(n)]), patch.object(Path, "is_file", return_value=True), \
                 patch.object(Path, "stat") as stat:
                stat.return_value.st_size = 131_000_000
                with self.assertRaises(pilot.IntegrityError): pilot.scratch_room(n)


@unittest.skipUnless(os.environ.get("MERIDIAN_WR009_INPUT") and os.environ.get("MERIDIAN_WR007_GDAL_PYTHON"),
                     "Opt-in pinned external APCP field and existing independent interpreter required")
class RealHistoricalField(unittest.TestCase):
    def test_actual_receipt_replay_input_immutability_and_interval(self):
        source = Path(os.environ["MERIDIAN_WR009_INPUT"]); original = pilot.digest(source)
        accepted = json.loads(pilot.PIN.with_name("integrity-receipt.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as n:
            paths = [Path(n)/f"receipt-{i}.json" for i in range(2)]
            for out in paths:
                v = pilot.run(source, os.environ["MERIDIAN_WR007_GDAL_PYTHON"], out)
                self.assertEqual(v["independent_comparison"]["bit_identical_cells"], 1038240)
                self.assertEqual(v["temporal_support"]["interval_duration_seconds"], 21600)
                self.assertEqual(v["statistics_native_kg_per_m2"]["missing_cells"], 0)
                self.assertEqual(pilot.digest(out), accepted["full_scientific_receipt"]["sha256"])
                with self.assertRaises(pilot.IntegrityError): pilot.run(source, os.environ["MERIDIAN_WR007_GDAL_PYTHON"], out)
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
        self.assertEqual(pilot.digest(source), original)


if __name__ == "__main__": unittest.main()
