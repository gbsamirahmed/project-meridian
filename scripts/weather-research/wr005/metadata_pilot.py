"""WR005 metadata-only experiment; no observation decoder or acceptance path.

Uses the inspected v202607 schema. Source bytes, first/last years and current
positions do not prove station-era eligibility. See the accompanying README.
"""

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
import sys

MAX_INPUT_BYTES = 2_000_000
MAX_ROWS = 10_000
MAX_HEADER_ROWS = 200
csv.field_size_limit(65_536)
SCHEMA = (
    "src_id", "station_name", "station_file_name", "historic_county", "authority",
    "station_latitude", "station_longitude", "station_elevation", "first_year", "last_year",
)
HEADER_GLOBALS = {
    "Conventions": ["BADC-CSV", "1"],
    "title": ["Midas-open: Station site metadata for uk-hourly-weather-obs"],
    "source": ["Met Office MIDAS database"],
    "collection_name": ["midas-open"],
    "collection_version_number": ["dataset-version-202607"],
}
# Absence of these facts is a property of the inspected metadata product, not a
# finding that stations have bad instruments or missing meteorological values.
REFERENCE_GAPS = (
    "historical_location_and_elevation_support_unproven",
    "station_era_instrument_height_and_exposure_unproven",
    "historical_reporting_capability_unproven",
    "physical_temperature_time_and_average_support_unproven",
    "temperature_qc_j_state_missing_and_revision_encoding_unverified",
    "planned_valid_time_availability_unverified",
    "study_domain_not_frozen",
)


class InputError(ValueError):
    """A bounded error code, without source paths or raw records."""


def fingerprint(path):
    try:
        size = path.stat().st_size
        if not path.is_file() or size > MAX_INPUT_BYTES:
            raise InputError("input_size_or_type")
        digest = hashlib.sha256()
        total = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(65_536), b""):
                total += len(chunk)
                if total > MAX_INPUT_BYTES:
                    raise InputError("input_size_or_type")
                digest.update(chunk)
        if size != total:
            raise InputError("input_changed_during_hash")
        return {"bytes": total, "sha256": digest.hexdigest()}
    except OSError as exc:
        raise InputError("input_unavailable") from exc


def parse_metadata(path):
    """Parse only the documented metadata schema; never guess missing tokens."""
    fingerprint(path)  # Bound allocation before parsing, including standalone tests.
    globals_seen, attributes = {}, {}
    records, identifiers = [], set()
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.reader(stream, strict=True)
            for index, row in enumerate(reader):
                if index >= MAX_HEADER_ROWS:
                    raise InputError("metadata_header_limit")
                if row == ["data"]:
                    break
                if len(row) < 3:
                    raise InputError("malformed_metadata_header")
                if row[1] == "G" and row[0] in HEADER_GLOBALS:
                    if row[0] in globals_seen:
                        raise InputError("ambiguous_metadata_identity")
                    globals_seen[row[0]] = row[2:]
                if row[0] in ("long_name", "type"):
                    key = (row[0], row[1])
                    if key in attributes:
                        raise InputError("ambiguous_column_definition")
                    attributes[key] = row[2:]
            else:
                raise InputError("missing_data_marker")
            if globals_seen != HEADER_GLOBALS:
                raise InputError("edition_or_product_mismatch")
            if tuple(next(reader, [])) != SCHEMA:
                raise InputError("unsupported_metadata_schema")
            for column in SCHEMA:
                expected_type = "int" if column == "src_id" else (
                    "float" if column in SCHEMA[5:] else "char"
                )
                if attributes.get(("type", column)) != [expected_type]:
                    raise InputError("unsupported_column_type")
            for column, unit in (("station_latitude", "degrees"),
                                 ("station_longitude", "degrees"),
                                 ("station_elevation", "m"),
                                 ("first_year", "year"), ("last_year", "year")):
                definition = attributes.get(("long_name", column), [])
                if len(definition) != 2 or definition[-1] != unit:
                    raise InputError("unsupported_metadata_units")
                if column.startswith("station_l") and "WGS84" not in definition[0]:
                    raise InputError("unsupported_metadata_crs")
            for row in reader:
                if row == ["end data"]:
                    if any(extra for extra in reader):
                        raise InputError("unexpected_trailing_content")
                    break
                if len(records) >= MAX_ROWS or len(row) != len(SCHEMA):
                    raise InputError("metadata_row_shape_or_limit")
                record = dict(zip(SCHEMA, row))
                source = record["src_id"]
                if not source.isascii() or not source.isdecimal() or len(source) != 5:
                    raise InputError("invalid_source_identity")
                if source in identifiers:
                    raise InputError("duplicate_source_identity")
                identifiers.add(source)
                for column in SCHEMA[5:]:
                    try:
                        value = float(record[column])
                    except ValueError as exc:
                        raise InputError("unknown_metadata_numeric_or_missing_encoding") from exc
                    if not math.isfinite(value):
                        raise InputError("unknown_metadata_numeric_or_missing_encoding")
                    record[column] = value
                lat, lon = record["station_latitude"], record["station_longitude"]
                first, last = record["first_year"], record["last_year"]
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise InputError("invalid_coordinates")
                if not (first.is_integer() and last.is_integer() and 1 <= first <= last <= 2025):
                    raise InputError("invalid_reporting_year_range")
                records.append(record)
            else:
                raise InputError("missing_end_data_marker")
    except (csv.Error, UnicodeError) as exc:
        raise InputError("malformed_csv_or_encoding") from exc
    except OSError as exc:
        raise InputError("input_unavailable") from exc
    if not records:
        raise InputError("empty_metadata")
    return sorted(records, key=lambda record: int(record["src_id"]))


def assess(records):
    """An error-blind eligibility receipt, without location/name/value disclosure."""
    inventory = []
    nominations = 0
    for record in records:
        source = record["src_id"]
        if source == "99999":
            status, reasons = "REJECT", ["commissioning_identifier"]
        elif not record["first_year"] <= 2025 <= record["last_year"]:
            status, reasons = "REJECT", ["year_range_does_not_nominate_2025"]
        else:
            nominations += 1
            status, reasons = "UNINTERPRETABLE", list(REFERENCE_GAPS)
        inventory.append({"src_id": source, "status": status, "reasons": reasons})
    return {
        "metadata_rows": len(records), "unique_source_ids": len(records),
        "year_range_nominations_2025": nominations,
        "strict_eligible_station_eras": 0, "selected_station_era": None,
        "annual_file_gate": "BLOCKED", "annual_observation_files_opened": 0,
        "reference_records_accepted": 0, "reference_records_examined": 0,
        "unknown_reference_requirements": list(REFERENCE_GAPS),
        "selection_order": "numeric src_id, then historical era start if evidenced; take at most one eligible era",
        "inventory": inventory,
    }


def inspect_change_log(path, records):
    """Join listed 2025 filenames to metadata; never open the listed objects."""
    fingerprint(path)
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise InputError("change_log_unavailable_or_encoding") from exc
    if not lines or lines[0] != "Record of changes between dataset version 202607 and dataset version 202507":
        raise InputError("change_log_edition_mismatch")
    starts = [(i, re.fullmatch(r"New files for year 2025\. Total number of files = (\d+)", line))
              for i, line in enumerate(lines)]
    starts = [(i, match) for i, match in starts if match]
    if len(starts) != 1:
        raise InputError("change_log_section_ambiguous")
    index, match = starts[0]
    count = int(match.group(1))
    names = []
    for line in lines[index + 1:]:
        if not line:
            break
        names.append(line)
    if len(names) != count or len(set(names)) != count:
        raise InputError("change_log_count_or_duplicate")
    by_id = {record["src_id"]: record for record in records}
    qcv_counts, qcv1_ids, listed_ids = {"0": 0, "1": 0}, set(), set()
    for name in names:
        entry = re.fullmatch(
            r"midas-open_uk-hourly-weather-obs_dv-202607_([^_]+)_(\d{5})_(.+)_qcv-([01])_2025\.csv", name
        )
        if not entry:
            raise InputError("unsupported_change_log_filename")
        county, source, station_name, qcv = entry.groups()
        record = by_id.get(source)
        if not record or county != record["historic_county"] or station_name != record["station_file_name"]:
            raise InputError("change_log_metadata_identity_mismatch")
        qcv_counts[qcv] += 1
        listed_ids.add(source)
        if qcv == "1":
            qcv1_ids.add(source)
    nominations = {r["src_id"] for r in records if r["first_year"] <= 2025 <= r["last_year"] and r["src_id"] != "99999"}
    return {
        "listed_new_2025_files": count, "listed_qcv_counts": qcv_counts,
        "listed_2025_source_ids": len(listed_ids),
        "qcv1_source_ids_match_year_nominations": qcv1_ids == nominations,
        "interpretation": "release-change-log filenames inspected; object presence, contents, passed QC and station-era continuity NOT verified",
    }


def run(input_dir):
    pins = json.loads(Path(__file__).with_name("input-pins.json").read_text(encoding="utf-8"))
    identities = {}
    for name, expected in pins["files"].items():
        identities[name] = fingerprint(input_dir / name)
        if identities[name] != expected:
            raise InputError("pinned_input_mismatch")
    metadata = next(name for name in pins["files"] if name.endswith("station-metadata.csv"))
    records = parse_metadata(input_dir / metadata)
    result = assess(records)
    change_log = next(name for name in pins["files"] if name.endswith("change_log.txt"))
    result["change_log_join"] = inspect_change_log(input_dir / change_log, records)
    for name, identity in identities.items():
        if fingerprint(input_dir / name) != identity:
            raise InputError("input_changed_during_inspection")
    return {
        "receipt_schema": "meridian-weather-wr005-metadata-v1",
        "edition": pins["edition"], "doi": pins["doi"],
        "outcome": "B — PARTIAL INTERPRETATION", "input_files": identities,
        "network_requests": 0, "network_transfer_bytes": 0,
        "provenance": "user-supplied local copies; download session/date and provider checksum not captured",
        **result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    try:
        # Never write into the immutable input directory or overwrite an output.
        if args.receipt.resolve().is_relative_to(args.input_dir.resolve()):
            raise InputError("output_inside_input_directory")
        result = run(args.input_dir)
        with args.receipt.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({key: result[key] for key in (
            "outcome", "metadata_rows", "year_range_nominations_2025",
            "strict_eligible_station_eras", "annual_file_gate",
        )}, ensure_ascii=False))
        return 0  # Successful metadata experiment; NOT successful reference eligibility.
    except (InputError, OSError) as exc:
        code = str(exc) if isinstance(exc, InputError) else "output_unavailable_or_exists"
        print(json.dumps({"outcome": "C — BLOCKED", "error": code}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
