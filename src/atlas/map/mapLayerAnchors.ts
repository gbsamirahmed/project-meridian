import type * as maplibregl from "maplibre-gl";

export function getFirstSymbolLayerId(map: maplibregl.Map): string | undefined {
  return map
    .getStyle()
    ?.layers?.find(
      (layer) =>
        layer.type === "symbol" && layer.id !== "terrain-stack-boundary-layer"
    )?.id;
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
  const contextLayerIds = layers
    .filter((layer) => {
      if (layer.type === "symbol" || !("source-layer" in layer)) return false;
      return contextSourceLayers.has(layer["source-layer"] ?? "");
    })
    .map((layer) => layer.id);
  const symbolLayerIds = layers
    .filter(
      (layer) => layer.type === "symbol" && layer.id !== stackBoundaryLayerId
    )
    .map((layer) => layer.id);

  for (const layerId of contextLayerIds) map.moveLayer(layerId);
  for (const layerId of symbolLayerIds) map.moveLayer(layerId);
}
