import type * as maplibregl from "maplibre-gl";
import { getFirstSymbolLayerId } from "../../atlas/map/mapLayerAnchors";

const FILLED_WEATHER_LAYER_ORDER = [
  "global-cloud-cover-layer-a",
  "global-cloud-cover-layer-b",
  "global-precipitation-layer-a",
  "global-precipitation-layer-b",
] as const;

const WEATHER_OVERLAY_LAYER_ORDER = [
  "temperature-contours-halo",
  "temperature-contours-layer",
  "temperature-contour-labels",
  "pressure-contours-layer",
  "pressure-contour-labels",
  "wind-particle-layer",
] as const;

export function getWeatherInsertionLayerId(map: maplibregl.Map): string | undefined {
  return (
    map.getStyle()?.layers?.find((layer) => {
      if (!("source-layer" in layer)) return false;
      return (
        layer["source-layer"] === "transportation" ||
        layer["source-layer"] === "boundary"
      );
    })?.id ?? getFirstSymbolLayerId(map)
  );
}

export function placeWeatherLayersInOrder(map: maplibregl.Map): void {
  if (!map.getStyle()?.layers) return;
  const insertionLayerId = getWeatherInsertionLayerId(map);
  for (const layerId of FILLED_WEATHER_LAYER_ORDER) {
    if (map.getLayer(layerId)) map.moveLayer(layerId, insertionLayerId);
  }
  const firstLabelLayerId = getFirstSymbolLayerId(map);
  for (const layerId of WEATHER_OVERLAY_LAYER_ORDER) {
    if (map.getLayer(layerId)) map.moveLayer(layerId, firstLabelLayerId);
  }
}
