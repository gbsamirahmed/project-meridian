import maplibregl from "maplibre-gl";

import {
  PRECIPITATION_DRY_THRESHOLD_MM,
  PRECIPITATION_INTENSITY_LEVELS,
} from "../config/layerVisuals";
import { WEATHER_GRID_MIN_ZOOM } from "../config/gridConfig";
import { getFirstSymbolLayerId } from "./mapLayerOrder";
import { interpolateWeatherAtLocation } from "./weatherInterpolation";

import type { PrecipitationIntensityLevel } from "../config/layerVisuals";
import type { WeatherGrid } from "../types/weatherGrid";

const SOURCE_ID = "precipitation-symbols-source";
const LAYER_ID = "precipitation-symbols-layer";
const ICON_PREFIX = "precipitation-intensity-";
const SAMPLE_COUNT = 25;

interface PrecipitationSymbolProperties {
  icon: string;
  valueLabel: string;
  precipitation: number;
  precipitationType: "unspecified";
}

interface Candidate {
  longitude: number;
  latitude: number;
  precipitation: number;
}

type PrecipitationSymbolCollection = GeoJSON.FeatureCollection<
  GeoJSON.Point,
  PrecipitationSymbolProperties
>;

let activeSignature: string | null = null;
let coverageVisible = true;
let layerEnabled = true;

function getIntensityLevel(value: number): PrecipitationIntensityLevel {
  let level = PRECIPITATION_INTENSITY_LEVELS[0];

  for (const candidate of PRECIPITATION_INTENSITY_LEVELS) {
    if (value >= candidate.value) level = candidate;
  }

  return level;
}

function drawDrop(
  context: CanvasRenderingContext2D,
  centerX: number,
  top: number,
  color: string
): void {
  context.beginPath();
  context.moveTo(centerX, top);
  context.bezierCurveTo(
    centerX - 2,
    top + 4,
    centerX - 7,
    top + 10,
    centerX - 7,
    top + 16
  );
  context.bezierCurveTo(
    centerX - 7,
    top + 23,
    centerX - 2,
    top + 27,
    centerX,
    top + 27
  );
  context.bezierCurveTo(
    centerX + 4,
    top + 27,
    centerX + 7,
    top + 23,
    centerX + 7,
    top + 16
  );
  context.bezierCurveTo(
    centerX + 7,
    top + 10,
    centerX + 2,
    top + 4,
    centerX,
    top
  );
  context.closePath();
  context.fillStyle = color;
  context.strokeStyle = "#10201f";
  context.lineWidth = 2.5;
  context.stroke();
  context.fill();
}

function createDropIcon(level: PrecipitationIntensityLevel): ImageData {
  const canvas = document.createElement("canvas");
  canvas.width = 112;
  canvas.height = 40;
  const context = canvas.getContext("2d");

  if (!context) throw new Error("Could not create precipitation icon canvas");

  const spacing = 24;
  const groupWidth = (level.drops - 1) * spacing;
  const startX = canvas.width / 2 - groupWidth / 2;

  for (let index = 0; index < level.drops; index++) {
    drawDrop(context, startX + index * spacing, 4, level.color);
  }

  return context.getImageData(0, 0, canvas.width, canvas.height);
}

function ensureIcons(map: maplibregl.Map): void {
  const seenDropCounts = new Set<number>();

  for (const level of PRECIPITATION_INTENSITY_LEVELS) {
    if (seenDropCounts.has(level.drops)) continue;

    const iconId = `${ICON_PREFIX}${level.drops}`;

    if (!map.hasImage(iconId)) {
      map.addImage(iconId, createDropIcon(level), { pixelRatio: 2 });
    }

    seenDropCounts.add(level.drops);
  }
}

function sampleCandidates(
  grid: WeatherGrid,
  forecastHour: number
): Candidate[] {
  const values: number[][] = [];
  const candidates: Candidate[] = [];
  let maximum: Candidate | null = null;

  for (let row = 0; row < SAMPLE_COUNT; row++) {
    const latitude =
      grid.bounds.north -
      ((grid.bounds.north - grid.bounds.south) * row) /
        (SAMPLE_COUNT - 1);
    const rowValues: number[] = [];

    for (let column = 0; column < SAMPLE_COUNT; column++) {
      const longitude =
        grid.bounds.west +
        ((grid.bounds.east - grid.bounds.west) * column) /
          (SAMPLE_COUNT - 1);
      const precipitation =
        interpolateWeatherAtLocation(
          grid,
          forecastHour,
          latitude,
          longitude
        )?.precipitation ?? 0;

      rowValues.push(precipitation);

      if (!maximum || precipitation > maximum.precipitation) {
        maximum = { longitude, latitude, precipitation };
      }
    }

    values.push(rowValues);
  }

  for (let row = 1; row < SAMPLE_COUNT - 1; row++) {
    for (let column = 1; column < SAMPLE_COUNT - 1; column++) {
      const precipitation = values[row][column];

      if (precipitation < PRECIPITATION_DRY_THRESHOLD_MM) continue;

      let isLocalMaximum = true;

      for (let rowOffset = -1; rowOffset <= 1; rowOffset++) {
        for (let columnOffset = -1; columnOffset <= 1; columnOffset++) {
          if (rowOffset === 0 && columnOffset === 0) continue;

          const neighbor = values[row + rowOffset][column + columnOffset];

          if (
            neighbor > precipitation ||
            (neighbor === precipitation &&
              rowOffset * 3 + columnOffset < 0)
          ) {
            isLocalMaximum = false;
          }
        }
      }

      if (!isLocalMaximum) continue;

      candidates.push({
        longitude:
          grid.bounds.west +
          ((grid.bounds.east - grid.bounds.west) * column) /
            (SAMPLE_COUNT - 1),
        latitude:
          grid.bounds.north -
          ((grid.bounds.north - grid.bounds.south) * row) /
            (SAMPLE_COUNT - 1),
        precipitation,
      });
    }
  }

  if (
    candidates.length === 0 &&
    maximum &&
    maximum.precipitation >= PRECIPITATION_DRY_THRESHOLD_MM
  ) {
    candidates.push(maximum);
  }

  return candidates.sort(
    (first, second) => second.precipitation - first.precipitation
  );
}

function buildSymbolGeoJson(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number
): PrecipitationSymbolCollection {
  const container = map.getContainer();
  const isMobile = container.clientWidth <= 500;
  const minimumDistance = isMobile ? 118 : 150;
  const maximumSymbols = isMobile ? 4 : 7;
  const acceptedPoints: maplibregl.Point[] = [];
  const features: PrecipitationSymbolCollection["features"] = [];

  const addSymbol = (candidate: Candidate, point: maplibregl.Point) => {
    const level = getIntensityLevel(candidate.precipitation);

    features.push({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [candidate.longitude, candidate.latitude],
      },
      properties: {
        icon: `${ICON_PREFIX}${level.drops}`,
        precipitation: candidate.precipitation,
        precipitationType: "unspecified",
        valueLabel:
          candidate.precipitation >= 1
            ? `${candidate.precipitation.toFixed(1)} mm`
            : "",
      },
    });
    acceptedPoints.push(point);
  };

  for (const candidate of sampleCandidates(grid, forecastHour)) {
    const point = map.project([candidate.longitude, candidate.latitude]);
    const isVisible =
      point.x >= 24 &&
      point.y >= 24 &&
      point.x <= container.clientWidth - 24 &&
      point.y <= container.clientHeight - 24;
    const isSeparated = acceptedPoints.every(
      (accepted) =>
        Math.hypot(point.x - accepted.x, point.y - accepted.y) >=
        minimumDistance
    );

    if (!isVisible || !isSeparated) continue;

    addSymbol(candidate, point);

    if (features.length >= maximumSymbols) break;
  }

  // A broad, almost uniform precipitation area may have its mathematical
  // maximum in the padded off-screen margin. In that case choose one stable
  // representative point from the visible field rather than exposing a grid.
  if (features.length === 0) {
    let visibleMaximum: Candidate | null = null;

    for (let row = 1; row <= 3; row++) {
      for (let column = 1; column <= 3; column++) {
        const point = new maplibregl.Point(
          (container.clientWidth * column) / 4,
          (container.clientHeight * row) / 4
        );
        const location = map.unproject(point);
        const precipitation = interpolateWeatherAtLocation(
          grid,
          forecastHour,
          location.lat,
          location.lng
        )?.precipitation;

        if (
          precipitation !== undefined &&
          precipitation >= PRECIPITATION_DRY_THRESHOLD_MM &&
          (!visibleMaximum || precipitation > visibleMaximum.precipitation)
        ) {
          visibleMaximum = {
            longitude: location.lng,
            latitude: location.lat,
            precipitation,
          };
        }
      }
    }

    if (visibleMaximum) {
      addSymbol(
        visibleMaximum,
        map.project([visibleMaximum.longitude, visibleMaximum.latitude])
      );
    }
  }

  return { type: "FeatureCollection", features };
}

function getViewSignature(map: maplibregl.Map): string {
  const center = map.getCenter();
  const container = map.getContainer();

  return [
    center.lng.toFixed(3),
    center.lat.toFixed(3),
    map.getZoom().toFixed(2),
    map.getBearing().toFixed(0),
    map.getPitch().toFixed(0),
    container.clientWidth,
    container.clientHeight,
  ].join(":");
}

function setLayerOpacity(map: maplibregl.Map, visible: boolean): void {
  if (!map.getLayer(LAYER_ID)) return;

  map.setPaintProperty(
    LAYER_ID,
    "icon-opacity",
    visible && layerEnabled ? 0.96 : 0
  );
  map.setPaintProperty(
    LAYER_ID,
    "text-opacity",
    visible && layerEnabled ? 0.94 : 0
  );
}

export function updatePrecipitationSymbols(
  map: maplibregl.Map,
  grid: WeatherGrid,
  forecastHour: number
): void {
  layerEnabled = true;
  ensureIcons(map);

  const signature = `${grid.fetchedAt}:${forecastHour}:${getViewSignature(map)}`;
  const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;

  if (signature !== activeSignature || !source) {
    const data = buildSymbolGeoJson(map, grid, forecastHour);

    if (source) source.setData(data);
    else map.addSource(SOURCE_ID, { type: "geojson", data });

    activeSignature = signature;
  }

  if (!map.getLayer(LAYER_ID)) {
    map.addLayer(
      {
        id: LAYER_ID,
        type: "symbol",
        source: SOURCE_ID,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        layout: {
          "icon-image": ["get", "icon"],
          "icon-size": ["interpolate", ["linear"], ["zoom"], 5, 0.72, 11, 0.94],
          "icon-allow-overlap": false,
          "text-field": ["get", "valueLabel"],
          "text-font": ["Noto Sans Regular"],
          "text-size": 10.5,
          "text-offset": [0, 1.45],
          "text-allow-overlap": false,
          "symbol-sort-key": ["*", -1, ["get", "precipitation"]],
        },
        paint: {
          "icon-opacity": 0.96,
          "text-color": "#ecf9ff",
          "text-halo-color": "#15201f",
          "text-halo-width": 1.6,
          "text-opacity": 0.94,
        },
      },
      getFirstSymbolLayerId(map)
    );
  }

  setLayerOpacity(map, coverageVisible);
}

export function setPrecipitationSymbolCoverage(
  map: maplibregl.Map,
  visible: boolean
): void {
  coverageVisible = visible;
  setLayerOpacity(map, visible);
}

export function setPrecipitationSymbolEnabled(
  map: maplibregl.Map,
  enabled: boolean
): void {
  layerEnabled = enabled;
  setLayerOpacity(map, coverageVisible);
}

export function removePrecipitationSymbols(map: maplibregl.Map): void {
  activeSignature = null;
  coverageVisible = true;
  layerEnabled = true;

  if (map.getLayer(LAYER_ID)) map.removeLayer(LAYER_ID);
  if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);

  for (let drops = 1; drops <= 4; drops++) {
    const iconId = `${ICON_PREFIX}${drops}`;

    if (map.hasImage(iconId)) map.removeImage(iconId);
  }
}
