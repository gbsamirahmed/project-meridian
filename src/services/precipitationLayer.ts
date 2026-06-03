import maplibregl from "maplibre-gl";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "precipitation-source";
const LAYER_ID = "precipitation-layer";

type PrecipitationFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  {
    precipitation: number;
  }
>;

function buildPrecipitationGeoJson(
  gridPoints: GridPoint[],
  forecastHour: number
): PrecipitationFeatureCollection {
  return {
    type: "FeatureCollection",
    features: gridPoints.map((point) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [point.longitude, point.latitude],
      },
      properties: {
        precipitation: point.precipitation[forecastHour],
      },
    })),
  };
}

export function updatePrecipitationLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[],
  forecastHour: number
): void {
  const data = buildPrecipitationGeoJson(gridPoints, forecastHour);

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
    type: "circle",
    source: SOURCE_ID,
    paint: {
      "circle-radius": [
        "interpolate",
        ["linear"],
        ["zoom"],
        7,
        18,
        9,
        34,
        11,
        52,
      ],

      "circle-color": [
        "interpolate",
        ["linear"],
        ["get", "precipitation"],
        0,
        "#dbeafe",
        0.5,
        "#60a5fa",
        1,
        "#2563eb",
        2,
        "#1d4ed8",
        5,
        "#172554",
      ],

      "circle-opacity": [
        "interpolate",
        ["linear"],
        ["get", "precipitation"],
        0,
        0,
        0.2,
        0.2,
        1,
        0.45,
        5,
        0.75,
      ],

      "circle-blur": 0.4,
    },
  });
}

export function removePrecipitationLayer(
  map: maplibregl.Map
): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}