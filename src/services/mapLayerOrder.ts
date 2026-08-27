import type maplibregl from "maplibre-gl";

export function getFirstSymbolLayerId(
  map: maplibregl.Map
): string | undefined {
  return map
    .getStyle()
    .layers.find(
      (layer) =>
        layer.type === "symbol" &&
        layer.id !== "terrain-stack-boundary-layer"
    )?.id;
}

const FORECAST_OVERLAY_LAYER_ORDER = [
  "temperature-contours-halo",
  "temperature-contours-layer",
  "temperature-contour-labels",
  "pressure-contours-layer",
  "pressure-contour-labels",
  "wind-field-halo",
  "wind-field-layer",
  "precipitation-symbols-layer",
] as const;

export function placeForecastOverlaysInOrder(map: maplibregl.Map): void {
  const firstLabelLayerId = getFirstSymbolLayerId(map);

  for (const layerId of FORECAST_OVERLAY_LAYER_ORDER) {
    if (map.getLayer(layerId)) map.moveLayer(layerId, firstLabelLayerId);
  }
}

export function getWeatherInsertionLayerId(
  map: maplibregl.Map
): string | undefined {
  return (
    map.getStyle().layers.find((layer) => {
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
  const contextSourceLayers = new Set([
    "water",
    "waterway",
    "transportation",
    "boundary",
  ]);
  const contextLayerIds = map
    .getStyle()
    .layers.filter((layer) => {
      if (layer.type === "symbol" || !("source-layer" in layer)) {
        return false;
      }

      return contextSourceLayers.has(layer["source-layer"] ?? "");
    })
    .map((layer) => layer.id);
  const symbolLayerIds = map
    .getStyle()
    .layers.filter(
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
