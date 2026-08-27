import type { WeatherGridBounds } from "../types/weatherGrid";

export function getGridCoordinates(
  latitude: number,
  longitude: number,
  bounds: WeatherGridBounds
): {
  x: number;
  y: number;
} | null {
  if (
    bounds.east === bounds.west ||
    bounds.north === bounds.south
  ) {
    return null;
  }

  const xRatio =
    (longitude - bounds.west) /
    (bounds.east - bounds.west);

  const yRatio =
    (bounds.north - latitude) /
    (bounds.north - bounds.south);

  return {
    x: xRatio,
    y: yRatio,
  };
}
