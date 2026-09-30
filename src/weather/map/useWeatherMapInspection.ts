import { useEffect, useState } from "react";
import {
  getScalarTimestepAtTime,
  getVectorTimestepAtTime,
} from "../data/globalWeatherService";
import {
  sampleScalarField,
  sampleVectorField,
} from "../data/numericTileCache";
import type {
  ScalarFieldTimestep,
  ScalarWeatherFieldSource,
  VectorFieldTimestep,
  VectorWeatherFieldSource,
} from "../types/globalWeather";

export interface WeatherInspectionPoint {
  latitude: number;
  longitude: number;
}

interface SampleState<T> {
  key: string;
  value: T | null;
}

function sampleKey(
  manifestId: string,
  timestepId: string,
  point: WeatherInspectionPoint
): string {
  return [
    manifestId,
    timestepId,
    point.longitude.toFixed(5),
    point.latitude.toFixed(5),
  ].join(":");
}

function useScalarInspection(
  label: string,
  point: WeatherInspectionPoint | null,
  source: ScalarWeatherFieldSource | null,
  timestep: ScalarFieldTimestep | null
): number | null | undefined {
  const [sample, setSample] = useState<SampleState<number> | null>(null);
  useEffect(() => {
    if (!point || !source || !timestep) return;
    let current = true;
    const key = sampleKey(source.manifest.id, timestep.id, point);
    sampleScalarField(source, timestep, point.longitude, point.latitude)
      .then((value) => {
        if (current) setSample({ key, value });
      })
      .catch((error: unknown) => {
        if (current) {
          console.error(label, error);
          setSample({ key, value: null });
        }
      });
    return () => {
      current = false;
    };
  }, [label, point, source, timestep]);
  if (!point || !source || !timestep) return undefined;
  return sample?.key === sampleKey(source.manifest.id, timestep.id, point)
    ? sample.value
    : undefined;
}

function useWindInspection(
  point: WeatherInspectionPoint | null,
  source: VectorWeatherFieldSource | null,
  timestep: VectorFieldTimestep | null
): { u: number; v: number } | null | undefined {
  const [sample, setSample] = useState<
    SampleState<{ u: number; v: number }> | null
  >(null);
  useEffect(() => {
    if (!point || !source || !timestep) return;
    let current = true;
    const key = sampleKey(source.manifest.id, timestep.id, point);
    sampleVectorField(source, timestep, point.longitude, point.latitude)
      .then((value) => {
        if (current) setSample({ key, value });
      })
      .catch((error: unknown) => {
        if (current) {
          console.error("Global wind inspection failed", error);
          setSample({ key, value: null });
        }
      });
    return () => {
      current = false;
    };
  }, [point, source, timestep]);
  if (!point || !source || !timestep) return undefined;
  return sample?.key === sampleKey(source.manifest.id, timestep.id, point)
    ? sample.value
    : undefined;
}

export interface WeatherMapInspectionInput {
  point: WeatherInspectionPoint | null;
  validTime: string | null;
  precipitation: ScalarWeatherFieldSource | null;
  clouds: ScalarWeatherFieldSource | null;
  wind: VectorWeatherFieldSource | null;
  temperature: ScalarWeatherFieldSource | null;
  pressure: ScalarWeatherFieldSource | null;
}

export function useWeatherMapInspection(input: WeatherMapInspectionInput) {
  const precipitationTimestep = input.precipitation
    ? getScalarTimestepAtTime(input.precipitation, input.validTime)
    : null;
  const cloudTimestep = input.clouds
    ? getScalarTimestepAtTime(input.clouds, input.validTime)
    : null;
  const windTimestep = input.wind
    ? getVectorTimestepAtTime(input.wind, input.validTime)
    : null;
  const temperatureTimestep = input.temperature
    ? getScalarTimestepAtTime(input.temperature, input.validTime)
    : null;
  const pressureTimestep = input.pressure
    ? getScalarTimestepAtTime(input.pressure, input.validTime)
    : null;

  return {
    precipitationTimestep,
    cloudTimestep,
    windTimestep,
    temperatureTimestep,
    pressureTimestep,
    precipitationValue: useScalarInspection(
      "Global precipitation inspection failed",
      input.point,
      input.precipitation,
      precipitationTimestep
    ),
    cloudValue: useScalarInspection(
      "Global cloud inspection failed",
      input.point,
      input.clouds,
      cloudTimestep
    ),
    temperatureValue: useScalarInspection(
      "Global temperature inspection failed",
      input.point,
      input.temperature,
      temperatureTimestep
    ),
    pressureValue: useScalarInspection(
      "Global pressure inspection failed",
      input.point,
      input.pressure,
      pressureTimestep
    ),
    windValue: useWindInspection(input.point, input.wind, windTimestep),
  };
}