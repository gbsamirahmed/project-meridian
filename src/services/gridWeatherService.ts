import { generateGrid } from "./gridService";

import type { SelectedLocation } from "../types/location";
import type { GridPoint } from "../types/gridPoint";

export async function getWeatherGrid(
  center: SelectedLocation
): Promise<GridPoint[]> {
  console.log("Fetching weather grid...");

  const points = generateGrid(center);

  const gridPoints = await Promise.all(
    points.map(async (point) => {
      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${point.latitude}&longitude=${point.longitude}&current=temperature_2m,cloud_cover,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m`
      );

      const data = await response.json();

      return {
        latitude: point.latitude,
        longitude: point.longitude,

        temperature: data.current.temperature_2m,
        cloudCover: data.current.cloud_cover,
        precipitation: data.current.precipitation,
        pressure: data.current.pressure_msl,

        windSpeed: data.current.wind_speed_10m,
        windDirection: data.current.wind_direction_10m,
      };
    })
  );

  return gridPoints;
}