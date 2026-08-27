import maplibregl from "maplibre-gl";

import {
  LAYER_VISUAL_STRENGTHS,
  PRECIPITATION_DRY_THRESHOLD_MM,
  PRECIPITATION_INTENSITY_LEVELS,
  WEATHER_SURFACE_COVERAGE_HIDE_MS,
  WEATHER_SURFACE_CROSSFADE_MS,
} from "../config/layerVisuals";
import { WEATHER_GRID_MIN_ZOOM } from "../config/gridConfig";
import { interpolateGridValue } from "./interpolation";
import { getWeatherInsertionLayerId } from "./mapLayerOrder";
import { buildWeatherMatrix } from "./weatherMatrix";

import type { PrimaryView } from "../types/layer";
import type { WeatherGrid } from "../types/weatherGrid";

export type WeatherSurfaceLayer = "clouds" | "precipitation";

const CANVAS_SIZE = 384;
const EDGE_FADE_WIDTH = 0.1;
const SURFACE_SLOTS = [
  {
    sourceId: "weather-surface-source-a",
    layerId: "weather-surface-layer-a",
  },
  {
    sourceId: "weather-surface-source-b",
    layerId: "weather-surface-layer-b",
  },
] as const;

let activeSlotIndex: 0 | 1 | null = null;
let activeSurfaceSignature: string | null = null;
let activeSurfaceLayer: WeatherSurfaceLayer | null = null;
let coverageIsVisible = true;
let transitionGeneration = 0;

interface Rgb {
  r: number;
  g: number;
  b: number;
}

interface Rgba extends Rgb {
  a: number;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function smoothstep(edge0: number, edge1: number, value: number): number {
  const ratio = clamp((value - edge0) / (edge1 - edge0), 0, 1);
  return ratio * ratio * (3 - 2 * ratio);
}

function parseHexColor(color: string): Rgb {
  const value = color.replace("#", "");

  return {
    r: Number.parseInt(value.slice(0, 2), 16),
    g: Number.parseInt(value.slice(2, 4), 16),
    b: Number.parseInt(value.slice(4, 6), 16),
  };
}

function interpolateColor(value: number): Rgb {
  const stops = PRECIPITATION_INTENSITY_LEVELS;
  if (value <= stops[0].value) {
    return parseHexColor(stops[0].color);
  }

  const lastStop = stops[stops.length - 1];

  if (value >= lastStop.value) {
    return parseHexColor(lastStop.color);
  }

  for (let index = 0; index < stops.length - 1; index++) {
    const start = stops[index];
    const end = stops[index + 1];

    if (value >= start.value && value <= end.value) {
      const ratio = (value - start.value) / (end.value - start.value);
      const startColor = parseHexColor(start.color);
      const endColor = parseHexColor(end.color);

      return {
        r: Math.round(startColor.r + (endColor.r - startColor.r) * ratio),
        g: Math.round(startColor.g + (endColor.g - startColor.g) * ratio),
        b: Math.round(startColor.b + (endColor.b - startColor.b) * ratio),
      };
    }
  }

  return parseHexColor(stops[0].color);
}

function cloudColor(value: number): Rgba {
  const cover = clamp(value, 0, 100);
  const darkness = Math.round(231 - cover * 0.42);
  const alpha = Math.round(
    255 * smoothstep(8, 100, cover) * (0.14 + cover / 190)
  );

  return {
    r: darkness - 5,
    g: darkness,
    b: Math.min(255, darkness + 5),
    a: alpha,
  };
}

function precipitationColor(value: number): Rgba {
  if (value < PRECIPITATION_DRY_THRESHOLD_MM) {
    return { r: 0, g: 0, b: 0, a: 0 };
  }

  const color = interpolateColor(value);
  let opacity = PRECIPITATION_INTENSITY_LEVELS[0].opacity;

  for (let index = 0; index < PRECIPITATION_INTENSITY_LEVELS.length - 1; index++) {
    const start = PRECIPITATION_INTENSITY_LEVELS[index];
    const end = PRECIPITATION_INTENSITY_LEVELS[index + 1];

    if (value >= start.value && value <= end.value) {
      const ratio = (value - start.value) / (end.value - start.value);
      opacity = start.opacity + (end.opacity - start.opacity) * ratio;
      break;
    }

    if (value >= end.value) opacity = end.opacity;
  }

  return {
    ...color,
    a: Math.round(255 * opacity),
  };
}

function getSurfaceValue(
  layer: WeatherSurfaceLayer,
  grid: WeatherGrid,
  forecastHour: number
): number[][] {
  return buildWeatherMatrix(
    grid.points,
    grid.rows,
    grid.columns,
    forecastHour,
    (point, hour) => {
      // Cloud cover is intentionally a two-dimensional model field. Keeping it
      // behind this renderer boundary allows a later atmospheric or volumetric
      // cloud path without coupling it to terrain or temperature rendering; it
      // does not describe the shape or position of individual clouds.
      if (layer === "clouds") return point.cloudCover[hour];
      return point.precipitation[hour];
    }
  );
}

function createWeatherSurfaceImage(
  layer: WeatherSurfaceLayer,
  grid: WeatherGrid,
  forecastHour: number
): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;

  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error("Could not create weather surface canvas context");
  }

  const matrix = getSurfaceValue(layer, grid, forecastHour);
  const image = context.createImageData(CANVAS_SIZE, CANVAS_SIZE);

  for (let y = 0; y < CANVAS_SIZE; y++) {
    for (let x = 0; x < CANVAS_SIZE; x++) {
      const xRatio = x / (CANVAS_SIZE - 1);
      const yRatio = y / (CANVAS_SIZE - 1);
      const value = interpolateGridValue(
        matrix,
        xRatio * (grid.columns - 1),
        yRatio * (grid.rows - 1)
      );
      const color =
        layer === "clouds"
          ? cloudColor(value)
          : precipitationColor(value);
      const edgeDistance = Math.min(
        xRatio,
        1 - xRatio,
        yRatio,
        1 - yRatio
      );
      const coverageAlpha = smoothstep(
        0,
        EDGE_FADE_WIDTH,
        edgeDistance
      );
      const pixelIndex = (y * CANVAS_SIZE + x) * 4;

      image.data[pixelIndex] = color.r;
      image.data[pixelIndex + 1] = color.g;
      image.data[pixelIndex + 2] = color.b;
      image.data[pixelIndex + 3] = Math.round(color.a * coverageAlpha);
    }
  }

  context.putImageData(image, 0, 0);
  return canvas;
}

function getImageCoordinates(
  grid: WeatherGrid
): [[number, number], [number, number], [number, number], [number, number]] {
  const { west, south, east, north } = grid.bounds;

  return [
    [west, north],
    [east, north],
    [east, south],
    [west, south],
  ];
}

export function isWeatherSurfaceLayer(
  layer: PrimaryView
): layer is WeatherSurfaceLayer {
  return layer === "clouds" || layer === "precipitation";
}

export function updateWeatherSurface(
  map: maplibregl.Map,
  layer: WeatherSurfaceLayer,
  grid: WeatherGrid,
  forecastHour: number
): void {
  if (
    activeSlotIndex !== null &&
    !map.getLayer(SURFACE_SLOTS[activeSlotIndex].layerId)
  ) {
    activeSlotIndex = null;
    activeSurfaceSignature = null;
    activeSurfaceLayer = null;
    transitionGeneration += 1;
  }

  const signature = [
    layer,
    forecastHour,
    grid.fetchedAt,
    grid.bounds.west,
    grid.bounds.south,
    grid.bounds.east,
    grid.bounds.north,
  ].join(":");

  if (signature === activeSurfaceSignature) return;

  const surfaceCanvas = createWeatherSurfaceImage(
    layer,
    grid,
    forecastHour
  );
  const coordinates = getImageCoordinates(grid);
  const previousSlotIndex = activeSlotIndex;
  const nextSlotIndex: 0 | 1 = activeSlotIndex === 0 ? 1 : 0;
  const nextSlot = SURFACE_SLOTS[nextSlotIndex];
  const source = map.getSource(nextSlot.sourceId) as
    | maplibregl.CanvasSource
    | undefined;

  if (source) {
    const targetCanvas = source.getCanvas();
    const targetContext = targetCanvas.getContext("2d");

    if (!targetContext) {
      throw new Error("Could not update weather surface canvas context");
    }

    targetContext.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    targetContext.drawImage(surfaceCanvas, 0, 0);
    source.setCoordinates(coordinates);
    source.play();
  } else {
    map.addSource(nextSlot.sourceId, {
      type: "canvas",
      canvas: surfaceCanvas,
      animate: false,
      coordinates,
    });
  }

  if (!map.getLayer(nextSlot.layerId)) {
    map.addLayer(
      {
        id: nextSlot.layerId,
        type: "raster",
        source: nextSlot.sourceId,
        minzoom: WEATHER_GRID_MIN_ZOOM,
        paint: {
          "raster-opacity": 0,
          "raster-resampling": "linear",
          // CanvasSource extends ImageSource, so MapLibre includes this raster
          // layer in its terrain render-to-texture path and drapes the field
          // over the DEM. The canvas stays static between forecast updates.
          // Source fading is disabled; the two layers crossfade explicitly.
          "raster-fade-duration": 0,
        },
      },
      getWeatherInsertionLayerId(map)
    );
  }

  map.setPaintProperty(nextSlot.layerId, "raster-opacity-transition", {
    duration: WEATHER_SURFACE_CROSSFADE_MS,
    delay: 0,
  });

  const generation = transitionGeneration + 1;
  const layerStrength = LAYER_VISUAL_STRENGTHS[layer];

  transitionGeneration = generation;
  activeSlotIndex = nextSlotIndex;
  activeSurfaceSignature = signature;
  activeSurfaceLayer = layer;

  // Two animation frames allow MapLibre to upload the incoming canvas while
  // the previous terrain-draped surface stays visible underneath it.
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      if (
        generation !== transitionGeneration ||
        !map.getLayer(nextSlot.layerId)
      ) {
        return;
      }

      const nextSource = map.getSource(nextSlot.sourceId) as
        | maplibregl.CanvasSource
        | undefined;

      nextSource?.pause();

      map.setPaintProperty(
        nextSlot.layerId,
        "raster-opacity",
        coverageIsVisible ? layerStrength : 0
      );

      if (previousSlotIndex !== null) {
        const previousLayerId = SURFACE_SLOTS[previousSlotIndex].layerId;

        if (map.getLayer(previousLayerId)) {
          map.setPaintProperty(previousLayerId, "raster-opacity", 0);
        }
      }
    });
  });
}

export function setWeatherSurfaceCoverage(
  map: maplibregl.Map,
  isVisible: boolean
): void {
  if (coverageIsVisible === isVisible) return;

  coverageIsVisible = isVisible;

  for (let index = 0; index < SURFACE_SLOTS.length; index++) {
    const slot = SURFACE_SLOTS[index];

    if (!map.getLayer(slot.layerId)) continue;

    const opacity =
      isVisible && index === activeSlotIndex && activeSurfaceLayer
        ? LAYER_VISUAL_STRENGTHS[activeSurfaceLayer]
        : 0;

    map.setPaintProperty(slot.layerId, "raster-opacity-transition", {
      duration: isVisible
        ? WEATHER_SURFACE_CROSSFADE_MS
        : WEATHER_SURFACE_COVERAGE_HIDE_MS,
      delay: 0,
    });
    map.setPaintProperty(slot.layerId, "raster-opacity", opacity);
  }
}

export function removeWeatherSurface(map: maplibregl.Map): void {
  transitionGeneration += 1;
  activeSlotIndex = null;
  activeSurfaceSignature = null;
  activeSurfaceLayer = null;
  coverageIsVisible = true;

  for (const slot of SURFACE_SLOTS) {
    if (map.getLayer(slot.layerId)) map.removeLayer(slot.layerId);
  }

  for (const slot of SURFACE_SLOTS) {
    if (map.getSource(slot.sourceId)) map.removeSource(slot.sourceId);
  }
}
