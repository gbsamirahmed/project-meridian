import maplibregl from "maplibre-gl";

import { GRID_SIZE } from "../config/gridConfig";
import { interpolateGridValue } from "./interpolation";

import type { GridPoint } from "../types/gridPoint";

const SOURCE_ID = "hillshade-raster-source";
const LAYER_ID = "hillshade-raster-layer";

const CANVAS_SIZE = 200;

function buildElevationMatrix(
  gridPoints: GridPoint[]
): number[][] {
  const matrix: number[][] = [];

  for (let row = 0; row < GRID_SIZE; row++) {
    const rowValues: number[] = [];

    for (let column = 0; column < GRID_SIZE; column++) {
      const index = row * GRID_SIZE + column;

      rowValues.push(
        gridPoints[index].elevation
      );
    }

    matrix.push(rowValues);
  }

  return matrix;
}

function calculateHillshade(
  matrix: number[][],
  x: number,
  y: number
): number {
  const step = 0.25;

  const west = interpolateGridValue(
    matrix,
    Math.max(0, x - step),
    y
  );

  const east = interpolateGridValue(
    matrix,
    Math.min(GRID_SIZE - 1, x + step),
    y
  );

  const north = interpolateGridValue(
    matrix,
    x,
    Math.max(0, y - step)
  );

  const south = interpolateGridValue(
    matrix,
    x,
    Math.min(GRID_SIZE - 1, y + step)
  );

  const dzdx = east - west;
  const dzdy = south - north;

  const slopeX = -dzdx;
  const slopeY = -dzdy;

  const lightX = -0.6;
  const lightY = -0.6;

  const brightness =
    (slopeX * lightX +
      slopeY * lightY) /
    1000;

  return Math.max(
    0,
    Math.min(
      255,
      Math.round(
        128 + brightness * 255
      )
    )
  );
}

function createHillshadeRaster(
  gridPoints: GridPoint[]
): string {
  const canvas = document.createElement("canvas");

  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error(
      "Could not create hillshade canvas context"
    );
  }

  const matrix = buildElevationMatrix(
    gridPoints
  );

  const imageData = context.createImageData(
    CANVAS_SIZE,
    CANVAS_SIZE
  );

  for (let y = 0; y < CANVAS_SIZE; y++) {
    for (let x = 0; x < CANVAS_SIZE; x++) {
      const gridX =
        (x / (CANVAS_SIZE - 1)) *
        (GRID_SIZE - 1);

      const gridY =
        (y / (CANVAS_SIZE - 1)) *
        (GRID_SIZE - 1);

      const shade =
        calculateHillshade(
          matrix,
          gridX,
          gridY
        );

      const pixelIndex =
        (y * CANVAS_SIZE + x) * 4;

      imageData.data[pixelIndex] = shade;
      imageData.data[pixelIndex + 1] = shade;
      imageData.data[pixelIndex + 2] = shade;
      imageData.data[pixelIndex + 3] = 255;
    }
  }

  context.putImageData(
    imageData,
    0,
    0
  );

  return canvas.toDataURL(
    "image/png"
  );
}

function getRasterCoordinates(
  gridPoints: GridPoint[]
): [
  [number, number],
  [number, number],
  [number, number],
  [number, number],
] {
  const longitudes = gridPoints.map(
    (point) => point.longitude
  );

  const latitudes = gridPoints.map(
    (point) => point.latitude
  );

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

export function updateHillshadeRasterLayer(
  map: maplibregl.Map,
  gridPoints: GridPoint[],
  opacity: number
): void {
  if (gridPoints.length === 0) return;

  const imageUrl =
    createHillshadeRaster(
      gridPoints
    );

  const coordinates =
    getRasterCoordinates(
      gridPoints
    );

  const existingSource =
    map.getSource(
      SOURCE_ID
    ) as
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

export function removeHillshadeRasterLayer(
  map: maplibregl.Map
): void {
  if (map.getLayer(LAYER_ID)) {
    map.removeLayer(LAYER_ID);
  }

  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}