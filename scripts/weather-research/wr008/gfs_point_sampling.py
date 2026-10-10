"""WR008: finite native-grid research, never a production Weather query service."""
from __future__ import annotations

import argparse
import ctypes
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

PROFILE = HERE / "query-profile.json"
PINS = HERE / "input-pins.json"


def validate_pins(profile_path):
    pin = json.loads(PINS.read_text())
    if field.digest(profile_path) != pin["query_profile_sha256"]:
        raise field.IntegrityError("Unfrozen query profile")
    for name, checksum in pin["wr007_files"].items():
        if field.digest(HERE.parent / "wr007" / name) != checksum:
            raise field.IntegrityError("WR007 implementation/evidence identity changed")


def process_memory():
    """Windows PSAPI process working set, not arrays or a mobile memory estimate."""
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ["peak_working_set", "working_set", "peak_paged_pool",
                "paged_pool", "peak_nonpaged_pool", "nonpaged_pool", "pagefile", "peak_pagefile"]]
    counters = Counters(); counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    call = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
    call.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    if not call(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
    return {name + "_bytes": int(getattr(counters, name)) for name in
            ["working_set", "peak_working_set", "pagefile", "peak_pagefile"]}


def safe_json(value):
    if isinstance(value, float) and not math.isfinite(value): return {"nonfinite": repr(value)}
    if isinstance(value, dict): return {k: safe_json(v) for k, v in value.items()}
    if isinstance(value, list): return [safe_json(v) for v in value]
    return value


def validate_query(query):
    if not isinstance(query, dict) or set(query) != {"latitude", "longitude", "method"}: return "MALFORMED_QUERY"
    for key in ["latitude", "longitude"]:
        value = query[key]
        if type(value) not in (int, float): return "INVALID_COORDINATE_TYPE"
        try: finite = math.isfinite(value)
        except OverflowError: finite = False
        if not finite: return "NONFINITE_COORDINATE"
    if not -90 <= query["latitude"] <= 90: return "LATITUDE_OUT_OF_RANGE"
    if query["method"] not in ("NEAREST", "BILINEAR"): return "UNSUPPORTED_METHOD"
    return None


class Grid:
    def __init__(self, metadata):
        m = metadata
        if (m["gridType"], m["gridDefinitionTemplateNumber"], m["scanningMode"], m["shapeOfTheEarth"]) != ("regular_ll", 0, 0, 6):
            raise field.IntegrityError("Unsupported grid/scan/Earth shape")
        self.nx, self.ny = m["Ni"], m["Nj"]
        self.dx, self.dy = m["iDirectionIncrementInDegrees"], m["jDirectionIncrementInDegrees"]
        self.north, self.south = m["latitudeOfFirstGridPointInDegrees"], m["latitudeOfLastGridPointInDegrees"]
        self.west, self.east = m["longitudeOfFirstGridPointInDegrees"], m["longitudeOfLastGridPointInDegrees"]
        if (self.nx < 4 or self.ny < 4 or self.dx <= 0 or self.dy <= 0 or self.north != 90 or self.south != -90
                or self.west != 0 or self.nx * self.dx != 360 or self.east != (self.nx-1)*self.dx
                or self.south != self.north-(self.ny-1)*self.dy or m["numberOfPoints"] != self.nx*self.ny):
            raise field.IntegrityError("Unsupported finite global point-grid geometry")
        self.radius = m["radius"]

    def description(self):
        return {"type":"regular_ll", "rows":self.ny, "columns":self.nx, "north":self.north,
                "south":self.south, "west":self.west, "east":self.east, "longitude_step":self.dx,
                "latitude_step":-self.dy, "scan_mode":0, "Earth_radius_m":self.radius,
                "registration":"native grid nodes", "longitude_periodic":True, "latitude_periodic":False,
                "duplicate_360_endpoint":False, "bilinear_latitude_domain":[self.south+self.dy,self.north-self.dy]}

    def position(self, latitude, longitude):
        native_lon = float(longitude) % 360.0
        if native_lon == 360.0: native_lon = 0.0  # Negative sub-ULP remainder rounded to endpoint.
        signed_lon = native_lon-360 if native_lon >= 180 else native_lon
        return (self.north-float(latitude))/self.dy, native_lon/self.dx, native_lon, signed_lon

    def coordinates(self, row, col): return self.north-self.dy*row, self.west+self.dx*col


def half_up(value):
    lower = math.floor(value)
    return lower + int(value-lower >= .5)


class Sampler:
    def __init__(self, values, mask, metadata):
        self.grid = Grid(metadata)
        if values.shape != mask.shape or values.shape != (self.grid.ny,self.grid.nx) or mask.dtype != np.bool_:
            raise field.IntegrityError("Array shape/mask does not match grid")
        self.values, self.mask = values, mask

    def query(self, query):
        result = {"input_coordinate":safe_json(query), "status":validate_query(query)}
        if result["status"]: return result
        g = self.grid; method = query["method"]
        row, col, lon, signed = g.position(query["latitude"],query["longitude"])
        result.update({"method":method, "normalised_coordinate":{"latitude":float(query["latitude"]),
                       "longitude_minus180_180":signed, "longitude_0_360":lon}})
        if method == "BILINEAR" and not g.south+g.dy <= query["latitude"] <= g.north-g.dy:
            result["status"] = "UNSUPPORTED_POLAR_CAP_BILINEAR"; return result
        if method == "NEAREST":
            r, c = half_up(row), half_up(col) % g.nx
            if r in (0,g.ny-1): c = 0  # Same geographic pole: canonical native representative.
            nodes = [(r,c,1.0)]
        else:
            r, c = math.floor(row), math.floor(col)
            if r == g.ny-2: r -= 1  # Southern endpoint: two non-polar rows.
            v, u = row-r, col-c
            nodes = [(r,c,(1-v)*(1-u)),(r,(c+1)%g.nx,(1-v)*u),
                     (r+1,c,v*(1-u)),(r+1,(c+1)%g.nx,v*u)]
        result["nodes"] = []
        for r,c,weight in nodes:
            if not (0 <= r < g.ny and 0 <= c < g.nx): raise field.IntegrityError("Index out of bounds")
            latitude, longitude = g.coordinates(r,c)
            missing = bool(self.mask[r,c]); value = float(self.values[r,c])
            result["nodes"].append({"row":r,"column":c,"latitude":latitude,"longitude_0_360":longitude,
                                    "weight":weight,"missing":missing,
                                    "temperature_K":None if missing or not math.isfinite(value) else value})
        if any(n["missing"] for n in result["nodes"]):
            result["status"] = "MISSING_CONTRIBUTING_NODE"; return result
        if any(n["temperature_K"] is None for n in result["nodes"]):
            result["status"] = "UNINTERPRETABLE_NODE"; return result
        weights = [n["weight"] for n in result["nodes"]]
        if not all(math.isfinite(w) and 0 <= w <= 1 for w in weights) or abs(math.fsum(weights)-1) > 8*np.finfo(float).eps:
            raise field.IntegrityError("Invalid bilinear weights")
        result.update({"status":"OK", "temperature_K":math.fsum(n["weight"]*n["temperature_K"] for n in result["nodes"]),
                       "weight_sum":math.fsum(weights), "pole_column_canonicalised":method == "NEAREST" and nodes[0][0] in (0,g.ny-1)})
        return result


def queries(profile):
    return [(loc["id"]+":"+method,{"latitude":loc["latitude"],"longitude":loc["longitude"],"method":method})
            for loc in profile["locations"] for method in profile["methods"]] + [
                ("invalid-"+str(i),q) for i,q in enumerate(profile["invalid_queries"])]


def reference(path, profile, output):
    """Independent geometry via GDAL affine; independent interpolation via GDAL warp."""
    if output.exists() or output.with_name(output.stem+"-resources.json").exists():
        raise field.IntegrityError("Refuse reference output overwrite")
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from rasterio.warp import reproject
    from rasterio.windows import Window
    pin = json.loads(field.PIN.read_text()); field.require_external(output)
    before = process_memory(); started = time.perf_counter()
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        intermediate = Path(temporary)/"decoded"
        field.gdal_decode(path,intermediate,pin)  # Reuse accepted identity/geometry guards unchanged.
        decoded_temporary_bytes = sum(p.stat().st_size for p in Path(temporary).rglob("*") if p.is_file())
        versions = json.loads(intermediate.with_suffix(".json").read_text()); results=[]
        with rasterio.Env(GRIB_NORMALIZE_UNITS="NO",GRIB_ADJUST_LONGITUDE_RANGE="NO",GDAL_CACHEMAX=16_000_000):
            with rasterio.open(path) as ds:
                dx,dy = ds.transform.a,-ds.transform.e
                north,south = ds.xy(0,0)[1],ds.xy(ds.height-1,0)[1]
                for identity,q in queries(profile):
                    if validate_query(q): continue
                    latitude,longitude = float(q["latitude"]),float(q["longitude"]) % 360
                    if longitude == 360.0: longitude = 0.0
                    corner_col,corner_row = ~ds.transform*(longitude,latitude)
                    row,col = corner_row-.5,corner_col-.5
                    if q["method"] == "NEAREST":
                        probe_lon = longitude-360 if longitude >= ds.bounds.right else longitude
                        r,c = ds.index(probe_lon,latitude); c %= ds.width
                        if r in (0,ds.height-1): c=0; probe_lon=0
                        sampled = float(next(ds.sample([(probe_lon,latitude)]))[0])
                        if sampled != float(ds.read(1,window=Window(c,r,1,1))[0,0]):
                            raise field.IntegrityError("GDAL sample does not match independently indexed node")
                        results.append({"id":identity,"status":"OK","indices":[[r,c]],"weights":[1.0],"temperature_K":sampled})
                        continue
                    if not south+dy <= latitude <= north-dy:
                        results.append({"id":identity,"status":"UNSUPPORTED_POLAR_CAP_BILINEAR"}); continue
                    r,c = math.floor(row),math.floor(col)
                    if r == ds.height-2: r -= 1
                    patch = np.empty((2,2),dtype=np.float64)
                    for j in range(2):
                        for i in range(2): patch[j,i] = ds.read(1,window=Window((c+i)%ds.width,r+j,1,1))[0,0]
                    x,y = ds.xy(r,c)
                    patch_transform = from_origin(x-dx/2,y+dy/2,dx,dy)
                    destination = np.full((1,1),np.nan)
                    reproject(patch,destination,src_transform=patch_transform,src_crs=ds.crs,
                              dst_transform=from_origin(longitude-.0005,latitude+.0005,.001,.001),
                              dst_crs=ds.crs,resampling=Resampling.bilinear,dst_nodata=np.nan,num_threads=1)
                    weights = np.outer([1-(row-r),row-r],[1-(col-c),col-c]).ravel()
                    results.append({"id":identity,"status":"OK","indices":[[r,c],[r,(c+1)%ds.width],[r+1,c],[r+1,(c+1)%ds.width]],
                                    "weights":weights.tolist(),"temperature_K":float(destination[0,0]),
                                    "node_temperatures_K":patch.ravel().tolist(),"independent_dot_K":float(np.dot(weights,patch.ravel())),
                                    "node_coordinates":[list(ds.xy(rr,cc)) for rr,cc in [[r,c],[r,(c+1)%ds.width],[r+1,c],[r+1,(c+1)%ds.width]]]})
    content = {"decoder":{k:versions[k] for k in ["python","rasterio","gdal","numpy"]},"queries":results,
               "mechanism":"GDAL georeferenced sample and GDAL warp bilinear; four-node periodic patch; same sphere CRS"}
    output.write_bytes(field.canonical(content))
    return {"baseline":before,"after":process_memory(),"elapsed_seconds":time.perf_counter()-started,
            "decoded_temporary_bytes":decoded_temporary_bytes}


def comparison(primary, independent, grid):
    references = {q["id"]:q for q in independent["queries"]}; differences=[]; kernel=[]; exact=[]; weight_diffs=[]; exact_inputs=0; n=0; b=0
    required = {q["id"] for q in primary if q["status"] in ("OK","UNSUPPORTED_POLAR_CAP_BILINEAR")}
    if set(references) != required or len(references) != len(independent["queries"]):
        raise field.IntegrityError("Missing, duplicate or unexpected independent query")
    for q in primary:
        if q["id"] not in references: continue
        ref = references[q["id"]]
        if q["status"] != ref["status"]: raise field.IntegrityError("Boundary status disagreement")
        if q["status"] != "OK": continue
        indices = [[v["row"],v["column"]] for v in q["nodes"]]
        if indices != ref["indices"]: raise field.IntegrityError("Independent node selection disagreement")
        weights = np.array([v["weight"] for v in q["nodes"]]); other = np.array(ref["weights"])
        position_factor = 1+360/grid.dx+180/grid.dy
        weight_bound = 32*np.finfo(float).eps*position_factor
        weight_difference = float(np.max(abs(weights-other)))
        if not np.all(np.isfinite(other)) or weight_difference > weight_bound:
            raise field.IntegrityError("Independent weight disagreement")
        weight_diffs.append(weight_difference)
        magnitude = max(abs(v["temperature_K"]) for v in q["nodes"])
        arithmetic_bound = 128*np.finfo(float).eps*magnitude*position_factor
        difference = abs(q["temperature_K"]-ref["temperature_K"])
        if q["method"] == "BILINEAR":
            primary_nodes = np.array([v["temperature_K"] for v in q["nodes"]])
            secondary_nodes = np.array(ref["node_temperatures_K"])
            node_mask = np.zeros(primary_nodes.shape,dtype=bool)
            field.compare_arrays(primary_nodes,secondary_nodes,node_mask,node_mask,json.loads(field.PIN.read_text())["expected"])
            decoding_bound = math.fsum(w*abs(v["temperature_K"]-t) for w,v,t in zip(weights,q["nodes"],ref["node_temperatures_K"]))
            kernel_diff = abs(ref["temperature_K"]-ref["independent_dot_K"])
            if not math.isfinite(kernel_diff) or kernel_diff > arithmetic_bound:
                raise field.IntegrityError("GDAL interpolation arithmetic disagreement")
            kernel.append(kernel_diff); b += 1
            for node,coord in zip(q["nodes"],ref["node_coordinates"]):
                if coord != [node["longitude_0_360"],node["latitude"]]: raise field.IntegrityError("Node coordinate disagreement")
        else:
            a=np.array([q["nodes"][0]["temperature_K"]]); z=np.zeros(a.shape,dtype=bool)
            field.compare_arrays(a,np.array([ref["temperature_K"]]),z,z,json.loads(field.PIN.read_text())["expected"])
            decoding_bound = abs(a[0]-ref["temperature_K"])
            n += 1
        if not math.isfinite(difference) or difference > decoding_bound+arithmetic_bound:
            raise field.IntegrityError("Independent sampled temperature disagreement")
        q["independent_comparison"] = {"difference_K":difference,"weighted_decoder_bound_K":decoding_bound,
                                        "arithmetic_bound_K":arithmetic_bound,"status":"PASS"}
        differences.append(difference)
        if np.count_nonzero(weights) == 1:
            exact.append(difference)
            active = q["nodes"][int(np.flatnonzero(weights)[0])]
            if (q["normalised_coordinate"]["latitude"],q["normalised_coordinate"]["longitude_0_360"]) == (active["latitude"],active["longitude_0_360"]): exact_inputs += 1
    return {"nearest_comparisons":n,"bilinear_comparisons":b,"native_node_value_comparisons":len(exact),
            "exact_node_input_comparisons":exact_inputs,"boundary_status_comparisons":len(references)-len(differences),
            "compared_queries":len(differences),"maximum_difference_K":max(differences),
            "mean_absolute_difference_K":float(np.mean(differences)),"maximum_weight_difference":max(weight_diffs),
            "maximum_GDAL_kernel_vs_independent_dot_difference_K":max(kernel),"unexplained_disagreements":0,
            "weight_tolerance":"32 eps64 * (1+360/dx+180/dy)",
            "arithmetic_tolerance":"128 eps64 * maximum node magnitude * (1+360/dx+180/dy)",
            "independence":"Distinct decoding and GDAL sampling kernel; shared finite boundary policy, independent affine indexing; no independent polar/missing-data kernel validation"}


def run(path, gdal_python, output, profile_path=PROFILE):
    field.require_external(output)
    resources_path = output.with_name(output.stem+"-resources.json")
    if output.exists() or resources_path.exists(): raise field.IntegrityError("Refuse output overwrite")
    validate_pins(profile_path)
    pin=json.loads(field.PIN.read_text()); profile=json.loads(profile_path.read_text())
    started=time.perf_counter(); baseline=process_memory()
    values,mask,lat,lon,metadata,versions=field.eccodes_decode(path,pin)
    del lat,lon
    accepted=json.loads(field.PIN.with_name("integrity-receipt.json").read_text())
    decoded_hash=hashlib.sha256(values.astype("<f8",copy=False).tobytes()).hexdigest()
    if decoded_hash != accepted["decoded_float64_little_endian_sha256"]: raise field.IntegrityError("WR007 decoded identity changed")
    values.setflags(write=False); mask.setflags(write=False)
    mask_hash=hashlib.sha256(mask.tobytes()).hexdigest()
    sampler=Sampler(values,mask,metadata); before_query=process_memory(); records=[]
    for identity,query in queries(profile):
        record=sampler.query(query); record["id"]=identity; records.append(record)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        ref_path=Path(temporary)/"reference.json"
        subprocess.run([str(gdal_python),"-B",str(Path(__file__).resolve()),"--reference-only","--input",str(path.resolve()),
                        "--output",str(ref_path),"--profile",str(profile_path.resolve())],check=True)
        independent=json.loads(ref_path.read_text()); child_resources=json.loads(ref_path.with_name("reference-resources.json").read_text())
        compared=comparison(records,independent,sampler.grid)
    if (field.digest(path) != pin["input"]["sha256"] or hashlib.sha256(values.tobytes()).hexdigest() != decoded_hash
            or hashlib.sha256(mask.tobytes()).hexdigest() != mask_hash):
        raise field.IntegrityError("Scientific input/array mutated")
    receipt={"schema":"meridian-weather-wr008-sampling-v1","input":pin["input"],"source":pin["source"],
             "query_profile_sha256":field.digest(profile_path),"grid":sampler.grid.description(),
             "field":{"variable":"Temperature","parameter":[0,0,0],"fixed_surface":[103,2],"units":"K",
                      "reference_time":"2025-01-15T00:00:00Z","lead_hours":24,"valid_time":"2025-01-16T00:00:00Z"},
             "primary_decoder":versions,"independent_decoder":independent["decoder"],"comparison":compared,
             "queries":records,"decoded_array_sha256":decoded_hash,"input_and_arrays_unchanged":True,
             "limitations":["grid-axis nearest, not spherical/geodesic nearest", "bilinear angular-coordinate estimate; no finer meteorological resolution",
               "bilinear excludes polar caps; nearest pole canonical column zero", "all four bilinear nodes required even at zero weight; no missing-value renormalisation",
               "model-ground-relative 2 m diagnostic; not actual mountain/valley sensor support", "no terrain correction, skill, reference pairing or production API"]}
    output.write_bytes(field.canonical(receipt))
    resources={"primary_baseline":baseline,"primary_before_queries":before_query,"primary_after":process_memory(),
               "independent_process":child_resources,"elapsed_seconds":time.perf_counter()-started,
               "scientific_retrieval_requests":0,"scientific_transfer_bytes":0,"documentation_retrievals":0,
               "network_qualification":"No retrieval code executed; Git control/OS traffic not metered, no zero-total-network claim"}
    resources_path.write_bytes(field.canonical(resources))
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True); parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--gdal-python",type=Path); parser.add_argument("--profile",type=Path,default=PROFILE)
    parser.add_argument("--reference-only",action="store_true"); args=parser.parse_args()
    if args.reference_only:
        validate_pins(args.profile)
        resources=reference(args.input,json.loads(args.profile.read_text()),args.output)
        args.output.with_name(args.output.stem+"-resources.json").write_bytes(field.canonical(resources))
    else:
        if args.gdal_python is None: parser.error("--gdal-python is required")
        receipt=run(args.input,args.gdal_python,args.output,args.profile)
        print(json.dumps(receipt["comparison"],indent=2))


if __name__ == "__main__": main()
