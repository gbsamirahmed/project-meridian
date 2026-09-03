import type { RouteConditionFieldCoverage, RouteWeather } from "./routeConditions";

export type DerivedUnavailable = { state: "unavailable"; reason: "missing-input" | "incompatible-reference" | "different-forecast" };
export type FreezingStructure = "no-separated-levels-indicated" | "multiple-levels-indicated" | "inconsistent-levels" | "unknown";
export type FreezingContext = DerivedUnavailable | {
  state: "available";
  /** Approximate geometric metres above mean sea level, not a survey datum transform. */
  altitudeM: number;
  highestAltitudeM: number | null;
  separationM: number;
  levelDifferenceM: number | null;
  position: "below" | "near" | "above";
  structure: FreezingStructure;
};
export type WindContext = DerivedUnavailable | {
  state: "available";
  orientation: "calm" | "light" | "mixed" | "headwind" | "tailwind" | "crosswind-left" | "crosswind-right" | "unknown";
};
export type GustContext = DerivedUnavailable | {
  state: "available";
  /** Signed; a lower gust diagnostic is not silently clamped or replaced. No direction. */
  excessMs: number | null;
};
export type VisibilityContext = DerivedUnavailable | {
  state: "available";
  category: "very-poor" | "poor" | "moderate" | "good";
};
export interface DerivedConditionSample {
  /** Resolves original terrain, requested arrival and per-field provenance without copying them. */
  routeSampleIndex: number;
  evidenceFields: ReadonlyArray<keyof RouteWeather>;
  freezing: FreezingContext;
  wind: WindContext;
  gust: GustContext;
  visibilityCloud: {
    visibility: VisibilityContext;
    ceiling: DerivedUnavailable | { state: "available"; reference: "model-surface"; interpretation: "raw-only" };
  };
}
export interface FreezingCrossingEvent {
  kind: "freezing-crossing";
  direction: "above" | "below";
  fromSampleIndex: number;
  toSampleIndex: number;
  confirmedAtSampleIndex: number;
  /** Midpoint of a sample bracket, NOT temporally interpolated weather. */
  approximateDistanceM: number;
  approximateArrivalTime: string;
}
export interface VisibilitySectionEvent {
  kind: "poor-visibility-section";
  fromSampleIndex: number;
  toSampleIndex: number;
  /** First/last known sample only; gaps and forecast boundaries are not assumed clear. */
  boundary: "observed-samples";
}
export interface ConditionExtremumEvent {
  kind: "peak-gust" | "strongest-crosswind" | "strongest-headwind" | "minimum-visibility";
  fromSampleIndex: number;
  toSampleIndex: number;
  value: number;
  units: "m/s" | "m";
}
export type RouteConditionEvent = FreezingCrossingEvent | VisibilitySectionEvent | ConditionExtremumEvent;
export interface DerivedRouteConditions {
  version: 1;
  routeId: string;
  samples: DerivedConditionSample[];
  events: RouteConditionEvent[];
  coverage: Record<"freezing" | "wind" | "gust" | "visibility" | "ceiling", RouteConditionFieldCoverage>;
  summary: { aboveFreezingSamples: number; multipleLevelSamples: number; freezingCrossings: number };
}
