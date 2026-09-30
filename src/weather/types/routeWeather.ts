export type RouteWeatherScalarKey =
  | "temperature"
  | "precipitation"
  | "cloud"
  | "gust"
  | "visibility"
  | "freezingLevel"
  | "highestFreezingLevel"
  | "cloudCeiling";

export type WeatherSampleUnavailableReason =
  | "source-unavailable"
  | "outside-forecast"
  | "tile-unavailable"
  | "no-data";

export interface RouteWeatherSampleRequest {
  coordinate: { longitude: number; latitude: number };
  requestedTime: string;
}

export interface WeatherSampleProvenance {
  fieldId: string;
  model: string;
  product: string;
  runTime: string;
  sourceLevel: string;
  units: string;
  nativeResolutionDegrees: number;
  verticalReference?: "surface" | "mean-sea-level" | "model-surface";
  requestedTime: string;
  validTime: string;
  forecastHour: number;
  temporalOffsetMinutes: number;
  timeSemantics: "instantaneous" | "interval-total";
  accumulationStart?: string;
  accumulationEnd?: string;
}

export interface AvailableWeatherScalarSample {
  state: "available";
  value: number;
  units: string;
  provenance: WeatherSampleProvenance;
}

export interface UnavailableWeatherSample {
  state: "unavailable";
  requestedTime: string;
  reason: WeatherSampleUnavailableReason;
}

export type WeatherScalarSample =
  | AvailableWeatherScalarSample
  | UnavailableWeatherSample;

export interface AvailableWeatherWindSample {
  state: "available";
  uMs: number;
  vMs: number;
  speedMs: number;
  directionFromDegrees: number | null;
  provenance: WeatherSampleProvenance;
}

export type WeatherWindSample =
  | AvailableWeatherWindSample
  | UnavailableWeatherSample;

export interface RouteWeatherSample {
  coordinate: { longitude: number; latitude: number };
  requestedTime: string;
  scalars: Record<RouteWeatherScalarKey, WeatherScalarSample>;
  wind: WeatherWindSample;
}