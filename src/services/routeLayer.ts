import maplibregl from "maplibre-gl";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import { unwrapRouteCoordinates } from "./routeGeometry";
import type { RouteCoordinate } from "../types/route";

export const ROUTE_SOURCE_ID = "planned-route-source";
export const ROUTE_FOCUS_SOURCE_ID = "planned-route-focus-source";
export const ROUTE_CASING_LAYER_ID = "planned-route-casing";
export const ROUTE_LINE_LAYER_ID = "planned-route-line";
export const ROUTE_ENDPOINT_LAYER_ID = "planned-route-endpoints";
export const ROUTE_FOCUS_LAYER_ID = "planned-route-focus";

const routeCoordinatesByMap = new WeakMap<maplibregl.Map, RouteCoordinate[]>();

function routeData(coordinates: RouteCoordinate[]): GeoJSON.FeatureCollection {
  if (coordinates.length < 2) {
    return { type: "FeatureCollection", features: [] };
  }
  const displayCoordinates = unwrapRouteCoordinates(coordinates);
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
      data: routeData([]),
    });
    routeCoordinatesByMap.delete(map);
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
  focusedIndex: number | null
): void {
  if (!map.isStyleLoaded()) return;
  ensureRouteLayers(map);
  if (routeCoordinatesByMap.get(map) !== coordinates) {
    const source = map.getSource(ROUTE_SOURCE_ID) as maplibregl.GeoJSONSource;
    source.setData(routeData(coordinates));
    routeCoordinatesByMap.set(map, coordinates);
  }
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
    ROUTE_CASING_LAYER_ID,
  ]) {
    if (map.getLayer(layerId)) map.removeLayer(layerId);
  }
  if (map.getSource(ROUTE_SOURCE_ID)) map.removeSource(ROUTE_SOURCE_ID);
  if (map.getSource(ROUTE_FOCUS_SOURCE_ID)) map.removeSource(ROUTE_FOCUS_SOURCE_ID);
  routeCoordinatesByMap.delete(map);
}
