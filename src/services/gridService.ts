import { GRID_RADIUS, GRID_SPACING } from "../config/gridConfig";

import type { SelectedLocation } from "../types/location";

export function generateGrid(
  center: SelectedLocation
): SelectedLocation[] {
  const points: SelectedLocation[] = [];

  for (let latOffset = -GRID_RADIUS; latOffset <= GRID_RADIUS; latOffset++) {
    for (let lonOffset = -GRID_RADIUS; lonOffset <= GRID_RADIUS; lonOffset++) {
      points.push({
        latitude: center.latitude + latOffset * GRID_SPACING,
        longitude: center.longitude + lonOffset * GRID_SPACING,
      });
    }
  }

  return points;
}