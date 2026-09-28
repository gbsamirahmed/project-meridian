"""Run Meridian Earth Laboratory 007 uncertain underlying-surface inference."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = Path(__file__).resolve().parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from analyze_surface_evidence import _terrain_aggregates
from surface_evidence import AnalysisGrid, numeric_summary, sha256_file, stable_json_sha256
from underlying_surface_model import (
    CLASSES, categorical_preferences, fuse_sources, geology_preferences,
    sentinel_preferences, terrain_preferences,
)


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read(path: Path, *, categorical: bool = False) -> np.ndarray:
    with rasterio.open(path) as source:
        values = source.read(1)
        if categorical:
            return values
        values = values.astype(np.float64)
        if source.nodata is not None:
            values[values == source.nodata] = np.nan
        return values


def _write_float(path: Path, values: np.ndarray, grid: AnalysisGrid) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.asarray(values, dtype=np.float32)
    encoded = np.where(np.isfinite(data), data, -9999.0).astype(np.float32)
    with rasterio.open(path, "w", driver="GTiff", width=grid.width, height=grid.height, count=1, dtype="float32", crs=grid.crs, transform=grid.transform, nodata=-9999.0, compress="deflate", predictor=3) as target:
        target.write(encoded, 1)


def _write_byte(path: Path, values: np.ndarray, grid: AnalysisGrid) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", width=grid.width, height=grid.height, count=1, dtype="uint8", crs=grid.crs, transform=grid.transform, nodata=0, compress="deflate") as target:
        target.write(np.asarray(values, dtype=np.uint8), 1)


def _verify_inputs(config: dict[str, Any]) -> tuple[dict[str, Path], dict[str, str]]:
    paths: dict[str, Path] = {}
    hashes: dict[str, str] = {}
    for name, item in config["frozen_inputs"].items():
        path = _path(item["path"])
        observed = sha256_file(path)
        if observed.lower() != item["sha256"].lower():
            raise RuntimeError(f"Frozen input changed: {path} ({observed})")
        paths[name] = path
        hashes[name] = observed
    lab006 = json.loads(paths["lab006_report"].read_text(encoding="utf-8"))
    if lab006.get("deterministic_result_sha256") != config["frozen_inputs"]["lab006_report"]["deterministic_result_sha256"]:
        raise RuntimeError("Lab 006 deterministic result identity is not the frozen value")
    return paths, hashes


def _lookup(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _upsample_20m(values: np.ndarray) -> np.ndarray:
    return np.repeat(np.repeat(values, 2, axis=0), 2, axis=1)


def _group_summary(ids: np.ndarray, lookup: dict[int, str], probabilities: np.ndarray, uncertainty: np.ndarray) -> list[dict[str, Any]]:
    rows = []
    for identifier in sorted(int(value) for value in np.unique(ids)):
        mask = ids == identifier
        if not np.any(mask):
            continue
        rows.append({
            "id": identifier, "name": lookup.get(identifier, "unavailable"), "cells": int(mask.sum()),
            "mean_probabilities": {name: float(np.nanmean(probabilities[..., index][mask])) for index, name in enumerate(CLASSES)},
            "mean_uncertainty": float(np.nanmean(uncertainty[mask])),
        })
    return rows


def _binned(values: np.ndarray, edges: list[float], probabilities: np.ndarray, uncertainty: np.ndarray) -> list[dict[str, Any]]:
    rows = []
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = np.isfinite(values) & (values >= lower) & (values < upper)
        if not np.any(mask):
            continue
        rows.append({
            "lower": lower, "upper": None if np.isinf(upper) else upper, "cells": int(mask.sum()),
            "mean_probabilities": {name: float(np.nanmean(probabilities[..., index][mask])) for index, name in enumerate(CLASSES)},
            "mean_uncertainty": float(np.nanmean(uncertainty[mask])),
        })
    return rows


def _coverage(availability: dict[str, np.ndarray], superficial_mapped: np.ndarray, valid: np.ndarray, probabilities: np.ndarray, uncertainty: np.ndarray) -> tuple[dict[str, Any], np.ndarray]:
    count = sum(np.asarray(availability[name], dtype=np.uint8) for name in ("terrain", "sentinel", "habitat", "geology"))
    total = int(valid.size)
    result: dict[str, Any] = {
        "total_cells": total, "valid_model_cells": int(valid.sum()), "no_valid_model_cells": int((~valid).sum()),
        "families": {name: {"cells": int(np.count_nonzero(mask & valid)), "fraction_of_aoi": float(np.mean(mask & valid))} for name, mask in availability.items()},
        "bgs_superficial_context": {
            "source_available_cells": int(np.count_nonzero(availability["geology"] & valid)),
            "mapped_deposit_cells": int(np.count_nonzero(superficial_mapped & valid)),
            "valid_none_mapped_cells": int(np.count_nonzero(availability["geology"] & ~superficial_mapped & valid)),
            "source_unavailable_cells": int(np.count_nonzero(~availability["geology"] & valid)),
        },
        "family_count": {},
    }
    for number in range(5):
        mask = valid & (count == number)
        result["family_count"][str(number)] = {
            "cells": int(mask.sum()), "fraction_of_valid_model": float(mask.sum() / max(valid.sum(), 1)),
            "mean_uncertainty": None if not np.any(mask) else float(np.nanmean(uncertainty[mask])),
            "mean_other_unknown": None if not np.any(mask) else float(np.nanmean(probabilities[..., 5][mask])),
        }
    return result, count


def _context_at(row: int, column: int, arrays: dict[str, np.ndarray], habitat_lookup: dict[str, Any], geology_lookup: dict[str, Any]) -> dict[str, Any]:
    source_id = int(arrays["habitat_source"][row, column])
    group_id = int(arrays["habitat_group"][row, column])
    bedrock_id = int(arrays["bedrock_unit"][row, column])
    superficial_id = int(arrays["superficial_unit"][row, column])
    bedrock = {int(item["id"]): item for item in geology_lookup["bedrock"]["palette"]}.get(bedrock_id)
    superficial = {int(item["id"]): item for item in geology_lookup["superficial"]["palette"]}.get(superficial_id)
    return {
        "habitat": {
            "source_category_id": source_id,
            "source_class": habitat_lookup["source_categories"].get(str(source_id), "unavailable"),
            "meridian_group": habitat_lookup["simplified_groups"].get(str(group_id), "unavailable"),
            "temporal_context": "Historical contextual field survey, 1979-1997; not assumed unchanged.",
        },
        "geology": {
            "bedrock_unit": None if bedrock is None else bedrock["name"],
            "formation": None if bedrock is None else bedrock["properties"].get("LEX_D"),
            "lithology": None if bedrock is None else bedrock["properties"].get("RCS_D"),
            "nominal_scale": None if bedrock is None else bedrock["properties"].get("NOM_SCALE"),
            "nominal_mapping_year": None if bedrock is None else bedrock["properties"].get("NOM_BGS_YR"),
            "release": None if bedrock is None else bedrock["properties"].get("RELEASED"),
            "superficial_deposit": None if superficial is None else superficial["name"],
            "superficial_status": "valid_none_mapped" if superficial_id == 0 else "mapped_deposit",
        },
    }


def _save_diagnostics(output: Path, probabilities: np.ndarray, dominant: np.ndarray, uncertainty: np.ndarray, conflict: np.ndarray, contributions: dict[str, np.ndarray], evidence_count: np.ndarray, arrays: dict[str, np.ndarray], trace: dict[str, Any]) -> list[Path]:
    images = output / "images"; images.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    colours = ["#6f6b68", "#b58a59", "#66543f", "#8ca45a", "#5b8e83", "#3c4144"]
    cmap = ListedColormap(colours); norm = BoundaryNorm(np.arange(.5, 7.5), 6)
    def save(name, figure):
        path = images / name; figure.savefig(path, dpi=160, bbox_inches="tight"); plt.close(figure); paths.append(path)
    fig, ax = plt.subplots(figsize=(7, 7)); im=ax.imshow(dominant, cmap=cmap, norm=norm); ax.set_title("Dominant inferred underlying surface class"); ax.set_axis_off();
    handles=[plt.Line2D([0],[0],marker='s',linestyle='',color=colours[i],label=CLASSES[i]) for i in range(6)]; ax.legend(handles=handles,loc="lower left",fontsize=8); save("dominant-surface-class.png",fig)
    fig, ax=plt.subplots(figsize=(7,7)); im=ax.imshow(uncertainty,cmap="magma",vmin=0,vmax=1); ax.set_title("Normalized model uncertainty (entropy)"); ax.set_axis_off(); fig.colorbar(im,ax=ax,label="0 certain — 1 maximally ambiguous"); save("uncertainty-entropy.png",fig)
    for index, name in enumerate(CLASSES):
        fig, ax=plt.subplots(figsize=(7,7)); im=ax.imshow(probabilities[...,index],cmap="viridis",vmin=0,vmax=.65); ax.set_title(f"P({name}) — underlying surface inference"); ax.set_axis_off(); fig.colorbar(im,ax=ax,label="probability"); save(f"probability-{name}.png",fig)
    fig, axes=plt.subplots(1,5,figsize=(18,4),constrained_layout=True)
    for axis,(source,values) in zip(axes[:4],contributions.items()): axis.imshow(np.argmax(values,axis=-1)+1,cmap=cmap,norm=norm); axis.set_title(f"{source} preferred class"); axis.set_axis_off()
    im=axes[4].imshow(conflict,cmap="inferno",vmin=0,vmax=1); axes[4].set_title("Source conflict (JS)"); axes[4].set_axis_off(); fig.colorbar(im,ax=axes[4],fraction=.05); save("source-contributions-and-conflict.png",fig)
    fig, axes=plt.subplots(1,3,figsize=(13,4),constrained_layout=True); axes[0].imshow(evidence_count,cmap="viridis",vmin=0,vmax=4); axes[0].set_title("Available major families (0–4)"); axes[1].imshow(arrays["habitat_group"]>0,cmap="gray"); axes[1].set_title("Historical habitat available"); axes[2].imshow(arrays["superficial_group"]>0,cmap="gray"); axes[2].set_title("Mapped superficial deposit\n(black can be valid none mapped)"); [axis.set_axis_off() for axis in axes]; save("evidence-coverage.png",fig)
    fig, axes=plt.subplots(1,3,figsize=(13,4),constrained_layout=True); axes[0].imshow(arrays["slope"],cmap="magma",vmin=0,vmax=60); axes[0].set_title("Mean slope (degrees)"); axes[1].imshow(arrays["roughness"],cmap="viridis",vmin=0,vmax=1.5); axes[1].set_title("~15 m roughness (m RMS)"); axes[2].imshow(dominant,cmap=cmap,norm=norm); axes[2].set_title("Dominant inference"); [axis.set_axis_off() for axis in axes]; save("terrain-and-inferred-surface.png",fig)
    fig, ax=plt.subplots(figsize=(10,5)); names=list(trace["surface"]["probabilities"]); values=list(trace["surface"]["probabilities"].values()); ax.bar(names,values,color=colours); ax.set_ylim(0,.65); ax.set_ylabel("probability"); ax.set_title("Canonical Tryfan point evidence trace"); ax.tick_params(axis='x',rotation=25); text=f"NRW: {trace['context']['habitat']['source_class']}\nBGS: {trace['context']['geology']['bedrock_unit']}\nSuperficial: {trace['context']['geology']['superficial_status']}\nSlope {trace['evidence']['terrain']['slope_degrees']:.1f}°, roughness {trace['evidence']['terrain']['roughness_15m_rms_m']:.2f} m\nNDVI temporal median {trace['evidence']['sentinel']['ndvi_temporal_median']:.3f}\nUncertainty {trace['surface']['uncertainty']:.3f}"; ax.text(1.02,.95,text,transform=ax.transAxes,va='top',fontsize=8); save("canonical-tryfan-evidence-trace.png",fig)
    return paths


def run(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths, hashes_before = _verify_inputs(config)
    output = _path(config["output_root"]); rasters=output/"rasters"; contributions_root=output/"contributions"
    west,south,east,north=config["aoi"]["bounds"]
    grid=AnalysisGrid(config["aoi"]["crs"],west,south,east,north,float(config["aoi"]["resolution_m"]))
    lab005a=paths["lab005a_report"].parent; lab005c=paths["lab005c_report"].parent; lab006=paths["lab006_report"].parent
    source_products = {
        **{f"lab005a:{item.name}": item for item in sorted((lab005a / "rasters").glob("*.tif"))},
        "lab005c:ndvi_surface_median_10m.tif": lab005c / "temporal" / "ndvi_surface_median_10m.tif",
        "lab005c:ndvi_surface_standard_deviation_10m.tif": lab005c / "temporal" / "ndvi_surface_standard_deviation_10m.tif",
        "lab005c:ndmi_surface_median_20m.tif": lab005c / "temporal" / "ndmi_surface_median_20m.tif",
        "lab005c:persistent_low_ndvi_evidence_10m.tif": lab005c / "temporal" / "persistent_low_ndvi_evidence_10m.tif",
        "lab006:habitat-source-category-10m.tif": lab006 / "aligned" / "habitat-source-category-10m.tif",
        "lab006:habitat-simplified-group-10m.tif": lab006 / "aligned" / "habitat-simplified-group-10m.tif",
        "lab006:geology-bedrock-unit-10m.tif": lab006 / "aligned" / "geology-bedrock-unit-10m.tif",
        "lab006:geology-bedrock-broad-group-10m.tif": lab006 / "aligned" / "geology-bedrock-broad-group-10m.tif",
        "lab006:geology-superficial-unit-10m.tif": lab006 / "aligned" / "geology-superficial-unit-10m.tif",
        "lab006:geology-superficial-broad-group-10m.tif": lab006 / "aligned" / "geology-superficial-broad-group-10m.tif",
    }
    source_hashes_before = {name: sha256_file(item) for name, item in source_products.items()}
    terrain=_terrain_aggregates(lab005a,grid)
    ndvi=_read(lab005c/"temporal"/"ndvi_surface_median_10m.tif"); ndvi_std=_read(lab005c/"temporal"/"ndvi_surface_standard_deviation_10m.tif"); ndmi=_upsample_20m(_read(lab005c/"temporal"/"ndmi_surface_median_20m.tif")); persistent=_read(lab005c/"temporal"/"persistent_low_ndvi_evidence_10m.tif",categorical=True)>0
    arrays={
        "slope":terrain["slope_mean"],"roughness":terrain["roughness15_mean"],"elevation":terrain["elevation_mean"],
        "habitat_source":_read(lab006/"aligned"/"habitat-source-category-10m.tif",categorical=True),"habitat_group":_read(lab006/"aligned"/"habitat-simplified-group-10m.tif",categorical=True),
        "bedrock_unit":_read(lab006/"aligned"/"geology-bedrock-unit-10m.tif",categorical=True),"bedrock_group":_read(lab006/"aligned"/"geology-bedrock-broad-group-10m.tif",categorical=True),
        "superficial_unit":_read(lab006/"aligned"/"geology-superficial-unit-10m.tif",categorical=True),"superficial_group":_read(lab006/"aligned"/"geology-superficial-broad-group-10m.tif",categorical=True),
    }
    habitat_lookup=_lookup(paths["habitat_lookup"]); geology_lookup=_lookup(paths["geology_lookup"])
    habitat_groups={int(key):value for key,value in habitat_lookup["simplified_groups"].items()}; superficial_groups={int(key):value for key,value in geology_lookup["superficial"]["broad_groups"].items()}
    terrain_pref,terrain_available=terrain_preferences(arrays["slope"],arrays["roughness"],config["continuous_rules"]["terrain"])
    sentinel_pref,sentinel_available=sentinel_preferences(ndvi,ndvi_std,ndmi,persistent,config["continuous_rules"]["sentinel"])
    habitat_pref,habitat_available=categorical_preferences(arrays["habitat_group"],habitat_groups,config["habitat_preferences"])
    geology_pref,geology_available,superficial_mapped=geology_preferences(arrays["superficial_group"],superficial_groups,arrays["bedrock_group"],config["geology_superficial_preferences"])
    preferences={"terrain":terrain_pref,"sentinel":sentinel_pref,"habitat":habitat_pref,"geology":geology_pref}; availability={"terrain":terrain_available,"sentinel":sentinel_available,"habitat":habitat_available,"geology":geology_available}
    baseline=[config["baseline_support"][name] for name in CLASSES]
    fused=fuse_sources(preferences,availability,config["source_budgets"],baseline,config["missing_source_unknown_support"],config["conflict_unknown_support"],terrain_available)
    probabilities=fused["probabilities"]
    for index,name in enumerate(CLASSES): _write_float(rasters/f"probability-{name}-10m.tif",probabilities[...,index],grid)
    _write_float(rasters/"uncertainty-normalized-entropy-10m.tif",fused["uncertainty"],grid); _write_float(rasters/"source-conflict-js-10m.tif",fused["conflict"],grid); _write_byte(rasters/"dominant-surface-class-10m.tif",fused["dominant"],grid)
    coverage,evidence_count=_coverage(availability,superficial_mapped,terrain_available,probabilities,fused["uncertainty"]); _write_byte(rasters/"evidence-family-count-10m.tif",evidence_count,grid)
    for source,values in fused["contributions"].items():
        for index,name in enumerate(CLASSES): _write_float(contributions_root/f"{source}-{name}-support-10m.tif",values[...,index],grid)
    point=config["canonical_point"]; row=int((north-point["northing"])/grid.resolution_m); column=int((point["easting"]-west)/grid.resolution_m)
    context=_context_at(row,column,arrays,habitat_lookup,geology_lookup)
    lab005c_report=json.loads(paths["lab005c_report"].read_text(encoding="utf-8"))
    lab006_report_data=json.loads(paths["lab006_report"].read_text(encoding="utf-8"))
    observation_context=[{"season":season,"product_id":value["metadata"]["official_product_id"],"acquisition_time_utc":value["metadata"]["official_acquisition_time_utc"],"selection_rationale":value["metadata"]["selection_rationale"]} for season,value in sorted(lab005c_report["observations"].items())]
    trace={
        "coordinate":point,"grid":{"row":row,"column":column,"cell_size_m":10,"information_resolution_warning":"Alignment cell size is not uniform source resolution."},"context":context,
        "evidence":{
            "terrain":{"temporal_class":"structural_quasi_static","elevation_m_odn":float(arrays["elevation"][row,column]),"slope_degrees":float(arrays["slope"][row,column]),"roughness_15m_rms_m":float(arrays["roughness"][row,column])},
            "sentinel":{"temporal_class":"dated_dynamic_observational","ndvi_temporal_median":float(ndvi[row,column]),"ndvi_temporal_stddev":float(ndvi_std[row,column]),"ndmi_temporal_median_20m":float(ndmi[row,column]),"persistent_low_ndvi_diagnostic":bool(persistent[row,column]),"observations":observation_context},
            "habitat":{"temporal_class":"historical_contextual","available":bool(habitat_available[row,column])},"geology":{"temporal_class":"structural_quasi_static_context","available":bool(geology_available[row,column]),"superficial_deposit_mapped":bool(superficial_mapped[row,column])},
        },
        "source_support":{source:{name:float(values[row,column,index]) for index,name in enumerate(CLASSES)} for source,values in fused["contributions"].items()},
        "conflict":float(fused["conflict"][row,column]),"surface":{"scores":{name:float(fused["scores"][row,column,index]) for index,name in enumerate(CLASSES)},"probabilities":{name:float(probabilities[row,column,index]) for index,name in enumerate(CLASSES)},"dominant":CLASSES[int(fused["dominant"][row,column])-1],"uncertainty":float(fused["uncertainty"][row,column])},
    }
    _write_json(output/"canonical-tryfan-evidence-trace.json",trace)
    diagnostics=_save_diagnostics(output,probabilities,fused["dominant"],fused["uncertainty"],fused["conflict"],fused["contributions"],evidence_count,arrays,trace)
    valid=terrain_available
    class_stats={name:numeric_summary(probabilities[...,index],"probability") for index,name in enumerate(CLASSES)}
    probability_sums=np.sum(probabilities,axis=-1)
    probability_validation={
        "minimum_probability":float(np.nanmin(probabilities)),
        "maximum_probability":float(np.nanmax(probabilities)),
        "minimum_sum":float(np.nanmin(probability_sums[valid])),
        "maximum_sum":float(np.nanmax(probability_sums[valid])),
        "maximum_absolute_sum_error":float(np.nanmax(np.abs(probability_sums[valid]-1.0))),
        "out_of_range_cells":int(np.count_nonzero(valid & np.any((probabilities<0)|(probabilities>1),axis=-1))),
        "non_finite_model_cells":int(np.count_nonzero(valid & ~np.all(np.isfinite(probabilities),axis=-1))),
    }
    dominant_summary={name:{"cells":int(np.count_nonzero(fused["dominant"]==index+1)),"fraction_of_valid_model":float(np.count_nonzero(fused["dominant"]==index+1)/valid.sum())} for index,name in enumerate(CLASSES)}
    conflict_threshold=float(np.nanpercentile(fused["conflict"][valid],75)); high_conflict=valid&(fused["conflict"]>=conflict_threshold); low_conflict=valid&(fused["conflict"]<=np.nanpercentile(fused["conflict"][valid],25))
    quantitative={
        "probability_validation":probability_validation,"probability_statistics":class_stats,"uncertainty":numeric_summary(fused["uncertainty"],"normalized_entropy_0_to_1"),"dominant_class":dominant_summary,"coverage":coverage,
        "slope_bins":_binned(arrays["slope"],[0,10,20,30,40,60,float("inf")],probabilities,fused["uncertainty"]),"roughness_bins":_binned(arrays["roughness"],[0,.15,.3,.6,1.2,float("inf")],probabilities,fused["uncertainty"]),
        "by_habitat_group":_group_summary(arrays["habitat_group"],habitat_groups,probabilities,fused["uncertainty"]),"by_superficial_group":_group_summary(arrays["superficial_group"],{0:"valid_none_mapped",**superficial_groups},probabilities,fused["uncertainty"]),
        "conflict":{
            "p75_threshold":conflict_threshold,"high_conflict_fraction":float(np.mean(high_conflict)),"mean_uncertainty_high_conflict":float(np.nanmean(fused["uncertainty"][high_conflict])),"mean_other_unknown_high_conflict":float(np.nanmean(probabilities[...,5][high_conflict])),
            "mean_uncertainty_low_conflict":float(np.nanmean(fused["uncertainty"][low_conflict])),"mean_other_unknown_low_conflict":float(np.nanmean(probabilities[...,5][low_conflict])),
        },
    }
    lab005a_convention=Path(config["frozen_inputs"]["lab005a_report"]["path"]).parent
    lab006_convention=Path(config["frozen_inputs"]["lab006_report"]["path"]).parent
    package={
        "schema_version":1,
        "model_version":config["model_version"],
        "ontology":{"classes":list(CLASSES),"scope":"Tryfan broad underlying surface character; not a global ontology or temporal surface state"},
        "aoi":config["aoi"],
        "probability_rasters":{name:str((rasters/f"probability-{name}-10m.tif").relative_to(output)) for name in CLASSES},
        "dominant_raster":str((rasters/"dominant-surface-class-10m.tif").relative_to(output)),
        "uncertainty_raster":str((rasters/"uncertainty-normalized-entropy-10m.tif").relative_to(output)),
        "context":{
            "habitat":{
                "source_category_raster":str(lab006_convention/"aligned"/"habitat-source-category-10m.tif"),
                "group_raster":str(lab006_convention/"aligned"/"habitat-simplified-group-10m.tif"),
                "lookup":config["frozen_inputs"]["habitat_lookup"]["path"],
                "source_report":config["frozen_inputs"]["lab006_report"]["path"],
                "provenance":{key:lab006_report_data["sources"]["habitat"][key] for key in ("provider","product","licence","publication_date","survey_period","effective_scale","crs")},
                "temporal_class":"historical_contextual",
                "survey_period":"1979-1997",
            },
            "geology":{
                "bedrock_unit_raster":str(lab006_convention/"aligned"/"geology-bedrock-unit-10m.tif"),
                "superficial_unit_raster":str(lab006_convention/"aligned"/"geology-superficial-unit-10m.tif"),
                "lookup":config["frozen_inputs"]["geology_lookup"]["path"],
                "source_report":config["frozen_inputs"]["lab006_report"]["path"],
                "provenance":{key:lab006_report_data["sources"]["geology"][key] for key in ("provider","product","licence","nominal_scale","service_data_release","access_constraint")},
                "temporal_class":"structural_quasi_static_context",
                "nominal_scale":"1:50,000",
            },
            "sentinel":{"source_report":config["frozen_inputs"]["lab005c_report"]["path"],"temporal_class":"dated_dynamic_observational","observations":observation_context},
            "terrain":{"temporal_class":"structural_quasi_static","source_report":str(lab005a_convention/"lab005a-surface-analysis.json")},
        },
        "semantic_invariants":config["semantic_invariants"],
        "canonical_trace":"canonical-tryfan-evidence-trace.json",
    }
    _write_json(output/"lab007-surface-model-package.json",package)
    hashes_after={name:sha256_file(path) for name,path in paths.items()}
    if hashes_before != hashes_after: raise RuntimeError("A frozen upstream input changed during Lab 007")
    source_hashes_after={name:sha256_file(item) for name,item in source_products.items()}
    if source_hashes_before != source_hashes_after:
        raise RuntimeError("A frozen upstream data product changed during Lab 007")
    generated=sorted(path for path in output.rglob("*") if path.is_file() and path.name!="lab007-report.json")
    report={"experiment":config["experiment"],"model_version":config["model_version"],"configuration_sha256":sha256_file(config_path),"frozen_inputs":config["frozen_inputs"],"frozen_hashes_before_and_after":{"before":hashes_before,"after":hashes_after,"unchanged":True},"frozen_source_products":{"hashes":source_hashes_before,"unchanged_during_run":source_hashes_before==source_hashes_after},"temporal_semantics":{"terrain":"structural/quasi-static derived morphology","geology":"structural/quasi-static broad context","habitat":"historical contextual survey (1979-1997)","sentinel":"dated dynamic observations; dates retained in package/trace; not inferred as permanent state"},"method":{"type":"bounded additive evidence support; no ML","classes":list(CLASSES),"source_budgets":config["source_budgets"],"baseline_support":config["baseline_support"],"continuous_rules":config["continuous_rules"],"normalization":"non-negative class scores divided by their cell sum","uncertainty":"Shannon entropy divided by ln(6)","other_unknown":"positive prior plus missing-source and source-conflict support; never arithmetic remainder","conflict":"specificity-weighted mean pairwise Jensen-Shannon divergence"},"semantic_invariants":config["semantic_invariants"],"quantitative_diagnostics":quantitative,"canonical_tryfan_trace":trace,"diagnostics":[str(path.relative_to(output)) for path in diagnostics],"limitations":["The 10 m grid is computational alignment, not common source information resolution.","No output identifies individual rocks, fractures, vegetation objects, material textures, seasonal state or square-metre truth.","Historical habitat and dated Sentinel evidence retain their temporal context.","Probabilities are explicit assumptions constrained by available evidence, not calibrated classification accuracy."],"outputs":[{"path":str(path.relative_to(output)),"bytes":path.stat().st_size,"sha256":sha256_file(path)} for path in generated],"storage_bytes":sum(path.stat().st_size for path in generated)}
    payload={key:value for key,value in report.items() if key!="deterministic_result_sha256"}; report["deterministic_result_sha256"]=stable_json_sha256(payload); _write_json(output/"lab007-report.json",report)
    print(json.dumps({"report":str(output/"lab007-report.json"),"deterministic_result_sha256":report["deterministic_result_sha256"],"storage_bytes":report["storage_bytes"],"valid_model_cells":int(valid.sum()),"diagnostics":len(diagnostics)},indent=2))
    return report


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--config",type=Path,default=ROOT/"docs"/"earth-lab"/"tryfan-007-underlying-surface.json"); arguments=parser.parse_args(); run(arguments.config.resolve()); return 0


if __name__=="__main__": raise SystemExit(main())
