import { generateGrid } from "./gridService";
import { WEATHER_GRID_CACHE_SIZE } from "../config/gridConfig";

import type { GridPoint } from "../types/gridPoint";
import type {
  WeatherGrid,
  WeatherGridRequest,
} from "../types/weatherGrid";

interface OpenMeteoGridResponse {
  hourly?: {
    time?: string[];
    temperature_2m?: number[];
    cloud_cover?: number[];
    precipitation?: number[];
    pressure_msl?: number[];
    wind_speed_10m?: number[];
    wind_direction_10m?: number[];
  };
}

const gridCache = new Map<string, WeatherGrid>();

function roundCoordinate(value: number): string {
  return value.toFixed(4);
}

function getCacheKey(request: WeatherGridRequest): string {
  const { bounds, rows, columns } = request;

  return [
    roundCoordinate(bounds.west),
    roundCoordinate(bounds.south),
    roundCoordinate(bounds.east),
    roundCoordinate(bounds.north),
    rows,
    columns,
  ].join(":");
}

function readHourlyValues(
  response: OpenMeteoGridResponse,
  pointIndex: number
): Omit<GridPoint, "latitude" | "longitude"> {
  const hourly = response.hourly;

  if (
    !hourly?.time ||
    !hourly.temperature_2m ||
    !hourly.cloud_cover ||
    !hourly.precipitation ||
    !hourly.pressure_msl ||
    !hourly.wind_speed_10m ||
    !hourly.wind_direction_10m
  ) {
    throw new Error(
      `Weather grid response ${pointIndex + 1} is missing hourly data`
    );
  }

  return {
    temperature: hourly.temperature_2m,
    cloudCover: hourly.cloud_cover,
    precipitation: hourly.precipitation,
    pressure: hourly.pressure_msl,
    windSpeed: hourly.wind_speed_10m,
    windDirection: hourly.wind_direction_10m,
  };
}

export async function getWeatherGrid(
  request: WeatherGridRequest,
  signal?: AbortSignal
): Promise<WeatherGrid> {
  const cacheKey = getCacheKey(request);
  const cachedGrid = gridCache.get(cacheKey);

  if (cachedGrid) {
    return cachedGrid;
  }

  const points = generateGrid(request);

  const latitudes = points
    .map((point) => roundCoordinate(point.latitude))
    .join(",");

  const longitudes = points
    .map((point) => roundCoordinate(point.longitude))
    .join(",");

  const weatherResponse = await fetch(
    `https://api.open-meteo.com/v1/forecast?latitude=${latitudes}&longitude=${longitudes}&hourly=temperature_2m,cloud_cover,precipitation,pressure_msl,wind_speed_10m,wind_direction_10m&forecast_hours=25`,
    { signal }
  );

  if (!weatherResponse.ok) {
    throw new Error(
      `Weather grid API error: ${weatherResponse.status}`
    );
  }

  const weatherData: unknown = await weatherResponse.json();

  if (!Array.isArray(weatherData) || weatherData.length !== points.length) {
    throw new Error("Expected weather grid API response to be an array");
  }

  const grid: WeatherGrid = {
    ...request,
    times: (weatherData[0] as OpenMeteoGridResponse).hourly?.time ?? [],
    points: weatherData.map((locationData, index) => ({
      latitude: points[index].latitude,
      longitude: points[index].longitude,
      ...readHourlyValues(
        locationData as OpenMeteoGridResponse,
        index
      ),
    })),
    fetchedAt: Date.now(),
  };

  gridCache.set(cacheKey, grid);

  while (gridCache.size > WEATHER_GRID_CACHE_SIZE) {
    const oldestKey = gridCache.keys().next().value;

    if (oldestKey === undefined) break;
    gridCache.delete(oldestKey);
  }

  return grid;
}
