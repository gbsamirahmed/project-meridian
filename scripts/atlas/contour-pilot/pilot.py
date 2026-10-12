"""Bounded offline contour apparatus; no acquisition or source writes."""
import argparse
import ctypes
import gc
import hashlib
import json
import os
from pathlib import Path
import time

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"
os.environ["PROJ_NETWORK"] = "OFF"
os.environ["GDAL_PAM_ENABLED"] = "NO"

import contourpy
import numpy as np
import pyproj
import rasterio
from rasterio.windows import Window, from_bounds
from shapely import STRtree
from shapely.geometry import LineString, box
from shapely.ops import unary_union

CORE = (2624000, 1091000, 2626000, 1093000)
CONTEXT = (2623750, 1090750, 2626250, 1093250)
LEVELS = list(range(2000, 3201, 10))
LIMITS = {"scratchBytes": 150_000_000, "storedVertices": 2_000_000,
          "workingSetBytes": 512 * 1024**2, "seconds": 1200}
NOTICE = ("produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and "
          "© Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS "
          "by the European Union and ESA; all rights reserved")
XY_PIPELINE = ("proj=pipeline step inv proj=somerc lat_0=46.9524055555556 "
               "lon_0=7.43958333333333 k_0=1 x_0=2600000 y_0=1200000 ellps=bessel "
               "step proj=push v_3 step proj=cart ellps=bessel step proj=helmert "
               "x=674.374 y=15.056 z=405.346 step inv proj=cart ellps=WGS84 "
               "step proj=pop v_3 step proj=unitconvert xy_in=rad xy_out=deg")
XY = pyproj.Transformer.from_pipeline(XY_PIPELINE)
pyproj.network.set_network_enabled(False)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def memory():
    if os.name != "nt":
        raise RuntimeError("This approved resource monitor requires Windows")
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ("peak", "working", "pagedPeak",
                "paged", "nonpagedPeak", "nonpaged", "pagefile", "pagefilePeak")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise RuntimeError("Working-set measurement unavailable")
    return int(counters.working), int(counters.peak)


class Budget:
    def __init__(self, root, start):
        self.root, self.start, self.vertices = root, start, 0
        self.peak = 0

    def check(self, added_vertices=0, added_bytes=0):
        current, peak = memory()
        self.peak = max(self.peak, peak)
        size = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
        if peak > LIMITS["workingSetBytes"] or time.monotonic() - self.start > LIMITS["seconds"]:
            raise RuntimeError("Process working-set/time limit reached")
        if size + added_bytes > LIMITS["scratchBytes"]-8192 or self.vertices + added_vertices > LIMITS["storedVertices"]:
            raise RuntimeError("Combined scratch/vertex limit reached")
        return size

    def write(self, path, value):
        body = canonical(value) + b"\n"
        self.check(added_bytes=len(body))
        with path.open("xb") as stream:
            stream.write(body)


def generator(x, y, z):
    if contourpy.__version__ != "1.4.0":
        raise ValueError("Unapproved contour implementation")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Invalid coordinates")
    if x.ndim == 1:
        if not (np.diff(x) > 0).all() or not (np.diff(y) > 0).all():
            raise ValueError("Non-monotonic coordinates")
    else:
        if not (np.diff(x, axis=1) > 0).all() or not (np.diff(y, axis=0) > 0).all():
            raise ValueError("Non-monotonic curvilinear coordinates")
    return contourpy.contour_generator(x=x, y=y, z=np.ma.masked_invalid(z),
        name="serial", line_type="Separate", z_interp="Linear", corner_mask=False,
        quad_as_tri=False, thread_count=1)


def allocation_allowed(cells, current_bytes):
    # Conservative preflight after the observed native-grid resource stop.
    # This is not an OS allocation guarantee; peak working-set checks remain required.
    return current_bytes + cells*40 <= LIMITS["workingSetBytes"]


def edge_residual(points, x, y, z, level):
    """Independent interpolation on candidate grid edges, including curvilinear XY."""
    ax = x if x.ndim == 1 else x.mean(axis=0)
    ay = y if y.ndim == 1 else y.mean(axis=1)
    if x.ndim == 2:
        px, py = XY.transform(points[:, 0], points[:, 1], direction="INVERSE")
        cols = np.clip(np.floor((px-CORE[0]-1)/2).astype(int), 0, z.shape[1]-2)
        rows = np.clip(np.floor((py-CORE[1]-1)/2).astype(int), 0, z.shape[0]-2)
    else:
        cols = np.clip(np.searchsorted(ax, points[:, 0]) - 1, 0, z.shape[1] - 2)
        rows = np.clip(np.searchsorted(ay, points[:, 1]) - 1, 0, z.shape[0] - 2)
    best_distance = np.full(len(points), np.inf)
    best_error = np.full(len(points), np.inf)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            r = np.clip(rows + dr, 0, z.shape[0] - 2)
            c = np.clip(cols + dc, 0, z.shape[1] - 2)
            for a, b in (((0, 0), (0, 1)), ((0, 0), (1, 0)),
                         ((1, 0), (1, 1)), ((0, 1), (1, 1))):
                ra, ca, rb, cb = r+a[0], c+a[1], r+b[0], c+b[1]
                if x.ndim == 1:
                    p = np.column_stack((x[ca], y[ra]))
                    q = np.column_stack((x[cb], y[rb]))
                else:
                    p = np.column_stack((x[ra, ca], y[ra, ca]))
                    q = np.column_stack((x[rb, cb], y[rb, cb]))
                d = q-p
                t = np.clip(np.sum((points-p)*d, axis=1)/np.sum(d*d, axis=1), 0, 1)
                distance = np.sum((points-p-t[:, None]*d)**2, axis=1)
                error = np.abs(z[ra, ca]*(1-t)+z[rb, cb]*t-level)
                valid = np.isfinite(error)
                better = valid & ((distance < best_distance-1e-25) |
                    ((np.abs(distance-best_distance) < 1e-25) & (error < best_error)))
                best_distance[better], best_error[better] = distance[better], error[better]
    if np.sqrt(best_distance).max(initial=0) > (1e-6 if x.ndim == 1 and x.max() > 1000 else 1e-10):
        raise ValueError("Contour vertex does not lie on a declared sample edge")
    result = float(best_error.max(initial=0))
    if result > 0.001:
        raise ValueError(f"Edge height residual {result} exceeds 0.001 m")
    return result


def block_mean(z):
    if z.shape[0] % 4 or z.shape[1] % 4:
        raise ValueError("Unaligned aggregation")
    blocks = z.reshape(z.shape[0]//4, 4, z.shape[1]//4, 4)
    result = blocks.mean(axis=(1, 3), dtype=np.float64)
    result[~np.isfinite(blocks).all(axis=(1, 3))] = np.nan
    return result


def smooth(z):
    weights = np.exp(-0.5*np.arange(-3, 4, dtype=float)**2)
    weights /= weights.sum()
    result = z.copy()
    for axis in (0, 1):
        padded = np.pad(result, [(3, 3) if i == axis else (0, 0) for i in (0, 1)],
                        mode="constant", constant_values=np.nan)
        out = np.zeros_like(result)
        for offset, weight in enumerate(weights):
            selection = [slice(None), slice(None)]
            selection[axis] = slice(offset, offset+result.shape[axis])
            out += padded[tuple(selection)]*weight
        result = out
    return result


def require_product(meta):
    required = ("id", "source", "revision", "surface", "verticalReference", "units",
                "horizontalReference", "processing", "rights", "limitations")
    if any(not meta.get(key) for key in required) or meta["units"] != "m":
        raise ValueError("Incomplete/unsupported contour semantics")
    if meta["verticalReference"] not in ("LN02", "EGM2008"):
        raise ValueError("Unsupported height reference")
    if meta["horizontalReference"] not in ("EPSG:2056", "CRS84"):
        raise ValueError("Unsupported horizontal reference")


def require_merge(a, b):
    if (a["verticalReference"], a["surface"], a["source"]) != (
            b["verticalReference"], b["surface"], b["source"]):
        raise ValueError("Unapproved heightfield/source fusion")


def line_parts(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "LineString":
        return [geometry]
    if geometry.geom_type in ("MultiLineString", "GeometryCollection"):
        return [part for child in geometry.geoms for part in line_parts(child)]
    return []


def metric(points, geographic):
    if not geographic:
        return points
    xx, yy = XY.transform(points[:, 0], points[:, 1], direction="INVERSE")
    return np.column_stack((xx, yy))


def export_product(folder, meta, x, y, z, budget):
    require_product(meta)
    current, _ = memory()
    if not allocation_allowed(z.size, current):
        raise RuntimeError("Contour allocation preflight exceeds the approved working-set ceiling")
    folder.mkdir()
    budget.check()
    cg = generator(x, y, z)
    finite = np.isfinite(z)
    stats = {"shape": list(z.shape), "finite": int(finite.sum()), "invalid": int((~finite).sum()),
             "minimum": float(z[finite].min()), "maximum": float(z[finite].max()),
             "samplesOutsideDeclaredLevels": int(((z < LEVELS[0]) | (z > LEVELS[-1])).sum()),
             "lines": 0, "vertices": 0, "lengthMetres": 0., "maxEdgeResidualMetres": 0.,
             "partitionMaxDisplacementMetres": 0., "partitionLengthDifferenceMetres": 0.,
             "crs84RoundtripMaxMetres": 0., "simplificationMaxMetres": 0.,
             "simplificationCollapsedRings": 0, "simplificationIntroducedCrossings": 0,
             "byLevel": {}}
    geographic = meta["horizontalReference"] == "CRS84"
    partitions = [box(xx, yy, xx+1000, yy+1000)
                  for yy in (1091000, 1092000) for xx in (2624000, 2625000)]
    streams = [ (folder/"master.ndjson").open("xb") ] + [
        (folder/f"partition-{i}.ndjson").open("xb") for i in range(4)]
    simplified_previous = []
    originals_previous = []
    try:
        for level in LEVELS:
            budget.check()
            lines = cg.lines(level)
            metric_lines, simple_lines = [], []
            level_vertices = 0
            for index, coords in enumerate(lines):
                if len(coords) < 2 or not np.isfinite(coords).all():
                    raise ValueError("Invalid contour geometry")
                stats["maxEdgeResidualMetres"] = max(stats["maxEdgeResidualMetres"],
                    edge_residual(coords, x, y, z, level))
                projected = metric(coords, geographic)
                geometry = LineString(projected)
                metric_lines.append(geometry)
                simple = geometry.simplify(2., preserve_topology=True)
                simple_lines.append(simple)
                stats["simplificationMaxMetres"] = max(stats["simplificationMaxMetres"], geometry.hausdorff_distance(simple))
                if geometry.is_ring and (not simple.is_ring or simple.length == 0):
                    stats["simplificationCollapsedRings"] += 1
                # Explicit computational XY-only round trip, not datum accuracy.
                lon, lat = XY.transform(projected[:, 0], projected[:, 1])
                backx, backy = XY.transform(lon, lat, direction="INVERSE")
                stats["crs84RoundtripMaxMetres"] = max(stats["crs84RoundtripMaxMetres"],
                    float(np.hypot(backx-projected[:, 0], backy-projected[:, 1]).max()))
                record = {"product": meta["id"], "levelMetres": level, "index": level % 100 == 0,
                          "twentyMetreSubset": level % 20 == 0, "line": index, "coordinates": coords.tolist()}
                body = canonical(record)+b"\n"
                budget.check(len(coords), len(body))
                streams[0].write(body)
                budget.vertices += len(coords)
                clipped = geometry.intersection(box(*CORE))
                pieces = []
                for partition, stream in zip(partitions, streams[1:]):
                    for part in line_parts(geometry.intersection(partition)):
                        pieces.append(part)
                        points = list(part.coords)
                        body = canonical({"product": meta["id"], "levelMetres": level,
                                          "line": index, "coordinates": points})+b"\n"
                        budget.check(len(points), len(body))
                        stream.write(body)
                        budget.vertices += len(points)
                joined = unary_union(pieces)
                if not clipped.is_empty:
                    displacement = clipped.hausdorff_distance(joined)
                    length_error = abs(clipped.length-joined.length)
                    if displacement > 1e-6 or length_error > 1e-6:
                        raise ValueError("Partition reconstruction failed")
                    stats["partitionMaxDisplacementMetres"] = max(stats["partitionMaxDisplacementMetres"], displacement)
                    stats["partitionLengthDifferenceMetres"] = max(stats["partitionLengthDifferenceMetres"], length_error)
                stats["lines"] += 1
                stats["vertices"] += len(coords)
                level_vertices += len(coords)
                stats["lengthMetres"] += geometry.length
            # Test 2 m simplification against adjacent and all earlier levels.
            if simplified_previous:
                tree = STRtree(simplified_previous)
                for original, simple in zip(metric_lines, simple_lines):
                    for candidate in tree.query(simple, predicate="intersects"):
                        if not original.intersects(originals_previous[candidate]):
                            stats["simplificationIntroducedCrossings"] += 1
                del tree
            simplified_previous.extend(simple_lines)
            originals_previous.extend(metric_lines)
            stats["byLevel"][str(level)] = {"lines": len(lines), "vertices": level_vertices,
                "lengthMetres": sum(line.length for line in metric_lines)}
            for stream in streams:
                stream.flush()
            del lines
    finally:
        for stream in streams:
            stream.close()
    stats["simplificationAccepted"] = (stats["simplificationMaxMetres"] <= 2. and
        stats["simplificationCollapsedRings"] == 0 and stats["simplificationIntroducedCrossings"] == 0)
    if stats["crs84RoundtripMaxMetres"] > .01:
        raise ValueError("XY roundtrip exceeds 0.01 m")
    manifest = dict(meta, levelsMetres=LEVELS, intervalMetres=10, indexIntervalMetres=100,
        flags={"algorithm": "ContourPy 1.4.0 serial", "line_type": "Separate",
               "z_interp": "Linear", "corner_mask": False, "quad_as_tri": False},
        geometry="native XY NDJSON; partitions EPSG:2056; not RFC7946", statistics=stats,
        files={path.name: digest(path) for path in sorted(folder.glob("*.ndjson"))})
    budget.write(folder/"manifest.json", manifest)
    print(meta["id"], stats["vertices"], "vertices", "peak", budget.peak, flush=True)
    del cg, originals_previous, simplified_previous
    gc.collect()
    return manifest


def verify_inputs(data_root, pins):
    if len({source["id"] for source in pins["inputs"]}) != len(pins["inputs"]):
        raise ValueError("Duplicate input identities")
    for source in pins["inputs"]:
        path = data_root/source["path"]
        if not path.is_file() or path.stat().st_size != source["bytes"] or digest(path) != source["sha256"]:
            raise ValueError("Missing/changed approved input: "+source["id"])


def load_swiss(data_root, pins):
    result = np.full((4000, 4000), np.nan, dtype=np.float32)
    for source in pins["inputs"][:4]:
        with rasterio.open(data_root/source["path"]) as ds:
            if ds.crs.to_epsg() != 2056 or ds.res != (.5, .5) or ds.shape != (2000, 2000) or ds.nodata != -9999:
                raise ValueError("Unexpected Swiss grid profile")
            col = int((ds.bounds.left-CORE[0])/.5)
            row = int((CORE[3]-ds.bounds.top)/.5)
            result[row:row+2000, col:col+2000] = ds.read(1, masked=True).filled(np.nan)
    return result[::-1].copy()


def run(data_root, output, pins, budget_root=None):
    start = time.monotonic()
    if output.exists():
        raise ValueError("Fresh output directory required")
    output.mkdir(parents=True)
    budget = Budget(budget_root or output, start)
    verify_inputs(data_root, pins)
    versions = {"python": __import__("platform").python_version(), "numpy": np.__version__,
                "contourpy": contourpy.__version__, "rasterio": rasterio.__version__,
                "GDAL": rasterio.__gdal_version__, "pyproj": pyproj.__version__,
                "PROJ": pyproj.proj_version_str, "shapely": __import__("shapely").__version__}
    receipts = []
    try:
        for run_number in (1, 2):
            folder = output/f"run-{run_number}"
            folder.mkdir()
            z = load_swiss(data_root, pins)
            budget.check()
            z2 = block_mean(z)
            x, y = np.arange(CORE[0]+.25, CORE[2], .5), np.arange(CORE[1]+.25, CORE[3], .5)
            common = {"source": "swissALTI3D", "revision": "2024/2 retained tiles",
                "surface": "DTM", "verticalReference": "LN02", "units": "m",
                "horizontalReference": "EPSG:2056", "rights": "Swiss OGD; ©swisstopo",
                "limitations": "Per-cell epochs unknown; sample-centre reconstruction; no survey accuracy claim"}
            results = [export_product(folder/"swiss-native", dict(common, id="swiss-native",
                processing="native 0.5 m sample centres"), x, y, z, budget)]
            del z
            gc.collect()
            x2, y2 = np.arange(CORE[0]+1., CORE[2], 2.), np.arange(CORE[1]+1., CORE[3], 2.)
            results.append(export_product(folder/"swiss-2m", dict(common, id="swiss-2m",
                processing="strict valid 4×4 arithmetic block means"), x2, y2, z2, budget))
            zs = smooth(z2)
            results.append(export_product(folder/"swiss-smoothed", dict(common, id="swiss-smoothed",
                processing="2 m block means; Gaussian sigma 2 m, radius 6 m, full valid kernel"), x2, y2, zs, budget))
            del zs
            pipeline = pins["compoundPipeline"]
            for source in pins["inputs"][5:]:
                pipeline = pipeline.replace(Path(source["path"]).name, str(data_root/source["path"]).replace("\\", "/"))
            transform = pyproj.Transformer.from_pipeline(pipeline)
            xx, yy = np.meshgrid(x2, y2)
            lon, lat, height = transform.transform(xx, yy, z2, errcheck=True)
            diagnostic = {"heightOffsetMetres": {"min": float((height-z2).min()),
                "max": float((height-z2).max()), "mean": float((height-z2).mean())},
                "combinedAccuracy": "unknown (-1)", "pipeline": pins["compoundPipeline"]}
            results.append(export_product(folder/"swiss-egm-diagnostic", dict(common,
                id="swiss-egm-diagnostic", verticalReference="EGM2008", horizontalReference="CRS84",
                processing="full compound transformed XY/height of 2 m field; diagnostic only"), lon, lat, height, budget))
            # Copernicus window and cross-source point-post diagnostic, no full raster copy.
            west, south = XY.transform(CONTEXT[0], CONTEXT[1])
            east, north = XY.transform(CONTEXT[2], CONTEXT[3])
            with rasterio.open(data_root/pins["inputs"][4]["path"]) as ds:
                if ds.crs.to_epsg() != 4326 or ds.tags().get("AREA_OR_POINT") != "Point":
                    raise ValueError("Unexpected Copernicus registration")
                corners = [XY.transform(a, b) for a in (CONTEXT[0], CONTEXT[2]) for b in (CONTEXT[1], CONTEXT[3])]
                window = from_bounds(min(p[0] for p in corners), min(p[1] for p in corners),
                    max(p[0] for p in corners), max(p[1] for p in corners), ds.transform)
                c0, r0 = int(np.floor(window.col_off))-1, int(np.floor(window.row_off))-1
                c1, r1 = int(np.ceil(window.col_off+window.width))+1, int(np.ceil(window.row_off+window.height))+1
                if min(c0, r0) < 0 or c1 > ds.width or r1 > ds.height:
                    raise ValueError("Insufficient global context/halo")
                window = Window(c0, r0, c1-c0, r1-r0)
                global_z = ds.read(1, window=window, masked=True).filled(np.nan)[::-1].copy()
                affine = ds.window_transform(window)
                gx = affine.c+(np.arange(global_z.shape[1])+.5)*affine.a
                gy = (affine.f+(np.arange(global_z.shape[0])+.5)*affine.e)[::-1]
                # All 2 m Swiss transformed samples bilinearly sampled from the native posts.
                col = (lon-gx[0])/affine.a
                row = (lat-gy[0])/(-affine.e)
                ci, ri = np.floor(col).astype(int), np.floor(row).astype(int)
                if (ci < 0).any() or (ri < 0).any() or (ci+1 >= len(gx)).any() or (ri+1 >= len(gy)).any():
                    raise ValueError("Cross-source sampling outside support")
                fx, fy = col-ci, row-ri
                sampled = ((1-fx)*(1-fy)*global_z[ri, ci]+fx*(1-fy)*global_z[ri, ci+1]+
                           (1-fx)*fy*global_z[ri+1, ci]+fx*fy*global_z[ri+1, ci+1])
                delta = sampled-height
                diagnostic["copernicusDsmMinusTransformedSwissDtmMetres"] = {
                    "count": int(np.isfinite(delta).sum()), "mean": float(np.nanmean(delta)),
                    "min": float(np.nanmin(delta)), "max": float(np.nanmax(delta)),
                    "p05MedianP95": np.nanpercentile(delta, [5, 50, 95]).tolist(),
                    "interpretation": "represented-field diagnostic, not error/change/accuracy"}
            del xx, yy, lon, lat, height, z2, delta, sampled, ci, ri, col, row, fx, fy
            gc.collect()
            results.append(export_product(folder/"copernicus-native", {
                "id": "copernicus-native", "source": "Copernicus GLO-30 public COG",
                "revision": "retained 2021 distribution; exact sub-release unknown", "surface": "DSM",
                "verticalReference": "EGM2008", "horizontalReference": "CRS84", "units": "m",
                "processing": "native one-arcsecond point centres; bounded context plus one-post halo",
                "rights": NOTICE+"; GLO-30 F Article 6 liability/non-endorsement/downstream terms",
                "limitations": "No bare-earth/10 m accuracy claim; different epoch and footprint"}, gx, gy, global_z, budget))
            del global_z
            receipt = {"inputPinsSha256": hashlib.sha256(canonical(pins)).hexdigest(),
                       "versions": versions, "products": results, "verticalDiagnostic": diagnostic}
            budget.write(folder/"receipt.json", receipt)
            receipts.append(receipt)
            gc.collect()
        if canonical(receipts[0]) != canonical(receipts[1]):
            raise ValueError("Deterministic replay mismatch")
        verify_inputs(data_root, pins)
        budget.write(output/"completion.json", {"status": "complete", "deterministic": True,
            "receiptSha256": hashlib.sha256(canonical(receipts[0])).hexdigest(),
            "storedVertices": budget.vertices, "scratchBytesBeforeFinalReceipt": budget.check(),
            "peakWorkingSetBytes": budget.peak, "elapsedSeconds": time.monotonic()-start,
            "sourceHashesVerifiedBeforeAndAfter": True, "networkRequests": 0, "limits": LIMITS})
    except Exception as error:
        # Partial products are retained and never relabelled as complete.
        body = {"status": "stopped", "reason": str(error), "storedVertices": budget.vertices,
                "peakWorkingSetBytes": budget.peak, "elapsedSeconds": time.monotonic()-start}
        path = output/"stopped.json"
        if not path.exists():
            path.write_bytes(canonical(body)+b"\n")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--budget-root", type=Path)
    args = parser.parse_args()
    pins = json.loads(Path(__file__).with_name("input-pins.json").read_text())
    run(args.data_root, args.output, pins, args.budget_root)
