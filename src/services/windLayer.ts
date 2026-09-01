import type maplibregl from "maplibre-gl";

import type { Basemap } from "../types/layer";
import type {
  VectorWeatherFieldSource,
  VectorWeatherTimestep,
} from "../types/globalWeather";
import { GlobalWindVectorField } from "./globalWindSource";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import {
  WIND_PARTICLE_LAYER_ID,
  WindParticleLayer,
} from "./windParticleLayer";

let activeLayer: WindParticleLayer | null = null;
let updateGeneration = 0;
let pendingField: GlobalWindVectorField | null = null;

function ensureLayer(map: maplibregl.Map): WindParticleLayer {
  if (!map.getLayer(WIND_PARTICLE_LAYER_ID)) {
    activeLayer = new WindParticleLayer();
    map.addLayer(activeLayer, getFirstSymbolLayerId(map));
  } else if (!activeLayer) {
    map.removeLayer(WIND_PARTICLE_LAYER_ID);
    activeLayer = new WindParticleLayer();
    map.addLayer(activeLayer, getFirstSymbolLayerId(map));
  }
  return activeLayer;
}

export function updateGlobalWindLayer(
  map: maplibregl.Map,
  source: VectorWeatherFieldSource,
  timestep: VectorWeatherTimestep,
  basemap: Basemap
): void {
  const layer = ensureLayer(map);
  layer.setBasemap(basemap);
  layer.setEnabled(true);
  const signature = `${source.manifest.id}:${timestep.id}`;
  if (layer.getFieldSignature() === signature) {
    layer.scheduleCoverageRefresh();
    return;
  }
  if (pendingField?.signature === signature) return;
  const generation = ++updateGeneration;
  pendingField?.dispose();
  const field = new GlobalWindVectorField(source, timestep);
  pendingField = field;
  void field
    .prepareCoverage(map)
    .then((ready) => {
      if (generation !== updateGeneration || pendingField !== field) {
        field.dispose();
        return;
      }
      pendingField = null;
      if (!ready) {
        field.dispose();
        return;
      }
      layer.setField(field);
    })
    .catch(() => {
      if (generation === updateGeneration && pendingField === field) {
        pendingField = null;
      }
      field.dispose();
    });
}

export function setWindLayerEnabled(
  _map: maplibregl.Map,
  enabled: boolean
): void {
  activeLayer?.setEnabled(enabled);
}

export function removeWindLayer(map: maplibregl.Map): void {
  updateGeneration++;
  pendingField?.dispose();
  pendingField = null;

  if (map.getLayer(WIND_PARTICLE_LAYER_ID)) {
    map.removeLayer(WIND_PARTICLE_LAYER_ID);
  }

  activeLayer = null;
}
