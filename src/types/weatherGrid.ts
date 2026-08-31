import type { GridPoint } from "./gridPoint";

export interface WeatherGridBounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface WeatherGridRequest {
  bounds: WeatherGridBounds;
  viewportBounds: WeatherGridBounds;
  rows: number;
  columns: number;
}

export interface WeatherGrid {
  bounds: WeatherGridBounds;
  rows: number;
  columns: number;
  points: GridPoint[];
  times: string[];
  fetchedAt: number;
}

export type WeatherGridStatus =
  | "idle"
  | "loading"
  | "refreshing"
  | "ready"
  | "rate-limited"
  | "error";
