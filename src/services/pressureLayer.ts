import maplibregl from "maplibre-gl";

import { LAYER_VISUAL_STRENGTHS } from "../config/layerVisuals";
import { WEATHER_GRID_MIN_ZOOM } from "../config/gridConfig";
import { buildContourGeoJson } from "./contourGeometry";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import { buildWeatherMatrix } from "./weatherMatrix";

import type { WeatherGrid } from "../types/weatherGrid";

const SOURCE_ID = "pressure-contours-source";
const LINE_LAYER_ID = "pressure-contours-layer";
const LABEL_LAYER_ID = "pressure-contour-labels";
const PRESSURE_MAX_ZOOM = 10.8;

let activeSignature: string | null = null;
let coverageVisible = true;
let layerEnabled = true;

function choosePressureInterval(range: number): number | null {
  if (range < 0.9) return null;
  if (range < 3) return 1;
  if (range < 7) return 2;
  return 4;
}

function buildPressureContours(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number
) {
  if (map.getZoom() > PRESSURE_MAX_ZOOM) {
    return buildContourGeoJson({
      matrix: [],
      bounds: grid.bounds,
      levels: [],
      formatLabel: String,
    });
  }

  const matrix = buildWeatherMatrix(
    grid.points,
    grid.rows,
    grid.columns,
    forecastHour,
    (point, hour) => point.pressure[hour]
  );
  const values = matrix.flat().filter(Number.isFinite);

  if (values.length === 0) {
    return buildContourGeoJson({
      matrix,
      bounds: grid.bounds,
      levels: [],
      formatLabel: String,
    });
  }

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const interval = choosePressureInterval(maximum - minimum);

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
    formatLabel: (level) => `${level}`,
  });
}

function setLayerOpacity(map: maplibregl.Map, visible: boolean): void {
  if (map.getLayer(LINE_LAYER_ID)) {
    map.setPaintProperty(
      LINE_LAYER_ID,
      "line-opacity",
      visible && layerEnabled
        ? [
            "interpolate",
            ["linear"],
            ["zoom"],
            5,
            LAYER_VISUAL_STRENGTHS.pressureLine,
            9,
            0.7,
            PRESSURE_MAX_ZOOM,
            0,
          ]
        : 0
    );
  }

  if (map.getLayer(LABEL_LAYER_ID)) {
    map.setPaintProperty(
      LABEL_LAYER_ID,
      "text-opacity",
      visible && layerEnabled
        ? [
            "interpolate",
            ["linear"],
            ["zoom"],
            5,
            LAYER_VISUAL_STRENGTHS.pressureLabel,
            9,
            0.78,
            PRESSURE_MAX_ZOOM,
            0,
          ]
        : 0
    );
  }
}

export function updatePressureLayer(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number
): void {
  layerEnabled = true;
  const zoomBucket = map.getZoom() > PRESSURE_MAX_ZOOM ? "hidden" : "regional";
  const signature = `${grid.fetchedAt}:${forecastHour}:${zoomBucket}`;
  const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

  if (signature !== activeSignature || !source) {
    const data = buildPressureContours(map, grid, forecastHour);

    if (source) source.setData(data);
    else map.addSource(SOURCE_ID, { type: "geojson", data });

    activeSignature = signature;
  }

  const beforeId = getFirstSymbolLayerId(map);

  if (!map.getLayer(LINE_LAYER_ID)) {
    map.addLayer(
      {
        id: LINE_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        maxzoom: PRESSURE_MAX_ZOOM + 0.2,
        filter: ["==", ["geometry-type"], "LineString"],
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#a8cbc5",
          "line-width": ["interpolate", ["linear"], ["zoom"], 5, 0.9, 10, 1.25],
          "line-opacity": LAYER_VISUAL_STRENGTHS.pressureLine,
          "line-blur": 0.15,
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
        maxzoom: PRESSURE_MAX_ZOOM + 0.2,
        filter: ["==", ["geometry-type"], "LineString"],
        layout: {
          "text-field": ["get", "label"],
          "text-font": ["Noto Sans Regular"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 5, 10, 10, 11.5],
          "symbol-placement": "line",
          "symbol-spacing": 230,
          "text-rotation-alignment": "map",
          "text-pitch-alignment": "viewport",
          "text-keep-upright": true,
          "text-max-angle": 35,
          "text-allow-overlap": false,
          "text-padding": 10,
        },
        paint: {
          "text-color": "#d9f3ef",
          "text-halo-color": "#17211f",
          "text-halo-width": 1.5,
          "text-opacity": LAYER_VISUAL_STRENGTHS.pressureLabel,
        },
      },
      beforeId
    );
  }

  setLayerOpacity(map, coverageVisible);
}

export function setPressureLayerCoverage(
  map: maplibregl.Map,
  visible: boolean
): void {
  coverageVisible = visible;
  setLayerOpacity(map, visible);
}

export function setPressureLayerEnabled(
  map: maplibregl.Map,
  enabled: boolean
): void {
  layerEnabled = enabled;
  setLayerOpacity(map, coverageVisible);
}

export function removePressureLayer(map: maplibregl.Map): void {
  activeSignature = null;
  coverageVisible = true;
  layerEnabled = true;

  if (map.getLayer(LABEL_LAYER_ID)) map.removeLayer(LABEL_LAYER_ID);
  if (map.getLayer(LINE_LAYER_ID)) map.removeLayer(LINE_LAYER_ID);
  if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
}
