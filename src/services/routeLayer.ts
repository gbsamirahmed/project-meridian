import maplibregl from "maplibre-gl";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import { unwrapRouteCoordinates } from "./routeGeometry";
import { routeConditionColour } from "./routeConditionStyle";
import type { RouteCoordinate } from "../types/route";
import type {
  RouteConditionMode,
  RouteConditions,
} from "../types/routeConditions";

export const ROUTE_SOURCE_ID = "planned-route-source";
export const ROUTE_FOCUS_SOURCE_ID = "planned-route-focus-source";
export const ROUTE_CASING_LAYER_ID = "planned-route-casing";
export const ROUTE_LINE_LAYER_ID = "planned-route-line";
export const ROUTE_CONDITION_LAYER_ID = "planned-route-conditions";
export const ROUTE_ENDPOINT_LAYER_ID = "planned-route-endpoints";
export const ROUTE_FOCUS_LAYER_ID = "planned-route-focus";

const routeSignatureByMap = new WeakMap<maplibregl.Map, unknown[]>();

function routeData(
  coordinates: RouteCoordinate[],
  conditions: RouteConditions | null,
  mode: RouteConditionMode
): GeoJSON.FeatureCollection {
  if (coordinates.length < 2) {
    return { type: "FeatureCollection", features: [] };
  }
  const displayCoordinates = unwrapRouteCoordinates(coordinates);
  const conditionFeatures: GeoJSON.Feature[] =
    mode !== "none" && conditions?.samples.length === coordinates.length
      ? displayCoordinates.slice(0, -1).map((point, index) => ({
          type: "Feature",
          properties: {
            kind: "condition-segment",
            routeSampleIndex: index,
            colour: routeConditionColour(conditions.samples[index], mode),
          },
          geometry: {
            type: "LineString",
            coordinates: [
              [point.longitude, point.latitude],
              [
                displayCoordinates[index + 1].longitude,
                displayCoordinates[index + 1].latitude,
              ],
            ],
          },
        }))
      : [];
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { kind: "route" },
        geometry: {
          type: "LineString",
          coordinates: displayCoordinates.map((point) => [
            point.longitude,
            point.latitude,
          ]),
        },
      },
      ...conditionFeatures,
      {
        type: "Feature",
        properties: { kind: "start" },
        geometry: {
          type: "Point",
          coordinates: [
            displayCoordinates[0].longitude,
            displayCoordinates[0].latitude,
          ],
        },
      },
      {
        type: "Feature",
        properties: { kind: "finish" },
        geometry: {
          type: "Point",
          coordinates: [
            displayCoordinates[displayCoordinates.length - 1].longitude,
            displayCoordinates[displayCoordinates.length - 1].latitude,
          ],
        },
      },
    ],
  };
}

function focusData(coordinate: RouteCoordinate | null): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: coordinate
      ? [
          {
            type: "Feature",
            properties: { kind: "focus" },
            geometry: {
              type: "Point",
              coordinates: [coordinate.longitude, coordinate.latitude],
            },
          },
        ]
      : [],
  };
}

function ensureRouteLayers(map: maplibregl.Map): void {
  if (!map.getSource(ROUTE_SOURCE_ID)) {
    map.addSource(ROUTE_SOURCE_ID, {
      type: "geojson",
      data: routeData([], null, "none"),
    });
    routeSignatureByMap.delete(map);
  }
  if (!map.getSource(ROUTE_FOCUS_SOURCE_ID)) {
    map.addSource(ROUTE_FOCUS_SOURCE_ID, {
      type: "geojson",
      data: focusData(null),
    });
  }
  const beforeId = getFirstSymbolLayerId(map);
  if (!map.getLayer(ROUTE_CASING_LAYER_ID)) {
    map.addLayer(
      {
        id: ROUTE_CASING_LAYER_ID,
        type: "line",
        source: ROUTE_SOURCE_ID,
        filter: ["==", ["get", "kind"], "route"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#0a1110",
          "line-opacity": 0.82,
          "line-width": ["interpolate", ["linear"], ["zoom"], 3, 3, 10, 7],
        },
      },
      beforeId
    );
  }
  if (!map.getLayer(ROUTE_LINE_LAYER_ID)) {
    map.addLayer(
      {
        id: ROUTE_LINE_LAYER_ID,
        type: "line",
        source: ROUTE_SOURCE_ID,
        filter: ["==", ["get", "kind"], "route"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#ff7652",
          "line-opacity": 0.96,
          "line-width": ["interpolate", ["linear"], ["zoom"], 3, 1.5, 10, 3.8],
        },
      },
      beforeId
    );
  }
  if (!map.getLayer(ROUTE_CONDITION_LAYER_ID)) {
    map.addLayer(
      {
        id: ROUTE_CONDITION_LAYER_ID,
        type: "line",
        source: ROUTE_SOURCE_ID,
        filter: ["==", ["get", "kind"], "condition-segment"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ["coalesce", ["get", "colour"], "#7b8581"],
          "line-opacity": 0.98,
          "line-width": ["interpolate", ["linear"], ["zoom"], 3, 2.2, 10, 4.5],
        },
      },
      beforeId
    );
  }
  if (!map.getLayer(ROUTE_ENDPOINT_LAYER_ID)) {
    map.addLayer(
      {
        id: ROUTE_ENDPOINT_LAYER_ID,
        type: "circle",
        source: ROUTE_SOURCE_ID,
        filter: ["in", ["get", "kind"], ["literal", ["start", "finish"]]],
        paint: {
          "circle-radius": 5,
          "circle-color": [
            "case",
            ["==", ["get", "kind"], "start"],
            "#87d5a5",
            "#ff7652",
          ],
          "circle-stroke-color": "#f7f2e8",
          "circle-stroke-width": 1.5,
        },
      },
      beforeId
    );
  }
  if (!map.getLayer(ROUTE_FOCUS_LAYER_ID)) {
    map.addLayer(
      {
        id: ROUTE_FOCUS_LAYER_ID,
        type: "circle",
        source: ROUTE_FOCUS_SOURCE_ID,
        filter: ["==", ["get", "kind"], "focus"],
        paint: {
          "circle-radius": 7,
          "circle-color": "#f7f2e8",
          "circle-stroke-color": "#ff7652",
          "circle-stroke-width": 3,
        },
      },
      beforeId
    );
  }
}

export function updateRouteLayer(
  map: maplibregl.Map,
  coordinates: RouteCoordinate[],
  focusedIndex: number | null,
  conditions: RouteConditions | null = null,
  mode: RouteConditionMode = "none"
): void {
  if (!map.isStyleLoaded()) return;
  ensureRouteLayers(map);
  const signature = [coordinates, conditions, mode];
  const previousSignature = routeSignatureByMap.get(map);
  if (
    !previousSignature ||
    previousSignature.some((value, index) => value !== signature[index])
  ) {
    const source = map.getSource(ROUTE_SOURCE_ID) as maplibregl.GeoJSONSource;
    source.setData(routeData(coordinates, conditions, mode));
    routeSignatureByMap.set(map, signature);
  }
  const hasConditionSegments =
    mode !== "none" && conditions?.samples.length === coordinates.length;
  map.setLayoutProperty(
    ROUTE_LINE_LAYER_ID,
    "visibility",
    hasConditionSegments ? "none" : "visible"
  );
  map.setLayoutProperty(
    ROUTE_CONDITION_LAYER_ID,
    "visibility",
    hasConditionSegments ? "visible" : "none"
  );
  const focus =
    focusedIndex === null
      ? null
      : coordinates[Math.max(0, Math.min(coordinates.length - 1, focusedIndex))] ?? null;
  const focusSource = map.getSource(ROUTE_FOCUS_SOURCE_ID) as maplibregl.GeoJSONSource;
  focusSource.setData(focusData(focus));
  const beforeId = getFirstSymbolLayerId(map);
  for (const layerId of [
    ROUTE_CASING_LAYER_ID,
    ROUTE_LINE_LAYER_ID,
    ROUTE_CONDITION_LAYER_ID,
    ROUTE_ENDPOINT_LAYER_ID,
    ROUTE_FOCUS_LAYER_ID,
  ]) {
    if (map.getLayer(layerId)) map.moveLayer(layerId, beforeId);
  }
}

export function removeRouteLayer(map: maplibregl.Map): void {
  for (const layerId of [
    ROUTE_FOCUS_LAYER_ID,
    ROUTE_ENDPOINT_LAYER_ID,
    ROUTE_LINE_LAYER_ID,
    ROUTE_CONDITION_LAYER_ID,
    ROUTE_CASING_LAYER_ID,
  ]) {
    if (map.getLayer(layerId)) map.removeLayer(layerId);
  }
  if (map.getSource(ROUTE_SOURCE_ID)) map.removeSource(ROUTE_SOURCE_ID);
  if (map.getSource(ROUTE_FOCUS_SOURCE_ID)) map.removeSource(ROUTE_FOCUS_SOURCE_ID);
  routeSignatureByMap.delete(map);
}
