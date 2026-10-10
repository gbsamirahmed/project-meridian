"""WR010 finite evidence experiment; no production field framework or acquisition."""
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

import numpy as np

HERE = Path(__file__).resolve().parent
for previous in ("wr007", "wr008", "wr009"):
    sys.path.insert(0, str(HERE.parent / previous))
import gfs_field_pilot as field
import gfs_point_sampling as spatial
import gfs_precipitation_pilot as precipitation

PIN = HERE / "input-pins.json"
Error = field.IntegrityError


def temporal(m):
    """Only the two evidenced support profiles; other statistics remain unsupported."""
    if m.get("productDefinitionTemplateNumber") == 8:
        return precipitation.interval(m)
    try:
        if m["productDefinitionTemplateNumber"] != 0 or m["stepType"] != "instant":
            raise Error("Unsupported temporal structure")
        ref = datetime.strptime(f'{m["dataDate"]:08d}{m["dataTime"]:04d}', "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        lead = precipitation.seconds(m["forecastTime"], m["indicatorOfUnitOfTimeRange"])
        valid = datetime.strptime(f'{m["validityDate"]:08d}{m["validityTime"]:04d}', "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        if valid != ref + timedelta(seconds=lead) or m["startStep"] != m["endStep"] or precipitation.seconds(m["endStep"], m["stepUnits"]) != lead:
            raise Error("Contradictory instantaneous time metadata")
    except (KeyError, TypeError, ValueError, OverflowError) as e:
        raise Error("Incomplete/unsupported temporal metadata") from e
    return {"kind": "instant", "reference_time": precipitation.stamp(ref), "valid_time": precipitation.stamp(valid), "forecast_lead_seconds": lead}


def identity(m, grid_seal, input_seal, evidence):
    """A small research receipt, explicitly limited to inspected deterministic profiles."""
    if m.get("typeOfProcessedData") != 1 or m.get("productDefinitionTemplateNumber") not in (0, 8):
        raise Error("Unsupported deterministic/ensemble product")
    parameter = [m[k] for k in ("discipline", "parameterCategory", "parameterNumber")]
    units = {(0, 0, 0): "K", (0, 1, 8): "kg m**-2", (0, 2, 2): "m s**-1", (0, 2, 3): "m s**-1", (0, 6, 1): "%"}
    if units.get(tuple(parameter)) != m.get("units"):
        raise Error("Unsupported parameter/native unit pairing")
    levels = {(0, 0, 0): (103, 2), (0, 1, 8): (1, 0), (0, 2, 2): (103, 10), (0, 2, 3): (103, 10), (0, 6, 1): (10, 0)}
    if levels[tuple(parameter)] != (m.get("typeOfFirstFixedSurface"), m.get("level")):
        raise Error("Unsupported vertical meaning")
    if evidence not in ("retained_independent_numerical", "new_independent_numerical", "metadata_only"):
        raise Error("Unknown evidence grade; decoding is not skill")
    if any(not isinstance(s, str) or len(s) != 64 or any(c not in "0123456789abcdef" for c in s) for s in (input_seal, grid_seal)):
        raise Error("Missing input/grid provenance")
    spatial.Grid(m)
    return {"model": "NOAA/NCEP GFS delivered product", "parameter": parameter, "native_unit": m["units"],
            "vertical": {"first_surface_code": m["typeOfFirstFixedSurface"], "level": m["level"], "type": m["typeOfLevel"]},
            "temporal": temporal(m), "grid_section3_sha256": grid_seal, "input_sha256": input_seal,
            "product": {k: m[k] for k in ("centre", "subCentre", "tablesVersion", "localTablesVersion", "generatingProcessIdentifier")},
            "ensemble": {"kind": "deterministic", "member": None, "qualification": "no ensemble structure validated"},
            "evidence": evidence, "quality": "decoding integrity; forecast accuracy untested"}


def vector_pair(a, b, am, bm):
    if a["parameter"] != [0, 2, 2] or b["parameter"] != [0, 2, 3]:
        raise Error("Not the specified ordered U/V pair")
    for k in ("model", "product", "native_unit", "vertical", "temporal", "grid_section3_sha256", "ensemble"):
        if a[k] != b[k]:
            raise Error("Vector component mismatch: " + k)
    if a["evidence"] == "metadata_only" or b["evidence"] == "metadata_only":
        raise Error("Metadata-only pair is not numerical vector evidence")
    if am.get("uvRelativeToGrid") != 0 or bm.get("uvRelativeToGrid") != 0 or am.get("resolutionAndComponentFlags") != 48 or bm.get("resolutionAndComponentFlags") != 48:
        raise Error("Unsupported vector coordinate frame")
    return {"components": [a["input_sha256"], b["input_sha256"]], "basis": "eastward/northward, encoded Table3.3 bit5=0",
            "status": "aligned numerical component pair", "limitations": "no derived speed/direction, gusts, local wind accuracy or pole-vector transport"}


def compatibility(a, b):
    """Equality along separate scientific axes is not permission to replace a quantity."""
    return {"same_encoded_grid": a["grid_section3_sha256"] == b["grid_section3_sha256"],
            "same_reference": a["temporal"]["reference_time"] == b["temporal"]["reference_time"],
            "same_valid_endpoint": a["temporal"]["valid_time"] == b["temporal"]["valid_time"],
            "same_temporal_support": a["temporal"] == b["temporal"],
            "same_vertical_support": a["vertical"] == b["vertical"],
            "same_native_units": a["native_unit"] == b["native_unit"],
            "same_parameter": a["parameter"] == b["parameter"],
            "same_ensemble_structure": a["ensemble"] == b["ensemble"],
            "interchangeable_quantity": a["parameter"] == b["parameter"] and a["vertical"] == b["vertical"] and a["temporal"] == b["temporal"] and a["native_unit"] == b["native_unit"]}


def numeric_compare(a, b, mask, other_mask, m):
    if a.shape != b.shape or a.shape != mask.shape or mask.shape != other_mask.shape or not np.array_equal(mask, other_mask):
        raise Error("Grid/missingness disagreement")
    if not a.size or mask.dtype != np.bool_ or other_mask.dtype != np.bool_ or np.any(mask) or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise Error("Actual bitmap/non-finite profile unsupported")
    if m["dataRepresentationTemplateNumber"] != 3 or m["binaryScaleFactor"] != 0 or m["decimalScaleFactor"] not in (1, 2):
        raise Error("Unsupported predeclared scaling profile")
    d = 10.0 ** -m["decimalScaleFactor"]; r = m["referenceValue"]
    reconstructed = a / d - r; integer = np.rint(reconstructed)
    residual = np.abs(reconstructed-integer)
    if np.any(integer < 0) or np.any(integer >= 2**24) or np.any(residual > 64*np.finfo(float).eps*np.maximum(1, np.abs(a/d))):
        raise Error("Outside exact binary32 integer/lattice domain")
    summed = integer.astype(np.float32) + np.float32(r)
    coefficient = np.float32(d)
    predicted = (summed*coefficient).astype(np.float64)
    bounds = (np.abs(np.spacing(summed)).astype(float)*.5*abs(float(coefficient))
              + np.abs(integer+r)*abs(float(coefficient)-d)
              + np.abs(np.spacing(predicted.astype(np.float32))).astype(float)*.5
              + 8*np.finfo(float).eps*np.abs(a))
    difference = np.abs(a-b)
    if not np.array_equal(predicted, b) or np.any(difference > bounds):
        raise Error("Unexplained independent decoder disagreement")
    return {"compared_cells": int(a.size), "mask_agreement": True, "maximum_absolute_difference_native": float(difference.max()),
            "mean_absolute_difference_native": float(difference.mean()), "maximum_analytic_bound_native": float(bounds.max()),
            "exact_predicted_binary32_cells": int(np.count_nonzero(predicted == b)), "unexplained_disagreements": 0,
            "tolerance": "predeclared per-cell binary32 sum/coefficient/product bound AND exact g2clib profile"}


def query_reuse(values, mask, metadata, independent, transform, queries):
    """Reuse WR008 mathematics, explicitly replace its temperature-labelled receipt keys."""
    sampler = spatial.Sampler(values, mask, metadata); result = []
    for query in queries:
        raw = sampler.query(query)
        q = {k: v for k, v in raw.items() if k not in ("temperature_K", "nodes")}
        if "nodes" in raw:
            q["nodes"] = [{("native_value" if k == "temperature_K" else k): v for k, v in n.items()} for n in raw["nodes"]]
        if raw["status"] == "OK":
            q["native_value"] = raw["temperature_K"]
            # Independent node positions from the checked GDAL affine, not WR008 Grid.
            row = (float(query["latitude"])-transform[5])/transform[4]-.5
            col = ((float(query["longitude"]) % 360)-transform[2])/transform[0]-.5
            if query["method"] == "NEAREST":
                rr, cc = math.floor(row+.5), math.floor(col+.5) % independent.shape[1]
                if rr in (0, independent.shape[0]-1): cc = 0
                nodes = [(rr, cc)]; weights = np.array([1.])
            else:
                rr, cc = math.floor(row), math.floor(col)
                if rr == independent.shape[0]-2: rr -= 1
                nodes = [(rr, cc), (rr, (cc+1) % independent.shape[1]), (rr+1, cc), (rr+1, (cc+1) % independent.shape[1])]
                weights = np.outer([1-(row-rr), row-rr], [1-(col-cc), col-cc]).ravel()
            if nodes != [(n["row"], n["column"]) for n in raw["nodes"]]:
                raise Error("GDAL affine independent node mismatch")
            av = np.array([n["temperature_K"] for n in raw["nodes"]]); bv = np.array([independent[r, c] for r, c in nodes])
            if np.max(np.abs(weights-[n["weight"] for n in raw["nodes"]])) > 32*np.finfo(float).eps*(1+360/.25+180/.25):
                raise Error("Independent query weights mismatch")
            numeric_compare(av, bv, np.zeros(av.shape, dtype=bool), np.zeros(av.shape, dtype=bool), metadata)
            ref = float(np.dot(weights, bv)); diff = abs(q["native_value"]-ref)
            bound = float(np.dot(weights, np.abs(av-bv))) + 128*np.finfo(float).eps*max(1, float(np.abs(bv).max()))*(1+360/.25+180/.25)
            if not math.isfinite(ref) or diff > bound:
                raise Error("Independent arithmetic query disagreement")
            q["comparison"] = {"native_value": ref, "difference_native": diff, "bound_native": bound,
                               "mechanism": "independent GDAL decoding/affine and separately implemented NumPy dot; not independent GDAL warp"}
        result.append(q)
    return result


def checked_pin():
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    for name, seal in pin["dependencies"].items():
        if field.digest(HERE.parent/name) != seal: raise Error("Retained evidence changed")
    return pin


def secondary(path, output, fp):
    import rasterio
    body = field.pinned_input(path, fp); sec = precipitation.sections(body)
    before = spatial.process_memory()
    with rasterio.Env(GRIB_NORMALIZE_UNITS="NO", GRIB_ADJUST_LONGITUDE_RANGE="NO", GDAL_CACHEMAX=16_000_000):
        with rasterio.open(path) as d:
            tags = d.tags(1)
            if d.count != 1 or any(tags.get(k) != v for k, v in fp["gdal"].items()) or [int(x) for x in tags["GRIB_PDS_TEMPLATE_NUMBERS"].split()] != list(sec[4][9:]):
                raise Error("Independent GDAL metadata/raw template disagreement")
            if (d.height, d.width) != (721, 1440) or tuple(d.transform) != (.25, 0, -.125, 0, -.25, 90.125, 0, 0, 1) or d.crs.to_dict().get("R") != 6371229:
                raise Error("Independent geometry/orientation disagreement")
            values, mask = d.read(1), d.read_masks(1) == 0
            meta = {"tags": tags, "transform": list(d.transform), "crs": d.crs.to_wkt(), "versions": {"python": sys.version.split()[0], "rasterio": rasterio.__version__, "GDAL": rasterio.__gdal_version__, "numpy": np.__version__}}
    np.savez(output.with_suffix(".npz"), values=values, mask=mask)
    output.with_suffix(".json").write_bytes(field.canonical(meta))
    output.with_suffix(".resources.json").write_bytes(field.canonical({"before": before, "after": spatial.process_memory()}))


def run(input_root, gdal_python, output, borrowed_paths):
    pin = checked_pin(); output = Path(output); field.require_external(output)
    if output.exists() or output.with_name(output.stem+"-resources.json").exists(): raise Error("Refuse output overwrite")
    precipitation.scratch_room(output.parent); before = spatial.process_memory(); results = {}; resources = []
    for name, fp in pin["fields"].items():
        path = Path(input_root)/fp["input"]["filename"]
        body = field.pinned_input(path, fp); sec = precipitation.sections(body)
        grid_seal = hashlib.sha256(sec[3]).hexdigest()
        if grid_seal != pin["section3_sha256"]: raise Error("Encoded grid mismatch")
        if sec[3][54] != 48: raise Error("Actual component flags disagree")
        concept = identity(fp["expected"], grid_seal, fp["input"]["sha256"], "new_independent_numerical")
        # No ensemble identifiers are silently converted to deterministic member zero.
        import eccodes as ec
        h = ec.codes_new_from_message(body)
        try:
            if any(ec.codes_is_defined(h, k) for k in ("perturbationNumber", "numberOfForecastsInEnsemble", "typeOfEnsembleForecast")):
                raise Error("Unexpected ensemble structure")
        finally: ec.codes_release(h)
        a, mask, lat, lon, metadata, versions = field.eccodes_decode(path, fp)
        a.setflags(write=False); mask.setflags(write=False)
        array_seal = hashlib.sha256(a.astype("<f8").tobytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="wr010-", dir=output.parent) as directory:
            ref = Path(directory)/"reference"
            subprocess.run([str(gdal_python), "-B", str(Path(__file__).resolve()), "--secondary", name, "--inputs", str(input_root), "--output", str(ref)], check=True)
            independent = json.loads(ref.with_suffix(".json").read_text(encoding="utf-8"))
            with np.load(ref.with_suffix(".npz"), allow_pickle=False) as decoded:
                agreement = numeric_compare(a, decoded["values"], mask, decoded["mask"], metadata)
                queries = query_reuse(a, mask, metadata, decoded["values"], independent["transform"], pin["selection"]["queries"])
            resources.append({"field": name, "secondary": json.loads(ref.with_suffix(".resources.json").read_text()), "temporary_bytes": sum(p.stat().st_size for p in Path(directory).iterdir())})
        if name == "cloud" and (a.min() < 0 or a.max() > 100): raise Error("Cloud percent outside documented bounds; do not clamp")
        results[name] = {"input": fp["input"], "source": fp["source"], "metadata": metadata, "candidate_contract": concept,
                         "primary_decoder": versions, "secondary_decoder": independent, "numerical_agreement": agreement,
                         "statistics_native": {"minimum": float(a.min()), "maximum": float(a.max()), "mean_unweighted_nodes": float(a.mean()),
                           "valid_cells": int(a.size), "missing_cells": int(mask.sum()), "negative_cells": int(np.count_nonzero(a < 0)), "zero_cells": int(np.count_nonzero(a == 0))},
                         "decoded_float64_sha256": array_seal, "queries": queries}
        if field.digest(path) != fp["input"]["sha256"] or hashlib.sha256(a.astype("<f8").tobytes()).hexdigest() != array_seal: raise Error("Scientific input/array mutation")
        del a, mask, lat, lon
    pair = vector_pair(results["u10"]["candidate_contract"], results["v10"]["candidate_contract"], results["u10"]["metadata"], results["v10"]["metadata"])
    concepts = {k: v["candidate_contract"] for k, v in results.items()}
    for name, previous in (("temperature", "wr007"), ("precipitation", "wr009")):
        old = json.loads((HERE.parent/previous/"input-pins.json").read_text(encoding="utf-8"))
        m = dict(old["expected"])
        borrowed_path = Path(borrowed_paths[name])
        sec = precipitation.sections(field.pinned_input(borrowed_path, old))
        if hashlib.sha256(sec[3]).hexdigest() != pin["section3_sha256"]: raise Error("Retained grid seal changed")
        # Actual Section 4 octet 18, rather than an assumption from friendly aliases.
        if name == "temperature": m["indicatorOfUnitOfTimeRange"] = sec[4][17]
        concepts[name] = identity(m, pin["section3_sha256"], old["input"]["sha256"], "retained_independent_numerical")
    matrix = {a+":"+b: compatibility(concepts[a], concepts[b]) for a in concepts for b in concepts if a < b}
    receipt = {"schema": "meridian-wr010-evidence-v1", "outcome": "A", "fields": results, "vector_pair": pair,
               "candidate_contracts": concepts, "compatibility_matrix": matrix,
               "reused_evidence": pin["borrowed"], "limitations": ["one deterministic delivered GFS grid/run/end-time", "no real bitmap, categories, upper-air or ensemble validation", "component basis at poles is degenerate; canonical pole node is numerical only", "interpolation adds no model resolution; no forecast skill, reference or terrain correction"]}
    output.write_bytes(field.canonical(receipt))
    output.with_name(output.stem+"-resources.json").write_bytes(field.canonical({"primary_before": before, "primary_after": spatial.process_memory(), "fields": resources, "retrievals_during_run": 0}))
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--inputs", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--gdal-python", type=Path); p.add_argument("--secondary", choices=("u10", "v10", "cloud"))
    p.add_argument("--temperature-input", type=Path); p.add_argument("--precipitation-input", type=Path); args = p.parse_args()
    if args.secondary:
        field.require_external(args.output)
        if any(args.output.with_suffix(x).exists() for x in (".npz", ".json", ".resources.json")): raise Error("Refuse reference overwrite")
        fp = checked_pin()["fields"][args.secondary]; secondary(args.inputs/fp["input"]["filename"], args.output, fp)
    else:
        if args.gdal_python is None or args.temperature_input is None or args.precipitation_input is None: p.error("Independent GDAL interpreter and both retained inputs required")
        print(json.dumps({k: v["numerical_agreement"] for k, v in run(args.inputs, args.gdal_python, args.output, {"temperature": args.temperature_input, "precipitation": args.precipitation_input})["fields"].items()}, indent=2))
