"""Synthetic selection/assertion/output tests; no historical station fixtures."""

import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import measurement_support as pilot


def synthetic(source="00032", county="caithness", first=2024, last=2025):
    return {"src_id": source, "historic_county": county,
            "first_year": first, "last_year": last, "station_name": "SYNTHETIC"}


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.expected = {"candidate": synthetic(), "profile": copy.deepcopy(pilot.PROFILE)}

    def test_order_and_error_blind_group(self):
        rows = [synthetic("00070"), synthetic("00001", "elsewhere"), synthetic()]
        chosen, count = pilot.nominate(rows)
        self.assertEqual(chosen["src_id"], "00032")
        self.assertEqual(count, 2)
        self.assertEqual(pilot.nominate(list(reversed(rows))), (chosen, count))
        self.assertNotIn("temperature", chosen)

    def test_year_range_and_commissioning_exclusion(self):
        chosen, count = pilot.nominate([
            synthetic("00001", last=2024), synthetic("00002", first=2026, last=2026),
            synthetic("99999"), synthetic(),
        ])
        self.assertEqual((chosen["src_id"], count), ("00032", 1))

    def test_no_nominee_is_not_empty_eligible_series(self):
        with self.assertRaisesRegex(pilot.InputError, "no_audit_nominee"):
            pilot.nominate([synthetic(county="elsewhere")])

    def test_changed_first_candidate_cannot_fall_back(self):
        with self.assertRaisesRegex(pilot.InputError, "no_substitution"):
            pilot.nominate([synthetic("00031"), synthetic()])

    def assert_unsupported(self, supplied):
        with self.assertRaisesRegex(pilot.InputError, "unsupported_assertion"):
            pilot.validate_frozen(supplied, self.expected)

    def test_network_height_cannot_become_historical_fact(self):
        supplied = copy.deepcopy(self.expected)
        supplied["candidate"]["historical_sensor_height_m"] = 1.25
        self.assert_unsupported(supplied)

    def test_nominal_time_cannot_become_physical_time(self):
        supplied = copy.deepcopy(self.expected)
        supplied["candidate"]["physical_time_offset_minutes"] = -10
        self.assert_unsupported(supplied)

    def test_unverified_qc_cannot_become_accepted(self):
        supplied = copy.deepcopy(self.expected)
        supplied["candidate"]["temperature_qc"] = "ACCEPT"
        self.assert_unsupported(supplied)

    def test_period_or_candidate_replacement_rejected(self):
        for change in ("period", "candidate"):
            supplied = copy.deepcopy(self.expected)
            if change == "period":
                supplied["profile"]["year"] = 2024
            else:
                supplied["candidate"]["src_id"] = "00070"
            self.assert_unsupported(supplied)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(
            prefix="wr006-synthetic-", dir=os.environ.get("MERIDIAN_WR006_SCRATCH")
        )
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)

    def test_input_and_repository_output_rejected(self):
        for target in (self.root / "new.json", Path(pilot.__file__).with_name("forbidden.json")):
            with self.assertRaisesRegex(pilot.InputError, "output_inside"):
                pilot.write_receipt(target, {}, [self.root])
            self.assertFalse(target.exists())

    def test_no_overwrite(self):
        out = self.root / "receipt.json"
        pilot.write_receipt(out, {"synthetic": True}, [])
        original = out.read_bytes()
        with self.assertRaises(FileExistsError):
            pilot.write_receipt(out, {"synthetic": False}, [])
        self.assertEqual(out.read_bytes(), original)

    def test_malformed_frozen_receipt(self):
        file = self.root / "bad.json"
        file.write_text("not JSON", encoding="utf-8")
        with self.assertRaisesRegex(pilot.InputError, "malformed_or_unavailable"):
            pilot.load_json(file)

    def test_altered_public_body_fails_pin_check(self):
        file = self.root / "selection.json"
        file.write_text("{}", encoding="utf-8")
        body = self.root / "synthetic.html"
        body.write_text("altered synthetic text", encoding="utf-8")
        pins = {"requests": [{"saved_as": body.name, "body_bytes": 1, "sha256": "0" * 64}]}
        original = pilot.load_json
        def load(path):
            return pins if path.name == "public-evidence-pins.json" else original(path)
        with patch.object(pilot, "freeze", return_value={}), patch.object(pilot, "load_json", side_effect=load):
            with self.assertRaisesRegex(pilot.InputError, "public_evidence_pin_mismatch"):
                pilot.audit(self.root, file, self.root)


if __name__ == "__main__":
    unittest.main()
