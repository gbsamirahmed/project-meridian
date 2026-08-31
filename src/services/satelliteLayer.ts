import type maplibregl from "maplibre-gl";

import { SATELLITE_PROVIDER } from "../config/satelliteProvider";
import {
  ELEVATION_RELIEF_LAYER_ID,
  HILLSHADE_LAYER_ID,
} from "./terrainLayers";

export const SATELLITE_SOURCE_ID = "satellite-imagery-source";
export const SATELLITE_LAYER_ID = "satellite-imagery-layer";

export type SatelliteLayerStatus =
  | "unavailable"
  | "idle"
  | "loading"
  | "ready"
  | "degraded"
  | "error";

interface TileJsonMetadata {
  tiles: string[];
  attribution: string;
  bounds?: [number, number, number, number];
  minzoom?: number;
  maxzoom?: number;
  scheme?: "xyz" | "tms";
}

interface RawTileJsonMetadata {
  tiles?: unknown;
  attribution?: unknown;
  bounds?: unknown;
  minzoom?: unknown;
  maxzoom?: unknown;
  scheme?: unknown;
}

const basemapVisibilityByMap = new WeakMap<
  maplibregl.Map,
  Map<string, "visible" | "none">
>();
const satelliteLoadByMap = new WeakMap<
  maplibregl.Map,
  Promise<SatelliteLayerStatus>
>();
const satelliteMetadataByMap = new WeakMap<
  maplibregl.Map,
  TileJsonMetadata
>();
const satelliteFailedByMap = new WeakSet<maplibregl.Map>();

function readOptionalNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function readOptionalBounds(
  value: unknown
): [number, number, number, number] | undefined {
  if (
    !Array.isArray(value) ||
    value.length !== 4 ||
    !value.every((coordinate) =>
      typeof coordinate === "number" && Number.isFinite(coordinate)
    )
  ) {
    return undefined;
  }

  return value as [number, number, number, number];
}

function parseTileJsonMetadata(value: unknown): TileJsonMetadata | null {
  if (!value || typeof value !== "object") return null;

  const metadata = value as RawTileJsonMetadata;
  if (
    !Array.isArray(metadata.tiles) ||
    metadata.tiles.length === 0 ||
    !metadata.tiles.every(
      (tile) => typeof tile === "string" && tile.length > 0
    ) ||
    typeof metadata.attribution !== "string" ||
    metadata.attribution.trim().length === 0
  ) {
    return null;
  }

  const minzoom = readOptionalNumber(metadata.minzoom);
  const maxzoom = readOptionalNumber(metadata.maxzoom);
  const bounds = readOptionalBounds(metadata.bounds);
  const scheme =
    metadata.scheme === "xyz" || metadata.scheme === "tms"
      ? metadata.scheme
      : undefined;

  return {
    tiles: metadata.tiles,
    attribution: metadata.attribution,
    ...(bounds ? { bounds } : {}),
    ...(minzoom !== undefined ? { minzoom } : {}),
    ...(maxzoom !== undefined ? { maxzoom } : {}),
    ...(scheme ? { scheme } : {}),
  };
}

export function captureSatelliteBasemapLayers(map: maplibregl.Map): void {
  const visibility = new Map<string, "visible" | "none">();

  for (const layer of map.getStyle().layers) {
    if (layer.type === "background" || layer.type === "symbol") continue;

    visibility.set(
      layer.id,
      layer.layout?.visibility === "none" ? "none" : "visible"
    );
  }

  basemapVisibilityByMap.set(map, visibility);
}

function setConventionalBasemapVisible(
  map: maplibregl.Map,
  visible: boolean
): void {
  const layerVisibility = basemapVisibilityByMap.get(map);
  if (!layerVisibility) return;

  for (const [layerId, originalVisibility] of layerVisibility) {
    if (!map.getLayer(layerId)) continue;

    map.setLayoutProperty(
      layerId,
      "visibility",
      visible ? originalVisibility : "none"
    );
  }
}

function getSatelliteInsertionLayerId(
  map: maplibregl.Map
): string | undefined {
  if (map.getLayer(ELEVATION_RELIEF_LAYER_ID)) {
    return ELEVATION_RELIEF_LAYER_ID;
  }

  if (map.getLayer(HILLSHADE_LAYER_ID)) return HILLSHADE_LAYER_ID;

  return map.getStyle().layers.find((layer) => layer.type === "symbol")?.id;
}

function addSatelliteSourceAndLayer(
  map: maplibregl.Map,
  metadata: TileJsonMetadata
): void {
  if (!map.getSource(SATELLITE_SOURCE_ID)) {
    map.addSource(SATELLITE_SOURCE_ID, {
      type: "raster",
      tiles: metadata.tiles,
      tileSize: SATELLITE_PROVIDER.tileSize,
      attribution: metadata.attribution,
      ...(metadata.bounds ? { bounds: metadata.bounds } : {}),
      ...(metadata.minzoom !== undefined
        ? { minzoom: metadata.minzoom }
        : {}),
      ...(metadata.maxzoom !== undefined
        ? { maxzoom: metadata.maxzoom }
        : {}),
      ...(metadata.scheme ? { scheme: metadata.scheme } : {}),
    });
  }

  if (!map.getLayer(SATELLITE_LAYER_ID)) {
    map.addLayer(
      {
        id: SATELLITE_LAYER_ID,
        type: "raster",
        source: SATELLITE_SOURCE_ID,
        layout: { visibility: "none" },
        paint: {
          "raster-opacity": 1,
          "raster-fade-duration": 180,
          "raster-resampling": "linear",
        },
      },
      getSatelliteInsertionLayerId(map)
    );
  }
}

export function ensureSatelliteLayer(
  map: maplibregl.Map
): Promise<SatelliteLayerStatus> {
  if (!SATELLITE_PROVIDER.tileJsonUrl) {
    return Promise.resolve("unavailable");
  }

  if (map.getSource(SATELLITE_SOURCE_ID) && map.getLayer(SATELLITE_LAYER_ID)) {
    return Promise.resolve("ready");
  }

  if (satelliteFailedByMap.has(map)) return Promise.resolve("error");

  const cachedMetadata = satelliteMetadataByMap.get(map);
  if (cachedMetadata && map.isStyleLoaded()) {
    addSatelliteSourceAndLayer(map, cachedMetadata);
    return Promise.resolve("ready");
  }

  const pendingLoad = satelliteLoadByMap.get(map);
  if (pendingLoad) return pendingLoad;

  const load = fetch(SATELLITE_PROVIDER.tileJsonUrl)
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Satellite metadata returned HTTP ${response.status}`);
      }

      const metadata = parseTileJsonMetadata(await response.json());
      if (!metadata) {
        throw new Error("Satellite metadata did not contain raster tiles");
      }

      satelliteMetadataByMap.set(map, metadata);
      if (!map.isStyleLoaded()) return "error" as const;

      addSatelliteSourceAndLayer(map, metadata);
      return "ready" as const;
    })
    .catch((error: unknown) => {
      satelliteFailedByMap.add(map);
      console.warn("Satellite imagery is unavailable for this session.", error);
      return "error" as const;
    })
    .finally(() => {
      satelliteLoadByMap.delete(map);
    });

  satelliteLoadByMap.set(map, load);
  return load;
}

export function applySatelliteLayerState(
  map: maplibregl.Map,
  enabled: boolean
): void {
  const canShowSatellite =
    enabled &&
    !satelliteFailedByMap.has(map) &&
    map.getLayer(SATELLITE_LAYER_ID) !== undefined;

  setConventionalBasemapVisible(map, !canShowSatellite);

  if (map.getLayer(SATELLITE_LAYER_ID)) {
    map.setLayoutProperty(
      SATELLITE_LAYER_ID,
      "visibility",
      canShowSatellite ? "visible" : "none"
    );
  }
}
