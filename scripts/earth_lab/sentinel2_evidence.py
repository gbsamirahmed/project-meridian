"""Bounded Sentinel-2 L2A acquisition helpers for Earth Lab 005B."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import Resampling, reproject, transform_bounds

from observational_evidence import EvidenceQuery, Observation
from surface_evidence import AnalysisGrid, scl_summary


OFFICIAL_STAC = "https://stac.dataspace.copernicus.eu/v1"
COG_STAC = "https://earth-search.aws.element84.com/v1"


def _json_request(url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json", "User-Agent": "Meridian-Earth-Lab/005B"},
        method="GET" if body is None else "POST",
    )
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def stac_search(endpoint: str, collection: str, request: EvidenceQuery, limit: int = 50) -> list[dict[str, Any]]:
    if request.crs != "EPSG:4326":
        raise ValueError("STAC search bounds must be supplied in EPSG:4326")
    body = {
        "collections": [collection],
        "bbox": list(request.bounds),
        "datetime": request.datetime_range,
        "limit": limit,
    }
    return list(_json_request(f"{endpoint}/search", body).get("features", []))


def observation_from_items(official_item: dict[str, Any], cog_item: dict[str, Any]) -> Observation:
    official_product = official_item["id"]
    mirror_product = cog_item["properties"].get("s2:product_uri", "").removesuffix(".SAFE")
    if official_product != mirror_product:
        raise ValueError(f"Official/CDSE product {official_product} does not match COG product {mirror_product}")
    assets: dict[str, dict[str, Any]] = {}
    for name, asset in cog_item["assets"].items():
        raster_bands = asset.get("raster:bands") or [{}]
        assets[name] = {
            "href": asset.get("href"),
            "type": asset.get("type"),
            "raster": raster_bands[0],
            "eo": (asset.get("eo:bands") or [{}])[0],
        }
    properties = dict(official_item["properties"])
    properties["cog_mirror_item_id"] = cog_item["id"]
    properties["cog_mirror_provider"] = "Element 84 Earth Search / AWS open-data COG mirror"
    return Observation(
        provider="Copernicus Data Space Ecosystem",
        product_id=official_product,
        acquired_at=properties["datetime"],
        source_crs="EPSG:32630",
        assets=assets,
        properties=properties,
    )


def read_scl_to_grid(url: str, grid: AnalysisGrid) -> np.ndarray:
    destination = np.zeros((grid.height, grid.width), dtype=np.uint8)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        with rasterio.open(url) as source:
            reproject(
                source=rasterio.band(source, 1),
                destination=destination,
                src_transform=source.transform,
                src_crs=source.crs,
                src_nodata=source.nodata,
                dst_transform=grid.transform,
                dst_crs=grid.crs,
                dst_nodata=0,
                resampling=Resampling.nearest,
            )
    return destination


def score_scl(url: str, grid: AnalysisGrid) -> dict[str, Any]:
    return scl_summary(read_scl_to_grid(url, grid))


def extract_native_window(url: str, destination: Path, bounds_bng: tuple[float, float, float, float]) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    bounds_key = ','.join(f'{value:.3f}' for value in bounds_bng)
    if destination.exists():
        with rasterio.open(destination) as cached:
            if (
                cached.tags().get("MERIDIAN_SOURCE_URL") == url
                and cached.tags().get("MERIDIAN_BOUNDS_BNG") == bounds_key
            ):
                cached_bounds = rasterio.transform.array_bounds(cached.height, cached.width, cached.transform)
                return {
                    "path": str(destination),
                    "width": int(cached.width),
                    "height": int(cached.height),
                    "crs": str(cached.crs),
                    "native_pixel_size": [abs(float(cached.transform.a)), abs(float(cached.transform.e))],
                    "native_bounds": list(cached_bounds),
                    "source_url": url,
                }
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        with rasterio.open(url) as source:
            native_bounds = transform_bounds("EPSG:27700", source.crs, *bounds_bng, densify_pts=21)
            window = from_bounds(*native_bounds, source.transform).round_offsets().round_lengths()
            window = window.intersection(rasterio.windows.Window(0, 0, source.width, source.height))
            data = source.read(1, window=window)
            transform = source.window_transform(window)
            profile = source.profile.copy()
            profile.update(
                width=data.shape[1],
                height=data.shape[0],
                transform=transform,
                compress="deflate",
                tiled=True,
                blockxsize=min(256, max(16, (data.shape[1] // 16) * 16)),
                blockysize=min(256, max(16, (data.shape[0] // 16) * 16)),
            )
            with rasterio.open(destination, "w", **profile) as output:
                output.write(data, 1)
                output.update_tags(
                    MERIDIAN_SOURCE_URL=url,
                    MERIDIAN_BOUNDS_BNG=bounds_key,
                    MERIDIAN_EXTRACTION="bounded native-grid window; no reprojection",
                )
    return {
        "path": str(destination),
        "width": int(data.shape[1]),
        "height": int(data.shape[0]),
        "crs": str(profile["crs"]),
        "native_pixel_size": [abs(float(transform.a)), abs(float(transform.e))],
        "native_bounds": list(rasterio.transform.array_bounds(data.shape[0], data.shape[1], transform)),
        "source_url": url,
    }
