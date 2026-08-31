import type maplibregl from "maplibre-gl";

import type { Basemap } from "../types/layer";
import type { WeatherGrid } from "../types/weatherGrid";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import { createForecastWindField } from "./windField";
import {
  WIND_PARTICLE_LAYER_ID,
  WindParticleLayer,
} from "./windParticleLayer";

let activeLayer: WindParticleLayer | null = null;
let coverageVisible = true;

export function updateWindLayer(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number,
  basemap: Basemap
): void {
  if (!map.getLayer(WIND_PARTICLE_LAYER_ID)) {
    activeLayer = new WindParticleLayer();
    map.addLayer(activeLayer, getFirstSymbolLayerId(map));
  } else if (!activeLayer) {
    // A development hot reload can leave a custom layer owned by the previous
    // module instance. Replacing it keeps one renderer and one animation loop.
    map.removeLayer(WIND_PARTICLE_LAYER_ID);
    activeLayer = new WindParticleLayer();
    map.addLayer(activeLayer, getFirstSymbolLayerId(map));
  }

  activeLayer.setField(createForecastWindField(grid, forecastHour));
  activeLayer.setBasemap(basemap);
  activeLayer.setEnabled(true);
  activeLayer.setCoverageVisible(coverageVisible);
}

export function setWindLayerCoverage(
  _map: maplibregl.Map,
  visible: boolean
): void {
  coverageVisible = visible;
  activeLayer?.setCoverageVisible(visible);
}

export function setWindLayerEnabled(
  _map: maplibregl.Map,
  enabled: boolean
): void {
  activeLayer?.setEnabled(enabled);
}

export function removeWindLayer(map: maplibregl.Map): void {
  coverageVisible = true;

  if (map.getLayer(WIND_PARTICLE_LAYER_ID)) {
    map.removeLayer(WIND_PARTICLE_LAYER_ID);
  }

  activeLayer = null;
}
