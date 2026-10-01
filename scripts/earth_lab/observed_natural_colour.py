"""Lab 010: local, observed RGB only; no acquisition or reconstruction."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import ColorInterp
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject, transform_bounds

import experiment_paths  # Establish the existing scripts import path.
from meridian_paths import resolve_storage_roots


BOUNDS = (264900, 357800, 267900, 360800)
BANDS = ("B04", "B03", "B02")
WARNING = (
    "Sentinel-2 natural colour has 10 m native spatial resolution. Any finer "
    "raster representation used by the renderer is interpolation and does not "
    "constitute additional observed spatial detail."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_rgb(reflectance: np.ndarray) -> np.ndarray:
    if not np.isfinite(reflectance).all():
        raise ValueError("Unexpected nodata; do not conceal gaps in the observation")
    return np.rint(np.clip((reflectance - 0.02) / 0.28, 0, 1) * 255).astype(np.uint8)


def world_uv(easting: float, northing: float) -> tuple[float, float]:
    """Existing Landscape is +X east, +Y south; raster row zero is north."""
    return ((easting - BOUNDS[0]) / 3000, (BOUNDS[3] - northing) / 3000)


def build(repository: Path) -> dict:
    root = resolve_storage_roots(repository_root=repository, require_data=True).data
    estate = root / "experiments/earth-lab"
    b = estate / "tryfan-005b/sentinel2-surface-evidence"
    c = estate / "tryfan-005c/sentinel2-temporal-evidence"
    b_report = json.loads((b / "lab005b-report.json").read_text())
    c_report = json.loads((c / "lab005c-report.json").read_text())
    config = json.loads((repository / "docs/earth-lab/tryfan-005c-temporal-evidence.json").read_text())
    catalogue = json.loads((repository / "docs/atlas/tryfan-data-catalog.json").read_text())
    if tuple(catalogue["geographic_area"]["extent_bng"]) != BOUNDS:
        raise ValueError("Canonical Tryfan extent changed")
    audit = []
    for observation in config["observations"]:
        season = observation["season"]
        folder = b / "source-native" if season == "summer" else c / "observations" / season / "source-native"
        files = []
        for name, band in config["bands"].items():
            native_m = band["native_resolution_m"]
            path = folder / f"{band['code']}_{native_m}m-native-window.tif"
            expected = next(x["sha256"] for x in c_report["input_files"] if x["season"] == season and x["band"] == name)
            actual = sha256(path)
            if actual != expected:
                raise ValueError(f"Frozen {season} {name} source hash mismatch")
            with rasterio.open(path) as src:
                if str(src.crs) != "EPSG:32630" or abs(src.transform.a) != native_m or abs(src.transform.e) != native_m:
                    raise ValueError("Unexpected native CRS/resolution")
                files.append({"band": band["code"], "native_resolution_m": native_m,
                              "path": "${MERIDIAN_DATA_ROOT}/" + path.relative_to(root).as_posix(),
                              "sha256": actual, "source_url": src.tags()["MERIDIAN_SOURCE_URL"],
                              "dimensions": [src.width, src.height], "bounds": list(src.bounds),
                              "transform": list(src.transform)[:6]})
        audit.append({**observation, "processing_level": "Level-2A bottom-of-atmosphere surface reflectance",
                      "source_crs": "EPSG:32630", "actual_aoi_scl": c_report["observations"][season]["actual_aoi_scl"],
                      "retained_files": files})
    observation = next(x for x in audit if x["season"] == "summer")
    if observation["official_product_id"] != b_report["observation"]["official_product_id"]:
        raise ValueError("Lab 005B/005C observation identity mismatch")
    output = estate / "tryfan-010/observed-natural-colour-v1"
    output.mkdir(parents=True, exist_ok=True)
    transform = from_bounds(*BOUNDS, 300, 300)
    channels = []
    for code in BANDS:
        path = b / "source-native" / f"{code}_10m-native-window.tif"
        with rasterio.open(path) as src:
            needed = transform_bounds("EPSG:27700", src.crs, *BOUNDS, densify_pts=21)
            if not (src.bounds.left <= needed[0] and src.bounds.bottom <= needed[1]
                    and src.bounds.right >= needed[2] and src.bounds.top >= needed[3]):
                raise ValueError("Retained native window does not cover the AOI")
            dn = src.read(1)
            values = dn.astype(np.float32) * np.float32(0.0001) - np.float32(0.1)
            values[dn == src.nodata] = np.nan
            destination = np.full((300, 300), np.nan, dtype=np.float32)
            reproject(values, destination, src_transform=src.transform, src_crs=src.crs,
                      src_nodata=np.nan, dst_transform=transform, dst_crs="EPSG:27700",
                      dst_nodata=np.nan, resampling=Resampling.bilinear, num_threads=1)
            channels.append(destination)
    reflectance = np.stack(channels)
    rgb = display_rgb(reflectance)
    outputs = []
    for name, array in [("lab010-rgb-reflectance-10m.tif", reflectance), ("lab010-natural-colour-10m.tif", rgb)]:
        path = output / name
        with rasterio.open(path, "w", driver="GTiff", width=300, height=300, count=3,
                           dtype=array.dtype, crs="EPSG:27700", transform=transform,
                           compress="deflate", nodata=-9999 if array.dtype == np.float32 else None) as dst:
            dst.write(array)
            dst.colorinterp = (ColorInterp.red, ColorInterp.green, ColorInterp.blue)
            dst.update_tags(MERIDIAN_LAB="010", MERIDIAN_NATIVE_RESOLUTION_M="10",
                            MERIDIAN_OBSERVATION=observation["official_product_id"])
        with rasterio.open(path) as check:
            assert check.crs.to_epsg() == 27700 and tuple(check.bounds) == BOUNDS
            assert check.shape == (300, 300) and check.transform == transform
            np.testing.assert_array_equal(check.read(), array)
        outputs.append({"path": name, "sha256": sha256(path), "bytes": path.stat().st_size})
    png = output / "lab010-natural-colour-10m.png"
    Image.fromarray(np.moveaxis(rgb, 0, -1)).save(png)
    np.testing.assert_array_equal(np.array(Image.open(png)), np.moveaxis(rgb, 0, -1))
    outputs.append({"path": png.name, "sha256": sha256(png), "bytes": png.stat().st_size})
    manifest = {
        "schema_version": 1, "experiment": "LAB 010 — OBSERVED NATURAL-COLOUR SURFACE",
        "research_question": "What does measured Tryfan terrain look like surfaced with observed Sentinel natural colour?",
        "warning": WARNING, "season_audit": audit, "selected_season": "summer",
        "selected_observation": b_report["observation"],
        "selection_rationale": "Summer has zero AOI cloud/cloud-shadow/snow/nodata and 58.06-degree sun; spring has 0.33% cloud and 6% topographic shadow, winter 25.28% snow/59.20% shadow, autumn 1.53% cloud/62.35% shadow. Summer still has 1.84% SCL topographic shadow, which is retained, not corrected. No seasonal composite.",
        "licence": {**config["licence"], "attribution": "Contains modified Copernicus Sentinel data 2026."},
        "source_report_hashes": {"lab005b": sha256(b / "lab005b-report.json"), "lab005c": sha256(c / "lab005c-report.json")},
        "aoi": {"crs": "EPSG:27700", "bounds": list(BOUNDS), "dimensions": [300, 300],
                "pixel_size_m": [10, 10], "transform": list(transform)[:6], "row_zero": "north", "column_zero": "west"},
        "processing": {"bands_in_rgb_order": list(BANDS), "source_crs": "EPSG:32630",
                       "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                                   "rasterio": rasterio.__version__, "gdal": rasterio.__gdal_version__},
                       "source_native_pixel_size_m": 10, "destination_pixel_size_m": 10,
                       "reflectance": "DN * 0.0001 - 0.1; source DN 0 is nodata; negative valid reflectance retained",
                       "resampling": "bilinear, one GDAL thread, no sharpening or local enhancement",
                       "display": "uint8 round(255 * clip((reflectance - 0.02) / 0.28, 0, 1)); gamma 1; fixed Lab 005C common RGB stretch",
                       "nodata_cells": int(np.count_nonzero(~np.isfinite(reflectance).all(axis=0))),
                       "renderer_adapter": "same 300×300 PNG, no finer resampling; sRGB display bytes, bilinear texture filtering"},
        "products": outputs, "deterministic_product_identity": hashlib.sha256(json.dumps(outputs, sort_keys=True).encode()).hexdigest(),
        "semantics": {"observed": "Native Sentinel reflectance and unchanged measured terrain",
                      "derived": "Crop, reprojection, fixed display transformation",
                      "rendered": "Unreal base colour, fixed roughness/specular; no reconstructed detail"},
        "visual_acceptance": "pending_manual_fixed_camera_comparison"
    }
    # Retained observation metadata contains URLs, not source-window machine-local paths.
    (output / "lab010-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    result = build(args.repository)
    print(json.dumps({"identity": result["deterministic_product_identity"], "products": result["products"]}, indent=2))
