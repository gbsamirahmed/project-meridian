import maplibregl from "maplibre-gl";

import type { GridPoint } from "../types/gridPoint";

export function renderTemperatureLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[]
): maplibregl.Marker[] {
  const temperatures = gridPoints.map(
    (point) => point.temperature
  );

  const minTemp = Math.min(...temperatures);
  const maxTemp = Math.max(...temperatures);

  return gridPoints.map((point) => {
    const element = document.createElement("div");

    let ratio = 0.5;

    if (maxTemp !== minTemp) {
      ratio =
        (point.temperature - minTemp) /
        (maxTemp - minTemp);
    }

    const hue = 240 - ratio * 240;

    element.className = "temperature-marker";
    element.style.backgroundColor =
      `hsl(${hue}, 85%, 50%)`;

    return new maplibregl.Marker({
      element,
    })
      .setLngLat([
        point.longitude,
        point.latitude,
      ])
      .addTo(map);
  });
}