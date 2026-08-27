import maplibregl from "maplibre-gl";

import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";
import { WEATHER_GRID_MIN_ZOOM } from "../config/gridConfig";
import { buildContourGeoJson } from "./contourGeometry";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import { buildWeatherMatrix } from "./weatherMatrix";

import type { WeatherGrid } from "../types/weatherGrid";

const SOURCE_ID = "temperature-contours-source";
const HALO_LAYER_ID = "temperature-contours-halo";
const LINE_LAYER_ID = "temperature-contours-layer";
const LABEL_LAYER_ID = "temperature-contour-labels";

let activeSignature: string | null = null;
let coverageVisible = true;

function chooseInterval(range: number): number | null {
  if (range < 0.6) return null;
  if (range < 4) return 1;
  if (range < 10) return 2;
  return 5;
}

function buildTemperatureContours(
  grid: WeatherGrid,
  forecastHour: number
) {
  const matrix = buildWeatherMatrix(
    grid.points,
    grid.rows,
    grid.columns,
    forecastHour,
    (point, hour) => point.temperature[hour]
  );
  const values = matrix.flat().filter(Number.isFinite);

  if (values.length === 0) {
    return buildContourGeoJson({
      matrix: [],
      bounds: grid.bounds,
      levels: [],
      formatLabel: String,
    });
  }

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const interval = chooseInterval(maximum - minimum);

  if (interval === null) {
    return buildContourGeoJson({
      matrix,
      bounds: grid.bounds,
      levels: [],
      formatLabel: String,
    });
  }

  const levels: number[] = [];
  const firstLevel = Math.ceil(minimum / interval) * interval;

  for (let level = firstLevel; level <= maximum; level += interval) {
    if (level > minimum && level < maximum) levels.push(level);
  }

  return buildContourGeoJson({
    matrix,
    bounds: grid.bounds,
    levels,
    formatLabel: (level) => `${level}°`,
    isEmphasized: (level) => level === 0,
  });
}

function setLayerOpacity(map: maplibregl.Map, visible: boolean): void {
  if (map.getLayer(HALO_LAYER_ID)) {
    map.setPaintProperty(
      HALO_LAYER_ID,
      "line-opacity",
      visible ? LAYER_VISUAL_STRENGTHS.temperatureHalo : 0
    );
  }

  if (map.getLayer(LINE_LAYER_ID)) {
    map.setPaintProperty(
      LINE_LAYER_ID,
      "line-opacity",
      visible ? LAYER_VISUAL_STRENGTHS.temperatureContour : 0
    );
  }

  if (map.getLayer(LABEL_LAYER_ID)) {
    map.setPaintProperty(LABEL_LAYER_ID, "text-opacity", visible ? 0.92 : 0);
  }
}

export function updateTemperatureContourLayer(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number
): void {
  const signature = `${grid.fetchedAt}:${forecastHour}`;
  const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

  if (signature !== activeSignature || !source) {
    const data = buildTemperatureContours(grid, forecastHour);

    if (source) source.setData(data);
    else map.addSource(SOURCE_ID, { type: "geojson", data });

    activeSignature = signature;
  }

  const beforeId = getFirstSymbolLayerId(map);

  if (!map.getLayer(HALO_LAYER_ID)) {
    map.addLayer(
      {
        id: HALO_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#17211f",
          "line-width": ["case", ["get", "emphasized"], 2.7, 1.75],
          "line-opacity": LAYER_VISUAL_STRENGTHS.temperatureHalo,
          "line-blur": 0.35,
        },
      },
      beforeId
    );
  }

  if (!map.getLayer(LINE_LAYER_ID)) {
    map.addLayer(
      {
        id: LINE_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": [
            "case",
            ["get", "emphasized"],
            "#dff8ff",
            "#ffb36b",
          ],
          "line-width": ["case", ["get", "emphasized"], 1.85, 1.1],
          "line-opacity": LAYER_VISUAL_STRENGTHS.temperatureContour,
          "line-dasharray": [3, 2],
        },
      },
      beforeId
    );
  }

  if (!map.getLayer(LABEL_LAYER_ID)) {
    map.addLayer(
      {
        id: LABEL_LAYER_ID,
        type: "symbol",
        source: SOURCE_ID,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        filter: ["==", ["geometry-type"], "Point"],
        layout: {
          "text-field": ["get", "label"],
          "text-font": ["Noto Sans Regular"],
          "text-size": 10.5,
          "text-allow-overlap": false,
        },
        paint: {
          "text-color": "#fff3e4",
          "text-halo-color": "#17211f",
          "text-halo-width": 1.6,
          "text-opacity": 0.92,
        },
      },
      beforeId
    );
  }

  setLayerOpacity(map, coverageVisible);
}

export function setTemperatureContourCoverage(
  map: maplibregl.Map,
  visible: boolean
): void {
  coverageVisible = visible;
  setLayerOpacity(map, visible);
}

export function removeTemperatureContourLayer(map: maplibregl.Map): void {
  activeSignature = null;
  coverageVisible = true;

  if (map.getLayer(LABEL_LAYER_ID)) map.removeLayer(LABEL_LAYER_ID);
  if (map.getLayer(LINE_LAYER_ID)) map.removeLayer(LINE_LAYER_ID);
  if (map.getLayer(HALO_LAYER_ID)) map.removeLayer(HALO_LAYER_ID);
  if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
}
