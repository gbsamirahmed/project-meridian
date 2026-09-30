import type { RouteWeatherScalarKey } from "../../weather/types/routeWeather";

export type RouteConditionFieldKey = RouteWeatherScalarKey | "wind";

export interface RouteConditionFieldCoverage {
  availableSamples: number;
  totalSamples: number;
}
