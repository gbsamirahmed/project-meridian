"""Synthetic metadata tests. No real observations, QC decoding or forecast errors."""

import contextlib
import csv
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import metadata_pilot as pilot


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(
            prefix="meridian-wr005-synthetic-", dir=os.environ.get("MERIDIAN_WR005_SCRATCH")
        )
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.path = self.root / "synthetic.csv"
        self.header = [[key, "G", *value] for key, value in pilot.HEADER_GLOBALS.items()]
        for column in pilot.SCHEMA:
            kind = "int" if column == "src_id" else (
                "float" if column in pilot.SCHEMA[5:] else "char"
            )
            self.header.append(["type", column, kind])
        for column, unit in (("station_latitude", "degrees"),
                             ("station_longitude", "degrees"),
                             ("station_elevation", "m"),
                             ("first_year", "year"), ("last_year", "year")):
            self.header.append(["long_name", column, "Synthetic WGS84 definition", unit])
        self.columns = list(pilot.SCHEMA)
        self.rows = [["00002", "SYNTHETIC SITE", "synthetic-site", "synthetic-county",
                      "synthetic-authority", "52", "-1", "20", "2024", "2025"]]

    def write(self, end=True, trailing=None):
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerows([*self.header, ["data"], self.columns, *self.rows])
            if end:
                writer.writerow(["end data"])
            if trailing:
                writer.writerow(trailing)

    def assert_error(self, code):
        with self.assertRaisesRegex(pilot.InputError, "^" + code + "$"):
            pilot.parse_metadata(self.path)

    def test_valid_synthetic_metadata_stays_uninterpretable(self):
        self.write()
        result = pilot.assess(pilot.parse_metadata(self.path))
        self.assertEqual(result["year_range_nominations_2025"], 1)
        self.assertEqual(result["strict_eligible_station_eras"], 0)
        self.assertIsNone(result["selected_station_era"])
        self.assertEqual(result["inventory"][0]["status"], "UNINTERPRETABLE")
        self.assertEqual(result["annual_observation_files_opened"], 0)

    def test_malformed_header(self):
        self.header.insert(0, ["title"])
        self.write()
        self.assert_error("malformed_metadata_header")

    def test_missing_column(self):
        self.columns.remove("src_id")
        self.write()
        self.assert_error("unsupported_metadata_schema")

    def test_unknown_temperature_qc_not_a_metadata_acceptance_rule(self):
        # An observation/QC column cannot smuggle a record into this metadata parser.
        self.columns.append("air_temperature_q")
        self.rows[0].append("UNKNOWN")
        self.write()
        self.assert_error("unsupported_metadata_schema")

    def test_missing_value_ambiguity(self):
        for token in ("", "NA", "NaN", "Infinity"):
            with self.subTest(token=token):
                self.rows[0][7] = token
                self.write()
                self.assert_error("unknown_metadata_numeric_or_missing_encoding")

    def test_duplicate_identity_quarantined_without_revision_guess(self):
        for identical in (True, False):
            with self.subTest(identical=identical):
                duplicate = self.rows[0].copy()
                if not identical:
                    duplicate[7] = "30"
                self.rows = [self.rows[0], duplicate]
                self.write()
                self.assert_error("duplicate_source_identity")

    def test_nominal_timestamp_cannot_supply_physical_time(self):
        self.write()
        gaps = pilot.assess(pilot.parse_metadata(self.path))["unknown_reference_requirements"]
        self.assertIn("physical_temperature_time_and_average_support_unproven", gaps)
        self.columns.append("ob_time")
        self.rows[0].append("2025-01-02 00:00:00")
        self.write()
        self.assert_error("unsupported_metadata_schema")

    def test_unsupported_station_era_assertion(self):
        self.write()
        gaps = pilot.assess(pilot.parse_metadata(self.path))["unknown_reference_requirements"]
        self.assertIn("station_era_instrument_height_and_exposure_unproven", gaps)
        self.columns.append("sensor_height_2025")
        self.rows[0].append("1.25")
        self.write()
        self.assert_error("unsupported_metadata_schema")

    def test_edition_mismatch(self):
        for row in self.header:
            if row[0] == "collection_version_number":
                row[-1] = "dataset-version-202507"
        self.write()
        self.assert_error("edition_or_product_mismatch")

    def test_ambiguous_identity_header(self):
        self.header.append(["source", "G", "Other source"])
        self.write()
        self.assert_error("ambiguous_metadata_identity")

    def test_unit_and_crs_changes(self):
        for row in self.header:
            if row[:2] == ["long_name", "station_elevation"]:
                row[-1] = "ft"
        self.write()
        self.assert_error("unsupported_metadata_units")
        for row in self.header:
            if row[:2] == ["long_name", "station_elevation"]:
                row[-1] = "m"
            if row[:2] == ["long_name", "station_latitude"]:
                row[2] = "Unspecified datum"
        self.write()
        self.assert_error("unsupported_metadata_crs")

    def test_bad_coordinates_and_years(self):
        self.rows[0][5] = "91"
        self.write()
        self.assert_error("invalid_coordinates")
        self.rows[0][5] = "52"
        self.rows[0][8] = "2026"
        self.write()
        self.assert_error("invalid_reporting_year_range")

    def test_truncation_and_trailing_records(self):
        self.write(end=False)
        self.assert_error("missing_end_data_marker")
        self.write(trailing=["unexpected"])
        self.assert_error("unexpected_trailing_content")

    def test_resource_and_shape_bounds(self):
        self.write()
        with patch.object(pilot, "MAX_INPUT_BYTES", 1):
            self.assert_error("input_size_or_type")
        with patch.object(pilot, "MAX_ROWS", 0):
            self.assert_error("metadata_row_shape_or_limit")
        self.rows[0].pop()
        self.write()
        self.assert_error("metadata_row_shape_or_limit")

    def test_commissioning_and_year_exclusions(self):
        self.rows.append([*self.rows[0]])
        self.rows[0][0] = "99999"
        self.rows[1][9] = "2024"
        self.write()
        result = pilot.assess(pilot.parse_metadata(self.path))
        self.assertEqual(result["year_range_nominations_2025"], 0)
        self.assertEqual([row["status"] for row in result["inventory"]], ["REJECT", "REJECT"])
        self.assertIn("commissioning_identifier", result["inventory"][1]["reasons"])

    def test_order_and_receipt_reproducibility(self):
        self.rows.append(self.rows[0].copy())
        self.rows[1][0] = "00001"
        self.write()
        before = pilot.fingerprint(self.path)
        first = pilot.assess(pilot.parse_metadata(self.path))
        self.assertEqual(first, pilot.assess(pilot.parse_metadata(self.path)))
        self.assertEqual([row["src_id"] for row in first["inventory"]], ["00001", "00002"])
        self.assertEqual(before, pilot.fingerprint(self.path))

    def test_missing_input_separate_from_scientific_exclusion(self):
        with self.assertRaisesRegex(pilot.InputError, "^input_unavailable$"):
            pilot.run(self.root / "absent")
        self.write()
        result = pilot.assess(pilot.parse_metadata(self.path))
        self.assertEqual(result["annual_file_gate"], "BLOCKED")

    def test_pin_mismatch(self):
        (self.root / "00README_catalogue_and_licence.txt").write_text("untrusted replacement")
        with self.assertRaisesRegex(pilot.InputError, "^pinned_input_mismatch$"):
            pilot.run(self.root)

    def test_change_log_join_is_listing_not_qc_or_history(self):
        self.write()
        records = pilot.parse_metadata(self.path)
        log = self.root / "synthetic-change-log.txt"
        log.write_text(
            "Record of changes between dataset version 202607 and dataset version 202507\n"
            "New files for year 2025. Total number of files = 1\n"
            "midas-open_uk-hourly-weather-obs_dv-202607_synthetic-county_00002_synthetic-site_qcv-1_2025.csv\n\n"
        )
        before = pilot.fingerprint(log)
        joined = pilot.inspect_change_log(log, records)
        self.assertTrue(joined["qcv1_source_ids_match_year_nominations"])
        self.assertEqual(pilot.assess(records)["strict_eligible_station_eras"], 0)
        self.assertEqual(before, pilot.fingerprint(log))
        log.write_text(log.read_text().replace("00002", "00003"))
        with self.assertRaisesRegex(pilot.InputError, "^change_log_metadata_identity_mismatch$"):
            pilot.inspect_change_log(log, records)

    def test_change_log_edition_and_count(self):
        self.write()
        records = pilot.parse_metadata(self.path)
        log = self.root / "synthetic-change-log.txt"
        log.write_text("Record of changes between dataset version 202507 and dataset version 202407\n")
        with self.assertRaisesRegex(pilot.InputError, "^change_log_edition_mismatch$"):
            pilot.inspect_change_log(log, records)
        log.write_text(
            "Record of changes between dataset version 202607 and dataset version 202507\n"
            "New files for year 2025. Total number of files = 2\n\n"
        )
        with self.assertRaisesRegex(pilot.InputError, "^change_log_count_or_duplicate$"):
            pilot.inspect_change_log(log, records)

    def test_cli_refuses_input_directory_output(self):
        with patch.object(sys, "argv", ["metadata_pilot.py", "--input-dir", str(self.root),
                                        "--receipt", str(self.root / "receipt.json")]):
            with contextlib.redirect_stderr(io.StringIO()) as captured:
                self.assertEqual(pilot.main(), 2)
        self.assertEqual(json.loads(captured.getvalue())["error"], "output_inside_input_directory")
        self.assertFalse((self.root / "receipt.json").exists())

    def test_cli_no_overwrite(self):
        target = self.root / "receipt.json"
        target.write_text("preserve this output")
        with patch.object(sys, "argv", ["metadata_pilot.py", "--input-dir", str(self.root / "inputs"),
                                        "--receipt", str(target)]):
            with patch.object(pilot, "run", return_value={}), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(pilot.main(), 2)
        self.assertEqual(target.read_text(), "preserve this output")


if __name__ == "__main__":
    unittest.main()
