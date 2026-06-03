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
        `https://api.open-meteo.com/v1/forecast?latitude=${point.latitude}&longitude=${point.longitude}&hourly=temperature_2m,cloud_cover,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m&forecast_hours=25`
      );

      const data = await response.json();

      return {
        latitude: point.latitude,
        longitude: point.longitude,

        temperature: data.hourly.temperature_2m,
        cloudCover: data.hourly.cloud_cover,
        precipitation: data.hourly.precipitation,
        pressure: data.hourly.pressure_msl,

        windSpeed: data.hourly.wind_speed_10m,
        windDirection: data.hourly.wind_direction_10m,
      };
    })
  );

  return gridPoints;
}