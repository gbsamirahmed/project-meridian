import type * as maplibregl from "maplibre-gl";

import type { Basemap } from "../../atlas/map/mapTypes";
import { getScalarTimestepAtTime, getVectorTimestepAtTime } from "../data/globalWeatherService";
import type {
  ScalarWeatherFieldSource,
  VectorWeatherFieldSource,
} from "../types/globalWeather";
import {
  removeGlobalCloudLayer,
  setGlobalCloudEnabled,
  updateGlobalCloudLayer,
} from "./globalCloudLayer";
import {
  removeGlobalPrecipitationLayer,
  setGlobalPrecipitationEnabled,
  updateGlobalPrecipitationLayer,
} from "./globalPrecipitationLayer";
import {
  removePressureLayer,
  setPressureLayerEnabled,
  updatePressureLayer,
} from "./pressureLayer";
import {
  removeTemperatureContourLayer,
  setTemperatureContourEnabled,
  updateTemperatureContourLayer,
} from "./temperatureContourLayer";
import {
  removeWindLayer,
  setWindLayerEnabled,
  updateGlobalWindLayer,
} from "./windLayer";
import { placeWeatherLayersInOrder } from "./weatherLayerOrder";

export interface WeatherMapOverlays {
  precipitation: boolean;
  clouds: boolean;
  temperatureContours: boolean;
  pressureIsobars: boolean;
  windFlow: boolean;
}

export interface WeatherMapState {
  basemap: Basemap;
  overlays: WeatherMapOverlays;
  precipitation: ScalarWeatherFieldSource | null;
  clouds: ScalarWeatherFieldSource | null;
  wind: VectorWeatherFieldSource | null;
  temperature: ScalarWeatherFieldSource | null;
  pressure: ScalarWeatherFieldSource | null;
  validTime: string | null;
}

/** Concrete Weather-owned map integration with a pending-until-renderable contract. */
export class WeatherMapController {
  private readonly map: maplibregl.Map;
  private readonly onRendered: () => void;
  private state: WeatherMapState | null = null;
  private pending = false;

  constructor(map: maplibregl.Map, onRendered: () => void = () => undefined) {
    this.map = map;
    this.onRendered = onRendered;
  }

  update(state: WeatherMapState): void {
    this.state = state;
    this.pending = true;
    this.flushIfRenderable();
  }

  styleChanged(): void {
    this.pending = true;
    this.flushIfRenderable();
  }

  viewportChanged(): void {
    this.pending = true;
    this.flushIfRenderable();
  }

  mapBecameRenderable(): void {
    this.flushIfRenderable();
  }

  destroy(): void {
    removeGlobalCloudLayer(this.map);
    removeGlobalPrecipitationLayer(this.map);
    removeTemperatureContourLayer(this.map);
    removePressureLayer(this.map);
    removeWindLayer(this.map);
    this.state = null;
    this.pending = false;
  }

  private flushIfRenderable(): void {
    if (!this.pending || !this.state || !this.map.isStyleLoaded()) return;
    const state = this.state;
    const cloud = state.clouds
      ? getScalarTimestepAtTime(state.clouds, state.validTime)
      : null;
    const precipitation = state.precipitation
      ? getScalarTimestepAtTime(state.precipitation, state.validTime)
      : null;
    const temperature = state.temperature
      ? getScalarTimestepAtTime(state.temperature, state.validTime)
      : null;
    const pressure = state.pressure
      ? getScalarTimestepAtTime(state.pressure, state.validTime)
      : null;
    const wind = state.wind
      ? getVectorTimestepAtTime(state.wind, state.validTime)
      : null;

    if (state.overlays.clouds && state.clouds && cloud) {
      updateGlobalCloudLayer(this.map, state.clouds, cloud);
    } else {
      setGlobalCloudEnabled(this.map, false);
    }
    if (state.overlays.precipitation && state.precipitation && precipitation) {
      updateGlobalPrecipitationLayer(this.map, state.precipitation, precipitation);
    } else {
      setGlobalPrecipitationEnabled(this.map, false);
    }
    if (state.overlays.temperatureContours && state.temperature && temperature) {
      updateTemperatureContourLayer(this.map, state.temperature, temperature);
    } else {
      setTemperatureContourEnabled(this.map, false);
    }
    if (state.overlays.pressureIsobars && state.pressure && pressure) {
      updatePressureLayer(this.map, state.pressure, pressure);
    } else {
      setPressureLayerEnabled(this.map, false);
    }
    if (state.overlays.windFlow && state.wind && wind) {
      updateGlobalWindLayer(this.map, state.wind, wind, state.basemap);
    } else {
      setWindLayerEnabled(this.map, false);
    }
    placeWeatherLayersInOrder(this.map);
    this.onRendered();
    this.pending = false;
  }
}
