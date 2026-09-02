import type {
  ImportedRouteGeometry,
  ResampledRouteGeometry,
  RouteCoordinate,
} from "../types/route";

export const DEFAULT_ROUTE_SAMPLE_SPACING_M = 40;
export const MAX_ROUTE_SAMPLES = 6000;
export const MAX_GPX_SOURCE_POINTS = 100000;
export const MAX_GPX_FILE_BYTES = 15 * 1024 * 1024;
const EARTH_RADIUS_M = 6371008.8;
const CONTIGUOUS_SEGMENT_GAP_M = 500;

interface GpxElementLike {
  getAttribute(name: string): string | null;
  getElementsByTagNameNS(namespace: string, localName: string): ArrayLike<GpxElementLike>;
  textContent: string | null;
}

interface GpxDocumentLike {
  getElementsByTagNameNS(namespace: string, localName: string): ArrayLike<GpxElementLike>;
  querySelector(selector: string): GpxElementLike | null;
}

function radians(value: number): number {
  return (value * Math.PI) / 180;
}

export function shortestLongitudeDelta(from: number, to: number): number {
  return ((to - from + 540) % 360) - 180;
}

export function normaliseLongitude(longitude: number): number {
  return ((longitude + 540) % 360) - 180;
}

export function unwrapRouteCoordinates(
  coordinates: RouteCoordinate[]
): RouteCoordinate[] {
  if (coordinates.length === 0) return [];
  const unwrapped: RouteCoordinate[] = [
    { ...coordinates[0], longitude: normaliseLongitude(coordinates[0].longitude) },
  ];
  for (let index = 1; index < coordinates.length; index++) {
    const previous = unwrapped[index - 1];
    unwrapped.push({
      latitude: coordinates[index].latitude,
      longitude:
        previous.longitude +
        shortestLongitudeDelta(previous.longitude, coordinates[index].longitude),
    });
  }
  return unwrapped;
}

export function geodesicDistanceM(
  first: RouteCoordinate,
  second: RouteCoordinate
): number {
  const latitude1 = radians(first.latitude);
  const latitude2 = radians(second.latitude);
  const latitudeDelta = latitude2 - latitude1;
  const longitudeDelta = radians(
    shortestLongitudeDelta(first.longitude, second.longitude)
  );
  const haversine =
    Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(latitude1) *
      Math.cos(latitude2) *
      Math.sin(longitudeDelta / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.min(1, Math.sqrt(haversine)));
}

function parseCoordinate(element: GpxElementLike): RouteCoordinate | null {
  const latitude = Number(element.getAttribute("lat"));
  const longitude = Number(element.getAttribute("lon"));
  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    latitude < -90 ||
    latitude > 90 ||
    longitude < -180 ||
    longitude > 180
  ) {
    return null;
  }
  return { latitude, longitude };
}

function coordinatesFrom(
  element: GpxElementLike,
  pointName: "trkpt" | "rtept"
): RouteCoordinate[] {
  return Array.from(element.getElementsByTagNameNS("*", pointName))
    .map(parseCoordinate)
    .filter((point): point is RouteCoordinate => point !== null);
}

function routeLength(points: RouteCoordinate[]): number {
  return points.slice(1).reduce(
    (distance, point, index) => distance + geodesicDistanceM(points[index], point),
    0
  );
}

export function chooseGpxRouteCoordinates(
  trackSegments: RouteCoordinate[][],
  routeCandidates: RouteCoordinate[][]
): { coordinates: RouteCoordinate[]; sourceSegmentCount: number } {
  const usableSegments = trackSegments.filter((segment) => segment.length >= 2);
  const chains: RouteCoordinate[][] = [];
  for (const segment of usableSegments) {
    const current = chains[chains.length - 1];
    if (
      current &&
      geodesicDistanceM(current[current.length - 1], segment[0]) <=
        CONTIGUOUS_SEGMENT_GAP_M
    ) {
      current.push(
        ...(geodesicDistanceM(current[current.length - 1], segment[0]) < 0.5
          ? segment.slice(1)
          : segment)
      );
    } else {
      chains.push([...segment]);
    }
  }
  const candidates = [
    ...chains,
    ...routeCandidates.filter((candidate) => candidate.length >= 2),
  ];
  if (candidates.length === 0) {
    throw new Error("The GPX file does not contain a usable track or route.");
  }
  const coordinates = candidates.reduce((longest, candidate) =>
    routeLength(candidate) > routeLength(longest) ? candidate : longest
  );
  if (coordinates.length > MAX_GPX_SOURCE_POINTS) {
    throw new Error(
      `The GPX contains more than ${MAX_GPX_SOURCE_POINTS.toLocaleString()} usable points.`
    );
  }
  return {
    coordinates,
    sourceSegmentCount: usableSegments.length || routeCandidates.length,
  };
}

export function parseGpxDocument(
  document: GpxDocumentLike,
  fallbackName = "Imported route"
): ImportedRouteGeometry {
  if (document.querySelector("parsererror")) {
    throw new Error("The selected file is not valid GPX/XML.");
  }
  const trackSegments = Array.from(
    document.getElementsByTagNameNS("*", "trkseg")
  ).map((segment) => coordinatesFrom(segment, "trkpt"));
  const routeCandidates = Array.from(
    document.getElementsByTagNameNS("*", "rte")
  ).map((route) => coordinatesFrom(route, "rtept"));
  const selected = chooseGpxRouteCoordinates(trackSegments, routeCandidates);
  const nameElement = Array.from(
    document.getElementsByTagNameNS("*", "name")
  )[0];
  const name = nameElement?.textContent?.trim() || fallbackName;
  return {
    id: `route-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name,
    coordinates: selected.coordinates,
    sourcePointCount: selected.coordinates.length,
    sourceSegmentCount: selected.sourceSegmentCount,
  };
}

export function parseGpxText(
  text: string,
  fallbackName = "Imported route"
): ImportedRouteGeometry {
  const document = new DOMParser().parseFromString(text, "application/xml");
  return parseGpxDocument(document, fallbackName);
}

function interpolateCoordinate(
  first: RouteCoordinate,
  second: RouteCoordinate,
  fraction: number
): RouteCoordinate {
  return {
    latitude: first.latitude + (second.latitude - first.latitude) * fraction,
    longitude: normaliseLongitude(
      first.longitude + shortestLongitudeDelta(first.longitude, second.longitude) * fraction
    ),
  };
}

export function resampleRouteGeometry(
  route: ImportedRouteGeometry,
  requestedSpacingM = DEFAULT_ROUTE_SAMPLE_SPACING_M
): ResampledRouteGeometry {
  if (route.coordinates.length < 2) {
    throw new Error("A route needs at least two usable coordinates.");
  }
  const sourceDistances = [0];
  for (let index = 1; index < route.coordinates.length; index++) {
    sourceDistances.push(
      sourceDistances[index - 1] +
        geodesicDistanceM(route.coordinates[index - 1], route.coordinates[index])
    );
  }
  const totalDistanceM = sourceDistances[sourceDistances.length - 1];
  if (!Number.isFinite(totalDistanceM) || totalDistanceM < 10) {
    throw new Error("The GPX route is too short for journey analysis.");
  }
  const spacingM = Math.max(
    requestedSpacingM,
    totalDistanceM / Math.max(1, MAX_ROUTE_SAMPLES - 1)
  );
  const targetDistances: number[] = [];
  for (let distance = 0; distance < totalDistanceM; distance += spacingM) {
    targetDistances.push(distance);
  }
  targetDistances.push(totalDistanceM);
  const coordinates: RouteCoordinate[] = [];
  let sourceIndex = 1;
  for (const targetDistance of targetDistances) {
    while (
      sourceIndex < sourceDistances.length - 1 &&
      sourceDistances[sourceIndex] < targetDistance
    ) {
      sourceIndex += 1;
    }
    const beforeDistance = sourceDistances[sourceIndex - 1];
    const afterDistance = sourceDistances[sourceIndex];
    const fraction =
      afterDistance === beforeDistance
        ? 0
        : (targetDistance - beforeDistance) / (afterDistance - beforeDistance);
    coordinates.push(
      interpolateCoordinate(
        route.coordinates[sourceIndex - 1],
        route.coordinates[sourceIndex],
        Math.max(0, Math.min(1, fraction))
      )
    );
  }
  return {
    id: route.id,
    name: route.name,
    coordinates,
    cumulativeDistancesM: targetDistances,
    totalDistanceM,
    spacingM,
    sourcePointCount: route.sourcePointCount,
  };
}

export function getRouteBounds(coordinates: RouteCoordinate[]): {
  west: number;
  south: number;
  east: number;
  north: number;
} {
  const latitudes = coordinates.map((point) => point.latitude);
  const wrapped = coordinates
    .map((point) => ((point.longitude % 360) + 360) % 360)
    .sort((a, b) => a - b);
  let largestGap = -1;
  let gapIndex = 0;
  for (let index = 0; index < wrapped.length; index++) {
    const next = index === wrapped.length - 1 ? wrapped[0] + 360 : wrapped[index + 1];
    const gap = next - wrapped[index];
    if (gap > largestGap) {
      largestGap = gap;
      gapIndex = index;
    }
  }
  const westWrapped = wrapped[(gapIndex + 1) % wrapped.length];
  const eastWrapped = wrapped[gapIndex] + (gapIndex === wrapped.length - 1 ? 0 : 360);
  const west = westWrapped > 180 ? westWrapped - 360 : westWrapped;
  let east = eastWrapped > 180 ? eastWrapped - 360 : eastWrapped;
  while (east < west) east += 360;
  return {
    west,
    east,
    south: Math.min(...latitudes),
    north: Math.max(...latitudes),
  };
}
