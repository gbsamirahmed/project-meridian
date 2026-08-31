import maplibregl from "maplibre-gl";

import { LAYER_VISUAL_STRENGTHS, WEATHER_SURFACE_CROSSFADE_MS } from "../config/layerVisuals";
import { loadNumericTile } from "./numericTileCache";
import { precipitationColor } from "./precipitationStyle";
import { getWeatherInsertionLayerId } from "./mapLayerOrder";

import type {
  ScalarWeatherFieldSource,
  ScalarWeatherTimestep,
} from "../types/globalWeather";

const PROTOCOL = "meridian-scalar-weather";
const SLOT_IDS = [
  { sourceId: "global-precipitation-source-a", layerId: "global-precipitation-layer-a" },
  { sourceId: "global-precipitation-source-b", layerId: "global-precipitation-layer-b" },
] as const;
type SlotIndex = 0 | 1;

interface RegisteredField {
  source: ScalarWeatherFieldSource;
  timestep: ScalarWeatherTimestep;
}

const registeredFields = new Map<number, RegisteredField>();
let protocolRegistered = false;
let nextFieldId = 0;
let activeSlot: SlotIndex | null = null;
let activeSignature: string | null = null;
let pendingSignature: string | null = null;
let transitionGeneration = 0;
let enabled = false;

async function transparentTile(): Promise<ImageBitmap> {
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  return createImageBitmap(canvas);
}

function colourize(values: Uint16Array, field: RegisteredField): HTMLCanvasElement {
  const size = field.source.manifest.tiles.tileSize;
  const { noData, scale, offset } = field.source.manifest.tiles;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Could not create global precipitation tile context");
  const image = context.createImageData(size, size);

  for (let index = 0; index < values.length; index++) {
    const encoded = values[index];
    if (encoded === noData) continue;
    const color = precipitationColor(encoded * scale + offset);
    const pixel = index * 4;
    image.data[pixel] = color.r;
    image.data[pixel + 1] = color.g;
    image.data[pixel + 2] = color.b;
    image.data[pixel + 3] = color.a;
  }
  context.putImageData(image, 0, 0);
  return canvas;
}

function ensureProtocol(): void {
  if (protocolRegistered) return;
  maplibregl.addProtocol(PROTOCOL, async (request, abortController) => {
    const match = request.url.match(
      /^meridian-scalar-weather:\/\/field\/(\d+)\/(\d+)\/(\d+)\/(\d+)$/
    );
    if (!match) throw new Error("Invalid global scalar weather tile URL");

    const [, fieldValue, zoomValue, xValue, yValue] = match;
    const field = registeredFields.get(Number(fieldValue));
    if (!field || abortController.signal.aborted) return { data: await transparentTile() };

    try {
      const tile = await loadNumericTile(
        field.source,
        field.timestep,
        Number(zoomValue),
        Number(xValue),
        Number(yValue)
      );
      if (abortController.signal.aborted) return { data: await transparentTile() };
      return { data: await createImageBitmap(colourize(tile.values, field)) };
    } catch (error) {
      console.error("Global precipitation tile failed", error);
      return { data: await transparentTile() };
    }
  });
  protocolRegistered = true;
}

function registerField(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep
): number {
  const fieldId = ++nextFieldId;
  registeredFields.set(fieldId, { source, timestep });
  while (registeredFields.size > 24) {
    const oldest = registeredFields.keys().next().value as number | undefined;
    if (oldest === undefined) break;
    registeredFields.delete(oldest);
  }
  return fieldId;
}

export function updateGlobalPrecipitationLayer(
  map: maplibregl.Map,
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep
): void {
  enabled = true;
  if (activeSlot !== null && !map.getLayer(SLOT_IDS[activeSlot].layerId)) {
    activeSlot = null;
    activeSignature = null;
    pendingSignature = null;
    transitionGeneration += 1;
  }
  const signature = `${source.manifest.id}:${timestep.id}`;
  if (signature === activeSignature) {
    setGlobalPrecipitationEnabled(map, true);
    return;
  }
  if (signature === pendingSignature) return;

  ensureProtocol();
  const previousSlot = activeSlot;
  const nextSlot: SlotIndex = activeSlot === 0 ? 1 : 0;
  const slot = SLOT_IDS[nextSlot];
  const fieldId = registerField(source, timestep);
  const tileUrl = `${PROTOCOL}://field/${fieldId}/{z}/{x}/{y}`;
  const rasterSource = map.getSource(slot.sourceId) as maplibregl.RasterTileSource | undefined;

  if (rasterSource) {
    rasterSource.setTiles([tileUrl]);
  } else {
    map.addSource(slot.sourceId, {
      type: "raster",
      tiles: [tileUrl],
      tileSize: source.manifest.tiles.tileSize,
      minzoom: source.manifest.tiles.minZoom,
      maxzoom: source.manifest.tiles.maxZoom,
      bounds: source.manifest.coverage.bounds,
      attribution: `<a href="${source.manifest.attribution.url}" target="_blank">${source.manifest.attribution.label}</a>`,
    });
  }

  if (!map.getLayer(slot.layerId)) {
    map.addLayer(
      {
        id: slot.layerId,
        type: "raster",
        source: slot.sourceId,
        paint: {
          "raster-opacity": 0,
          "raster-resampling": "linear",
          "raster-fade-duration": 0,
        },
      },
      getWeatherInsertionLayerId(map)
    );
  }
  map.setPaintProperty(slot.layerId, "raster-opacity-transition", {
    duration: WEATHER_SURFACE_CROSSFADE_MS,
    delay: 0,
  });

  const generation = ++transitionGeneration;
  pendingSignature = signature;
  const reveal = () => {
    if (generation !== transitionGeneration || !map.getLayer(slot.layerId)) {
      map.off("sourcedata", onSourceData);
      return;
    }
    if (!map.isSourceLoaded(slot.sourceId)) return;

    map.off("sourcedata", onSourceData);
    activeSlot = nextSlot;
    activeSignature = signature;
    pendingSignature = null;
    map.setPaintProperty(
      slot.layerId,
      "raster-opacity",
      enabled ? LAYER_VISUAL_STRENGTHS.precipitation : 0
    );
    if (previousSlot !== null) {
      const previousLayer = SLOT_IDS[previousSlot].layerId;
      if (map.getLayer(previousLayer)) map.setPaintProperty(previousLayer, "raster-opacity", 0);
    }
  };
  const onSourceData = (event: maplibregl.MapSourceDataEvent) => {
    if (event.sourceId === slot.sourceId) reveal();
  };
  map.on("sourcedata", onSourceData);
  window.requestAnimationFrame(reveal);
  map.triggerRepaint();
}

export function setGlobalPrecipitationEnabled(map: maplibregl.Map, isEnabled: boolean): void {
  enabled = isEnabled;
  SLOT_IDS.forEach((slot, index) => {
    if (!map.getLayer(slot.layerId)) return;
    map.setPaintProperty(
      slot.layerId,
      "raster-opacity",
      isEnabled && index === activeSlot ? LAYER_VISUAL_STRENGTHS.precipitation : 0
    );
  });
}

export function removeGlobalPrecipitationLayer(map: maplibregl.Map): void {
  transitionGeneration += 1;
  activeSlot = null;
  activeSignature = null;
  pendingSignature = null;
  enabled = false;
  registeredFields.clear();
  for (const slot of SLOT_IDS) {
    if (map.getLayer(slot.layerId)) map.removeLayer(slot.layerId);
  }
  for (const slot of SLOT_IDS) {
    if (map.getSource(slot.sourceId)) map.removeSource(slot.sourceId);
  }
}
