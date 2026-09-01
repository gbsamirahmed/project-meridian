import { generateGrid } from "./gridService";
import {
  WEATHER_GRID_CACHE_MAX_AGE_MS,
  WEATHER_GRID_CACHE_SIZE,
} from "../config/gridConfig";

import type { GridPoint } from "../types/gridPoint";
import type {
  WeatherGrid,
  WeatherGridRequest,
} from "../types/weatherGrid";

interface OpenMeteoGridResponse {
  hourly?: {
    time?: string[];
    temperature_2m?: number[];
    pressure_msl?: number[];
  };
}

interface CachedWeatherGrid {
  grid: WeatherGrid;
  lastUsedAt: number;
}

export class WeatherGridHttpError extends Error {
  readonly status: number;
  readonly retryAfterMs: number | null;

  constructor(status: number, retryAfterMs: number | null) {
    super(`Weather grid API error: ${status}`);
    this.name = "WeatherGridHttpError";
    this.status = status;
    this.retryAfterMs = retryAfterMs;
  }
}

const gridCache = new Map<string, CachedWeatherGrid>();

function roundCoordinate(value: number): string {
  return value.toFixed(4);
}

export function getWeatherGridRequestKey(
  request: WeatherGridRequest
): string {
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

function parseRetryAfter(value: string | null): number | null {
  if (!value) return null;

  const seconds = Number(value);

  if (Number.isFinite(seconds)) {
    return Math.max(0, seconds * 1000);
  }

  const retryAt = Date.parse(value);
  return Number.isFinite(retryAt)
    ? Math.max(0, retryAt - Date.now())
    : null;
}

function isFresh(entry: CachedWeatherGrid, now: number): boolean {
  return now - entry.grid.fetchedAt <= WEATHER_GRID_CACHE_MAX_AGE_MS;
}

function safelyCoversViewport(
  grid: WeatherGrid,
  request: WeatherGridRequest
): boolean {
  const longitudeInset = (grid.bounds.east - grid.bounds.west) * 0.12;
  const latitudeInset = (grid.bounds.north - grid.bounds.south) * 0.12;
  const viewport = request.viewportBounds;

  return (
    viewport.west >= grid.bounds.west + longitudeInset &&
    viewport.east <= grid.bounds.east - longitudeInset &&
    viewport.south >= grid.bounds.south + latitudeInset &&
    viewport.north <= grid.bounds.north - latitudeInset
  );
}

function readReusableGrid(request: WeatherGridRequest): WeatherGrid | null {
  const now = Date.now();
  const requestKey = getWeatherGridRequestKey(request);
  const exact = gridCache.get(requestKey);

  if (exact && isFresh(exact, now)) {
    exact.lastUsedAt = now;
    gridCache.delete(requestKey);
    gridCache.set(requestKey, exact);
    return exact.grid;
  }

  let best: { key: string; entry: CachedWeatherGrid; area: number } | null =
    null;

  for (const [key, entry] of gridCache) {
    if (!isFresh(entry, now)) {
      gridCache.delete(key);
      continue;
    }

    if (
      entry.grid.rows !== request.rows ||
      entry.grid.columns !== request.columns
    ) {
      continue;
    }

    if (!safelyCoversViewport(entry.grid, request)) continue;

    const area =
      (entry.grid.bounds.east - entry.grid.bounds.west) *
      (entry.grid.bounds.north - entry.grid.bounds.south);

    if (!best || area < best.area) best = { key, entry, area };
  }

  if (!best) return null;

  best.entry.lastUsedAt = now;
  gridCache.delete(best.key);
  gridCache.set(best.key, best.entry);
  return best.entry.grid;
}

function readHourlyValues(
  response: OpenMeteoGridResponse,
  pointIndex: number
): Omit<GridPoint, "latitude" | "longitude"> {
  const hourly = response.hourly;

  if (
    !hourly?.time ||
    !hourly.temperature_2m ||
    !hourly.pressure_msl
  ) {
    throw new Error(
      `Weather grid response ${pointIndex + 1} is missing hourly data`
    );
  }

  return {
    temperature: hourly.temperature_2m,
    pressure: hourly.pressure_msl,
  };
}

export async function getWeatherGrid(
  request: WeatherGridRequest,
  signal?: AbortSignal
): Promise<WeatherGrid> {
  const cacheKey = getWeatherGridRequestKey(request);
  const cachedGrid = readReusableGrid(request);

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
    `https://api.open-meteo.com/v1/forecast?latitude=${latitudes}&longitude=${longitudes}&hourly=temperature_2m,pressure_msl&forecast_hours=25`,
    { signal }
  );

  if (!weatherResponse.ok) {
    throw new WeatherGridHttpError(
      weatherResponse.status,
      parseRetryAfter(weatherResponse.headers.get("Retry-After"))
    );
  }

  const weatherData: unknown = await weatherResponse.json();

  if (!Array.isArray(weatherData) || weatherData.length !== points.length) {
    throw new Error("Expected weather grid API response to be an array");
  }

  const grid: WeatherGrid = {
    bounds: request.bounds,
    rows: request.rows,
    columns: request.columns,
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

  gridCache.set(cacheKey, { grid, lastUsedAt: Date.now() });

  while (gridCache.size > WEATHER_GRID_CACHE_SIZE) {
    const oldestKey = gridCache.keys().next().value;

    if (oldestKey === undefined) break;
    gridCache.delete(oldestKey);
  }

  return grid;
}
