"""Build Meridian's static global GFS precipitation proof-of-concept dataset.

The script downloads only the APCP byte ranges listed in NOAA's public GFS
inventory files. It decodes GRIB2 with ECMWF ecCodes, validates accumulation
metadata, and writes lossless uint16 numeric PNG tiles plus a provider-neutral
manifest. It deliberately does not colour the data; the browser owns styling.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import eccodes
import numpy as np
from PIL import Image


NOAA_BUCKET = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
WEB_MERCATOR_LIMIT = 85.0511287798066
TILE_SIZE = 256
MIN_ZOOM = 0
MAX_ZOOM = 3
VALUE_SCALE_MM = 0.01
VALUE_OFFSET_MM = 0.0
NO_DATA_VALUE = 65_535
PACKING_NOISE_TOLERANCE_MM = 0.1
EXPECTED_NI = 1_440
EXPECTED_NJ = 721
INTERVAL_PATTERN = re.compile(r"(?P<start>\d+)-(?P<end>\d+) hour acc fcst")
GFS_CYCLES = (18, 12, 6, 0)
DEFAULT_CANDIDATE_COUNT = 12
HTTP_RETRY_ATTEMPTS = 3


@dataclass(frozen=True)
class InventoryRecord:
    offset: int
    end_offset: int
    description: str
    start_step: int
    end_step: int


@dataclass
class DecodedField:
    values: np.ndarray
    metadata: dict[str, Any]
    source_record: InventoryRecord
    duplicate_records: int


@dataclass(frozen=True)
class PlannedTimestep:
    forecast_hour: int
    records: tuple[InventoryRecord, ...]
    derivation_start_step: int


@dataclass(frozen=True)
class RunResolution:
    date: str
    cycle: str
    run_time: datetime
    plan: tuple[PlannedTimestep, ...]
    checked_candidates: tuple[dict[str, str], ...]


class SourceUnavailableError(RuntimeError):
    """Raised when a NOAA object needed for a candidate run is unavailable."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate static numeric precipitation tiles from one GFS run."
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--run",
        help="Specific completed GFS run in YYYYMMDDHH form.",
    )
    selection.add_argument(
        "--latest",
        action="store_true",
        help="Resolve the latest fully usable GFS run (the default).",
    )
    parser.add_argument(
        "--hours",
        default="1-24",
        help="Inclusive forecast-hour range, for example 1-24 (default: %(default)s).",
    )
    parser.add_argument(
        "--candidate-count",
        type=int,
        default=DEFAULT_CANDIDATE_COUNT,
        help="Maximum recent cycles to inspect when resolving --latest.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("public/weather/gfs"),
        help="Dataset root written beneath the Vite public directory.",
    )
    parser.add_argument(
        "--keep-downloads",
        action="store_true",
        help="Keep downloaded APCP GRIB messages inside the run directory.",
    )
    return parser.parse_args()


def parse_hours(value: str) -> list[int]:
    match = re.fullmatch(r"(\d+)-(\d+)", value)
    if not match:
        raise ValueError("--hours must use inclusive START-END syntax")

    start, end = (int(part) for part in match.groups())
    if start < 1 or end < start:
        raise ValueError("forecast-hour range must start at 1 and increase")

    return list(range(start, end + 1))


def validate_run(value: str) -> tuple[str, str, datetime]:
    if not re.fullmatch(r"\d{10}", value):
        raise ValueError("--run must use YYYYMMDDHH")

    run_time = datetime.strptime(value, "%Y%m%d%H").replace(tzinfo=timezone.utc)
    return value[:8], value[8:], run_time


def fetch_bytes(
    url: str,
    byte_range: tuple[int, int] | None = None,
    attempts: int = HTTP_RETRY_ATTEMPTS,
) -> bytes:
    headers = {"User-Agent": "Meridian-GFS-POC/1.0"}
    if byte_range:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[1]}"

    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in (403, 404):
                raise SourceUnavailableError(f"HTTP {error.code} for {url}") from error
            if error.code not in (429, 500, 502, 503, 504) or attempt == attempts:
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == attempts:
                raise
        time.sleep(2 ** (attempt - 1))

    raise RuntimeError("unreachable HTTP retry state")


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def gfs_file_base(date_value: str, cycle: str, forecast_hour: int) -> str:
    return (
        f"{NOAA_BUCKET}/gfs.{date_value}/{cycle}/atmos/"
        f"gfs.t{cycle}z.pgrb2.0p25.f{forecast_hour:03d}"
    )


def parse_inventory(text: str) -> list[InventoryRecord]:
    raw_records: list[tuple[int, str]] = []
    for line in text.splitlines():
        parts = line.split(":", 4)
        if len(parts) < 5:
            continue
        raw_records.append((int(parts[1]), line))

    matches: list[InventoryRecord] = []
    for index, (offset, line) in enumerate(raw_records):
        if ":APCP:surface:" not in line:
            continue
        interval_match = INTERVAL_PATTERN.search(line)
        if not interval_match:
            continue

        start_step = int(interval_match.group("start"))
        end_step = int(interval_match.group("end"))
        if index + 1 >= len(raw_records):
            raise ValueError("APCP record is the final inventory entry; byte range is unknown")

        matches.append(
            InventoryRecord(
                offset=offset,
                end_offset=raw_records[index + 1][0] - 1,
                description=line,
                start_step=start_step,
                end_step=end_step,
            )
        )

    if not matches:
        raise ValueError("No interval-based APCP surface records found")

    return matches


def plan_timesteps(
    inventories: dict[int, list[InventoryRecord]], forecast_hours: list[int]
) -> tuple[PlannedTimestep, ...]:
    available_accumulation_starts: set[int] = set()
    plan: list[PlannedTimestep] = []

    for forecast_hour in forecast_hours:
        records = [
            record
            for record in inventories[forecast_hour]
            if record.end_step == forecast_hour
        ]
        intervals = sorted({(record.start_step, record.end_step) for record in records})
        direct_start = forecast_hour - 1
        if any(record.start_step == direct_start for record in records):
            selected_start = direct_start
        else:
            viable_starts = sorted(
                {
                    record.start_step
                    for record in records
                    if record.start_step in available_accumulation_starts
                },
                reverse=True,
            )
            if not viable_starts:
                raise ValueError(
                    f"f{forecast_hour:03d} cannot produce an honest one-hour interval; "
                    f"available APCP intervals are {intervals}"
                )
            selected_start = viable_starts[0]

        selected_records = tuple(
            record for record in records if record.start_step == selected_start
        )
        plan.append(
            PlannedTimestep(
                forecast_hour=forecast_hour,
                records=selected_records,
                derivation_start_step=selected_start,
            )
        )
        available_accumulation_starts.add(selected_start)

    return tuple(plan)


def discover_latest_archive_date(reference_time: datetime) -> date:
    for year in range(reference_time.year, reference_time.year - 3, -1):
        query = urllib.parse.urlencode(
            {"list-type": "2", "delimiter": "/", "prefix": f"gfs.{year}"}
        )
        root = ET.fromstring(fetch_bytes(f"{NOAA_BUCKET}/?{query}"))
        namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
        available_dates: list[date] = []
        for prefix in root.findall("s3:CommonPrefixes/s3:Prefix", namespace):
            if prefix.text and re.fullmatch(r"gfs\.\d{8}/", prefix.text):
                available_dates.append(datetime.strptime(prefix.text[4:12], "%Y%m%d").date())
        if available_dates:
            return max(available_dates)
    raise SourceUnavailableError("NOAA archive listing did not contain a recent GFS date")


def candidate_run_times(latest_date: date, count: int) -> list[datetime]:
    if count < 1:
        raise ValueError("--candidate-count must be at least 1")
    candidates: list[datetime] = []
    day = latest_date
    while len(candidates) < count:
        for cycle in GFS_CYCLES:
            candidates.append(
                datetime(day.year, day.month, day.day, cycle, tzinfo=timezone.utc)
            )
            if len(candidates) == count:
                break
        day -= timedelta(days=1)
    return candidates


def probe_run(
    run_time: datetime, forecast_hours: list[int]
) -> tuple[PlannedTimestep, ...]:
    date_value = run_time.strftime("%Y%m%d")
    cycle = run_time.strftime("%H")
    # The final required hour is a cheap completeness gate before requesting
    # every inventory for a cycle that NOAA may still be publishing.
    last_hour = forecast_hours[-1]
    last_inventory = parse_inventory(fetch_text(f"{gfs_file_base(date_value, cycle, last_hour)}.idx"))
    inventories: dict[int, list[InventoryRecord]] = {last_hour: last_inventory}
    for forecast_hour in forecast_hours:
        if forecast_hour not in inventories:
            inventories[forecast_hour] = parse_inventory(
                fetch_text(f"{gfs_file_base(date_value, cycle, forecast_hour)}.idx")
            )
    return plan_timesteps(inventories, forecast_hours)


def resolve_run(args: argparse.Namespace, forecast_hours: list[int]) -> RunResolution:
    if args.run:
        date_value, cycle, run_time = validate_run(args.run)
        print(f"Checking requested GFS {run_time:%Y-%m-%d %HZ}...")
        plan = probe_run(run_time, forecast_hours)
        return RunResolution(
            date=date_value,
            cycle=cycle,
            run_time=run_time,
            plan=plan,
            checked_candidates=(
                {"runTime": run_time.isoformat().replace("+00:00", "Z"), "result": "usable"},
            ),
        )

    reference_time = datetime.now(timezone.utc)
    latest_date = discover_latest_archive_date(reference_time)
    checked: list[dict[str, str]] = []
    for run_time in candidate_run_times(latest_date, args.candidate_count):
        label = f"{run_time:%Y-%m-%d %HZ}"
        print(f"Checking GFS {label}...")
        try:
            plan = probe_run(run_time, forecast_hours)
        except (SourceUnavailableError, ValueError) as error:
            reason = str(error)
            print(f"  Run rejected: {reason}")
            checked.append(
                {"runTime": run_time.isoformat().replace("+00:00", "Z"), "result": reason}
            )
            continue

        print(
            f"  Required f{forecast_hours[0]:03d} through "
            f"f{forecast_hours[-1]:03d} inventories are usable."
        )
        checked.append(
            {"runTime": run_time.isoformat().replace("+00:00", "Z"), "result": "usable"}
        )
        return RunResolution(
            date=run_time.strftime("%Y%m%d"),
            cycle=run_time.strftime("%H"),
            run_time=run_time,
            plan=plan,
            checked_candidates=tuple(checked),
        )

    raise SourceUnavailableError(
        f"No fully usable GFS run found in the latest {args.candidate_count} cycles"
    )


def decode_grib(message_bytes: bytes, record: InventoryRecord) -> tuple[np.ndarray, dict[str, Any]]:
    message = eccodes.codes_new_from_message(message_bytes)
    if message is None:
        raise ValueError("ecCodes could not decode the APCP message")

    try:
        metadata_keys = [
            "shortName",
            "name",
            "units",
            "stepType",
            "stepRange",
            "startStep",
            "endStep",
            "lengthOfTimeRange",
            "indicatorOfUnitForTimeRange",
            "Ni",
            "Nj",
            "latitudeOfFirstGridPointInDegrees",
            "longitudeOfFirstGridPointInDegrees",
            "latitudeOfLastGridPointInDegrees",
            "longitudeOfLastGridPointInDegrees",
            "iDirectionIncrementInDegrees",
            "jDirectionIncrementInDegrees",
            "jScansPositively",
            "iScansNegatively",
        ]
        metadata = {
            key: eccodes.codes_get(message, key)
            for key in metadata_keys
            if eccodes.codes_is_defined(message, key)
        }
        ni = int(metadata["Ni"])
        nj = int(metadata["Nj"])
        values = np.asarray(
            eccodes.codes_get_values(message), dtype=np.float32
        ).reshape((nj, ni))
    finally:
        eccodes.codes_release(message)

    return values, metadata


def validate_metadata(metadata: dict[str, Any], start_step: int, end_step: int) -> None:
    expected = {
        "shortName": "tp",
        "stepType": "accum",
        "startStep": start_step,
        "endStep": end_step,
        "lengthOfTimeRange": end_step - start_step,
        "Ni": EXPECTED_NI,
        "Nj": EXPECTED_NJ,
        "iDirectionIncrementInDegrees": 0.25,
        "jDirectionIncrementInDegrees": 0.25,
        "jScansPositively": 0,
        "iScansNegatively": 0,
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(
                f"Unexpected GRIB metadata {key}={metadata.get(key)!r}; expected {value!r}"
            )

    if metadata.get("units") != "kg m**-2":
        raise ValueError(f"Unexpected APCP units: {metadata.get('units')!r}")
    if metadata.get("indicatorOfUnitForTimeRange") != 1:
        raise ValueError("APCP accumulation interval is not expressed in hours")


def load_forecast_field(
    date: str,
    cycle: str,
    forecast_hour: int,
    records: tuple[InventoryRecord, ...],
    keep_directory: Path | None,
) -> DecodedField:
    forecast_token = f"f{forecast_hour:03d}"
    base = gfs_file_base(date, cycle, forecast_hour)

    decoded_candidates: list[tuple[np.ndarray, dict[str, Any]]] = []
    for candidate_index, record in enumerate(records):
        message_bytes = fetch_bytes(base, (record.offset, record.end_offset))
        values, metadata = decode_grib(message_bytes, record)
        validate_metadata(metadata, record.start_step, forecast_hour)
        decoded_candidates.append((values, metadata))

        if keep_directory:
            keep_directory.mkdir(parents=True, exist_ok=True)
            (keep_directory / f"{forecast_token}-{candidate_index + 1}.grib2").write_bytes(
                message_bytes
            )

    reference_values, reference_metadata = decoded_candidates[0]
    for candidate_values, candidate_metadata in decoded_candidates[1:]:
        if candidate_metadata != reference_metadata or not np.array_equal(
            candidate_values, reference_values
        ):
            raise ValueError(
                f"Duplicate APCP records disagree for {forecast_token}; refusing to guess"
            )

    if np.any(~np.isfinite(reference_values)):
        raise ValueError(f"Non-finite precipitation values found in {forecast_token}")
    if float(np.min(reference_values)) < 0:
        raise ValueError(f"Negative precipitation found in {forecast_token}")

    return DecodedField(
        values=reference_values,
        metadata=reference_metadata,
        source_record=records[0],
        duplicate_records=len(records),
    )


def mercator_pixel_coordinates(zoom: int, tile_x: int, tile_y: int) -> tuple[np.ndarray, np.ndarray]:
    tile_count = 2**zoom
    x_pixels = tile_x * TILE_SIZE + np.arange(TILE_SIZE, dtype=np.float64) + 0.5
    y_pixels = tile_y * TILE_SIZE + np.arange(TILE_SIZE, dtype=np.float64) + 0.5
    world_size = tile_count * TILE_SIZE
    longitudes = x_pixels / world_size * 360.0 - 180.0
    mercator_y = y_pixels / world_size
    latitudes = np.degrees(np.arctan(np.sinh(np.pi * (1.0 - 2.0 * mercator_y))))
    return longitudes, latitudes


def sample_gfs_grid(values: np.ndarray, longitudes: np.ndarray, latitudes: np.ndarray) -> np.ndarray:
    # GFS is stored north-to-south and 0..359.75 degrees east. Longitude is
    # periodic, so interpolation remains continuous across the antimeridian.
    grid_x = np.mod(longitudes, 360.0) / 0.25
    grid_y = np.clip((90.0 - latitudes) / 0.25, 0.0, EXPECTED_NJ - 1.0)

    x0 = np.floor(grid_x).astype(np.int32) % EXPECTED_NI
    x1 = (x0 + 1) % EXPECTED_NI
    y0 = np.floor(grid_y).astype(np.int32)
    y1 = np.minimum(y0 + 1, EXPECTED_NJ - 1)
    x_weight = (grid_x - np.floor(grid_x))[None, :]
    y_weight = (grid_y - np.floor(grid_y))[:, None]

    top = values[y0[:, None], x0[None, :]] * (1.0 - x_weight) + values[
        y0[:, None], x1[None, :]
    ] * x_weight
    bottom = values[y1[:, None], x0[None, :]] * (1.0 - x_weight) + values[
        y1[:, None], x1[None, :]
    ] * x_weight
    return top * (1.0 - y_weight) + bottom * y_weight


def encode_numeric_png(sampled_values: np.ndarray, output_path: Path) -> None:
    quantized = np.rint(
        (sampled_values - VALUE_OFFSET_MM) / VALUE_SCALE_MM
    ).astype(np.int64)
    if np.any(quantized < 0) or np.any(quantized >= NO_DATA_VALUE):
        raise ValueError("Quantized precipitation exceeds uint16 numeric tile range")

    encoded = quantized.astype(np.uint16)
    rgba = np.empty((TILE_SIZE, TILE_SIZE, 4), dtype=np.uint8)
    rgba[:, :, 0] = (encoded >> 8).astype(np.uint8)
    rgba[:, :, 1] = (encoded & 255).astype(np.uint8)
    rgba[:, :, 2] = 0
    rgba[:, :, 3] = 255

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(
        output_path,
        format="PNG",
        optimize=True,
        compress_level=9,
    )


def write_tile_pyramid(values: np.ndarray, timestep_directory: Path) -> tuple[int, int]:
    file_count = 0
    byte_count = 0
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        tile_count = 2**zoom
        for tile_y in range(tile_count):
            for tile_x in range(tile_count):
                longitudes, latitudes = mercator_pixel_coordinates(
                    zoom, tile_x, tile_y
                )
                sampled = sample_gfs_grid(values, longitudes, latitudes)
                path = timestep_directory / str(zoom) / str(tile_x) / f"{tile_y}.png"
                encode_numeric_png(sampled, path)
                file_count += 1
                byte_count += path.stat().st_size
    return file_count, byte_count


def source_value_at(values: np.ndarray, longitude: float, latitude: float) -> float:
    sampled = sample_gfs_grid(
        values,
        np.asarray([longitude], dtype=np.float64),
        np.asarray([latitude], dtype=np.float64),
    )
    return float(sampled[0, 0])


def exported_value_at(run_directory: Path, step_id: str, longitude: float, latitude: float) -> float:
    world_size = TILE_SIZE * 2**MAX_ZOOM
    wrapped_longitude = ((longitude + 180.0) % 360.0) - 180.0
    x = ((wrapped_longitude + 180.0) / 360.0) * world_size
    latitude = max(-WEB_MERCATOR_LIMIT, min(WEB_MERCATOR_LIMIT, latitude))
    sine = math.sin(math.radians(latitude))
    y = (0.5 - math.log((1 + sine) / (1 - sine)) / (4 * math.pi)) * world_size
    pixel_x = min(world_size - 1, max(0, int(x)))
    pixel_y = min(world_size - 1, max(0, int(y)))
    tile_x, local_x = divmod(pixel_x, TILE_SIZE)
    tile_y, local_y = divmod(pixel_y, TILE_SIZE)
    tile_path = run_directory / "tiles" / step_id / str(MAX_ZOOM) / str(tile_x) / f"{tile_y}.png"
    rgba = np.asarray(Image.open(tile_path).convert("RGBA"), dtype=np.uint8)
    encoded = int(rgba[local_y, local_x, 0]) * 256 + int(rgba[local_y, local_x, 1])
    if encoded == NO_DATA_VALUE:
        raise ValueError("Validation sample unexpectedly hit no-data")
    return encoded * VALUE_SCALE_MM + VALUE_OFFSET_MM


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_json_atomically(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        write_json(temporary_path, value)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def latest_pointer_for_manifest(manifest: dict[str, Any], run_id: str) -> dict[str, Any]:
    timesteps = manifest["timesteps"]
    return {
        "schemaVersion": 1,
        "model": manifest["model"],
        "product": manifest["product"],
        "variable": manifest["variable"]["id"],
        "runTime": manifest["runTime"],
        "generatedAt": manifest["generatedAt"],
        "firstValidTime": timesteps[0]["validTime"],
        "lastValidTime": timesteps[-1]["validTime"],
        "timestepCount": len(timesteps),
        "manifest": f"{run_id}/manifest.json",
    }


def publish_existing_run(
    output_root: Path,
    run_directory: Path,
    run_id: str,
    run_time: datetime,
    forecast_hours: list[int],
) -> bool:
    if not run_directory.exists():
        return False

    manifest_path = run_directory / "manifest.json"
    validation_path = run_directory / "validation.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        actual_hours = [step["forecastHour"] for step in manifest["timesteps"]]
        expected_tiles = len(forecast_hours) * sum(4**zoom for zoom in range(MIN_ZOOM, MAX_ZOOM + 1))
        actual_tiles = sum(1 for _ in (run_directory / "tiles").rglob("*.png"))
        if (
            manifest["runTime"] != run_time.isoformat().replace("+00:00", "Z")
            or actual_hours != forecast_hours
            or validation["summary"]["tileFileCount"] != expected_tiles
            or actual_tiles != expected_tiles
        ):
            raise ValueError("manifest, validation, or tile count does not match the requested run")
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        raise FileExistsError(
            f"Run directory exists but is not a reusable validated dataset: {run_directory}"
        ) from error

    write_json_atomically(
        output_root / "latest.json", latest_pointer_for_manifest(manifest, run_id)
    )
    print(f"Reused validated immutable run {run_id}; updated latest.json atomically.")
    return True


def main() -> None:
    args = parse_args()
    forecast_hours = parse_hours(args.hours)
    resolution = resolve_run(args, forecast_hours)
    date_value = resolution.date
    cycle = resolution.cycle
    run_time = resolution.run_time
    run_id = run_time.strftime("%Y%m%dT%HZ")
    run_directory = args.output_root / run_id
    staging_directory = args.output_root / f".{run_id}-building"

    if publish_existing_run(
        args.output_root, run_directory, run_id, run_time, forecast_hours
    ):
        return

    if staging_directory.exists():
        shutil.rmtree(staging_directory)
    staging_directory.mkdir(parents=True, exist_ok=True)

    timesteps: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    total_tile_files = 0
    total_tile_bytes = 0
    sample_locations = {
        "Snowdonia": (-4.0762, 53.0685),
        "central-US": (-97.0, 38.0),
        "Japan": (139.7, 35.7),
        "antimeridian-west": (-179.9, 0.0),
        "antimeridian-east": (179.9, 0.0),
    }
    accumulation_fields_by_start: dict[int, np.ndarray] = {}
    generation_started_at = datetime.now(timezone.utc)

    try:
        print(f"Using GFS {run_time:%Y-%m-%d %HZ}.")
        for planned_step in resolution.plan:
            forecast_hour = planned_step.forecast_hour
            step_id = f"f{forecast_hour:03d}"
            print(f"Downloading and decoding {step_id}...")
            keep_directory = staging_directory / "source" if args.keep_downloads else None
            field = load_forecast_field(
                date_value,
                cycle,
                forecast_hour,
                planned_step.records,
                keep_directory,
            )

            source_start_step = planned_step.derivation_start_step
            if source_start_step == forecast_hour - 1:
                interval_values = field.values.copy()
                derivation = (
                    f"direct {source_start_step}-{forecast_hour} hour APCP"
                )
            else:
                previous_accumulation = accumulation_fields_by_start.get(source_start_step)
                if previous_accumulation is None:
                    raise ValueError(
                        f"Missing prior {source_start_step}-{forecast_hour - 1} APCP "
                        f"needed to derive {step_id}"
                    )
                interval_values = field.values - previous_accumulation
                derivation = (
                    f"{source_start_step}-{forecast_hour} minus "
                    f"{source_start_step}-{forecast_hour - 1} hour APCP"
                )

            minimum_difference = float(np.min(interval_values))
            negative_value_count = int(np.count_nonzero(interval_values < 0))
            if minimum_difference < -PACKING_NOISE_TOLERANCE_MM:
                raise ValueError(
                    f"APCP interval derivation decreased by {minimum_difference:.3f} mm "
                    f"in {step_id}"
                )
            # GRIB packing can produce tiny subtraction noise. Clamp only that
            # numerical residue after rejecting meteorologically meaningful
            # negative differences above.
            interval_values = np.maximum(interval_values, 0.0)
            accumulation_fields_by_start[source_start_step] = field.values
            valid_time = run_time + timedelta(hours=forecast_hour)
            accumulation_start = run_time + timedelta(hours=forecast_hour - 1)
            tile_directory = staging_directory / "tiles" / step_id
            tile_files, tile_bytes = write_tile_pyramid(interval_values, tile_directory)
            total_tile_files += tile_files
            total_tile_bytes += tile_bytes

            sample_results = []
            for name, (longitude, latitude) in sample_locations.items():
                source_value = source_value_at(interval_values, longitude, latitude)
                exported_value = exported_value_at(
                    staging_directory, step_id, longitude, latitude
                )
                sample_results.append(
                    {
                        "name": name,
                        "longitude": longitude,
                        "latitude": latitude,
                        "sourceMm": round(source_value, 4),
                        "exportedMm": round(exported_value, 4),
                        "absoluteDifferenceMm": round(
                            abs(source_value - exported_value), 4
                        ),
                    }
                )

            minimum = float(np.min(interval_values))
            maximum = float(np.max(interval_values))
            validations.append(
                {
                    "id": step_id,
                    "sourceStepRange": field.metadata["stepRange"],
                    "sourceStartStep": int(field.metadata["startStep"]),
                    "sourceEndStep": int(field.metadata["endStep"]),
                    "exportedStartStep": forecast_hour - 1,
                    "exportedEndStep": forecast_hour,
                    "accumulationHours": 1,
                    "derivation": derivation,
                    "sourceUnits": field.metadata["units"],
                    "minimumMm": minimum,
                    "maximumMm": maximum,
                    "negativeValueCountBeforeClamp": negative_value_count,
                    "negativeValueCountAfterClamp": int(
                        np.count_nonzero(interval_values < 0)
                    ),
                    "preClampMinimumDifferenceMm": minimum_difference,
                    "packingNoiseToleranceMm": PACKING_NOISE_TOLERANCE_MM,
                    "duplicateInventoryRecords": field.duplicate_records,
                    "duplicateRecordsIdentical": True,
                    "samples": sample_results,
                    "tileFiles": tile_files,
                    "tileBytes": tile_bytes,
                }
            )
            timesteps.append(
                {
                    "id": step_id,
                    "forecastHour": forecast_hour,
                    "validTime": valid_time.isoformat().replace("+00:00", "Z"),
                    "accumulationStart": accumulation_start.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "accumulationEnd": valid_time.isoformat().replace("+00:00", "Z"),
                    "accumulationHours": 1,
                    "minimum": minimum,
                    "maximum": maximum,
                    "tileTemplate": f"tiles/{step_id}/{{z}}/{{x}}/{{y}}.png",
                }
            )
            print(
                f"  {minimum:.2f}..{maximum:.2f} mm; "
                f"{tile_files} tiles; {tile_bytes / 1024:.1f} KiB"
            )

        generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        manifest = {
            "schemaVersion": 1,
            "id": f"gfs-0p25-apcp-{run_id.lower()}",
            "model": "NOAA GFS",
            "product": "pgrb2.0p25",
            "runTime": run_time.isoformat().replace("+00:00", "Z"),
            "variable": {
                "id": "precipitation",
                "sourceParameter": "APCP",
                "displayName": "Total precipitation",
                "units": "mm",
                "nativeResolutionDegrees": 0.25,
                "accumulationSemantics": "interval-total",
            },
            "coverage": {
                "bounds": [-180.0, -WEB_MERCATOR_LIMIT, 180.0, WEB_MERCATOR_LIMIT],
                "worldWrap": True,
                "polarLimit": "Web Mercator clips beyond ±85.05112878° latitude.",
            },
            "tiles": {
                "format": "png",
                "encoding": "uint16-rg",
                "tileSize": TILE_SIZE,
                "minZoom": MIN_ZOOM,
                "maxZoom": MAX_ZOOM,
                "scale": VALUE_SCALE_MM,
                "offset": VALUE_OFFSET_MM,
                "noData": NO_DATA_VALUE,
                "resampling": "bilinear-from-canonical-grid",
                "overzoom": True,
            },
            "timesteps": timesteps,
            "attribution": {
                "label": "Derived from NOAA Global Forecast System (GFS)",
                "url": "https://registry.opendata.aws/noaa-gfs-bdp-pds/",
                "source": NOAA_BUCKET,
            },
            "generatedAt": generated_at,
        }
        write_json(staging_directory / "manifest.json", manifest)
        validation = {
            "run": run_id,
            "generationStartedAt": generation_started_at.isoformat().replace(
                "+00:00", "Z"
            ),
            "candidateRunsChecked": list(resolution.checked_candidates),
            "sourceGrid": {
                "columns": EXPECTED_NI,
                "rows": EXPECTED_NJ,
                "longitudeConvention": "0..359.75 degrees east",
                "latitudeOrder": "90..-90 degrees north-to-south",
                "resolutionDegrees": 0.25,
            },
            "encoding": {
                "description": "uint16 value = red * 256 + green",
                "scale": VALUE_SCALE_MM,
                "offset": VALUE_OFFSET_MM,
                "noData": NO_DATA_VALUE,
            },
            "timesteps": validations,
            "summary": {
                "timestepCount": len(timesteps),
                "tileFileCount": total_tile_files,
                "tileBytes": total_tile_bytes,
                "minimumMm": min(item["minimumMm"] for item in validations),
                "maximumMm": max(item["maximumMm"] for item in validations),
                "negativeValueCount": sum(
                    item["negativeValueCountBeforeClamp"] for item in validations
                ),
            },
        }
        write_json(staging_directory / "validation.json", validation)

        # pathlib.replace cannot move a populated directory reliably on
        # Windows. shutil.move retains the staged-write behaviour and falls
        # back to a directory copy when an atomic rename is unavailable.
        shutil.move(str(staging_directory), str(run_directory))
        latest_pointer = latest_pointer_for_manifest(manifest, run_id)
        write_json_atomically(
            args.output_root / "latest.json",
            latest_pointer,
        )
        print(
            f"Wrote {len(timesteps)} timesteps and {total_tile_files} tiles "
            f"({total_tile_bytes / 1024 / 1024:.2f} MiB) to {run_directory}"
        )
        print(f"Updated {args.output_root / 'latest.json'} atomically.")
    except Exception:
        if staging_directory.exists():
            shutil.rmtree(staging_directory)
        raise


if __name__ == "__main__":
    main()
