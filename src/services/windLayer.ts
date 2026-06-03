import maplibregl from "maplibre-gl";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "wind-source";
const LAYER_ID = "wind-layer";

type WindFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  {
    windSpeed: number;
    windDirection: number;
  }
>;

function buildWindGeoJson(
  gridPoints: GridPoint[]
): WindFeatureCollection {
  return {
    type: "FeatureCollection",
    features: gridPoints.map((point) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [point.longitude, point.latitude],
      },
      properties: {
        windSpeed: point.windSpeed,
        windDirection: point.windDirection,
      },
    })),
  };
}

export function updateWindLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[]
): void {
  const data = buildWindGeoJson(gridPoints);

  const existingSource = map.getSource(SOURCE_ID) as
    | maplibregl.GeoJSONSource
    | undefined;

  if (existingSource) {
    existingSource.setData(data);
    return;
  }

  map.addSource(SOURCE_ID, {
    type: "geojson",
    data,
  });

  map.addLayer({
    id: LAYER_ID,
    type: "symbol",
    source: SOURCE_ID,
    layout: {
      "text-field": "➤",
      "text-size": [
        "interpolate",
        ["linear"],
        ["get", "windSpeed"],
        0,
        12,
        20,
        20,
        50,
        30,
      ],
      "text-rotate": ["get", "windDirection"],
      "text-allow-overlap": true,
      "text-ignore-placement": true,
    },
    paint: {
      "text-color": "#0f172a",
      "text-halo-color": "#ffffff",
      "text-halo-width": 1,
      "text-opacity": 0.75,
    },
  });
}

export function removeWindLayer(map: maplibregl.Map): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}