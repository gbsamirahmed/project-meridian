"""WR006 pinned evidence audit; no observation decoder or eligibility engine.

The C decisions describe this inspected bundle, not every MIDAS station. New
history/dictionaries require a separate review; they cannot silently pass here.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

SPEC = importlib.util.spec_from_file_location(
    "wr005_pinned_metadata", Path(__file__).resolve().parents[1] / "wr005/metadata_pilot.py"
)
metadata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metadata)
InputError = metadata.InputError
CHECKPOINT = "8a432d80afd3888dee82f23a42996a66fdaea283"
PROFILE = {
    "edition": "202607",
    "audit_group": "historic_county == caithness",
    "year": 2025,
    "exclude_src_id": ["99999"],
    "order": "ascending numeric src_id; no replacement",
    "intended_interval_utc": ["2025-01-01T00:00:00Z", "2025-02-02T00:00:00Z"],
    "interpretation": "metadata audit nomination, NOT historically eligible era or verification cohort",
}
GAPS = [
    "dated_station_location_equipment_and_identity_history_unavailable",
    "historical_temperature_sensor_height_unproven",
    "historical_physical_temperature_time_and_averaging_unproven",
    "edition_header_missing_codes_qc_and_revision_applicability_unverified",
    "actual_reference_records_uninspected",
]


def nominate(records):
    """Freeze an audit subject, never an eligible historical thermometer."""
    nominees = sorted(
        (r for r in records if r["historic_county"] == "caithness"
         and r["src_id"] != "99999" and r["first_year"] <= 2025 <= r["last_year"]),
        key=lambda r: int(r["src_id"]),
    )
    if not nominees:
        raise InputError("no_audit_nominee")
    if nominees[0]["src_id"] != "00032":
        raise InputError("audit_candidate_changed_no_substitution")
    return nominees[0], len(nominees)


def freeze(input_dir):
    verified = metadata.run(input_dir)
    name = next(n for n in verified["input_files"] if n.endswith("station-metadata.csv"))
    candidate, count = nominate(metadata.parse_metadata(input_dir / name))
    # Retain WR005 byte identities and its explicit lack of historical support.
    return {
        "schema": "meridian-weather-wr006-frozen-audit-selection-v1",
        "starting_checkpoint": CHECKPOINT, "profile": PROFILE,
        "inputs": verified["input_files"], "audit_group_nominations": count,
        "candidate": candidate, "annual_files_opened": 0,
        "observation_values_examined": 0,
    }


def validate_frozen(supplied, expected):
    # Equality rejects added height/time/QC/history claims as well as changed IDs.
    if supplied != expected:
        raise InputError("frozen_selection_changed_or_unsupported_assertion")


def load_json(path):
    metadata.fingerprint(path)
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError("malformed_or_unavailable_receipt") from exc


def audit(input_dir, frozen_path, public_dir):
    frozen_identity = metadata.fingerprint(frozen_path)
    expected = freeze(input_dir)
    validate_frozen(load_json(frozen_path), expected)
    pins = load_json(Path(__file__).with_name("public-evidence-pins.json"))
    identities = {}
    for entry in pins["requests"]:
        name = entry["saved_as"]
        actual = metadata.fingerprint(public_dir / name)
        if actual != {"bytes": entry["body_bytes"], "sha256": entry["sha256"]}:
            raise InputError("public_evidence_pin_mismatch")
        identities[name] = actual
    for name, identity in identities.items():
        if metadata.fingerprint(public_dir / name) != identity:
            raise InputError("public_evidence_changed_during_audit")
    if metadata.fingerprint(frozen_path) != frozen_identity or freeze(input_dir) != expected:
        raise InputError("selection_or_input_changed_during_audit")
    return {
        "schema": "meridian-weather-wr006-evidence-audit-v1",
        "selection": expected, "frozen_selection_identity": frozen_identity,
        "public_evidence": identities,
        "interpretation": "reproduces the report's manually reviewed bounded evidence decision; not automated scientific validation",
        "scientific_outcome": "C — EVIDENCE BLOCKED",
        "reference_target_decision": "C — STRICT AND REVISED TARGETS BLOCKED",
        "historically_eligible_eras_established": 0,
        "support_gaps": GAPS,
        "qc_documentary_refinement": "historical MESQL layout and temperature descriptors read; no v202607 real-record acceptance rule",
        "annual_files_opened": 0, "observation_values_examined": 0,
        "reference_records_accepted": 0, "forecast_files_opened": 0,
        "audit_network_requests": 0, "audit_network_bytes": 0,
        "prior_public_retrieval_requests": len(pins["requests"]),
        "prior_public_retrieval_body_bytes": sum(e["body_bytes"] for e in pins["requests"]),
    }


def write_receipt(path, result, protected):
    output = path.resolve()
    repository = Path(__file__).resolve().parents[3]
    if output.is_relative_to(repository) or any(output.is_relative_to(p.resolve()) for p in protected):
        raise InputError("output_inside_repository_or_input_directory")
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["freeze", "audit"])
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--frozen-selection", type=Path)
    parser.add_argument("--public-evidence-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "audit":
            if args.frozen_selection is None or args.public_evidence_dir is None:
                raise InputError("audit_requires_frozen_selection_and_public_evidence")
            result = audit(args.input_dir, args.frozen_selection, args.public_evidence_dir)
            protected = [args.input_dir, args.public_evidence_dir]
        else:
            result, protected = freeze(args.input_dir), [args.input_dir]
        write_receipt(args.receipt, result, protected)
        print(json.dumps({"src_id": "00032", "mode": args.mode,
                          "meaning": "audit nomination only; no eligible era established"}))
        return 0
    except (InputError, OSError) as exc:
        code = str(exc) if isinstance(exc, InputError) else "output_unavailable_or_exists"
        print(json.dumps({"error": code}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
