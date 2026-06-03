import type { SelectedLocation } from "../types/location";

export function generateGrid(
  center: SelectedLocation,
  spacing: number = 0.15
): SelectedLocation[] {
  const points: SelectedLocation[] = [];

  for (let latOffset = -4; latOffset <= 4; latOffset++) {
    for (let lonOffset = -4; lonOffset <= 4; lonOffset++) {
      points.push({
        latitude: center.latitude + latOffset * spacing,
        longitude: center.longitude + lonOffset * spacing,
      });
    }
  }

  return points;
}