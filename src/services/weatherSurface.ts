import maplibregl from "maplibre-gl";

import {
  LAYER_VISUAL_STRENGTHS,
  WEATHER_SURFACE_COVERAGE_HIDE_MS,
  WEATHER_SURFACE_CROSSFADE_MS,
} from "../config/layerVisuals";
import { WEATHER_GRID_MIN_ZOOM } from "../config/gridConfig";
import { interpolateGridValue } from "./interpolation";
import { getWeatherInsertionLayerId } from "./mapLayerOrder";
import { precipitationColor } from "./precipitationStyle";
import { buildWeatherMatrix } from "./weatherMatrix";

import type { WeatherGrid } from "../types/weatherGrid";

export type WeatherSurfaceLayer = "clouds" | "precipitation";

const WEATHER_TILE_SIZE = 256;
const WEATHER_TILE_MAX_ZOOM = 8;
const WEATHER_TILE_PROTOCOL = "meridian-weather";
const RETAINED_FIELD_VERSIONS = 12;
const EDGE_FADE_WIDTH = 0.1;
type SurfaceSlotIndex = 0 | 1;

interface SurfaceState {
  activeSlotIndex: SurfaceSlotIndex | null;
  activeSignature: string | null;
  enabled: boolean;
  pendingSlotIndex: SurfaceSlotIndex | null;
  pendingSignature: string | null;
  slotFieldVersions: [number | null, number | null];
  slots: readonly [
    { sourceId: string; layerId: string },
    { sourceId: string; layerId: string },
  ];
  transitionGeneration: number;
}

function createSurfaceState(layer: WeatherSurfaceLayer): SurfaceState {
  return {
    activeSlotIndex: null,
    activeSignature: null,
    enabled: false,
    pendingSlotIndex: null,
    pendingSignature: null,
    slotFieldVersions: [null, null],
    slots: [
      {
        sourceId: `weather-${layer}-source-a`,
        layerId: `weather-${layer}-layer-a`,
      },
      {
        sourceId: `weather-${layer}-source-b`,
        layerId: `weather-${layer}-layer-b`,
      },
    ],
    transitionGeneration: 0,
  };
}

const surfaceStates: Record<WeatherSurfaceLayer, SurfaceState> = {
  clouds: createSurfaceState("clouds"),
  precipitation: createSurfaceState("precipitation"),
};

let coverageIsVisible = true;
let nextFieldVersion = 0;
let weatherTileProtocolRegistered = false;

interface WeatherTileField {
  bounds: WeatherGrid["bounds"];
  columns: number;
  layer: WeatherSurfaceLayer;
  matrix: number[][];
  rows: number;
}

const weatherTileFields = new Map<number, WeatherTileField>();

interface Rgba {
  r: number;
  g: number;
  b: number;
  a: number;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

function smoothstep(edge0: number, edge1: number, value: number): number {
  const ratio = clamp((value - edge0) / (edge1 - edge0), 0, 1);
  return ratio * ratio * (3 - 2 * ratio);
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

function tileYToLatitude(y: number): number {
  return (
    (Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180) /
    Math.PI
  );
}

function renderWeatherTile(
  field: WeatherTileField,
  zoom: number,
  tileX: number,
  tileY: number
): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = WEATHER_TILE_SIZE;
  canvas.height = WEATHER_TILE_SIZE;
  const context = canvas.getContext("2d");

  if (!context) {
    throw new Error("Could not create weather tile canvas context");
  }

  const image = context.createImageData(
    WEATHER_TILE_SIZE,
    WEATHER_TILE_SIZE
  );
  const tileCount = 2 ** zoom;
  const longitudeSpan = field.bounds.east - field.bounds.west;
  const latitudeSpan = field.bounds.north - field.bounds.south;

  for (let y = 0; y < WEATHER_TILE_SIZE; y++) {
    const worldY = (tileY + (y + 0.5) / WEATHER_TILE_SIZE) / tileCount;
    const latitude = tileYToLatitude(worldY);
    const yRatio = (field.bounds.north - latitude) / latitudeSpan;

    for (let x = 0; x < WEATHER_TILE_SIZE; x++) {
      const worldX = (tileX + (x + 0.5) / WEATHER_TILE_SIZE) / tileCount;
      const longitude = worldX * 360 - 180;
      const xRatio = (longitude - field.bounds.west) / longitudeSpan;
      const pixelIndex = (y * WEATHER_TILE_SIZE + x) * 4;

      if (xRatio < 0 || xRatio > 1 || yRatio < 0 || yRatio > 1) {
        continue;
      }

      const value = interpolateGridValue(
        field.matrix,
        xRatio * (field.columns - 1),
        yRatio * (field.rows - 1)
      );
      const color =
        field.layer === "clouds"
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

      image.data[pixelIndex] = color.r;
      image.data[pixelIndex + 1] = color.g;
      image.data[pixelIndex + 2] = color.b;
      image.data[pixelIndex + 3] = Math.round(color.a * coverageAlpha);
    }
  }

  context.putImageData(image, 0, 0);
  return canvas;
}

async function createTransparentWeatherTile(): Promise<ImageBitmap> {
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  return createImageBitmap(canvas);
}

function ensureWeatherTileProtocol(): void {
  if (weatherTileProtocolRegistered) return;

  maplibregl.addProtocol(
    WEATHER_TILE_PROTOCOL,
    async (request, abortController) => {
      const match = request.url.match(
        /^meridian-weather:\/\/field\/(\d+)\/(\d+)\/(\d+)\/(\d+)$/
      );

      if (!match) throw new Error("Invalid Meridian weather tile URL");

      const [, versionValue, zoomValue, xValue, yValue] = match;
      const field = weatherTileFields.get(Number(versionValue));

      if (!field || abortController.signal.aborted) {
        return { data: await createTransparentWeatherTile() };
      }

      const canvas = renderWeatherTile(
        field,
        Number(zoomValue),
        Number(xValue),
        Number(yValue)
      );
      const bitmap = await createImageBitmap(canvas);

      return { data: bitmap };
    }
  );
  weatherTileProtocolRegistered = true;
}

function registerWeatherTileField(
  state: SurfaceState,
  slotIndex: SurfaceSlotIndex,
  layer: WeatherSurfaceLayer,
  grid: WeatherGrid,
  forecastHour: number
): number {
  const version = ++nextFieldVersion;

  weatherTileFields.set(version, {
    bounds: grid.bounds,
    columns: grid.columns,
    layer,
    matrix: getSurfaceValue(layer, grid, forecastHour),
    rows: grid.rows,
  });
  state.slotFieldVersions[slotIndex] = version;

  while (weatherTileFields.size > RETAINED_FIELD_VERSIONS) {
    const oldestVersion = weatherTileFields.keys().next().value as
      | number
      | undefined;

    if (oldestVersion === undefined) break;
    const versionIsMounted = Object.values(surfaceStates).some((candidate) =>
      candidate.slotFieldVersions.includes(oldestVersion)
    );

    if (versionIsMounted) {
      const field = weatherTileFields.get(oldestVersion);
      weatherTileFields.delete(oldestVersion);
      weatherTileFields.set(oldestVersion, field!);
      continue;
    }

    weatherTileFields.delete(oldestVersion);
  }

  return version;
}

export function updateWeatherSurface(
  map: maplibregl.Map,
  layer: WeatherSurfaceLayer,
  grid: WeatherGrid,
  forecastHour: number
): void {
  const state = surfaceStates[layer];
  state.enabled = true;

  if (
    state.activeSlotIndex !== null &&
    !map.getLayer(state.slots[state.activeSlotIndex].layerId)
  ) {
    state.activeSlotIndex = null;
    state.activeSignature = null;
    state.pendingSlotIndex = null;
    state.pendingSignature = null;
    state.transitionGeneration += 1;
  }

  if (
    state.pendingSlotIndex !== null &&
    (!map.getLayer(state.slots[state.pendingSlotIndex].layerId) ||
      !map.getSource(state.slots[state.pendingSlotIndex].sourceId))
  ) {
    state.pendingSlotIndex = null;
    state.pendingSignature = null;
    state.transitionGeneration += 1;
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

  if (signature === state.activeSignature) {
    setWeatherSurfaceEnabled(map, layer, true);
    return;
  }

  if (signature === state.pendingSignature) return;

  ensureWeatherTileProtocol();
  const previousSlotIndex = state.activeSlotIndex;
  const nextSlotIndex: SurfaceSlotIndex =
    state.activeSlotIndex === 0 ? 1 : 0;
  const nextSlot = state.slots[nextSlotIndex];
  const fieldVersion = registerWeatherTileField(
    state,
    nextSlotIndex,
    layer,
    grid,
    forecastHour
  );
  const tileUrl = `${WEATHER_TILE_PROTOCOL}://field/${fieldVersion}/{z}/{x}/{y}`;
  const source = map.getSource(nextSlot.sourceId) as
    | maplibregl.RasterTileSource
    | undefined;

  if (source) {
    source.setTiles([tileUrl]);
  } else {
    map.addSource(nextSlot.sourceId, {
      type: "raster",
      tiles: [tileUrl],
      tileSize: WEATHER_TILE_SIZE,
      maxzoom: WEATHER_TILE_MAX_ZOOM,
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
          // Native raster tiles participate in MapLibre's terrain
          // render-to-texture path, so the sampled field stays draped while
          // parent and child tiles provide stable zoom fallbacks. Source fading
          // is disabled because the two mounted layers crossfade explicitly.
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

  const generation = state.transitionGeneration + 1;
  const layerStrength = LAYER_VISUAL_STRENGTHS[layer];

  state.transitionGeneration = generation;
  state.pendingSlotIndex = nextSlotIndex;
  state.pendingSignature = signature;

  // A raster source reports loaded only after its current visible tiles are
  // renderable. Keep the previous slot authoritative until then, so a forecast
  // update or region refresh never exposes partially prepared tiles.
  const revealIncomingSurface = () => {
    if (
      generation !== state.transitionGeneration ||
      !map.getLayer(nextSlot.layerId)
    ) {
      map.off("sourcedata", handleIncomingSourceData);
      return;
    }

    if (!map.isSourceLoaded(nextSlot.sourceId)) return;

    map.off("sourcedata", handleIncomingSourceData);
    state.activeSlotIndex = nextSlotIndex;
    state.activeSignature = signature;
    state.pendingSlotIndex = null;
    state.pendingSignature = null;

    map.setPaintProperty(
      nextSlot.layerId,
      "raster-opacity",
      state.enabled && coverageIsVisible ? layerStrength : 0
    );

    if (previousSlotIndex !== null) {
      const previousLayerId = state.slots[previousSlotIndex].layerId;

      if (map.getLayer(previousLayerId)) {
        map.setPaintProperty(previousLayerId, "raster-opacity", 0);
      }
    }
  };
  const handleIncomingSourceData = (
    event: maplibregl.MapSourceDataEvent
  ) => {
    if (event.sourceId === nextSlot.sourceId) revealIncomingSurface();
  };

  map.on("sourcedata", handleIncomingSourceData);
  window.requestAnimationFrame(revealIncomingSurface);
  map.triggerRepaint();
}

export function setWeatherSurfaceCoverage(
  map: maplibregl.Map,
  isVisible: boolean
): void {
  if (coverageIsVisible === isVisible) return;

  coverageIsVisible = isVisible;

  for (const [layer, state] of Object.entries(surfaceStates) as Array<
    [WeatherSurfaceLayer, SurfaceState]
  >) {
    for (let index = 0; index < state.slots.length; index++) {
      const slot = state.slots[index];

      if (!map.getLayer(slot.layerId)) continue;

      const opacity =
        state.enabled && isVisible && index === state.activeSlotIndex
          ? LAYER_VISUAL_STRENGTHS[layer]
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
}

export function setWeatherSurfaceEnabled(
  map: maplibregl.Map,
  layer: WeatherSurfaceLayer,
  enabled: boolean
): void {
  const state = surfaceStates[layer];
  state.enabled = enabled;

  for (let index = 0; index < state.slots.length; index++) {
    const slot = state.slots[index];
    if (!map.getLayer(slot.layerId)) continue;

    const opacity =
      enabled &&
      coverageIsVisible &&
      index === state.activeSlotIndex
        ? LAYER_VISUAL_STRENGTHS[layer]
        : 0;

    map.setPaintProperty(slot.layerId, "raster-opacity", opacity);
  }
}

export function removeWeatherSurface(map: maplibregl.Map): void {
  weatherTileFields.clear();
  coverageIsVisible = true;

  for (const state of Object.values(surfaceStates)) {
    state.transitionGeneration += 1;
    state.activeSlotIndex = null;
    state.activeSignature = null;
    state.pendingSlotIndex = null;
    state.pendingSignature = null;
    state.slotFieldVersions[0] = null;
    state.slotFieldVersions[1] = null;
    state.enabled = false;

    for (const slot of state.slots) {
      if (map.getLayer(slot.layerId)) map.removeLayer(slot.layerId);
    }

    for (const slot of state.slots) {
      if (map.getSource(slot.sourceId)) map.removeSource(slot.sourceId);
    }
  }
}
