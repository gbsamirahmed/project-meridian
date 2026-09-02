export interface RouteCoordinate {
  longitude: number;
  latitude: number;
}

export interface ImportedRouteGeometry {
  id: string;
  name: string;
  coordinates: RouteCoordinate[];
  sourcePointCount: number;
  sourceSegmentCount: number;
}

export interface ResampledRouteGeometry {
  id: string;
  name: string;
  coordinates: RouteCoordinate[];
  cumulativeDistancesM: number[];
  totalDistanceM: number;
  spacingM: number;
  sourcePointCount: number;
}

export interface TerrainRouteSample extends RouteCoordinate {
  index: number;
  cumulativeDistanceM: number;
  elevationM: number | null;
  smoothedElevationM: number | null;
  gradient: number | null;
  cumulativeAscentM: number | null;
  cumulativeDescentM: number | null;
}

export interface TerrainRoute {
  id: string;
  name: string;
  samples: TerrainRouteSample[];
  totalDistanceM: number;
  totalAscentM: number | null;
  totalDescentM: number | null;
  elevationCoverage: "complete" | "partial" | "unavailable";
  spacingM: number;
  sourcePointCount: number;
}

export type JourneyPace = "relaxed" | "normal" | "fast";
export type JourneyParty = "solo" | "group";
export type JourneyLoad = "light" | "heavy";
export type JourneyPlanningMode =
  | "profile"
  | "target-duration"
  | "target-finish";

export interface JourneyProfile {
  activity: "hiking";
  pace: JourneyPace;
  party: JourneyParty;
  load: JourneyLoad;
  plannedBreakMinutes: number;
}

export interface JourneyPlan {
  mode: JourneyPlanningMode;
  departureTime: string;
  targetDurationMinutes: number;
  targetFinishTime: string;
}

export interface JourneyScheduleSample {
  routeSampleIndex: number;
  cumulativeDistanceM: number;
  movingElapsedMinutes: number;
  stoppedElapsedMinutes: number;
  elapsedMinutes: number;
  arrivalTime: string;
  earliestArrivalTime: string;
  latestArrivalTime: string;
}

export type TargetPaceComparison =
  | "slower-than-baseline"
  | "close-to-baseline"
  | "faster-than-baseline";

export interface JourneySchedule {
  routeId: string;
  departureTime: string;
  expectedFinishTime: string;
  movingMinutes: number;
  stoppedMinutes: number;
  totalMinutes: number;
  likelyMinimumMinutes: number;
  likelyMaximumMinutes: number;
  movementScale: number;
  targetComparison: TargetPaceComparison;
  samples: JourneyScheduleSample[];
}

export type RoutePreparationStatus =
  | "idle"
  | "parsing"
  | "loading-elevation"
  | "ready"
  | "partial"
  | "error";
