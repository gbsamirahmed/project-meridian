import type { SelectedLocation } from "../types/location";

export function generateGrid(
  center: SelectedLocation,
  spacing: number = 0.15
): SelectedLocation[] {
  const points: SelectedLocation[] = [];

  for (let latOffset = -2; latOffset <= 2; latOffset++) {
    for (let lonOffset = -2; lonOffset <= 2; lonOffset++) {
      points.push({
        latitude: center.latitude + latOffset * spacing,
        longitude: center.longitude + lonOffset * spacing,
      });
    }
  }

  return points;
}