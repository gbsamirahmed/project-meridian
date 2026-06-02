import { generateGrid } from "./gridService";

import type { SelectedLocation } from "../types/location";
import type { GridPoint } from "../types/gridPoint";

export async function getTemperatureGrid(
  center: SelectedLocation
): Promise<GridPoint[]> {
  const points = generateGrid(center);

  const gridPoints = await Promise.all(
    points.map(async (point) => {
      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${point.latitude}&longitude=${point.longitude}&current=temperature_2m`
      );

      const data = await response.json();

      return {
        latitude: point.latitude,
        longitude: point.longitude,
        temperature: data.current.temperature_2m,
      };
    })
  );

  return gridPoints;
}