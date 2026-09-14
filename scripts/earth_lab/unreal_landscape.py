from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject


LANDSCAPE_MID_VALUE = 32768
LANDSCAPE_ENCODING_STEPS_PER_UNSCALED_UNIT = 128.0


@dataclass(frozen=True, slots=True)
class LandscapeSettings:
    output_vertices: int = 2017
    quads_per_section: int = 63
    sections_per_component: int = 4
    components_per_axis: int = 16
    vertical_origin_m_odn: float = 650.0
    unreal_z_scale: float = 150.0

    @property
    def quads_per_axis(self) -> int:
        return self.output_vertices - 1

    def validate(self) -> None:
        expected = (
            self.quads_per_section
            * int(round(math.sqrt(self.sections_per_component)))
            * self.components_per_axis
            + 1
        )
        if expected != self.output_vertices:
            raise ValueError(
                f"Landscape layout produces {expected} vertices, not {self.output_vertices}"
            )
        if self.unreal_z_scale <= 0:
            raise ValueError("Unreal Z scale must be positive")


def encode_elevation_m(
    elevation_m: np.ndarray,
    vertical_origin_m_odn: float,
    unreal_z_scale: float,
) -> np.ndarray:
    if not np.all(np.isfinite(elevation_m)):
        raise ValueError("Unreal Landscape cannot preserve missing terrain cells")
    unrounded = (
        (elevation_m - vertical_origin_m_odn)
        * 100.0
        * LANDSCAPE_ENCODING_STEPS_PER_UNSCALED_UNIT
        / unreal_z_scale
        + LANDSCAPE_MID_VALUE
    )
    if float(unrounded.min()) < 0 or float(unrounded.max()) > 65535:
        raise ValueError("Elevation range does not fit the configured Unreal Z scale")
    return np.rint(unrounded).astype(np.uint16)


def decode_elevation_m(
    encoded: np.ndarray,
    vertical_origin_m_odn: float,
    unreal_z_scale: float,
) -> np.ndarray:
    return (
        (encoded.astype(np.float64) - LANDSCAPE_MID_VALUE)
        / LANDSCAPE_ENCODING_STEPS_PER_UNSCALED_UNIT
        * unreal_z_scale
        / 100.0
        + vertical_origin_m_odn
    )


def resample_full_extent(
    source_values: np.ndarray,
    source_transform: rasterio.Affine,
    source_crs: rasterio.crs.CRS,
    source_nodata: float | None,
    output_vertices: int,
) -> tuple[np.ndarray, rasterio.Affine]:
    height, width = source_values.shape
    left, bottom, right, top = rasterio.transform.array_bounds(
        height, width, source_transform
    )
    output_transform = from_bounds(
        left, bottom, right, top, output_vertices, output_vertices
    )
    destination = np.full((output_vertices, output_vertices), np.nan, dtype=np.float32)
    reproject(
        source=source_values,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        src_nodata=source_nodata,
        dst_transform=output_transform,
        dst_crs=source_crs,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )
    if not np.all(np.isfinite(destination)):
        raise ValueError("Resampling produced missing terrain; no fill is permitted")
    return destination, output_transform


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_heightmaps(encoded: np.ndarray, stem: Path) -> dict[str, Any]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    png_path = stem.with_suffix(".png")
    r16_path = stem.with_suffix(".r16")
    Image.fromarray(encoded).save(png_path)
    encoded.astype("<u2", copy=False).tofile(r16_path)

    png_decoded = np.asarray(Image.open(png_path), dtype=np.uint16)
    r16_decoded = np.fromfile(r16_path, dtype="<u2").reshape(encoded.shape)
    if not np.array_equal(encoded, png_decoded):
        raise RuntimeError("16-bit PNG round trip changed encoded heights")
    if not np.array_equal(encoded, r16_decoded):
        raise RuntimeError("R16 round trip changed encoded heights")
    return {
        "png": {
            "path": png_path.name,
            "bytes": png_path.stat().st_size,
            "sha256": _sha256(png_path),
        },
        "r16": {
            "path": r16_path.name,
            "bytes": r16_path.stat().st_size,
            "sha256": _sha256(r16_path),
            "byte_order": "little-endian",
        },
    }


def _spatial_round_trip_error(
    original: np.ndarray,
    original_transform: rasterio.Affine,
    encoded_decoded: np.ndarray,
    encoded_transform: rasterio.Affine,
    crs: rasterio.crs.CRS,
) -> dict[str, float]:
    restored = np.full(original.shape, np.nan, dtype=np.float32)
    reproject(
        source=encoded_decoded.astype(np.float32),
        destination=restored,
        src_transform=encoded_transform,
        src_crs=crs,
        dst_transform=original_transform,
        dst_crs=crs,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )
    difference = restored.astype(np.float64) - original.astype(np.float64)
    return {
        "maximum_absolute_m": float(np.max(np.abs(difference))),
        "mean_absolute_m": float(np.mean(np.abs(difference))),
        "rmse_m": float(np.sqrt(np.mean(np.square(difference)))),
    }


def convert_surface(
    source_path: Path,
    destination_root: Path,
    surface: str,
    settings: LandscapeSettings,
) -> dict[str, Any]:
    with rasterio.open(source_path) as source:
        source_values = source.read(1, masked=True)
        if np.ma.getmaskarray(source_values).any():
            raise ValueError(
                f"{source_path.name} contains nodata; Landscape conversion refuses to fill it"
            )
        original = source_values.filled(np.nan).astype(np.float32, copy=False)
        resampled, resampled_transform = resample_full_extent(
            original,
            source.transform,
            source.crs,
            source.nodata,
            settings.output_vertices,
        )
        source_metadata = {
            "path": source_path.name,
            "width": source.width,
            "height": source.height,
            "crs": str(source.crs),
            "bounds": [
                float(source.bounds.left),
                float(source.bounds.bottom),
                float(source.bounds.right),
                float(source.bounds.top),
            ],
            "pixel_size_m": [
                abs(float(source.transform.a)),
                abs(float(source.transform.e)),
            ],
            "nodata": source.nodata,
            "minimum_m": float(original.min()),
            "maximum_m": float(original.max()),
        }
        source_transform = source.transform
        source_crs = source.crs

    encoded = encode_elevation_m(
        resampled, settings.vertical_origin_m_odn, settings.unreal_z_scale
    )
    decoded = decode_elevation_m(
        encoded, settings.vertical_origin_m_odn, settings.unreal_z_scale
    )
    encoding_error = decoded - resampled.astype(np.float64)
    files = _write_heightmaps(
        encoded, destination_root / f"{source_path.stem}-landscape-2017"
    )
    return {
        "surface": surface,
        "source": source_metadata,
        "output": {
            "width": settings.output_vertices,
            "height": settings.output_vertices,
            "encoded_minimum": int(encoded.min()),
            "encoded_maximum": int(encoded.max()),
            "decoded_minimum_m": float(decoded.min()),
            "decoded_maximum_m": float(decoded.max()),
            "files": files,
        },
        "validation": {
            "encoding_maximum_absolute_error_m": float(
                np.max(np.abs(encoding_error))
            ),
            "encoding_mean_absolute_error_m": float(
                np.mean(np.abs(encoding_error))
            ),
            "spatial_resample_round_trip": _spatial_round_trip_error(
                original,
                source_transform,
                decoded,
                resampled_transform,
                source_crs,
            ),
            "northwest_encoded": int(encoded[0, 0]),
            "northeast_encoded": int(encoded[0, -1]),
            "southwest_encoded": int(encoded[-1, 0]),
            "southeast_encoded": int(encoded[-1, -1]),
        },
    }


def build_landscape_import(
    terrain_root: Path,
    destination_root: Path,
    settings: LandscapeSettings | None = None,
) -> dict[str, Any]:
    settings = settings or LandscapeSettings()
    settings.validate()
    terrain_root = terrain_root.resolve()
    destination_root = destination_root.resolve()
    repository_root = Path(__file__).resolve().parents[2]
    if destination_root == repository_root or repository_root in destination_root.parents:
        raise ValueError("Generated Unreal terrain must be written outside the Git worktree")

    lab_manifest_path = terrain_root / "metadata" / "manifest.json"
    lab_manifest = json.loads(lab_manifest_path.read_text(encoding="utf-8"))
    aoi = lab_manifest["aoi"]
    bounds = [float(value) for value in aoi["bounds"]]
    width_m = bounds[2] - bounds[0]
    height_m = bounds[3] - bounds[1]
    if not math.isclose(width_m, height_m):
        raise ValueError("Lab 002 currently requires a square Landscape AOI")
    xy_scale_m = width_m / settings.quads_per_axis

    surfaces = {}
    for surface in ("dtm", "dsm"):
        source_name = lab_manifest["rasters"][surface]["path"]
        surfaces[surface] = convert_surface(
            terrain_root / "rasters" / source_name,
            destination_root / "heightmaps",
            surface,
            settings,
        )

    result = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "representation": {
            "type": "Unreal Landscape",
            "default_surface": "dtm",
            "reason": (
                "Landscape retains a dense measured height field while providing built-in "
                "terrain LOD and a route toward larger partitioned areas."
            ),
        },
        "source_manifest": str(lab_manifest_path.relative_to(terrain_root)),
        "source_crs": str(aoi["crs"]),
        "source_aoi_bounds": bounds,
        "dimension_conversion": {
            "source_cells": [
                surfaces["dtm"]["source"]["width"],
                surfaces["dtm"]["source"]["height"],
            ],
            "output_vertices": [settings.output_vertices, settings.output_vertices],
            "method": "bilinear resampling over the unchanged full AOI bounds",
            "samples_added_per_axis": (
                settings.output_vertices - surfaces["dtm"]["source"]["width"]
            ),
            "sample_count_change_percent": (
                settings.output_vertices / surfaces["dtm"]["source"]["width"] - 1.0
            )
            * 100.0,
            "cropped": False,
            "padded": False,
            "smoothed_or_eroded": False,
        },
        "unreal_landscape": {
            "quads_per_section": settings.quads_per_section,
            "sections_per_component": settings.sections_per_component,
            "components": [
                settings.components_per_axis,
                settings.components_per_axis,
            ],
            "quads_per_axis": settings.quads_per_axis,
            "xy_scale_cm": xy_scale_m * 100.0,
            "z_scale": settings.unreal_z_scale,
            "expected_world_dimensions_m": [width_m, height_m],
            "flip_y_axis_on_import": False,
        },
        "coordinate_frame": {
            "local_origin_bng": {
                "easting": (bounds[0] + bounds[2]) / 2.0,
                "northing": (bounds[1] + bounds[3]) / 2.0,
                "elevation_m_odn": settings.vertical_origin_m_odn,
            },
            "unreal_origin_cm": [0.0, 0.0, 0.0],
            "axis_mapping": {
                "+X": "British National Grid east",
                "+Y": "British National Grid south (PNG rows run north to south)",
                "+Z": "up",
            },
            "bng_from_unreal": {
                "easting": "266400 + X_cm / 100",
                "northing": "359300 - Y_cm / 100",
                "elevation_m_odn": "650 + Z_cm / 100",
            },
        },
        "height_encoding": {
            "formula_encode": (
                "uint16 = round((elevation_m_ODN - 650) * 100 * 128 / 150 + 32768)"
            ),
            "formula_decode": (
                "elevation_m_ODN = 650 + (uint16 - 32768) / 128 * 150 / 100"
            ),
            "unreal_mid_value": LANDSCAPE_MID_VALUE,
            "vertical_origin_m_odn": settings.vertical_origin_m_odn,
            "z_scale": settings.unreal_z_scale,
            "quantization_step_m": settings.unreal_z_scale / 128.0 / 100.0,
            "vertical_exaggeration": 1.0,
        },
        "surfaces": surfaces,
    }
    destination_root.mkdir(parents=True, exist_ok=True)
    manifest_path = destination_root / "unreal-landscape-manifest.json"
    manifest_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
