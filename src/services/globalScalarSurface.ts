import maplibregl from "maplibre-gl";

import { WEATHER_SURFACE_CROSSFADE_MS } from "../config/layerVisuals";
import { getWeatherInsertionLayerId } from "./mapLayerOrder";
import { loadNumericTile } from "./numericTileCache";

import type {
  ScalarFieldTimestep,
  ScalarWeatherFieldSource,
} from "../types/globalWeather";

const PROTOCOL = "meridian-scalar-weather";
type SlotIndex = 0 | 1;

interface Rgba {
  r: number;
  g: number;
  b: number;
  a: number;
}

interface RegisteredField {
  source: ScalarWeatherFieldSource;
  timestep: ScalarFieldTimestep;
  colour: (value: number) => Rgba;
  failed: boolean;
}

export interface GlobalScalarSurface {
  update(
    map: maplibregl.Map,
    source: ScalarWeatherFieldSource,
    timestep: ScalarFieldTimestep
  ): void;
  setEnabled(map: maplibregl.Map, enabled: boolean): void;
  remove(map: maplibregl.Map): void;
}

interface SurfaceOptions {
  id: string;
  opacity: number;
  colour: (value: number) => Rgba;
}

const registeredFields = new Map<number, RegisteredField>();
const reportedTileFailures = new Set<string>();
let protocolRegistered = false;
let nextFieldId = 0;

async function transparentTile(): Promise<ImageBitmap> {
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  return createImageBitmap(canvas);
}

function colourize(
  values: Uint8Array | Uint16Array,
  field: RegisteredField
): HTMLCanvasElement {
  const size = field.source.manifest.tiles.tileSize;
  const { noData, scale, offset } = field.source.manifest.tiles;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Could not create global weather tile context");
  const image = context.createImageData(size, size);

  for (let index = 0; index < values.length; index++) {
    const encoded = values[index];
    if (encoded === noData) continue;
    const color = field.colour(encoded * scale + offset);
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
    if (!field || abortController.signal.aborted) {
      return { data: await transparentTile() };
    }

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
      field.failed = true;
      if (!reportedTileFailures.has(request.url)) {
        reportedTileFailures.add(request.url);
        console.error(`Global ${field.source.manifest.field.id} tile failed`, error);
      }
      return { data: await transparentTile() };
    }
  });
  protocolRegistered = true;
}

function registerField(
  source: ScalarWeatherFieldSource,
  timestep: ScalarFieldTimestep,
  colour: (value: number) => Rgba
): number {
  const fieldId = ++nextFieldId;
  registeredFields.set(fieldId, { source, timestep, colour, failed: false });
  return fieldId;
}

export function createGlobalScalarSurface(
  options: SurfaceOptions
): GlobalScalarSurface {
  const slots = [
    {
      sourceId: `global-${options.id}-source-a`,
      layerId: `global-${options.id}-layer-a`,
      fieldId: null as number | null,
    },
    {
      sourceId: `global-${options.id}-source-b`,
      layerId: `global-${options.id}-layer-b`,
      fieldId: null as number | null,
    },
  ];
  let activeSlot: SlotIndex | null = null;
  let activeSignature: string | null = null;
  let pendingSignature: string | null = null;
  let transitionGeneration = 0;
  let enabled = false;

  const setEnabled = (map: maplibregl.Map, isEnabled: boolean) => {
    enabled = isEnabled;
    slots.forEach((slot, index) => {
      if (!map.getLayer(slot.layerId)) return;
      map.setPaintProperty(
        slot.layerId,
        "raster-opacity",
        isEnabled && index === activeSlot ? options.opacity : 0
      );
    });
  };

  const update = (
    map: maplibregl.Map,
    source: ScalarWeatherFieldSource,
    timestep: ScalarFieldTimestep
  ) => {
    enabled = true;
    if (activeSlot !== null && !map.getLayer(slots[activeSlot].layerId)) {
      activeSlot = null;
      activeSignature = null;
      pendingSignature = null;
      transitionGeneration += 1;
    }

    const signature = `${source.manifest.id}:${timestep.id}`;
    if (signature === activeSignature) {
      setEnabled(map, true);
      return;
    }
    if (signature === pendingSignature) return;

    ensureProtocol();
    const previousSlot = activeSlot;
    const nextSlot: SlotIndex = activeSlot === 0 ? 1 : 0;
    const slot = slots[nextSlot];
    if (slot.fieldId !== null) {
      registeredFields.delete(slot.fieldId);
      const prefix = `${PROTOCOL}://field/${slot.fieldId}/`;
      for (const url of reportedTileFailures) {
        if (url.startsWith(prefix)) reportedTileFailures.delete(url);
      }
    }
    const fieldId = registerField(source, timestep, options.colour);
    slot.fieldId = fieldId;
    const tileUrl = `${PROTOCOL}://field/${fieldId}/{z}/{x}/{y}`;
    const rasterSource = map.getSource(slot.sourceId) as
      | maplibregl.RasterTileSource
      | undefined;

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
      const field = registeredFields.get(fieldId);
      if (generation !== transitionGeneration || !map.getLayer(slot.layerId)) {
        map.off("sourcedata", onSourceData);
        return;
      }
      if (field?.failed) {
        map.off("sourcedata", onSourceData);
        pendingSignature = null;
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
        enabled ? options.opacity : 0
      );
      if (previousSlot !== null) {
        const previousLayer = slots[previousSlot].layerId;
        if (map.getLayer(previousLayer)) {
          map.setPaintProperty(previousLayer, "raster-opacity", 0);
        }
      }
    };
    const onSourceData = (event: maplibregl.MapSourceDataEvent) => {
      if (event.sourceId === slot.sourceId) reveal();
    };
    map.on("sourcedata", onSourceData);
    window.requestAnimationFrame(reveal);
    map.triggerRepaint();
  };

  const remove = (map: maplibregl.Map) => {
    transitionGeneration += 1;
    activeSlot = null;
    activeSignature = null;
    pendingSignature = null;
    enabled = false;
    for (const slot of slots) {
      if (map.getLayer(slot.layerId)) map.removeLayer(slot.layerId);
      if (slot.fieldId !== null) registeredFields.delete(slot.fieldId);
      slot.fieldId = null;
    }
    for (const slot of slots) {
      if (map.getSource(slot.sourceId)) map.removeSource(slot.sourceId);
    }
  };

  return { update, setEnabled, remove };
}
