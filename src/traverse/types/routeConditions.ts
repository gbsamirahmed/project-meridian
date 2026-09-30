import type { RouteWeatherScalarKey, WeatherSampleProvenance } from "../../weather/types/routeWeather";
import type { RouteCoordinate } from "./route";
import type { RouteConditionFieldCoverage, RouteConditionFieldKey } from "./routeConditionBase";
import type { DerivedRouteConditions } from "./derivedRouteConditions";

export type RouteConditionMode =
  | "none"
  | "temperature"
  | "precipitation"
  | "wind"
  | "gradient";

export type RouteConditionUnavailableReason =
  | "source-unavailable"
  | "outside-forecast"
  | "tile-unavailable"
  | "no-data";

export type RouteConditionProvenance = WeatherSampleProvenance;

export interface AvailableScalarRouteCondition {
  state: "available";
  value: number;
  units: string;
  provenance: RouteConditionProvenance;
}

export interface UnavailableRouteCondition {
  state: "unavailable";
  requestedTime: string;
  reason: RouteConditionUnavailableReason;
}

export type ScalarRouteCondition =
  | AvailableScalarRouteCondition
  | UnavailableRouteCondition;

export interface RouteRelativeWind {
  /** Positive values flow in the direction of travel (tailwind). */
  alongRouteMs: number;
  /** Positive values flow toward the traveller's right-hand side. */
  crossRouteMs: number;
  headwindMs: number;
  tailwindMs: number;
  crosswindMs: number;
  crosswindFrom: "left" | "right" | "calm";
}

export interface AvailableWindRouteCondition {
  state: "available";
  uMs: number;
  vMs: number;
  speedMs: number;
  directionFromDegrees: number | null;
  relative: RouteRelativeWind | null;
  provenance: RouteConditionProvenance;
}

export type WindRouteCondition =
  | AvailableWindRouteCondition
  | UnavailableRouteCondition;

export type RouteScalarKey = RouteWeatherScalarKey;

export type RouteWeather = Record<RouteScalarKey, ScalarRouteCondition> & { wind: WindRouteCondition };

export interface RouteConditionSample {
  routeSampleIndex: number;
  coordinate: RouteCoordinate;
  cumulativeDistanceM: number;
  routeProgress: number;
  routeBearingDegrees: number | null;
  terrain: {
    elevationM: number | null;
    gradient: number | null;
  };
  journey: {
    movingElapsedMinutes: number;
    stoppedElapsedMinutes: number;
    elapsedMinutes: number;
    expectedArrivalTime: string;
    earliestArrivalTime: string;
    latestArrivalTime: string;
  };
  /** Raw model fields. Atmospheric heights do not imply ice or cloud immersion. */
  weather: RouteWeather;
}

export interface RouteConditionSummary {
  temperatureRangeC: [number, number] | null;
  precipitationMaximumMm: number | null;
  precipitationEncountered: boolean | null;
  cloudRangePercent: [number, number] | null;
  windMaximumMs: number | null;
  headwindMaximumMs: number | null;
  crosswindMaximumMs: number | null;
  gustMaximumMs: number | null;
  visibilityMinimumM: number | null;
  freezingLevelRangeGpm: [number, number] | null;
}

export interface RouteConditions {
  derived: DerivedRouteConditions;
  routeId: string;
  generatedAt: string;
  samples: RouteConditionSample[];
  coverage: Record<RouteConditionFieldKey, RouteConditionFieldCoverage>;
  summary: RouteConditionSummary;
}

export type RouteConditionStatus =
  | "idle"
  | "loading"
  | "ready"
  | "partial"
  | "unavailable";
