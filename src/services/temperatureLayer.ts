import maplibregl from "maplibre-gl";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "temperature-source";
const LAYER_ID = "temperature-layer";

type TemperatureFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  {
    temperature: number;
    ratio: number;
  }
>;

function buildTemperatureGeoJson(
  gridPoints: GridPoint[]
): TemperatureFeatureCollection {
  const temperatures = gridPoints.map((point) => point.temperature);

  const minTemp = Math.min(...temperatures);
  const maxTemp = Math.max(...temperatures);

  return {
    type: "FeatureCollection",
    features: gridPoints.map((point) => {
      let ratio = 0.5;

      if (maxTemp !== minTemp) {
        ratio = (point.temperature - minTemp) / (maxTemp - minTemp);
      }

      return {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [point.longitude, point.latitude],
        },
        properties: {
          temperature: point.temperature,
          ratio,
        },
      };
    }),
  };
}

export function updateTemperatureLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[]
): void {
  const data = buildTemperatureGeoJson(gridPoints);

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
        32,
        11,
        48,
      ],
      "circle-color": [
        "interpolate",
        ["linear"],
        ["get", "ratio"],
        0,
        "#1d4ed8",
        0.25,
        "#06b6d4",
        0.5,
        "#22c55e",
        0.75,
        "#facc15",
        1,
        "#ef4444",
      ],
      "circle-opacity": 0.45,
      "circle-blur": 0.35,
    },
  });
}

export function removeTemperatureLayer(map: maplibregl.Map): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}