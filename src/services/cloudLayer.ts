import maplibregl from "maplibre-gl";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "cloud-source";
const LAYER_ID = "cloud-layer";

type CloudFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  {
    cloudCover: number;
  }
>;

function buildCloudGeoJson(
  gridPoints: GridPoint[],
  forecastHour: number
): CloudFeatureCollection {
  return {
    type: "FeatureCollection",
    features: gridPoints.map((point) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [point.longitude, point.latitude],
      },
      properties: {
        cloudCover: point.cloudCover[forecastHour],
      },
    })),
  };
}

export function updateCloudLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[],
  forecastHour: number
): void {
  const data = buildCloudGeoJson(gridPoints, forecastHour);

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
        ["get", "cloudCover"],
        0,
        "#ffffff",
        50,
        "#cbd5e1",
        100,
        "#64748b",
      ],
      "circle-opacity": [
        "interpolate",
        ["linear"],
        ["get", "cloudCover"],
        0,
        0,
        30,
        0.2,
        70,
        0.45,
        100,
        0.65,
      ],
      "circle-blur": 0.4,
    },
  });
}

export function removeCloudLayer(map: maplibregl.Map): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}