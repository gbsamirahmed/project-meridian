import { geodesicDistanceM, shortestLongitudeDelta } from "./routeGeometry";
import { buildDerivedRouteConditions } from "./derivedRouteConditions";

import type { JourneySchedule, RouteCoordinate, TerrainRoute } from "../types/route";
import type {
  AvailableWindRouteCondition,
  RouteConditionSample,
  RouteConditionSummary,
  RouteConditions,
  RouteRelativeWind,
  RouteScalarKey,
  ScalarRouteCondition,
  WindRouteCondition,
} from "../types/routeConditions";
import type {
  RouteWeatherSample,
  WeatherScalarSample,
  WeatherWindSample,
} from "../../weather/types/routeWeather";

const SCALAR_KEYS: RouteScalarKey[] = [
  "temperature",
  "precipitation",
  "cloud",
  "gust",
  "visibility",
  "freezingLevel",
  "highestFreezingLevel",
  "cloudCeiling",
];

function radians(value: number): number {
  return (value * Math.PI) / 180;
}

export function routeBearingDegrees(
  coordinates: RouteCoordinate[],
  index: number
): number | null {
  if (coordinates.length < 2 || index < 0 || index >= coordinates.length) {
    return null;
  }
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

export function interpretScalarWeatherSample(
  sample: WeatherScalarSample
): ScalarRouteCondition {
  return sample;
}

export function interpretWindWeatherSample(
  sample: WeatherWindSample,
  bearingDegrees: number | null
): WindRouteCondition {
  if (sample.state === "unavailable") return sample;
  return {
    ...sample,
    relative: deriveRouteRelativeWind(sample.uMs, sample.vMs, bearingDegrees),
  } satisfies AvailableWindRouteCondition;
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
  const gusts: number[] = [];
  const visibility: number[] = [];
  const freezing: number[] = [];
  for (const sample of samples) {
    if (sample.weather.gust?.state === "available") {
      gusts.push(sample.weather.gust.value);
    }
    if (sample.weather.visibility?.state === "available") {
      visibility.push(sample.weather.visibility.value);
    }
    if (sample.weather.freezingLevel?.state === "available") {
      freezing.push(sample.weather.freezingLevel.value);
    }
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
    gustMaximumMs: gusts.length ? Math.max(...gusts) : null,
    visibilityMinimumM: visibility.length ? Math.min(...visibility) : null,
    freezingLevelRangeGpm: numericRange(freezing),
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

/** Interprets provider-neutral Weather samples relative to a Traverse route. */
export function buildRouteConditions(
  route: TerrainRoute,
  schedule: JourneySchedule,
  weatherSamples: RouteWeatherSample[]
): RouteConditions {
  if (
    route.id !== schedule.routeId ||
    route.samples.length !== schedule.samples.length ||
    route.samples.length !== weatherSamples.length
  ) {
    throw new Error("Route terrain, journey schedule, and weather samples do not match.");
  }

  const coordinates = route.samples.map((sample) => ({
    longitude: sample.longitude,
    latitude: sample.latitude,
  }));
  const samples: RouteConditionSample[] = route.samples.map((sample, index) => {
    const journey = schedule.samples[index];
    const weather = weatherSamples[index];
    if (
      !journey ||
      journey.routeSampleIndex !== sample.index ||
      !weather ||
      weather.requestedTime !== journey.arrivalTime
    ) {
      throw new Error("Route, journey, and weather samples are not aligned.");
    }
    const bearing = routeBearingDegrees(coordinates, index);
    return {
      routeSampleIndex: sample.index,
      coordinate: weather.coordinate,
      cumulativeDistanceM: sample.cumulativeDistanceM,
      routeProgress:
        sample.cumulativeDistanceM / Math.max(1, route.totalDistanceM),
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
        ...Object.fromEntries(
          SCALAR_KEYS.map((key) => [
            key,
            interpretScalarWeatherSample(weather.scalars[key]),
          ])
        ) as Record<RouteScalarKey, ScalarRouteCondition>,
        wind: interpretWindWeatherSample(weather.wind, bearing),
      },
    };
  });

  return {
    routeId: route.id,
    generatedAt: new Date().toISOString(),
    samples,
    coverage: {
      ...Object.fromEntries(
        SCALAR_KEYS.map((key) => [
          key,
          coverageFor(samples, (sample) => sample.weather[key]),
        ])
      ) as Record<
        RouteScalarKey,
        RouteConditions["coverage"]["temperature"]
      >,
      wind: coverageFor(samples, (sample) => sample.weather.wind),
    },
    summary: buildRouteConditionSummary(samples),
    derived: buildDerivedRouteConditions(route.id, samples),
  };
}