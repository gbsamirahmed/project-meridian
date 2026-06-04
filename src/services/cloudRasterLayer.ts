import maplibregl from "maplibre-gl";

import { GRID_SIZE } from "../config/gridConfig";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "cloud-raster-source";
const LAYER_ID = "cloud-raster-layer";

const CANVAS_SIZE = 200;

function buildCloudMatrix(
  gridPoints: GridPoint[],
  forecastHour: number
): number[][] {
  const matrix: number[][] = [];

  for (let row = 0; row < GRID_SIZE; row++) {
    const rowValues: number[] = [];

    for (let column = 0; column < GRID_SIZE; column++) {
      const index = row * GRID_SIZE + column;
      rowValues.push(gridPoints[index].cloudCover[forecastHour]);
    }

    matrix.push(rowValues);
  }

  return matrix;
}

function interpolateValue(
  matrix: number[][],
  x: number,
  y: number
): number {
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);

  const x1 = Math.min(x0 + 1, GRID_SIZE - 1);
  const y1 = Math.min(y0 + 1, GRID_SIZE - 1);

  const dx = x - x0;
  const dy = y - y0;

  const topLeft = matrix[y0][x0];
  const topRight = matrix[y0][x1];
  const bottomLeft = matrix[y1][x0];
  const bottomRight = matrix[y1][x1];

  const top = topLeft * (1 - dx) + topRight * dx;
  const bottom = bottomLeft * (1 - dx) + bottomRight * dx;

  return top * (1 - dy) + bottom * dy;
}

function createCloudRaster(
  gridPoints: GridPoint[],
  forecastHour: number
): string {
  const canvas = document.createElement("canvas");

  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error("Could not create cloud raster canvas context");
  }

  const matrix = buildCloudMatrix(gridPoints, forecastHour);

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

      const cloudCover = interpolateValue(
        matrix,
        gridX,
        gridY
      );

      const opacity = Math.max(
        0,
        Math.min(180, (cloudCover / 100) * 180)
      );

      const pixelIndex =
        (y * CANVAS_SIZE + x) * 4;

      imageData.data[pixelIndex] = 230;
      imageData.data[pixelIndex + 1] = 235;
      imageData.data[pixelIndex + 2] = 240;
      imageData.data[pixelIndex + 3] = opacity;
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

export function updateCloudRasterLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[],
  forecastHour: number
): void {
  if (gridPoints.length === 0) return;

  const imageUrl = createCloudRaster(
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
      "raster-opacity": 0.65,
      "raster-resampling": "linear",
    },
  });
}

export function removeCloudRasterLayer(
  map: maplibregl.Map
): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}