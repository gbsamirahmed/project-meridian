import { buildContourGeoJson } from "./contourGeometry";

import type { ContourFeatureCollection } from "./contourGeometry";
import type { WeatherGridBounds } from "../types/weatherGrid";

export function chooseTemperatureContourInterval(
  zoom: number,
  range: number
): number | null {
  if (!Number.isFinite(range) || range < 0.8) return null;
  if (zoom < 3) return range > 110 ? 20 : 10;
  if (zoom < 6) return range > 70 ? 10 : 5;
  if (zoom < 9) return range > 35 ? 5 : 2.5;
  if (zoom < 12) return range > 18 ? 5 : 2;
  return range > 12 ? 5 : 2.5;
}

export function buildTemperatureContourData(
  matrix: number[][],
  bounds: WeatherGridBounds,
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
  const interval = chooseTemperatureContourInterval(zoom, maximum - minimum);
  const levels: number[] = [];
  if (interval !== null) {
    const first = Math.ceil(minimum / interval) * interval;
    for (let level = first; level <= maximum; level += interval) {
      const normalized = Number(level.toFixed(5));
      if (normalized > minimum && normalized < maximum) levels.push(normalized);
    }
  }
  return buildContourGeoJson({
    matrix,
    bounds,
    levels,
    formatLabel: (level) =>
      `${Number.isInteger(level) ? level.toFixed(0) : level.toFixed(1)}°C`,
    isEmphasized: (level) => level === 0 || level % 10 === 0,
    upsampleFactor: 1,
  });
}
