from __future__ import annotations

import io
import math
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from PIL import Image

from evidence import geodesic_distance_m, interpret_recording_states, percentile
from models import ActivitySample, NormalizedActivity, RecordingState


TERRARIUM_ZOOM = 15
TERRARIUM_TILE_SIZE = 256
TERRARIUM_TEMPLATE = (
    "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
)
WEB_MERCATOR_LIMIT = 85.05112878
CANONICAL_SPACING_M = 10.0
LOW_SPEED_REVIEW_MPS = 0.6
LOW_SPEED_WINDOW_SECONDS = 30.0
LOW_SPEED_MIN_EFFICIENCY = 0.35


@dataclass(slots=True, frozen=True)
class MovementPoint:
    chain_id: int
    latitude: float
    longitude: float
    timestamp_s: float
    movement_elapsed_s: float
    chain_distance_m: float
    activity_distance_m: float


@dataclass(slots=True, frozen=True)
class TerrainVariant:
    id: str
    spacing_m: float
    median_radius: int
    hysteresis_m: float
    gradient_half_window_m: float = 120.0


@dataclass(slots=True)
class TerrainProfile:
    variant: TerrainVariant
    points: list[MovementPoint]
    raw_elevations_m: list[float]
    processed_elevations_m: list[float]
    gradients: list[float | None]
    raw_positive_variation_m: float
    processed_positive_variation_m: float
    ascent_after_hysteresis_m: float
    descent_after_hysteresis_m: float


TERRAIN_VARIANTS = (
    TerrainVariant("current_40m_median5_h3", 40, 2, 3),
    TerrainVariant("fixed_footprint_20m_median9_h3", 20, 4, 3),
    TerrainVariant("fixed_footprint_10m_median17_h3", 10, 8, 3),
    TerrainVariant("current_style_20m_median5_h3", 20, 2, 3),
    TerrainVariant("current_style_10m_median5_h3", 10, 2, 3),
    TerrainVariant("lighter_40m_median3_h2", 40, 1, 2, 80),
    TerrainVariant("fixed_light_20m_median5_h2", 20, 2, 2, 80),
    TerrainVariant("fixed_light_10m_median9_h2", 10, 4, 2, 80),
    TerrainVariant("smoothing_only_20m_median3_h3", 20, 1, 3, 80),
    TerrainVariant("lighter_20m_median3_h2", 20, 1, 2, 80),
    TerrainVariant("lighter_10m_median3_h2", 10, 1, 2, 80),
    TerrainVariant("lower_hysteresis_20m_median3_h1", 20, 1, 1, 80),
)


def _shortest_longitude_delta(start: float, end: float) -> float:
    return ((end - start + 540) % 360) - 180


def _interpolate_sample(
    first: ActivitySample,
    second: ActivitySample,
    fraction: float,
) -> tuple[float, float, float]:
    assert first.latitude is not None and first.longitude is not None
    assert second.latitude is not None and second.longitude is not None
    assert first.timestamp is not None and second.timestamp is not None
    latitude = first.latitude + (second.latitude - first.latitude) * fraction
    longitude = first.longitude + _shortest_longitude_delta(
        first.longitude, second.longitude
    ) * fraction
    longitude = ((longitude + 540) % 360) - 180
    timestamp_s = first.timestamp.timestamp() + (
        second.timestamp.timestamp() - first.timestamp.timestamp()
    ) * fraction
    return latitude, longitude, timestamp_s


def _low_speed_progress_is_coherent(
    samples: Sequence[ActivitySample],
    movement_indices: set[int],
    segment_index: int,
) -> bool:
    first = samples[segment_index]
    second = samples[segment_index + 1]
    if first.timestamp is None or second.timestamp is None:
        return False
    centre = (first.timestamp.timestamp() + second.timestamp.timestamp()) / 2
    start = segment_index
    end = segment_index
    while start > 0 and start - 1 in movement_indices:
        timestamp = samples[start - 1].timestamp
        if timestamp is None or centre - timestamp.timestamp() > LOW_SPEED_WINDOW_SECONDS:
            break
        start -= 1
    while end + 1 in movement_indices:
        timestamp = samples[end + 2].timestamp
        if timestamp is None or timestamp.timestamp() - centre > LOW_SPEED_WINDOW_SECONDS:
            break
        end += 1
    path_distance = 0.0
    for index in range(start, end + 1):
        left = samples[index]
        right = samples[index + 1]
        if None in (left.latitude, left.longitude, right.latitude, right.longitude):
            continue
        path_distance += geodesic_distance_m(
            left.latitude,
            left.longitude,
            right.latitude,
            right.longitude,
        )
    window_start = samples[start]
    window_end = samples[end + 1]
    if None in (
        window_start.latitude,
        window_start.longitude,
        window_end.latitude,
        window_end.longitude,
    ):
        return False
    net_distance = geodesic_distance_m(
        window_start.latitude,
        window_start.longitude,
        window_end.latitude,
        window_end.longitude,
    )
    # There is deliberately no minimum walking speed. Very slow movement remains
    # usable when it makes coherent geographic progress rather than jittering.
    return path_distance >= 3 and net_distance / max(path_distance, 1e-6) >= LOW_SPEED_MIN_EFFICIENCY


def accepted_movement_segment_indices(activity: NormalizedActivity) -> set[int]:
    evidence = interpret_recording_states(activity)
    movement = {
        segment.start_index
        for segment in evidence
        if segment.state == RecordingState.MOVEMENT
    }
    accepted: set[int] = set()
    for segment in evidence:
        if segment.state != RecordingState.MOVEMENT or segment.speed_mps is None:
            continue
        if segment.speed_mps >= LOW_SPEED_REVIEW_MPS or _low_speed_progress_is_coherent(
            activity.samples, movement, segment.start_index
        ):
            accepted.add(segment.start_index)
    return accepted


def build_movement_chains(activity: NormalizedActivity) -> list[list[ActivitySample]]:
    accepted = accepted_movement_segment_indices(activity)
    chains: list[list[ActivitySample]] = []
    current: list[ActivitySample] = []
    for index in range(max(0, len(activity.samples) - 1)):
        if index in accepted:
            if not current:
                current = [activity.samples[index]]
            current.append(activity.samples[index + 1])
        elif current:
            if len(current) >= 2:
                chains.append(current)
            current = []
    if len(current) >= 2:
        chains.append(current)
    return chains


def resample_movement_chains(
    chains: Sequence[Sequence[ActivitySample]],
    spacing_m: float = CANONICAL_SPACING_M,
) -> list[MovementPoint]:
    result: list[MovementPoint] = []
    activity_distance = 0.0
    movement_elapsed = 0.0
    for chain_id, chain in enumerate(chains):
        distances = [0.0]
        valid = True
        for first, second in zip(chain, chain[1:]):
            if None in (
                first.latitude,
                first.longitude,
                second.latitude,
                second.longitude,
                first.timestamp,
                second.timestamp,
            ):
                valid = False
                break
            distances.append(
                distances[-1]
                + geodesic_distance_m(
                    first.latitude,
                    first.longitude,
                    second.latitude,
                    second.longitude,
                )
            )
        if not valid or distances[-1] < 3:
            continue
        targets = list(np.arange(0, distances[-1], spacing_m, dtype=float))
        if not targets or distances[-1] - targets[-1] > 0.5:
            targets.append(distances[-1])
        source_index = 1
        chain_start_elapsed = movement_elapsed
        start_timestamp = chain[0].timestamp
        assert start_timestamp is not None
        for target in targets:
            while source_index < len(distances) - 1 and distances[source_index] < target:
                source_index += 1
            before_distance = distances[source_index - 1]
            after_distance = distances[source_index]
            fraction = (
                0.0
                if after_distance == before_distance
                else (target - before_distance) / (after_distance - before_distance)
            )
            latitude, longitude, timestamp_s = _interpolate_sample(
                chain[source_index - 1], chain[source_index], min(1.0, max(0.0, fraction))
            )
            result.append(
                MovementPoint(
                    chain_id,
                    latitude,
                    longitude,
                    timestamp_s,
                    chain_start_elapsed + timestamp_s - start_timestamp.timestamp(),
                    target,
                    activity_distance + target,
                )
            )
        chain_end = chain[-1].timestamp
        assert chain_end is not None
        movement_elapsed += chain_end.timestamp() - start_timestamp.timestamp()
        activity_distance += distances[-1]
    return result


def downsample_movement_points(
    points: Sequence[MovementPoint], spacing_m: float
) -> list[MovementPoint]:
    if spacing_m <= CANONICAL_SPACING_M + 0.01:
        return list(points)
    grouped: dict[int, list[MovementPoint]] = {}
    for point in points:
        grouped.setdefault(point.chain_id, []).append(point)
    result: list[MovementPoint] = []
    for chain in grouped.values():
        next_distance = 0.0
        for point in chain:
            if point.chain_distance_m + 0.01 >= next_distance:
                result.append(point)
                next_distance += spacing_m
        if result[-1] != chain[-1]:
            result.append(chain[-1])
    return result


def _median_smooth(values: Sequence[float], radius: int) -> list[float]:
    if radius <= 0:
        return list(values)
    return [
        float(np.median(values[max(0, index - radius) : index + radius + 1]))
        for index in range(len(values))
    ]


def _positive_variation(points: Sequence[MovementPoint], elevations: Sequence[float]) -> float:
    return sum(
        max(0.0, elevations[index] - elevations[index - 1])
        for index in range(1, len(points))
        if points[index].chain_id == points[index - 1].chain_id
    )


def _hysteresis_totals(
    points: Sequence[MovementPoint], elevations: Sequence[float], threshold: float
) -> tuple[float, float]:
    ascent = 0.0
    descent = 0.0
    reference: float | None = None
    chain_id: int | None = None
    for point, elevation in zip(points, elevations):
        if point.chain_id != chain_id:
            chain_id = point.chain_id
            reference = elevation
            continue
        assert reference is not None
        difference = elevation - reference
        if abs(difference) >= threshold:
            if difference > 0:
                ascent += difference
            else:
                descent -= difference
            reference = elevation
    return ascent, descent


def _gradients(
    points: Sequence[MovementPoint], elevations: Sequence[float], radius: int
) -> list[float | None]:
    result: list[float | None] = []
    for index, point in enumerate(points):
        before = max(0, index - radius)
        after = min(len(points) - 1, index + radius)
        while before < index and points[before].chain_id != point.chain_id:
            before += 1
        while after > index and points[after].chain_id != point.chain_id:
            after -= 1
        distance = points[after].chain_distance_m - points[before].chain_distance_m
        result.append(
            None if distance < 1 else (elevations[after] - elevations[before]) / distance
        )
    return result


def build_terrain_profile(
    canonical_points: Sequence[MovementPoint],
    canonical_elevations: Sequence[float],
    variant: TerrainVariant,
) -> TerrainProfile:
    if len(canonical_points) != len(canonical_elevations):
        raise ValueError("Terrain elevations do not align with movement points")
    elevation_by_point = {point: elevation for point, elevation in zip(canonical_points, canonical_elevations)}
    points = downsample_movement_points(canonical_points, variant.spacing_m)
    raw = [elevation_by_point[point] for point in points]
    processed: list[float] = []
    chain_start = 0
    for index in range(1, len(points) + 1):
        if index == len(points) or points[index].chain_id != points[chain_start].chain_id:
            processed.extend(_median_smooth(raw[chain_start:index], variant.median_radius))
            chain_start = index
    ascent, descent = _hysteresis_totals(points, processed, variant.hysteresis_m)
    radius = max(1, round(variant.gradient_half_window_m / variant.spacing_m))
    return TerrainProfile(
        variant,
        points,
        raw,
        processed,
        _gradients(points, processed, radius),
        _positive_variation(points, raw),
        _positive_variation(points, processed),
        ascent,
        descent,
    )


def profile_summary(profile: TerrainProfile) -> dict[str, float | str | int | None]:
    gradients = [value for value in profile.gradients if value is not None]
    return {
        "variant": profile.variant.id,
        "spacing_m": profile.variant.spacing_m,
        "sample_count": len(profile.points),
        "raw_positive_variation_m": profile.raw_positive_variation_m,
        "processed_positive_variation_m": profile.processed_positive_variation_m,
        "ascent_after_hysteresis_m": profile.ascent_after_hysteresis_m,
        "descent_after_hysteresis_m": profile.descent_after_hysteresis_m,
        "smoothing_removed_m": profile.raw_positive_variation_m
        - profile.processed_positive_variation_m,
        "hysteresis_removed_m": profile.processed_positive_variation_m
        - profile.ascent_after_hysteresis_m,
        "gradient_p10": percentile(gradients, 0.1),
        "gradient_median": percentile(gradients, 0.5),
        "gradient_p90": percentile(gradients, 0.9),
    }


class TerrariumTileCache:
    def __init__(
        self,
        root: Path,
        memory_tile_limit: int = 96,
        fallback_roots: Sequence[Path] = (),
    ):
        self.root = root
        self.fallback_roots = tuple(fallback_roots)
        self.memory_tile_limit = memory_tile_limit
        self.memory: OrderedDict[tuple[int, int], np.ndarray] = OrderedDict()
        self.downloaded_tiles = 0
        self.cache_hits = 0
        self.primary_cache_hits = 0
        self.fallback_cache_hits = 0
        self.downloaded_bytes = 0
        self.failed_tiles: list[str] = []

    @staticmethod
    def _world_pixel(latitude: float, longitude: float) -> tuple[float, float]:
        world_size = TERRARIUM_TILE_SIZE * (2**TERRARIUM_ZOOM)
        latitude = min(WEB_MERCATOR_LIMIT, max(-WEB_MERCATOR_LIMIT, latitude))
        sine = math.sin(math.radians(latitude))
        return (
            ((longitude + 180) / 360) * world_size,
            (0.5 - math.log((1 + sine) / (1 - sine)) / (4 * math.pi)) * world_size,
        )

    @staticmethod
    def _tile_key(pixel_x: int, pixel_y: int) -> tuple[int, int, int, int]:
        count = 2**TERRARIUM_ZOOM
        world_size = TERRARIUM_TILE_SIZE * count
        x = pixel_x % world_size
        y = min(world_size - 1, max(0, pixel_y))
        return x // TERRARIUM_TILE_SIZE, y // TERRARIUM_TILE_SIZE, x % TERRARIUM_TILE_SIZE, y % TERRARIUM_TILE_SIZE

    def required_tiles(self, points: Iterable[MovementPoint]) -> set[tuple[int, int]]:
        result: set[tuple[int, int]] = set()
        for point in points:
            pixel_x, pixel_y = self._world_pixel(point.latitude, point.longitude)
            x0, y0 = math.floor(pixel_x), math.floor(pixel_y)
            for x, y in ((x0, y0), (x0 + 1, y0), (x0, y0 + 1), (x0 + 1, y0 + 1)):
                tile_x, tile_y, _, _ = self._tile_key(x, y)
                result.add((tile_x, tile_y))
        return result

    def _path(self, tile: tuple[int, int]) -> Path:
        return self.root / str(TERRARIUM_ZOOM) / str(tile[0]) / f"{tile[1]}.png"

    @staticmethod
    def _path_under(root: Path, tile: tuple[int, int]) -> Path:
        return root / str(TERRARIUM_ZOOM) / str(tile[0]) / f"{tile[1]}.png"

    def _existing_path(self, tile: tuple[int, int]) -> Path | None:
        primary = self._path(tile)
        if primary.is_file() and primary.stat().st_size > 0:
            return primary
        for root in self.fallback_roots:
            candidate = self._path_under(root, tile)
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
        return None

    def _download(self, tile: tuple[int, int]) -> None:
        path = self._path(tile)
        existing = self._existing_path(tile)
        if existing is not None:
            self.cache_hits += 1
            if existing == path:
                self.primary_cache_hits += 1
            else:
                self.fallback_cache_hits += 1
            return
        url = TERRARIUM_TEMPLATE.format(z=TERRARIUM_ZOOM, x=tile[0], y=tile[1])
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "Meridian terrain research/1"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = response.read()
                with Image.open(io.BytesIO(payload)) as image:
                    if image.size != (TERRARIUM_TILE_SIZE, TERRARIUM_TILE_SIZE):
                        raise ValueError(f"Unexpected terrain tile dimensions {image.size}")
                    image.verify()
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(".png.tmp")
                temporary.write_bytes(payload)
                temporary.replace(path)
                self.downloaded_tiles += 1
                self.downloaded_bytes += len(payload)
                return
            except (OSError, ValueError, urllib.error.URLError) as error:
                last_error = error
                time.sleep(0.5 * (2**attempt))
        self.failed_tiles.append(f"{tile[0]}/{tile[1]}")
        raise RuntimeError(f"Unable to download terrain tile {tile[0]}/{tile[1]}") from last_error

    def prepare(self, points: Sequence[MovementPoint], concurrency: int = 6) -> int:
        tiles = sorted(self.required_tiles(points))
        self.prepare_tiles(tiles, concurrency)
        return len(tiles)

    def prepare_tiles(
        self, tiles: Iterable[tuple[int, int]], concurrency: int = 6
    ) -> int:
        ordered = sorted(set(tiles))
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
            list(executor.map(self._download, ordered))
        return len(ordered)

    def _load(self, tile: tuple[int, int]) -> np.ndarray:
        cached = self.memory.get(tile)
        if cached is not None:
            self.memory.move_to_end(tile)
            return cached
        path = self._existing_path(tile)
        if path is None:
            raise FileNotFoundError(f"Terrain tile {tile[0]}/{tile[1]} is not prepared")
        with Image.open(path) as image:
            data = np.asarray(image.convert("RGB"), dtype=np.float64)
        self.memory[tile] = data
        while len(self.memory) > self.memory_tile_limit:
            self.memory.popitem(last=False)
        return data

    def _pixel_elevation(self, pixel_x: int, pixel_y: int) -> float:
        tile_x, tile_y, local_x, local_y = self._tile_key(pixel_x, pixel_y)
        pixel = self._load((tile_x, tile_y))[local_y, local_x]
        return float(pixel[0] * 256 + pixel[1] + pixel[2] / 256 - 32768)

    def sample(self, points: Sequence[MovementPoint]) -> list[float]:
        result: list[float] = []
        for point in points:
            pixel_x, pixel_y = self._world_pixel(point.latitude, point.longitude)
            x0, y0 = math.floor(pixel_x), math.floor(pixel_y)
            fraction_x, fraction_y = pixel_x - x0, pixel_y - y0
            top_left = self._pixel_elevation(x0, y0)
            top_right = self._pixel_elevation(x0 + 1, y0)
            bottom_left = self._pixel_elevation(x0, y0 + 1)
            bottom_right = self._pixel_elevation(x0 + 1, y0 + 1)
            top = top_left * (1 - fraction_x) + top_right * fraction_x
            bottom = bottom_left * (1 - fraction_x) + bottom_right * fraction_x
            result.append(top * (1 - fraction_y) + bottom * fraction_y)
        return result
