import type { GridPoint } from "../types/gridPoint";

export function getGridCoordinates(
  latitude: number,
  longitude: number,
  gridPoints: GridPoint[]
): {
  x: number;
  y: number;
} | null {
  if (gridPoints.length === 0) {
    return null;
  }

  const longitudes = gridPoints.map(
    (point) => point.longitude
  );

  const latitudes = gridPoints.map(
    (point) => point.latitude
  );

  const west = Math.min(...longitudes);
  const east = Math.max(...longitudes);

  const south = Math.min(...latitudes);
  const north = Math.max(...latitudes);

  const xRatio =
    (longitude - west) /
    (east - west);

  const yRatio =
    (north - latitude) /
    (north - south);

  return {
    x: xRatio,
    y: yRatio,
  };
}