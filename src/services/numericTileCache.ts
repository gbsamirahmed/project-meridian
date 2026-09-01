import {
  resolveScalarTileUrl,
  resolveVectorTileUrl,
} from "./globalWeatherService";

import type {
  ScalarWeatherFieldSource,
  ScalarWeatherTimestep,
  VectorWeatherFieldSource,
  VectorWeatherTimestep,
} from "../types/globalWeather";

export interface ScalarNumericTile {
  kind: "scalar";
  values: Uint8Array | Uint16Array;
  size: number;
  byteLength: number;
}

export interface VectorNumericTile {
  kind: "vector";
  uCodes: Uint16Array;
  vCodes: Uint16Array;
  size: number;
  byteLength: number;
}

type WeatherNumericTile = ScalarNumericTile | VectorNumericTile;

const MAX_CACHE_BYTES = 64 * 1024 * 1024;
const tileCache = new Map<string, WeatherNumericTile>();
const pendingTiles = new Map<string, Promise<WeatherNumericTile>>();
const pinsByOwner = new Map<string, Set<string>>();
let cachedBytes = 0;

function isPinned(url: string): boolean {
  for (const urls of pinsByOwner.values()) {
    if (urls.has(url)) return true;
  }
  return false;
}

function retainTile<T extends WeatherNumericTile>(url: string, tile: T): T {
  const replaced = tileCache.get(url);
  if (replaced) cachedBytes -= replaced.byteLength;
  tileCache.delete(url);
  tileCache.set(url, tile);
  cachedBytes += tile.byteLength;

  while (cachedBytes > MAX_CACHE_BYTES) {
    const oldestKey = [...tileCache.keys()].find((key) => !isPinned(key));
    if (!oldestKey) break;
    const oldest = tileCache.get(oldestKey);
    tileCache.delete(oldestKey);
    if (oldest) cachedBytes -= oldest.byteLength;
  }
  return tile;
}

function touchTile<T extends WeatherNumericTile>(url: string, tile: T): T {
  tileCache.delete(url);
  tileCache.set(url, tile);
  return tile;
}

export function decodeNumericPixels(
  rgba: Uint8ClampedArray,
  encoding: ScalarWeatherFieldSource["manifest"]["tiles"]["encoding"]
): Uint8Array | Uint16Array {
  const length = rgba.length / 4;
  if (encoding === "uint8-r") {
    const values = new Uint8Array(length);
    for (let index = 0; index < length; index++) values[index] = rgba[index * 4];
    return values;
  }

  const values = new Uint16Array(length);
  for (let index = 0; index < length; index++) {
    values[index] = rgba[index * 4] * 256 + rgba[index * 4 + 1];
  }
  return values;
}

export function decodeVectorPixels(
  rgba: Uint8ClampedArray
): Pick<VectorNumericTile, "uCodes" | "vCodes"> {
  const length = rgba.length / 4;
  const uCodes = new Uint16Array(length);
  const vCodes = new Uint16Array(length);
  for (let index = 0; index < length; index++) {
    const offset = index * 4;
    const red = rgba[offset];
    const green = rgba[offset + 1];
    const blue = rgba[offset + 2];
    uCodes[index] = (red << 2) | (green >> 6);
    vCodes[index] = ((green & 0x3f) << 4) | (blue >> 4);
  }
  return { uCodes, vCodes };
}

async function decodeNumericPng(
  url: string,
  tileSize: number,
  encoding: ScalarWeatherFieldSource["manifest"]["tiles"]["encoding"]
): Promise<ScalarNumericTile> {
  const response = await fetch(url, { cache: "force-cache" });
  if (!response.ok) throw new Error(`Numeric weather tile returned HTTP ${response.status}`);

  const bitmap = await createImageBitmap(await response.blob());
  const canvas = document.createElement("canvas");
  canvas.width = tileSize;
  canvas.height = tileSize;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) {
    bitmap.close();
    throw new Error("Could not decode numeric weather tile");
  }

  context.drawImage(bitmap, 0, 0, tileSize, tileSize);
  bitmap.close();
  const rgba = context.getImageData(0, 0, tileSize, tileSize).data;
  const values = decodeNumericPixels(rgba, encoding);
  return {
    kind: "scalar",
    values,
    size: tileSize,
    byteLength: values.byteLength,
  };
}

async function decodeVectorPng(
  url: string,
  tileSize: number
): Promise<VectorNumericTile> {
  const response = await fetch(url, { cache: "force-cache" });
  if (!response.ok) {
    throw new Error(`Numeric wind tile returned HTTP ${response.status}`);
  }
  const bitmap = await createImageBitmap(await response.blob());
  const canvas = document.createElement("canvas");
  canvas.width = tileSize;
  canvas.height = tileSize;
  const context = canvas.getContext("2d", { willReadFrequently: true });
  if (!context) {
    bitmap.close();
    throw new Error("Could not decode numeric wind tile");
  }
  context.drawImage(bitmap, 0, 0, tileSize, tileSize);
  bitmap.close();
  const decoded = decodeVectorPixels(
    context.getImageData(0, 0, tileSize, tileSize).data
  );
  return {
    kind: "vector",
    ...decoded,
    size: tileSize,
    byteLength: decoded.uCodes.byteLength + decoded.vCodes.byteLength,
  };
}

export function loadNumericTile(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  zoom: number,
  x: number,
  y: number
): Promise<ScalarNumericTile> {
  const url = resolveScalarTileUrl(source, timestep, zoom, x, y);
  const cached = tileCache.get(url);
  if (cached?.kind === "scalar") return Promise.resolve(touchTile(url, cached));

  const pending = pendingTiles.get(url);
  if (pending) return pending as Promise<ScalarNumericTile>;

  const request = decodeNumericPng(
    url,
    source.manifest.tiles.tileSize,
    source.manifest.tiles.encoding
  )
    .then((tile) => retainTile(url, tile))
    .finally(() => pendingTiles.delete(url));
  pendingTiles.set(url, request);
  return request;
}


export function loadVectorTile(
  source: VectorWeatherFieldSource,
  timestep: VectorWeatherTimestep,
  zoom: number,
  x: number,
  y: number
): Promise<VectorNumericTile> {
  const url = resolveVectorTileUrl(source, timestep, zoom, x, y);
  const cached = tileCache.get(url);
  if (cached?.kind === "vector") return Promise.resolve(touchTile(url, cached));
  const pending = pendingTiles.get(url);
  if (pending) return pending as Promise<VectorNumericTile>;
  const request = decodeVectorPng(url, source.manifest.tiles.tileSize)
    .then((tile) => retainTile(url, tile))
    .finally(() => pendingTiles.delete(url));
  pendingTiles.set(url, request);
  return request;
}

export function getCachedVectorTile(
  source: VectorWeatherFieldSource,
  timestep: VectorWeatherTimestep,
  zoom: number,
  x: number,
  y: number
): VectorNumericTile | null {
  const url = resolveVectorTileUrl(source, timestep, zoom, x, y);
  const cached = tileCache.get(url);
  return cached?.kind === "vector" ? touchTile(url, cached) : null;
}

export function getCachedScalarTile(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  zoom: number,
  x: number,
  y: number
): ScalarNumericTile | null {
  const url = resolveScalarTileUrl(source, timestep, zoom, x, y);
  const cached = tileCache.get(url);
  return cached?.kind === "scalar" ? touchTile(url, cached) : null;
}

async function readVectorWorldPixel(
  source: VectorWeatherFieldSource,
  timestep: VectorWeatherTimestep,
  pixelX: number,
  pixelY: number
): Promise<{ u: number; v: number } | null> {
  const {
    maxZoom,
    tileSize,
    componentScale,
    componentBias,
    noDataCode,
  } = source.manifest.tiles;
  const count = 2 ** maxZoom;
  const worldSize = count * tileSize;
  const wrappedX = ((pixelX % worldSize) + worldSize) % worldSize;
  const limitedY = Math.max(0, Math.min(worldSize - 1, pixelY));
  const tileX = Math.floor(wrappedX / tileSize);
  const tileY = Math.floor(limitedY / tileSize);
  const localX = wrappedX % tileSize;
  const localY = limitedY % tileSize;
  const tile = await loadVectorTile(
    source,
    timestep,
    maxZoom,
    tileX,
    tileY
  );
  const index = localY * tile.size + localX;
  const uCode = tile.uCodes[index];
  const vCode = tile.vCodes[index];
  if (uCode === noDataCode || vCode === noDataCode) return null;
  return {
    u: (uCode - componentBias) * componentScale,
    v: (vCode - componentBias) * componentScale,
  };
}

export async function sampleVectorField(
  source: VectorWeatherFieldSource,
  timestep: VectorWeatherTimestep,
  longitude: number,
  latitude: number
): Promise<{ u: number; v: number } | null> {
  if (
    latitude < source.manifest.coverage.bounds[1] ||
    latitude > source.manifest.coverage.bounds[3]
  ) {
    return null;
  }
  const { maxZoom, tileSize } = source.manifest.tiles;
  const worldSize = 2 ** maxZoom * tileSize;
  const worldX = longitudeToWorldX(longitude, worldSize);
  const worldY = latitudeToWorldY(latitude, worldSize);
  const x0 = Math.floor(worldX);
  const y0 = Math.floor(worldY);
  const xWeight = worldX - x0;
  const yWeight = worldY - y0;
  const samples = await Promise.all([
    readVectorWorldPixel(source, timestep, x0, y0),
    readVectorWorldPixel(source, timestep, x0 + 1, y0),
    readVectorWorldPixel(source, timestep, x0, y0 + 1),
    readVectorWorldPixel(source, timestep, x0 + 1, y0 + 1),
  ]);
  if (samples.some((sample) => sample === null)) return null;
  const [topLeft, topRight, bottomLeft, bottomRight] = samples as Array<{
    u: number;
    v: number;
  }>;
  const interpolate = (key: "u" | "v") => {
    const top = topLeft[key] * (1 - xWeight) + topRight[key] * xWeight;
    const bottom =
      bottomLeft[key] * (1 - xWeight) + bottomRight[key] * xWeight;
    return top * (1 - yWeight) + bottom * yWeight;
  };
  return { u: interpolate("u"), v: interpolate("v") };
}

export function setNumericTilePins(owner: string, urls: Iterable<string>): void {
  pinsByOwner.set(owner, new Set(urls));
}

export function clearNumericTilePins(owner: string): void {
  pinsByOwner.delete(owner);
}

export function getNumericTileCacheStats(): {
  bytes: number;
  tileCount: number;
  pendingCount: number;
} {
  return {
    bytes: cachedBytes,
    tileCount: tileCache.size,
    pendingCount: pendingTiles.size,
  };
}

function longitudeToWorldX(longitude: number, worldSize: number): number {
  const wrapped = ((longitude + 180) % 360 + 360) % 360;
  return (wrapped / 360) * worldSize - 0.5;
}

function latitudeToWorldY(latitude: number, worldSize: number): number {
  const limited = Math.max(-85.05112878, Math.min(85.05112878, latitude));
  const sine = Math.sin((limited * Math.PI) / 180);
  return (
    (0.5 - Math.log((1 + sine) / (1 - sine)) / (4 * Math.PI)) * worldSize - 0.5
  );
}

function readCachedScalarWorldPixel(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  zoom: number,
  pixelX: number,
  pixelY: number
): number | null | undefined {
  const { tileSize, noData, scale, offset } = source.manifest.tiles;
  const tileCount = 2 ** zoom;
  const worldSize = tileCount * tileSize;
  const wrappedX = ((pixelX % worldSize) + worldSize) % worldSize;
  const limitedY = Math.max(0, Math.min(worldSize - 1, pixelY));
  const tileX = Math.floor(wrappedX / tileSize);
  const tileY = Math.floor(limitedY / tileSize);
  const localX = wrappedX % tileSize;
  const localY = limitedY % tileSize;
  const tile = getCachedScalarTile(source, timestep, zoom, tileX, tileY);
  if (!tile) return undefined;
  const encoded = tile.values[localY * tile.size + localX];
  return encoded === noData ? null : encoded * scale + offset;
}

export function sampleCachedScalarField(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  zoom: number,
  longitude: number,
  latitude: number
): number | null | undefined {
  if (
    latitude < source.manifest.coverage.bounds[1] ||
    latitude > source.manifest.coverage.bounds[3]
  ) {
    return null;
  }
  const worldSize = 2 ** zoom * source.manifest.tiles.tileSize;
  const worldX = longitudeToWorldX(longitude, worldSize);
  const worldY = latitudeToWorldY(latitude, worldSize);
  const x0 = Math.floor(worldX);
  const y0 = Math.floor(worldY);
  const xWeight = worldX - x0;
  const yWeight = worldY - y0;
  const samples = [
    readCachedScalarWorldPixel(source, timestep, zoom, x0, y0),
    readCachedScalarWorldPixel(source, timestep, zoom, x0 + 1, y0),
    readCachedScalarWorldPixel(source, timestep, zoom, x0, y0 + 1),
    readCachedScalarWorldPixel(source, timestep, zoom, x0 + 1, y0 + 1),
  ];
  if (samples.some((value) => value === undefined)) return undefined;
  if (samples.some((value) => value === null)) return null;
  const [topLeft, topRight, bottomLeft, bottomRight] = samples as number[];
  const top = topLeft * (1 - xWeight) + topRight * xWeight;
  const bottom = bottomLeft * (1 - xWeight) + bottomRight * xWeight;
  return top * (1 - yWeight) + bottom * yWeight;
}

async function readWorldPixel(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  pixelX: number,
  pixelY: number
): Promise<number | null> {
  const { maxZoom, tileSize, noData, scale, offset } = source.manifest.tiles;
  const tileCount = 2 ** maxZoom;
  const worldSize = tileCount * tileSize;
  const wrappedX = ((pixelX % worldSize) + worldSize) % worldSize;
  const limitedY = Math.max(0, Math.min(worldSize - 1, pixelY));
  const tileX = Math.floor(wrappedX / tileSize);
  const tileY = Math.floor(limitedY / tileSize);
  const localX = wrappedX % tileSize;
  const localY = limitedY % tileSize;
  const tile = await loadNumericTile(source, timestep, maxZoom, tileX, tileY);
  const encoded = tile.values[localY * tile.size + localX];
  return encoded === noData ? null : encoded * scale + offset;
}

export async function sampleScalarField(
  source: ScalarWeatherFieldSource,
  timestep: ScalarWeatherTimestep,
  longitude: number,
  latitude: number
): Promise<number | null> {
  if (latitude < source.manifest.coverage.bounds[1] || latitude > source.manifest.coverage.bounds[3]) {
    return null;
  }

  const { maxZoom, tileSize } = source.manifest.tiles;
  const worldSize = 2 ** maxZoom * tileSize;
  const worldX = longitudeToWorldX(longitude, worldSize);
  const worldY = latitudeToWorldY(latitude, worldSize);
  const x0 = Math.floor(worldX);
  const y0 = Math.floor(worldY);
  const xWeight = worldX - x0;
  const yWeight = worldY - y0;
  const [topLeft, topRight, bottomLeft, bottomRight] = await Promise.all([
    readWorldPixel(source, timestep, x0, y0),
    readWorldPixel(source, timestep, x0 + 1, y0),
    readWorldPixel(source, timestep, x0, y0 + 1),
    readWorldPixel(source, timestep, x0 + 1, y0 + 1),
  ]);

  if ([topLeft, topRight, bottomLeft, bottomRight].some((value) => value === null)) {
    return null;
  }
  const top = topLeft! * (1 - xWeight) + topRight! * xWeight;
  const bottom = bottomLeft! * (1 - xWeight) + bottomRight! * xWeight;
  return top * (1 - yWeight) + bottom * yWeight;
}

export function clearNumericTileCache(): void {
  tileCache.clear();
  pendingTiles.clear();
  pinsByOwner.clear();
  cachedBytes = 0;
}
