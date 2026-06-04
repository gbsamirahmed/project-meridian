import maplibregl from "maplibre-gl";

import { interpolateGridValue } from "./interpolation";
import { GRID_SIZE } from "../config/gridConfig";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "temperature-raster-source";
const LAYER_ID = "temperature-raster-layer";

const CANVAS_SIZE = 200;
const ALPHA = 180;

interface Rgb {
  r: number;
  g: number;
  b: number;
}

const TEMPERATURE_SCALE = [
  { temperature: -20, color: { r: 30, g: 64, b: 175 } },
  { temperature: -10, color: { r: 37, g: 99, b: 235 } },
  { temperature: 0, color: { r: 6, g: 182, b: 212 } },
  { temperature: 10, color: { r: 34, g: 197, b: 94 } },
  { temperature: 20, color: { r: 250, g: 204, b: 21 } },
  { temperature: 30, color: { r: 239, g: 68, b: 68 } },
  { temperature: 40, color: { r: 126, g: 34, b: 206 } },
];

function interpolateNumber(
  start: number,
  end: number,
  ratio: number
): number {
  return start + (end - start) * ratio;
}

function interpolateColor(
  start: Rgb,
  end: Rgb,
  ratio: number
): Rgb {
  return {
    r: Math.round(interpolateNumber(start.r, end.r, ratio)),
    g: Math.round(interpolateNumber(start.g, end.g, ratio)),
    b: Math.round(interpolateNumber(start.b, end.b, ratio)),
  };
}

function temperatureToRgb(temperature: number): Rgb {
  if (temperature <= TEMPERATURE_SCALE[0].temperature) {
    return TEMPERATURE_SCALE[0].color;
  }

  const lastStop = TEMPERATURE_SCALE[TEMPERATURE_SCALE.length - 1];

  if (temperature >= lastStop.temperature) {
    return lastStop.color;
  }

  for (let index = 0; index < TEMPERATURE_SCALE.length - 1; index++) {
    const currentStop = TEMPERATURE_SCALE[index];
    const nextStop = TEMPERATURE_SCALE[index + 1];

    if (
      temperature >= currentStop.temperature &&
      temperature <= nextStop.temperature
    ) {
      const ratio =
        (temperature - currentStop.temperature) /
        (nextStop.temperature - currentStop.temperature);

      return interpolateColor(
        currentStop.color,
        nextStop.color,
        ratio
      );
    }
  }

  return TEMPERATURE_SCALE[0].color;
}

function buildTemperatureMatrix(
  gridPoints: GridPoint[],
  forecastHour: number
): number[][] {
  const matrix: number[][] = [];

  for (let row = 0; row < GRID_SIZE; row++) {
    const rowValues: number[] = [];

    for (let column = 0; column < GRID_SIZE; column++) {
      const index = row * GRID_SIZE + column;
      rowValues.push(gridPoints[index].temperature[forecastHour]);
    }

    matrix.push(rowValues);
  }

  return matrix;
}

function createTemperatureRaster(
  gridPoints: GridPoint[],
  forecastHour: number
): string {
  const canvas = document.createElement("canvas");

  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error("Could not create raster canvas context");
  }

  const matrix = buildTemperatureMatrix(
    gridPoints,
    forecastHour
  );

  const imageData = context.createImageData(
    CANVAS_SIZE,
    CANVAS_SIZE
  );

  for (let y = 0; y < CANVAS_SIZE; y++) {
    for (let x = 0; x < CANVAS_SIZE; x++) {
      const gridX =
        (x / (CANVAS_SIZE - 1)) * (GRID_SIZE - 1);

      const gridY =
        (y / (CANVAS_SIZE - 1)) * (GRID_SIZE - 1);

      const temperature = interpolateGridValue(
        matrix,
        gridX,
        gridY
      );

      const rgb = temperatureToRgb(temperature);

      const pixelIndex =
        (y * CANVAS_SIZE + x) * 4;

      imageData.data[pixelIndex] = rgb.r;
      imageData.data[pixelIndex + 1] = rgb.g;
      imageData.data[pixelIndex + 2] = rgb.b;
      imageData.data[pixelIndex + 3] = ALPHA;
    }
  }

  context.putImageData(imageData, 0, 0);

  return canvas.toDataURL("image/png");
}

function getRasterCoordinates(
  gridPoints: GridPoint[]
): [
  [number, number],
  [number, number],
  [number, number],
  [number, number],
] {
  const longitudes = gridPoints.map((point) => point.longitude);
  const latitudes = gridPoints.map((point) => point.latitude);

  const west = Math.min(...longitudes);
  const east = Math.max(...longitudes);
  const south = Math.min(...latitudes);
  const north = Math.max(...latitudes);

  return [
    [west, north],
    [east, north],
    [east, south],
    [west, south],
  ];
}

export function updateRasterLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[],
  forecastHour: number
): void {
  if (gridPoints.length === 0) return;

  const imageUrl = createTemperatureRaster(
    gridPoints,
    forecastHour
  );

  const coordinates = getRasterCoordinates(gridPoints);

  const existingSource = map.getSource(SOURCE_ID) as
    | maplibregl.ImageSource
    | undefined;

  if (existingSource) {
    existingSource.updateImage({
      url: imageUrl,
      coordinates,
    });

    return;
  }

  map.addSource(SOURCE_ID, {
    type: "image",
    url: imageUrl,
    coordinates,
  });

  map.addLayer({
    id: LAYER_ID,
    type: "raster",
    source: SOURCE_ID,
    paint: {
      "raster-opacity": 0.4,
      "raster-resampling": "linear",
    },
  });
}

export function removeRasterLayer(map: maplibregl.Map): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}