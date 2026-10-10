"""WR009: one pinned accumulation, isolated from production Weather behaviour."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "wr007"))
import gfs_field_pilot as field
sys.path.insert(0, str(HERE.parent / "wr008"))
from gfs_point_sampling import process_memory

PIN = HERE / "input-pins.json"
IntegrityError = field.IntegrityError
canonical = field.canonical
digest = field.digest
UTC = timezone.utc
TIME_SECONDS = {0: 60, 1: 3600, 2: 86400, 10: 10800, 11: 21600, 12: 43200, 13: 1}


def checked_integer(value):
    if type(value) is not int or value < 0:
        raise IntegrityError("Missing, non-integer or negative temporal value")
    return value


def seconds(value, unit):
    checked_integer(value)
    if type(unit) is not int or unit not in TIME_SECONDS:
        raise IntegrityError("Unsupported time unit; calendar/missing/local units not guessed")
    return value * TIME_SECONDS[unit]


def stamp(value):
    return value.isoformat().replace("+00:00", "Z")


def interval(metadata):
    """Finite PDT 4.8, one-range accumulation; no generic statistical decoder."""
    m = metadata
    try:
        for key, wanted in {"productDefinitionTemplateNumber": 8, "typeOfStatisticalProcessing": 1,
                            "numberOfTimeRange": 1, "numberOfMissingInStatisticalProcess": 0,
                            "typeOfTimeIncrement": 2, "timeIncrement": 0,
                            "indicatorOfUnitForTimeIncrement": 255}.items():
            if type(m[key]) is not int or m[key] != wanted:
                raise IntegrityError(f"Unsupported statistical/time profile: {key}")
        if m["stepType"] != "accum":
            raise IntegrityError("Not an accumulation")
        reference = datetime.strptime(f'{checked_integer(m["dataDate"]):08d}{checked_integer(m["dataTime"]):04d}',
                                      "%Y%m%d%H%M").replace(tzinfo=UTC)
        start_seconds = seconds(m["forecastTime"], m["indicatorOfUnitOfTimeRange"])
        duration = seconds(m["lengthOfTimeRange"], m["indicatorOfUnitForTimeRange"])
        if duration <= 0:
            raise IntegrityError("Accumulation interval must have positive duration")
        start = reference + timedelta(seconds=start_seconds)
        end = datetime(*(checked_integer(m[k]) for k in ["yearOfEndOfOverallTimeInterval",
                       "monthOfEndOfOverallTimeInterval", "dayOfEndOfOverallTimeInterval",
                       "hourOfEndOfOverallTimeInterval", "minuteOfEndOfOverallTimeInterval",
                       "secondOfEndOfOverallTimeInterval"]), tzinfo=UTC)
        valid = datetime.strptime(f'{checked_integer(m["validityDate"]):08d}{checked_integer(m["validityTime"]):04d}',
                                  "%Y%m%d%H%M").replace(tzinfo=UTC)
        if end != start + timedelta(seconds=duration) or valid != end:
            raise IntegrityError("Interval bounds/duration/valid time disagree")
        if seconds(m["startStep"], m["stepUnits"]) != start_seconds:
            raise IntegrityError("ecCodes startStep disagrees with encoded forecastTime")
        lead_seconds = int((end-reference).total_seconds())
        if seconds(m["endStep"], m["stepUnits"]) != lead_seconds:
            raise IntegrityError("ecCodes endStep disagrees with explicit interval end")
    except (KeyError, TypeError, ValueError, OverflowError) as e:
        if isinstance(e, IntegrityError):
            raise
        raise IntegrityError("Incomplete or invalid interval metadata") from e
    return {"kind": "accumulation", "reference_time": stamp(reference),
            "interval_start": stamp(start), "interval_end": stamp(end), "valid_time": stamp(valid),
            "interval_duration_seconds": duration, "forecast_lead_to_start_seconds": start_seconds,
            "forecast_lead_to_end_seconds": lead_seconds, "statistical_process_code": 1,
            "time_increment_type_code": 2, "time_increment": 0,
            "increment_unit": "255: missing/not specified; zero increment denotes continuous or near-continuous processing",
            "support_qualification": "model accumulation over the encoded interval; no within-interval intensity/timing"}


def sections(body):
    field.validate_framing(body)
    found = {}; offset = 16
    while offset < len(body)-4:
        size = int.from_bytes(body[offset:offset+4], "big")
        if size < 5 or offset+size > len(body)-4:
            raise IntegrityError("Malformed GRIB section extent")
        number = body[offset+4]
        if number in found:
            raise IntegrityError("Repeated section; multi-field payload unsupported")
        found[number] = body[offset:offset+size]; offset += size
    if offset != len(body)-4 or list(found) != [1, 3, 4, 5, 6, 7]:
        raise IntegrityError("Unexpected section layout")
    return found


def check_section4(section, metadata):
    """Read only documented fixed PDT 4.8 octets; does not unpack numerical data."""
    if len(section) != 58 or section[4] != 4 or int.from_bytes(section[7:9], "big") != 8:
        raise IntegrityError("Unsupported Section 4 template/length")
    fields = {"parameterCategory": (10, 1), "parameterNumber": (11, 1),
              "indicatorOfUnitOfTimeRange": (18, 1), "forecastTime": (19, 4),
              "typeOfFirstFixedSurface": (23, 1), "yearOfEndOfOverallTimeInterval": (35, 2),
              "monthOfEndOfOverallTimeInterval": (37, 1), "dayOfEndOfOverallTimeInterval": (38, 1),
              "hourOfEndOfOverallTimeInterval": (39, 1), "minuteOfEndOfOverallTimeInterval": (40, 1),
              "secondOfEndOfOverallTimeInterval": (41, 1), "numberOfTimeRange": (42, 1),
              "numberOfMissingInStatisticalProcess": (43, 4), "typeOfStatisticalProcessing": (47, 1),
              "typeOfTimeIncrement": (48, 1), "indicatorOfUnitForTimeRange": (49, 1),
              "lengthOfTimeRange": (50, 4), "indicatorOfUnitForTimeIncrement": (54, 1),
              "timeIncrement": (55, 4)}
    encoded = {k: int.from_bytes(section[o-1:o-1+n], "big") for k, (o, n) in fields.items()}
    if any(metadata.get(k) != v for k, v in encoded.items()):
        raise IntegrityError("Raw PDT octets/ecCodes metadata disagree")
    return encoded


def grid_compatibility(metadata, pin, section3):
    if any(metadata.get(k) != pin["temperature_grid"][k] for k in pin["grid_keys"]):
        raise IntegrityError("Temperature/precipitation grid metadata differ")
    seal = hashlib.sha256(section3).hexdigest()
    if seal != pin["section3_sha256"] or seal != pin["temperature_section3_sha256"]:
        raise IntegrityError("Raw grid definition differs")
    return {"status": "IDENTICAL ENCODED SECTION 3 AND CHECKED NATIVE COORDINATES",
            "section3_sha256": seal, "metadata": pin["temperature_grid"],
            "temperature_input": pin["temperature_input"],
            "reuse": "WR008 angular-nearest/qualified-bilinear geometry only; accumulation support must accompany every value",
            "point_sampling_executed": False}


def water_equivalent_mm(value, unit):
    # A narrowly labelled unit example, never an implicit field conversion.
    if unit != "kg m**-2" or type(value) not in (int, float) or not math.isfinite(value):
        raise IntegrityError("Unsupported mass-per-area conversion")
    return value / 1000.0 * 1000.0  # depth m at stipulated water density 1000 kg/m3 -> mm


def compare_arrays(a, b, mask, other, metadata):
    if a.shape != b.shape or a.shape != mask.shape or other.shape != mask.shape:
        raise IntegrityError("Decoder dimensions/orientation disagree")
    if not np.array_equal(mask, other):
        raise IntegrityError("Decoder missingness masks disagree")
    if (metadata["referenceValue"], metadata["binaryScaleFactor"], metadata["decimalScaleFactor"]) != (0, -4, 0):
        raise IntegrityError("Unsupported numerical scaling profile")
    aa, bb = a[~mask], b[~mask]
    if not aa.size or not np.all(np.isfinite(aa)) or not np.all(np.isfinite(bb)):
        raise IntegrityError("Non-finite/empty unmasked field")
    integers = aa * 16
    if not np.array_equal(integers, np.rint(integers)) or np.any(integers < 0) or np.any(integers >= 2**24):
        raise IntegrityError("Values outside supported exact binary32 integer lattice")
    predicted = (integers.astype(np.float32) * np.float32(2**-4)).astype(np.float64)
    if not np.array_equal(predicted, aa) or not np.array_equal(aa, bb):
        raise IntegrityError("Independent decoder disagreement; zero tolerance for this exact scaling")
    differences = np.abs(aa-bb)
    return {"compared_cells": int(aa.size), "mask_agreement": True,
            "bit_identical_cells": int(np.count_nonzero(aa == bb)),
            "maximum_absolute_difference_native": float(differences.max()),
            "mean_absolute_difference_native": float(differences.mean()),
            "nonzero_difference_cells": int(np.count_nonzero(differences)),
            "tolerance_native": 0, "unexplained_disagreements": 0,
            "basis": "R=0, D=0, E=-4: exact binary32 integers below 2**24 scaled by exact 1/16; all cells satisfy the proof domain"}


def checked_pin(pin):
    for name, seal in pin["dependencies"].items():
        if digest(HERE.parent/name) != seal:
            raise IntegrityError("Retained WR007/WR008 dependency evidence changed")


def scratch_room(root):
    # Outputs belong in a dedicated owned directory, not an authoritative collection.
    total = 0
    for p in Path(root).rglob("*"):
        if p.is_file():
            total += p.stat().st_size
        if total + 20_000_000 > 150_000_000:
            raise IntegrityError("Insufficient owned scratch room for bounded temporary decode")


def gdal_decode(path, output, pin):
    import rasterio
    before = process_memory()
    body = field.pinned_input(path, pin); sec = sections(body)
    expected_time = interval(pin["expected"])
    with rasterio.Env(GRIB_NORMALIZE_UNITS="NO", GRIB_ADJUST_LONGITUDE_RANGE="NO"):
        with rasterio.open(path) as d:
            tags = d.tags(1)
            required = {"GRIB_UNIT": "[kg/(m^2)]", "GRIB_ELEMENT": "APCP06", "GRIB_SHORT_NAME": "0-SFC",
                        "GRIB_REF_TIME": "1736899200", "GRIB_VALID_TIME": "1736985600",
                        "GRIB_FORECAST_SECONDS": "64800", "GRIB_PDS_PDTN": "8"}
            raw = [int(x) for x in tags.get("GRIB_PDS_TEMPLATE_NUMBERS", "").split()]
            if d.count != 1 or any(tags.get(k) != v for k, v in required.items()) or raw != list(sec[4][9:]):
                raise IntegrityError("GDAL quantity/unit/interval/PDT metadata disagreement")
            if (d.height, d.width) != (721, 1440) or tuple(d.transform) != (0.25, 0, -0.125, 0, -0.25, 90.125, 0, 0, 1):
                raise IntegrityError("GDAL grid orientation/registration disagreement")
            if d.crs is None or d.crs.to_dict().get("R") != 6371229:
                raise IntegrityError("GDAL Earth shape disagreement")
            values, mask = d.read(1), d.read_masks(1) == 0
            result = {"python": sys.version.split()[0], "rasterio": rasterio.__version__,
                      "gdal": rasterio.__gdal_version__, "numpy": np.__version__, "metadata": tags,
                      "sample_lon_lat": [d.xy(r, c) for r, c in pin["sample_indices"]],
                      "transform": list(d.transform), "crs_wkt": d.crs.to_wkt(),
                      "interval": expected_time, "raw_template_octets_agree": True}
    np.savez(output.with_suffix(".npz"), values=values, mask=mask)
    output.with_suffix(".json").write_bytes(canonical(result))
    output.with_suffix(".resources.json").write_bytes(canonical({"baseline": before, "after": process_memory()}))


def run(path, gdal_python, output, pin_path=PIN):
    output = Path(output); field.require_external(output)
    resource_path = output.with_name(output.stem+"-resources.json")
    if output.exists() or resource_path.exists():
        raise IntegrityError("Output exists; refuse overwrite")
    pin = json.loads(Path(pin_path).read_text(encoding="utf-8")); checked_pin(pin)
    scratch_room(output.parent)
    before = process_memory(); started = time.perf_counter()
    body = field.pinned_input(path, pin); sec = sections(body)
    encoded = check_section4(sec[4], pin["expected"])
    support = interval(pin["expected"])
    grid = grid_compatibility(pin["expected"], pin, sec[3])
    values, mask, lat, lon, metadata, versions = field.eccodes_decode(path, pin)
    check_section4(sec[4], metadata); interval(metadata)
    values.setflags(write=False); mask.setflags(write=False)
    array_seal = hashlib.sha256(values.astype("<f8").tobytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="wr009-", dir=output.parent) as name:
        reference = Path(name)/"reference"
        subprocess.run([str(gdal_python), "-B", str(Path(__file__).resolve()), "--gdal-only",
                        "--input", str(path), "--output", str(reference), "--pins", str(pin_path)], check=True)
        secondary = json.loads(reference.with_suffix(".json").read_text(encoding="utf-8"))
        resources = json.loads(reference.with_suffix(".resources.json").read_text(encoding="utf-8"))
        temporary_bytes = sum(p.stat().st_size for p in Path(name).iterdir())
        with np.load(reference.with_suffix(".npz"), allow_pickle=False) as decoded:
            agreement = compare_arrays(values, decoded["values"], mask, decoded["mask"], metadata)
    samples = []
    for i, (r, c) in enumerate(pin["sample_indices"]):
        if secondary["sample_lon_lat"][i] != [float(lon[r, c]), float(lat[r, c])]:
            raise IntegrityError("GDAL sample coordinates differ")
        samples.append({"row": r, "column": c, "latitude": float(lat[r, c]),
                        "longitude_0_360": float(lon[r, c]), "native_kg_per_m2": float(values[r, c])})
    valid = values[~mask]
    receipt = {"schema": "meridian-weather-wr009-integrity-v1", "outcome": "A",
               "input": pin["input"], "source": pin["source"], "message_metadata": metadata,
               "raw_section4_interpretation": encoded, "temporal_support": support,
               "grid_compatibility": grid, "primary_decoder": versions, "independent_decoder": secondary,
               "independent_comparison": agreement, "decoded_float64_little_endian_sha256": array_seal,
               "statistics_native_kg_per_m2": {"minimum": float(valid.min()), "maximum": float(valid.max()),
                   "mean": float(valid.mean()), "population_standard_deviation": float(valid.std(ddof=0)),
                   "valid_cells": int(valid.size), "missing_cells": int(mask.sum()),
                   "finite_cells": int(np.count_nonzero(np.isfinite(valid))), "zero_cells": int(np.count_nonzero(valid == 0)),
                   "negative_cells": int(np.count_nonzero(valid < 0))}, "samples": samples,
               "transformations": ["reshape original scan order; native kg/m2 retained; no conversion, clamping, sampling or resampling"],
               "limitations": ["one actual accumulation/packing/grid; no bitmap or internal missing values",
                               "no forecast skill, observations, phase/local intensity or terrain suitability",
                               "exact suite/build revision unresolved; preserved-input replay is distinct from future archive availability"]}
    if digest(path) != pin["input"]["sha256"] or hashlib.sha256(values.astype("<f8").tobytes()).hexdigest() != array_seal:
        raise IntegrityError("Input/decoded field changed")
    output.write_bytes(canonical(receipt))
    resource_path.write_bytes(canonical({"primary_baseline": before, "primary_after": process_memory(),
                                       "reference": resources, "temporary_bytes": temporary_bytes,
                                       "elapsed_seconds": time.perf_counter()-started,
                                       "messages_per_run": {"ecCodes": 1, "GDAL": 1}, "retrievals_during_run": 0}))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pins", type=Path, default=PIN); parser.add_argument("--gdal-python", type=Path)
    parser.add_argument("--gdal-only", action="store_true"); args = parser.parse_args()
    if args.gdal_only:
        field.require_external(args.output)
        if any(args.output.with_suffix(s).exists() for s in [".npz", ".json", ".resources.json"]):
            raise IntegrityError("Reference output exists; refuse overwrite")
        pin = json.loads(args.pins.read_text(encoding="utf-8")); checked_pin(pin)
        gdal_decode(args.input, args.output, pin)
    else:
        if args.gdal_python is None: parser.error("--gdal-python required")
        print(json.dumps(run(args.input, args.gdal_python, args.output, args.pins)["independent_comparison"], indent=2))


if __name__ == "__main__":
    main()
