import maplibregl from "maplibre-gl";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "pressure-source";
const LAYER_ID = "pressure-layer";

type PressureFeatureCollection = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  {
    pressure: number;
    ratio: number;
  }
>;

function buildPressureGeoJson(
  gridPoints: GridPoint[]
): PressureFeatureCollection {
  const pressures = gridPoints.map(
    (point) => point.pressure
  );

  const minPressure = Math.min(...pressures);
  const maxPressure = Math.max(...pressures);

  return {
    type: "FeatureCollection",
    features: gridPoints.map((point) => {
      let ratio = 0.5;

      if (maxPressure !== minPressure) {
        ratio =
          (point.pressure - minPressure) /
          (maxPressure - minPressure);
      }

      return {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [
            point.longitude,
            point.latitude,
          ],
        },
        properties: {
          pressure: point.pressure,
          ratio,
        },
      };
    }),
  };
}

export function updatePressureLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[]
): void {
  const data = buildPressureGeoJson(gridPoints);

  const existingSource = map.getSource(
    SOURCE_ID
  ) as maplibregl.GeoJSONSource | undefined;

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
        ["get", "ratio"],
        0,
        "#7f1d1d",
        0.25,
        "#dc2626",
        0.5,
        "#f59e0b",
        0.75,
        "#22c55e",
        1,
        "#2563eb",
      ],

      "circle-opacity": 0.45,
      "circle-blur": 0.4,
    },
  });
}

export function removePressureLayer(
  map: maplibregl.Map
): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}