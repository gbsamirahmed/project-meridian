import { sampleWindVectorAtLocation } from "./weatherInterpolation";

import type { MutableWindVector } from "./weatherInterpolation";
import type { WeatherGrid, WeatherGridBounds } from "../types/weatherGrid";

export interface WindVectorField {
  bounds: WeatherGridBounds;
  signature: string;
  sample(
    latitude: number,
    longitude: number,
    target: MutableWindVector
  ): boolean;
}

class ForecastWindVectorField implements WindVectorField {
  readonly bounds: WeatherGridBounds;
  readonly signature: string;
  private readonly grid: WeatherGrid;
  private readonly forecastHour: number;

  constructor(grid: WeatherGrid, forecastHour: number) {
    this.grid = grid;
    this.forecastHour = forecastHour;
    this.bounds = grid.bounds;
    this.signature = `${grid.fetchedAt}:${forecastHour}`;
  }

  sample(
    latitude: number,
    longitude: number,
    target: MutableWindVector
  ): boolean {
    return sampleWindVectorAtLocation(
      this.grid,
      this.forecastHour,
      latitude,
      longitude,
      target
    );
  }
}

export function createForecastWindField(
  grid: WeatherGrid,
  forecastHour: number
): WindVectorField {
  return new ForecastWindVectorField(grid, forecastHour);
}
