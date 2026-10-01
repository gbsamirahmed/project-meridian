"""Lab 011: signed provider-product difference, never semantic object heights."""
from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from PIL import Image

import experiment_paths  # Establish the existing storage-resolver import path.
from meridian_paths import resolve_storage_roots

BOUNDS = (264900, 357800, 267900, 360800)
THRESHOLDS = (0.25, 0.5, 1.0, 2.0, 3.0)
SCALES = (1, 3, 5, 10, 20)
WARNING = "DSM-DTM is a signed provider-product difference, not object height. Low residual does not exclude rock; high residual does not identify rock or vegetation."


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def statistics(a):
    v = np.asarray(a)[np.isfinite(a)].astype(np.float64)
    if not v.size:
        return {"valid_cells": 0}
    percentiles = (1, 5, 25, 50, 75, 90, 95, 99, 99.5, 99.9)
    return {"valid_cells": int(v.size), "min_m": float(v.min()), "max_m": float(v.max()),
            "mean_m": float(v.mean()), "median_m": float(np.median(v)), "std_m": float(v.std()),
            "percentiles_m": {str(p): float(x) for p, x in zip(percentiles, np.percentile(v, percentiles))}}


def difference(dtm, dsm):
    valid = np.isfinite(dtm) & np.isfinite(dsm)
    result = np.full(dtm.shape, np.nan, np.float32)
    result[valid] = dsm[valid].astype(np.float64) - dtm[valid].astype(np.float64)
    return result


def window_fields(a, size):
    """Valid square windows only; even sizes centre 0.5 m SE of labelled cell."""
    a = np.asarray(a, dtype=np.float64)
    if size == 1:
        return {"mean":a.astype(np.float32), "max":a.astype(np.float32),
                "std":np.zeros(a.shape,np.float32), "range":np.zeros(a.shape,np.float32)}
    def box_sum(x):
        integral = np.pad(x, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        return integral[size:, size:] - integral[:-size, size:] - integral[size:, :-size] + integral[:-size, :-size]
    mean = box_sum(a) / size**2
    variance = np.maximum(0, box_sum(a*a) / size**2 - mean*mean)
    # Separable extrema avoid an enormous size x size sliding-window allocation.
    rows = np.lib.stride_tricks.sliding_window_view(a, size, axis=0)
    lo, hi = rows.min(-1), rows.max(-1)
    lo = np.lib.stride_tricks.sliding_window_view(lo, size, axis=1).min(-1)
    hi = np.lib.stride_tricks.sliding_window_view(hi, size, axis=1).max(-1)
    def align(x):
        out = np.full(a.shape, np.nan, np.float32)
        start = (size-1)//2
        out[start:start+x.shape[0], start:start+x.shape[1]] = x
        return out
    return {"mean": align(mean), "std": align(np.sqrt(variance)), "range": align(hi-lo), "max": align(hi)}


def components(mask):
    """Deterministic 4-neighbour run-length union/find; no extra dependency."""
    labels = np.zeros(mask.shape, np.int32)
    parents = [0]
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    previous = []
    for row, values in enumerate(mask):
        transitions = np.diff(np.pad(values.astype(np.int8), (1, 1)))
        current = []
        j = 0
        for start, stop in zip(np.flatnonzero(transitions == 1), np.flatnonzero(transitions == -1)):
            label = len(parents)
            parents.append(label)
            labels[row, start:stop] = label
            while j < len(previous) and previous[j][1] <= start:
                j += 1
            k = j
            while k < len(previous) and previous[k][0] < stop:
                p = find(previous[k][2])
                q = find(label)
                parents[max(p, q)] = min(p, q)
                k += 1
            current.append((int(start), int(stop), label))
        previous = current
    roots = np.array([find(i) for i in range(len(parents))], np.int32)
    unique = np.unique(roots[1:])
    compact = np.zeros(len(parents), np.int32)
    compact[unique] = np.arange(1, len(unique)+1)
    return compact[roots[labels]]


def component_summary(labels, residual):
    rr, cc = np.nonzero(labels)
    ids = labels[rr, cc]
    count = int(labels.max())
    area = np.bincount(ids, minlength=count+1)
    if not count:
        return {"component_count": 0}, []
    values = residual[rr, cc].astype(np.float64)
    total = np.bincount(ids, weights=values, minlength=count+1)
    squares = np.bincount(ids, weights=values**2, minlength=count+1)
    maximum = np.full(count+1, -np.inf)
    np.maximum.at(maximum, ids, values)
    rmin, cmin = np.full(count+1, labels.shape[0]), np.full(count+1, labels.shape[1])
    rmax, cmax = np.zeros(count+1, int), np.zeros(count+1, int)
    np.minimum.at(rmin, ids, rr); np.minimum.at(cmin, ids, cc)
    np.maximum.at(rmax, ids, rr); np.maximum.at(cmax, ids, cc)
    ordered = sorted(range(1, count+1), key=lambda i: (-int(area[i]), i))
    records = []
    for i in ordered[:30]:
        mean = total[i]/area[i]
        records.append({"id": i, "area_m2": int(area[i]), "max_m": float(maximum[i]),
                        "mean_m": float(mean), "std_m": float(np.sqrt(max(0, squares[i]/area[i]-mean*mean))),
                        "bounds_bng": [int(BOUNDS[0]+cmin[i]), int(BOUNDS[3]-rmax[i]-1),
                                       int(BOUNDS[0]+cmax[i]+1), int(BOUNDS[3]-rmin[i])],
                        "bbox_fill_fraction": float(area[i]/((rmax[i]-rmin[i]+1)*(cmax[i]-cmin[i]+1))),
                        "bbox_axis_ratio": float(max(rmax[i]-rmin[i]+1, cmax[i]-cmin[i]+1)/min(rmax[i]-rmin[i]+1, cmax[i]-cmin[i]+1)),
                        "touches_aoi_edge": bool(rmin[i] == 0 or cmin[i] == 0 or rmax[i] == labels.shape[0]-1 or cmax[i] == labels.shape[1]-1)})
    areas = area[1:]
    robust = maximum[1:][areas >= 9]
    summary = {"component_count": count, "covered_cells": int(areas.sum()),
               "components_per_km2": count/9, "area_percentiles_m2": {str(p): float(v) for p,v in zip((50,90,95,99),np.percentile(areas,(50,90,95,99)))},
               "largest_area_m2": int(areas.max()), "single_cell_components": int(np.sum(areas == 1)),
               "single_cell_share_of_threshold_area_pct": float(100*np.sum(areas[areas == 1])/areas.sum()),
               "area_in_components_at_least_m2_pct": {str(n): float(100*np.sum(areas[areas >= n])/areas.sum()) for n in (4,9,25,100)},
               "maximum_in_component_at_least_9m2_m": float(robust.max()) if robust.size else None,
               "largest_components": records}
    return summary, records


def raster(path, values, profile):
    with rasterio.open(path, "w", **{**profile, "driver": "GTiff", "dtype": "float32", "count": 1,
                                    "nodata": np.nan, "compress": "deflate", "predictor": 3}) as dst:
        dst.write(values.astype(np.float32), 1)
        dst.set_band_unit(1, "m")


def build(repo):
    root = resolve_storage_roots(repository_root=repo, require_data=True).data
    source = root / "sources/atlas/tryfan/welsh-lidar-1m"
    catalogue = json.loads((repo / "docs/atlas/tryfan-data-catalog.json").read_text())
    source_files = catalogue["products"][0]["files"]
    audit = []
    for item in source_files:
        path = root / item["destination"].split("${MERIDIAN_DATA_ROOT}/", 1)[1]
        if sha256(path) != item["sha256"]:
            raise ValueError("Preserved source identity mismatch: " + path.name)
        audit.append({"path": item["destination"], "sha256": item["sha256"], "bytes": path.stat().st_size})
    manifest = json.loads((source / "metadata/manifest.json").read_text())
    tiles = manifest["catalogue"]["national_features"]
    if any(x["date"] != "02-03-2021" or x["delivery"] != "11" for x in tiles):
        raise ValueError("Incompatible acquisition provenance")
    arrays, grids = [], []
    for kind in ("dtm", "dsm"):
        with rasterio.open(source / f"rasters/tryfan-004-{kind}-1m.tif") as src:
            grids.append((src.crs, src.transform, src.shape, src.bounds))
            arrays.append(src.read(1, masked=True).filled(np.nan))
            profile = src.profile
    if grids[0] != grids[1] or str(grids[0][0]) != "EPSG:27700" or tuple(grids[0][3]) != BOUNDS or grids[0][2] != (3000,3000):
        raise ValueError("Nonidentical or noncanonical source grids")
    if not all(np.isfinite(a).all() for a in arrays):
        raise ValueError("Incomplete AOI coverage; do not conceal nodata")
    dtm, dsm = arrays
    residual = difference(dtm, dsm)
    if abs(float(np.median(residual))) > 0.5:
        raise ValueError("Unexpected systematic difference; review before interpreting")
    output = root / "experiments/earth-lab/tryfan-011/observed-surface-height-v1"
    output.mkdir(parents=True, exist_ok=True)
    raster(output / "lab011-signed-residual-1m.tif", residual, profile)
    dy, dx = np.gradient(dtm.astype(np.float64), edge_order=2)
    slope = np.degrees(np.arctan(np.hypot(dx,dy))).astype(np.float32)
    terrain5 = window_fields(dtm, 5)
    # Departure from local mean: a planar slope is zero in valid interior windows.
    departure = dtm - terrain5["mean"]
    raster(output / "lab011-dtm-local-relief-5m.tif", terrain5["range"], profile)
    raster(output / "lab011-dtm-departure-from-5m-mean.tif", departure, profile)
    threshold_report = {}
    for threshold in THRESHOLDS:
        labels = components(residual > threshold)
        summary, _ = component_summary(labels, residual)
        summary["aoi_area_pct"] = float(100*np.mean(residual > threshold))
        threshold_report[str(threshold)] = summary
    scale_report, fields = {}, {}
    for size in SCALES:
        f = window_fields(residual, size)
        scale_report[str(size)] = {key: statistics(value) for key,value in f.items() if key != "mean"}
        scale_report[str(size)]["mean_gt_1m_pct_of_valid_windows"] = float(100*np.mean(f["mean"][np.isfinite(f["mean"])] > 1))
        if size in (5,20):
            raster(output / f"lab011-residual-range-{size}m.tif", f["range"], profile)
            raster(output / f"lab011-residual-std-{size}m.tif", f["std"], profile)
            fields[size] = f
    slope_report = []
    for lo, hi in ((0,10),(10,20),(20,30),(30,45),(45,60),(60,90)):
        mask = (slope >= lo) & (slope < hi)
        slope_report.append({"slope_degrees": [lo,hi], "cells": int(mask.sum()),
                             "residual": statistics(residual[mask]), "residual_gt_1m_pct": float(100*np.mean(residual[mask] > 1)) if mask.any() else None})
    rough_report = []
    for lo, hi in ((0,.1),(.1,.25),(.25,.5),(.5,1),(1,2),(2,1000)):
        mask = (np.abs(departure) >= lo) & (np.abs(departure) < hi)
        rough_report.append({"absolute_dtm_departure_m": [lo,hi], "cells": int(mask.sum()), "residual": statistics(residual[mask])})
    # Exact source sample coordinates, including both extrema and interior corners.
    points = [(5,5),(5,2994),(2994,5),(2994,2994),(1500,1500),
              tuple(int(x) for x in np.unravel_index(np.argmax(residual),residual.shape)),
              tuple(int(x) for x in np.unravel_index(np.argmin(residual),residual.shape))]
    samples = []
    for row,col in points:
        patch = residual[max(0,row-2):row+3,max(0,col-2):col+3]
        samples.append({"row": row, "column": col, "easting_m": BOUNDS[0]+col+.5,
                        "northing_m": BOUNDS[3]-row-.5, "dtm_m": float(dtm[row,col]), "dsm_m": float(dsm[row,col]),
                        "residual_m": float(residual[row,col]), "residual_5x5_neighbourhood": statistics(patch),
                        "slope_degrees": float(slope[row,col]), "dtm_relief_5m_m": float(terrain5["range"][row,col]),
                        "distance_to_nearest_1km_grid_line_m": min(abs((BOUNDS[0]+col+.5)-round((BOUNDS[0]+col+.5)/1000)*1000),
                                                                  abs((BOUNDS[3]-row-.5)-round((BOUNDS[3]-row-.5)/1000)*1000))})
    # Choose crop centres using scores on 100x100 blocks, never semantic labels.
    examples = []
    block_shape = (30,100,30,100)
    block_res = residual.reshape(block_shape).mean((1,3))
    block_relief = np.nanmean(terrain5["range"].reshape(block_shape),axis=(1,3))
    scores = {"strong-positive": block_res, "high-terrain-low-residual": np.where(block_res <= .25,block_relief,-np.inf),
              "both-high": np.where(block_res > 1,block_relief,-np.inf), "smooth-terrain": -block_relief}
    for name,score in scores.items():
        br,bc = np.unravel_index(np.argmax(score),score.shape)
        r,c = int(br)*100,int(bc)*100
        examples.append({"name": name,"row_start": r,"column_start": c,"size_cells": 100,
                         "bounds_bng": [BOUNDS[0]+c,BOUNDS[3]-r-100,BOUNDS[0]+c+100,BOUNDS[3]-r],
                         "mean_residual_m": float(block_res[br,bc]),"mean_local_dtm_relief_5m_m": float(block_relief[br,bc])})
    # Fixed continuous quantitative display; negative differences remain in canonical raster.
    positive = np.clip(np.log1p(np.maximum(residual,0))/np.log(11),0,1)
    display = np.rint(matplotlib.colormaps["viridis"](positive)[...,:3]*255).astype(np.uint8)
    Image.fromarray(display).save(output / "lab011-positive-residual-diagnostic-1m.png")
    fig,ax=plt.subplots(figsize=(10,1.5),layout="constrained")
    colourbar=matplotlib.colorbar.ColorbarBase(ax,cmap=matplotlib.colormaps["viridis"],norm=matplotlib.colors.Normalize(0,1),orientation="horizontal")
    ticks=np.array([0,.25,.5,1,2,3,5,10])
    colourbar.set_ticks(np.log1p(ticks)/np.log(11),labels=[str(x) for x in ticks])
    colourbar.set_label("Unreal diagnostic: positive DSM−DTM (m); log1p stretch; ≥10m saturated, ≤0m at lower endpoint")
    fig.savefig(output/"lab011-renderer-legend.png",dpi=150,metadata={"Software":"Meridian Lab 011"}); plt.close(fig)
    figure(output / "lab011-overview.png", dtm,dsm,residual,terrain5,departure,fields)
    fig,ax = plt.subplots(1,2,figsize=(12,4),layout="constrained")
    ax[0].hist(residual.ravel(),bins=240,range=(-12,25),log=True,color="0.35")
    ax[0].set(xlabel="Signed DSM−DTM (m)",ylabel="Cells (log count)",title="Full distribution; signed extremes retained")
    sorted_values = np.sort(residual.ravel())
    sample_indices = np.linspace(0,len(sorted_values)-1,10000,dtype=int)
    ax[1].plot(sorted_values[sample_indices],100*sample_indices/(len(sorted_values)-1),color="0.25")
    ax[1].set(xlabel="Signed DSM−DTM (m)",ylabel="Cumulative cells (%)",title="Empirical cumulative distribution")
    fig.savefig(output / "lab011-distribution.png",dpi=150,metadata={"Software":"Meridian Lab 011"}); plt.close(fig)
    crops(output, examples, dtm, residual, terrain5)
    # Lab 010 comparison: signed 1m mean aggregated exactly into its 10m footprint.
    lab010 = root / "experiments/earth-lab/tryfan-010/observed-natural-colour-v1"
    lm = json.loads((lab010 / "lab010-manifest.json").read_text())
    for item in lm["products"]:
        if sha256(lab010/item["path"]) != item["sha256"]:
            raise ValueError("Lab 010 identity mismatch")
    with rasterio.open(lab010 / "lab010-rgb-reflectance-10m.tif") as src:
        if src.crs != grids[0][0] or tuple(src.bounds) != BOUNDS or src.shape != (300,300):
            raise ValueError("Lab 010 registration mismatch")
        rgb = src.read()
    aggregated = residual.reshape(300,10,300,10).mean((1,3))
    colour_comparison = {"method": "Mean signed 1m difference in exact 10x10m cells; Pearson correlation with unaltered reflectance bands, no semantic classification",
                         "correlation_rgb": [float(np.corrcoef(aggregated.ravel(),band.ravel())[0,1]) for band in rgb],
                         "lab010_manifest_sha256": sha256(lab010 / "lab010-manifest.json"),
                         "limitation": "10m colour is too coarse to identify single-cell or several-metre structures; different acquisition dates and illumination confound correlation."}
    products = [{"path": p.name,"bytes": p.stat().st_size,"sha256": sha256(p)} for p in sorted(output.iterdir()) if p.suffix in (".tif",".png")]
    report = {"schema_version":1,"experiment":"LAB 011 — OBSERVED SURFACE-HEIGHT STRUCTURE","warning":WARNING,
              "sources":audit,"provider":"Welsh Government","acquisition":"2021-03-02","delivery":"11",
              "source_urls": {k: manifest["selection"][k+"_url"] for k in ("dtm","dsm")},"licence":manifest["licence"],
              "vertical_reference": {"units":"metres, as established by retained source/terrain manifests", "datum":"ODN in existing terrain provenance; neither TIFF explicitly encodes a vertical CRS/unit",
                                     "compatibility":"Same provider delivery/acquisition and identical grids. No vertical transformation. Absolute datum independently unspecified in downloaded TIFF metadata; difference is relative to these paired products.",
                                     "classification":"Provider DTM/DSM labels; exact rocky-ground filtering/interpolation rules unavailable. No object-height interpretation."},
              "aoi":{"crs":"EPSG:27700","bounds":list(BOUNDS),"dimensions":[3000,3000],"pixel_size_m":1,"transform":list(grids[0][1])[:6],"row_zero":"north","column_zero":"west"},
              "processing":{"subtraction":"float64 DSM minus DTM then float32 output; signed values retained; no smoothing/resampling", "nodata":"NaN if either source invalid; both source masks contain zero invalid cells", "thresholds_m":list(THRESHOLDS),"connectivity":4,
                            "window_sizes_m":list(SCALES),"window_edges":"Only complete square windows; undefined boundary diagnostics are NaN. Even windows centre 0.5m east/south of labelled cell.",
                            "slope":"arctan(hypot(dDTM/dx,dDTM/dy)), NumPy 1m gradient; second-order one-sided outer edge", "roughness":"DTM minus 5x5 local mean, not slope-confounded elevation standard deviation; local relief=max-min over 5x5",
                            "runtime":{"python":platform.python_version(),"numpy":np.__version__,"rasterio":rasterio.__version__,"gdal":rasterio.__gdal_version__,"matplotlib":matplotlib.__version__},
                            "renderer_display":"viridis(clip(log(1+max(residual,0))/log(11),0,1)); fixed 0–10m log stretch; 3000x3000 1m RGB, north at row zero; negatives visible only in signed offline view"},
              "residual_statistics":statistics(residual),"negative_statistics":statistics(residual[residual<0]),"negative_area_pct":float(100*np.mean(residual<0)),
              "negative_tail_area_pct":{"below_minus_0.25m":float(100*np.mean(residual < -.25)),"below_minus_1m":float(100*np.mean(residual < -1)),"below_minus_2m":float(100*np.mean(residual < -2))},
              "near_zero_area_pct":{"abs_le_0.1m":float(100*np.mean(np.abs(residual)<=.1)),"abs_le_0.25m":float(100*np.mean(np.abs(residual)<=.25))},
              "thresholds":threshold_report,"multiscale":scale_report,"slope_relationship":slope_report,"roughness_relationship":rough_report,
              "independent_sample_coordinates":samples,"diagnostic_crops":examples,"lab010_comparison":colour_comparison,
              "extremes_assessment":"Both extremes are interior valid paired source cells, not AOI/nodata/resampling edges. Neighbourhoods retained for review. Product interpolation/classification or genuine surface variation cannot be distinguished without return-level evidence; no extremes discarded.",
              "products":products,"semantics":{"observed":"Provider DTM and DSM", "derived":"Signed difference and quantitative diagnostics", "rendered":"Offline figures and reversible quantitative Unreal display", "inferred":"No semantic classes; cautious analytical interpretation only", "reconstructed":"None"},
              "manual_visual_acceptance":"Pending fixed-camera Lab 010/Lab 011/overlay inspection; lighting warning not corrected"}
    report["identity"] = hashlib.sha256(json.dumps(report,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    (output / "lab011-manifest.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report


def figure(path, dtm,dsm,residual,terrain,departure,fields):
    fig,axes = plt.subplots(2,4,figsize=(18,10),layout="constrained")
    views = [(dtm,"DTM: provider terrain (m)","terrain",None,None),
             (dsm,"DSM: provider surface (m)","terrain",None,None),
             (residual,"Signed DSM−DTM (m); display clipped ±2","coolwarm",-2,2),
             (np.maximum(residual,0),"Positive difference (m); display 0–p99","viridis",0,float(np.percentile(residual,99))),
             (fields[5]["std"],"Residual std, 5m square (m)","magma",0,2),
             (fields[20]["range"],"Residual range, 20m square (m)","magma",0,10),
             (terrain["range"],"DTM local relief, 5m square (m)","cividis",0,15),
             (np.abs(departure),"Absolute DTM departure from 5m mean (m)","cividis",0,1)]
    for ax,(a,title,cmap,lo,hi) in zip(axes.flat,views):
        im=ax.imshow(a,origin="upper",extent=BOUNDS[0:1]+BOUNDS[2:3]+BOUNDS[1:2]+BOUNDS[3:4],cmap=cmap,vmin=lo,vmax=hi)
        ax.set(title=title,xlabel="BNG easting (m)",ylabel="BNG northing (m)")
        fig.colorbar(im,ax=ax,shrink=.65,label="m")
    fig.savefig(path,dpi=130,metadata={"Software":"Meridian Lab 011"}); plt.close(fig)


def crops(output,examples,dtm,residual,terrain):
    fig,axes=plt.subplots(len(examples),3,figsize=(12,14),layout="constrained")
    for row,item in enumerate(examples):
        r,c=item["row_start"],item["column_start"]
        box=item["bounds_bng"]; extent=(box[0],box[2],box[1],box[3])
        for ax,a,title,cmap,lo,hi in zip(axes[row],(dtm,residual,terrain["range"]),
                ("DTM (m)","Signed residual (m)","DTM 5m relief (m)"),("terrain","coolwarm","cividis"),(None,-2,0),(None,2,15)):
            im=ax.imshow(a[r:r+100,c:c+100],origin="upper",extent=extent,cmap=cmap,vmin=lo,vmax=hi)
            ax.set(title=item["name"]+" / "+title,xlabel="BNG easting (m)",ylabel="BNG northing (m)")
            fig.colorbar(im,ax=ax,shrink=.65)
    fig.savefig(output/"lab011-diagnostic-crops.png",dpi=130,metadata={"Software":"Meridian Lab 011"}); plt.close(fig)


if __name__ == "__main__":
    report=build(Path(__file__).resolve().parents[2])
    print(json.dumps({"identity":report["identity"],"residual":report["residual_statistics"],"products":report["products"]},indent=2))
