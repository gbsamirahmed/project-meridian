import type maplibregl from "maplibre-gl";

export function getFirstSymbolLayerId(
  map: maplibregl.Map
): string | undefined {
  return map
    .getStyle()
    ?.layers?.find(
      (layer) =>
        layer.type === "symbol" &&
        layer.id !== "terrain-stack-boundary-layer"
    )?.id;
}

const FILLED_WEATHER_LAYER_ORDER = [
  "weather-clouds-layer-a",
  "weather-clouds-layer-b",
  "global-precipitation-layer-a",
  "global-precipitation-layer-b",
  "weather-precipitation-layer-a",
  "weather-precipitation-layer-b",
] as const;

const FORECAST_OVERLAY_LAYER_ORDER = [
  "temperature-contours-halo",
  "temperature-contours-layer",
  "temperature-contour-labels",
  "pressure-contours-layer",
  "pressure-contour-labels",
  "wind-particle-layer",
  "precipitation-symbols-layer",
] as const;

export function placeForecastOverlaysInOrder(map: maplibregl.Map): void {
  if (!map.getStyle()?.layers) return;
  const weatherInsertionLayerId = getWeatherInsertionLayerId(map);

  for (const layerId of FILLED_WEATHER_LAYER_ORDER) {
    if (map.getLayer(layerId)) map.moveLayer(layerId, weatherInsertionLayerId);
  }

  const firstLabelLayerId = getFirstSymbolLayerId(map);

  for (const layerId of FORECAST_OVERLAY_LAYER_ORDER) {
    if (map.getLayer(layerId)) map.moveLayer(layerId, firstLabelLayerId);
  }
}

export function getWeatherInsertionLayerId(
  map: maplibregl.Map
): string | undefined {
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

export function placeGeographicContextAboveOverlays(
  map: maplibregl.Map,
  stackBoundaryLayerId?: string
): void {
  const layers = map.getStyle()?.layers;
  if (!layers) return;
  const contextSourceLayers = new Set([
    "water",
    "waterway",
    "transportation",
    "boundary",
  ]);
  const contextLayerIds = layers.filter((layer) => {
      if (layer.type === "symbol" || !("source-layer" in layer)) {
        return false;
      }

      return contextSourceLayers.has(layer["source-layer"] ?? "");
    })
    .map((layer) => layer.id);
  const symbolLayerIds = layers.filter(
      (layer) =>
        layer.type === "symbol" && layer.id !== stackBoundaryLayerId
    )
    .map((layer) => layer.id);

  for (const layerId of contextLayerIds) {
    map.moveLayer(layerId);
  }

  for (const layerId of symbolLayerIds) {
    map.moveLayer(layerId);
  }
}
