import { getGridCoordinates } from "./gridCoordinates";

import type { GridPoint } from "../types/gridPoint";
import type { WeatherGrid } from "../types/weatherGrid";

export interface InterpolatedWeather {
  temperature: number;
  cloudCover: number;
  precipitation: number;
  pressure: number;
  windSpeed: number;
  windDirection: number;
  windFlowBearing: number;
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

  const wind = sampleWindVectorFromSamples(samples, forecastHour);
  const result: InterpolatedWeather = {
    temperature: interpolateScalar(
      samples,
      forecastHour,
      (point, hour) => point.temperature[hour]
    ),
    cloudCover: interpolateScalar(
      samples,
      forecastHour,
      (point, hour) => point.cloudCover[hour]
    ),
    precipitation: interpolateScalar(
      samples,
      forecastHour,
      (point, hour) => point.precipitation[hour]
    ),
    pressure: interpolateScalar(
      samples,
      forecastHour,
      (point, hour) => point.pressure[hour]
    ),
    windSpeed: wind.speed,
    windDirection: wind.fromDirection,
    windFlowBearing: wind.flowBearing,
  };

  return Object.values(result).every(Number.isFinite) ? result : null;
}

function sampleWindVectorFromSamples(
  samples: CellSample[],
  forecastHour: number,
  target: MutableWindVector = {
    eastwardFlow: 0,
    northwardFlow: 0,
    speed: 0,
    flowBearing: 0,
    fromDirection: 0,
  }
): MutableWindVector {
  let eastwardFlow = 0;
  let northwardFlow = 0;

  for (const sample of samples) {
    const speed = sample.point.windSpeed[forecastHour];
    const fromDirection = sample.point.windDirection[forecastHour];
    const flowRadians = ((fromDirection + 180) * Math.PI) / 180;

    eastwardFlow += Math.sin(flowRadians) * speed * sample.weight;
    northwardFlow += Math.cos(flowRadians) * speed * sample.weight;
  }

  const bearing = (Math.atan2(eastwardFlow, northwardFlow) * 180) / Math.PI;

  target.eastwardFlow = eastwardFlow;
  target.northwardFlow = northwardFlow;
  target.speed = Math.hypot(eastwardFlow, northwardFlow);
  target.flowBearing = (bearing + 360) % 360;
  target.fromDirection = (target.flowBearing + 180) % 360;

  return target;
}

export function sampleWindVectorAtLocation(
  grid: WeatherGrid,
  forecastHour: number,
  latitude: number,
  longitude: number,
  target: MutableWindVector
): boolean {
  const longitudeSpan = grid.bounds.east - grid.bounds.west;
  const latitudeSpan = grid.bounds.north - grid.bounds.south;

  if (longitudeSpan === 0 || latitudeSpan === 0) {
    return false;
  }

  const xRatio = (longitude - grid.bounds.west) / longitudeSpan;
  const yRatio = (grid.bounds.north - latitude) / latitudeSpan;

  if (xRatio < 0 || xRatio > 1 || yRatio < 0 || yRatio > 1) return false;

  const gridX = xRatio * (grid.columns - 1);
  const gridY = yRatio * (grid.rows - 1);
  const x0 = Math.floor(gridX);
  const y0 = Math.floor(gridY);
  const x1 = Math.min(x0 + 1, grid.columns - 1);
  const y1 = Math.min(y0 + 1, grid.rows - 1);
  const dx = gridX - x0;
  const dy = gridY - y0;
  const point0 = grid.points[y0 * grid.columns + x0];
  const point1 = grid.points[y0 * grid.columns + x1];
  const point2 = grid.points[y1 * grid.columns + x1];
  const point3 = grid.points[y1 * grid.columns + x0];
  const weight0 = (1 - dx) * (1 - dy);
  const weight1 = dx * (1 - dy);
  const weight2 = dx * dy;
  const weight3 = (1 - dx) * dy;
  let eastwardFlow = 0;
  let northwardFlow = 0;
  const speed0 = point0.windSpeed[forecastHour];
  const speed1 = point1.windSpeed[forecastHour];
  const speed2 = point2.windSpeed[forecastHour];
  const speed3 = point3.windSpeed[forecastHour];
  const radians0 = ((point0.windDirection[forecastHour] + 180) * Math.PI) / 180;
  const radians1 = ((point1.windDirection[forecastHour] + 180) * Math.PI) / 180;
  const radians2 = ((point2.windDirection[forecastHour] + 180) * Math.PI) / 180;
  const radians3 = ((point3.windDirection[forecastHour] + 180) * Math.PI) / 180;

  eastwardFlow += Math.sin(radians0) * speed0 * weight0;
  eastwardFlow += Math.sin(radians1) * speed1 * weight1;
  eastwardFlow += Math.sin(radians2) * speed2 * weight2;
  eastwardFlow += Math.sin(radians3) * speed3 * weight3;
  northwardFlow += Math.cos(radians0) * speed0 * weight0;
  northwardFlow += Math.cos(radians1) * speed1 * weight1;
  northwardFlow += Math.cos(radians2) * speed2 * weight2;
  northwardFlow += Math.cos(radians3) * speed3 * weight3;

  const bearing = (Math.atan2(eastwardFlow, northwardFlow) * 180) / Math.PI;

  target.eastwardFlow = eastwardFlow;
  target.northwardFlow = northwardFlow;
  target.speed = Math.hypot(eastwardFlow, northwardFlow);
  target.flowBearing = (bearing + 360) % 360;
  target.fromDirection = (target.flowBearing + 180) % 360;

  return (
    Number.isFinite(target.eastwardFlow) &&
    Number.isFinite(target.northwardFlow) &&
    Number.isFinite(target.speed) &&
    Number.isFinite(target.flowBearing) &&
    Number.isFinite(target.fromDirection)
  );
}

export function formatWindDirection(direction: number): string {
  const names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(((direction % 360) + 360) / 45) % names.length;

  return `${names[index]} (${Math.round(direction)}° from)`;
}
