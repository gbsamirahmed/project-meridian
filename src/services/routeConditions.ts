import { geodesicDistanceM, shortestLongitudeDelta } from "./routeGeometry";
import {
  prepareScalarFieldCoordinates,
  prepareVectorFieldCoordinates,
  sampleCachedScalarField,
  sampleCachedVectorField,
} from "./numericTileCache";

import type {
  ScalarFieldTimestep,
  ScalarWeatherFieldSource,
  VectorFieldTimestep,
  VectorWeatherFieldSource,
} from "../types/globalWeather";
import type { JourneySchedule, RouteCoordinate, TerrainRoute } from "../types/route";
import type {
  AvailableScalarRouteCondition,
  AvailableWindRouteCondition,
  RouteConditionProvenance,
  RouteConditions,
  RouteConditionSample,
  RouteConditionSummary,
  RouteRelativeWind,
  ScalarRouteCondition,
  UnavailableRouteCondition,
  WindRouteCondition,
} from "../types/routeConditions";

interface RouteConditionSources {
  temperature: ScalarWeatherFieldSource | null;
  precipitation: ScalarWeatherFieldSource | null;
  cloud: ScalarWeatherFieldSource | null;
  wind: VectorWeatherFieldSource | null;
}

interface ScheduledRoutePoint {
  coordinate: RouteCoordinate;
  expectedArrivalTime: string;
}

interface SelectedRoutePoint extends ScheduledRoutePoint {
  temperatureTimestep: ScalarFieldTimestep | null;
  precipitationTimestep: ScalarFieldTimestep | null;
  cloudTimestep: ScalarFieldTimestep | null;
  windTimestep: VectorFieldTimestep | null;
}

function milliseconds(value: string): number {
  return Date.parse(value);
}

export function selectInstantaneousTimestep<T extends { validTime: string }>(
  timesteps: T[],
  requestedTime: string
): T | null {
  const requested = milliseconds(requestedTime);
  if (!Number.isFinite(requested) || timesteps.length === 0) return null;
  const ordered = [...timesteps].sort(
    (first, second) => milliseconds(first.validTime) - milliseconds(second.validTime)
  );
  const first = milliseconds(ordered[0].validTime);
  const last = milliseconds(ordered[ordered.length - 1].validTime);
  if (requested < first || requested > last) return null;
  return ordered.reduce((closest, candidate) => {
    const closestDistance = Math.abs(milliseconds(closest.validTime) - requested);
    const candidateDistance = Math.abs(milliseconds(candidate.validTime) - requested);
    return candidateDistance < closestDistance ? candidate : closest;
  });
}

export function selectPrecipitationTimestep(
  timesteps: ScalarFieldTimestep[],
  requestedTime: string
): ScalarFieldTimestep | null {
  const requested = milliseconds(requestedTime);
  if (!Number.isFinite(requested)) return null;
  const intervals = timesteps
    .filter(
      (step) =>
        typeof step.accumulationStart === "string" &&
        typeof step.accumulationEnd === "string"
    )
    .sort(
      (first, second) =>
        milliseconds(first.accumulationEnd!) - milliseconds(second.accumulationEnd!)
    );
  const exact = intervals.find(
    (step) => milliseconds(step.accumulationEnd!) === requested
  );
  if (exact) return exact;
  return (
    intervals.find((step) => {
      const start = milliseconds(step.accumulationStart!);
      const end = milliseconds(step.accumulationEnd!);
      return requested > start && requested < end;
    }) ?? null
  );
}

function radians(value: number): number {
  return (value * Math.PI) / 180;
}

export function routeBearingDegrees(
  coordinates: RouteCoordinate[],
  index: number
): number | null {
  if (coordinates.length < 2 || index < 0 || index >= coordinates.length) return null;
  let before = Math.max(0, index - 1);
  let after = Math.min(coordinates.length - 1, index + 1);
  while (
    before > 0 &&
    geodesicDistanceM(coordinates[before], coordinates[after]) < 0.5
  ) {
    before -= 1;
  }
  while (
    after < coordinates.length - 1 &&
    geodesicDistanceM(coordinates[before], coordinates[after]) < 0.5
  ) {
    after += 1;
  }
  const first = coordinates[before];
  const second = coordinates[after];
  if (geodesicDistanceM(first, second) < 0.5) return null;
  const latitude1 = radians(first.latitude);
  const latitude2 = radians(second.latitude);
  const deltaLongitude = radians(
    shortestLongitudeDelta(first.longitude, second.longitude)
  );
  const y = Math.sin(deltaLongitude) * Math.cos(latitude2);
  const x =
    Math.cos(latitude1) * Math.sin(latitude2) -
    Math.sin(latitude1) * Math.cos(latitude2) * Math.cos(deltaLongitude);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

export function deriveRouteRelativeWind(
  uMs: number,
  vMs: number,
  bearingDegrees: number | null
): RouteRelativeWind | null {
  if (bearingDegrees === null) return null;
  const bearing = radians(bearingDegrees);
  const routeEast = Math.sin(bearing);
  const routeNorth = Math.cos(bearing);
  const alongRouteMs = uMs * routeEast + vMs * routeNorth;
  const crossRouteMs = uMs * routeNorth - vMs * routeEast;
  const crosswindMs = Math.abs(crossRouteMs);
  return {
    alongRouteMs,
    crossRouteMs,
    headwindMs: Math.max(0, -alongRouteMs),
    tailwindMs: Math.max(0, alongRouteMs),
    crosswindMs,
    crosswindFrom:
      crosswindMs < 0.05 ? "calm" : crossRouteMs > 0 ? "left" : "right",
  };
}

function unavailable(
  requestedTime: string,
  reason: UnavailableRouteCondition["reason"]
): UnavailableRouteCondition {
  return { state: "unavailable", requestedTime, reason };
}

function provenance(
  source: ScalarWeatherFieldSource | VectorWeatherFieldSource,
  timestep: ScalarFieldTimestep | VectorFieldTimestep,
  requestedTime: string
): RouteConditionProvenance {
  const accumulation =
    "accumulationStart" in timestep
      ? {
          accumulationStart: timestep.accumulationStart,
          accumulationEnd: timestep.accumulationEnd,
        }
      : {};
  return {
    fieldId: source.manifest.field.id,
    model: source.manifest.model,
    product: source.manifest.product,
    runTime: source.manifest.runTime,
    sourceLevel: source.manifest.field.sourceLevel,
    requestedTime,
    validTime: timestep.validTime,
    forecastHour: timestep.forecastHour,
    temporalOffsetMinutes:
      (milliseconds(timestep.validTime) - milliseconds(requestedTime)) / 60000,
    timeSemantics: source.manifest.field.timeSemantics,
    ...accumulation,
  };
}

export function resolvedScalarCondition(
  source: ScalarWeatherFieldSource | null,
  timestep: ScalarFieldTimestep | null,
  requestedTime: string,
  value: number | null | undefined
): ScalarRouteCondition {
  if (!source) return unavailable(requestedTime, "source-unavailable");
  if (!timestep) return unavailable(requestedTime, "outside-forecast");
  if (value === undefined) {
    return unavailable(requestedTime, "tile-unavailable");
  }
  if (value === null) return unavailable(requestedTime, "no-data");
  return {
    state: "available",
    value,
    units: source.manifest.field.units,
    provenance: provenance(source, timestep, requestedTime),
  } satisfies AvailableScalarRouteCondition;
}

export function resolvedWindCondition(
  source: VectorWeatherFieldSource | null,
  timestep: VectorFieldTimestep | null,
  requestedTime: string,
  vector: { u: number; v: number } | null | undefined,
  bearingDegrees: number | null
): WindRouteCondition {
  if (!source) return unavailable(requestedTime, "source-unavailable");
  if (!timestep) return unavailable(requestedTime, "outside-forecast");
  if (vector === undefined) {
    return unavailable(requestedTime, "tile-unavailable");
  }
  if (vector === null) return unavailable(requestedTime, "no-data");
  const speedMs = Math.hypot(vector.u, vector.v);
  return {
    state: "available",
    uMs: vector.u,
    vMs: vector.v,
    speedMs,
    directionFromDegrees:
      speedMs < 0.05
        ? null
        : ((180 + (Math.atan2(vector.u, vector.v) * 180) / Math.PI) % 360 + 360) %
          360,
    relative: deriveRouteRelativeWind(vector.u, vector.v, bearingDegrees),
    provenance: provenance(source, timestep, requestedTime),
  } satisfies AvailableWindRouteCondition;
}

async function sampleScalarSelections(
  source: ScalarWeatherFieldSource | null,
  selections: SelectedRoutePoint[],
  pick: (point: SelectedRoutePoint) => ScalarFieldTimestep | null,
  signal?: AbortSignal
): Promise<Array<number | null | undefined>> {
  const values: Array<number | null | undefined> = selections.map(() => undefined);
  if (!source) return values;
  const groups = new Map<
    string,
    { timestep: ScalarFieldTimestep; indexes: number[] }
  >();
  selections.forEach((point, index) => {
    const timestep = pick(point);
    if (!timestep) return;
    const group = groups.get(timestep.id) ?? { timestep, indexes: [] };
    group.indexes.push(index);
    groups.set(timestep.id, group);
  });
  for (const group of groups.values()) {
    await prepareScalarFieldCoordinates(
      source,
      group.timestep,
      group.indexes.map((index) => selections[index].coordinate),
      signal
    );
    for (const index of group.indexes) {
      const coordinate = selections[index].coordinate;
      values[index] = sampleCachedScalarField(
        source,
        group.timestep,
        source.manifest.tiles.maxZoom,
        coordinate.longitude,
        coordinate.latitude
      );
    }
  }
  return values;
}

async function sampleWindSelections(
  source: VectorWeatherFieldSource | null,
  selections: SelectedRoutePoint[],
  signal?: AbortSignal
): Promise<Array<{ u: number; v: number } | null | undefined>> {
  const values: Array<{ u: number; v: number } | null | undefined> =
    selections.map(() => undefined);
  if (!source) return values;
  const groups = new Map<
    string,
    { timestep: VectorFieldTimestep; indexes: number[] }
  >();
  selections.forEach((point, index) => {
    if (!point.windTimestep) return;
    const group = groups.get(point.windTimestep.id) ?? {
      timestep: point.windTimestep,
      indexes: [],
    };
    group.indexes.push(index);
    groups.set(point.windTimestep.id, group);
  });
  for (const group of groups.values()) {
    await prepareVectorFieldCoordinates(
      source,
      group.timestep,
      group.indexes.map((index) => selections[index].coordinate),
      signal
    );
    for (const index of group.indexes) {
      const coordinate = selections[index].coordinate;
      values[index] = sampleCachedVectorField(
        source,
        group.timestep,
        source.manifest.tiles.maxZoom,
        coordinate.longitude,
        coordinate.latitude
      );
    }
  }
  return values;
}

function numericRange(values: number[]): [number, number] | null {
  return values.length ? [Math.min(...values), Math.max(...values)] : null;
}

export function buildRouteConditionSummary(
  samples: RouteConditionSample[]
): RouteConditionSummary {
  const temperatures: number[] = [];
  const precipitation: number[] = [];
  const clouds: number[] = [];
  const winds: number[] = [];
  const headwinds: number[] = [];
  const crosswinds: number[] = [];
  for (const sample of samples) {
    if (sample.weather.temperature.state === "available") {
      temperatures.push(sample.weather.temperature.value);
    }
    if (sample.weather.precipitation.state === "available") {
      precipitation.push(sample.weather.precipitation.value);
    }
    if (sample.weather.cloud.state === "available") {
      clouds.push(sample.weather.cloud.value);
    }
    if (sample.weather.wind.state === "available") {
      winds.push(sample.weather.wind.speedMs);
      if (sample.weather.wind.relative) {
        headwinds.push(sample.weather.wind.relative.headwindMs);
        crosswinds.push(sample.weather.wind.relative.crosswindMs);
      }
    }
  }
  return {
    temperatureRangeC: numericRange(temperatures),
    precipitationMaximumMm: precipitation.length
      ? Math.max(...precipitation)
      : null,
    precipitationEncountered: precipitation.length
      ? precipitation.some((value) => value > 0)
      : null,
    cloudRangePercent: numericRange(clouds),
    windMaximumMs: winds.length ? Math.max(...winds) : null,
    headwindMaximumMs: headwinds.length ? Math.max(...headwinds) : null,
    crosswindMaximumMs: crosswinds.length ? Math.max(...crosswinds) : null,
  };
}

function coverageFor(
  samples: RouteConditionSample[],
  selector: (sample: RouteConditionSample) => { state: string }
) {
  return {
    availableSamples: samples.filter(
      (sample) => selector(sample).state === "available"
    ).length,
    totalSamples: samples.length,
  };
}

export async function buildRouteConditions(
  route: TerrainRoute,
  schedule: JourneySchedule,
  sources: RouteConditionSources,
  signal?: AbortSignal
): Promise<RouteConditions> {
  if (
    route.id !== schedule.routeId ||
    route.samples.length !== schedule.samples.length
  ) {
    throw new Error("Route terrain and journey schedule do not match.");
  }
  const points: SelectedRoutePoint[] = route.samples.map((sample, index) => {
    const journey = schedule.samples[index];
    if (!journey || journey.routeSampleIndex !== sample.index) {
      throw new Error("Route and journey samples are not aligned.");
    }
    return {
      coordinate: { longitude: sample.longitude, latitude: sample.latitude },
      expectedArrivalTime: journey.arrivalTime,
      temperatureTimestep: sources.temperature
        ? selectInstantaneousTimestep(
            sources.temperature.manifest.timesteps,
            journey.arrivalTime
          )
        : null,
      precipitationTimestep: sources.precipitation
        ? selectPrecipitationTimestep(
            sources.precipitation.manifest.timesteps,
            journey.arrivalTime
          )
        : null,
      cloudTimestep: sources.cloud
        ? selectInstantaneousTimestep(
            sources.cloud.manifest.timesteps,
            journey.arrivalTime
          )
        : null,
      windTimestep: sources.wind
        ? selectInstantaneousTimestep(
            sources.wind.manifest.timesteps,
            journey.arrivalTime
          )
        : null,
    };
  });
  const [
    temperatureValues,
    precipitationValues,
    cloudValues,
    windValues,
  ] = await Promise.all([
    sampleScalarSelections(
      sources.temperature,
      points,
      (point) => point.temperatureTimestep,
      signal
    ),
    sampleScalarSelections(
      sources.precipitation,
      points,
      (point) => point.precipitationTimestep,
      signal
    ),
    sampleScalarSelections(
      sources.cloud,
      points,
      (point) => point.cloudTimestep,
      signal
    ),
    sampleWindSelections(sources.wind, points, signal),
  ]);
  if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
  const coordinates = points.map((point) => point.coordinate);
  const samples: RouteConditionSample[] = route.samples.map((sample, index) => {
    const point = points[index];
    const journey = schedule.samples[index];
    const bearing = routeBearingDegrees(coordinates, index);
    return {
      routeSampleIndex: sample.index,
      coordinate: point.coordinate,
      cumulativeDistanceM: sample.cumulativeDistanceM,
      routeProgress: sample.cumulativeDistanceM / Math.max(1, route.totalDistanceM),
      routeBearingDegrees: bearing,
      terrain: {
        elevationM: sample.smoothedElevationM,
        gradient: sample.gradient,
      },
      journey: {
        movingElapsedMinutes: journey.movingElapsedMinutes,
        stoppedElapsedMinutes: journey.stoppedElapsedMinutes,
        elapsedMinutes: journey.elapsedMinutes,
        expectedArrivalTime: journey.arrivalTime,
        earliestArrivalTime: journey.earliestArrivalTime,
        latestArrivalTime: journey.latestArrivalTime,
      },
      weather: {
        temperature: resolvedScalarCondition(
          sources.temperature,
          point.temperatureTimestep,
          point.expectedArrivalTime,
          temperatureValues[index]
        ),
        precipitation: resolvedScalarCondition(
          sources.precipitation,
          point.precipitationTimestep,
          point.expectedArrivalTime,
          precipitationValues[index]
        ),
        cloud: resolvedScalarCondition(
          sources.cloud,
          point.cloudTimestep,
          point.expectedArrivalTime,
          cloudValues[index]
        ),
        wind: resolvedWindCondition(
          sources.wind,
          point.windTimestep,
          point.expectedArrivalTime,
          windValues[index],
          bearing
        ),
      },
    };
  });
  return {
    routeId: route.id,
    generatedAt: new Date().toISOString(),
    samples,
    coverage: {
      temperature: coverageFor(samples, (sample) => sample.weather.temperature),
      precipitation: coverageFor(samples, (sample) => sample.weather.precipitation),
      cloud: coverageFor(samples, (sample) => sample.weather.cloud),
      wind: coverageFor(samples, (sample) => sample.weather.wind),
    },
    summary: buildRouteConditionSummary(samples),
  };
}
