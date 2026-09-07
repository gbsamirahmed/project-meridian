import { buildContourGeoJson } from "./contourGeometry";

import type { ContourFeatureCollection } from "./contourGeometry";
import type { GeographicBounds } from "../types/globalWeather";

export function choosePressureContourInterval(
  zoom: number,
  range: number
): number | null {
  if (!Number.isFinite(range) || range < 0.9) return null;
  if (zoom < 3) return 8;
  if (zoom < 8) return 4;
  return range < 8 ? 2 : 4;
}

export function buildPressureContourData(
  matrix: number[][],
  bounds: GeographicBounds,
  zoom: number
): ContourFeatureCollection {
  const values = matrix.flat().filter(Number.isFinite);
  if (values.length === 0) {
    return buildContourGeoJson({
      matrix,
      bounds,
      levels: [],
      formatLabel: String,
      upsampleFactor: 1,
    });
  }
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const interval = choosePressureContourInterval(zoom, maximum - minimum);
  const levels: number[] = [];
  if (interval !== null) {
    const first = Math.ceil(minimum / interval) * interval;
    for (let level = first; level <= maximum; level += interval) {
      const normalized = Number(level.toFixed(1));
      if (normalized > minimum && normalized < maximum) levels.push(normalized);
    }
  }
  return buildContourGeoJson({
    matrix,
    bounds,
    levels,
    formatLabel: (level) => `${Number.isInteger(level) ? level.toFixed(0) : level.toFixed(1)} hPa`,
    isEmphasized: (level) => level % 8 === 0,
    upsampleFactor: 1,
  });
}
