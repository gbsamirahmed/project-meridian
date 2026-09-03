"""Exact GFS atmospheric diagnostics; shared acquisition, not a provider framework.

The inspection command caches only indexed messages in an ignored run directory.
It never downloads full GRIB files and never publishes a discovery pointer.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
import shutil
import uuid

import numpy as np
from PIL import Image

import gfs_weather_builder as core


@dataclass(frozen=True)
class AtmosphericField:
    id: str
    parameter: str
    level: str
    short_name: str
    level_type: str
    source_units: str
    category: int
    number: int
    name: str
    units: str
    vertical_reference: str


FIELDS = (
    AtmosphericField("gust_surface", "GUST", "surface", "gust", "surface",
                     "m s**-1", 2, 22, "Surface wind gust", "m/s", "surface"),
    AtmosphericField("visibility_surface", "VIS", "surface", "vis", "surface",
                     "m", 19, 0, "Model visibility", "m", "surface"),
    AtmosphericField("freezing_level", "HGT", "0C isotherm", "gh", "isothermZero",
                     "gpm", 3, 5, "0°C isotherm height", "gpm", "mean-sea-level"),
    AtmosphericField("highest_freezing_level", "HGT", "highest tropospheric freezing level",
                     "gh", "highestTroposphericFreezing", "gpm", 3, 5,
                     "Highest tropospheric freezing level", "gpm", "mean-sea-level"),
    AtmosphericField("cloud_ceiling", "HGT", "cloud ceiling", "gh", "cloudCeiling",
                     "gpm", 3, 5, "Cloud ceiling (experimental)", "gpm", "model-surface"),
)


def select_record(inventory: str, hour: int, field: AtmosphericField):
    candidates = [record for record in core.parse_inventory_index(inventory)
                  if record.parameter == field.parameter and record.level == field.level
                  and record.time_description == f"{hour} hour fcst"]
    if len(candidates) != 1:
        raise ValueError(f"Expected one instantaneous {field.id} f{hour:03d}; found {len(candidates)}")
    return candidates[0]


def validate_metadata(metadata: dict, run_time: datetime, hour: int, field: AtmosphericField):
    valid = run_time + timedelta(hours=hour)
    expected = {
        "shortName": field.short_name, "units": field.source_units,
        "typeOfLevel": field.level_type, "level": 0,
        "discipline": 0, "parameterCategory": field.category, "parameterNumber": field.number,
        "productDefinitionTemplateNumber": 0, "stepType": "instant",
        "startStep": hour, "endStep": hour, "forecastTime": hour,
        "Ni": core.EXPECTED_NI, "Nj": core.EXPECTED_NJ,
        "gridType": "regular_ll", "scanningMode": 0,
        "jScansPositively": 0, "iScansNegatively": 0,
        "jPointsAreConsecutive": 0, "alternativeRowScanning": 0,
        "iDirectionIncrementInDegrees": 0.25, "jDirectionIncrementInDegrees": 0.25,
        "latitudeOfFirstGridPointInDegrees": 90.0, "longitudeOfFirstGridPointInDegrees": 0.0,
        "latitudeOfLastGridPointInDegrees": -90.0, "longitudeOfLastGridPointInDegrees": 359.75,
        "dataDate": int(run_time.strftime("%Y%m%d")), "dataTime": int(run_time.strftime("%H%M")),
        "validityDate": int(valid.strftime("%Y%m%d")), "validityTime": int(valid.strftime("%H%M")),
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"{field.id}: unexpected {key}={metadata.get(key)!r}, expected {value!r}")
    if metadata.get("typeOfStatisticalProcessing") not in (None, 255):
        raise ValueError(f"{field.id}: unexpected statistical processing")


def normalise_missing(values: np.ndarray, metadata: dict) -> np.ndarray:
    result = values.copy()
    count = int(metadata["numberOfMissing"])
    # 9999 is also a perfectly valid visibility/height. Only a declared bitmap
    # missing marker is masked, using equality, never a relative isclose test.
    if count:
        result[result == np.float32(metadata["missingValue"])] = np.nan
    if np.isinf(result).any() or int(np.isnan(result).sum()) != count:
        raise ValueError("Inconsistent GRIB missing-value metadata")
    return result


def load_field(resolution, hour: int, field: AtmosphericField, cache: Path):
    base = core.gfs_file_base(resolution.date, resolution.cycle, hour)
    record = select_record(core.fetch_text(base + ".idx"), hour, field)
    path = cache / f"{field.id}-f{hour:03d}-{record.offset}-{record.end_offset}.grib2"
    if path.exists():
        payload = path.read_bytes()
    else:
        payload = core.fetch_bytes(base, (record.offset, record.end_offset))
        if len(payload) != record.end_offset - record.offset + 1:
            raise ValueError("Indexed GRIB byte-range length mismatch")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    values, metadata = core.decode_grib(payload, record)
    validate_metadata(metadata, resolution.run_time, hour, field)
    return normalise_missing(values, metadata), metadata, record


def distribution(values: np.ndarray) -> dict:
    finite = values[np.isfinite(values)]
    return {
        "count": int(values.size), "missing": int(values.size - finite.size),
        "minimum": float(finite.min()) if finite.size else None,
        "maximum": float(finite.max()) if finite.size else None,
        "percentiles": {str(p): float(np.percentile(finite, p)) for p in (1, 5, 25, 50, 75, 95, 99, 99.9)} if finite.size else {},
        "zeros": int(np.count_nonzero(finite == 0)),
        "nearCeilingSentinel": int(np.count_nonzero(np.abs(finite - 20000) <= 1)),
    }


def inspect_run(args, resolution, hours):
    started = time.monotonic()
    directory = source_cache(args, resolution)
    results = {}
    for field in FIELDS:
        arrays, steps = [], []
        for hour in hours:
            values, metadata, record = load_field(resolution, hour, field, directory)
            arrays.append(values.ravel())
            steps.append({"hour": hour, "inventory": record.description, "metadata": metadata, **distribution(values)})
            print(f"Inspected {field.id} f{hour:03d}", flush=True)
        results[field.id] = {"summary": distribution(np.concatenate(arrays)), "timesteps": steps}
        print(json.dumps({field.id: results[field.id]["summary"]}), flush=True)
    core.write_json(directory / "inspection.json", {
        "runTime": resolution.run_time.isoformat(), "checkedCandidates": resolution.checked_candidates,
        "fields": results, "seconds": time.monotonic() - started,
    })


def encoding(field: AtmosphericField) -> tuple[float, float, tuple[float, float]]:
    if field.id == "gust_surface":
        return 0.1, 0.0, (0.0, 200.0)
    if field.id == "visibility_surface":
        return 10.0, 0.0, (0.0, 100000.0)
    return 5.0, -1000.0, (-1000.0, 20001.0 if field.id == "cloud_ceiling" else 30000.0)


def source_cache(args, resolution):
    run_id = resolution.run_time.strftime("%Y%m%dT%HZ")
    # Inspection must not create an immutable run before precipitation can stage
    # it. Reuse the initial inspection cache if already present; otherwise keep
    # this disposable, bounded (five messages/hour) cache outside the run assets.
    existing = args.output_root / run_id / "atmospheric-source"
    return existing if existing.exists() else args.output_root / f".{run_id}-atmospheric-source-building"


def validated_values(values: np.ndarray, field: AtmosphericField) -> tuple[np.ndarray, int]:
    _, _, bounds = encoding(field)
    finite = values[np.isfinite(values)]
    if np.isinf(values).any() or (finite.size and (finite.min() < bounds[0] or finite.max() > bounds[1])):
        raise ValueError(f"{field.id} exceeds validated physical range {bounds}")
    result = values.copy()
    sentinel = np.zeros(values.shape, dtype=bool)
    if field.id == "cloud_ceiling":
        # NOAA UPP CALCEILING uses 20000 for no ceiling. GRIB packing moves this
        # slightly (observed <0.4 gpm); a documented 1 gpm tolerance is distinct
        # from bitmap missing. Mask BEFORE interpolation, never mix a sentinel
        # with actual heights. Edges consequently remain conservatively no-data.
        sentinel = np.isfinite(values) & (np.abs(values - 20000.0) <= 1.0)
        result[sentinel] = np.nan
    return result, int(sentinel.sum())


def encode_png(values: np.ndarray, path: Path, field: AtmosphericField):
    scale, offset, bounds = encoding(field)
    valid = np.isfinite(values)
    if np.isinf(values).any() or np.any(values[valid] < bounds[0]) or np.any(values[valid] > bounds[1]):
        raise ValueError(f"{field.id} invalid tile values")
    codes = np.full(values.shape, core.NO_DATA_VALUE, dtype=np.uint16)
    quantized = np.rint((values[valid] - offset) / scale)
    if np.any(quantized < 0) or np.any(quantized >= core.NO_DATA_VALUE):
        raise ValueError("Scalar encoding exceeds uint16 range")
    codes[valid] = quantized.astype(np.uint16)
    rgba = np.zeros((*values.shape, 4), dtype=np.uint8)
    rgba[:, :, 0], rgba[:, :, 1], rgba[:, :, 3] = codes >> 8, codes & 255, 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba).save(path, format="PNG", optimize=True, compress_level=9)


def decode_png(path: Path, field: AtmosphericField):
    rgba = np.asarray(Image.open(path).convert("RGBA"), dtype=np.uint8)
    codes = rgba[:, :, 0].astype(np.uint16) * 256 + rgba[:, :, 1].astype(np.uint16)
    scale, offset, _ = encoding(field)
    values = codes.astype(np.float64) * scale + offset
    values[codes == core.NO_DATA_VALUE] = np.nan
    return values


def field_manifest(field, resolution, timesteps):
    scale, offset, bounds = encoding(field)
    ceiling = field.id == "cloud_ceiling"
    interpretation = {
        "gust_surface": "Instantaneous surface gust diagnostic; not a preceding-hour maximum; no direction.",
        "visibility_surface": "Model meteorological visibility; source often saturates near 24.1 km; not local sight distance.",
        "freezing_level": "Geopotential height of the 0°C isotherm; zero is retained; not an ice detector.",
        "highest_freezing_level": "Highest tropospheric 0°C crossing retained separately; zero is retained.",
        "cloud_ceiling": "Experimental ceiling above model surface, not cloud base or cloud immersion. UPP no-ceiling values within 1 gpm of 20000 are unavailable before interpolation.",
    }[field.id]
    return {
        "schemaVersion": 2, "id": f"gfs-0p25-{field.id}-{resolution.run_time:%Y%m%dT%HZ}",
        "model": "NOAA GFS", "product": "pgrb2.0p25",
        "runTime": resolution.run_time.isoformat().replace("+00:00", "Z"),
        "field": {"id": field.id, "kind": "scalar", "sourceParameter": field.parameter,
                  "sourceLevel": field.level, "displayName": field.name, "units": field.units,
                  "sourceUnits": field.source_units, "validRange": list(bounds),
                  "verticalReference": field.vertical_reference, "timeSemantics": "instantaneous",
                  "noDataMeaning": "missing-or-no-diagnosed-ceiling" if ceiling else "missing",
                  "interpretation": interpretation,
                  "nativeResolution": {"longitudeDegrees": 0.25, "latitudeDegrees": 0.25}},
        "tiles": {"format": "png", "encoding": "uint16-rg", "tileSize": core.TILE_SIZE,
                  "minZoom": core.MIN_ZOOM, "maxZoom": core.MAX_ZOOM, "scale": scale,
                  "offset": offset, "noData": core.NO_DATA_VALUE,
                  "resampling": "bilinear-from-canonical-grid", "overzoom": True},
        "coverage": {"bounds": [-180, -core.WEB_MERCATOR_LIMIT, 180, core.WEB_MERCATOR_LIMIT],
                     "worldWrap": True, "polarLimit": "Web Mercator clips beyond ±85.05112878° latitude."},
        "timesteps": timesteps,
        "attribution": {"label": "Derived from NOAA Global Forecast System (GFS)",
                        "url": "https://registry.opendata.aws/noaa-gfs-bdp-pds/", "source": core.NOAA_BUCKET},
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def build_field(args, resolution, hours, run_directory, run_id, field):
    started = time.monotonic()
    destination = run_directory / field.id.replace("_", "-")
    relative_manifest = f"{run_id}/{destination.name}/manifest.json"
    expected_tiles = len(hours) * sum(4**z for z in range(core.MIN_ZOOM, core.MAX_ZOOM + 1))
    if destination.exists():
        existing = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
        expected = field_manifest(field, resolution, existing["timesteps"])
        if (existing["field"] != expected["field"] or existing["tiles"] != expected["tiles"]
                or existing["runTime"] != expected["runTime"]
                or [s["forecastHour"] for s in existing["timesteps"]] != hours
                or any(s["validTime"] != (resolution.run_time + timedelta(hours=s["forecastHour"])).isoformat().replace("+00:00", "Z") for s in existing["timesteps"])
                or len(list((destination / "tiles").rglob("*.png"))) != expected_tiles):
            raise ValueError(f"Refusing to overwrite inconsistent immutable {field.id}")
        core.publish_catalog_field(args.output_root, field.id, existing, relative_manifest)
        print(f"Reused validated {field.id} {run_id}", flush=True)
        return
    staging = args.output_root / f".{run_id}-{field.id}-{uuid.uuid4().hex}-building"
    staging.mkdir(parents=True)
    validations, steps = [], []
    tile_bytes = tile_count = 0
    try:
        for hour in hours:
            raw, metadata, record = load_field(resolution, hour, field, source_cache(args, resolution))
            values, sentinel_count = validated_values(raw, field)
            finite = values[np.isfinite(values)]
            if not finite.size:
                raise ValueError(f"{field.id} f{hour:03d} has no publishable values")
            step_id = f"f{hour:03d}"
            for zoom in range(core.MIN_ZOOM, core.MAX_ZOOM + 1):
                for y in range(2**zoom):
                    for x in range(2**zoom):
                        longitude, latitude = core.mercator_pixel_coordinates(zoom, x, y)
                        sampled = core.sample_gfs_grid(values, longitude, latitude)
                        path = staging / "tiles" / step_id / str(zoom) / str(x) / f"{y}.png"
                        encode_png(sampled, path, field)
                        # Byte/pixel decode validation on every exported tile.
                        decoded = decode_png(path, field)
                        valid = np.isfinite(sampled)
                        if not np.array_equal(valid, np.isfinite(decoded)) or (valid.any() and
                            np.max(np.abs(decoded[valid] - sampled[valid])) > encoding(field)[0] / 2 + 1e-5):
                            raise ValueError("Exported scalar PNG failed quantisation/no-data validation")
                        tile_count += 1
                        tile_bytes += path.stat().st_size
            steps.append({"id": step_id, "forecastHour": hour,
                          "validTime": (resolution.run_time + timedelta(hours=hour)).isoformat().replace("+00:00", "Z"),
                          "minimum": float(finite.min()), "maximum": float(finite.max()),
                          "tileTemplate": f"tiles/{step_id}/{{z}}/{{x}}/{{y}}.png"})
            validations.append({"id": step_id, "inventory": record.description, "metadata": metadata,
                                "raw": distribution(raw), "published": distribution(values),
                                "noCeilingCount": sentinel_count})
            print(f"  {field.id} {step_id}: {finite.min():.2f}..{finite.max():.2f} {field.units}", flush=True)
        manifest = field_manifest(field, resolution, steps)
        core.write_json(staging / "manifest.json", manifest)
        core.write_json(staging / "validation.json", {
            "timesteps": validations, "checkedCandidates": resolution.checked_candidates,
            "summary": {"tileCount": tile_count, "tileBytes": tile_bytes, "seconds": time.monotonic() - started,
                        "bitmapMissing": sum(s["raw"]["missing"] for s in validations),
                        "noCeilingCount": sum(s["noCeilingCount"] for s in validations)}})
        if tile_count != expected_tiles:
            raise ValueError("Incomplete atmospheric tile pyramid")
        # Match the established builder's Windows move/copy fallback. Catalogue
        # publication still occurs only after the complete validated tree exists.
        shutil.move(str(staging), str(destination))
        core.publish_catalog_field(args.output_root, field.id, manifest, relative_manifest)
        print(f"Published {field.id}: {tile_count} tiles, {tile_bytes / 1048576:.2f} MiB", flush=True)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def build_atmospheric_datasets(args, resolution, hours, run_directory, run_id):
    failures = []
    for field in FIELDS:
        try:
            build_field(args, resolution, hours, run_directory, run_id, field)
        except Exception as error:
            failures.append(f"{field.id}: {error}")
            print(f"Retained previous {field.id} catalogue entry: {error}", flush=True)
    if failures:
        raise RuntimeError("Atmospheric field build failures: " + "; ".join(failures))


if __name__ == "__main__":
    args = core.parse_args()
    hours = core.parse_hours(args.hours)
    inspect_run(args, core.resolve_run(args, hours), hours)
