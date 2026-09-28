"""Small deterministic helpers for categorical Earth Lab evidence."""
from __future__ import annotations

from collections import Counter
import math
import re
from typing import Any

import numpy as np


def _clip_ring_to_edge(points, inside, intersect):
    if not points:
        return []
    output = []
    previous = points[-1]
    for current in points:
        if inside(current):
            if not inside(previous):
                output.append(intersect(previous, current))
            output.append(current)
        elif inside(previous):
            output.append(intersect(previous, current))
        previous = current
    return output


def clip_ring_to_bounds(ring: list[list[float]], bounds: tuple[float, float, float, float]) -> list[list[float]]:
    west, south, east, north = bounds
    points = [[float(point[0]), float(point[1])] for point in ring]
    if points and points[0] == points[-1]:
        points = points[:-1]
    def vertical(x):
        return lambda a, b: [x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])]
    def horizontal(y):
        return lambda a, b: [a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y]
    points = _clip_ring_to_edge(points, lambda p: p[0] >= west, vertical(west))
    points = _clip_ring_to_edge(points, lambda p: p[0] <= east, vertical(east))
    points = _clip_ring_to_edge(points, lambda p: p[1] >= south, horizontal(south))
    points = _clip_ring_to_edge(points, lambda p: p[1] <= north, horizontal(north))
    if len(points) < 3:
        return []
    return points + [points[0]]


def clip_geometry_to_bounds(geometry: dict[str, Any], bounds: tuple[float, float, float, float]) -> dict[str, Any] | None:
    geometry_type = geometry.get("type")
    polygons = [geometry.get("coordinates", [])] if geometry_type == "Polygon" else geometry.get("coordinates", []) if geometry_type == "MultiPolygon" else []
    clipped_polygons = []
    for polygon in polygons:
        rings = [clip_ring_to_bounds(ring, bounds) for ring in polygon]
        rings = [ring for ring in rings if ring]
        if rings:
            clipped_polygons.append(rings)
    if not clipped_polygons:
        return None
    if geometry_type == "Polygon" and len(clipped_polygons) == 1:
        return {"type": "Polygon", "coordinates": clipped_polygons[0]}
    return {"type": "MultiPolygon", "coordinates": clipped_polygons}


def parse_mosaic_components(label: str) -> dict[str, float]:
    """Parse NRW labels such as ``Mosaic of:50% B.1.1,50% E.2.1``."""
    if not label or "mosaic" not in label.lower():
        return {}
    pairs = re.findall(r"([0-9]+(?:\.[0-9]+)?)%\s*([A-Z][A-Z0-9.]+)", label)
    return {code: float(percent) / 100.0 for percent, code in pairs}


def habitat_group(code: str | None, label: str, mapping: dict[str, str]) -> str:
    """Return a documented broad group without replacing the source category."""
    components = parse_mosaic_components(label)
    if components:
        grouped: Counter[str] = Counter()
        for component, weight in components.items():
            grouped[mapping.get(component, "other_or_unknown")] += weight
        if not grouped:
            return "other_or_unknown"
        top = grouped.most_common()
        if len(top) > 1 and math.isclose(top[0][1], top[1][1], abs_tol=1e-9):
            return "mixed_mosaic"
        return top[0][0]
    return mapping.get(code or "", "other_or_unknown")


def categorical_summary(values: np.ndarray, lookup: dict[int, str], cell_area_m2: float) -> dict[str, Any]:
    array = np.asarray(values)
    total = int(array.size)
    counts = {int(k): int(v) for k, v in zip(*np.unique(array, return_counts=True))}
    categories = []
    for identifier, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        categories.append({
            "id": identifier,
            "name": lookup.get(identifier, "unknown"),
            "cells": count,
            "area_km2": count * float(cell_area_m2) / 1_000_000.0,
            "fraction": count / total if total else 0.0,
        })
    mapped = total - counts.get(0, 0)
    return {
        "total_cells": total,
        "mapped_cells": mapped,
        "coverage_fraction": mapped / total if total else 0.0,
        "categories": categories,
    }


def category_numeric_summary(categories: np.ndarray, fields: dict[str, np.ndarray], lookup: dict[int, str]) -> list[dict[str, Any]]:
    cat = np.asarray(categories)
    rows = []
    for identifier in sorted(int(v) for v in np.unique(cat) if int(v) != 0):
        mask = cat == identifier
        row: dict[str, Any] = {"id": identifier, "name": lookup.get(identifier, "unknown"), "cells": int(mask.sum())}
        for field_name, field in fields.items():
            selected = np.asarray(field, dtype=np.float64)[mask]
            selected = selected[np.isfinite(selected)]
            row[field_name] = None if not selected.size else {
                "mean": float(np.mean(selected)),
                "median": float(np.median(selected)),
                "p10": float(np.percentile(selected, 10)),
                "p90": float(np.percentile(selected, 90)),
            }
        rows.append(row)
    return rows


def binary_overlap(left: np.ndarray, right: np.ndarray, valid: np.ndarray | None = None) -> dict[str, Any]:
    a = np.asarray(left, dtype=bool)
    b = np.asarray(right, dtype=bool)
    use = np.ones(a.shape, dtype=bool) if valid is None else np.asarray(valid, dtype=bool)
    intersection = int(np.count_nonzero(a & b & use))
    union = int(np.count_nonzero((a | b) & use))
    left_count = int(np.count_nonzero(a & use))
    right_count = int(np.count_nonzero(b & use))
    return {
        "valid_cells": int(np.count_nonzero(use)),
        "intersection_cells": intersection,
        "union_cells": union,
        "jaccard": intersection / union if union else None,
        "right_given_left": intersection / left_count if left_count else None,
        "left_given_right": intersection / right_count if right_count else None,
    }


def mode_reduce_2x2(values: np.ndarray, nodata: int = 0) -> np.ndarray:
    """Reduce a categorical raster without interpolating identifiers."""
    array = np.asarray(values)
    if array.shape[0] % 2 or array.shape[1] % 2:
        raise ValueError("Categorical grid dimensions must be divisible by two")
    blocks = array.reshape(array.shape[0] // 2, 2, array.shape[1] // 2, 2).transpose(0, 2, 1, 3).reshape(array.shape[0] // 2, array.shape[1] // 2, 4)
    output = np.full(blocks.shape[:2], nodata, dtype=array.dtype)
    for row in range(output.shape[0]):
        for column in range(output.shape[1]):
            sample = blocks[row, column]
            usable = sample[sample != nodata]
            if usable.size:
                identifiers, counts = np.unique(usable, return_counts=True)
                output[row, column] = identifiers[np.argmax(counts)]
    return output


def nearest_palette_indices(rgba: np.ndarray, palette: list[dict[str, Any]], tolerance: float) -> np.ndarray:
    """Classify a rendered categorical WMS by published feature colours."""
    image = np.asarray(rgba, dtype=np.uint8)
    if image.ndim != 3 or image.shape[2] != 4:
        raise ValueError("Expected an RGBA image")
    result = np.zeros(image.shape[:2], dtype=np.uint16)
    if not palette:
        return result
    colours = np.asarray([entry["rgb"] for entry in palette], dtype=np.float32)
    identifiers = np.asarray([entry["id"] for entry in palette], dtype=np.uint16)
    opaque = image[..., 3] > 0
    pixels = image[..., :3].astype(np.float32)
    distances = np.linalg.norm(pixels[..., None, :] - colours[None, None, :, :], axis=-1)
    nearest = np.argmin(distances, axis=-1)
    accepted = opaque & (np.take_along_axis(distances, nearest[..., None], axis=-1)[..., 0] <= float(tolerance))
    result[accepted] = identifiers[nearest[accepted]]
    return result
