import { getGridCoordinates } from "./gridCoordinates";

import type { GridPoint } from "../types/gridPoint";
import type { WeatherGrid } from "../types/weatherGrid";

export interface InterpolatedWeather {
  temperature: number;
  pressure: number;
}

export interface MutableWindVector {
  eastwardFlow: number;
  northwardFlow: number;
  speed: number;
  flowBearing: number;
  fromDirection: number;
}

interface CellSample {
  point: GridPoint;
  weight: number;
}

function getCellSamples(
  grid: WeatherGrid,
  latitude: number,
  longitude: number
): CellSample[] | null {
  const coordinates = getGridCoordinates(latitude, longitude, grid.bounds);

  if (
    !coordinates ||
    coordinates.x < 0 ||
    coordinates.x > 1 ||
    coordinates.y < 0 ||
    coordinates.y > 1
  ) {
    return null;
  }

  const gridX = coordinates.x * (grid.columns - 1);
  const gridY = coordinates.y * (grid.rows - 1);
  const x0 = Math.floor(gridX);
  const y0 = Math.floor(gridY);
  const x1 = Math.min(x0 + 1, grid.columns - 1);
  const y1 = Math.min(y0 + 1, grid.rows - 1);
  const dx = gridX - x0;
  const dy = gridY - y0;

  return [
    { point: grid.points[y0 * grid.columns + x0], weight: (1 - dx) * (1 - dy) },
    { point: grid.points[y0 * grid.columns + x1], weight: dx * (1 - dy) },
    { point: grid.points[y1 * grid.columns + x1], weight: dx * dy },
    { point: grid.points[y1 * grid.columns + x0], weight: (1 - dx) * dy },
  ];
}

function interpolateScalar(
  samples: CellSample[],
  forecastHour: number,
  selector: (point: GridPoint, hour: number) => number
): number {
  return samples.reduce(
    (total, sample) =>
      total + selector(sample.point, forecastHour) * sample.weight,
    0
  );
}

export function interpolateWeatherAtLocation(
  grid: WeatherGrid,
  forecastHour: number,
  latitude: number,
  longitude: number
): InterpolatedWeather | null {
  const samples = getCellSamples(grid, latitude, longitude);

  if (!samples) return null;

  const result: InterpolatedWeather = {
    temperature: interpolateScalar(
      samples,
      forecastHour,
      (point, hour) => point.temperature[hour]
    ),
    pressure: interpolateScalar(
      samples,
      forecastHour,
      (point, hour) => point.pressure[hour]
    ),
  };

  return Object.values(result).every(Number.isFinite) ? result : null;
}

export function formatWindDirection(direction: number): string {
  const names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(((direction % 360) + 360) / 45) % names.length;

  return `${names[index]} (${Math.round(direction)}° from)`;
}
