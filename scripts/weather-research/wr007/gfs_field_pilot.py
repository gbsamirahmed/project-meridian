"""WR007: a pinned single-field experiment, never a production ingestion path."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

PIN = Path(__file__).with_name("input-pins.json")
REPOSITORY = Path(__file__).resolve().parents[3]
MAX_INPUT = 50_000_000


class IntegrityError(ValueError):
    """The field is corrupt, unexpected or outside this finite profile."""


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def validate_framing(body):
    # Framing checks are not a replacement GRIB decoder.
    if len(body) < 20 or body[:4] != b"GRIB" or body[7] != 2:
        raise IntegrityError("Not a complete GRIB edition 2 message")
    if int.from_bytes(body[8:16], "big") != len(body) or body[-4:] != b"7777":
        raise IntegrityError("Truncated, concatenated or malformed GRIB message")


def pinned_input(path, pin):
    path = Path(path)
    require_external(path)
    if path.stat().st_size != pin["input"]["bytes"] or path.stat().st_size > MAX_INPUT:
        raise IntegrityError("Unexpected input size")
    if digest(path) != pin["input"]["sha256"]:
        raise IntegrityError("Input checksum mismatch")
    body = path.read_bytes()  # Only the verified 874,115-byte message, never a parent.
    validate_framing(body)
    return body


def require_external(path):
    if Path(path).resolve().is_relative_to(REPOSITORY):
        raise IntegrityError("Scientific inputs/outputs must remain outside the repository")


def validate_metadata(metadata, pin):
    for key, expected in pin["expected"].items():
        if metadata.get(key) != expected:
            raise IntegrityError(f"Unexpected {key}: {metadata.get(key)!r}; expected {expected!r}")


def wrap_longitude(longitude):
    if not 0 <= longitude < 360:
        raise IntegrityError("Longitude outside retained [0,360) convention")
    return (longitude + 180) % 360 - 180


def compare_arrays(primary, secondary, primary_mask, secondary_mask, metadata):
    import numpy as np
    if primary.shape != secondary.shape or primary.shape != primary_mask.shape:
        raise IntegrityError("Array orientation/dimensions disagree")
    if secondary_mask.shape != primary.shape or not np.array_equal(primary_mask, secondary_mask):
        raise IntegrityError("Missingness masks disagree")
    valid = ~primary_mask
    a, b = primary[valid], secondary[valid]
    if not a.size or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise IntegrityError("No finite comparable values")
    # This diagnostic follows g2clib comunpack.c's float calculation. It is
    # not another decoder; GDAL has already decoded the independent payload.
    if metadata["binaryScaleFactor"] != 0 or metadata["decimalScaleFactor"] != 2:
        raise IntegrityError("Unsupported rounding diagnostic profile")
    ref = metadata["referenceValue"]
    integers = np.rint(a * 100 - ref)
    residual = np.abs(a * 100 - ref - integers)
    if float(residual.max()) > 64 * np.finfo(np.float64).eps * max(float(np.abs(a * 100).max()), 1):
        raise IntegrityError("Values not on encoded integer lattice")
    if np.any(integers < 0) or np.any(integers >= 2**24):
        raise IntegrityError("Integers outside exact binary32 range")
    coefficient = np.float32(0.01)
    summed = integers.astype(np.float32) + np.float32(ref)
    predicted = (summed * coefficient).astype(np.float64)
    # Two binary32 rounded operations and a rounded decimal coefficient:
    # half-ULP(sum)*|D32| + |exact sum|*|D32-D| + half-ULP(product).
    bounds = (np.abs(np.spacing(summed)).astype(np.float64) * 0.5 * abs(float(coefficient))
              + np.abs(integers + ref) * abs(float(coefficient) - 0.01)
              + np.abs(np.spacing(predicted.astype(np.float32))).astype(np.float64) * 0.5
              + 8 * np.finfo(np.float64).eps * np.abs(a))
    differences = np.abs(a - b)
    if not np.array_equal(predicted, b) or np.any(differences > bounds):
        raise IntegrityError("Unexplained independent decoder disagreement")
    return {
        "status": "INDEPENDENT AGREEMENT WITH EXPLAINED BINARY32 ROUNDING",
        "compared_cells": int(a.size), "mask_agreement": True,
        "bit_identical_cells": int(np.count_nonzero(a == b)),
        "non_identical_cells": int(np.count_nonzero(a != b)),
        "maximum_absolute_difference_K": float(differences.max()),
        "mean_absolute_difference_K": float(differences.mean()),
        "maximum_derived_rounding_bound_K": float(bounds.max()),
        "g2clib_rounding_profile_exact_cells": int(np.count_nonzero(predicted == b)),
        "maximum_integer_lattice_residual": float(residual.max()),
        "tolerance_policy": "per-cell two-operation binary32 bound; exact g2clib profile also required",
    }


def gdal_decode(path, out, pin):
    import numpy as np
    import rasterio
    require_external(out)
    if out.with_suffix(".npz").exists() or out.with_suffix(".json").exists():
        raise IntegrityError("GDAL output already exists; refuse overwrite")
    pinned_input(path, pin)
    with rasterio.Env(GRIB_NORMALIZE_UNITS="NO", GRIB_ADJUST_LONGITUDE_RANGE="NO"):
        with rasterio.open(path) as dataset:
            tags = dataset.tags(1)
            required = {"GRIB_UNIT": "[K]", "GRIB_ELEMENT": "TMP", "GRIB_SHORT_NAME": "2-HTGL",
                        "GRIB_REF_TIME": "1736899200", "GRIB_VALID_TIME": "1736985600",
                        "GRIB_FORECAST_SECONDS": "86400", "GRIB_PDS_PDTN": "0"}
            if dataset.count != 1 or any(tags.get(k) != v for k, v in required.items()):
                raise IntegrityError("GDAL parameter/level/units/time metadata disagreement")
            if (dataset.height, dataset.width) != (721, 1440):
                raise IntegrityError("GDAL dimensions disagreement")
            if tuple(dataset.transform) != (0.25, 0.0, -0.125, 0.0, -0.25, 90.125, 0.0, 0.0, 1.0):
                raise IntegrityError("GDAL orientation/registration disagreement")
            if dataset.crs is None or dataset.crs.to_dict().get("R") != 6371229:
                raise IntegrityError("GDAL Earth definition disagreement")
            coordinates = [dataset.xy(r, c) for r, c in pin["sample_indices"]]
            result = {"rasterio": rasterio.__version__, "gdal": rasterio.__gdal_version__,
                      "numpy": np.__version__, "python": sys.version.split()[0],
                      "metadata": tags, "transform": list(dataset.transform),
                      "crs_wkt": dataset.crs.to_wkt(), "sample_lon_lat": coordinates,
                      "configuration": {"GRIB_NORMALIZE_UNITS": "NO", "GRIB_ADJUST_LONGITUDE_RANGE": "NO"}}
            values, mask = dataset.read(1), dataset.read_masks(1) == 0
    np.savez(out.with_suffix(".npz"), values=values, mask=mask)
    out.with_suffix(".json").write_bytes(canonical(result))


def eccodes_decode(path, pin):
    import eccodes as ec
    import numpy as np
    body = pinned_input(path, pin)
    handle = ec.codes_new_from_message(body)
    if handle is None:
        raise IntegrityError("ecCodes could not create message")
    try:
        metadata = {k: ec.codes_get(handle, k) for k in pin["metadata_keys"]}
        # Read code-table numbers explicitly; friendly aliases are insufficient.
        for key in pin["numeric_code_keys"]:
            metadata[key] = ec.codes_get_long(handle, key)
        validate_metadata(metadata, pin)  # Before extracting numerical contents.
        values = np.reshape(ec.codes_get_values(handle), (metadata["Nj"], metadata["Ni"]))
        latitudes = np.reshape(ec.codes_get_array(handle, "latitudes"), values.shape)
        longitudes = np.reshape(ec.codes_get_array(handle, "longitudes"), values.shape)
        expected_latitudes = 90 - np.arange(721) * 0.25
        expected_longitudes = np.arange(1440) * 0.25
        if not np.array_equal(latitudes, np.broadcast_to(expected_latitudes[:, None], values.shape)):
            raise IntegrityError("Latitude ordering/coordinates mismatch")
        if not np.array_equal(longitudes, np.broadcast_to(expected_longitudes[None, :], values.shape)):
            raise IntegrityError("Longitude ordering/coordinates mismatch")
        # This finite pilot supports the inspected no-bitmap/no-internal-missing
        # packing only. It does not invent a universal missing sentinel rule.
        mask = np.zeros(values.shape, dtype=bool)
        if not np.all(np.isfinite(values)):
            raise IntegrityError("Unexpected non-finite value without missingness declaration")
        versions = {"python": sys.version.split()[0], "eccodes_python": importlib.metadata.version("eccodes"),
                    "eccodes_native": ec.codes_get_api_version(), "numpy": np.__version__}
        return values, mask, latitudes, longitudes, metadata, versions
    finally:
        ec.codes_release(handle)


def run(path, gdal_python, output, pin, pin_path=PIN):
    import numpy as np
    require_external(output)
    if Path(output).exists():
        raise IntegrityError("Receipt already exists; choose a new output")
    if Path(output).resolve() == Path(path).resolve():
        raise IntegrityError("Output must not replace input")
    values, mask, lat, lon, metadata, versions = eccodes_decode(path, pin)
    intermediate = Path(output).with_name(Path(output).stem + "-gdal")
    if intermediate.with_suffix(".npz").exists() or intermediate.with_suffix(".json").exists():
        raise IntegrityError("Intermediate already exists; choose a new output")
    # Separate interpreter and GDAL/degrib/g2clib, never a second ecCodes wrapper.
    subprocess.run([str(gdal_python), "-B", str(Path(__file__).resolve()), "--gdal-only",
                    "--input", str(Path(path).resolve()), "--output", str(intermediate),
                    "--pins", str(Path(pin_path).resolve())], check=True)
    secondary = json.loads(intermediate.with_suffix(".json").read_text(encoding="utf-8"))
    with np.load(intermediate.with_suffix(".npz"), allow_pickle=False) as decoded:
        comparison = compare_arrays(values, decoded["values"], mask, decoded["mask"], metadata)
    samples = []
    for i, (row, column) in enumerate(pin["sample_indices"]):
        longitude, latitude = float(lon[row, column]), float(lat[row, column])
        if secondary["sample_lon_lat"][i] != [longitude, latitude]:
            raise IntegrityError("GDAL sample coordinates do not identify the same cells")
        wrapped = wrap_longitude(longitude)
        if wrapped % 360 != longitude:
            raise IntegrityError("Longitude mapping is not reversible")
        samples.append({"row": row, "column": column, "latitude": latitude, "longitude_0_360": longitude,
                        "longitude_minus180_180": wrapped, "temperature_K": float(values[row, column])})
    receipt = {"schema": "meridian-weather-wr007-integrity-v1", "outcome": "A — VERIFIED NUMERICAL FIELD",
               "input": pin["input"], "source": pin["source"], "message_metadata": metadata,
               "primary_decoder": versions, "secondary_decoder": secondary, "independent_comparison": comparison,
               "grid": {"shape_rows_columns": list(values.shape), "registration": "grid points; GDAL pixel centres",
                        "native_longitudes": "[0,360), no duplicate 360 endpoint", "pole_rows_present": True},
               "statistics_K": {"minimum": float(values.min()), "maximum": float(values.max()),
                                "mean": float(values.mean()), "population_standard_deviation": float(values.std(ddof=0)),
                                "valid_cells": int(values.size), "missing_cells": int(mask.sum())},
               "decoded_float64_little_endian_sha256": hashlib.sha256(values.astype("<f8").tobytes()).hexdigest(),
               "samples": samples, "transformations": ["reshape in original scanning order",
                                                       "reversible longitude labels for samples only"],
               "limitations": ["one field/grid/packing, no bitmap or internal missing values",
                               "delivered grid, not FV3 computational mesh", "no forecast skill/reference evaluation",
                               "no station support or mobile/browser runtime demonstrated"]}
    if digest(path) != pin["input"]["sha256"]:
        raise IntegrityError("Input changed during experiment")
    Path(output).write_bytes(canonical(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pins", type=Path, default=PIN)
    parser.add_argument("--gdal-python", type=Path)
    parser.add_argument("--gdal-only", action="store_true")
    args = parser.parse_args()
    pin = json.loads(args.pins.read_text(encoding="utf-8"))
    if args.gdal_only:
        gdal_decode(args.input, args.output, pin)
    else:
        if args.gdal_python is None:
            parser.error("--gdal-python is required for independent agreement")
        result = run(args.input, args.gdal_python, args.output, pin, args.pins)
        print(json.dumps(result["independent_comparison"], indent=2))


if __name__ == "__main__":
    main()
