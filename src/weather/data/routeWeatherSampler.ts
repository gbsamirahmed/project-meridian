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
import type {
  RouteWeatherSample,
  RouteWeatherSampleRequest,
  RouteWeatherScalarKey,
  WeatherSampleProvenance,
  WeatherScalarSample,
  WeatherWindSample,
  UnavailableWeatherSample,
} from "../types/routeWeather";

export interface RouteWeatherSources
  extends Partial<Record<RouteWeatherScalarKey, ScalarWeatherFieldSource | null>> {
  temperature: ScalarWeatherFieldSource | null;
  precipitation: ScalarWeatherFieldSource | null;
  cloud: ScalarWeatherFieldSource | null;
  wind: VectorWeatherFieldSource | null;
}

interface SelectedRequest extends RouteWeatherSampleRequest {
  scalarTimesteps: Record<RouteWeatherScalarKey, ScalarFieldTimestep | null>;
  windTimestep: VectorFieldTimestep | null;
}

export const ROUTE_WEATHER_SCALAR_KEYS: RouteWeatherScalarKey[] = [
  "temperature",
  "precipitation",
  "cloud",
  "gust",
  "visibility",
  "freezingLevel",
  "highestFreezingLevel",
  "cloudCeiling",
];

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
    (first, second) =>
      milliseconds(first.validTime) - milliseconds(second.validTime)
  );
  const first = milliseconds(ordered[0].validTime);
  const last = milliseconds(ordered[ordered.length - 1].validTime);
  if (requested < first || requested > last) return null;
  return ordered.reduce((closest, candidate) => {
    const closestDistance = Math.abs(milliseconds(closest.validTime) - requested);
    const candidateDistance = Math.abs(
      milliseconds(candidate.validTime) - requested
    );
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
        milliseconds(first.accumulationEnd!) -
        milliseconds(second.accumulationEnd!)
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

function unavailable(
  requestedTime: string,
  reason: UnavailableWeatherSample["reason"]
): UnavailableWeatherSample {
  return { state: "unavailable", requestedTime, reason };
}

function provenance(
  source: ScalarWeatherFieldSource | VectorWeatherFieldSource,
  timestep: ScalarFieldTimestep | VectorFieldTimestep,
  requestedTime: string
): WeatherSampleProvenance {
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
    units: source.manifest.field.units,
    nativeResolutionDegrees:
      source.manifest.field.nativeResolution.longitudeDegrees,
    verticalReference:
      source.manifest.field.kind === "scalar"
        ? source.manifest.field.verticalReference
        : undefined,
    requestedTime,
    validTime: timestep.validTime,
    forecastHour: timestep.forecastHour,
    temporalOffsetMinutes:
      (milliseconds(timestep.validTime) - milliseconds(requestedTime)) / 60_000,
    timeSemantics: source.manifest.field.timeSemantics,
    ...accumulation,
  };
}

export function resolveWeatherScalarSample(
  source: ScalarWeatherFieldSource | null,
  timestep: ScalarFieldTimestep | null,
  requestedTime: string,
  value: number | null | undefined
): WeatherScalarSample {
  if (!source) return unavailable(requestedTime, "source-unavailable");
  if (!timestep) return unavailable(requestedTime, "outside-forecast");
  if (value === undefined) return unavailable(requestedTime, "tile-unavailable");
  if (value === null || !Number.isFinite(value)) {
    return unavailable(requestedTime, "no-data");
  }
  return {
    state: "available",
    value,
    units: source.manifest.field.units,
    provenance: provenance(source, timestep, requestedTime),
  };
}

export function resolveWeatherWindSample(
  source: VectorWeatherFieldSource | null,
  timestep: VectorFieldTimestep | null,
  requestedTime: string,
  vector: { u: number; v: number } | null | undefined
): WeatherWindSample {
  if (!source) return unavailable(requestedTime, "source-unavailable");
  if (!timestep) return unavailable(requestedTime, "outside-forecast");
  if (vector === undefined) return unavailable(requestedTime, "tile-unavailable");
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
        : ((180 + (Math.atan2(vector.u, vector.v) * 180) / Math.PI) % 360 +
            360) %
          360,
    provenance: provenance(source, timestep, requestedTime),
  };
}

async function sampleScalarSelections(
  source: ScalarWeatherFieldSource | null,
  selections: SelectedRequest[],
  pick: (selection: SelectedRequest) => ScalarFieldTimestep | null,
  signal?: AbortSignal
): Promise<Array<number | null | undefined>> {
  const values: Array<number | null | undefined> = selections.map(
    () => undefined
  );
  if (!source) return values;
  const groups = new Map<
    string,
    { timestep: ScalarFieldTimestep; indexes: number[] }
  >();
  selections.forEach((selection, index) => {
    const timestep = pick(selection);
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
  selections: SelectedRequest[],
  signal?: AbortSignal
): Promise<Array<{ u: number; v: number } | null | undefined>> {
  const values: Array<{ u: number; v: number } | null | undefined> =
    selections.map(() => undefined);
  if (!source) return values;
  const groups = new Map<
    string,
    { timestep: VectorFieldTimestep; indexes: number[] }
  >();
  selections.forEach((selection, index) => {
    if (!selection.windTimestep) return;
    const group = groups.get(selection.windTimestep.id) ?? {
      timestep: selection.windTimestep,
      indexes: [],
    };
    group.indexes.push(index);
    groups.set(selection.windTimestep.id, group);
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

export async function sampleRouteWeather(
  requests: RouteWeatherSampleRequest[],
  sources: RouteWeatherSources,
  signal?: AbortSignal
): Promise<RouteWeatherSample[]> {
  const selections: SelectedRequest[] = requests.map((request) => ({
    ...request,
    scalarTimesteps: Object.fromEntries(
      ROUTE_WEATHER_SCALAR_KEYS.map((key) => [
        key,
        (key === "precipitation"
          ? selectPrecipitationTimestep
          : selectInstantaneousTimestep)(
          sources[key]?.manifest.timesteps ?? [],
          request.requestedTime
        ),
      ])
    ) as SelectedRequest["scalarTimesteps"],
    windTimestep: sources.wind
      ? selectInstantaneousTimestep(
          sources.wind.manifest.timesteps,
          request.requestedTime
        )
      : null,
  }));

  const scalarValues = {} as Record<
    RouteWeatherScalarKey,
    Array<number | null | undefined>
  >;
  let nextField = 0;
  const scalarWorker = async () => {
    while (nextField < ROUTE_WEATHER_SCALAR_KEYS.length) {
      if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
      const key = ROUTE_WEATHER_SCALAR_KEYS[nextField++];
      scalarValues[key] = await sampleScalarSelections(
        sources[key] ?? null,
        selections,
        (selection) => selection.scalarTimesteps[key],
        signal
      );
    }
  };
  const [windValues] = await Promise.all([
    sampleWindSelections(sources.wind, selections, signal),
    ...Array.from({ length: 3 }, scalarWorker),
  ]);
  if (signal?.aborted) throw new DOMException("Aborted", "AbortError");

  return selections.map((selection, index) => ({
    coordinate: selection.coordinate,
    requestedTime: selection.requestedTime,
    scalars: Object.fromEntries(
      ROUTE_WEATHER_SCALAR_KEYS.map((key) => [
        key,
        resolveWeatherScalarSample(
          sources[key] ?? null,
          selection.scalarTimesteps[key],
          selection.requestedTime,
          scalarValues[key][index]
        ),
      ])
    ) as RouteWeatherSample["scalars"],
    wind: resolveWeatherWindSample(
      sources.wind,
      selection.windTimestep,
      selection.requestedTime,
      windValues[index]
    ),
  }));
}