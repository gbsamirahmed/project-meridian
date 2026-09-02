from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


EARTH_RADIUS_M = 6_371_008.8
MAX_ROUTE_SAMPLES = 100_000
CONTIGUOUS_SEGMENT_GAP_M = 500.0


@dataclass(slots=True, frozen=True)
class RouteCoordinate:
    latitude: float
    longitude: float


@dataclass(slots=True, frozen=True)
class RouteGeometry:
    name: str
    coordinates: tuple[RouteCoordinate, ...]
    cumulative_distances_m: tuple[float, ...]
    total_distance_m: float


def shortest_longitude_delta(start: float, end: float) -> float:
    return ((end - start + 540.0) % 360.0) - 180.0


def geodesic_distance_m(first: RouteCoordinate, second: RouteCoordinate) -> float:
    latitude_1 = math.radians(first.latitude)
    latitude_2 = math.radians(second.latitude)
    latitude_delta = latitude_2 - latitude_1
    longitude_delta = math.radians(
        shortest_longitude_delta(first.longitude, second.longitude)
    )
    haversine = (
        math.sin(latitude_delta / 2.0) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(longitude_delta / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(haversine)))


def _valid_coordinate(element: ET.Element) -> RouteCoordinate | None:
    try:
        latitude = float(element.attrib["lat"])
        longitude = float(element.attrib["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        return None
    return RouteCoordinate(latitude, longitude)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _length(coordinates: Sequence[RouteCoordinate]) -> float:
    return sum(
        geodesic_distance_m(first, second)
        for first, second in zip(coordinates, coordinates[1:])
    )


def _choose_coordinates(root: ET.Element) -> list[RouteCoordinate]:
    segments: list[list[RouteCoordinate]] = []
    routes: list[list[RouteCoordinate]] = []
    for element in root.iter():
        name = _local_name(element.tag)
        if name not in {"trkseg", "rte"}:
            continue
        point_name = "trkpt" if name == "trkseg" else "rtept"
        points = [
            point
            for child in element.iter()
            if _local_name(child.tag) == point_name
            for point in [_valid_coordinate(child)]
            if point is not None
        ]
        if len(points) >= 2:
            (segments if name == "trkseg" else routes).append(points)

    chains: list[list[RouteCoordinate]] = []
    for segment in segments:
        if (
            chains
            and geodesic_distance_m(chains[-1][-1], segment[0])
            <= CONTIGUOUS_SEGMENT_GAP_M
        ):
            chains[-1].extend(
                segment[1:]
                if geodesic_distance_m(chains[-1][-1], segment[0]) < 0.5
                else segment
            )
        else:
            chains.append(list(segment))
    candidates = chains + routes
    if not candidates:
        raise ValueError("GPX does not contain a usable track or route")
    return max(candidates, key=_length)


def parse_gpx_geometry(path: Path) -> RouteGeometry:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        raise ValueError(f"Unable to parse GPX geometry: {path.name}") from error
    coordinates = _choose_coordinates(root)
    distances = [0.0]
    for first, second in zip(coordinates, coordinates[1:]):
        distances.append(distances[-1] + geodesic_distance_m(first, second))
    if distances[-1] < 10.0:
        raise ValueError("Route is too short for terrain analysis")
    name = path.stem
    for element in root.iter():
        if _local_name(element.tag) == "name" and element.text and element.text.strip():
            name = element.text.strip()
            break
    return RouteGeometry(name, tuple(coordinates), tuple(distances), distances[-1])


def _interpolate(
    first: RouteCoordinate, second: RouteCoordinate, fraction: float
) -> RouteCoordinate:
    longitude = first.longitude + shortest_longitude_delta(
        first.longitude, second.longitude
    ) * fraction
    longitude = ((longitude + 540.0) % 360.0) - 180.0
    return RouteCoordinate(
        first.latitude + (second.latitude - first.latitude) * fraction,
        longitude,
    )


def resample_route(route: RouteGeometry, spacing_m: float) -> RouteGeometry:
    if not math.isfinite(spacing_m) or spacing_m <= 0:
        raise ValueError("Route sampling interval must be positive")
    target_count = math.ceil(route.total_distance_m / spacing_m) + 1
    if target_count > MAX_ROUTE_SAMPLES:
        raise ValueError(
            f"Route would exceed the explicit {MAX_ROUTE_SAMPLES:,}-sample limit"
        )
    targets = [index * spacing_m for index in range(target_count - 1)]
    if not targets or route.total_distance_m - targets[-1] > 0.01:
        targets.append(route.total_distance_m)
    else:
        targets[-1] = route.total_distance_m
    result: list[RouteCoordinate] = []
    source_index = 1
    for target in targets:
        while (
            source_index < len(route.cumulative_distances_m) - 1
            and route.cumulative_distances_m[source_index] < target
        ):
            source_index += 1
        before = route.cumulative_distances_m[source_index - 1]
        after = route.cumulative_distances_m[source_index]
        fraction = 0.0 if after == before else (target - before) / (after - before)
        result.append(
            _interpolate(
                route.coordinates[source_index - 1],
                route.coordinates[source_index],
                min(1.0, max(0.0, fraction)),
            )
        )
    return RouteGeometry(route.name, tuple(result), tuple(targets), route.total_distance_m)
