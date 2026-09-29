"""Build Lab 006 independent habitat and geological evidence for a bounded AOI."""
from __future__ import annotations

import argparse
from collections import Counter
import io
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from PIL import Image
import rasterio
from rasterio.features import rasterize

ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_surface_evidence import _terrain_aggregates
from experiment_paths import resolve_repository_value
from contextual_evidence import (
    binary_overlap,
    categorical_summary,
    category_numeric_summary,
    habitat_group,
    mode_reduce_2x2,
    nearest_palette_indices,
    clip_geometry_to_bounds,
)
from surface_evidence import AnalysisGrid, sha256_file, stable_json_sha256


def _path(value: str) -> Path:
    return resolve_repository_value(ROOT, value)


def _get(url: str, parameters: dict[str, Any] | None = None) -> bytes:
    full = url if not parameters else f"{url}?{urlencode(parameters)}"
    request = Request(full, headers={"User-Agent": "Project-Meridian-Earth-Lab/006"})
    with urlopen(request, timeout=120) as response:
        return response.read()


def _cached(path: Path, url: str, parameters: dict[str, Any] | None = None) -> bytes:
    if path.exists():
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _get(url, parameters)
    path.write_bytes(payload)
    return payload


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_category(path: Path, values: np.ndarray, grid: AnalysisGrid) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path, "w", driver="GTiff", width=grid.width, height=grid.height, count=1,
        dtype=str(values.dtype), crs=grid.crs, transform=grid.transform, nodata=0,
        compress="deflate", predictor=1,
    ) as target:
        target.write(values, 1)


def _read(path: Path) -> np.ndarray:
    with rasterio.open(path) as source:
        return source.read(1)


def _grid(config: dict[str, Any], resolution: float) -> AnalysisGrid:
    west, south, east, north = config["aoi"]["bounds"]
    return AnalysisGrid(config["aoi"]["crs"], west, south, east, north, resolution)


def _verify_frozen(config: dict[str, Any]) -> tuple[Path, Path]:
    paths = []
    for key in ("lab005a_report", "lab005c_report"):
        item = config["frozen_inputs"][key]
        path = _path(item["path"])
        observed = sha256_file(path)
        if observed.lower() != item["sha256"].lower():
            raise RuntimeError(f"Frozen input changed: {path} ({observed})")
        paths.append(path)
    return paths[0].parent, paths[1].parent


def _habitat(config: dict[str, Any], source: Path, aligned: Path, grids: dict[int, AnalysisGrid]) -> dict[str, Any]:
    settings = config["habitat"]
    _cached(source / "wfs-capabilities.xml", settings["capabilities_url"])
    west, south, east, north = config["aoi"]["bounds"]
    request = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": settings["layer"], "srsName": config["aoi"]["crs"],
        "bbox": f"{west},{south},{east},{north},urn:ogc:def:crs:EPSG::27700",
        "outputFormat": "application/json",
    }
    payload = _cached(source / "nrw-phase1-aoi.geojson", settings["service_url"], request)
    collection = json.loads(payload)
    source_features = [feature for feature in collection.get("features", []) if feature.get("geometry")]
    features = []
    for feature in source_features:
        geometry = clip_geometry_to_bounds(feature["geometry"], (west, south, east, north))
        if geometry:
            features.append({**feature, "geometry": geometry})
    clipped_collection = {"type": "FeatureCollection", "name": "nrw_phase1_tryfan_lab006_clipped", "features": features}
    _write_json(source / "nrw-phase1-aoi-clipped.geojson", clipped_collection)
    source_keys = []
    broad_groups = []
    for feature in features:
        properties = feature.get("properties") or {}
        code = str(properties.get("phase1_code") or "NA")
        label = str(properties.get("label") or code)
        key = label if "mosaic" in label.lower() else code
        source_keys.append(key)
        broad_groups.append(habitat_group(code, label, settings["simplified_groups"]))
    source_names = sorted(set(source_keys))
    group_names = sorted(set(broad_groups))
    source_ids = {name: index + 1 for index, name in enumerate(source_names)}
    group_ids = {name: index + 1 for index, name in enumerate(group_names)}
    shapes_source = [(feature["geometry"], source_ids[key]) for feature, key in zip(features, source_keys)]
    shapes_group = [(feature["geometry"], group_ids[key]) for feature, key in zip(features, broad_groups)]
    outputs: dict[int, dict[str, np.ndarray]] = {}
    for resolution, grid in grids.items():
        original = rasterize(shapes_source, out_shape=(grid.height, grid.width), transform=grid.transform, fill=0, all_touched=False, dtype="uint16")
        simplified = rasterize(shapes_group, out_shape=(grid.height, grid.width), transform=grid.transform, fill=0, all_touched=False, dtype="uint8")
        _write_category(aligned / f"habitat-source-category-{resolution}m.tif", original, grid)
        _write_category(aligned / f"habitat-simplified-group-{resolution}m.tif", simplified, grid)
        outputs[resolution] = {"source": original, "group": simplified}
    code_names = settings.get("code_names", {})
    display_names = {identifier: (f"{name} — {code_names[name]}" if name in code_names else name) for name, identifier in source_ids.items()}
    lookup = {
        "source_categories": {str(identifier): display_names[identifier] for identifier in sorted(display_names)},
        "simplified_groups": {str(identifier): name for name, identifier in group_ids.items()},
        "warning": "Aligned cell size is not source positional accuracy; category identifiers were rasterized without interpolation.",
    }
    _write_json(aligned / "habitat-category-lookup.json", lookup)
    return {
        "source_intersecting_feature_count": len(source_features),
        "feature_count": len(features),
        "observed_survey_values": sorted({str((f.get("properties") or {}).get("survey")) for f in features}),
        "lookup": lookup,
        "arrays": outputs,
        "summary_10m_source": categorical_summary(outputs[10]["source"], display_names, 100.0),
        "summary_10m_simplified": categorical_summary(outputs[10]["group"], {v: k for k, v in group_ids.items()}, 100.0),
    }


def _wms_map(config: dict[str, Any], layer: str, path: Path, grid: AnalysisGrid) -> np.ndarray:
    west, south, east, north = config["aoi"]["bounds"]
    payload = _cached(path, config["geology"]["service_url"], {
        "service": "WMS", "version": "1.3.0", "request": "GetMap", "layers": layer,
        "styles": "", "crs": "EPSG:27700", "bbox": f"{west},{south},{east},{north}",
        "width": grid.width, "height": grid.height, "format": "image/png", "transparent": "TRUE",
    })
    return np.asarray(Image.open(io.BytesIO(payload)).convert("RGBA"))


def _feature_info(config: dict[str, Any], layer: str, row: int, column: int, grid: AnalysisGrid) -> list[dict[str, Any]]:
    west, south, east, north = config["aoi"]["bounds"]
    payload = _get(config["geology"]["service_url"], {
        "service": "WMS", "version": "1.3.0", "request": "GetFeatureInfo", "layers": layer,
        "query_layers": layer, "styles": "", "crs": "EPSG:27700", "bbox": f"{west},{south},{east},{north}",
        "width": grid.width, "height": grid.height, "format": "image/png", "info_format": "application/geo+json",
        "i": column, "j": row, "feature_count": 10,
    })
    return json.loads(payload).get("features", [])


def _feature_rgb(properties: dict[str, Any]) -> list[int] | None:
    keys = [("BGSRED", "BGSGREEN", "BGSBLUE"), ("bgsred", "bgsgreen", "bgsblue")]
    for red, green, blue in keys:
        if all(key in properties and properties[key] is not None for key in (red, green, blue)):
            return [int(properties[red]), int(properties[green]), int(properties[blue])]
    return None


def _unit_name(properties: dict[str, Any]) -> str:
    for key in ("LEX_RCS_D", "LEX_D", "RCS_D", "LEX_RCS_I", "LEX", "UNIT_NAME"):
        if properties.get(key):
            return str(properties[key])
    return "unnamed_geological_unit"


def _recover_palette(config: dict[str, Any], layer_key: str, rgba: np.ndarray, cache: Path, grid: AnalysisGrid) -> list[dict[str, Any]]:
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))["units"]
    layer = config["geology"]["layers"][layer_key]
    opaque = rgba[..., 3] > 0
    colours, counts = np.unique(rgba[opaque, :3].reshape(-1, 3), axis=0, return_counts=True) if np.any(opaque) else (np.empty((0, 3), dtype=np.uint8), np.empty(0, dtype=int))
    order = np.argsort(counts)[::-1]
    recovered: dict[tuple[int, int, int], dict[str, Any]] = {}
    minimum = int(config["geology"]["palette_minimum_pixels"])
    for index in order:
        colour = colours[index]
        if counts[index] < minimum:
            break
        positions = np.argwhere(opaque & np.all(rgba[..., :3] == colour, axis=2))
        row, column = (int(value) for value in positions[len(positions) // 2])
        try:
            features = _feature_info(config, layer, row, column, grid)
        except Exception:
            continue
        best = None
        best_distance = float("inf")
        for feature in features:
            properties = feature.get("properties") or {}
            feature_colour = _feature_rgb(properties)
            if feature_colour is None:
                continue
            distance = float(np.linalg.norm(colour.astype(float) - np.asarray(feature_colour, dtype=float)))
            if distance < best_distance:
                best, best_distance = properties, distance
        if best is None or best_distance > 35:
            continue
        rgb = tuple(_feature_rgb(best) or colour.tolist())
        if rgb not in recovered:
            keep = {key: value for key, value in best.items() if key.upper() in {"LEX_RCS_D", "LEX_RCS_I", "LEX_D", "RCS_D", "RCS_X", "RCS_ORIGIN", "TYPE_D", "MAX_AGE", "MIN_AGE", "NOM_SCALE", "NOM_BGS_YR", "VERSION", "RELEASED", "MAP_SRC", "MAP_WEB", "SOURCE", "BGSRED", "BGSGREEN", "BGSBLUE"}}
            recovered[rgb] = {"name": _unit_name(best), "rgb": list(rgb), "properties": keep, "sample_pixel": [column, row]}
    units = []
    for identifier, item in enumerate(sorted(recovered.values(), key=lambda value: (value["name"], value["rgb"])), 1):
        units.append({"id": identifier, **item})
    _write_json(cache, {"layer": layer, "units": units})
    return units


def _substrate_group(name: str, layer_key: str) -> str:
    text = name.lower()
    if layer_key == "superficial":
        if "talus" in text: return "talus_angular_rock_fragments"
        if "peat" in text: return "peat"
        if "till" in text: return "glacial_till"
        if "alluv" in text: return "alluvial_sediment"
        if "hummock" in text: return "hummocky_glacial_deposit"
        if "head" in text: return "slope_deposit_head"
        return "other_superficial_deposit"
    if any(term in text for term in ("rhyolite", "microgranite", "felsic tuff", "pyroclastic")): return "felsic_igneous_or_volcaniclastic"
    if "sandstone" in text: return "sandstone_dominant"
    if any(term in text for term in ("mudstone", "siltstone")): return "fine_grained_sedimentary"
    return "other_bedrock"


def _fill_opaque_cartography(categories: np.ndarray, opaque: np.ndarray) -> tuple[np.ndarray, int]:
    """Resolve WMS label/boundary pixels spatially without filling true transparency."""
    result = np.asarray(categories).copy()
    missing = np.asarray(opaque, dtype=bool) & (result == 0)
    if not np.any(missing) or not np.any(result > 0):
        return result, 0
    count = int(np.count_nonzero(missing))
    remaining = missing.copy()
    while np.any(remaining):
        changed = np.zeros(remaining.shape, dtype=bool)
        for row_shift, column_shift in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted = np.roll(result, (row_shift, column_shift), axis=(0, 1))
            candidate = remaining & (shifted > 0)
            if row_shift == -1: candidate[-1, :] = False
            if row_shift == 1: candidate[0, :] = False
            if column_shift == -1: candidate[:, -1] = False
            if column_shift == 1: candidate[:, 0] = False
            result[candidate] = shifted[candidate]
            changed |= candidate
        remaining &= ~changed
        if not np.any(changed):
            break
    return result, count - int(np.count_nonzero(remaining))


def _geology(config: dict[str, Any], source: Path, aligned: Path, grids: dict[int, AnalysisGrid]) -> dict[str, Any]:
    _cached(source / "wms-capabilities.xml", config["geology"]["service_url"], {"service": "WMS", "request": "GetCapabilities", "version": "1.3.0"})
    result: dict[str, Any] = {"layers": {}}
    for layer_key, layer in config["geology"]["layers"].items():
        rgba = _wms_map(config, layer, source / f"{layer_key}-aoi-10m.png", grids[10])
        palette = _recover_palette(config, layer_key, rgba, source / f"{layer_key}-units.json", grids[10])
        raw10 = nearest_palette_indices(rgba, palette, float(config["geology"]["palette_tolerance_rgb"]))
        categories10, filled_cartographic_cells = _fill_opaque_cartography(raw10, rgba[..., 3] > 0)
        categories20 = mode_reduce_2x2(categories10)
        _write_category(aligned / f"geology-{layer_key}-unit-10m.tif", categories10, grids[10])
        _write_category(aligned / f"geology-{layer_key}-unit-20m.tif", categories20, grids[20])
        groups = sorted({_substrate_group(item["name"], layer_key) for item in palette})
        group_ids = {name: index + 1 for index, name in enumerate(groups)}
        unit_to_group = {item["id"]: group_ids[_substrate_group(item["name"], layer_key)] for item in palette}
        grouped10 = np.zeros_like(categories10, dtype=np.uint8)
        for unit_id, group_id in unit_to_group.items(): grouped10[categories10 == unit_id] = group_id
        grouped20 = mode_reduce_2x2(grouped10)
        _write_category(aligned / f"geology-{layer_key}-broad-group-10m.tif", grouped10, grids[10])
        _write_category(aligned / f"geology-{layer_key}-broad-group-20m.tif", grouped20, grids[20])
        lookup = {item["id"]: item["name"] for item in palette}
        lookup[0] = "no mapped deposit / transparent WMS" if layer_key == "superficial" else "unresolved"
        result["layers"][layer_key] = {
            "source_layer": layer, "palette": palette,
            "cartographic_cells_assigned_from_nearest_unit": filled_cartographic_cells,
            "raw_unresolved_opaque_fraction": float(np.mean((raw10 == 0) & (rgba[..., 3] > 0))),
            "summary_10m": categorical_summary(categories10, lookup, 100.0),
            "broad_groups": {str(identifier): name for name, identifier in group_ids.items()},
            "arrays": {"unit10": categories10, "unit20": categories20, "group10": grouped10, "group20": grouped20},
        }
    serializable = {key: {k: v for k, v in value.items() if k != "arrays"} for key, value in result["layers"].items()}
    _write_json(aligned / "geology-category-lookup.json", serializable)
    return result


def _legend_names(summary: dict[str, Any], maximum: int = 9) -> list[str]:
    return [f"{row['name']} ({row['fraction']:.1%})" for row in summary["categories"] if row["id"] != 0][:maximum]


def _diagnostics(images: Path, habitat: dict[str, Any], geology: dict[str, Any], terrain: dict[str, np.ndarray], sentinel: dict[str, np.ndarray]) -> list[Path]:
    images.mkdir(parents=True, exist_ok=True)
    paths = []
    habitat_group = habitat["arrays"][10]["group"]
    bedrock = geology["layers"]["bedrock"]["arrays"]["unit10"]
    superficial = geology["layers"]["superficial"]["arrays"]["unit10"]

    def save(name: str, figure):
        path = images / name
        figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        paths.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True)
    axes[0].imshow(habitat["arrays"][10]["source"], interpolation="nearest")
    axes[0].set_title("NRW Phase 1 source categories\n10 m aligned display; legacy survey boundaries")
    axes[1].imshow(habitat_group, interpolation="nearest")
    axes[1].set_title("Documented broad habitat grouping")
    for axis in axes: axis.set_axis_off()
    fig.text(0.5, 0.01, "North is up · AOI 3 × 3 km · aligned cell size is not source accuracy", ha="center")
    fig.text(0.01, -0.04, "Leading source categories: " + "; ".join(_legend_names(habitat["summary_10m_source"], 6)), fontsize=8)
    save("habitat-map.png", fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), constrained_layout=True)
    axes[0].imshow(bedrock, interpolation="nearest"); axes[0].set_title("BGS Geology 50K bedrock units")
    axes[1].imshow(superficial, interpolation="nearest"); axes[1].set_title("BGS Geology 50K superficial deposits\nblack = none/unresolved")
    for axis in axes: axis.set_axis_off()
    fig.text(0.5, 0.01, "North is up · nominal source scale 1:50,000 · WMS-derived categorical evidence", ha="center")
    fig.text(0.01, -0.04, "Bedrock: " + "; ".join(_legend_names(geology["layers"]["bedrock"]["summary_10m"], 5)), fontsize=7)
    fig.text(0.01, -0.075, "Superficial: " + "; ".join(_legend_names(geology["layers"]["superficial"]["summary_10m"], 5)), fontsize=7)
    save("geology-map.png", fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    axes[0].imshow(terrain["slope_mean"], cmap="magma", vmin=0, vmax=60); axes[0].set_title("Mean slope (degrees)")
    axes[1].imshow(habitat_group, interpolation="nearest"); axes[1].set_title("Broad habitat context")
    axes[2].imshow(terrain["roughness15_mean"], cmap="viridis"); axes[2].set_title("~15 m roughness (m RMS)")
    for axis in axes: axis.set_axis_off()
    save("habitat-vs-terrain.png", fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    axes[0].imshow(habitat_group, interpolation="nearest"); axes[0].set_title("Broad habitat context")
    axes[1].imshow(sentinel["persistent_low_ndvi"], cmap="gray", vmin=0, vmax=1); axes[1].set_title("005C persistent low-NDVI evidence")
    disagree = (habitat_group > 0).astype(np.int8) + sentinel["persistent_low_ndvi"].astype(np.int8) * 2
    axes[2].imshow(disagree, cmap=ListedColormap(["black", "#356859", "#d8a334", "#ef6c3e"]), vmin=0, vmax=3); axes[2].set_title("Spatial comparison\n(not ground-truth agreement)")
    for axis in axes: axis.set_axis_off()
    save("habitat-vs-lab005c.png", fig)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    axes[0].imshow(bedrock, interpolation="nearest"); axes[0].set_title("Bedrock unit")
    axes[1].imshow(superficial, interpolation="nearest"); axes[1].set_title("Superficial deposit")
    axes[2].imshow(terrain["elevation_mean"], cmap="terrain"); axes[2].contour(terrain["slope_mean"], levels=[20, 35, 50], colors="k", linewidths=.35); axes[2].set_title("Elevation + slope contours")
    for axis in axes: axis.set_axis_off()
    save("geology-vs-terrain.png", fig)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10), constrained_layout=True)
    panels = [(terrain["slope_mean"], "Slope", "magma"), (terrain["roughness15_mean"], "Roughness ~15 m", "viridis"), (habitat_group, "Habitat grouping", "tab20"), (bedrock, "Bedrock unit", "tab20"), (superficial, "Superficial deposit", "tab20"), (sentinel["persistent_low_ndvi"], "005C persistent low NDVI", "gray")]
    for axis, (values, title, cmap) in zip(axes.flat, panels): axis.imshow(values, cmap=cmap, interpolation="nearest"); axis.set_title(title); axis.set_axis_off()
    fig.suptitle("Lab 006 evidence overview — independent channels, not a fused classification")
    save("combined-evidence-overview.png", fig)
    return paths


def run(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = _path(config["output_root"])
    source = output / "source"
    aligned = output / "aligned"
    images = output / "images"
    lab005a, lab005c = _verify_frozen(config)
    grids = {10: _grid(config, 10.0), 20: _grid(config, 20.0)}
    habitat = _habitat(config, source / "nrw", aligned, grids)
    geology = _geology(config, source / "bgs", aligned, grids)
    terrain10 = _terrain_aggregates(lab005a, grids[10])
    sentinel = {
        "persistent_low_ndvi": _read(lab005c / "temporal" / "persistent_low_ndvi_evidence_10m.tif").astype(bool),
        "high_ndvi_variability": _read(lab005c / "temporal" / "high_ndvi_variability_10m.tif").astype(bool),
        "low_variability": _read(lab005c / "temporal" / "low_temporal_spectral_variability_10m.tif").astype(bool),
    }
    habitat_lookup = {int(key): value for key, value in habitat["lookup"]["simplified_groups"].items()}
    habitat_relationships = category_numeric_summary(habitat["arrays"][10]["group"], {
        "elevation_m_odn": terrain10["elevation_mean"], "slope_degrees": terrain10["slope_mean"],
        "roughness_15m_rms_m": terrain10["roughness15_mean"], "curvature_per_m": terrain10["curvature_mean"],
        "persistent_low_ndvi_fraction": sentinel["persistent_low_ndvi"].astype(float),
        "high_ndvi_variability_fraction": sentinel["high_ndvi_variability"].astype(float),
    }, habitat_lookup)
    geology_relationships = {}
    for layer_key, layer in geology["layers"].items():
        geology_relationships[layer_key] = category_numeric_summary(layer["arrays"]["unit10"], {
            "elevation_m_odn": terrain10["elevation_mean"], "slope_degrees": terrain10["slope_mean"],
            "roughness_15m_rms_m": terrain10["roughness15_mean"],
        }, {item["id"]: item["name"] for item in layer["palette"]})
    natural_ids = [int(key) for key, name in habitat_lookup.items() if name in {"natural_rock", "scree"}]
    rock_context = np.isin(habitat["arrays"][10]["group"], natural_ids)
    agreement = {
        "habitat_rock_or_scree_vs_005c_persistent_low_ndvi": binary_overlap(rock_context, sentinel["persistent_low_ndvi"]),
        "interpretation": "Overlap compares independent coarse habitat context with a Sentinel diagnostic. Neither channel is ground truth and disagreement is retained.",
    }
    image_paths = _diagnostics(images, habitat, geology, terrain10, sentinel)
    evidence_package = {
        "schema_version": 1, "aoi": config["aoi"],
        "channels": {
            "terrain": {"source": config["frozen_inputs"]["lab005a_report"], "resolution": "derived from ~0.992 m validated R16; aggregates available on 10 m and 20 m grids"},
            "sentinel": {"source": config["frozen_inputs"]["lab005c_report"], "resolution": "10 m and 20 m observed/derived evidence; referenced, not regenerated"},
            "habitat": {"source": config["habitat"], "aligned_products": [str(path.relative_to(output)) for path in sorted(aligned.glob("habitat-*.tif"))], "meaning": "original legacy Phase 1 categories plus documented broad grouping"},
            "geology": {"source": config["geology"], "aligned_products": [str(path.relative_to(output)) for path in sorted(aligned.glob("geology-*.tif"))], "meaning": "BGS 1:50,000 WMS categorical context; not detailed vector or visual texture"},
        },
        "rule": "Every channel retains source, scale and evidence type. Lab 007 must not interpret aligned grid cell size as observation resolution.",
    }
    _write_json(output / "lab006-evidence-package.json", evidence_package)
    serializable_geology = {key: {k: v for k, v in value.items() if k != "arrays"} for key, value in geology["layers"].items()}
    generated_files = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "lab006-report.json")
    report = {
        "experiment": config["experiment"], "configuration_sha256": sha256_file(config_path),
        "aoi": config["aoi"], "frozen_inputs": config["frozen_inputs"],
        "sources": {"habitat": config["habitat"], "geology": config["geology"]},
        "habitat": {k: v for k, v in habitat.items() if k != "arrays"},
        "geology": serializable_geology,
        "relationships": {"habitat_by_group": habitat_relationships, "geology_by_unit": geology_relationships, "cross_evidence": agreement},
        "research_judgement": {
            "habitat_addition": "Adds named field-mapped habitat context and legacy categorical boundaries that Sentinel spectra alone cannot identify, while remaining old/generalised evidence rather than present-day metre truth.",
            "geology_addition": "Adds independent 1:50,000 bedrock and superficial-deposit context that constrains broad substrate families but cannot specify exposed-rock texture, fractures or boulders.",
            "useful_scale": "Habitat is useful at mapped patch/landform scale with undocumented positional precision; geology at 1:50,000 broad-unit scale. 10 m/20 m rasters are alignment products only.",
            "lab007": "Sufficient to constrain a first explicitly uncertain surface interpretation when kept as independent channels alongside terrain and frozen Sentinel evidence.",
            "must_not_infer": ["square-metre material truth", "individual rocks or boulders", "visual texture or fracture geometry", "present habitat unchanged since the 1979-1997 survey", "geology exposure wherever bedrock is mapped"],
        },
        "outputs": [{"path": str(path.relative_to(output)), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in generated_files],
        "storage_bytes": sum(path.stat().st_size for path in generated_files),
    }
    deterministic_payload = {key: value for key, value in report.items() if key not in {"deterministic_result_sha256"}}
    report["deterministic_result_sha256"] = stable_json_sha256(deterministic_payload)
    _write_json(output / "lab006-report.json", report)
    print(json.dumps({"report": str(output / "lab006-report.json"), "deterministic_result_sha256": report["deterministic_result_sha256"], "storage_bytes": report["storage_bytes"], "images": [str(path) for path in image_paths]}, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "docs" / "earth-lab" / "tryfan-006-contextual-evidence.json")
    arguments = parser.parse_args()
    run(arguments.config.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
