from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_bounds
from rasterio.windows import Window, from_bounds as window_from_bounds


matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

CRS = "EPSG:27700"
HISTORIC_TYPENAME = "geonode:nrw_lidar_tile_catalogue_archive"
NATIONAL_TYPENAME = "geonode:welsh_government_lidar_tile_catalogue_2020_2023"
WFS_URL = "https://datamap.gov.wales/geoserver/ows"
NATIONAL_DTM_COG = (
    "https://dmwproductionblob.blob.core.windows.net/cogs/lidar/"
    "wales_dtm_32bit_cog.tif"
)
NATIONAL_DSM_COG = (
    "https://dmwproductionblob.blob.core.windows.net/cogs/lidar/"
    "wales_dsm_32bit_cog.tif"
)
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"


@dataclass(frozen=True, slots=True)
class Aoi:
    identifier: str
    name: str
    center_easting: float
    center_northing: float
    width_m: float
    height_m: float

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        half_width = self.width_m / 2
        half_height = self.height_m / 2
        return (
            self.center_easting - half_width,
            self.center_northing - half_height,
            self.center_easting + half_width,
            self.center_northing + half_height,
        )


def load_aoi(path: Path) -> Aoi:
    payload = json.loads(path.read_text(encoding="utf-8"))
    center = payload["center"]
    if center["crs"] != CRS:
        raise ValueError(f"AOI center must use {CRS}")
    aoi = Aoi(
        identifier=str(payload["id"]),
        name=str(payload["name"]),
        center_easting=float(center["easting"]),
        center_northing=float(center["northing"]),
        width_m=float(payload["width_m"]),
        height_m=float(payload["height_m"]),
    )
    if aoi.width_m <= 0 or aoi.height_m <= 0:
        raise ValueError("AOI dimensions must be positive")
    return aoi


def _wfs_url(type_name: str, aoi: Aoi) -> str:
    left, bottom, right, top = aoi.bounds
    query = urllib.parse.urlencode(
        {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": type_name,
            "outputFormat": "application/json",
            "srsName": CRS,
            "bbox": f"{left},{bottom},{right},{top},{CRS}",
        }
    )
    return f"{WFS_URL}?{query}"


def query_catalogue(type_name: str, aoi: Aoi) -> dict[str, Any]:
    request = urllib.request.Request(
        _wfs_url(type_name, aoi), headers={"User-Agent": "Meridian-Earth-Lab/1"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _clean_properties(feature: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in feature.get("properties", {}).items():
        result[key] = value.strip() if isinstance(value, str) else value
    return result


def normalized_catalogue_features(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [_clean_properties(feature) for feature in payload.get("features", [])]


def _parse_date(value: str) -> datetime:
    for pattern in ("%d-%m-%Y", "%d-%b-%Y", "%Y"):
        try:
            return datetime.strptime(value, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    # Seasonal historic labels such as "Feb---April-2007" still carry a year.
    for token in reversed(value.replace("_", "-").split("-")):
        if token.isdigit() and len(token) == 4:
            return datetime(int(token), 1, 1, tzinfo=timezone.utc)
    raise ValueError(f"Could not parse survey date: {value}")


def choose_source(
    historic: Iterable[dict[str, Any]], national: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for feature in historic:
        if feature.get("dtm_url"):
            candidates.append(
                {
                    "family": "nrw_historic",
                    "resolution_m": float(feature["resolution"]),
                    "survey_date": str(feature["date_flown"]),
                    "dtm_url": _https_url(str(feature["dtm_url"])),
                    "dsm_url": _https_url(str(feature["dsm_url"]))
                    if feature.get("dsm_url")
                    else None,
                }
            )
    for feature in national:
        if feature.get("dtm_link"):
            candidates.append(
                {
                    "family": "welsh_government_2020_2023",
                    "resolution_m": 1.0,
                    "survey_date": str(feature["date"]),
                    "dtm_url": NATIONAL_DTM_COG,
                    "dsm_url": NATIONAL_DSM_COG,
                }
            )
    if not candidates:
        raise RuntimeError("No DTM catalogue coverage intersects the AOI")
    candidates.sort(
        key=lambda item: (
            float(item["resolution_m"]),
            -_parse_date(str(item["survey_date"])).timestamp(),
        )
    )
    return candidates[0]


def _https_url(value: str) -> str:
    return value if value.startswith("https://") else f"https://{value}"


def _gdal_environment() -> dict[str, str]:
    return {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
        "GDAL_HTTP_MULTIRANGE": "YES",
        "CPL_VSIL_CURL_USE_HEAD": "YES",
        "CPL_VSIL_CURL_CACHE_SIZE": str(32 * 1024 * 1024),
    }


def output_profile(aoi: Aoi, nodata: float = -9999.0) -> dict[str, Any]:
    width = int(round(aoi.width_m))
    height = int(round(aoi.height_m))
    if not math.isclose(width, aoi.width_m) or not math.isclose(height, aoi.height_m):
        raise ValueError("The 1 m output grid requires whole-metre AOI dimensions")
    return {
        "driver": "GTiff",
        "width": width,
        "height": height,
        "count": 1,
        "dtype": "float32",
        "crs": CRS,
        "transform": from_bounds(*aoi.bounds, width, height),
        "nodata": nodata,
        "compress": "DEFLATE",
        "predictor": 3,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }


def extract_cog(url: str, aoi: Aoi, destination: Path) -> dict[str, Any]:
    profile = output_profile(aoi)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tif.partial")
    with rasterio.Env(**_gdal_environment()):
        with rasterio.open(url) as source:
            if str(source.crs) != CRS:
                raise ValueError(f"Unexpected source CRS: {source.crs}")
            if not math.isclose(abs(float(source.transform.a)), 1.0):
                raise ValueError(f"Unexpected source resolution: {source.transform.a}")
            window = window_from_bounds(*aoi.bounds, transform=source.transform)
            window = Window(
                round(window.col_off),
                round(window.row_off),
                round(window.width),
                round(window.height),
            )
            values = source.read(1, window=window, masked=True)
    encoded = values.filled(profile["nodata"]).astype(np.float32, copy=False)
    with rasterio.open(temporary, "w", **profile) as output:
        output.write(encoded, 1)
        output.update_tags(
            source_url=url,
            aoi_id=aoi.identifier,
            retrieval="bounded COG HTTP range window",
        )
    temporary.replace(destination)
    return raster_stats(destination)


def raster_stats(path: Path) -> dict[str, Any]:
    with rasterio.open(path) as source:
        values = source.read(1, masked=True)
        valid = values.compressed()
        if not valid.size:
            minimum = maximum = mean = None
        else:
            minimum = float(valid.min())
            maximum = float(valid.max())
            mean = float(valid.mean())
        return {
            "path": path.name,
            "bytes": path.stat().st_size,
            "driver": source.driver,
            "width": source.width,
            "height": source.height,
            "crs": str(source.crs),
            "pixel_size_m": [
                abs(float(source.transform.a)),
                abs(float(source.transform.e)),
            ],
            "dtype": source.dtypes[0],
            "nodata": source.nodata,
            "valid_cells": int(valid.size),
            "nodata_cells": int(values.size - valid.size),
            "minimum_m": minimum,
            "maximum_m": maximum,
            "mean_m": mean,
        }


def compare_surfaces(dtm_path: Path, dsm_path: Path) -> dict[str, Any]:
    with rasterio.open(dtm_path) as dtm_source, rasterio.open(dsm_path) as dsm_source:
        dtm = dtm_source.read(1, masked=True)
        dsm = dsm_source.read(1, masked=True)
    combined_mask = np.ma.getmaskarray(dtm) | np.ma.getmaskarray(dsm)
    difference = np.ma.array(dsm.data - dtm.data, mask=combined_mask)
    valid = difference.compressed()
    if not valid.size:
        return {"comparable_cells": 0}
    return {
        "comparable_cells": int(valid.size),
        "minimum_m": float(valid.min()),
        "maximum_m": float(valid.max()),
        "mean_m": float(valid.mean()),
        "median_m": float(np.median(valid)),
        "cells_dsm_over_dtm_2m_percent": float(np.mean(valid > 2.0) * 100.0),
        "cells_dsm_below_dtm_0_25m_percent": float(np.mean(valid < -0.25) * 100.0),
    }


def write_previews(dtm_path: Path, preview_root: Path) -> list[dict[str, Any]]:
    preview_root.mkdir(parents=True, exist_ok=True)
    with rasterio.open(dtm_path) as source:
        values = source.read(1, masked=True).astype(np.float64)
        extent = [source.bounds.left, source.bounds.right, source.bounds.bottom, source.bounds.top]
        dx = abs(float(source.transform.a))
        dy = abs(float(source.transform.e))

    valid = values.compressed()
    low, high = np.percentile(valid, [2, 98])
    elevation_path = preview_root / "elevation.png"
    figure, axis = plt.subplots(figsize=(8, 8), dpi=150)
    image = axis.imshow(values, cmap="terrain", vmin=low, vmax=high, extent=extent)
    axis.set_title("DTM elevation — metres above Ordnance Datum")
    axis.set_xlabel("British National Grid easting (m)")
    axis.set_ylabel("British National Grid northing (m)")
    figure.colorbar(image, ax=axis, label="Elevation (m)", shrink=0.8)
    figure.tight_layout()
    figure.savefig(elevation_path)
    plt.close(figure)

    filled = values.filled(np.nan)
    grad_y, grad_x = np.gradient(filled, dy, dx)
    slope = np.pi / 2 - np.arctan(np.hypot(grad_x, grad_y))
    aspect = np.arctan2(-grad_x, grad_y)
    azimuth = np.deg2rad(315.0)
    altitude = np.deg2rad(45.0)
    shade = (
        np.sin(altitude) * np.sin(slope)
        + np.cos(altitude) * np.cos(slope) * np.cos(azimuth - aspect)
    )
    shade = np.ma.array(np.clip((shade + 1.0) / 2.0, 0.0, 1.0), mask=values.mask)
    hillshade_path = preview_root / "hillshade.png"
    figure, axis = plt.subplots(figsize=(8, 8), dpi=150)
    axis.imshow(shade, cmap="gray", vmin=0, vmax=1, extent=extent)
    axis.set_title("DTM analytical hillshade — 315° azimuth, 45° altitude")
    axis.set_xlabel("British National Grid easting (m)")
    axis.set_ylabel("British National Grid northing (m)")
    figure.tight_layout()
    figure.savefig(hillshade_path)
    plt.close(figure)
    return [
        {"path": elevation_path.name, "bytes": elevation_path.stat().st_size},
        {"path": hillshade_path.name, "bytes": hillshade_path.stat().st_size},
    ]


def _wgs84_bounds(aoi: Aoi) -> dict[str, float]:
    transformer = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)
    left, bottom, right, top = aoi.bounds
    west, south = transformer.transform(left, bottom)
    east, north = transformer.transform(right, top)
    return {"west": west, "south": south, "east": east, "north": north}


def run(aoi: Aoi, data_root: Path) -> dict[str, Any]:
    data_root = data_root.resolve()
    repository_root = Path(__file__).resolve().parents[2]
    if data_root == repository_root or repository_root in data_root.parents:
        raise ValueError("Generated terrain data must be written outside the Git worktree")
    metadata_root = data_root / "metadata"
    raster_root = data_root / "rasters"
    preview_root = data_root / "previews"
    metadata_root.mkdir(parents=True, exist_ok=True)

    historic_payload = query_catalogue(HISTORIC_TYPENAME, aoi)
    national_payload = query_catalogue(NATIONAL_TYPENAME, aoi)
    historic = normalized_catalogue_features(historic_payload)
    national = normalized_catalogue_features(national_payload)
    (metadata_root / "historic-catalogue.json").write_text(
        json.dumps(historic_payload, indent=2) + "\n", encoding="utf-8"
    )
    (metadata_root / "national-catalogue.json").write_text(
        json.dumps(national_payload, indent=2) + "\n", encoding="utf-8"
    )
    selected = choose_source(historic, national)
    if selected["family"] != "welsh_government_2020_2023":
        raise RuntimeError(
            "The best source is a finer historic archive. Its tiled ZIP must be "
            "reviewed before extraction; the national COG is not silently substituted."
        )

    dtm_path = raster_root / f"{aoi.identifier}-dtm-1m.tif"
    dsm_path = raster_root / f"{aoi.identifier}-dsm-1m.tif"
    dtm_stats = extract_cog(str(selected["dtm_url"]), aoi, dtm_path)
    dsm_stats = extract_cog(str(selected["dsm_url"]), aoi, dsm_path)
    comparison = compare_surfaces(dtm_path, dsm_path)
    previews = write_previews(dtm_path, preview_root)

    result = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "aoi": {
            **asdict(aoi),
            "crs": CRS,
            "bounds": list(aoi.bounds),
            "bounds_wgs84": _wgs84_bounds(aoi),
        },
        "catalogue": {
            "historic_query": _wfs_url(HISTORIC_TYPENAME, aoi),
            "national_query": _wfs_url(NATIONAL_TYPENAME, aoi),
            "historic_features": historic,
            "national_features": national,
        },
        "selection": {
            **selected,
            "reason": (
                "Historic coverage intersecting the AOI is 1 m; the national survey has the same "
                "native resolution, newer capture, consistent AOI coverage, and direct COG access."
            ),
        },
        "licence": {
            "name": "Open Government Licence for Public Sector Information, version 3.0",
            "url": OGL_URL,
            "attribution": "Contains Welsh Government information licensed under the Open Government Licence v3.0.",
        },
        "retrieval": {
            "method": "bounded HTTP range reads from national Cloud Optimized GeoTIFFs",
            "source_objects_downloaded_whole": False,
            "local_path_convention": "rasters/<aoi-id>-{dtm,dsm}-1m.tif; previews/{elevation,hillshade}.png",
        },
        "rasters": {"dtm": dtm_stats, "dsm": dsm_stats},
        "surface_difference_dsm_minus_dtm": comparison,
        "previews": previews,
    }
    manifest_path = metadata_root / "manifest.json"
    manifest_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
