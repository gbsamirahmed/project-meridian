import { generateGrid } from "./gridService";

import type { SelectedLocation } from "../types/location";
import type { GridPoint } from "../types/gridPoint";

export async function getWeatherGrid(
  center: SelectedLocation
): Promise<GridPoint[]> {
  console.log("Fetching weather grid...");

  const points = generateGrid(center);

  const latitudes = points
    .map((point) => point.latitude)
    .join(",");

  const longitudes = points
    .map((point) => point.longitude)
    .join(",");

  const weatherResponse = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitudes}&longitude=${longitudes}&hourly=temperature_2m,cloud_cover,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m&forecast_hours=25`
  );

  if (!weatherResponse.ok) {
    throw new Error(
      `Weather grid API error: ${weatherResponse.status}`
    );
  }

  const elevationResponse = await fetch(
    `https://api.open-meteo.com/v1/elevation?latitude=${latitudes}&longitude=${longitudes}`
  );

  if (!elevationResponse.ok) {
    throw new Error(
      `Elevation API error: ${elevationResponse.status}`
    );
  }

  const weatherData = await weatherResponse.json();
  const elevationData = await elevationResponse.json();

  if (!Array.isArray(weatherData)) {
    throw new Error("Expected weather grid API response to be an array");
  }

  if (!Array.isArray(elevationData.elevation)) {
    throw new Error("Expected elevation API response to include elevation array");
  }

  return weatherData.map((locationData, index) => ({
    latitude: points[index].latitude,
    longitude: points[index].longitude,
    elevation: elevationData.elevation[index],

    temperature: locationData.hourly.temperature_2m,
    cloudCover: locationData.hourly.cloud_cover,
    precipitation: locationData.hourly.precipitation,
    pressure: locationData.hourly.pressure_msl,

    windSpeed: locationData.hourly.wind_speed_10m,
    windDirection: locationData.hourly.wind_direction_10m,
  }));
}