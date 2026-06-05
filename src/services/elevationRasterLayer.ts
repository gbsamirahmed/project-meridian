import maplibregl from "maplibre-gl";

import { GRID_SIZE } from "../config/gridConfig";
import { interpolateGridValue } from "./interpolation";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "elevation-raster-source";
const LAYER_ID = "elevation-raster-layer";

const CANVAS_SIZE = 200;

interface Rgb {
  r: number;
  g: number;
  b: number;
}

const ELEVATION_SCALE = [
  { elevation: 0, color: { r: 34, g: 120, b: 60 } },
  { elevation: 250, color: { r: 74, g: 155, b: 80 } },
  { elevation: 500, color: { r: 150, g: 180, b: 90 } },
  { elevation: 750, color: { r: 210, g: 190, b: 115 } },
  { elevation: 1000, color: { r: 170, g: 130, b: 90 } },
  { elevation: 1500, color: { r: 120, g: 95, b: 80 } },
  { elevation: 2500, color: { r: 150, g: 150, b: 150 } },
  { elevation: 3500, color: { r: 220, g: 220, b: 220 } },
];

function interpolateNumber(start: number, end: number, ratio: number): number {
  return start + (end - start) * ratio;
}

function interpolateColor(start: Rgb, end: Rgb, ratio: number): Rgb {
  return {
    r: Math.round(interpolateNumber(start.r, end.r, ratio)),
    g: Math.round(interpolateNumber(start.g, end.g, ratio)),
    b: Math.round(interpolateNumber(start.b, end.b, ratio)),
  };
}

function elevationToRgb(elevation: number): Rgb {
  if (elevation <= ELEVATION_SCALE[0].elevation) {
    return ELEVATION_SCALE[0].color;
  }

  const lastStop = ELEVATION_SCALE[ELEVATION_SCALE.length - 1];

  if (elevation >= lastStop.elevation) {
    return lastStop.color;
  }

  for (let index = 0; index < ELEVATION_SCALE.length - 1; index++) {
    const currentStop = ELEVATION_SCALE[index];
    const nextStop = ELEVATION_SCALE[index + 1];

    if (
      elevation >= currentStop.elevation &&
      elevation <= nextStop.elevation
    ) {
      const ratio =
        (elevation - currentStop.elevation) /
        (nextStop.elevation - currentStop.elevation);

      return interpolateColor(
        currentStop.color,
        nextStop.color,
        ratio
      );
    }
  }

  return ELEVATION_SCALE[0].color;
}

function buildElevationMatrix(
  gridPoints: GridPoint[]
): number[][] {
  const matrix: number[][] = [];

  for (let row = 0; row < GRID_SIZE; row++) {
    const rowValues: number[] = [];

    for (let column = 0; column < GRID_SIZE; column++) {
      const index = row * GRID_SIZE + column;
      rowValues.push(gridPoints[index].elevation);
    }

    matrix.push(rowValues);
  }

  return matrix;
}

function createElevationRaster(
  gridPoints: GridPoint[]
): string {
  const canvas = document.createElement("canvas");

  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error("Could not create elevation raster canvas context");
  }

  const matrix = buildElevationMatrix(gridPoints);

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

      const elevation = interpolateGridValue(
        matrix,
        gridX,
        gridY
      );

      const rgb = elevationToRgb(elevation);

      const pixelIndex =
        (y * CANVAS_SIZE + x) * 4;

      imageData.data[pixelIndex] = rgb.r;
      imageData.data[pixelIndex + 1] = rgb.g;
      imageData.data[pixelIndex + 2] = rgb.b;
      imageData.data[pixelIndex + 3] = 255;
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

export function updateElevationRasterLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[],
  opacity: number
): void {
  if (gridPoints.length === 0) return;

  const imageUrl = createElevationRaster(gridPoints);
  const coordinates = getRasterCoordinates(gridPoints);

  const existingSource = map.getSource(SOURCE_ID) as
    | maplibregl.ImageSource
    | undefined;

  if (existingSource) {
    existingSource.updateImage({
      url: imageUrl,
      coordinates,
    });

    if (map.getLayer(LAYER_ID)) {
      map.setPaintProperty(
        LAYER_ID,
        "raster-opacity",
        opacity
      );
    }

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
      "raster-opacity": opacity,
      "raster-resampling": "linear",
    },
  });
}

export function removeElevationRasterLayer(
  map: maplibregl.Map
): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}