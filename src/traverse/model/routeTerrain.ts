import type {
  ResampledRouteGeometry,
  TerrainRoute,
  TerrainRouteSample,
} from "../types/route";

const ELEVATION_SMOOTHING_RADIUS = 2;
const GRADIENT_WINDOW_RADIUS = 3;
const ASCENT_HYSTERESIS_M = 3;

function median(values: number[]): number {
  const ordered = [...values].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2
    ? ordered[middle]
    : (ordered[middle - 1] + ordered[middle]) / 2;
}

export function smoothElevations(
  elevations: Array<number | null>,
  radius = ELEVATION_SMOOTHING_RADIUS
): Array<number | null> {
  return elevations.map((elevation, index) => {
    if (elevation === null) return null;
    const window = elevations
      .slice(Math.max(0, index - radius), index + radius + 1)
      .filter((value): value is number => value !== null && Number.isFinite(value));
    return window.length >= Math.min(3, radius * 2 + 1) ? median(window) : elevation;
  });
}

export function calculateSmoothedGradients(
  elevations: Array<number | null>,
  cumulativeDistancesM: number[],
  radius = GRADIENT_WINDOW_RADIUS
): Array<number | null> {
  return elevations.map((elevation, index) => {
    if (elevation === null) return null;
    let before = Math.max(0, index - radius);
    let after = Math.min(elevations.length - 1, index + radius);
    while (before < index && elevations[before] === null) before += 1;
    while (after > index && elevations[after] === null) after -= 1;
    const beforeElevation = elevations[before];
    const afterElevation = elevations[after];
    const distance = cumulativeDistancesM[after] - cumulativeDistancesM[before];
    if (
      beforeElevation === null ||
      afterElevation === null ||
      distance < 1
    ) {
      return null;
    }
    return (afterElevation - beforeElevation) / distance;
  });
}

export function calculateAscentDescent(
  elevations: Array<number | null>,
  hysteresisM = ASCENT_HYSTERESIS_M
): {
  cumulativeAscentM: Array<number | null>;
  cumulativeDescentM: Array<number | null>;
  totalAscentM: number | null;
  totalDescentM: number | null;
} {
  const cumulativeAscentM: Array<number | null> = [];
  const cumulativeDescentM: Array<number | null> = [];
  const first = elevations.find((value): value is number => value !== null);
  if (first === undefined) {
    return {
      cumulativeAscentM: elevations.map(() => null),
      cumulativeDescentM: elevations.map(() => null),
      totalAscentM: null,
      totalDescentM: null,
    };
  }
  let reference = first;
  let ascent = 0;
  let descent = 0;
  for (const elevation of elevations) {
    if (elevation === null) {
      cumulativeAscentM.push(null);
      cumulativeDescentM.push(null);
      continue;
    }
    const difference = elevation - reference;
    if (Math.abs(difference) >= hysteresisM) {
      if (difference > 0) ascent += difference;
      else descent += -difference;
      reference = elevation;
    }
    cumulativeAscentM.push(ascent);
    cumulativeDescentM.push(descent);
  }
  return {
    cumulativeAscentM,
    cumulativeDescentM,
    totalAscentM: ascent,
    totalDescentM: descent,
  };
}

export function buildTerrainRoute(
  geometry: ResampledRouteGeometry,
  elevations: Array<number | null>
): TerrainRoute {
  if (elevations.length !== geometry.coordinates.length) {
    throw new Error("Elevation samples do not match the resampled route.");
  }
  const validCount = elevations.filter(
    (value): value is number => value !== null && Number.isFinite(value)
  ).length;
  const coverage =
    validCount === elevations.length
      ? "complete"
      : validCount === 0
        ? "unavailable"
        : "partial";
  const smoothed = smoothElevations(elevations);
  const gradients = calculateSmoothedGradients(
    smoothed,
    geometry.cumulativeDistancesM
  );
  const totals = calculateAscentDescent(smoothed);
  const samples: TerrainRouteSample[] = geometry.coordinates.map(
    (coordinate, index) => ({
      ...coordinate,
      index,
      cumulativeDistanceM: geometry.cumulativeDistancesM[index],
      elevationM: elevations[index],
      smoothedElevationM: smoothed[index],
      gradient: gradients[index],
      cumulativeAscentM: totals.cumulativeAscentM[index],
      cumulativeDescentM: totals.cumulativeDescentM[index],
    })
  );
  return {
    id: geometry.id,
    name: geometry.name,
    samples,
    totalDistanceM: geometry.totalDistanceM,
    totalAscentM: coverage === "complete" ? totals.totalAscentM : null,
    totalDescentM: coverage === "complete" ? totals.totalDescentM : null,
    elevationCoverage: coverage,
    spacingM: geometry.spacingM,
    sourcePointCount: geometry.sourcePointCount,
  };
}
